from __future__ import annotations

import os
from dataclasses import dataclass

from core.config.edarsahub_config import (
    EdarsaHubSQLConfig,
    get_edarsahub_sql_config,
)
from core.sql_first.connection_factory import (
    get_edarsahub_pymssql_connection,
)


EXPECTED_DATABASE = "EDARSAHUB"

# Identidades exclusivamente read-only y, por tanto,
# invalidas dentro del contrato de escritura.
PROHIBITED_WRITER_IDENTITIES = frozenset(
    {
        "hrlectura",
        "gptlectura",
        "gptread",
    }
)


@dataclass(frozen=True)
class SQLWriterIdentity:
    database_name: str
    login_name: str
    user_name: str


def _normalized(value) -> str:
    return str(value or "").strip()


def _required_writer_db_user() -> str:
    value = os.getenv(
        "EDARSAHUB_SQL_WRITER_DB_USER"
    )
    if not value:
        raise RuntimeError(
            "Variable obligatoria no configurada: "
            "EDARSAHUB_SQL_WRITER_DB_USER"
        )
    return value.strip()


def validate_writer_config(
    *,
    config: EdarsaHubSQLConfig | None = None,
    expected_db_user: str | None = None,
) -> tuple[EdarsaHubSQLConfig, str]:
    cfg = config or get_edarsahub_sql_config(
        "writer"
    )

    if cfg.profile != "writer":
        raise RuntimeError(
            "La conexion no usa el perfil writer."
        )

    if cfg.database.casefold() != (
        EXPECTED_DATABASE.casefold()
    ):
        raise RuntimeError(
            "El perfil writer debe apuntar a "
            "EDARSAHUB."
        )

    db_user_source = (
        expected_db_user
        if expected_db_user is not None
        else _required_writer_db_user()
    )
    db_user = db_user_source.strip()

    if not db_user:
        raise RuntimeError(
            "EDARSAHUB_SQL_WRITER_DB_USER "
            "no puede estar vacio."
        )

    configured_identities = {
        cfg.user.casefold(),
        db_user.casefold(),
    }

    prohibited = (
        configured_identities
        & PROHIBITED_WRITER_IDENTITIES
    )

    if prohibited:
        raise RuntimeError(
            "Identidad SQL prohibida para escritura: "
            + ", ".join(sorted(prohibited))
        )

    return cfg, db_user


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
    expected_db_user: str | None = None,
) -> SQLWriterIdentity:
    cfg, db_user = validate_writer_config(
        config=config,
        expected_db_user=expected_db_user,
    )

    identity = _read_identity(conn)

    expected = {
        "database_name": EXPECTED_DATABASE,
        "login_name": cfg.user,
        "user_name": db_user,
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
            "Identidad SQL writer invalida: "
            + details
        )

    return identity


def open_validated_writer_connection():
    # Validar configuracion e identidad declarada antes
    # de intentar abrir una conexion.
    cfg, db_user = validate_writer_config()

    conn = get_edarsahub_pymssql_connection(
        profile="writer"
    )

    try:
        identity = validate_writer_identity(
            conn,
            config=cfg,
            expected_db_user=db_user,
        )
    except Exception:
        conn.close()
        raise

    return conn, identity
