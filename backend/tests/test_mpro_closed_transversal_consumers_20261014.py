from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

API = ROOT / "backend/modules/comercial_v2/mpro_closed_api.py"
SYNC = ROOT / "backend/modules/comercial_v2/sync_comercial_edarsahub.py"
COMMERCIAL = ROOT / "backend/modules/comercial/service.py"
EXECUTIVE = ROOT / "backend/modules/dashboard_ejecutivo/routes.py"
PROTECTED = ROOT / "backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py"


def _text(path):
    return path.read_text(encoding="utf-8")


def test_origen_and_130qro_share_venta_encabezado_final_authority():
    text = _text(API)
    assert 'codigo not in {"ORIGEN", "130QRO"}' in text
    assert "FROM Venta_Encabezado AS ve" in text
    assert "ve.Vn_Precio_Neto_Importe AS Vn_Precio_Neto_Importe" in text
    assert "ve.Sc_Cve_Sucursal = '{sucursal}'" in text
    assert "Comanda_Detalle" not in text


def test_closed_sync_persists_shared_final_authority():
    text = _text(SYNC)
    assert "def sync_mpro_ventas_cerradas(" in text
    assert "build_mpro_closed_sales_query(" in text
    assert "map_mpro_ventas_cerradas(" in text
    assert "upsert_kpi_diario(kpi)" in text


def test_commercial_and_executive_consume_shared_kpi_service():
    commercial = _text(COMMERCIAL)
    executive = _text(EXECUTIVE)
    assert "KPIsCanonicosService.resumen_periodo(" in commercial
    assert "KPIsCanonicosService.resumen_periodo_desglosado(" in executive
    assert 'desglose.get("acumulado_cerrado")' in executive


def test_protected_intraday_job_is_not_part_of_final_closed_change():
    text = _text(PROTECTED)
    assert "sync_comercial_abiertas_v2" in str(PROTECTED)
    assert "PROVISIONAL_COMANDA" in text
