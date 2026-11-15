from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from mcp import Client
from mcp.server.auth.provider import AccessToken

from worker_mcp import auth, client, server
from worker_mcp.config import (
    WorkerMcpConfig,
    WorkerMcpConfigError,
)
from worker_mcp.oauth_pkce import OAuthValidationError
from worker_mcp.oauth_security import (
    SUPPORTED_SCOPES,
    require_tool_scope,
    validate_grant,
)

ROOT = Path(__file__).resolve().parents[2]
GATEWAY = ROOT / "backend/modules/worker_mcp/gateway_router.py"


def _config() -> WorkerMcpConfig:
    return WorkerMcpConfig(
        issuer_url="https://auth.example.test",
        resource_url="https://mcp.example.test/mcp",
        backend_url="https://hub.example.test",
        allowed_hosts=("mcp.example.test",),
        allowed_origins=("https://chat.example.test",),
    )


def _access_token() -> AccessToken:
    return AccessToken(
        token="opaque-test-token",
        client_id="edarsahub-authenticated-user",
        scopes=["worker:submit", "worker:status"],
        resource="https://mcp.example.test/mcp",
    )


@pytest.mark.asyncio
async def test_mcp_exposes_exactly_two_public_tools():
    mcp = server.build_mcp_server(_config())

    async with Client(mcp) as mcp_client:
        result = await mcp_client.list_tools()

    assert {tool.name for tool in result.tools} == {
        "submit_objective",
        "get_job_status",
    }


