import pytest

from modules.costos_margenes import reglas_margen_repository as repo
from modules.costos_margenes import reglas_margen_service as service


def _base_kwargs(**overrides):
    data = {
        "nivel_aplicacion": "PRODUCTO",
        "entidad_codigo": "",
        "margen_esperado": 65.0,
        "producto_id": None,
        "empresa_id": None,
        "sucursal_id": None,
    }
    data.update(overrides)
    return data


def test_producto_nuevo_sin_productoid_falla_cerrado(monkeypatch):
    def no_sql(*args, **kwargs):
        raise AssertionError("No debe consultar SQL sin ProductoID")

    monkeypatch.setattr(
        service,
        "execute_sql_query_params",
        no_sql,
    )

    with pytest.raises(service.AlertasMargenError) as exc:
        service.crear_regla_margen(
            **_base_kwargs()
        )

    assert exc.value.codigo == "PRODUCTO_ID_CANONICO_REQUERIDO"


def test_producto_id_inexistente_falla_cerrado(monkeypatch):
    monkeypatch.setattr(
        service,
        "_get_conn",
        lambda: ("host", 1433, "db", "user", "password"),
    )

    calls = []

    def fake_query(*args):
        calls.append(args)
        return []

    monkeypatch.setattr(
        service,
        "execute_sql_query_params",
        fake_query,
    )

    with pytest.raises(service.AlertasMargenError) as exc:
        service.crear_regla_margen(
            **_base_kwargs(producto_id=999999)
        )

    assert exc.value.codigo == "PRODUCTO_ID_CANONICO_NO_EXISTE"
    assert len(calls) == 1

    query = calls[0][-2]
    params = calls[0][-1]

    assert "Producto_Catalogo" in query
    assert "ProductoID = %s" in query
    assert params == (999999,)


def test_producto_id_valido_se_propaga_a_repository(monkeypatch):
    monkeypatch.setattr(
        service,
        "_get_conn",
        lambda: ("host", 1433, "db", "user", "password"),
    )

    monkeypatch.setattr(
        service,
        "execute_sql_query_params",
        lambda *args: [{"ProductoID": 101}],
    )

    duplicate_calls = []

    def fake_duplicate(
        nivel_aplicacion,
        entidad_codigo,
        empresa_id=None,
        sucursal_id=None,
        excluir_regla_id=None,
        producto_id=None,
    ):
        duplicate_calls.append(
            {
                "nivel_aplicacion": nivel_aplicacion,
                "entidad_codigo": entidad_codigo,
                "producto_id": producto_id,
            }
        )
        return False

    monkeypatch.setattr(
        service,
        "verificar_duplicado_regla",
        fake_duplicate,
    )

    create_calls = []

    def fake_create(**kwargs):
        create_calls.append(kwargs)
        return {
            "regla_id": "TEST-101",
            "producto_id": kwargs["producto_id"],
        }

    monkeypatch.setattr(
        service,
        "crear_regla",
        fake_create,
    )

    result = service.crear_regla_margen(
        **_base_kwargs(producto_id=101)
    )

    assert result["producto_id"] == 101

    assert duplicate_calls == [
        {
            "nivel_aplicacion": "PRODUCTO",
            "entidad_codigo": "",
            "producto_id": 101,
        }
    ]

    assert len(create_calls) == 1
    assert create_calls[0]["producto_id"] == 101
    assert create_calls[0]["nivel_aplicacion"] == "PRODUCTO"


def test_producto_duplicado_se_evalua_por_productoid(monkeypatch):
    monkeypatch.setattr(
        service,
        "_get_conn",
        lambda: ("host", 1433, "db", "user", "password"),
    )

    monkeypatch.setattr(
        service,
        "execute_sql_query_params",
        lambda *args: [{"ProductoID": 101}],
    )

    observed = {}

    def fake_duplicate(
        nivel_aplicacion,
        entidad_codigo,
        empresa_id=None,
        sucursal_id=None,
        excluir_regla_id=None,
        producto_id=None,
    ):
        observed["producto_id"] = producto_id
        observed["nivel"] = nivel_aplicacion
        return True

    monkeypatch.setattr(
        service,
        "verificar_duplicado_regla",
        fake_duplicate,
    )

    def must_not_create(**kwargs):
        raise AssertionError(
            "Una regla duplicada no debe persistirse"
        )

    monkeypatch.setattr(
        service,
        "crear_regla",
        must_not_create,
    )

    with pytest.raises(service.AlertasMargenError) as exc:
        service.crear_regla_margen(
            **_base_kwargs(producto_id=101)
        )

    assert exc.value.codigo == "REGLA_DUPLICADA"
    assert observed == {
        "producto_id": 101,
        "nivel": "PRODUCTO",
    }


