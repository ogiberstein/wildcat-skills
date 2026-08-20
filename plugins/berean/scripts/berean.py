#!/usr/bin/env python3
"""Berean: release, verify and evaluate evidence-backed protocol agents."""

import argparse
import sys

from berean_lib import BereanError
from berean_lib import answers as answers_lib
from berean_lib import corpus as corpus_lib
from berean_lib import citations as citations_lib
from berean_lib import jsonio
from berean_lib import promote as promote_lib
from berean_lib import reads as reads_lib
from berean_lib import release as release_lib


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


def cmd_check_answer(args):
    answer = jsonio.load(args.answer, "answer")
    manifest = jsonio.load(args.corpus, "corpus manifest")
    corpus_lib.validate(manifest)
    records = reads_lib.load(args.reads)
    return report(
        answers_lib.check(
            answer, manifest, args.root, records, args.chain_id, args.block_number
        )
    )


def cmd_verify_release(args):
    return report(release_lib.verify(args.release))


def cmd_promote(args):
    record = promote_lib.promote(args.release, args.note)
    print(f"promoted {record['release_digest']} on {record['evals']['cases']} case(s)")
    return 0


def cmd_rollback(args):
    record = promote_lib.rollback(args.release, args.to, args.reason, args.note)
    print(f"rolled back to {record['restored_digest']}")
    return 0


def cmd_promotion_chain(args):
    import os

    from berean_lib import canonical

    document = release_lib.load(args.release)
    chain_path = os.path.join(args.release, release_lib.PROMOTIONS_FILE)
    chain = promote_lib.load_chain(chain_path) if os.path.exists(chain_path) else []
    for record in chain:
        print(canonical.dumps(record))
    print(f"state: {promote_lib.state(chain, document)}")
    return 0


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

    answer = commands.add_parser(
        "check-answer", help="prove an answer's classes, citations and reads"
    )
    answer.add_argument("answer", help="the answer document")
    answer.add_argument("--corpus", required=True, help="the corpus manifest")
    answer.add_argument("--root", required=True, help="the document tree the manifest pins")
    answer.add_argument("--reads", required=True, help="the preserved reads file")
    answer.add_argument("--chain-id", required=True, type=int, help="the declared chain id")
    answer.add_argument(
        "--block-number", required=True, type=int, help="the declared block number"
    )
    answer.set_defaults(handler=cmd_check_answer)

    verify_release = commands.add_parser(
        "verify-release", help="run the release gates by name"
    )
    verify_release.add_argument("release", help="the release directory")
    verify_release.set_defaults(handler=cmd_verify_release)

    promote = commands.add_parser(
        "promote", help="record a promotion on the release's own eval report"
    )
    promote.add_argument("release", help="the release directory")
    promote.add_argument("--note", required=True, help="context for the record")
    promote.set_defaults(handler=cmd_promote)

    rollback = commands.add_parser("rollback", help="record a rollback to another release")
    rollback.add_argument("release", help="the release directory")
    rollback.add_argument("--to", required=True, help="the restored release digest")
    rollback.add_argument("--reason", required=True, help="why the release stands down")
    rollback.add_argument("--note", required=True, help="context for the record")
    rollback.set_defaults(handler=cmd_rollback)

    chain = commands.add_parser("promotion-chain", help="print and check the promotion chain")
    chain.add_argument("release", help="the release directory")
    chain.set_defaults(handler=cmd_promotion_chain)

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
