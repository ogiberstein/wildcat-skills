"""The loopback transport implements single, batch and notification JSON-RPC."""

from concurrent.futures import ThreadPoolExecutor
import http.client
import json
from pathlib import Path
from threading import Thread
import tempfile
import unittest
from unittest import mock

from lazarus_lib.errors import LazarusError
from lazarus_lib.replay import INVALID_REQUEST, PARSE_ERROR
from lazarus_lib.server import ReplayHTTPServer, make_server
from lazarus import run

from .test_replay import custom_material
from .test_verifier import write_fixture


class RunningServer:
    def __init__(self, fixture: Path):
        self.server = make_server(fixture, port=0)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)

    @property
    def address(self):
        return self.server.server_address

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def post(self, body):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        connection = http.client.HTTPConnection(*self.address, timeout=2)
        connection.request(
            "POST",
            "/",
            body=raw,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        data = response.read()
        connection.close()
        return response.status, None if not data else json.loads(data)


class ServerTests(unittest.TestCase):
    def fixture(self, root: Path):
        material = custom_material(method="eth_chainId", params=[], result="0x1")
        write_fixture(root, material)

    def test_server_binds_only_loopback_after_fixture_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            server = make_server(root, port=0)
            try:
                self.assertEqual(server.server_address[0], "127.0.0.1")
            finally:
                server.server_close()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with (root / "rpc.jsonl").open("ab") as handle:
                handle.write(b"\n")
            with mock.patch.object(
                ReplayHTTPServer,
                "server_bind",
                side_effect=AssertionError("bind happened before verification"),
            ):
                with self.assertRaises(LazarusError):
                    make_server(root, port=0)

    def test_cli_routes_replay_to_the_loopback_server(self):
        with mock.patch("lazarus_lib.server.serve_fixture") as serve:
            self.assertEqual(run(["replay", "/fixture", "--port", "9753"]), 0)
        serve.assert_called_once_with(Path("/fixture"), port=9753)

    def test_single_request_and_caller_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with RunningServer(root) as server:
                status, body = server.post(
                    {"params": [], "method": "eth_chainId", "id": "mine", "jsonrpc": "2.0"}
                )
            self.assertEqual(status, 200)
            self.assertEqual(body, {"jsonrpc": "2.0", "id": "mine", "result": "0x1"})

    def test_batch_mixed_with_notifications_omits_notification_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            request = [
                {"jsonrpc": "2.0", "method": "eth_chainId", "params": []},
                {"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []},
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "eth_getStorageAt",
                    "params": ["0x" + "11" * 20, "0x" + "00" * 32, "0x0"],
                },
            ]
            with RunningServer(root) as server:
                status, body = server.post(request)
            self.assertEqual(status, 200)
            self.assertEqual([item["id"] for item in body], [1, 2])
            self.assertEqual(body[0]["result"], "0x1")
            self.assertEqual(body[1]["error"]["code"], -32070)

    def test_only_notifications_returns_no_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with RunningServer(root) as server:
                status, body = server.post(
                    [
                        {"jsonrpc": "2.0", "method": "eth_chainId", "params": []},
                        {
                            "jsonrpc": "2.0",
                            "method": "eth_getStorageAt",
                            "params": ["0x" + "11" * 20, "0x" + "00" * 32, "0x0"],
                        },
                    ]
                )
            self.assertEqual((status, body), (204, None))

    def test_malformed_json_rpc_and_empty_batches_return_stable_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with RunningServer(root) as server:
                malformed = server.post(b"{")
                empty = server.post([])
                invalid = server.post({"jsonrpc": "2.0", "id": True, "method": "x"})
            self.assertEqual(malformed[1]["error"]["code"], PARSE_ERROR)
            self.assertEqual(empty[1]["error"]["code"], INVALID_REQUEST)
            self.assertEqual(invalid[1]["error"]["code"], INVALID_REQUEST)

    def test_concurrent_reads_are_immutable_and_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with RunningServer(root) as server:
                def read(identifier):
                    return server.post(
                        {"jsonrpc": "2.0", "id": identifier, "method": "eth_chainId", "params": []}
                    )

                with ThreadPoolExecutor(max_workers=8) as pool:
                    responses = list(pool.map(read, range(32)))
            self.assertEqual([body["id"] for status, body in responses], list(range(32)))
            self.assertTrue(all(status == 200 for status, body in responses))
            self.assertTrue(all(body["result"] == "0x1" for status, body in responses))


if __name__ == "__main__":
    unittest.main()
