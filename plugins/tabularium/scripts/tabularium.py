#!/usr/bin/env python3
"""Build and verify deterministic Tabularium credit-event releases."""

import argparse
import sys

from tabularium_lib.builder import build
from tabularium_lib.core import TabulariumError
from tabularium_lib.verifier import verify


def make_parser():
    parser = argparse.ArgumentParser(
        description="Build deterministic Tabularium credit-event JSONL."
    )
    subcommands = parser.add_subparsers(dest="command", metavar="{build,verify}")
    build_parser = subcommands.add_parser(
        "build", help="build canonical venue-qualified credit-event JSONL"
    )
    build_parser.add_argument(
        "--adapter",
        choices=("goldfinch", "euler-v1", "euler-v2"),
        default="goldfinch",
        help="source adapter (default: goldfinch)",
    )
    build_parser.add_argument("--source", required=True, help="preserved source JSON")
    build_parser.add_argument(
        "--capture-manifest", required=True, help="preserved capture manifest JSON"
    )
    build_parser.add_argument("--out", required=True, help="canonical JSONL output")
    build_parser.add_argument(
        "--manifest", required=True, help="coverage manifest output"
    )
    build_parser.add_argument("--release", required=True, help="release identifier")
    verify_parser = subcommands.add_parser(
        "verify",
        help="verify a release offline from its coverage manifest",
        description="Verify a release fully offline from its coverage manifest.",
    )
    verify_parser.add_argument("manifest", help="coverage manifest to verify")
    return parser


def main(argv=None):
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help(sys.stderr)
        return 2
    if args.command == "verify":
        try:
            report = verify(args.manifest)
        except (OSError, TabulariumError) as error:
            print("tabularium: verification failed: %s" % error, file=sys.stderr)
            return 1
        print(
            "verified %s offline: %d event(s), sha256 %s"
            % (report.release, report.rows, report.sha256)
        )
        return 0
    try:
        report = build(
            args.source,
            args.capture_manifest,
            args.out,
            args.manifest,
            args.release,
            args.adapter,
        )
    except (OSError, TabulariumError) as error:
        print("tabularium: %s" % error, file=sys.stderr)
        return 2
    print(
        "built %d event(s): %s; sha256 %s"
        % (
            report.rows,
            ", ".join("%s=%d" % item for item in sorted(report.families.items())),
            report.sha256,
        ),
        file=sys.stderr,
    )
    print(
        "not mapped as events: %s"
        % ", ".join(
            "%s=%d" % item for item in sorted(report.unmapped_counts.items())
        ),
        file=sys.stderr,
    )
    print("coverage manifest sha256 %s" % report.manifest_sha256, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
