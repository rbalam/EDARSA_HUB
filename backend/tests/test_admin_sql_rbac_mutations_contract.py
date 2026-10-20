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
