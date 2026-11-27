"""Security regression for SQL-backed catalog workflow permissions (no live SQL)."""
import ast
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1] / "modules"
ROUTES = {
    "catalogos_workflow_compat/routes.py": (
        "compat_put_catalogo_niveles",
        "compat_get_permisos_catalogo",
        "compat_post_permisos_catalogo",
    ),
    "catalogos_workflow_sql/routes.py": (
        "put_catalogo_niveles",
        "get_permisos_catalogo",
        "post_permisos_catalogo",
    ),
}


def _route_functions(path):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    return {
        node.name: node for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef)
    }


@pytest.mark.parametrize("path,names", list(ROUTES.items()))
def test_six_privileged_routes_require_explicit_sql_rbac_admin(path, names):
    functions = _route_functions(path)
    for name in names:
        fn = functions[name]
        assert any(
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "Depends"
            and len(value.args) == 1
            and isinstance(value.args[0], ast.Call)
            and isinstance(value.args[0].func, ast.Name)
            and value.args[0].func.id == "require_explicit_permission"
            and len(value.args[0].args) == 1
            and isinstance(value.args[0].args[0], ast.Constant)
            and value.args[0].args[0].value == "RBAC_ADMIN"
            for value in fn.args.defaults
        ), f"{path}:{name} must require canonical SQL RBAC_ADMIN"


def test_self_service_catalog_permissions_remain_authenticated_not_admin_only():
    functions = _route_functions("catalogos_workflow_compat/routes.py")
    fn = functions["compat_get_mis_permisos_catalogos"]
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "require_explicit_permission"
        for node in ast.walk(fn)
    )
    assert any(
        isinstance(node, ast.Name) and node.id == "get_current_user"
        for node in ast.walk(fn)
    )


class _DenyCursor:
    def execute(self, *_args, **_kwargs):
        pass

    def fetchone(self):
        return None


class _DenyConn:
    def cursor(self):
        return _DenyCursor()

    def close(self):
        pass


@pytest.mark.parametrize("method,path", [
    ("PUT", "/api/sistema/catalogos/test/niveles"),
    ("GET", "/api/sistema/catalogos/permisos/41"),
    ("POST", "/api/sistema/permisos-catalogos"),
    ("PUT", "/api/sql/catalogos-workflow/config/test/niveles"),
    ("GET", "/api/sql/catalogos-workflow/permisos/usuario/41"),
    ("POST", "/api/sql/catalogos-workflow/permisos"),
])
def test_privileged_route_denies_missing_token_and_missing_sql_grant(monkeypatch, method, path):
    from core.security import get_current_user
    from core.rbac import middleware as rbac
    from core.sql_first import db as sql_db
    from modules.catalogos_workflow_compat import routes as compat
    from modules.catalogos_workflow_sql import routes as workflow_sql

    app = FastAPI()
    app.include_router(compat.router)
    app.include_router(workflow_sql.router)
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "41", "UsuarioID": 41, "email": "test@example.invalid", "role": "SUPERADMIN"
    }
    monkeypatch.setattr(rbac, "verify_token", lambda _token: {
        "user_id": "41", "email": "test@example.invalid", "role": "SUPERADMIN"
    })
    monkeypatch.setattr(sql_db, "get_sql_connection", lambda: _DenyConn())
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.request(method, path, json={} if method in ("PUT", "POST") else None)
        assert response.status_code == 401, (method, path, response.text)
        response = client.request(
            method, path,
            headers={"Authorization": "Bearer test-token"},
            json={} if method in ("PUT", "POST") else None,
        )
        assert response.status_code == 403, (method, path, response.text)


def test_self_service_catalog_route_does_not_require_sql_admin(monkeypatch):
    from core.security import get_current_user
    from core.sql_first import db as sql_db
    from modules.catalogos_workflow_compat import routes as compat

    app = FastAPI()
    app.include_router(compat.router)
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "41", "UsuarioID": 41, "email": "test@example.invalid", "role": "USER"
    }
    monkeypatch.setattr(sql_db, "get_sql_connection", lambda: _DenyConn())
    monkeypatch.setattr(compat.repo, "get_mis_permisos_catalogos", lambda usuario_id: {"usuario_id": usuario_id})

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/sistema/mis-permisos-catalogos")
        assert response.status_code == 200, response.text
        assert response.json()["usuario_id"] == 41
