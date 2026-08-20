"""Citations pass as exact bytes or fail by name."""

import os
import tempfile
import unittest

from tests.support import SCRIPTS  # noqa: F401

from berean_lib import citations, corpus, digests
from tests.test_corpus import make_tree, failures

TEXT = "# Guide\n\nThe registry refuses café entries after close.\n".encode("utf-8")


def cite(data, start, end, doc="guide.md"):
    piece = data[start:end]
    return {
        "format": citations.FORMAT,
        "doc": doc,
        "byte_start": start,
        "byte_end": end,
        "sha256": digests.of_bytes(piece),
        "display_text": piece.decode("utf-8"),
    }


class CitationTests(unittest.TestCase):
    def setUp(self):
        self.root_holder = tempfile.TemporaryDirectory()
        self.root = self.root_holder.name
        make_tree(self.root, {"guide.md": TEXT})
        self.manifest = corpus.build(self.root, "v1")

    def tearDown(self):
        self.root_holder.cleanup()

    def test_an_exact_span_passes_every_check(self):
        citation = cite(TEXT, 9, 21)
        self.assertEqual(failures(citations.check(citation, self.manifest, self.root)), [])

    def test_a_multibyte_span_passes_when_whole(self):
        start = TEXT.index("café".encode("utf-8"))
        citation = cite(TEXT, start, start + len("café".encode("utf-8")))
        self.assertEqual(failures(citations.check(citation, self.manifest, self.root)), [])
        self.assertEqual(citation["display_text"], "café")

    def test_a_span_splitting_a_character_fails_citation_text(self):
        start = TEXT.index("café".encode("utf-8"))
        citation = {
            "format": citations.FORMAT,
            "doc": "guide.md",
            "byte_start": start,
            "byte_end": start + 4,
            "sha256": digests.of_bytes(TEXT[start:start + 4]),
            "display_text": "caf?",
        }
        self.assertEqual(
            failures(citations.check(citation, self.manifest, self.root)), ["citation-text"]
        )

    def test_a_wrong_digest_fails_citation_bytes(self):
        citation = cite(TEXT, 9, 21)
        citation["sha256"] = "0" * 64
        self.assertEqual(
            failures(citations.check(citation, self.manifest, self.root)), ["citation-bytes"]
        )

    def test_wrong_display_text_fails_citation_text(self):
        citation = cite(TEXT, 9, 21)
        citation["display_text"] = "something else"
        self.assertEqual(
            failures(citations.check(citation, self.manifest, self.root)), ["citation-text"]
        )

    def test_a_range_past_the_file_fails_citation_range(self):
        citation = cite(TEXT, 0, 8)
        citation["byte_end"] = len(TEXT) + 1
        self.assertEqual(
            failures(citations.check(citation, self.manifest, self.root)), ["citation-range"]
        )

    def test_an_empty_range_fails_the_shape(self):
        citation = cite(TEXT, 0, 8)
        citation["byte_end"] = 0
        self.assertEqual(
            failures(citations.check(citation, self.manifest, self.root)), ["citation-shape"]
        )

    def test_a_boolean_offset_fails_the_shape(self):
        citation = cite(TEXT, 0, 8)
        citation["byte_start"] = False
        self.assertEqual(
            failures(citations.check(citation, self.manifest, self.root)), ["citation-shape"]
        )

    def test_an_unpinned_document_fails_citation_doc(self):
        citation = cite(TEXT, 0, 8, doc="elsewhere.md")
        self.assertEqual(
            failures(citations.check(citation, self.manifest, self.root)), ["citation-doc"]
        )

    def test_a_drifted_file_fails_citation_pin(self):
        citation = cite(TEXT, 0, 8)
        with open(os.path.join(self.root, "guide.md"), "ab") as handle:
            handle.write(b"\n")
        self.assertEqual(
            failures(citations.check(citation, self.manifest, self.root)), ["citation-pin"]
        )

    def test_an_undeclared_field_fails_the_shape(self):
        citation = cite(TEXT, 0, 8)
        citation["confidence"] = "high"
        self.assertEqual(
            failures(citations.check(citation, self.manifest, self.root)), ["citation-shape"]
        )


class CliTests(unittest.TestCase):
    def test_the_cli_proves_and_refuses_end_to_end(self):
        import importlib

        berean = importlib.import_module("berean")
        from berean_lib import canonical

        with tempfile.TemporaryDirectory() as work:
            root = os.path.join(work, "docs")
            make_tree(root, {"guide.md": TEXT})
            manifest_path = os.path.join(work, "corpus-manifest.json")
            self.assertEqual(
                berean.main(["build-corpus", root, "--out", manifest_path]), 0
            )
            self.assertEqual(
                berean.main(["verify-corpus", manifest_path, "--root", root]), 0
            )
            citation_path = os.path.join(work, "quote.json")
            with open(citation_path, "w", encoding="utf-8") as handle:
                handle.write(canonical.dumps(cite(TEXT, 9, 21)) + "\n")
            self.assertEqual(
                berean.main(
                    ["check-citation", citation_path, "--corpus", manifest_path, "--root", root]
                ),
                0,
            )
            with open(os.path.join(root, "guide.md"), "wb") as handle:
                handle.write(TEXT.replace(b"refuses", b"accepts"))
            self.assertEqual(
                berean.main(["verify-corpus", manifest_path, "--root", root]), 1
            )
            self.assertEqual(
                berean.main(
                    ["check-citation", citation_path, "--corpus", manifest_path, "--root", root]
                ),
                1,
            )

    def test_usage_errors_exit_two(self):
        import importlib

        berean = importlib.import_module("berean")
        self.assertEqual(
            berean.main(["verify-corpus", "/no/such/manifest.json", "--root", "/tmp"]), 2
        )


if __name__ == "__main__":
    unittest.main()
