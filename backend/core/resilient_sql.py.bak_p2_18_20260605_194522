from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - SQL Server Resilient Connection
=============================================
Capa de conexión resiliente para SQL Server remoto.

MEJORAS IMPLEMENTADAS (Abril 2026):
1. Timeouts incrementados para servidor remoto
2. Reintentos automáticos con backoff
3. Health check antes de queries críticos
4. Mejor manejo de errores de red vs errores de query
5. Logging detallado para diagnóstico

USO:
    from core.resilient_sql import execute_resilient_query, test_connection_health
    
    # Query simple con reintentos automáticos
    results = await execute_resilient_query(db, "SELECT * FROM tabla")
    
    # Health check
    health = await test_connection_health(db)
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum

import pymssql
import pytds

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURACIÓN DE RESILIENCIA
# =============================================================================

class ResilientConfig:
    """Configuración para conexiones resilientes"""
    
    # Timeouts (incrementados para servidor remoto)
    LOGIN_TIMEOUT = 30          # Timeout para establecer conexión (era 15)
    QUERY_TIMEOUT = 90          # Timeout para queries (era 45)
    CONNECT_TIMEOUT = 30        # Timeout general de conexión
    
    # Reintentos
    MAX_RETRIES = 3             # Número máximo de reintentos
    RETRY_DELAY_BASE = 2        # Segundos base entre reintentos
    RETRY_DELAY_MAX = 15        # Máximo delay entre reintentos
    RETRY_BACKOFF = 2           # Multiplicador de backoff
    
    # Health check
    HEALTH_CHECK_QUERY = "SELECT 1 AS health"
    HEALTH_CHECK_TIMEOUT = 10
    
    # Errores recuperables (se reintenta)
    RECOVERABLE_ERRORS = [
        "connection timed out",
        "dbprocess is dead",
        "adaptive server connection",
        "connection reset",
        "broken pipe",
        "network error",
        "temporarily unavailable",
        "connection refused"
    ]


class ConnectionErrorType(Enum):
    """Tipos de errores de conexión"""
    NETWORK = "network"           # Error de red (timeout, conexión rechazada)
    AUTH = "authentication"       # Error de autenticación
    QUERY = "query"               # Error en la query SQL
    UNKNOWN = "unknown"           # Error desconocido


# =============================================================================
# ID DEL SERVIDOR EDARSA HUB
# =============================================================================

EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"


# =============================================================================
# FUNCIONES DE DIAGNÓSTICO
# =============================================================================

def classify_error(error: Exception) -> Tuple[ConnectionErrorType, str]:
    """
    Clasifica un error de conexión SQL Server.
    
    Returns:
        Tuple (tipo de error, descripción)
    """
    error_str = str(error).lower()
    
    # Errores de red/timeout
    network_keywords = [
        "timed out", "timeout", "connection reset", "broken pipe",
        "network", "refused", "unreachable", "dbprocess is dead",
        "adaptive server", "temporarily unavailable"
    ]
    for keyword in network_keywords:
        if keyword in error_str:
            return (ConnectionErrorType.NETWORK, f"Error de red: {keyword}")
    
    # Errores de autenticación
    auth_keywords = ["login failed", "authentication", "access denied", "permission"]
    for keyword in auth_keywords:
        if keyword in error_str:
            return (ConnectionErrorType.AUTH, f"Error de autenticación: {keyword}")
    
    # Errores de query
    query_keywords = ["syntax error", "invalid column", "invalid object", "conversion"]
    for keyword in query_keywords:
        if keyword in error_str:
            return (ConnectionErrorType.QUERY, f"Error de query: {keyword}")
    
    return (ConnectionErrorType.UNKNOWN, str(error)[:100])


def is_recoverable_error(error: Exception) -> bool:
    """Determina si un error es recuperable (se puede reintentar)"""
    error_str = str(error).lower()
    return any(keyword in error_str for keyword in ResilientConfig.RECOVERABLE_ERRORS)


def get_retry_delay(attempt: int) -> float:
    """Calcula el delay para un reintento con backoff exponencial"""
    delay = ResilientConfig.RETRY_DELAY_BASE * (ResilientConfig.RETRY_BACKOFF ** (attempt - 1))
    return min(delay, ResilientConfig.RETRY_DELAY_MAX)


# =============================================================================
# FUNCIONES DE CONEXIÓN RESILIENTE
# =============================================================================

async def get_edarsa_hub_server(db) -> Optional[Dict]:
    """Obtiene la configuración del servidor EDARSA HUB desde MongoDB."""
    try:
        server = await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})
        if not server:
            logger.error("Servidor EDARSA HUB no encontrado o inactivo")
            return None
        return server
    except Exception as e:
        logger.error(f"Error obteniendo configuración del servidor: {e}")
        return None


