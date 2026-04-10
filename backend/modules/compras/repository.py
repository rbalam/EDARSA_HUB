"""
EDARSA HUB - Compras Module Repository
======================================
Acceso a datos para el módulo de compras.

FASE 4 DEL REFACTOR MODULAR (Diciembre 2025):
- Queries SQL para MPRO y SoftRestaurant
- Acceso a MongoDB para configuración de servidores
"""

from typing import Dict, List, Optional, Any
import logging

from core.db import execute_sql_query


# ============================================================================
# INYECCIÓN DE DEPENDENCIA: MongoDB
# ============================================================================

_db = None


def init_compras_repository(database) -> None:
    """Inicializa el repositorio con la conexión a MongoDB."""
    global _db
    _db = database


def get_db():
    """Obtiene la conexión a MongoDB inyectada."""
    if _db is None:
        raise RuntimeError("Compras repository not initialized. Call init_compras_repository(db) first.")
    return _db


# ============================================================================
# SERVIDORES
# ============================================================================

async def get_server_by_id(server_id: str) -> Optional[Dict]:
    """Obtiene un servidor activo por ID."""
    return await get_db().servers.find_one({"id": server_id, "active": True}, {"_id": 0})


# ============================================================================
# PARÁMETROS DE COMPRAS (MongoDB)
# ============================================================================

async def get_compras_params(server_id: str, sucursal: str) -> Optional[Dict]:
    """Obtiene los parámetros de compras para un servidor/sucursal."""
    return await get_db().compras_params.find_one(
        {"server_id": server_id, "sucursal": sucursal},
        {"_id": 0}
    )


async def save_compras_params(server_id: str, sucursal: str, params: Dict) -> None:
    """Guarda o actualiza los parámetros de compras."""
    await get_db().compras_params.update_one(
        {"server_id": server_id, "sucursal": sucursal},
        {"$set": {**params, "server_id": server_id, "sucursal": sucursal}},
        upsert=True
    )


# ============================================================================
# QUERIES SQL - INVENTARIOS FÍSICOS
# ============================================================================

def query_inventarios_fisicos_mpro(server: Dict, almacen_filtro: str = "", sucursal_id: str = None) -> List[Dict]:
    """
    Obtiene inventarios físicos de MPRO.
    """
    sucursal_filtro = f"AND F.Sc_Cve_Sucursal = '{sucursal_id}'" if sucursal_id else ""
    
    query = f"""
    SELECT DISTINCT
        F.If_Folio as folio,
        CONVERT(VARCHAR, F.If_Fecha, 23) as fecha,
        F.Sc_Cve_Sucursal as sucursal_id,
        S.Sc_Nombre as sucursal,
        F.Al_Cve_Almacen as almacen_id,
        A.Al_Nombre as almacen,
        (SELECT COUNT(*) FROM Inventario_Fisico_Detalle D WHERE D.If_Folio = F.If_Folio) as productos,
        'MPRO' as origen
    FROM Inventario_Fisico F
    INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
    INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
    WHERE 1=1 {almacen_filtro} {sucursal_filtro}
    ORDER BY F.If_Fecha DESC, F.If_Folio DESC
    """
    
    return execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )


def query_inventarios_fisicos_sr(server: Dict, almacen_filtro: str = "") -> List[Dict]:
    """
    Obtiene inventarios físicos de SoftRestaurant.
    """
    query = f"""
    SELECT DISTINCT
        CAST(F.idfolioconteo as VARCHAR) as folio,
        CONVERT(VARCHAR, F.fecha, 23) as fecha,
        '' as sucursal_id,
        '' as sucursal,
        CAST(F.idalmacen as VARCHAR) as almacen_id,
        A.descripcion as almacen,
        (SELECT COUNT(*) FROM detalleconteo D WHERE D.idfolioconteo = F.idfolioconteo) as productos,
        'SoftRestaurant' as origen
    FROM folioconteo F
    INNER JOIN almacen A ON A.idalmacen = F.idalmacen
    WHERE 1=1 {almacen_filtro}
    ORDER BY F.fecha DESC, F.idfolioconteo DESC
    """
    
    return execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )


# ============================================================================
# QUERIES SQL - PEDIDOS VIGENTES
# ============================================================================

def query_pedidos_vigentes_mpro(server: Dict, sucursal_id: str = None) -> List[Dict]:
    """
    Obtiene pedidos/requisiciones vigentes de MPRO.
    """
    sucursal_filtro = f"WHERE R.Sc_Cve_Sucursal = '{sucursal_id}'" if sucursal_id else ""
    
    query = f"""
    SELECT DISTINCT
        R.Rq_Folio as folio,
        CONVERT(VARCHAR, R.Rq_Fecha, 23) as fecha,
        R.Sc_Cve_Sucursal as sucursal_id,
        S.Sc_Nombre as sucursal,
        R.Al_Cve_Almacen as almacen_id,
        A.Al_Nombre as almacen,
        R.Rq_Total as total,
        R.Rq_Estado as estado,
        (SELECT COUNT(*) FROM Requisicion_Detalle D WHERE D.Rq_Folio = R.Rq_Folio) as productos,
        'MPRO' as origen
    FROM Requisicion R
    INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = R.Sc_Cve_Sucursal
    INNER JOIN Almacen A ON A.Al_Cve_Almacen = R.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = R.Sc_Cve_Sucursal
    {sucursal_filtro}
    ORDER BY R.Rq_Fecha DESC, R.Rq_Folio DESC
    """
    
    return execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )


