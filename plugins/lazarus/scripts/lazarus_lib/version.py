"""The version Lazarus stamps into a fixture manifest as `tool_version`.

This is the writer's version, not the skill's. It appears inside every manifest
this build writes, and the checked-in Goldfinch fixture's demonstration rebuilds
its manifest and compares the bytes, so moving this number rewrites the
provenance of every fixture already captured and breaks that comparison.

So it moves when the writer or the format moves, and not when the skill's
frontier advances. The skill's evolution label lives in
`skills/lazarus/EVOLUTION.md` and the host manifests follow it; the two axes are
kept apart deliberately, and `tests/test_scaffold.py` holds them to that.
"""

__version__ = "0.1.0"
