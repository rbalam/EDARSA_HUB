"""Contrato de ruta Caja V1 sin dependencias de SQL ni envios."""
import ast
from pathlib import Path


def test_bootstrap_requires_canonical_auth_and_rbac():
    path = Path(__file__).resolve().parents[1] / "modules/finanzas/incidencias_caja_routes.py"
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    function = next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "obtener_bootstrap_cajas"
    )
    assert any(
        isinstance(d, ast.Call) and isinstance(d.func, ast.Name)
        and d.func.id == "Depends"
        for arg in function.args.defaults for d in [arg]
    )
    assert "RBACSQLService.get_permission_scope_by_code" in text
    assert '"registro_habilitado": False' in text
    assert '"motivos": []' in text
    assert "registrar_expediente_v1" not in text
    comercial = (Path(__file__).resolve().parents[1] / "modules/comercial/__init__.py").read_text(encoding="utf-8")
    assert comercial.count("router.include_router(cajas_router)") == 1
    assert comercial.count("from modules.finanzas.incidencias_caja_routes import router as cajas_router") == 1
    assert not any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "post" for d in n.decorator_list)
        for n in tree.body
    )


def test_bootstrap_http_rbac_fail_closed(monkeypatch):
    """HTTP hermetico; no SQL real, cookies reales ni escrituras."""
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    from modules.finanzas import incidencias_caja_routes as cajas

    app = FastAPI()
    app.include_router(cajas.router)
    state = {"user": {"_sql_usuario_id": 17}, "permission": {"permitido": True}}

    def current_user():
        if state["user"] is None:
            raise HTTPException(status_code=401, detail="NO_AUTENTICADO")
        return state["user"]

    def permission(user_id, code):
        assert user_id == 17
        assert code == cajas.CAJAS_INCIDENCIAS_CREAR
        value = state["permission"]
        if isinstance(value, Exception):
            raise value
        return value

    app.dependency_overrides[cajas.get_current_user] = current_user
    monkeypatch.setattr(cajas.RBACSQLService, "get_permission_scope_by_code", permission)

    with TestClient(app) as client:
        url = "/comercial/cajas/bootstrap"
        state["user"] = None
        assert client.get(url).status_code == 401
        state["user"] = {"_sql_usuario_id": 17}
        state["permission"] = {"permitido": False}
        assert client.get(url).status_code == 403
        state["permission"] = RuntimeError("SQL unavailable")
        assert client.get(url).status_code == 503
        state["permission"] = {"permitido": True}
        response = client.get(url)
        assert response.status_code == 200
        payload = response.json()
        assert payload["autorizado"] is False
        assert payload["registro_habilitado"] is False
        assert payload["motivos"] == []
        assert payload["contexto"] is None
        assert client.post(url, json={}).status_code == 405
