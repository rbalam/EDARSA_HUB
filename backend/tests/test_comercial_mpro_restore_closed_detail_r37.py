from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "backend/modules/comercial_v2/ticket_snapshot.py"
SYNC = ROOT / "backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py"


def test_closed_canonical_has_comanda_product_fallback():
    snapshot = SNAPSHOT.read_text(encoding="utf-8")
    sync = SYNC.read_text(encoding="utf-8")
    assert "QUERY_MPRO_DETALLE_CERRADAS_CANONICAS_COMANDA" in snapshot
    fallback = snapshot.split(
        "QUERY_MPRO_DETALLE_CERRADAS_CANONICAS_COMANDA", 1
    )[1].split(
        "QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES", 1
    )[0]
    assert "Comanda_Detalle d" in fallback
    assert "EXISTS (" in fallback
    assert "Venta_Encabezado ve" in fallback
    assert "d.Cd_Concepto" in fallback
    assert "d.Pr_Cve_Producto" in fallback

    assert "def _prefer_real_mpro_detail_rows(" in sync
    assert "QUERY_MPRO_DETALLE_CERRADAS_CANONICAS_COMANDA.format" in sync
    assert "_prefer_real_mpro_detail_rows(" in sync


def test_summary_is_only_last_resort_not_preferred_detail():
    sync = SYNC.read_text(encoding="utf-8")
    helper = sync.split(
        "def _prefer_real_mpro_detail_rows(", 1
    )[1].split(
        "def _summarize_mpro_ticket_rows", 1
    )[0]
    assert '"DETALLE RESUMIDO" not in name' in helper
    assert '"VENTA SIN DETALLE DE PRODUCTO" not in name' in helper
