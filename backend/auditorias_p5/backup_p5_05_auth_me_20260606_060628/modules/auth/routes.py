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
    get_current_user, 
    set_auth_cookie, 
    clear_auth_cookie,
    get_current_user_dual,
    create_access_token,
    ACCESS_TOKEN_MINUTES
)
# FASE A P1-REFRESH-TOKENS: Importar módulo de refresh tokens
from core.refresh_tokens import (
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

# Router sin prefix - se agregará en server.py como /api
router = APIRouter(tags=["auth"])


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
    Autentica un usuario y retorna token JWT.
    
    FASE AUTH-SECURITY-01: 
    - Retorna {token, user} en body para compatibilidad con frontend actual
    - TAMBIÉN setea cookie httpOnly para futura migración
    
    FASE A P1-REFRESH-TOKENS:
    - Genera access token corto (ACCESS_TOKEN_MINUTES)
    - Genera refresh token (7 días)
    - Guarda hash del refresh token en EDARSAHUB.Sesiones
    - Setea ambas cookies httpOnly
    - MANTIENE respuesta legacy {token, user} por compatibilidad temporal
    """
    # Autenticar usuario (valida credenciales contra MongoDB)
    result = await service.login_user(credentials.email, credentials.password)
    
    # Extraer datos del usuario
    user_data = result.get("user", {})
    user_id = user_data.get("id", user_data.get("_id", ""))
    email = user_data.get("email", credentials.email)
    role = user_data.get("role", "Usuario")
    
    # FASE A P1-REFRESH-TOKENS: Crear tokens
    # Access token corto (15 minutos por defecto)
    access_token = create_access_token(str(user_id), email, role, token_type="internal")
    
    # Refresh token (7 días por defecto)
    refresh_token = generate_refresh_token()
    
    # Obtener contexto del request
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Crear sesión en EDARSAHUB SQL Server (NO BLOQUEANTE)
    # OPTIMIZACIÓN: Timeout de 3 segundos para no bloquear login
    session_info = None
    try:
        import asyncio
        session_info = await asyncio.wait_for(
            create_session(
                user_id=int(user_id) if str(user_id).isdigit() else hash(str(user_id)) % 2147483647,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                user_type="interno"
            ),
            timeout=3.0  # Timeout de 3 segundos
        )
    except asyncio.TimeoutError:
        import logging
        logging.warning(f"Timeout creando sesión en EDARSAHUB (continuando con login legacy)")
    except Exception as e:
        # Si falla la creación de sesión en SQL, continuar con login legacy
        import logging
        logging.warning(f"No se pudo crear sesión en EDARSAHUB (continuando con login legacy): {e}")
    
    # Setear cookies httpOnly
    # Access token cookie (corta duración)
    set_auth_cookie(response, access_token, short_lived=True)
    
    # Refresh token cookie (solo si se creó sesión)
    if session_info:
        set_refresh_cookie(response, refresh_token)
    
    # Retornar respuesta LEGACY para compatibilidad con frontend actual
    # NOTA: El campo "token" seguirá siendo el access token corto
    # El frontend actual lo guarda en memoryToken como fallback
    return {
        "token": access_token,
        "user": user_data,
        "expires_in": ACCESS_TOKEN_MINUTES * 60  # Nuevo campo informativo
    }


@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """
    Cierra la sesión del usuario.
    
    FASE AUTH-SECURITY-01: Elimina la cookie de autenticación.
    
    FASE A P1-REFRESH-TOKENS:
    - Revoca la sesión actual en EDARSAHUB.Sesiones
    - Elimina ambas cookies (access y refresh)
    
    Nota: El frontend actual usa clearSession() para limpiar localStorage/sessionStorage.
    Este endpoint complementa esa funcionalidad limpiando las cookies httpOnly.
    """
    # Obtener refresh token de cookie para identificar la sesión
    refresh_token = get_refresh_token_from_request(request)
    
    if refresh_token:
        # Validar y obtener sesión
        session = await validate_and_get_session(refresh_token)
        
        if session:
            # Revocar sesión en BD
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            
            try:
                await revoke_session(
                    session_id=session["session_id"],
                    reason="logout",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            except Exception as e:
                import logging
                logging.warning(f"Error revocando sesión: {e}")
    
    # Eliminar cookies
    clear_auth_cookie(response)
    clear_refresh_cookie(response)
    
    return {"message": "Sesión cerrada correctamente"}


@router.post("/auth/refresh")
async def refresh_tokens(request: Request, response: Response):
    """
    FASE A P1-REFRESH-TOKENS: Renueva el access token usando el refresh token.
    
    Este endpoint:
    1. Lee el refresh token de la cookie
    2. Valida que exista una sesión activa con ese token
    3. Genera un nuevo access token
    4. Rota el refresh token (el anterior queda inválido)
    5. Detecta y maneja replay attacks
    
    Returns:
        200: Nuevos tokens seteados en cookies
        401: Refresh token inválido, expirado, o replay detectado
    """
    # Obtener refresh token de cookie
    refresh_token = get_refresh_token_from_request(request)
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Verificar si es replay attack
    is_replay, replay_info = await detect_and_handle_replay(
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if is_replay:
        # Limpiar cookies y forzar re-login
        clear_auth_cookie(response)
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=401, 
            detail="Sesión inválida - posible uso no autorizado detectado"
        )
    
    # Validar sesión
    session = await validate_and_get_session(refresh_token)
    
    if not session:
        # Token no encontrado o expirado
        clear_auth_cookie(response)
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Sesión expirada")
    
    # Obtener datos del usuario para el nuevo access token
    # El user_id está en la sesión, necesitamos el email y role
    user_id = session["user_id"]
    
    # Buscar usuario en MongoDB para obtener email y role
    from modules.auth.service import get_user_by_id
    user_data = await get_user_by_id(user_id)
    
    if not user_data:
        clear_auth_cookie(response)
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    email = user_data.get("email", "")
    role = user_data.get("role", "Usuario")
    
    # Generar nuevos tokens
    new_access_token = create_access_token(str(user_id), email, role, token_type="internal")
    new_refresh_token = generate_refresh_token()
    
    # Rotar refresh token en BD
    try:
        await rotate_refresh_token(
            old_session_id=session["session_id"],
            familia_id=session["familia_id"],
            user_id=user_id,
            new_refresh_token=new_refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            user_type=session.get("user_type", "interno")
        )
    except Exception as e:
        import logging
        logging.error(f"Error rotando token: {e}")
        raise HTTPException(status_code=500, detail="Error interno")
    
    # Setear nuevas cookies
    set_auth_cookie(response, new_access_token, short_lived=True)
    set_refresh_cookie(response, new_refresh_token)
    
    return {
        "message": "Token renovado",
        "expires_in": ACCESS_TOKEN_MINUTES * 60
    }


@router.post("/auth/logout-all")
async def logout_all_sessions(request: Request, response: Response):
    """
    FASE A P1-REFRESH-TOKENS: Cierra TODAS las sesiones del usuario.
    
    Útil cuando:
    - El usuario sospecha que su cuenta fue comprometida
    - Quiere cerrar sesiones en otros dispositivos
    
    Returns:
        200: Todas las sesiones revocadas
        401: No autenticado
    """
    # Verificar autenticación actual
    try:
        current_user = await get_current_user_dual(request)
    except HTTPException:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    user_id = current_user.get("id", current_user.get("_id"))
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Usuario no identificado")
    
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Convertir user_id a int si es necesario
    user_id_int = int(user_id) if str(user_id).isdigit() else hash(str(user_id)) % 2147483647
    
    # Revocar todas las sesiones
    try:
        sessions_revoked = await revoke_all_user_sessions(
            user_id=user_id_int,
            reason="logout_all",
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        import logging
        logging.error(f"Error revocando sesiones: {e}")
        sessions_revoked = 0
    
    # Limpiar cookies de la sesión actual
    clear_auth_cookie(response)
    clear_refresh_cookie(response)
    
    return {
        "message": "Todas las sesiones cerradas",
        "sessions_revoked": sessions_revoked
    }


@router.get("/auth/me")
async def get_me(request: Request):
    """
    Retorna los datos del usuario autenticado.
    
    FASE AUTH-SECURITY-01: Soporta autenticación dual (Header O Cookie).
    FASE FILTRO-FIX: También retorna token para setear en memoria (CORS fallback).
    """
    current_user = await get_current_user_dual(request)
    
    # Generar token fresco para que el frontend pueda usarlo en memoria
    # Esto soluciona el problema donde al recargar la página el token no está en memoria
    user_id = current_user.get("id", current_user.get("_id", ""))
    email = current_user.get("email", "")
    role = current_user.get("role", current_user.get("rol", ""))
    
    from core.security import create_access_token
    fresh_token = create_access_token(str(user_id), email, role, token_type="internal")
    
    return {
        **current_user,
        "token": fresh_token  # Token para setear en memoria
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


@router.get("/auth/me/menu-permissions")
async def get_my_menu_permissions(current_user: Dict = Depends(get_user_dual)):
    """
    BARRIDO SEGURIDAD: Retorna los permisos de menú efectivos para el usuario.
    
    Este endpoint es para que el frontend sepa qué módulos mostrar.
    Combina:
    - Rol legacy (Usuario, Supervisor, Administrador)
    - sec_roles RBAC
    - permisos funcionales específicos
    
    Retorna un diccionario con módulos y si el usuario tiene acceso.
    """
    context = await resolve_user_access_context(current_user)
    
    # Definir permisos por módulo
    # Estos permisos determinan qué módulos se muestran en el menú
    modulos_permisos = {
        'mis_tareas': True,  # Todos los usuarios autenticados
        'tablero_ejecutivo': (
            context.tiene_acceso_global or 
            current_user.get('role') in ['Supervisor', 'Administrador'] or
            'COMERCIAL_TABLERO_VER' in context.permisos or
            len(context.servers_ids) > 0  # Si tiene servidores asignados
        ),
        'comercial': (
            context.tiene_acceso_global or
            len(context.servers_ids) > 0 or
            'COMERCIAL_DASHBOARD_VER' in context.permisos
        ),
        'compras': (
            context.tiene_acceso_global or
            len(context.servers_ids) > 0 or
            'COMPRAS_DASHBOARD_VER' in context.permisos
        ),
        'operaciones': (
            context.tiene_acceso_global or
            len(context.servers_ids) > 0
        ),
        'finanzas': (
            context.tiene_acceso_global or
            current_user.get('role') in ['Supervisor', 'Administrador'] or
            'FINANZAS_VER' in context.permisos
        ),
        'produccion': (
            context.tiene_acceso_global or
            current_user.get('role') in ['Supervisor', 'Administrador']
        ),
        'recursos_humanos': (
            context.tiene_acceso_global or
            current_user.get('role') in ['Supervisor', 'Administrador'] or
            'RH_VER' in context.permisos
        ),
        'reportes_bi': (
            context.tiene_acceso_global or
            current_user.get('role') in ['Supervisor', 'Administrador']
        ),
        'catalogos': (
            context.tiene_acceso_global or
            current_user.get('role') in ['Supervisor', 'Administrador'] or
            len(context.permisos_catalogos) > 0
        ),
        # Sistema
        'centro_control': (
            context.tiene_acceso_global or
            current_user.get('role') in ['Supervisor', 'Administrador', 'Director']
        ),
        'servidores': (
            context.tiene_acceso_global or
            current_user.get('role') == 'Administrador'
        ),
        'programacion': (
            context.tiene_acceso_global or
            current_user.get('role') in ['Supervisor', 'Administrador'] or
            'SCHEDULER_VER' in context.permisos
        ),
        'automatizaciones': (
            context.tiene_acceso_global or
            current_user.get('role') in ['Supervisor', 'Administrador', 'Gerente', 'Director', 'Auditor']
        ),
        'asignaciones': (
            context.tiene_acceso_global or
            current_user.get('role') == 'Administrador'
        ),
        'catalogo_sql': (
            context.tiene_acceso_global or
            current_user.get('role') in ['Supervisor', 'Administrador']
        ),
        'explorador_bd': (
            context.tiene_acceso_global or
            current_user.get('role') == 'Administrador'
        ),
        'alertas': (
            context.tiene_acceso_global or
            current_user.get('role') in ['Supervisor', 'Administrador']
        ),
        'usuarios': (
            context.tiene_acceso_global or
            current_user.get('role') == 'Administrador' or
            'SISTEMA_USUARIOS_VER' in context.permisos
        ),
    }
    
    return {
        'user_id': context.user_id,
        'email': context.email,
        'role_legacy': current_user.get('role'),
        'tiene_acceso_global': context.tiene_acceso_global,
        'fuente_acceso': context.fuente_acceso,
        'permisos_modulos': modulos_permisos,
        'permisos_funcionales': context.permisos,
        'sec_roles': context.sec_roles,
        'servers_count': len(context.servers_ids),
        'empresas_count': len(context.empresas_ids),
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
    
    # Obtener URL base del frontend
    # Usar el header Origin o Referer, o default a la URL de preview
    origin = request.headers.get("origin", "")
    if not origin:
        referer = request.headers.get("referer", "")
        if referer:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            origin = f"{parsed.scheme}://{parsed.netloc}"
    
    # Default a preview URL si no hay origin
    if not origin:
        import os
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