def test_config_fails_closed_without_required_env(monkeypatch):
    for name in (
        "EDARSAHUB_MCP_ISSUER_URL",
        "EDARSAHUB_MCP_RESOURCE_URL",
        "EDARSAHUB_MCP_BACKEND_URL",
        "EDARSAHUB_MCP_ALLOWED_HOSTS",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(
        WorkerMcpConfigError,
        match="REQUIRED_ENV_MISSING",
    ):
        WorkerMcpConfig.from_env()


@pytest.mark.asyncio
async def test_token_verifier_delegates_auth_to_canonical_ingress(
    monkeypatch,
):
    monkeypatch.setattr(
        auth,
        "verify_worker_access",
        lambda *, backend_url, token: (
            backend_url == "https://hub.example.test"
            and token == "opaque-test-token"
        ),
    )

    verifier = auth.EdarsahubTokenVerifier(
        backend_url="https://hub.example.test",
        resource_url="https://mcp.example.test/mcp",
    )

    token = await verifier.verify_token("opaque-test-token")

    assert token is not None
    assert token.scopes == [
        "worker:submit",
        "worker:status",
    ]


@pytest.mark.asyncio
async def test_token_verifier_fails_closed(monkeypatch):
    monkeypatch.setattr(
        auth,
        "verify_worker_access",
        lambda **kwargs: False,
    )

    verifier = auth.EdarsahubTokenVerifier(
        backend_url="https://hub.example.test",
        resource_url="https://mcp.example.test/mcp",
    )

    assert await verifier.verify_token("denied-token") is None


def test_submit_tool_delegates_only_to_semantic_ingress(monkeypatch):
    server.build_mcp_server(_config())
    monkeypatch.setattr(
        server,
        "get_access_token",
        _access_token,
    )

    captured: dict[str, Any] = {}

    def fake_submit(*, backend_url, token, payload):
        captured["backend_url"] = backend_url
        captured["token"] = token
        captured["payload"] = payload
        return {
            "status": "SUBMITTED",
            "job_id": "SEM-TEST-1",
            "capability": "READ_ONLY_CANARY",
            "bounded_context": "WORKER_INGRESS",
            "production_touched": False,
        }

    monkeypatch.setattr(
        server,
        "backend_submit_objective",
        fake_submit,
    )

    result = server.submit_objective_tool(
        objective="Canary",
        bounded_context="WORKER_INGRESS",
        mode="READ_ONLY",
        capability="READ_ONLY_CANARY",
        request_key="mcp-test-1",
        constraints={},
    )

    assert result["status"] == "SUBMITTED"
    assert result["production_touched"] is False
    assert captured["backend_url"] == "https://hub.example.test"
    assert captured["token"] == "opaque-test-token"
    assert set(captured["payload"]) == {
        "objective",
        "bounded_context",
        "mode",
        "capability",
        "constraints",
        "request_key",
    }
    assert "actions" not in captured["payload"]
    assert "checks" not in captured["payload"]


def test_status_tool_delegates_to_canonical_status_endpoint(monkeypatch):
    server.build_mcp_server(_config())
    monkeypatch.setattr(
        server,
        "get_access_token",
        _access_token,
    )
    monkeypatch.setattr(
        server,
        "backend_get_job_status",
        lambda *, backend_url, token, job_id: {
            "job_id": job_id,
            "lifecycle": "RESULT",
            "status": "READ_ONLY_COMPLETE",
            "quality_gate": "PASS",
            "certification": "CERTIFIED_READ_ONLY",
            "tests": "PASS",
            "percent_complete": 100,
            "blockers": [],
            "files_changed": [],
            "production_touched": False,
        },
    )

    result = server.get_job_status_tool("SEM-TEST-1")

    assert result["quality_gate"] == "PASS"
    assert result["production_touched"] is False


def test_backend_client_auth_probe_accepts_only_canonical_404_shape(
    monkeypatch,
):
    monkeypatch.setattr(
        client,
        "exchange_service_credential",
        lambda *, backend_url, credential: "short-internal-jwt",
    )
    monkeypatch.setattr(
        client,
        "_request_json",
        lambda **kwargs: (
            404,
            {
                "detail": {
                    "job_id": "MCP-AUTH-PROBE",
                    "lifecycle": "NOT_FOUND",
                    "status": "NOT_FOUND",
                    "production_touched": False,
                }
            },
        ),
    )

    assert client.verify_worker_access(
        backend_url="https://hub.example.test",
        token="opaque-test-token",
    ) is True


def test_adapter_has_no_dangerous_low_level_surface():
    text = open(
        server.__file__,
        encoding="utf-8",
    ).read().lower()

    for forbidden in (
        "submit_job(",
        "subprocess",
        "os.system",
        "git push",
        "worker_runtime_wake",
        "receive_queue",
        "dispatch_job",
        "pymssql.connect",
        "pyodbc.connect",
    ):
        assert forbidden not in text


def test_backend_client_exchanges_service_credential_before_auth_probe(
    monkeypatch,
):
    calls = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        if kwargs["url"].endswith("/api/internal/worker/auth/exchange"):
            assert kwargs["token"] == "opaque-service-credential"
            return 200, {
                "access_token": "short-internal-jwt",
                "token_type": "Bearer",
                "expires_in": 900,
            }
        assert kwargs["token"] == "short-internal-jwt"
        return 404, {
            "detail": {
                "job_id": "MCP-AUTH-PROBE",
                "lifecycle": "NOT_FOUND",
                "status": "NOT_FOUND",
                "production_touched": False,
            }
        }

    monkeypatch.setattr(client, "_request_json", fake_request)

    assert client.verify_worker_access(
        backend_url="https://hub.example.test",
        token="opaque-service-credential",
    ) is True
    assert len(calls) == 2


def test_backend_client_fails_closed_when_exchange_is_denied(
    monkeypatch,
):
    monkeypatch.setattr(
        client,
        "_request_json",
        lambda **kwargs: (
            401,
            {"detail": "SERVICE_CREDENTIAL_INVALID"},
        ),
    )

    assert client.verify_worker_access(
        backend_url="https://hub.example.test",
        token="denied-service-credential",
    ) is False


def test_status_exchanges_service_credential_before_canonical_read(
    monkeypatch,
):
    calls = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        if kwargs["url"].endswith("/api/internal/worker/auth/exchange"):
            return 200, {"access_token": "short-internal-jwt"}
        assert kwargs["token"] == "short-internal-jwt"
        return 200, {
            "job_id": "SEM-TEST-1",
            "lifecycle": "RESULT",
            "status": "READ_ONLY_COMPLETE",
            "production_touched": False,
        }

    monkeypatch.setattr(client, "_request_json", fake_request)

    result = client.get_job_status(
        backend_url="https://hub.example.test",
        token="opaque-service-credential",
        job_id="SEM-TEST-1",
    )

    assert result["lifecycle"] == "RESULT"
    assert len(calls) == 2



def test_gateway_publishes_standard_and_legacy_protected_resource_metadata_routes():
    text = GATEWAY.read_text(encoding="utf-8")
    assert '"/.well-known/oauth-protected-resource/api/mcp"' in text
    assert '"/api/mcp/.well-known/oauth-protected-resource"' in text
    assert "protected_resource_metadata(" in text
    assert 'origin + "/api/mcp"' in text
    assert 'origin + "/api/mcp/oauth"' in text


def test_gateway_advertises_reachable_public_metadata_uri():
    text = GATEWAY.read_text(encoding="utf-8")
    assert '"/api/mcp/.well-known/oauth-protected-resource"' in text
    assert "public_https_origin(request)" in text
    assert "except PublicOriginError" in text
    assert '"/api/mcp/.well-known/oauth-protected-resource"' in text
    assert 'origin + "/api/mcp/oauth"' in text


def test_gateway_metadata_is_owned_by_public_gateway_not_loopback_upstream():
    text = GATEWAY.read_text(encoding="utf-8")
    metadata_block = text.split("_ALLOWED_RESPONSE_HEADERS", 1)[0]
    assert "origin = public_https_origin(request)" in metadata_block
    assert "MCP_PUBLIC_ORIGIN_UNAVAILABLE" in metadata_block
    assert 'origin + "/api/mcp"' in metadata_block
    assert 'origin + "/api/mcp/oauth"' in metadata_block
    assert 'upstream + "/.well-known/oauth-protected-resource"' not in metadata_block

def test_refresh_token_session_types_are_isolated_from_mcp_service():
    root = Path(__file__).resolve().parents[2]
    refresh_text = (root / "backend/core/refresh_tokens.py").read_text(encoding="utf-8")
    routes_text = (root / "backend/modules/auth/routes.py").read_text(encoding="utf-8")

    assert "expected_user_type: Optional[str] = None" in refresh_text
    assert "FechaRevocacion IS NULL" in refresh_text
    assert "LOWER(LTRIM(RTRIM(ISNULL(TipoUsuario, ''))))" in refresh_text
    assert routes_text.count(
        'validate_and_get_session(refresh_token, expected_user_type="interno")'
    ) == 2
    assert 'expected_user_type="interno"' in routes_text
    assert 'user_type="interno"' in routes_text


@pytest.mark.asyncio
async def test_token_verifier_preserves_narrow_status_scope_without_elevation(
    monkeypatch,
):
    def fake_request(**kwargs):
        if kwargs["url"].endswith("/api/internal/worker/auth/exchange"):
            return 200, {
                "access_token": "short-internal-jwt",
                "token_type": "Bearer",
                "expires_in": 900,
                "scope": "worker:status",
                "scopes": ["worker:status"],
                "resource": "https://mcp.example.test/api/mcp",
            }
        return 404, {
            "detail": {
                "job_id": "MCP-AUTH-PROBE",
                "lifecycle": "NOT_FOUND",
                "status": "NOT_FOUND",
                "production_touched": False,
            }
        }

    monkeypatch.setattr(client, "_request_json", fake_request)
    verifier = auth.EdarsahubTokenVerifier(
        backend_url="https://hub.example.test",
        resource_url="http://127.0.0.1:32913/mcp",
    )

    verified = await verifier.verify_token("status-only-token")
    assert verified is not None
    assert verified.scopes == ["worker:status"]
    assert "worker:submit" not in verified.scopes


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exchange_payload",
    [
        {"access_token": "short-internal-jwt"},
        {"access_token": "short-internal-jwt", "scope": ""},
        {"access_token": "short-internal-jwt", "scope": "worker:admin"},
        {
            "access_token": "short-internal-jwt",
            "scope": "worker:status",
            "expires_at": 1,
        },
        {
            "access_token": "short-internal-jwt",
            "scope": "worker:status",
            "resource": "http://insecure.example.test/api/mcp",
        },
    ],
)
async def test_token_verifier_fails_closed_on_missing_invalid_or_expired_grant(
    monkeypatch,
    exchange_payload,
):
    monkeypatch.setattr(
        client,
        "_request_json",
        lambda **kwargs: (200, exchange_payload),
    )
    verifier = auth.EdarsahubTokenVerifier(
        backend_url="https://hub.example.test",
        resource_url="https://mcp.example.test/mcp",
    )
    assert await verifier.verify_token("bad-grant-token") is None


