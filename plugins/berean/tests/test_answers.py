"""Answer records: the specification's first five gates, mechanically."""

import json
import os
import tempfile
import unittest

from tests.support import SCRIPTS, SCHEMAS  # noqa: F401

from berean_lib import answers, citations, corpus, digests, reads
from tests.test_corpus import make_tree, failures
from tests.test_reads import record, write_reads

DOC = "# Terms\n\nThe pause flag halts new entries. Version 3 keeps it set.\n".encode("utf-8")
CHAIN_ID = 1
BLOCK = 13097494


def span(data, needle):
    start = data.index(needle.encode("utf-8"))
    return start, start + len(needle.encode("utf-8"))


class AnswerFixture(unittest.TestCase):
    def setUp(self):
        self.holder = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.holder.name, "docs")
        make_tree(self.root, {"terms.md": DOC})
        self.manifest = corpus.build(self.root, "v1")
        self.read_record = record("eth_getStorageAt", ["0x8bbd", "0x0", "0xc7da16"])
        self.reads_path = os.path.join(self.holder.name, "reads.jsonl")
        write_reads(self.reads_path, [self.read_record])
        self.records = reads.load(self.reads_path)

    def tearDown(self):
        self.holder.cleanup()

    def citation(self, needle, identifier="c1"):
        start, end = span(DOC, needle)
        return {
            "id": identifier,
            "format": citations.FORMAT,
            "doc": "terms.md",
            "byte_start": start,
            "byte_end": end,
            "sha256": digests.of_bytes(DOC[start:end]),
            "display_text": needle,
        }

    def read(self, identifier="r1"):
        return {
            "id": identifier,
            "chain_id": CHAIN_ID,
            "block_number": BLOCK,
            "request_key": self.read_record["request_key"],
        }

    def answer(self, **overrides):
        base = {
            "format": answers.FORMAT,
            "question": "Is the pause flag set?",
            "kind": "answer",
            "refusal": None,
            "sentences": [
                {
                    "text": "The documentation says the pause flag halts new entries.",
                    "source_class": "document",
                    "evidence": ["c1"],
                },
                {
                    "text": "Slot zero reads one at the declared block.",
                    "source_class": "chain_read",
                    "evidence": ["r1"],
                },
            ],
            "citations": [self.citation("The pause flag halts new entries.")],
            "reads": [self.read()],
            "discrepancies": [],
        }
        base.update(overrides)
        return base

    def check(self, answer):
        return answers.check(
            answer, self.manifest, self.root, self.records, CHAIN_ID, BLOCK
        )


class GateOneTests(AnswerFixture):
    def test_a_classified_answer_passes(self):
        self.assertEqual(failures(self.check(self.answer())), [])

    def test_an_unknown_source_class_fails_the_shape(self):
        bad = self.answer()
        bad["sentences"][0]["source_class"] = "vibes"
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_an_evidence_free_document_sentence_fails(self):
        bad = self.answer()
        bad["sentences"][0]["evidence"] = []
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_a_user_supplied_fact_carries_no_evidence(self):
        good = self.answer()
        good["sentences"].append(
            {"text": "You said the lender is fund A.", "source_class": "user_supplied", "evidence": []}
        )
        self.assertEqual(failures(self.check(good)), [])
        bad = self.answer()
        bad["sentences"].append(
            {"text": "You said the lender is fund A.", "source_class": "user_supplied", "evidence": ["c1"]}
        )
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_a_calculation_derives_from_known_evidence(self):
        good = self.answer()
        good["sentences"].append(
            {"text": "So one of one flag is set.", "source_class": "calculation", "evidence": ["c1", "r1"]}
        )
        self.assertEqual(failures(self.check(good)), [])


class GateTwoTests(AnswerFixture):
    def test_a_mismatched_span_fails_answer_citations(self):
        bad = self.answer()
        bad["citations"][0]["display_text"] = "The pause flag halts all entries."
        self.assertEqual(failures(self.check(bad)), ["answer-citations"])

    def test_a_drifted_corpus_file_fails_answer_citations(self):
        with open(os.path.join(self.root, "terms.md"), "ab") as handle:
            handle.write(b"\n")
        self.assertEqual(failures(self.check(self.answer())), ["answer-citations"])


class GateThreeTests(AnswerFixture):
    def test_a_read_without_a_preserved_record_fails(self):
        bad = self.answer()
        bad["reads"][0]["request_key"] = "0" * 64
        self.assertEqual(failures(self.check(bad)), ["answer-reads"])

    def test_a_read_naming_another_block_fails(self):
        bad = self.answer()
        bad["reads"][0]["block_number"] = BLOCK + 1
        self.assertEqual(failures(self.check(bad)), ["answer-reads"])

    def test_a_read_naming_another_chain_fails(self):
        bad = self.answer()
        bad["reads"][0]["chain_id"] = 10
        self.assertEqual(failures(self.check(bad)), ["answer-reads"])

    def test_a_boolean_block_number_fails_the_shape(self):
        bad = self.answer()
        bad["reads"][0]["block_number"] = True
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])


