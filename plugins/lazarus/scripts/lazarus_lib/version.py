"""The version Lazarus stamps into a fixture manifest as `tool_version`.

This is the writer's version, not the skill's. It appears inside every manifest
this build writes. Historical fixtures retain the version that wrote them;
deterministic rebuild checks therefore select the writer version for the
fixture format they are rebuilding instead of relabelling old captures.

So it moves when the writer or the format moves, and not when the skill's
frontier advances. The skill's evolution label lives in
`skills/lazarus/EVOLUTION.md` and the host manifests follow it; the two axes are
kept apart deliberately, and `tests/test_scaffold.py` holds them to that.
"""

__version__ = "0.2.0"

# Manifest v1 has no receipt witness or receipt-trie relation. Rebuilding that
# historical format must preserve the writer identity its released bytes carry;
# manifest v2 uses the current writer above.
MANIFEST_V1_WRITER_VERSION = "0.1.0"
