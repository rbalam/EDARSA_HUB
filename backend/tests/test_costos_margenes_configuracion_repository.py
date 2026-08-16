from modules.costos_margenes import configuracion_repository as repo


def test_precedencia_usuario_unidad_empresa(monkeypatch):
    monkeypatch.setattr(
        repo,
        "resolver_empresa_id_desde_unidad",
        lambda unidad_pk: 7,
    )

    monkeypatch.setattr(
        repo,
        "_leer_config_empresa",
        lambda empresa_id: {
            "MargenMinimoPorcentaje": 30,
            "MultiploRedondeo": 5,
            "MetodoRedondeo": "ARRIBA",
        },
    )

    monkeypatch.setattr(
        repo,
        "_leer_config_unidad",
        lambda empresa_id, unidad_pk: {
            "MargenMinimoPorcentaje": 35,
            "MultiploRedondeo": None,
            "MetodoRedondeo": "MAS_CERCANO",
        },
    )

    monkeypatch.setattr(
        repo,
        "_leer_config_usuario",
        lambda usuario_id: {
            "MargenMinimoPorcentaje": None,
            "MultiploRedondeo": 10,
            "MetodoRedondeo": None,
        },
    )

    result = repo.resolver_configuracion_efectiva(
        "11111111-1111-1111-1111-111111111111",
        usuario_id=99,
    )

    assert result["empresa_id"] == 7

    assert result["margen_minimo_porcentaje"] == 35
    assert result["fuentes"]["margen_minimo_porcentaje"] == "UNIDAD"

    assert result["multiplo_redondeo"] == 10
    assert result["fuentes"]["multiplo_redondeo"] == "USUARIO"

    assert result["metodo_redondeo"] == "MAS_CERCANO"
    assert result["fuentes"]["metodo_redondeo"] == "UNIDAD"


def test_null_no_inventa_default(monkeypatch):
    monkeypatch.setattr(
        repo,
        "resolver_empresa_id_desde_unidad",
        lambda unidad_pk: 7,
    )

    monkeypatch.setattr(repo, "_leer_config_empresa", lambda empresa_id: None)
    monkeypatch.setattr(
        repo,
        "_leer_config_unidad",
        lambda empresa_id, unidad_pk: None,
    )
    monkeypatch.setattr(repo, "_leer_config_usuario", lambda usuario_id: None)

    result = repo.resolver_configuracion_efectiva(
        "11111111-1111-1111-1111-111111111111",
        usuario_id=99,
    )

    assert result["margen_minimo_porcentaje"] is None
    assert result["multiplo_redondeo"] is None
    assert result["metodo_redondeo"] is None

    assert result["fuentes"]["margen_minimo_porcentaje"] is None
    assert result["fuentes"]["multiplo_redondeo"] is None
    assert result["fuentes"]["metodo_redondeo"] is None


def test_unidad_es_obligatoria():
    try:
        repo.resolver_configuracion_efectiva("")
    except ValueError as exc:
        assert str(exc) == "UNIDAD_NEGOCIO_PK_REQUERIDA"
    else:
        raise AssertionError("Debio rechazar unidad vacia")


def test_empresa_no_resuelta_falla_cerrado(monkeypatch):
    monkeypatch.setattr(
        repo,
        "resolver_empresa_id_desde_unidad",
        lambda unidad_pk: None,
    )

    try:
        repo.resolver_configuracion_efectiva(
            "11111111-1111-1111-1111-111111111111"
        )
    except ValueError as exc:
        assert str(exc) == "EMPRESA_NO_RESUELTA_DESDE_UNIDAD"
    else:
        raise AssertionError("Debio fallar cerrado")
