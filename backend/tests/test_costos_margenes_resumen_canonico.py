from pathlib import Path
import ast


REPOSITORY = Path(
    "/app/backend/modules/costos_margenes/repository.py"
)


def _summary_source():
    source = REPOSITORY.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    node = next(
        item
        for item in tree.body
        if isinstance(
            item,
            ast.FunctionDef,
        )
        and item.name
        == "get_resumen_costos_margenes"
    )

    return (
        ast.get_source_segment(
            source,
            node,
        )
        or ""
    )


def test_summary_only_active_products():
    source = _summary_source()

    assert "p.Activo = 1" in source
    assert "p.Activo IS NULL" not in source


def test_summary_uses_same_mpro_commercial_filters():
    source = _summary_source()

    assert (
        "_mpro_comercial_where('p')"
        in source
    )

    assert (
        "_mpro_menu_pos_where('p')"
        in source
    )


def test_summary_recipe_is_active_detail():
    source = _summary_source()

    assert (
        "Sync_Productos_Recetas"
        in source
    )

    assert (
        "ISNULL(r.Activo, 1) = 1"
        in source
    )

    assert "p.TieneReceta" not in source


def test_summary_cost_is_active_recipe_sum():
    source = _summary_source()

    assert "SUM(" in source
    assert "r.CostoTotal" in source

    assert (
        "AVG(CASE WHEN p.CostoReceta"
        not in source
    )


def test_summary_margin_uses_price_without_tax():
    source = _summary_source()

    assert "p.PrecioSinImpuestos" in source

    assert (
        "p.MargenBrutoPorcentaje"
        not in source
    )

    assert (
        "p.MargenBrutoPesos"
        not in source
    )


def test_summary_nonpositive_base_is_not_margin_calculable():
    source = _summary_source()

    assert (
        "p.PrecioSinImpuestos > 0"
        in source
    )

    assert (
        "NULLIF("
        in source
    )
