import os
from unittest.mock import patch

import pytest

os.environ.setdefault("EDARSAHUB_SQL_HOST", "test.invalid")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "test_readonly")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "test_only")
os.environ.setdefault("JWT_SECRET", "test_only")

from modules.comercial_analytics.schemas import (
    CommercialDrilldownRequest,
)
from modules.comercial_analytics.service import build_drilldown


ROWS = [
    {
        "fecha_operacion": "2025-12-10",
        "unidad_negocio_pk": "pk-mid",
        "unidad_negocio_id": "130MID",
        "unidad_negocio_nombre": "130° Mérida",
        "ventas_total": 100,
        "pax_total": 2,
        "tickets_total": 1,
    },
    {
        "fecha_operacion": "2026-01-05",
        "unidad_negocio_pk": "pk-mid",
        "unidad_negocio_id": "130MID",
        "unidad_negocio_nombre": "130° Mérida",
        "ventas_total": 200,
        "pax_total": 3,
        "tickets_total": 2,
    },
    {
        "fecha_operacion": "2026-02-05",
        "unidad_negocio_pk": "pk-mid",
        "unidad_negocio_id": "130MID",
        "unidad_negocio_nombre": "130° Mérida",
        "ventas_total": 999,
        "pax_total": 9,
        "tickets_total": 9,
    },
]


def payload(metric="ventas", level="year"):
    return CommercialDrilldownRequest(
        metric=metric,
        level=level,
        scope={
            "mode": "historical_periods",
            "periods": [
                {"year": 2025, "months": [12]},
                {"year": 2026, "months": [1]},
            ],
        },
        business_unit_code="130MID",
    )


@patch(
    "modules.comercial_analytics.service."
    "KPIsCanonicosService.series_periodo",
    return_value=ROWS,
)
def test_year_drilldown_uses_selected_months_only(mock_series):
    result = build_drilldown(
        payload(),
        allowed_unit_codes=["130MID"],
    )

    assert result["level"] == "year"
    assert result["total"] == 300
    assert [item["key"] for item in result["items"]] == [
        "2026",
        "2025",
    ]
    assert result["traceability"]["source"] == (
        "KPIS_CANONICOS_SERVICE"
    )
    assert result["traceability"]["temporal_field"] == (
        "fecha_operacion"
    )


@patch(
    "modules.comercial_analytics.service."
    "KPIsCanonicosService.series_periodo",
    return_value=ROWS,
)
def test_metric_pax(mock_series):
    result = build_drilldown(
        payload(metric="pax", level="month"),
        allowed_unit_codes=["130MID"],
    )

    assert result["total"] == 5
    assert [item["value"] for item in result["items"]] == [3, 2]


@patch(
    "modules.comercial_analytics.service."
    "KPIsCanonicosService.series_periodo",
    return_value=ROWS,
)
def test_operational_day_level(mock_series):
    result = build_drilldown(
        payload(metric="cheques", level="operational_day"),
        allowed_unit_codes=["130MID"],
    )

    assert result["total"] == 3
    assert [item["key"] for item in result["items"]] == [
        "2025-12-10",
        "2026-01-05",
    ]


def test_rejects_unit_outside_rbac():
    with pytest.raises(PermissionError):
        build_drilldown(
            payload(),
            allowed_unit_codes=["CIENFUEGOS"],
        )
