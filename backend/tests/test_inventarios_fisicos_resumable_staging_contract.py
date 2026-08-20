from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MIGRATION = (
    ROOT
    / "backend"
    / "database"
    / "migrations"
    / "20260817_030_inventarios_fisicos_resumable_staging.sql"
)

ROLLBACK = (
    ROOT
    / "backend"
    / "database"
    / "rollback"
    / "20260817_030_inventarios_fisicos_resumable_staging_rollback.sql"
)

VALIDATION = (
    ROOT
    / "backend"
    / "database"
    / "validation"
    / "20260817_030_inventarios_fisicos_resumable_staging_validation.sql"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_migration_creates_run_and_staging_tables():
    sql = read(MIGRATION)

    assert "Compras_Inventarios_Fisicos_SyncRuns" in sql
    assert "Compras_Inventarios_Fisicos_Stage" in sql
    assert "Compras_Inventarios_Fisicos_Detalle_Stage" in sql
    assert "run_id" in sql
    assert "unidad_negocio_id" in sql
    assert "server_id" in sql


def test_run_status_is_fail_closed():
    sql = read(MIGRATION)

    for status in (
        "STAGING",
        "VALIDATED",
        "ACTIVATING",
        "ACTIVE",
        "FAILED",
        "ABANDONED",
    ):
        assert status in sql


def test_header_staging_key_is_run_and_unit_scoped():
    sql = read(MIGRATION)

    assert """
                    run_id,
                    server_id,
                    unidad_negocio_id,
                    folio
""" in sql


def test_detail_staging_key_is_run_and_unit_scoped():
    sql = read(MIGRATION)

    assert """
                    run_id,
                    server_id,
                    unidad_negocio_id,
                    folio,
                    almacen_id,
                    codigo_producto
""" in sql


def test_migration_is_transactional():
    sql = read(MIGRATION)

    assert "SET XACT_ABORT ON" in sql
    assert "BEGIN TRANSACTION" in sql
    assert "COMMIT TRANSACTION" in sql
    assert "ROLLBACK TRANSACTION" in sql


def test_rollback_only_removes_new_objects():
    sql = read(ROLLBACK)

    assert (
        "DROP TABLE "
        "dbo.Compras_Inventarios_Fisicos_Detalle_Stage"
    ) in sql

    assert (
        "DROP TABLE "
        "dbo.Compras_Inventarios_Fisicos_Stage"
    ) in sql

    assert (
        "DROP TABLE "
        "dbo.Compras_Inventarios_Fisicos_SyncRuns"
    ) in sql

    assert (
        "DROP TABLE dbo.Compras_Inventarios_Fisicos_Sync;"
        not in sql
    )

    assert (
        "DROP TABLE "
        "dbo.Compras_Inventarios_Fisicos_Detalle_Sync;"
        not in sql
    )


def test_validation_requires_new_objects():
    sql = read(VALIDATION)

    assert "INVENTARIOS_RESUMABLE_STAGING_SCHEMA_OK=1" in sql
    assert "SYNC_RUNS_TABLE_MISSING" in sql
    assert "HEADER_STAGE_TABLE_MISSING" in sql
    assert "DETAIL_STAGE_TABLE_MISSING" in sql
