#!/usr/bin/env python3
"""Janus command-line surface: manifest validation and report rendering.

This module is built across the Fiat runbook. Step 1 establishes the module and
its command dispatch; `validate` lands in step 2 and `report` in step 6. Each
subcommand is registered here and raises `NotImplementedError` until its step
lands, so the module imports cleanly from the first step and the test suite can
grow with it.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional, Tuple


VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Manifest validation
#
# The codes below are an interface other tools cite; renumbering them breaks
# those citations. A manifest is rejected the moment one rule fails, and the
# first failure's code and message are what the caller sees. The rules enforce
# gate 1 directly: every effect list must be present, an omitted list is an
# error rather than a silent permit, and no effect may be a wildcard, so a
# manifest can never say a hook may change anything.
# ---------------------------------------------------------------------------

HOST_ACTIONS = {
    "createMarket",
    "deposit",
    "queueWithdrawal",
    "executeWithdrawal",
    "transfer",
    "borrow",
    "repay",
    "closeMarket",
    "nukeFromOrbit",
    "setMaxTotalSupply",
    "setAnnualInterestAndReserveRatioBips",
    "setProtocolFeeBips",
    "executePendingAnnualInterestBipsReduction",
}

TOP_LEVEL_KEYS = {
    "manifestVersion",
    "host",
    "hook",
    "rollbackRule",
    "thresholds",
    "liveness",
    # Tolerated documentation keys that carry no rule.
    "$schema",
    "$id",
}

REQUIRED_TOP_LEVEL = ["manifestVersion", "host", "hook", "rollbackRule", "thresholds", "liveness"]

THRESHOLD_KEYS = {
    "action",
    "entryPoints",
    "extraDataAllowed",
    "permittedStorageWrites",
    "permittedCalls",
    "permittedValueMovements",
    "gasBudget",
    "failureMode",
    "mayReturnValues",
}

EFFECT_LISTS = ("permittedStorageWrites", "permittedCalls", "permittedValueMovements")

WILDCARDS = {"*", "any", "all", "ANY", "ALL", "*.*"}

STORAGE_SCOPES = {"hook", "host", "external"}
CALL_KINDS = {"call", "staticcall", "delegatecall"}

LIVENESS_KEYS = {"withdrawal", "uninstall", "emergency"}


class ManifestError(Exception):
    """A single, coded validation failure."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _require_keys(obj: dict, required, code: str, where: str) -> None:
    for key in required:
        if key not in obj:
            raise ManifestError(code, f"{where} is missing required key '{key}'")


def _no_unknown_keys(obj: dict, allowed, code: str, where: str) -> None:
    for key in obj:
        if key not in allowed:
            raise ManifestError(code, f"{where} carries unknown key '{key}'")


def _effect_values(effect: dict) -> List[str]:
    """The free-text fields of one effect, where a wildcard would hide."""
    values = []
    for key in ("slot", "target", "asset", "recipient"):
        if key in effect and isinstance(effect[key], str):
            values.append(effect[key])
    return values


