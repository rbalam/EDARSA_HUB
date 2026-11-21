from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYNC_JOB = ROOT / "backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py"
ENRICH = ROOT / "backend/core/scheduler/jobs/inteligencia_comercial_enrich.py"


def test_pos_config_resolution_disambiguates_shared_server_with_unit_pk():
    text = SYNC_JOB.read_text(encoding="utf-8")
    block = text.split("def get_pos_config_for_unidad", 1)[1].split(
        "def audit_syncpos_canonical_configs", 1
    )[0]
    assert "get_server_connection_config(" in block
    assert "unidad_negocio_pk=unidad_row.get(\"unidad_pk\")" in block


def test_mpro_payments_join_uses_document_reference_not_sales_folio():
    text = ENRICH.read_text(encoding="utf-8")
    block = text.split("def _extract_mpro", 1)[1].split(
        "# ============================================================================\n# ESCRITURA EN EDARSAHUB", 1
    )[0]
    assert "INNER JOIN Comanda_Pago cp WITH (NOLOCK) ON cp.Co_Folio = v.Vn_Documento" in block
    assert "INNER JOIN Comanda_Pago cp WITH (NOLOCK) ON cp.Co_Folio = v.Vn_Folio" not in block
    assert "AND v.Sc_Cve_Sucursal = '{suc}'" in block
