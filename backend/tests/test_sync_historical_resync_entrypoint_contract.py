from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "frontend" / "src" / "components" / "admin" / "ResyncPanel.jsx"


def test_resync_exposes_historical_sync_entrypoint_without_replacing_manual_resync():
    text = PANEL.read_text(encoding="utf-8")
    assert "Re-sincronización Manual" in text
    assert "Sincronización Histórica" in text
    assert "navigate('/sync-historical')" in text
    assert 'data-testid="open-sync-historical-from-resync"' in text


def test_historical_entrypoint_change_does_not_reference_protected_open_sales_job():
    text = PANEL.read_text(encoding="utf-8")
    assert "sync_comercial_abiertas_v2" not in text
