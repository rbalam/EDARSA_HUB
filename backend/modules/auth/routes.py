
# P5-05 Auth token compatibility helper
def _p5_extract_usuario_id_from_payload(payload):
    if not isinstance(payload, dict):
        return None
    return (
        payload.get("sub")
        or payload.get("user_id")
        or payload.get("usuario_id")
        or payload.get("IDUsuario")
        or payload.get("id")
    )

import os
from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Auth Module Routes
===============================
Endpoints de autenticación, usuarios y roles.

FASE 3 DEL REFACTOR MODULAR (Diciembre 2025):
- Migrado desde server.py
- Mismas rutas, mismas respuestas, misma funcionalidad
- Sin cambios en URLs para compatibilidad con frontend

FASE 11 (Diciembre 2025):
- POST /users - Creación administrativa de usuarios (NUEVO)
- POST /roles protegido con RBAC

FASE AUTH-SECURITY-01 (Diciembre 2025):
- Todos los endpoints usan autenticación dual (Header + Cookie)

ENDPOINTS:
- POST /auth/register - Registro de usuario (PÚBLICO)
- POST /auth/login - Login
- GET /auth/me - Usuario actual
- POST /users - Crear usuario (admin, FASE 11)
- GET /users - Lista de usuarios
- PUT /users/{user_id} - Actualizar usuario
- DELETE /users/{user_id} - Desactivar usuario
- PUT /users/{user_id}/permissions - Actualizar permisos
- GET /roles/modulos - Módulos disponibles
- GET /roles - Lista de roles
- POST /roles - Crear rol (protegido RBAC FASE 11)
- PUT /roles/{role_id} - Actualizar rol
- DELETE /roles/{role_id} - Eliminar rol
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Request

from core.security import (
    AUTH_COOKIE_NAME,
    get_current_user,
    set_auth_cookie,
    clear_auth_cookie,
    get_current_user_dual,
    create_access_token,
    verify_token,
    ACCESS_TOKEN_MINUTES
)
# FASE A P1-REFRESH-TOKENS / P1-2: Importar módulo de refresh tokens y sesiones
from core.refresh_tokens import (
    RefreshTokenReuseError,
    generate_refresh_token,
    hash_refresh_token,
    set_refresh_cookie,
    clear_refresh_cookie,
    get_refresh_token_from_request,
    create_session,
    validate_and_get_session,
    rotate_refresh_token,
    detect_and_handle_replay,
    revoke_session,
    revoke_all_user_sessions
)
from modules.auth import service
from modules.auth import context_service
from modules.auth.schemas import User, UserCreate, UserLogin, MODULOS_DISPONIBLES
from core.user_access_context import resolve_user_access_context
from core.rbac.service import get_user_permissions as get_rbac_user_permissions

# Router sin prefix - se agregará en server.py como /api
router = APIRouter(tags=["auth"])


def _extract_request_access_token(request: Request) -> Optional[str]:
    """Extrae el access token activo del request con la misma prioridad que get_current_user_dual."""
    auth_header = (request.headers.get("authorization") or "").strip()
    if auth_header.startswith("Bearer "):
        candidate = auth_header[7:].strip()
        if candidate and candidate not in ("null", "undefined"):
            return candidate
    cookie_token = (request.cookies.get(AUTH_COOKIE_NAME) or "").strip()
    if cookie_token and cookie_token not in ("null", "undefined"):
        return cookie_token
    return None


def _canonical_session_user_ids(user_dict: Dict) -> List[str]:
    """Resuelve los identificadores canonicos del usuario para dbo.Sesiones sin hash()."""
    raw_candidates = [
        user_dict.get("id"),
        user_dict.get("_id"),
        user_dict.get("public_uuid"),
        user_dict.get("PublicUUID"),
        user_dict.get("usuario_id"),
        user_dict.get("UsuarioID"),
        user_dict.get("_sql_usuario_id"),
    ]
    resolved: List[str] = []
    seen = set()
    for val in raw_candidates:
        if val is None or isinstance(val, bool):
            continue
        text = str(val).strip()
        if not text:
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            resolved.append(text)
    return resolved


# ============================================================================
# DEPENDENCIA DUAL PARA TODOS LOS ENDPOINTS
# ============================================================================

async def get_user_dual(request: Request) -> Dict:
    """
    Dependencia que usa autenticación dual (Header O Cookie).
    FASE AUTH-SECURITY-01: Todos los endpoints de auth usan esta dependencia.
    """
    return await get_current_user_dual(request)


