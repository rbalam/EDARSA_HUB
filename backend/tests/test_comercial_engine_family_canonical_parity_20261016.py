from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MPRO = ROOT / "backend/modules/comercial_v2/mpro_closed_api.py"
SYNC = ROOT / "backend/modules/comercial_v2/sync_comercial_edarsahub.py"
PROTECTED = ROOT / "backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py"

def _text(path):
    return path.read_text(encoding="utf-8")

def test_mpro_closed_sales_is_engine_transversal_not_unit_allowlisted():
    text = _text(MPRO)
    block = text.split("def build_mpro_closed_sales_query(", 1)[1].split(
        "def execute_mpro_select_via_api(", 1
    )[0]
    assert 'codigo not in {"ORIGEN", "130QRO"}' not in block
    assert "FROM Venta_Encabezado AS ve" in block
    assert "ve.Vn_Precio_Neto_Importe AS Vn_Precio_Neto_Importe" in block
    assert "ve.Sc_Cve_Sucursal = '{sucursal}'" in block
    assert "MPRO closed-sales canonical branch id is required" in block

def test_softrestaurant_closed_day_rule_is_engine_transversal():
    text = _text(SYNC)
    block = text.split("def build_softrestaurant_ventas_cerradas_query(", 1)[1].split(
        "QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS", 1
    )[0]
    assert "offset_hours = 9" in block
    assert "== 'ESTELAR'" not in block
    assert "== 'CIENFUEGOS'" not in block
    assert "== '130MID'" not in block
    assert "DATEADD(hour, -{offset_hours}, tr.apertura)" in text

def test_protected_intraday_worker_remains_unchanged():
    text = _text(PROTECTED)
    assert "PROVISIONAL_COMANDA" in text
    assert "MPRO ORIGEN/QRO: API local (NO SQL Server central)" in text
