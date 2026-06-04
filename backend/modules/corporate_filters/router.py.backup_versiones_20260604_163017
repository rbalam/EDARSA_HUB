from fastapi import APIRouter, Query, Body
from typing import Dict, Any, List, Optional
import os
import logging

from core.db import execute_sql_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/corporate-filters", tags=["Corporate Filters"])


def _env_first(*names: str, default: Optional[str] = None) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


def get_edarsahub_sql_config() -> Dict[str, Any]:
    """
    Configuración única para consultar EDARSAHUB SQL.
    No usar servidores remotos.
    No abrir conexión live a SoftRestaurant/MPRO/Enterprise.
    """
    host = _env_first("EDARSAHUB_SQL_HOST", "SQLSERVER_HOST", "SQL_HOST", "MSSQL_HOST")
    port = int(_env_first("EDARSAHUB_SQL_PORT", "SQLSERVER_PORT", "SQL_PORT", "MSSQL_PORT", default="1433"))
    database = _env_first("EDARSAHUB_SQL_DATABASE", "SQLSERVER_DATABASE", "SQL_DATABASE", "MSSQL_DATABASE", default="EDARSAHUB")
    username = _env_first("EDARSAHUB_SQL_USER", "EDARSAHUB_SQL_USERNAME", "SQLSERVER_USERNAME", "SQL_USER", "MSSQL_USER")
    password = _env_first("EDARSAHUB_SQL_PASSWORD", "SQLSERVER_PASSWORD", "SQL_PASSWORD", "MSSQL_PASSWORD")

    missing = []
    if not host:
        missing.append("EDARSAHUB_SQL_HOST / SQLSERVER_HOST / SQL_HOST / MSSQL_HOST")
    if not username:
        missing.append("EDARSAHUB_SQL_USER / EDARSAHUB_SQL_USERNAME / SQL_USER / MSSQL_USER")
    if not password:
        missing.append("EDARSAHUB_SQL_PASSWORD / SQLSERVER_PASSWORD / SQL_PASSWORD / MSSQL_PASSWORD")

    if missing:
        raise RuntimeError("Faltan variables de entorno SQL EDARSAHUB: " + ", ".join(missing))

    return {
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "password": password,
    }


def q(sql: str) -> List[Dict[str, Any]]:
    cfg = get_edarsahub_sql_config()
    return execute_sql_query(
        cfg["host"],
        cfg["port"],
        cfg["database"],
        cfg["username"],
        cfg["password"],
        sql,
        timeout_seconds=45
    )


def safe_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    return bool(value)


