#!/usr/bin/env python3
"""Compatibility wrapper for H8 API Factory persistence.

The canonical DDL lives in:
backend/database/migrations/20261015_integrations_api_factory.sql

This wrapper exists only for legacy/manual invocation paths and deliberately
does not duplicate the migration SQL.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path("/app/backend")
sys.path.insert(0, str(BACKEND_DIR))

from core.sql_first.db import get_sql_connection


MIGRATION_FILE = (
    BACKEND_DIR
    / "database"
    / "migrations"
    / "20261015_integrations_api_factory.sql"
)

VERIFY = r"""
SELECT
    OBJECT_ID('dbo.Sistema_ApiFactoryApi','U') AS api,
    OBJECT_ID('dbo.Sistema_ApiFactoryVersion','U') AS version,
    OBJECT_ID('dbo.Sistema_ApiFactoryConsumer','U') AS consumer,
    OBJECT_ID('dbo.Sistema_ApiFactoryConsumerGrant','U') AS consumer_grant,
    OBJECT_ID('dbo.Sistema_ApiFactoryConsumerEmpresa','U') AS consumer_empresa,
    OBJECT_ID('dbo.Sistema_ApiFactoryConsumerUnidad','U') AS consumer_unidad
"""


def main() -> None:
    if not MIGRATION_FILE.is_file():
        raise SystemExit("ERROR: migracion canonica API Factory no encontrada")

    ddl = MIGRATION_FILE.read_text(encoding="utf-8")

    conn = get_sql_connection()
    try:
        cur = conn.cursor()
        cur.execute(ddl)
        conn.commit()

        verify = conn.cursor()
        verify.execute(VERIFY)
        row = verify.fetchone()
        if not row or not all(row):
            raise SystemExit("ERROR: persistencia API Factory incompleta")

        print("OK: persistencia canonica API Factory lista.")
        print("PRODUCTION_TOUCHED=NO")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