# ============================================================================
# AUTENTICACIÓN
# ============================================================================

@router.post("/auth/register")
async def register(user_data: UserCreate):
    """Registra un nuevo usuario."""
    return await service.register_user(user_data)


@router.post("/auth/login")
async def login(credentials: UserLogin, request: Request, response: Response):
    """
    Autentica un usuario, crea una sesion persistente revocable en dbo.Sesiones (fail-closed)
    y emite un access token JWT vinculado a ese SesionID ('sid') junto con el refresh token.
    """
    import asyncio
    import logging

    result = await service.login_user(credentials.email, credentials.password)

    user_data = result.get("user", {})
    user_id = user_data.get("id", user_data.get("_id", ""))
    email = user_data.get("email", credentials.email)
    role = user_data.get("role", "Usuario")
    raw_uid = user_data.get("usuario_id") if user_data.get("usuario_id") is not None else user_data.get("UsuarioID")
    try:
        canonical_uid = int(raw_uid) if raw_uid is not None and not isinstance(raw_uid, bool) else None
    except Exception:
        canonical_uid = None
    canonical_puuid = user_data.get("public_uuid") or user_data.get("PublicUUID")
    if not canonical_puuid and isinstance(user_id, str) and "-" in user_id:
        canonical_puuid = user_id

    refresh_token = generate_refresh_token()
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # P1-2: Crear sesion en EDARSAHUB SQL Server de forma fail-closed antes de emitir el JWT
    try:
        session_info = await asyncio.wait_for(
            create_session(
                user_id=str(user_id),
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                user_type="interno"
            ),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        logging.error("[AUTH] Timeout creando sesión segura en EDARSAHUB (fail-closed)")
        raise HTTPException(
            status_code=503,
            detail="No se pudo iniciar la sesión segura. Intenta nuevamente."
        )
    except Exception as e:
        logging.error(f"[AUTH] Error creando sesión segura en EDARSAHUB (fail-closed): {e}")
        raise HTTPException(
            status_code=503,
            detail="No se pudo iniciar la sesión segura. Intenta nuevamente."
        )

    session_id = (session_info or {}).get("session_id")
    if not session_id:
        logging.error("[AUTH] create_session no devolvió session_id válido (fail-closed)")
        raise HTTPException(
            status_code=503,
            detail="No se pudo iniciar la sesión segura. Intenta nuevamente."
        )

    access_token = create_access_token(
        str(user_id),
        email,
        role,
        token_type="internal",
        usuario_id=canonical_uid,
        public_uuid=str(canonical_puuid) if canonical_puuid else None,
        session_id=str(session_id),
    )

    set_auth_cookie(response, access_token, short_lived=True)
    set_refresh_cookie(response, refresh_token)

    safe_user_data = {
        k: v for k, v in user_data.items()
        if k not in ('password_hash', 'password', 'PasswordHashTexto', '_session_id')
    }

    return {
        "token": access_token,
        "user": safe_user_data,
        "expires_in": ACCESS_TOKEN_MINUTES * 60
    }


@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """
    Cierra la sesión del usuario e invalida inmediatamente el SesionID en dbo.Sesiones,
    tanto por cookie refresh token como por el claim 'sid' del access token (fail-closed).
    """
    import logging

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    session_ids_to_revoke: List[str] = []

    clear_auth_cookie(response)
    clear_refresh_cookie(response)

    try:
        refresh_token = get_refresh_token_from_request(request)
        if refresh_token:
            session = await validate_and_get_session(refresh_token, expected_user_type="interno")
            if session and session.get("session_id"):
                session_ids_to_revoke.append(str(session["session_id"]))

        access_token = _extract_request_access_token(request)
        if access_token:
            try:
                payload = verify_token(access_token)
                sid = str(payload.get("sid") or "").strip()
                if sid and sid not in session_ids_to_revoke:
                    session_ids_to_revoke.append(sid)
            except HTTPException:
                pass

        for sid in session_ids_to_revoke:
            await revoke_session(
                session_id=sid,
                reason="logout",
                ip_address=ip_address,
                user_agent=user_agent
            )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[AUTH] Error revocando sesión en logout (fail-closed): {e}")
        raise HTTPException(
            status_code=503,
            detail="Error cerrando sesión en el servidor"
        )

    return {"message": "Sesión cerrada correctamente"}


@router.post("/auth/refresh")
async def refresh_tokens(request: Request, response: Response):
    """
    FASE A P1-REFRESH-TOKENS / P1-2: Renueva el access token usando rotacion atomica
    de refresh token en dbo.Sesiones con proteccion contra replay y concurrencia.
    """
    import logging

    refresh_token = get_refresh_token_from_request(request)

    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    is_replay, replay_info = await detect_and_handle_replay(
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
        expected_user_type="interno",
    )

    if is_replay:
        clear_auth_cookie(response)
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=401,
            detail="Sesión inválida - posible uso no autorizado detectado"
        )

    session = await validate_and_get_session(refresh_token, expected_user_type="interno")

    if not session:
        clear_auth_cookie(response)
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Sesión expirada")

    user_id = session["user_id"]

    from modules.auth.service import get_user_by_id
    user_data = await get_user_by_id(user_id)

    if not user_data or not user_data.get("active", True):
        try:
            await revoke_session(
                session_id=session["session_id"],
                reason="user_inactive",
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception:
            pass
        clear_auth_cookie(response)
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Usuario no autorizado")

    email = user_data.get("email", "")
    role = user_data.get("role", "Usuario")
    raw_uid = user_data.get("usuario_id") if user_data.get("usuario_id") is not None else user_data.get("UsuarioID")
    try:
        canonical_uid = int(raw_uid) if raw_uid is not None and not isinstance(raw_uid, bool) else None
    except Exception:
        canonical_uid = None
    canonical_puuid = user_data.get("public_uuid") or user_data.get("PublicUUID")
    if not canonical_puuid and isinstance(user_id, str) and "-" in str(user_id):
        canonical_puuid = str(user_id)

    new_refresh_token = generate_refresh_token()

    # Rotar atomicamente en BD ANTES de emitir el nuevo access token vinculado al nuevo SesionID
    try:
        rotated = await rotate_refresh_token(
            old_session_id=session["session_id"],
            familia_id=session["familia_id"],
            user_id=user_id,
            new_refresh_token=new_refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            user_type="interno",
            old_refresh_token=refresh_token,
        )
    except RefreshTokenReuseError:
        clear_auth_cookie(response)
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=401,
            detail="Sesión inválida - posible uso no autorizado detectado"
        )
    except Exception as e:
        logging.error(f"Error rotando token: {e}")
        raise HTTPException(status_code=500, detail="Error interno")

    new_access_token = create_access_token(
        str(user_id),
        email,
        role,
        token_type="internal",
        usuario_id=canonical_uid,
        public_uuid=str(canonical_puuid) if canonical_puuid else None,
        session_id=str(rotated["session_id"]),
    )

    set_auth_cookie(response, new_access_token, short_lived=True)
    set_refresh_cookie(response, new_refresh_token)

    return {
        "token": new_access_token,
        "message": "Token renovado",
        "expires_in": ACCESS_TOKEN_MINUTES * 60
    }


