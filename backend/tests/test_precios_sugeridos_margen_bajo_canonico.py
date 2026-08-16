from pathlib import Path
import ast


SERVICE = Path(
    "/app/backend/modules/comercial/services/"
    "precios_sugeridos_consolidado_service.py"
)


def _source():
    return SERVICE.read_text(encoding="utf-8")


def test_precio_sin_impuestos_sale_de_sync_productos():
    source = _source()

    assert (
        "p.PrecioSinImpuestos as precio_sin_impuestos"
        in source
    )


def test_margen_actual_usa_precio_sin_impuestos():
    source = _source()

    assert (
        "p.get('precio_sin_impuestos')"
        in source
    )

    assert (
        "margen_monto = (\n"
        "                precio_sin_impuestos\n"
        "                - costo_receta\n"
        "            )"
        in source
    )

    assert (
        "margen_monto\n"
        "                / precio_sin_impuestos\n"
        "                * 100"
        in source
    )


def test_margen_bajo_no_contiene_umbral_20():
    source = _source()

    assert "< 20" not in source
    assert "<20" not in source


def test_margen_bajo_compara_con_margen_efectivo():
    source = _source()

    assert (
        'margen_efectivo_filtro = p.get(\n'
        '                "_margen_efectivo"\n'
        '            )'
        in source
    )

    assert (
        "margen_porcentaje\n"
        "                < margen_efectivo_filtro"
        in source
    )


def test_margen_bajo_excluye_vinos():
    source = _source()

    marker = "if margen_bajo:"
    start = source.index(marker)
    block = source[start:start + 1200]

    assert "if es_vino:" in block
    assert "continue" in block


def test_service_sigue_siendo_python_valido():
    ast.parse(_source())
