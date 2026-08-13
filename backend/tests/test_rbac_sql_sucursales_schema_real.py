import ast
from pathlib import Path

from core.rbac_sql.service import RBACSQLService


SERVICE = (
    Path(__file__).parents[1]
    / "core"
    / "rbac_sql"
    / "service.py"
)


def _source(name):
    src = SERVICE.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(src)

    node = next(
        n
        for n in ast.walk(tree)
        if isinstance(
            n,
            ast.FunctionDef,
        )
        and n.name == name
    )

    return (
        ast.get_source_segment(
            src,
            node,
        )
        or ""
    )


def test_get_sucursales_usa_schema_real():
    src = _source(
        "get_sucursales"
    )

    assert (
        "dbo.Usuario_SucursalesAsignacion"
        in src
    )

    assert "UsuarioID" in src
    assert "ServidorID" in src
    assert "SucursalCodigo" in src

    assert "EmpresaID" not in src
    assert "Sistema_Sucursales" not in src
    assert "Sistema_SucursalServidorMapeo" not in src
    assert "Sistema_EmpresasMongoMap" not in src


def test_build_context_preserva_sucursales(
    monkeypatch,
):
    monkeypatch.setattr(
        RBACSQLService,
        "get_roles",
        lambda usuario_id: [],
    )

    monkeypatch.setattr(
        RBACSQLService,
        "get_empresas",
        lambda usuario_id: [],
    )

    monkeypatch.setattr(
        RBACSQLService,
        "get_sucursales",
        lambda usuario_id: [
            {
                "UsuarioID": usuario_id,
                "ServidorID": "srv-a",
                "SucursalCodigo": "suc-a",
            }
        ],
    )

    monkeypatch.setattr(
        RBACSQLService,
        "get_servidores",
        lambda usuario_id: [],
    )

    monkeypatch.setattr(
        RBACSQLService,
        "get_unidades",
        lambda usuario_id: [],
    )

    ctx = RBACSQLService.build_context(
        17
    )

    assert ctx["sucursales"] == [
        {
            "UsuarioID": 17,
            "ServidorID": "srv-a",
            "SucursalCodigo": "suc-a",
        }
    ]
