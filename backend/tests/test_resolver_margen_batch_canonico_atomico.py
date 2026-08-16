from modules.costos_margenes import reglas_margen_service as service


UNIT = (
    "11111111-1111-1111-1111-111111111111"
)


def test_batch_precarga_reglas_una_vez(
    monkeypatch,
):
    calls = {
        "rules": 0,
        "config": 0,
    }

    def fake_rules(**kwargs):
        calls["rules"] += 1

        return [
            {
                "regla_id": "1",
                "nivel_aplicacion": "PRODUCTO",
                "producto_clave": "A",
                "subfamilia_codigo": None,
                "familia_codigo": None,
                "grupo_codigo": None,
                "margen_esperado": 41,
                "empresa_id": None,
                "sucursal_id": None,
                "server_id": None,
                "fecha_creacion": None,
            },
        ]

    def fake_config(
        unidad_pk,
        usuario_id=None,
    ):
        calls["config"] += 1

        return {
            "empresa_id": 1,
            "unidad_negocio_pk": unidad_pk,
            "usuario_id": usuario_id,
            "margen_minimo_porcentaje": 65,
            "fuentes": {
                "margen_minimo_porcentaje":
                    "UNIDAD",
            },
        }

    monkeypatch.setattr(
        service,
        "cargar_reglas_margen_vigentes",
        fake_rules,
    )

    monkeypatch.setattr(
        service,
        "resolver_configuracion_efectiva",
        fake_config,
    )

    rows = service.resolver_margenes_esperados_batch(
        [
            {
                "producto_clave": "A",
                "subfamilia_codigo": None,
                "familia_codigo": None,
                "grupo_codigo": None,
            },
            {
                "producto_clave": "B",
                "subfamilia_codigo": None,
                "familia_codigo": None,
                "grupo_codigo": None,
            },
        ],
        unidad_negocio_pk=UNIT,
    )

    assert calls["rules"] == 1
    assert calls["config"] == 1

    assert rows[0]["fuente_margen_efectivo"] == "PRODUCTO"
    assert rows[0]["margen_efectivo"] == 41

    assert rows[1]["fuente_margen_efectivo"] == "UNIDAD"
    assert rows[1]["margen_efectivo"] == 65


def test_usuario_override_evitar_reglas(
    monkeypatch,
):
    calls = {
        "rules": 0,
        "config": 0,
    }

    def fake_rules(**kwargs):
        calls["rules"] += 1
        raise AssertionError(
            "RULES_NO_DEBEN_CARGARSE"
        )

    def fake_config(
        unidad_pk,
        usuario_id=None,
    ):
        calls["config"] += 1

        return {
            "empresa_id": 1,
            "unidad_negocio_pk": unidad_pk,
            "usuario_id": usuario_id,
            "margen_minimo_porcentaje": 72,
            "fuentes": {
                "margen_minimo_porcentaje":
                    "USUARIO",
            },
        }

    monkeypatch.setattr(
        service,
        "cargar_reglas_margen_vigentes",
        fake_rules,
    )

    monkeypatch.setattr(
        service,
        "resolver_configuracion_efectiva",
        fake_config,
    )

    rows = service.resolver_margenes_esperados_batch(
        [
            {
                "producto_clave": "A",
            },
            {
                "producto_clave": "B",
            },
        ],
        unidad_negocio_pk=UNIT,
        usuario_id=10,
    )

    assert calls["config"] == 1
    assert calls["rules"] == 0

    assert all(
        r["fuente_margen_efectivo"]
        == "USUARIO"
        for r in rows
    )

    assert all(
        r["margen_efectivo"]
        == 72
        for r in rows
    )


