from pathlib import Path

SOURCE = Path(
    "/app/backend/modules/compras/sync_service.py"
).read_text(encoding="utf-8")


def test_detail_query_accepts_canonical_branch():
    assert (
        "sucursal_origen_id: Optional[str] = None"
        in SOURCE
    )


def test_mpro_fails_closed_without_branch():
    assert (
        "MPRO requiere sucursal_origen_id canónica"
        in SOURCE
    )


def test_mpro_header_filters_source_branch():
    assert (
        "AND F.Sc_Cve_Sucursal = "
        "'{safe_sucursal_origen}'"
        in SOURCE
    )


def test_snapshot_replace_is_unit_scoped():
    assert SOURCE.count(
        "AND unidad_negocio_id = %s"
    ) >= 3


def test_detail_key_is_scoped_by_business_unit():
    expected = """    key_names = [
        "server_id",
        "unidad_negocio_id",
        "folio",
        "codigo_producto",
        "almacen_id",
    ]
"""
    assert SOURCE.count(expected) >= 3
