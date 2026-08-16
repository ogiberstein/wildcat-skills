"""The block every predicate carries, whatever its artefact.

Two lists. `claims` are the things that were checked, each naming the subject
digest it covers and what happened to it. `commands` are the things that were
run, each declaring whether its output has to match byte for byte on a replay.

A dataset predicate and a contract release predicate fill these in differently
and inherit the same five core gates, which is the whole reason the split
exists.

The vocabularies are closed. A disposition outside this list is a producer
inventing a state the verifier cannot reason about, and `passed` is the only one
that needs no reason attached.
"""

CLAIMS = "claims"
COMMANDS = "commands"

DISPOSITIONS = ("passed", "failed", "skipped", "timed_out", "redacted")
NEEDS_REASON = tuple(d for d in DISPOSITIONS if d != "passed")

DETERMINISM = ("exact", "nondeterministic")

CLAIM_FIELDS = frozenset({"name", "subject", "disposition", "reason", "detail"})
COMMAND_FIELDS = frozenset(
    {"name", "argv", "determinism", "output_digest", "detail"}
)


def block(predicate, key):
    """The named list from a predicate, or None when it is absent or wrong.

    Returning None for both cases is deliberate: the gate that cares about the
    difference reports it, and every other caller wants the same answer, which
    is that there is nothing here to read.
    """
    if not isinstance(predicate, dict):
        return None
    found = predicate.get(key)
    if not isinstance(found, list):
        return None
    return found


def claims(predicate):
    return block(predicate, CLAIMS)


def commands(predicate):
    return block(predicate, COMMANDS)


def label(entry, index, kind):
    """A name for an entry that may not have one, for use in a gate message."""
    if isinstance(entry, dict) and isinstance(entry.get("name"), str):
        return entry["name"]
    return "%s %d" % (kind, index + 1)


def walk(value):
    """Every (key, value) pair anywhere inside a parsed predicate.

    Used by the gates that have to hold wherever in the predicate a producer
    puts something, rather than only at the top level.
    """
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            for pair in walk(child):
                yield pair
    elif isinstance(value, list):
        for child in value:
            for pair in walk(child):
                yield pair


def normalise_key(key):
    """Fold a key for comparison: case, underscores and hyphens dropped."""
    return "".join(c for c in key.lower() if c.isalnum())