@pytest.mark.parametrize(
    "nivel,codigo",
    [
        ("GRUPO", "G01"),
        ("FAMILIA", "F01"),
        ("SUBFAMILIA", "SF01"),
    ],
)
def test_niveles_no_producto_conservan_entidad_codigo(
    monkeypatch,
    nivel,
    codigo,
):
    duplicate_calls = []
    create_calls = []

    def fake_duplicate(
        nivel_aplicacion,
        entidad_codigo,
        empresa_id=None,
        sucursal_id=None,
        excluir_regla_id=None,
        producto_id=None,
    ):
        duplicate_calls.append(
            (
                nivel_aplicacion,
                entidad_codigo,
                producto_id,
            )
        )
        return False

    def fake_create(**kwargs):
        create_calls.append(kwargs)
        return {
            "regla_id": "TEST-NON-PRODUCT",
            "nivel_aplicacion": kwargs[
                "nivel_aplicacion"
            ],
        }

    monkeypatch.setattr(
        service,
        "verificar_duplicado_regla",
        fake_duplicate,
    )

    monkeypatch.setattr(
        service,
        "crear_regla",
        fake_create,
    )

    result = service.crear_regla_margen(
        nivel_aplicacion=nivel,
        entidad_codigo=codigo,
        margen_esperado=65.0,
    )

    assert result["nivel_aplicacion"] == nivel

    assert duplicate_calls == [
        (nivel, codigo, None)
    ]

    assert create_calls[0]["entidad_codigo"] == codigo
    assert create_calls[0]["producto_id"] is None


def test_repository_duplicado_producto_usa_productoid(monkeypatch):
    monkeypatch.setattr(
        repo,
        "_get_conn",
        lambda: ("host", 1433, "db", "user", "password"),
    )

    observed = {}

    def fake_execute(*args):
        observed["query"] = args[-2]
        observed["params"] = args[-1]
        return [{"cnt": 1}]

    monkeypatch.setattr(
        repo,
        "execute_sql_query_params",
        fake_execute,
    )

    result = repo.verificar_duplicado_regla(
        nivel_aplicacion="PRODUCTO",
        entidad_codigo="RIBEYE-500",
        producto_id=101,
    )

    assert result is True

    query = observed["query"]

    assert "ProductoID = %s" in query
    assert "ProductoClave" not in query
    assert "RIBEYE-500" not in query
    assert observed["params"][0:2] == (
        "PRODUCTO",
        101,
    )


def test_repository_insert_producto_usa_columna_productoid(
    monkeypatch,
):
    monkeypatch.setattr(
        repo,
        "_get_conn",
        lambda: ("host", 1433, "db", "user", "password"),
    )

    observed = {}

    def fake_execute(*args):
        observed["query"] = args[-2]
        observed["params"] = args[-1]
        return []

    monkeypatch.setattr(
        repo,
        "execute_sql_query_params",
        fake_execute,
    )

    monkeypatch.setattr(
        repo,
        "obtener_regla_por_id",
        lambda regla_id: {
            "regla_id": regla_id,
            "producto_id": 101,
        },
    )

    result = repo.crear_regla(
        nivel_aplicacion="PRODUCTO",
        entidad_codigo="RIBEYE-500",
        margen_esperado=65.0,
        producto_id=101,
    )

    assert result["producto_id"] == 101

    query = observed["query"]

    assert "ProductoID" in query
    assert "ProductoClave" not in query
    assert "RIBEYE-500" not in query
    assert "%s" in query
    assert observed["params"][1] == "PRODUCTO"
    assert observed["params"][2] == 101


