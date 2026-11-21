"""Observabilidad sanitizada del HTTP 400 del upstream MCP (solo logging; sin cambio funcional)."""
import contextlib
import importlib
import json
import logging
import sys
import types

import httpx
import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient


def _load_gateway():
    """Import the gateway with OAuth router stubbed so the test needs no SQL config."""
    oauth_name, gateway_name = "modules.worker_mcp.oauth_server", "modules.worker_mcp.gateway_router"
    saved = {name: sys.modules.get(name) for name in (oauth_name, gateway_name)}
    stub = types.ModuleType(oauth_name)
    stub.router = APIRouter()
    sys.modules[oauth_name] = stub
    sys.modules.pop(gateway_name, None)
    try:
        return importlib.import_module(gateway_name)
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


gateway_router = _load_gateway()

SECRET = "SECRET-TOKEN-VALUE-123"
COOKIE = "SESSIONCOOKIE-ABC"
BODY_SECRET = "BODY-SECRET-XYZ"
LOGGER = "edarsahub.worker_mcp.gateway"


class _FailingStream(httpx.AsyncByteStream):
    async def __aiter__(self):
        raise httpx.ReadError("boom")
        yield b""  # pragma: no cover


def _client(monkeypatch, handler):
    monkeypatch.setenv("EDARSAHUB_MCP_UPSTREAM_URL", "http://127.0.0.1:32913")
    monkeypatch.delenv("EDARSAHUB_MCP_INPROCESS", raising=False)
    real = httpx.AsyncClient
    monkeypatch.setattr(
        gateway_router.httpx, "AsyncClient",
        lambda **kw: real(transport=httpx.MockTransport(handler), **kw),
    )
    app = FastAPI()
    app.include_router(gateway_router.router)
    return TestClient(app)


def _post(client, body=None, **headers):
    base = {
        "Authorization": f"Bearer {SECRET}", "Cookie": f"sid={COOKIE}",
        "Content-Type": "application/json", "Accept": "application/json, text/event-stream",
    }
    base.update(headers)
    payload = body if body is not None else json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"note": BODY_SECRET}}
    )
    return client.post("/api/mcp", content=payload, headers=base)


def _rpc_error(code):
    return httpx.Response(
        400, json={"jsonrpc": "2.0", "id": None, "error": {"code": code, "message": f"x {BODY_SECRET}"}},
    )


@pytest.mark.parametrize("body,expected", [
    (b'{"error":{"code":-32700,"message":"m"}}', ("parse_error", -32700)),
    (b'{"error":{"code":-32600,"message":"m"}}', ("invalid_request", -32600)),
    (b'{"error":{"code":-32602,"message":"m"}}', ("invalid_params", -32602)),
    (b'{"error":{"code":-32000,"message":"m"}}', ("jsonrpc_other", -32000)),
    (b"Invalid Content-Type header", ("content_type_invalid", None)),
    (b"Bad Request: Missing session ID", ("session_id_missing", None)),
    (b"not json at all", ("unclassified", None)),
    (b'{"error":"plain"}', ("unclassified", None)),
    (b'{"error":{"code":true}}', ("unclassified", None)),
    (b"x" * 70000, ("oversized", None)),
])
def test_classification_uses_closed_vocabulary(body, expected):
    assert gateway_router._classify_400(body) == expected


def test_400_is_passed_through_unchanged_and_logged_sanitized(monkeypatch, caplog):
    upstream = httpx.Response(
        400, headers={"content-type": "application/json", "x-internal": "leak"},
        json={"jsonrpc": "2.0", "id": None, "error": {"code": -32602, "message": BODY_SECRET}},
    )
    client = _client(monkeypatch, lambda request: upstream)
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        reply = _post(client, **{"MCP-Protocol-Version": "2099-01-01"})
    assert reply.status_code == 400
    assert reply.json()["error"]["code"] == -32602
    assert reply.headers["content-type"].startswith("application/json")
    assert "x-internal" not in reply.headers
    lines = [r.getMessage() for r in caplog.records if r.name == LOGGER]
    assert len(lines) == 1
    line = lines[0]
    assert "mcp_upstream_400" in line and "rpc_method=initialize" in line
    assert "error_class=invalid_params" in line and "jsonrpc_code=-32602" in line
    assert "content_type=json" in line and "accept=json+sse" in line
    assert "protocol_version=unknown" in line and "has_auth=true" in line
    for forbidden in (SECRET, COOKIE, BODY_SECRET, "Bearer", "2099-01-01", "sid="):
        assert forbidden not in line


