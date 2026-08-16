"""Shared paths and fixture loading for Tabularium tests."""

import copy
import json
from pathlib import Path
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def minimal_snapshot():
    value = json.loads((FIXTURES / "minimal-snapshot.json").read_text())
    return copy.deepcopy(value)
