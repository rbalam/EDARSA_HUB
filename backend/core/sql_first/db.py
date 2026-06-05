import os

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    pyodbc = None
    PYODBC_AVAILABLE = False

def get_sql_connection():
    if not PYODBC_AVAILABLE:
        raise RuntimeError("pyodbc no disponible en este entorno")
    
    server = os.getenv("EDARSAHUB_SQL_HOST")
    database = os.getenv("EDARSAHUB_SQL_DATABASE")
    user = os.getenv("EDARSAHUB_SQL_USER")
    password = os.getenv("EDARSAHUB_SQL_PASSWORD")
    port = os.getenv("EDARSAHUB_SQL_PORT", "1433")

    if not all([server, database, user, password]):
        raise RuntimeError("Faltan variables SQL EDARSAHUB")

    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
    )

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
