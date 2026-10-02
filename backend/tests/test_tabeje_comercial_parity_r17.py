from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DRILL = ROOT / "frontend/src/components/comercial/KpiDrilldownDialog.jsx"
REPOSITORY = ROOT / "backend/modules/comercial_analytics/repository_tickets.py"
COMERCIAL = ROOT / "frontend/src/pages/Comercial.js"
SYNC_OPEN = ROOT / "backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py"


def test_executive_does_not_cross_to_server_rbac_routes():
    text = DRILL.read_text(encoding="utf-8")
    assert "/comercial/detalle-ventas-agrupado/" not in text
    assert "/comercial/ticket-venta/" not in text
    assert "/v2/comercial/analytics/tickets" in text


def test_analytics_reuses_certified_comercial_services():
    text = REPOSITORY.read_text(encoding="utf-8")
    assert "merge_open_snapshot_tickets" in text
    assert "build_ticket_venta" in text
    assert "TABLERO_COMERCIAL_VENTAS_DIA_CERTIFIED_PATH" in text
    assert '"rbac": "UNIDAD_NEGOCIO"' in text


def test_day_view_keeps_comercial_interaction_contract():
    text = DRILL.read_text(encoding="utf-8")
    assert "Selecciona un folio para abrir el ticket de venta." in text
    assert "modoVentasDia && item.ticket_pk" in text
    assert "totalsFor(rows)" in text


def test_protected_comercial_and_open_sync_contract_remain_present():
    comercial = COMERCIAL.read_text(encoding="utf-8")
    sync_open = SYNC_OPEN.read_text(encoding="utf-8")
    assert "MÓDULO BLINDADO - NO MODIFICAR" in comercial
    assert "/comercial/detalle-ventas-agrupado/" in comercial
    assert "sync_comercial_abiertas_v2" in sync_open
