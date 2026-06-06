"""
core/db.py
Compatibilidad legacy SQL-FIRST.

Reglas:
- NO abrir conexiones directas con pymssql.connect / pyodbc.connect aquí.
- EDARSAHUB SQL debe pasar por core.sql_first.db.
- Servidores externos deben pasar por core.pool o connection_factory.
- Este archivo conserva nombres legacy para no romper módulos antiguos.
"""

import logging
import time
import re
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass

from core.sql_first.db import (
    get_sql_connection,
    sql_connection,
    fetch_all_dict,
    fetch_one_dict,
    execute_sql,
)

from core.sql_first.connection_factory import (
    get_edarsahub_connection,
    get_edarsahub_pymssql_connection,
    get_external_sql_connection,
)


class ResilientConfig:
    LOGIN_TIMEOUT = 45
    QUERY_TIMEOUT = 120
    CONNECT_TIMEOUT = 45
    MAX_RETRIES = 4
    RETRY_DELAY_BASE = 2
    RETRY_DELAY_MAX = 20
    RETRY_BACKOFF = 2
    HEALTH_CHECK_QUERY = "SELECT 1 AS health"
    HEALTH_CHECK_TIMEOUT = 20
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
        "communication link failure",
        "server is unavailable",
        "operation timed out",
    ]


class ConnectionErrorType(Enum):
    NETWORK = "network"
    AUTH = "authentication"
    QUERY = "query"
    TIMEOUT = "timeout"
    DEAD_CONNECTION = "dead_connection"
    UNKNOWN = "unknown"


@dataclass
class SafeQueryResult:
    success: bool
    data: List[Dict[str, Any]]
    status: str
    message: str
    rows_affected: int = 0
    error_code: Optional[str] = None


_server_status_cache: Dict[str, Dict[str, Any]] = {}
_column_existence_cache: Dict[str, Dict[str, bool]] = {}


def get_connection():
    return get_sql_connection()


def get_db_connection():
    return get_sql_connection()


def get_conn():
    return get_sql_connection()


def classify_error(error: Exception) -> Tuple[ConnectionErrorType, str]:
    error_str = str(error).lower()

    if "dbprocess is dead" in error_str or "dbprocess dead" in error_str:
        return (ConnectionErrorType.DEAD_CONNECTION, "Conexión muerta")

    if "timed out" in error_str or "timeout" in error_str:
        return (ConnectionErrorType.TIMEOUT, "Timeout")

    for keyword in ["connection reset", "broken pipe", "network", "refused", "unreachable", "adaptive server"]:
        if keyword in error_str:
            return (ConnectionErrorType.NETWORK, f"Error red: {keyword}")

    for keyword in ["login failed", "authentication", "access denied", "permission"]:
        if keyword in error_str:
            return (ConnectionErrorType.AUTH, f"Error auth: {keyword}")

    for keyword in ["syntax error", "invalid column", "invalid object", "conversion"]:
        if keyword in error_str:
            return (ConnectionErrorType.QUERY, f"Error query: {keyword}")

    return (ConnectionErrorType.UNKNOWN, str(error)[:150])


def is_recoverable_error(error: Exception) -> bool:
    error_str = str(error).lower()
    return any(keyword in error_str for keyword in ResilientConfig.RECOVERABLE_ERRORS)


def get_retry_delay(attempt: int) -> float:
    delay = ResilientConfig.RETRY_DELAY_BASE * (ResilientConfig.RETRY_BACKOFF ** (attempt - 1))
    return min(delay, ResilientConfig.RETRY_DELAY_MAX)


def parse_sql_server_host(host: str, default_port: int = 1433) -> tuple:
    host = str(host or "").strip()
    port = default_port
    instance = None
    hostname = host

    match = re.match(r'^([^,\\]+),(\d+)\\(.+)$', host)
    if match:
        return (match.group(1), int(match.group(2)), match.group(3))

    match = re.match(r'^([^,\\]+)\\([^,]+),(\d+)$', host)
    if match:
        return (match.group(1), int(match.group(3)), match.group(2))

    match = re.match(r'^([^,\\]+)\\(.+)$', host)
    if match:
        return (match.group(1), port, match.group(2))

    match = re.match(r'^([^,\\]+),(\d+)$', host)
    if match:
        return (match.group(1), int(match.group(2)), None)

    return (hostname, port, instance)