def test_repository_fecha_inicio_omitida_usa_getdate_sql(
    monkeypatch,
):
    monkeypatch.setattr(
        repo,
        "_get_conn",
        lambda: ("host", 1433, "db", "user", "password"),
    )

    observed = {}

    def fake_execute(*args):
        observed["query"] = args[-2]
        observed["params"] = args[-1]
        return []

    monkeypatch.setattr(
        repo,
        "execute_sql_query_params",
        fake_execute,
    )

    monkeypatch.setattr(
        repo,
        "obtener_regla_por_id",
        lambda regla_id: {"regla_id": regla_id},
    )

    repo.crear_regla(
        nivel_aplicacion="PRODUCTO",
        entidad_codigo="",
        margen_esperado=65.0,
        producto_id=101,
        fecha_inicio=None,
    )

    assert "GETDATE()" in observed["query"]

    # 14 parametros cuando fecha_inicio no se envia:
    # fecha_inicio no debe agregarse al tuple.
    assert len(observed["params"]) == 13


def test_repository_fecha_inicio_explicita_es_parametro(
    monkeypatch,
):
    from datetime import datetime

    monkeypatch.setattr(
        repo,
        "_get_conn",
        lambda: ("host", 1433, "db", "user", "password"),
    )

    observed = {}

    def fake_execute(*args):
        observed["query"] = args[-2]
        observed["params"] = args[-1]
        return []

    monkeypatch.setattr(
        repo,
        "execute_sql_query_params",
        fake_execute,
    )

    monkeypatch.setattr(
        repo,
        "obtener_regla_por_id",
        lambda regla_id: {"regla_id": regla_id},
    )

    fecha = datetime(2026, 8, 15, 4, 30, 0)

    repo.crear_regla(
        nivel_aplicacion="PRODUCTO",
        entidad_codigo="",
        margen_esperado=65.0,
        producto_id=101,
        fecha_inicio=fecha,
    )

    assert fecha in observed["params"]


def test_listar_reglas_expone_productoid_canonico(monkeypatch):
    from modules.costos_margenes import reglas_margen_repository as repo

    calls = []

    def fake_execute(*args):
        query = args[-2]
        calls.append(query)

        if "COUNT(*)" in query:
            return [{"total": 1}]

        return [{
            "regla_id": "R1",
            "nivel_aplicacion": "PRODUCTO",
            "grupo_codigo": None,
            "familia_codigo": None,
            "subfamilia_codigo": None,
            "producto_clave": None,
            "producto_id": 321,
            "margen_esperado": 30,
            "costo_maximo": None,
            "utilidad_minima": None,
            "severidad_base": "MEDIA",
            "descripcion": None,
            "activo": 1,
            "fecha_inicio": None,
            "fecha_fin": None,
            "fecha_creacion": None,
            "fecha_modificacion": None,
            "creado_por": "TEST",
            "modificado_por": None,
        }]

    monkeypatch.setattr(
        repo,
        "_get_conn",
        lambda: ("conn",),
    )

    monkeypatch.setattr(
        repo,
        "execute_sql_query_params",
        fake_execute,
    )

    reglas, total = repo.listar_reglas()

    assert total == 1
    assert reglas[0]["producto_id"] == 321
    assert reglas[0]["entidad_codigo"] == "321"

    data_queries = [
        q
        for q in calls
        if "COUNT(*)" not in q
    ]

    assert len(data_queries) == 1
    assert (
        "ProductoID as producto_id"
        in data_queries[0]
    )


def test_obtener_regla_expone_productoid_canonico(monkeypatch):
    from modules.costos_margenes import reglas_margen_repository as repo

    captured = {}

    def fake_execute(*args):
        captured["query"] = args[-2]

        return [{
            "regla_id": "R1",
            "nivel_aplicacion": "PRODUCTO",
            "grupo_codigo": None,
            "familia_codigo": None,
            "subfamilia_codigo": None,
            "producto_clave": None,
            "producto_id": 654,
            "margen_esperado": 35,
            "costo_maximo": None,
            "utilidad_minima": None,
            "severidad_base": "MEDIA",
            "descripcion": None,
            "activo": 1,
            "fecha_inicio": None,
            "fecha_fin": None,
            "fecha_creacion": None,
            "fecha_modificacion": None,
            "creado_por": "TEST",
            "modificado_por": None,
        }]

    monkeypatch.setattr(
        repo,
        "_get_conn",
        lambda: ("conn",),
    )

    monkeypatch.setattr(
        repo,
        "execute_sql_query_params",
        fake_execute,
    )

    regla = repo.obtener_regla_por_id("R1")

    assert regla["producto_id"] == 654
    assert regla["entidad_codigo"] == "654"

    assert (
        "ProductoID as producto_id"
        in captured["query"]
    )

