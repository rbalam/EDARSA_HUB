from decimal import Decimal
from pathlib import Path

from scripts.poblar_ventas_detalle_producto_canonico import _prorratear_mpro_por_ticket

ROOT = Path(__file__).resolve().parents[2]
DETAIL = ROOT / "backend" / "scripts/poblar_ventas_detalle_producto_canonico.py"


def _row(product, gross, target, descuento_producto="0", pct="0"):
    return {
        "id_transaccion": "MPRO:ORIGEN:1",
        "numero_ticket": "1",
        "es_kpi_valido": 1,
        "importe_neto_ticket": Decimal(target),
        "importe_bruto": Decimal(gross),
        "descuento_producto_importe": Decimal(descuento_producto),
        "descuento_global_importe": Decimal("0"),
        "descuento_pct": Decimal(pct),
        "producto_codigo_fuente": product,
        "producto_nombre": product,
    }


def test_mpro_preserves_explicit_product_discount_and_separates_header_delta():
    out = _prorratear_mpro_por_ticket([
        _row("A", "100", "180", "10", "10"),
        _row("B", "100", "180", "0", "0"),
    ])
    products = [x for x in out if not str(x["producto_codigo_fuente"]).startswith("__ISCAM_AJUSTE_")]
    adjustments = [x for x in out if str(x["producto_codigo_fuente"]).startswith("__ISCAM_AJUSTE_")]
    assert [x["importe_neto"] for x in products] == [Decimal("90.0000"), Decimal("100.0000")]
    assert [x["descuento_producto_importe"] for x in products] == [Decimal("10"), Decimal("0")]
    assert len(adjustments) == 1
    assert adjustments[0]["importe_neto"] == Decimal("-10.0000")
    assert sum(x["importe_neto"] for x in out) == Decimal("180.0000")


def test_mpro_product_discount_can_close_ticket_to_zero_without_fake_adjustment():
    out = _prorratear_mpro_por_ticket([
        _row("PRODUCTO_A", "100", "0", "100", "100"),
    ])
    assert len(out) == 1
    assert out[0]["importe_neto"] == Decimal("0.0000")
    assert out[0]["descuento_producto_importe"] == Decimal("100")


def test_mpro_header_without_product_detail_becomes_technical_adjustment():
    row = _row("HEADER_SIN_DETALLE", "0", "125", "0")
    out = _prorratear_mpro_por_ticket([row])
    assert out[0]["producto_codigo_fuente"] == "__ISCAM_AJUSTE_ENCABEZADO__"
    assert out[0]["cantidad"] == Decimal("0")
    assert out[0]["importe_bruto"] == Decimal("125.0000")
    assert out[0]["importe_neto"] == Decimal("125.0000")


def test_mpro_zero_net_zero_gross_preserves_real_product_lines():
    out = _prorratear_mpro_por_ticket([
        _row("PRODUCTO_A", "0", "0", "0"),
        _row("PRODUCTO_B", "0", "0", "0"),
    ])
    assert [x["producto_codigo_fuente"] for x in out] == [
        "PRODUCTO_A",
        "PRODUCTO_B",
    ]
    assert [x["importe_neto"] for x in out] == [
        Decimal("0.0000"),
        Decimal("0.0000"),
    ]


def test_mpro_branch_filter_uses_header_and_detail_schema():
    text = DETAIL.read_text(encoding="utf-8")
    block = text.split("def _extract_mpro(", 1)[1].split("PRORRATEO_Q4", 1)[0]
    assert "v.Sc_Cve_Sucursal = %s" in block
    assert "d.Sc_Cve_Sucursal = h.Sc_Cve_Sucursal" in block


def test_mpro_detail_uses_venta_explicit_discount_amount():
    text = DETAIL.read_text(encoding="utf-8")
    block = text.split("def _extract_mpro(", 1)[1].split("PRORRATEO_Q4", 1)[0]
    assert "FROM Venta vd" in block
    assert "vd.Vn_Precio_Lista_Importe" in block
    assert "vd.Vn_Descuento_Importe" in block
    assert "vd.Vn_Descuento_Global_Importe" in block
    assert "AS descuento_pct" in block
    assert "Comanda_Detalle" not in block
