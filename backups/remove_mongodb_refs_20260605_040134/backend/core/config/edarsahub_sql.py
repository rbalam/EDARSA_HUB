"""
EDARSA HUB - Helper de conexión SQL
===================================
Funciones de utilidad para conectar a EDARSAHUB SQL.
"""
import pymssql
from typing import List, Dict, Any, Optional
from .edarsahub_config import get_edarsahub_sql_config


def get_edarsahub_connection(timeout: int = 30):
    """
    Obtiene una conexión pymssql a EDARSAHUB SQL.
    
    Returns:
        pymssql.Connection
    """
    cfg = get_edarsahub_sql_config()
    return pymssql.connect(
        server=cfg.host,
        port=cfg.port,
        database=cfg.database,
        user=cfg.user,
        password=cfg.password,
        login_timeout=timeout,
        as_dict=True
    )


def execute_edarsahub_query(query: str, timeout: int = 30) -> List[Dict[str, Any]]:
    """
    Ejecuta una query en EDARSAHUB SQL y retorna resultados como lista de dicts.
    
    Args:
        query: SQL query a ejecutar
        timeout: Timeout en segundos
        
    Returns:
        Lista de diccionarios con los resultados
    """
    conn = get_edarsahub_connection(timeout=timeout)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        conn.close()


def get_edarsahub_sql_config_safe() -> dict:
    """Retorna config sin password para logging."""
    return get_edarsahub_sql_config().safe_dict()
