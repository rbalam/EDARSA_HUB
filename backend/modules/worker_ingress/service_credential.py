"""Canonical service-credential exchange for the Universal Worker MCP.

Reuses dbo.Sesiones, Usuario_Catalogo, canonical SQL RBAC and the existing
short-lived EDARSAHUB access-token issuer. It does not create sessions,
roles, permissions, tables, or another authentication store.
"""
from __future__ import annotations

import hashlib
from typing import Any

from core.rbac_sql.service import RBACSQLService
from core.security import ACCESS_TOKEN_MINUTES, create_access_token
from core.sql_first.db import get_sql_connection
from modules.auth.repository import AuthRepository


SERVICE_SESSION_TYPE = "mcp_service"
REQUIRED_PERMISSION = "RBAC_ADMIN"


class WorkerServiceCredentialError(ValueError):
    """Fail-closed service credential validation error."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _credential_hash(credential: str) -> str:
    value = str(credential or "").strip()
    if not value:
        raise WorkerServiceCredentialError("SERVICE_CREDENTIAL_REQUIRED")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _resolve_active_service_session(credential: str) -> dict[str, Any]:
    digest = _credential_hash(credential)
    conn = get_sql_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT TOP 2
                SesionID,
                UsuarioID,
                TipoUsuario,
                FechaExpiracion,
                EstaActiva
            FROM dbo.Sesiones
            WHERE RefreshTokenHash = %s
              AND LOWER(LTRIM(RTRIM(ISNULL(TipoUsuario, '')))) = %s
              AND ISNULL(EstaActiva, 0) = 1
              AND FechaExpiracion > GETUTCDATE()
              AND FechaRevocacion IS NULL
            ORDER BY FechaCreacion DESC, SesionID DESC
            """,
            (digest, SERVICE_SESSION_TYPE),
        )
        rows = cur.fetchall()
        columns = [item[0] for item in cur.description] if cur.description else []
    finally:
        conn.close()

    if len(rows) != 1:
        raise WorkerServiceCredentialError("SERVICE_CREDENTIAL_INVALID")

    return dict(zip(columns, rows[0]))


def exchange_service_credential(credential: str) -> dict[str, Any]:
    """Exchange one active opaque MCP credential for a short internal JWT."""
    session = _resolve_active_service_session(credential)
    public_user_id = str(session.get("UsuarioID") or "").strip()
    if not public_user_id:
        raise WorkerServiceCredentialError("SERVICE_IDENTITY_MISSING")

    user = AuthRepository.get_user_by_id(public_user_id)
    if not user or not bool(user.get("active")):
        raise WorkerServiceCredentialError("SERVICE_IDENTITY_INACTIVE")

    sql_user_id = user.get("_sql_usuario_id") or user.get("UsuarioID")
    if not sql_user_id:
        raise WorkerServiceCredentialError("SERVICE_SQL_IDENTITY_MISSING")

    if not RBACSQLService.can_access_permission(
        sql_user_id,
        REQUIRED_PERMISSION,
    ):
        raise WorkerServiceCredentialError("SERVICE_PERMISSION_DENIED")

    email = str(user.get("email") or "").strip().lower()
    user_id = str(user.get("id") or "").strip()
    role = str(user.get("role") or "Usuario").strip() or "Usuario"
    if not email or not user_id:
        raise WorkerServiceCredentialError("SERVICE_IDENTITY_INCOMPLETE")

    access_token = create_access_token(
        user_id,
        email,
        role,
        token_type="internal",
    )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": int(ACCESS_TOKEN_MINUTES) * 60,
    }
