"""The Ephoros signal lint catches its three rules and leaves the rest alone.

The neighbours matter as much as the specimens. This marketplace writes a
hundred f-string `print` calls, which are command-line output rather than
telemetry, and takes means of sentence lengths and layout positions, which are
not durations.
"""

import importlib.util
import io
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "ephoros" / "scripts" / "ephoros.py"
ALERT_FIXTURES = ROOT / "tests" / "fixtures" / "ephoros" / "alert-rules"

spec = importlib.util.spec_from_file_location("ephoros_lint", SCRIPT)
ephoros = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ephoros)


def codes(source):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "sample.py"
        path.write_text(source, encoding="utf-8")
        return sorted(f.code for f in ephoros.check(path))


def yaml_findings(source, name="sample.yaml"):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / name
        path.write_text(source, encoding="utf-8")
        return ephoros.check(path)


class LogMessages(unittest.TestCase):
    def test_it_flags_an_f_string_message(self):
        self.assertIn("E001", codes(
            "import logging\nn = 3\nlogging.info(f'harvested {n} blocks')\n"))

    def test_it_flags_percent_formatting(self):
        self.assertIn("E001", codes("log = get()\nlog.warning('failed %s' % name)\n"))

    def test_it_flags_dot_format(self):
        self.assertIn("E001", codes("logger = get()\nlogger.error('at {}'.format(x))\n"))

    def test_it_allows_a_stable_name_with_fields(self):
        self.assertEqual([], codes(
            "logger = get()\nlogger.info('harvest_done', extra={'blocks': n})\n"))

    def test_it_ignores_print_which_is_not_telemetry(self):
        self.assertEqual([], codes("n = 3\nprint(f'harvested {n} blocks')\n"))

    def test_it_ignores_an_unrelated_object_with_an_info_method(self):
        self.assertEqual([], codes(
            "class Report:\n    def info(self, text):\n        return text\n\n"
            "Report().info(f'value {x}')\n"))


class MetricLabels(unittest.TestCase):
    def test_it_flags_an_address_label(self):
        self.assertIn("E002", codes(
            "h = Histogram('d', labels={'address': a, 'venue': v})\n"))

    def test_it_flags_a_hash_label_in_a_list(self):
        self.assertIn("E002", codes("c = Counter('c', labelnames=['tx_hash', 'chain'])\n"))

    def test_it_flags_a_request_id_tag(self):
        self.assertIn("E002", codes("m = metric('m', tags=['request_id'])\n"))

    def test_it_allows_bounded_labels(self):
        self.assertEqual([], codes(
            "h = Histogram('d', labelnames=['route', 'status_class', 'venue'])\n"))


class Durations(unittest.TestCase):
    def test_it_flags_a_mean_duration(self):
        self.assertIn("E003", codes("import statistics\nmean_latency = statistics.mean(samples)\n"))

    def test_it_flags_the_sum_over_len_idiom_on_durations(self):
        self.assertIn("E003", codes("avg = sum(durations) / len(durations)\n"))

    def test_it_allows_a_mean_of_something_that_is_not_a_duration(self):
        self.assertEqual([], codes("mean = sum(lengths) / len(lengths)\n"))

    def test_it_allows_a_mean_of_layout_positions(self):
        self.assertEqual([], codes("order = sum(positions) / len(positions)\n"))


class Suppression(unittest.TestCase):
    def test_a_stated_reason_suppresses(self):
        self.assertEqual([], codes(
            "log = get()\nlog.info(f'x {y}')  # ephoros: allow one-off migration script\n"))

    def test_a_bare_pragma_does_not_suppress(self):
        self.assertIn("E001", codes("log = get()\nlog.info(f'x {y}')  # ephoros: allow\n"))


