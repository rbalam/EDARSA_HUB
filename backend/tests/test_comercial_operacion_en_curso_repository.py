from datetime import date

from modules.comercial_analytics.repository_operational import (
    build_current_operation,
)


def test_common_date_prevents_mixed_operational_days():
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
                "propinas_abiertas": 5,
                "tickets_abiertos": 1,
                "pax_abiertos": 2,
                "ventas_cerradas_dia": 100,
                "propinas_cerradas_dia": 10,
                "tickets_cerrados_dia": 2,
                "pax_cerrados_dia": 4,
            }]

        return [{
            "unidad_negocio_id": "B",
            "unidad_negocio_nombre": "Unidad B",
            "fecha_operacion": "2026-08-01",
            "ventas_abiertas": 10,
            "propinas_abiertas": 1,
            "tickets_abiertos": 1,
            "pax_abiertos": 1,
            "ventas_cerradas_dia": 20,
            "propinas_cerradas_dia": 2,
            "tickets_cerrados_dia": 1,
            "pax_cerrados_dia": 1,
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

    assert result["fecha_operacion"] == "2026-08-02"
    assert result["fechas_operacion"] == ["2026-08-02"]
    assert result["fecha_operacion_multiple"] is False

    by_unit = {
        item["unidad_negocio_id"]: item
        for item in result["items"]
    }

    assert by_unit["A"]["cerradas"]["ventas"] == 100
    assert by_unit["A"]["abiertas"]["ventas"] == 50
    assert by_unit["A"]["operacion_estimada"]["ventas"] == 150

    assert by_unit["B"]["cerradas"]["ventas"] == 0
    assert by_unit["B"]["abiertas"]["ventas"] == 0
    assert by_unit["B"]["operacion_estimada"]["ventas"] == 0
    assert by_unit["B"]["operacion_estimada"]["propinas"] == 0
    assert by_unit["B"]["operacion_estimada"]["cheques"] == 0
    assert by_unit["B"]["operacion_estimada"]["pax"] == 0

    assert result["totales"]["cerradas"] == {
        "ventas": 100.0,
        "propinas": 10.0,
        "cheques": 2.0,
        "pax": 4.0,
    }
    assert result["totales"]["abiertas"] == {
        "ventas": 50.0,
        "propinas": 5.0,
        "cheques": 1.0,
        "pax": 2.0,
    }
    assert result["totales"]["operacion_estimada"] == {
        "ventas": 150.0,
        "propinas": 15.0,
        "cheques": 3.0,
        "pax": 6.0,
    }


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
def test_current_operation_preserves_comercial_drilldown_metadata():
    result = build_current_operation(
        allowed_unit_codes=["ORIGEN"],
        date_resolver=lambda unit: date(2026, 10, 1),
        sales_reader=lambda operation_date, units: [{
            "unidad_negocio_id": "ORIGEN",
            "unidad_negocio_nombre": "ORIGEN",
            "server_id": "SERVER-MPRO",
            "sucursal_id": "0023",
            "sucursal_nombre": "ORIGEN",
            "sistema_origen": "MPRO",
            "fecha_operacion": "2026-10-01",
            "ventas_abiertas": 2095,
            "tickets_abiertos": 3,
            "pax_abiertos": 7,
            "ventas_cerradas_dia": 4231,
            "tickets_cerrados_dia": 2,
            "pax_cerrados_dia": 15,
        }],
    )

    item = result["items"][0]

    assert item["server_id"] == "SERVER-MPRO"
    assert item["sucursal_id"] == "0023"
    assert item["sucursal_nombre"] == "ORIGEN"
    assert item["sistema_origen"] == "MPRO"


def test_executive_current_day_uses_certified_comercial_sales_detail():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    tablero = (
        root / "frontend/src/pages/TableroEjecutivo.js"
    ).read_text(encoding="utf-8")
    drill = (
        root
        / "frontend/src/components/comercial/KpiDrilldownDialog.jsx"
    ).read_text(encoding="utf-8")

    assert "server_id: item.server_id || null" in tablero
    assert "sucursal_id: item.sucursal_id || null" in tablero
    assert "/comercial/detalle-ventas-agrupado/" in drill
    assert "periodo: 'dia'" in drill
    assert "row.fuente_ticket || 'CERRADA'" in drill
    assert "/comercial/ticket-venta/" in drill
    assert "hasMissingOpen" in drill
