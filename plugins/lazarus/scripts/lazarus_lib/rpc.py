"""Small fail-closed JSON-RPC client used only by capture."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .canonical import dumps, loads
from .errors import FormatError, LazarusError
from .limits import CaptureLimits
from .scrub import sanitised_rpc_error


class RpcTransportError(LazarusError):
    """A safe provider transport or protocol failure."""


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class RpcOutcome:
    result: Any = None
    error: dict[str, Any] | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


class JsonRpcClient:
    def __init__(
        self,
        url: str,
        limits: CaptureLimits,
        *,
        headers: Mapping[str, str] | None = None,
        opener: Any = None,
    ) -> None:
        self._url = url
        self._limits = limits
        self._headers = {"Content-Type": "application/json"}
        self._headers.update(headers or {})
        self._opener = opener or build_opener(ProxyHandler({}), _RejectRedirects())
        self._next_id = 1

    def call(self, method: str, params: list[Any] | dict[str, Any]) -> Any:
        outcome = self.request_many([(method, params)])[0]
        if outcome.error is not None:
            raise RpcTransportError(f"provider rejected JSON-RPC method {method}")
        return outcome.result

    def request_many(
        self,
        calls: list[tuple[str, list[Any] | dict[str, Any]]],
    ) -> list[RpcOutcome]:
        if not calls:
            return []
        requests = []
        identifiers = []
        for method, params in calls:
            identifier = self._next_id
            self._next_id += 1
            identifiers.append(identifier)
            requests.append(
                {"jsonrpc": "2.0", "id": identifier, "method": method, "params": params}
            )
        self._limits.before_request(len(requests))
        payload: Any = requests[0] if len(requests) == 1 else requests
        parsed = self._post(dumps(payload))
        responses = parsed if isinstance(parsed, list) else [parsed]
        by_id: dict[int, RpcOutcome] = {}
        for response in responses:
            if not isinstance(response, dict):
                raise FormatError("provider JSON-RPC response must be an object")
            if response.get("jsonrpc") != "2.0":
                raise FormatError("provider JSON-RPC response has the wrong version")
            identifier = response.get("id")
            if not isinstance(identifier, int) or isinstance(identifier, bool):
                raise FormatError("provider JSON-RPC response has an invalid id")
            if identifier not in identifiers or identifier in by_id:
                raise FormatError(
                    "provider JSON-RPC response has an unknown or duplicate id"
                )
            has_result = "result" in response
            has_error = "error" in response
            if has_result == has_error:
                raise FormatError("provider JSON-RPC response needs exactly one outcome")
            by_id[identifier] = (
                RpcOutcome(result=response["result"])
                if has_result
                else RpcOutcome(error=sanitised_rpc_error(response["error"]))
            )
        if set(by_id) != set(identifiers):
            raise FormatError("provider JSON-RPC batch response is incomplete")
        return [by_id[identifier] for identifier in identifiers]

    def _post(self, body: bytes) -> Any:
        request = Request(self._url, data=body, headers=self._headers, method="POST")
        limit = self._limits.response_read_limit()
        try:
            with self._opener.open(
                request,
                timeout=self._limits.remaining_seconds(),
            ) as response:
                raw = response.read(limit + 1)
        except HTTPError as exc:
            exc.close()
            raise RpcTransportError("provider transport failed") from None
        except (URLError, OSError, TimeoutError):
            raise RpcTransportError("provider transport failed") from None
        self._limits.after_response(len(raw))
        if len(raw) > limit:
            raise RpcTransportError("provider response exceeded the capture byte limit")
        try:
            return loads(raw, max_bytes=limit)
        except FormatError:
            raise RpcTransportError("provider returned invalid JSON") from None
