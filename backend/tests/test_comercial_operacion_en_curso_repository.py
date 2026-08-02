from datetime import date

from modules.comercial_analytics.repository_operational import (
    build_current_operation,
)


def test_each_unit_uses_its_current_operational_date():
    requested = []

    def resolver(unit_code):
        return {
            "A": date(2026, 8, 2),
            "B": date(2026, 8, 1),
        }[unit_code]

    def reader(operation_date, units):
        requested.append(
            (operation_date.isoformat(), tuple(units))
        )

        if units == ["A"]:
            return [{
                "unidad_negocio_id": "A",
                "unidad_negocio_nombre": "Unidad A",
                "fecha_operacion": "2026-08-02",
                "ventas_abiertas": 50,
                "tickets_abiertos": 1,
                "pax_abiertos": 2,
                "ventas_cerradas_dia": 100,
                "tickets_cerrados_dia": 2,
                "pax_cerrados_dia": 4,
            }]

        return [{
            "unidad_negocio_id": "B",
            "unidad_negocio_nombre": "Unidad B",
            "fecha_operacion": "2026-08-01",
            "ventas_abiertas": 10,
            "ventas_cerradas_dia": 20,
        }]

    result = build_current_operation(
        allowed_unit_codes=["A", "B"],
        date_resolver=resolver,
        sales_reader=reader,
    )

    assert requested == [
        ("2026-08-02", ("A",)),
        ("2026-08-01", ("B",)),
    ]
    assert result["fecha_operacion_multiple"] is True
    assert result["totales"]["operacion_estimada"][
        "ventas"
    ] == 180


def test_missing_current_snapshot_returns_zero():
    result = build_current_operation(
        allowed_unit_codes=["A"],
        date_resolver=lambda unit: date(2026, 8, 2),
        sales_reader=lambda operation_date, units: [],
    )

    item = result["items"][0]

    assert item["fecha_operacion"] == "2026-08-02"
    assert item["cerradas"]["ventas"] == 0
    assert item["abiertas"]["ventas"] == 0
    assert item["operacion_estimada"]["ventas"] == 0


def test_rows_from_other_dates_are_not_used():
    result = build_current_operation(
        allowed_unit_codes=["A"],
        date_resolver=lambda unit: date(2026, 8, 2),
        sales_reader=lambda operation_date, units: [{
            "unidad_negocio_id": "A",
            "fecha_operacion": "2026-07-31",
            "ventas_abiertas": 900,
            "ventas_cerradas_dia": 100,
        }],
    )

    assert result["totales"]["operacion_estimada"][
        "ventas"
    ] == 0


def test_unresolved_unit_does_not_fallback():
    def resolver(unit_code):
        if unit_code == "A":
            raise RuntimeError("sin configuración")
        return date(2026, 8, 2)

    result = build_current_operation(
        allowed_unit_codes=["A", "B"],
        date_resolver=resolver,
        sales_reader=lambda operation_date, units: [],
    )

    assert [item["unidad_negocio_id"] for item in result[
        "items"
    ]] == ["B"]
    assert result["unidades_sin_fecha_operativa"][0][
        "unidad_negocio_id"
    ] == "A"
    assert result["traceability"][
        "fallback_to_last_data_date"
    ] is False
    assert result["traceability"][
        "fallback_to_civil_date"
    ] is False


def test_closed_and_open_values_remain_separate():
    result = build_current_operation(
        allowed_unit_codes=["A"],
        date_resolver=lambda unit: date(2026, 8, 2),
        sales_reader=lambda operation_date, units: [{
            "unidad_negocio_id": "A",
            "fecha_operacion": "2026-08-02",
            "ventas_abiertas": 75,
            "propinas_abiertas": 5,
            "tickets_abiertos": 2,
            "pax_abiertos": 3,
            "ventas_cerradas_dia": 125,
            "propinas_cerradas_dia": 10,
            "tickets_cerrados_dia": 4,
            "pax_cerrados_dia": 8,
        }],
    )

    item = result["items"][0]

    assert item["cerradas"]["ventas"] == 125
    assert item["abiertas"]["ventas"] == 75
    assert item["operacion_estimada"]["ventas"] == 200
    assert item["operacion_estimada"]["cheques"] == 6
    assert item["operacion_estimada"]["pax"] == 11
