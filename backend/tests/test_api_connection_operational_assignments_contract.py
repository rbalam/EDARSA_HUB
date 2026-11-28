from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "backend" / "modules" / "api_connections" / "assignment_repository.py"
ROUTES = ROOT / "backend" / "modules" / "api_connections" / "routes.py"


def test_assignment_repository_uses_canonical_tables_and_writer():
    text = REPO.read_text(encoding="utf-8")
    assert "Sistema_EmpresasServidores" in text
    assert "Servidores_Conexiones" in text
    assert "Sistema_Empresas" in text
    assert "open_validated_writer_connection" in text
    assert "SET TRANSACTION ISOLATION LEVEL SERIALIZABLE" in text
    assert "tipo_conexion = 'API_LOCAL'" in text


def test_assignment_removal_is_soft_not_delete():
    text = REPO.read_text(encoding="utf-8").upper()
    assert "SET ACTIVO = 0" in text
    assert "DELETE FROM DBO.SISTEMA_EMPRESASSERVIDORES" not in text


def test_assignment_routes_are_explicitly_admin_guarded():
    text = ROUTES.read_text(encoding="utf-8")
    assert 'require_explicit_permission("RBAC_ADMIN")' in text
    assert '@router.get("/{api_id}/assignments")' in text
    assert '@router.post("/{api_id}/assignments")' in text
    assert '@router.delete("/{api_id}/assignments/{empresa_id}/{rol_conexion}")' in text
