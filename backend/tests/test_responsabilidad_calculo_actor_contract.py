"""Contract regression for trusted identity on responsibility calculation.

Isolates the route functions to avoid touching SQL, HTTP providers or Production.
"""
import ast
import asyncio
import inspect
from pathlib import Path

import pytest


_ROUTE = (
    Path(__file__).resolve().parents[1]
    / "modules"
    / "fase2_operativo"
    / "routes"
    / "responsabilidad_routes.py"
)


class FakeHTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


class FakeResponsabilidadService:
    def __init__(self, db):
        self.db = db

    async def calcular_responsabilidad(self, **kwargs):
        return kwargs


def _isolated_calcular():
    tree = ast.parse(_ROUTE.read_text(encoding="utf-8"))
    selected = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in {
            "_get_authenticated_responsabilidad_actor",
            "calcular_responsabilidad",
        }
    ]
    assert len(selected) == 2
    for node in selected:
        node.decorator_list = []
        node.returns = None
    ns = {
        "Query": lambda *args, **kwargs: False,
        "Depends": lambda dependency: None,
        "require_explicit_permission": lambda code: None,
        "get_role_code": lambda user: user.get("role", ""),
        "get_db": object,
        "ResponsabilidadService": FakeResponsabilidadService,
        "HTTPException": FakeHTTPException,
    }
    for name in (
        "ModuloDesactivadoError",
        "WorkflowNoEncontradoError",
        "CalculoYaExisteError",
        "SinDiferenciasError",
    ):
        ns[name] = type(name, (Exception,), {})
    module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    exec(compile(module, str(_ROUTE), "exec"), ns)
    return ns["calcular_responsabilidad"]


def test_calcular_no_longer_accepts_caller_usuario_id():
    fn = _isolated_calcular()
    assert "usuario_id" not in inspect.signature(fn).parameters


def test_calcular_audits_authenticated_actor_not_spoofed_identity():
    fn = _isolated_calcular()
    result = asyncio.run(
        fn(
            "workflow-test",
            False,
            {"id": "trusted-user", "user_id": "untrusted-alias", "role": "SUPERADMIN"},
        )
    )
    assert result["workflow_id"] == "workflow-test"
    assert result["usuario_id"] == "trusted-user"


def test_calcular_missing_identity_fails_closed_with_403():
    fn = _isolated_calcular()
    with pytest.raises(FakeHTTPException) as exc:
        asyncio.run(fn("workflow-test", False, {"role": "SUPERADMIN"}))
    assert exc.value.status_code == 403
