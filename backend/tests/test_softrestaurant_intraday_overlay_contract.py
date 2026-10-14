import json

from modules.comercial_v2.repository_readonly import (
    _overlay_softrestaurant_intraday_from_detail_json,
)


def test_softrestaurant_open_detail_keeps_pos_total_and_separates_tip():
    row = {
        "sistema_origen": "SOFTRESTAURANT",
        "ventas_cerradas_dia": 0,
        "tickets_cerrados_dia": 0,
        "pax_cerrados_dia": 0,
        "propinas_cerradas_dia": 0,
        "detalle_abiertas_json": json.dumps([
            {
                "folio_origen": "1",
                "total_ticket": 111900.0,
                "propina": 10382.3,
                "pax": 76,
            }
        ]),
    }

    result = _overlay_softrestaurant_intraday_from_detail_json(row)

    assert result["ventas_abiertas"] == 111900.0
    assert result["propinas_abiertas"] == 10382.3
    assert result["total_estimado_dia"] == 111900.0
    assert result["propinas_total"] == 10382.3
    assert result["tickets_abiertos"] == 1
    assert result["pax_abiertos"] == 76


def test_softrestaurant_open_detail_preserves_closed_portion():
    row = {
        "sistema_origen": "SOFTRESTAURANT",
        "ventas_cerradas_dia": 133109.0,
        "tickets_cerrados_dia": 26,
        "pax_cerrados_dia": 70,
        "propinas_cerradas_dia": 12000.0,
        "detalle_abiertas_json": json.dumps([
            {
                "folio_origen": "A",
                "total_ticket": 300.0,
                "propina": 40.0,
                "pax": 3,
            },
            {
                "folio_origen": "B",
                "total_ticket": 230.0,
                "propina": 30.0,
                "pax": 2,
            },
        ]),
    }

    result = _overlay_softrestaurant_intraday_from_detail_json(row)

    assert result["ventas_abiertas"] == 530.0
    assert result["propinas_abiertas"] == 70.0
    assert result["tickets_abiertos"] == 2
    assert result["pax_abiertos"] == 5

    assert result["ventas_cerradas_dia"] == 133109.0
    assert result["tickets_cerrados_dia"] == 26
    assert result["pax_cerrados_dia"] == 70
    assert result["propinas_cerradas_dia"] == 12000.0

    assert result["total_estimado_dia"] == 133639.0
    assert result["propinas_total"] == 12070.0


def test_non_softrestaurant_is_untouched():
    row = {
        "sistema_origen": "MPRO",
        "ventas_abiertas": 50.0,
        "detalle_abiertas_json": json.dumps([
            {"folio_origen": "1", "total_ticket": 100.0, "propina": 10.0}
        ]),
    }

    assert _overlay_softrestaurant_intraday_from_detail_json(row) is row
    assert row["ventas_abiertas"] == 50.0
