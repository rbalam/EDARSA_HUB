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


class RefreshTokenReuseError(RuntimeError):
    """Error fail-closed al detectar rotacion concurrente o reutilizacion de refresh token."""


def _normalize_user_id_candidates(user_id: Any) -> list[str]:
    """Normaliza identificadores canonicos de usuario (sin hash() ni truncamiento)."""
    raw_items = user_id if isinstance(user_id, (list, tuple, set)) else [user_id]
    candidates: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        if item is None or isinstance(item, bool):
            continue
        text = str(item).strip()
        if not text:
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            candidates.append(text)
    return candidates


def _open_session_tx_connection():
    """Abre una conexion pymssql dedicada (autocommit=False) para transacciones atomicas de sesion."""
    import pymssql
    from core.db import parse_sql_server_host

    config = _get_sql_config()
    hostname, parsed_port, instance = parse_sql_server_host(config["host"], config["port"])
    server = f"{hostname}\\{instance}" if instance else hostname
    connect_kwargs = {
        "server": server,
        "user": config["username"],
        "password": config["password"],
        "database": config["database"],
        "timeout": 5,
        "login_timeout": 5,
        "autocommit": False,
    }
    if not instance and parsed_port:
        connect_kwargs["port"] = int(parsed_port)
    return pymssql.connect(**connect_kwargs)


async def _execute_sql_async(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
    """
    Ejecuta una query SQL de forma asincrona usando asyncio.to_thread.
    """
    import asyncio
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
                timeout_seconds=5
            )

            if fetch_one:
                if not results:
                    return None
                if isinstance(results[0], dict):
                    return tuple(results[0].values())
                return results[0]
            elif fetch_all:
                if results and isinstance(results[0], dict):
                    return [tuple(r.values()) for r in results]
                return results
            return results
        except Exception as e:
            logger.error(f"Error ejecutando SQL: {e}")
            raise

    return await asyncio.to_thread(_sync_execute)


async def is_session_active(
    session_id: str,
    expected_user_type: Optional[str] = None,
) -> bool:
    """
    Verifica fail-closed en dbo.Sesiones si un SesionID sigue activo y no revocado.
    Usa columna nombrada (SesionID) para compatibilidad estricta con pymssql as_dict=True.
    """
    sid = str(session_id or "").strip()
    if not sid:
        return False

    query = """
        SELECT TOP 1 SesionID
        FROM Sesiones
        WHERE
            SesionID = %s
            AND EstaActiva = 1
            AND FechaExpiracion > GETUTCDATE()
            AND FechaRevocacion IS NULL
    """
    params = [sid]
    if expected_user_type:
        query += """
            AND LOWER(LTRIM(RTRIM(ISNULL(TipoUsuario, '')))) =
                LOWER(LTRIM(RTRIM(%s)))
        """
        params.append(expected_user_type)

    result = await _execute_sql_async(query, tuple(params), fetch_one=True)
    if not result:
        return False
    first_val = result[0] if isinstance(result, (tuple, list)) else result
    return str(first_val or "").strip().lower() == sid.lower()


