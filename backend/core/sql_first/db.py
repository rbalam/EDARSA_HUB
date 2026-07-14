from contextlib import contextmanager
from core.sql_first.connection_factory import get_edarsahub_connection


def get_sql_connection(profile: str = "default"):
    """
    Fachada compatible para consumidores SQL-first existentes.
    La apertura fisica pertenece a connection_factory.
    """
    return get_edarsahub_connection(profile)


@contextmanager
def sql_connection(profile: str = "default"):
    conn = get_sql_connection(profile)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def readonly_sql_connection(profile: str = "default"):
    """
    Conexión read-only fail-closed con identidad SQL validada.

    El único perfil permitido es ``default`` y debe resolver exactamente a
    EDARSAHUB / HRLectura / HRLectura.
    """
    if profile != "default":
        raise ValueError(
            "Solo se permite el perfil read-only default"
        )

    from core.connections.edarsahub_readonly_repository import (
        validate_readonly_identity,
    )
    from core.connections.hrlectura_connection_factory import (
        build_hrlectura_connection_factory,
    )

    connection_factory = (
        build_hrlectura_connection_factory()
    )
    conn = connection_factory()

    try:
        validate_readonly_identity(conn)
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


def fetch_all_dict_readonly(
    sql: str,
    params=None,
    profile: str = "default",
):
    params = params or []

    with readonly_sql_connection(profile) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return _rows_to_dicts(cur)


def fetch_one_dict_readonly(
    sql: str,
    params=None,
    profile: str = "default",
):
    rows = fetch_all_dict_readonly(
        sql,
        params,
        profile=profile,
    )
    return rows[0] if rows else None


def execute_sql(sql: str, params=None, profile: str = "default"):
    params = params or []
    with sql_connection(profile) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.rowcount
