import ast
from pathlib import Path


ROUTES = Path(
    "/app/backend/modules/costos_margenes/routes.py"
)


def _source():
    return ROUTES.read_text(
        encoding="utf-8"
    )


def _tree():
    return ast.parse(_source())


def _function(name):
    for node in _tree().body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ) and node.name == name:
            return node

    raise AssertionError(
        f"Funcion no encontrada: {name}"
    )


def test_importa_resolver_configuracion_efectiva():
    imports = [
        node
        for node in _tree().body
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "modules.costos_margenes.configuracion_repository"
    ]

    assert imports

    imported_names = {
        alias.name
        for node in imports
        for alias in node.names
    }

    assert "resolver_configuracion_efectiva" in imported_names


def test_helper_usa_usuario_sql_y_unidad_canonica():
    fn = _function(
        "_resolve_configuracion_efectiva"
    )

    text = ast.get_source_segment(
        _source(),
        fn,
    )

    assert "_get_sql_usuario_id(current_user)" in text
    assert "resolver_configuracion_efectiva(" in text
    assert "usuario_id=usuario_id" in text
    assert "current_user.get('id')" not in text
    assert 'current_user.get("id")' not in text


def test_listar_productos_conserva_unidad_pk():
    fn = _function("listar_productos")

    text = ast.get_source_segment(
        _source(),
        fn,
    )

    assert (
        "_resolve_configuracion_efectiva("
        in text
    )

    assert (
        "unidad_negocio_pk=unidad_pk_filtro"
        in text
    )

    assert "unidad_negocio_pk=None" not in text


def test_routes_no_descarta_unidad_pk():
    assert "unidad_negocio_pk=None" not in _source()
