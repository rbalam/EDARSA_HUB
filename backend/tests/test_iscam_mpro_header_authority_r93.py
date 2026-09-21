from decimal import Decimal
from pathlib import Path

from scripts.poblar_ventas_detalle_producto_canonico import _prorratear_mpro_por_ticket

ROOT = Path(__file__).resolve().parents[2]
DETAIL = ROOT / "backend" / "scripts" / "poblar_ventas_detalle_producto_canonico.py"


def _row(product, gross, target, descuento="0"):
    return {
        "id_transaccion": "MPRO:ORIGEN:1",
        "numero_ticket": "1",
        "es_kpi_valido": 1,
        "importe_neto_ticket": Decimal(target),
        "descuento_comanda": Decimal(descuento),
        "importe_bruto": Decimal(gross),
        "producto_codigo_fuente": product,
        "producto_nombre": product,
    }


def test_mpro_uses_final_header_even_when_comanda_discount_does_not_explain_delta():
    out = _prorratear_mpro_por_ticket([
        _row("A", "100", "180", "0"),
        _row("B", "100", "180", "0"),
    ])
    assert sum(x["importe_neto"] for x in out) == Decimal("180.0000")
    assert [x["importe_neto"] for x in out] == [Decimal("90.0000"), Decimal("90.0000")]


def test_mpro_header_total_is_preserved_with_rounding_residual():
    out = _prorratear_mpro_por_ticket([
        _row("A", "1", "1", "0"),
        _row("B", "1", "1", "0"),
        _row("C", "1", "1", "0"),
    ])
    assert sum(x["importe_neto"] for x in out) == Decimal("1.0000")


def test_mpro_zero_final_header_distributes_zero_without_inventing_sales():
    out = _prorratear_mpro_por_ticket([
        _row("A", "80", "0", "80"),
        _row("B", "20", "0", "80"),
    ])
    assert sum(x["importe_neto"] for x in out) == Decimal("0.0000")


def test_mpro_header_without_product_detail_becomes_technical_adjustment():
    row = _row("HEADER_SIN_DETALLE", "0", "125", "0")
    out = _prorratear_mpro_por_ticket([row])
    assert out[0]["producto_codigo_fuente"] == "__ISCAM_AJUSTE_ENCABEZADO__"
    assert out[0]["cantidad"] == Decimal("0")
    assert out[0]["importe_bruto"] == Decimal("125.0000")
    assert out[0]["importe_neto"] == Decimal("125.0000")


def test_mpro_zero_gross_non_header_still_fails_closed():
    import pytest
    with pytest.raises(RuntimeError, match="sin detalle monetario distribuible"):
        _prorratear_mpro_por_ticket([_row("PRODUCTO_REAL", "0", "125", "0")])


def test_mpro_detail_join_is_scoped_to_same_branch():
    text = DETAIL.read_text(encoding="utf-8")
    block = text.split("def _extract_mpro(", 1)[1].split("PRORRATEO_Q4", 1)[0]
    assert "d.Sc_Cve_Sucursal = h.Sc_Cve_Sucursal" in block