@router.post("/auth/logout-all")
async def logout_all_sessions(request: Request, response: Response):
    """
    FASE A P1-REFRESH-TOKENS / P1-2: Revoca TODAS las sesiones internas activas del usuario
    en dbo.Sesiones usando identificadores canonicos (sin hash() inseguro), fail-closed.
    """
    import logging

    try:
        current_user = await get_current_user_dual(request)
    except HTTPException:
        raise HTTPException(status_code=401, detail="No autenticado")

    canonical_user_ids = _canonical_session_user_ids(current_user)
    if not canonical_user_ids:
        raise HTTPException(status_code=401, detail="Usuario no identificado")

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    clear_auth_cookie(response)
    clear_refresh_cookie(response)

    try:
        sessions_revoked = await revoke_all_user_sessions(
            user_id=canonical_user_ids,
            reason="logout_all",
            revoked_by_user_id=canonical_user_ids[0],
            ip_address=ip_address,
            user_agent=user_agent,
            expected_user_type="interno",
        )
    except Exception as e:
        logging.error(f"[AUTH] Error revocando sesiones en logout-all (fail-closed): {e}")
        raise HTTPException(
            status_code=503,
            detail="No se pudieron revocar todas las sesiones"
        )

    return {
        "message": "Todas las sesiones cerradas",
        "sessions_revoked": sessions_revoked
    }


