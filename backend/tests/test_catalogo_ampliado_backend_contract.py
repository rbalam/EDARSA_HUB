from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / "backend/modules/catalogo_ampliado/routes.py"
REPO = ROOT / "backend/modules/catalogo_ampliado/repository.py"
SCHEMAS = ROOT / "backend/modules/catalogo_ampliado/schemas.py"


def test_backend_is_sql_first_and_has_no_mongo():
    text = (ROUTES.read_text() + REPO.read_text() + SCHEMAS.read_text()).lower()
    assert "mongo" not in text
    assert "core.sql_first.db" in REPO.read_text()


def test_activation_is_per_company_and_fail_closed():
    text = ROUTES.read_text()
    assert '/empresas/{empresa_id}/configuracion' in text
    assert 'CatalogoLegalAmpliadoActivo' in text
    assert '_assert_empresa_activa(empresa_id)' in text


def test_people_are_reused_by_links_not_embedded_duplicates():
    text = REPO.read_text()
    assert "Gobierno_PersonaVinculo" in text
    assert "TipoEntidad" in text and "EntidadClave" in text
    assert "NombreProveedor" not in text
    assert "PasswordHash" not in text


def test_preventive_endpoint_is_forward_looking():
    text = REPO.read_text()
    assert "DiasRestantes" in text
    assert "v.FechaVencimiento>=CAST(GETDATE() AS date)" in text
    assert "DATEADD(DAY,?,CAST(GETDATE() AS date))" in text


def test_document_owner_is_normalized_by_route():
    text = ROUTES.read_text()
    assert 'data["propietario_tipo"] == "EMPRESA"' in text
    assert 'data["propietario_tipo"] == "PERSONA"' in text
    assert 'persona_empresa_rol_id requerido' in text
