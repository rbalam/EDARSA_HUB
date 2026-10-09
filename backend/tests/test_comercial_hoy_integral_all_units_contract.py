from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "modules/comercial/routes.py"


def test_hoy_uses_mexico_timezone_in_dashboard_and_drilldown():
    text = ROUTES.read_text(encoding="utf-8")
    assert "from zoneinfo import ZoneInfo" in text
    assert text.count('datetime.now(ZoneInfo("America/Mexico_City"))') >= 2


def test_hoy_prefers_canonical_ticket_summary_before_engine_branch():
    text = ROUTES.read_text(encoding="utf-8")
    dash = text.index("async def comercial_dashboard(")
    canonical = text.index("summarize_current_day_tickets(", dash)
    sr = text.index("if is_softrestaurant_system(server.get('system_type')):", canonical)
    mp = text.index("elif is_mpro_system(server.get('system_type')):", sr)
    assert dash < canonical < sr < mp
    block = text[canonical:sr]
    assert '"source_type": (' in block
    assert '"DETALLE_VENTAS_CANONICO"' in block
    assert '"ventas_periodo": ventas_hoy' in block
    assert '"cheques_total": cheques_hoy' in block
    assert '"pax_total": pax_hoy' in block


def test_daily_drilldown_keeps_open_snapshot_merge_for_all_engines():
    text = ROUTES.read_text(encoding="utf-8")
    start = text.index("async def comercial_detalle_ventas_agrupado(")
    end = text.index('@router.get("/comercial/ticket-venta/{server_id}")', start)
    block = text[start:end]
    assert 'if periodo == "dia":' in block
    assert 'merge_open_snapshot_tickets(' in block
    assert 'fecha_ini_dt = hoy_inicio' in block
