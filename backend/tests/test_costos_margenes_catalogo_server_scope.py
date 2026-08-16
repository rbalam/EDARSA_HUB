from pathlib import Path
import ast


ROOT = Path("/app")

REPO = (
    ROOT
    / "backend/modules/costos_margenes/repository.py"
)

ROUTES = (
    ROOT
    / "backend/modules/costos_margenes/routes.py"
)


def _get_fn(
    path,
    name,
    cls,
):
    source = path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    fn = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, cls)
        and node.name == name
    )

    return (
        source,
        fn,
        ast.get_source_segment(
            source,
            fn,
        ),
    )


def test_catalogo_no_filtra_unidad_legacy():
    _, _, segment = _get_fn(
        REPO,
        "get_productos_con_costos",
        ast.FunctionDef,
    )

    assert (
        "CONVERT(varchar(36), "
        "p.UnidadNegocioID) = %s"
        not in segment
    )


def test_catalogo_no_filtra_empresa_legacy():
    _, _, segment = _get_fn(
        REPO,
        "get_productos_con_costos",
        ast.FunctionDef,
    )

    assert (
        "p.EmpresaID = %s"
        not in segment
    )


def test_catalogo_conserva_server_scope():
    _, _, segment = _get_fn(
        REPO,
        "get_productos_con_costos",
        ast.FunctionDef,
    )

    assert "p.ServerID" in segment

    assert (
        "servidor_id"
        in segment
        or "servidores_ids"
        in segment
    )


def test_contexto_unidad_sigue_en_firma():
    _, fn, _ = _get_fn(
        REPO,
        "get_productos_con_costos",
        ast.FunctionDef,
    )

    args = {
        a.arg
        for a in fn.args.args
    }

    assert "unidad_negocio_pk" in args
    assert "empresa_id" in args


def test_route_resuelve_server_desde_unidad():
    _, _, segment = _get_fn(
        ROUTES,
        "listar_productos",
        ast.AsyncFunctionDef,
    )

    assert "_resolve_servidor_filtro(" in segment

    assert (
        "servidor_id="
        "servidor_id_filtro"
        in segment
    )

    assert (
        "unidad_negocio_pk="
        "unidad_pk_filtro"
        in segment
    )
