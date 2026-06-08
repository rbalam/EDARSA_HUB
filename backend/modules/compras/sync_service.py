
# REGLA CRÍTICA SYNC ORIGEN → EDARSAHUB:
# ServerID, OrigenSistema, id_empresa e id_unidad_negocio NO existen ni deben leerse desde SoftRestaurant/MPRO.
# Esos campos se agregan desde el contexto EDARSAHUB del servidor/unidad antes de hacer MERGE al destino.


# NOTA SQL-FIRST:
# Los nombres de tablas origen SoftRestaurant/MPRO deben vivir en adapters.
# Destinos EDARSAHUB conservan nombres canónicos:
# Inventario_*, Compras_*.
# invfisico/invfisicomovtos NO deben mapearse a Inventario_Movimientos;
# se mantienen en Compras_Inventarios_Fisicos_Sync hasta migración canónica futura.

"""
COMPRAS SYNC SERVICE - Sincronización de Inventarios y Requisiciones a EDARSAHUB
================================================================================
POLÍTICA: Todo se lee de EDARSAHUB SQL. Los servidores físicos solo se consultan
durante la sincronización (job background).


from modules.compras.adapters import softrestaurant_pro_adapter
from modules.compras.adapters import mpro_adapter
Tablas EDARSAHUB:
- Compras_Inventarios_Fisicos_Sync: Inventarios físicos sincronizados
- Compras_Requisiciones_Sync: Requisiciones/pedidos sincronizados
- Compras_Sync_Log: Log de sincronizaciones
"""

import os
import pymssql
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from core.config.edarsahub_config import get_edarsahub_sql_config
from core.sql_first.db import get_sql_connection
_edarsa_cfg = get_edarsahub_sql_config()


logger = logging.getLogger(__name__)

# P2-01: Configuración EDARSAHUB centralizada (sin fallbacks legacy)
EDARSAHUB_CONFIG = {
    'host': _edarsa_cfg.host,
    'port': _edarsa_cfg.port,
    'database': _edarsa_cfg.database,
    'username': _edarsa_cfg.user,
    'password': _edarsa_cfg.password
}




TIPO_MOVIMIENTO_SR_TO_EDARSAHUB = {
    # Compras
    "EPC": 1,  # ENTRADA_COMPRA
    "SPC": 2,  # SALIDA_DEV_PROV

    # Traspasos
    "ETA": 5,  # TRASPASO_ENTRADA
    "STA": 6,  # TRASPASO_SALIDA

    # Inventario físico / ajustes
    "ECI": 3,  # AJUSTE_ENTRADA
    "SCI": 4,  # AJUSTE_SALIDA

    # Otras entradas
    "EPA": 3,
    "EPL": 3,
    "EPB": 3,

    # Otras salidas
    "SPA": 4,
    "SPM": 4,
    "SPD": 4,
}




def registrar_concepto_movimiento_no_mapeado(acumulador, concepto, cantidad=None, fecha=None):
    concepto = str(concepto or "NULL").strip().upper()
    if concepto not in acumulador:
        acumulador[concepto] = {
            "idconcepto": concepto,
            "registros": 0,
            "cantidad_total": 0,
            "ejemplo_fecha": str(fecha) if fecha else None,
        }
    acumulador[concepto]["registros"] += 1
    try:
        acumulador[concepto]["cantidad_total"] += float(cantidad or 0)
    except Exception:
        pass
    if not acumulador[concepto].get("ejemplo_fecha") and fecha:
        acumulador[concepto]["ejemplo_fecha"] = str(fecha)


def resolver_proveedor_edarsahub(cursor, empresa_id, proveedor_origen_id=None, proveedor_nombre=None, proveedor_rfc=None):
    """
    Resuelve ProveedorID canónico EDARSAHUB.
    Prohibido usar ProveedorID=1 como default.

    Si no existe, crea placeholder trazable por código origen.
    """
    proveedor_origen_id = str(proveedor_origen_id or "").strip()
    proveedor_nombre = str(proveedor_nombre or proveedor_origen_id or "PROVEEDOR ORIGEN SIN NOMBRE").strip()
    proveedor_rfc = str(proveedor_rfc or "").strip()

    if proveedor_rfc:
        cursor.execute("""
            SELECT TOP 1 ProveedorID
            FROM dbo.Proveedor_Catalogo
            WHERE EmpresaID = %s AND RFC = %s
            ORDER BY ProveedorID
        """, (empresa_id, proveedor_rfc))
        row = cursor.fetchone()
        if row:
            return row[0]

    if proveedor_origen_id:
        cursor.execute("""
            SELECT TOP 1 ProveedorID
            FROM dbo.Proveedor_Catalogo
            WHERE EmpresaID = %s
              AND (
                    CodigoProveedor = %s
                 OR CodigoOrigen = %s
                 OR CAST(ProveedorID AS NVARCHAR(50)) = %s
              )
            ORDER BY ProveedorID
        """, (empresa_id, proveedor_origen_id, proveedor_origen_id, proveedor_origen_id))
        row = cursor.fetchone()
        if row:
            return row[0]

    codigo = proveedor_origen_id or f"ORIGEN_SIN_CODIGO_{proveedor_nombre[:20]}"

    cursor.execute("""
        INSERT INTO dbo.Proveedor_Catalogo
        (
            EmpresaID,
            CodigoProveedor,
            CodigoOrigen,
            RazonSocial,
            NombreComercial,
            RFC,
            Activo,
            FechaCreacion
        )
        OUTPUT INSERTED.ProveedorID
        VALUES (%s, %s, %s, %s, %s, NULLIF(%s, ''), 1, GETDATE())
    """, (
        empresa_id,
        codigo,
        codigo,
        proveedor_nombre,
        proveedor_nombre,
        proveedor_rfc
    ))

    return cursor.fetchone()[0]


def map_tipo_movimiento_softrestaurant(idconcepto, cantidad=None):
    """
    Mapea idconcepto de SoftRestaurant a Inventario_TipoMovimiento.TipoMovimientoID.

    Si no hay mapeo, devuelve None para evitar insertar movimientos ambiguos.
    """
    concepto = str(idconcepto or "").strip().upper()
    if concepto in TIPO_MOVIMIENTO_SR_TO_EDARSAHUB:
        return TIPO_MOVIMIENTO_SR_TO_EDARSAHUB[concepto]

    return None


def get_compras_adapter(system_type: str):
    """
    Retorna adapter por sistema origen.
    Los nombres de tablas origen viven solo en adapters.
    EDARSAHUB conserva modelo canónico.
    """
    st = (system_type or "").upper()

    if "SOFT" in st:
        return softrestaurant_pro_adapter

    if "MPRO" in st or "MANAGEMENT" in st or "MANAGMENT" in st:
        return mpro_adapter

    return None


