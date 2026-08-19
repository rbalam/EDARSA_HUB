import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / "backend/modules/admin_sql/routes.py"


def _source():
    return ROUTES.read_text(encoding="utf-8")


def _function_source(name):
    tree = ast.parse(_source())
    lines = _source().splitlines()

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return "\n".join(lines[node.lineno - 1:node.end_lineno])

    raise AssertionError(f"Funcion no encontrada: {name}")


def test_get_roles_preserves_module_action_granularity():
    src = _function_source("get_roles")

    assert 'p.get("AccionID")' in src
    assert '"modulo_id": str(modulo_id)' in src
    assert '"accion_id": int(accion_id)' in src
    assert '"accion_codigo": accion_codigo' in src


def test_get_roles_does_not_reduce_permissions_to_module_strings():
    src = _function_source("get_roles")

    assert 'pmap.setdefault(rid, set()).add(str(modulo_id))' not in src
    assert 'r["permisos"] = sorted(' in src
    assert 'p["modulo_id"]' in src
    assert 'p["accion_id"]' in src


def test_update_role_accepts_module_action_objects():
    src = _function_source("update_role_sql")

    assert 'p.get("modulo_id")' in src
    assert 'p.get("accion_id")' in src
    assert 'p.get("accion_codigo")' in src


def test_update_role_writes_canonical_permission_table():
    src = _function_source("update_role_sql")

    assert "dbo.Usuario_PermisosRolModulo" in src
    assert "dbo.Usuario_Modulos" in src
    assert "dbo.Usuario_Acciones" in src


def test_update_role_uses_exact_module_action_key():
    src = _function_source("update_role_sql")

    compact = " ".join(src.split())

    assert (
        "WHERE RolID = %s AND ModuloID = %s AND AccionID = %s"
        in compact
    )


def test_no_parallel_rbac_permission_table_in_role_writer():
    src = _function_source("update_role_sql")

    assert "Sistema_RBAC_" not in src
    assert "sec_permisos" not in src
    assert "sec_roles" not in src
    assert "Mongo" not in src


def test_get_roles_permission_query_selects_action_id():
    """
    El GET /roles debe recuperar AccionID desde la fuente canónica.
    Sin AccionID, pmap descarta todos los permisos y la UI reabre
    el rol como si no tuviera permisos asignados.
    """
    import inspect
    import modules.admin_sql.routes as routes

    src = inspect.getsource(routes.get_roles)

    assert "prm.AccionID" in src
    assert 'accion_id = p.get("AccionID")' in src
    assert '"accion_id": int(accion_id)' in src


def test_get_roles_does_not_return_module_only_permissions():
    """
    El contrato de lectura debe conservar ModuloID + AccionID.
    """
    import inspect
    import modules.admin_sql.routes as routes

    src = inspect.getsource(routes.get_roles)

    assert 'key = (str(modulo_id), int(accion_id))' in src
    assert '"modulo_id": str(modulo_id)' in src
    assert '"accion_id": int(accion_id)' in src
