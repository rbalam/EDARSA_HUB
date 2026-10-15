from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTRACTOR = ROOT / "backend" / "scripts" / "poblar_ventas_detalle_producto_canonico.py"
CONTRACT = ROOT / "backend" / "modules" / "comercial_v2" / "ticket_contract.py"


def test_detail_insert_uses_ticket_contract_columns_and_dynamic_placeholders():
    extractor = EXTRACTOR.read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")

    assert 'insert_columns = base_columns + tuple(FIELDS)' in extractor
    assert 'placeholders = ",".join(["%s"] * len(insert_columns))' in extractor
    assert '*(r.get(field) for field in FIELDS)' in extractor

    for field in ("ticket_subtotal", "ticket_impuesto", "ticket_total"):
        assert field in contract


def test_detail_insert_keeps_atomic_delete_and_insert_transaction():
    extractor = EXTRACTOR.read_text(encoding="utf-8")
    block = extractor.split("def _insert_rows(", 1)[1].split("def sync_detalle_producto_canonico_dia", 1)[0]
    assert "conn.autocommit(False)" in block
    assert "DELETE FROM {DESTINO}" in block
    assert "conn.commit()" in block
    assert "conn.rollback()" in block
