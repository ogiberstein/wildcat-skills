"""Shared paths for the berean test suite."""

from pathlib import Path
import sys

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"
SCHEMAS = PLUGIN_ROOT / "schemas"
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
