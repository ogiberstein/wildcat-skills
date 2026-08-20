"""The manifest validator accepts the honest manifest and rejects each fault.

The honest Wildcat manifest under `harness/manifests/` must validate, and each
fixture under `fixtures/` must fail with the specific code its name carries.
The codes are an interface other tools cite, so a fixture that failed with the
wrong code would be a silent contract break; the test pins the code, not just
the failure.
"""

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JANUS = ROOT / "scripts" / "janus.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
HONEST = ROOT / "harness" / "manifests" / "wildcat-open-term.json"


def load_janus():
    spec = importlib.util.spec_from_file_location("janus_cli", JANUS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.janus = load_janus()

    def test_the_honest_manifest_validates(self):
        ok, message = self.janus.validate_manifest_file(str(HONEST))
        self.assertTrue(ok, message)

    def test_each_fixture_fails_with_its_named_code(self):
        fixtures = sorted(FIXTURES.glob("j*.json"))
        self.assertGreaterEqual(len(fixtures), 14, "fixtures are missing")
        for path in fixtures:
            expected = path.name.split("_", 1)[0].upper()  # e.g. "J009"
            with self.subTest(fixture=path.name):
                ok, message = self.janus.validate_manifest_file(str(path))
                self.assertFalse(ok, f"{path.name} unexpectedly validated")
                self.assertTrue(
                    message.startswith(expected + ":"),
                    f"{path.name}: expected {expected}, got {message}",
                )

    def test_validate_command_exit_code(self):
        # A valid file exits 0; a batch containing one bad file exits 1.
        self.assertEqual(self.janus.main(["validate", str(HONEST)]), 0)
        bad = str(FIXTURES / "j009_wildcard.json")
        self.assertEqual(self.janus.main(["validate", str(HONEST), bad]), 1)

    def test_wildcard_is_rejected_everywhere_it_could_hide(self):
        # Gate 1: a wildcard in a call target or a value recipient is refused
        # just as it is in a storage slot.
        import json

        honest = json.loads(HONEST.read_text(encoding="utf-8"))
        honest.pop("$schema", None)
        for name, entry in (
            ("permittedCalls", {"target": "any", "kind": "call"}),
            ("permittedValueMovements", {"asset": "USDC", "recipient": "*"}),
        ):
            with self.subTest(field=name):
                probe = json.loads(json.dumps(honest))
                probe["thresholds"][0][name] = [entry]
                with self.assertRaises(self.janus.ManifestError) as caught:
                    self.janus.validate_manifest_obj(probe)
                self.assertEqual(caught.exception.code, "J009")


if __name__ == "__main__":
    unittest.main()
