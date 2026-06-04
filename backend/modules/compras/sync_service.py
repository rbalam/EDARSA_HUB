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
            query += " AND LOWER(server_id) = LOWER(%s)"
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
                    COUNT(F.Pr_Cve_Producto) as total_productos
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
                    CAST(A.idalmacen AS VARCHAR) as almacen_id,
                    '' as sucursal,
                    '' as sucursal_id,
                    'FISICO' as tipo,
                    'CERRADO' as estatus,
                    0 as total_productos
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
    """
    server_id = server_info.get('id')
    system_type = server_info.get('system_type', '').upper()
    unidad_codigo = unidad_info.get('codigo', '')
    
    logger.info(f"[SYNC] Iniciando sync almacenes: {unidad_codigo} ({system_type})")
    
    try:
        if 'MPRO' in system_type or 'MANAGEMENT' in system_type:
            query_origen = """
                SELECT 
                    Al_Cve_Almacen AS almacen_id,
                    Al_Descripcion AS nombre,
                    Sc_Cve_Sucursal AS sucursal_id,
                    Al_Estatus AS activo
                FROM Almacen
                WHERE Al_Estatus = 'A'
            """
        else:
            query_origen = """
                SELECT 
                    CAST(idalmacen AS VARCHAR) AS almacen_id,
                    nombre,
                    CAST(idsucursal AS VARCHAR) AS sucursal_id,
                    estatus AS activo
                FROM almacen
                WHERE estatus = 1
            """
        
        result_origen = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_origen
        )
        
        if result_origen is None:
            return {"success": False, "error": "Timeout o error de conexión", "records_synced": 0}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        records_synced = 0
        for row in result_origen:
            try:
                cursor.execute("""
                    MERGE INTO Inventario_Almacenes AS target
                    USING (SELECT %s AS AlmacenID) AS source ON target.AlmacenID = source.AlmacenID AND target.ServerID = %s
                    WHEN MATCHED THEN UPDATE SET NombreAlmacen = %s, SucursalID = %s, Activo = %s, FechaModificacion = GETDATE()
                    WHEN NOT MATCHED THEN INSERT (AlmacenID, ServerID, NombreAlmacen, SucursalID, Activo, OrigenSistema, FechaCreacion)
                    VALUES (%s, %s, %s, %s, %s, %s, GETDATE());
                """, (
                    row.get('almacen_id'), server_id, row.get('nombre', ''), row.get('sucursal_id', ''),
                    1 if row.get('activo') in ('A', 1, '1', True) else 0,
                    row.get('almacen_id'), server_id, row.get('nombre', ''), row.get('sucursal_id', ''),
                    1 if row.get('activo') in ('A', 1, '1', True) else 0, system_type
                ))
                records_synced += 1
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando almacen {row.get('almacen_id')}: {e}")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "records_synced": records_synced}
        
    except Exception as e:
        logger.error(f"[SYNC] Error sync almacenes {unidad_codigo}: {e}")
        return {"success": False, "error": str(e), "records_synced": 0}


def sync_existencias_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable
) -> Dict[str, Any]:
    """
    Sincroniza existencias de inventario desde servidor físico a EDARSAHUB.
    Destino: Inventario_Existencias
    """
    server_id = server_info.get('id')
    system_type = server_info.get('system_type', '').upper()
    unidad_codigo = unidad_info.get('codigo', '')
    
    logger.info(f"[SYNC] Iniciando sync existencias: {unidad_codigo} ({system_type})")
    
    try:
        if 'MPRO' in system_type or 'MANAGEMENT' in system_type:
            query_origen = """
                SELECT TOP 5000
                    Ar_Cve_Articulo AS producto_id,
                    Ar_Descripcion AS producto_nombre,
                    Al_Cve_Almacen AS almacen_id,
                    Ex_Existencia AS existencia,
                    Ex_Costo_Promedio AS costo_promedio,
                    Ex_Ultimo_Costo AS ultimo_costo
                FROM Existencia E
                INNER JOIN Articulo A ON A.Ar_Cve_Articulo = E.Ar_Cve_Articulo
                WHERE E.Ex_Existencia <> 0
            """
        else:
            query_origen = """
                SELECT TOP 5000
                    CAST(I.idinsumo AS VARCHAR) AS producto_id,
                    I.nombre AS producto_nombre,
                    CAST(E.idalmacen AS VARCHAR) AS almacen_id,
                    E.existencia,
                    E.costopromedio AS costo_promedio,
                    E.ultimocosto AS ultimo_costo
                FROM existencias E
                INNER JOIN insumos I ON I.idinsumo = E.idinsumo
                WHERE E.existencia <> 0
            """
        
        result_origen = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_origen
        )
        
        if result_origen is None:
            return {"success": False, "error": "Timeout o error de conexión", "records_synced": 0}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        # Marcar existencias anteriores como históricas
        cursor.execute("""
            UPDATE Inventario_Existencias SET EsActual = 0
            WHERE ServerID = %s AND EsActual = 1
        """, (server_id,))
        
        records_synced = 0
        for row in result_origen:
            try:
                cursor.execute("""
                    INSERT INTO Inventario_Existencias
                    (ServerID, ProductoID, ProductoNombre, AlmacenID, Existencia, CostoPromedio, UltimoCosto, OrigenSistema, EsActual, FechaSync)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, GETDATE())
                """, (
                    server_id, row.get('producto_id'), row.get('producto_nombre', ''),
                    row.get('almacen_id'), float(row.get('existencia') or 0),
                    float(row.get('costo_promedio') or 0), float(row.get('ultimo_costo') or 0),
                    system_type
                ))
                records_synced += 1
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando existencia {row.get('producto_id')}: {e}")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "records_synced": records_synced}
        
    except Exception as e:
        logger.error(f"[SYNC] Error sync existencias {unidad_codigo}: {e}")
        return {"success": False, "error": str(e), "records_synced": 0}


def sync_movimientos_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    fecha_inicio: str = None,
    fecha_fin: str = None
) -> Dict[str, Any]:
    """
    Sincroniza movimientos de inventario desde servidor físico a EDARSAHUB.
    Destino: Inventario_Movimientos, Inventario_MovimientosDetalle
    """
    server_id = server_info.get('id')
    system_type = server_info.get('system_type', '').upper()
    unidad_codigo = unidad_info.get('codigo', '')
    
    logger.info(f"[SYNC] Iniciando sync movimientos: {unidad_codigo} ({system_type})")
    
    # Por defecto últimos 7 días
    if not fecha_inicio:
        from datetime import datetime, timedelta
        fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    if not fecha_fin:
        from datetime import datetime
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
    
    try:
        if 'MPRO' in system_type or 'MANAGEMENT' in system_type:
            query_origen = f"""
                SELECT TOP 2000
                    M.Mv_Folio AS folio,
                    M.Mv_Fecha AS fecha,
                    M.Mv_Tipo AS tipo_movimiento,
                    M.Al_Cve_Almacen AS almacen_id,
                    CASE WHEN M.Mv_Tipo IN ('EN', 'CO', 'AJ+') THEN 1 ELSE 0 END AS es_entrada,
                    D.Ar_Cve_Articulo AS producto_id,
                    A.Ar_Descripcion AS producto_nombre,
                    D.Md_Cantidad AS cantidad,
                    D.Md_Costo AS costo_unitario
                FROM Movimiento M
                INNER JOIN Movimiento_Detalle D ON D.Mv_Folio = M.Mv_Folio
                INNER JOIN Articulo A ON A.Ar_Cve_Articulo = D.Ar_Cve_Articulo
                WHERE M.Mv_Fecha >= '{fecha_inicio}' AND M.Mv_Fecha <= '{fecha_fin}'
                ORDER BY M.Mv_Fecha DESC
            """
        else:
            query_origen = f"""
                SELECT TOP 2000
                    M.folio,
                    M.fecha,
                    M.concepto AS tipo_movimiento,
                    CAST(M.idalmacen AS VARCHAR) AS almacen_id,
                    M.esentrada AS es_entrada,
                    CAST(D.idinsumo AS VARCHAR) AS producto_id,
                    I.nombre AS producto_nombre,
                    D.cantidad,
                    D.costo AS costo_unitario
                FROM movimientos M
                INNER JOIN movimientosmov D ON D.idmovimiento = M.idmovimiento
                INNER JOIN insumos I ON I.idinsumo = D.idinsumo
                WHERE M.fecha >= '{fecha_inicio}' AND M.fecha <= '{fecha_fin}'
                ORDER BY M.fecha DESC
            """
        
        result_origen = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_origen
        )
        
        if result_origen is None:
            return {"success": False, "error": "Timeout o error de conexión", "records_synced": 0}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        records_synced = 0
        for row in result_origen:
            try:
                cursor.execute("""
                    INSERT INTO Inventario_MovimientosDetalle
                    (ServerID, Folio, FechaMovimiento, TipoMovimiento, AlmacenID, EsEntrada,
                     CodigoProducto, NombreProducto, Cantidad, CostoUnitario, OrigenSistema, FechaSync)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE())
                """, (
                    server_id, str(row.get('folio') or ''), row.get('fecha'),
                    row.get('tipo_movimiento', ''), row.get('almacen_id', ''),
                    1 if row.get('es_entrada') in (1, '1', True) else 0,
                    row.get('producto_id'), row.get('producto_nombre', ''),
                    float(row.get('cantidad') or 0), float(row.get('costo_unitario') or 0),
                    system_type
                ))
                records_synced += 1
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando movimiento {row.get('folio')}: {e}")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "records_synced": records_synced}
        
    except Exception as e:
        logger.error(f"[SYNC] Error sync movimientos {unidad_codigo}: {e}")
        return {"success": False, "error": str(e), "records_synced": 0}


def sync_pedidos_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    dias_atras: int = 30
) -> Dict[str, Any]:
    """
    Sincroniza pedidos de compra desde servidor físico a EDARSAHUB.
    Destino: Compras_Pedidos, Compras_PedidosDetalle
    """
    server_id = server_info.get('id')
    system_type = server_info.get('system_type', '').upper()
    unidad_codigo = unidad_info.get('codigo', '')
    unidad_id = unidad_info.get('id', '')
    
    logger.info(f"[SYNC] Iniciando sync pedidos: {unidad_codigo} ({system_type})")
    
    try:
        if 'MPRO' in system_type or 'MANAGEMENT' in system_type:
            query_cabecera = f"""
                SELECT TOP 500
                    Pc_Folio AS folio,
                    Pc_Fecha AS fecha,
                    Pc_Estatus AS estatus,
                    Pv_Cve_Proveedor AS proveedor_id,
                    P.Pv_Nombre AS proveedor_nombre,
                    Pc_Importe_Total AS importe_total,
                    Pc_Comentario AS comentario
                FROM Pedido_Compra PC
                LEFT JOIN Proveedor P ON P.Pv_Cve_Proveedor = PC.Pv_Cve_Proveedor
                WHERE Pc_Fecha >= DATEADD(day, -{dias_atras}, GETDATE())
                ORDER BY Pc_Fecha DESC
            """
        else:
            query_cabecera = f"""
                SELECT TOP 500
                    idPedidoCompra AS folio,
                    fecha,
                    estatus,
                    CAST(idProveedor AS VARCHAR) AS proveedor_id,
                    P.razonSocial AS proveedor_nombre,
                    importe AS importe_total,
                    comentarios AS comentario
                FROM pedidoscompra PC
                LEFT JOIN proveedores P ON P.idProveedor = PC.idProveedor
                WHERE fecha >= DATEADD(day, -{dias_atras}, GETDATE())
                ORDER BY fecha DESC
            """
        
        result_cabecera = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_cabecera
        )
        
        if result_cabecera is None:
            return {"success": False, "error": "Timeout o error de conexión", "records_synced": 0}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        records_synced = 0
        for row in result_cabecera:
            try:
                cursor.execute("""
                    MERGE INTO Compras_Pedidos AS target
                    USING (SELECT %s AS FolioPedido, %s AS ServerID) AS source 
                    ON target.FolioPedido = source.FolioPedido AND target.ServerID = source.ServerID
                    WHEN MATCHED THEN UPDATE SET 
                        FechaPedido = %s, Estatus = %s, ProveedorID = %s, ProveedorNombre = %s,
                        ImporteTotal = %s, Comentario = %s, FechaModificacion = GETDATE()
                    WHEN NOT MATCHED THEN INSERT 
                        (FolioPedido, ServerID, UnidadNegocioID, FechaPedido, Estatus, ProveedorID, ProveedorNombre,
                         ImporteTotal, Comentario, OrigenSistema, SyncStatus, FechaCreacion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'SYNCED', GETDATE());
                """, (
                    str(row.get('folio')), server_id,
                    row.get('fecha'), row.get('estatus', ''), row.get('proveedor_id', ''),
                    row.get('proveedor_nombre', ''), float(row.get('importe_total') or 0), row.get('comentario', ''),
                    str(row.get('folio')), server_id, unidad_id, row.get('fecha'), row.get('estatus', ''),
                    row.get('proveedor_id', ''), row.get('proveedor_nombre', ''),
                    float(row.get('importe_total') or 0), row.get('comentario', ''), system_type
                ))
                records_synced += 1
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando pedido {row.get('folio')}: {e}")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "records_synced": records_synced}
        
    except Exception as e:
        logger.error(f"[SYNC] Error sync pedidos {unidad_codigo}: {e}")
        return {"success": False, "error": str(e), "records_synced": 0}


def sync_ordenes_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    dias_atras: int = 30
) -> Dict[str, Any]:
    """
    Sincroniza órdenes de compra desde servidor físico a EDARSAHUB.
    Destino: Compras_Ordenes, Compras_OrdenesDetalle
    """
    server_id = server_info.get('id')
    system_type = server_info.get('system_type', '').upper()
    unidad_codigo = unidad_info.get('codigo', '')
    unidad_id = unidad_info.get('id', '')
    
    logger.info(f"[SYNC] Iniciando sync ordenes: {unidad_codigo} ({system_type})")
    
    try:
        if 'MPRO' in system_type or 'MANAGEMENT' in system_type:
            query_cabecera = f"""
                SELECT TOP 500
                    Oc_Folio AS folio,
                    Oc_Fecha AS fecha,
                    Oc_Estatus AS estatus,
                    Pv_Cve_Proveedor AS proveedor_id,
                    P.Pv_Nombre AS proveedor_nombre,
                    Oc_Importe_Total AS importe_total
                FROM Orden_Compra OC
                LEFT JOIN Proveedor P ON P.Pv_Cve_Proveedor = OC.Pv_Cve_Proveedor
                WHERE Oc_Fecha >= DATEADD(day, -{dias_atras}, GETDATE())
                ORDER BY Oc_Fecha DESC
            """
        else:
            query_cabecera = f"""
                SELECT TOP 500
                    idOrdenCompra AS folio,
                    fecha,
                    estatus,
                    CAST(idProveedor AS VARCHAR) AS proveedor_id,
                    P.razonSocial AS proveedor_nombre,
                    importe AS importe_total
                FROM ordenescompra OC
                LEFT JOIN proveedores P ON P.idProveedor = OC.idProveedor
                WHERE fecha >= DATEADD(day, -{dias_atras}, GETDATE())
                ORDER BY fecha DESC
            """
        
        result_cabecera = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_cabecera
        )
        
        if result_cabecera is None:
            return {"success": False, "error": "Timeout o error de conexión", "records_synced": 0}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        records_synced = 0
        for row in result_cabecera:
            try:
                cursor.execute("""
                    MERGE INTO Compras_Ordenes AS target
                    USING (SELECT %s AS FolioOrden, %s AS ServerID) AS source 
                    ON target.FolioOrden = source.FolioOrden AND target.ServerID = source.ServerID
                    WHEN MATCHED THEN UPDATE SET 
                        FechaOrden = %s, Estatus = %s, ProveedorID = %s, ProveedorNombre = %s,
                        ImporteTotal = %s, FechaModificacion = GETDATE()
                    WHEN NOT MATCHED THEN INSERT 
                        (FolioOrden, ServerID, UnidadNegocioID, FechaOrden, Estatus, ProveedorID, ProveedorNombre,
                         ImporteTotal, OrigenSistema, SyncStatus, FechaCreacion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'SYNCED', GETDATE());
                """, (
                    str(row.get('folio')), server_id,
                    row.get('fecha'), row.get('estatus', ''), row.get('proveedor_id', ''),
                    row.get('proveedor_nombre', ''), float(row.get('importe_total') or 0),
                    str(row.get('folio')), server_id, unidad_id, row.get('fecha'), row.get('estatus', ''),
                    row.get('proveedor_id', ''), row.get('proveedor_nombre', ''),
                    float(row.get('importe_total') or 0), system_type
                ))
                records_synced += 1
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando orden {row.get('folio')}: {e}")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "records_synced": records_synced}
        
    except Exception as e:
        logger.error(f"[SYNC] Error sync ordenes {unidad_codigo}: {e}")
        return {"success": False, "error": str(e), "records_synced": 0}


def sync_recepciones_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    dias_atras: int = 30
) -> Dict[str, Any]:
    """
    Sincroniza recepciones/facturas de compra desde servidor físico a EDARSAHUB.
    Destino: Compras_Recepciones, Compras_RecepcionesDetalle
    """
    server_id = server_info.get('id')
    system_type = server_info.get('system_type', '').upper()
    unidad_codigo = unidad_info.get('codigo', '')
    unidad_id = unidad_info.get('id', '')
    
    logger.info(f"[SYNC] Iniciando sync recepciones: {unidad_codigo} ({system_type})")
    
    try:
        if 'MPRO' in system_type or 'MANAGEMENT' in system_type:
            query_cabecera = f"""
                SELECT TOP 500
                    Re_Folio AS folio,
                    Re_Factura AS folio_factura,
                    Re_Fecha AS fecha,
                    Re_Estatus AS estatus,
                    Pv_Cve_Proveedor AS proveedor_id,
                    P.Pv_Nombre AS proveedor_nombre,
                    Re_Importe_Total AS importe_total
                FROM Recepcion R
                LEFT JOIN Proveedor P ON P.Pv_Cve_Proveedor = R.Pv_Cve_Proveedor
                WHERE Re_Fecha >= DATEADD(day, -{dias_atras}, GETDATE())
                ORDER BY Re_Fecha DESC
            """
        else:
            query_cabecera = f"""
                SELECT TOP 500
                    idRecepcion AS folio,
                    factura AS folio_factura,
                    fecha,
                    estatus,
                    CAST(idProveedor AS VARCHAR) AS proveedor_id,
                    P.razonSocial AS proveedor_nombre,
                    importe AS importe_total
                FROM recepciones R
                LEFT JOIN proveedores P ON P.idProveedor = R.idProveedor
                WHERE fecha >= DATEADD(day, -{dias_atras}, GETDATE())
                ORDER BY fecha DESC
            """
        
        result_cabecera = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_cabecera
        )
        
        if result_cabecera is None:
            return {"success": False, "error": "Timeout o error de conexión", "records_synced": 0}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        records_synced = 0
        for row in result_cabecera:
            try:
                cursor.execute("""
                    MERGE INTO Compras_Recepciones AS target
                    USING (SELECT %s AS FolioRecepcion, %s AS ServerID) AS source 
                    ON target.FolioRecepcion = source.FolioRecepcion AND target.ServerID = source.ServerID
                    WHEN MATCHED THEN UPDATE SET 
                        FolioFactura = %s, FechaRecepcion = %s, Estatus = %s, ProveedorID = %s, ProveedorNombre = %s,
                        ImporteTotal = %s, FechaModificacion = GETDATE()
                    WHEN NOT MATCHED THEN INSERT 
                        (FolioRecepcion, FolioFactura, ServerID, UnidadNegocioID, FechaRecepcion, Estatus, 
                         ProveedorID, ProveedorNombre, ImporteTotal, OrigenSistema, SyncStatus, FechaCreacion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'SYNCED', GETDATE());
                """, (
                    str(row.get('folio')), server_id,
                    row.get('folio_factura', ''), row.get('fecha'), row.get('estatus', ''),
                    row.get('proveedor_id', ''), row.get('proveedor_nombre', ''),
                    float(row.get('importe_total') or 0),
                    str(row.get('folio')), row.get('folio_factura', ''), server_id, unidad_id,
                    row.get('fecha'), row.get('estatus', ''), row.get('proveedor_id', ''),
                    row.get('proveedor_nombre', ''), float(row.get('importe_total') or 0), system_type
                ))
                records_synced += 1
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando recepcion {row.get('folio')}: {e}")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "records_synced": records_synced}
        
    except Exception as e:
        logger.error(f"[SYNC] Error sync recepciones {unidad_codigo}: {e}")
        return {"success": False, "error": str(e), "records_synced": 0}
