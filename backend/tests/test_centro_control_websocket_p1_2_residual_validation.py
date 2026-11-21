"""WS-AUTH-R5: validacion del cierre de hallazgos residuales H01, H02 y H04 del WS /api/centro-control/ws.

Origen: caracterizacion P1-2 (READ_ONLY). Las pruebas que documentaban las brechas
se invirtieron para validar el comportamiento seguro y los criterios de aceptacion
(antes xfail estricto) ahora son pruebas normales. Se conservan todos los controles
negativos. SQL se simula; no hay acceso SQL LIVE, Produccion ni DML/DDL.
"""
from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET", "unit-test-only-signing-material-p1-ws-0001")
os.environ.setdefault("EDARSAHUB_SQL_HOST", "127.0.0.1")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "HRLectura")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "unit-test-only-placeholder")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from core.centro_control import routes as cc_routes
from core.centro_control.websocket import NotificationManager
from core.security import AUTH_COOKIE_NAME, create_access_token

WS = "/api/centro-control/ws"


def _jwt(email="ricardo@edarsa.com.mx"):
    return create_access_token(
        user_id="11111111-1111-1111-1111-111111111111",
        email=email,
        role="SUPERADMIN",
        usuario_id=8,
        public_uuid="11111111-1111-1111-1111-111111111111",
    )


@pytest.fixture
def state(monkeypatch):
    """Usuario activo con permiso; los flags pueden cambiarse a mitad de sesion."""
    flags = {"active": True, "perm": True}

    async def _fake_user(email, uid=None):
        return {"email": email, "active": flags["active"]}, "sql"

    monkeypatch.setattr("core.security._get_user_sql_only", _fake_user)
    monkeypatch.setattr(cc_routes, "_has_explicit_ws_permission_sql", lambda email, perm: flags["perm"])
    mgr = NotificationManager()
    monkeypatch.setattr(cc_routes, "get_notification_manager", lambda: mgr)
    return flags, mgr


def _client():
    app = FastAPI()
    app.include_router(cc_routes.router)
    return TestClient(app)


def _accepted(client, headers):
    client.cookies.set(AUTH_COOKIE_NAME, _jwt())
    try:
        with client.websocket_connect(WS, headers=headers) as ws:
            return ws.receive_json().get("tipo") == "conexion_establecida"
    except WebSocketDisconnect:
        return False


# ---------------------------------------------------------------- H01 Origin == Host
def test_h01_cross_origin_against_real_host_is_rejected(state, monkeypatch):
    """CSWSH clasico: pagina en evil.test abre WS contra el host real -> rechazado."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    assert _accepted(_client(), {"origin": "https://evil.test", "host": "app.edarsa.test"}) is False


def test_h01_origin_outside_allowlist_rejected_even_if_matches_host(state, monkeypatch):
    """R5: un Origin fuera de CORS_ORIGINS se rechaza aunque coincida con Host (DNS rebinding / vhost)."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    assert _accepted(_client(), {"origin": "https://evil.test", "host": "evil.test"}) is False


def test_h01_scheme_downgrade_rejected_via_host_match(state, monkeypatch):
    """R5: http:// no se acepta por coincidir con Host si el allowlist solo tiene https://."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    assert _accepted(_client(), {"origin": "http://app.edarsa.test", "host": "app.edarsa.test"}) is False


def test_h01_allowlisted_origin_still_accepted(state, monkeypatch):
    """Compatibilidad: Origin explicitamente configurado (p.ej. Preview) sigue aceptado."""
    monkeypatch.setenv("CORS_ORIGINS", "https://preview.edarsa.test,https://app.edarsa.test")
    assert _accepted(_client(), {"origin": "https://preview.edarsa.test", "host": "backend.internal"}) is True
    assert _accepted(_client(), {"origin": "https://app.edarsa.test/", "host": "app.edarsa.test"}) is True


# ---------------------------------------------------------------- H02 CORS vacio
@pytest.mark.parametrize("raw", [None, "", " , ", "*", " * , "])
def test_h02_empty_absent_or_wildcard_cors_is_fail_closed(state, monkeypatch, raw):
    """R5: sin CORS_ORIGINS util no existe origen implicito (ni localhost:3000)."""
    if raw is None:
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("CORS_ORIGINS", raw)
    assert cc_routes._allowed_ws_origins() == set()
    assert _accepted(_client(), {"origin": "http://localhost:3000", "host": "app.edarsa.test"}) is False
    assert _accepted(_client(), {"origin": "http://localhost:3000", "host": "localhost:3000"}) is False


def test_h02_foreign_origin_still_rejected_with_empty_cors(state, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "")
    assert _accepted(_client(), {"origin": "https://evil.test", "host": "app.edarsa.test"}) is False


def test_h02_explicit_localhost_still_allowed_when_configured(state, monkeypatch):
    """Compatibilidad local legitima: solo si localhost esta configurado explicitamente."""
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    assert _accepted(_client(), {"origin": "http://localhost:3000", "host": "localhost:8001"}) is True


def test_bearer_without_origin_allowed_even_with_empty_cors(state, monkeypatch):
    """Clientes no-navegador con Bearer y sin Origin no dependen de CORS (sin cookie => sin CSWSH)."""
    monkeypatch.setenv("CORS_ORIGINS", "")
    client = _client()
    with client.websocket_connect(WS, headers={"authorization": f"Bearer {_jwt()}"}) as ws:
        assert ws.receive_json()["tipo"] == "conexion_establecida"


def test_cookie_without_origin_rejected_cswsh(state, monkeypatch):
    """Cookie HttpOnly sin Origin se rechaza siempre (proteccion CSWSH)."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    assert _accepted(_client(), {"host": "app.edarsa.test"}) is False


