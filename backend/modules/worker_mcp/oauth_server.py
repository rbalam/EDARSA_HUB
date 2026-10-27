"""OAuth 2.1-style authorization server boundary for EDARSAHUB Worker MCP.

Reuses the canonical EDARSAHUB user session/RBAC system and dbo.Sesiones.
No second user directory, role model, or credential store is introduced.
"""
from __future__ import annotations

import hashlib
import html
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode, urlsplit

import jwt
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from core.rbac_sql.service import RBACSQLService
from core.security import JWT_ALGORITHM, JWT_SECRET, get_current_user_dual
from core.sql_first.db import get_sql_connection
from modules.auth.repository import AuthRepository

from .oauth_discovery import MCP_SCOPES, authorization_metadata
from .oauth_pkce import (
    OAuthValidationError,
    validate_pkce_challenge,
    validate_redirect_uri,
    validate_scopes,
    verify_pkce,
)


router = APIRouter(prefix="/api/mcp/oauth", tags=["worker-mcp-oauth"])

CLIENT_TOKEN_TYPE = "mcp_oauth_client"
CODE_SESSION_TYPE = "mcp_oauth_code"
REFRESH_SESSION_TYPE = "mcp_oauth_refresh"
ACCESS_SESSION_TYPE = "mcp_service"
REQUIRED_PERMISSION = "RBAC_ADMIN"
ACCESS_TTL_SECONDS = 15 * 60
CODE_TTL_SECONDS = 5 * 60
REFRESH_TTL_SECONDS = 7 * 24 * 60 * 60
CLIENT_TTL_SECONDS = 365 * 24 * 60 * 60
_ALLOWED_SCOPES = frozenset(MCP_SCOPES)