@router.get("/auth/me")
async def get_me(request: Request):
    """
    Retorna los datos del usuario autenticado con validacion fail-closed de sesion.
    P1-2: NUNCA genera ni reactiva un nuevo token tras logout; devuelve el token vigente
    ya verificado del request para hidratar memoria en el SPA sin extender su expiracion.
    """
    current_user = await get_current_user_dual(request)

    # Defensa en profundidad: si un token legacy sin 'sid' trae cookie refresh revocada/expirada, rechazar
    if not current_user.get("_session_id"):
        refresh_token = get_refresh_token_from_request(request)
        if refresh_token:
            active_session = await validate_and_get_session(refresh_token, expected_user_type="interno")
            if not active_session:
                raise HTTPException(status_code=401, detail="Sesión revocada o expirada")

    safe_user = {
        k: v for k, v in current_user.items()
        if k not in ('password_hash', 'password', 'PasswordHashTexto', '_session_id')
    }

    user_id = safe_user.get("id", safe_user.get("_id", ""))
    raw_uid = safe_user.get("usuario_id") if safe_user.get("usuario_id") is not None else safe_user.get("UsuarioID")
    try:
        canonical_uid = int(raw_uid) if raw_uid is not None and not isinstance(raw_uid, bool) else None
    except Exception:
        canonical_uid = None
    canonical_puuid = safe_user.get("public_uuid") or safe_user.get("PublicUUID")
    if not canonical_puuid and isinstance(user_id, str) and "-" in str(user_id):
        canonical_puuid = str(user_id)
    if canonical_uid is not None:
        safe_user["usuario_id"] = canonical_uid
    if canonical_puuid:
        safe_user["public_uuid"] = str(canonical_puuid)

    active_token = _extract_request_access_token(request)

    return {
        **safe_user,
        "token": active_token
    }


# ============================================================================
# CONTEXTO DE USUARIO (FASE 2)
# ============================================================================

@router.get("/auth/me/context")
async def get_my_context(current_user: Dict = Depends(get_user_dual)):
    """
    Obtiene el contexto completo del usuario actual.
    Incluye empresas permitidas, rol RBAC, permisos y sucursales.
    
    FASE 2: Endpoint nuevo, no reemplaza /auth/me
    """
    context = await context_service.get_user_context(current_user['id'])
    if not context:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return context


@router.post("/auth/context")
async def change_context(
    data: Dict,
    current_user: Dict = Depends(get_user_dual)
):
    """
    Cambia el contexto activo del usuario (empresa/sucursal).
    
    Body:
        empresa_id: UUID de la empresa a activar
        sucursal_id: UUID de la sucursal (opcional)
    
    FASE 2: Endpoint nuevo para cambio de contexto sin re-login
    """
    empresa_id = data.get('empresa_id')
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    context = await context_service.get_user_context_for_empresa(
        current_user['id'],
        empresa_id
    )
    
    if not context:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if 'error' in context:
        raise HTTPException(status_code=403, detail=context['error'])
    
    return context


@router.get("/auth/empresas")
async def get_my_empresas(current_user: Dict = Depends(get_user_dual)):
    """
    Obtiene las empresas disponibles para el usuario actual.
    
    FASE 2: Endpoint nuevo para selector de empresa en frontend
    """
    empresas = await context_service.get_empresas_disponibles(current_user['id'])
    return empresas


# ============================================================================
# DIAGNÓSTICO DE ACCESO (BARRIDO SEGURIDAD)
# ============================================================================

@router.get("/auth/me/access-context")
async def get_my_access_context(current_user: Dict = Depends(get_user_dual)):
    """
    BARRIDO SEGURIDAD: Endpoint de diagnóstico del contexto de acceso efectivo.
    
    Retorna el contexto REAL de acceso calculado por resolve_user_access_context().
    Útil para:
    - Auditoría de seguridad
    - Diagnóstico de problemas de permisos
    - Verificación de configuración RBAC
    
    El resultado incluye:
    - Fuente de acceso (SUPERADMIN, ADMIN, RBAC, LEGACY, MIXTO)
    - Empresas efectivas
    - Servidores efectivos
    - Almacenes efectivos
    - Permisos funcionales calculados
    """
    context = await resolve_user_access_context(current_user)
    return context.to_dict()


