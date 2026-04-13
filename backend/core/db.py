"""
EDARSA HUB - Conexiones a Base de Datos
=======================================
Gestión centralizada de conexiones a MongoDB y SQL Server.

FASE 1 DEL REFACTOR MODULAR (Diciembre 2025):
- Migrado: execute_sql_query() y funciones de soporte
- Migrado: Sistema de caché de estado de servidores (cooldown)
- Migrado: Parseo de cadenas de conexión SQL Server

INTEGRACIÓN RESILIENTE (Abril 2026):
- Reintentos automáticos con backoff exponencial
- Timeouts incrementados para servidores remotos (30s login, 90s query)
- Clasificación de errores: red, autenticación, query, desconocido
- Health check disponible para diagnóstico

COMPATIBILIDAD:
- server.py mantiene wrappers que importan desde aquí
- portal_proveedores.py usa la función vía init_portal_db()
- Todos los endpoints existentes siguen funcionando sin cambios

USO:
    from core.db import execute_sql_query, test_sql_connection
"""

import re
import logging
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
from enum import Enum

# Imports para SQL Server
import pymssql
import pytds


# ============================================================================
# CONFIGURACIÓN DE RESILIENCIA (Abril 2026)
# ============================================================================

class ResilientConfig:
    """Configuración para conexiones resilientes a SQL Server remoto"""
    
    # Timeouts incrementados para servidor remoto
    LOGIN_TIMEOUT = 30          # Timeout para establecer conexión (antes: 15s)
    QUERY_TIMEOUT = 90          # Timeout para queries (antes: 45s)
    CONNECT_TIMEOUT = 30        # Timeout general de conexión
    
    # Reintentos
    MAX_RETRIES = 3             # Número máximo de reintentos
    RETRY_DELAY_BASE = 2        # Segundos base entre reintentos
    RETRY_DELAY_MAX = 15        # Máximo delay entre reintentos
    RETRY_BACKOFF = 2           # Multiplicador de backoff exponencial
    
    # Health check
    HEALTH_CHECK_QUERY = "SELECT 1 AS health"
    HEALTH_CHECK_TIMEOUT = 15
    
    # Errores recuperables (se puede reintentar)
    RECOVERABLE_ERRORS = [
        "connection timed out",
        "dbprocess is dead",
        "adaptive server connection",
        "connection reset",
        "broken pipe",
        "network error",
        "temporarily unavailable",
        "connection refused",
        "login timeout",
        "communication link failure"
    ]


class ConnectionErrorType(Enum):
    """Tipos de errores de conexión SQL Server"""
    NETWORK = "network"           # Error de red (timeout, conexión rechazada)
    AUTH = "authentication"       # Error de autenticación
    QUERY = "query"               # Error en la query SQL
    TIMEOUT = "timeout"           # Timeout específico
    DEAD_CONNECTION = "dead_connection"  # Conexión muerta (DBPROCESS dead)
    UNKNOWN = "unknown"           # Error desconocido


def classify_error(error: Exception) -> Tuple[ConnectionErrorType, str]:
    """
    Clasifica un error de conexión SQL Server para determinar si es recuperable.
    
    Returns:
        Tuple (tipo de error, descripción)
    """
    error_str = str(error).lower()
    
    # Errores no críticos (retornar como query success con 0 resultados)
    non_critical = ["previous statement didn't produce any results", "no results"]
    for keyword in non_critical:
        if keyword in error_str:
            return (ConnectionErrorType.QUERY, "Query sin resultados (no es error)")
    
    # Conexión muerta (específico)
    if "dbprocess is dead" in error_str or "dbprocess dead" in error_str:
        return (ConnectionErrorType.DEAD_CONNECTION, "Conexión muerta - pool inválido")
    
    # Timeouts
    timeout_keywords = ["timed out", "timeout", "login timeout"]
    for keyword in timeout_keywords:
        if keyword in error_str:
            return (ConnectionErrorType.TIMEOUT, f"Timeout: {keyword}")
    
    # Errores de red
    network_keywords = [
        "connection reset", "broken pipe", "network", "refused", 
        "unreachable", "adaptive server", "temporarily unavailable",
        "communication link"
    ]
    for keyword in network_keywords:
        if keyword in error_str:
            return (ConnectionErrorType.NETWORK, f"Error de red: {keyword}")
    
    # Errores de autenticación
    auth_keywords = ["login failed", "authentication", "access denied", "permission"]
    for keyword in auth_keywords:
        if keyword in error_str:
            return (ConnectionErrorType.AUTH, f"Error de autenticación: {keyword}")
    
    # Errores de query SQL
    query_keywords = ["syntax error", "invalid column", "invalid object", "conversion"]
    for keyword in query_keywords:
        if keyword in error_str:
            return (ConnectionErrorType.QUERY, f"Error de query: {keyword}")
    
    return (ConnectionErrorType.UNKNOWN, str(error)[:150])