def get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB usando configuración de variables de entorno"""
    return get_sql_connection()


# =============================================================================
# LECTURA DE DATOS SINCRONIZADOS (Endpoints usan estas funciones)
# =============================================================================


def _get_edarsahub_context(server_info: Dict, unidad_info: Dict) -> Dict:
    """
    Resuelve el contexto EDARSAHUB (EmpresaID, SucursalID) a partir de server_info y unidad_info.
    
    REGLA: No usar ServerID ni OrigenSistema en tablas canónicas.
    Las tablas canónicas EDARSAHUB usan EmpresaID + SucursalID como contexto.
    """
    # EmpresaID viene de Servidores_Conexiones.EmpresaID
    empresa_id = server_info.get('EmpresaID') or server_info.get('empresa_id')
    
    # SucursalID: intentar de unidad_info.sucursal_origen_id, sino usar 1 como default
    sucursal_id = None
    if unidad_info:
        sucursal_origen = unidad_info.get('sucursal_origen_id')
        if sucursal_origen and str(sucursal_origen).isdigit():
            sucursal_id = int(sucursal_origen)
    
    # Fallback: usar un ID derivado del código de unidad o 1
    if not sucursal_id:
        sucursal_id = 1  # Default si no hay mapeo
    
    if not empresa_id:
        empresa_id = 1  # Default si no hay mapeo
    
    return {
        'empresa_id': int(empresa_id),
        'sucursal_id': int(sucursal_id),
        'system_type': server_info.get('system_type', 'UNKNOWN'),
        'server_name': server_info.get('nombre', 'UNKNOWN'),
        'unidad_codigo': unidad_info.get('codigo', '') if unidad_info else ''
    }



def obtener_inventarios_fisicos_sync(
    unidad_negocio_id: str = None,
    server_id: str = None,
    sucursal: str = None,
    almacen: str = None,
    limit: int = 500
) -> List[Dict]:
    """
    Obtiene inventarios físicos DESDE EDARSAHUB (sincronizados).
    NO se conecta a servidores en vivo.
    """
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        # NO-LIVE / EDARSAHUB única fuente: se leen TODOS los inventarios capturados
        # (ACTIVE y REPLACED) deduplicando por inventario físico real
        # (server_id+sucursal_id+almacen_id+folio) y prefiriendo ACTIVE. Esto corrige
        # el caso en que un sync marcó los registros como REPLACED pero el insert de la
        # nueva tanda ACTIVE falló (POS inaccesible), dejando data válida oculta (MPRO).
        inner_where = "WHERE sync_status IN ('ACTIVE', 'REPLACED')"
        params = []
        
        if unidad_negocio_id:
            inner_where += " AND unidad_negocio_id = %s"
            params.append(unidad_negocio_id)
        
        if server_id:
            inner_where += " AND LOWER(server_id) = LOWER(%s)"
            params.append(server_id)
        
        if sucursal:
            inner_where += " AND (sucursal LIKE %s OR sucursal_id = %s)"
            params.extend([f'%{sucursal}%', sucursal])
        
        if almacen and almacen != 'TODOS':
            inner_where += " AND almacen LIKE %s"
            params.append(f'%{almacen}%')
        
        query = f"""
            SELECT 
                folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
                tipo, estatus, total_productos, comentario, unidad_negocio_id, 
                unidad_negocio_codigo, server_id, system_type,
                sync_timestamp, sync_status
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY server_id, sucursal_id, almacen_id, folio
                        ORDER BY CASE WHEN sync_status = 'ACTIVE' THEN 0 ELSE 1 END, sync_timestamp DESC
                    ) AS _rn
                FROM Compras_Inventarios_Fisicos_Sync
                {inner_where}
            ) t
            WHERE t._rn = 1
            ORDER BY fecha DESC OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convertir datetime a string
        for row in rows:
            if row.get('fecha'):
                row['fecha'] = row['fecha'].isoformat() if hasattr(row['fecha'], 'isoformat') else str(row['fecha'])
            if row.get('sync_timestamp'):
                row['sync_timestamp'] = str(row['sync_timestamp'])
        
        logger.info(f"[SYNC-READ] Inventarios físicos: {len(rows)} registros desde EDARSAHUB")
        return rows
        
    except Exception as e:
        logger.error(f"[SYNC-READ] Error obteniendo inventarios: {e}")
        return []


def obtener_requisiciones_sync(
    unidad_negocio_id: str = None,
    server_id: str = None,
    sucursal: str = None,
    limit: int = 500
) -> List[Dict]:
    """
    Obtiene requisiciones/pedidos DESDE EDARSAHUB (sincronizados).
    NO se conecta a servidores en vivo.
    """
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        query = """
            SELECT 
                tipo, folio, fecha, fecha_entrega, proveedor, proveedor_id,
                sucursal, sucursal_id, total_productos, importe, estatus,
                unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
                sync_timestamp, sync_status
            FROM Compras_Requisiciones_Sync
            WHERE sync_status = 'ACTIVE'
        """
        params = []
        
        if unidad_negocio_id:
            query += " AND unidad_negocio_id = %s"
            params.append(unidad_negocio_id)
        
        if server_id:
            query += " AND server_id = %s"
            params.append(server_id)
        
        if sucursal:
            query += " AND (sucursal LIKE %s OR sucursal_id = %s)"
            params.extend([f'%{sucursal}%', sucursal])
        
        query += f" ORDER BY fecha DESC OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convertir datetime a string
        for row in rows:
            for date_field in ['fecha', 'fecha_entrega', 'sync_timestamp']:
                if row.get(date_field):
                    row[date_field] = row[date_field].isoformat() if hasattr(row[date_field], 'isoformat') else str(row[date_field])
        
        logger.info(f"[SYNC-READ] Requisiciones: {len(rows)} registros desde EDARSAHUB")
        return rows
        
    except Exception as e:
        logger.error(f"[SYNC-READ] Error obteniendo requisiciones: {e}")
        return []


# =============================================================================
# SINCRONIZACIÓN (Job Background - se conecta a servidores físicos)
# =============================================================================

