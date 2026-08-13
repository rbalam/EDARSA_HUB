import ast
from pathlib import Path


TARGET = Path(
    "/app/backend/core/inventarios/"
    "canonizacion_productos_service.py"
)


def _source():
    return TARGET.read_text(encoding="utf-8")


def _string_literals():
    tree = ast.parse(_source())

    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
    ]


def test_no_usa_mapeo_legacy():
    src = _source()

    assert "Sistema_SucursalServidorMapeo" not in src
    assert "Sistema_EmpresasMongoMap" not in src
    assert "MongoUUID" not in src
    assert "MongoSucursalUUID" not in src


def test_reutiliza_resolver_canonico():
    src = _source()

    assert (
        "from core.inventarios.resolver_canonico "
        "import resolver_sucursal_id"
    ) in src

    assert "resolver_sucursal_id(" in src


def test_pasa_scope_sucursal_origen():
    src = _source()

    assert (
        'sucursal_origen_id = '
        'u.get("sucursal_origen_id")'
    ) in src

    assert (
        "resolver_sucursal_id(\n"
        "            str(server_id),\n"
        "            sucursal_origen_id,"
    ) in src


def test_no_hardcode_mpro_scope_productivo():
    literals = set(_string_literals())

    assert "0021" not in literals
    assert "0023" not in literals
    assert "130QRO" not in literals

    # ORIGEN puede aparecer legítimamente en documentación,
    # pero no como literal exacto usado como valor funcional.
    assert "ORIGEN" not in literals