def option(
    row: Dict[str, Any],
    id_field: str,
    name_field: str,
    code_field: Optional[str] = None,
    id_empresa_field: Optional[str] = None,
    id_unidad_field: Optional[str] = None,
    id_sucursal_field: Optional[str] = None,
    tipo_field: Optional[str] = None,
    metadata_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    metadata = {}
    for f in metadata_fields or []:
        if f in row:
            metadata[f] = row.get(f)

    return {
        "id": str(row.get(id_field)) if row.get(id_field) is not None else None,
        "nombre": str(row.get(name_field) or ""),
        "codigo": str(row.get(code_field)) if code_field and row.get(code_field) is not None else None,
        "id_empresa": str(row.get(id_empresa_field)) if id_empresa_field and row.get(id_empresa_field) is not None else None,
        "id_unidad_negocio": str(row.get(id_unidad_field)) if id_unidad_field and row.get(id_unidad_field) is not None else None,
        "id_sucursal": str(row.get(id_sucursal_field)) if id_sucursal_field and row.get(id_sucursal_field) is not None else None,
        "tipo": str(row.get(tipo_field)) if tipo_field and row.get(tipo_field) is not None else None,
        "activo": safe_bool(row.get("activo"), True),
        "visible_en_operaciones": safe_bool(row.get("visible_en_operaciones"), True),
        "metadata": metadata
    }


def table_exists(table_name: str) -> bool:
    sql = f"""
    SELECT TOP 1 TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_NAME = '{table_name}'
    """
    return len(q(sql)) > 0


def column_exists(table_name: str, column_name: str) -> bool:
    sql = f"""
    SELECT TOP 1 COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = '{table_name}'
      AND COLUMN_NAME = '{column_name}'
    """
    return len(q(sql)) > 0


def get_empresas() -> List[Dict[str, Any]]:
    sql = """
    SELECT
        EmpresaID AS id_empresa,
        NombreEmpresa AS nombre,
        CodigoEmpresa AS codigo,
        Activo AS activo,
        1 AS visible_en_operaciones
    FROM Sistema_Empresas
    WHERE Activo = 1 OR Activo IS NULL
    ORDER BY NombreEmpresa
    """
    return [
        option(r, "id_empresa", "nombre", "codigo")
        for r in q(sql)
    ]


def get_unidades_negocio() -> List[Dict[str, Any]]:
    sql = """
    SELECT
        CAST(id AS VARCHAR(36)) AS id_unidad_negocio,
        CAST(server_id AS VARCHAR(36)) AS id_empresa,
        nombre,
        codigo,
        activo,
        1 AS visible_en_operaciones
    FROM Unidades_Negocio
    WHERE activo = 1 OR activo IS NULL
    ORDER BY nombre
    """
    return [
        option(r, "id_unidad_negocio", "nombre", "codigo", id_empresa_field="id_empresa")
        for r in q(sql)
    ]


def get_servidores() -> List[Dict[str, Any]]:
    sql = """
    SELECT
        CAST(id AS VARCHAR(36)) AS servidor_conexion_id,
        nombre,
        system_type AS tipo_sistema,
        activo,
        visible_en_operaciones,
        0 AS es_core
    FROM Servidores_Conexiones
    WHERE activo = 1 OR activo IS NULL
    ORDER BY system_type, nombre
    """
    return [
        option(
            r,
            "servidor_conexion_id",
            "nombre",
            "tipo_sistema",
            tipo_field="tipo_sistema",
            metadata_fields=["tipo_sistema", "es_core"]
        )
        for r in q(sql)
    ]


def get_periodos() -> List[Dict[str, Any]]:
    return [
        {"id": "hoy", "nombre": "Hoy", "codigo": "HOY", "activo": True, "visible_en_operaciones": True, "metadata": {}},
        {"id": "ayer", "nombre": "Ayer", "codigo": "AYER", "activo": True, "visible_en_operaciones": True, "metadata": {}},
        {"id": "semana_actual", "nombre": "Semana actual", "codigo": "SEMANA", "activo": True, "visible_en_operaciones": True, "metadata": {}},
        {"id": "mes_actual", "nombre": "Mes actual", "codigo": "MES", "activo": True, "visible_en_operaciones": True, "metadata": {}},
        {"id": "rango_personalizado", "nombre": "Rango personalizado", "codigo": "RANGO", "activo": True, "visible_en_operaciones": True, "metadata": {}}
    ]


def get_optional_catalog(table_candidates: List[str], id_candidates: List[str], name_candidates: List[str], code_candidates: List[str] = None) -> List[Dict[str, Any]]:
    """
    Lector tolerante para catálogos que pueden tener nombres distintos.
    No crea tablas.
    No rompe si la tabla no existe.
    """
    code_candidates = code_candidates or []

    for table in table_candidates:
        if not table_exists(table):
            continue

        columns_sql = f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table}'
        """
        cols = {r["COLUMN_NAME"] for r in q(columns_sql)}

        id_col = next((c for c in id_candidates if c in cols), None)
        name_col = next((c for c in name_candidates if c in cols), None)
        code_col = next((c for c in code_candidates if c in cols), None)
        empresa_col = "id_empresa" if "id_empresa" in cols else None
        activo_col = "activo" if "activo" in cols else None

        if not id_col or not name_col:
            continue

        selected = [id_col, name_col]
        if code_col:
            selected.append(code_col)
        if empresa_col:
            selected.append(empresa_col)
        if activo_col:
            selected.append(activo_col)

        sql = f"""
        SELECT TOP 1000 {", ".join(selected)}
        FROM {table}
        {"WHERE ISNULL(activo, 1) = 1" if activo_col else ""}
        ORDER BY {name_col}
        """

        rows = q(sql)

        result = []
        for r in rows:
            result.append(option(
                r,
                id_col,
                name_col,
                code_col,
                id_empresa_field=empresa_col
            ))
        return result

    return []


@router.get("/health")
async def corporate_filters_health():
    try:
        cfg = get_edarsahub_sql_config()
        rows = q("SELECT DB_NAME() AS database_name, @@SERVERNAME AS server_name")
        return {
            "success": True,
            "service": "corporate_filters",
            "source": "EDARSAHUB_SQL",
            "database": rows[0]["database_name"] if rows else cfg["database"],
            "remote_connections_required": False,
            "status": "OK"
        }
    except Exception as e:
        return {
            "success": False,
            "service": "corporate_filters",
            "source": "EDARSAHUB_SQL",
            "remote_connections_required": False,
            "status": "SYNC_ERROR",
            "message": str(e)
        }


@router.get("/bootstrap")
async def corporate_filters_bootstrap(scope: str = Query("global")):
    """
    Bootstrap de filtros corporativos.

    Este endpoint debe sustituir gradualmente los fetch duplicados de:
    /api/empresas
    /api/unidades-negocio
    /api/sucursales
    /api/almacenes
    /api/servers
    etc.
    """
    filters = {
        "empresas": [],
        "unidades_negocio": [],
        "servidores": [],
        "sucursales": [],
        "almacenes": [],
        "vendedores": [],
        "productos": [],
        "proveedores": [],
        "centros_costo": [],
        "proyectos": [],
        "periodos": []
    }

    dependencies = {
        "unidades_negocio": ["empresas"],
        "sucursales": ["empresas", "unidades_negocio"],
        "almacenes": ["empresas", "sucursales"],
        "vendedores": ["empresas", "sucursales"],
        "productos": ["empresas"],
        "proveedores": ["empresas"],
        "centros_costo": ["empresas"],
        "proyectos": ["empresas"]
    }

    try:
        filters["empresas"] = get_empresas()
        filters["unidades_negocio"] = get_unidades_negocio()
        filters["servidores"] = get_servidores()
        filters["periodos"] = get_periodos()

        filters["sucursales"] = get_optional_catalog(
            ["Sistema_Sucursales", "RH_Cat_Sucursales", "Sucursales", "Sync_Sucursales"],
            ["SucursalID", "id_sucursal", "sucursal_id", "id"],
            ["NombreSucursal", "nombre", "nombre_sucursal", "Sucursal", "descripcion"],
            ["CodigoSucursal", "codigo", "clave", "codigo_sucursal"]
        )

        filters["almacenes"] = get_optional_catalog(
            ["Inventario_Almacenes", "Sistema_Almacenes", "Almacenes", "Sync_Almacenes"],
            ["AlmacenID", "id", "id_almacen", "almacen_id"],
            ["NombreAlmacen", "nombre", "nombre_almacen", "Almacen", "descripcion"],
            ["CodigoAlmacen", "codigo", "clave", "codigo_almacen"]
        )

        filters["vendedores"] = get_optional_catalog(
            ["Comercial_Vendedores", "Sync_Vendedores", "Vendedores"],
            ["id_vendedor", "vendedor_id", "VendedorID", "id"],
            ["nombre", "nombre_vendedor", "Vendedor", "descripcion"],
            ["codigo", "clave", "codigo_vendedor"]
        )

        filters["productos"] = get_optional_catalog(
            ["Sync_Productos", "Comercial_Productos", "Inventarios_Productos", "Productos"],
            ["id_producto", "producto_id", "ProductoID", "id"],
            ["nombre", "nombre_producto", "Producto", "descripcion"],
            ["codigo", "clave", "codigo_producto"]
        )

        filters["proveedores"] = get_optional_catalog(
            ["Proveedor_Catalogo", "Compras_Proveedores", "Proveedores"],
            ["ProveedorID", "id_proveedor", "proveedor_id", "id"],
            ["RazonSocial", "NombreComercial", "nombre", "razon_social", "nombre_comercial", "Proveedor"],
            ["CodigoProveedor", "RFC", "codigo", "rfc", "clave"]
        )

        filters["centros_costo"] = get_optional_catalog(
            ["Sistema_CentrosCosto", "Contabilidad_CentrosCosto", "CentrosCosto"],
            ["id_centro_costo", "centro_costo_id", "CentroCostoID", "id"],
            ["nombre", "descripcion"],
            ["codigo", "clave"]
        )

        filters["proyectos"] = get_optional_catalog(
            ["Sistema_Proyectos", "Proyectos"],
            ["id_proyecto", "proyecto_id", "ProyectoID", "id"],
            ["nombre", "descripcion"],
            ["codigo", "clave"]
        )

        return {
            "success": True,
            "source": "EDARSAHUB_SQL",
            "mode": "snapshot",
            "scope": scope,
            "filters": filters,
            "dependencies": dependencies,
            "status": {
                "status": "OK",
                "remote_connections_required": False,
                "message": "Filtros corporativos cargados desde EDARSAHUB SQL"
            }
        }

    except Exception as e:
        logger.exception("Error en corporate_filters_bootstrap")
        return {
            "success": False,
            "source": "EDARSAHUB_SQL",
            "mode": "snapshot",
            "scope": scope,
            "filters": filters,
            "dependencies": dependencies,
            "status": {
                "status": "SYNC_ERROR",
                "remote_connections_required": False,
                "message": str(e)
            }
        }


@router.post("/resolve")
async def corporate_filters_resolve(payload: Dict[str, Any] = Body(...)):
    scope = payload.get("scope", "global")
    requested_filters = payload.get("requested_filters", [])

    bootstrap = await corporate_filters_bootstrap(scope)

    filters = bootstrap.get("filters", {})
    if requested_filters:
        filters = {k: v for k, v in filters.items() if k in requested_filters}

    return {
        "success": bootstrap.get("success", False),
        "source": "EDARSAHUB_SQL",
        "scope": scope,
        "filters": filters,
        "status": bootstrap.get("status", {})
    }
