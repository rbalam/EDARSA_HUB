"""
Compatibilidad legacy para módulos antiguos.

NO abrir conexiones aquí directamente.
Toda conexión EDARSAHUB debe pasar por core.sql_first.db.
"""

from core.sql_first.db import (
    get_sql_connection,
    sql_connection,
    fetch_all_dict,
    fetch_one_dict,
    execute_sql,
)

def get_connection():
    return get_sql_connection()

def get_db_connection():
    return get_sql_connection()

def get_conn():
    return get_sql_connection()
