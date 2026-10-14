from modules.comercial import ticket_service


def _hist(folio, pax, venta):
    return {
        "folio": folio,
        "pax": pax,
        "total_venta": venta,
        "importe": venta,
        "fuente_ticket": "CERRADA",
    }


def _snap(folio, pax, total, propina=0.0):
    return {
        "folio": folio,
        "folio_origen": folio,
        "sistema_origen": "SOFTRESTAURANT",
        "estado_ticket": "ABIERTA",
        "fecha_hora": "2026-10-13T12:00:00",
        "pax": pax,
        "propina": propina,
        "total_ticket": total,
        "producto_codigo": "P1",
        "producto_nombre": "P1",
        "cantidad": 1,
        "precio_unitario": total,
        "importe_bruto": total,
        "descuento_producto": 0,
        "descuento_pct": 0,
    }


def test_softrestaurant_mixed_keeps_closed_and_adds_open(monkeypatch):
    monkeypatch.setattr(
        ticket_service,
        "load_open_snapshot_lines",
        lambda *_: [_snap("200", 2, 2200, 200)],
    )

    result = ticket_service.merge_open_snapshot_tickets(
        [_hist("100", 1, 18377)],
        "ANY_SOFTRESTAURANT_UNIT",
        "",
        "2026-10-13",
    )

    by_folio = {str(x["folio"]): x for x in result}

    assert set(by_folio) == {"100", "200"}
    assert by_folio["100"]["total_venta"] == 18377
    assert by_folio["100"]["pax"] == 1
    assert by_folio["200"]["total_venta"] == 2200
    assert by_folio["200"]["pax"] == 2


def test_softrestaurant_same_folio_is_not_duplicated(monkeypatch):
    monkeypatch.setattr(
        ticket_service,
        "load_open_snapshot_lines",
        lambda *_: [_snap("100", 1, 18577, 200)],
    )

    result = ticket_service.merge_open_snapshot_tickets(
        [_hist("100", 1, 18377)],
        "ANY_SOFTRESTAURANT_UNIT",
        "",
        "2026-10-13",
    )

    assert len(result) == 1
    assert result[0]["folio"] == "100"
    assert result[0]["total_venta"] == 18377


def test_softrestaurant_rule_has_no_unit_specific_branching():
    import inspect

    source = inspect.getsource(
        ticket_service.merge_open_snapshot_tickets
    )

    for unit in ("CIENFUEGOS", "130MID", "ESTELAR"):
        assert unit not in source

    assert "SOFTRESTAURANT" not in source or "result = []" not in source


def test_mpro_behavior_remains_separate(monkeypatch):
    snapshot = [{
        "folio": "21-0053793",
        "folio_origen": "21-0045655",
        "sistema_origen": "MPRO",
        "estado_ticket": "CERRADA",
        "fecha_hora": "2026-10-13T12:00:00",
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

    result = ticket_service.merge_open_snapshot_tickets(
        [_hist("21-0045655", 2, 2870)],
        "130QRO",
        "0021",
        "2026-10-13",
    )

    assert len(result) == 1
    assert result[0]["folio"] == "21-0045655"
    assert result[0]["total_venta"] == 2870