def is_recoverable_error(error: Exception) -> bool:
    """Determina si un error es recuperable (se puede reintentar)"""
    error_str = str(error).lower()
    return any(keyword in error_str for keyword in ResilientConfig.RECOVERABLE_ERRORS)


def get_retry_delay(attempt: int) -> float:
    """Calcula el delay para un reintento con backoff exponencial"""
    delay = ResilientConfig.RETRY_DELAY_BASE * (ResilientConfig.RETRY_BACKOFF ** (attempt - 1))
    return min(delay, ResilientConfig.RETRY_DELAY_MAX)

# ============================================================================
# VARIABLES GLOBALES - CACHÉ DE ESTADO DE SERVIDORES
# ============================================================================
# Diccionario en memoria para tracking rápido de estado de servidores.
# Implementa backoff exponencial para evitar comportamiento de bot/malware
# cuando un servidor SQL está caído.

_server_status_cache: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# FUNCIONES DE PARSEO DE CONEXIÓN SQL SERVER
# ============================================================================

def parse_sql_server_host(host: str, default_port: int = 1433) -> tuple:
    """
    Parsea cadenas de conexión SQL Server en varios formatos:
    - hostname
    - hostname,port
    - hostname\\instance
    - hostname,port\\instance
    - hostname\\instance,port
    
    Args:
        host: Cadena de conexión del host
        default_port: Puerto por defecto (1433)
    
    Returns:
        Tuple (hostname_only, port, instance)
        - hostname_only: solo el hostname sin instancia
        - port: puerto como entero
        - instance: nombre de la instancia o None
    """
    # Remover espacios
    host = host.strip()
    port = default_port
    instance = None
    hostname = host
    
    # Caso 1: hostname,port\instance (ej: server.ddns.net,6669\nationalsoft)
    match = re.match(r'^([^,\\]+),(\d+)\\(.+)$', host)
    if match:
        hostname = match.group(1)
        port = int(match.group(2))
        instance = match.group(3)
        logging.info(f"Parsed DDNS format: hostname={hostname}, port={port}, instance={instance}")
        return (hostname, port, instance)
    
    # Caso 2: hostname\instance,port (ej: server\instance,1433)
    match = re.match(r'^([^,\\]+)\\([^,]+),(\d+)$', host)
    if match:
        hostname = match.group(1)
        instance = match.group(2)
        port = int(match.group(3))
        logging.info(f"Parsed instance,port format: hostname={hostname}, instance={instance}, port={port}")
        return (hostname, port, instance)
    
    # Caso 3: hostname\instance (ej: server\SQLEXPRESS)
    match = re.match(r'^([^,\\]+)\\(.+)$', host)
    if match:
        hostname = match.group(1)
        instance = match.group(2)
        logging.info(f"Parsed instance format: hostname={hostname}, instance={instance}")
        return (hostname, port, instance)
    
    # Caso 4: hostname,port (ej: server.com,1433)
    match = re.match(r'^([^,\\]+),(\d+)$', host)
    if match:
        hostname = match.group(1)
        port = int(match.group(2))
        logging.info(f"Parsed host,port format: hostname={hostname}, port={port}")
        return (hostname, port, None)
    
    # Caso 5: Solo hostname
    logging.info(f"Using simple hostname: {host}")
    return (host, port, None)


# ============================================================================
# FUNCIONES DE CACHÉ DE ESTADO DE SERVIDORES (COOLDOWN)
# ============================================================================

