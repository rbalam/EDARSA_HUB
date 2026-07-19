from fastapi import HTTPException


INVENTORY_SQL_ERROR_CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"
INVENTORY_SQL_ERROR_QUERY_TIMEOUT = "QUERY_TIMEOUT"
INVENTORY_SQL_ERROR_DEAD_DBPROCESS = "DEAD_DBPROCESS"
INVENTORY_SQL_ERROR_NETWORK = "NETWORK"
INVENTORY_SQL_ERROR_AUTHENTICATION = "AUTHENTICATION"
INVENTORY_SQL_ERROR_SCHEMA = "SCHEMA"
INVENTORY_SQL_ERROR_PROCESSING = "PROCESSING"


def classify_inventory_sql_error(exc: Exception) -> str:
    """Clasifica errores SQL del análisis de inventario para manejo seguro."""
    msg = str(exc or "").lower()
    if "dbprocess is dead" in msg or "not enabled" in msg:
        return INVENTORY_SQL_ERROR_DEAD_DBPROCESS
    if "adaptive server connection timed out" in msg or "login timeout" in msg:
        return INVENTORY_SQL_ERROR_CONNECTION_TIMEOUT
    if "timeout expired" in msg or "query timeout" in msg:
        return INVENTORY_SQL_ERROR_QUERY_TIMEOUT
    if "invalid column name" in msg or "invalid object name" in msg or "syntax" in msg:
        return INVENTORY_SQL_ERROR_SCHEMA
    if "login failed" in msg or "not associated with a trusted sql server connection" in msg:
        return INVENTORY_SQL_ERROR_AUTHENTICATION
    if "communication link failure" in msg or "connection was reset" in msg or "network" in msg:
        return INVENTORY_SQL_ERROR_NETWORK
    return INVENTORY_SQL_ERROR_PROCESSING


def is_inventory_transient_error(classification: str) -> bool:
    return classification in {
        INVENTORY_SQL_ERROR_CONNECTION_TIMEOUT,
        INVENTORY_SQL_ERROR_QUERY_TIMEOUT,
        INVENTORY_SQL_ERROR_DEAD_DBPROCESS,
        INVENTORY_SQL_ERROR_NETWORK,
    }


def should_retry_inventory_once(classification: str, attempt: int) -> bool:
    return attempt == 1 and is_inventory_transient_error(classification)


def inventory_analysis_safe_http_exception(exc: Exception) -> HTTPException:
    classification = classify_inventory_sql_error(exc)
    if is_inventory_transient_error(classification):
        return HTTPException(
            status_code=503,
            detail="Servicio SQL canónico temporalmente no disponible. Reintente en unos segundos.",
        )
    return HTTPException(
        status_code=500,
        detail="Error generando análisis canónico SoftRestaurant.",
    )