def test_unknown_request_method_is_not_echoed(monkeypatch, caplog):
    client = _client(monkeypatch, lambda request: _rpc_error(-32600))
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": f"custom/{BODY_SECRET}"})
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        _post(client, body=body)
    line = [r.getMessage() for r in caplog.records if r.name == LOGGER][0]
    assert "rpc_method=other" in line and BODY_SECRET not in line


def test_non_400_responses_are_unchanged_and_not_logged(monkeypatch, caplog):
    def handler(request):
        if request.headers.get("authorization"):
            return httpx.Response(
                200, headers={"content-type": "application/json"},
                stream=httpx.ByteStream(b'{"ok": true}'),
            )
        return httpx.Response(401, headers={"www-authenticate": "Bearer"}, stream=httpx.ByteStream(b""))

    client = _client(monkeypatch, handler)
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        ok = _post(client)
        denied = client.post("/api/mcp", content=b"{}", headers={"Content-Type": "application/json"})
    assert ok.status_code == 200 and ok.json() == {"ok": True}
    assert denied.status_code == 401
    assert not [r for r in caplog.records if r.name == LOGGER]


def test_400_body_read_failure_fails_closed(monkeypatch, caplog):
    client = _client(monkeypatch, lambda request: httpx.Response(400, stream=_FailingStream()))
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        reply = _post(client)
    assert reply.status_code == 502
    assert reply.text == "MCP upstream unavailable"
    assert not [r for r in caplog.records if r.name == LOGGER]


def test_logging_failure_never_changes_the_proxied_response(monkeypatch):
    def broken(_body):
        raise RuntimeError("classifier failed")

    monkeypatch.setattr(gateway_router, "_classify_400", broken)
    client = _client(monkeypatch, lambda request: _rpc_error(-32700))
    reply = _post(client)
    assert reply.status_code == 400
    assert reply.json()["error"]["code"] == -32700


def test_upstream_allowlist_is_unchanged(monkeypatch):
    monkeypatch.setenv("EDARSAHUB_MCP_UPSTREAM_URL", "http://example.test:80")
    client = TestClient(_app_only_router())
    assert _post(client).status_code == 503


def _app_only_router():
    app = FastAPI()
    app.include_router(gateway_router.router)
    return app


from contextlib import asynccontextmanager
from pathlib import Path

if importlib.util.find_spec("mcp") is None:
    for _candidate in sorted(Path("/app/.runtime/worker_mcp/venv/lib").glob("python*/site-packages")):
        sys.path.append(str(_candidate))

from mcp.server.auth.provider import AccessToken
from modules.worker_mcp.config import WorkerMcpConfig
from modules.worker_mcp.server import build_mcp_server, build_transport_security


class _StubTokenVerifier:
    async def verify_token(self, token: str) -> AccessToken | None:
        if token != SECRET:
            return None
        return AccessToken(
            token=token,
            client_id="user-1",
            scopes=["mcp:tools"],
            expires_at=None,
            resource="https://edarsahub.example.com/api/mcp",
        )


def _build_real_upstream():
    cfg = WorkerMcpConfig(
        issuer_url="http://127.0.0.1:32913",
        resource_url="http://127.0.0.1:32913/mcp",
        backend_url="http://127.0.0.1:8001",
        allowed_hosts=("127.0.0.1:*", "localhost:*"),
        allowed_origins=(),
    )
    mcp_server = build_mcp_server(
        cfg,
        token_verifier=_StubTokenVerifier(),
    )
    upstream_app = mcp_server.streamable_http_app(
        json_response=True,
        stateless_http=True,
        transport_security=build_transport_security(cfg),
        host=cfg.bind_host,
    )
    return mcp_server, upstream_app


