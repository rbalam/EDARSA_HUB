import ast
from pathlib import Path

from core.rbac_sql.service import RBACSQLService


SERVICE = (
    Path(__file__).parents[1]
    / "core"
    / "rbac_sql"
    / "service.py"
)


def _functions():
    src = SERVICE.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(src)
    result = {}

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name in {
                "get_unidades",
                "can_access_unidad",
            }
        ):
            result[node.name] = (
                ast.get_source_segment(
                    src,
                    node,
                )
                or ""
            )

    return result


def test_get_unidades_usa_scope_canonico():
    functions = _functions()
    src = functions["get_unidades"]

    assert "dbo.Unidades_Negocio" in src
    assert (
        "dbo.Usuario_ServidoresAsignacion"
        in src
    )
    assert (
        "dbo.Usuario_SucursalesAsignacion"
        in src
    )
    assert "ActiveUnitsOnServer" in src


def test_get_unidades_no_usa_legacy():
    functions = _functions()

    src = (
        functions["get_unidades"]
        + functions["can_access_unidad"]
    )

    forbidden = (
        "Sistema_Sucursales",
        "Sistema_SucursalServidorMapeo",
        "Sistema_EmpresasMongoMap",
        "Mongo",
        "sc.ServidorID",
        "sc.unidad_negocio_id",
        "sc.unidad_negocio_pk",
    )

    for token in forbidden:
        assert token not in src


def test_no_hardcodes_de_unidades():
    functions = _functions()

    src = (
        functions["get_unidades"]
        + functions["can_access_unidad"]
    )

    forbidden = (
        '"0021"',
        "'0021'",
        '"0023"',
        "'0023'",
        '"130QRO"',
        "'130QRO'",
        '"ORIGEN"',
        "'ORIGEN'",
    )

    for token in forbidden:
        assert token not in src


def test_can_access_unidad_fail_closed_sql_error(
    monkeypatch,
):
    def boom(usuario_id):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        RBACSQLService,
        "get_unidades",
        boom,
    )

    assert not RBACSQLService.can_access_unidad(
        17,
        "unit-a",
    )


def test_can_access_unidad_match_exacto(
    monkeypatch,
):
    monkeypatch.setattr(
        RBACSQLService,
        "get_unidades",
        lambda usuario_id: [
            {
                "UnidadNegocioID":
                    "ABC-123",
            }
        ],
    )

    assert RBACSQLService.can_access_unidad(
        17,
        "abc-123",
    )

    assert not RBACSQLService.can_access_unidad(
        17,
        "xyz-999",
    )


def test_can_access_unidad_inputs_invalidos():
    assert not RBACSQLService.can_access_unidad(
        None,
        "abc",
    )

    assert not RBACSQLService.can_access_unidad(
        17,
        None,
    )

    assert not RBACSQLService.can_access_unidad(
        17,
        "",
    )