def sync_inventarios_fisicos_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_query_func
) -> Dict:
    """
    Sincroniza inventarios físicos desde un servidor físico a EDARSAHUB.
    Esta función se llama desde el job de sincronización.
    
    Args:
        server_info: Diccionario con host, port, database, username, password, system_type
        unidad_info: Diccionario con id, codigo, nombre
        execute_sql_query_func: Función para ejecutar queries en el servidor origen
    
    Returns:
        Dict con status, records_synced, error
    """
    from core.system_type_utils import is_mpro_system, is_softrestaurant_system
    
    server_id = server_info.get('id')
    system_type = server_info.get('system_type', '')
    unidad_id = unidad_info.get('id')
    unidad_codigo = unidad_info.get('codigo')
    
    logger.info(f"[SYNC] Iniciando sync inventarios: {unidad_codigo} ({system_type})")
    
    try:
        # Query según tipo de sistema
        if is_mpro_system(system_type):
            # MPRO usa tabla "Fisico" (no Fisico_Inventario)
            query = """
                SELECT 
                    F.Fi_Folio as folio,
                    F.Fi_Fecha as fecha,
                    A.Al_Descripcion as almacen,
                    A.Al_Cve_Almacen as almacen_id,
                    S.Sc_Descripcion as sucursal,
                    A.Sc_Cve_Sucursal as sucursal_id,
                    'FISICO' as tipo,
                    'CERRADO' as estatus,
                    COUNT(F.Pr_Cve_Producto) as total_productos,
                    MAX(F.Fi_Comentario) as comentario
                FROM Fisico F
                INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
                LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
                WHERE F.Fi_Fecha >= DATEADD(MONTH, -6, GETDATE())
                GROUP BY F.Fi_Folio, F.Fi_Fecha, A.Al_Descripcion, A.Al_Cve_Almacen, S.Sc_Descripcion, A.Sc_Cve_Sucursal
                ORDER BY F.Fi_Fecha DESC
            """
        elif is_softrestaurant_system(system_type):
            # SoftRestaurant usa tabla "invfisico"
            query = """
                SELECT 
                    CAST(INV.folio AS VARCHAR) as folio,
                    INV.fecha as fecha,
                    A.nombre as almacen,
                    CAST(A.
) as almacen_id,
                    '' as sucursal,
                    '' as sucursal_id,
                    'FISICO' as tipo,
                    'CERRADO' as estatus,
                    0 as total_productos,
                    '' as comentario
                FROM invfisico INV
                LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
                WHERE INV.fecha >= DATEADD(MONTH, -6, GETDATE())
                ORDER BY INV.fecha DESC
            """
        else:
            return {"status": "ERROR", "records_synced": 0, "error": f"Sistema no soportado: {system_type}"}
        
        # Ejecutar query en servidor origen
        rows = execute_sql_query_func(
            server_info['host'],
            server_info['port'],
            server_info['database'],
            server_info['username'],
            server_info['password'],
            query
        )
        
        if not rows:
            return {"status": "OK", "records_synced": 0, "error": None}
        
        # Guardar en EDARSAHUB
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        # Marcar registros anteriores como inactivos
        cursor.execute("""
            UPDATE Compras_Inventarios_Fisicos_Sync 
            SET sync_status = 'REPLACED' 
            WHERE server_id = %s AND sync_status = 'ACTIVE'
        """, (server_id,))
        
        # Insertar nuevos registros
        records_synced = 0
        for row in rows:
            try:
                cursor.execute("""
                    INSERT INTO Compras_Inventarios_Fisicos_Sync
                    (unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
                     folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
                     tipo, estatus, total_productos, comentario, sync_source, sync_timestamp, sync_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'SYNC', GETDATE(), 'ACTIVE')
                """, (
                    unidad_id, unidad_codigo, server_id, system_type,
                    str(row.get('folio', '')),
                    row.get('fecha'),
                    row.get('almacen', ''),
                    str(row.get('almacen_id', '')),
                    row.get('sucursal', ''),
                    str(row.get('sucursal_id', '')),
                    row.get('tipo', 'FISICO'),
                    row.get('estatus', ''),
                    row.get('total_productos', 0),
                    (row.get('comentario') or '')[:50]
                ))
                records_synced += 1
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando inventario {row.get('folio')}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"[SYNC] Inventarios sincronizados: {records_synced} de {len(rows)}")
        return {"status": "OK", "records_synced": records_synced, "error": None}
        
    except Exception as e:
        logger.error(f"[SYNC] Error sync inventarios {unidad_codigo}: {e}")
        return {"status": "ERROR", "records_synced": 0, "error": str(e)}


def sync_requisiciones_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_query_func
) -> Dict:
    """
    Sincroniza requisiciones/pedidos desde un servidor físico a EDARSAHUB.
    """
    from core.system_type_utils import is_mpro_system, is_softrestaurant_system
    
    server_id = server_info.get('id')
    system_type = server_info.get('system_type', '')
    unidad_id = unidad_info.get('id')
    unidad_codigo = unidad_info.get('codigo')
    
    logger.info(f"[SYNC] Iniciando sync requisiciones: {unidad_codigo} ({system_type})")
    
    try:
        # Query según tipo de sistema
        if is_mpro_system(system_type):
            query = """
                SELECT 
                    'OC' as tipo,
                    OC.Oc_Folio as folio,
                    OC.Oc_Fecha as fecha,
                    OC.Oc_Fecha_Entrega as fecha_entrega,
                    P.Pv_Nombre as proveedor,
                    OC.Pv_Cve_Proveedor as proveedor_id,
                    S.Sc_Descripcion as sucursal,
                    OC.Sc_Cve_Sucursal as sucursal_id,
                    1 as total_productos,
                    ISNULL(OC.Oc_Total, 0) as importe,
                    CASE OC.Oc_Status 
                        WHEN 0 THEN 'PENDIENTE'
                        WHEN 1 THEN 'RECIBIDO'
                        ELSE 'OTRO'
                    END as estatus
                FROM Orden_Compra OC
                LEFT JOIN Proveedor P ON P.Pv_Cve_Proveedor = OC.Pv_Cve_Proveedor
                LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = OC.Sc_Cve_Sucursal
                WHERE OC.Oc_Status = 0
                AND OC.Oc_Fecha >= DATEADD(MONTH, -3, GETDATE())
                ORDER BY OC.Oc_Fecha DESC
            """
        elif is_softrestaurant_system(system_type):
            query = """
                SELECT 
                    'OC' as tipo,
                    OC.folio as folio,
                    OC.fecha as fecha,
                    OC.fechaentrega as fecha_entrega,
                    P.nombre as proveedor,
                    CAST(OC.idProveedor AS VARCHAR) as proveedor_id,
                    '' as sucursal,
                    '' as sucursal_id,
                    (SELECT COUNT(*) FROM ordenescompramov WHERE idOrdenCompra = OC.idOrdenCompra) as total_productos,
                    ISNULL(OC.total, 0) as importe,
                    CASE OC.estatus
                        WHEN 0 THEN 'PENDIENTE'
                        WHEN 1 THEN 'PARCIAL'
                        WHEN 2 THEN 'RECIBIDO'
                        ELSE 'OTRO'
                    END as estatus
                FROM ordenescompra OC
                LEFT JOIN proveedores P ON P.idProveedor = OC.idProveedor
                WHERE OC.estatus IN (0, 1)
                AND OC.fecha >= DATEADD(MONTH, -3, GETDATE())
                ORDER BY OC.fecha DESC
            """
        else:
            return {"status": "ERROR", "records_synced": 0, "error": f"Sistema no soportado: {system_type}"}
        
        # Ejecutar query en servidor origen
        rows = execute_sql_query_func(
            server_info['host'],
            server_info['port'],
            server_info['database'],
            server_info['username'],
            server_info['password'],
            query
        )
        
        if not rows:
            return {"status": "OK", "records_synced": 0, "error": None}
        
        # Guardar en EDARSAHUB
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        # Marcar registros anteriores como inactivos
        cursor.execute("""
            UPDATE Compras_Requisiciones_Sync 
            SET sync_status = 'REPLACED' 
            WHERE server_id = %s AND sync_status = 'ACTIVE'
        """, (server_id,))
        
        # Insertar nuevos registros
        records_synced = 0
        for row in rows:
            try:
                cursor.execute("""
                    INSERT INTO Compras_Requisiciones_Sync
                    (unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
                     tipo, folio, fecha, fecha_entrega, proveedor, proveedor_id,
                     sucursal, sucursal_id, total_productos, importe, estatus,
                     sync_source, sync_timestamp, sync_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'SYNC', GETDATE(), 'ACTIVE')
                """, (
                    unidad_id, unidad_codigo, server_id, system_type,
                    row.get('tipo', 'OC'),
                    str(row.get('folio', '')),
                    row.get('fecha'),
                    row.get('fecha_entrega'),
                    row.get('proveedor', ''),
                    str(row.get('proveedor_id', '')),
                    row.get('sucursal', ''),
                    str(row.get('sucursal_id', '')),
                    row.get('total_productos', 0),
                    row.get('importe', 0),
                    row.get('estatus', '')
                ))
                records_synced += 1
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando requisición {row.get('folio')}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"[SYNC] Requisiciones sincronizadas: {records_synced} de {len(rows)}")
        return {"status": "OK", "records_synced": records_synced, "error": None}
        
    except Exception as e:
        logger.error(f"[SYNC] Error sync requisiciones {unidad_codigo}: {e}")
        return {"status": "ERROR", "records_synced": 0, "error": str(e)}


