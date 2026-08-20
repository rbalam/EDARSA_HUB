from pathlib import Path
import ast


ROOT = Path("/app")
ROUTES = ROOT / "backend/modules/catalogos/routes.py"
SCHEMAS = ROOT / "backend/modules/catalogos/schemas.py"


def _routes():
    return ROUTES.read_text(encoding="utf-8")


def _schemas():
    return SCHEMAS.read_text(encoding="utf-8")


def test_routes_compile_as_python():
    ast.parse(_routes())


def test_tipo_autorizacion_schema_uses_current_canonical_columns():
    src = _schemas()

    assert '"CodigoTipoAutorizacion"' in src
    assert '"NombreTipoAutorizacion"' in src
    assert '"AccionID"' in src
    assert '"RequiereUnidadNegocio"' in src


def test_tipo_autorizacion_schema_does_not_expose_legacy_columns():
    src = _schemas()

    block = src.split('"Usuario_TiposAutorizacion": {', 1)[1]
    block = block.split("# === HOMOLOGACIÓN ===", 1)[0]

    assert '"Codigo"' not in block
    assert '"NivelesRequeridos"' not in block


def test_matrix_read_endpoint_exists():
    src = _routes()

    assert (
        '@router.get("/autorizaciones/tipos/{tipo_autorizacion_id}/matriz")'
        in src
    )
    assert "dbo.Usuario_MatrizAutorizacion" in src


def test_matrix_selector_catalog_endpoint_exists():
    src = _routes()

    assert '@router.get("/autorizaciones/catalogos")' in src

    assert "dbo.Usuario_Roles" in src
    assert "dbo.Usuario_Modulos" in src
    assert "dbo.Usuario_Acciones" in src
    assert "dbo.Usuario_Catalogo" in src


def test_matrix_read_endpoints_remain_read_only():
    src = _routes()

    start = src.index(
        '@router.get("/autorizaciones/tipos/{tipo_autorizacion_id}/matriz")'
    )
    end = src.index(
        '@router.get("/autorizaciones/catalogos")',
        start,
    )

    block = src[start:end].upper()

    assert "INSERT INTO" not in block
    assert "UPDATE DBO." not in block
    assert "DELETE FROM" not in block


def test_matrix_selector_endpoint_remains_read_only():
    src = _routes()

    start = src.index(
        '@router.get("/autorizaciones/catalogos")'
    )
    end = src.index(
        '@router.post("/autorizaciones/tipos/{tipo_autorizacion_id}/matriz")',
        start,
    )

    block = src[start:end].upper()

    assert "INSERT INTO" not in block
    assert "UPDATE DBO." not in block
    assert "DELETE FROM" not in block


def test_matrix_queries_are_parameterized_for_ids():
    src = _routes()

    start = src.index(
        'async def obtener_matriz_autorizacion('
    )
    end = src.index(
        '@router.get("/autorizaciones/catalogos")',
        start,
    )

    block = src[start:end]

    assert "WHERE TA.TipoAutorizacionID = %s" in block
    assert "WHERE MA.TipoAutorizacionID = %s" in block


def test_no_new_authorization_source_of_truth_created():
    src = _routes()

    assert "CREATE TABLE" not in src
    assert "Mongo" not in src[
        src.index("# MATRICES DE AUTORIZACION - CONSULTA CANONICA"):
        src.index("# ENDPOINTS DE ADMINISTRACIÓN")
    ]


def test_matrix_admin_requires_explicit_seguridad_configurar():
    src = _routes()

    assert (
        'require_explicit_permission("SEGURIDAD_CONFIGURAR")'
        in src
    )


def test_matrix_admin_does_not_use_legacy_admin_bypass():
    src = _routes()

    start = src.index(
        "# MATRICES DE AUTORIZACION - CONSULTA CANONICA"
    )
    end = src.index(
        "# ENDPOINTS DE ADMINISTRACIÓN",
        start,
    )

    block = src[start:end]

    assert "es_admin(" not in block
    assert "es_superadmin(" not in block
    assert "es_supervisor_o_superior(" not in block
    assert "require_admin(" not in block


def test_matrix_admin_permission_is_not_unrelated_domain_permission():
    src = _routes()

    start = src.index(
        "# MATRICES DE AUTORIZACION - CONSULTA CANONICA"
    )
    end = src.index(
        "# ENDPOINTS DE ADMINISTRACIÓN",
        start,
    )

    block = src[start:end]

    assert "COMPRAS_FACT_CONFIGURAR" not in block
    assert "COSTOS_MARGENES_CONFIGURAR" not in block
    assert "INTELIGENCIA_COMERCIAL_CONFIGURAR" not in block


def test_matrix_write_endpoints_exist():
    src = _routes()

    assert (
        '@router.post("/autorizaciones/tipos/{tipo_autorizacion_id}/matriz")'
        in src
    )
    assert (
        '@router.put("/autorizaciones/matriz/{matriz_autorizacion_id}")'
        in src
    )


def test_matrix_write_endpoints_require_explicit_permission():
    src = _routes()

    assert src.count(
        'require_explicit_permission("SEGURIDAD_CONFIGURAR")'
    ) >= 4


def test_matrix_write_uses_parameterized_sql():
    src = _routes()

    assert "VALUES (" in src
    assert "%s" in src
    assert "WHERE MatrizAutorizacionID = %s" in src


def test_matrix_write_validates_range_overlap():
    src = _routes()

    assert "rango monetario se solapa" in src


def test_matrix_write_validates_user_role_compatibility():
    src = _routes()

    assert "dbo.Usuario_RolesContexto" in src
    assert "UsuarioID no tiene el RolID activo indicado" in src


def test_matrix_write_is_transactional():
    src = _routes()

    assert "conn.commit()" in src
    assert "conn.rollback()" in src


def test_matrix_write_does_not_use_mongodb():
    src = _routes()

    start = src.index(
        '@router.post("/autorizaciones/tipos/{tipo_autorizacion_id}/matriz")'
    )
    end = src.index(
        "# ENDPOINTS DE ADMINISTRACIÓN",
        start,
    )

    block = src[start:end].lower()

    assert "mongodb" not in block
    assert "pymongo" not in block
