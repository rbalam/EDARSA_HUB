from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[1]

ROUTES = (
    ROOT
    / "modules"
    / "costos_margenes"
    / "routes.py"
)

REPO = (
    ROOT
    / "modules"
    / "costos_margenes"
    / "repository.py"
)


def _function(path, name):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ) and node.name == name:
            return (
                ast.get_source_segment(
                    source,
                    node,
                )
                or ""
            )

    raise AssertionError(name)


def test_no_existe_umbral_legacy_20():
    source = REPO.read_text(
        encoding="utf-8"
    )

    assert "margen_porcentaje < 20" not in source


def test_productos_y_resumen_comparten_helper():
    productos = _function(
        ROUTES,
        "listar_productos",
    )
    resumen = _function(
        ROUTES,
        "obtener_resumen",
    )

    assert (
        "_resolver_margen_efectivo_productos("
        in productos
    )

    assert (
        "_contar_productos_margen_bajo_canonico("
        in resumen
    )


def test_helper_delega_al_resolver_batch():
    source = _function(
        ROUTES,
        "_resolver_margen_efectivo_productos",
    )

    assert (
        "resolver_margenes_esperados_batch("
        in source
    )

    assert "< 20" not in source
    assert "<20" not in source


def test_contador_compara_real_con_efectivo():
    source = _function(
        ROUTES,
        "_contar_productos_margen_bajo_canonico",
    )

    assert "margen_porcentaje" in source
    assert "margen_efectivo" in source
    assert (
        "< float(margen_efectivo)"
        in source
    )


def test_contador_pagina():
    source = _function(
        ROUTES,
        "_contar_productos_margen_bajo_canonico",
    )

    assert "page_size=200" in source
    assert "while True:" in source
    assert "page += 1" in source


def test_sin_categorias_comerciales_hardcodeadas():
    source = ROUTES.read_text(
        encoding="utf-8"
    ).upper()

    for value in (
        '"ALIMENTOS"',
        "'ALIMENTOS'",
        '"BEBIDAS"',
        "'BEBIDAS'",
        '"PUROS"',
        "'PUROS'",
        '"OTROS"',
        "'OTROS'",
    ):
        assert value not in source
