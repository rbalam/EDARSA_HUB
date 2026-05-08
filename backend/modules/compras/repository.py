"""
EDARSA HUB - Compras Module Repository
======================================
Acceso a datos para el módulo de compras.

FASE 4 DEL REFACTOR MODULAR (Diciembre 2025):
- Queries SQL para MPRO y SoftRestaurant
- Acceso a MongoDB para configuración de servidores

BLINDAJE ABRIL 2026:
- Validación de existencia de tablas antes de ejecutar queries
- Retorno homologado cuando tabla no existe
- Prevención de contaminación del pool SQL
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from core.db import execute_sql_query


# ============================================================================
# BLINDAJE: RESULTADO HOMOLOGADO PARA QUERIES DE COMPRAS
# ============================================================================

@dataclass
class ComprasQueryResult:
    """Resultado homologado para queries del módulo de compras."""
    success: bool
    data: List[Dict]
    status: str  # SUCCESS, NO_DATA, TABLE_NOT_FOUND, SCHEMA_MISMATCH, CONNECTION_ERROR
    message: str


def validate_table_exists(server: Dict, table_name: str) -> bool:
    """
    Valida si una tabla existe en el servidor SQL.
    Usa INFORMATION_SCHEMA para verificación segura.
    """
    query = f"""
    SELECT COUNT(*) as exists_flag 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME = '{table_name}'
    """
    try:
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query, timeout_seconds=10
        )
        if result and result[0].get('exists_flag', 0) > 0:
            return True
        return False
    except Exception as e:
        logging.warning(f"Error validando tabla {table_name}: {e}")
        return False


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


def _decrypt_server_password(server: Optional[Dict]) -> Optional[Dict]:
    """
    Descifra el password de un servidor obtenido de MongoDB.
    
    FASE 3C.1: Helper para manejar passwords cifrados.
    """
    if not server:
        return server
    
    password = server.get('password', '')
    if password:
        try:
            from core.secret_manager import decrypt_secret, is_encrypted_secret
            if is_encrypted_secret(password):
                server['password'] = decrypt_secret(password)
            # Si no está cifrado, es legacy - dejar tal cual
        except Exception as e:
            logging.error(f"[DECRYPT_ERROR] Error descifrando password de servidor {server.get('id', 'N/A')}: {type(e).__name__}")
    
    return server


# ============================================================================
# SERVIDORES
# ============================================================================

async def get_server_by_id(server_id: str) -> Optional[Dict]:
    """
    Obtiene un servidor activo por ID.
    
    FASE 3C.1: Descifra automáticamente el password si está cifrado.
    """
    server = await get_db().servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    return _decrypt_server_password(server)


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


def query_pedidos_vigentes_sr(server: Dict) -> ComprasQueryResult:
    """
    Obtiene pedidos vigentes de SoftRestaurant.
    
    BLINDAJE ABRIL 2026:
    - Valida existencia de tabla 'pedidocompra' antes de ejecutar
    - Retorna resultado homologado si la tabla no existe
    - No contamina el pool con queries a tablas inexistentes
    """
    # Primero validar que exista la tabla pedidocompra
    if not validate_table_exists(server, 'pedidocompra'):
        logging.info(f"[COMPRAS] Tabla 'pedidocompra' no existe en {server['name']} - operación no soportada")
        return ComprasQueryResult(
            success=True,  # No es error, simplemente no está disponible
            data=[],
            status="TABLE_NOT_FOUND",
            message=f"El servidor {server['name']} no tiene módulo de pedidos de compra instalado"
        )
    
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
    
    try:
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        )
        
        if result:
            return ComprasQueryResult(
                success=True,
                data=result,
                status="SUCCESS",
                message=f"Se encontraron {len(result)} pedidos"
            )
        else:
            return ComprasQueryResult(
                success=True,
                data=[],
                status="NO_DATA",
                message="No hay pedidos de compra vigentes"
            )
    except Exception as e:
        error_str = str(e).lower()
        logging.error(f"[COMPRAS] Error en query_pedidos_vigentes_sr: {e}")
        
        # Clasificar error para no contaminar pool
        if "invalid object" in error_str or "no existe" in error_str:
            return ComprasQueryResult(
                success=False,
                data=[],
                status="SCHEMA_MISMATCH",
                message=f"Error de esquema en {server['name']}: tabla o columna no encontrada"
            )
        
        return ComprasQueryResult(
            success=False,
            data=[],
            status="CONNECTION_ERROR",
            message=f"Error de conexión: {str(e)[:200]}"
        )


# ============================================================================
# QUERIES SQL - DETALLE DE PEDIDO/REQUISICIÓN
# ============================================================================

def query_detalle_pedido_mpro(server: Dict, folio: str) -> List[Dict]:
    """
    Obtiene el detalle de productos de un pedido/requisición en MPRO.
    Incluye existencia y consumo para cálculo de automatización.
    """
    query = f"""
    SELECT 
        RD.Pr_Cve_Producto as codigo,
        P.Pr_Descripcion as nombre,
        RD.Rd_Cantidad as cantidad,
        RD.Rd_Costo as costo,
        ISNULL((
            SELECT TOP 1 ID.Id_Existencia 
            FROM Inventario_Fisico_Detalle ID
            INNER JOIN Inventario_Fisico I ON I.If_Folio = ID.If_Folio
            WHERE ID.Pr_Cve_Producto = RD.Pr_Cve_Producto 
            AND I.Al_Cve_Almacen = R.Al_Cve_Almacen
            ORDER BY I.If_Fecha DESC
        ), 0) as existencia,
        ISNULL((
            SELECT AVG(CAST(MD.Md_Cantidad as FLOAT))
            FROM Movimiento_Detalle MD
            INNER JOIN Movimiento M ON M.Mv_Folio = MD.Mv_Folio
            WHERE MD.Pr_Cve_Producto = RD.Pr_Cve_Producto
            AND M.Al_Cve_Almacen = R.Al_Cve_Almacen
            AND M.Tm_Cve_TipoMov IN (SELECT Tm_Cve_TipoMov FROM Tipo_Movimiento WHERE Tm_Tipo = 'S')
            AND M.Mv_Fecha >= DATEADD(DAY, -15, GETDATE())
        ), 0) as consumo_promedio
    FROM Requisicion_Detalle RD
    INNER JOIN Requisicion R ON R.Rq_Folio = RD.Rq_Folio
    INNER JOIN Producto P ON P.Pr_Cve_Producto = RD.Pr_Cve_Producto
    WHERE RD.Rq_Folio = '{folio}'
    ORDER BY P.Pr_Descripcion
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
    'query_detalle_pedido_mpro',
    # Facturas
    'query_detalle_factura_mpro',
    'query_facturas_proveedor_mpro',
]
