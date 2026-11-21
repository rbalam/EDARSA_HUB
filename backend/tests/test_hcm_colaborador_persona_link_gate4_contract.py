from pathlib import Path

SQL = (
    Path(__file__).resolve().parents[1]
    / "database"
    / "migrations"
    / "20261106_hcm_colaborador_gobierno_persona_link.sql"
).read_text(encoding="utf-8")


def test_gate4_uses_canonical_gobierno_persona():
    assert "ADD PersonaID BIGINT NULL" in SQL
    assert (
        "REFERENCES dbo.Gobierno_Persona(PersonaID)"
        in SQL
    )
    assert (
        "IX_RH_Colaboradores_Expediente_PersonaID"
        in SQL
    )


def test_gate4_preserves_legacy_colaborador_identity():
    upper = SQL.upper()

    assert "DROP TABLE" not in upper
    assert "DROP COLUMN" not in upper
    assert "ALTER COLUMN COLABORADORID" not in upper
    assert "DROP CONSTRAINT" not in upper


def test_gate4_performs_no_backfill_or_data_mutation():
    upper = SQL.upper()

    forbidden = (
        "UPDATE DBO.RH_COLABORADORES_EXPEDIENTE",
        "INSERT INTO DBO.GOBIERNO_PERSONA",
        "INSERT INTO DBO.RH_COLABORADORES_EXPEDIENTE",
        "DELETE FROM DBO.RH_COLABORADORES_EXPEDIENTE",
        "MERGE DBO.RH_COLABORADORES_EXPEDIENTE",
    )

    for token in forbidden:
        assert token not in upper


def test_gate4_does_not_create_parallel_person_master():
    upper = SQL.upper()

    assert "CREATE TABLE DBO.RH_PERSONA" not in upper
    assert "CREATE TABLE DBO.RH_PERSONAS" not in upper
    assert "CREATE TABLE DBO.HCM_PERSONA" not in upper
    assert "CREATE TABLE DBO.HCM_PERSONAS" not in upper


def test_gate4_is_idempotent():
    upper = SQL.upper()

    assert "COL_LENGTH(" in upper
    assert "SYS.FOREIGN_KEYS" in upper
    assert "SYS.INDEXES" in upper


def test_gate4_is_transactional_and_reversible_on_error():
    upper = SQL.upper()

    assert "BEGIN TRANSACTION" in upper
    assert "COMMIT TRANSACTION" in upper
    assert "ROLLBACK TRANSACTION" in upper
    assert "SET XACT_ABORT ON" in upper


def test_gate4_requires_both_existing_canonical_objects():
    assert (
        "Falta dbo.RH_Colaboradores_Expediente."
        in SQL
    )
    assert (
        "Falta dbo.Gobierno_Persona BOS canonica."
        in SQL
    )