def query_pedidos_vigentes_sr(server: Dict) -> List[Dict]:
    """
    Obtiene pedidos vigentes de SoftRestaurant.
    """
    query = """
    SELECT DISTINCT
        CAST(P.idpedidocompra as VARCHAR) as folio,
        CONVERT(VARCHAR, P.fecha, 23) as fecha,
        '' as sucursal_id,
        '' as sucursal,
        CAST(P.idalmacen as VARCHAR) as almacen_id,
        A.descripcion as almacen,
        P.total as total,
        CASE P.estatus 
            WHEN 0 THEN 'Pendiente'
            WHEN 1 THEN 'Autorizado'
            WHEN 2 THEN 'Recibido'
            ELSE 'Desconocido'
        END as estado,
        (SELECT COUNT(*) FROM detallepedidocompra D WHERE D.idpedidocompra = P.idpedidocompra) as productos,
        'SoftRestaurant' as origen
    FROM pedidocompra P
    INNER JOIN almacen A ON A.idalmacen = P.idalmacen
    ORDER BY P.fecha DESC, P.idpedidocompra DESC
    """
    
    return execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )


# ============================================================================
# QUERIES SQL - DETALLE DE FACTURA
# ============================================================================

def query_detalle_factura_mpro(server: Dict, folio: str) -> List[Dict]:
    """
    Obtiene el detalle de una factura/entrada en MPRO.
    """
    query = f"""
    SELECT 
        MD.Pr_Cve_Producto as codigo,
        P.Pr_Descripcion as producto,
        MD.Md_Cantidad as cantidad,
        MD.Md_Costo as costo,
        MD.Md_Importe as importe
    FROM Movimiento_Detalle MD
    INNER JOIN Movimiento M ON M.Mv_Folio = MD.Mv_Folio
    INNER JOIN Producto P ON P.Pr_Cve_Producto = MD.Pr_Cve_Producto
    WHERE M.Mv_Documento = '{folio}'
    ORDER BY P.Pr_Descripcion
    """
    
    return execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )


# ============================================================================
# QUERIES SQL - FACTURAS DE PROVEEDOR
# ============================================================================

def query_facturas_proveedor_mpro(server: Dict, sucursal_id: str = None, meses: str = None, anio: str = None) -> List[Dict]:
    """
    Obtiene facturas de proveedores en MPRO.
    """
    sucursal_filtro = f"AND M.Sc_Cve_Sucursal = '{sucursal_id}'" if sucursal_id else ""
    
    # Filtro de fechas
    fecha_filtro = ""
    if meses and anio:
        meses_list = meses.split(',')
        meses_sql = ','.join([f"'{m.zfill(2)}'" for m in meses_list])
        fecha_filtro = f"AND FORMAT(M.Mv_Fecha, 'MM') IN ({meses_sql}) AND YEAR(M.Mv_Fecha) = {anio}"
    
    query = f"""
    SELECT 
        M.Mv_Documento as folio,
        CONVERT(VARCHAR, M.Mv_Fecha, 23) as fecha,
        P.Pv_Nombre as proveedor,
        M.Mv_Total as total,
        S.Sc_Nombre as sucursal,
        (SELECT COUNT(*) FROM Movimiento_Detalle MD WHERE MD.Mv_Folio = M.Mv_Folio) as productos
    FROM Movimiento M
    INNER JOIN Proveedor P ON P.Pv_Cve_Proveedor = M.Pv_Cve_Proveedor
    INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = M.Sc_Cve_Sucursal
    WHERE M.Tm_Cve_TipoMov IN (SELECT Tm_Cve_TipoMov FROM Tipo_Movimiento WHERE Tm_Tipo = 'E')
    {sucursal_filtro} {fecha_filtro}
    ORDER BY M.Mv_Fecha DESC
    """
    
    return execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )


__all__ = [
    'init_compras_repository',
    'get_db',
    'get_server_by_id',
    'get_compras_params',
    'save_compras_params',
    # Inventarios físicos
    'query_inventarios_fisicos_mpro',
    'query_inventarios_fisicos_sr',
    # Pedidos
    'query_pedidos_vigentes_mpro',
    'query_pedidos_vigentes_sr',
    # Facturas
    'query_detalle_factura_mpro',
    'query_facturas_proveedor_mpro',
]
