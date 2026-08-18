# The Horos example

`fixture/` is a miniature repository holding one file per classifier rule
class: a binary asset, a lockfile, a marker-generated file, a generated
directory, a vendored directory, a sourcemap, a single-line blob, a minified
bundle, and a directory vendored through `.gitattributes`. One hand-written
file, `src/app.py`, stays readable. Its committed boundary lives at
`fixture/.horos/boundary.json`.

Run everything from the repository root.

## Reproduce the boundary

```bash
python3 plugins/horos/skills/horos/scripts/horos.py scan plugins/horos/examples/fixture --json
```

prints the boundary document byte for byte as committed, and

```bash
python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/fixture
```

exits 0 with `boundary matches the tree`.

## The mutation that makes check fail

Delete the fixture's lockfile and the boundary no longer matches:

```bash
rm plugins/horos/examples/fixture/yarn.lock
python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/fixture
```

exits 1 and names the drift: `drift: yarn.lock: in the boundary but no longer
evidenced by the tree`. Restore it with `git checkout` afterwards. The same
failure fires in the other direction when a new sink appears that the
committed boundary lacks, which is the control against a boundary edited to
hide something.

## The skeleton map

```bash
python3 plugins/horos/skills/horos/scripts/horos.py map plugins/horos/examples/fixture/src/app.py
```

prints the module's skeleton instead of the module.
