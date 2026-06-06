import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

# Intentar pyodbc primero, luego pymssql como fallback
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except (ImportError, OSError):
    pyodbc = None
    PYODBC_AVAILABLE = False

try:
    import pymssql
    PYMSSQL_AVAILABLE = True
except ImportError:
    pymssql = None
    PYMSSQL_AVAILABLE = False

def get_sql_connection():
    """
    Conexión centralizada a SQL Server.
    Usa pyodbc si está disponible, sino pymssql como fallback.
    """
    server = os.getenv("EDARSAHUB_SQL_HOST")
    database = os.getenv("EDARSAHUB_SQL_DATABASE")
    user = os.getenv("EDARSAHUB_SQL_USER")
    password = os.getenv("EDARSAHUB_SQL_PASSWORD")
    port = int(os.getenv("EDARSAHUB_SQL_PORT", "1433"))

    if not all([server, database, user, password]):
        raise RuntimeError("Faltan variables SQL EDARSAHUB")

    # Intentar pyodbc primero
    if PYODBC_AVAILABLE:
        try:
            return pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server},{port};"
                f"DATABASE={database};"
                f"UID={user};"
                f"PWD={password};"
                "TrustServerCertificate=yes;"
                "Encrypt=no;"
            )
        except Exception:
            pass  # Fallback a pymssql

    # Fallback a pymssql
    if PYMSSQL_AVAILABLE:
        return pymssql.connect(
            server=server,
            port=port,
            user=user,
            password=password,
            database=database,
            as_dict=False
        )

    raise RuntimeError("Ni pyodbc ni pymssql disponibles en este entorno")

def fetch_all_dict(sql, params=None):
    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows

def fetch_one_dict(sql, params=None):
    rows = fetch_all_dict(sql, params)
    return rows[0] if rows else None