MENU_PERMISSION_MAP = {
    "mis_tareas": [],
    "ia": [
        "IA_ASSISTANT_VER",
    ],
    "tablero_ejecutivo": [
        "TABLERO_EJECUTIVO_VER",
        "COMERCIAL_TABLERO_VER",
        "COMERCIAL_DASHBOARD_VER",
    ],
    "comercial": [
        "COMERCIAL_VER",
        "COMERCIAL_DASHBOARD_VER",
    ],
    "compras": [
        "COMPRAS_VER",
        "COMPRAS_DASHBOARD_VER",
        "COMPRAS_INVENTARIOS_VER",
    ],
    "operaciones": [
        "OPERACIONES_VER",
        "OPERACIONES_DASHBOARD_VER",
    ],
    "finanzas": [
        "FINANZAS_VER",
    ],
    "produccion": [
        "PRODUCCION_VER",
    ],
    "recursos_humanos": [
        "RH_VER",
        "RECURSOS_HUMANOS_VER",
    ],
    "reportes_bi": [
        "REPORTES_BI_VER",
        "REPORTES_VER",
    ],
    "catalogos": [
        "CATALOGOS_VER",
        "CATALOGO_VER",
    ],
    "centro_control": [
        "CENTRO_CONTROL_VER",
    ],
    "servidores": [
        "SERVIDORES_VER",
        "SISTEMA_SERVIDORES_VER",
    ],
    "programacion": [
        "SCHEDULER_VER",
        "PROGRAMACION_VER",
    ],
    "automatizaciones": [
        "AUDITORIA_VER",
        "AUTOMATIZACIONES_VER",
    ],
    "asignaciones": [
        "ASIGNACIONES_VER",
        "SISTEMA_ASIGNACIONES_VER",
    ],
    "catalogo_sql": [
        "CATALOGO_SQL_VER",
    ],
    "explorador_bd": [
        "EXPLORADOR_BD_VER",
    ],
    "alertas": [
        "ALERTAS_VER",
    ],
    "usuarios": [
        "SISTEMA_USUARIOS_VER",
        "USUARIOS_VER",
    ],
}


def _normalize_permission_codes(permisos: List[str]) -> List[str]:
    normalized = set()

    for permiso in permisos or []:
        if not permiso:
            continue

        raw = str(permiso).strip()
        if not raw:
            continue

        normalized.add(raw)
        normalized.add(raw.upper())

        if "." in raw:
            modulo, accion = raw.rsplit(".", 1)
            normalized.add(f"{modulo}_{accion}".upper())

    return sorted(normalized)


def _group_permissions_by_module(permisos_flat: List[str]) -> Dict[str, Dict[str, bool]]:
    grouped = {}

    for permiso in permisos_flat or []:
        if "_" not in permiso:
            continue

        modulo, accion = permiso.rsplit("_", 1)
        if not modulo or not accion:
            continue

        grouped.setdefault(modulo, {})[accion] = True

    return grouped


def _build_menu_permissions(
    permissions_flat: List[str],
    tiene_acceso_global: bool,
) -> Dict[str, bool]:
    permission_set = set(_normalize_permission_codes(permissions_flat))

    menu = {}
    for menu_key, required_permissions in MENU_PERMISSION_MAP.items():
        if menu_key == "mis_tareas":
            menu[menu_key] = True
            continue

        menu[menu_key] = bool(
            tiene_acceso_global
            or any(perm in permission_set for perm in required_permissions)
        )

    return menu


