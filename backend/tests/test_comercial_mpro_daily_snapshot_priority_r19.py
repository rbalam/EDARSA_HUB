from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "modules/comercial/ticket_service.py"


def test_mpro_closed_daily_snapshot_overrides_existing_list_rows():
    text = SERVICE.read_text(encoding="utf-8")
    block = text.split(
        "def merge_open_snapshot_tickets(", 1
    )[1].split(
        "def _real_product_row(", 1
    )[0]
    assert "preferidos_api_local_mpro" in block
    assert '"CERRADA"' in block
    assert '"MPRO"' in block
    assert "not in preferidos_api_local_mpro" in block


def test_mpro_closed_ticket_prefers_api_local_snapshot_before_canonical():
    text = SERVICE.read_text(encoding="utf-8")
    block = text.split(
        "def build_ticket_venta(", 1
    )[1]
    assert "preferir_snapshot_mpro" in block
    assert (
        "closed_rows = [] if preferir_snapshot_mpro "
        "else _query_edarsahub_tablero("
    ) in block
    assert "API_LOCAL_DIA" in block
