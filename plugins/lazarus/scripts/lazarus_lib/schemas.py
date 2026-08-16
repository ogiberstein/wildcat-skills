"""Built-in Lazarus schema registry and semantic format checks."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from .canonical import dumps, load
from .errors import FormatError, IntegrityError


SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "schemas"
SCHEMAS: dict[tuple[str, int], tuple[str, str]] = {
    ("plan", 1): (
        "plan-v1.json",
        "f7081f2007ac8116215ffcb508a2ffc09d9c04fba512d87d1b69a885b72915de",
    ),
    ("header", 1): (
        "header-v1.json",
        "222e16df19169ae545e49ea423928ef63400ed078972e24734ac0697296fc9ac",
    ),
    ("rpc-record", 1): (
        "rpc-record-v1.json",
        "47c3036ab84c10cf09abc450bc7ba862d1de91d6619b5ecb46c71bc49ee9501e",
    ),
    ("proof-record", 1): (
        "proof-record-v1.json",
        "3ed92e5ebb37ca2358e3b0b28b57333cb4f6c6bc5a2e760d81f73a226c679ee7",
    ),
    ("manifest", 1): (
        "manifest-v1.json",
        "53acaefd6ddaf5648dc9d16345fc13c64c3bd7786851271ef922b67b9f423c14",
    ),
}


def _schema(kind: str, version: int) -> dict[str, Any]:
    registered = SCHEMAS.get((kind, version))
    if registered is None:
        raise FormatError(f"unsupported {kind} schema version: {version}")
    filename, expected_digest = registered
    path = SCHEMA_ROOT / filename
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise IntegrityError(f"cannot read built-in schema: {filename}") from exc
    actual_digest = hashlib.sha256(raw).hexdigest()
    if actual_digest != expected_digest:
        raise IntegrityError(f"built-in schema digest mismatch: {filename}")
    value = load(path)
    if not isinstance(value, dict):
        raise IntegrityError(f"built-in schema is not an object: {filename}")
    return value


def validate_builtin_schemas() -> None:
    for kind, version in SCHEMAS:
        schema = _schema(kind, version)
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise IntegrityError(f"invalid built-in {kind} schema: {exc.message}") from exc


def validate_document(kind: str, document: Any) -> Any:
    if not isinstance(document, dict):
        raise FormatError(f"{kind} document must be an object")
    version = document.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise FormatError(f"{kind} schema_version must be an integer")
    schema = _schema(kind, version)
    try:
        Draft202012Validator(schema).validate(document)
    except ValidationError as exc:
        location = "/".join(str(part) for part in exc.absolute_path) or "<root>"
        raise FormatError(f"invalid {kind} at {location}: {exc.message}") from exc
    # Canonical encoding also rejects floats and unsupported Python values that
    # JSON Schema deliberately permits as generic JSON instances.
    dumps(document)
    semantic = {
        "plan": _validate_plan,
        "header": _validate_header,
        "rpc-record": _validate_rpc_record,
        "proof-record": _validate_proof_record,
        "manifest": _validate_manifest,
    }[kind]
    semantic(document)
    return document


def _require_unique(values: list[str], label: str) -> None:
    if len(set(values)) != len(values):
        raise FormatError(f"duplicate {label}")


def _validate_plan(plan: dict[str, Any]) -> None:
    requests = plan["requests"]
    limit = plan["limits"]["max_requests"]
    if len(requests) > limit:
        raise FormatError("plan requests exceed max_requests")
    names = [request["name"] for request in requests]
    _require_unique(names, "request name")
    request_bytes = [dumps({"method": item["method"], "params": item["params"]}) for item in requests]
    if len(set(request_bytes)) != len(request_bytes):
        raise FormatError("duplicate exact request")
    addresses = [target["address"].lower() for target in plan["proof_targets"]]
    _require_unique(addresses, "proof target address")
    for target in plan["proof_targets"]:
        slots = [slot.lower() for slot in target["slots"]]
        if slots != sorted(slots) or len(slots) != len(set(slots)):
            raise FormatError(f"proof slots must be sorted and unique: {target['address']}")


def _validate_header(header: dict[str, Any]) -> None:
    rpc = header["rpc_result"]
    comparisons = {
        "number": "number",
        "hash": "hash",
        "parentHash": "parent_hash",
        "stateRoot": "state_root",
    }
    for rpc_name, header_name in comparisons.items():
        if rpc_name in rpc and rpc[rpc_name] != header[header_name]:
            raise FormatError(f"header {header_name} disagrees with rpc_result.{rpc_name}")


def _validate_rpc_record(record: dict[str, Any]) -> None:
    from .records import request_key

    expected = request_key(record["method"], record["params"])
    if record["request_key"] != expected:
        raise FormatError("RPC record request_key does not match method and params")
    if not record["required"] and "error" in record["outcome"]:
        return
    if record["required"] and "error" in record["outcome"]:
        raise FormatError("a required RPC record cannot preserve an error outcome")


def _validate_proof_record(record: dict[str, Any]) -> None:
    keys = [item["key"].lower() for item in record["storage_proof"]]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise FormatError("storage proof keys must be sorted and unique")


def _validate_manifest(manifest: dict[str, Any]) -> None:
    from .paths import validate_relative_path

    paths = [validate_relative_path(item["path"]) for item in manifest["components"]]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise FormatError("manifest component paths must be sorted and unique")
    if "manifest.json" in paths:
        raise FormatError("manifest cannot list itself as a component")
    failures = manifest["optional_failures"]
    if failures != sorted(failures) or len(failures) != len(set(failures)):
        raise FormatError("optional failures must be sorted and unique")
