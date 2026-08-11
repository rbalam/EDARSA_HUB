from pathlib import Path
import ast


ROOT = Path("/app")
SERVER = ROOT / "backend/server.py"
SECURITY = ROOT / "backend/core/security.py"


def _get_function_source(path: Path, name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ) and node.name == name:
            return ast.get_source_segment(source, node) or ""

    raise AssertionError(f"{name} no encontrado")


def test_get_sucursales_uses_canonical_access_context():
    source = _get_function_source(
        SERVER,
        "get_sucursales",
    )

    assert "resolve_user_access_context(current_user)" in source
    assert "has_server_access(context, server_id)" in source
    assert "context.sucursales_por_server.get" in source


def test_get_sucursales_is_fail_closed_without_branch_scope():
    source = _get_function_source(
        SERVER,
        "get_sucursales",
    )

    assert "if not sucursales_permitidas:" in source
    assert "sucursales_filtradas = []" in source


def test_get_sucursales_does_not_call_legacy_filter():
    source = _get_function_source(
        SERVER,
        "get_sucursales",
    )

    assert "filter_sucursales_by_permissions(" not in source


def test_get_sucursales_has_no_live_pos_query():
    source = _get_function_source(
        SERVER,
        "get_sucursales",
    )

    assert "execute_sql_query(" not in source
    assert "Sc_Cve_Sucursal" not in source
    assert "Al_Cve_Almacen" not in source


def test_server_does_not_import_dead_server_helpers():
    source = SERVER.read_text(encoding="utf-8")

    assert "    user_has_server_access,\n" not in source
    assert "    filter_servers_by_permissions,\n" not in source


def test_legacy_filter_still_exists_but_has_no_server_consumer():
    security_source = SECURITY.read_text(
        encoding="utf-8",
    )

    server_source = SERVER.read_text(
        encoding="utf-8",
    )

    assert (
        "def filter_sucursales_by_permissions"
        in security_source
    )

    assert (
        "filter_sucursales_by_permissions("
        not in _get_function_source(
            SERVER,
            "get_sucursales",
        )
    )

    assert (
        "filter_sucursales_by_permissions,"
        not in server_source
    )
