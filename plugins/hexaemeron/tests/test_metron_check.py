"""The Metron budget check reads its three files, and refuses what it cannot read.

The refusals matter more than the happy path here. All three files arrive from outside
the process, and the fault this marketplace keeps producing is a field that satisfies a
presence check while carrying nothing a comparison can use.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "metron" / "scripts" / "metron.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "metron"
BUDGETS = FIXTURES / "metron-budgets.json"

spec = importlib.util.spec_from_file_location("metron_check", SCRIPT)
metron = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metron)


def budget(**overrides):
    """One well-formed budget, with fields replaced or removed by the caller.

    A field set to the sentinel is dropped, which is how the absent-field tests reach
    every required key without writing nine near-identical literals.
    """
    entry = {
        "name": "harvest.usdc.wall_clock",
        "unit": "s",
        "limit": 1200,
        "variance": 0.05,
        "direction": "lower_is_better",
    }
    entry.update(overrides)
    return {key: value for key, value in entry.items() if value is not DROP}


DROP = object()


class TempFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, document):
        """A file holding the JSON encoding of `document`, whatever its type."""
        path = Path(self.tmp.name) / name
        path.write_text(json.dumps(document), encoding="utf-8")
        return str(path)

    def write_raw(self, name, text):
        """A file holding exactly `text`, for the cases that are not JSON at all."""
        path = Path(self.tmp.name) / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def budgets_file(self, *entries):
        return self.write("budgets.json", {"budgets": list(entries)})

    def refusal(self, path):
        with self.assertRaises(metron.BudgetError) as caught:
            metron.load_budgets(path)
        return str(caught.exception)


class ShippedFixtureTests(unittest.TestCase):
    def test_the_committed_budget_file_loads(self):
        found = metron.load_budgets(str(BUDGETS))
        self.assertEqual(len(found), 3)
        self.assertEqual(found[0]["name"], "harvest.usdc.wall_clock")

    def test_the_committed_fixture_covers_both_directions(self):
        """A fixture with only lower-is-better budgets would never exercise the other
        branch of the comparison."""
        directions = {entry["direction"] for entry in metron.load_budgets(str(BUDGETS))}
        self.assertEqual(directions, set(metron.DIRECTIONS))

    def test_file_order_is_kept(self):
        """The file is reviewed by a person, so the report should read the way it does."""
        names = [entry["name"] for entry in metron.load_budgets(str(BUDGETS))]
        self.assertEqual(names, sorted(names, key=names.index))
        self.assertEqual(names[0], "harvest.usdc.wall_clock")


class BudgetFileTests(TempFiles):
    def test_a_well_formed_budget_loads(self):
        found = metron.load_budgets(self.budgets_file(budget()))
        self.assertEqual(found[0]["limit"], 1200)

    def test_every_required_field_is_required(self):
        for field in metron.REQUIRED:
            with self.subTest(missing=field):
                path = self.budgets_file(budget(**{field: DROP}))
                self.assertIn(field, self.refusal(path))

    def test_a_name_that_names_nothing_is_refused(self):
        for value in ("", "   ", 7, None, True):
            with self.subTest(name=value):
                self.assertIn("name", self.refusal(self.budgets_file(budget(name=value))))

    def test_a_unit_that_states_nothing_is_refused(self):
        for value in ("", "  ", 3, None):
            with self.subTest(unit=value):
                self.assertIn("unit", self.refusal(self.budgets_file(budget(unit=value))))

    def test_a_limit_that_is_not_a_number_is_refused(self):
        for value in ("1200", None, [1200], {}):
            with self.subTest(limit=value):
                self.assertIn("limit", self.refusal(self.budgets_file(budget(limit=value))))

    def test_a_boolean_limit_is_not_a_number(self):
        """Python makes True an integer, so a membership or isinstance check would have
        compared a limit of true against a measurement."""
        self.assertIn("limit", self.refusal(self.budgets_file(budget(limit=True))))

    def test_a_negative_limit_is_refused(self):
        self.assertIn("negative", self.refusal(self.budgets_file(budget(limit=-1))))

    def test_a_zero_limit_is_allowed(self):
        """Zero is a real ceiling for a count: no round trips, no layout shift."""
        found = metron.load_budgets(self.budgets_file(budget(limit=0)))
        self.assertEqual(found[0]["limit"], 0)

    def test_a_variance_outside_its_range_is_refused(self):
        for value in (-0.1, 1.0, 1.5, 5):
            with self.subTest(variance=value):
                self.assertIn(
                    "variance", self.refusal(self.budgets_file(budget(variance=value)))
                )

    def test_a_variance_of_zero_is_allowed(self):
        """A budget that tolerates no drift at all is a choice, not an error."""
        found = metron.load_budgets(self.budgets_file(budget(variance=0)))
        self.assertEqual(found[0]["variance"], 0)

    def test_a_boolean_variance_is_refused(self):
        self.assertIn("variance", self.refusal(self.budgets_file(budget(variance=True))))

    def test_a_direction_outside_the_two_is_refused(self):
        for value in ("faster", "", None, "LOWER_IS_BETTER", True):
            with self.subTest(direction=value):
                self.assertIn(
                    "direction", self.refusal(self.budgets_file(budget(direction=value)))
                )

    def test_a_duplicate_budget_name_is_refused(self):
        path = self.budgets_file(budget(), budget())
        self.assertIn("declared twice", self.refusal(path))

    def test_an_unknown_field_is_refused(self):
        path = self.budgets_file(budget(threshold=5))
        self.assertIn("threshold", self.refusal(path))

    def test_a_top_level_that_is_not_an_object_is_refused(self):
        for document in ([], "budgets", 7, None):
            with self.subTest(document=document):
                path = self.write("odd.json", document)
                self.assertIn("object", self.refusal(path))

    def test_a_budgets_key_that_is_not_a_list_is_refused(self):
        for value in ({}, "one", 3, None):
            with self.subTest(budgets=value):
                path = self.write("odd.json", {"budgets": value})
                self.assertIn("budgets array", self.refusal(path))

    def test_an_empty_budget_list_is_refused(self):
        """A file declaring nothing is not a budget file, and a check over it would pass
        every run without looking at one."""
        self.assertIn("no budgets", self.refusal(self.write("empty.json", {"budgets": []})))

    def test_an_entry_that_is_not_an_object_is_refused(self):
        for value in ("harvest", 7, [], None):
            with self.subTest(entry=value):
                path = self.write("odd.json", {"budgets": [value]})
                self.assertIn("object", self.refusal(path))

    def test_a_file_that_is_not_json_is_refused(self):
        for text in ("not json", "", "{", "[1,"):
            with self.subTest(text=text):
                self.assertIn("readable JSON", self.refusal(self.write_raw("bad.json", text)))

    def test_the_non_standard_json_constants_are_refused(self):
        """json.loads accepts NaN, Infinity and -Infinity by default, which are a Python
        extension rather than JSON. Every comparison against nan is False, including !=, so
        a nan measurement does not fail a threshold: it falls through whichever branch is
        tested last. An infinite limit means nothing ever exceeds it."""
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token):
                text = ('{"budgets":[{"name":"a","unit":"s","limit":%s,'
                        '"variance":0.05,"direction":"lower_is_better"}]}' % token)
                message = self.refusal(self.write_raw("odd.json", text))
                self.assertIn("not permitted", message)
                self.assertIn(token, message)

    def test_a_non_finite_measurement_is_refused(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token):
                path = self.write_raw("run.json", '{"measurements":{"a":%s}}' % token)
                with self.assertRaises(metron.BudgetError) as caught:
                    metron.load_measurements(path, "run")
                self.assertIn("not permitted", str(caught.exception))

    def test_number_accepts_only_finite_reals(self):
        for value in (0, 1, -1, 3.5, -2.25):
            with self.subTest(value=value, expect=True):
                self.assertTrue(metron.number(value))
        for value in (True, False, "1", None, [], {},
                      float("inf"), float("-inf"), float("nan")):
            with self.subTest(value=value, expect=False):
                self.assertFalse(metron.number(value))

    def test_a_json_string_is_not_an_object(self):
        """`"budgets"` is valid JSON and is not a budget file. The refusal has to say which
        of the two problems it met."""
        self.assertIn("object", self.refusal(self.write("odd.json", "budgets")))

    def test_a_file_that_is_not_there_is_refused(self):
        self.assertIn("cannot read", self.refusal(str(Path(self.tmp.name) / "absent.json")))

    def test_nothing_raises_a_bare_exception(self):
        """Every malformed shape gets a BudgetError naming the fault, because a traceback
        out of a CI check tells the reader nothing they can act on."""
        for document in (None, 7, "x", [], {}, {"budgets": None}, {"budgets": [None]},
                         {"budgets": [{}]}, {"budgets": [{"name": None}]}):
            path = self.write("odd.json", document)
            with self.subTest(document=document):
                with self.assertRaises(metron.BudgetError):
                    metron.load_budgets(path)


class MeasurementFileTests(TempFiles):
    def test_a_measurements_object_loads(self):
        path = self.write("run.json", {"measurements": {"a": 1, "b": 2.5}})
        self.assertEqual(metron.load_measurements(path, "run"), {"a": 1, "b": 2.5})

    def test_a_bare_mapping_loads_too(self):
        """Whatever produced the run may not wrap it. Both shapes read the same."""
        path = self.write("run.json", {"a": 1})
        self.assertEqual(metron.load_measurements(path, "run"), {"a": 1})

    def test_a_value_that_is_not_a_number_is_refused(self):
        for value in ("120", None, [1], {}, True):
            with self.subTest(value=value):
                path = self.write("run.json", {"measurements": {"a": value}})
                with self.assertRaises(metron.BudgetError) as caught:
                    metron.load_measurements(path, "run")
                self.assertIn("a", str(caught.exception))

    def test_a_document_carrying_both_shapes_is_refused(self):
        """Taking the wrapped block drops the top-level values in silence, and a dropped
        measurement is the difference between an `undeclared` verdict and no verdict."""
        path = self.write("run.json", {"measurements": {"a": 1}, "b": 2, "c": 3.5})
        with self.assertRaises(metron.BudgetError) as caught:
            metron.load_measurements(path, "run")
        message = str(caught.exception)
        self.assertIn("b", message)
        self.assertIn("c", message)

    def test_metadata_beside_the_block_is_allowed(self):
        """A producer recording a note or a timestamp alongside its numbers is doing the
        right thing, and only a stray number is ambiguous."""
        for extra in ({"note": "why"}, {"recorded_at": "2026-08-19"},
                      {"ok": True}, {"tags": ["nightly"]}):
            with self.subTest(extra=extra):
                document = {"measurements": {"a": 1}}
                document.update(extra)
                path = self.write("run.json", document)
                self.assertEqual(metron.load_measurements(path, "run"), {"a": 1})

    def test_a_negative_measurement_is_allowed(self):
        """A delta or a temperature can be negative. The comparison decides what it means,
        not the loader."""
        path = self.write("run.json", {"measurements": {"a": -3}})
        self.assertEqual(metron.load_measurements(path, "run"), {"a": -3})

    def test_a_top_level_that_is_not_an_object_is_refused(self):
        for document in ([], "run", 7):
            with self.subTest(document=document):
                path = self.write("run.json", document)
                with self.assertRaises(metron.BudgetError):
                    metron.load_measurements(path, "run")

    def test_the_label_appears_in_the_refusal(self):
        """`run` and `baseline` read the same file shape, so the message has to say which
        one was being read."""
        path = self.write("odd.json", [])
        for what in ("run", "baseline"):
            with self.subTest(what=what):
                with self.assertRaises(metron.BudgetError) as caught:
                    metron.load_measurements(path, what)
                self.assertIn(what, str(caught.exception))


class FileHandlingTests(TempFiles):
    def test_a_directory_is_refused_rather_than_raising(self):
        directory = Path(self.tmp.name) / "adir"
        directory.mkdir()
        self.assertIn("cannot read", self.refusal(str(directory)))

    def test_a_file_past_the_cap_is_refused(self):
        path = Path(self.tmp.name) / "big.json"
        path.write_text("{" + " " * (metron.MAX_BYTES + 1) + "}", encoding="utf-8")
        self.assertIn("larger than", self.refusal(str(path)))

    def test_a_file_at_the_cap_is_read(self):
        """The cap keeps a mistaken path from reading something enormous. It should not
        refuse a file that merely approaches it."""
        entry = {"name": "a", "unit": "s", "limit": 1, "variance": 0.05,
                 "direction": "lower_is_better"}
        document = json.dumps({"budgets": [entry]})
        padding = " " * (metron.MAX_BYTES - len(document) - 1)
        path = Path(self.tmp.name) / "wide.json"
        path.write_text(document[:-1] + padding + "}", encoding="utf-8")
        self.assertLessEqual(path.stat().st_size, metron.MAX_BYTES)
        self.assertEqual(len(metron.load_budgets(str(path))), 1)


class CommandLineTests(TempFiles):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def test_a_readable_pair_exits_zero(self):
        run = self.write("run.json", {"measurements": {"harvest.usdc.wall_clock": 1100}})
        proc = self.run_cli("check", "--budgets", str(BUDGETS), "--run", run)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_a_malformed_budget_file_exits_two(self):
        bad = self.write_raw("bad.json", "not json")
        run = self.write("run.json", {"measurements": {"a": 1}})
        proc = self.run_cli("check", "--budgets", bad, "--run", run)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("metron: error:", proc.stderr)

    def test_no_subcommand_exits_two(self):
        self.assertEqual(self.run_cli().returncode, 2)

    def test_both_subcommands_are_offered(self):
        parser = metron.build_parser()
        for action in parser._subparsers._group_actions:  # noqa: SLF001
            self.assertEqual(sorted(action.choices), ["check", "record"])
            return
        raise AssertionError("the parser offers no subcommands")


if __name__ == "__main__":
    unittest.main()
