from modules.costos_margenes import reglas_margen_service as service


def _sin_regla(**kwargs):
    return {
        "regla": None,
        "fuente": "SIN_REGLA",
        "margen_esperado": None,
    }


def test_producto_corta_cascada(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "resolver_regla_aplicable",
        lambda **kwargs: {
            "regla": {"regla_id": "x"},
            "fuente": "PRODUCTO",
            "margen_esperado": 40.0,
        },
    )

    called = {"config": False}

    def config(*args, **kwargs):
        called["config"] = True
        return {}

    monkeypatch.setattr(
        service,
        "resolver_configuracion_efectiva",
        config,
    )

    result = service.resolver_margen_esperado(
        producto_clave="X",
        unidad_negocio_pk=(
            "11111111-1111-1111-1111-111111111111"
        ),
    )

    assert result["fuente"] == "PRODUCTO"
    assert result["margen_efectivo"] == 40.0
    assert (
        result["fuente_margen_efectivo"]
        == "PRODUCTO"
    )
    assert called["config"] is False


def test_unidad_es_fallback(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "resolver_regla_aplicable",
        _sin_regla,
    )

    monkeypatch.setattr(
        service,
        "resolver_configuracion_efectiva",
        lambda unidad_pk, usuario_id=None: {
            "empresa_id": 1,
            "unidad_negocio_pk": unidad_pk,
            "margen_minimo_porcentaje": 65,
            "fuentes": {
                "margen_minimo_porcentaje":
                    "UNIDAD",
            },
        },
    )

    result = service.resolver_margen_esperado(
        unidad_negocio_pk=(
            "11111111-1111-1111-1111-111111111111"
        ),
    )

    assert result["fuente"] == "UNIDAD"
    assert result["margen_efectivo"] == 65.0
    assert (
        result["fuente_margen_efectivo"]
        == "UNIDAD"
    )


def test_empresa_es_ultimo_fallback(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "resolver_regla_aplicable",
        _sin_regla,
    )

    monkeypatch.setattr(
        service,
        "resolver_configuracion_efectiva",
        lambda unidad_pk, usuario_id=None: {
            "empresa_id": 1,
            "unidad_negocio_pk": unidad_pk,
            "margen_minimo_porcentaje": 65,
            "fuentes": {
                "margen_minimo_porcentaje":
                    "EMPRESA",
            },
        },
    )

    result = service.resolver_margen_esperado(
        unidad_negocio_pk=(
            "11111111-1111-1111-1111-111111111111"
        ),
    )

    assert result["fuente"] == "EMPRESA"
    assert result["margen_efectivo"] == 65.0


def test_sin_regla_y_sin_config_no_inventa(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "resolver_regla_aplicable",
        _sin_regla,
    )

    result = service.resolver_margen_esperado()

    assert result["fuente"] == "SIN_REGLA"
    assert result["margen_efectivo"] is None
    assert (
        result["fuente_margen_efectivo"]
        is None
    )
    assert result["estado"] == "SIN_MARGEN_EFECTIVO"
