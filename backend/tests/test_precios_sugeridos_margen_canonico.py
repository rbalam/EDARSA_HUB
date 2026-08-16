import ast
from pathlib import Path


ROOT = Path("/app")

ROUTER = (
    ROOT
    / "backend/modules/comercial/"
      "routes_precios_sugeridos.py"
)

SERVICE = (
    ROOT
    / "backend/modules/comercial/services/"
      "precios_sugeridos_consolidado_service.py"
)


def _text(path):
    return path.read_text(encoding="utf-8")


def _fn(path, name, async_fn=False):
    source = _text(path)
    tree = ast.parse(source)

    cls = (
        ast.AsyncFunctionDef
        if async_fn
        else ast.FunctionDef
    )

    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, cls)
        and node.name == name
    ]

    assert len(matches) == 1

    return ast.get_source_segment(
        source,
        matches[0],
    )


def test_router_ya_no_expone_035():
    source = _fn(
        ROUTER,
        "get_precios_sugeridos",
        async_fn=True,
    )

    assert "Query(0.35" not in source
    assert "margen_objetivo" not in source


def test_service_ya_no_tiene_margen_035():
    source = _fn(
        SERVICE,
        "obtener_precios_sugeridos",
    )

    assert "margen_objetivo" not in source
    assert "0.35" not in source


def test_service_usa_batch_canonico():
    source = _fn(
        SERVICE,
        "obtener_precios_sugeridos",
    )

    assert (
        "resolver_margenes_esperados_batch("
        in source
    )

    for token in (
        "producto_clave",
        "subfamilia_codigo",
        "familia_codigo",
        "grupo_codigo",
        "unidad_negocio_pk",
        "usuario_id",
    ):
        assert token in source


def test_query_tiene_contexto_clasificacion():
    source = _fn(
        SERVICE,
        "obtener_precios_sugeridos",
    )

    for token in (
        "FamiliaCodigoFuente",
        "SubFamiliaCodigoFuente",
        "Comercial_ClasificacionesProducto",
        "grupo_codigo",
    ):
        assert token in source


def test_no_vinos_convierte_porcentaje():
    source = _fn(
        SERVICE,
        "obtener_precios_sugeridos",
    )

    tree = ast.parse(source)

    assert "margen_pct / 100.0" in source

    formula_ok = False

    for node in ast.walk(tree):
        if not isinstance(node, ast.BinOp):
            continue

        if not isinstance(node.op, ast.Div):
            continue

        if not (
            isinstance(node.left, ast.Name)
            and node.left.id == "costo_receta"
        ):
            continue

        right = node.right

        if not (
            isinstance(right, ast.BinOp)
            and isinstance(right.op, ast.Sub)
            and isinstance(right.left, ast.Constant)
            and right.left.value == 1
            and isinstance(right.right, ast.Name)
            and right.right.id == "margen_factor"
        ):
            continue

        formula_ok = True
        break

    assert formula_ok


def test_margen_falla_cerrado_si_invalido():
    source = _fn(
        SERVICE,
        "obtener_precios_sugeridos",
    )

    assert "margen_pct <= 0" in source
    assert "margen_pct >= 100" in source
    assert "MARGEN_EFECTIVO_FUERA_RANGO" in source


def test_vinos_no_consumen_margen_general():
    source = _fn(
        SERVICE,
        "obtener_precios_sugeridos",
    )

    wine_start = source.index(
        "if es_vino:"
    )

    nonwine_start = source.index(
        "else:\n"
        "            # NO VINOS:",
        wine_start,
    )

    wine_block = source[
        wine_start:nonwine_start
    ]

    assert "VINOS_RANGOS_MX" in _text(SERVICE)
    assert "margen_efectivo" not in wine_block
    assert "resolver_margenes_esperados_batch" not in wine_block


def test_tabulacion_vinos_permanece():
    source = _text(SERVICE)

    assert "MargenMultiplicador" in source
    assert "VINOS_RANGOS_MX" in source
    assert (
        "precio_sugerido = costo_botella * multiplicador"
        in source
    )


def test_redondeo_canonico_permanece():
    source = _text(SERVICE)

    assert "redondear_a_multiplo(" in source
    assert "round(precio_minimo / 5)" not in source
    assert "round(precio_sugerido / 5)" not in source


def test_top_level_declara_resolucion_por_producto():
    source = _text(SERVICE)

    assert (
        "'CANONICA_POR_PRODUCTO'"
        in source
    )

    assert "margen_objetivo_usado" not in source
