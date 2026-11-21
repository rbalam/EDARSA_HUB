"""Pruebas P1-1: Autenticacion, Origin y RBAC fail-closed para WS /api/centro-control/ws."""
from __future__ import annotations

import os
from pathlib import Path

# Defaults seguros para ejecucion offline en worktree aislado sin .env
os.environ.setdefault("JWT_SECRET", "unit-test-only-signing-material-p1-ws-0001")
os.environ.setdefault("EDARSAHUB_SQL_HOST", "127.0.0.1")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "HRLectura")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "unit-test-only-placeholder")
os.environ.setdefault("CORS_ORIGINS", "https://app.edarsa.test,http://localhost:3000")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from core.centro_control import routes as cc_routes
from core.centro_control.websocket import NotificationManager
from core.security import AUTH_COOKIE_NAME, create_access_token


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(cc_routes.router)
    return app


def _make_jwt(email: str = "ricardo@edarsa.com.mx", role: str = "SUPERADMIN") -> str:
    return create_access_token(
        user_id="11111111-1111-1111-1111-111111111111",
        email=email,
        role=role,
        usuario_id=8,
        public_uuid="11111111-1111-1111-1111-111111111111",
    )


@pytest.fixture(autouse=True)
def _isolate_ws_cors_origins(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test,http://localhost:3000")


def _fresh_manager(monkeypatch) -> NotificationManager:
    mgr = NotificationManager()
    monkeypatch.setattr(cc_routes, "get_notification_manager", lambda: mgr)
    return mgr


def test_ws_rejects_anonymous_without_credentials(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    client = TestClient(_build_test_app())
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            "/api/centro-control/ws",
            headers={"origin": "http://localhost:3000"},
        ):
            pass
    assert exc_info.value.code == 1008
    assert mgr.connection_count == 0


def test_ws_rejects_query_string_jwt_only(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    jwt_val = _make_jwt()
    client = TestClient(_build_test_app())
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            f"/api/centro-control/ws?token={jwt_val}",
            headers={"origin": "http://localhost:3000"},
        ):
            pass
    assert exc_info.value.code == 1008
    assert mgr.connection_count == 0


def test_ws_rejects_invalid_jwt(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    client = TestClient(_build_test_app())
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            "/api/centro-control/ws",
            headers={
                "origin": "http://localhost:3000",
                "authorization": "Bearer invalid.jwt.value",
            },
        ):
            pass
    assert exc_info.value.code == 1008
    assert mgr.connection_count == 0


def test_ws_rejects_disallowed_origin_even_with_valid_auth(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    jwt_val = _make_jwt()

    async def _fake_user(email, uid=None):
        return {"id": "11111111-1111-1111-1111-111111111111", "email": email, "active": True, "role": "SUPERADMIN"}, "SQL"

    monkeypatch.setattr("core.security._get_user_sql_only", _fake_user)
    monkeypatch.setattr(cc_routes, "_has_explicit_ws_permission_sql", lambda email, perm: True)

    client = TestClient(_build_test_app())
    client.cookies.set(AUTH_COOKIE_NAME, jwt_val)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            "/api/centro-control/ws",
            headers={"origin": "https://evil.attacker.example"},
        ):
            pass
    assert exc_info.value.code == 1008
    assert mgr.connection_count == 0


def test_ws_rejects_cookie_auth_without_origin_header(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    jwt_val = _make_jwt()

    async def _fake_user(email, uid=None):
        return {"id": "11111111-1111-1111-1111-111111111111", "email": email, "active": True, "role": "SUPERADMIN"}, "SQL"

    monkeypatch.setattr("core.security._get_user_sql_only", _fake_user)
    monkeypatch.setattr(cc_routes, "_has_explicit_ws_permission_sql", lambda email, perm: True)

    client = TestClient(_build_test_app())
    client.cookies.set(AUTH_COOKIE_NAME, jwt_val)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/centro-control/ws"):
            pass
    assert exc_info.value.code == 1008
    assert mgr.connection_count == 0


def test_ws_rejects_inactive_user(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    jwt_val = _make_jwt()

    async def _fake_inactive(email, uid=None):
        return {"id": "11111111-1111-1111-1111-111111111111", "email": email, "active": False, "role": "SUPERADMIN"}, "SQL"

    monkeypatch.setattr("core.security._get_user_sql_only", _fake_inactive)
    monkeypatch.setattr(cc_routes, "_has_explicit_ws_permission_sql", lambda email, perm: True)

    client = TestClient(_build_test_app())
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            "/api/centro-control/ws",
            headers={
                "origin": "http://localhost:3000",
                "authorization": f"Bearer {jwt_val}",
            },
        ):
            pass
    assert exc_info.value.code == 1008
    assert mgr.connection_count == 0


def test_ws_rejects_authenticated_user_without_centro_control_ver(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    jwt_val = _make_jwt(email="admin-sin-permiso@edarsa.com.mx", role="ADMIN")

    async def _fake_user(email, uid=None):
        return {"id": "22222222-2222-2222-2222-222222222222", "email": email, "active": True, "role": "ADMIN"}, "SQL"

    monkeypatch.setattr("core.security._get_user_sql_only", _fake_user)
    monkeypatch.setattr(cc_routes, "_has_explicit_ws_permission_sql", lambda email, perm: False)

    client = TestClient(_build_test_app())
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            "/api/centro-control/ws",
            headers={
                "origin": "http://localhost:3000",
                "authorization": f"Bearer {jwt_val}",
            },
        ):
            pass
    assert exc_info.value.code == 1008
    assert mgr.connection_count == 0


def test_ws_fails_closed_when_sql_rbac_raises(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    jwt_val = _make_jwt()

    async def _fake_user(email, uid=None):
        return {"id": "11111111-1111-1111-1111-111111111111", "email": email, "active": True, "role": "SUPERADMIN"}, "SQL"

    def _boom(email, perm):
        raise RuntimeError("SQL_CONNECTION_UNAVAILABLE")

    monkeypatch.setattr("core.security._get_user_sql_only", _fake_user)
    monkeypatch.setattr(cc_routes, "_has_explicit_ws_permission_sql", _boom)

    client = TestClient(_build_test_app())
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            "/api/centro-control/ws",
            headers={
                "origin": "http://localhost:3000",
                "authorization": f"Bearer {jwt_val}",
            },
        ):
            pass
    assert exc_info.value.code == 1008
    assert mgr.connection_count == 0


def test_ws_accepts_authorized_cookie_user_and_handles_ping_pong(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    jwt_val = _make_jwt(email="ricardo@edarsa.com.mx", role="SUPERADMIN")
    checked_perms = []

    async def _fake_user(email, uid=None):
        return {"id": "11111111-1111-1111-1111-111111111111", "email": email, "active": True, "role": "SUPERADMIN"}, "SQL"

    def _check_perm(email, perm):
        checked_perms.append((email, perm))
        return perm == "CENTRO_CONTROL_VER"

    monkeypatch.setattr("core.security._get_user_sql_only", _fake_user)
    monkeypatch.setattr(cc_routes, "_has_explicit_ws_permission_sql", _check_perm)

    client = TestClient(_build_test_app())
    client.cookies.set(AUTH_COOKIE_NAME, jwt_val)
    with client.websocket_connect(
        "/api/centro-control/ws",
        headers={"origin": "https://app.edarsa.test"},
    ) as ws:
        welcome = ws.receive_json()
        assert welcome["tipo"] == "conexion_establecida"
        assert mgr.connection_count == 1
        conn_info = next(iter(mgr._connections.values()))
        assert conn_info.user_email == "ricardo@edarsa.com.mx"
        assert checked_perms == [("ricardo@edarsa.com.mx", "CENTRO_CONTROL_VER")]

        ws.send_json({"tipo": "ping"})
        pong = ws.receive_json()
        assert pong["tipo"] == "pong"

    assert mgr.connection_count == 0


def test_ws_accepts_authorized_bearer_without_origin_and_same_origin_host(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    jwt_val = _make_jwt(email="operador@edarsa.com.mx", role="OPERADOR")

    async def _fake_user(email, uid=None):
        return {"id": "33333333-3333-3333-3333-333333333333", "email": email, "active": True, "role": "OPERADOR"}, "SQL"

    monkeypatch.setattr("core.security._get_user_sql_only", _fake_user)
    monkeypatch.setattr(cc_routes, "_has_explicit_ws_permission_sql", lambda email, perm: perm == "CENTRO_CONTROL_VER")

    client = TestClient(_build_test_app())
    # 1. Bearer sin Origin (cliente tecnico autorizado)
    with client.websocket_connect(
        "/api/centro-control/ws",
        headers={"authorization": f"Bearer {jwt_val}"},
    ) as ws:
        msg = ws.receive_json()
        assert msg["tipo"] == "conexion_establecida"

    # 2. Cookie con Origin de Preview explicitamente configurado en CORS_ORIGINS
    #    (WS-AUTH-R5 H01: la compatibilidad Preview/Produccion proviene del allowlist, no de Host)
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://app.edarsa.test,http://localhost:3000,https://preview.edarsa.local",
    )
    client.cookies.set(AUTH_COOKIE_NAME, jwt_val)
    with client.websocket_connect(
        "/api/centro-control/ws",
        headers={"host": "preview.edarsa.local", "origin": "https://preview.edarsa.local"},
    ) as ws:
        msg = ws.receive_json()
        assert msg["tipo"] == "conexion_establecida"

    # 3. Control negativo R5: coincidir con Host sin estar en el allowlist se rechaza (1008)
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test,http://localhost:3000")
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            "/api/centro-control/ws",
            headers={"host": "preview.edarsa.local", "origin": "https://preview.edarsa.local"},
        ):
            pass
    assert exc.value.code == 1008


@pytest.mark.asyncio
async def test_notification_manager_connect_rejects_anonymous_fail_closed():
    mgr = NotificationManager()
    events = []

    class _DummyWS:
        async def accept(self):
            events.append("accept")

        async def close(self, code: int = 1000):
            events.append(("close", code))

        async def send_json(self, payload):
            events.append(("send", payload))

    with pytest.raises(PermissionError, match="WS_AUTHENTICATED_USER_REQUIRED"):
        await mgr.connect(_DummyWS(), user_email="anonymous")

    assert events == [("close", 1008)]
    assert mgr.connection_count == 0


def test_frontend_four_clients_keep_canonical_ws_endpoint_contract():
    repo_root = Path(__file__).resolve().parents[2]
    frontend_clients = [
        "frontend/src/components/centro-control/useWebSocketNotifications.js",
        "frontend/src/lib/ResilientWebSocket.js",
        "frontend/src/lib/sincronizacionEnVivo.js",
        "frontend/src/lib/websocketBlindado.js",
    ]
    for rel in frontend_clients:
        text = (repo_root / rel).read_text(encoding="utf-8")
        assert "/api/centro-control/ws" in text, f"Missing canonical WS path in {rel}"
        assert "?token=" not in text, f"Query token must not be used in {rel}"
