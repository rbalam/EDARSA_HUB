from __future__ import annotations

from dataclasses import dataclass

from core.config.edarsahub_config import (
    EdarsaHubSQLConfig,
    get_edarsahub_sql_config,
)
from core.sql_first.connection_factory import (
    get_edarsahub_pymssql_connection,
)


CANONICAL_PROFILE = "default"
EXPECTED_DATABASE = "EDARSAHUB"
EXPECTED_LOGIN = "HRLectura"
EXPECTED_USER = "HRLectura"


@dataclass(frozen=True)
class SQLWriterIdentity:
    database_name: str
    login_name: str
    user_name: str


def _normalized(value) -> str:
    return str(value or "").strip()


def validate_writer_config(
    *,
    config: EdarsaHubSQLConfig | None = None,
) -> EdarsaHubSQLConfig:
    """
    Valida la configuracion canonica antes de abrir SQL.

    HRLectura es la identidad canonica confirmada para
    EDARSAHUB y dispone de los permisos requeridos.
    No se admiten perfiles o credenciales paralelas.
    """
    cfg = config or get_edarsahub_sql_config(
        CANONICAL_PROFILE
    )

    if cfg.profile != CANONICAL_PROFILE:
        raise RuntimeError(
            "La conexion debe usar el perfil canonico "
            "default."
        )

    if cfg.database.casefold() != (
        EXPECTED_DATABASE.casefold()
    ):
        raise RuntimeError(
            "La conexion canonica debe apuntar a "
            "EDARSAHUB."
        )

    if cfg.user.casefold() != (
        EXPECTED_LOGIN.casefold()
    ):
        raise RuntimeError(
            "El login canonico debe ser HRLectura."
        )

    return cfg


def _read_identity(conn) -> SQLWriterIdentity:
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                DB_NAME(),
                SUSER_SNAME(),
                USER_NAME()
            """
        )
        row = cur.fetchone()
    finally:
        close = getattr(cur, "close", None)
        if close:
            close()

    if not row or len(row) < 3:
        raise RuntimeError(
            "No fue posible resolver la identidad SQL."
        )

    return SQLWriterIdentity(
        database_name=_normalized(row[0]),
        login_name=_normalized(row[1]),
        user_name=_normalized(row[2]),
    )


def validate_writer_identity(
    conn,
    *,
    config: EdarsaHubSQLConfig | None = None,
) -> SQLWriterIdentity:
    cfg = validate_writer_config(
        config=config
    )
    identity = _read_identity(conn)

    expected = {
        "database_name": EXPECTED_DATABASE,
        "login_name": cfg.user,
        "user_name": EXPECTED_USER,
    }
    actual = {
        "database_name": identity.database_name,
        "login_name": identity.login_name,
        "user_name": identity.user_name,
    }

    mismatches = [
        key
        for key, expected_value in expected.items()
        if actual[key].casefold()
        != expected_value.casefold()
    ]

    if mismatches:
        details = ", ".join(
            (
                f"{key}: esperado={expected[key]!r}, "
                f"actual={actual[key]!r}"
            )
            for key in mismatches
        )
        raise RuntimeError(
            "Identidad SQL canonica invalida: "
            + details
        )

    return identity


def open_validated_writer_connection():
    """
    Abre la conexion EDARSAHUB canonica mediante pymssql.

    El uso explicito de pymssql conserva el contrato de
    parametros ``%s`` del reset transaccional.
    """
    cfg = validate_writer_config()

    conn = get_edarsahub_pymssql_connection(
        profile=CANONICAL_PROFILE
    )

    try:
        identity = validate_writer_identity(
            conn,
            config=cfg,
        )
    except Exception:
        conn.close()
        raise

    return conn, identity
