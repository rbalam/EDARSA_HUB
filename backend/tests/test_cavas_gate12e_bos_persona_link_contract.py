from pathlib import Path

SQL = Path('backend/database/migrations/20260910_cavas_gate12e_bos_persona_link.sql').read_text(encoding='utf-8')

def test_gate12e_uses_single_bos_persona_link():
    assert 'ADD PersonaID BIGINT NULL' in SQL
    assert 'REFERENCES dbo.Gobierno_Persona(PersonaID)' in SQL
    assert 'IX_CavaSocios_Socios_PersonaID' in SQL

def test_gate12e_does_not_duplicate_client_identity():
    assert 'ADD ClienteID' not in SQL
    assert 'REFERENCES dbo.Cliente_Catalogo' not in SQL
    assert 'Entidad_Catalogo' not in SQL

def test_gate12e_is_non_destructive_and_no_backfill():
    upper = SQL.upper()
    assert 'DROP TABLE' not in upper
    assert 'DROP COLUMN' not in upper
    assert 'UPDATE DBO.CAVASOCIOS_SOCIOS' not in upper
    assert 'INSERT INTO DBO.CAVASOCIOS_SOCIOS' not in upper
    assert 'DELETE FROM DBO.CAVASOCIOS_SOCIOS' not in upper

def test_gate12e_preserves_operational_socio_model():
    assert 'SocioID' not in [line.strip() for line in SQL.splitlines() if line.strip().upper().startswith('ALTER COLUMN')]
