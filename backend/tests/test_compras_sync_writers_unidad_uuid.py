import ast
from pathlib import Path

import pytest


TARGET = (
    Path(__file__).resolve().parents[1]
    / "modules"
    / "compras"
    / "sync_service.py"
)


def _source():
    return TARGET.read_text(encoding="utf-8")


def _tree():
    return ast.parse(_source())


def _get_function(name):
    for node in _tree().body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return node
    raise AssertionError(f"Funcion no encontrada: {name}")


def _merge_execute(function_name, table):
    fn = _get_function(function_name)

    matches = []

    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue

        func = node.func

        if not (
            isinstance(func, ast.Attribute)
            and func.attr == "execute"
            and isinstance(func.value, ast.Name)
            and func.value.id == "cursor"
        ):
            continue

        if len(node.args) < 2:
            continue

        sql_node = node.args[0]
        params_node = node.args[1]

        if not (
            isinstance(sql_node, ast.Constant)
            and isinstance(sql_node.value, str)
        ):
            continue

        if f"MERGE INTO {table} AS target" not in sql_node.value:
            continue

        matches.append((sql_node.value, params_node))

    assert len(matches) == 1, (
        f"{function_name}/{table}: "
        f"se esperaba 1 MERGE, encontrados {len(matches)}"
    )

    return matches[0]


@pytest.mark.parametrize(
    "function_name,table",
    [
        ("sync_pedidos_from_server", "Compras_Pedidos"),
        ("sync_ordenes_from_server", "Compras_Ordenes"),
        ("sync_recepciones_from_server", "Compras_Recepciones"),
    ],
)
def test_writer_obtiene_uuid_del_contexto(function_name, table):
    fn = _get_function(function_name)

    found = False

    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign):
            continue

        if len(node.targets) != 1:
            continue

        target = node.targets[0]

        if not (
            isinstance(target, ast.Name)
            and target.id == "unidad_negocio_pk"
        ):
            continue

        value = node.value

        if not (
            isinstance(value, ast.Subscript)
            and isinstance(value.value, ast.Name)
            and value.value.id == "ctx"
        ):
            continue

        key = value.slice

        if isinstance(key, ast.Constant) and key.value == "unidad_negocio_pk":
            found = True
            break

    assert found, (
        f"{function_name}: unidad_negocio_pk "
        "no proviene de ctx['unidad_negocio_pk']"
    )


@pytest.mark.parametrize(
    "function_name,table,expected",
    [
        (
            "sync_pedidos_from_server",
            "Compras_Pedidos",
            [
                "empresa_id",
                "sucursal_id",
                "folio",
                "total",
                "unidad_negocio_pk",
                "folio",
                "empresa_id",
                "sucursal_id",
                "unidad_negocio_pk",
                "fecha",
                "total",
                "total",
            ],
        ),
        (
            "sync_ordenes_from_server",
            "Compras_Ordenes",
            [
                "empresa_id",
                "sucursal_id",
                "folio",
                "total",
                "unidad_negocio_pk",
                "folio",
                "empresa_id",
                "sucursal_id",
                "unidad_negocio_pk",
                "fecha",
                "proveedor_id",
                "total",
                "total",
            ],
        ),
        (
            "sync_recepciones_from_server",
            "Compras_Recepciones",
            [
                "empresa_id",
                "sucursal_id",
                "folio",
                "total",
                "unidad_negocio_pk",
                "folio",
                "empresa_id",
                "sucursal_id",
                "unidad_negocio_pk",
                "almacen_id",
                "proveedor_id",
                "fecha",
                "total",
                "total",
            ],
        ),
    ],
)
def test_merge_uuid_y_parametros_exactos(
    function_name,
    table,
    expected,
):
    sql, params = _merge_execute(function_name, table)

    assert "unidad_negocio_pk = %s" in sql
    assert "unidad_negocio_pk" in sql

    assert isinstance(params, ast.Tuple)

    actual = []

    for item in params.elts:
        assert isinstance(item, ast.Name), (
            f"{function_name}: parametro no simple: "
            f"{ast.dump(item, include_attributes=False)}"
        )
        actual.append(item.id)

    assert sql.count("%s") == len(actual)
    assert actual == expected


def test_contexto_no_contiene_defaults_legacy():
    fn = _get_function("_get_edarsahub_context")
    text = ast.get_source_segment(_source(), fn)

    assert text is not None

    assert "empresa_id = 1" not in text
    assert "sucursal_id = 1" not in text

    assert "resolver_empresa_id" in text
    assert "resolver_sucursal_id" in text

    assert "UNIDAD_NEGOCIO_PK_NO_RESUELTA" in text
    assert "EMPRESA_CANONICA_NO_RESUELTA" in text
    assert "SUCURSAL_CANONICA_NO_RESUELTA" in text


def test_contexto_falla_cerrado_si_falta_uuid():
    fn = _get_function("_get_edarsahub_context")

    raises = []

    for node in ast.walk(fn):
        if isinstance(node, ast.Raise):
            raises.append(
                ast.get_source_segment(_source(), node) or ""
            )

    joined = "\n".join(raises)

    assert "UNIDAD_NEGOCIO_PK_NO_RESUELTA" in joined


def test_no_writer_inventa_uuid():
    for function_name in (
        "sync_pedidos_from_server",
        "sync_ordenes_from_server",
        "sync_recepciones_from_server",
    ):
        fn = _get_function(function_name)
        text = ast.get_source_segment(_source(), fn)

        assert text is not None

        assert "unidad_negocio_pk = ctx['unidad_negocio_pk']" in text

        assert "uuid.uuid4" not in text
        assert "uuid4(" not in text
        assert "unidad_negocio_pk = 1" not in text
        assert "unidad_negocio_pk = '1'" not in text