def test_status_only_access_token_cannot_call_submit_objective_tool(monkeypatch):
    server.build_mcp_server(_config())
    monkeypatch.setattr(
        server,
        "get_access_token",
        lambda: AccessToken(
            token="status-only-token",
            client_id="edarsahub-authenticated-user",
            scopes=["worker:status"],
            resource="https://mcp.example.test/mcp",
        ),
    )
    called = {"submit": False}
    monkeypatch.setattr(
        server,
        "backend_submit_objective",
        lambda **kwargs: called.__setitem__("submit", True),
    )

    with pytest.raises(
        PermissionError,
        match="MCP_SCOPE_FORBIDDEN:INSUFFICIENT_SCOPE",
    ):
        server.submit_objective_tool(
            objective="Should fail closed",
            bounded_context="WORKER_INGRESS",
            mode="READ_ONLY",
            capability="READ_ONLY_CANARY",
        )
    assert called["submit"] is False


def test_submit_only_access_token_cannot_call_get_job_status_tool(monkeypatch):
    server.build_mcp_server(_config())
    monkeypatch.setattr(
        server,
        "get_access_token",
        lambda: AccessToken(
            token="submit-only-token",
            client_id="edarsahub-authenticated-user",
            scopes=["worker:submit"],
            resource="https://mcp.example.test/mcp",
        ),
    )
    called = {"status": False}
    monkeypatch.setattr(
        server,
        "backend_get_job_status",
        lambda **kwargs: called.__setitem__("status", True),
    )

    with pytest.raises(
        PermissionError,
        match="MCP_SCOPE_FORBIDDEN:INSUFFICIENT_SCOPE",
    ):
        server.get_job_status_tool("SEM-TEST-1")
    assert called["status"] is False


