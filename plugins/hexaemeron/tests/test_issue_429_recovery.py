#!/usr/bin/env python3
"""Permanent composition guards for the issue 429 recovery."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[3]
PRODUCT_HEAD = "f11fe174161f46bf79080422169ad943214e1b4f"
PINNED_BASE = "c4650f02a979e859ce36374779eac9cd70744288"
PRODUCT_SUFFIX = (
    ROOT
    / "audit"
    / "rounds"
    / "fiat-429-audit-record-schema-timestamp-synopsis.md"
)
PRODUCT_SUFFIX_SHA256 = (
    "51891eaf4a387acb79ab65c9508c09cb84828cb40c475a3b363fddcecd74fe8d"
)
ROOT_AUDIT_SHA256 = (
    "c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa"
)
STUDY_SHA256 = (
    "14576e2985024efc8e950b9ad2a22977fb9f2d6e6c64a7460996d63b577056d2"
)
RUNBOOK_SHA256 = (
    "e2a2488af4cab26db47275c8ac0c9dbf9aa2278b9ca91279005168e87f039e75"
)
OVERLAPS = (
    ".agents/plugins/marketplace.json",
    ".claude-plugin/marketplace.json",
    "audit/AUDIT.md",
    "plugins/hexaemeron/.claude-plugin/plugin.json",
    "plugins/hexaemeron/.codex-plugin/plugin.json",
    "plugins/hexaemeron/README.md",
    "plugins/hexaemeron/agents/warden.md",
    "plugins/hexaemeron/skills/fiat/EVOLUTION.md",
    "plugins/hexaemeron/skills/fiat/SKILL.md",
    "plugins/hexaemeron/skills/fiat/references/audit-loop.md",
    "plugins/hexaemeron/skills/fiat/scripts/hexctl.py",
    "plugins/hexaemeron/tests/test_fiat_skill.py",
    "plugins/hexaemeron/tests/test_hexctl.py",
    "tests/promise_machine_coverage.json",
    "tests/test_evolution_contract.py",
    "tests/test_version_propagation.py",
)
COMPOSITION_MANIFEST = (
    ROOT
    / "plugins"
    / "hexaemeron"
    / "docs"
    / "audit-record-schema-timestamp-synopsis-recovery"
    / "composition-manifest.json"
)
RECOVERY_DOCS = COMPOSITION_MANIFEST.parent
TRAILERS = (
    "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>",
    "Wildcat-Origin: shoggoth",
)


def git(*args, text=False):
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    ).stdout


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Issue429RecoveryTests(unittest.TestCase):
    def composition_commit(self):
        matches = []
        for line in git("rev-list", "--parents", "HEAD", text=True).splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[1:] == [PRODUCT_HEAD, PINNED_BASE]:
                matches.append(fields[0])
        self.assertEqual(
            len(matches),
            1,
            "the history must contain one product-first, pinned-base-second join",
        )
        return matches[0]

    def test_composition_has_exact_parent_order_and_signed_header(self):
        commit = self.composition_commit()
        raw = git("cat-file", "commit", commit)
        header = raw.split(b"\n\n", 1)[0]
        self.assertIn(b"gpgsig ", header)
        self.assertEqual(
            git("show", "-s", "--format=%P", commit, text=True).strip(),
            f"{PRODUCT_HEAD} {PINNED_BASE}",
        )

    def test_complete_product_range_remains_reachable_with_provenance(self):
        commits = git(
            "rev-list", f"{PINNED_BASE}..{PRODUCT_HEAD}", text=True
        ).splitlines()
        self.assertEqual(len(commits), 52)
        for commit in commits:
            with self.subTest(commit=commit):
                subprocess.run(
                    ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                    cwd=ROOT,
                    check=True,
                )
                raw = git("cat-file", "commit", commit)
                self.assertIn(b"gpgsig ", raw.split(b"\n\n", 1)[0])
                message = raw.split(b"\n\n", 1)[1].decode("utf-8")
                for trailer in TRAILERS:
                    self.assertEqual(message.splitlines().count(trailer), 1)

    def test_manifest_covers_every_overlap_and_both_retained_behaviours(self):
        manifest = json.loads(COMPOSITION_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "fiat-429-composition/v1")
        self.assertEqual(manifest["product_head"], PRODUCT_HEAD)
        self.assertEqual(manifest["pinned_base"], PINNED_BASE)
        self.assertEqual(manifest["parent_order"], [PRODUCT_HEAD, PINNED_BASE])
        entries = manifest["overlaps"]
        self.assertEqual(tuple(item["path"] for item in entries), OVERLAPS)
        self.assertEqual(len(entries), 16)
        self.assertEqual(sum(bool(item["textual_conflict"]) for item in entries), 15)
        for item in entries:
            with self.subTest(path=item["path"]):
                self.assertTrue(item["current_behaviour"].strip())
                self.assertTrue(item["product_behaviour"].strip())
                self.assertTrue(item["resolution"].strip())

    def test_root_audit_is_the_exact_pinned_base_blob(self):
        current = (ROOT / "audit" / "AUDIT.md").read_bytes()
        self.assertEqual(hashlib.sha256(current).hexdigest(), ROOT_AUDIT_SHA256)
        self.assertEqual(current, git("show", f"{PINNED_BASE}:audit/AUDIT.md"))

    def test_product_suffix_is_exact_and_keeps_its_record_distribution(self):
        data = PRODUCT_SUFFIX.read_bytes()
        self.assertEqual(data.count(b"\n"), 574)
        self.assertEqual(hashlib.sha256(data).hexdigest(), PRODUCT_SUFFIX_SHA256)
        headings = re.findall(
            rb"^## audit-record-schema-timestamp-synopsis, step ([123]), round ",
            data,
            flags=re.MULTILINE,
        )
        self.assertEqual(Counter(headings), Counter({b"1": 12, b"2": 15, b"3": 2}))
        self.assertEqual(data.count(b"Audit schema: fiat-audit-round/v1\n"), 29)

    def test_receipted_study_and_runbook_have_exact_committed_copies(self):
        self.assertEqual(sha256(RECOVERY_DOCS / "study.md"), STUDY_SHA256)
        self.assertEqual(sha256(RECOVERY_DOCS / "runbook.md"), RUNBOOK_SHA256)


if __name__ == "__main__":
    unittest.main()
