from modules.costos_margenes import reglas_margen_service as service


UNIT_PK = (
    "11111111-1111-1111-1111-111111111111"
)


def test_usuario_gana_sobre_producto(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "resolver_configuracion_efectiva",
        lambda unidad_pk, usuario_id=None: {
            "empresa_id": 1,
            "unidad_negocio_pk": unidad_pk,
            "usuario_id": usuario_id,
            "margen_minimo_porcentaje": 72,
            "fuentes": {
                "margen_minimo_porcentaje":
                    "USUARIO",
            },
        },
    )

    called = {
        "regla": False,
    }

    def regla(**kwargs):
        called["regla"] = True

        return {
            "regla": {
                "regla_id": "producto",
            },
            "fuente": "PRODUCTO",
            "margen_esperado": 40,
        }

    monkeypatch.setattr(
        service,
        "resolver_regla_aplicable",
        regla,
    )

    result = service.resolver_margen_esperado(
        producto_clave="X",
        unidad_negocio_pk=UNIT_PK,
        usuario_id=100,
    )

    assert result["fuente"] == "USUARIO"
    assert result["margen_efectivo"] == 72
    assert (
        result["fuente_margen_efectivo"]
        == "USUARIO"
    )
    assert result["usuario_id"] == 100

    assert called["regla"] is False


def test_producto_gana_si_usuario_no_override(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "resolver_configuracion_efectiva",
        lambda unidad_pk, usuario_id=None: {
            "empresa_id": 1,
            "unidad_negocio_pk": unidad_pk,
            "usuario_id": usuario_id,
            "margen_minimo_porcentaje": 65,
            "fuentes": {
                "margen_minimo_porcentaje":
                    "UNIDAD",
            },
        },
    )

    monkeypatch.setattr(
        service,
        "resolver_regla_aplicable",
        lambda **kwargs: {
            "regla": {
                "regla_id": "producto",
            },
            "fuente": "PRODUCTO",
            "margen_esperado": 40,
        },
    )

    result = service.resolver_margen_esperado(
        producto_clave="X",
        unidad_negocio_pk=UNIT_PK,
        usuario_id=100,
    )

    assert result["fuente"] == "PRODUCTO"
    assert result["margen_efectivo"] == 40


def test_unidad_fallback_sin_override_usuario(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "resolver_configuracion_efectiva",
        lambda unidad_pk, usuario_id=None: {
            "empresa_id": 1,
            "unidad_negocio_pk": unidad_pk,
            "usuario_id": usuario_id,
            "margen_minimo_porcentaje": 65,
            "fuentes": {
                "margen_minimo_porcentaje":
                    "UNIDAD",
            },
        },
    )

    monkeypatch.setattr(
        service,
        "resolver_regla_aplicable",
        lambda **kwargs: {
            "regla": None,
            "fuente": "SIN_REGLA",
            "margen_esperado": None,
        },
    )

    result = service.resolver_margen_esperado(
        unidad_negocio_pk=UNIT_PK,
        usuario_id=100,
    )

    assert result["fuente"] == "UNIDAD"
    assert result["margen_efectivo"] == 65


def test_empresa_fallback_sin_override_usuario(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "resolver_configuracion_efectiva",
        lambda unidad_pk, usuario_id=None: {
            "empresa_id": 1,
            "unidad_negocio_pk": unidad_pk,
            "usuario_id": usuario_id,
            "margen_minimo_porcentaje": 65,
            "fuentes": {
                "margen_minimo_porcentaje":
                    "EMPRESA",
            },
        },
    )

    monkeypatch.setattr(
        service,
        "resolver_regla_aplicable",
        lambda **kwargs: {
            "regla": None,
            "fuente": "SIN_REGLA",
            "margen_esperado": None,
        },
    )

    result = service.resolver_margen_esperado(
        unidad_negocio_pk=UNIT_PK,
        usuario_id=100,
    )

    assert result["fuente"] == "EMPRESA"
    assert result["margen_efectivo"] == 65


def test_sin_usuario_conserva_cascada_negocio(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "resolver_configuracion_efectiva",
        lambda unidad_pk, usuario_id=None: {
            "empresa_id": 1,
            "unidad_negocio_pk": unidad_pk,
            "usuario_id": None,
            "margen_minimo_porcentaje": 65,
            "fuentes": {
                "margen_minimo_porcentaje":
                    "UNIDAD",
            },
        },
    )

    monkeypatch.setattr(
        service,
        "resolver_regla_aplicable",
        lambda **kwargs: {
            "regla": {
                "regla_id": "familia",
            },
            "fuente": "FAMILIA",
            "margen_esperado": 55,
        },
    )

    result = service.resolver_margen_esperado(
        familia_codigo="F",
        unidad_negocio_pk=UNIT_PK,
    )

    assert result["fuente"] == "FAMILIA"
    assert result["margen_efectivo"] == 55


def test_usuario_sin_unidad_no_se_inventa(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "resolver_regla_aplicable",
        lambda **kwargs: {
            "regla": None,
            "fuente": "SIN_REGLA",
            "margen_esperado": None,
        },
    )

    result = service.resolver_margen_esperado(
        usuario_id=100,
    )

    assert result["fuente"] == "SIN_REGLA"
    assert result["margen_efectivo"] is None
    assert result["estado"] == "SIN_MARGEN_EFECTIVO"