def _grant(**changes):
    resource = "https://erp-crm-enterprise-1.preview.emergentagent.com/api/mcp"
    args = dict(
        requested_scopes="worker:status",
        identity_scopes=frozenset({"worker:status"}),
        consented_scopes=frozenset({"worker:status"}),
        resource=resource,
        registered_resource=resource,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        revoked=False,
    )
    args.update(changes)
    return validate_grant(**args)


def test_oauth_security_valid_grants_and_mutual_scope_isolation():
    assert _grant() == frozenset({"worker:status"})
    assert _grant(
        requested_scopes="worker:status worker:submit",
        identity_scopes=SUPPORTED_SCOPES,
        consented_scopes=SUPPORTED_SCOPES,
    ) == SUPPORTED_SCOPES

    require_tool_scope("worker:status", frozenset({"worker:status"}))
    require_tool_scope("worker:submit", frozenset({"worker:submit"}))

    with pytest.raises(OAuthValidationError, match="INSUFFICIENT_SCOPE"):
        require_tool_scope("worker:submit", frozenset({"worker:status"}))
    with pytest.raises(OAuthValidationError, match="INSUFFICIENT_SCOPE"):
        require_tool_scope("worker:status", frozenset({"worker:submit"}))
    with pytest.raises(OAuthValidationError, match="TOOL_SCOPE_NOT_CONFIGURED"):
        require_tool_scope("worker:admin", frozenset({"worker:admin"}))
    with pytest.raises(OAuthValidationError, match="INSUFFICIENT_SCOPE"):
        require_tool_scope("worker:status", None)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "changes,expected_code",
    [
        ({"revoked": True}, "GRANT_REVOKED"),
        (
            {"expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)},
            "GRANT_EXPIRED",
        ),
        (
            {"expires_at": datetime.now() + timedelta(minutes=5)},
            "EXPIRATION_INVALID",
        ),
        ({"consented_scopes": frozenset()}, "CONSENT_REQUIRED"),
        ({"consented_scopes": {"worker:status"}}, "CONSENT_REQUIRED"),
        ({"requested_scopes": "worker:submit"}, "SCOPES_FORBIDDEN"),
        ({"resource": "https://example.org/api/mcp"}, "RESOURCE_MISMATCH"),
        (
            {
                "resource": "http://example.org/api/mcp",
                "registered_resource": "http://example.org/api/mcp",
            },
            "RESOURCE_INVALID",
        ),
        (
            {
                "resource": "https://example.org/api/mcp/",
                "registered_resource": "https://example.org/api/mcp/",
            },
            "RESOURCE_INVALID",
        ),
        (
            {
                "resource": "https://example.org/api/mcp?x=1",
                "registered_resource": "https://example.org/api/mcp?x=1",
            },
            "RESOURCE_INVALID",
        ),
        (
            {
                "resource": "https://example.org:99999/api/mcp",
                "registered_resource": "https://example.org:99999/api/mcp",
            },
            "RESOURCE_INVALID",
        ),
    ],
)
def test_oauth_security_invalid_grants_fail_closed(changes, expected_code):
    with pytest.raises(OAuthValidationError, match=expected_code):
        _grant(**changes)


