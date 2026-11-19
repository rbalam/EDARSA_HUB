"""HTTP bridge from MCP to the certified EDARSAHUB semantic ingress."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping

from .oauth_pkce import OAuthValidationError, validate_scopes
from .oauth_security import SUPPORTED_SCOPES, _validate_resource

_SAFE_REASON_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,80}$")


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


class WorkerMcpAuthorizationError(WorkerMcpBackendError):
    """Explicit HTTP 401/403 authorization or insufficient-scope failure."""

    def __init__(
        self,
        code: str,
        *,
        status_code: int = 403,
        required_scope: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ):
        super().__init__(
            code,
            status_code=status_code,
            payload=payload,
        )
        self.required_scope = required_scope


class WorkerMcpValidationError(WorkerMcpBackendError):
    """Explicit HTTP 422/400 semantic or schema validation failure."""

    def __init__(
        self,
        code: str,
        *,
        status_code: int = 422,
        reason_code: str = "VALIDATION_ERROR",
        payload: Mapping[str, Any] | None = None,
    ):
        super().__init__(
            code,
            status_code=status_code,
            payload=payload,
        )
        self.reason_code = reason_code


def _extract_validation_reason(payload: Mapping[str, Any]) -> str:
    detail = payload.get("detail")
    if isinstance(detail, str) and detail.strip():
        candidate = detail.strip().split(":", 1)[0].strip().upper()
        if _SAFE_REASON_CODE_RE.fullmatch(candidate):
            return candidate
    if isinstance(detail, Mapping):
        state = str(detail.get("error_code") or detail.get("status") or "").strip().upper()
        if _SAFE_REASON_CODE_RE.fullmatch(state):
            return state
    if isinstance(detail, list):
        return "SCHEMA_VALIDATION_ERROR"
    return "VALIDATION_ERROR"


def extract_safe_validation_diagnostic(payload: Mapping[str, Any]) -> dict[str, str]:
    """Extract bounded secret-free field/correction hints from FastAPI 422/400 error payloads."""
    detail = payload.get("detail")
    out: dict[str, str] = {}
    if isinstance(detail, Mapping):
        for key in ("rejected_field", "capability", "classification", "allowed_correction"):
            val = detail.get(key)
            if isinstance(val, str) and val.strip():
                out[key] = val.strip()[:240]
    elif isinstance(detail, list) and detail:
        fields: list[str] = []
        for item in detail[:5]:
            if not isinstance(item, Mapping):
                continue
            loc = item.get("loc")
            if isinstance(loc, (list, tuple)) and loc:
                field_path = ".".join(str(part) for part in loc if str(part) != "body")
                if field_path and re.fullmatch(r"[A-Za-z0-9_.-]{1,120}", field_path):
                    fields.append(field_path)
        if fields:
            out["rejected_field"] = ",".join(fields)
        out["allowed_correction"] = (
            "Provide required WorkerObjectiveRequest fields (objective, bounded_context, mode, capability, constraints) "
            "without extra top-level keys."
        )
    return out


def _extract_auth_error(
    status_code: int,
    payload: Mapping[str, Any],
    default_required_scope: str,
) -> WorkerMcpAuthorizationError:
    if status_code == 401:
        return WorkerMcpAuthorizationError(
            "AUTHENTICATION_REQUIRED",
            status_code=401,
            payload=payload,
        )
    detail = payload.get("detail")
    if isinstance(detail, Mapping):
        err = str(detail.get("error") or "").strip().upper()
        if err == "INSUFFICIENT_SCOPE":
            raw_req = str(
                detail.get("required_scope") or default_required_scope
            ).strip()
            required_scope = (
                raw_req if raw_req in SUPPORTED_SCOPES else default_required_scope
            )
            return WorkerMcpAuthorizationError(
                "INSUFFICIENT_SCOPE",
                status_code=403,
                required_scope=required_scope,
                payload=payload,
            )
        state = str(detail.get("status") or "").strip().upper()
        if state == "REQUESTER_DENIED":
            return WorkerMcpAuthorizationError(
                "REQUESTER_DENIED",
                status_code=403,
                payload=payload,
            )
    return WorkerMcpAuthorizationError(
        "AUTHORIZATION_FORBIDDEN",
        status_code=403,
        payload=payload,
    )


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


def _probe_worker_access(
    *,
    backend_url: str,
    internal_token: str,
) -> bool:
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

    return _probe_worker_access(
        backend_url=backend_url,
        internal_token=internal_token,
    )


def verify_worker_access_grant(
    *,
    backend_url: str,
    token: str,
) -> dict[str, Any] | None:
    """Verify a bearer credential and extract its bounded OAuth/MCP scopes."""
    try:
        status_code, response = _request_json(
            method="POST",
            url=(
                backend_url.rstrip("/")
                + "/api/internal/worker/auth/exchange"
            ),
            token=token,
        )
    except WorkerMcpBackendError:
        return None

    access_token = str(response.get("access_token") or "").strip()
    if status_code != 200 or not access_token:
        return None

    raw_scope = response.get("scope")
    if isinstance(raw_scope, str) and raw_scope.strip():
        scope_str = raw_scope.strip()
    elif isinstance(response.get("scopes"), list) and all(
        isinstance(item, str) and item.strip()
        for item in response["scopes"]
    ):
        scope_str = " ".join(
            item.strip() for item in response["scopes"]
        )
    else:
        return None

    try:
        granted_scopes = validate_scopes(scope_str, SUPPORTED_SCOPES)
    except OAuthValidationError:
        return None

    expires_at_raw = response.get("expires_at")
    expires_at: int | None = None
    if expires_at_raw is not None:
        if isinstance(expires_at_raw, bool) or not isinstance(
            expires_at_raw, int
        ):
            return None
        if expires_at_raw <= int(time.time()):
            return None
        expires_at = expires_at_raw

    resource_raw = response.get("resource")
    resource: str | None = None
    if resource_raw is not None:
        if not isinstance(resource_raw, str) or not resource_raw.strip():
            return None
        try:
            _validate_resource(resource_raw.strip())
        except OAuthValidationError:
            return None
        resource = resource_raw.strip()

    try:
        probe_ok = _probe_worker_access(
            backend_url=backend_url,
            internal_token=access_token,
        )
    except WorkerMcpBackendError:
        return None
    if not probe_ok:
        return None

    return {
        "scopes": granted_scopes,
        "expires_at": expires_at,
        "resource": resource,
    }


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
        if status_code in (401, 403):
            raise _extract_auth_error(
                status_code,
                response,
                "worker:submit",
            )
        if status_code in (400, 422):
            raise WorkerMcpValidationError(
                "SEMANTIC_VALIDATION_FAILED",
                status_code=status_code,
                reason_code=_extract_validation_reason(response),
                payload=response,
            )
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
        if status_code in (401, 403):
            raise _extract_auth_error(
                status_code,
                response,
                "worker:status",
            )
        if status_code in (400, 422):
            raise WorkerMcpValidationError(
                "STATUS_VALIDATION_FAILED",
                status_code=status_code,
                reason_code=_extract_validation_reason(response),
                payload=response,
            )
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
