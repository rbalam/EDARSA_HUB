from pathlib import Path
import ast


ROOT = Path("/app")

ROUTES = ROOT / "backend/modules/costos_margenes/routes.py"
REPO = ROOT / "backend/modules/costos_margenes/repository.py"
SCHEMA = ROOT / "backend/modules/costos_margenes/schemas.py"


def _fn(path, name, async_fn=False):
    source = path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    cls = (
        ast.AsyncFunctionDef
        if async_fn
        else ast.FunctionDef
    )

    fn = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, cls)
        and node.name == name
    )

    return source, fn


def test_usuario_canonico_en_listado():
    source, fn = _fn(
        ROUTES,
        "listar_productos",
        async_fn=True,
    )

    segment = ast.get_source_segment(
        source,
        fn,
    )

    assert "_get_sql_usuario_id(" in segment

    assert "_resolver_margen_efectivo_productos(" in segment

    helper_source, helper = _fn(
        ROUTES,
        "_resolver_margen_efectivo_productos",
    )

    helper_segment = ast.get_source_segment(
        helper_source,
        helper,
    )

    assert "resolver_margenes_esperados_batch(" in helper_segment


def test_umbral_20_fuera_del_listado():
    source, fn = _fn(
        ROUTES,
        "listar_productos",
        async_fn=True,
    )

    segment = ast.get_source_segment(
        source,
        fn,
    )

    assert "umbral_margen" not in segment
    assert "Query(20" not in segment


def test_umbral_fuera_repository_listado():
    source, fn = _fn(
        REPO,
        "get_productos_con_costos",
    )

    segment = ast.get_source_segment(
        source,
        fn,
    )

    assert "umbral_margen" not in segment


def test_contexto_clasificacion():
    source, fn = _fn(
        REPO,
        "get_productos_con_costos",
    )

    segment = ast.get_source_segment(
        source,
        fn,
    )

    for token in (
        "FamiliaCodigoFuente",
        "SubFamiliaCodigoFuente",
        "Comercial_ClasificacionesProducto",
        "grupo_codigo",
    ):
        assert token in segment


def test_schema_atomico():
    source = SCHEMA.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    cls = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "ProductoCostoMargen"
    )

    fields = {
        node.target.id:
            ast.unparse(node.annotation)
        for node in cls.body
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
        )
    }

    assert "str" in fields["unidad_negocio_pk"]
    assert "margen_efectivo" in fields
    assert "fuente_margen_efectivo" in fields
