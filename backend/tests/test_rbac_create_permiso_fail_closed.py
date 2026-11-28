"""Regression contract: RBAC permission creation must never claim false SQL persistence."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_PATH = ROOT / "backend/core/rbac/repository.py"


def _create_permiso_method():
    module = ast.parse(REPOSITORY_PATH.read_text(encoding="utf-8"))
    repository = next(
        node for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "RBACRepository"
    )
    method = next(
        node for node in repository.body
        if isinstance(node, ast.FunctionDef) and node.name == "create_permiso"
    )
    # Compile only the real method; avoid importing unrelated application/SQL modules.
    isolated = ast.Module(
        body=[ast.ClassDef(
            name="IsolatedRepository", bases=[], keywords=[],
            body=[method], decorator_list=[]
        )],
        type_ignores=[],
    )
    namespace = {"logger": __import__("logging").getLogger(__name__)}
    exec(compile(ast.fix_missing_locations(isolated), str(REPOSITORY_PATH), "exec"), namespace)
    return namespace["IsolatedRepository"]


def test_create_permiso_rejects_false_success_without_sql_write():
    repository = _create_permiso_method()()
    payload = {"codigo": "TEST_CREAR", "activo": False}
    with pytest.raises(NotImplementedError, match="CREATE_PERMISO_NO_PERSISTENCE"):
        repository.create_permiso(payload)
    assert payload == {"codigo": "TEST_CREAR", "activo": False}


def test_create_permiso_has_no_success_return_path():
    module = ast.parse(REPOSITORY_PATH.read_text(encoding="utf-8"))
    cls = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == "RBACRepository")
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "create_permiso")
    assert not any(isinstance(n, ast.Return) for n in ast.walk(method))
    assert any(isinstance(n, ast.Raise) for n in ast.walk(method))
