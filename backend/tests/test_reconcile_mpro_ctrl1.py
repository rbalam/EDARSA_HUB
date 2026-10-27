"""Unit tests without any POS/SQL network access."""
from decimal import Decimal

import pytest

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "core/inventarios/reconcile_mpro_ctrl1.py"
_spec = importlib.util.spec_from_file_location("reconcile_mpro_ctrl1_testable", MODULE_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
build_reconciliation_plan = _module.build_reconciliation_plan


def fixture_rows():
    source = [
        {"fecha": "2026-10-08", "folio": "A", "cantidad": Decimal("5000"), "unidad": "GR"},
        {"fecha": "2026-10-13", "folio": "B", "cantidad": Decimal("4500"), "unidad": "GR"},
        {"fecha": "2026-10-23", "folio": "C", "cantidad": Decimal("6200"), "unidad": "GR"},
    ]
    hub = []
    for movement_id, date, folio, original in [
        (53898, "2026-10-08", "A", "5"),
        (53899, "2026-10-13", "B", "4.5"),
        (53903, "2026-10-23", "C", "6.2"),
    ]:
        hub.append({
            "MovimientoID": movement_id, "fecha": date,
            "EmpresaID": 2, "SucursalID": 2, "ProductoID": 2014,
            "CodigoAlmacen": "0001", "ReferenciaTipo": "MOVIMIENTO_POS|112",
            "FolioReferencia": folio, "Naturaleza": "E", "Activo": 1,
            "Cantidad": Decimal(original),
        })
    return source, hub


def test_exact_three_verified_differences():
    source, hub = fixture_rows()
    plan = build_reconciliation_plan(source, hub)
    assert len(plan) == 3
    assert sum(p["needs_update"] for p in plan) == 3
    assert sum((p["source_ctrl1"] for p in plan), Decimal(0)) == 15700


def test_idempotent_existing_correct_rows():
    source, hub = fixture_rows()
    hub[0]["Cantidad"] = Decimal("5000")
    plan = build_reconciliation_plan(source, hub)
    assert sum(p["needs_update"] for p in plan) == 2


@pytest.mark.parametrize("field,value", [
    ("EmpresaID", 3), ("SucursalID", 3), ("ProductoID", 9),
    ("CodigoAlmacen", "999"), ("ReferenciaTipo", "MOVIMIENTO_POS|109"),
    ("Naturaleza", "S"), ("Activo", 0), ("FolioReferencia", "wrong"),
])
def test_fails_closed_for_identity_drift(field, value):
    source, hub = fixture_rows()
    hub[0][field] = value
    with pytest.raises(ValueError):
        build_reconciliation_plan(source, hub)


def test_fails_closed_on_changed_origin_value():
    source, hub = fixture_rows()
    source[0]["cantidad"] = Decimal("5")
    with pytest.raises(ValueError, match="ORIGEN_CTRL1"):
        build_reconciliation_plan(source, hub)


def test_fails_closed_on_duplicate_hub_line():
    source, hub = fixture_rows()
    with pytest.raises(ValueError):
        build_reconciliation_plan(source, hub + [hub[0]])


def test_fails_closed_for_different_origin_unit():
    source, hub = fixture_rows()
    source[0]["unidad"] = "KG"
    with pytest.raises(ValueError, match="UNIDAD"):
        build_reconciliation_plan(source, hub)


def test_fails_closed_on_noncertified_hub_value():
    source, hub = fixture_rows()
    hub[0]["Cantidad"] = Decimal("7")
    with pytest.raises(ValueError, match="CAMBIO_INESPERADO"):
        build_reconciliation_plan(source, hub)


def test_commercial_and_soft_sync_files_not_modified_by_this_feature():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    script = (root / "core/inventarios/reconcile_mpro_ctrl1.py").read_text()
    assert "sync_comercial_v2" not in script
    assert "sync_comercial_abiertas_v2" not in script
    assert "sync_movimientos_canonico(" not in script
