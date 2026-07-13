from __future__ import annotations

import ast
import re
from pathlib import Path


TARGET = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validacion_propinas_tpv.py"
)


def _call_name(node: ast.Call) -> str:
    try:
        return ast.unparse(node.func)
    except Exception:
        return ""


def test_uses_canonical_connection_chain():
    source = TARGET.read_text(encoding="utf-8")

    required = {
        "list_unidades_negocio",
        "get_server_for_unidad",
        "get_server_connection_info",
        "get_external_sql_connection",
    }

    for name in required:
        assert name in source

    forbidden = {
        "pytds.connect",
        "pymssql.connect",
        "pyodbc.connect",
    }

    for name in forbidden:
        assert name not in source


def test_has_no_connection_environment_fallbacks():
    source = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(TARGET))

    found = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        name = _call_name(node)

        if name in {
            "os.getenv",
            "os.environ.get",
        }:
            found.append(
                (
                    name,
                    getattr(node, "lineno", None),
                )
            )

    assert found == []


def test_has_no_ipv4_or_literal_connection_config():
    source = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(TARGET))

    assert re.search(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        source,
    ) is None

    sensitive_keys = {
        "host",
        "server",
        "port",
        "database",
        "database_name",
        "user",
        "username",
        "password",
        "passwd",
        "pwd",
    }

    findings = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue

        for key_node, value_node in zip(
            node.keys,
            node.values,
        ):
            if not (
                isinstance(key_node, ast.Constant)
                and isinstance(key_node.value, str)
            ):
                continue

            key = key_node.value.lower()

            if key not in sensitive_keys:
                continue

            if (
                isinstance(value_node, ast.Constant)
                and value_node.value not in {
                    None,
                    "",
                }
            ):
                findings.append(
                    (
                        key,
                        getattr(value_node, "lineno", None),
                    )
                )

    assert findings == []
