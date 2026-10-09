from datetime import date

import pytest

from modules.sync_historicos.planner import (
    HistoricalPlanError,
    build_historical_plan,
    partition_range,
)


def _registry(system_code="MPRO"):
    return [
        {
            "eligible_for_historical": True,
            "system_code": system_code,
            "system_id": 2,
            "system_capability_id": 201,
            "capability_key": "ventas_encabezado",
            "category_key": "VENTAS",
            "category_name": "Ventas",
            "entity_key": "VENTA_ENCABEZADO",
            "handler": "sync_ventas_encabezado",
            "date_field": "fecha",
            "business_key": ["unidad_negocio_pk", "folio"],
            "dependencias": [],
            "execution_order": 10,
            "supports_resume": True,
            "supports_safe_stop": True,
            "version": "1",
            "metadata": {
                "chunk_unit": "day",
                "max_attempts": 3,
                "retry_backoff_seconds": 5,
            },
        },
        {
            "eligible_for_historical": True,
            "system_code": system_code,
            "system_id": 2,
            "system_capability_id": 202,
            "capability_key": "ventas_detalle",
            "category_key": "VENTAS",
            "category_name": "Ventas",
            "entity_key": "VENTA_DETALLE",
            "handler": "sync_ventas_detalle",
            "date_field": "fecha",
            "business_key": ["unidad_negocio_pk", "folio", "renglon"],
            "dependencias": [
                {"codigo": "ventas_encabezado", "obligatoria": True},
            ],
            "execution_order": 20,
            "supports_resume": True,
            "supports_safe_stop": True,
            "version": "1",
            "metadata": {
                "chunk_unit": "day",
                "max_attempts": 3,
            },
        },
    ]


def _unit(system_code="MPRO"):
    return {
        "unit_id": "11111111-1111-1111-1111-111111111111",
        "unit_code": "UNIDAD-A",
        "connection_id": "22222222-2222-2222-2222-222222222222",
        "system_id": 2,
        "system_code": system_code,
        "system_version_id": None,
        "branch_id": 10,
        "branch_origin_id": "ORIG-A",
        "company_id": 5,
    }


def test_partition_range_requires_declared_strategy():
    with pytest.raises(
        HistoricalPlanError,
        match="CHUNK_STRATEGY_MISSING_OR_UNSUPPORTED",
    ):
        partition_range(
            date(2026, 1, 1),
            date(2026, 1, 2),
            {},
        )


def test_dependency_is_added_before_selected_capability():
    plan = build_historical_plan(
        start=date(2026, 1, 1),
        end=date(2026, 1, 2),
        selected_systems=["MPRO"],
        selected_units=["UNIDAD-A"],
        selected_capabilities=["ventas_detalle"],
        registry=_registry(),
        unit_contexts=[_unit()],
        correlation_id="33333333-3333-3333-3333-333333333333",
    )

    assert len(plan.atomic_units) == 4
    assert [u.capability_key for u in plan.atomic_units] == [
        "ventas_encabezado",
        "ventas_encabezado",
        "ventas_detalle",
        "ventas_detalle",
    ]
    assert len({u.atomic_key for u in plan.atomic_units}) == 4


def test_unit_cannot_execute_capability_for_another_system():
    with pytest.raises(
        HistoricalPlanError,
        match="CAPABILITY_NOT_ELIGIBLE",
    ):
        build_historical_plan(
            start=date(2026, 1, 1),
            end=date(2026, 1, 1),
            selected_systems=["SOFTRESTAURANT"],
            selected_units=["UNIDAD-A"],
            selected_capabilities=["ventas_detalle"],
            registry=_registry(system_code="MPRO"),
            unit_contexts=[_unit(system_code="SOFTRESTAURANT")],
        )


def test_atomic_key_is_deterministic_for_same_scope():
    kwargs = dict(
        start=date(2026, 1, 1),
        end=date(2026, 1, 1),
        selected_systems=["MPRO"],
        selected_units=["UNIDAD-A"],
        selected_capabilities=["ventas_encabezado"],
        registry=_registry(),
        unit_contexts=[_unit()],
    )
    first = build_historical_plan(**kwargs)
    second = build_historical_plan(**kwargs)
    assert first.atomic_units[0].atomic_key == second.atomic_units[0].atomic_key


def test_protected_open_sales_sync_is_not_referenced():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    sources = [
        root / "modules/sync_historicos/planner.py",
        root / "modules/sync_historicos/job_repository.py",
        root / "database/migrations/20261009_002_sync_historical_planner.sql",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in sources).lower()
    assert "sync_comercial_abiertas_v2" not in text


def test_ambiguous_system_capability_binding_is_rejected():
    registry = _registry()
    duplicate = dict(registry[0])
    duplicate["system_capability_id"] = 999
    with pytest.raises(
        HistoricalPlanError,
        match="AMBIGUOUS_SYSTEM_CAPABILITY_BINDING",
    ):
        build_historical_plan(
            start=date(2026, 1, 1),
            end=date(2026, 1, 1),
            selected_systems=["MPRO"],
            selected_units=["UNIDAD-A"],
            selected_capabilities=["ventas_encabezado"],
            registry=registry + [duplicate],
            unit_contexts=[_unit()],
        )
