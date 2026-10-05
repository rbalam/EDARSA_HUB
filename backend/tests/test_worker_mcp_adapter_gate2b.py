from __future__ import annotations

from typing import Any

import pytest

from mcp import Client
from mcp.server.auth.provider import AccessToken

from modules.worker_mcp import auth, server
from modules.worker_mcp.config import (
    WorkerMcpConfig,
    WorkerMcpConfigError,
)


def _config() -> WorkerMcpConfig:
    return WorkerMcpConfig(
        issuer_url="https://auth.example.test",
        resource_url="https://mcp.example.test/mcp",
        allowed_hosts=("mcp.example.test",),
        allowed_origins=("https://chat.example.test",),
    )


@pytest.mark.asyncio
async def test_mcp_exposes_exactly_two_public_tools():
    mcp = server.build_mcp_server(_config())

    async with Client(mcp) as client:
        result = await client.list_tools()

    assert {tool.name for tool in result.tools} == {
        "submit_objective",
        "get_job_status",
    }


def test_config_fails_closed_without_required_env(monkeypatch):
    for name in (
        "EDARSAHUB_MCP_ISSUER_URL",
        "EDARSAHUB_MCP_RESOURCE_URL",
        "EDARSAHUB_MCP_ALLOWED_HOSTS",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(
        WorkerMcpConfigError,
        match="REQUIRED_ENV_MISSING",
    ):
        WorkerMcpConfig.from_env()


@pytest.mark.asyncio
async def test_token_verifier_uses_existing_edarsahub_auth_and_sql_authority(
    monkeypatch,
):
    monkeypatch.setattr(
        auth,
        "verify_token",
        lambda token: {
            "user_id": "user-1",
            "email": "admin@example.com",
            "role": "SuperAdministrador",
        },
    )
    monkeypatch.setattr(
        auth,
        "authorize_requester",
        lambda requester: {
            "allowed": requester.get("email") == "admin@example.com",
        },
    )

    verifier = auth.EdarsahubTokenVerifier(
        resource_url="https://mcp.example.test/mcp",
    )

    token = await verifier.verify_token("opaque-test-token")

    assert token is not None
    assert token.subject == "admin@example.com"
    assert token.client_id == "user-1"
    assert token.scopes == [
        "worker:submit",
        "worker:status",
    ]


@pytest.mark.asyncio
async def test_token_verifier_rejects_denied_requester(
    monkeypatch,
):
    monkeypatch.setattr(
        auth,
        "verify_token",
        lambda token: {
            "user_id": "user-2",
            "email": "denied@example.com",
            "role": "Usuario",
        },
    )
    monkeypatch.setattr(
        auth,
        "authorize_requester",
        lambda requester: {
            "allowed": False,
            "reason": "NOT_SUPERADMIN",
        },
    )

    verifier = auth.EdarsahubTokenVerifier(
        resource_url="https://mcp.example.test/mcp",
    )

    assert await verifier.verify_token("opaque-test-token") is None


def _access_token() -> AccessToken:
    return AccessToken(
        token="opaque",
        client_id="user-1",
        scopes=["worker:submit", "worker:status"],
        subject="admin@example.com",
        resource="https://mcp.example.test/mcp",
        claims={
            "email": "admin@example.com",
            "role": "SuperAdministrador",
            "user_id": "user-1",
        },
    )


def test_submit_tool_delegates_only_to_semantic_ingress(
    monkeypatch,
):
    monkeypatch.setattr(
        server,
        "get_access_token",
        _access_token,
    )
    monkeypatch.setattr(
        server,
        "authorize_requester",
        lambda requester: {"allowed": True},
    )

    captured: dict[str, Any] = {}

    def fake_submit(payload, *, current_user):
        captured["payload"] = payload
        captured["current_user"] = current_user
        return {
            "status": "SUBMITTED",
            "job_id": "SEM-TEST-1",
            "capability": "READ_ONLY_CANARY",
            "bounded_context": "WORKER_INGRESS",
            "production_touched": False,
        }

    monkeypatch.setattr(
        server,
        "_submit_objective",
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
    assert captured["payload"].keys() == {
        "objective",
        "bounded_context",
        "mode",
        "capability",
        "constraints",
        "request_key",
    }
    assert "actions" not in captured["payload"]
    assert "checks" not in captured["payload"]


def test_status_tool_delegates_to_canonical_status_reader(
    monkeypatch,
):
    monkeypatch.setattr(
        server,
        "get_access_token",
        _access_token,
    )
    monkeypatch.setattr(
        server,
        "authorize_requester",
        lambda requester: {"allowed": True},
    )
    monkeypatch.setattr(
        server,
        "_get_job_status",
        lambda job_id: {
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


def test_adapter_has_no_low_level_worker_or_shell_surface():
    source = server.__file__
    assert source

    text = open(source, encoding="utf-8").read().lower()

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
