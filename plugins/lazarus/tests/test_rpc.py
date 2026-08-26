"""The capture transport bounds and reorders JSON-RPC without leaking errors."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import unittest

from lazarus_lib.errors import FormatError, ResourceLimitError
from lazarus_lib.limits import CaptureLimits
from lazarus_lib.rpc import JsonRpcClient, RpcTransportError

from .fake_rpc import FakeRpc, RpcError


def limits(**changes):
    values = {
        "max_requests": 20,
        "max_component_bytes": 4096,
        "max_total_bytes": 16384,
        "max_elapsed_seconds": 10,
    }
    values.update(changes)
    return CaptureLimits(values)


class RpcTests(unittest.TestCase):
    def test_out_of_order_batch_responses_return_in_request_order(self):
        def dispatch(method, params, server):
            return params[0]

        with FakeRpc(dispatch, reverse_batches=True) as server:
            client = JsonRpcClient(server.url, limits())
            outcomes = client.request_many([("one", [1]), ("two", [2]), ("three", [3])])
        self.assertEqual([item.result for item in outcomes], [1, 2, 3])

    def test_rpc_errors_keep_only_code_and_stable_message(self):
        def dispatch(method, params, server):
            return RpcError(-32602, "secret provider URL", {"token": "bearer-secret"})

        with FakeRpc(dispatch) as server:
            outcome = JsonRpcClient(server.url, limits()).request_many([("bad", [])])[0]
        self.assertEqual(
            outcome.error,
            {"code": -32602, "message": "provider request failed"},
        )

    def test_missing_or_duplicate_batch_ids_fail(self):
        raw = b'[{"jsonrpc":"2.0","id":1,"result":1},{"jsonrpc":"2.0","id":1,"result":2}]'
        with FakeRpc(lambda *args: None, raw_response=raw) as server:
            client = JsonRpcClient(server.url, limits())
            with self.assertRaisesRegex(FormatError, "duplicate"):
                client.request_many([("one", []), ("two", [])])

    def test_response_body_is_bounded_before_json_parsing(self):
        with FakeRpc(lambda *args: None, raw_response=b" " * 65) as server:
            client = JsonRpcClient(server.url, limits(max_component_bytes=64))
            with self.assertRaisesRegex(ResourceLimitError, "RPC response"):
                client.call("large", [])

    def test_declared_response_size_is_validated_before_reading(self):
        valid = b'{"jsonrpc":"2.0","id":1,"result":"0x1"}'
        with FakeRpc(
            lambda *args: None,
            raw_response=valid,
            declared_length="not-a-number",
        ) as server:
            with self.assertRaisesRegex(RpcTransportError, "content length"):
                JsonRpcClient(server.url, limits()).call("invalid-length", [])
        with FakeRpc(
            lambda *args: None,
            raw_response=valid,
            declared_length="4097",
        ) as server:
            with self.assertRaisesRegex(ResourceLimitError, "RPC response"):
                JsonRpcClient(server.url, limits()).call("oversized-length", [])

    def test_hostile_response_nesting_is_bounded(self):
        nested = b'{"jsonrpc":"2.0","id":1,"result":' + b'{"x":' * 65
        nested += b"0" + b"}" * 66
        with FakeRpc(lambda *args: None, raw_response=nested) as server:
            with self.assertRaisesRegex(ResourceLimitError, "nesting"):
                JsonRpcClient(
                    server.url,
                    limits(max_component_bytes=16384, max_total_bytes=32768),
                ).call("nested", [])

    def test_redirects_are_refused_before_credentials_reach_another_origin(self):
        received = []

        class Target(BaseHTTPRequestHandler):
            def do_GET(self):
                received.append(self.headers.get("Authorization"))
                self.send_response(200)
                self.end_headers()

            def log_message(self, format, *args):
                return

        target = ThreadingHTTPServer(("127.0.0.1", 0), Target)
        target_thread = Thread(target=target.serve_forever, daemon=True)
        target_thread.start()
        target_url = f"http://127.0.0.1:{target.server_address[1]}/target"

        class Redirect(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(302)
                self.send_header("Location", target_url)
                self.end_headers()

            def log_message(self, format, *args):
                return

        redirect = ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
        redirect_thread = Thread(target=redirect.serve_forever, daemon=True)
        redirect_thread.start()
        try:
            url = f"http://127.0.0.1:{redirect.server_address[1]}/rpc"
            client = JsonRpcClient(
                url,
                limits(),
                headers={"Authorization": "Bearer redirect-secret"},
            )
            with self.assertRaisesRegex(RpcTransportError, "transport"):
                client.call("eth_chainId", [])
            self.assertEqual(received, [])
        finally:
            redirect.shutdown()
            redirect.server_close()
            redirect_thread.join(timeout=2)
            target.shutdown()
            target.server_close()
            target_thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
