from contextlib import contextmanager
from core.config.edarsahub_config import get_edarsahub_sql_config


def get_sql_connection(profile: str = "default"):
    cfg = get_edarsahub_sql_config(profile)

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
def sql_connection(profile: str = "default"):
    conn = get_sql_connection(profile)
    try:
        yield conn
    finally:
        conn.close()


def _rows_to_dicts(cur):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def fetch_all_dict(sql: str, params=None, profile: str = "default"):
    params = params or []
    with sql_connection(profile) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return _rows_to_dicts(cur)


def fetch_one_dict(sql: str, params=None, profile: str = "default"):
    rows = fetch_all_dict(sql, params, profile=profile)
    return rows[0] if rows else None


def execute_sql(sql: str, params=None, profile: str = "default"):
    params = params or []
    with sql_connection(profile) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.rowcount
