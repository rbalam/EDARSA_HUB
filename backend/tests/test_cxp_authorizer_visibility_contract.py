from pathlib import Path
import ast


TARGET = Path(
    "/app/backend/modules/finanzas/cuentas_por_pagar.py"
)


def source():
    return TARGET.read_text(encoding="utf-8")


def function_source(name):
    src = source()
    tree = ast.parse(src)

    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ) and node.name == name:
            lines = src.splitlines()
            return "\n".join(
                lines[node.lineno - 1:node.end_lineno]
            )

    raise AssertionError(f"Funcion no encontrada: {name}")


def test_visibility_uses_canonical_detail_table():
    src = function_source(
        "_cxp_authorization_visibility"
    )

    assert "dbo.Usuario_AutorizacionesDetalle" in src
    assert "UsuarioAutorizadorID" in src
    assert "NivelAutorizacion" in src
    assert "Resultado" in src


def test_visibility_uses_real_pending_column():
    src = function_source(
        "_cxp_authorization_visibility"
    )

    assert 'resultado == "PENDIENTE"' in src
    assert "EstatusDetalle" not in src


def test_visibility_is_user_specific():
    src = function_source(
        "_cxp_authorization_visibility"
    )

    assert "_get_cxp_usuario_id(current_user)" in src
    assert "UsuarioAutorizadorID" in src
    assert '"es_autorizador_actual"' in src
    assert '"puede_resolver_autorizacion"' in src


def test_visibility_requires_open_authorization():
    src = function_source(
        "_cxp_authorization_visibility"
    )

    assert '"PENDIENTE", "EN_PROCESO"' in src


def test_factura_dict_exposes_visibility():
    src = function_source("_cxp_factura_dict")

    assert "current_user=None" in src
    assert "_cxp_authorization_visibility" in src
    assert '"puede_resolver_autorizacion"' in src
    assert '"es_autorizador_actual"' in src


def test_no_generic_admin_logic_inside_visibility():
    src = source()
    tree = ast.parse(src)

    fn = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_cxp_authorization_visibility"
    )

    names = {
        node.id
        for node in ast.walk(fn)
        if isinstance(node, ast.Name)
    }

    calls = set()

    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue

        if isinstance(node.func, ast.Name):
            calls.add(node.func.id)

        elif isinstance(node.func, ast.Attribute):
            calls.add(node.func.attr)

    assert "FINANZAS_ADMINISTRAR" not in names
    assert "require_any_finanzas_permission" not in calls


def test_no_parallel_authorization_schema():
    src = source()

    assert "CxP_Autorizadores" not in src
    assert "Finanzas_CxP_Autorizadores" not in src
