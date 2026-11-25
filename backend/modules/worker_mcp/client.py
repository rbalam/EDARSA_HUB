"""HTTP bridge from MCP to the certified EDARSAHUB semantic ingress."""
from __future__ import annotations

import json
import re
import socket
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


_RETRYABLE_503_STATES = frozenset(
    {"WRITER_BUSY", "CLAIM_BUSY", "REMOTE_MOVED_RETRYABLE", "BACKEND_UNREACHABLE"}
)
_KNOWN_503_STATES = _RETRYABLE_503_STATES | frozenset(
    {"RECOVERY_REQUIRED", "BLOCKED_CONVERGENCE"}
)
_SUBMIT_OBJECTIVE_TIMEOUT_SECONDS = 45.0


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


class WorkerMcpUpstreamUnavailableError(WorkerMcpBackendError):
    """Explicit HTTP 503 transient/convergence or HTTP 504 timeout failure."""

    def __init__(
        self,
        code: str,
        *,
        status_code: int = 503,
        reason_code: str = "UPSTREAM_UNAVAILABLE",
        retryable: bool = True,
        payload: Mapping[str, Any] | None = None,
    ):
        super().__init__(
            code,
            status_code=status_code,
            payload=payload,
        )
        self.reason_code = reason_code
        self.retryable = bool(retryable)


_SAFE_JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")
_SAFE_PUB_CATEGORIES = frozenset({
    "GIT_AUTH_FAILURE",
    "CONVERGENCE_FAILURE",
    "CONFLICT_OR_CONTENTION",
    "PUBLICATION_FAILURE",
})
_DIAG_SENSITIVE_MARKERS = (
    "ghp_", "gho_", "ghu_", "ghs_", "github_pat_", "bearer ",
    "password", "passwd", "secret", "token", "api_key", "apikey", "://",
)


