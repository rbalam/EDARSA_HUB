from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "modules/comercial_v2/ticket_snapshot.py"
SYNC = ROOT / "core/scheduler/jobs/sync_comercial_abiertas_v2_job.py"
SERVICE = ROOT / "modules/comercial/ticket_service.py"
FRONT = ROOT.parent / "frontend/src/pages/Comercial.js"


def test_softrestaurant_zero_total_open_tickets_are_not_omitted():
    snapshot = SNAPSHOT.read_text(encoding="utf-8")
    sync = SYNC.read_text(encoding="utf-8")
    assert "AND ISNULL(ch.total, 0) >= 0" in snapshot
    assert "AND ISNULL(total, 0) >= 0" in sync
    assert "AND ISNULL(ch.total, 0) > 0" not in snapshot


def test_softrestaurant_product_discount_contract_is_persisted():
    text = SNAPSHOT.read_text(encoding="utf-8")
    assert "d.descuento" in text
    assert "AS descuento_pct" in text
    assert "AS descuento_producto" in text
    assert "AS importe_neto_producto" in text
    assert '"descuento_pct":' in text
    assert '"descuento_producto":' in text
    assert '"importe_neto_producto":' in text


def test_ticket_service_splits_product_and_account_discounts():
    text = SERVICE.read_text(encoding="utf-8")
    assert '"descuento_productos": descuento_productos' in text
    assert '"descuento_cuenta": descuento_cuenta' in text
    assert '"descuento_importe":' in text
    assert '"importe_neto":' in text


def test_ticket_ui_shows_product_and_account_discount_amounts():
    text = FRONT.read_text(encoding="utf-8")
    assert "DESC. PRODUCTOS" in text
    assert "DESC. CUENTA" in text
    assert "TOTAL PROD." in text
    assert "item.descuento_pct" in text
