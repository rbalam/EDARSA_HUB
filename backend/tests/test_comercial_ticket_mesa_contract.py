from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANON = ROOT / "backend/scripts/poblar_ventas_detalle_producto_canonico.py"
SNAP = ROOT / "backend/modules/comercial_v2/ticket_snapshot.py"
SERVICE = ROOT / "backend/modules/comercial/ticket_service.py"
COMERCIAL = ROOT / "frontend/src/pages/Comercial.js"
KPI = ROOT / "frontend/src/components/comercial/KpiDrilldownDialog.jsx"


def test_softrestaurant_open_uses_tempcheques_mesa():
    text = SNAP.read_text(encoding="utf-8")
    assert "tempcheques ch" in text
    assert "ch.mesa" in text
    assert '"mesa": str(row.get("mesa")' in text


def test_mpro_uses_comanda_referencia_as_mesa():
    canon = CANON.read_text(encoding="utf-8")
    snap = SNAP.read_text(encoding="utf-8")
    assert "c.Co_Referencia" in canon
    assert "c.Co_Referencia" in snap
    assert 'AS mesa' in canon


def test_closed_ticket_persists_and_reads_mesa_without_live_pos():
    canon = CANON.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    assert '"mesa": _s(r.get("mesa"))[:100] or None' in canon
    assert "descuento_pct,\n            mesa" in canon
    assert "Comercial_Inteligencia_VentasDetalleProducto" in service
    assert "mesa," in service
    assert '"mesa": mesa' in service


def test_ticket_headers_render_mesa():
    for path in (COMERCIAL, KPI):
        text = path.read_text(encoding="utf-8")
        assert "ticket.mesa" in text
        assert "<span>MESA:</span>" in text
