from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DETAIL = ROOT / "scripts/poblar_ventas_detalle_producto_canonico.py"


def test_mpro_closed_detail_persists_vendor_from_canonical_pos_tables():
    text = DETAIL.read_text(encoding="utf-8")
    block = text.split("def _extract_mpro(", 1)[1].split("PRORRATEO_Q4", 1)[0]
    assert "v.Vn_Cve_Vendedor" in block
    assert "LEFT JOIN Vendedor vnd" in block
    assert "vnd.Vn_Descripcion" in block
    assert "AS vendedor_id" in block
    assert "AS vendedor_nombre" in block
    assert "l.vendedor_id" in block
    assert "l.vendedor_nombre" in block
