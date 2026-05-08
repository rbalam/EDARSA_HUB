"""
REPOSITORY READONLY - COMERCIAL V2
===================================

Funciones de SOLO LECTURA para endpoints v2.
Lee exclusivamente de tablas Comercial_*_v2 en EDARSAHUB.

NO consulta:
- SQL vivo a SoftRestaurant/MPRO
- MongoDB cache
- Datos demo

FUENTES ÚNICAS:
- Comercial_KPIs_Diarios_v2
- Comercial_KPIs_Mensuales_v2
- Comercial_Ventas_Dia_Abiertas_v2
- Comercial_SyncLog_v2
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
import logging

from core.db import execute_sql_query

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURACIÓN EDARSAHUB (SOLO LECTURA)
# =============================================================================

EDARSAHUB_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'HRLectura',
    'password': 'National09$'
}


def _execute_readonly_query(query: str) -> List[Dict]:
    """Ejecuta una query de SOLO LECTURA en EDARSAHUB."""
    try:
        result = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        return result or []
    except Exception as e:
        logger.error(f"Error ejecutando query EDARSAHUB v2: {e}")
        raise


# =============================================================================
# FUNCIONES DE LECTURA - KPIs DIARIOS
# =============================================================================

def get_kpis_diarios(
    fecha_inicio: date,
    fecha_fin: date,
    unidades_permitidas: Optional[List[str]] = None
) -> List[Dict]:
    """
    Obtiene KPIs diarios desde Comercial_KPIs_Diarios_v2.
    
    Args:
        fecha_inicio: Fecha de inicio del período
        fecha_fin: Fecha de fin del período
        unidades_permitidas: Lista de unidad_negocio_id permitidas por RBAC
        
    Returns:
        Lista de KPIs diarios
    """
    where_clauses = [
        f"fecha_operacion BETWEEN '{fecha_inicio.isoformat()}' AND '{fecha_fin.isoformat()}'",
        "activo = 1",
        "es_demo = 0"
    ]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    query = f"""
    SELECT 
        id,
        unidad_negocio_id,
        unidad_negocio_nombre,
        server_id,
        sucursal_id,
        sistema_origen,
        fecha_operacion,
        anio,
        mes,
        dia,
        ventas_total,
        ventas_sin_propina,
        propinas_total,
        tickets_total,
        pax_total,
        ticket_promedio,
        pax_promedio,
        ventas_cerradas,
        ventas_abiertas,
        total_estimado_dia,
        es_venta_abierta,
        es_corte_cerrado,
        fuente_original,
        hash_origen,
        fecha_creacion,
        fecha_ultima_actualizacion
    FROM Comercial_KPIs_Diarios_v2
    WHERE {' AND '.join(where_clauses)}
    ORDER BY fecha_operacion DESC, unidad_negocio_id
    """
    
    return _execute_readonly_query(query)


def get_kpis_diarios_agregados(
    fecha_inicio: date,
    fecha_fin: date,
    unidades_permitidas: Optional[List[str]] = None
) -> Dict:
    """
    Obtiene KPIs diarios agregados (totales) para el dashboard.
    """
    where_clauses = [
        f"fecha_operacion BETWEEN '{fecha_inicio.isoformat()}' AND '{fecha_fin.isoformat()}'",
        "activo = 1",
        "es_demo = 0"
    ]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    query = f"""
    SELECT 
        COUNT(*) as total_registros,
        COUNT(DISTINCT unidad_negocio_id) as total_unidades,
        COUNT(DISTINCT fecha_operacion) as total_dias,
        SUM(ventas_total) as ventas_total,
        SUM(tickets_total) as tickets_total,
        SUM(pax_total) as pax_total,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max
    FROM Comercial_KPIs_Diarios_v2
    WHERE {' AND '.join(where_clauses)}
    """
    
    result = _execute_readonly_query(query)
    return result[0] if result else {}


def get_kpis_por_unidad(
    fecha_inicio: date,
    fecha_fin: date,
    unidades_permitidas: Optional[List[str]] = None
) -> List[Dict]:
    """
    Obtiene KPIs agregados por unidad para el dashboard.
    """
    where_clauses = [
        f"fecha_operacion BETWEEN '{fecha_inicio.isoformat()}' AND '{fecha_fin.isoformat()}'",
        "activo = 1",
        "es_demo = 0"
    ]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    query = f"""
    SELECT 
        unidad_negocio_id,
        unidad_negocio_nombre,
        sistema_origen,
        COUNT(*) as dias,
        SUM(ventas_total) as ventas_total,
        SUM(ventas_sin_propina) as ventas_sin_propina,
        SUM(propinas_total) as propinas_total,
        SUM(tickets_total) as tickets_total,
        SUM(pax_total) as pax_total,
        AVG(ticket_promedio) as ticket_promedio_avg,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max
    FROM Comercial_KPIs_Diarios_v2
    WHERE {' AND '.join(where_clauses)}
    GROUP BY unidad_negocio_id, unidad_negocio_nombre, sistema_origen
    ORDER BY unidad_negocio_id
    """
    
    return _execute_readonly_query(query)


# =============================================================================
# FUNCIONES DE LECTURA - KPIs MENSUALES
# =============================================================================

def get_kpis_mensuales(
    anio: int,
    mes_inicio: int = 1,
    mes_fin: int = 12,
    unidades_permitidas: Optional[List[str]] = None
) -> List[Dict]:
    """
    Obtiene KPIs mensuales desde Comercial_KPIs_Mensuales_v2.
    """
    where_clauses = [
        f"anio = {anio}",
        f"mes BETWEEN {mes_inicio} AND {mes_fin}",
        "activo = 1"
    ]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    query = f"""
    SELECT 
        id,
        unidad_negocio_id,
        unidad_negocio_nombre,
        anio,
        mes,
        ventas_total,
        tickets_total,
        pax_total,
        ticket_promedio,
        pax_promedio,
        dias_con_venta,
        fecha_ultima_actualizacion
    FROM Comercial_KPIs_Mensuales_v2
    WHERE {' AND '.join(where_clauses)}
    ORDER BY anio DESC, mes DESC, unidad_negocio_id
    """
    
    return _execute_readonly_query(query)


# =============================================================================
# FUNCIONES DE LECTURA - VENTAS DIA ABIERTAS
# =============================================================================

def get_ventas_dia_abiertas(
    fecha: date,
    unidades_permitidas: Optional[List[str]] = None
) -> List[Dict]:
    """
    Obtiene ventas del día (abiertas/sin corte) desde Comercial_Ventas_Dia_Abiertas_v2.
    
    Esta tabla contiene el snapshot más reciente del día actual para cada unidad,
    actualizado cada 5 minutos por el job sync_comercial_abiertas_v2.
    
    Columnas principales:
    - ventas_abiertas: Ventas sin cierre aún
    - ventas_cerradas_dia: Ventas ya cerradas del mismo día
    - total_estimado_dia: ventas_abiertas + ventas_cerradas_dia
    """
    where_clauses = [
        f"fecha_operacion = '{fecha.isoformat()}'"
    ]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    query = f"""
    SELECT 
        id,
        unidad_negocio_id,
        unidad_negocio_nombre,
        server_id,
        sucursal_id,
        sucursal_nombre,
        sistema_origen,
        snapshot_timestamp,
        fecha_operacion,
        ventas_abiertas,
        tickets_abiertos,
        pax_abiertos,
        ventas_cerradas_dia,
        tickets_cerrados_dia,
        pax_cerrados_dia,
        total_estimado_dia,
        fuente_original,
        sync_run_id,
        fecha_ultima_actualizacion
    FROM Comercial_Ventas_Dia_Abiertas_v2
    WHERE {' AND '.join(where_clauses)}
    ORDER BY unidad_negocio_id
    """
    
    return _execute_readonly_query(query)


# =============================================================================
# FUNCIONES DE LECTURA - SYNC LOG
# =============================================================================

def get_sync_status(
    unidades_permitidas: Optional[List[str]] = None,
    limit: int = 50
) -> List[Dict]:
    """
    Obtiene el estado de sincronización desde Comercial_SyncLog_v2.
    """
    where_clauses = ["1=1"]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    query = f"""
    SELECT TOP {limit}
        id,
        run_id,
        run_type,
        unidad_negocio_id,
        server_id,
        fecha_inicio,
        fecha_fin,
        status,
        records_processed,
        records_inserted,
        records_updated,
        records_skipped,
        records_errored,
        source_connection_status,
        error_message,
        duration_seconds,
        created_at
    FROM Comercial_SyncLog_v2
    WHERE {' AND '.join(where_clauses)}
    ORDER BY created_at DESC
    """
    
    return _execute_readonly_query(query)


def get_last_sync_by_unidad(
    unidades_permitidas: Optional[List[str]] = None
) -> List[Dict]:
    """
    Obtiene la última sincronización por unidad.
    """
    where_clauses = ["status = 'SUCCESS'"]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    query = f"""
    SELECT 
        unidad_negocio_id,
        MAX(created_at) as ultima_sync,
        MAX(fecha_fin) as ultimo_dia_sync
    FROM Comercial_SyncLog_v2
    WHERE {' AND '.join(where_clauses)}
    GROUP BY unidad_negocio_id
    ORDER BY unidad_negocio_id
    """
    
    return _execute_readonly_query(query)


# =============================================================================
# FUNCIONES DE LECTURA - UNIDADES
# =============================================================================

def get_unidades_disponibles(
    unidades_permitidas: Optional[List[str]] = None
) -> List[Dict]:
    """
    Obtiene las unidades que tienen datos en Comercial v2.
    """
    where_clauses = ["activo = 1", "es_demo = 0"]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    query = f"""
    SELECT DISTINCT
        unidad_negocio_id,
        unidad_negocio_nombre,
        sistema_origen,
        server_id,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max,
        COUNT(*) as total_dias,
        SUM(ventas_total) as ventas_historicas
    FROM Comercial_KPIs_Diarios_v2
    WHERE {' AND '.join(where_clauses)}
    GROUP BY unidad_negocio_id, unidad_negocio_nombre, sistema_origen, server_id
    ORDER BY unidad_negocio_id
    """
    
    return _execute_readonly_query(query)


# =============================================================================
# FUNCIONES DE SALUD
# =============================================================================

def check_v2_health() -> Dict:
    """
    Verifica el estado de salud de Comercial v2.
    """
    try:
        # Test básico de conexión
        result = _execute_readonly_query("SELECT 1 AS test")
        
        if not result:
            return {"status": "error", "message": "No response from EDARSAHUB"}
        
        # Verificar datos
        stats = _execute_readonly_query("""
            SELECT 
                COUNT(*) as total_registros,
                COUNT(DISTINCT unidad_negocio_id) as total_unidades,
                MIN(fecha_operacion) as fecha_min,
                MAX(fecha_operacion) as fecha_max
            FROM Comercial_KPIs_Diarios_v2
            WHERE activo = 1 AND es_demo = 0
        """)
        
        if stats:
            return {
                "status": "ok",
                "source": "EDARSAHUB_V2",
                "table": "Comercial_KPIs_Diarios_v2",
                "total_registros": stats[0].get('total_registros', 0),
                "total_unidades": stats[0].get('total_unidades', 0),
                "rango_datos": {
                    "desde": str(stats[0].get('fecha_min', '')),
                    "hasta": str(stats[0].get('fecha_max', ''))
                }
            }
        
        return {"status": "ok", "source": "EDARSAHUB_V2", "message": "Connected but no data"}
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "message": str(e)}
