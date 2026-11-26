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
