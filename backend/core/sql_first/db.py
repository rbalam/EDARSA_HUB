from contextlib import contextmanager
from core.config.edarsahub_config import get_edarsahub_sql_config

def get_sql_connection():
    cfg = get_edarsahub_sql_config()

    try:
        import pyodbc
        return pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={cfg.host},{cfg.port};"
            f"DATABASE={cfg.database};"
            f"UID={cfg.user};"
            f"PWD={cfg.password};"
            "TrustServerCertificate=yes;Encrypt=no;"
        )
    except Exception:
        import pymssql
        return pymssql.connect(
            server=cfg.host,
            port=cfg.port,
            user=cfg.user,
            password=cfg.password,
            database=cfg.database,
            login_timeout=10,
            timeout=30,
            tds_version="7.0",
        )

@contextmanager
def sql_connection():
    conn = get_sql_connection()
    try:
        yield conn
    finally:
        conn.close()

def fetch_all_dict(sql: str, params=None):
    params = params or []
    with sql_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

def fetch_one_dict(sql: str, params=None):
    rows = fetch_all_dict(sql, params)
    return rows[0] if rows else None

def execute_sql(sql: str, params=None):
    params = params or []
    with sql_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.rowcount