class _StaticTokenVerifier:
    def __init__(self, tokens: dict[str, AccessToken]):
        self._tokens = tokens

    async def verify_token(self, token: str) -> AccessToken | None:
        return self._tokens.get(token)


async def _invoke_asgi_http(
    asgi_app: Any,
    *,
    method: str = "POST",
    path: str = "/mcp",
    bearer_token: str | None = None,
    json_body: Any | None = None,
    host: str = "mcp.example.test",
) -> tuple[int, dict[str, str], dict[str, Any]]:
    import json as _json

    raw_body = (
        _json.dumps(json_body).encode("utf-8")
        if json_body is not None
        else b""
    )
    headers: list[tuple[bytes, bytes]] = [
        (b"host", host.encode("ascii")),
        (b"accept", b"application/json, text/event-stream"),
    ]
    if json_body is not None:
        headers.append((b"content-type", b"application/json"))
        headers.append(
            (b"content-length", str(len(raw_body)).encode("ascii"))
        )
    if bearer_token is not None:
        headers.append(
            (b"authorization", f"Bearer {bearer_token}".encode("utf-8"))
        )

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "https",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 50000),
        "server": ("127.0.0.1", 32913),
    }

    sent_body = False

    async def receive() -> dict[str, Any]:
        nonlocal sent_body
        if not sent_body:
            sent_body = True
            return {
                "type": "http.request",
                "body": raw_body,
                "more_body": False,
            }
        return {"type": "http.disconnect"}

    resp_status = 0
    resp_headers: dict[str, str] = {}
    resp_chunks: list[bytes] = []

    async def send(event: dict[str, Any]) -> None:
        nonlocal resp_status
        if event.get("type") == "http.response.start":
            resp_status = int(event["status"])
            for k, v in event.get("headers") or []:
                resp_headers[k.decode("latin1").lower()] = v.decode("latin1")
        elif event.get("type") == "http.response.body":
            resp_chunks.append(event.get("body", b"") or b"")

    await asgi_app(scope, receive, send)
    body_bytes = b"".join(resp_chunks)
    parsed = _json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    return resp_status, resp_headers, parsed


