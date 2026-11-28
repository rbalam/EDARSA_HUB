"""Isolated behavioral tests for SQL catalog-permission writes.

These tests execute the real endpoint body with an in-memory SQL cursor double.
They do not claim to be integration tests against EDARSAHUB SQL Server.
"""
import ast
import asyncio
from pathlib import Path

import pytest
from fastapi import HTTPException

SOURCE = Path(__file__).resolve().parents[1] / "modules/admin_sql/routes.py"


class Cursor:
    def __init__(self, *, target=True, superadmin=True, fail_on_write=False):
        self.target = target
        self.superadmin = superadmin
        self.fail_on_write = fail_on_write
        self.statements = []
        self.last_sql = ""
        self.rowcount = 1

    def execute(self, sql, params=()):
        self.last_sql = sql
        self.statements.append(sql)
        if self.fail_on_write and "UPDATE dbo.Usuario_PermisosCatalogosFlujo" in sql:
            raise RuntimeError("simulated SQL failure")

    def fetchone(self):
        if "SELECT TOP 1 UsuarioID" in self.last_sql:
            return {"UsuarioID": 42} if self.target else None
        if "SELECT TOP 1 1 AS Autorizado" in self.last_sql:
            return {"Autorizado": 1} if self.superadmin else None
        return None


class Connection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self, **kwargs):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def endpoint(connection):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef)
                and n.name == "save_permisos_catalogos")
    # Drop FastAPI decorators and injected dependency defaults only in the test harness.
    node.decorator_list = []
    node.args.defaults = [ast.Constant(value=None) for _ in node.args.defaults]
    namespace = {
        "Depends": lambda x: None,
        "get_current_user": lambda: None,
        "require_explicit_permission": lambda x: None,
        "HTTPException": HTTPException,
        "require_admin": lambda user: None,
        "get_edarsahub_pymssql_connection": lambda **kwargs: connection,
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 str(SOURCE), "exec"), namespace)
    return namespace["save_permisos_catalogos"]


def invoke(connection, email="admin@example.test"):
    return asyncio.run(endpoint(connection)(
        {"user_id": "42", "catalogos_permitidos": []},
        {"email": email, "role": "ADMIN"},
    ))


def test_scoped_admin_denied_without_any_write():
    cursor = Cursor(superadmin=False)
    conn = Connection(cursor)
    with pytest.raises(HTTPException) as exc:
        invoke(conn)
    assert exc.value.status_code == 403
    assert conn.commits == 0 and conn.rollbacks == 1 and conn.closed
    assert not any("UPDATE dbo." in sql or "INSERT INTO dbo." in sql for sql in cursor.statements)


def test_missing_actor_identity_denied_before_write():
    cursor = Cursor()
    conn = Connection(cursor)
    with pytest.raises(HTTPException) as exc:
        invoke(conn, email="")
    assert exc.value.status_code == 403
    assert conn.commits == 0 and conn.rollbacks == 1


def test_sql_write_failure_rolls_back_and_does_not_claim_success():
    cursor = Cursor(fail_on_write=True)
    conn = Connection(cursor)
    with pytest.raises(HTTPException) as exc:
        invoke(conn)
    assert exc.value.status_code == 500
    assert conn.commits == 0 and conn.rollbacks == 1 and conn.closed


def test_authorized_superadmin_commits_once():
    cursor = Cursor()
    conn = Connection(cursor)
    result = invoke(conn)
    assert result["success"] is True
    assert conn.commits == 1 and conn.rollbacks == 0 and conn.closed
