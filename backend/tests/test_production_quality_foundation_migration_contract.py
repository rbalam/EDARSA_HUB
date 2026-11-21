from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MIG = ROOT / (
    "backend/database/migrations/"
    "20260924_001_production_quality_foundation.sql"
)

ROLLBACK = ROOT / (
    "backend/database/migrations/"
    "20260924_001_production_quality_foundation_rollback.sql"
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_foundation_files_exist():
    assert MIG.is_file()
    assert ROLLBACK.is_file()


def test_foundation_tables_are_exactly_declared():
    sql = text(MIG)

    expected = (
        "Production_Item",
        "Production_Station",
        "Production_QualityStandard",
        "Production_QualityStandardVersion",
        "Production_Measurement",
        "Production_Evidence",
        "Production_QualityDecision",
        "Production_QualityAction",
        "Production_Device",
        "Production_DeviceCalibration",
    )

    for name in expected:
        assert f"dbo.{name}" in sql

    assert "Production_Rework" not in sql
    assert "Production_QualityOverride" not in sql


def test_migration_is_transactional_and_idempotent():
    sql = text(MIG).upper()

    assert "SET XACT_ABORT ON" in sql
    assert "BEGIN TRANSACTION" in sql
    assert "COMMIT TRANSACTION" in sql
    assert "ROLLBACK TRANSACTION" in sql

    for name in (
        "PRODUCTION_ITEM",
        "PRODUCTION_STATION",
        "PRODUCTION_QUALITYSTANDARD",
        "PRODUCTION_QUALITYSTANDARDVERSION",
        "PRODUCTION_MEASUREMENT",
        "PRODUCTION_EVIDENCE",
        "PRODUCTION_QUALITYDECISION",
        "PRODUCTION_QUALITYACTION",
        "PRODUCTION_DEVICE",
        "PRODUCTION_DEVICECALIBRATION",
    ):
        token = f"OBJECT_ID('DBO.{name}', 'U') IS NULL"
        assert token in sql


def test_tenant_scope_and_operational_date_contract():
    sql = text(MIG)

    assert "EmpresaID int NOT NULL" in sql
    assert "UnidadNegocioID uniqueidentifier NOT NULL" in sql

    for table in (
        "Production_Item",
        "Production_Measurement",
        "Production_Evidence",
    ):
        block = sql.split(
            f"CREATE TABLE dbo.{table}",
            1,
        )[1].split(");", 1)[0]

        assert "FechaOperacion date NOT NULL" in block


def test_canonical_fk_contracts_are_reused():
    sql = text(MIG)

    assert "REFERENCES dbo.Sistema_Empresas(EmpresaID)" in sql
    assert "REFERENCES dbo.Unidades_Negocio(id)" in sql
    assert "REFERENCES dbo.Usuario_Catalogo(UsuarioID)" in sql


def test_idempotency_contracts_exist():
    sql = text(MIG)

    for token in (
        "UQ_Production_Item_Source",
        "UQ_Production_Measurement_Idempotency",
        "UQ_Production_Evidence_Idempotency",
        "UQ_Production_QD_Idempotency",
        "UQ_Production_QA_Idempotency",
    ):
        assert token in sql


def test_evidence_is_metadata_only():
    sql = text(MIG).lower()

    assert "storagepath nvarchar(500)" in sql
    assert "contenthash varchar(128)" in sql

    forbidden = (
        "varbinary(max)",
        "image ",
        "base64",
    )

    for token in forbidden:
        assert token not in sql


def test_devices_do_not_persist_secrets():
    sql = text(MIG).lower()

    forbidden = (
        "password",
        "secret",
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "connectionstring",
    )

    for token in forbidden:
        assert token not in sql


def test_no_mongo_or_live_dependency():
    sql = text(MIG).lower()

    assert "mongodb://" not in sql
    assert "mongodb+srv://" not in sql
    assert "pymongo" not in sql
    assert "edarsahub_produccion" not in sql


def test_quality_actions_cover_rework_and_override():
    sql = text(MIG)

    assert "'REWORK'" in sql
    assert "'OVERRIDE'" in sql
    assert "Production_QualityAction" in sql


def test_rollback_reverse_dependency_order():
    sql = text(ROLLBACK)

    drops = (
        "DROP TABLE dbo.Production_DeviceCalibration;",
        "DROP TABLE dbo.Production_QualityAction;",
        "DROP TABLE dbo.Production_QualityDecision;",
        "DROP TABLE dbo.Production_Evidence;",
        "DROP TABLE dbo.Production_Measurement;",
        "DROP TABLE dbo.Production_Device;",
        "DROP TABLE dbo.Production_QualityStandardVersion;",
        "DROP TABLE dbo.Production_QualityStandard;",
        "DROP TABLE dbo.Production_Item;",
        "DROP TABLE dbo.Production_Station;",
    )

    positions = [sql.index(statement) for statement in drops]

    assert positions == sorted(positions)


def test_gate5d1_has_no_runtime_sql_execution_contract():
    artifacts = (
        text(MIG)
        + "\n"
        + text(ROLLBACK)
    ).lower()

    forbidden = (
        "pymssql" + ".connect",
        "pyodbc" + ".connect",
        "sqlalchemy" + ".create_engine",
    )

    for token in forbidden:
        assert token not in artifacts