def create_connection(server: Dict, timeout_override: int = None) -> Optional[pymssql.Connection]:
    """
    Crea una conexión SQL Server con configuración resiliente.
    
    Args:
        server: Configuración del servidor
        timeout_override: Timeout personalizado (opcional)
        
    Returns:
        Conexión pymssql o None si falla
    """
    login_timeout = timeout_override or ResilientConfig.LOGIN_TIMEOUT
    query_timeout = timeout_override or ResilientConfig.QUERY_TIMEOUT
    
    try:
        conn = pymssql.connect(
            server=server['host'],
            port=server['port'],
            user=server['username'],
            password=server['password'],
            database=server['database'],
            login_timeout=login_timeout,
            timeout=query_timeout,
            autocommit=True,  # Para evitar transacciones pendientes
            charset='UTF8'
        )
        return conn
    except Exception as e:
        logger.warning(f"Error creando conexión: {e}")
        return None


async def test_connection_health(db) -> Dict[str, Any]:
    """
    Realiza un health check completo de la conexión a EDARSA HUB.
    
    Returns:
        Dict con estado de la conexión y diagnóstico
    """
    result = {
        "healthy": False,
        "server": None,
        "latency_ms": None,
        "error": None,
        "error_type": None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    server = await get_edarsa_hub_server(db)
    if not server:
        result["error"] = "Servidor EDARSA HUB no configurado"
        result["error_type"] = "configuration"
        return result
    
    result["server"] = f"{server['host']}:{server['port']}/{server['database']}"
    
    start_time = time.time()
    
    try:
        conn = pymssql.connect(
            server=server['host'],
            port=server['port'],
            user=server['username'],
            password=server['password'],
            database=server['database'],
            login_timeout=ResilientConfig.HEALTH_CHECK_TIMEOUT,
            timeout=ResilientConfig.HEALTH_CHECK_TIMEOUT
        )
        
        cursor = conn.cursor()
        cursor.execute(ResilientConfig.HEALTH_CHECK_QUERY)
        cursor.fetchone()
        conn.close()
        
        latency = (time.time() - start_time) * 1000
        
        result["healthy"] = True
        result["latency_ms"] = round(latency, 2)
        
        logger.info(f"Health check exitoso - Latencia: {result['latency_ms']}ms")
        
    except Exception as e:
        error_type, error_desc = classify_error(e)
        result["error"] = str(e)[:200]
        result["error_type"] = error_type.value
        result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
        
        logger.warning(f"Health check fallido - {error_type.value}: {error_desc}")
    
    return result


async def execute_resilient_query(
    db,
    query: str,
    max_retries: int = None,
    timeout: int = None
) -> Tuple[List[Dict], Optional[str]]:
    """
    Ejecuta una query SQL con reintentos automáticos y manejo de errores.
    
    Args:
        db: Conexión a MongoDB (para obtener credenciales)
        query: Query SQL a ejecutar
        max_retries: Número máximo de reintentos (default: 3)
        timeout: Timeout en segundos (default: 90)
        
    Returns:
        Tuple (resultados, error)
        - resultados: Lista de dicts con los resultados
        - error: String con el error si falló, None si fue exitoso
    """
    max_retries = max_retries or ResilientConfig.MAX_RETRIES
    timeout = timeout or ResilientConfig.QUERY_TIMEOUT
    
    server = await get_edarsa_hub_server(db)
    if not server:
        return ([], "Servidor EDARSA HUB no disponible")
    
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"Intento {attempt}/{max_retries} - Query: {query[:50]}...")
            
            conn = pymssql.connect(
                server=server['host'],
                port=server['port'],
                user=server['username'],
                password=server['password'],
                database=server['database'],
                login_timeout=ResilientConfig.LOGIN_TIMEOUT,
                timeout=timeout,
                autocommit=True,
                as_dict=True
            )
            
            cursor = conn.cursor()
            cursor.execute(query)
            
            results = list(cursor.fetchall())
            
            # Convertir datetime a string
            for row in results:
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row[key] = value.isoformat()
            
            conn.close()
            
            logger.debug(f"Query exitosa - {len(results)} registros")
            return (results, None)
            
        except Exception as e:
            last_error = e
            error_type, error_desc = classify_error(e)
            
            logger.warning(f"Intento {attempt} fallido - {error_type.value}: {error_desc}")
            
            # Si es error de autenticación o query, no reintentar
            if error_type in [ConnectionErrorType.AUTH, ConnectionErrorType.QUERY]:
                logger.error(f"Error no recuperable: {e}")
                return ([], str(e))
            
            # Si es recuperable y hay más intentos, esperar y reintentar
            if attempt < max_retries and is_recoverable_error(e):
                delay = get_retry_delay(attempt)
                logger.info(f"Esperando {delay}s antes del siguiente intento...")
                await asyncio.sleep(delay)
            else:
                break
    
    error_msg = f"Fallaron {max_retries} intentos. Último error: {str(last_error)[:200]}"
    logger.error(error_msg)
    return ([], error_msg)


