from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "modules/comercial/ticket_service.py"
ROUTES = ROOT / "modules/comercial/routes.py"


def test_open_snapshot_is_resolved_by_canonical_unit_not_ui_sucursal():
    text = SERVICE.read_text(encoding="utf-8")
    start = text.index("def load_open_snapshot_lines(")
    end = text.index("def merge_open_snapshot_tickets(", start)
    block = text[start:end]

    assert "unidad_negocio_id" in block
    assert "fecha_operacion" in block
    assert "ORDER BY snapshot_timestamp DESC" in block
    assert "CONVERT(varchar(100), sucursal_id)" not in block
    assert "sucursal.upper()" not in block


def test_daily_drilldown_and_ticket_use_same_open_snapshot_loader():
    service = SERVICE.read_text(encoding="utf-8")
    routes = ROUTES.read_text(encoding="utf-8")

    assert "load_open_snapshot_lines(" in service
    assert "merge_open_snapshot_tickets(" in service
    assert "merge_open_snapshot_tickets(" in routes
    assert "build_ticket_venta(" in service
