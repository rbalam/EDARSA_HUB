from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "modules/comercial_v2/ticket_snapshot.py"
FRONTEND = ROOT.parent / "frontend/src/pages/Comercial.js"


def test_softrestaurant_visible_folio_uses_numcheque():
    text = SNAPSHOT.read_text(encoding="utf-8")
    start = text.index("QUERY_SOFTRESTAURANT_DETALLE_ABIERTAS")
    end = text.index("QUERY_MPRO_DETALLE_ABIERTAS", start)
    block = text[start:end]
    assert "ch.numcheque" in block
    assert "AS folio_origen" in block
    assert "ON d.foliodet = ch.folio" in block


def test_ticket_date_is_trimmed_to_seconds():
    text = (ROOT.parent / "frontend/src/components/comercial/TicketVentaModal.jsx").read_text(encoding="utf-8")
    assert ".replace('T', ' ').slice(0, 19)" in text