@contextlib.contextmanager
def _gateway_with_real_upstream(monkeypatch):
    monkeypatch.setenv("EDARSAHUB_MCP_UPSTREAM_URL", "http://127.0.0.1:32913")
    monkeypatch.setenv("EDARSAHUB_MCP_PUBLIC_ORIGIN", "https://edarsahub.example.com")
    monkeypatch.delenv("EDARSAHUB_MCP_INPROCESS", raising=False)
    _mcp_server, upstream_app = _build_real_upstream()
    real_async_client = httpx.AsyncClient

    @asynccontextmanager
    async def _lifespan(_app: FastAPI):
        async with upstream_app.router.lifespan_context(upstream_app):
            yield

    monkeypatch.setattr(
        gateway_router.httpx,
        "AsyncClient",
        lambda **kw: real_async_client(
            transport=httpx.ASGITransport(app=upstream_app),
            **kw,
        ),
    )
    app = FastAPI(lifespan=_lifespan)
    app.include_router(gateway_router.router)
    with TestClient(app) as client:
        yield client


def _init_payload(protocol_version: str = "2025-06-18") -> str:
    return json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": protocol_version,
            "capabilities": {},
            "clientInfo": {"name": "chatgpt-connector", "version": "1.0.0"},
        },
    })


@pytest.mark.parametrize(
    "requested_version,header_version,expected_version",
    [
        ("2024-11-05", None, "2024-11-05"),
        ("2025-03-26", None, "2025-03-26"),
        ("2025-06-18", "2025-06-18", "2025-06-18"),
        ("2025-11-25", "  2025-11-25  ", "2025-11-25"),
        ("2099-01-01", None, "2025-11-25"),
        ("2025-06-18", "2099-01-01", "2025-06-18"),
        ("2025-06-18", "", "2025-06-18"),
    ],
)
def test_gateway_initialize_protocol_version_negotiation(
    monkeypatch, requested_version, header_version, expected_version
):
    with _gateway_with_real_upstream(monkeypatch) as client:
        extra = {} if header_version is None else {"MCP-Protocol-Version": header_version}
        reply = _post(client, body=_init_payload(requested_version), **extra)
    assert reply.status_code == 200
    data = reply.json()
    assert data["result"]["protocolVersion"] == expected_version
    assert data["result"]["serverInfo"]["name"] == "EDARSAHUB Universal Worker"


def test_gateway_handshake_initialized_and_tools_list_discovery(monkeypatch):
    with _gateway_with_real_upstream(monkeypatch) as client:
        init_reply = _post(
            client,
            body=_init_payload("2025-06-18"),
            **{"MCP-Protocol-Version": "2025-06-18"},
        )
        assert init_reply.status_code == 200

        notif_reply = _post(
            client,
            body=json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            **{"MCP-Protocol-Version": "2025-06-18"},
        )
        assert notif_reply.status_code == 202

        tools_reply = _post(
            client,
            body=json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
            **{"MCP-Protocol-Version": "2025-06-18"},
        )
        assert tools_reply.status_code == 200
        tools = {tool["name"]: tool for tool in tools_reply.json()["result"]["tools"]}
        assert set(tools.keys()) == {"submit_objective", "get_job_status"}
        assert "objective" in tools["submit_objective"]["inputSchema"]["properties"]
        assert "job_id" in tools["get_job_status"]["inputSchema"]["properties"]


@pytest.mark.parametrize("bad_version", ["2099-01-01", ""])
def test_gateway_does_not_silently_downgrade_incompatible_mcp_versions(monkeypatch, bad_version):
    with _gateway_with_real_upstream(monkeypatch) as client:
        notif_reply = _post(
            client,
            body=json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            **{"MCP-Protocol-Version": bad_version},
        )
        assert notif_reply.status_code == 400

        tools_reply = _post(
            client,
            body=json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
            **{"MCP-Protocol-Version": bad_version},
        )
        assert tools_reply.status_code == 400


