"""The reporter renders a findings file to human Markdown and SARIF 2.1.0.

The sample findings render to a Markdown report naming each gate and to a
SARIF log with one result per finding linked to its gate rule. An empty
findings set renders a report that states the manifest and the sequence count
rather than claiming safety.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JANUS = ROOT / "scripts" / "janus.py"
SAMPLE = ROOT / "examples" / "findings.sample.json"


def load_janus():
    spec = importlib.util.spec_from_file_location("janus_cli", JANUS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReporterTests(unittest.TestCase):
    def setUp(self):
        self.janus = load_janus()
        self.data = self.janus.load_findings(str(SAMPLE))

    def test_the_sample_findings_load(self):
        self.assertEqual(self.data["host"], "wildcat-v2.5")
        self.assertEqual(len(self.data["findings"]), 5)

    def test_markdown_names_each_gate_and_hook(self):
        md = self.janus.render_markdown(self.data)
        self.assertIn("Janus conformance report", md)
        self.assertIn("wildcat-open-term", md)
        for f in self.data["findings"]:
            self.assertIn(f["hook"], md)
            self.assertIn(str(f["gate"]), md)

    def test_sarif_is_well_formed_2_1_0(self):
        sarif = self.janus.render_sarif(self.data)
        self.assertEqual(sarif["version"], "2.1.0")
        run = sarif["runs"][0]
        self.assertEqual(run["tool"]["driver"]["name"], "Janus")
        # One result per finding, each linked to its gate rule.
        self.assertEqual(len(run["results"]), len(self.data["findings"]))
        rule_ids = {rule["id"] for rule in run["tool"]["driver"]["rules"]}
        for result, finding in zip(run["results"], self.data["findings"]):
            self.assertEqual(result["ruleId"], f"janus-gate-{finding['gate']}")
            self.assertIn(result["ruleId"], rule_ids)
            self.assertEqual(result["level"], "error")

    def test_sarif_round_trips_as_json(self):
        sarif = self.janus.render_sarif(self.data)
        self.assertEqual(json.loads(json.dumps(sarif))["version"], "2.1.0")

    def test_empty_findings_report_states_context_not_safety(self):
        clean = {"host": "wildcat-v2.5", "manifest": "wildcat-open-term", "sequences": 12, "findings": []}
        md = self.janus.render_markdown(clean)
        self.assertIn("12", md)
        self.assertIn("wildcat-open-term", md)
        self.assertIn("not a proof of safety", md)
        sarif = self.janus.render_sarif(clean)
        self.assertEqual(sarif["runs"][0]["results"], [])

    def test_report_command_writes_both_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            md = str(Path(d) / "report.md")
            sarif = str(Path(d) / "report.sarif")
            rc = self.janus.main(["report", "--findings", str(SAMPLE), "--md", md, "--sarif", sarif])
            self.assertEqual(rc, 0)
            self.assertIn("Janus conformance report", Path(md).read_text(encoding="utf-8"))
            self.assertEqual(json.loads(Path(sarif).read_text(encoding="utf-8"))["version"], "2.1.0")


if __name__ == "__main__":
    unittest.main()
