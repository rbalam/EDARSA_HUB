from datetime import date

from modules.comercial_analytics.repository_operational import (
    build_current_operation,
)


def test_each_unit_preserves_its_operational_date_and_values():
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

    assert result["fecha_operacion"] is None
    assert result["fechas_operacion"] == [
        "2026-08-01",
        "2026-08-02",
    ]
    assert result["fecha_operacion_multiple"] is True

    by_unit = {
        item["unidad_negocio_id"]: item
        for item in result["items"]
    }

    assert by_unit["A"]["fecha_operacion"] == "2026-08-02"
    assert by_unit["A"]["cerradas"]["ventas"] == 100
    assert by_unit["A"]["abiertas"]["ventas"] == 50
    assert by_unit["A"]["operacion_estimada"]["ventas"] == 150

    assert by_unit["B"]["fecha_operacion"] == "2026-08-01"
    assert by_unit["B"]["cerradas"]["ventas"] == 20
    assert by_unit["B"]["abiertas"]["ventas"] == 10
    assert by_unit["B"]["operacion_estimada"]["ventas"] == 30

    assert result["totales"]["cerradas"] == {
        "ventas": 120.0,
        "propinas": 12.0,
        "cheques": 3.0,
        "pax": 5.0,
    }
    assert result["totales"]["abiertas"] == {
        "ventas": 60.0,
        "propinas": 6.0,
        "cheques": 2.0,
        "pax": 3.0,
    }
    assert result["totales"]["operacion_estimada"] == {
        "ventas": 180.0,
        "propinas": 18.0,
        "cheques": 5.0,
        "pax": 8.0,
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

    # Tablero Ejecutivo conserva RBAC por unidad y no cruza
    # directamente a las rutas Comercial protegidas por server_id.
    assert "/comercial/detalle-ventas-agrupado/" not in drill
    assert "/comercial/ticket-venta/" not in drill

    # Ventas del Dia utiliza el endpoint analytics del Ejecutivo.
    assert "/v2/comercial/analytics/tickets" in drill
    assert "ticketPk: item.ticket_pk" in drill

    # Cada sucursal conserva su fecha operativa propia en Ventas del Día.
    assert "currentOperationSuppressed = false" in drill


def test_previous_mpro_before_first_turn_does_not_replay_closed_sales():
    result = build_current_operation(
        allowed_unit_codes=["130QRO"],
        operation_context_resolver=lambda unit: {
            "fecha_operacion": date(2026, 10, 12),
            "metodo_fecha_operacion": "ANTES_PRIMER_TURNO_CRUZA",
            "turno_operativo_codigo": "FUERA_HORARIO",
            "timestamp_consulta": __import__("datetime").datetime(
                2026, 10, 13, 10, 49
            ),
        },
        sales_reader=lambda operation_date, units: [{
            "unidad_negocio_id": "130QRO",
            "fecha_operacion": "2026-10-12",
            "sistema_origen": "MPRO",
            "ventas_abiertas": 0,
            "propinas_abiertas": 0,
            "tickets_abiertos": 0,
            "pax_abiertos": 0,
            "ventas_cerradas_dia": 84508,
            "propinas_cerradas_dia": 10190,
            "tickets_cerrados_dia": 17,
            "pax_cerrados_dia": 43,
        }],
    )

    item = result["items"][0]

    assert item["fecha_operacion"] == "2026-10-12"
    assert item["cerradas"]["ventas"] == 0
    assert item["abiertas"]["ventas"] == 0
    assert item["operacion_estimada"]["ventas"] == 0
    assert item["current_display_policy"] == (
        "MPRO_PREVIOUS_DATE_BEFORE_FIRST_TURN_OPEN_ONLY"
    )


def test_previous_softrestaurant_after_cut_keeps_only_open_remainder():
    result = build_current_operation(
        allowed_unit_codes=["130MID"],
        operation_context_resolver=lambda unit: {
            "fecha_operacion": date(2026, 10, 12),
            "metodo_fecha_operacion": "TURNO_CRUZA_MEDIANOCHE_MADRUGADA",
            "turno_operativo_codigo": "CENA",
            "timestamp_consulta": __import__("datetime").datetime(
                2026, 10, 13, 10, 49
            ),
        },
        sales_reader=lambda operation_date, units: [{
            "unidad_negocio_id": "130MID",
            "fecha_operacion": "2026-10-12",
            "sistema_origen": "SOFTRESTAURANT",
            "ventas_abiertas": 260,
            "propinas_abiertas": 0,
            "tickets_abiertos": 2,
            "pax_abiertos": 3,
            "ventas_cerradas_dia": 124671.20,
            "propinas_cerradas_dia": 8372.80,
            "tickets_cerrados_dia": 24,
            "pax_cerrados_dia": 68,
        }],
    )

    item = result["items"][0]

    assert item["cerradas"]["ventas"] == 0
    assert item["abiertas"]["ventas"] == 260
    assert item["operacion_estimada"]["ventas"] == 260
    assert item["operacion_estimada"]["cheques"] == 2
    assert item["operacion_estimada"]["pax"] == 3
    assert item["current_display_policy"] == (
        "SOFT_PREVIOUS_DATE_AFTER_CUT_OPEN_ONLY"
    )


def test_previous_softrestaurant_without_cut_remains_current_operation():
    result = build_current_operation(
        allowed_unit_codes=["CIENFUEGOS"],
        operation_context_resolver=lambda unit: {
            "fecha_operacion": date(2026, 10, 12),
            "metodo_fecha_operacion": "TURNO_CRUZA_MEDIANOCHE_MADRUGADA",
            "turno_operativo_codigo": "CENA",
            "timestamp_consulta": __import__("datetime").datetime(
                2026, 10, 13, 10, 49
            ),
        },
        sales_reader=lambda operation_date, units: [{
            "unidad_negocio_id": "CIENFUEGOS",
            "fecha_operacion": "2026-10-12",
            "sistema_origen": "SOFTRESTAURANT",
            "ventas_abiertas": 101517.70,
            "propinas_abiertas": 10382.30,
            "tickets_abiertos": 22,
            "pax_abiertos": 76,
            "ventas_cerradas_dia": 0,
            "propinas_cerradas_dia": 0,
            "tickets_cerrados_dia": 0,
            "pax_cerrados_dia": 0,
        }],
    )

    item = result["items"][0]

    assert item["cerradas"]["ventas"] == 0
    assert item["abiertas"]["ventas"] == 101517.70
    assert item["operacion_estimada"]["ventas"] == 101517.70
    assert item["operacion_estimada"]["cheques"] == 22
    assert item["operacion_estimada"]["pax"] == 76
    assert item["current_display_policy"] == (
        "SOFT_PREVIOUS_DATE_UNCUT"
    )


def test_current_date_operation_keeps_open_and_closed_portions():
    result = build_current_operation(
        allowed_unit_codes=["ORIGEN"],
        operation_context_resolver=lambda unit: {
            "fecha_operacion": date(2026, 10, 13),
            "metodo_fecha_operacion": "TURNO_ACTIVO",
            "turno_operativo_codigo": "DESAYUNO",
            "timestamp_consulta": __import__("datetime").datetime(
                2026, 10, 13, 10, 49
            ),
        },
        sales_reader=lambda operation_date, units: [{
            "unidad_negocio_id": "ORIGEN",
            "fecha_operacion": "2026-10-13",
            "sistema_origen": "MPRO",
            "ventas_abiertas": 5540,
            "propinas_abiertas": 0,
            "tickets_abiertos": 4,
            "pax_abiertos": 12,
            "ventas_cerradas_dia": 0,
            "propinas_cerradas_dia": 0,
            "tickets_cerrados_dia": 0,
            "pax_cerrados_dia": 0,
        }],
    )

    item = result["items"][0]

    assert item["abiertas"]["ventas"] == 5540
    assert item["operacion_estimada"]["ventas"] == 5540
    assert item["current_display_policy"] == "CURRENT_OPERATION_DATE"