def mark_server_offline(host: str, error: Exception = None) -> None:
    status = _server_status_cache.get(host, {})
    fail_count = int(status.get("fail_count", 0)) + 1
    wait_minutes = min(2 ** fail_count, 60)

    _server_status_cache[host] = {
        "is_online": False,
        "last_check": datetime.now(timezone.utc),
        "fail_count": fail_count,
        "wait_minutes": wait_minutes,
        "error": str(error)[:300] if error else None,
    }


def mark_server_online(host: str) -> None:
    _server_status_cache[host] = {
        "is_online": True,
        "last_check": datetime.now(timezone.utc),
        "fail_count": 0,
        "wait_minutes": 0,
        "error": None,
    }


def is_server_offline_in_memory(host: str) -> bool:
    status = _server_status_cache.get(host)
    if not status or status.get("is_online", True):
        return False

    last_check = status.get("last_check")
    wait_minutes = float(status.get("wait_minutes", 0))

    if not last_check:
        return False

    elapsed = (datetime.now(timezone.utc) - last_check).total_seconds() / 60
    return elapsed < wait_minutes


def get_server_cooldown_info(host: str) -> Dict[str, Any]:
    status = _server_status_cache.get(host, {})
    last_check = status.get("last_check")
    wait_minutes = float(status.get("wait_minutes", 0))

    remaining = 0
    if last_check:
        elapsed = (datetime.now(timezone.utc) - last_check).total_seconds() / 60
        remaining = max(0, wait_minutes - elapsed)

    return {
        "host": host,
        "is_offline": is_server_offline_in_memory(host),
        "fail_count": status.get("fail_count", 0),
        "wait_minutes": wait_minutes,
        "remaining_minutes": remaining,
        "error": status.get("error"),
    }


def reset_server_cache(host: str = None) -> Dict[str, Any]:
    if host:
        _server_status_cache.pop(host, None)
        return {"reset": host}
    _server_status_cache.clear()
    return {"reset": "all"}


def get_server_cache_status() -> Dict[str, Any]:
    return {
        "total": len(_server_status_cache),
        "servers": {
            host: get_server_cooldown_info(host)
            for host in _server_status_cache
        },
    }


def check_column_exists(host: str, port: int, database: str, username: str, password: str,
                        table: str, column: str) -> bool:
    cache_key = f"{host}:{database}"
    column_key = f"{table}.{column}"

    if cache_key in _column_existence_cache and column_key in _column_existence_cache[cache_key]:
        return _column_existence_cache[cache_key][column_key]

    _column_existence_cache.setdefault(cache_key, {})

    try:
        query = f"""
        SELECT TOP 1 1 AS existe
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table}'
          AND COLUMN_NAME = '{column}'
        """
        result = execute_sql_query(host, port, database, username, password, query)
        exists = bool(result)
        _column_existence_cache[cache_key][column_key] = exists
        return exists
    except Exception as e:
        logging.warning(f"[DB Cache] Error verificando columna {table}.{column}: {e}")
        _column_existence_cache[cache_key][column_key] = False
        return False


def get_propina_safe_column(has_propina: bool) -> str:
    return ""


def get_propina_safe_column_tempcheques(has_propina: bool) -> str:
    return ""


def _rows_to_dicts(cursor):
    if not getattr(cursor, "description", None):
        return []

    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    result = []

    for row in rows:
        if isinstance(row, dict):
            result.append(row)
        else:
            result.append({cols[i]: row[i] for i in range(len(cols))})

    for item in result:
        for k, v in list(item.items()):
            if isinstance(v, datetime):
                item[k] = v.isoformat()

    return result


def _external_config(host, port, database, username, password):
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    server = f"{hostname}\\{instance}" if instance else hostname

    return {
        "host": server,
        "port": parsed_port,
        "database": database,
        "username": username,
        "password": password,
    }