def mark_server_offline(host: str) -> None:
    """
    Marca un servidor como offline en caché de memoria con backoff exponencial.
    
    El backoff exponencial evita que el sistema parezca un ataque cuando
    un servidor SQL está caído, incrementando el tiempo de espera entre reintentos.
    
    Args:
        host: Hostname del servidor
    """
    global _server_status_cache
    current = _server_status_cache.get(host, {})
    fail_count = current.get("fail_count", 0) + 1
    
    # Backoff exponencial: 5min, 10min, 20min, 30min máximo
    wait_minutes = min(5 * (2 ** (fail_count - 1)), 30)
    
    _server_status_cache[host] = {
        "is_online": False,
        "last_check": datetime.now(timezone.utc),
        "fail_count": fail_count,
        "wait_minutes": wait_minutes
    }
    logging.info(f"Servidor {host} marcado offline (intento {fail_count}) - próximo reintento en {wait_minutes} min")


def mark_server_online(host: str) -> None:
    """
    Marca un servidor como online en caché de memoria.
    Resetea el contador de fallos y el tiempo de espera.
    
    Args:
        host: Hostname del servidor
    """
    global _server_status_cache
    _server_status_cache[host] = {
        "is_online": True,
        "last_check": datetime.now(timezone.utc),
        "fail_count": 0,
        "wait_minutes": 0
    }


def is_server_offline_in_memory(host: str) -> bool:
    """
    Verifica si un servidor está marcado como offline.
    Usa backoff exponencial para evitar parecer un ataque.
    
    Args:
        host: Hostname del servidor
        
    Returns:
        True si el servidor está en cooldown, False si se puede intentar conexión
    """
    status = _server_status_cache.get(host)
    if not status:
        return False
    
    if status.get("is_online", True):
        return False
    
    # Verificar si ha pasado suficiente tiempo según el backoff
    last_check = status.get("last_check")
    wait_minutes = status.get("wait_minutes", 5)
    
    if last_check:
        diff = (datetime.now(timezone.utc) - last_check).total_seconds() / 60
        if diff < wait_minutes:
            logging.debug(f"Servidor {host} en cooldown - esperar {wait_minutes - diff:.1f} min más")
            return True
    
    return False


def get_server_cooldown_info(host: str) -> dict:
    """
    Obtiene información del cooldown de un servidor.
    
    Args:
        host: Hostname del servidor
        
    Returns:
        Dict con información del estado:
        - is_offline: bool
        - fail_count: int (si offline)
        - wait_minutes: int (si offline)
        - remaining_minutes: float (si offline)
    """
    status = _server_status_cache.get(host, {})
    if not status or status.get("is_online", True):
        return {"is_offline": False}
    
    last_check = status.get("last_check")
    wait_minutes = status.get("wait_minutes", 5)
    
    if last_check:
        diff = (datetime.now(timezone.utc) - last_check).total_seconds() / 60
        remaining = max(0, wait_minutes - diff)
        return {
            "is_offline": True,
            "fail_count": status.get("fail_count", 0),
            "wait_minutes": wait_minutes,
            "remaining_minutes": round(remaining, 1)
        }
    
    return {"is_offline": True}


def reset_server_cache() -> None:
    """
    Resetea completamente el caché de estado de servidores.
    Útil para testing o cuando se necesita forzar reconexiones.
    """
    global _server_status_cache
    _server_status_cache = {}
    logging.info("Server status cache reset")


def get_server_cache_status() -> Dict[str, Any]:
    """
    Obtiene el estado actual del caché de servidores.
    Útil para debugging y monitoreo.
    
    Returns:
        Dict con estado de todos los servidores en caché
    """
    return dict(_server_status_cache)


# ============================================================================
# FUNCIONES DE CONEXIÓN SQL SERVER
# ============================================================================

def test_sql_connection(host: str, port: int, database: str, username: str, password: str) -> bool:
    """
    Prueba la conexión a SQL Server usando pytds (preferido) con fallback a pymssql.
    
    Args:
        host: Hostname del servidor (puede incluir instancia y/o puerto)
        port: Puerto por defecto
        database: Nombre de la base de datos
        username: Usuario
        password: Contraseña
        
    Returns:
        True si la conexión es exitosa, False en caso contrario
    """
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    logging.info(f"Testing connection to: hostname={hostname}, port={parsed_port}, instance={instance}, db={database}")
    
    # Primero intentar con pytds (mejor soporte para conexiones complejas)
    try:
        logging.info("Intentando conexión con pytds...")
        conn = pytds.connect(
            server=hostname,
            port=parsed_port,
            database=database,
            user=username,
            password=password,
            timeout=30,
            login_timeout=30
        )
        conn.close()
        logging.info("Conexión exitosa con pytds")
        return True
    except Exception as pytds_error:
        logging.warning(f"pytds falló: {str(pytds_error)}, intentando pymssql...")
    
    # Fallback a pymssql
    try:
        server_string = f"{hostname}\\{instance}" if instance else hostname
        conn = pymssql.connect(
            server=server_string, 
            port=parsed_port, 
            user=username, 
            password=password, 
            database=database
        )
        conn.close()
        logging.info("Conexión exitosa con pymssql")
        return True
    except Exception as pymssql_error:
        logging.error(f"pymssql también falló: {str(pymssql_error)}")
        return False


