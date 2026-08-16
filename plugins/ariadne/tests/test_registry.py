"""The predicate registry, including the state it is in at this point: empty."""

import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import registry  # noqa: E402


class Fake(object):
    TYPE = "https://ariadne.wildcat.finance/fake/v1"
    SUMMARY = "a predicate registered by a test and nowhere else"


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = registry.Registry()

    def test_a_module_registers_and_is_found_by_type(self):
        self.registry.register(Fake)
        self.assertIs(self.registry.get(Fake.TYPE), Fake)
        self.assertTrue(self.registry.knows(Fake.TYPE))
        self.assertEqual(len(self.registry), 1)

    def test_an_unknown_type_is_reported_rather_than_raised(self):
        self.assertIsNone(self.registry.get("https://example.test/unknown/v1"))
        self.assertFalse(self.registry.knows("https://example.test/unknown/v1"))

    def test_registering_the_same_module_twice_is_harmless(self):
        self.registry.register(Fake)
        self.registry.register(Fake)
        self.assertEqual(len(self.registry), 1)

    def test_a_second_module_claiming_the_same_type_is_refused(self):
        class Impostor(object):
            TYPE = Fake.TYPE
            SUMMARY = "a different module under the same type URI"

        self.registry.register(Fake)
        with self.assertRaises(registry.RegistryError) as caught:
            self.registry.register(Impostor)
        self.assertIn("already registered", str(caught.exception))

    def test_a_module_without_a_summary_is_refused(self):
        class Bare(object):
            TYPE = "https://example.test/bare/v1"

        with self.assertRaises(registry.RegistryError) as caught:
            self.registry.register(Bare)
        self.assertIn("SUMMARY", str(caught.exception))

    def test_a_type_that_is_not_a_uri_is_refused(self):
        class Loose(object):
            TYPE = "solidity-release"
            SUMMARY = "a predicate naming itself without a URI"

        with self.assertRaises(registry.RegistryError) as caught:
            self.registry.register(Loose)
        self.assertIn("type URI", str(caught.exception))

    def test_entries_are_sorted_by_type(self):
        class Other(object):
            TYPE = "https://ariadne.wildcat.finance/aardvark/v1"
            SUMMARY = "sorts first"

        self.registry.register(Fake)
        self.registry.register(Other)
        self.assertEqual(
            [type_uri for type_uri, _ in self.registry.entries()],
            [Other.TYPE, Fake.TYPE],
        )


class DefaultRegistryTests(unittest.TestCase):
    def test_the_default_registry_holds_the_predicates_that_ship(self):
        """One so far. Importing the package is what registers it, so this also
        asserts that the side effect happened."""
        from ariadne_lib import predicates  # noqa: F401

        self.assertEqual(
            [type_uri for type_uri, _ in registry.DEFAULT.entries()],
            ["https://ariadne.wildcat.finance/solidity-release/v1"],
        )


if __name__ == "__main__":
    unittest.main()