@pytest.mark.asyncio
async def test_gate3l_http_boundary_401_403_stepup_and_200_separation(
    monkeypatch,
):
    tokens = {
        "tok-status": AccessToken(
            token="tok-status",
            client_id="chatgpt-client",
            scopes=["worker:status"],
            resource="https://mcp.example.test/mcp",
        ),
        "tok-submit-only": AccessToken(
            token="tok-submit-only",
            client_id="chatgpt-client",
            scopes=["worker:submit"],
            resource="https://mcp.example.test/mcp",
        ),
        "tok-both": AccessToken(
            token="tok-both",
            client_id="chatgpt-client",
            scopes=["worker:status", "worker:submit"],
            resource="https://mcp.example.test/mcp",
        ),
    }
    cfg = _config()
    mcp_srv = server.build_mcp_server(
        cfg,
        token_verifier=_StaticTokenVerifier(tokens),
    )
    http_app = mcp_srv.streamable_http_app(
        json_response=True,
        stateless_http=True,
        transport_security=server.build_transport_security(cfg),
    )

    submit_calls: list[dict[str, Any]] = []

    def fake_submit(*, backend_url: str, token: str, payload: dict[str, Any]):
        if payload.get("capability") == "UNAPPROVED_CAPABILITY":
            raise client.WorkerMcpValidationError(
                "SEMANTIC_VALIDATION_FAILED",
                status_code=422,
                reason_code="SEMANTIC_CAPABILITY_UNKNOWN",
                payload={"detail": "SEMANTIC_CAPABILITY_UNKNOWN"},
            )
        submit_calls.append({"token": token, "payload": payload})
        return {
            "status": "SUBMITTED",
            "job_id": "SEM-GATE3L-001",
            "capability": payload["capability"],
            "bounded_context": payload["bounded_context"],
            "production_touched": False,
        }

    monkeypatch.setattr(server, "backend_submit_objective", fake_submit)
    monkeypatch.setattr(
        server,
        "backend_get_job_status",
        lambda *, backend_url, token, job_id: {
            "job_id": job_id,
            "lifecycle": "RESULT",
            "status": "READ_ONLY_COMPLETE",
            "quality_gate": "PASS",
            "certification": "CERTIFIED_READ_ONLY",
            "tests": "PASS",
            "percent_complete": 100,
            "production_touched": False,
        },
    )

    async with mcp_srv.session_manager.run():
        # 1. Unauthenticated -> HTTP 401 advertising worker:status worker:submit
        st_401, hdr_401, body_401 = await _invoke_asgi_http(
            http_app,
            bearer_token=None,
            json_body={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )
        assert st_401 == 401
        assert body_401["error"] == "invalid_token"
        assert 'error="invalid_token"' in hdr_401["www-authenticate"]
        assert 'resource_metadata="' in hdr_401["www-authenticate"]
        assert (
            'scope="worker:status worker:submit"'
            in hdr_401["www-authenticate"]
        )

        # 2. worker:status token -> get_job_status returns HTTP 200 OK
        st_ok, hdr_ok, body_ok = await _invoke_asgi_http(
            http_app,
            bearer_token="tok-status",
            json_body={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_job_status",
                    "arguments": {"job_id": "SEM-GATE3L-001"},
                },
            },
        )
        assert st_ok == 200
        assert "www-authenticate" not in hdr_ok
        assert body_ok["result"].get("isError") is not True
        assert (
            body_ok["result"]["structuredContent"]["status"]
            == "READ_ONLY_COMPLETE"
        )

        # 3. worker:status token -> submit_objective returns HTTP 403 insufficient_scope
        st_403, hdr_403, body_403 = await _invoke_asgi_http(
            http_app,
            bearer_token="tok-status",
            json_body={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "submit_objective",
                    "arguments": {
                        "objective": "Test step-up challenge",
                        "bounded_context": "WORKER_INGRESS",
                        "mode": "READ_ONLY",
                        "capability": "READ_ONLY_CANARY",
                    },
                },
            },
        )
        assert st_403 == 403
        assert body_403["error"] == "insufficient_scope"
        assert body_403["required_scope"] == "worker:submit"
        assert body_403["code"] == "INSUFFICIENT_SCOPE"
        assert 'error="insufficient_scope"' in hdr_403["www-authenticate"]
        assert 'resource_metadata="' in hdr_403["www-authenticate"]
        assert (
            'scope="worker:status worker:submit"'
            in hdr_403["www-authenticate"]
        )
        assert submit_calls == []

        # 4. Batch JSON-RPC containing submit_objective with worker:status also fails closed 403
        st_batch, _, _ = await _invoke_asgi_http(
            http_app,
            bearer_token="tok-status",
            json_body=[
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "get_job_status",
                        "arguments": {"job_id": "SEM-GATE3L-001"},
                    },
                },
                {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {
                        "name": "submit_objective",
                        "arguments": {
                            "objective": "Batch bypass attempt",
                            "bounded_context": "WORKER_INGRESS",
                            "mode": "READ_ONLY",
                            "capability": "READ_ONLY_CANARY",
                        },
                    },
                },
            ],
        )
        assert st_batch == 403
        assert submit_calls == []

        # 5. worker:submit-only token -> get_job_status returns HTTP 403 insufficient_scope
        st_stat_403, hdr_stat_403, body_stat_403 = await _invoke_asgi_http(
            http_app,
            bearer_token="tok-submit-only",
            json_body={
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "get_job_status",
                    "arguments": {"job_id": "SEM-GATE3L-001"},
                },
            },
        )
        assert st_stat_403 == 403
        assert body_stat_403["required_scope"] == "worker:status"
        assert (
            'scope="worker:status worker:submit"'
            in hdr_stat_403["www-authenticate"]
        )

        # 6. worker:status + worker:submit + HTTP 422 validation error -> HTTP 200 ToolError (NOT 403)
        st_422, hdr_422, body_422 = await _invoke_asgi_http(
            http_app,
            bearer_token="tok-both",
            json_body={
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {
                    "name": "submit_objective",
                    "arguments": {
                        "objective": "Invalid capability test",
                        "bounded_context": "WORKER_INGRESS",
                        "mode": "READ_ONLY",
                        "capability": "UNAPPROVED_CAPABILITY",
                    },
                },
            },
        )
        assert st_422 == 200
        assert "www-authenticate" not in hdr_422
        assert body_422["result"]["isError"] is True
        err_text = body_422["result"]["content"][0]["text"]
        assert "VALIDATION_ERROR_422:SEMANTIC_CAPABILITY_UNKNOWN" in err_text
        assert submit_calls == []

        # 7. worker:status + worker:submit + valid payload -> HTTP 200 SUBMITTED
        st_sub_ok, _, body_sub_ok = await _invoke_asgi_http(
            http_app,
            bearer_token="tok-both",
            json_body={
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "submit_objective",
                    "arguments": {
                        "objective": "Valid canary objective",
                        "bounded_context": "WORKER_INGRESS",
                        "mode": "READ_ONLY",
                        "capability": "READ_ONLY_CANARY",
                    },
                },
            },
        )
        assert st_sub_ok == 200
        assert body_sub_ok["result"].get("isError") is not True
        assert (
            body_sub_ok["result"]["structuredContent"]["status"]
            == "SUBMITTED"
        )
        assert len(submit_calls) == 1


