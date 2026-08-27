from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIG = ROOT / 'backend' / 'database' / 'migrations' / '20260827_034_catalogo_ampliado_core.sql'
CONTRACT = ROOT / 'docs' / 'architecture' / 'CATALOGO_AMPLIADO_V1_CANONICAL_CONTRACT.md'


def test_schema_is_additive_canonical_and_atomic():
    sql = MIG.read_text(encoding='utf-8')
    assert "OBJECT_ID('dbo.Sistema_Empresas','U')" in sql
    assert 'CREATE TABLE dbo.Gobierno_EmpresaConfiguracion' in sql
    assert 'CREATE TABLE dbo.Gobierno_Persona' in sql
    assert 'CREATE TABLE dbo.Gobierno_PersonaVinculo' in sql
    assert 'CREATE TABLE dbo.Gobierno_PersonaEmpresaRol' in sql
    assert 'CREATE TABLE dbo.Gobierno_Documento' in sql
    assert 'CREATE TABLE dbo.Gobierno_DocumentoVersion' in sql
    assert 'CREATE TABLE dbo.Gobierno_DocumentoMovimiento' in sql
    assert 'CREATE TABLE dbo.Gobierno_AlertaRegla' in sql
    assert 'CREATE TABLE dbo.Gobierno_AlertaEvento' in sql
    assert 'REFERENCES dbo.Sistema_Empresas(EmpresaID)' in sql
    assert 'DROP TABLE' not in sql.upper()
    assert 'MONGO' not in sql.upper()


def test_persona_links_do_not_copy_external_master_payloads():
    sql = MIG.read_text(encoding='utf-8')
    start = sql.index("CREATE TABLE dbo.Gobierno_PersonaVinculo")
    end = sql.index("IF OBJECT_ID('dbo.Gobierno_RolCorporativoCatalogo'", start)
    link = sql[start:end]
    assert 'TipoEntidad' in link and 'EntidadClave' in link
    for forbidden in ('RazonSocial', 'NombreProveedor', 'EmailCliente', 'PasswordHash'):
        assert forbidden not in link


def test_document_owner_is_exactly_one_atomic_subject():
    sql = MIG.read_text(encoding='utf-8')
    assert "PropietarioTipo='PERSONA' AND PersonaID IS NOT NULL AND EmpresaID IS NULL AND PersonaEmpresaRolID IS NULL" in sql
    assert "PropietarioTipo='EMPRESA' AND EmpresaID IS NOT NULL AND PersonaID IS NULL AND PersonaEmpresaRolID IS NULL" in sql
    assert "PropietarioTipo='RELACION' AND PersonaEmpresaRolID IS NOT NULL AND PersonaID IS NULL AND EmpresaID IS NULL" in sql


def test_versions_and_alerts_are_idempotent_auditable_and_preventive():
    sql = MIG.read_text(encoding='utf-8')
    assert 'UQ_GobDocVer_Num UNIQUE(DocumentoID,NumeroVersion)' in sql
    assert 'UQ_GobDocVer_Hash UNIQUE(DocumentoID,SHA256)' in sql
    assert 'Gobierno_DocumentoMovimiento' in sql
    assert 'DiasAntes BETWEEN 0 AND 3650' in sql
    assert 'UQ_GobAE_Idem UNIQUE(DocumentoVersionID,AlertaReglaID,FechaObjetivo)' in sql


def test_contract_reuses_existing_task_notification_and_whatsapp_capabilities():
    text = CONTRACT.read_text(encoding='utf-8')
    assert 'Tareas_Inventario' in text
    assert 'Operativo_Notificaciones_Log' in text
    assert 'TwilioWhatsAppProvider' in text
    assert 'no se crea un segundo centro de tareas' in text
