"""The committed reading boundary must describe the tracked tree it ships with.

Criterion 6 of `plugins/horos/docs/scoped-entry/study.md`. The audit record
already carries this failure once: Marking run, step 4, round 1 refreshed the
boundary by hand after `check` flagged the marking evidence copies as new
sinks, and no guard was written. It recurred. This fixture is the guard, and it
is an expected failure until the step that fixes the drift lands.
"""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "horos" / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

import horos  # noqa: E402


class BoundaryCurrencyTests(unittest.TestCase):
    @unittest.expectedFailure
    def test_the_committed_boundary_matches_a_fresh_scan(self):
        committed = horos.load_boundary(str(ROOT))
        fresh = horos.boundary_document(
            horos.scan_tree(
                str(ROOT),
                include_untracked=committed.get("universe") == "tracked+untracked",
            )
        )
        drift = horos.diff_documents(committed, fresh)
        self.assertEqual(
            [path for path, _ in drift],
            [],
            "regenerate with: python3 plugins/horos/skills/horos/scripts/horos.py "
            "scan . --write",
        )


if __name__ == "__main__":
    unittest.main()
