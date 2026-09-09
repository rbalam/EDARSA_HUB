from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_catalogo_repository_uses_pymssql_placeholders():
    s=(ROOT/'backend/modules/catalogo_ampliado/repository.py').read_text(encoding='utf-8')
    assert '?' not in s
    assert '%s' in s
