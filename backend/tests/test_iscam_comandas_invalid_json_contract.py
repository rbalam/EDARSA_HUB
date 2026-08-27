from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISCAM = ROOT / "backend/modules/inteligencia_comercial/iscam_routes.py"

def test_openjson_items_is_guarded_by_isjson():
    text = ISCAM.read_text(encoding="utf-8")
    assert "ISJSON(s.items) = 1" in text
    assert "ELSE N'[]'" in text
    assert "OPENJSON(s.items) WITH (" not in text
