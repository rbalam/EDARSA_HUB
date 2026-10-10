"""HTTP bridge from MCP to the certified EDARSAHUB semantic ingress."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping


class WorkerMcpBackendError(RuntimeError):
    def __init__(
        self,
        code: str,
        *,
        status_code: int | None = None,
        payload: Mapping[str, Any] | None = None,
    ):
        super().__init__(code)
        self.code = code
        self.status_code = status_code
        self.payload = dict(payload or {})


def _request_json(
    *,
    method: str,
    url: str,
    token: str,
    payload: Mapping[str, Any] | None = None,
    timeout: float = 15.0,
) -> tuple[int, dict[str, Any]]:
    body = None
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    if payload is not None:
        body = json.dumps(
            dict(payload),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            raw = response.read()
            status_code = int(response.status)
    except urllib.error.HTTPError as exc:
        status_code = int(exc.code)
        raw = exc.read()
    except urllib.error.URLError as exc:
        raise WorkerMcpBackendError(
            "BACKEND_UNREACHABLE",
        ) from exc

    try:
        decoded = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        decoded = {}

    return status_code, decoded if isinstance(decoded, dict) else {}


def exchange_service_credential(
    *,
    backend_url: str,
    credential: str,
) -> str:
    status_code, response = _request_json(
        method="POST",
        url=(
            backend_url.rstrip("/")
            + "/api/internal/worker/auth/exchange"
        ),
        token=credential,
    )
    access_token = str(response.get("access_token") or "").strip()
    if status_code != 200 or not access_token:
        raise WorkerMcpBackendError(
            "SERVICE_CREDENTIAL_EXCHANGE_FAILED",
            status_code=status_code,
            payload=response,
        )
    return access_token


def verify_worker_access(
    *,
    backend_url: str,
    token: str,
) -> bool:
    try:
        internal_token = exchange_service_credential(
            backend_url=backend_url,
            credential=token,
        )
    except WorkerMcpBackendError:
        return False

    status_code, payload = _request_json(
        method="GET",
        url=(
            backend_url.rstrip("/")
            + "/api/internal/worker/jobs/MCP-AUTH-PROBE"
        ),
        token=internal_token,
    )
    if status_code == 200:
        return True
    if status_code == 404:
        detail = payload.get("detail")
        if isinstance(detail, Mapping):
            return str(
                detail.get("lifecycle") or ""
            ).upper() == "NOT_FOUND"
    return False


def submit_objective(
    *,
    backend_url: str,
    token: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    internal_token = exchange_service_credential(
        backend_url=backend_url,
        credential=token,
    )
    status_code, response = _request_json(
        method="POST",
        url=(
            backend_url.rstrip("/")
            + "/api/internal/worker/objectives"
        ),
        token=internal_token,
        payload=payload,
    )
    if status_code != 202:
        raise WorkerMcpBackendError(
            "SEMANTIC_SUBMIT_FAILED",
            status_code=status_code,
            payload=response,
        )
    return response


def get_job_status(
    *,
    backend_url: str,
    token: str,
    job_id: str,
) -> dict[str, Any]:
    internal_token = exchange_service_credential(
        backend_url=backend_url,
        credential=token,
    )
    status_code, response = _request_json(
        method="GET",
        url=(
            backend_url.rstrip("/")
            + "/api/internal/worker/jobs/"
            + urllib.parse.quote(job_id, safe="")
        ),
        token=internal_token,
    )
    if status_code not in (200, 404):
        raise WorkerMcpBackendError(
            "STATUS_READ_FAILED",
            status_code=status_code,
            payload=response,
        )

    if status_code == 404:
        detail = response.get("detail")
        if isinstance(detail, Mapping):
            return dict(detail)
    return response
