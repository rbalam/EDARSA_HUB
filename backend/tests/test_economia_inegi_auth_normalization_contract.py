from pathlib import Path


MIGRATION = Path(
    "database/migrations/20260808_002_economia_inegi_public_xml_auth.sql"
)


def test_migration_exists():
    assert MIGRATION.exists()


def test_normalizes_public_xml_auth():
    text = MIGRATION.read_text(
        encoding="utf-8"
    )

    assert "INEGI" in text
    assert "RequiereAutenticacion = 0" in text
    assert "FechaModificacionUTC" in text


def test_does_not_activate_provider():
    text = MIGRATION.read_text(
        encoding="utf-8"
    )

    assert "Activo = 1" not in text


def test_does_not_touch_series_values():
    text = MIGRATION.read_text(
        encoding="utf-8"
    )

    assert "Economia_Series" not in text
    assert "Economia_Valores" not in text


def test_has_transaction_guardrails():
    text = MIGRATION.read_text(
        encoding="utf-8"
    )

    assert "XACT_ABORT" in text
    assert "BEGIN TRANSACTION" in text
    assert "ROLLBACK TRANSACTION" in text
