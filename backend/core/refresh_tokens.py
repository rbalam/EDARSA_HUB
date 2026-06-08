from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Refresh Tokens Module
==================================
Sistema de refresh tokens con rotación y detección de replay.

FASE A: P1-REFRESH-TOKENS (2025-04-27)

Este módulo implementa:
- Generación de refresh tokens criptográficamente seguros
- Hash SHA256 para almacenamiento (nunca el token plano)
- Rotación de tokens en cada uso
- Detección de replay attacks
- Gestión de sesiones en EDARSAHUB SQL Server

SEGURIDAD:
- Los refresh tokens son opacos (UUID + entropy)
- Solo se almacena el hash SHA256
- La rotación invalida tokens anteriores
- El replay detecta tokens robados y revoca la familia completa
"""

import os
import secrets
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from uuid import uuid4

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN (Variables de entorno con defaults)
# ============================================================================

# Duración del access token en minutos (default 15 min)
ACCESS_TOKEN_MINUTES: int = int(os.environ.get('ACCESS_TOKEN_MINUTES', '15'))

# Duración del refresh token en días (default 7 días)
REFRESH_TOKEN_DAYS: int = int(os.environ.get('REFRESH_TOKEN_DAYS', '7'))

# Nombres de cookies para refresh tokens
REFRESH_COOKIE_NAME: str = "edarsa_refresh_token"
REFRESH_COOKIE_PATH: str = "/api/auth"  # Solo disponible en endpoints de auth


# ============================================================================
# GENERACIÓN Y HASH DE TOKENS
# ============================================================================

def generate_refresh_token() -> str:
    """
    Genera un refresh token criptográficamente seguro.
    
    El token es opaco (no JWT) para:
    - Permitir revocación desde el servidor
    - No exponer información en el token
    - Facilitar rotación
    
    Returns:
        Token de 43 caracteres (32 bytes en base64url)
    """
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """
    Genera el hash SHA256 del refresh token para almacenamiento.
    
    NUNCA se almacena el token plano en la base de datos.
    
    Args:
        token: Refresh token en texto plano
        
    Returns:
        Hash SHA256 en hexadecimal (64 caracteres)
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def verify_refresh_token_hash(token: str, stored_hash: str) -> bool:
    """
    Verifica que un token coincide con su hash almacenado.
    
    Args:
        token: Refresh token a verificar
        stored_hash: Hash almacenado en BD
        
    Returns:
        True si coinciden, False si no
    """
    computed_hash = hash_refresh_token(token)
    # Comparación de tiempo constante para evitar timing attacks
    return secrets.compare_digest(computed_hash, stored_hash)


# ============================================================================
# GESTIÓN DE COOKIES
# ============================================================================

def set_refresh_cookie(response, token: str) -> None:
    """
    Establece la cookie de refresh token.
    
    Características:
    - httpOnly: No accesible desde JavaScript
    - Secure: Solo HTTPS en producción
    - SameSite: Strict para máxima protección CSRF
    - Path: Restringido a endpoints de auth
    
    Args:
        response: FastAPI Response object
        token: Refresh token (texto plano, se envía al cliente)
    """
    is_production = os.environ.get("ENV", "production").lower() == "production"
    
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_production,
        samesite="strict",  # Más restrictivo que "lax"
        path=REFRESH_COOKIE_PATH,
        max_age=REFRESH_TOKEN_DAYS * 24 * 60 * 60
    )


def clear_refresh_cookie(response) -> None:
    """
    Elimina la cookie de refresh token.
    
    Args:
        response: FastAPI Response object
    """
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH
    )


def get_refresh_token_from_request(request) -> Optional[str]:
    """
    Extrae el refresh token de la cookie del request.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Refresh token o None si no existe
    """
    return request.cookies.get(REFRESH_COOKIE_NAME)


# ============================================================================
# OPERACIONES DE SESIÓN EN SQL SERVER
# ============================================================================

# Configuración de SQL Server para EDARSAHUB
_sql_config = None