def execute_sql_query(
    host: str, 
    port: int, 
    database: str, 
    username: str, 
    password: str, 
    query: str, 
    timeout_seconds: int = 45
) -> List[Dict]:
    """
    Ejecuta una consulta SQL usando connection pooling centralizado.
    
    REFACTORIZADO EN PRIORIDAD 1 (Abril 2026):
    - Ahora usa pool de conexiones en lugar de crear conexión por request
    - Reduce overhead de 100-500ms a ~5ms por conexión
    - Mantiene compatibilidad total con llamadas existentes
    
    Incluye verificación de estado offline con backoff exponencial.
    
    Args:
        host: Hostname del servidor SQL (puede incluir instancia y/o puerto)
        port: Puerto por defecto
        database: Nombre de la base de datos
        username: Usuario
        password: Contraseña
        query: Query SQL a ejecutar
        timeout_seconds: Timeout en segundos (default 45)
        
    Returns:
        Lista de diccionarios con los resultados. Lista vacía si hay error.
    """
    # Verificar si el servidor está en cooldown (offline con backoff)
    if is_server_offline_in_memory(host):
        cooldown = get_server_cooldown_info(host)
        logging.info(f"Servidor {host} en cooldown - {cooldown.get('remaining_minutes', 0):.1f} min restantes")
        return []
    
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    logging.debug(f"Conectando a SQL Server vía pool: hostname={hostname}, port={parsed_port}, db={database}")
    
    # Importar pool aquí para evitar import circular
    from core.pool import pooled_connection, get_pool_manager
    
    try:
        # Usar connection pooling
        with pooled_connection(hostname, parsed_port, database, username, password, instance) as conn:
            # Determinar el driver usado para este pool
            driver = get_pool_manager().get_pool_driver(hostname, parsed_port, database)
            
            if driver == "pymssql":
                cursor = conn.cursor(as_dict=True)
                cursor.execute(query)
                # pymssql maneja bien UPDATE/INSERT - fetchall retorna vacío
                try:
                    results = list(cursor.fetchall())
                except Exception:
                    results = []  # UPDATE/INSERT no tienen resultados
            else:
                # pytds
                cursor = conn.cursor()
                cursor.execute(query)
                # Verificar si hay resultados antes de fetchall
                # cursor.description es None para UPDATE/INSERT/DELETE
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    results = []
                    for row in rows:
                        row_dict = {}
                        for i, col in enumerate(columns):
                            row_dict[col] = row[i]
                        results.append(row_dict)
                else:
                    # UPDATE/INSERT/DELETE - no hay resultados
                    results = []
            
            # Convertir datetime a string ISO
            for row in results:
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row[key] = value.isoformat()
            
            logging.debug(f"Query exitosa via pool ({driver}): {len(results)} registros")
            mark_server_online(host)
            return results
            
    except Exception as pool_error:
        error_str = str(pool_error).lower()
        logging.warning(f"Pool falló para {host}: {pool_error}")
        
        # "Previous statement didn't produce any results" no es error real
        # Significa que la query fue exitosa pero no retornó filas (ej: SELECT sin resultados)
        if "previous statement didn't produce" in error_str:
            logging.info(f"Query sin resultados para {host} (no es error)")
            mark_server_online(host)
            return []  # Lista vacía = sin resultados
        
        # Detectar errores de conexión muerta y limpiar el pool
        dead_pool_indicators = ["dbprocess is dead", "connection reset", "broken pipe", "dead connection"]
        if any(indicator in error_str for indicator in dead_pool_indicators):
            logging.warning(f"Pool corrupto detectado para {host} - limpiando...")
            try:
                from core.pool import get_pool_manager
                get_pool_manager().close_pool(hostname, parsed_port, database)
            except Exception as cleanup_error:
                logging.warning(f"Error limpiando pool: {cleanup_error}")
        
        # Fallback: conexión directa con reintentos resilientes
        return _execute_sql_query_direct(
            host, port, database, username, password, query, timeout_seconds
        )


