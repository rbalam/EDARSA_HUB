from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Helper de conexión SQL
===================================
Funciones de utilidad para conectar a EDARSAHUB SQL.
"""
import pymssql
from typing import List, Dict, Any, Optional
from .edarsahub_config import get_edarsahub_sql_config
from core.sql_first.db import get_sql_connection


def get_edarsahub_connection(timeout: int = 30):
    """
    Obtiene una conexión pymssql a EDARSAHUB SQL.
    
    Returns:
        pymssql.Connection
    """
    cfg = get_edarsahub_sql_config()
    return get_sql_connection()


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