class OAuthServerError(ValueError):
    def __init__(self, code: str, *, status_code: int = 400):
        super().__init__(code)
        self.code = code
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _public_origin(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def _issuer(request: Request) -> str:
    return _public_origin(request) + "/api/mcp/oauth"


def _resource(request: Request) -> str:
    return _public_origin(request) + "/api/mcp"


def _token_hash(token: str) -> str:
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


def _sign(kind: str, claims: dict[str, Any], ttl_seconds: int) -> str:
    now = _now()
    payload = {
        "typ": kind,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        **claims,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise OAuthServerError("invalid_grant") from exc
    if str(payload.get("typ") or "") != expected_type:
        raise OAuthServerError("invalid_grant")
    return payload


def _validate_https_redirect(uri: str) -> str:
    value = str(uri or "").strip()
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.fragment
    ):
        raise OAuthServerError("invalid_redirect_uri")
    return value


def _register_client_id(
    *,
    redirect_uris: tuple[str, ...],
    client_name: str,
) -> str:
    return _sign(
        CLIENT_TOKEN_TYPE,
        {
            "redirect_uris": list(redirect_uris),
            "client_name": client_name[:120],
            "token_endpoint_auth_method": "none",
        },
        CLIENT_TTL_SECONDS,
    )


def _client_registration(client_id: str) -> dict[str, Any]:
    payload = _decode(client_id, CLIENT_TOKEN_TYPE)
    redirects = tuple(
        str(item).strip()
        for item in payload.get("redirect_uris") or []
        if str(item).strip()
    )
    if not redirects:
        raise OAuthServerError("invalid_client", status_code=401)
    for uri in redirects:
        _validate_https_redirect(uri)
    return {
        "client_id": client_id,
        "redirect_uris": redirects,
        "client_name": str(payload.get("client_name") or "MCP Client"),
    }


def _insert_session_token(
    *,
    user_id: int,
    token: str,
    session_type: str,
    ttl_seconds: int,
    family_id: str | None = None,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> dict[str, str]:
    session_id = secrets.token_hex(16)
    family = family_id or secrets.token_hex(16)
    expires_at = _now() + timedelta(seconds=ttl_seconds)
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO dbo.Sesiones (
                SesionID, UsuarioID, TipoUsuario, RefreshTokenHash,
                FamiliaTokenID, FechaCreacion, FechaExpiracion,
                UltimaActividad, EstaActiva, IPCliente, UserAgent,
                FechaModificacion
            ) VALUES (
                %s, %s, %s, %s, %s, GETUTCDATE(), %s,
                GETUTCDATE(), 1, %s, %s, GETUTCDATE()
            )
            """,
            (
                session_id,
                int(user_id),
                session_type,
                _token_hash(token),
                family,
                expires_at,
                (ip_address or "")[:45] or None,
                (user_agent or "")[:500] or None,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return {"session_id": session_id, "family_id": family}


def _consume_session_token(
    token: str,
    expected_type: str,
) -> dict[str, Any]:
    digest = _token_hash(token)
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT TOP 2
                SesionID, UsuarioID, TipoUsuario, FamiliaTokenID
            FROM dbo.Sesiones
            WHERE RefreshTokenHash = %s
              AND LOWER(LTRIM(RTRIM(ISNULL(TipoUsuario, '')))) = %s
              AND ISNULL(EstaActiva, 0) = 1
              AND FechaExpiracion > GETUTCDATE()
              AND FechaRevocacion IS NULL
            ORDER BY FechaCreacion DESC, SesionID DESC
            """,
            (digest, expected_type),
        )
        rows = cur.fetchall()
        cols = [item[0] for item in cur.description] if cur.description else []
        if len(rows) != 1:
            raise OAuthServerError("invalid_grant")
        record = dict(zip(cols, rows[0]))
        cur.execute(
            """
            UPDATE dbo.Sesiones
            SET EstaActiva = 0,
                FechaRevocacion = GETUTCDATE(),
                MotivoRevocacion = 'oauth_consumed',
                FechaModificacion = GETUTCDATE()
            WHERE SesionID = %s
              AND EstaActiva = 1
            """,
            (record["SesionID"],),
        )
        conn.commit()
        return record
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def _sql_user_id(user: dict[str, Any]) -> int:
    raw = (
        user.get("_sql_usuario_id")
        or user.get("usuario_id")
        or user.get("UsuarioID")
    )
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise OAuthServerError("identity_missing", status_code=403) from exc
    if value <= 0:
        raise OAuthServerError("identity_missing", status_code=403)
    return value


def _require_worker_permission(user_id: int) -> None:
    if not RBACSQLService.can_access_permission(user_id, REQUIRED_PERMISSION):
        raise OAuthServerError("access_denied", status_code=403)


def _user_for_id(user_id: int) -> dict[str, Any]:
    user = AuthRepository.get_user_by_id(str(user_id))
    if not user or not bool(user.get("active")):
        raise OAuthServerError("access_denied", status_code=403)
    _require_worker_permission(user_id)
    return user


def _request_context(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


def _issue_access_token(
    *,
    user_id: int,
    request: Request,
) -> str:
    token = secrets.token_urlsafe(48)
    ip, ua = _request_context(request)
    _insert_session_token(
        user_id=user_id,
        token=token,
        session_type=ACCESS_SESSION_TYPE,
        ttl_seconds=ACCESS_TTL_SECONDS,
        user_agent=ua,
        ip_address=ip,
    )
    return token


def _issue_refresh_token(
    *,
    user_id: int,
    client_id: str,
    scopes: frozenset[str],
    resource: str,
    request: Request,
    family_id: str | None = None,
) -> str:
    token = _sign(
        REFRESH_SESSION_TYPE,
        {
            "uid": int(user_id),
            "client_id_hash": _token_hash(client_id),
            "scope": " ".join(sorted(scopes)),
            "resource": resource,
            "nonce": secrets.token_urlsafe(16),
        },
        REFRESH_TTL_SECONDS,
    )
    ip, ua = _request_context(request)
    _insert_session_token(
        user_id=user_id,
        token=token,
        session_type=REFRESH_SESSION_TYPE,
        ttl_seconds=REFRESH_TTL_SECONDS,
        family_id=family_id,
        user_agent=ua,
        ip_address=ip,
    )
    return token


def _oauth_error(code: str, *, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": code},
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@router.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_metadata(request: Request):
    issuer = _issuer(request)
    payload = authorization_metadata(issuer)
    payload["registration_endpoint"] = issuer + "/register"
    return JSONResponse(payload)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def oauth_register(request: Request):
    try:
        data = await request.json()
    except Exception:
        return _oauth_error("invalid_client_metadata")

    redirect_values = data.get("redirect_uris") if isinstance(data, dict) else None
    if not isinstance(redirect_values, list) or not redirect_values:
        return _oauth_error("invalid_redirect_uri")

    try:
        redirects = tuple(_validate_https_redirect(item) for item in redirect_values)
    except OAuthServerError as exc:
        return _oauth_error(exc.code)

    response_types = data.get("response_types") or ["code"]
    grant_types = data.get("grant_types") or ["authorization_code", "refresh_token"]
    token_auth = str(data.get("token_endpoint_auth_method") or "none")
    if response_types != ["code"]:
        return _oauth_error("invalid_client_metadata")
    if any(item not in {"authorization_code", "refresh_token"} for item in grant_types):
        return _oauth_error("invalid_client_metadata")
    if token_auth != "none":
        return _oauth_error("invalid_client_metadata")

    client_name = str(data.get("client_name") or "MCP Client").strip() or "MCP Client"
    client_id = _register_client_id(
        redirect_uris=redirects,
        client_name=client_name,
    )
    return JSONResponse(
        status_code=201,
        content={
            "client_id": client_id,
            "client_id_issued_at": int(_now().timestamp()),
            "redirect_uris": list(redirects),
            "client_name": client_name[:120],
            "response_types": ["code"],
            "grant_types": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_method": "none",
        },
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


def _validated_authorization_request(
    request: Request,
    values: dict[str, str],
    user_id: int,
) -> dict[str, Any]:
    if values.get("response_type") != "code":
        raise OAuthServerError("unsupported_response_type")

    client = _client_registration(values.get("client_id", ""))
    redirect_uri = validate_redirect_uri(
        values.get("redirect_uri", ""),
        client["redirect_uris"],
    )
    challenge = validate_pkce_challenge(
        values.get("code_challenge", ""),
        values.get("code_challenge_method", ""),
    )
    _require_worker_permission(user_id)
    scopes = validate_scopes(
        values.get("scope", ""),
        _ALLOWED_SCOPES,
    )
    resource = str(values.get("resource") or _resource(request)).strip()
    if resource != _resource(request):
        raise OAuthServerError("invalid_target")

    return {
        "client": client,
        "redirect_uri": redirect_uri,
        "challenge": challenge,
        "scopes": scopes,
        "resource": resource,
        "state": str(values.get("state") or ""),
    }


def _hidden(name: str, value: str) -> str:
    return (
        '<input type="hidden" name="'
        + html.escape(name, quote=True)
        + '" value="'
        + html.escape(value, quote=True)
        + '">'
    )


@router.get("/authorize", response_class=HTMLResponse)
async def oauth_authorize(request: Request):
    values = {key: value for key, value in request.query_params.items()}
    try:
        user = await get_current_user_dual(request)
    except HTTPException:
        login_url = _public_origin(request) + "/login"
        return HTMLResponse(
            status_code=200,
            content=(
                "<!doctype html><html><body>"
                "<h2>EDARSAHUB - Autorizar ChatGPT</h2>"
                "<p>Inicia sesion en EDARSAHUB y despues vuelve a esta ventana.</p>"
                f'<p><a href="{html.escape(login_url, quote=True)}" target="_blank">'
                "Abrir inicio de sesion</a></p>"
                "<button onclick=\"location.reload()\">Ya inicie sesion - continuar</button>"
                "</body></html>"
            ),
            headers={"Cache-Control": "no-store"},
        )

    try:
        user_id = _sql_user_id(user)
        validated = _validated_authorization_request(request, values, user_id)
    except (OAuthServerError, OAuthValidationError) as exc:
        return HTMLResponse(
            status_code=400,
            content="<h2>Solicitud OAuth invalida</h2><p>" + html.escape(str(exc)) + "</p>",
            headers={"Cache-Control": "no-store"},
        )

    fields = "".join(
        _hidden(key, str(values.get(key) or ""))
        for key in (
            "response_type", "client_id", "redirect_uri", "scope", "state",
            "code_challenge", "code_challenge_method", "resource",
        )
    )
    scope_text = html.escape(" ".join(sorted(validated["scopes"])))
    client_name = html.escape(validated["client"]["client_name"])
    email = html.escape(str(user.get("email") or ""))
    return HTMLResponse(
        content=(
            "<!doctype html><html><body>"
            "<h2>Autorizar EDARSAHUB Universal Worker</h2>"
            f"<p>Cliente: <strong>{client_name}</strong></p>"
            f"<p>Usuario: <strong>{email}</strong></p>"
            f"<p>Permisos solicitados: <code>{scope_text}</code></p>"
            "<p>Esta conexion puede enviar objetivos semanticos aprobados al Worker "
            "y consultar su estado. No expone SQL, terminal ni acciones Worker de bajo nivel.</p>"
            '<form method="post" action="/api/mcp/oauth/authorize">'
            + fields
            + '<button type="submit" name="decision" value="approve">Autorizar</button> '
            + '<button type="submit" name="decision" value="deny">Cancelar</button>'
            + "</form></body></html>"
        ),
        headers={"Cache-Control": "no-store"},
    )


@router.post("/authorize")
async def oauth_authorize_submit(request: Request):
    form = await request.form()
    values = {key: str(value) for key, value in form.items()}
    try:
        user = await get_current_user_dual(request)
        user_id = _sql_user_id(user)
        validated = _validated_authorization_request(request, values, user_id)
    except HTTPException:
        return _oauth_error("login_required", status_code=401)
    except (OAuthServerError, OAuthValidationError) as exc:
        code = exc.code if isinstance(exc, OAuthServerError) else str(exc)
        return _oauth_error(code)

    redirect_uri = validated["redirect_uri"]
    state_value = validated["state"]
    if values.get("decision") != "approve":
        query = {"error": "access_denied"}
        if state_value:
            query["state"] = state_value
        return RedirectResponse(redirect_uri + "?" + urlencode(query), status_code=302)

    code = _sign(
        CODE_SESSION_TYPE,
        {
            "uid": user_id,
            "client_id_hash": _token_hash(values["client_id"]),
            "redirect_uri": redirect_uri,
            "scope": " ".join(sorted(validated["scopes"])),
            "resource": validated["resource"],
            "code_challenge": validated["challenge"],
            "nonce": secrets.token_urlsafe(16),
        },
        CODE_TTL_SECONDS,
    )
    ip, ua = _request_context(request)
    _insert_session_token(
        user_id=user_id,
        token=code,
        session_type=CODE_SESSION_TYPE,
        ttl_seconds=CODE_TTL_SECONDS,
        user_agent=ua,
        ip_address=ip,
    )
    query = {"code": code}
    if state_value:
        query["state"] = state_value
    return RedirectResponse(redirect_uri + "?" + urlencode(query), status_code=302)


def _token_response(
    *,
    access_token: str,
    refresh_token: str,
    scopes: frozenset[str],
) -> JSONResponse:
    return JSONResponse(
        {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": ACCESS_TTL_SECONDS,
            "refresh_token": refresh_token,
            "scope": " ".join(sorted(scopes)),
        },
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@router.post("/token")
async def oauth_token(request: Request):
    form = await request.form()
    grant_type = str(form.get("grant_type") or "")
    client_id = str(form.get("client_id") or "")
    try:
        _client_registration(client_id)
    except OAuthServerError as exc:
        return _oauth_error(exc.code, status_code=exc.status_code)

    if grant_type == "authorization_code":
        code = str(form.get("code") or "")
        verifier = str(form.get("code_verifier") or "")
        redirect_uri = str(form.get("redirect_uri") or "")
        try:
            record = _consume_session_token(code, CODE_SESSION_TYPE)
            claims = _decode(code, CODE_SESSION_TYPE)
            if claims.get("client_id_hash") != _token_hash(client_id):
                raise OAuthServerError("invalid_grant")
            client = _client_registration(client_id)
            validate_redirect_uri(redirect_uri, client["redirect_uris"])
            if redirect_uri != claims.get("redirect_uri"):
                raise OAuthServerError("invalid_grant")
            if not verify_pkce(verifier, str(claims.get("code_challenge") or "")):
                raise OAuthServerError("invalid_grant")
            user_id = int(record["UsuarioID"])
            if int(claims.get("uid") or 0) != user_id:
                raise OAuthServerError("invalid_grant")
            _user_for_id(user_id)
            scopes = validate_scopes(
                str(claims.get("scope") or ""),
                _ALLOWED_SCOPES,
            )
            resource = str(claims.get("resource") or "")
            if resource != _resource(request):
                raise OAuthServerError("invalid_target")
            access_token = _issue_access_token(user_id=user_id, request=request)
            refresh_token = _issue_refresh_token(
                user_id=user_id,
                client_id=client_id,
                scopes=scopes,
                resource=resource,
                request=request,
            )
            return _token_response(
                access_token=access_token,
                refresh_token=refresh_token,
                scopes=scopes,
            )
        except (OAuthServerError, OAuthValidationError, ValueError):
            return _oauth_error("invalid_grant")

    if grant_type == "refresh_token":
        refresh_token = str(form.get("refresh_token") or "")
        try:
            record = _consume_session_token(refresh_token, REFRESH_SESSION_TYPE)
            claims = _decode(refresh_token, REFRESH_SESSION_TYPE)
            if claims.get("client_id_hash") != _token_hash(client_id):
                raise OAuthServerError("invalid_grant")
            user_id = int(record["UsuarioID"])
            if int(claims.get("uid") or 0) != user_id:
                raise OAuthServerError("invalid_grant")
            _user_for_id(user_id)
            scopes = validate_scopes(
                str(claims.get("scope") or ""),
                _ALLOWED_SCOPES,
            )
            resource = str(claims.get("resource") or "")
            if resource != _resource(request):
                raise OAuthServerError("invalid_target")
            access_token = _issue_access_token(user_id=user_id, request=request)
            new_refresh = _issue_refresh_token(
                user_id=user_id,
                client_id=client_id,
                scopes=scopes,
                resource=resource,
                request=request,
                family_id=str(record.get("FamiliaTokenID") or "") or None,
            )
            return _token_response(
                access_token=access_token,
                refresh_token=new_refresh,
                scopes=scopes,
            )
        except (OAuthServerError, OAuthValidationError, ValueError):
            return _oauth_error("invalid_grant")

    return _oauth_error("unsupported_grant_type")


@router.get("/health")
async def oauth_health():
    return {
        "status": "ready",
        "authorization_code": True,
        "pkce": "S256",
        "refresh_rotation": True,
        "production_touched": False,
    }
