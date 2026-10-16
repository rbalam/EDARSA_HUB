from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL = ROOT / "backend" / "database" / "migrations" / "20261015_integrations_api_factory.sql"
WRAPPER = ROOT / "backend" / "migrations" / "integrations_api_factory_20261015.py"


def test_h8_uses_canonical_sql_migration_root():
    assert SQL.is_file()
    assert "backend/database/migrations" in SQL.as_posix()


def test_h8_migration_is_idempotent_for_all_six_tables():
    text = SQL.read_text(encoding="utf-8")
    tables = (
        "Sistema_ApiFactoryApi",
        "Sistema_ApiFactoryVersion",
        "Sistema_ApiFactoryConsumer",
        "Sistema_ApiFactoryConsumerGrant",
        "Sistema_ApiFactoryConsumerEmpresa",
        "Sistema_ApiFactoryConsumerUnidad",
    )
    for table in tables:
        assert f"IF OBJECT_ID('dbo.{table}', 'U') IS NULL" in text
        assert f"CREATE TABLE dbo.{table}" in text


def test_legacy_wrapper_reuses_canonical_migration_without_ddl_copy():
    text = WRAPPER.read_text(encoding="utf-8")
    assert '"20261015_integrations_api_factory.sql"' in text
    assert 'read_text(encoding="utf-8")' in text
    assert "CREATE TABLE dbo.Sistema_ApiFactoryApi" not in text
