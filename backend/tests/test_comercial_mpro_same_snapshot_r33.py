from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / "backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py"


def test_mpro_snapshot_uses_summary_set_as_authority():
    text = SYNC.read_text(encoding="utf-8")
    assert "def _merge_mpro_summary_detail_rows(" in text
    assert "def _summarize_mpro_ticket_rows(" in text
    assert "rows_resumen_abiertas" in text
    assert "rows_resumen_canonico" in text
    assert "rows_resumen_provisional" in text
    assert "metricas_snapshot = _summarize_mpro_ticket_rows" in text


def test_mpro_header_is_derived_from_same_serialized_rows():
    text = SYNC.read_text(encoding="utf-8")
    marker = "# El encabezado se deriva del MISMO conjunto de tickets"
    block = text.split(marker, 1)[1].split(
        "if detalle_completo:", 1
    )[0]
    assert 'ventas_abiertas = abiertas_snapshot["ventas"]' in block
    assert 'tickets_abiertos = abiertas_snapshot["tickets"]' in block
    assert 'ventas_cerradas_dia = cerradas_snapshot["ventas"]' in block
    assert 'tickets_cerrados_dia = cerradas_snapshot["tickets"]' in block
    assert "total_estimado_dia = (" in block


def test_closed_tickets_override_open_same_folio():
    text = SYNC.read_text(encoding="utf-8")
    assert "folios_cerrados" in text
    assert "not in folios_cerrados" in text
