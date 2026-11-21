from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / "backend" / "modules" / "api_connections" / "routes.py"
REPOSITORY = ROOT / "backend" / "modules" / "api_connections" / "repository.py"
SERVIDORES = ROOT / "frontend" / "src" / "pages" / "Servidores.js"


def test_api_write_schemas_do_not_accept_legacy_business_aliases():
    text = ROUTES.read_text(encoding="utf-8")
    create_block = text.split("class ApiConnectionCreate", 1)[1].split(
        "class ApiConnectionUpdate", 1
    )[0]
    update_block = text.split("class ApiConnectionUpdate", 1)[1].split(
        "class ApiOperationalAssignmentRequest", 1
    )[0]
    for legacy in ("servidor_padre", "servidor_padre_id", "sucursal_destino", "hora_replica"):
        assert legacy not in create_block
        assert legacy not in update_block


def test_api_create_does_not_store_business_aliases_in_sql_fields():
    text = REPOSITORY.read_text(encoding="utf-8")
    assert "data.get(\"servidor_padre\"" not in text
    assert "data.get(\"sucursal_destino\"" not in text
    assert "hora_replica = data.get(" not in text
    assert "NULL,\n        NULL,\n        NULL," in text


def test_api_ui_has_no_legacy_business_aliases_and_uses_assignments():
    text = SERVIDORES.read_text(encoding="utf-8")
    assert "fetchUnidadesNegocio" in text
    assert "Asignación operativa (opcional)" in text
    assert "/assignments" in text
    assert "servidor_padre" not in text
    assert "sucursal_destino" not in text
    assert "hora_replica" not in text
    assert "Servidor Padre" not in text
    assert "Sucursal Destino" not in text
    assert "Hora de Réplica" not in text
