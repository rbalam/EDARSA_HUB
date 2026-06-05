from fastapi import APIRouter, Query, Body
from typing import Dict, Any, List, Optional
import os
import logging

from core.db import execute_sql_query
from core.config.edarsahub_config import get_edarsahub_sql_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/corporate-filters", tags=["Corporate Filters"])


# ============================================================
# Configuración SQL EDARSAHUB (P2-01: Centralizado)
# ============================================================

def get_sql_config():
    """P2-01: Usa config centralizado."""
    cfg = get_edarsahub_sql_config()
    return cfg.host, cfg.port, cfg.database, cfg.user, cfg.password


def sql_query(query: str) -> List[Dict[str, Any]]:
    host, port, database, username, password = get_sql_config()
    return execute_sql_query(host, port, database, username, password, query, timeout_seconds=45)


def q(query: str) -> List[Dict[str, Any]]:
    return sql_query(query)


# ============================================================
# Helpers seguros de SQL Server
# ============================================================

def safe_sql_literal(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("'", "''")


def object_exists(object_name: str, object_type: Optional[str] = None) -> bool:
    obj = safe_sql_literal(object_name)
    if object_type:
        typ = safe_sql_literal(object_type)
        sql = f"SELECT OBJECT_ID('dbo.{obj}', '{typ}') AS object_id"
    else:
        sql = f"SELECT OBJECT_ID('dbo.{obj}') AS object_id"
    rows = sql_query(sql)
    return bool(rows and rows[0].get("object_id") is not None)


def table_exists(table_name: str) -> bool:
    return object_exists(table_name)


def get_columns(table_name: str) -> Dict[str, str]:
    table = safe_sql_literal(table_name)
    sql = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'"
    rows = sql_query(sql)
    return {str(r["COLUMN_NAME"]).lower(): str(r["COLUMN_NAME"]) for r in rows if r.get("COLUMN_NAME")}


def pick_col(cols: Dict[str, str], candidates: List[str]) -> Optional[str]:
    for candidate in candidates:
        key = candidate.lower()
        if key in cols:
            return cols[key]
    return None


def bracket(identifier: str) -> str:
    return "[" + str(identifier).replace("]", "]]") + "]"


def make_select_expr(col: Optional[str], alias: str, cast_varchar: bool = False) -> str:
    if not col:
        return f"CAST(NULL AS NVARCHAR(255)) AS {bracket(alias)}"
    if cast_varchar:
        return f"CAST({bracket(col)} AS NVARCHAR(255)) AS {bracket(alias)}"
    return f"{bracket(col)} AS {bracket(alias)}"


def normalize_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    return bool(value)


def make_option(row: Dict[str, Any], metadata_fields: Optional[List[str]] = None) -> Dict[str, Any]:
    metadata = {}
    for field in metadata_fields or []:
        if field in row:
            metadata[field] = row.get(field)
    return {
        "id": str(row.get("id")) if row.get("id") is not None else None,
        "nombre": str(row.get("nombre") or ""),
        "codigo": str(row.get("codigo")) if row.get("codigo") is not None else None,
        "id_empresa": str(row.get("id_empresa")) if row.get("id_empresa") is not None else None,
        "id_unidad_negocio": str(row.get("id_unidad_negocio")) if row.get("id_unidad_negocio") is not None else None,
        "id_sucursal": str(row.get("id_sucursal")) if row.get("id_sucursal") is not None else None,
        "tipo": str(row.get("tipo")) if row.get("tipo") is not None else None,
        "activo": normalize_bool(row.get("activo"), True),
        "visible_en_operaciones": normalize_bool(row.get("visible_en_operaciones"), True),
        "metadata": metadata
    }


def load_catalog_real(
    table_candidates: List[str],
    id_candidates: List[str],
    name_candidates: List[str],
    code_candidates: Optional[List[str]] = None,
    empresa_candidates: Optional[List[str]] = None,
    unidad_candidates: Optional[List[str]] = None,
    sucursal_candidates: Optional[List[str]] = None,
    activo_candidates: Optional[List[str]] = None,
    visible_candidates: Optional[List[str]] = None,
    tipo_candidates: Optional[List[str]] = None,
    max_rows: int = 5000
) -> List[Dict[str, Any]]:
    code_candidates = code_candidates or []
    empresa_candidates = empresa_candidates or ["id_empresa", "EmpresaID", "empresa_id"]
    unidad_candidates = unidad_candidates or ["id_unidad_negocio", "UnidadNegocioID", "unidad_negocio_id"]
    sucursal_candidates = sucursal_candidates or ["id_sucursal", "SucursalID", "sucursal_id"]
    activo_candidates = activo_candidates or ["activo", "Activo", "is_active"]
    visible_candidates = visible_candidates or ["visible_en_operaciones", "VisibleEnOperaciones"]
    tipo_candidates = tipo_candidates or ["tipo", "tipo_sistema", "system_type"]

    for table in table_candidates:
        if not table_exists(table):
            continue
        cols = get_columns(table)
        id_col = pick_col(cols, id_candidates)
        name_col = pick_col(cols, name_candidates)
        code_col = pick_col(cols, code_candidates)
        empresa_col = pick_col(cols, empresa_candidates)
        unidad_col = pick_col(cols, unidad_candidates)
        sucursal_col = pick_col(cols, sucursal_candidates)
        activo_col = pick_col(cols, activo_candidates)
        visible_col = pick_col(cols, visible_candidates)
        tipo_col = pick_col(cols, tipo_candidates)

        if not id_col or not name_col:
            continue

        select_exprs = [
            make_select_expr(id_col, "id", cast_varchar=True),
            make_select_expr(name_col, "nombre", cast_varchar=True),
            make_select_expr(code_col, "codigo", cast_varchar=True),
            make_select_expr(empresa_col, "id_empresa", cast_varchar=True),
            make_select_expr(unidad_col, "id_unidad_negocio", cast_varchar=True),
            make_select_expr(sucursal_col, "id_sucursal", cast_varchar=True),
            make_select_expr(tipo_col, "tipo", cast_varchar=True),
        ]
        if activo_col:
            select_exprs.append(f"CAST(ISNULL({bracket(activo_col)}, 1) AS BIT) AS [activo]")
        else:
            select_exprs.append("CAST(1 AS BIT) AS [activo]")
        if visible_col:
            select_exprs.append(f"CAST(ISNULL({bracket(visible_col)}, 1) AS BIT) AS [visible_en_operaciones]")
        else:
            select_exprs.append("CAST(1 AS BIT) AS [visible_en_operaciones]")

        where_parts = []
        if activo_col:
            where_parts.append(f"ISNULL({bracket(activo_col)}, 1) = 1")
        where_sql = "WHERE " + " AND ".join(where_parts) if where_parts else ""

        sql = f"SELECT TOP {int(max_rows)} {', '.join(select_exprs)} FROM {bracket(table)} {where_sql} ORDER BY {bracket(name_col)}"
        rows = sql_query(sql)
        return [make_option(row, metadata_fields=["id_empresa", "id_unidad_negocio", "id_sucursal", "tipo"]) for row in rows]
    return []


# ============================================================
# Catálogos corporativos
# ============================================================

def get_empresas() -> List[Dict[str, Any]]:
    return load_catalog_real(
        table_candidates=["Sistema_Empresas"],
        id_candidates=["EmpresaID", "id_empresa", "id"],
        name_candidates=["NombreEmpresa", "nombre", "RazonSocial"],
        code_candidates=["CodigoEmpresa", "codigo", "clave"],
        max_rows=1000
    )


def get_unidades_negocio() -> List[Dict[str, Any]]:
    return load_catalog_real(
        table_candidates=["Unidades_Negocio", "Sistema_UnidadesNegocio"],
        id_candidates=["id", "UnidadNegocioID", "id_unidad_negocio"],
        name_candidates=["nombre", "NombreUnidad", "NombreUnidadNegocio", "descripcion"],
        code_candidates=["codigo", "CodigoUnidad", "CodigoUnidadNegocio"],
        empresa_candidates=["server_id", "EmpresaID", "id_empresa"],
        max_rows=1000
    )


def get_servidores() -> List[Dict[str, Any]]:
    if object_exists("vw_Servidores_Conexiones_Versiones", "V"):
        table = "vw_Servidores_Conexiones_Versiones"
        cols = get_columns(table)
        id_col = pick_col(cols, ["servidor_conexion_id", "id"])
        name_col = pick_col(cols, ["nombre"])
        tipo_col = pick_col(cols, ["tipo_sistema", "system_type"])
        activo_col = pick_col(cols, ["activo"])
        version_id_col = pick_col(cols, ["sistema_version_id"])
        version_sistema_col = pick_col(cols, ["version_sistema"])
        nombre_sistema_col = pick_col(cols, ["nombre_sistema"])

        select_exprs = [
            make_select_expr(id_col, "id", True),
            make_select_expr(name_col, "nombre", True),
            make_select_expr(tipo_col, "codigo", True),
            make_select_expr(tipo_col, "tipo", True),
            make_select_expr(version_id_col, "sistema_version_id", True),
            make_select_expr(version_sistema_col, "version_sistema", True),
            make_select_expr(nombre_sistema_col, "nombre_sistema", True),
        ]
        if activo_col:
            select_exprs.append(f"CAST(ISNULL({bracket(activo_col)}, 1) AS BIT) AS [activo]")
        else:
            select_exprs.append("CAST(1 AS BIT) AS [activo]")
        select_exprs.append("CAST(1 AS BIT) AS [visible_en_operaciones]")

        where_sql = f"WHERE ISNULL({bracket(activo_col)}, 1) = 1" if activo_col else ""
        sql = f"SELECT {', '.join(select_exprs)} FROM {bracket(table)} {where_sql} ORDER BY {bracket(tipo_col) if tipo_col else bracket(name_col)}, {bracket(name_col)}"
        rows = sql_query(sql)
        result = []
        for row in rows:
            item = make_option(row, metadata_fields=["sistema_version_id", "version_sistema", "nombre_sistema", "tipo"])
            item["sistema_version_id"] = row.get("sistema_version_id")
            item["version_sistema"] = row.get("version_sistema")
            item["nombre_sistema"] = row.get("nombre_sistema")
            result.append(item)
        return result

    return load_catalog_real(
        table_candidates=["Servidores_Conexiones"],
        id_candidates=["id", "servidor_conexion_id"],
        name_candidates=["nombre"],
        code_candidates=["system_type", "tipo_sistema"],
        tipo_candidates=["system_type", "tipo_sistema"],
        max_rows=1000
    )


def get_sucursales() -> List[Dict[str, Any]]:
    return load_catalog_real(
        table_candidates=["Sistema_Sucursales", "Sucursales", "Sync_Sucursales"],
        id_candidates=["SucursalID", "id_sucursal", "id"],
        name_candidates=["NombreSucursal", "nombre_sucursal", "nombre", "Sucursal"],
        code_candidates=["CodigoSucursal", "codigo_sucursal", "codigo"],
        empresa_candidates=["EmpresaID", "id_empresa"],
        max_rows=2000
    )


def get_almacenes() -> List[Dict[str, Any]]:
    return load_catalog_real(
        table_candidates=["Inventario_Almacenes", "Sistema_Almacenes", "Almacenes"],
        id_candidates=["AlmacenID", "id_almacen", "id"],
        name_candidates=["NombreAlmacen", "nombre_almacen", "nombre", "Almacen"],
        code_candidates=["CodigoAlmacen", "codigo_almacen", "codigo"],
        empresa_candidates=["EmpresaID", "id_empresa"],
        sucursal_candidates=["SucursalID", "id_sucursal"],
        max_rows=5000
    )


def get_proveedores() -> List[Dict[str, Any]]:
    return load_catalog_real(
        table_candidates=["Proveedor_Catalogo", "Compras_Proveedores", "Proveedores"],
        id_candidates=["ProveedorID", "id_proveedor", "id"],
        name_candidates=["RazonSocial", "NombreComercial", "nombre"],
        code_candidates=["CodigoProveedor", "RFC", "codigo"],
        max_rows=5000
    )


def get_productos() -> List[Dict[str, Any]]:
    return load_catalog_real(
        table_candidates=["Sync_Productos", "Comercial_Productos", "Productos"],
        id_candidates=["ProductoID", "id_producto", "id"],
        name_candidates=["Nombre", "NombreProducto", "nombre"],
        code_candidates=["CodigoFuente", "CodigoProducto", "codigo"],
        max_rows=5000
    )


def get_vendedores() -> List[Dict[str, Any]]:
    return load_catalog_real(
        table_candidates=["Comercial_Vendedores", "Sync_Vendedores", "Vendedores"],
        id_candidates=["VendedorID", "id_vendedor", "id"],
        name_candidates=["Nombre", "NombreVendedor", "nombre"],
        code_candidates=["CodigoVendedor", "codigo"],
        max_rows=5000
    )


def get_centros_costo() -> List[Dict[str, Any]]:
    return load_catalog_real(
        table_candidates=["Sistema_CentrosCosto", "Global_Cat_CentrosCosto", "CentrosCosto"],
        id_candidates=["CentroCostoID", "id_centro_costo", "id"],
        name_candidates=["Nombre", "NombreCentroCosto", "nombre"],
        code_candidates=["CodigoCentroCosto", "codigo"],
        max_rows=2000
    )


def get_proyectos() -> List[Dict[str, Any]]:
    return load_catalog_real(
        table_candidates=["Sistema_Proyectos", "Proyectos"],
        id_candidates=["ProyectoID", "id_proyecto", "id"],
        name_candidates=["Nombre", "NombreProyecto", "nombre"],
        code_candidates=["CodigoProyecto", "codigo"],
        max_rows=2000
    )


def get_versiones_sistemas() -> List[Dict[str, Any]]:
    if not table_exists("Sistema_VersionesSistemas"):
        return []
    return load_catalog_real(
        table_candidates=["Sistema_VersionesSistemas"],
        id_candidates=["sistema_version_id"],
        name_candidates=["version_sistema", "nombre_sistema"],
        code_candidates=["tipo_sistema"],
        tipo_candidates=["tipo_sistema"],
        max_rows=1000
    )


def get_periodos() -> List[Dict[str, Any]]:
    return [
        {"id": "hoy", "nombre": "Hoy", "codigo": "HOY", "id_empresa": None, "id_unidad_negocio": None, "id_sucursal": None, "tipo": None, "activo": True, "visible_en_operaciones": True, "metadata": {}},
        {"id": "ayer", "nombre": "Ayer", "codigo": "AYER", "id_empresa": None, "id_unidad_negocio": None, "id_sucursal": None, "tipo": None, "activo": True, "visible_en_operaciones": True, "metadata": {}},
        {"id": "semana_actual", "nombre": "Semana actual", "codigo": "SEMANA", "id_empresa": None, "id_unidad_negocio": None, "id_sucursal": None, "tipo": None, "activo": True, "visible_en_operaciones": True, "metadata": {}},
        {"id": "mes_actual", "nombre": "Mes actual", "codigo": "MES", "id_empresa": None, "id_unidad_negocio": None, "id_sucursal": None, "tipo": None, "activo": True, "visible_en_operaciones": True, "metadata": {}},
        {"id": "rango", "nombre": "Rango personalizado", "codigo": "RANGO", "id_empresa": None, "id_unidad_negocio": None, "id_sucursal": None, "tipo": None, "activo": True, "visible_en_operaciones": True, "metadata": {}}
    ]


# ============================================================
# Endpoints Corporate Filters
# ============================================================

@router.get("/health")
async def health():
    try:
        rows = sql_query("SELECT DB_NAME() AS database_name, @@SERVERNAME AS server_name")
        return {"success": True, "service": "corporate_filters", "source": "EDARSAHUB_SQL", "remote_connections_required": False, "database": rows[0].get("database_name") if rows else None, "status": "OK"}
    except Exception as exc:
        return {"success": False, "service": "corporate_filters", "source": "EDARSAHUB_SQL", "remote_connections_required": False, "status": "SYNC_ERROR", "message": str(exc)}


@router.get("/bootstrap")
async def bootstrap(scope: str = Query("global")):
    filters = {"empresas": [], "unidades_negocio": [], "servidores": [], "sucursales": [], "almacenes": [], "vendedores": [], "productos": [], "proveedores": [], "centros_costo": [], "proyectos": [], "periodos": [], "versiones_sistemas": []}
    dependencies = {"unidades_negocio": ["empresas"], "sucursales": ["empresas", "unidades_negocio"], "almacenes": ["empresas", "sucursales"], "vendedores": ["empresas", "sucursales"], "productos": ["empresas"], "proveedores": ["empresas"], "centros_costo": ["empresas"], "proyectos": ["empresas"], "servidores": ["empresas", "versiones_sistemas"]}
    try:
        filters["empresas"] = get_empresas()
        filters["unidades_negocio"] = get_unidades_negocio()
        filters["servidores"] = get_servidores()
        filters["sucursales"] = get_sucursales()
        filters["almacenes"] = get_almacenes()
        filters["vendedores"] = get_vendedores()
        filters["productos"] = get_productos()
        filters["proveedores"] = get_proveedores()
        filters["centros_costo"] = get_centros_costo()
        filters["proyectos"] = get_proyectos()
        filters["periodos"] = get_periodos()
        filters["versiones_sistemas"] = get_versiones_sistemas()
        return {"success": True, "source": "EDARSAHUB_SQL", "mode": "snapshot", "scope": scope, "filters": filters, "dependencies": dependencies, "status": {"status": "OK", "remote_connections_required": False, "message": "Filtros cargados desde EDARSAHUB SQL"}}
    except Exception as exc:
        logger.exception("Error cargando corporate filters")
        return {"success": False, "source": "EDARSAHUB_SQL", "mode": "snapshot", "scope": scope, "filters": filters, "dependencies": dependencies, "status": {"status": "SYNC_ERROR", "remote_connections_required": False, "message": str(exc)}}


@router.post("/resolve")
async def resolve(payload: Dict[str, Any] = Body(...)):
    scope = payload.get("scope", "global")
    requested_filters = payload.get("requested_filters") or []
    result = await bootstrap(scope)
    filters = result.get("filters", {})
    if requested_filters:
        filters = {k: v for k, v in filters.items() if k in requested_filters}
    return {"success": result.get("success", False), "source": "EDARSAHUB_SQL", "scope": scope, "filters": filters, "status": result.get("status", {})}


# ============================================================
# Endpoints Admin Versiones Sistemas
# ============================================================

@router.get("/admin/versiones-sistemas")
async def listar_versiones_sistemas():
    if not table_exists("Sistema_VersionesSistemas"):
        return {"success": False, "message": "Tabla no existe", "data": []}
    sql = "SELECT sistema_version_id, tipo_sistema, nombre_sistema, version_sistema, descripcion, proveedor, motor_base_datos, es_version_default, activo, created_at FROM Sistema_VersionesSistemas ORDER BY tipo_sistema, version_sistema"
    return {"success": True, "source": "EDARSAHUB_SQL", "data": sql_query(sql)}


@router.get("/admin/servidores-versiones")
async def listar_servidores_con_versiones():
    if object_exists("vw_Servidores_Conexiones_Versiones", "V"):
        sql = "SELECT servidor_conexion_id, nombre, tipo_sistema, host, database_name, activo, sistema_version_id, nombre_sistema, version_sistema, es_version_default, version_activa FROM vw_Servidores_Conexiones_Versiones ORDER BY tipo_sistema, nombre"
    else:
        sql = "SELECT id AS servidor_conexion_id, nombre, system_type AS tipo_sistema, host, database_name, activo, sistema_version_id FROM Servidores_Conexiones ORDER BY system_type, nombre"
    return {"success": True, "source": "EDARSAHUB_SQL", "data": sql_query(sql)}


@router.post("/admin/versiones-sistemas")
async def crear_version_sistema(payload: Dict[str, Any] = Body(...)):
    tipo = safe_sql_literal(payload.get("tipo_sistema") or "")
    nombre = safe_sql_literal(payload.get("nombre_sistema") or tipo)
    version = safe_sql_literal(payload.get("version_sistema") or "")
    if not tipo or not version:
        return {"success": False, "message": "tipo_sistema y version_sistema son obligatorios"}
    sql = f"IF EXISTS (SELECT 1 FROM Sistema_VersionesSistemas WHERE tipo_sistema='{tipo}' AND version_sistema='{version}') SELECT CAST(0 AS BIT) AS success, 'Ya existe' AS message ELSE INSERT INTO Sistema_VersionesSistemas (tipo_sistema, nombre_sistema, version_sistema, es_version_default, activo, created_by) OUTPUT CAST(1 AS BIT) AS success, inserted.sistema_version_id VALUES ('{tipo}', '{nombre}', '{version}', 0, 1, 'API_ADMIN')"
    rows = sql_query(sql)
    if rows and not rows[0].get("success"):
        return {"success": False, "message": rows[0].get("message", "Error")}
    return {"success": True, "source": "EDARSAHUB_SQL", "data": rows[0] if rows else None}


@router.put("/admin/versiones-sistemas/{sistema_version_id}")
async def actualizar_version_sistema(sistema_version_id: str, payload: Dict[str, Any] = Body(...)):
    allowed = ["nombre_sistema", "version_sistema", "descripcion", "proveedor", "motor_base_datos", "es_version_default", "activo", "observaciones"]
    updates = []
    for f in allowed:
        if f not in payload:
            continue
        v = payload[f]
        if f in ["es_version_default", "activo"]:
            updates.append(f"{f}={1 if v else 0}")
        elif v is None:
            updates.append(f"{f}=NULL")
        else:
            updates.append(f"{f}='{safe_sql_literal(v)}'")
    if not updates:
        return {"success": False, "message": "No hay campos válidos"}
    sql = f"UPDATE Sistema_VersionesSistemas SET {','.join(updates)}, updated_at=SYSUTCDATETIME() OUTPUT inserted.sistema_version_id, inserted.tipo_sistema, inserted.version_sistema WHERE sistema_version_id='{safe_sql_literal(sistema_version_id)}'"
    rows = sql_query(sql)
    return {"success": True, "data": rows[0]} if rows else {"success": False, "message": "No encontrada"}


@router.put("/admin/servidores/{servidor_conexion_id}/version")
async def asignar_version_a_servidor(servidor_conexion_id: str, payload: Dict[str, Any] = Body(...)):
    version_id = safe_sql_literal(payload.get("sistema_version_id") or "")
    if not version_id:
        return {"success": False, "message": "sistema_version_id obligatorio"}
    sql = f"IF NOT EXISTS (SELECT 1 FROM Sistema_VersionesSistemas WHERE sistema_version_id='{version_id}' AND activo=1) SELECT CAST(0 AS BIT) AS success, 'Version no existe' AS message ELSE UPDATE Servidores_Conexiones SET sistema_version_id='{version_id}' OUTPUT CAST(1 AS BIT) AS success, inserted.id AS servidor_conexion_id, inserted.nombre WHERE id='{safe_sql_literal(servidor_conexion_id)}'"
    rows = sql_query(sql)
    if rows and not rows[0].get("success"):
        return {"success": False, "message": rows[0].get("message", "Error")}
    return {"success": True, "data": rows[0]} if rows else {"success": False, "message": "No encontrado"}
