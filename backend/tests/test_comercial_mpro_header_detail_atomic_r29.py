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


def test_header_and_detail_are_atomic_when_detail_is_incomplete():
    text = SYNC.read_text(encoding="utf-8")
    assert "necesita_resumen_abiertas" in text
    assert "necesita_resumen_cerradas" in text
    assert "folios_abiertos_detalle" in text
    assert "folios_cerrados_detalle" in text
    assert "SOURCE_ERROR: snapshot MPRO incompleto" in text
    assert "QUERY_MPRO_DETALLE_CERRADAS_CANONICAS_RESUMEN" in text
    assert "QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES_RESUMEN" in text
    assert "QUERY_MPRO_DETALLE_ABIERTAS_RESUMEN" in text
