"""Canonical service-credential exchange for the Universal Worker MCP.

Reuses dbo.Sesiones, Usuario_Catalogo, canonical SQL RBAC and the existing
short-lived EDARSAHUB access-token issuer. It does not create sessions,
roles, permissions, tables, or another authentication store.
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
import hashlib
from typing import Any

from core.rbac_sql.service import RBACSQLService
from core.security import ACCESS_TOKEN_MINUTES, create_access_token
from core.sql_first.db import get_sql_connection
from modules.auth.repository import AuthRepository
from modules.worker_mcp.oauth_pkce import OAuthValidationError, validate_scopes
from modules.worker_mcp.oauth_security import SUPPORTED_SCOPES, validate_grant
from modules.worker_mcp.oauth_server import (
    decode_mcp_service_token_claims,
    mint_scoped_internal_access_token,
    resolve_identity_scopes,
)


SERVICE_SESSION_TYPE = "mcp_service"
REQUIRED_PERMISSION = "RBAC_ADMIN"
_LEGACY_OPAQUE_RESOURCE = "https://edarsahub.internal/api/mcp"


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


def _coerce_utc_datetime(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return raw.replace(tzinfo=timezone.utc)
        return raw.astimezone(timezone.utc)
    if isinstance(raw, date):
        return datetime.combine(raw, time.max, tzinfo=timezone.utc)
    text = str(raw or "").strip()
    if not text:
        raise WorkerServiceCredentialError("SERVICE_SESSION_EXPIRATION_INVALID")
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise WorkerServiceCredentialError(
            "SERVICE_SESSION_EXPIRATION_INVALID"
        ) from exc
    if parsed.tzinfo is None:
        if len(text) == 10:
            parsed = datetime.combine(parsed.date(), time.max)
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def exchange_service_credential(credential: str) -> dict[str, Any]:
    """Exchange one active MCP service credential for a short internal JWT."""
    raw_credential = str(credential or "").strip()
    session = _resolve_active_service_session(raw_credential)
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

    session_expires_at = _coerce_utc_datetime(session.get("FechaExpiracion"))
    session_revoked = not bool(session.get("EstaActiva", 1))
    identity_scopes = resolve_identity_scopes(user)
    if not identity_scopes:
        raise WorkerServiceCredentialError("SERVICE_PERMISSION_DENIED")

    token_resource: str | None = None
    effective_expires_at = session_expires_at

    if "." in raw_credential:
        try:
            claims = decode_mcp_service_token_claims(raw_credential)
            claim_uid = int(claims.get("uid") or 0)
            claim_exp = datetime.fromtimestamp(
                int(claims["exp"]),
                tz=timezone.utc,
            )
        except (OAuthValidationError, ValueError, KeyError, TypeError) as exc:
            raise WorkerServiceCredentialError(
                "SERVICE_CREDENTIAL_INVALID"
            ) from exc

        if claim_uid != int(sql_user_id):
            raise WorkerServiceCredentialError("SERVICE_IDENTITY_MISMATCH")

        effective_expires_at = min(session_expires_at, claim_exp)
        token_scope_str = str(claims.get("scope") or "").strip()
        token_resource = str(claims.get("resource") or "").strip()
        try:
            consented_scopes = validate_scopes(
                token_scope_str,
                SUPPORTED_SCOPES,
            )
            granted_scopes = validate_grant(
                requested_scopes=token_scope_str,
                identity_scopes=identity_scopes,
                consented_scopes=consented_scopes,
                resource=token_resource,
                registered_resource=token_resource,
                expires_at=effective_expires_at,
                revoked=session_revoked,
            )
        except OAuthValidationError as exc:
            if str(exc) in {
                "SCOPES_FORBIDDEN",
                "CONSENT_REQUIRED",
                "INSUFFICIENT_SCOPE",
            }:
                raise WorkerServiceCredentialError(
                    "SERVICE_PERMISSION_DENIED"
                ) from exc
            raise WorkerServiceCredentialError(
                "SERVICE_CREDENTIAL_INVALID"
            ) from exc

        access_token = mint_scoped_internal_access_token(
            user_id=user_id,
            email=email,
            role=role,
            scopes=granted_scopes,
            resource=token_resource,
            usuario_id=int(sql_user_id),
            public_uuid=public_user_id,
        )
    else:
        try:
            granted_scopes = validate_grant(
                requested_scopes=" ".join(sorted(identity_scopes)),
                identity_scopes=identity_scopes,
                consented_scopes=identity_scopes,
                resource=_LEGACY_OPAQUE_RESOURCE,
                registered_resource=_LEGACY_OPAQUE_RESOURCE,
                expires_at=session_expires_at,
                revoked=session_revoked,
            )
        except OAuthValidationError as exc:
            raise WorkerServiceCredentialError(
                "SERVICE_CREDENTIAL_INVALID"
            ) from exc

        if granted_scopes == SUPPORTED_SCOPES:
            access_token = create_access_token(
                user_id,
                email,
                role,
                token_type="internal",
            )
        else:
            access_token = mint_scoped_internal_access_token(
                user_id=user_id,
                email=email,
                role=role,
                scopes=granted_scopes,
                resource=None,
                usuario_id=int(sql_user_id),
                public_uuid=public_user_id,
            )

    ordered_scopes = sorted(granted_scopes)
    response: dict[str, Any] = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": int(ACCESS_TOKEN_MINUTES) * 60,
        "scope": " ".join(ordered_scopes),
        "scopes": ordered_scopes,
        "expires_at": int(effective_expires_at.timestamp()),
    }
    if token_resource:
        response["resource"] = token_resource
    return response
