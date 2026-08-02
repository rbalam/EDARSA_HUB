from modules.comercial_analytics.operational_service import (
    build_operational_snapshot,
)


UNITS = [
    {
        "unidad_negocio_id": "A",
        "unidad_negocio_nombre": "Unidad A",
    },
    {
        "unidad_negocio_id": "B",
        "unidad_negocio_nombre": "Unidad B",
    },
]


def test_closed_plus_open_same_operational_day():
    result = build_operational_snapshot(
        effective_operational_date="2026-08-02",
        allowed_units=UNITS,
        closed_rows=[{
            "unidad_negocio_id": "A",
            "fecha_operacion": "2026-08-02",
            "ventas": 100,
            "propinas": 10,
            "cheques": 2,
            "pax": 4,
        }],
        open_rows=[{
            "unidad_negocio_id": "A",
            "fecha_operacion": "2026-08-02",
            "ventas": 50,
            "propinas": 5,
            "cheques": 1,
            "pax": 2,
        }],
    )

    unit = result["items"][0]

    assert unit["cerradas"]["ventas"] == 100
    assert unit["abiertas"]["ventas"] == 50
    assert unit["operacion_estimada"]["ventas"] == 150
    assert unit["operacion_estimada"]["cheques"] == 3
    assert unit["operacion_estimada"]["pax"] == 6


def test_units_without_activity_return_zero():
    result = build_operational_snapshot(
        effective_operational_date="2026-08-02",
        allowed_units=UNITS,
        closed_rows=[],
        open_rows=[],
    )

    assert len(result["items"]) == 2

    for item in result["items"]:
        assert item["cerradas"]["ventas"] == 0
        assert item["abiertas"]["ventas"] == 0
        assert item["operacion_estimada"]["ventas"] == 0
        assert item["operacion_estimada"]["cheques"] == 0
        assert item["operacion_estimada"]["pax"] == 0


def test_does_not_fallback_to_last_day_with_data():
    result = build_operational_snapshot(
        effective_operational_date="2026-08-02",
        allowed_units=UNITS,
        closed_rows=[{
            "unidad_negocio_id": "A",
            "fecha_operacion": "2026-08-01",
            "ventas": 999,
            "cheques": 9,
            "pax": 9,
        }],
        open_rows=[{
            "unidad_negocio_id": "A",
            "fecha_operacion": "2026-08-01",
            "ventas": 888,
            "cheques": 8,
            "pax": 8,
        }],
    )

    assert result["totales"]["operacion_estimada"]["ventas"] == 0
    assert result["traceability"]["fallback_to_last_data_date"] is False


def test_old_open_tickets_are_excluded():
    result = build_operational_snapshot(
        effective_operational_date="2026-08-02",
        allowed_units=UNITS,
        closed_rows=[],
        open_rows=[
            {
                "unidad_negocio_id": "A",
                "fecha_operacion": "2026-08-01",
                "ventas": 500,
            },
            {
                "unidad_negocio_id": "A",
                "fecha_operacion": "2026-08-02",
                "ventas": 100,
            },
        ],
    )

    assert result["items"][0]["abiertas"]["ventas"] == 100


def test_rows_outside_rbac_are_excluded():
    result = build_operational_snapshot(
        effective_operational_date="2026-08-02",
        allowed_units=UNITS,
        closed_rows=[{
            "unidad_negocio_id": "NO_PERMITIDA",
            "fecha_operacion": "2026-08-02",
            "ventas": 1000,
        }],
        open_rows=[],
    )

    assert result["totales"]["operacion_estimada"]["ventas"] == 0


def test_historical_and_operational_domains_are_explicitly_separated():
    result = build_operational_snapshot(
        effective_operational_date="2026-08-02",
        allowed_units=UNITS,
        closed_rows=[],
        open_rows=[],
    )

    traceability = result["traceability"]

    assert traceability["domain"] == "operacion_en_curso"
    assert traceability["historical"] is False
    assert traceability["live"] is True
    assert traceability["temporal_field"] == "fecha_operacion"
