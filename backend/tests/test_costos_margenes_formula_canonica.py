from pathlib import Path


REPOSITORY = Path(
    "/app/backend/modules/costos_margenes/repository.py"
)


def _source():
    return REPOSITORY.read_text(
        encoding="utf-8"
    )


def test_receta_real_exige_componente_activo():
    source = _source()

    assert (
        "AND ISNULL(r_chk.Activo, 1) = 1"
        in source
    )


def test_costo_receta_suma_solo_componentes_activos():
    source = _source()

    assert (
        "AND ISNULL(r.Activo, 1) = 1"
        in source
    )


def test_numero_insumos_cuenta_solo_componentes_activos():
    source = _source()

    assert (
        "AND ISNULL(r_cnt.Activo, 1) = 1"
        in source
    )


def test_repository_no_aplica_umbral_paralelo_margen_bajo():
    source = _source()

    assert "if margen_bajo:" not in source
    assert "umbral_margen" not in source
    assert "p.PrecioSinImpuestos as precio_sin_impuestos" in source


def test_margen_runtime_usa_precio_sin_impuestos():
    source = _source()
    compact = "".join(source.split())

    assert "precio_base=_safe_decimal(row.get('precio_sin_impuestos')" in compact
    assert "margen_pesos=round(precio_base-costo_receta" in compact
    assert "(margen_pesos/precio_base)*100" in compact


def test_precio_base_no_positivo_no_genera_margen():
    source = _source()

    assert "if precio_base > 0:" in source
    assert "margen_pesos = None" in source
    assert "margen_porcentaje = None" in source
