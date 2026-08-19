"""Every registered predicate, held to returning rather than raising.

A statement arrives from whoever wrote it. `safejson` bounds its size, depth and
duplicate keys before a gate sees it, but nothing bounds its *shape*: a producer
can put a string where an object belongs at any depth, and a gate that indexes
before it type-checks turns that into an escaping exception.

`verify.report` already catches an exception out of a predicate module and turns
it into a failed check, so an escape is not fatal. It is still a defect: the
single `predicate-check` line replaces every gate that module would have
reported, so a reader loses the detail that tells them what to fix.

This sweep is generic over the registry, so a predicate added later is covered
without editing this file.
"""

import copy
import itertools
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import registry  # noqa: E402
import ariadne_lib.predicates  # noqa: F401,E402  (registers the shipped predicates)

JUNK = (
    None,
    0,
    1,
    -1,
    True,
    False,
    "",
    "a value where an object belongs",
    [],
    {},
    [None],
    [[]],
    [{}],
    {"a": None},
    {"a": {"b": [1, 2]}},
    3.5,
    {"0": "1"},
    [{"start": None}],
)
"""Shapes a careless or hostile producer can put anywhere. `True` and `False` are
in here on purpose: Python makes them integers, so a gate comparing bounds will
happily order them."""


class Stub(object):
    """The three attributes a predicate module reads off a statement.

    A real `Statement` refuses a predicate that is not an object, so the guards
    at the top of each gate are unreachable through it. They still have to hold,
    because a caller can assemble a predicate and check it directly.
    """

    def __init__(self, predicate):
        self.predicate = predicate
        self.subjects = []

    def covers(self, digest):
        return False


def modules():
    found = []
    for type_uri, _ in registry.DEFAULT.entries():
        module = registry.DEFAULT.get(type_uri)
        if callable(getattr(module, "check", None)):
            found.append((type_uri, module))
    return found


def sample(module):
    """A predicate body shaped like the module's own field table.

    Values are deliberately thin. The point is to have every declared key
    present so the sweep can replace one at a time.
    """
    body = {}
    for field in getattr(module, "PREDICATE_FIELDS", ()):
        body[field] = [] if field in ("claims", "commands") else {}
    return body


class RobustnessTests(unittest.TestCase):
    def test_the_registry_holds_something_to_sweep(self):
        self.assertTrue(modules())

    def test_no_check_raises_when_the_whole_predicate_is_junk(self):
        for type_uri, module in modules():
            for value in JUNK:
                with self.subTest(predicate=type_uri, value=repr(value)):
                    for found in module.check(Stub(value)):
                        self.assertIn(found.passed, (True, False))

    def test_no_check_raises_when_one_declared_field_is_junk(self):
        for type_uri, module in modules():
            base = sample(module)
            for field, value in itertools.product(base, JUNK):
                body = copy.deepcopy(base)
                body[field] = value
                with self.subTest(predicate=type_uri, field=field, value=repr(value)):
                    for found in module.check(Stub(body)):
                        self.assertIn(found.passed, (True, False))

    def test_a_junk_predicate_never_passes_a_check(self):
        """Returning rather than raising is not enough. A shape nobody could read
        must not come back clean."""
        for type_uri, module in modules():
            for value in JUNK:
                with self.subTest(predicate=type_uri, value=repr(value)):
                    found = module.check(Stub(value))
                    self.assertTrue(any(not gate.passed for gate in found))


if __name__ == "__main__":
    unittest.main()
