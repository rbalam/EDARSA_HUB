from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_finanzas_legacy_presupuestos_exige_rbac_sql_y_alcance_unidad():
    source = read("server.py")

    assert "def _finanzas_require_view_scope" in source
    assert "def _finanzas_require_write_scope" in source
    assert "FINANZAS_VER" in source
    assert "FINANZAS_ADMINISTRAR" in source
    assert "FINANZAS_EDITAR" in source
    assert "CONVERT(varchar(36), p.UnidadNegocioID) IN" in source
    assert "categorias financieras desde presupuestos canonicos" in source
    assert '{"Categoria": "Ventas", "Tipo": "Ingreso"}' not in source


def test_costos_margenes_usa_permiso_y_unidad_canonica_sin_rbac_legacy():
    routes = read("modules/costos_margenes/routes.py")

    assert 'COSTOS_MARGENES_VER = "COMERCIAL_VER"' in routes
    assert "RBACSQLService.get_permission_scope_by_code" in routes
    assert "resolve_authorized_unidad_scope" in routes
    assert "UNIDAD_CANONICA_REQUERIDA" in routes
    assert "get_resumen_costos_margenes(unidad_negocio_pk=unidad_pk)" in routes
    assert "execute_sql_query" not in routes
    assert "tiene_acceso_lectura_comercial" not in routes
    assert "Usuario_ServidoresAsignacion" not in routes
    assert "_mpro_menu_listas_para_unidad" not in routes
    assert "QRO_ORIGEN" not in routes
    assert "QRO" not in routes
    assert "ORIGEN" not in routes
    assert "TODOS" not in routes
    assert "unidad_negocio_pk=unidad_pk_filtro" in routes
    assert "servidores_ids=servidores_ids_filtro" in routes


def test_costos_margenes_productos_parametriza_filtros_usuario():
    repo = read("modules/costos_margenes/repository.py")

    assert "get_resumen_costos_margenes(" in repo
    assert "unidad_negocio_pk: Optional[str] = None" in repo
    assert "execute_sql_query_params(*conn, count_query, tuple(query_params))" in repo
    assert "execute_sql_query_params(*conn, data_query, tuple(query_params))" in repo
    assert "CONVERT(varchar(36), p.UnidadNegocioID) = %s" in repo
    assert "p.SystemType = %s" in repo
    assert "p.Nombre LIKE %s OR p.CodigoFuente LIKE %s" in repo
    assert "p.ServerID = '{servidor_id}'" not in repo
    assert "p.SystemType = '{sistema_origen}'" not in repo
    assert "LIKE '%{busqueda}%'" not in repo
    assert "ProductoCodigoFuentePadded = {prefix}CodigoFuente" in repo
    assert "mpos.Lista IN" not in repo
    assert "listas_sql" not in repo
    assert "mpro_menu_listas" not in repo


def test_layout_fallback_no_abre_modulos_por_rol_legacy():
    layout = read("../frontend/src/pages/Layout.js")

    assert "Falla cerrada: la visibilidad de módulos críticos solo viene de RBAC SQL." in layout
    assert "setMenuPermissions({ mis_tareas: true });" in layout
    assert "programacion: isAdmin" not in layout
    assert "automatizaciones: isAdmin" not in layout
    assert "usuarios: isAdmin" not in layout
