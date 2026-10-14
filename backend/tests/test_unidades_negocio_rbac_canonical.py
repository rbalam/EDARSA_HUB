import ast
from pathlib import Path


SERVER = Path(__file__).parents[1] / "server.py"


def _endpoint_source():
    src = SERVER.read_text(encoding="utf-8")
    tree = ast.parse(src)

    node = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.AsyncFunctionDef)
        and n.name == "get_unidades_negocio"
    )

    return ast.get_source_segment(src, node) or ""


def test_unidades_negocio_no_usa_allowed_servers_legacy():
    block = _endpoint_source()
    assert "current_user.get('allowed_servers'" not in block
    assert "RBACSQLService.get_unidades" in block
    assert "resolve_sql_usuario_id" in block


def test_unidades_negocio_filtra_por_unidad_canonica():
    block = _endpoint_source()
    assert "UnidadNegocioID" in block
    assert "u.get('id')" in block
    assert "unidades_ids" in block


def test_unidades_negocio_preserva_sucursal_de_unidad():
    block = _endpoint_source()
    assert '"sucursales": [{' in block
    assert "sucursal_origen_id or u.get('codigo')" in block


def test_unidades_negocio_preserva_admin_global():
    block = _endpoint_source()
    assert "is_admin_global" in block
    assert "unidades_filtradas = unidades_sql" in block
