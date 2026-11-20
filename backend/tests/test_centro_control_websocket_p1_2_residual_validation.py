"""P1-2 (READ_ONLY): caracterizacion + criterios de aceptacion de hallazgos residuales H01-H04 del WS /api/centro-control/ws.

Estas pruebas DOCUMENTAN el comportamiento actual (no lo corrigen). Cada prueba
afirma lo que el codigo hace hoy; si una correccion futura cambia el
comportamiento, la prueba correspondiente debe invertirse.
SQL se simula; no hay acceso a Produccion ni DML/DDL.
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


def test_h01_origin_outside_allowlist_accepted_when_it_matches_host(state, monkeypatch):
    """CONFIRMADO: un Origin fuera de CORS_ORIGINS se acepta si coincide con Host.

    Ocurre cuando el Host llega controlado por el origen (p.ej. DNS rebinding o
    un vhost/proxy que reenvia Host arbitrario). En DNS rebinding el navegador no
    envia la cookie de edarsa, por lo que la explotacion real requiere ademas una
    credencial valida -> riesgo BAJO, pero el allowlist deja de ser la unica autoridad.
    """
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    assert _accepted(_client(), {"origin": "https://evil.test", "host": "evil.test"}) is True


def test_h01_http_scheme_accepted_via_host_match(state, monkeypatch):
    """CONFIRMADO: el fallback Host acepta tambien http:// aunque el allowlist solo tenga https://."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    assert _accepted(_client(), {"origin": "http://app.edarsa.test", "host": "app.edarsa.test"}) is True


# ---------------------------------------------------------------- H02 CORS vacio
@pytest.mark.parametrize("raw", [None, "", " , ", "*"])
def test_h02_empty_or_wildcard_cors_falls_back_to_localhost(state, monkeypatch, raw):
    """CONFIRMADO: sin CORS_ORIGINS util, el WS acepta http://localhost:3000 (no fail-closed)."""
    if raw is None:
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("CORS_ORIGINS", raw)
    assert cc_routes._allowed_ws_origins() == {"http://localhost:3000"}
    assert _accepted(_client(), {"origin": "http://localhost:3000", "host": "app.edarsa.test"}) is True


def test_h02_foreign_origin_still_rejected_with_empty_cors(state, monkeypatch):
    """Alcance real de H02: solo se abre localhost:3000, no cualquier origen."""
    monkeypatch.setenv("CORS_ORIGINS", "")
    assert _accepted(_client(), {"origin": "https://evil.test", "host": "app.edarsa.test"}) is False


# ---------------------------------------------------------------- H04 sin revalidacion
def test_h04_revoked_permission_keeps_session_alive(state, monkeypatch):
    """CONFIRMADO: tras revocar CENTRO_CONTROL_VER, la sesion abierta sigue respondiendo."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    flags, mgr = state
    client = _client()
    client.cookies.set(AUTH_COOKIE_NAME, _jwt())
    with client.websocket_connect(WS, headers={"origin": "https://app.edarsa.test"}) as ws:
        assert ws.receive_json()["tipo"] == "conexion_establecida"
        flags["perm"] = False  # revocacion en SQL
        ws.send_json({"tipo": "ping"})
        assert ws.receive_json()["tipo"] == "pong"
        assert mgr.connection_count == 1


def test_h04_deactivated_user_keeps_session_alive(state, monkeypatch):
    """CONFIRMADO: usuario desactivado en SQL conserva su sesion WS abierta."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    flags, mgr = state
    client = _client()
    client.cookies.set(AUTH_COOKIE_NAME, _jwt())
    with client.websocket_connect(WS, headers={"origin": "https://app.edarsa.test"}) as ws:
        ws.receive_json()
        flags["active"] = False
        ws.send_json({"tipo": "ping"})
        assert ws.receive_json()["tipo"] == "pong"
        assert mgr.connection_count == 1


def test_h04_new_connection_after_revocation_is_rejected(state, monkeypatch):
    """Control: la revocacion SI aplica a conexiones nuevas (el hueco es solo en sesiones abiertas)."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    flags, _ = state
    flags["perm"] = False
    assert _accepted(_client(), {"origin": "https://app.edarsa.test"}) is False


# =============================================================================
# CRITERIOS DE ACEPTACION SEGUROS (objetivo R3)
# Marcados xfail(strict=True): fallan hoy (confirman la brecha) y, cuando una
# correccion autorizada los satisfaga, xfail estricto obliga a quitar la marca.
# =============================================================================
_R3 = "Brecha confirmada en P1-2; se corrige solo en un Gate R3 autorizado"


@pytest.mark.xfail(strict=True, reason=_R3)
def test_accept_h01_origin_outside_allowlist_rejected_even_if_matches_host(state, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    assert _accepted(_client(), {"origin": "https://evil.test", "host": "evil.test"}) is False


@pytest.mark.xfail(strict=True, reason=_R3)
def test_accept_h01_scheme_downgrade_rejected(state, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    assert _accepted(_client(), {"origin": "http://app.edarsa.test", "host": "app.edarsa.test"}) is False


@pytest.mark.xfail(strict=True, reason=_R3)
@pytest.mark.parametrize("raw", [None, "", "*"])
def test_accept_h02_empty_cors_is_fail_closed(state, monkeypatch, raw):
    if raw is None:
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("CORS_ORIGINS", raw)
    assert _accepted(_client(), {"origin": "http://localhost:3000", "host": "app.edarsa.test"}) is False


@pytest.mark.xfail(strict=True, reason=_R3)
def test_accept_h04_revocation_closes_open_session(state, monkeypatch):
    """Tras revocar permiso, el siguiente intercambio debe terminar con cierre 1008."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test")
    flags, mgr = state
    client = _client()
    client.cookies.set(AUTH_COOKIE_NAME, _jwt())
    with client.websocket_connect(WS, headers={"origin": "https://app.edarsa.test"}) as ws:
        ws.receive_json()
        flags["perm"] = False
        ws.send_json({"tipo": "ping"})
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
        assert exc.value.code == 1008
    assert mgr.connection_count == 0