def execute_sql_query(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    query: str,
    timeout_seconds: int = 45,
    context: str = "web"
) -> List[Dict]:
    if is_server_offline_in_memory(host):
        logging.info(f"Servidor {host} en cooldown")
        return []

    hostname, parsed_port, instance = parse_sql_server_host(host, port)

    try:
        from core.pool import pooled_connection, get_pool_manager, POOL_CONTEXT_WEB, POOL_CONTEXT_JOBS

        pool_context = POOL_CONTEXT_JOBS if context == "jobs" else POOL_CONTEXT_WEB

        with pooled_connection(hostname, parsed_port, database, username, password, instance, context=pool_context) as conn:
            driver = get_pool_manager().get_pool_driver(hostname, parsed_port, database, context=pool_context)

            if driver == "pymssql":
                cursor = conn.cursor(as_dict=True)
            else:
                cursor = conn.cursor()

            cursor.execute(query)
            results = _rows_to_dicts(cursor)
            mark_server_online(host)
            return results

    except Exception as pool_error:
        logging.warning(f"Pool falló para {host}: {pool_error}")

        if "previous statement" in str(pool_error).lower():
            mark_server_online(host)
            return []

        # Fallback centralizado, sin pymssql.connect directo aquí
        try:
            config = _external_config(host, port, database, username, password)
            conn = get_external_sql_connection(config)
            try:
                try:
                    cursor = conn.cursor(as_dict=True)
                except TypeError:
                    cursor = conn.cursor()

                cursor.execute(query)
                results = _rows_to_dicts(cursor)
                mark_server_online(host)
                return results
            finally:
                conn.close()
        except Exception as e:
            if is_recoverable_error(e):
                mark_server_offline(host, e)
            logging.error(f"Error execute_sql_query {host}: {str(e)[:300]}")
            return []


def execute_sql_query_params(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    query: str,
    params: tuple = None,
    timeout_seconds: int = 45,
    context: str = "web"
) -> List[Dict]:
    if is_server_offline_in_memory(host):
        return []

    hostname, parsed_port, instance = parse_sql_server_host(host, port)

    try:
        from core.pool import pooled_connection, get_pool_manager, POOL_CONTEXT_WEB, POOL_CONTEXT_JOBS

        pool_context = POOL_CONTEXT_JOBS if context == "jobs" else POOL_CONTEXT_WEB

        with pooled_connection(hostname, parsed_port, database, username, password, instance, context=pool_context) as conn:
            driver = get_pool_manager().get_pool_driver(hostname, parsed_port, database, context=pool_context)

            if driver == "pymssql":
                cursor = conn.cursor(as_dict=True)
            else:
                cursor = conn.cursor()

            cursor.execute(query, params or ())
            results = _rows_to_dicts(cursor)
            mark_server_online(host)
            return results

    except Exception as e:
        logging.warning(f"Pool params falló para {host}: {e}")

        try:
            config = _external_config(host, port, database, username, password)
            conn = get_external_sql_connection(config)
            try:
                try:
                    cursor = conn.cursor(as_dict=True)
                except TypeError:
                    cursor = conn.cursor()

                cursor.execute(query, params or ())
                results = _rows_to_dicts(cursor)
                mark_server_online(host)
                return results
            finally:
                conn.close()
        except Exception as final_error:
            if is_recoverable_error(final_error):
                mark_server_offline(host, final_error)
            logging.error(f"Error execute_sql_query_params {host}: {str(final_error)[:300]}")
            return []


def test_sql_connection(host: str, port: int, database: str, username: str, password: str) -> bool:
    result = sql_health_check(host, port, database, username, password)
    return bool(result.get("healthy"))


def sql_health_check(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str
) -> Dict[str, Any]:
    result = {
        "healthy": False,
        "server": None,
        "database": database,
        "latency_ms": None,
        "error": None,
        "error_type": None,
        "driver_used": "central_factory",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "login_timeout": ResilientConfig.LOGIN_TIMEOUT,
            "query_timeout": ResilientConfig.QUERY_TIMEOUT,
            "max_retries": ResilientConfig.MAX_RETRIES,
        },
        "recommendations": [],
    }

    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    result["server"] = f"{hostname}:{parsed_port}"
    if instance:
        result["server"] += f"\\{instance}"

    if is_server_offline_in_memory(host):
        cooldown = get_server_cooldown_info(host)
        result["error"] = f"Servidor en cooldown - {cooldown.get('remaining_minutes', 0):.1f} min restantes"
        result["error_type"] = "cooldown"
        return result

    start = time.time()

    try:
        rows = execute_sql_query(
            host,
            port,
            database,
            username,
            password,
            ResilientConfig.HEALTH_CHECK_QUERY,
            timeout_seconds=ResilientConfig.HEALTH_CHECK_TIMEOUT,
        )

        latency = (time.time() - start) * 1000
        result["healthy"] = True
        result["latency_ms"] = round(latency, 2)
        result["recommendations"].append("Conexión saludable")
        mark_server_online(host)
        return result

    except Exception as e:
        latency = (time.time() - start) * 1000
        error_type, desc = classify_error(e)
        result["latency_ms"] = round(latency, 2)
        result["error"] = str(e)[:300]
        result["error_type"] = error_type.value
        result["recommendations"].append(desc)

        if is_recoverable_error(e):
            mark_server_offline(host, e)

        return result