def test_gateway_forwards_modern_mcp_method_header(monkeypatch):
    from mcp_types import CLIENT_CAPABILITIES_META_KEY, PROTOCOL_VERSION_META_KEY

    with _gateway_with_real_upstream(monkeypatch) as client:
        reply = _post(
            client,
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/list",
                "params": {
                    "_meta": {
                        PROTOCOL_VERSION_META_KEY: "2026-07-28",
                        CLIENT_CAPABILITIES_META_KEY: {},
                    },
                },
            }),
            **{"MCP-Protocol-Version": "2026-07-28", "Mcp-Method": "tools/list"},
        )
    assert reply.status_code == 200
    tools = {tool["name"] for tool in reply.json()["result"]["tools"]}
    assert tools == {"submit_objective", "get_job_status"}


def test_gateway_validates_external_origin_and_strips_it_before_loopback(monkeypatch):
    monkeypatch.setenv(
        "EDARSAHUB_MCP_ALLOWED_ORIGINS",
        "https://chatgpt.com,http://localhost:*",
    )
    with _gateway_with_real_upstream(monkeypatch) as client:
        ok_chatgpt = _post(
            client,
            body=_init_payload("2025-06-18"),
            Origin="https://chatgpt.com",
        )
        assert ok_chatgpt.status_code == 200

        ok_localhost = _post(
            client,
            body=json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
            Origin="http://localhost:5173",
            **{"MCP-Protocol-Version": "2025-06-18"},
        )
        assert ok_localhost.status_code == 200

        ok_same_origin = _post(
            client,
            body=_init_payload("2025-06-18"),
            Origin="https://edarsahub.example.com",
            **{
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "edarsahub.example.com",
            },
        )
        assert ok_same_origin.status_code == 200

        denied_origin = _post(
            client,
            body=_init_payload("2025-06-18"),
            Origin="https://evil.example.test",
        )
        assert denied_origin.status_code == 403
        assert denied_origin.text == "Invalid Origin header"

        empty_origin = _post(
            client,
            body=_init_payload("2025-06-18"),
            Origin="   ",
        )
        assert empty_origin.status_code == 403


def test_gateway_preserves_oauth_bearer_authentication(monkeypatch):
    with _gateway_with_real_upstream(monkeypatch) as client:
        missing_auth = client.post(
            "/api/mcp",
            content=_init_payload("2025-06-18"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "edarsahub.example.com",
            },
        )
        assert missing_auth.status_code == 401
        challenge = missing_auth.headers.get("www-authenticate", "")
        assert "https://edarsahub.example.com/api/mcp/.well-known/oauth-protected-resource" in challenge
        assert "127.0.0.1" not in challenge

        bad_token = _post(
            client,
            body=_init_payload("2025-06-18"),
            Authorization="Bearer invalid-token",
        )
        assert bad_token.status_code == 401


def test_get_job_status_projects_sanitized_result_detail(monkeypatch):
    from modules.worker_mcp import server

    expected = {
        "checks": [
            {
                "source_job_id": "JOB-1",
                "result_status": "GIT_TESTS_FAILED",
                "failed_checks": [
                    {
                        "type": "pytest",
                        "status": "FAIL",
                        "returncode": 1,
                        "output": "FAILED test_x",
                        "assertion_lines": [
                            "E AssertionError"
                        ],
                    }
                ],
                "production_touched": False,
            }
        ]
    }

    monkeypatch.setattr(
        server,
        "_BACKEND_URL",
        "http://backend.test",
    )

    monkeypatch.setattr(
        server,
        "_bearer_token",
        lambda: "opaque-test-token",
    )

    monkeypatch.setattr(
        server,
        "backend_get_job_status",
        lambda **kwargs: {
            "job_id": "JOB-1",
            "lifecycle": "RESULT",
            "status": "READ_ONLY_COMPLETE",
            "certification": "CERTIFIED_READ_ONLY",
            "work_completion": "COMPLETE",
            "quality_gate": "PASS",
            "tests": "PASS",
            "percent_complete": 100,
            "production_touched": False,
            "result_detail_evidence": expected,
        },
    )

    result = server.get_job_status_tool(
        "JOB-1"
    )

    assert (
        result[
            "result_detail_evidence"
        ]
        == expected
    )
