from modules.comercial import ticket_service


def test_mpro_closed_snapshot_uses_origin_folio_for_atomic_identity(monkeypatch):
    snapshot = [{
        "folio": "21-0053793",
        "folio_origen": "21-0045655",
        "sistema_origen": "MPRO",
        "estado_ticket": "CERRADA",
        "fecha_hora": "2026-10-12T10:00:00",
        "pax": 2,
        "propina": 431,
        "total_ticket": 2870,
        "producto_codigo": "P1",
        "producto_nombre": "P1",
        "cantidad": 1,
        "precio_unitario": 2870,
        "importe_bruto": 2870,
        "descuento_producto": 0,
        "descuento_pct": 0,
    }]
    monkeypatch.setattr(
        ticket_service,
        "load_open_snapshot_lines",
        lambda *_: snapshot,
    )

    historical = [{
        "folio": "21-0045655",
        "total_venta": 2870,
        "importe": 2870,
        "pax": 2,
        "num_productos": 1,
        "fuente_ticket": "CERRADA",
    }]

    result = ticket_service.merge_open_snapshot_tickets(
        historical,
        "130QRO",
        "0021",
        "2026-10-12",
    )

    assert ticket_service._snapshot_display_folio(snapshot[0]) == "21-0045655"
    assert len(result) == 1
    assert result[0]["folio"] == "21-0045655"
    assert result[0]["pax"] == 2
    assert result[0]["total_venta"] == 2870.0


def test_softrestaurant_snapshot_sale_excludes_tip():
    row = {
        "folio": "104262",
        "folio_origen": "104262",
        "sistema_origen": "SOFTRESTAURANT",
        "estado_ticket": "ABIERTA",
        "total_ticket": 7178.30,
        "propina": 936.30,
    }

    assert ticket_service._snapshot_sales_amount(row) == 6242.0


def test_mpro_snapshot_sale_does_not_subtract_tip():
    row = {
        "folio": "21-0053793",
        "folio_origen": "21-0045655",
        "sistema_origen": "MPRO",
        "estado_ticket": "CERRADA",
        "total_ticket": 2870,
        "propina": 431,
    }

    assert ticket_service._snapshot_sales_amount(row) == 2870.0