def validate_system_type(server_config: Dict, expected_system_types: Optional[List[str]] = None):
    if not expected_system_types:
        return SafeQueryResult(True, [], "SUCCESS", "Sin validación system_type")

    system_type = str(server_config.get("system_type") or "").upper()
    expected = [str(x).upper() for x in expected_system_types]

    if system_type not in expected:
        return SafeQueryResult(
            False,
            [],
            "SYSTEM_TYPE_MISMATCH",
            f"system_type {system_type} no permitido. Esperado: {expected}",
            error_code="SYSTEM_TYPE_MISMATCH",
        )

    return SafeQueryResult(True, [], "SUCCESS", "system_type válido")


KNOWN_TABLES = {
    "SOFTRESTAURANT": ["cheques", "cheqdet", "productos", "grupos", "familias"],
    "SOFTRESTAURANT_PRO": ["cheques", "cheqdet", "productos", "grupos", "familias"],
    "MPRO": ["Venta_Encabezado", "Venta_Detalle", "Producto"],
    "MANAGEMENTPRO": ["Venta_Encabezado", "Venta_Detalle", "Producto"],
}


def execute_query_safe(
    server_config: Dict,
    query: str,
    expected_system_types: Optional[List[str]] = None,
    required_tables: Optional[List[str]] = None,
    module_name: str = "UNKNOWN",
    timeout_seconds: int = 45,
    validate_tables: bool = False
) -> SafeQueryResult:
    if expected_system_types:
        validation = validate_system_type(server_config, expected_system_types)
        if not validation.success:
            return validation

    required_fields = ["host", "port", "database", "username", "password"]
    missing = [f for f in required_fields if not server_config.get(f)]

    if missing:
        return SafeQueryResult(
            False,
            [],
            "CONNECTION_ERROR",
            f"Configuración incompleta. Campos faltantes: {', '.join(missing)}",
            error_code="MISSING_CONFIG",
        )

    if validate_tables and required_tables:
        system_type = server_config.get("system_type", "UNKNOWN")
        known = KNOWN_TABLES.get(str(system_type).upper(), [])
        unknown = [t for t in required_tables if t.lower() not in [k.lower() for k in known]]
        if unknown:
            logging.warning(f"[{module_name}] Tablas no reconocidas para {system_type}: {unknown}")

    try:
        data = execute_sql_query(
            server_config["host"],
            int(server_config.get("port") or 1433),
            server_config["database"],
            server_config["username"],
            server_config["password"],
            query,
            timeout_seconds,
        )

        return SafeQueryResult(
            True,
            data,
            "SUCCESS" if data else "NO_DATA",
            f"Query ejecutada. Registros: {len(data)}",
            rows_affected=len(data),
        )

    except Exception as e:
        error_str = str(e).lower()

        if "invalid object" in error_str:
            status = "SCHEMA_MISMATCH"
            code = "INVALID_TABLE"
        elif "timeout" in error_str:
            status = "CONNECTION_ERROR"
            code = "TIMEOUT"
        elif "login" in error_str or "authentication" in error_str:
            status = "CONNECTION_ERROR"
            code = "AUTH_FAILED"
        else:
            status = "QUERY_ERROR"
            code = "UNKNOWN"

        return SafeQueryResult(
            False,
            [],
            status,
            str(e)[:500],
            error_code=code,
        )


def get_sync_mongo_db():
    """
    Legacy placeholder.
    Mongo no debe ser fuente productiva.
    """
    raise RuntimeError("MongoDB no es fuente productiva. Usar SQL Server.")


def init_db_connections():
    return {"sql": True, "mongo": False}


def execute_query_safe_legacy(*args, **kwargs):
    return execute_query_safe(*args, **kwargs)
