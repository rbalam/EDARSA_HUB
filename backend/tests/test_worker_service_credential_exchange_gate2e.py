from __future__ import annotations

import hashlib

import pytest

from modules.worker_ingress import service_credential as svc


class _Cursor:
    def __init__(self, rows):
        self._rows = rows
        self.description = [
            ("SesionID",),
            ("UsuarioID",),
            ("TipoUsuario",),
            ("FechaExpiracion",),
            ("EstaActiva",),
        ]
        self.sql = ""
        self.params = ()

    def execute(self, sql, params):
        self.sql = sql
        self.params = tuple(params)

    def fetchall(self):
        return list(self._rows)


class _Connection:
    def __init__(self, rows):
        self.cursor_obj = _Cursor(rows)
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def close(self):
        self.closed = True


def _session(public_uuid="11111111-1111-1111-1111-111111111111"):
    return (
        "session-1",
        public_uuid,
        "mcp_service",
        "2027-10-05",
        1,
    )


def _user(*, active=True):
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "UsuarioID": 8,
        "_sql_usuario_id": 8,
        "email": "admin@example.com",
        "role": "SuperAdministrador",
        "active": active,
    }


def test_empty_credential_fails_closed():
    with pytest.raises(
        svc.WorkerServiceCredentialError,
        match="SERVICE_CREDENTIAL_REQUIRED",
    ):
        svc.exchange_service_credential("")


def test_query_requires_service_type_active_unexpired_and_not_revoked(
    monkeypatch,
):
    conn = _Connection([_session()])
    monkeypatch.setattr(svc, "get_sql_connection", lambda: conn)
    monkeypatch.setattr(
        svc.AuthRepository,
        "get_user_by_id",
        lambda value: _user(),
    )
    monkeypatch.setattr(
        svc.RBACSQLService,
        "can_access_permission",
        lambda user_id, permission: True,
    )
    monkeypatch.setattr(
        svc,
        "create_access_token",
        lambda *args, **kwargs: "short-jwt",
    )

    result = svc.exchange_service_credential("opaque-secret")

    sql = conn.cursor_obj.sql
    normalized_sql = " ".join(sql.split())
    assert "LOWER(LTRIM(RTRIM(ISNULL(TipoUsuario, ''))))" in normalized_sql
    assert "LOWER(LTRIM(RTRIM(%s)))" in normalized_sql
    assert "ISNULL(EstaActiva, 0) = 1" in sql
    assert "FechaExpiracion > GETUTCDATE()" in sql
    assert "FechaRevocacion IS NULL" in sql
    assert conn.cursor_obj.params == (
        hashlib.sha256(b"opaque-secret").hexdigest(),
        "mcp_service",
    )
    assert result["access_token"] == "short-jwt"
    assert result["expires_in"] == int(svc.ACCESS_TOKEN_MINUTES) * 60
    assert conn.closed is True


def test_missing_or_ambiguous_session_fails_closed(monkeypatch):
    for rows in ([], [_session(), _session()]):
        conn = _Connection(rows)
        monkeypatch.setattr(svc, "get_sql_connection", lambda: conn)

        with pytest.raises(
            svc.WorkerServiceCredentialError,
            match="SERVICE_CREDENTIAL_INVALID",
        ):
            svc.exchange_service_credential("opaque-secret")


def test_inactive_user_fails_closed(monkeypatch):
    conn = _Connection([_session()])
    monkeypatch.setattr(svc, "get_sql_connection", lambda: conn)
    monkeypatch.setattr(
        svc.AuthRepository,
        "get_user_by_id",
        lambda value: _user(active=False),
    )

    with pytest.raises(
        svc.WorkerServiceCredentialError,
        match="SERVICE_IDENTITY_INACTIVE",
    ):
        svc.exchange_service_credential("opaque-secret")


def test_missing_rbac_admin_fails_closed(monkeypatch):
    conn = _Connection([_session()])
    monkeypatch.setattr(svc, "get_sql_connection", lambda: conn)
    monkeypatch.setattr(
        svc.AuthRepository,
        "get_user_by_id",
        lambda value: _user(),
    )
    monkeypatch.setattr(
        svc.RBACSQLService,
        "can_access_permission",
        lambda user_id, permission: False,
    )

    with pytest.raises(
        svc.WorkerServiceCredentialError,
        match="SERVICE_PERMISSION_DENIED",
    ):
        svc.exchange_service_credential("opaque-secret")


def test_success_reuses_short_internal_token_issuer(monkeypatch):
    conn = _Connection([_session()])
    captured = {}

    monkeypatch.setattr(svc, "get_sql_connection", lambda: conn)
    monkeypatch.setattr(
        svc.AuthRepository,
        "get_user_by_id",
        lambda value: _user(),
    )

    def permission(user_id, code):
        captured["permission"] = (user_id, code)
        return True

    def mint(user_id, email, role, token_type="internal"):
        captured["mint"] = (user_id, email, role, token_type)
        return "short-jwt"

    monkeypatch.setattr(
        svc.RBACSQLService,
        "can_access_permission",
        permission,
    )
    monkeypatch.setattr(svc, "create_access_token", mint)

    result = svc.exchange_service_credential("opaque-secret")

    assert captured["permission"] == (8, "RBAC_ADMIN")
    assert captured["mint"] == (
        "11111111-1111-1111-1111-111111111111",
        "admin@example.com",
        "SuperAdministrador",
        "internal",
    )
    assert result["access_token"] == "short-jwt"
    assert result["token_type"] == "Bearer"


def test_module_has_no_credential_creation_or_schema_mutation():
    text = open(svc.__file__, encoding="utf-8").read().lower()

    for forbidden in (
        "insert into dbo.sesiones",
        "update dbo.sesiones",
        "delete from dbo.sesiones",
        "create table",
        "alter table",
        "drop table",
        "jwt_secret",
    ):
        assert forbidden not in text