def validate_manifest_obj(manifest) -> None:
    """Raise ManifestError on the first rule a manifest breaks."""
    if not isinstance(manifest, dict):
        raise ManifestError("J002", "manifest is not a JSON object")

    _require_keys(manifest, REQUIRED_TOP_LEVEL, "J002", "manifest")
    _no_unknown_keys(manifest, TOP_LEVEL_KEYS, "J014", "manifest")

    if manifest["manifestVersion"] != "1":
        raise ManifestError(
            "J003", f"manifestVersion must be \"1\", got {manifest['manifestVersion']!r}"
        )

    if manifest["rollbackRule"] not in ("full", "none"):
        raise ManifestError(
            "J004", f"rollbackRule must be 'full' or 'none', got {manifest['rollbackRule']!r}"
        )

    thresholds = manifest["thresholds"]
    if not isinstance(thresholds, list) or not thresholds:
        raise ManifestError("J005", "thresholds must be a non-empty array")

    for index, threshold in enumerate(thresholds):
        where = f"threshold[{index}]"
        if not isinstance(threshold, dict):
            raise ManifestError("J006", f"{where} is not an object")
        _require_keys(threshold, THRESHOLD_KEYS, "J006", where)
        _no_unknown_keys(threshold, THRESHOLD_KEYS, "J014", where)

        if threshold["action"] not in HOST_ACTIONS:
            raise ManifestError("J007", f"{where} names unknown action {threshold['action']!r}")

        entry_points = threshold["entryPoints"]
        if not isinstance(entry_points, list) or not entry_points:
            raise ManifestError("J006", f"{where}.entryPoints must be a non-empty array")

        for name in EFFECT_LISTS:
            effects = threshold[name]
            if not isinstance(effects, list):
                raise ManifestError(
                    "J008",
                    f"{where}.{name} must be a list; an omitted or non-list effect list is "
                    "forbidden, since a hook's permitted effects are enumerated, not assumed",
                )
            for effect in effects:
                if not isinstance(effect, dict):
                    raise ManifestError("J008", f"{where}.{name} entry is not an object")
                for value in _effect_values(effect):
                    if value in WILDCARDS:
                        raise ManifestError(
                            "J009",
                            f"{where}.{name} contains the wildcard {value!r}; a manifest may "
                            "not say a hook can change anything",
                        )
                # The scope and kind fields are enumerations. Enforce them here,
                # not only in the schema, or an unrecognised scope or call kind
                # would validate and the harness would meet it as an unknown
                # effect at run time. Fail closed on the unrecognised value.
                if name == "permittedStorageWrites" and effect.get("scope") not in STORAGE_SCOPES:
                    raise ManifestError(
                        "J015",
                        f"{where}.{name} has scope {effect.get('scope')!r}; "
                        f"must be one of {sorted(STORAGE_SCOPES)}",
                    )
                if name == "permittedCalls" and effect.get("kind") not in CALL_KINDS:
                    raise ManifestError(
                        "J015",
                        f"{where}.{name} has kind {effect.get('kind')!r}; "
                        f"must be one of {sorted(CALL_KINDS)}",
                    )

        if not isinstance(threshold["extraDataAllowed"], bool):
            raise ManifestError("J006", f"{where}.extraDataAllowed must be a boolean")

        gas = threshold["gasBudget"]
        if not isinstance(gas, int) or isinstance(gas, bool) or gas < 1:
            raise ManifestError("J010", f"{where}.gasBudget must be a positive integer")

        if threshold["failureMode"] not in ("fail-open", "fail-closed"):
            raise ManifestError(
                "J011", f"{where}.failureMode must be 'fail-open' or 'fail-closed'"
            )

        if not isinstance(threshold["mayReturnValues"], bool):
            raise ManifestError("J012", f"{where}.mayReturnValues must be a boolean")

    liveness = manifest["liveness"]
    if not isinstance(liveness, dict):
        raise ManifestError("J013", "liveness must be an object")
    _require_keys(liveness, LIVENESS_KEYS, "J013", "liveness")
    _no_unknown_keys(liveness, LIVENESS_KEYS, "J014", "liveness")
    for key in LIVENESS_KEYS:
        if not isinstance(liveness[key], str) or not liveness[key].strip():
            raise ManifestError("J013", f"liveness.{key} must be a non-empty string")


def validate_manifest_file(path: str) -> Tuple[bool, str]:
    """Return (ok, message) for one manifest file, never raising."""
    try:
        with open(path, encoding="utf-8") as handle:
            manifest = json.load(handle)
    except json.JSONDecodeError as error:
        return False, f"J001: {path}: not valid JSON: {error}"
    except OSError as error:
        return False, f"J001: {path}: cannot read: {error}"
    try:
        validate_manifest_obj(manifest)
    except ManifestError as error:
        return False, f"{error.code}: {path}: {error.message}"
    return True, f"{path}: valid"


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate hook manifests against the schema rules."""
    failures = 0
    for path in args.manifests:
        ok, message = validate_manifest_file(path)
        print(message)
        if not ok:
            failures += 1
    return 1 if failures else 0


def cmd_report(args: argparse.Namespace) -> int:
    """Render human and SARIF reports from a findings file. Lands in step 6."""
    raise NotImplementedError("janus report lands in runbook step 6")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="janus",
        description="Hook-conformance manifest validation and report rendering.",
    )
    parser.add_argument("--version", action="version", version=f"janus {VERSION}")
    sub = parser.add_subparsers(dest="command")

    validate = sub.add_parser("validate", help="validate hook manifests")
    validate.add_argument("manifests", nargs="+", help="manifest JSON files")
    validate.set_defaults(func=cmd_validate)

    report = sub.add_parser("report", help="render human and SARIF reports")
    report.add_argument("--findings", required=True, help="findings JSON file")
    report.add_argument("--md", help="human-readable Markdown output path")
    report.add_argument("--sarif", help="SARIF 2.1.0 output path")
    report.set_defaults(func=cmd_report)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
