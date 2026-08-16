#!/usr/bin/env python3
"""ariadne -- signed evidence another person can check.

Five subcommands:

    predicates  list the predicate types this build understands
    capture     read a build on disk into a statement
    inspect     read a statement or DSSE envelope and report what it covers
    verify      run the gates over a statement and report each one
    replay      re-run the deterministic commands a statement records

Exit codes: 0 success, 1 a gate was breached, 2 usage or validation error.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ariadne_lib import digests, envelope, registry, replay, safejson, verify  # noqa: E402
from ariadne_lib import predicates  # noqa: E402,F401  (registers them)
from ariadne_lib.capture import foundry  # noqa: E402
from ariadne_lib.statement import StatementError  # noqa: E402

GATE_BREACHED = 1
USAGE_ERROR = 2

READ_ERRORS = (envelope.EnvelopeError, StatementError, safejson.InputError)


def load_document(path, max_bytes, max_depth):
    """Read and parse a file, bounded twice: on disk and in the parser."""
    if not os.path.exists(path):
        raise safejson.InputError("no such file")
    if not os.path.isfile(path):
        # A fifo reports a size of zero and then blocks the read until
        # somebody writes to it, so the size cap would wave it through and the
        # tool would hang on a document that never arrives.
        raise safejson.InputError("not a regular file; a statement is read from one")
    try:
        size = os.path.getsize(path)
    except OSError as error:
        raise safejson.InputError("cannot read: %s" % error)
    if size > max_bytes:
        raise safejson.InputError(
            "%d bytes, over the %d byte cap" % (size, max_bytes)
        )
    try:
        with open(path, "rb") as handle:
            data = handle.read(max_bytes + 1)
    except OSError as error:
        raise safejson.InputError("cannot read: %s" % error)
    if len(data) > max_bytes:
        raise safejson.InputError(
            "grew past the %d byte cap while being read" % max_bytes
        )
    return envelope.read(data, safejson.loader(max_bytes, max_depth))


def cmd_predicates(args):
    entries = registry.DEFAULT.entries()
    if args.json:
        print(json.dumps([{"type": t, "summary": s} for t, s in entries], indent=2))
        return 0
    if not entries:
        print("no predicates registered in this build")
        print("a statement of any type still parses; its predicate goes unchecked")
        return 0
    width = max(len(t) for t, _ in entries)
    for type_uri, summary in entries:
        print("%s  %s" % (type_uri.ljust(width), summary))
    return 0


def cmd_inspect(args):
    try:
        document = load_document(args.file, args.max_bytes, args.max_depth)
    except READ_ERRORS as error:
        print("%s: %s" % (args.file, error), file=sys.stderr)
        return USAGE_ERROR

    found = document.statement
    known = registry.DEFAULT.knows(found.predicate_type)
    if args.json:
        print(
            json.dumps(
                {
                    "predicateType": found.predicate_type,
                    "predicateTypeKnown": known,
                    "subjects": [entry.to_dict() for entry in found.subjects],
                    "signatureState": document.signature_state,
                },
                indent=2,
            )
        )
        return 0

    print("predicate type: %s" % found.predicate_type)
    print("                %s" % ("registered" if known else "not registered here"))
    print("signatures:     %s" % document.signature_state)
    print("subjects:")
    for entry in found.subjects:
        print("  %s  %s" % (digests.short(entry.digest), entry.name or "<unnamed>"))
    return 0


def cmd_verify(args):
    try:
        document = load_document(args.file, args.max_bytes, args.max_depth)
    except READ_ERRORS as error:
        print("%s: %s" % (args.file, error), file=sys.stderr)
        return USAGE_ERROR

    report = verify.report(document, registry.DEFAULT)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        for line in report.lines():
            print(line)
    return 0 if report.ok else GATE_BREACHED


def parse_pairs(value, allowed, what):
    """`a=1,b=2` into a dict, refusing a key the caller did not define."""
    found = {}
    for part in value.split(","):
        key, separator, entry = part.partition("=")
        key = key.strip()
        if not separator or key not in allowed:
            raise argparse.ArgumentTypeError(
                "%s takes %s as key=value pairs, got %r"
                % (what, ", ".join(sorted(allowed)), part)
            )
        found[key] = entry.strip()
    return found


def deployment(value):
    found = parse_pairs(
        value,
        {"chain_id", "address", "creation_tx", "implementation"},
        "--deployment",
    )
    for field in ("chain_id", "address", "creation_tx"):
        if field not in found:
            raise argparse.ArgumentTypeError("--deployment needs %s" % field)
    try:
        found["chain_id"] = int(found["chain_id"])
    except ValueError:
        raise argparse.ArgumentTypeError("--deployment chain_id must be a number")
    return found


def audit(value):
    found = parse_pairs(value, {"report", "revision", "scope"}, "--audit")
    for field in ("report", "revision", "scope"):
        if field not in found:
            raise argparse.ArgumentTypeError("--audit needs %s" % field)
    try:
        report = digests.of_file(found["report"])
    except digests.DigestError as error:
        raise argparse.ArgumentTypeError("--audit report: %s" % error)
    return {
        "report_digest": report,
        "covered_revision": found["revision"],
        "scope": found["scope"],
    }


def cmd_capture(args):
    try:
        statement = foundry.capture(
            args.project,
            repository=args.repository,
            commit=args.commit,
            previous=args.previous,
            previous_name=args.previous_name,
            contracts=args.contract or None,
            build_command=args.build_command or None,
            tests=args.tests,
            fuzz=args.fuzz,
            audits=args.audit or None,
            deployments=args.deployment or None,
            first_release_reason=args.first_release_reason,
        )
    except (foundry.CaptureError, digests.DigestError) as error:
        print("capture failed: %s" % error, file=sys.stderr)
        return USAGE_ERROR

    body = json.dumps(statement, indent=2) + "\n"
    if args.out:
        try:
            with open(args.out, "w") as handle:
                handle.write(body)
        except OSError as error:
            print("cannot write %s: %s" % (args.out, error), file=sys.stderr)
            return USAGE_ERROR
        print("wrote %s" % args.out)
    else:
        sys.stdout.write(body)
    return 0


def recomputer(project):
    """How to recompute a Solidity release's build output, or None.

    A build's recorded output digest is over the artefacts rather than over
    what the command printed, so the comparison means recomputing the artefacts
    the way capture did.
    """
    if not project:
        return None

    def recompute(step):
        try:
            subjects = foundry.release_subjects(foundry.confined(project, "--project"))
        except foundry.CaptureError:
            return None
        return foundry.bundle(subjects)

    return recompute


def cmd_replay(args):
    try:
        document = load_document(args.file, args.max_bytes, args.max_depth)
    except READ_ERRORS as error:
        print("%s: %s" % (args.file, error), file=sys.stderr)
        return USAGE_ERROR

    if args.allow_execution and not args.project:
        print(
            "--allow-execution needs --project, the directory to run in",
            file=sys.stderr,
        )
        return USAGE_ERROR

    if args.allow_execution:
        # Running the commands in a statement nobody has checked is taking
        # instructions from a document on trust, which is the habit this whole
        # tool exists to break.
        report = verify.report(document, registry.DEFAULT)
        if not report.ok:
            print(
                "refusing to run: this statement does not verify", file=sys.stderr
            )
            for gate in report.ordered:
                if not gate.passed:
                    print("  %s" % gate.line(), file=sys.stderr)
            return GATE_BREACHED

    result = replay.replay(
        document.statement,
        allow_execution=args.allow_execution,
        cwd=args.project,
        recompute=recomputer(args.project),
        timeout=args.timeout,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        for line in result.lines():
            print(line)
    return 0 if result.ok else GATE_BREACHED


def add_input_bounds(parser):
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=safejson.DEFAULT_MAX_BYTES,
        help="refuse a file larger than this (default %(default)s)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=safejson.DEFAULT_MAX_DEPTH,
        help="refuse JSON nested deeper than this (default %(default)s)",
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="ariadne", description="Signed evidence another person can check."
    )
    subcommands = parser.add_subparsers(dest="command")

    listing = subcommands.add_parser(
        "predicates", help="list the predicate types this build understands"
    )
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(handler=cmd_predicates)

    inspect = subcommands.add_parser(
        "inspect", help="report what a statement or envelope covers"
    )
    inspect.add_argument("file")
    inspect.add_argument("--json", action="store_true")
    add_input_bounds(inspect)
    inspect.set_defaults(handler=cmd_inspect)

    grab = subcommands.add_parser(
        "capture", help="read a build on disk into a statement"
    )
    grab.add_argument(
        "kind",
        choices=["solidity-release"],
        help="the predicate to capture; one so far",
    )
    grab.add_argument("--project", required=True)
    grab.add_argument("--repository", required=True)
    grab.add_argument("--commit", required=True)
    grab.add_argument("--previous")
    grab.add_argument("--previous-name")
    grab.add_argument("--contract", action="append")
    grab.add_argument("--build-command", action="append")
    grab.add_argument(
        "--tests",
        help="disposition[:reason]; absent means skipped with a reason saying so",
    )
    grab.add_argument("--fuzz", help="disposition[:reason], as for --tests")
    grab.add_argument("--audit", action="append", type=audit)
    grab.add_argument("--deployment", action="append", type=deployment)
    grab.add_argument("--first-release-reason")
    grab.add_argument("--out")
    grab.set_defaults(handler=cmd_capture)

    check = subcommands.add_parser(
        "verify", help="run the core gates over a statement"
    )
    check.add_argument("file")
    check.add_argument("--json", action="store_true")
    add_input_bounds(check)
    check.set_defaults(handler=cmd_verify)

    again = subcommands.add_parser(
        "replay", help="re-run the deterministic commands a statement records"
    )
    again.add_argument("file")
    again.add_argument(
        "--allow-execution",
        action="store_true",
        help="actually run the exact commands; without this the plan is printed",
    )
    again.add_argument("--project", help="the directory to run in")
    again.add_argument("--timeout", type=int, default=replay.DEFAULT_TIMEOUT)
    again.add_argument("--json", action="store_true")
    add_input_bounds(again)
    again.set_defaults(handler=cmd_replay)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "handler", None):
        parser.print_help()
        return USAGE_ERROR
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