# ---------------------------------------------------------------- H04 revalidacion en sesion activa
def _open(client):
    client.cookies.set(AUTH_COOKIE_NAME, _jwt())
    return client.websocket_connect(WS, headers={"origin": "https://app.edarsa.test"})


def _assert_closed_1008(ws):
    ws.send_json({"tipo": "ping"})
    with pytest.raises(WebSocketDisconnect) as exc:
        ws.receive_json()
    assert exc.value.code == 1008


def test_h04_revoked_permission_closes_open_session_1008(state, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    flags, mgr = state
    with _open(_client()) as ws:
        assert ws.receive_json()["tipo"] == "conexion_establecida"
        flags["perm"] = False  # revocacion en SQL
        _assert_closed_1008(ws)
    assert mgr.connection_count == 0


def test_h04_deactivated_user_closes_open_session_1008(state, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    flags, mgr = state
    with _open(_client()) as ws:
        ws.receive_json()
        flags["active"] = False
        _assert_closed_1008(ws)
    assert mgr.connection_count == 0


def test_h04_revoked_session_sid_closes_open_session_1008(state, monkeypatch):
    """Sesion revocada en dbo.Sesiones (helper canonico verify_token_session_active) cierra 1008."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    flags, mgr = state
    session = {"active": True}

    async def _fake_session_active(payload, expected_user_type=None):
        return session["active"]

    monkeypatch.setattr("core.security.verify_token_session_active", _fake_session_active)
    with _open(_client()) as ws:
        ws.receive_json()
        session["active"] = False
        _assert_closed_1008(ws)
    assert mgr.connection_count == 0


def test_h04_sql_error_during_revalidation_is_fail_closed(state, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    flags, mgr = state
    with _open(_client()) as ws:
        ws.receive_json()

        def _boom(email, perm):
            raise RuntimeError("sql down")

        monkeypatch.setattr(cc_routes, "_has_explicit_ws_permission_sql", _boom)
        _assert_closed_1008(ws)
    assert mgr.connection_count == 0


def test_h04_authorized_session_keeps_working_and_revalidates_each_message(state, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    flags, mgr = state
    calls = {"n": 0}

    def _perm(email, perm):
        calls["n"] += 1
        return perm == "CENTRO_CONTROL_VER"

    monkeypatch.setattr(cc_routes, "_has_explicit_ws_permission_sql", _perm)
    with _open(_client()) as ws:
        ws.receive_json()
        for _ in range(3):
            ws.send_json({"tipo": "ping"})
            assert ws.receive_json()["tipo"] == "pong"
        assert mgr.connection_count == 1
    assert calls["n"] == 4  # handshake + 3 revalidaciones


def test_h04_idle_connection_revalidated_on_interval(state, monkeypatch):
    """Conexion inactiva: al vencer el intervalo se revalida y se cierra 1008 si fue revocada."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    monkeypatch.setattr(cc_routes, "_WS_REVALIDATE_INTERVAL_SECONDS", 0.05)
    flags, mgr = state
    with _open(_client()) as ws:
        ws.receive_json()
        flags["perm"] = False
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
        assert exc.value.code == 1008
    assert mgr.connection_count == 0


def test_h04_new_connection_after_revocation_is_rejected(state, monkeypatch):
    """Control: la revocacion aplica a conexiones nuevas."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    flags, _ = state
    flags["perm"] = False
    assert _accepted(_client(), {"origin": "https://app.edarsa.test"}) is False


def test_h04_authorized_reconnection_after_regrant(state, monkeypatch):
    """Reconexion autorizada: tras restituir el permiso, una nueva conexion se acepta."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    flags, mgr = state
    with _open(_client()) as ws:
        ws.receive_json()
        flags["perm"] = False
        _assert_closed_1008(ws)
    flags["perm"] = True
    assert _accepted(_client(), {"origin": "https://app.edarsa.test"}) is True
