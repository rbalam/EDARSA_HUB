"""Pruebas P1-2: Revocacion de sesiones, logout-all sin hash(), /auth/me y rotacion atomica."""
from __future__ import annotations

import asyncio
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

os.environ.setdefault("JWT_SECRET", "unit-test-only-signing-material-p1-2-sessions-0001")
os.environ.setdefault("EDARSAHUB_SQL_HOST", "127.0.0.1")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "HRLectura")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "unit-test-only-placeholder")
os.environ.setdefault("CORS_ORIGINS", "https://app.edarsa.test,http://localhost:3000")

import jwt as pyjwt
import pytest
from fastapi import FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from core import refresh_tokens as rt
from core import security as sec
from core.centro_control import routes as cc_routes
from core.centro_control.websocket import NotificationManager
from modules.auth import routes as auth_routes


class InMemorySesionesDB:
    """Simulador thread-safe de dbo.Sesiones + dbo.SesionesHistorico para pruebas deterministas."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []
        self.fail_on_next_op: Optional[str] = None
        self.raise_on_is_active: bool = False

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    async def execute_sql_async(
        self, query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False
    ):
        q = " ".join((query or "").split())
        p = tuple(params or ())
        with self.lock:
            if self.fail_on_next_op and self.fail_on_next_op in q.upper():
                self.fail_on_next_op = None
                raise RuntimeError("SIMULATED_SQL_FAILURE")

            if q.startswith("DELETE FROM Sesiones WHERE SesionID = %s"):
                self.sessions.pop(str(p[0]), None)
                return []

            if q.startswith("INSERT INTO Sesiones "):
                sid, uid, utype, rhash, fid, exp, ip, ua = p
                if isinstance(exp, str):
                    exp_dt = datetime.strptime(exp, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                else:
                    exp_dt = exp
                self.sessions[str(sid)] = {
                    "SesionID": str(sid),
                    "UsuarioID": str(uid),
                    "TipoUsuario": str(utype),
                    "RefreshTokenHash": str(rhash),
                    "FamiliaTokenID": str(fid),
                    "FechaCreacion": self._now(),
                    "FechaExpiracion": exp_dt,
                    "UltimaActividad": self._now(),
                    "EstaActiva": 1,
                    "FechaRevocacion": None,
                    "MotivoRevocacion": None,
                    "ReemplazadaPorSesionID": None,
                    "RevocadoPorUsuarioID": None,
                    "IPCliente": ip,
                    "UserAgent": ua,
                }
                return []

            if q.startswith("INSERT INTO SesionesHistorico"):
                self.history.append({"params": p})
                return []

            if q.startswith("SELECT TOP 1 1 FROM Sesiones WHERE SesionID = %s"):
                if self.raise_on_is_active:
                    raise RuntimeError("SQL_DOWN_IS_ACTIVE")
                sid = str(p[0])
                utype = str(p[1]).strip().lower() if len(p) > 1 else None
                row = self.sessions.get(sid)
                if (
                    row
                    and row["EstaActiva"] == 1
                    and row["FechaRevocacion"] is None
                    and row["FechaExpiracion"] > self._now()
                    and (utype is None or row["TipoUsuario"].strip().lower() == utype)
                ):
                    return (1,) if fetch_one else [(1,)]
                return None if fetch_one else []

            if "FROM Sesiones WHERE RefreshTokenHash = %s AND EstaActiva = 1" in q:
                rhash = str(p[0])
                utype = str(p[1]).strip().lower() if len(p) > 1 else None
                for row in self.sessions.values():
                    if (
                        row["RefreshTokenHash"] == rhash
                        and row["EstaActiva"] == 1
                        and row["FechaRevocacion"] is None
                        and row["FechaExpiracion"] > self._now()
                        and (utype is None or row["TipoUsuario"].strip().lower() == utype)
                    ):
                        tup = (
                            row["SesionID"],
                            row["UsuarioID"],
                            row["TipoUsuario"],
                            row["FamiliaTokenID"],
                            row["FechaCreacion"],
                            row["FechaExpiracion"],
                            row["UltimaActividad"],
                            row["IPCliente"],
                            row["UserAgent"],
                        )
                        return tup if fetch_one else [tup]
                return None if fetch_one else []

            if "FROM Sesiones WHERE RefreshTokenHash = %s AND EstaActiva = 0 AND MotivoRevocacion = 'token_rotated'" in q:
                rhash = str(p[0])
                utype = str(p[1]).strip().lower() if len(p) > 1 else None
                for row in self.sessions.values():
                    if (
                        row["RefreshTokenHash"] == rhash
                        and row["EstaActiva"] == 0
                        and row["MotivoRevocacion"] == "token_rotated"
                        and (utype is None or row["TipoUsuario"].strip().lower() == utype)
                    ):
                        tup = (
                            row["SesionID"],
                            row["UsuarioID"],
                            row["TipoUsuario"],
                            row["FamiliaTokenID"],
                            row["MotivoRevocacion"],
                            row["ReemplazadaPorSesionID"],
                        )
                        return tup if fetch_one else [tup]
                return None if fetch_one else []

            if q.startswith("SELECT UsuarioID, TipoUsuario FROM Sesiones WHERE SesionID = %s AND EstaActiva = 1"):
                row = self.sessions.get(str(p[0]))
                if row and row["EstaActiva"] == 1:
                    return (row["UsuarioID"], row["TipoUsuario"]) if fetch_one else [(row["UsuarioID"], row["TipoUsuario"])]
                return None if fetch_one else []

            if q.startswith("UPDATE Sesiones") and "WHERE SesionID = %s AND EstaActiva = 1" in q:
                reason, revoked_by, sid = p
                row = self.sessions.get(str(sid))
                if row and row["EstaActiva"] == 1:
                    row["EstaActiva"] = 0
                    row["FechaRevocacion"] = self._now()
                    row["MotivoRevocacion"] = reason
                    row["RevocadoPorUsuarioID"] = revoked_by
                return []

            if q.startswith("SELECT SesionID, TipoUsuario FROM Sesiones WHERE FamiliaTokenID = %s AND EstaActiva = 1"):
                fid = str(p[0])
                rows = [
                    (r["SesionID"], r["TipoUsuario"])
                    for r in self.sessions.values()
                    if r["FamiliaTokenID"] == fid and r["EstaActiva"] == 1
                ]
                return rows

            if q.startswith("UPDATE Sesiones") and "WHERE FamiliaTokenID = %s AND EstaActiva = 1" in q:
                reason, fid = p
                for r in self.sessions.values():
                    if r["FamiliaTokenID"] == str(fid) and r["EstaActiva"] == 1:
                        r["EstaActiva"] = 0
                        r["FechaRevocacion"] = self._now()
                        r["MotivoRevocacion"] = reason
                return []

            if "CAST(UsuarioID AS VARCHAR(100)) IN (" in q:
                in_count = q.split("CAST(UsuarioID AS VARCHAR(100)) IN (", 1)[1].split(")", 1)[0].count("%s")
                has_type = "TipoUsuario" in q and "LOWER(LTRIM(RTRIM(%s)))" in q
                has_except = "SesionID != %s" in q

                if q.startswith("SELECT SesionID, TipoUsuario, UsuarioID FROM Sesiones"):
                    idx = 0
                    cands = {str(x).lower() for x in p[idx : idx + in_count]}
                    idx += in_count
                    utype = str(p[idx]).strip().lower() if has_type else None
                    if has_type:
                        idx += 1
                    exc_sid = str(p[idx]) if has_except else None
                    matched = [
                        (r["SesionID"], r["TipoUsuario"], r["UsuarioID"])
                        for r in self.sessions.values()
                        if r["EstaActiva"] == 1
                        and str(r["UsuarioID"]).lower() in cands
                        and (utype is None or r["TipoUsuario"].strip().lower() == utype)
                        and (exc_sid is None or r["SesionID"] != exc_sid)
                    ]
                    return matched

                if q.startswith("UPDATE Sesiones"):
                    reason, revoked_by = p[0], p[1]
                    idx = 2
                    cands = {str(x).lower() for x in p[idx : idx + in_count]}
                    idx += in_count
                    utype = str(p[idx]).strip().lower() if has_type else None
                    if has_type:
                        idx += 1
                    exc_sid = str(p[idx]) if has_except else None
                    for r in self.sessions.values():
                        if (
                            r["EstaActiva"] == 1
                            and str(r["UsuarioID"]).lower() in cands
                            and (utype is None or r["TipoUsuario"].strip().lower() == utype)
                            and (exc_sid is None or r["SesionID"] != exc_sid)
                        ):
                            r["EstaActiva"] = 0
                            r["FechaRevocacion"] = self._now()
                            r["MotivoRevocacion"] = reason
                            r["RevocadoPorUsuarioID"] = revoked_by
                    return []

            raise AssertionError(f"Unexpected SQL in test fake: {q} params={p}")

    def execute_atomic_rotation_sync(
        self,
        *,
        old_session_id: str,
        new_session_id: str,
        familia_id: str,
        user_id: str,
        new_token_hash: str,
        old_token_hash: Optional[str],
        expires_at_str: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        user_type: str,
    ) -> bool:
        with self.lock:
            row = self.sessions.get(str(old_session_id))
            if (
                not row
                or row["EstaActiva"] != 1
                or row["FechaRevocacion"] is not None
                or row["FechaExpiracion"] <= self._now()
                or (old_token_hash and row["RefreshTokenHash"] != old_token_hash)
            ):
                return False

            row["EstaActiva"] = 0
            row["FechaRevocacion"] = self._now()
            row["MotivoRevocacion"] = "token_rotated"
            row["ReemplazadaPorSesionID"] = str(new_session_id)

            exp_dt = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            self.sessions[str(new_session_id)] = {
                "SesionID": str(new_session_id),
                "UsuarioID": str(user_id),
                "TipoUsuario": str(user_type),
                "RefreshTokenHash": str(new_token_hash),
                "FamiliaTokenID": str(familia_id),
                "FechaCreacion": self._now(),
                "FechaExpiracion": exp_dt,
                "UltimaActividad": self._now(),
                "EstaActiva": 1,
                "FechaRevocacion": None,
                "MotivoRevocacion": None,
                "ReemplazadaPorSesionID": None,
                "RevocadoPorUsuarioID": None,
                "IPCliente": ip_address,
                "UserAgent": user_agent,
            }
            return True


@pytest.fixture
def auth_env(monkeypatch):
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.edarsa.test,http://localhost:3000")

    db = InMemorySesionesDB()
    monkeypatch.setattr(rt, "_execute_sql_async", db.execute_sql_async)
    monkeypatch.setattr(rt, "_execute_atomic_rotation_sync", db.execute_atomic_rotation_sync)

    user_uuid = "11111111-1111-1111-1111-111111111111"
    user_record = {
        "id": user_uuid,
        "usuario_id": 8,
        "UsuarioID": 8,
        "public_uuid": user_uuid,
        "PublicUUID": user_uuid,
        "email": "ricardo@edarsa.com.mx",
        "name": "Ricardo Test",
        "role": "SuperAdministrador",
        "role_code": "SUPERADMIN",
        "active": True,
    }

    async def _fake_login_user(email: str, password: str):
        if email != user_record["email"] or password != "ValidPass123!":
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        return {"token": "legacy-ignored", "user": dict(user_record)}

    async def _fake_get_user_by_id(uid):
        if str(uid).lower() in (user_uuid, "8"):
            return dict(user_record)
        return None

    async def _fake_get_user_sql_only(email: str, user_id_from_token=None):
        if email == user_record["email"] or str(user_id_from_token or "").lower() in (user_uuid, "8"):
            return dict(user_record), "SQL_USUARIO_CATALOGO"
        return None, "SQL_NOT_FOUND"

    monkeypatch.setattr(auth_routes.service, "login_user", _fake_login_user)
    monkeypatch.setattr(auth_routes.service, "get_user_by_id", _fake_get_user_by_id)
    monkeypatch.setattr(sec, "_get_user_sql_only", _fake_get_user_sql_only)

    app = FastAPI()
    app.include_router(auth_routes.router, prefix="/api")
    app.include_router(cc_routes.router)
    return app, db, user_record


def test_static_no_insecure_python_hash_in_auth_routes():
    repo_root = Path(__file__).resolve().parents[2]
    src = (repo_root / "backend/modules/auth/routes.py").read_text(encoding="utf-8")
    assert "hash(str(" not in src, "hash(str(user_id)) inseguro no debe existir en auth/routes.py"
    assert "% 2147483647" not in src


def test_login_valid_and_fail_closed_when_session_creation_fails(auth_env):
    app, db, _ = auth_env
    client = TestClient(app)

    # 1. Login valido crea sesion en dbo.Sesiones y emite JWT con sid + refresh cookie
    r = client.post("/api/auth/login", json={"email": "ricardo@edarsa.com.mx", "password": "ValidPass123!"})
    assert r.status_code == 200
    body = r.json()
    token = body["token"]
    payload = sec.verify_token(token)
    assert payload.get("sid"), "El access token de login debe estar vinculado a SesionID (sid)"
    assert payload["sid"] in db.sessions
    assert db.sessions[payload["sid"]]["EstaActiva"] == 1
    assert rt.REFRESH_COOKIE_NAME in r.cookies
    assert sec.AUTH_COOKIE_NAME in r.cookies

    # 2. Fail-closed: si falla la creacion de sesion en SQL, login NO debe emitir token no revocable
    db.fail_on_next_op = "INSERT INTO SESIONES"
    r_fail = client.post("/api/auth/login", json={"email": "ricardo@edarsa.com.mx", "password": "ValidPass123!"})
    assert r_fail.status_code == 503
    assert "token" not in r_fail.json()


def test_logout_individual_immediate_revocation_and_me_does_not_remint(auth_env):
    app, db, _ = auth_env
    client = TestClient(app)

    login_r = client.post("/api/auth/login", json={"email": "ricardo@edarsa.com.mx", "password": "ValidPass123!"})
    assert login_r.status_code == 200
    tok = login_r.json()["token"]
    sid = sec.verify_token(tok)["sid"]

    # Antes de logout: /auth/me devuelve exactamente el mismo token vigente (sin mintear uno nuevo)
    me_before = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert me_before.status_code == 200
    assert me_before.json()["token"] == tok
    assert me_before.json()["email"] == "ricardo@edarsa.com.mx"
    assert "_session_id" not in me_before.json()

    # Logout individual
    lo = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {tok}"})
    assert lo.status_code == 200
    assert db.sessions[sid]["EstaActiva"] == 0
    assert db.sessions[sid]["MotivoRevocacion"] == "logout"

    # Revocacion inmediata: /auth/me con el JWT previo debe fallar con 401 y NUNCA regenerar token
    me_after = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert me_after.status_code == 401

    # Tambien con cookie copiada del access token revocado -> 401
    stolen = TestClient(app)
    stolen.cookies.set(sec.AUTH_COOKIE_NAME, tok)
    assert stolen.get("/api/auth/me").status_code == 401


def test_logout_via_bearer_only_without_refresh_cookie_revokes_sid(auth_env):
    app, db, _ = auth_env
    c_login = TestClient(app)
    tok = c_login.post("/api/auth/login", json={"email": "ricardo@edarsa.com.mx", "password": "ValidPass123!"}).json()["token"]
    sid = sec.verify_token(tok)["sid"]

    # Cliente sin cookie de refresh (solo Authorization: Bearer) hace logout
    c_bearer = TestClient(app)
    r = c_bearer.post("/api/auth/logout", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert db.sessions[sid]["EstaActiva"] == 0
    assert c_bearer.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"}).status_code == 401


def test_concurrent_sessions_individual_logout_and_logout_all_preserves_mcp(auth_env):
    app, db, user_record = auth_env

    # Insertar una sesion tecnica mcp_service del mismo usuario para confirmar que logout-all interno no la rompe
    db.sessions["mcp-svc-1"] = {
        "SesionID": "mcp-svc-1",
        "UsuarioID": user_record["id"],
        "TipoUsuario": "mcp_service",
        "RefreshTokenHash": "hash-mcp-service",
        "FamiliaTokenID": "fam-mcp",
        "FechaCreacion": datetime.now(timezone.utc),
        "FechaExpiracion": datetime.now(timezone.utc) + timedelta(days=1),
        "UltimaActividad": datetime.now(timezone.utc),
        "EstaActiva": 1,
        "FechaRevocacion": None,
        "MotivoRevocacion": None,
        "ReemplazadaPorSesionID": None,
        "RevocadoPorUsuarioID": None,
        "IPCliente": None,
        "UserAgent": None,
    }

    # Tres sesiones concurrentes del mismo usuario (UUID)
    c1, c2, c3 = TestClient(app), TestClient(app), TestClient(app)
    t1 = c1.post("/api/auth/login", json={"email": "ricardo@edarsa.com.mx", "password": "ValidPass123!"}).json()["token"]
    t2 = c2.post("/api/auth/login", json={"email": "ricardo@edarsa.com.mx", "password": "ValidPass123!"}).json()["token"]
    t3 = c3.post("/api/auth/login", json={"email": "ricardo@edarsa.com.mx", "password": "ValidPass123!"}).json()["token"]

    # Logout individual en dispositivo 1: solo revoca sesion 1; sesiones 2 y 3 siguen activas
    assert c1.post("/api/auth/logout").status_code == 200
    assert c1.get("/api/auth/me", headers={"Authorization": f"Bearer {t1}"}).status_code == 401
    assert c2.get("/api/auth/me", headers={"Authorization": f"Bearer {t2}"}).status_code == 200
    assert c3.get("/api/auth/me", headers={"Authorization": f"Bearer {t3}"}).status_code == 200

    # Logout-all desde dispositivo 2: revoca sesiones 2 y 3 (UUID sin hash())
    la = c2.post("/api/auth/logout-all", headers={"Authorization": f"Bearer {t2}"})
    assert la.status_code == 200
    assert la.json()["sessions_revoked"] == 2

    # Ambas sesiones quedan inmediatamente revocadas
    assert c2.get("/api/auth/me", headers={"Authorization": f"Bearer {t2}"}).status_code == 401
    assert c3.get("/api/auth/me", headers={"Authorization": f"Bearer {t3}"}).status_code == 401
    assert c3.post("/api/auth/refresh").status_code == 401

    # La sesion tecnica mcp_service permanece intacta
    assert db.sessions["mcp-svc-1"]["EstaActiva"] == 1


def test_refresh_rotation_and_sequential_replay_revokes_entire_family(auth_env):
    app, db, _ = auth_env
    client = TestClient(app)

    r_login = client.post("/api/auth/login", json={"email": "ricardo@edarsa.com.mx", "password": "ValidPass123!"})
    tok1 = r_login.json()["token"]
    sid1 = sec.verify_token(tok1)["sid"]
    old_refresh_cookie = r_login.cookies.get(rt.REFRESH_COOKIE_NAME)
    assert old_refresh_cookie

    # Rotacion legitima: invalida sid1, crea sid2, devuelve tok2 vinculado a sid2
    r_ref = client.post("/api/auth/refresh")
    assert r_ref.status_code == 200
    tok2 = r_ref.json()["token"]
    sid2 = sec.verify_token(tok2)["sid"]
    assert sid2 != sid1
    assert db.sessions[sid1]["EstaActiva"] == 0
    assert db.sessions[sid2]["EstaActiva"] == 1

    # tok1 ya no es valido inmediatamente; tok2 si
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok1}"}).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok2}"}).status_code == 200

    # Replay del refresh token anterior -> 401 y revoca TODA la familia (incluyendo sid2)
    attacker = TestClient(app)
    attacker.cookies.set(rt.REFRESH_COOKIE_NAME, old_refresh_cookie)
    r_replay = attacker.post("/api/auth/refresh")
    assert r_replay.status_code == 401
    assert db.sessions[sid2]["EstaActiva"] == 0
    assert db.sessions[sid2]["MotivoRevocacion"] == "replay_detected"
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok2}"}).status_code == 401


@pytest.mark.asyncio
async def test_concurrent_refresh_rotation_is_atomic_and_rejects_second_caller(auth_env):
    _, db, user_record = auth_env
    initial_refresh = rt.generate_refresh_token()
    s1 = await rt.create_session(user_id=user_record["id"], refresh_token=initial_refresh, user_type="interno")

    # Dos llamadas concurrentes con el mismo old_session_id / refresh token
    t_new_a = rt.generate_refresh_token()
    t_new_b = rt.generate_refresh_token()

    outcomes = await asyncio.gather(
        rt.rotate_refresh_token(
            old_session_id=s1["session_id"],
            familia_id=s1["familia_id"],
            user_id=user_record["id"],
            new_refresh_token=t_new_a,
            old_refresh_token=initial_refresh,
        ),
        rt.rotate_refresh_token(
            old_session_id=s1["session_id"],
            familia_id=s1["familia_id"],
            user_id=user_record["id"],
            new_refresh_token=t_new_b,
            old_refresh_token=initial_refresh,
        ),
        return_exceptions=True,
    )

    successes = [o for o in outcomes if isinstance(o, dict)]
    reuse_errors = [o for o in outcomes if isinstance(o, rt.RefreshTokenReuseError)]
    assert len(successes) == 1, f"Exactamente 1 rotacion debe ganar: {outcomes}"
    assert len(reuse_errors) == 1, f"La segunda rotacion concurrente debe lanzar RefreshTokenReuseError: {outcomes}"

    # Al detectarse el replay concurrente, toda la familia queda revocada fail-closed
    active_in_family = [
        r for r in db.sessions.values()
        if r["FamiliaTokenID"] == s1["familia_id"] and r["EstaActiva"] == 1
    ]
    assert active_in_family == []


@pytest.mark.asyncio
async def test_expired_jwt_and_sql_error_fail_closed_in_get_current_user(auth_env):
    _, db, user_record = auth_env

    # 1. JWT expirado -> 401
    expired_tok = pyjwt.encode(
        {
            "sub": user_record["id"],
            "user_id": user_record["id"],
            "email": user_record["email"],
            "role": user_record["role"],
            "type": "internal",
            "sid": "expired-sid",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        sec.JWT_SECRET,
        algorithm=sec.JWT_ALGORITHM,
    )
    with pytest.raises(Exception) as exc_exp:
        await sec.get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_tok))
    assert getattr(exc_exp.value, "status_code", None) == 401

    # 2. JWT con sid valido pero SQL falla al validar sesion -> 401 fail-closed
    active_tok = sec.create_access_token(
        user_record["id"],
        user_record["email"],
        user_record["role"],
        token_type="internal",
        usuario_id=8,
        public_uuid=user_record["id"],
        session_id="sid-sql-err",
    )
    db.raise_on_is_active = True
    with pytest.raises(Exception) as exc_sql:
        await sec.get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=active_tok))
    assert getattr(exc_sql.value, "status_code", None) == 401


def test_websocket_p1_1_regression_rejects_revoked_session_and_accepts_active(auth_env, monkeypatch):
    app, db, _ = auth_env
    mgr = NotificationManager()
    monkeypatch.setattr(cc_routes, "get_notification_manager", lambda: mgr)
    monkeypatch.setattr(cc_routes, "_has_explicit_ws_permission_sql", lambda email, perm: perm == "CENTRO_CONTROL_VER")

    client = TestClient(app)
    login_r = client.post("/api/auth/login", json={"email": "ricardo@edarsa.com.mx", "password": "ValidPass123!"})
    tok = login_r.json()["token"]

    # Sesion activa -> WebSocket P1-1 conecta y responde ping/pong
    with client.websocket_connect(
        "/api/centro-control/ws",
        headers={"origin": "https://app.edarsa.test", "authorization": f"Bearer {tok}"},
    ) as ws:
        welcome = ws.receive_json()
        assert welcome["tipo"] == "conexion_establecida"
        ws.send_json({"tipo": "ping"})
        assert ws.receive_json()["tipo"] == "pong"

    # Tras logout -> el mismo JWT con sid revocado es rechazado por WebSocket con 1008
    assert client.post("/api/auth/logout", headers={"Authorization": f"Bearer {tok}"}).status_code == 200
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            "/api/centro-control/ws",
            headers={"origin": "https://app.edarsa.test", "authorization": f"Bearer {tok}"},
        ):
            pass
    assert exc_info.value.code == 1008
    assert mgr.connection_count == 0

def test_logout_and_logout_all_fail_closed_on_sql_error(auth_env):
    app, db, _ = auth_env
    client = TestClient(app)

    tok = client.post("/api/auth/login", json={"email": "ricardo@edarsa.com.mx", "password": "ValidPass123!"}).json()["token"]

    # Fallo SQL durante logout -> 503 fail-closed (no 200 silencioso)
    db.fail_on_next_op = "UPDATE SESIONES"
    r_lo = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {tok}"})
    assert r_lo.status_code == 503

    # Fallo SQL durante logout-all -> 503 fail-closed (no 200 con sessions_revoked=0)
    db.fail_on_next_op = "UPDATE SESIONES"
    r_la = client.post("/api/auth/logout-all", headers={"Authorization": f"Bearer {tok}"})
    assert r_la.status_code == 503


def test_legacy_token_without_sid_compatible_and_me_blocks_revoked_refresh_cookie(auth_env):
    app, db, user_record = auth_env
    client = TestClient(app)

    # Token tecnico/legacy sin claim 'sid' conserva compatibilidad con create_access_token
    legacy_tok = sec.create_access_token(
        user_record["id"],
        user_record["email"],
        user_record["role"],
        token_type="internal",
        usuario_id=8,
        public_uuid=user_record["id"],
    )
    assert "sid" not in sec.verify_token(legacy_tok)
    r_ok = client.get("/api/auth/me", headers={"Authorization": f"Bearer {legacy_tok}"})
    assert r_ok.status_code == 200
    assert r_ok.json()["token"] == legacy_tok

    # Defensa en profundidad: si trae cookie refresh de una sesion ya revocada -> 401
    c_rev = TestClient(app)
    r_login = c_rev.post("/api/auth/login", json={"email": "ricardo@edarsa.com.mx", "password": "ValidPass123!"})
    revoked_refresh = r_login.cookies.get(rt.REFRESH_COOKIE_NAME)
    assert c_rev.post("/api/auth/logout").status_code == 200

    c_mix = TestClient(app)
    c_mix.cookies.set(rt.REFRESH_COOKIE_NAME, revoked_refresh)
    r_block = c_mix.get("/api/auth/me", headers={"Authorization": f"Bearer {legacy_tok}"})
    assert r_block.status_code == 401


def test_frontend_auth_clients_compatibility_contract():
    repo_root = Path(__file__).resolve().parents[2]
    auth_ctx = (repo_root / "frontend/src/contexts/AuthContext.jsx").read_text(encoding="utf-8")
    api_js = (repo_root / "frontend/src/lib/api.js").read_text(encoding="utf-8")
    assert "api.get('/auth/me')" in auth_ctx
    assert "api.post('/auth/login'" in auth_ctx
    assert "api.post('/auth/logout')" in auth_ctx
    assert "serverUser.token" in auth_ctx
    assert "/auth/refresh" in api_js
    assert "resp.data?.token" in api_js
