from modules.comercial import ticket_service


def test_soft_snapshot_keeps_zero_numcheque_accounts_atomic(monkeypatch):
    rows = [
        {
            "folio": "0",
            "folio_origen": "1",
            "sistema_origen": "SOFTRESTAURANT",
            "estado_ticket": "ABIERTA",
            "fecha_hora": "2026-10-08T10:00:00",
            "pax": 1,
            "propina": 35,
            "total_ticket": 1535,
            "producto_codigo": "A",
            "producto_nombre": "A",
            "cantidad": 1,
            "precio_unitario": 1500,
            "importe_bruto": 1500,
            "descuento_producto": 0,
            "descuento_pct": 0,
        },
        {
            "folio": "0",
            "folio_origen": "4",
            "sistema_origen": "SOFTRESTAURANT",
            "estado_ticket": "ABIERTA",
            "fecha_hora": "2026-10-08T11:00:00",
            "pax": 2,
            "propina": 30,
            "total_ticket": 6030,
            "producto_codigo": "B",
            "producto_nombre": "B",
            "cantidad": 1,
            "precio_unitario": 6000,
            "importe_bruto": 6000,
            "descuento_producto": 0,
            "descuento_pct": 0,
        },
    ]
    monkeypatch.setattr(ticket_service, "load_open_snapshot_lines", lambda *_: rows)

    result = ticket_service.merge_open_snapshot_tickets([], "CIENFUEGOS", "DEFAULT", "2026-10-08")

    assert [item["folio"] for item in result] == ["1", "4"]
    assert [item["total_venta"] for item in result] == [1535.0, 6030.0]


def test_soft_snapshot_display_folio_prefers_numcheque_when_nonzero():
    row = {
        "folio": "103994",
        "folio_origen": "2",
        "sistema_origen": "SOFTRESTAURANT",
    }
    assert ticket_service._snapshot_display_folio(row) == "103994"
    assert ticket_service._snapshot_ticket_identity(row) == "SOFTRESTAURANT:2"


def test_soft_snapshot_preserves_closed_and_adds_open_while_active(monkeypatch):
    rows = [
        {
            "folio": "103994",
            "folio_origen": "2",
            "sistema_origen": "SOFTRESTAURANT",
            "estado_ticket": "ABIERTA",
            "fecha_hora": "2026-10-08T10:30:00",
            "pax": 3,
            "propina": 85,
            "total_ticket": 1385,
            "producto_codigo": "P1",
            "producto_nombre": "P1",
            "cantidad": 1,
            "precio_unitario": 1300,
            "importe_bruto": 1300,
            "descuento_producto": 0,
            "descuento_pct": 0,
        }
    ]
    monkeypatch.setattr(ticket_service, "load_open_snapshot_lines", lambda *_: rows)
    closed = [{
        "folio": "900001",
        "total_venta": 9999,
        "importe": 9999,
        "pax": 10,
        "num_productos": 1,
        "fuente_ticket": "CERRADA",
    }]

    result = ticket_service.merge_open_snapshot_tickets(
        closed, "ANY_SOFTRESTAURANT_UNIT", "DEFAULT", "2026-10-08"
    )

    by_folio = {str(item["folio"]): item for item in result}

    assert set(by_folio) == {"900001", "103994"}
    assert by_folio["900001"]["total_venta"] == 9999
    assert by_folio["900001"]["pax"] == 10
    assert by_folio["103994"]["total_venta"] == 1385.0
    assert by_folio["103994"]["pax"] == 3
