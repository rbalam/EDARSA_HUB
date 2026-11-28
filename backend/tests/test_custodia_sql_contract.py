from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL = ROOT / "backend" / "database" / "migrations" / "20260917_2055_custodia_resguardos_core.sql"


def _text() -> str:
    return SQL.read_text(encoding="utf-8")


def test_uses_certified_canonical_contracts():
    text = _text()
    for token in [
        "dbo.RH_Colaboradores_Expediente(ColaboradorID)",
        "dbo.RH_Cat_Puestos(PuestoID)",
        "dbo.Producto_Catalogo(ProductoID)",
        "dbo.ActivoFijo_Activos(ActivoID)",
        "dbo.Sistema_Empresas(EmpresaID)",
        "dbo.Unidades_Negocio(id)",
        "dbo.Sistema_Sucursales(SucursalID)",
        "dbo.Usuario_Catalogo(UsuarioID)",
        "dbo.Gobierno_Documento(DocumentoID)",
        "dbo.RH_Nomina_Detalle(NominaDetalleID)",
    ]:
        assert token in text


def test_minimal_tables_present():
    low = _text().lower()
    for token in [
        "create table dbo.custodia_recurso",
        "create table dbo.custodia_resguardo",
        "create table dbo.custodia_movimiento",
        "create table dbo.custodia_devolucion",
        "create table dbo.custodia_incidencia",
        "create table dbo.custodia_cargopropuesto",
        "create table dbo.rh_uniformepolitica",
        "create table dbo.rh_uniformepoliticadetalle",
    ]:
        assert token in low


def test_no_parallel_canonical_masters_or_uniform_stock():
    low = _text().lower()
    for token in [
        "create table dbo.rh_colaboradores_expediente",
        "create table dbo.producto_catalogo",
        "create table dbo.activofijo_activos",
        "create table dbo.sistema_empresas",
        "create table dbo.unidades_negocio",
        "create table dbo.sistema_sucursales",
        "create table dbo.usuario_catalogo",
        "create table dbo.gobierno_documento",
        "create table dbo.rh_nomina_detalle",
        "create table dbo.rh_uniformeexistencias",
        "create table dbo.rh_uniformemovimientos",
        "create table dbo.rh_uniformetallas",
    ]:
        assert token not in low


def test_idempotency_contract():
    text = _text()
    for token in [
        "UQ_Custodia_Resguardo_Idempotency",
        "UQ_Custodia_Movimiento_Idempotency",
        "UQ_Custodia_Devolucion_Idempotency",
        "UQ_Custodia_Incidencia_Idempotency",
        "UQ_Custodia_Cargo_Idempotency",
    ]:
        assert token in text


def test_asset_is_exclusive_by_canonical_asset_id():
    text = _text()
    assert "UX_Custodia_Recurso_ActivoID" in text
    assert "WHERE ActivoID IS NOT NULL" in text


def test_uniform_policy_reuses_product_and_position():
    text = _text()
    assert "REFERENCES dbo.RH_Cat_Puestos(PuestoID)" in text
    assert "REFERENCES dbo.Producto_Catalogo(ProductoID)" in text


def test_cargo_proposal_links_payroll_but_does_not_create_it():
    low = _text().lower()
    assert "references dbo.rh_nomina_detalle(nominadetalleid)" in low
    assert "create table dbo.rh_nomina " not in low
    assert "create table dbo.rh_cat_conceptosnomina" not in low
