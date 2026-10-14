from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_MODULE = ROOT / "modules/comercial_v2/mpro_closed_api.py"
SYNC_MODULE = ROOT / "modules/comercial_v2/sync_comercial_edarsahub.py"
PROTECTED_JOB = ROOT / "core/scheduler/jobs/sync_comercial_abiertas_v2_job.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def test_closed_sales_uses_canonical_local_api_role():
    text = _text(API_MODULE)

    assert 'MPRO_CLOSED_SALES_API_ROLE = "VENTAS_DIA_API_LOCAL"' in text
    assert "get_connection_for_role(" in text
    assert "tipo_conexion = 'API_LOCAL'" in text


def test_closed_sales_has_no_central2020_fallback():
    text = _text(API_MODULE)
    query_builder = text.split(
        "def build_mpro_closed_sales_query(", 1
    )[1].split(
        "def execute_mpro_select_via_api(", 1
    )[0]

    assert "CENTRAL2020" not in query_builder.upper()
    assert "fallback" not in query_builder.lower()


def test_mpro_units_share_final_header_authority_and_select_only():
    text = _text(API_MODULE)

    assert 'codigo not in {"ORIGEN", "130QRO"}' in text
    assert "FROM Venta_Encabezado AS ve" in text
    assert "ve.Vn_Precio_Neto_Importe AS Vn_Precio_Neto_Importe" in text
    assert "ve.Sc_Cve_Sucursal = '{sucursal}'" in text
    assert "ISNULL(ve.Vn_Tabla, '') = 'Comanda'" in text
    assert "FROM Comanda AS c" not in text
    assert "INNER JOIN Comanda_Detalle AS cd" not in text
    assert 'startswith("SELECT")' in text


def test_incremental_mpro_closed_sync_uses_local_api_helper():
    text = _text(SYNC_MODULE)

    assert "resolve_mpro_closed_api(config.unidad_negocio_pk)" in text
    assert "build_mpro_closed_sales_query(" in text
    assert "execute_mpro_select_via_api(" in text
    assert "No se permite fallback silencioso" in text


def test_softrestaurant_closed_path_remains_present():
    text = _text(SYNC_MODULE)

    assert "sync_softrestaurant_ventas_cerradas" in text
    assert "build_softrestaurant_ventas_cerradas_query(" in text


def test_protected_job_still_declares_local_api_contract():
    text = _text(PROTECTED_JOB)

    assert "MPRO ORIGEN/QRO: API local (NO SQL Server central)" in text
    assert "SoftRestaurant: tabla tempcheques (abiertas) + cheques (cerradas)" in text
