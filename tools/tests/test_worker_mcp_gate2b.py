from __future__ import annotations

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