async def _build_effective_permissions_payload(current_user: Dict) -> Dict:
    context = await resolve_user_access_context(current_user)

    db = service.repo.get_db()
    rbac_payload = get_rbac_user_permissions(db, current_user)

    permisos_originales = list(rbac_payload.get("permisos", []) or [])
    raw_uid = current_user.get("usuario_id") if current_user.get("usuario_id") is not None else current_user.get("UsuarioID")
    try:
        canonical_uid = int(raw_uid) if raw_uid is not None and not isinstance(raw_uid, bool) else None
    except Exception:
        canonical_uid = None
    canonical_puuid = (
        current_user.get("public_uuid")
        or current_user.get("PublicUUID")
        or (str(context.user_id) if context.user_id and "-" in str(context.user_id) else None)
    )

    roles_contexto = []
    if canonical_uid is not None:
        try:
            from core.rbac_sql.service import RBACSQLService
            sql_perms = RBACSQLService.get_effective_permissions(canonical_uid) or []
            for sp in sql_perms:
                if sp and sp not in permisos_originales:
                    permisos_originales.append(sp)
        except Exception:
            pass
        try:
            from modules.rbac_context_sql.context_service import RBACContextService
            ctx_info = RBACContextService().get_user_context(current_user)
            if isinstance(ctx_info, dict):
                roles_contexto = list(ctx_info.get("roles_contexto") or [])
                for p in ctx_info.get("permisos_efectivos") or []:
                    code = p.get("CodigoPermiso") or p.get("codigo_permiso")
                    if code and code not in permisos_originales:
                        permisos_originales.append(code)
        except Exception:
            roles_contexto = []

    permisos_flat = _normalize_permission_codes(permisos_originales)
    permissions_by_module = _group_permissions_by_module(permisos_flat)

    roles = []
    for role in rbac_payload.get("roles", []) or []:
        roles.append({
            "rol_id": role.get("id"),
            "codigo": role.get("nombre"),
            "nombre": role.get("descripcion") or role.get("nombre"),
            "nivel_jerarquia": role.get("nivel_jerarquia", 0),
            "es_sistema": role.get("es_sistema", False),
            "activo": role.get("activo", True),
        })

    return {
        "user_id": context.user_id,
        "usuario_id": canonical_uid,
        "public_uuid": canonical_puuid,
        "email": context.email,
        "role_legacy": current_user.get("role"),
        "source": "RBAC_SQL_CANONICAL_WITH_LEGACY_COMPAT",
        "roles": roles,
        "roles_contexto": roles_contexto,
        "permissions": permissions_by_module,
        "permissions_flat": permisos_flat,
        "scope": {
            "tiene_acceso_global": context.tiene_acceso_global,
            "fuente_acceso": context.fuente_acceso,
            "empresas_ids": context.empresas_ids,
            "empresa_default_id": context.empresa_default_id,
            "servers_ids": context.servers_ids,
            "almacenes_por_server": context.almacenes_por_server,
            "sucursales_por_server": context.sucursales_por_server,
            "empresas_count": len(context.empresas_ids),
            "servers_count": len(context.servers_ids),
        },
    }


@router.get("/auth/me/effective-permissions")
async def get_my_effective_permissions(current_user: Dict = Depends(get_user_dual)):
    """
    Retorna permisos efectivos desde RBAC SQL canónico.
    """
    return await _build_effective_permissions_payload(current_user)


@router.get("/auth/me/menu-permissions")
async def get_my_menu_permissions(current_user: Dict = Depends(get_user_dual)):
    """
    Retorna permisos de menú derivados de permisos efectivos.
    """
    effective = await _build_effective_permissions_payload(current_user)
    scope = effective.get("scope", {})
    permissions_flat = effective.get("permissions_flat", [])

    modulos_permisos = _build_menu_permissions(
        permissions_flat=permissions_flat,
        tiene_acceso_global=bool(scope.get("tiene_acceso_global")),
    )

    return {
        "user_id": effective.get("user_id"),
        "email": effective.get("email"),
        "role_legacy": effective.get("role_legacy"),
        "source": effective.get("source"),
        "tiene_acceso_global": scope.get("tiene_acceso_global"),
        "fuente_acceso": scope.get("fuente_acceso"),
        "permisos_modulos": modulos_permisos,
        "permisos_funcionales": permissions_flat,
        "roles": effective.get("roles", []),
        "servers_count": scope.get("servers_count", 0),
        "empresas_count": scope.get("empresas_count", 0),
    }


# ============================================================================
# USUARIOS CRUD
# ============================================================================

@router.post("/users")
async def create_user_admin(user_data: Dict, current_user: Dict = Depends(get_user_dual)):
    """
    FASE 11: Crea un usuario desde administración.
    
    Este endpoint es DIFERENTE de POST /auth/register:
    - Requiere autenticación
    - Requiere permiso SISTEMA_USUARIOS_CREAR o fallback legacy (Administrador+)
    - NO genera token JWT (el usuario nuevo debe hacer login)
    - Respeta jerarquía de roles
    
    Body:
        email: str (requerido)
        name: str (requerido)
        password: str (requerido)
        role: str (opcional, default 'Usuario')
        telefono: str (opcional)
        sucursales: list (opcional)
        allowed_servers: list (opcional)
        allowed_sucursales: dict (opcional)
        allowed_warehouses: dict (opcional)
    """
    return await service.create_user_admin(user_data, current_user)


@router.get("/users", response_model=List[User])
async def get_users(current_user: Dict = Depends(get_user_dual)):
    """Obtiene todos los usuarios (solo admin)."""
    return await service.get_users(current_user)


