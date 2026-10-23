import ast
import re
from pathlib import Path

import pytest


def _load_validator_from_server_source():
    """Carga solo la politica readonly desde server.py sin importar el backend.

    Este test debe ser puro: no requiere variables EDARSAHUB_SQL_*, no abre
    conexiones y no toca ninguna base de datos. A la vez, valida la funcion real
    declarada en server.py para evitar mantener una copia divergente del guard.
    """
    source_path = Path(__file__).with_name("server.py")
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))

    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "BLOCKED_SQL_WORDS" in names:
                selected.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "_validate_readonly_sql":
            selected.append(node)

    if len(selected) != 2:
        raise RuntimeError("READONLY_POLICY_SOURCE_NOT_FOUND")

    module = ast.Module(body=selected, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"re": re}
    exec(compile(module, str(source_path), "exec"), namespace)
    return namespace["_validate_readonly_sql"]


_validate_readonly_sql = _load_validator_from_server_source()


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT TOP 10 * FROM dbo.Ventas",
        "SELECT COUNT(*) AS total FROM dbo.Ventas;",
        "WITH x AS (SELECT 1 AS n) SELECT n FROM x",
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES",
    ],
)
def test_allows_readonly_selects(sql):
    assert _validate_readonly_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO dbo.X(a) VALUES (1)",
        "UPDATE dbo.X SET a = 1",
        "DELETE FROM dbo.X",
        "DROP TABLE dbo.X",
        "ALTER TABLE dbo.X ADD b int",
        "TRUNCATE TABLE dbo.X",
        "CREATE TABLE dbo.X(a int)",
        "EXEC dbo.Algo",
        "SELECT * INTO dbo.Copia FROM dbo.X",
        "SELECT 1; DELETE FROM dbo.X",
        "SELECT 1 -- comentario",
        "SELECT 1 /* comentario */",
        "DECLARE @x int; SELECT @x",
        "USE master; SELECT 1",
    ],
)
def test_blocks_write_or_ambiguous_sql(sql):
    with pytest.raises(ValueError):
        _validate_readonly_sql(sql)
