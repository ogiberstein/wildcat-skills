#!/usr/bin/env python3
"""Berean: release, verify and evaluate evidence-backed protocol agents."""

import argparse
import sys

from berean_lib import BereanError
from berean_lib import corpus as corpus_lib
from berean_lib import citations as citations_lib
from berean_lib import jsonio


def report(checks):
    failed = 0
    for check in checks:
        print(check.line())
        if not check.passed:
            failed += 1
    if failed:
        print(f"refused: {failed} check(s) failed")
        return 1
    print("all checks passed")
    return 0


def cmd_build_corpus(args):
    document = corpus_lib.build(args.tree, args.corpus_version)
    corpus_lib.write(document, args.out)
    print(f"pinned {len(document['files'])} file(s); corpus digest {document['corpus_digest']}")
    return 0


def cmd_verify_corpus(args):
    document = jsonio.load(args.manifest, "corpus manifest")
    return report(corpus_lib.verify(document, args.root))


def cmd_check_citation(args):
    citation = jsonio.load(args.citation, "citation")
    manifest = jsonio.load(args.corpus, "corpus manifest")
    corpus_lib.validate(manifest)
    return report(citations_lib.check(citation, manifest, args.root))


def build_parser():
    parser = argparse.ArgumentParser(prog="berean", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build-corpus", help="pin a document tree into a corpus manifest")
    build.add_argument("tree", help="the document tree to pin")
    build.add_argument("--out", required=True, help="where the manifest lands")
    build.add_argument("--corpus-version", default="v1", help="the corpus version label")
    build.set_defaults(handler=cmd_build_corpus)

    verify = commands.add_parser("verify-corpus", help="hold a tree to its corpus manifest")
    verify.add_argument("manifest", help="the corpus manifest")
    verify.add_argument("--root", required=True, help="the document tree it pins")
    verify.set_defaults(handler=cmd_verify_corpus)

    check = commands.add_parser("check-citation", help="prove a citation as exact bytes")
    check.add_argument("citation", help="the citation document")
    check.add_argument("--corpus", required=True, help="the corpus manifest")
    check.add_argument("--root", required=True, help="the document tree the manifest pins")
    check.set_defaults(handler=cmd_check_citation)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except BereanError as error:
        print(f"refused: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
