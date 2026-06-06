"""
Factory centralizada de conexiones SQL EDARSAHUB.

Reglas:
- EDARSAHUB SQL: get_edarsahub_connection()
- Servidores externos: get_external_sql_connection(config)
- No imprimir secretos.
"""

from core.sql_first.db import get_sql_connection

def get_edarsahub_connection():
    return get_sql_connection()

def get_external_sql_connection(config: dict):
    if not config:
        raise ValueError("Config de servidor externo requerida")

    host = config.get("host") or config.get("server") or config.get("servidor")
    port = int(config.get("port") or config.get("puerto") or 1433)
    database = config.get("database_name") or config.get("database") or config.get("base_datos") or config.get("bd")
    username = config.get("username") or config.get("usuario") or config.get("user")
    password = config.get("password") or config.get("pwd")

    if not host or not database or not username or not password:
        raise ValueError("Config externa incompleta: host/database/username/password requeridos")

    try:
        import pymssql
        return pymssql.connect(
            server=host,
            port=port,
            user=username,
            password=password,
            database=database,
            login_timeout=10,
            timeout=30,
            tds_version="7.0",
        )
    except Exception:
        import pyodbc
        return pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "TrustServerCertificate=yes;Encrypt=no;"
        )