@router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: Dict, current_user: Dict = Depends(get_user_dual)):
    """Actualiza un usuario (solo admin)."""
    return await service.update_user(user_id, user_data, current_user)


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: Dict = Depends(get_user_dual)):
    """Desactiva un usuario (solo admin)."""
    return await service.delete_user(user_id, current_user)


@router.put("/users/{user_id}/permissions")
async def update_user_permissions(user_id: str, permissions: Dict, current_user: Dict = Depends(get_user_dual)):
    """Actualiza los permisos de un usuario (solo admin)."""
    return await service.update_user_permissions(user_id, permissions, current_user)


# ============================================================================
# ROLES CRUD
# ============================================================================

@router.get("/roles/modulos")
async def get_modulos_disponibles(current_user: Dict = Depends(get_user_dual)):
    """Obtiene la lista de módulos disponibles para asignar permisos."""
    # Permitir acceso a SuperAdministrador y Administrador
    if current_user['role'] not in ['SuperAdministrador', 'Administrador']:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="No autorizado")
    return MODULOS_DISPONIBLES


@router.get("/roles")
async def get_roles(current_user: Dict = Depends(get_user_dual)):
    """Obtiene todos los roles del sistema (solo admin)."""
    return await service.get_roles(current_user)


@router.post("/roles")
async def create_role(role_data: Dict, current_user: Dict = Depends(get_user_dual)):
    """Crea un nuevo rol (solo admin)."""
    return await service.create_role(role_data, current_user)


@router.put("/roles/{role_id}")
async def update_role(role_id: str, role_data: Dict, current_user: Dict = Depends(get_user_dual)):
    """Actualiza un rol existente (solo admin)."""
    return await service.update_role(role_id, role_data, current_user)


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str, current_user: Dict = Depends(get_user_dual)):
    """Elimina un rol (solo admin, no roles de sistema)."""
    return await service.delete_role(role_id, current_user)


# ==============================================================================
# PASSWORD RESET ENDPOINTS - TEMPORAL / SOLO PREVIEW
# ==============================================================================
# PROP-001 v2 - Aprobado para implementacion TEMPORAL en PREVIEW
# 
# DECLARACION ARQUITECTONICA:
# - Esta implementacion es TEMPORAL y SOLO para PREVIEW
# - NO redefine la arquitectura oficial del sistema
# - MongoDB es ubicacion TRANSITORIA/LEGACY para usuarios
# - La fuente maestra oficial sigue siendo BD EDARSAHUB
# - NO aplica a produccion sin aprobacion separada
# ==============================================================================

from pydantic import BaseModel, EmailStr

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/auth/forgot-password")
async def forgot_password(request_data: ForgotPasswordRequest, request: Request):
    """
    Solicitar recuperacion de contrasena.
    
    TEMPORAL - SOLO PREVIEW
    
    Siempre retorna mensaje generico para no revelar si el email existe.
    Si el email esta registrado, envia un correo con instrucciones.
    
    Rate limit: 3 solicitudes por hora por email, 5 por IP.
    """
    from modules.auth.password_reset import request_password_reset
    
    # Obtener IP y User-Agent
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # URL base del frontend para el enlace de reset.
    # IMPORTANTE: NO usar Origin/Referer de la petición: el usuario puede entrar
    # por un host alterno (ej. *.preview.emergentcf.cloud) que el proxy bloquea
    # con 403. El enlace SIEMPRE debe apuntar al dominio público canónico.
    origin = os.environ.get("FRONTEND_URL", "https://erp-crm-enterprise-1.preview.emergentagent.com")
    
    result = request_password_reset(
        email=request_data.email,
        ip=ip,
        user_agent=user_agent,
        base_url=origin
    )
    
    return {"message": result["message"]}


@router.post("/auth/reset-password")
async def reset_password_endpoint(request_data: ResetPasswordRequest, request: Request):
    """
    Cambiar contrasena usando token valido.
    
    TEMPORAL - SOLO PREVIEW
    
    El token debe ser valido, no usado, no expirado (1 hora).
    La nueva contrasena debe cumplir requisitos de complejidad.
    """
    from modules.auth.password_reset import reset_password
    
    # Obtener IP y User-Agent
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    result = reset_password(
        token=request_data.token,
        new_password=request_data.new_password,
        ip=ip,
        user_agent=user_agent
    )
    
    if not result["success"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {"message": result["message"]}


__all__ = ['router']