def log_sync_operation(
    unidad_negocio_id: str,
    server_id: str,
    sync_type: str,
    sync_start: datetime,
    sync_end: datetime,
    records_synced: int,
    status: str,
    error_message: str = None
):
    """Registra la operación de sincronización en el log"""
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Compras_Sync_Log
            (unidad_negocio_id, server_id, sync_type, sync_start, sync_end, 
             records_synced, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            unidad_negocio_id, server_id, sync_type,
            sync_start, sync_end, records_synced, status, error_message
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"[SYNC-LOG] Error registrando log: {e}")


def get_last_sync_info(server_id: str, sync_type: str) -> Optional[Dict]:
    """Obtiene información de la última sincronización"""
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
            SELECT TOP 1 * FROM Compras_Sync_Log
            WHERE server_id = %s AND sync_type = %s
            ORDER BY created_at DESC
        """, (server_id, sync_type))
        row = cursor.fetchone()
        conn.close()
        return row
    except Exception as e:
        logger.error(f"[SYNC-LOG] Error obteniendo último sync: {e}")
        return None


# ============================================================================
# FUNCIONES DE SINCRONIZACIÓN ADICIONALES - SQL-FIRST
# ============================================================================

def sync_almacenes_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable
) -> Dict[str, Any]:
    """
    Sincroniza catálogo de almacenes desde servidor físico a EDARSAHUB.
    Destino: Inventario_Almacenes
    
    Llave MERGE: EmpresaID + SucursalID + CodigoAlmacen
    """
    ctx = _get_edarsahub_context(server_info, unidad_info)
    empresa_id = ctx['empresa_id']
    sucursal_id = ctx['sucursal_id']
    system_type = ctx['system_type']
    
    logger.info(f"[SYNC] Iniciando sync almacenes: Empresa={empresa_id}, Sucursal={sucursal_id}")
    
    try:
        if 'MPRO' in system_type.upper() or 'MANAGEMENT' in system_type.upper():
            query_origen = """
                SELECT 
                    CAST(Al_Cve_Almacen AS VARCHAR(50)) AS codigo_almacen,
                    Al_Descripcion AS nombre_almacen,
                    'GENERAL' AS tipo_almacen,
                    CASE WHEN Al_Estatus = 'A' THEN 1 ELSE 0 END AS activo
                FROM Almacen
            """
        else:
            # SoftRestaurant Pro - usar nombres de tabla correctos
            query_origen = """
                SELECT 
                    CAST(idalmacen AS VARCHAR(50)) AS codigo_almacen,
                    nombre AS nombre_almacen,
                    ISNULL(tipo, 'GENERAL') AS tipo_almacen,
                    1 AS activo
                FROM almacen
            """
        
        result_origen = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_origen
        )
        
        if result_origen is None:
            return {"status": "ERROR", "error": "Timeout o error de conexión", "records_synced": 0}
        
        if not result_origen:
            return {"status": "OK", "records_synced": 0, "message": "Sin datos en origen"}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        records_synced = 0
        for row in result_origen:
            try:
                codigo = str(row.get('codigo_almacen', ''))[:50]
                nombre = str(row.get('nombre_almacen', ''))[:100]
                tipo = str(row.get('tipo_almacen', 'GENERAL'))[:50]
                activo = 1 if row.get('activo') in (1, '1', 'A', True) else 0
                
                cursor.execute("""
                    MERGE INTO Inventario_Almacenes AS target
                    USING (SELECT %s AS EmpresaID, %s AS SucursalID, %s AS CodigoAlmacen) AS source 
                    ON target.EmpresaID = source.EmpresaID 
                       AND target.SucursalID = source.SucursalID 
                       AND target.CodigoAlmacen = source.CodigoAlmacen
                    WHEN MATCHED THEN 
                        UPDATE SET NombreAlmacen = %s, TipoAlmacen = %s, Activo = %s, FechaModificacion = GETDATE()
                    WHEN NOT MATCHED THEN 
                        INSERT (EmpresaID, SucursalID, CodigoAlmacen, NombreAlmacen, TipoAlmacen, PermiteCompras, PermiteVentas, Activo, FechaAlta)
                        VALUES (%s, %s, %s, %s, %s, 1, 1, %s, GETDATE());
                """, (
                    empresa_id, sucursal_id, codigo,
                    nombre, tipo, activo,
                    empresa_id, sucursal_id, codigo, nombre, tipo, activo
                ))
                records_synced += 1
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando almacen {row.get('codigo_almacen')}: {e}")
        
        conn.commit()
        conn.close()
        
        return {"status": "OK", "records_synced": records_synced}
        
    except Exception as e:
        logger.error(f"[SYNC] Error en sync_almacenes: {e}")
        return {"status": "ERROR", "error": str(e), "records_synced": 0}



def sync_existencias_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable
) -> Dict[str, Any]:
    """
    Sincroniza existencias de inventario desde servidor físico a EDARSAHUB.
    Destino: Inventario_Existencias
    
    OPCIÓN B: Usa EmpresaID + SucursalID + AlmacenID + ProductoID como llave.
    NO usa ServerID ni OrigenSistema.
    """
    ctx = _get_edarsahub_context(server_info, unidad_info)
    empresa_id = ctx['empresa_id']
    sucursal_id = ctx['sucursal_id']
    system_type = ctx['system_type']
    
    logger.info(f"[SYNC] Iniciando sync existencias: Empresa={empresa_id}, Sucursal={sucursal_id}")
    
    try:
        if 'MPRO' in system_type.upper() or 'MANAGEMENT' in system_type.upper():
            query_origen = """
                SELECT TOP 5000
                    CAST(Ar_Cve_Articulo AS INT) AS producto_id,
                    CAST(Al_Cve_Almacen AS INT) AS almacen_id,
                    ISNULL(Ex_Existencia, 0) AS existencia,
                    ISNULL(Ex_Costo_Promedio, 0) AS costo_promedio
                FROM Existencia E
                WHERE E.Ex_Existencia <> 0
            """
        else:
            # SoftRestaurant Pro - NO tiene tabla "existencias"
            # Las existencias se calculan de movtosalmacen
            # Por ahora retornamos vacío hasta tener el cálculo correcto
            query_origen = """
                SELECT TOP 0 
                    0 AS producto_id,
                    0 AS almacen_id,
                    0 AS existencia,
                    0 AS costo_promedio
            """
            logger.warning(f"[SYNC] SoftRestaurant no tiene tabla 'existencias' directa - se requiere calcular de movtosalmacen")
        
        result_origen = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_origen
        )
        
        if result_origen is None:
            return {"status": "ERROR", "error": "Timeout o error de conexión", "records_synced": 0}
        
        if not result_origen:
            return {"status": "OK", "records_synced": 0, "message": "Sin datos en origen"}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        records_synced = 0
        for row in result_origen:
            try:
                almacen_id = row.get('almacen_id') or 1
                producto_id = row.get('producto_id') or 0
                existencia = float(row.get('existencia') or 0)
                costo = float(row.get('costo_promedio') or 0)
                
                # MERGE usando llave: EmpresaID + SucursalID + AlmacenID + ProductoID
                cursor.execute("""
                    MERGE INTO Inventario_Existencias AS target
                    USING (SELECT %s AS EmpresaID, %s AS SucursalID, %s AS AlmacenID, %s AS ProductoID) AS source 
                    ON target.EmpresaID = source.EmpresaID 
                       AND target.SucursalID = source.SucursalID 
                       AND target.AlmacenID = source.AlmacenID 
                       AND target.ProductoID = source.ProductoID
                    WHEN MATCHED THEN 
                        UPDATE SET ExistenciaActual = %s, CostoPromedio = %s, FechaModificacion = GETDATE()
                    WHEN NOT MATCHED THEN 
                        INSERT (EmpresaID, SucursalID, AlmacenID, ProductoID, ExistenciaActual, CostoPromedio, FechaAlta)
                        VALUES (%s, %s, %s, %s, %s, %s, GETDATE());
                """, (
                    empresa_id, sucursal_id, almacen_id, producto_id,
                    existencia, costo,
                    empresa_id, sucursal_id, almacen_id, producto_id, existencia, costo
                ))
                records_synced += 1
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando existencia {row.get('producto_id')}: {e}")
        
        conn.commit()
        conn.close()
        
        return {"status": "OK", "records_synced": records_synced}
        
    except Exception as e:
        logger.error(f"[SYNC] Error en sync_existencias: {e}")
        return {"status": "ERROR", "error": str(e), "records_synced": 0}



# ADVERTENCIA: sync_movimientos_from_server debe usar map_tipo_movimiento_softrestaurant() antes de MERGE.

# sync_movimientos_from_server debe:
# - usar map_tipo_movimiento_softrestaurant(idconcepto)
# - saltar registros con TipoMovimientoID None
# - devolver conceptos_no_mapeados en el resultado
def sync_movimientos_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    fecha_inicio: str = None,
    fecha_fin: str = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Sincroniza movimientos de inventario desde servidor físico a EDARSAHUB.
    Destino: Inventario_Movimientos + Inventario_MovimientosDetalle
    
    MAPEO: idconcepto (SoftRestaurant) → TipoMovimientoID (EDARSAHUB)
    - EPC → 1 (ENTRADA_COMPRA)
    - SPC → 2 (SALIDA_DEV_PROV)  
    - ETA → 5 (TRASPASO_ENTRADA)
    - STA → 6 (TRASPASO_SALIDA)
    - ECI → 3 (AJUSTE_ENTRADA)
    - SCI → 4 (AJUSTE_SALIDA)
    """
    ctx = _get_edarsahub_context(server_info, unidad_info)
    empresa_id = ctx['empresa_id']
    sucursal_id = ctx['sucursal_id']
    system_type = ctx['system_type']
    
    logger.info(f"[SYNC] Iniciando sync movimientos: Empresa={empresa_id}, Sucursal={sucursal_id}")
    
    try:
        if 'MPRO' in system_type.upper() or 'MANAGEMENT' in system_type.upper():
            query_origen = """
                SELECT TOP 2000
                    Mo_Fecha AS fecha_movimiento,
                    CAST(Al_Cve_Almacen AS INT) AS almacen_id,
                    Mo_Tipo AS concepto_origen,
                    CAST(Ar_Cve_Articulo AS VARCHAR(50)) AS producto_id,
                    ISNULL(Mo_Cantidad, 0) AS cantidad,
                    ISNULL(Mo_Costo, 0) AS costo
                FROM Movimiento
                WHERE Mo_Fecha >= DATEADD(DAY, -30, GETDATE())
            """
        else:
            # SoftRestaurant - usar idconcepto para mapear tipo
            query_origen = """
                SELECT TOP 2000
                    m.fecha AS fecha_movimiento,
                    CAST(m.idalmacen AS INT) AS almacen_id,
                    m.idconcepto AS concepto_origen,
                    CAST(m.idinsumo AS VARCHAR(50)) AS producto_id,
                    ISNULL(m.cantidad, 0) AS cantidad,
                    ISNULL(m.costo, 0) AS costo,
                    m.idcompra AS compra_id,
                    m.traspaso AS traspaso_id,
                    m.invfisico AS invfisico_id
                FROM movtosalmacen m
                WHERE m.fecha >= DATEADD(DAY, -30, GETDATE())
                  AND m.cancelado = 0
                ORDER BY m.fecha DESC
            """
        
        result_origen = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_origen
        )
        
        if result_origen is None:
            return {"status": "ERROR", "error": "Timeout o error de conexión", "encabezados_synced": 0, "detalles_synced": 0}
        
        if not result_origen:
            return {"status": "OK", "encabezados_synced": 0, "detalles_synced": 0, "message": "Sin datos en origen"}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        records_synced = 0
        skipped_no_mapping = 0
        
        for row in result_origen:
            try:
                concepto = row.get('concepto_origen')
                tipo_movimiento_id = map_tipo_movimiento_softrestaurant(concepto)
                
                if tipo_movimiento_id is None:
                    skipped_no_mapping += 1
                    continue
                
                almacen_id = int(row.get('almacen_id') or 1)
                producto_id = str(row.get('producto_id') or '')[:50]
                fecha = row.get('fecha_movimiento')
                cantidad = float(row.get('cantidad') or 0)
                costo = float(row.get('costo') or 0)
                
                # MERGE en Inventario_Movimientos
                # Llave: EmpresaID + SucursalID + AlmacenID + ProductoID + FechaMovimiento + TipoMovimientoID
                cursor.execute("""
                    MERGE INTO Inventario_Movimientos AS target
                    USING (SELECT %s AS EmpresaID, %s AS SucursalID, %s AS AlmacenID, 
                                  %s AS ProductoID, %s AS FechaMovimiento, %s AS TipoMovimientoID) AS source 
                    ON target.EmpresaID = source.EmpresaID 
                       AND target.SucursalID = source.SucursalID 
                       AND target.AlmacenID = source.AlmacenID
                       AND target.ProductoID = source.ProductoID
                       AND CAST(target.FechaMovimiento AS DATE) = CAST(source.FechaMovimiento AS DATE)
                       AND target.TipoMovimientoID = source.TipoMovimientoID
                    WHEN MATCHED THEN 
                        UPDATE SET Cantidad = Cantidad + %s, CostoUnitario = %s, ModifiedAt = GETDATE()
                    WHEN NOT MATCHED THEN 
                        INSERT (EmpresaID, SucursalID, AlmacenID, ProductoID, TipoMovimientoID, 
                                FechaMovimiento, Cantidad, CostoUnitario, CostoTotal, Activo, CreatedAt)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, GETDATE());
                """, (
                    empresa_id, sucursal_id, almacen_id, producto_id, fecha, tipo_movimiento_id,
                    cantidad, costo,
                    empresa_id, sucursal_id, almacen_id, producto_id, tipo_movimiento_id, 
                    fecha, cantidad, costo, cantidad * costo
                ))
                records_synced += 1
                
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando movimiento: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"[SYNC] Movimientos sync: {records_synced}, skipped (sin mapeo): {skipped_no_mapping}")
        
        return {
            "status": "OK", 
            "encabezados_synced": records_synced, 
            "detalles_synced": 0,
            "skipped_no_mapping": skipped_no_mapping
        }
        
    except Exception as e:
        logger.error(f"[SYNC] Error en sync_movimientos: {e}")
        return {"status": "ERROR", "error": str(e), "encabezados_synced": 0, "detalles_synced": 0}