def init_refresh_tokens_module(sql_config: dict) -> None:
    """
    Inicializa el módulo con la configuración de SQL Server.
    
    Args:
        sql_config: Dict con keys: host, port, database, username, password
    """
    global _sql_config
    _sql_config = sql_config
    logger.info("Módulo refresh_tokens inicializado con configuración SQL Server")


def _get_sql_config() -> dict:
    """Obtiene la configuración SQL inicializada."""
    if _sql_config is None:
        raise RuntimeError("Módulo refresh_tokens no inicializado. Llamar a init_refresh_tokens_module()")
    return _sql_config


async def _execute_sql_async(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
    """
    Ejecuta una query SQL de forma asíncrona usando executor.
    
    Args:
        query: Query SQL con placeholders %s
        params: Tupla de parámetros
        fetch_one: Si True, retorna solo un registro
        fetch_all: Si True, retorna todos los registros
        
    Returns:
        Resultados de la query o None
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    from core.db import execute_sql_query_params
    
    config = _get_sql_config()
    
    def _sync_execute():
        try:
            results = execute_sql_query_params(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                username=config['username'],
                password=config['password'],
                query=query,
                params=params,
                timeout_seconds=5  # Reducido de 30 a 5 segundos
            )
            
            if fetch_one and results:
                # Convertir dict a tuple para compatibilidad
                if isinstance(results[0], dict):
                    return tuple(results[0].values())
                return results[0]
            elif fetch_all:
                # Convertir dicts a tuples
                if results and isinstance(results[0], dict):
                    return [tuple(r.values()) for r in results]
                return results
            return results
        except Exception as e:
            logger.error(f"Error ejecutando SQL: {e}")
            raise
    
    # Ejecutar en thread pool para no bloquear el event loop
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, _sync_execute)


async def create_session(
    user_id: int,
    refresh_token: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    user_type: str = "interno"
) -> Dict[str, Any]:
    """
    Crea una nueva sesión en EDARSAHUB.
    
    Args:
        user_id: ID del usuario
        refresh_token: Refresh token generado (texto plano)
        ip_address: IP del cliente (opcional)
        user_agent: User-Agent del cliente (opcional)
        user_type: Tipo de usuario ('interno' o 'portal')
        
    Returns:
        Dict con session_id y familia_id
    """
    session_id = str(uuid4())
    familia_id = str(uuid4())
    token_hash = hash_refresh_token(refresh_token)
    
    # Calcular expiración
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS)
    
    # Primero intentar eliminar sesión existente con mismo ID (por si acaso)
    # Luego insertar nueva
    delete_query = "DELETE FROM Sesiones WHERE SesionID = %s"
    insert_query = """
        INSERT INTO Sesiones (
            SesionID, UsuarioID, TipoUsuario, RefreshTokenHash, FamiliaTokenID,
            FechaCreacion, FechaExpiracion, UltimaActividad,
            EstaActiva, IPCliente, UserAgent, FechaModificacion
        ) VALUES (
            %s, %s, %s, %s, %s,
            GETUTCDATE(), %s, GETUTCDATE(),
            1, %s, %s, GETUTCDATE()
        )
    """
    
    insert_params = (
        session_id, user_id, user_type, token_hash, familia_id,
        expires_at,  # Pasar datetime directamente, el driver lo convertirá
        ip_address[:45] if ip_address else None,
        user_agent[:500] if user_agent else None
    )
    
    try:
        # Primero eliminar si existe (evitar error de clave duplicada)
        try:
            await _execute_sql_async(delete_query, (session_id,))
        except Exception:
            pass  # Ignorar si no existe
        
        # Insertar nueva sesión
        await _execute_sql_async(insert_query, insert_params)
        
        # Registrar en histórico
        await _log_session_action(
            session_id=session_id,
            user_id=user_id,
            user_type=user_type,
            action="login",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Sesión creada para usuario {user_id}, session_id={session_id[:8]}...")
        
        return {
            "session_id": session_id,
            "familia_id": familia_id,
            "expires_at": expires_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creando sesión: {e}")
        raise


async def validate_and_get_session(refresh_token: str) -> Optional[Dict[str, Any]]:
    """
    Valida un refresh token y retorna la sesión si es válida.
    
    Args:
        refresh_token: Token a validar
        
    Returns:
        Dict con datos de sesión o None si inválido
    """
    token_hash = hash_refresh_token(refresh_token)
    
    query = """
        SELECT 
            SesionID, UsuarioID, TipoUsuario, FamiliaTokenID,
            FechaCreacion, FechaExpiracion, UltimaActividad,
            IPCliente, UserAgent
        FROM Sesiones
        WHERE 
            RefreshTokenHash = %s
            AND EstaActiva = 1
            AND FechaExpiracion > GETUTCDATE()
    """
    
    try:
        result = await _execute_sql_async(query, (token_hash,), fetch_one=True)
        
        if result:
            # SQL puede devolver datetimes como objetos datetime o como str
            # (según el driver/path). Normalizar defensivamente para no crashear
            # en .isoformat() (bug AUTH-REFRESH-500).
            def _iso(v):
                if v is None:
                    return None
                return v.isoformat() if hasattr(v, "isoformat") else str(v)

            return {
                "session_id": str(result[0]),
                "user_id": result[1],
                "user_type": result[2],
                "familia_id": str(result[3]),
                "created_at": _iso(result[4]),
                "expires_at": _iso(result[5]),
                "last_activity": _iso(result[6]),
                "ip_address": result[7],
                "user_agent": result[8]
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error validando sesión: {e}")
        raise


async def rotate_refresh_token(
    old_session_id: str,
    familia_id: str,
    user_id: int,
    new_refresh_token: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    user_type: str = "interno"
) -> Dict[str, Any]:
    """
    Rota el refresh token: invalida el anterior y crea uno nuevo.
    
    Este es el mecanismo principal de seguridad:
    - El token anterior queda inválido inmediatamente
    - Si alguien intenta usar el token anterior, se detecta como replay
    
    Args:
        old_session_id: ID de la sesión a invalidar
        familia_id: ID de familia (se mantiene para detección de replay)
        user_id: ID del usuario
        new_refresh_token: Nuevo token generado
        ip_address: IP actual
        user_agent: User-Agent actual
        user_type: Tipo de usuario
        
    Returns:
        Dict con nueva session_id y expires_at
    """
    new_session_id = str(uuid4())
    new_token_hash = hash_refresh_token(new_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS)
    
    try:
        # 1. Invalidar sesión anterior
        query_invalidate = """
            UPDATE Sesiones
            SET 
                EstaActiva = 0,
                FechaRevocacion = GETUTCDATE(),
                MotivoRevocacion = 'token_rotated',
                ReemplazadaPorSesionID = %s,
                FechaModificacion = GETUTCDATE()
            WHERE SesionID = %s AND EstaActiva = 1
        """
        await _execute_sql_async(query_invalidate, (new_session_id, old_session_id))
        
        # 2. Crear nueva sesión (misma familia)
        query_insert = """
            INSERT INTO Sesiones (
                SesionID, UsuarioID, TipoUsuario, RefreshTokenHash, FamiliaTokenID,
                FechaCreacion, FechaExpiracion, UltimaActividad,
                EstaActiva, IPCliente, UserAgent, FechaModificacion
            ) VALUES (
                %s, %s, %s, %s, %s,
                GETUTCDATE(), %s, GETUTCDATE(),
                1, %s, %s, GETUTCDATE()
            )
        """
        
        params = (
            new_session_id, user_id, user_type, new_token_hash, familia_id,
            expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            ip_address[:45] if ip_address else None,
            user_agent[:500] if user_agent else None
        )
        
        await _execute_sql_async(query_insert, params)
        
        # 3. Registrar en histórico
        await _log_session_action(
            session_id=new_session_id,
            user_id=user_id,
            user_type=user_type,
            action="refresh",
            ip_address=ip_address,
            user_agent=user_agent,
            details={"previous_session": old_session_id}
        )
        
        logger.info(f"Token rotado para usuario {user_id}: {old_session_id[:8]}... -> {new_session_id[:8]}...")
        
        return {
            "session_id": new_session_id,
            "expires_at": expires_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error rotando token: {e}")
        raise


async def detect_and_handle_replay(
    refresh_token: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Tuple[bool, Optional[Dict]]:
    """
    Detecta si un refresh token es un intento de replay.
    
    Un replay ocurre cuando:
    - El token ya fue rotado (existe en BD pero está inactivo)
    - El atacante intenta usar el token robado después de que la víctima lo rotó
    
    Si se detecta replay:
    - Se revoca TODA la familia de tokens
    - Tanto atacante como víctima quedan deslogueados
    - Se registra el evento de seguridad
    
    Args:
        refresh_token: Token a verificar
        ip_address: IP del request
        user_agent: User-Agent del request
        
    Returns:
        Tuple (is_replay, session_info)
        - is_replay: True si es un intento de replay
        - session_info: Info de la sesión afectada (para logging)
    """
    token_hash = hash_refresh_token(refresh_token)
    
    # Buscar si el token existió pero está inactivo (fue rotado)
    query = """
        SELECT 
            SesionID, UsuarioID, TipoUsuario, FamiliaTokenID,
            MotivoRevocacion, ReemplazadaPorSesionID
        FROM Sesiones
        WHERE 
            RefreshTokenHash = %s
            AND EstaActiva = 0
            AND MotivoRevocacion = 'token_rotated'
    """
    
    try:
        result = await _execute_sql_async(query, (token_hash,), fetch_one=True)
        
        if result:
            # ¡REPLAY DETECTADO!
            session_info = {
                "session_id": str(result[0]),
                "user_id": result[1],
                "user_type": result[2],
                "familia_id": str(result[3]),
                "replaced_by": str(result[5]) if result[5] else None
            }
            
            logger.warning(f"REPLAY DETECTADO para usuario {session_info['user_id']}, familia {session_info['familia_id'][:8]}...")
            
            # Revocar toda la familia
            await revoke_session_family(
                familia_id=session_info["familia_id"],
                user_id=session_info["user_id"],
                reason="replay_detected",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return True, session_info
        
        return False, None
        
    except Exception as e:
        logger.error(f"Error detectando replay: {e}")
        raise


async def revoke_session(
    session_id: str,
    reason: str = "logout",
    revoked_by_user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> bool:
    """
    Revoca una sesión específica.
    
    Args:
        session_id: ID de la sesión a revocar
        reason: Motivo ('logout', 'admin_revoked', 'security', etc.)
        revoked_by_user_id: ID del usuario que revoca (si es admin)
        ip_address: IP del request
        user_agent: User-Agent del request
        
    Returns:
        True si se revocó, False si no existía o ya estaba revocada
    """
    # Obtener info de la sesión antes de revocar
    query_get = """
        SELECT UsuarioID, TipoUsuario
        FROM Sesiones
        WHERE SesionID = %s AND EstaActiva = 1
    """
    
    try:
        session_info = await _execute_sql_async(query_get, (session_id,), fetch_one=True)
        
        if not session_info:
            return False
        
        user_id, user_type = session_info
        
        # Revocar
        query_revoke = """
            UPDATE Sesiones
            SET 
                EstaActiva = 0,
                FechaRevocacion = GETUTCDATE(),
                MotivoRevocacion = %s,
                RevocadoPorUsuarioID = %s,
                FechaModificacion = GETUTCDATE()
            WHERE SesionID = %s AND EstaActiva = 1
        """
        
        await _execute_sql_async(query_revoke, (reason, revoked_by_user_id, session_id))
        
        # Registrar en histórico
        await _log_session_action(
            session_id=session_id,
            user_id=user_id,
            user_type=user_type,
            action=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            performed_by=revoked_by_user_id
        )
        
        logger.info(f"Sesión {session_id[:8]}... revocada. Motivo: {reason}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error revocando sesión: {e}")
        raise


async def revoke_session_family(
    familia_id: str,
    user_id: int,
    reason: str = "security",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> int:
    """
    Revoca TODAS las sesiones de una familia.
    
    Se usa cuando se detecta replay attack.
    
    Args:
        familia_id: ID de la familia de tokens
        user_id: ID del usuario
        reason: Motivo de revocación
        ip_address: IP del request
        user_agent: User-Agent del request
        
    Returns:
        Número de sesiones revocadas
    """
    # Obtener todas las sesiones de la familia antes de revocar
    query_get = """
        SELECT SesionID, TipoUsuario
        FROM Sesiones
        WHERE FamiliaTokenID = %s AND EstaActiva = 1
    """
    
    try:
        sessions = await _execute_sql_async(query_get, (familia_id,), fetch_all=True)
        
        if not sessions:
            return 0
        
        # Revocar todas
        query_revoke = """
            UPDATE Sesiones
            SET 
                EstaActiva = 0,
                FechaRevocacion = GETUTCDATE(),
                MotivoRevocacion = %s,
                FechaModificacion = GETUTCDATE()
            WHERE FamiliaTokenID = %s AND EstaActiva = 1
        """
        
        await _execute_sql_async(query_revoke, (reason, familia_id))
        
        # Registrar cada sesión en histórico
        for session in sessions:
            session_id, user_type = session
            await _log_session_action(
                session_id=str(session_id),
                user_id=user_id,
                user_type=user_type,
                action=reason,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"familia_id": familia_id, "batch_revocation": True}
            )
        
        logger.warning(f"Familia {familia_id[:8]}... revocada ({len(sessions)} sesiones). Motivo: {reason}")
        
        return len(sessions)
        
    except Exception as e:
        logger.error(f"Error revocando familia: {e}")
        raise


async def revoke_all_user_sessions(
    user_id: int,
    reason: str = "logout_all",
    except_session_id: Optional[str] = None,
    revoked_by_user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> int:
    """
    Revoca TODAS las sesiones activas de un usuario.
    
    Args:
        user_id: ID del usuario
        reason: Motivo de revocación
        except_session_id: Sesión a excluir (opcional, para logout de otras)
        revoked_by_user_id: Quién revoca (si es admin)
        ip_address: IP del request
        user_agent: User-Agent del request
        
    Returns:
        Número de sesiones revocadas
    """
    # Construir query con o sin excepción
    if except_session_id:
        query_get = """
            SELECT SesionID, TipoUsuario
            FROM Sesiones
            WHERE UsuarioID = %s AND EstaActiva = 1 AND SesionID != %s
        """
        params_get = (user_id, except_session_id)
    else:
        query_get = """
            SELECT SesionID, TipoUsuario
            FROM Sesiones
            WHERE UsuarioID = %s AND EstaActiva = 1
        """
        params_get = (user_id,)
    
    try:
        sessions = await _execute_sql_async(query_get, params_get, fetch_all=True)
        
        if not sessions:
            return 0
        
        # Revocar todas
        if except_session_id:
            query_revoke = """
                UPDATE Sesiones
                SET 
                    EstaActiva = 0,
                    FechaRevocacion = GETUTCDATE(),
                    MotivoRevocacion = %s,
                    RevocadoPorUsuarioID = %s,
                    FechaModificacion = GETUTCDATE()
                WHERE UsuarioID = %s AND EstaActiva = 1 AND SesionID != %s
            """
            params_revoke = (reason, revoked_by_user_id, user_id, except_session_id)
        else:
            query_revoke = """
                UPDATE Sesiones
                SET 
                    EstaActiva = 0,
                    FechaRevocacion = GETUTCDATE(),
                    MotivoRevocacion = %s,
                    RevocadoPorUsuarioID = %s,
                    FechaModificacion = GETUTCDATE()
                WHERE UsuarioID = %s AND EstaActiva = 1
            """
            params_revoke = (reason, revoked_by_user_id, user_id)
        
        await _execute_sql_async(query_revoke, params_revoke)
        
        # Registrar en histórico
        for session in sessions:
            session_id, user_type = session
            await _log_session_action(
                session_id=str(session_id),
                user_id=user_id,
                user_type=user_type,
                action=reason,
                ip_address=ip_address,
                user_agent=user_agent,
                performed_by=revoked_by_user_id
            )
        
        logger.info(f"Revocadas {len(sessions)} sesiones del usuario {user_id}. Motivo: {reason}")
        
        return len(sessions)
        
    except Exception as e:
        logger.error(f"Error revocando sesiones del usuario: {e}")
        raise


async def get_user_active_sessions(user_id: int) -> list:
    """
    Obtiene todas las sesiones activas de un usuario.
    
    Útil para mostrar al usuario dónde tiene sesiones abiertas.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Lista de sesiones activas
    """
    query = """
        SELECT 
            SesionID, FechaCreacion, FechaExpiracion, UltimaActividad,
            IPCliente, UserAgent
        FROM Sesiones
        WHERE UsuarioID = %s AND EstaActiva = 1
        ORDER BY UltimaActividad DESC
    """
    
    try:
        results = await _execute_sql_async(query, (user_id,), fetch_all=True)
        
        sessions = []
        for row in results or []:
            sessions.append({
                "session_id": str(row[0]),
                "created_at": row[1].isoformat() if row[1] else None,
                "expires_at": row[2].isoformat() if row[2] else None,
                "last_activity": row[3].isoformat() if row[3] else None,
                "ip_address": row[4],
                "user_agent": row[5]
            })
        
        return sessions
        
    except Exception as e:
        logger.error(f"Error obteniendo sesiones del usuario: {e}")
        raise


# ============================================================================
# FUNCIONES AUXILIARES PRIVADAS
# ============================================================================

async def _log_session_action(
    session_id: str,
    user_id: int,
    user_type: str,
    action: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict] = None,
    performed_by: Optional[int] = None
) -> None:
    """
    Registra una acción de sesión en el histórico.
    
    Args:
        session_id: ID de la sesión
        user_id: ID del usuario
        user_type: Tipo de usuario
        action: Acción realizada
        ip_address: IP del cliente
        user_agent: User-Agent
        details: Detalles adicionales (se guarda como JSON)
        performed_by: ID del usuario que realizó la acción
    """
    import json
    details_json = json.dumps(details) if details else None
    
    query = """
        INSERT INTO SesionesHistorico (
            SesionID, UsuarioID, TipoUsuario, Accion,
            FechaAccion, IPCliente, UserAgent, DetallesJSON, AccionRealizadaPor
        ) VALUES (
            %s, %s, %s, %s,
            GETUTCDATE(), %s, %s, %s, %s
        )
    """
    
    params = (
        session_id, user_id, user_type, action,
        ip_address[:45] if ip_address else None,
        user_agent[:500] if user_agent else None,
        details_json,
        performed_by
    )
    
    try:
        await _execute_sql_async(query, params)
    except Exception as e:
        # No fallar la operación principal si el log falla
        logger.error(f"Error registrando historial de sesión: {e}")


async def update_session_activity(session_id: str) -> None:
    """
    Actualiza la marca de última actividad de una sesión.
    
    Args:
        session_id: ID de la sesión
    """
    query = """
        UPDATE Sesiones
        SET 
            UltimaActividad = GETUTCDATE(),
            FechaModificacion = GETUTCDATE()
        WHERE SesionID = %s AND EstaActiva = 1
    """
    
    try:
        await _execute_sql_async(query, (session_id,))
    except Exception as e:
        # No fallar la operación principal
        logger.error(f"Error actualizando actividad de sesión: {e}")
