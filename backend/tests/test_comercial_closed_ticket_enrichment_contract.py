from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DETAIL = ROOT / "scripts/poblar_ventas_detalle_producto_canonico.py"
SERVICE = ROOT / "modules/comercial/ticket_service.py"


def test_soft_closed_detail_uses_numcheque_seller_and_line_discount():
    text = DETAIL.read_text(encoding="utf-8")
    block = text.split("def _extract_soft(", 1)[1].split("SOFT_AJUSTE_CHEQUE", 1)[0]
    assert "ch.numcheque" in block
    assert "LEFT JOIN meseros m" in block
    assert "AS vendedor_nombre" in block
    assert "dc.descuento" in block
    assert "AS descuento_pct" in block
    assert "AS numero_ticket" in block
    assert "l.numcheque" in block


def test_closed_detail_materializes_new_canonical_fields():
    text = DETAIL.read_text(encoding="utf-8")
    assert '"vendedor_id": _s(r.get("vendedor_id")) or None' in text
    assert '"vendedor_nombre": _s(r.get("vendedor_nombre"))[:200] or None' in text
    assert '"descuento_pct": (' in text
    assert "vendedor_id," in text
    assert "vendedor_nombre," in text
    assert "descuento_pct" in text


def test_ticket_service_consumes_closed_seller_and_source_discount_pct():
    text = SERVICE.read_text(encoding="utf-8")
    closed = text.split("if closed_rows:", 1)[1].split("open_rows =", 1)[0]
    assert "descuento_pct_origen" in closed
    assert 'row.get("vendedor_nombre")' in closed
    assert '"vendedor": vendedor' in closed