def execute_sql_query_params(
    host: str, 
    port: int, 
    database: str, 
    username: str, 
    password: str, 
    query: str,
    params: tuple = None,
    timeout_seconds: int = 45
) -> List[Dict]:
    """
    Ejecuta una consulta SQL con PARÁMETROS NATIVOS para prevenir SQL Injection.
    
    FASE 6C-B (Diciembre 2025):
    - Usa parámetros nativos del driver (pymssql/pytds)
    - Los parámetros se pasan al driver, NO se interpolan en la query
    - Formato de placeholders: %s para pymssql, %s para pytds
    
    Args:
        host: Hostname del servidor SQL
        port: Puerto
        database: Nombre de la base de datos
        username: Usuario
        password: Contraseña
        query: Query SQL con placeholders %s (ej: "SELECT * FROM t WHERE id = %s")
        params: Tupla de parámetros (ej: (123,) o ("valor", 456))
        timeout_seconds: Timeout en segundos
        
    Returns:
        Lista de diccionarios con los resultados.
        
    Ejemplo:
        execute_sql_query_params(
            host, port, db, user, pwd,
            "SELECT * FROM users WHERE name = %s AND age > %s",
            ("Juan", 18)
        )
    """
    # Verificar si el servidor está en cooldown
    if is_server_offline_in_memory(host):
        cooldown = get_server_cooldown_info(host)
        logging.info(f"Servidor {host} en cooldown - {cooldown.get('remaining_minutes', 0):.1f} min restantes")
        return []
    
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    logging.debug(f"Conectando a SQL Server vía pool (params): hostname={hostname}, port={parsed_port}, db={database}")
    
    from core.pool import pooled_connection, get_pool_manager
    
    try:
        with pooled_connection(hostname, parsed_port, database, username, password, instance) as conn:
            driver = get_pool_manager().get_pool_driver(hostname, parsed_port, database)
            
            if driver == "pymssql":
                cursor = conn.cursor(as_dict=True)
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                results = list(cursor.fetchall())
            else:
                # pytds
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i]
                    results.append(row_dict)
            
            # Convertir datetime a string ISO
            for row in results:
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row[key] = value.isoformat()
            
            logging.debug(f"Query params exitosa via pool ({driver}): {len(results)} registros")
            mark_server_online(host)
            return results
            
    except Exception as pool_error:
        error_str = str(pool_error)
        logging.warning(f"Pool (params) falló para {host}: {error_str}")
        
        # Fallback: conexión directa
        return _execute_sql_query_params_direct(
            host, port, database, username, password, query, params, timeout_seconds
        )


