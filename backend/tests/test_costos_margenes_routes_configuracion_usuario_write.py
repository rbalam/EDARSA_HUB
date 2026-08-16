import ast
from pathlib import Path


ROUTES = Path(
    "/app/backend/modules/costos_margenes/routes.py"
)

SCHEMAS = Path(
    "/app/backend/modules/costos_margenes/schemas.py"
)


def _source():
    return ROUTES.read_text(encoding="utf-8")


def _function(name):
    tree = ast.parse(_source())

    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ) and node.name == name:
            return node

    raise AssertionError(
        f"Funcion no encontrada: {name}"
    )


def test_endpoint_write_existe():
    text = _source()

    assert (
        '@router.patch("/configuracion/usuario")'
        in text
    )


def test_endpoint_exige_configurar():
    fn = _function(
        "actualizar_configuracion_personal"
    )

    text = ast.get_source_segment(
        _source(),
        fn,
    )

    assert "COSTOS_MARGENES_CONFIGURAR" in text
    assert "_verify_costos_margenes_access(" in text


def test_usuario_no_viene_del_payload():
    schema = SCHEMAS.read_text(
        encoding="utf-8"
    )

    block = schema.split(
        "class ConfiguracionCostosMargenesUsuarioPatch",
        1,
    )[1].split(
        "# ==================== SYNC STATUS",
        1,
    )[0]

    assert "UsuarioID" not in block
    assert "usuario_id" not in block


def test_respuesta_usa_resolver_autoritativo():
    fn = _function(
        "actualizar_configuracion_personal"
    )

    text = ast.get_source_segment(
        _source(),
        fn,
    )

    assert "resolver_configuracion_efectiva(" in text
    assert "usuario_id=usuario_id" in text


def test_patch_distingue_omitido_de_null():
    fn = _function(
        "actualizar_configuracion_personal"
    )

    text = ast.get_source_segment(
        _source(),
        fn,
    )

    assert "model_fields_set" in text
    assert "__fields_set__" in text


def test_endpoint_scope_usa_mismo_permiso_configurar():
    fn = _function(
        "actualizar_configuracion_personal"
    )

    text = ast.get_source_segment(
        _source(),
        fn,
    )

    expected = (
        "resolve_authorized_unidad_scope("
    )

    assert expected in text

    scope_fragment = text.split(
        "resolve_authorized_unidad_scope(",
        1,
    )[1].split(
        ")",
        1,
    )[0]

    assert (
        "COSTOS_MARGENES_CONFIGURAR"
        in scope_fragment
    )

    assert (
        "COSTOS_MARGENES_VER"
        not in scope_fragment
    )
