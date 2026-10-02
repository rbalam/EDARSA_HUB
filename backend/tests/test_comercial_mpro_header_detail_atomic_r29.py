from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "backend/modules/comercial_v2/ticket_snapshot.py"
SYNC = ROOT / "backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py"


def test_mpro_summary_fallback_queries_exist():
    text = SNAPSHOT.read_text(encoding="utf-8")
    assert "QUERY_MPRO_DETALLE_ABIERTAS_RESUMEN" in text
    assert "QUERY_MPRO_DETALLE_CERRADAS_CANONICAS_RESUMEN" in text
    assert "QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES_RESUMEN" in text
    assert "VENTA CERRADA MPRO - DETALLE RESUMIDO" in text


def test_header_and_detail_are_atomic_from_same_snapshot_set():
    text = SYNC.read_text(encoding="utf-8")
    assert "def _merge_mpro_summary_detail_rows(" in text
    assert "def _summarize_mpro_ticket_rows(" in text
    assert "rows_resumen_abiertas" in text
    assert "rows_resumen_canonico" in text
    assert "rows_resumen_provisional" in text
    assert "folios_cerrados" in text
    assert "metricas_snapshot = _summarize_mpro_ticket_rows" in text
    assert "SOURCE_ERROR: snapshot MPRO incompleto" in text
    assert "QUERY_MPRO_DETALLE_CERRADAS_CANONICAS_RESUMEN" in text
    assert "QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES_RESUMEN" in text
    assert "QUERY_MPRO_DETALLE_ABIERTAS_RESUMEN" in text
