from pathlib import Path

import core.inventarios.resolver_canonico as rc


def setup_function():
    rc.clear_resolver_caches()


def test_resolver_sucursal_no_depende_de_tabla_legacy():
    source = Path(
        rc.__file__
    ).read_text(encoding="utf-8")

    start = source.index(
        "def resolver_sucursal_id("
    )

    end = source.index(
        "# Resolución de TIPO DE MOVIMIENTO",
        start,
    )

    function_source = source[start:end]

    assert (
        "Sistema_SucursalServidorMapeo"
        not in function_source
    )
    assert "Mongo" not in function_source
    assert "0021" not in function_source
    assert "0023" not in function_source
    assert "130QRO" not in function_source
    assert '"ORIGEN"' not in function_source
    assert "'ORIGEN'" not in function_source


def test_sucursal_softrestaurant_resuelve_por_unidad_canonica():
    unidad = rc.get_server_by_unidad_codigo(
        "CIENFUEGOS"
    )

    server_id = (
        unidad.get("server_id")
        or unidad.get("id")
    )

    res = rc.resolver_sucursal_id(
        str(server_id)
    )

    assert res.resuelto is True
    assert res.canonical_id == 3


def test_mpro_sin_sucursal_origen_es_ambiguo():
    unidad = rc.get_server_by_unidad_codigo(
        "ORIGEN"
    )

    server_id = (
        unidad.get("server_id")
        or unidad.get("id")
    )

    res = rc.resolver_sucursal_id(
        str(server_id)
    )

    assert res.resuelto is False
    assert res.motivo == "AMBIGUO_MULTISUCURSAL"


def test_mpro_resuelve_unidades_sin_hardcode():
    origen = rc.get_server_by_unidad_codigo(
        "ORIGEN"
    )
    qro = rc.get_server_by_unidad_codigo(
        "130QRO"
    )

    origen_server = (
        origen.get("server_id")
        or origen.get("id")
    )
    qro_server = (
        qro.get("server_id")
        or qro.get("id")
    )

    origen_scope = origen.get(
        "sucursal_origen_id"
    )
    qro_scope = qro.get(
        "sucursal_origen_id"
    )

    r_origen = rc.resolver_sucursal_id(
        str(origen_server),
        origen_scope,
    )
    r_qro = rc.resolver_sucursal_id(
        str(qro_server),
        qro_scope,
    )

    assert r_origen.resuelto is True
    assert r_qro.resuelto is True

    assert r_origen.canonical_id == 1
    assert r_qro.canonical_id == 2


def test_scope_mpro_inexistente_fail_closed():
    unidad = rc.get_server_by_unidad_codigo(
        "ORIGEN"
    )

    server_id = (
        unidad.get("server_id")
        or unidad.get("id")
    )

    res = rc.resolver_sucursal_id(
        str(server_id),
        "SUCURSAL_QUE_NO_EXISTE",
    )

    assert res.resuelto is False
    assert res.canonical_id is None
    assert res.motivo == "PENDIENTE_SIN_MAPEO"
