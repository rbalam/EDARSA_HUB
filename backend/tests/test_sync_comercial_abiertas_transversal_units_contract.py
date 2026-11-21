from pathlib import Path


JOB = (
    Path(__file__).resolve().parents[1]
    / "core"
    / "scheduler"
    / "jobs"
    / "sync_comercial_abiertas_v2_job.py"
)


def _unit_loader_block() -> str:
    text = JOB.read_text(encoding="utf-8")
    start = text.index("def _get_unidades_from_edarsahub()")
    end = text.index("\ndef _merge_mpro_summary_detail_rows(", start)
    return text[start:end]


def test_ventas_dia_loads_units_from_canonical_registry():
    block = _unit_loader_block()

    assert "UnidadesService.get_all()" in block
    assert 'row.get("server_id")' in block
    assert 'row.get("system_type")' in block
    assert 'row.get("sucursal_origen_id")' in block


def test_ventas_dia_classifies_both_supported_engine_families():
    block = _unit_loader_block()

    assert 'if "SOFT" in system_type:' in block
    assert 'elif "MPRO" in system_type or "MANAG" in system_type:' in block
    assert 'unidad["sistema"] = "SoftRestaurant"' in block
    assert 'unidad["sistema"] = "MPRO"' in block


def test_ventas_dia_unit_loader_has_no_fixed_current_unit_catalog():
    block = _unit_loader_block()

    # El universo operativo debe crecer con UnidadesService sin editar el job.
    for current_code in ("130MID", "CIENFUEGOS", "ESTELAR", "130QRO", "ORIGEN"):
        assert current_code not in block


def test_ventas_dia_processes_both_dynamic_unit_collections():
    text = JOB.read_text(encoding="utf-8")

    assert "unidades_sr, unidades_mpro = _get_unidades_from_edarsahub()" in text
    assert "for unidad in unidades_sr:" in text
    assert "for unidad in unidades_mpro:" in text
