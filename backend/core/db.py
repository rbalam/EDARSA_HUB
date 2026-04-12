"""
EDARSA HUB - Conexiones a Base de Datos
=======================================
Gestión centralizada de conexiones a MongoDB y SQL Server.

FASE 1 DEL REFACTOR MODULAR (Diciembre 2025):
- Migrado: execute_sql_query() y funciones de soporte
- Migrado: Sistema de caché de estado de servidores (cooldown)
- Migrado: Parseo de cadenas de conexión SQL Server

COMPATIBILIDAD:
- server.py mantiene wrappers que importan desde aquí
- portal_proveedores.py usa la función vía init_portal_db()
- Todos los endpoints existentes siguen funcionando sin cambios

USO:
    from core.db import execute_sql_query, test_sql_connection
"""

import re
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

# Imports para SQL Server
import pymssql
import pytds

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
                results = list(cursor.fetchall())
            else:
                # pytds
                cursor = conn.cursor()
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
            
            logging.debug(f"Query exitosa via pool ({driver}): {len(results)} registros")
            mark_server_online(host)
            return results
            
    except Exception as pool_error:
        error_str = str(pool_error)
        logging.warning(f"Pool falló para {host}: {error_str}")
        
        # Fallback: conexión directa sin pool (para casos edge)
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
    timeout_seconds: int = 45
) -> List[Dict]:
    """
    Ejecuta query SQL con conexión directa (fallback si el pool falla).
    
    Esta es la implementación original, mantenida como fallback de seguridad.
    No debe usarse directamente - usar execute_sql_query().
    """
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    logging.info(f"[FALLBACK] Conexión directa a SQL Server: {hostname}:{parsed_port}")
    
    # Intentar con pytds
    try:
        logging.info("[FALLBACK] Ejecutando query con pytds...")
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
        logging.info(f"[FALLBACK] Query exitosa con pytds: {len(results)} registros")
        mark_server_online(host)
        return results
        
    except Exception as pytds_error:
        logging.warning(f"[FALLBACK] pytds falló: {str(pytds_error)}, intentando pymssql...")
    
    # Fallback a pymssql
    try:
        server_string = f"{hostname}\\{instance}" if instance else hostname
        logging.info(f"[FALLBACK] Ejecutando query con pymssql en {server_string}:{parsed_port}...")
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
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        for row in results:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
        
        logging.info(f"[FALLBACK] Query exitosa con pymssql: {len(results)} registros")
        mark_server_online(host)
        return results
        
    except Exception as pymssql_error:
        error_msg = f"[FALLBACK] Error ejecutando consulta. pytds y pymssql fallaron: {str(pymssql_error)}"
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
# EXPORTACIONES PÚBLICAS
# ============================================================================

__all__ = [
    # SQL Server - Migrado en Fase 1, Pool en Prioridad 1
    'execute_sql_query',
    'test_sql_connection',
    'parse_sql_server_host',
    '_execute_sql_query_direct',  # Fallback interno
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