async def execute_resilient_update(
    db,
    query: str,
    max_retries: int = None,
    timeout: int = None
) -> Tuple[bool, Optional[str]]:
    """
    Ejecuta una query de UPDATE/INSERT/DELETE con reintentos.
    
    Returns:
        Tuple (éxito, error)
    """
    max_retries = max_retries or ResilientConfig.MAX_RETRIES
    timeout = timeout or ResilientConfig.QUERY_TIMEOUT
    
    server = await get_edarsa_hub_server(db)
    if not server:
        return (False, "Servidor EDARSA HUB no disponible")
    
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"Intento UPDATE {attempt}/{max_retries}")
            
            conn = pymssql.connect(
                server=server['host'],
                port=server['port'],
                user=server['username'],
                password=server['password'],
                database=server['database'],
                login_timeout=ResilientConfig.LOGIN_TIMEOUT,
                timeout=timeout,
                autocommit=True
            )
            
            cursor = conn.cursor()
            cursor.execute(query)
            conn.close()
            
            logger.debug("UPDATE exitoso")
            return (True, None)
            
        except Exception as e:
            last_error = e
            error_type, error_desc = classify_error(e)
            
            logger.warning(f"Intento UPDATE {attempt} fallido - {error_type.value}")
            
            if error_type in [ConnectionErrorType.AUTH, ConnectionErrorType.QUERY]:
                return (False, str(e))
            
            if attempt < max_retries and is_recoverable_error(e):
                delay = get_retry_delay(attempt)
                await asyncio.sleep(delay)
            else:
                break
    
    return (False, f"Fallaron {max_retries} intentos: {str(last_error)[:200]}")


# =============================================================================
# FUNCIONES DE DIAGNÓSTICO EXTENDIDO
# =============================================================================

async def run_connection_diagnosis(db) -> Dict[str, Any]:
    """
    Ejecuta un diagnóstico completo de la conexión SQL Server.
    
    Returns:
        Dict con diagnóstico detallado
    """
    diagnosis = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server_config": None,
        "health_check": None,
        "query_test": None,
        "recommendations": []
    }
    
    # 1. Verificar configuración del servidor
    server = await get_edarsa_hub_server(db)
    if not server:
        diagnosis["server_config"] = {"status": "ERROR", "message": "Servidor no encontrado"}
        diagnosis["recommendations"].append("Verificar que el servidor EDARSA HUB esté configurado correctamente")
        return diagnosis
    
    diagnosis["server_config"] = {
        "status": "OK",
        "host": server['host'],
        "port": server['port'],
        "database": server['database']
    }
    
    # 2. Health check
    health = await test_connection_health(db)
    diagnosis["health_check"] = health
    
    if not health["healthy"]:
        if health["error_type"] == "network":
            diagnosis["recommendations"].append("Verificar conectividad de red con el servidor SQL")
            diagnosis["recommendations"].append("Verificar que el firewall permita la conexión al puerto")
        elif health["error_type"] == "authentication":
            diagnosis["recommendations"].append("Verificar credenciales de acceso a SQL Server")
        return diagnosis
    
    # 3. Query de prueba
    results, error = await execute_resilient_query(
        db, 
        "SELECT TOP 1 name FROM sys.tables",
        max_retries=2,
        timeout=30
    )
    
    if error:
        diagnosis["query_test"] = {"status": "ERROR", "error": error}
        diagnosis["recommendations"].append("La conexión funciona pero las queries fallan")
    else:
        diagnosis["query_test"] = {"status": "OK", "sample_result": results[0] if results else None}
    
    # 4. Recomendaciones basadas en latencia
    if health.get("latency_ms", 0) > 1000:
        diagnosis["recommendations"].append(f"Latencia alta ({health['latency_ms']}ms) - considerar aumentar timeouts")
    elif health.get("latency_ms", 0) > 500:
        diagnosis["recommendations"].append(f"Latencia moderada ({health['latency_ms']}ms) - conexión estable pero lenta")
    
    if not diagnosis["recommendations"]:
        diagnosis["recommendations"].append("Conexión saludable - sin problemas detectados")
    
    return diagnosis


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ResilientConfig',
    'ConnectionErrorType',
    'execute_resilient_query',
    'execute_resilient_update',
    'test_connection_health',
    'run_connection_diagnosis',
    'classify_error',
    'is_recoverable_error',
    'get_edarsa_hub_server',
    'EDARSA_HUB_SERVER_ID',
]
