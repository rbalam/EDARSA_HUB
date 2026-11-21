from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend/src/pages/Servidores.js"


def test_api_factory_is_integrated_in_existing_servers_page():
    text = PAGE.read_text(encoding="utf-8")
    assert 'value="api-factory"' in text
    assert 'data-testid="tab-api-factory"' in text
    assert 'data-testid="api-factory-readonly"' in text
    assert "grid-cols-5" in text


def test_api_factory_ui_consumes_only_certified_readonly_endpoints():
    text = PAGE.read_text(encoding="utf-8")
    block = text.split("// ========== API FACTORY H8 - SOLO LECTURA ==========", 1)[1]
    block = block.split("// ========== ESTADO BITÁCORA ADMIN CORE ==========", 1)[0]
    assert "api.get('/integrations-center/api-factory/overview')" in block
    assert "api.get('/integrations-center/api-factory/apis')" in block
    assert "api.get('/integrations-center/api-factory/consumers')" in block
    assert "api.post(" not in block
    assert "api.put(" not in block
    assert "api.patch(" not in block
    assert "api.delete(" not in block


def test_api_factory_ui_has_no_secret_or_writer_controls():
    text = PAGE.read_text(encoding="utf-8")
    ui = text.split('{/* Tab: API Factory H8 - solo lectura */}', 1)[1]
    ui = ui.split('{/* Tab: Vtiger CRM */}', 1)[0]
    assert "CredentialReference" not in ui
    assert "credential_reference" not in ui
    assert "Crear API" not in ui
    assert "Publicar" not in ui
    assert "Revocar" not in ui
    assert "H8 · READ ONLY" in ui
