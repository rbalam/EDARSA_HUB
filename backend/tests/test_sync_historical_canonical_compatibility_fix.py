from datetime import date
from pathlib import Path

from modules.sync_historicos.planner import build_historical_plan

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT.parent / "frontend/src/pages/SyncHistorical.jsx"
CATALOG = ROOT / "modules/sync_historicos/catalog_service.py"
ADAPTER = ROOT / "modules/sync_historicos/comercial_detail_adapter.py"
MIGRATION = ROOT / "database/migrations/20261014_001_sync_historical_comercial_detalle.sql"


def _cap(system_code, system_id, capability_id):
    return {
        "eligible_for_historical": True,
        "system_code": system_code,
        "system_id": system_id,
        "system_capability_id": capability_id,
        "capability_key": "comercial_ventas_detalle",
        "category_key": "VENTAS",
        "category_name": "Comercial",
        "entity_key": "VENTA_DETALLE",
        "handler": "backfill_sync_sales",
        "date_field": "FechaHora",
        "business_key": ["UnidadNegocio", "NumeroTicket", "FechaHora"],
        "dependencias": [],
        "execution_order": 10,
        "supports_resume": True,
        "supports_safe_stop": True,
        "version": "historical-detail-v1",
        "metadata": {
            "chunk_unit": "day",
            "max_attempts": 3,
            "retry_backoff_seconds": 15,
        },
    }


def _unit(code, system_code, system_id, suffix):
    return {
        "unit_id": f"11111111-1111-1111-1111-{suffix}",
        "unit_code": code,
        "connection_id": f"22222222-2222-2222-2222-{suffix}",
        "system_id": system_id,
        "system_code": system_code,
        "system_version_id": None,
        "branch_id": system_id,
        "branch_origin_id": str(system_id),
        "company_id": system_id,
    }


def test_visual_grouping_uses_canonical_group_not_category_code():
    text = CATALOG.read_text(encoding="utf-8")
    assert 'display_category_key = "GROUP::" + category_name.upper()' in text
    assert "if category_key" not in text


def test_frontend_allows_partial_system_compatibility():
    text = FRONT.read_text(encoding="utf-8")
    assert "effectiveSystems.some" in text
    assert "partiallyCompatible" in text
    assert "planner ejecutará solo las sucursales válidas" in text
    assert "No compatible con toda la selección" not in text


def test_planner_keeps_only_valid_atomic_units_for_partial_compatibility():
    plan = build_historical_plan(
        start=date(2026, 1, 1),
        end=date(2026, 1, 1),
        selected_systems=["MPRO", "SOFTRESTAURANT_PRO"],
        selected_units=["MPRO-A", "SOFT-A"],
        selected_capabilities=["comercial_ventas_detalle"],
        registry=[_cap("MPRO", 2, 21)],
        unit_contexts=[
            _unit("MPRO-A", "MPRO", 2, "000000000001"),
            _unit("SOFT-A", "SOFTRESTAURANT_PRO", 1, "000000000002"),
        ],
        correlation_id="33333333-3333-3333-3333-333333333333",
    )
    assert len(plan.atomic_units) == 1
    assert plan.atomic_units[0].system_code == "MPRO"
    assert plan.atomic_units[0].unit_code == "MPRO-A"


def test_detail_adapter_is_isolated_from_protected_sales_syncs():
    text = ADAPTER.read_text(encoding="utf-8").lower()
    assert "resolve_pos_runtime_context" in text
    assert "pilot_backfill_sync_sales" in text
    assert "sync_comercial_abiertas_v2" not in text
    assert "sync_softrestaurant_ventas_cerradas" not in text
    assert "sync_mpro_ventas_cerradas" not in text
    assert "_ejecutar_sync_real" not in text


def test_detail_migration_binds_both_current_systems_without_touching_protected_syncs():
    text = MIGRATION.read_text(encoding="utf-8")
    assert "comercial_ventas_detalle" in text
    assert "SYNC_VENTAS_HISTORICAS" in text
    assert "'MPRO','SOFTRESTAURANT_PRO'" in text
    lower = text.lower()
    assert "sync_comercial_abiertas_v2" not in lower
    assert "sync_softrestaurant_ventas_cerradas" not in lower
    assert "sync_mpro_ventas_cerradas" not in lower
