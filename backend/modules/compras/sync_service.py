"""
COMPRAS SYNC SERVICE - Sincronización de Inventarios y Requisiciones a EDARSAHUB
================================================================================
POLÍTICA: Todo se lee de EDARSAHUB SQL. Los servidores físicos solo se consultan
durante la sincronización (job background).

Tablas EDARSAHUB:
- Compras_Inventarios_Fisicos_Sync: Inventarios físicos sincronizados
- Compras_Requisiciones_Sync: Requisiciones/pedidos sincronizados
- Compras_Sync_Log: Log de sincronizaciones
"""

import pymssql
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Configuración EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'HRLectura',
    'password': 'National09$'
}


def get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB"""
    return pymssql.connect(
        server=EDARSAHUB_CONFIG['host'],
        user=EDARSAHUB_CONFIG['username'],
        password=EDARSAHUB_CONFIG['password'],
        database=EDARSAHUB_CONFIG['database'],
        port=EDARSAHUB_CONFIG['port'],
        timeout=30
    )


# =============================================================================
# LECTURA DE DATOS SINCRONIZADOS (Endpoints usan estas funciones)
# =============================================================================

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
        
        query = """
            SELECT 
                folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
                tipo, estatus, total_productos, unidad_negocio_id, 
                unidad_negocio_codigo, server_id, system_type,
                sync_timestamp, sync_status
            FROM Compras_Inventarios_Fisicos_Sync
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
        
        if almacen and almacen != 'TODOS':
            query += " AND almacen LIKE %s"
            params.append(f'%{almacen}%')
        
        query += f" ORDER BY fecha DESC OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"
        
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
            query = """
                SELECT DISTINCT 
                    F.Fi_Folio as folio,
                    F.Fi_Fecha as fecha,
                    A.Al_Descripcion as almacen,
                    A.Al_Cve_Almacen as almacen_id,
                    S.Sc_Descripcion as sucursal,
                    A.Sc_Cve_Sucursal as sucursal_id,
                    'FISICO' as tipo,
                    CASE WHEN F.Fi_Status = 1 THEN 'CERRADO' ELSE 'ABIERTO' END as estatus,
                    (SELECT COUNT(*) FROM Fi_Detalle WHERE Fi_Folio = F.Fi_Folio) as total_productos
                FROM Fisico_Inventario F
                INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen
                LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
                WHERE F.Fi_Fecha >= DATEADD(MONTH, -6, GETDATE())
                ORDER BY F.Fi_Fecha DESC
            """
        elif is_softrestaurant_system(system_type):
            query = """
                SELECT DISTINCT
                    CAST(I.idInventario AS VARCHAR) as folio,
                    I.fecha as fecha,
                    A.nombre as almacen,
                    CAST(A.idAlmacen AS VARCHAR) as almacen_id,
                    '' as sucursal,
                    '' as sucursal_id,
                    'FISICO' as tipo,
                    CASE WHEN I.cerrado = 1 THEN 'CERRADO' ELSE 'ABIERTO' END as estatus,
                    (SELECT COUNT(*) FROM inventariomov WHERE idInventario = I.idInventario) as total_productos
                FROM inventario I
                INNER JOIN almacen A ON A.idAlmacen = I.idAlmacen
                WHERE I.fecha >= DATEADD(MONTH, -6, GETDATE())
                ORDER BY I.fecha DESC
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
                     tipo, estatus, total_productos, sync_source, sync_timestamp, sync_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'SYNC', GETDATE(), 'ACTIVE')
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
                    row.get('total_productos', 0)
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
