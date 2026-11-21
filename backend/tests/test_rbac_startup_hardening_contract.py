"""Contratos de hardening para inicialización RBAC."""
from __future__ import annotations

import ast
from pathlib import Path

import pymssql

from core.rbac.repository_sql import RBACRepositorySQL


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server.py"
REPOSITORY = ROOT / "core" / "rbac" / "repository_sql.py"


class _CallContextVisitor(ast.NodeVisitor):
    def __init__(self):
        self.stack = []
        self.ensure_contexts = []
        self.runtime_init_contexts = []

    def visit_FunctionDef(self, node):
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, node):
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_Call(self, node):
        func = node.func

        if isinstance(func, ast.Attribute) and func.attr == "ensure_initialized":
            self.ensure_contexts.append(tuple(self.stack))

        if isinstance(func, ast.Name) and func.id == "_initialize_rbac_runtime":
            self.runtime_init_contexts.append(tuple(self.stack))

        self.generic_visit(node)


def test_rbac_seed_is_not_executed_during_server_import():
    tree = ast.parse(SERVER.read_text(encoding="utf-8"))

    visitor = _CallContextVisitor()
    visitor.visit(tree)

    assert visitor.ensure_contexts
    assert all(
        context and context[-1] == "_initialize_rbac_runtime"
        for context in visitor.ensure_contexts
    )

    assert any(
        context and context[-1] == "startup_scheduler"
        for context in visitor.runtime_init_contexts
    )


def test_create_rol_uses_scope_identity_and_explicit_rollback():
    source = REPOSITORY.read_text(encoding="utf-8")
    tree = ast.parse(source)

    create_rol = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "create_rol"
    )

    segment = ast.get_source_segment(source, create_rol)

    assert "SCOPE_IDENTITY()" in segment
    assert "@@IDENTITY" not in segment
    assert "conn.rollback()" in segment


def test_seed_roles_accepts_concurrent_materialization():
    repo = object.__new__(RBACRepositorySQL)

    lookups = {"count": 0}

    def fake_get(_name):
        lookups["count"] += 1
        if lookups["count"] == 1:
            return None
        return {"nombre": "SUPERADMIN"}

    def fake_create(_role):
        raise pymssql.Error("simulated unique race")

    repo.get_rol_by_nombre = fake_get
    repo.create_rol = fake_create

    created = repo.seed_roles([
        {
            "nombre": "SUPERADMIN",
            "descripcion": "SuperAdministrador",
            "permisos": [],
            "nivel_jerarquia": 100,
            "es_sistema": True,
        }
    ])

    assert created == 0
    assert lookups["count"] == 2


def test_seed_roles_does_not_hide_unrelated_database_error():
    repo = object.__new__(RBACRepositorySQL)

    repo.get_rol_by_nombre = lambda _name: None

    def fake_create(_role):
        raise pymssql.Error("unrelated database failure")

    repo.create_rol = fake_create

    try:
        repo.seed_roles([
            {
                "nombre": "SUPERADMIN",
                "descripcion": "SuperAdministrador",
                "permisos": [],
                "nivel_jerarquia": 100,
                "es_sistema": True,
            }
        ])
    except pymssql.Error:
        pass
    else:
        raise AssertionError("database error must propagate")