async def create_session(
    user_id: Any,
    refresh_token: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    user_type: str = "interno"
) -> Dict[str, Any]:
    """
    Crea una nueva sesion en EDARSAHUB.
    """
    candidates = _normalize_user_id_candidates(user_id)
    if not candidates:
        raise ValueError("INVALID_USER_ID_FOR_SESSION")
    canonical_user_id = candidates[0]

    session_id = str(uuid4())
    familia_id = str(uuid4())
    token_hash = hash_refresh_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS)

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
        session_id, canonical_user_id, user_type, token_hash, familia_id,
        expires_at,
        ip_address[:45] if ip_address else None,
        user_agent[:500] if user_agent else None
    )

    try:
        try:
            await _execute_sql_async(delete_query, (session_id,))
        except Exception:
            pass

        await _execute_sql_async(insert_query, insert_params)

        await _log_session_action(
            session_id=session_id,
            user_id=canonical_user_id,
            user_type=user_type,
            action="login",
            ip_address=ip_address,
            user_agent=user_agent
        )

        logger.info(f"Sesión creada para usuario {canonical_user_id}, session_id={session_id[:8]}...")

        return {
            "session_id": session_id,
            "familia_id": familia_id,
            "expires_at": expires_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Error creando sesión: {e}")
        raise


async def validate_and_get_session(
    refresh_token: str,
    expected_user_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Valida un refresh token y retorna la sesion si es valida.
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
            AND FechaRevocacion IS NULL
    """
    params = [token_hash]
    if expected_user_type:
        query += """
            AND LOWER(LTRIM(RTRIM(ISNULL(TipoUsuario, '')))) =
                LOWER(LTRIM(RTRIM(%s)))
        """
        params.append(expected_user_type)

    try:
        result = await _execute_sql_async(query, tuple(params), fetch_one=True)

        if result:
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


def _execute_atomic_rotation_sync(
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
    """
    Ejecuta UPDATE (con UPDLOCK, HOLDLOCK y validacion rowcount==1) + INSERT
    dentro de una unica transaccion SQL Server para evitar rotacion concurrente duplicada.
    """
    conn = _open_session_tx_connection()
    try:
        cur = conn.cursor()
        if old_token_hash:
            query_invalidate = """
                UPDATE Sesiones WITH (UPDLOCK, HOLDLOCK)
                SET
                    EstaActiva = 0,
                    FechaRevocacion = GETUTCDATE(),
                    MotivoRevocacion = 'token_rotated',
                    ReemplazadaPorSesionID = %s,
                    FechaModificacion = GETUTCDATE()
                WHERE SesionID = %s
                  AND RefreshTokenHash = %s
                  AND EstaActiva = 1
                  AND FechaExpiracion > GETUTCDATE()
                  AND FechaRevocacion IS NULL
            """
            inv_params = (new_session_id, old_session_id, old_token_hash)
        else:
            query_invalidate = """
                UPDATE Sesiones WITH (UPDLOCK, HOLDLOCK)
                SET
                    EstaActiva = 0,
                    FechaRevocacion = GETUTCDATE(),
                    MotivoRevocacion = 'token_rotated',
                    ReemplazadaPorSesionID = %s,
                    FechaModificacion = GETUTCDATE()
                WHERE SesionID = %s
                  AND EstaActiva = 1
                  AND FechaExpiracion > GETUTCDATE()
                  AND FechaRevocacion IS NULL
            """
            inv_params = (new_session_id, old_session_id)

        cur.execute(query_invalidate, inv_params)
        if cur.rowcount != 1:
            conn.rollback()
            return False

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
        ins_params = (
            new_session_id,
            user_id,
            user_type,
            new_token_hash,
            familia_id,
            expires_at_str,
            ip_address[:45] if ip_address else None,
            user_agent[:500] if user_agent else None,
        )
        cur.execute(query_insert, ins_params)
        conn.commit()
        return True
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


async def rotate_refresh_token(
    old_session_id: str,
    familia_id: str,
    user_id: Any,
    new_refresh_token: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    user_type: str = "interno",
    old_refresh_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Rota el refresh token de forma atomica (una sola transaccion SQL con UPDLOCK, HOLDLOCK).

    Si otro request concurrente ya roto o revoco la sesion (rowcount != 1):
    - Revoca la familia completa de tokens (fail-closed)
    - Lanza RefreshTokenReuseError para rechazar con HTTP 401
    """
    import asyncio

    candidates = _normalize_user_id_candidates(user_id)
    if not candidates:
        raise ValueError("INVALID_USER_ID_FOR_ROTATION")
    canonical_user_id = candidates[0]

    new_session_id = str(uuid4())
    new_token_hash = hash_refresh_token(new_refresh_token)
    old_token_hash = hash_refresh_token(old_refresh_token) if old_refresh_token else None
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS)

    try:
        rotated = await asyncio.to_thread(
            _execute_atomic_rotation_sync,
            old_session_id=old_session_id,
            new_session_id=new_session_id,
            familia_id=familia_id,
            user_id=canonical_user_id,
            new_token_hash=new_token_hash,
            old_token_hash=old_token_hash,
            expires_at_str=expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            ip_address=ip_address,
            user_agent=user_agent,
            user_type=user_type,
        )

        if not rotated:
            logger.warning(
                f"ROTACION CONCURRENTE / REPLAY DETECTADO para usuario {canonical_user_id}, "
                f"sesion {str(old_session_id)[:8]}..., familia {str(familia_id)[:8]}..."
            )
            try:
                await revoke_session_family(
                    familia_id=familia_id,
                    user_id=canonical_user_id,
                    reason="replay_detected",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            except Exception as rev_exc:
                logger.error(f"Error revocando familia tras replay concurrente: {rev_exc}")
            raise RefreshTokenReuseError("Refresh token ya fue utilizado o revocado")

        await _log_session_action(
            session_id=new_session_id,
            user_id=canonical_user_id,
            user_type=user_type,
            action="refresh",
            ip_address=ip_address,
            user_agent=user_agent,
            details={"previous_session": old_session_id}
        )

        logger.info(f"Token rotado atomicamente para usuario {canonical_user_id}: {old_session_id[:8]}... -> {new_session_id[:8]}...")

        return {
            "session_id": new_session_id,
            "familia_id": familia_id,
            "expires_at": expires_at.isoformat()
        }

    except RefreshTokenReuseError:
        raise
    except Exception as e:
        logger.error(f"Error rotando token: {e}")
        raise


async def detect_and_handle_replay(
    refresh_token: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    expected_user_type: Optional[str] = None,
) -> Tuple[bool, Optional[Dict]]:
    """
    Detecta si un refresh token es un intento de replay y revoca la familia completa.
    """
    token_hash = hash_refresh_token(refresh_token)

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
    params = [token_hash]
    if expected_user_type:
        query += """
            AND LOWER(LTRIM(RTRIM(ISNULL(TipoUsuario, '')))) =
                LOWER(LTRIM(RTRIM(%s)))
        """
        params.append(expected_user_type)

    try:
        result = await _execute_sql_async(query, tuple(params), fetch_one=True)

        if result:
            session_info = {
                "session_id": str(result[0]),
                "user_id": result[1],
                "user_type": result[2],
                "familia_id": str(result[3]),
                "replaced_by": str(result[5]) if result[5] else None
            }

            logger.warning(f"REPLAY DETECTADO para usuario {session_info['user_id']}, familia {session_info['familia_id'][:8]}...")

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
    revoked_by_user_id: Optional[Any] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> bool:
    """
    Revoca una sesion especifica en dbo.Sesiones.
    """
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
        revoked_by_str = str(revoked_by_user_id).strip() if revoked_by_user_id is not None else None

        query_revoke = """
            UPDATE Sesiones WITH (UPDLOCK, HOLDLOCK)
            SET
                EstaActiva = 0,
                FechaRevocacion = GETUTCDATE(),
                MotivoRevocacion = %s,
                RevocadoPorUsuarioID = %s,
                FechaModificacion = GETUTCDATE()
            WHERE SesionID = %s AND EstaActiva = 1
        """

        await _execute_sql_async(query_revoke, (reason, revoked_by_str, session_id))

        await _log_session_action(
            session_id=session_id,
            user_id=user_id,
            user_type=user_type,
            action=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            performed_by=revoked_by_str
        )

        logger.info(f"Sesión {session_id[:8]}... revocada. Motivo: {reason}")

        return True

    except Exception as e:
        logger.error(f"Error revocando sesión: {e}")
        raise


async def revoke_session_family(
    familia_id: str,
    user_id: Any,
    reason: str = "security",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> int:
    """
    Revoca TODAS las sesiones activas de una familia de tokens.
    """
    query_get = """
        SELECT SesionID, TipoUsuario
        FROM Sesiones
        WHERE FamiliaTokenID = %s AND EstaActiva = 1
    """

    try:
        sessions = await _execute_sql_async(query_get, (familia_id,), fetch_all=True)

        if not sessions:
            return 0

        query_revoke = """
            UPDATE Sesiones WITH (UPDLOCK, HOLDLOCK)
            SET
                EstaActiva = 0,
                FechaRevocacion = GETUTCDATE(),
                MotivoRevocacion = %s,
                FechaModificacion = GETUTCDATE()
            WHERE FamiliaTokenID = %s AND EstaActiva = 1
        """

        await _execute_sql_async(query_revoke, (reason, familia_id))

        for session in sessions:
            session_id, user_type = session
            await _log_session_action(
                session_id=str(session_id),
                user_id=str(user_id),
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
    user_id: Any,
    reason: str = "logout_all",
    except_session_id: Optional[str] = None,
    revoked_by_user_id: Optional[Any] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    expected_user_type: Optional[str] = None,
) -> int:
    """
    Revoca TODAS las sesiones activas de un usuario por sus identificadores canonicos
    (PublicUUID, UsuarioID o alias en dbo.Sesiones.UsuarioID), sin hash() inseguro.
    """
    candidates = _normalize_user_id_candidates(user_id)
    if not candidates:
        raise ValueError("USER_ID_REQUIRED_FOR_SESSION_REVOCATION")

    placeholders = ", ".join(["%s"] * len(candidates))
    where_clauses = [
        f"CAST(UsuarioID AS VARCHAR(100)) IN ({placeholders})",
        "EstaActiva = 1",
    ]
    filter_params: list[Any] = list(candidates)

    if expected_user_type:
        where_clauses.append(
            "LOWER(LTRIM(RTRIM(ISNULL(TipoUsuario, '')))) = LOWER(LTRIM(RTRIM(%s)))"
        )
        filter_params.append(expected_user_type)

    if except_session_id:
        where_clauses.append("SesionID != %s")
        filter_params.append(except_session_id)

    where_sql = " AND ".join(where_clauses)
    query_get = f"""
        SELECT SesionID, TipoUsuario, UsuarioID
        FROM Sesiones
        WHERE {where_sql}
    """

    try:
        sessions = await _execute_sql_async(query_get, tuple(filter_params), fetch_all=True)

        if not sessions:
            return 0

        revoked_by_str = str(revoked_by_user_id).strip() if revoked_by_user_id is not None else None
        query_revoke = f"""
            UPDATE Sesiones WITH (UPDLOCK, HOLDLOCK)
            SET
                EstaActiva = 0,
                FechaRevocacion = GETUTCDATE(),
                MotivoRevocacion = %s,
                RevocadoPorUsuarioID = %s,
                FechaModificacion = GETUTCDATE()
            WHERE {where_sql}
        """
        params_revoke = tuple([reason, revoked_by_str] + filter_params)
        await _execute_sql_async(query_revoke, params_revoke)

        for session in sessions:
            session_id = session[0]
            user_type = session[1]
            stored_uid = session[2] if len(session) > 2 else candidates[0]
            await _log_session_action(
                session_id=str(session_id),
                user_id=str(stored_uid),
                user_type=user_type,
                action=reason,
                ip_address=ip_address,
                user_agent=user_agent,
                performed_by=revoked_by_str
            )

        logger.info(f"Revocadas {len(sessions)} sesiones del usuario {candidates[0]}. Motivo: {reason}")

        return len(sessions)

    except Exception as e:
        logger.error(f"Error revocando sesiones del usuario: {e}")
        raise


async def get_user_active_sessions(user_id: Any, expected_user_type: Optional[str] = None) -> list:
    """
    Obtiene todas las sesiones activas de un usuario por sus identificadores canonicos.
    """
    candidates = _normalize_user_id_candidates(user_id)
    if not candidates:
        return []

    placeholders = ", ".join(["%s"] * len(candidates))
    where_clauses = [
        f"CAST(UsuarioID AS VARCHAR(100)) IN ({placeholders})",
        "EstaActiva = 1",
        "FechaExpiracion > GETUTCDATE()",
        "FechaRevocacion IS NULL",
    ]
    params: list[Any] = list(candidates)
    if expected_user_type:
        where_clauses.append(
            "LOWER(LTRIM(RTRIM(ISNULL(TipoUsuario, '')))) = LOWER(LTRIM(RTRIM(%s)))"
        )
        params.append(expected_user_type)

    query = f"""
        SELECT
            SesionID, FechaCreacion, FechaExpiracion, UltimaActividad,
            IPCliente, UserAgent
        FROM Sesiones
        WHERE {" AND ".join(where_clauses)}
        ORDER BY UltimaActividad DESC
    """

    try:
        results = await _execute_sql_async(query, tuple(params), fetch_all=True)

        sessions = []
        for row in results or []:
            sessions.append({
                "session_id": str(row[0]),
                "created_at": row[1].isoformat() if hasattr(row[1], "isoformat") else (str(row[1]) if row[1] else None),
                "expires_at": row[2].isoformat() if hasattr(row[2], "isoformat") else (str(row[2]) if row[2] else None),
                "last_activity": row[3].isoformat() if hasattr(row[3], "isoformat") else (str(row[3]) if row[3] else None),
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
