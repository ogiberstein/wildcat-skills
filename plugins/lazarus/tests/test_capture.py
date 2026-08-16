"""A fake archive RPC exercises the complete finite capture boundary."""

import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from lazarus_lib.canonical import dump
from lazarus_lib.capture import CaptureError, _atomic_no_replace, capture_fixture
from lazarus_lib.errors import FormatError, IntegrityError, PathError, ResourceLimitError
from lazarus_lib.records import read_rpc_records
from lazarus_lib.verifier import verify_fixture

from . import support
from .fake_rpc import FakeRpc, RpcError, material_dispatch


class CaptureTests(unittest.TestCase):
    def material(self):
        material = support.synthetic_fixture_material()
        material["plan"]["limits"]["max_elapsed_seconds"] = 10
        return material

    def write_plan(self, root: Path, plan):
        path = root / "capture-plan.json"
        dump(path, plan)
        return path

    def test_cli_captures_and_verifies_one_deterministic_fixture(self):
        material = self.material()
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material), reverse_batches=True
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            result = subprocess.run(
                [
                    sys.executable,
                    str(support.SCRIPTS / "lazarus.py"),
                    "capture",
                    "--plan",
                    str(plan),
                    "--rpc-url",
                    server.url + "?apiKey=query-secret",
                    "--out",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = verify_fixture(output)
            self.assertIn(report["fixture_digest"], result.stdout)
            self.assertNotIn("query-secret", b"".join(
                path.read_bytes() for path in output.rglob("*") if path.is_file()
            ).decode("utf-8"))
            self.assertEqual(
                [request["params"] for request in server.requests if request["method"] == "eth_getBlockByNumber"],
                [[material["header"]["number"], False]] * 2,
            )

    def test_repeated_capture_has_identical_bytes_and_digest(self):
        material = self.material()
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            first = root / "first"
            second = root / "second"
            one = capture_fixture(plan, server.url, first)
            two = capture_fixture(plan, server.url, second)
            self.assertEqual(one["fixture_digest"], two["fixture_digest"])
            self.assertEqual(
                {path.relative_to(first): path.read_bytes() for path in first.rglob("*") if path.is_file()},
                {path.relative_to(second): path.read_bytes() for path in second.rglob("*") if path.is_file()},
            )

    def test_runtime_bearer_and_cookie_headers_never_enter_fixture(self):
        material = self.material()
        headers = {
            "Authorization": "Bearer bearer-secret",
            "Cookie": "session=cookie-secret",
        }
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            capture_fixture(plan, server.url, output, headers=headers)
            fixture_bytes = b"".join(
                path.read_bytes() for path in output.rglob("*") if path.is_file()
            )
            self.assertNotIn(b"bearer-secret", fixture_bytes)
            self.assertNotIn(b"cookie-secret", fixture_bytes)
            self.assertEqual(server.headers[0]["Authorization"], headers["Authorization"])
            self.assertEqual(server.headers[0]["Cookie"], headers["Cookie"])

    def test_expected_hash_and_header_equivocation_fail_without_output(self):
        material = self.material()
        bad_plan = copy.deepcopy(material["plan"])
        bad_plan["block"]["hash"] = support.hash32("ff")
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, bad_plan)
            output = root / "fixture"
            with self.assertRaises(IntegrityError):
                capture_fixture(plan, server.url, output)
            self.assertFalse(output.exists())

        calls = {"headers": 0}
        base = material_dispatch(material)

        def equivocate(method, params, server):
            result = base(method, params, server)
            if method == "eth_getBlockByNumber":
                calls["headers"] += 1
                if calls["headers"] == 2:
                    result = copy.deepcopy(result)
                    result["gasUsed"] = "0x1"
            return result

        with tempfile.TemporaryDirectory() as directory, FakeRpc(equivocate) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaises(IntegrityError):
                capture_fixture(plan, server.url, root / "fixture")
            self.assertFalse((root / "fixture").exists())

    def test_moving_tags_are_rejected_before_network_access(self):
        material = self.material()
        material["plan"]["requests"][0]["params"] = [{"block": "latest"}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(FormatError, "moving block tag"):
                capture_fixture(plan, "http://127.0.0.1:1/?token=secret", root / "fixture")
            self.assertFalse((root / "fixture").exists())

        material = support.synthetic_fixture_material()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(FormatError, "max_elapsed_seconds"):
                capture_fixture(plan, "http://127.0.0.1:1", root / "fixture")

    def test_hash_selector_rejection_uses_bracketed_number_fallback(self):
        material = self.material()
        material["plan"]["requests"] = []
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material, reject_hash_selectors=True)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            capture_fixture(plan, server.url, root / "fixture")
            state_requests = [
                item for item in server.requests if item["method"] in {"eth_getProof", "eth_getCode"}
            ]
            self.assertEqual(len(state_requests), 4)
            self.assertTrue(isinstance(state_requests[0]["params"][-1], dict))
            self.assertEqual(state_requests[1]["params"][-1], material["header"]["number"])
            self.assertEqual(
                len([item for item in server.requests if item["method"] == "eth_getBlockByNumber"]),
                2,
            )

    def test_optional_failure_is_sanitised_but_required_failure_aborts(self):
        material = self.material()
        material["plan"]["requests"] = [
            {
                "name": "optional",
                "method": "eth_getTransactionReceipt",
                "params": [],
                "required": False,
                "evidence": "recorded-rpc",
            }
        ]
        base = material_dispatch(material)

        def dispatch(method, params, server):
            if method == "eth_getTransactionReceipt":
                return RpcError(-32042, "provider said bearer-secret", {"url": "query-secret"})
            return base(method, params, server)

        with tempfile.TemporaryDirectory() as directory, FakeRpc(dispatch) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            capture_fixture(plan, server.url, output)
            record = read_rpc_records(output / "rpc.jsonl")[0]
            self.assertEqual(
                record["outcome"]["error"],
                {"code": -32042, "message": "provider request failed"},
            )
            self.assertNotIn("secret", (output / "rpc.jsonl").read_text())

        material["plan"]["requests"][0]["required"] = True
        with tempfile.TemporaryDirectory() as directory, FakeRpc(dispatch) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(CaptureError, "required"):
                capture_fixture(plan, server.url, root / "fixture")
            self.assertFalse((root / "fixture").exists())

    def test_proof_or_code_rejection_happens_before_finalisation(self):
        material = self.material()
        base = material_dispatch(material)

        def dispatch(method, params, server):
            if method == "eth_getCode":
                return "0x6001"
            return base(method, params, server)

        with tempfile.TemporaryDirectory() as directory, FakeRpc(dispatch) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(IntegrityError, "captured code"):
                capture_fixture(plan, server.url, root / "fixture")
            self.assertFalse((root / "fixture").exists())

        def bad_proof(method, params, server):
            result = base(method, params, server)
            if method == "eth_getProof":
                result = copy.deepcopy(result)
                node = result["accountProof"][0]
                result["accountProof"][0] = node[:-1] + ("0" if node[-1] != "0" else "1")
            return result

        with tempfile.TemporaryDirectory() as directory, FakeRpc(bad_proof) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(IntegrityError, "root"):
                capture_fixture(plan, server.url, root / "fixture")
            self.assertFalse((root / "fixture").exists())

    def test_response_byte_and_elapsed_time_limits_leave_no_output(self):
        material = self.material()
        material["plan"]["limits"]["max_component_bytes"] = 64
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaises(ResourceLimitError):
                capture_fixture(plan, server.url, root / "fixture")
            self.assertFalse((root / "fixture").exists())

    def test_oversized_plan_fails_before_client_or_network_creation(self):
        material = self.material()
        material["plan"]["limits"]["max_component_bytes"] = 1

        def forbidden_client(*args, **kwargs):
            raise AssertionError("client must not be created")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(ResourceLimitError, "capture plan"):
                capture_fixture(
                    plan,
                    "http://127.0.0.1:1",
                    root / "fixture",
                    client_factory=forbidden_client,
                )

    def test_elapsed_time_limit_leaves_no_output(self):
        material = self.material()

        class AdvancingClock:
            def __init__(self):
                self.value = 0.0

            def __call__(self):
                self.value += 0.34
                return self.value

        material["plan"]["limits"]["max_elapsed_seconds"] = 1
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(ResourceLimitError, "seconds"):
                capture_fixture(
                    plan,
                    server.url,
                    root / "fixture",
                    clock=AdvancingClock(),
                )
            self.assertFalse((root / "fixture").exists())

    def test_out_of_order_planned_responses_keep_their_exact_results(self):
        material = self.material()
        material["plan"]["requests"] = [
            {"name": "transaction", "method": "eth_getTransactionByHash", "params": [1], "required": True, "evidence": "recorded-rpc"},
            {"name": "receipt", "method": "eth_getTransactionReceipt", "params": [2], "required": True, "evidence": "recorded-rpc"},
        ]
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material), reverse_batches=True
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            capture_fixture(plan, server.url, output)
            records = {item["name"]: item for item in read_rpc_records(output / "rpc.jsonl")}
            self.assertEqual(records["transaction"]["outcome"]["result"]["params"], [1])
            self.assertEqual(records["receipt"]["outcome"]["result"]["params"], [2])

    def test_unknown_and_state_changing_methods_are_rejected_before_network(self):
        for method in ("eth_alpha", "evm_mine", "anvil_setBalance", "debug_setHead"):
            with self.subTest(method=method):
                material = self.material()
                material["plan"]["requests"][0]["method"] = method
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    plan = self.write_plan(root, material["plan"])
                    with self.assertRaisesRegex(FormatError, "read-only"):
                        capture_fixture(plan, "http://127.0.0.1:1", root / "fixture")

    def test_interrupted_finalisation_leaves_no_fixture_or_staging_directory(self):
        material = self.material()

        def interrupt(source, destination):
            raise OSError("simulated interruption")

        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with self.assertRaisesRegex(CaptureError, "finalisation"):
                capture_fixture(plan, server.url, output, finalizer=interrupt)
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".fixture.lazarus-*")), [])

    def test_existing_output_is_never_overwritten(self):
        material = self.material()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            output.mkdir()
            with self.assertRaisesRegex(PathError, "already exists"):
                capture_fixture(plan, "http://127.0.0.1:1", output)

    def test_output_created_during_capture_is_not_replaced(self):
        material = self.material()

        def race(source, destination):
            Path(destination).mkdir()
            _atomic_no_replace(source, destination)

        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with self.assertRaisesRegex(PathError, "appeared"):
                capture_fixture(
                    plan,
                    server.url,
                    output,
                    finalizer=race,
                )
            self.assertTrue(output.is_dir())
            self.assertEqual(list(output.iterdir()), [])
            self.assertEqual(list(root.glob(".fixture.lazarus-*")), [])


if __name__ == "__main__":
    unittest.main()
