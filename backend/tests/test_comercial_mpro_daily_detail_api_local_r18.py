from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "backend/modules/comercial_v2/ticket_snapshot.py"
SYNC = ROOT / "backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py"
SERVICE = ROOT / "backend/modules/comercial/ticket_service.py"


def test_mpro_daily_detail_has_open_and_closed_contracts():
    text = SNAPSHOT.read_text(encoding="utf-8")

    assert "QUERY_MPRO_DETALLE_ABIERTAS" in text
    assert "QUERY_MPRO_DETALLE_CERRADAS_CANONICAS" in text
    assert "QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES" in text

    canonical = text.split(
        "QUERY_MPRO_DETALLE_CERRADAS_CANONICAS", 1
    )[1].split(
        "QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES", 1
    )[0]
    assert "Venta_Encabezado ve" in canonical
    assert "ve.Vn_Documento" in canonical
    assert "ve.Vn_Precio_Neto_Importe" in canonical
    assert "ve.Es_Cve_Estado IN ('AC', 'FA')" in canonical

    provisional = text.split(
        "QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES", 1
    )[1]
    assert "Comanda_Detalle d" in provisional
    assert "c.Es_Cve_Estado = 'PA'" in provisional


def test_mpro_detail_uses_same_closed_source_decision_as_header():
    text = SYNC.read_text(encoding="utf-8")
    block = text.split(
        "# El encabezado MPRO se calcula con abiertas + cerradas", 1
    )[1].split(
        "# FIX 2026-05-15: Log detallado para QRO", 1
    )[0]

    assert "tickets_abiertos > 0" in block
    assert "tickets_cerrados_dia > 0" in block
    assert 'closed_sales_source' in block
    assert '"CANONICAL_VENTA_ENCABEZADO"' in block
    assert "QUERY_MPRO_DETALLE_CERRADAS_CANONICAS" in block
    assert "QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES" in block
    assert "_execute_query_via_api_local" in block
    assert "detalle_completo" in block


def test_comercial_endpoints_remain_no_live():
    text = SERVICE.read_text(encoding="utf-8")
    assert "_execute_query_via_api_local" not in text
    assert "requests.get(" not in text
    assert "API_LOCAL_DIA" in text
    assert "estado_snapshot" in text
