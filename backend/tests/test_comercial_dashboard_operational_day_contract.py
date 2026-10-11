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
    start = text.index("# HOY - CANONICO, ATOMICO Y TRANSVERSAL:")
    end = text.index("# FASE 3A.2: Migrado a helper centralizado", start)
    block = text[start:end]

    assert "sucursal_resolver = _dashboard_unit_resolution_sucursal(" in block
    assert "resolve_unidad_by_server_sucursal(" in block


def test_hoy_snapshot_is_transversal_for_all_supported_systems():
    text = ROUTES.read_text(encoding="utf-8")
    start = text.index("# HOY - CANONICO, ATOMICO Y TRANSVERSAL:")
    end = text.index("# FASE 3A.2: Migrado a helper centralizado", start)
    block = text[start:end]

    assert 'if periodo == "dia" and is_supported_system_type(' in block
    assert "get_ventas_dia_abiertas(" in block
    assert "Comercial_Ventas_Dia_Abiertas_v2" in block
    assert "SOLO a SoftRestaurant" not in block
    assert "get_dashboard_kpis_from_edarsahub(" not in block


def test_mpro_visible_unit_alias_is_resolved_dynamically_not_hardcoded():
    text = ROUTES.read_text(encoding="utf-8")
    helper_start = text.index("def _dashboard_unit_resolution_sucursal(")
    helper_end = text.index("\n# =", helper_start)
    helper = text[helper_start:helper_end]

    assert "UnidadesService.get_all()" in helper
    assert 'unidad.get("sucursal_origen_id")' in helper
    assert 'unidad.get("codigo")' in helper
    assert 'unidad.get("nombre")' in helper
    assert "130QRO" not in helper
    assert "ORIGEN" not in helper


def test_hoy_source_contract_is_engine_agnostic():
    text = ROUTES.read_text(encoding="utf-8")
    start = text.index("# HOY - CANONICO, ATOMICO Y TRANSVERSAL:")
    end = text.index("# FASE 3A.2: Migrado a helper centralizado", start)
    block = text[start:end]

    assert "server_id_norm" in block
    assert "unidad_codigo_hoy" in block
    assert '"source_type": (' in block
    assert '"EDARSAHUB_SNAPSHOT_DIA"' in block


def test_hoy_snapshot_matches_by_canonical_unit_not_server_topology():
    text = ROUTES.read_text(encoding="utf-8")
    start = text.index("# HOY - CANONICO, ATOMICO Y TRANSVERSAL:")
    end = text.index("# FASE 3A.2: Migrado a helper centralizado", start)
    block = text[start:end]

    assert "unidad_codigo_hoy" in block
    assert "unidad_negocio_codigo" in block
    assert "codigo_norm" in block

    # La identidad comercial no puede depender del server_id porque MPRO puede
    # escribir el snapshot mediante un API_LOCAL distinto al servidor canónico.
    assert "server_id_norm" not in block
    assert "candidatos = [" not in block


def test_hoy_snapshot_does_not_pick_first_row_from_shared_mpro_server():
    text = ROUTES.read_text(encoding="utf-8")
    start = text.index("# HOY - CANONICO, ATOMICO Y TRANSVERSAL:")
    end = text.index("# FASE 3A.2: Migrado a helper centralizado", start)
    block = text[start:end]

    assert "fila_hoy = next(" in block
    assert "row.get(\"unidad_negocio_codigo\")" in block
    assert "row.get(\"unidad_negocio_id\")" in block
