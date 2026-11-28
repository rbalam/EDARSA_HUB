"""Fail-closed contract for privileged role mutation endpoints (no SQL access)."""
import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "modules/admin_sql/routes.py"
TARGETS = ("create_role_sql", "update_role_sql", "delete_role_sql")


def _routes():
    module = ast.parse(SOURCE.read_text(encoding="utf-8"))
    return {node.name: node for node in module.body if isinstance(node, ast.AsyncFunctionDef)}


def test_role_mutations_require_explicit_sql_rbac_admin():
    routes = _routes()
    for name in TARGETS:
        fn = routes[name]
        defaults = fn.args.defaults
        assert any(
            isinstance(default, ast.Call)
            and isinstance(default.func, ast.Name)
            and default.func.id == "Depends"
            and default.args
            and isinstance(default.args[0], ast.Call)
            and isinstance(default.args[0].func, ast.Name)
            and default.args[0].func.id == "require_explicit_permission"
            and len(default.args[0].args) == 1
            and isinstance(default.args[0].args[0], ast.Constant)
            and default.args[0].args[0].value == "RBAC_ADMIN"
            for default in defaults
        ), f"{name} must require canonical explicit SQL RBAC_ADMIN"


def test_role_mutations_retain_admin_gate():
    for name in TARGETS:
        fn = _routes()[name]
        assert any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "require_admin"
            for node in ast.walk(fn)
        ), f"{name} must retain its existing admin role gate"


def test_catalog_permissions_global_write_requires_superadmin_sql():
    fn = _routes()["save_permisos_catalogos"]
    source = ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), fn)
    assert 'require_explicit_permission("RBAC_ADMIN")' in source
    assert "SUPERADMIN" in source and "SUPERADMINISTRADOR" in source
    assert "Usuario_RolesAsignacion" in source
    assert "actor_email" in source
    assert "status_code=403" in source
    assert source.index("if not cur.fetchone():") < source.index("UPDATE dbo.Usuario_PermisosCatalogosFlujo")


def test_global_role_mutations_require_sql_superadmin_gate():
    source = SOURCE.read_text(encoding="utf-8")
    routes = _routes()
    for name in TARGETS:
        fn = routes[name]
        body = ast.get_source_segment(source, fn)
        assert "_require_global_role_admin(current_user)" in body, name
        assert body.index("require_admin(current_user)") < body.index("_require_global_role_admin(current_user)")
    module = ast.parse(source)
    helper = next(n for n in module.body if isinstance(n, ast.FunctionDef)
                  and n.name == "_require_global_role_admin")
    helper_source = ast.get_source_segment(source, helper)
    assert "Usuario_RolesAsignacion" in helper_source
    assert "SUPERADMIN" in helper_source
    assert "status_code=403" in helper_source
    assert "status_code=503" in helper_source


def test_user_toggle_enforces_corporate_subset_and_atomic_session_revocation():
    fn = _routes()["toggle_user_activo"]
    source = ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), fn)
    assert 'require_explicit_permission("RBAC_ADMIN")' in source
    assert "Usuario_EmpresasAsignacion" in source
    assert "NOT EXISTS" in source
    assert "FueraAlcance" in source
    assert "Usuario sin alcance corporativo verificable" in source
    assert "SUPERADMIN" in source
    assert "WITH (UPDLOCK, HOLDLOCK)" in source
    assert "UPDATE dbo.Sesiones" in source
    assert source.index("UPDATE dbo.Sesiones") < source.index("conn.commit()")
    assert "conn.rollback()" in source