class AlertRules(unittest.TestCase):
    def test_a_missing_annotation_reports_e004(self):
        findings = ephoros.check(ALERT_FIXTURES / "missing.yaml")
        self.assertEqual(["E004"], [finding.code for finding in findings])

    def test_a_complete_alert_is_clean(self):
        self.assertEqual([], ephoros.check(ALERT_FIXTURES / "complete.yaml"))

    def test_e004_does_not_resolve_the_runbook_target(self):
        self.assertEqual([], ephoros.check(ALERT_FIXTURES / "dangling.yaml"))

    def test_an_annotated_neighbour_cannot_satisfy_the_missing_alert(self):
        findings = ephoros.check(ALERT_FIXTURES / "multi-alert.yaml")
        self.assertEqual(["E004"], [finding.code for finding in findings])
        self.assertEqual(7, findings[0].line)

    def test_a_top_level_pointer_does_not_satisfy_an_alert(self):
        source = "runbook: runbooks/top.md\n- alert: NeedsOwnPointer\n"
        self.assertEqual(["E004"], [f.code for f in yaml_findings(source)])

    def test_a_deeper_runbook_key_does_not_satisfy_annotations(self):
        source = ("- alert: NeedsDirectAnnotation\n"
                  "  annotations:\n"
                  "    links:\n"
                  "      runbook: runbooks/deep.md\n")
        self.assertEqual(["E004"], [f.code for f in yaml_findings(source)])

    def test_comments_do_not_create_or_satisfy_alerts(self):
        source = ("# - alert: CommentOnly\n"
                  "- alert: RealAlert\n"
                  "  annotations:\n"
                  "    # runbook: runbooks/comment.md\n")
        self.assertEqual(["E004"], [f.code for f in yaml_findings(source)])

    def test_block_scalars_do_not_create_or_satisfy_alerts(self):
        source = ("- alert: ScalarExample\n"
                  "  description: |\n"
                  "    annotations:\n"
                  "      runbook: runbooks/example.md\n"
                  "    - alert: NotARealNeighbour\n")
        self.assertEqual(["E004"], [f.code for f in yaml_findings(source)])

    def test_unsupported_mapping_and_flow_shapes_are_ignored(self):
        self.assertEqual([], ephoros.check(ALERT_FIXTURES / "false-positives.yaml"))

    def test_a_reasoned_suppression_covers_e004(self):
        self.assertEqual([], ephoros.check(ALERT_FIXTURES / "suppressed.yaml"))

    def test_pragma_shaped_scalar_text_does_not_suppress_e004(self):
        specimens = (
            'note: "# ephoros: allow quoted example"\n- alert: StillMissing\n',
            "note: |\n  # ephoros: allow block example\n- alert: StillMissing\n",
        )
        for source in specimens:
            with self.subTest(source=source):
                self.assertEqual(["E004"], [f.code for f in yaml_findings(source)])

    def test_an_unseparated_plain_scalar_hash_is_not_a_suppression_comment(self):
        source = ("- note: literal# ephoros: allow not a comment\n"
                  "- alert: StillMissing\n")
        self.assertEqual(["E004"], [finding.code for finding in yaml_findings(source)])

    def test_a_dedented_comment_after_a_block_scalar_can_suppress_e004(self):
        source = ("note: |\n"
                  "  scalar body\n"
                  "# ephoros: allow generated annotation arrives downstream\n"
                  "- alert: SuppressedMissingAnnotation\n")
        self.assertEqual([], yaml_findings(source))

    def test_a_bare_suppression_does_not_cover_e004(self):
        source = "# ephoros: allow\n- alert: StillMissing\n"
        self.assertEqual(["E004"], [f.code for f in yaml_findings(source)])

    def test_an_oversized_yaml_file_fails_visibly(self):
        source = "#" * (ephoros.MAX_YAML_BYTES + 1)
        self.assertEqual(["E000"], [f.code for f in yaml_findings(source)])

    def test_yaml_read_requests_only_the_cap_plus_one_byte(self):
        class RecordingReader(io.BytesIO):
            requested = None

            def read(self, size=-1):
                self.requested = size
                return super().read(size)

        reader = RecordingReader(b"#" * (ephoros.MAX_YAML_BYTES + 1))
        with mock.patch.object(Path, "open", return_value=reader), \
                mock.patch.object(Path, "read_bytes", side_effect=AssertionError):
            findings = ephoros.check(Path("bounded.yaml"))
        self.assertEqual(["E000"], [finding.code for finding in findings])
        self.assertEqual(ephoros.MAX_YAML_BYTES + 1, reader.requested)

    def test_bare_sequence_block_scalars_do_not_create_alerts(self):
        for marker in ("|", ">"):
            with self.subTest(marker=marker):
                source = f"examples:\n  - {marker}\n    - alert: ExampleOnly\n"
                self.assertEqual([], yaml_findings(source))

    def test_yaml_keys_are_case_sensitive(self):
        self.assertEqual([], yaml_findings("- Alert: UnsupportedCase\n"))
        source = ("- alert: MissingLowercaseKeys\n"
                  "  Annotations:\n"
                  "    Runbook: runbooks/wrong-case.md\n")
        self.assertEqual(["E004"], [finding.code for finding in yaml_findings(source)])

    def test_an_unseparated_hash_in_a_runbook_path_satisfies_presence(self):
        source = ("- alert: HashInPlainScalar\n"
                  "  annotations:\n"
                  "    runbook: runbooks/missing#book.md\n")
        self.assertEqual([], yaml_findings(source))

    def test_multiline_quoted_alert_text_does_not_fire_e004(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                source = f"notes: {quote}\n  - alert: QuotedExample\n  {quote}\n"
                self.assertEqual([], yaml_findings(source))

    def test_multiline_quoted_runbook_text_does_not_satisfy_e004(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                source = ("- alert: NeedsRealRunbook\n"
                          "  annotations:\n"
                          f"    note: {quote}\n"
                          "      runbook: runbooks/quoted.md\n"
                          f"      {quote}\n")
                self.assertEqual(["E004"], [finding.code for finding in yaml_findings(source)])

    def test_multiline_quoted_pragma_text_does_not_suppress_e004(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                source = (f"note: {quote}\n"
                          f"  # ephoros: allow quoted example {quote}\n"
                          "- alert: StillMissing\n")
                self.assertEqual(["E004"], [finding.code for finding in yaml_findings(source)])

    def test_quotes_inside_plain_scalars_do_not_hide_alerts(self):
        for quote, value in (("'", "O'Brien"), ('"', 'six" pipe')):
            with self.subTest(quote=quote):
                source = f"note: {value}\n- alert: StillMissing\n"
                self.assertEqual(
                    ["E004"], [finding.code for finding in yaml_findings(source)])

    def test_unseparated_quote_starts_do_not_hide_alerts(self):
        for shape in ("- note: plain:{quote}text", "  -{quote}text"):
            for quote in ("'", '"'):
                with self.subTest(shape=shape, quote=quote):
                    source = f"{shape.format(quote=quote)}\n- alert: StillMissing\n"
                    self.assertEqual(
                        ["E004"], [finding.code for finding in yaml_findings(source)])

    def test_plain_scalar_continuation_quotes_do_not_hide_alerts(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                source = ("- note: first\n"
                          f"    {quote}continued\n"
                          "- alert: StillMissing\n")
                self.assertEqual(
                    ["E004"], [finding.code for finding in yaml_findings(source)])

    def test_a_folded_plain_runbook_cannot_use_a_first_line_decoy(self):
        source = ("- alert: FoldedPointer\n"
                  "  annotations:\n"
                  "    runbook: runbooks/present.md\n"
                  "      extra\n")
        self.assertEqual(["E004"], [finding.code for finding in yaml_findings(source)])

    def test_single_line_and_valid_folded_plain_runbooks_satisfy_e004(self):
        single = ("- alert: SingleLine\n"
                  "  annotations:\n"
                  "    runbook: runbooks/present.md\n")
        folded = ("- alert: FoldedPath\n"
                  "  annotations:\n"
                  "    runbook: runbooks/present\n"
                  "      target.md\n")
        self.assertEqual([], yaml_findings(single))
        self.assertEqual([], yaml_findings(folded))

    def test_a_blank_plain_fold_cannot_collapse_to_a_valid_pointer(self):
        source = ("- alert: BlankFold\n"
                  "  annotations:\n"
                  "    runbook: runbooks/present\n"
                  "\n"
                  "      target.md\n")
        self.assertEqual(["E004"], [finding.code for finding in yaml_findings(source)])


class OverTheMarketplace(unittest.TestCase):
    def test_suffix_matching_directories_are_not_walked_as_files(self):
        with tempfile.TemporaryDirectory() as base:
            for name in ("generated.py", "generated.yaml", "generated.yml"):
                (Path(base) / name).mkdir()
            self.assertEqual([], ephoros.walk([base]))

    def test_the_shipped_tree_is_clean(self):
        findings = []
        for path in ephoros.walk([str(ROOT.parent)]):
            findings.extend(ephoros.check(path))
        self.assertEqual([], [str(f) for f in findings])


if __name__ == "__main__":
    unittest.main()