def _sanitize_diagnostic_hint(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    text = " ".join(raw.strip().split())
    if not text:
        return None
    low = text.lower()
    if any(marker in low for marker in _DIAG_SENSITIVE_MARKERS):
        return None
    return text[:240]


def _extract_unavailable_reason(payload: Mapping[str, Any]) -> tuple[str, bool]:
    detail = payload.get("detail")
    candidate = ""
    if isinstance(detail, Mapping):
        candidate = str(detail.get("status") or detail.get("error_code") or "").strip().upper()
    elif isinstance(detail, str):
        candidate = detail.strip().split(":", 1)[0].strip().upper()
    if candidate in _KNOWN_503_STATES:
        return candidate, candidate in _RETRYABLE_503_STATES
    return "UPSTREAM_UNAVAILABLE", True


def extract_safe_publication_diagnostic(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Extract sanitized publication failure details (category, job_id, recoverability) without leaking secrets."""
    detail = payload.get("detail")
    out: dict[str, Any] = {}
    if not isinstance(detail, Mapping):
        return out

    raw_job = str(detail.get("job_id") or "").strip()
    pub_diag = detail.get("publication_diagnostic")
    if isinstance(pub_diag, Mapping):
        if not raw_job:
            raw_job = str(pub_diag.get("job_id") or "").strip()
        cat = str(pub_diag.get("category") or "").strip().upper()
        if cat in _SAFE_PUB_CATEGORIES:
            out["category"] = cat
        err = str(pub_diag.get("error_code") or "").strip().upper()
        if _SAFE_REASON_CODE_RE.fullmatch(err):
            out["error_code"] = err
        if isinstance(pub_diag.get("retryable"), bool):
            out["retryable"] = pub_diag["retryable"]
        if isinstance(pub_diag.get("recovery_required"), bool):
            out["recovery_required"] = pub_diag["recovery_required"]
        hint = _sanitize_diagnostic_hint(pub_diag.get("recommended_action"))
        if hint:
            out["recommended_action"] = hint
    else:
        state = str(detail.get("status") or "").strip().upper()
        raw_reason = str(detail.get("reason") or "").strip().upper()
        if any(
            m in raw_reason
            for m in ("COULD NOT READ USERNAME", "HTTP 401", "HTTP 403", "AUTHENTICATION FAILED", "CREDENTIAL")
        ):
            out["category"] = "GIT_AUTH_FAILURE"
            out["error_code"] = "GIT_AUTH_FAILED"
            out["retryable"] = False
            out["recovery_required"] = True
        elif state == "BLOCKED_CONVERGENCE" or "CONVERGENCE" in raw_reason or "DIVERGENCE" in raw_reason:
            out["category"] = "CONVERGENCE_FAILURE"
            out["error_code"] = "BLOCKED_CONVERGENCE"
            out["retryable"] = False
            out["recovery_required"] = True
        elif state in {"WRITER_BUSY", "CLAIM_BUSY", "REMOTE_MOVED_RETRYABLE"}:
            out["category"] = "CONFLICT_OR_CONTENTION"
            out["error_code"] = state
            out["retryable"] = True
            out["recovery_required"] = False
        elif "IDEMPOTENCY_CONFLICT" in raw_reason or "RESIDUAL" in raw_reason:
            out["category"] = "CONFLICT_OR_CONTENTION"
            out["error_code"] = "JOB_DRAFT_IDEMPOTENCY_CONFLICT" if "IDEMPOTENCY_CONFLICT" in raw_reason else "QUEUE_PUBLISHER_RESIDUAL_CONFLICT"
            out["retryable"] = False
            out["recovery_required"] = True
        elif state == "RECOVERY_REQUIRED":
            out["category"] = "PUBLICATION_FAILURE"
            out["error_code"] = "PUSH_FAILED" if "PUSH_FAILED" in raw_reason else "RECOVERY_REQUIRED"
            out["retryable"] = False
            out["recovery_required"] = True

    if raw_job and _SAFE_JOB_ID_RE.fullmatch(raw_job):
        out["job_id"] = raw_job
    return out


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
        raw_http = detail.get("http_status")
        if isinstance(raw_http, int) and not isinstance(raw_http, bool) and 400 <= raw_http <= 599:
            out["http_status"] = str(raw_http)
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
    except (TimeoutError, socket.timeout) as exc:
        raise WorkerMcpUpstreamUnavailableError(
            "UPSTREAM_TIMEOUT",
            status_code=504,
            reason_code="UPSTREAM_TIMEOUT",
            retryable=True,
        ) from exc
    except urllib.error.URLError as exc:
        if isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout)):
            raise WorkerMcpUpstreamUnavailableError(
                "UPSTREAM_TIMEOUT",
                status_code=504,
                reason_code="UPSTREAM_TIMEOUT",
                retryable=True,
            ) from exc
        raise WorkerMcpUpstreamUnavailableError(
            "BACKEND_UNREACHABLE",
            status_code=503,
            reason_code="BACKEND_UNREACHABLE",
            retryable=True,
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
        timeout=_SUBMIT_OBJECTIVE_TIMEOUT_SECONDS,
    )
    if status_code != 202:
        if status_code in (401, 403):
            raise _extract_auth_error(
                status_code,
                response,
                "worker:submit",
            )
        if status_code in (400, 409, 422):
            raise WorkerMcpValidationError(
                "SEMANTIC_VALIDATION_FAILED",
                status_code=status_code,
                reason_code=_extract_validation_reason(response),
                payload=response,
            )
        if status_code == 503:
            reason_code, retryable = _extract_unavailable_reason(response)
            raise WorkerMcpUpstreamUnavailableError(
                "SEMANTIC_SUBMIT_UNAVAILABLE",
                status_code=503,
                reason_code=reason_code,
                retryable=retryable,
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


def _handle_readonly_status_error(
    status_code: int,
    response: Mapping[str, Any],
    *,
    error_code: str,
) -> None:
    if status_code in (401, 403):
        raise _extract_auth_error(
            status_code,
            response,
            "worker:status",
        )
    if status_code in (400, 409, 422):
        raise WorkerMcpValidationError(
            f"{error_code}_VALIDATION_FAILED",
            status_code=status_code,
            reason_code=_extract_validation_reason(response),
            payload=response,
        )
    if status_code == 503:
        reason_code, retryable = _extract_unavailable_reason(response)
        raise WorkerMcpUpstreamUnavailableError(
            f"{error_code}_UNAVAILABLE",
            status_code=503,
            reason_code=reason_code,
            retryable=retryable,
            payload=response,
        )
    raise WorkerMcpBackendError(
        f"{error_code}_FAILED",
        status_code=status_code,
        payload=response,
    )


def get_go_context(
    *,
    backend_url: str,
    token: str,
    domain: str,
    project: str = "EDARSAHUB",
    chain_id: str | None = None,
    objective_hint: str | None = None,
) -> dict[str, Any]:
    internal_token = exchange_service_credential(
        backend_url=backend_url,
        credential=token,
    )
    query: dict[str, str] = {"domain": domain, "project": project or "EDARSAHUB"}
    if chain_id:
        query["chain_id"] = chain_id
    if objective_hint:
        query["objective_hint"] = objective_hint
    status_code, response = _request_json(
        method="GET",
        url=(
            backend_url.rstrip("/")
            + "/api/internal/worker/context?"
            + urllib.parse.urlencode(query)
        ),
        token=internal_token,
    )
    if status_code != 200:
        _handle_readonly_status_error(status_code, response, error_code="GO_CONTEXT_READ")
    return response


def list_capabilities(
    *,
    backend_url: str,
    token: str,
) -> dict[str, Any]:
    internal_token = exchange_service_credential(
        backend_url=backend_url,
        credential=token,
    )
    status_code, response = _request_json(
        method="GET",
        url=backend_url.rstrip("/") + "/api/internal/worker/capabilities",
        token=internal_token,
    )
    if status_code != 200:
        _handle_readonly_status_error(status_code, response, error_code="CAPABILITIES_READ")
    return response


def preflight_objective(
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
        url=backend_url.rstrip("/") + "/api/internal/worker/objectives/preflight",
        token=internal_token,
        payload=payload,
    )
    if status_code != 200:
        _handle_readonly_status_error(status_code, response, error_code="OBJECTIVE_PREFLIGHT")
    return response


def get_runtime_convergence(
    *,
    backend_url: str,
    token: str,
) -> dict[str, Any]:
    internal_token = exchange_service_credential(
        backend_url=backend_url,
        credential=token,
    )
    status_code, response = _request_json(
        method="GET",
        url=backend_url.rstrip("/") + "/api/internal/worker/runtime-convergence",
        token=internal_token,
    )
    if status_code != 200:
        _handle_readonly_status_error(status_code, response, error_code="RUNTIME_CONVERGENCE_READ")
    return response
