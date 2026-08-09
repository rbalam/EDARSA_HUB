from pathlib import Path


MIGRATION = Path(
    "database/migrations/20260808_003_economia_inegi_activation.sql"
)


def test_file_exists():
    assert MIGRATION.exists()


def test_activation_only():
    text=MIGRATION.read_text(
        encoding="utf-8"
    )

    assert "Economia_Proveedores" in text
    assert "Economia_Series" in text
    assert "Activo=1" in text


def test_no_values_insert():
    text=MIGRATION.read_text(
        encoding="utf-8"
    )

    assert "Economia_Valores" in text
    assert "INSERT" not in text


def test_transaction_guardrails():
    text=MIGRATION.read_text(
        encoding="utf-8"
    )

    assert "XACT_ABORT" in text
    assert "BEGIN TRANSACTION" in text
    assert "ROLLBACK TRANSACTION" in text