class GateFourTests(AnswerFixture):
    def test_a_declared_disagreement_passes_and_is_counted(self):
        good = self.answer()
        good["discrepancies"] = [
            {
                "subject": "pause flag",
                "document_evidence": "c1",
                "chain_evidence": "r1",
                "note": "the document says set; the block read disagrees",
            }
        ]
        checks = self.check(good)
        self.assertEqual(failures(checks), [])
        domains = [c for c in checks if c.name == "answer-domains"][0]
        self.assertIn("1 declared", domains.detail)

    def test_a_disagreement_naming_unknown_evidence_fails_the_shape(self):
        bad = self.answer()
        bad["discrepancies"] = [
            {
                "subject": "pause flag",
                "document_evidence": "c9",
                "chain_evidence": "r1",
                "note": "the sides disagree",
            }
        ]
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])


class GateFiveTests(AnswerFixture):
    def refusal(self):
        return {
            "format": answers.FORMAT,
            "question": "What is the lender's home address?",
            "kind": "refusal",
            "refusal": {
                "boundary": "outside the declared question families",
                "detail": "the release answers protocol questions, not personal ones",
            },
            "sentences": [],
            "citations": [],
            "reads": [],
            "discrepancies": [],
        }

    def test_a_clean_refusal_passes(self):
        checks = self.check(self.refusal())
        self.assertEqual(failures(checks), [])
        self.assertEqual([c.name for c in checks], ["answer-shape", "answer-refusal"])

    def test_a_refusal_carrying_sentences_fails_the_shape(self):
        bad = self.refusal()
        bad["sentences"] = [
            {"text": "Here it is anyway.", "source_class": "document", "evidence": []}
        ]
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_a_refusal_without_a_boundary_fails_the_shape(self):
        bad = self.refusal()
        bad["refusal"] = {"boundary": " ", "detail": "unnamed"}
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])


class HygieneTests(AnswerFixture):
    def test_unused_evidence_fails_the_shape(self):
        bad = self.answer()
        bad["citations"].append(self.citation("Version 3 keeps it set.", "c2"))
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_duplicate_evidence_ids_fail_the_shape(self):
        bad = self.answer()
        bad["citations"].append(self.citation("Version 3 keeps it set.", "c1"))
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_a_shared_citation_and_read_id_fails_the_shape(self):
        bad = self.answer()
        bad["reads"][0]["id"] = "c1"
        bad["sentences"][1]["evidence"] = ["c1"]
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_an_undeclared_field_fails_the_shape(self):
        bad = self.answer()
        bad["model"] = "gpt"
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])


class SchemaAgreementTests(unittest.TestCase):
    def test_the_shipped_schema_matches_the_module(self):
        with open(SCHEMAS / "answer-v1.json", "r", encoding="utf-8") as handle:
            schema = json.load(handle)
        self.assertEqual(schema["properties"]["format"]["const"], answers.FORMAT)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(tuple(schema["required"]), answers.FIELDS)
        self.assertEqual(tuple(schema["properties"]["kind"]["enum"]), answers.KINDS)
        sentence = schema["properties"]["sentences"]["items"]
        self.assertEqual(tuple(sentence["required"]), answers.SENTENCE_FIELDS)
        self.assertEqual(
            tuple(sentence["properties"]["source_class"]["enum"]), answers.SOURCE_CLASSES
        )
        self.assertEqual(
            tuple(schema["properties"]["reads"]["items"]["required"]), answers.READ_FIELDS
        )
        self.assertEqual(
            schema["properties"]["sentences"]["maxItems"], answers.MAX_SENTENCES
        )


class CliTests(AnswerFixture):
    def test_the_cli_proves_and_refuses_an_answer(self):
        import importlib

        berean = importlib.import_module("berean")
        from berean_lib import canonical

        manifest_path = os.path.join(self.holder.name, "corpus-manifest.json")
        corpus.write(self.manifest, manifest_path)
        answer_path = os.path.join(self.holder.name, "answer.json")
        with open(answer_path, "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(self.answer()) + "\n")
        argv = [
            "check-answer", answer_path,
            "--corpus", manifest_path,
            "--root", self.root,
            "--reads", self.reads_path,
            "--chain-id", str(CHAIN_ID),
            "--block-number", str(BLOCK),
        ]
        self.assertEqual(berean.main(argv), 0)
        self.assertEqual(berean.main(argv[:-1] + [str(BLOCK + 1)]), 1)


if __name__ == "__main__":
    unittest.main()
