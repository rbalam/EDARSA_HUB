from pathlib import Path
import ast


SERVER = (
    Path(__file__).resolve().parents[1]
    / "server.py"
)

PERMISSIONS = {
    "create_server": "SERVIDORES_CREAR",
    "get_servers": "SERVIDORES_VER",
    "get_server": "SERVIDORES_VER",
    "update_server": "SERVIDORES_EDITAR",
    "delete_server": "SERVIDORES_ELIMINAR",
}


def _source():
    return SERVER.read_text(encoding="utf-8")


def _tree():
    return ast.parse(_source())


def _function(name):
    for node in ast.walk(_tree()):
        if (
            isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            )
            and node.name == name
        ):
            return node

    raise AssertionError(name)


def _segment(name):
    text = _source()
    node = _function(name)

    segment = ast.get_source_segment(
        text,
        node,
    )

    assert segment is not None
    return segment


def test_servers_crud_usa_rbac_explicito():
    for name, permission in PERMISSIONS.items():
        assert (
            f'require_explicit_permission("{permission}")'
            in _segment(name)
        )


def test_no_role_hardcode_en_mutaciones():
    forbidden = (
        "current_user['role'] not in "
        "['SuperAdministrador', 'Administrador']"
    )

    for name in (
        "create_server",
        "update_server",
        "delete_server",
    ):
        assert forbidden not in _segment(name)


def test_get_server_conserva_scope_individual():
    source = _segment("get_server")

    assert (
        "await validate_server_access_unified("
        "current_user, server_id)"
        in source
    )


def test_listado_conserva_sql_first():
    source = _segment("get_servers")

    assert "prefer_sql=True" in source
    assert "allow_mongo_fallback=False" in source


def test_mutaciones_conservan_no_mongo():
    for name in (
        "create_server",
        "update_server",
        "delete_server",
    ):
        assert "sync_mongo=False" in _segment(name)


def test_update_delete_conservan_core_guard():
    update = _segment("update_server")
    delete = _segment("delete_server")

    assert 'existing.get("tipo_conexion") == "CORE"' in update
    assert "es_editable_ui" in update

    assert 'existing.get("tipo_conexion") == "CORE"' in delete
    assert "es_eliminable_ui" in delete


def test_bypass_test_local_no_se_modifica_en_este_parche():
    source = _segment("create_server")

    assert "skip_connection_test" in source
    assert "'127.0.0.1'" in source
    assert "'localhost'" in source
    assert "'0.0.0.0'" in source
    assert "startswith('TEST_')" in source
