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
    assert "NULLIF(NULLIF(MAX(LTRIM(RTRIM(CONVERT(varchar(64), ch.numcheque)))), ''), '0')" in block
    assert "AS folio_origen" in block
    assert "ON d.foliodet = ch.folio" in block


def test_ticket_date_is_trimmed_to_seconds():
    text = (ROOT.parent / "frontend/src/components/comercial/TicketVentaModal.jsx").read_text(encoding="utf-8")
    assert ".replace('T', ' ').slice(0, 19)" in text


def test_snapshot_merge_preserves_internal_identity_for_zero_numcheque():
    service = (ROOT / "modules/comercial/ticket_service.py").read_text(encoding="utf-8")
    assert "def _snapshot_display_folio" in service
    assert 'if folio in {"", "0"}' in service
    assert "def _snapshot_ticket_identity" in service
    assert "def _snapshot_sales_amount" in service
    assert 'return _money(row.get("total_ticket"))' in service
    assert "return total - propina" not in service
