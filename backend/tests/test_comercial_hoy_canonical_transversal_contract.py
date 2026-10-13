from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "modules/comercial/routes.py"


def _text():
    return ROUTES.read_text(encoding="utf-8")


def test_dashboard_hoy_uses_current_operation_contract():
    text = _text()
    start = text.index("# HOY - CANONICO, ATOMICO Y TRANSVERSAL:")
    end = text.index("# FASE 3A.2: Migrado a helper centralizado", start)
    block = text[start:end]

    assert "_dashboard_current_operation_kpis(" in block
    assert "build_current_operation(" not in block
    assert "get_ventas_dia_abiertas(" not in block
    assert "OPERACION_EN_CURSO_CANONICA" in block


def test_current_operation_adapter_is_single_source():
    text = _text()
    start = text.index("def _dashboard_current_operation_item(")
    end = text.index("# FASE A-P0: GUARD RAIL", start)
    block = text[start:end]

    assert "build_current_operation(" in block
    assert "resolve_unidad_by_server_sucursal(" in block
    assert "_dashboard_unit_resolution_sucursal(" in block
    assert "get_ventas_dia_abiertas(" not in block


def test_ventas_tiempo_hoy_uses_same_contract():
    text = _text()
    start = text.index('@router.get("/comercial/ventas-tiempo/{server_id}")')
    end = text.index("# ENDPOINTS MIGRADOS FASE 5B-4E", start)
    block = text[start:end]

    assert "_dashboard_current_operation_kpis(" in block
    assert '"fuente_pax_hoy": fuente_pax_hoy' in block
    assert '"current_display_policy"' in block
    assert "SUM(ISNULL(ventas_abiertas, 0) + ISNULL(ventas_cerradas_dia, 0))" not in block


def test_daily_drilldown_uses_unit_operational_date():
    text = _text()
    start = text.index('@router.get("/comercial/detalle-ventas-agrupado/{server_id}")')
    end = text.index('@router.get("/comercial/ticket-venta/{server_id}")', start)
    block = text[start:end]

    assert "_dashboard_current_operation_item(" in block
    assert 'current_detail_item.get("fecha_operacion")' in block
    assert '"SOFT_PREVIOUS_DATE_AFTER_CUT_OPEN_ONLY"' in block
    assert '"MPRO_PREVIOUS_DATE_BEFORE_FIRST_TURN_OPEN_ONLY"' in block
    assert 'filtro_base += " AND 1 = 0"' in block
    assert "merge_open_snapshot_tickets(" in block