def sync_pedidos_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    dias_atras: int = 30,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Sincroniza pedidos de compra desde servidor físico a EDARSAHUB.
    Destino: Compras_Pedidos + Compras_PedidosDetalle
    
    Llave MERGE Encabezado: EmpresaID + SucursalID + FolioPedido
    Llave MERGE Detalle: PedidoCompraID + ProductoID (o renglon)
    """
    ctx = _get_edarsahub_context(server_info, unidad_info)
    empresa_id = ctx['empresa_id']
    sucursal_id = ctx['sucursal_id']
    system_type = ctx['system_type']
    
    logger.info(f"[SYNC] Iniciando sync pedidos: Empresa={empresa_id}, Sucursal={sucursal_id}")
    
    try:
        if 'MPRO' in system_type.upper() or 'MANAGEMENT' in system_type.upper():
            query_encabezado = f"""
                SELECT TOP 500
                    Pc_Folio AS folio_pedido,
                    Pc_Fecha AS fecha_pedido,
                    Pc_Fecha_Requerida AS fecha_requerida,
                    Pc_Total AS total,
                    Pc_Estatus AS estatus,
                    Pc_Observaciones AS observaciones
                FROM Pedido_Compra
                WHERE Pc_Fecha >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """
            query_detalle = f"""
                SELECT 
                    Pc_Folio AS folio_pedido,
                    Ar_Cve_Articulo AS producto_id,
                    Pcd_Cantidad AS cantidad,
                    Pcd_Precio AS precio_unitario
                FROM Pedido_Compra_Detalle PCD
                INNER JOIN Pedido_Compra PC ON PC.Pc_Cve_Pedido = PCD.Pc_Cve_Pedido
                WHERE PC.Pc_Fecha >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """
        else:
            query_encabezado = f"""
                SELECT TOP 500
                    CAST(p.folio AS VARCHAR(50)) AS folio_pedido,
                    p.fechacaptura AS fecha_pedido,
                    p.fecharecepcion AS fecha_requerida,
                    0 AS total,
                    'ACTIVO' AS estatus,
                    '' AS observaciones
                FROM pedidos p
                WHERE p.fechacaptura >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """
            query_detalle = f"""
                SELECT 
                    CAST(p.folio AS VARCHAR(50)) AS folio_pedido,
                    CAST(d.idinsumo AS INT) AS producto_id,
                    ISNULL(d.cantidad, 0) AS cantidad,
                    ISNULL(d.costo, 0) AS precio_unitario
                FROM pedidos p
                INNER JOIN pedidosdetalle d ON d.idpedido = p.idpedido
                WHERE p.fechacaptura >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """
        
        # Obtener encabezados
        result_enc = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_encabezado
        )
        
        if result_enc is None:
            return {"status": "ERROR", "error": "Timeout conexión encabezados", "encabezados_synced": 0, "detalles_synced": 0}
        
        if not result_enc:
            return {"status": "OK", "encabezados_synced": 0, "detalles_synced": 0, "message": "Sin pedidos en origen"}
        
        # Obtener detalles
        result_det = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_detalle
        ) or []
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        enc_synced = 0
        det_synced = 0
        
        for enc in result_enc:
            try:
                folio = str(enc.get('folio_pedido', ''))[:50]
                fecha = enc.get('fecha_pedido')
                total = float(enc.get('total') or 0)
                
                # MERGE encabezado
                cursor.execute("""
                    MERGE INTO Compras_Pedidos AS target
                    USING (SELECT %s AS EmpresaID, %s AS SucursalID, %s AS FolioPedido) AS source 
                    ON target.EmpresaID = source.EmpresaID 
                       AND target.SucursalID = source.SucursalID 
                       AND target.FolioPedido = source.FolioPedido
                    WHEN MATCHED THEN 
                        UPDATE SET Total = %s, ModifiedAt = GETDATE()
                    WHEN NOT MATCHED THEN 
                        INSERT (FolioPedido, EmpresaID, SucursalID, FechaPedido, SolicitanteUsuarioID, 
                                Prioridad, MotivoCompra, EstatusPedidoCompraID, Total, Activo, CreatedAt, TipoCambio, Subtotal, DescuentoTotal, ImpuestoTotal)
                        VALUES (%s, %s, %s, %s, 1, 'MEDIA', 'SYNC', 1, %s, 1, GETDATE(), 1, %s, 0, 0);
                """, (
                    empresa_id, sucursal_id, folio,
                    total,
                    folio, empresa_id, sucursal_id, fecha, total, total
                ))
                enc_synced += 1
                
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando pedido {enc.get('folio_pedido')}: {e}")
        
        # P3-01E FIX: insertar detalles Compras_PedidosDetalle
        if result_det:
            for det in result_det:
                try:
                    folio_det = str(det.get('folio_pedido') or det.get('folio') or '').strip()
                    if not folio_det:
                        continue
                    
                    producto_id = det.get('producto_id') or det.get('ProductoID') or 0
                    cantidad = float(det.get('cantidad') or det.get('Cantidad') or 0)
                    precio = float(det.get('precio_unitario') or det.get('precio') or det.get('costo') or 0)
                    
                    # Buscar PedidoCompraID por folio
                    cursor.execute("""
                        SELECT TOP 1 PedidoCompraID 
                        FROM Compras_Pedidos 
                        WHERE FolioPedido = %s AND EmpresaID = %s AND SucursalID = %s
                    """, (folio_det, empresa_id, sucursal_id))
                    
                    row = cursor.fetchone()
                    if not row:
                        continue
                    
                    pedido_compra_id = row[0]
                    
                    # Verificar si ya existe el detalle
                    cursor.execute("""
                        SELECT COUNT(*) FROM Compras_PedidosDetalle 
                        WHERE PedidoCompraID = %s AND ProductoID = %s
                    """, (pedido_compra_id, producto_id))
                    
                    if cursor.fetchone()[0] > 0:
                        continue
                    
                    # Calcular totales línea
                    subtotal = cantidad * precio
                    tasa_impuesto = 16.0
                    impuesto = subtotal * tasa_impuesto / 100
                    total_linea = subtotal + impuesto
                    
                    # Insertar detalle
                    cursor.execute("""
                        INSERT INTO Compras_PedidosDetalle (
                            PedidoCompraID, Renglon, ProductoID, Cantidad,
                            CantidadAtendida, CantidadCancelada, PrecioEstimado,
                            DescuentoPorcentaje, TasaImpuesto, SubtotalLinea,
                            ImpuestoImporte, TotalLinea, Activo, CreatedAt
                        ) VALUES (
                            %s, %s, %s, %s,
                            0, 0, %s,
                            0, %s, %s,
                            %s, %s, 1, GETDATE()
                        )
                    """, (
                        pedido_compra_id, det_synced + 1, producto_id, cantidad,
                        precio, tasa_impuesto, subtotal,
                        impuesto, total_linea
                    ))
                    det_synced += 1
                    
                except Exception as det_err:
                    logger.warning(f"[SYNC] Error detalle pedido: {det_err}")
            
            # Actualizar totales de encabezados
            cursor.execute("""
                UPDATE p SET
                    p.Subtotal = ISNULL(d.Subtotal, 0),
                    p.ImpuestoTotal = ISNULL(d.Impuesto, 0),
                    p.Total = ISNULL(d.Total, 0),
                    p.ModifiedAt = GETDATE()
                FROM Compras_Pedidos p
                INNER JOIN (
                    SELECT PedidoCompraID,
                           SUM(ISNULL(SubtotalLinea,0)) AS Subtotal,
                           SUM(ISNULL(ImpuestoImporte,0)) AS Impuesto,
                           SUM(ISNULL(TotalLinea,0)) AS Total
                    FROM Compras_PedidosDetalle
                    GROUP BY PedidoCompraID
                ) d ON d.PedidoCompraID = p.PedidoCompraID
                WHERE p.EmpresaID = %s AND p.SucursalID = %s
                  AND (p.Total = 0 OR p.Total IS NULL)
            """, (empresa_id, sucursal_id))
        
        conn.commit()
        conn.close()
        
        return {"status": "OK", "encabezados_synced": enc_synced, "detalles_synced": det_synced}
        
    except Exception as e:
        logger.error(f"[SYNC] Error en sync_pedidos: {e}")
        return {"status": "ERROR", "error": str(e), "encabezados_synced": 0, "detalles_synced": 0}



def sync_ordenes_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    dias_atras: int = 30,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Sincroniza órdenes de compra desde servidor físico a EDARSAHUB.
    Destino: Compras_Ordenes + Compras_OrdenesDetalle
    
    Llave MERGE: EmpresaID + SucursalID + FolioOrden
    """
    ctx = _get_edarsahub_context(server_info, unidad_info)
    empresa_id = ctx['empresa_id']
    sucursal_id = ctx['sucursal_id']
    system_type = ctx['system_type']
    
    logger.info(f"[SYNC] Iniciando sync ordenes: Empresa={empresa_id}, Sucursal={sucursal_id}")
    
    try:
        if 'MPRO' in system_type.upper() or 'MANAGEMENT' in system_type.upper():
            query_encabezado = f"""
                SELECT TOP 500
                    Oc_Folio AS folio_orden,
                    Oc_Fecha AS fecha_orden,
                    Pv_Cve_Proveedor AS proveedor_id,
                    Oc_Total AS total,
                    Oc_Estatus AS estatus
                FROM Orden_Compra
                WHERE Oc_Fecha >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """
        else:
            query_encabezado = f"""
                SELECT TOP 500
                    CAST(o.folio AS VARCHAR(50)) AS folio_orden,
                    o.fechacaptura AS fecha_orden,
                    CAST(o.idproveedor AS INT) AS proveedor_id,
                    0 AS total,
                    'ACTIVO' AS estatus
                FROM ordenescompra o
                WHERE o.fechacaptura >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """
        
        result_enc = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_encabezado
        )
        
        if result_enc is None:
            return {"status": "ERROR", "error": "Timeout conexión", "encabezados_synced": 0, "detalles_synced": 0}
        
        if not result_enc:
            return {"status": "OK", "encabezados_synced": 0, "detalles_synced": 0, "message": "Sin ordenes en origen"}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        enc_synced = 0
        
        for enc in result_enc:
            try:
                folio = str(enc.get('folio_orden', ''))[:50]
                fecha = enc.get('fecha_orden')
                proveedor_id = enc.get('proveedor_id') or 1
                total = float(enc.get('total') or 0)
                
                cursor.execute("""
                    MERGE INTO Compras_Ordenes AS target
                    USING (SELECT %s AS EmpresaID, %s AS SucursalID, %s AS FolioOrden) AS source 
                    ON target.EmpresaID = source.EmpresaID 
                       AND target.SucursalID = source.SucursalID 
                       AND target.FolioOrden = source.FolioOrden
                    WHEN MATCHED THEN 
                        UPDATE SET Total = %s, ModifiedAt = GETDATE()
                    WHEN NOT MATCHED THEN 
                        INSERT (FolioOrden, EmpresaID, SucursalID, FechaOrden, ProveedorID, CompradorUsuarioID,
                                MonedaID, TipoCambio, EstatusOrdenCompraID, Total, Activo, CreatedAt, Subtotal, DescuentoTotal, ImpuestoTotal)
                        VALUES (%s, %s, %s, %s, %s, 1, 1, 1, 1, %s, 1, GETDATE(), %s, 0, 0);
                """, (
                    empresa_id, sucursal_id, folio,
                    total,
                    folio, empresa_id, sucursal_id, fecha, proveedor_id, total, total
                ))
                enc_synced += 1
                
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando orden {enc.get('folio_orden')}: {e}")
        
        conn.commit()
        conn.close()
        
        return {"status": "OK", "encabezados_synced": enc_synced, "detalles_synced": 0}
        
    except Exception as e:
        logger.error(f"[SYNC] Error en sync_ordenes: {e}")
        return {"status": "ERROR", "error": str(e), "encabezados_synced": 0, "detalles_synced": 0}