def test_cascada_producto_familia_grupo(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "resolver_configuracion_efectiva",
        lambda *args, **kwargs: {
            "empresa_id": 1,
            "unidad_negocio_pk": UNIT,
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
        "cargar_reglas_margen_vigentes",
        lambda **kwargs: [
            {
                "regla_id": "P",
                "nivel_aplicacion": "PRODUCTO",
                "producto_clave": "A",
                "subfamilia_codigo": None,
                "familia_codigo": None,
                "grupo_codigo": None,
                "margen_esperado": 40,
                "empresa_id": None,
                "sucursal_id": None,
                "server_id": None,
                "fecha_creacion": None,
            },
            {
                "regla_id": "F",
                "nivel_aplicacion": "FAMILIA",
                "producto_clave": None,
                "subfamilia_codigo": None,
                "familia_codigo": "CARNE",
                "grupo_codigo": None,
                "margen_esperado": 55,
                "empresa_id": None,
                "sucursal_id": None,
                "server_id": None,
                "fecha_creacion": None,
            },
            {
                "regla_id": "G",
                "nivel_aplicacion": "GRUPO",
                "producto_clave": None,
                "subfamilia_codigo": None,
                "familia_codigo": None,
                "grupo_codigo": "ALIMENTOS",
                "margen_esperado": 60,
                "empresa_id": None,
                "sucursal_id": None,
                "server_id": None,
                "fecha_creacion": None,
            },
        ],
    )

    rows = service.resolver_margenes_esperados_batch(
        [
            {
                "producto_clave": "A",
                "familia_codigo": "CARNE",
                "grupo_codigo": "ALIMENTOS",
            },
            {
                "producto_clave": "B",
                "familia_codigo": "CARNE",
                "grupo_codigo": "ALIMENTOS",
            },
            {
                "producto_clave": "C",
                "familia_codigo": "OTRA",
                "grupo_codigo": "ALIMENTOS",
            },
            {
                "producto_clave": "D",
                "familia_codigo": "OTRA",
                "grupo_codigo": "OTRO",
            },
        ],
        unidad_negocio_pk=UNIT,
    )

    assert rows[0]["fuente_margen_efectivo"] == "PRODUCTO"
    assert rows[1]["fuente_margen_efectivo"] == "FAMILIA"
    assert rows[2]["fuente_margen_efectivo"] == "GRUPO"
    assert rows[3]["fuente_margen_efectivo"] == "UNIDAD"


def test_batch_vacio_no_consulta(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "cargar_reglas_margen_vigentes",
        lambda **kwargs: (
            (_ for _ in ()).throw(
                AssertionError(
                    "NO_DEBE_CONSULTAR"
                )
            )
        ),
    )

    result = service.resolver_margenes_esperados_batch(
        []
    )

    assert result == []


def _regla_producto(**overrides):
    regla = {
        "regla_id": "P",
        "nivel_aplicacion": "PRODUCTO",
        "producto_id": None,
        "producto_clave": None,
        "subfamilia_codigo": None,
        "familia_codigo": None,
        "grupo_codigo": None,
        "margen_esperado": 40,
        "empresa_id": None,
        "sucursal_id": None,
        "server_id": None,
        "fecha_creacion": None,
    }
    regla.update(overrides)
    return regla


def test_producto_id_canonico_tiene_prioridad_sobre_clave_legacy():
    resultado = service._seleccionar_regla_margen_desde_contexto(
        [
            _regla_producto(
                regla_id="CANONICA",
                producto_id=101,
                producto_clave="OTRA",
                margen_esperado=47,
            ),
            _regla_producto(
                regla_id="LEGACY",
                producto_clave="RIBEYE-500",
                margen_esperado=39,
            ),
        ],
        producto_id=101,
        producto_clave="RIBEYE-500",
    )

    assert resultado["fuente"] == "PRODUCTO"
    assert resultado["regla"]["regla_id"] == "CANONICA"
    assert resultado["margen_esperado"] == 47


def test_clave_legacy_no_contradice_producto_id_poblado():
    resultado = service._seleccionar_regla_margen_desde_contexto(
        [
            _regla_producto(
                producto_id=202,
                producto_clave="RIBEYE-500",
            ),
            {
                "regla_id": "F",
                "nivel_aplicacion": "FAMILIA",
                "producto_id": None,
                "producto_clave": None,
                "subfamilia_codigo": None,
                "familia_codigo": "CARNES",
                "grupo_codigo": None,
                "margen_esperado": 55,
                "empresa_id": None,
                "sucursal_id": None,
                "server_id": None,
                "fecha_creacion": None,
            },
        ],
        producto_id=101,
        producto_clave="RIBEYE-500",
        familia_codigo="CARNES",
    )

    assert resultado["fuente"] == "FAMILIA"
    assert resultado["regla"]["regla_id"] == "F"


def test_clave_legacy_solo_aplica_sin_producto_id():
    resultado = service._seleccionar_regla_margen_desde_contexto(
        [
            _regla_producto(
                producto_clave="RIBEYE-500",
                margen_esperado=39,
            ),
        ],
        producto_id=101,
        producto_clave="RIBEYE-500",
    )

    assert resultado["fuente"] == "PRODUCTO"
    assert resultado["margen_esperado"] == 39
