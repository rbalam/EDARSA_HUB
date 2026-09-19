from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
DDL=ROOT/'backend'/'database'/'migrations'/'20260908_catalogo_ampliado_gobierno_core.sql'
def text(): return DDL.read_text(encoding='utf-8')
def test_exact_11_tables():
    got=set(re.findall(r'CREATE TABLE dbo\.(Gobierno_[A-Za-z0-9_]+)',text(),flags=re.I))
    expected={'Gobierno_EmpresaConfiguracion','Gobierno_Persona','Gobierno_PersonaVinculo','Gobierno_RolCorporativoCatalogo','Gobierno_PersonaEmpresaRol','Gobierno_TipoDocumento','Gobierno_Documento','Gobierno_DocumentoVersion','Gobierno_DocumentoMovimiento','Gobierno_AlertaRegla','Gobierno_AlertaEvento'}
    assert got==expected
def test_no_parallel_masters_or_engines():
    low=text().lower()
    for token in ['create table dbo.sistema_empresas','create table dbo.usuario_catalogo','create table dbo.cliente_catalogo','create table dbo.proveedor_catalogo','create table dbo.cliente_contactos','create table dbo.proveedor_contactos','create table dbo.tareas_inventario','create table dbo.operativo_notificaciones_log','create table dbo.sistema_tareas']:
        assert token not in low
def test_typed_person_links():
    t=text()
    for token in ['REFERENCES dbo.Usuario_Catalogo(UsuarioID)','REFERENCES dbo.Cliente_Catalogo(ClienteID)','REFERENCES dbo.Proveedor_Catalogo(ProveedorID)','REFERENCES dbo.Cliente_Contactos(ContactoClienteID)','REFERENCES dbo.Proveedor_Contactos(ContactoID)','CK_GobPV_UnDestino']:
        assert token in t
def test_idempotent_guards():
    t=text()
    for name in re.findall(r'CREATE TABLE dbo\.(Gobierno_[A-Za-z0-9_]+)',t,flags=re.I):
        assert f"OBJECT_ID('dbo.{name}','U') IS NULL" in t
def test_no_business_dml_or_seeds():
    cleaned=re.sub(r'/\*.*?\*/',' ',text(),flags=re.S).lower()
    for token in (' merge ',' insert ',' update ',' delete '): assert token not in f' {cleaned} '
def test_alerts_reference_external_delivery():
    t=text(); assert 'TareaReferencia VARCHAR(50) NULL' in t; assert 'NotificacionReferencia VARCHAR(50) NULL' in t; assert 'FOREIGN KEY(TareaReferencia)' not in t; assert 'FOREIGN KEY(NotificacionReferencia)' not in t