def test_client_differentiates_http_403_auth_from_http_422_validation(
    monkeypatch,
):
    monkeypatch.setattr(
        client,
        "exchange_service_credential",
        lambda *, backend_url, credential: "short-internal-jwt",
    )

    # 403 insufficient_scope -> WorkerMcpAuthorizationError(INSUFFICIENT_SCOPE)
    monkeypatch.setattr(
        client,
        "_request_json",
        lambda **kwargs: (
            403,
            {
                "detail": {
                    "error": "INSUFFICIENT_SCOPE",
                    "required_scope": "worker:submit",
                    "code": "INSUFFICIENT_SCOPE",
                }
            },
        ),
    )
    with pytest.raises(client.WorkerMcpAuthorizationError) as exc_403:
        client.submit_objective(
            backend_url="https://hub.example.test",
            token="tok",
            payload={"objective": "x"},
        )
    assert exc_403.value.status_code == 403
    assert exc_403.value.code == "INSUFFICIENT_SCOPE"
    assert exc_403.value.required_scope == "worker:submit"

    # 422 semantic validation -> WorkerMcpValidationError with sanitized reason_code
    monkeypatch.setattr(
        client,
        "_request_json",
        lambda **kwargs: (
            422,
            {"detail": "SEMANTIC_CONSTRAINTS_UNSUPPORTED:caller_input_ignored"},
        ),
    )
    with pytest.raises(client.WorkerMcpValidationError) as exc_422:
        client.submit_objective(
            backend_url="https://hub.example.test",
            token="tok",
            payload={"objective": "x"},
        )
    assert exc_422.value.status_code == 422
    assert exc_422.value.code == "SEMANTIC_VALIDATION_FAILED"
    assert exc_422.value.reason_code == "SEMANTIC_CONSTRAINTS_UNSUPPORTED"
    assert "caller_input_ignored" not in exc_422.value.reason_code
