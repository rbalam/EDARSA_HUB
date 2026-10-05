from __future__ import annotations

from typing import Any

import pytest
from mcp import Client
from mcp.server.auth.provider import AccessToken

from modules.worker_mcp import auth, client, server
from modules.worker_mcp.config import (
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
