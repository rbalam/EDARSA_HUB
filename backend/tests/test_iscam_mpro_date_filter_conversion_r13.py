from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DETAIL = ROOT / "backend/scripts/poblar_ventas_detalle_producto_canonico.py"


def _extract_mpro_block() -> str:
    text = DETAIL.read_text(encoding="utf-8")
    return text.split("def _extract_mpro(", 1)[1].split("PRORRATEO_Q4", 1)[0]


def test_mpro_detail_filters_vn_fecha_as_calendar_date():
    block = _extract_mpro_block()
    assert "WHERE CONVERT(date, v.Vn_Fecha) >= CONVERT(date, %s)" in block
    assert "AND CONVERT(date, v.Vn_Fecha) < CONVERT(date, %s)" in block
    assert "WHERE v.Vn_Fecha >= %s" not in block


def test_mpro_detail_keeps_branch_and_canonical_header_guards():
    block = _extract_mpro_block()
    assert "AND v.Sc_Cve_Sucursal = %s" in block
    assert "AND ISNULL(v.Vn_Tabla, '') = 'Comanda'" in block
    assert "AND ISNULL(v.Es_Cve_Estado, '') IN ('AC', 'FA', 'CA')" in block
    assert "ISNULL(v.Vn_Precio_Neto_Importe, 0) AS importe_neto_ticket" in block


def test_mpro_date_filter_preserves_half_open_range():
    block = _extract_mpro_block()
    assert ">= CONVERT(date, %s)" in block
    assert "< CONVERT(date, %s)" in block
