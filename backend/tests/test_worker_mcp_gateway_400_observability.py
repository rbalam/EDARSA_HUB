"""Observabilidad sanitizada del HTTP 400 del upstream MCP (solo logging; sin cambio funcional)."""
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
