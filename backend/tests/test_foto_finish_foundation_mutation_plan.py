from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOSSIER = ROOT / "docs" / "modules" / "production_quality" / "FOTO_FINISH_FOUNDATION_MUTATION_PLAN_V1.md"

def test_foto_finish_foundation_plan_exists():
    assert DOSSIER.is_file()

def test_foto_finish_foundation_plan_required_sections():
    text = DOSSIER.read_text(encoding="utf-8")
    for n in range(1, 24):
        assert f"# {n:02d}." in text

def test_foto_finish_foundation_plan_architecture_guards():
    text = DOSSIER.read_text(encoding="utf-8")
    assert "SQL Server EDARSAHUB" in text
    assert "NO crear segundo KDS" in text
    assert "NO crea segundo catálogo de productos" in text
    assert "GATE5A_SQL_PHYSICAL_ANTI_DUPLICATION_READONLY" in text
    assert "GATE5B_FOUNDATION_MUTATION" in text

def test_foto_finish_foundation_plan_blocks_direct_foundation_sql():
    text = DOSSIER.read_text(encoding="utf-8")
    assert "SQL metadata audit" in text
    assert "SQL_MUTATION=NO" in text
    assert "collisions=0" in text
    assert "blockers=0" in text
