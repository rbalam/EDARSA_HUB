from pathlib import Path
import ast


ROUTES = Path(__file__).resolve().parents[1] / "modules" / "admin_sql" / "routes.py"


def _function_source(name: str) -> str:
    source = ROUTES.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return ast.get_source_segment(source, node) or ""

    raise AssertionError(f"Funcion no encontrada: {name}")


def test_get_catalogos_uses_config_as_registry():
    src = _function_source("get_catalogos_disponibles")

    assert "dbo.Sistema_CatalogosConfig" in src
    assert "ISNULL(Activo, 1) = 1" in src


def test_get_catalogos_does_not_expand_registry_from_permissions():
    src = _function_source("get_catalogos_disponibles")

    assert "FROM dbo.Sistema_CatalogosPermisos" not in src


def test_get_catalogos_does_not_expand_registry_from_requests():
    src = _function_source("get_catalogos_disponibles")

    assert "FROM dbo.Sistema_CatalogosSolicitudes" not in src


def test_save_validates_catalog_against_config():
    src = _function_source("save_permisos_catalogos")

    assert "FROM dbo.Sistema_CatalogosConfig" in src
    assert "ISNULL(Activo, 1) = 1" in src


def test_save_does_not_use_permissions_as_registry():
    src = _function_source("save_permisos_catalogos")

    validation_start = src.index("for raw in catalogos:")
    validation_src = src[validation_start:]

    before_update = validation_src.index(
        "UPDATE dbo.Sistema_CatalogosPermisos"
    )

    registry_validation = validation_src[:before_update]

    assert "FROM dbo.Sistema_CatalogosPermisos" not in registry_validation


def test_save_does_not_use_requests_as_registry():
    src = _function_source("save_permisos_catalogos")

    validation_start = src.index("for raw in catalogos:")
    validation_src = src[validation_start:]

    before_update = validation_src.index(
        "UPDATE dbo.Sistema_CatalogosPermisos"
    )

    registry_validation = validation_src[:before_update]

    assert "FROM dbo.Sistema_CatalogosSolicitudes" not in registry_validation


def test_permission_table_remains_permission_store():
    src = _function_source("save_permisos_catalogos")

    assert "UPDATE dbo.Sistema_CatalogosPermisos" in src
    assert "INSERT INTO dbo.Sistema_CatalogosPermisos" in src


def test_no_usuario_modulos_registry_in_catalog_runtime():
    get_src = _function_source("get_catalogos_disponibles").upper()
    save_src = _function_source("save_permisos_catalogos").upper()

    forbidden = (
        "FROM DBO.USUARIO_MODULOS",
        "JOIN DBO.USUARIO_MODULOS",
        "FROM USUARIO_MODULOS",
        "JOIN USUARIO_MODULOS",
    )

    for token in forbidden:
        assert token not in get_src
        assert token not in save_src