def sync_recepciones_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    dias_atras: int = 30,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Sincroniza recepciones de compra desde servidor físico a EDARSAHUB.
    Origen SR: tabla 'compras' (recepciones de mercancía)
    Destino: Compras_Recepciones + Compras_RecepcionesDetalle
    
    Llave MERGE: EmpresaID + SucursalID + FolioRecepcion
    """
    ctx = _get_edarsahub_context(server_info, unidad_info)
    empresa_id = ctx['empresa_id']
    sucursal_id = ctx['sucursal_id']
    system_type = ctx['system_type']
    
    logger.info(f"[SYNC] Iniciando sync recepciones: Empresa={empresa_id}, Sucursal={sucursal_id}")
    
    try:
        if 'MPRO' in system_type.upper() or 'MANAGEMENT' in system_type.upper():
            query_encabezado = f"""
                SELECT TOP 500
                    Re_Folio AS folio_recepcion,
                    Re_Fecha AS fecha_recepcion,
                    Pv_Cve_Proveedor AS proveedor_id,
                    Re_Total AS total
                FROM Recepcion
                WHERE Re_Fecha >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """
        else:
            # SoftRestaurant - tabla 'compras' (recepciones de mercancía)
            # NOTA: 'compras' no tiene idalmacen directamente, se debe obtener del movimiento
            query_encabezado = f"""
                SELECT TOP 500
                    CAST(c.idcompra AS VARCHAR(50)) AS folio_recepcion,
                    c.fechaaplicacion AS fecha_recepcion,
                    CAST(c.idproveedor AS INT) AS proveedor_id,
                    ISNULL(c.total, 0) AS total,
                    1 AS almacen_id
                FROM compras c
                WHERE c.fechaaplicacion >= DATEADD(DAY, -{dias_atras}, GETDATE())
                  AND ISNULL(c.cancelado, 0) = 0
            """
        
        result_enc = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_encabezado
        )
        
        if result_enc is None:
            return {"status": "ERROR", "error": "Timeout conexión", "encabezados_synced": 0, "detalles_synced": 0}
        
        if not result_enc:
            return {"status": "OK", "encabezados_synced": 0, "detalles_synced": 0, "message": "Sin recepciones en origen"}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        enc_synced = 0
        
        for enc in result_enc:
            try:
                folio = str(enc.get('folio_recepcion', ''))[:50]
                fecha = enc.get('fecha_recepcion')
                proveedor_id = enc.get('proveedor_id') or 1
                almacen_id = enc.get('almacen_id') or 1
                total = float(enc.get('total') or 0)
                
                cursor.execute("""
                    MERGE INTO Compras_Recepciones AS target
                    USING (SELECT %s AS EmpresaID, %s AS SucursalID, %s AS FolioRecepcion) AS source 
                    ON target.EmpresaID = source.EmpresaID 
                       AND target.SucursalID = source.SucursalID 
                       AND target.FolioRecepcion = source.FolioRecepcion
                    WHEN MATCHED THEN 
                        UPDATE SET Total = %s, ModifiedAt = GETDATE()
                    WHEN NOT MATCHED THEN 
                        INSERT (FolioRecepcion, EmpresaID, SucursalID, AlmacenID, ProveedorID, FechaRecepcion,
                                EstatusRecepcionID, Total, Activo, CreatedAt, Subtotal, ImpuestoTotal, TieneIncidencias)
                        VALUES (%s, %s, %s, %s, %s, %s, 1, %s, 1, GETDATE(), %s, 0, 0);
                """, (
                    empresa_id, sucursal_id, folio,
                    total,
                    folio, empresa_id, sucursal_id, almacen_id, proveedor_id, fecha, total, total
                ))
                enc_synced += 1
                
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando recepcion {enc.get('folio_recepcion')}: {e}")
        
        conn.commit()
        conn.close()
        
        return {"status": "OK", "encabezados_synced": enc_synced, "detalles_synced": 0}
        
    except Exception as e:
        logger.error(f"[SYNC] Error en sync_recepciones: {e}")
        return {"status": "ERROR", "error": str(e), "encabezados_synced": 0, "detalles_synced": 0}


