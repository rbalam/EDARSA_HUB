from pathlib import Path


ROUTES = (
    Path(__file__).resolve().parents[1]
    / "modules"
    / "comercial"
    / "routes.py"
)


def _day_block() -> str:
    text = ROUTES.read_text(encoding="utf-8")
    start = text.index('        elif periodo == "dia":')
    end = text.index('        elif periodo == "semana":', start)
    return text[start:end]


def test_comercial_hoy_uses_canonical_operational_date():
    block = _day_block()

    assert "resolve_unidad_by_server_sucursal(" in block
    assert "get_operational_window(" in block
    assert "ventana_operativa.fecha_operacion" in block
    assert "fecha_ini = fecha_operacion_dia.strftime" in block
    assert "fecha_fin = fecha_ini" in block


def test_comercial_hoy_does_not_use_calendar_date_directly():
    block = _day_block()

    assert "fecha_ini = hoy.strftime" not in block
    assert "fecha_fin = hoy.strftime" not in block


def test_comercial_hoy_comparisons_follow_operational_date():
    block = _day_block()

    assert "fecha_operacion_dia - timedelta(days=1)" in block
    assert "fecha_operacion_dia.replace(" in block



def test_softrestaurant_visible_unit_code_is_not_used_as_sucursal_origen_id():
    text = ROUTES.read_text(encoding="utf-8")
    helper_start = text.index("def _dashboard_unit_resolution_sucursal(")
    helper_end = text.index("\n# =", helper_start)
    helper = text[helper_start:helper_end]

    assert 'if is_softrestaurant_system(server.get("system_type")):' in helper
    assert "return None" in helper

    block = _day_block()
    assert "_dashboard_unit_resolution_sucursal(" in block


def test_softrestaurant_snapshot_resolution_uses_same_canonical_scope():
    text = ROUTES.read_text(encoding="utf-8")
    start = text.index("# HOY - SOFTRESTAURANT:")
    end = text.index("# FASE 3A.2: Migrado a helper centralizado", start)
    block = text[start:end]

    assert "sucursal_resolver = _dashboard_unit_resolution_sucursal(" in block
    assert "resolve_unidad_by_server_sucursal(" in block