def _execute_sql_query_params_direct(
    host: str, 
    port: int, 
    database: str, 
    username: str, 
    password: str, 
    query: str,
    params: tuple = None,
    timeout_seconds: int = 45
) -> List[Dict]:
    """
    Ejecuta query SQL con parámetros usando conexión directa (fallback).
    """
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    logging.info(f"[FALLBACK] Conexión directa con params a SQL Server: {hostname}:{parsed_port}")
    
    # Intentar con pytds
    try:
        conn = pytds.connect(
            server=hostname,
            port=parsed_port,
            database=database,
            user=username,
            password=password,
            timeout=timeout_seconds,
            login_timeout=15
        )
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                if isinstance(value, datetime):
                    value = value.isoformat()
                row_dict[col] = value
            results.append(row_dict)
        
        conn.close()
        mark_server_online(host)
        return results
        
    except Exception as pytds_error:
        logging.warning(f"[FALLBACK] pytds params falló: {str(pytds_error)}, intentando pymssql...")
    
    # Fallback a pymssql
    try:
        server_string = f"{hostname}\\{instance}" if instance else hostname
        conn = pymssql.connect(
            server=server_string, 
            port=parsed_port, 
            user=username, 
            password=password, 
            database=database, 
            timeout=timeout_seconds, 
            login_timeout=15
        )
        cursor = conn.cursor(as_dict=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = list(cursor.fetchall())
        
        for row in results:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
        
        conn.close()
        mark_server_online(host)
        return results
        
    except Exception as pymssql_error:
        logging.error(f"[FALLBACK] pymssql params también falló: {str(pymssql_error)}")
        mark_server_offline(host, str(pymssql_error))
        return []


def _execute_sql_query_direct(
    host: str, 
    port: int, 
    database: str, 
    username: str, 
    password: str, 
    query: str, 
    timeout_seconds: int = None,
    max_retries: int = None
) -> List[Dict]:
    """
    Ejecuta query SQL con conexión directa y REINTENTOS RESILIENTES.
    
    INTEGRACIÓN RESILIENTE (Abril 2026):
    - Reintentos automáticos con backoff exponencial
    - Timeouts incrementados (30s login, 90s query por defecto)
    - Clasificación de errores para decidir si reintentar
    - Logging detallado para diagnóstico
    
    Esta función se usa como fallback cuando el pool falla.
    
    Args:
        host: Hostname del servidor SQL
        port: Puerto
        database: Base de datos
        username: Usuario
        password: Contraseña
        query: Query SQL
        timeout_seconds: Timeout personalizado (default: ResilientConfig.QUERY_TIMEOUT)
        max_retries: Número de reintentos (default: ResilientConfig.MAX_RETRIES)
    
    Returns:
        Lista de diccionarios con resultados. Lista vacía si falla.
    """
    # Usar configuración resiliente por defecto
    timeout_seconds = timeout_seconds or ResilientConfig.QUERY_TIMEOUT
    max_retries = max_retries or ResilientConfig.MAX_RETRIES
    login_timeout = ResilientConfig.LOGIN_TIMEOUT
    
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        logging.info(f"[RESILIENT] Intento {attempt}/{max_retries} - {hostname}:{parsed_port}/{database}")
        
        # Intentar con pytds primero
        try:
            start_time = time.time()
            conn = pytds.connect(
                server=hostname,
                port=parsed_port,
                database=database,
                user=username,
                password=password,
                timeout=timeout_seconds,
                login_timeout=login_timeout
            )
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Verificar si hay resultados antes de fetchall
            # cursor.description es None para UPDATE/INSERT/DELETE
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        row_dict[col] = value
                    results.append(row_dict)
            else:
                # UPDATE/INSERT/DELETE - no hay resultados
                results = []
            
            conn.close()
            elapsed = (time.time() - start_time) * 1000
            logging.info(f"[RESILIENT] Query exitosa con pytds: {len(results)} registros en {elapsed:.0f}ms")
            mark_server_online(host)
            return results
            
        except Exception as pytds_error:
            error_type, error_desc = classify_error(pytds_error)
            
            # "Previous statement didn't produce any results" no es un error real
            # Es que la query no retornó resultados (ej: UPDATE sin OUTPUT)
            if "previous statement didn't produce" in str(pytds_error).lower():
                logging.info("[RESILIENT] Query completada sin resultados (pytds)")
                mark_server_online(host)
                return []  # Retornar lista vacía, no es error
            
            logging.warning(f"[RESILIENT] pytds falló (intento {attempt}): {error_type.value} - {error_desc}")
            last_error = pytds_error
            
            # Si es error de autenticación o query sintáctica, no reintentar
            if error_type in [ConnectionErrorType.AUTH]:
                break  # Error definitivo
            if error_type == ConnectionErrorType.QUERY and "invalid column" in str(pytds_error).lower():
                break  # Error de query inválida
        
        # Fallback a pymssql
        try:
            server_string = f"{hostname}\\{instance}" if instance else hostname
            start_time = time.time()
            
            conn = pymssql.connect(
                server=server_string, 
                port=parsed_port, 
                user=username, 
                password=password, 
                database=database, 
                timeout=timeout_seconds, 
                login_timeout=login_timeout
            )
            cursor = conn.cursor(as_dict=True)
            cursor.execute(query)
            results = list(cursor.fetchall())
            conn.close()
            
            for row in results:
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row[key] = value.isoformat()
            
            elapsed = (time.time() - start_time) * 1000
            logging.info(f"[RESILIENT] Query exitosa con pymssql: {len(results)} registros en {elapsed:.0f}ms")
            mark_server_online(host)
            return results
            
        except Exception as pymssql_error:
            error_type, error_desc = classify_error(pymssql_error)
            logging.warning(f"[RESILIENT] pymssql falló (intento {attempt}): {error_type.value} - {error_desc}")
            last_error = pymssql_error
            
            # Si es error de autenticación o query, no reintentar
            if error_type in [ConnectionErrorType.AUTH, ConnectionErrorType.QUERY]:
                logging.error(f"[RESILIENT] Error no recuperable: {error_type.value}")
                mark_server_offline(host)
                return []
        
        # Si es error recuperable y hay más intentos, aplicar backoff
        if attempt < max_retries and is_recoverable_error(last_error):
            delay = get_retry_delay(attempt)
            logging.info(f"[RESILIENT] Esperando {delay:.1f}s antes del siguiente intento (backoff)...")
            time.sleep(delay)
        elif attempt >= max_retries:
            break
    
    # Todos los intentos fallaron
    error_msg = f"[RESILIENT] Fallaron {max_retries} intentos. Último error: {str(last_error)[:200]}"
    logging.error(error_msg)
    mark_server_offline(host)
    return []


# ============================================================================
# FUNCIONES DE MONGODB (Placeholders para fases futuras)
# ============================================================================

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient

# Variables globales para conexiones MongoDB (se inicializarán en migración futura)
_mongo_client: Optional[AsyncIOMotorClient] = None
_mongo_db: Optional[AsyncIOMotorDatabase] = None
_sync_mongo_client: Optional[MongoClient] = None


async def get_mongo_client() -> AsyncIOMotorClient:
    """
    Obtiene el cliente MongoDB async.
    NOTA: No implementado aún - usar conexión de server.py
    """
    global _mongo_client
    if _mongo_client is None:
        raise RuntimeError("MongoDB client not initialized. Use server.py connection.")
    return _mongo_client


async def get_mongo_db() -> AsyncIOMotorDatabase:
    """
    Obtiene la base de datos MongoDB async.
    NOTA: No implementado aún - usar conexión de server.py
    """
    global _mongo_db
    if _mongo_db is None:
        raise RuntimeError("MongoDB database not initialized. Use server.py connection.")
    return _mongo_db


def get_sync_mongo_db():
    """
    Obtiene la base de datos MongoDB síncrona.
    NOTA: No implementado aún - usar conexión de server.py
    """
    global _sync_mongo_client
    if _sync_mongo_client is None:
        raise RuntimeError("Sync MongoDB client not initialized. Use server.py connection.")
    return _sync_mongo_client


def init_db_connections(mongo_url: str, db_name: str):
    """
    Inicializa las conexiones a bases de datos.
    NOTA: Se usará cuando se migre MongoDB desde server.py (fase futura)
    """
    pass


# ============================================================================
# FUNCIONES DE HEALTH CHECK SQL SERVER (Abril 2026)
# ============================================================================

def sql_health_check(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str
) -> Dict[str, Any]:
    """
    Ejecuta un health check completo de conexión SQL Server.
    
    Retorna un diagnóstico detallado incluyendo:
    - Estado de conexión
    - Latencia
    - Tipo de error si falla
    - Recomendaciones
    
    Args:
        host: Hostname del servidor
        port: Puerto
        database: Base de datos
        username: Usuario
        password: Contraseña
    
    Returns:
        Dict con diagnóstico completo
    """
    result = {
        "healthy": False,
        "server": None,
        "database": database,
        "latency_ms": None,
        "error": None,
        "error_type": None,
        "driver_used": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "login_timeout": ResilientConfig.LOGIN_TIMEOUT,
            "query_timeout": ResilientConfig.QUERY_TIMEOUT,
            "max_retries": ResilientConfig.MAX_RETRIES
        },
        "recommendations": []
    }
    
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    result["server"] = f"{hostname}:{parsed_port}"
    if instance:
        result["server"] += f"\\{instance}"
    
    # Verificar si está en cooldown
    if is_server_offline_in_memory(host):
        cooldown = get_server_cooldown_info(host)
        result["error"] = f"Servidor en cooldown - {cooldown.get('remaining_minutes', 0):.1f} min restantes"
        result["error_type"] = "cooldown"
        result["recommendations"].append("Esperar a que termine el cooldown o resetear caché con /api/sistema/pool-reset")
        return result
    
    start_time = time.time()
    
    # Intentar con pytds
    try:
        conn = pytds.connect(
            server=hostname,
            port=parsed_port,
            database=database,
            user=username,
            password=password,
            timeout=ResilientConfig.HEALTH_CHECK_TIMEOUT,
            login_timeout=ResilientConfig.HEALTH_CHECK_TIMEOUT
        )
        cursor = conn.cursor()
        cursor.execute(ResilientConfig.HEALTH_CHECK_QUERY)
        cursor.fetchone()
        conn.close()
        
        latency = (time.time() - start_time) * 1000
        result["healthy"] = True
        result["latency_ms"] = round(latency, 2)
        result["driver_used"] = "pytds"
        
        # Recomendaciones según latencia
        if latency > 3000:
            result["recommendations"].append(f"Latencia MUY ALTA ({latency:.0f}ms) - conexión inestable")
        elif latency > 1000:
            result["recommendations"].append(f"Latencia ALTA ({latency:.0f}ms) - considerar aumentar timeouts")
        elif latency > 500:
            result["recommendations"].append(f"Latencia MODERADA ({latency:.0f}ms) - conexión funcional")
        else:
            result["recommendations"].append("Conexión saludable - sin problemas detectados")
        
        logging.info(f"[HEALTH] SQL Server {hostname} OK - Latencia: {latency:.0f}ms")
        return result
        
    except Exception as pytds_error:
        logging.warning(f"[HEALTH] pytds falló: {pytds_error}")
    
    # Fallback a pymssql
    try:
        server_string = f"{hostname}\\{instance}" if instance else hostname
        conn = pymssql.connect(
            server=server_string,
            port=parsed_port,
            user=username,
            password=password,
            database=database,
            timeout=ResilientConfig.HEALTH_CHECK_TIMEOUT,
            login_timeout=ResilientConfig.HEALTH_CHECK_TIMEOUT
        )
        cursor = conn.cursor()
        cursor.execute(ResilientConfig.HEALTH_CHECK_QUERY)
        cursor.fetchone()
        conn.close()
        
        latency = (time.time() - start_time) * 1000
        result["healthy"] = True
        result["latency_ms"] = round(latency, 2)
        result["driver_used"] = "pymssql"
        
        if latency > 3000:
            result["recommendations"].append(f"Latencia MUY ALTA ({latency:.0f}ms) - conexión inestable")
        elif latency > 1000:
            result["recommendations"].append(f"Latencia ALTA ({latency:.0f}ms) - considerar aumentar timeouts")
        else:
            result["recommendations"].append("Conexión saludable con pymssql")
        
        logging.info(f"[HEALTH] SQL Server {hostname} OK (pymssql) - Latencia: {latency:.0f}ms")
        return result
        
    except Exception as pymssql_error:
        latency = (time.time() - start_time) * 1000
        error_type, error_desc = classify_error(pymssql_error)
        
        result["latency_ms"] = round(latency, 2)
        result["error"] = str(pymssql_error)[:200]
        result["error_type"] = error_type.value
        
        # Recomendaciones según tipo de error
        if error_type == ConnectionErrorType.TIMEOUT:
            result["recommendations"].append("Timeout de conexión - verificar firewall y accesibilidad de red")
            result["recommendations"].append("El servidor puede estar sobrecargado o inaccesible")
        elif error_type == ConnectionErrorType.DEAD_CONNECTION:
            result["recommendations"].append("Pool de conexiones inválido - ejecutar /api/sistema/pool-reset")
        elif error_type == ConnectionErrorType.AUTH:
            result["recommendations"].append("Error de autenticación - verificar credenciales")
        elif error_type == ConnectionErrorType.NETWORK:
            result["recommendations"].append("Error de red - verificar conectividad con el servidor")
        else:
            result["recommendations"].append(f"Error desconocido: {error_desc}")
        
        logging.error(f"[HEALTH] SQL Server {hostname} FAILED - {error_type.value}: {error_desc}")
        return result


# ============================================================================
# EXPORTACIONES PÚBLICAS
# ============================================================================

__all__ = [
    # SQL Server - Migrado en Fase 1, Pool en Prioridad 1
    'execute_sql_query',
    'execute_sql_query_params',
    'test_sql_connection',
    'parse_sql_server_host',
    '_execute_sql_query_direct',  # Fallback interno con reintentos
    # Health Check (Abril 2026)
    'sql_health_check',
    # Configuración resiliente
    'ResilientConfig',
    'ConnectionErrorType',
    'classify_error',
    'is_recoverable_error',
    'get_retry_delay',
    # Caché de servidores - Migrado en Fase 1
    'mark_server_offline',
    'mark_server_online',
    'is_server_offline_in_memory',
    'get_server_cooldown_info',
    'reset_server_cache',
    'get_server_cache_status',
    # MongoDB - Placeholders
    'get_mongo_client',
    'get_mongo_db',
    'get_sync_mongo_db',
    'init_db_connections',
]
