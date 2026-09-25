from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def text(path): return (ROOT/path).read_text(encoding='utf-8')


def test_router_registered_under_api():
    server=text('backend/server.py')
    assert 'from modules.catalogo_ampliado.routes import router as catalogo_ampliado_router' in server
    assert 'api_router.include_router(catalogo_ampliado_router)' in server


def test_repository_is_sql_first_and_typed_links():
    repo=text('backend/modules/catalogo_ampliado/repository.py')
    assert 'core.sql_first.db' in repo
    assert 'Gobierno_PersonaVinculo' in repo
    assert 'TipoEntidad' not in repo
    assert 'EntidadClave' not in repo
    for name in ('UsuarioID','ClienteID','ProveedorID','ContactoClienteID','ContactoProveedorID'):
        assert name in repo
    assert 'UsuarioAltaID' in repo and 'UsuarioActualizacionID' in repo
    assert 'mongo' not in repo.lower()


def test_routes_fail_closed_rbac_and_activation():
    routes=text('backend/modules/catalogo_ampliado/routes.py')
    assert 'has_full_access' in routes
    assert 'get_current_user' in routes
    assert '_sql_usuario_id' in routes
    assert 'CatalogoLegalAmpliadoActivo' in routes
    assert "sum(v is not None for v in targets)!=1" in routes
    assert "status_code=403" in routes
    assert "status_code=409" in routes


def test_document_versions_are_append_only_and_kardexed():
    repo=text('backend/modules/catalogo_ampliado/repository.py')
    assert 'MAX(NumeroVersion)' in repo
    assert 'UPDLOCK,HOLDLOCK' in repo
    assert "'NUEVA_VERSION'" in repo
    assert 'UPDATE dbo.Gobierno_DocumentoVersion' not in repo
    assert 'DELETE FROM dbo.Gobierno_DocumentoVersion' not in repo


def test_no_worker_or_production_contract_leak():
    routes=text('backend/modules/catalogo_ampliado/routes.py')
    repo=text('backend/modules/catalogo_ampliado/repository.py')
    combined=routes+repo
    assert 'Edarsahub_Produccion' not in combined
    assert 'tools/mirror_sync' not in combined
