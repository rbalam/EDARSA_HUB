from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
C=ROOT/"frontend/src/components/admin/ComercialRangeResyncCard.jsx"
P=ROOT/"frontend/src/components/admin/ResyncPanel.jsx"

def test_range_ui():
    t=C.read_text(encoding="utf-8")
    assert "Re-sincronización Comercial por rango" in t
    assert "Seleccionar todas" in t
    assert "Fecha inicio" in t and "Fecha fin" in t
    assert "percent_complete" in t
    assert "current_block" in t and "current_unit" in t
    assert "Actualiza existentes" in t
    assert "/admin/scheduler/resync/comercial-range/jobs" in t
    assert "/admin/scheduler/resync/comercial-range/active" in t

def test_integrated():
    t=P.read_text(encoding="utf-8")
    assert "ComercialRangeResyncCard" in t
    assert "<ComercialRangeResyncCard" in t
