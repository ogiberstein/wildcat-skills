"""Replay has no provider client and a miss cannot leave loopback."""

import http.client
from pathlib import Path
import socket
from threading import Thread
import tempfile
import unittest
from unittest import mock

from lazarus_lib.canonical import dumps, loads
from lazarus_lib.server import make_server
from lazarus import parser

from .test_replay import custom_material
from .test_verifier import write_fixture


class NoNetworkTests(unittest.TestCase):
    def test_replay_modules_do_not_import_capture_or_provider_transports(self):
        root = Path(__file__).resolve().parents[1] / "scripts" / "lazarus_lib"
        text = (root / "replay.py").read_text() + (root / "server.py").read_text()
        for forbidden in ("JsonRpcClient", "rpc_url", "urllib", "from .capture", "from .rpc"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)
        cli_lines = (root.parent / "lazarus.py").read_text().splitlines()
        top_level_imports = [
            line for line in cli_lines if line.startswith("from lazarus_lib")
        ]
        self.assertFalse(any("capture" in line or ".rpc" in line for line in top_level_imports))
        arguments = parser().parse_args(["replay", "/fixture"])
        self.assertFalse(hasattr(arguments, "rpc_url"))
        self.assertFalse(hasattr(arguments, "fallback"))

    def test_miss_uses_only_the_loopback_connection(self):
        material = custom_material(method="eth_chainId", params=[], result="0x1")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, material)
            server = make_server(root, port=0)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            real_connect = socket.socket.connect
            destinations = []

            def guarded_connect(sock, address):
                destinations.append(address)
                host = address[0]
                if not ip_is_loopback(host):
                    raise AssertionError(f"outbound replay connection: {address}")
                return real_connect(sock, address)

            try:
                with mock.patch.object(socket.socket, "connect", guarded_connect):
                    connection = http.client.HTTPConnection(*server.server_address, timeout=2)
                    body = dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "eth_getStorageAt",
                            "params": ["0x" + "11" * 20, "0x" + "00" * 32, "0x0"],
                        }
                    )
                    connection.request("POST", "/", body=body)
                    response = connection.getresponse()
                    payload = loads(response.read())
                    connection.close()
                self.assertEqual(payload["error"]["code"], -32070)
                self.assertTrue(destinations)
                self.assertTrue(all(ip_is_loopback(item[0]) for item in destinations))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


def ip_is_loopback(host):
    return host in {"127.0.0.1", "::1"}


if __name__ == "__main__":
    unittest.main()
