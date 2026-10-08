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
    assert [item["total_venta"] for item in result] == [1500.0, 6000.0]


def test_soft_snapshot_display_folio_prefers_numcheque_when_nonzero():
    row = {
        "folio": "103994",
        "folio_origen": "2",
        "sistema_origen": "SOFTRESTAURANT",
    }
    assert ticket_service._snapshot_display_folio(row) == "103994"
    assert ticket_service._snapshot_ticket_identity(row) == "SOFTRESTAURANT:2"
