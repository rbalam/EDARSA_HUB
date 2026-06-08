import os
from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
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
- vw_Comercial_KPIs_Diarios_v2_Runtime
- vw_Comercial_KPIs_Mensuales_v2_Runtime
- Comercial_Ventas_Dia_Abiertas_v2
- Comercial_SyncLog_v2
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
import logging

from core.db import execute_sql_query
from core.sql_first.db import get_sql_connection

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURACIÓN EDARSAHUB (SOLO LECTURA)
# =============================================================================

EDARSAHUB_CONFIG = {
    'host': os.getenv('EDARSAHUB_SQL_HOST'),
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': os.getenv('EDARSAHUB_SQL_USER'),
    'password': os.getenv('EDARSAHUB_SQL_PASSWORD')
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
    Obtiene KPIs diarios desde vw_Comercial_KPIs_Diarios_v2_Runtime.
    
    Args:
        fecha_inicio: Fecha de inicio del período
        fecha_fin: Fecha de fin del período
        unidades_permitidas: Lista de unidad_negocio_pk permitidas por RBAC
        
    Returns:
        Lista de KPIs diarios
    """
    where_clauses = [
        f"fecha_operacion BETWEEN '{fecha_inicio.isoformat()}' AND '{fecha_fin.isoformat()}'"
    ]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    query = f"""
    SELECT 
        id,
        unidad_negocio_pk,
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
        fecha_alta,
        fecha_sincronizacion
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE {' AND '.join(where_clauses)}
    ORDER BY fecha_operacion DESC, unidad_negocio_pk
    """
    
    return _execute_readonly_query(query)


def get_kpis_diarios_agregados(
    fecha_inicio: date,
    fecha_fin: date,
    unidades_permitidas: Optional[List[str]] = None,
    meses: Optional[List[int]] = None
) -> Dict:
    """
    Obtiene KPIs diarios agregados (totales) para el dashboard.

    MÁXIMA: KPI de ventas = ventas_sin_propina (las propinas NO cuentan como venta);
    propinas_total se informa por separado. Filtro por unidad_negocio_id canónico.
    Fuente: vw_Comercial_KPIs_Diarios_v2_Runtime (EDARSAHUB SQL, NO live, NO Mongo).
    """
    where_clauses = [
        f"fecha_operacion BETWEEN '{fecha_inicio.isoformat()}' AND '{fecha_fin.isoformat()}'"
    ]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{str(u).replace(chr(39), chr(39)+chr(39))}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    # FIX 2026-06-08: Sumar EXACTAMENTE los meses seleccionados (no el rango intermedio)
    if meses:
        meses_str = ','.join(str(int(m)) for m in meses)
        where_clauses.append(f"MONTH(fecha_operacion) IN ({meses_str})")
    
    query = f"""
    SELECT 
        COUNT(*) as total_registros,
        COUNT(DISTINCT unidad_negocio_id) as total_unidades,
        COUNT(DISTINCT fecha_operacion) as total_dias,
        SUM(ISNULL(ventas_sin_propina, 0)) as ventas_total,
        SUM(ISNULL(propinas_total, 0)) as propinas_total,
        SUM(ISNULL(tickets_total, 0)) as tickets_total,
        SUM(ISNULL(pax_total, 0)) as pax_total,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE {' AND '.join(where_clauses)}
    """
    
    result = _execute_readonly_query(query)
    return result[0] if result else {}


def get_kpis_por_unidad(
    fecha_inicio: date,
    fecha_fin: date,
    unidades_permitidas: Optional[List[str]] = None,
    meses: Optional[List[int]] = None
) -> List[Dict]:
    """
    Obtiene KPIs agregados por unidad para el dashboard desde EDARSAHUB SQL.

    MÁXIMA:
    - Se agrupa por unidad_negocio_id canónico (sin LIKE/nombre, sin SQL inválido).
    - KPI ventas = ventas_sin_propina; propinas_total queda separado y FUERA del KPI.
    - Fuente: vw_Comercial_KPIs_Diarios_v2_Runtime (NO live, NO Mongo).
    """
    where_clauses = [
        f"fecha_operacion BETWEEN '{fecha_inicio.isoformat()}' AND '{fecha_fin.isoformat()}'"
    ]

    if unidades_permitidas:
        ids_quoted = ','.join([f"'{str(u).replace(chr(39), chr(39)+chr(39))}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")

    # FIX 2026-06-08: Sumar EXACTAMENTE los meses seleccionados (no el rango intermedio)
    if meses:
        meses_str = ','.join(str(int(m)) for m in meses)
        where_clauses.append(f"MONTH(fecha_operacion) IN ({meses_str})")

    query = f"""
    SELECT 
        unidad_negocio_id as unidad_negocio_pk,
        MAX(unidad_negocio_nombre) as unidad_negocio_nombre,
        MAX(sistema_origen) as sistema_origen,
        COUNT(DISTINCT fecha_operacion) as dias,
        SUM(ISNULL(ventas_sin_propina, 0)) as ventas_total,
        SUM(ISNULL(ventas_sin_propina, 0)) as ventas_sin_propina,
        SUM(ISNULL(propinas_total, 0)) as propinas_total,
        SUM(ISNULL(tickets_total, 0)) as tickets_total,
        SUM(ISNULL(pax_total, 0)) as pax_total,
        CASE WHEN SUM(ISNULL(tickets_total, 0)) > 0
             THEN SUM(ISNULL(ventas_sin_propina, 0)) / SUM(ISNULL(tickets_total, 0))
             ELSE 0 END as ticket_promedio_avg,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE {' AND '.join(where_clauses)}
    GROUP BY unidad_negocio_id
    ORDER BY ventas_total DESC
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
    Obtiene KPIs mensuales desde vw_Comercial_KPIs_Mensuales_v2_Runtime.
    """
    where_clauses = [
        f"anio = {anio}",
        f"mes BETWEEN {mes_inicio} AND {mes_fin}"
    ]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    query = f"""
    SELECT 
        id,
        unidad_negocio_pk,
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
    FROM vw_Comercial_KPIs_Mensuales_v2_Runtime
    WHERE {' AND '.join(where_clauses)}
    ORDER BY anio DESC, mes DESC, unidad_negocio_pk
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
    
    NOTA: Por desfase de zona horaria UTC vs México, los datos pueden estar
    guardados con fecha UTC (día siguiente). Se buscan ambas fechas y se
    prioriza la más reciente.
    """
    from datetime import timedelta
    
    fecha_siguiente = fecha + timedelta(days=1)
    
    where_clauses = [
        f"(fecha_operacion = '{fecha.isoformat()}' OR fecha_operacion = '{fecha_siguiente.isoformat()}')"
    ]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    # Usar ROW_NUMBER para obtener solo el registro más reciente por unidad
    query = f"""
    WITH RankedData AS (
        SELECT 
            id,
            unidad_negocio_id AS unidad_negocio_pk,
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
            fecha_ultima_actualizacion,
            ROW_NUMBER() OVER (PARTITION BY unidad_negocio_id ORDER BY snapshot_timestamp DESC) as rn
        FROM Comercial_Ventas_Dia_Abiertas_v2
        WHERE {' AND '.join(where_clauses)}
    )
    SELECT 
        id,
        unidad_negocio_pk,
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
    FROM RankedData
    WHERE rn = 1
    ORDER BY unidad_negocio_pk
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
        unidad_negocio_pk,
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
        unidad_negocio_pk,
        MAX(created_at) as ultima_sync,
        MAX(fecha_fin) as ultimo_dia_sync
    FROM Comercial_SyncLog_v2
    WHERE {' AND '.join(where_clauses)}
    GROUP BY unidad_negocio_pk
    ORDER BY unidad_negocio_pk
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
    where_clauses = []
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    query = f"""
    SELECT DISTINCT
        unidad_negocio_pk,
        unidad_negocio_nombre,
        sistema_origen,
        server_id,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max,
        COUNT(*) as total_dias,
        SUM(ISNULL(ventas_sin_propina, 0)) as ventas_historicas
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE {' AND '.join(where_clauses)}
    GROUP BY unidad_negocio_pk, unidad_negocio_nombre, sistema_origen, server_id
    ORDER BY unidad_negocio_pk
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
                COUNT(DISTINCT unidad_negocio_pk) as total_unidades,
                MIN(fecha_operacion) as fecha_min,
                MAX(fecha_operacion) as fecha_max
            FROM vw_Comercial_KPIs_Diarios_v2_Runtime
            WHERE 1 = 1
        """)
        
        if stats:
            return {
                "status": "ok",
                "source": "EDARSAHUB_V2",
                "table": "vw_Comercial_KPIs_Diarios_v2_Runtime",
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



# =============================================================================
# FUNCIONES DE LECTURA - COMPARATIVOS DIARIOS
# =============================================================================

def get_comparativos_diarios(
    unidad_negocio_pk: str,
    fecha_actual: date
) -> Dict[str, Any]:
    """
    Obtiene datos comparativos diarios para una unidad:
    - Día actual (de Comercial_Ventas_Dia_Abiertas_v2)
    - Día anterior (de vw_Comercial_KPIs_Diarios_v2_Runtime)
    - Mismo día año anterior (de vw_Comercial_KPIs_Diarios_v2_Runtime)
    
    Si no existe dato, retorna 0 (no error).
    """
    from datetime import timedelta
    
    fecha_anterior = fecha_actual - timedelta(days=1)
    fecha_anio_ant = fecha_actual.replace(year=fecha_actual.year - 1)
    
    # Manejar año bisiesto: si fecha_anio_ant no existe (29 feb), usar 28 feb
    try:
        _ = fecha_anio_ant.isoformat()  # Validar que la fecha es válida
    except ValueError:
        fecha_anio_ant = fecha_actual.replace(year=fecha_actual.year - 1, day=28)
    
    result = {
        'dia_actual': {'ventas': 0, 'pax': 0, 'cheques': 0},
        'dia_anterior': {'ventas': 0, 'pax': 0, 'cheques': 0},
        'dia_anio_ant': {'ventas': 0, 'pax': 0, 'cheques': 0}
    }
    
    # Obtener día actual (de Ventas Abiertas)
    query_actual = f"""
    SELECT 
        ISNULL(total_estimado_dia, 0) as ventas,
        ISNULL(pax_abiertos, 0) + ISNULL(pax_cerrados_dia, 0) as pax,
        ISNULL(tickets_abiertos, 0) + ISNULL(tickets_cerrados_dia, 0) as cheques
    FROM Comercial_Ventas_Dia_Abiertas_v2
    WHERE unidad_negocio_id = '{unidad_negocio_pk}'
      AND fecha_operacion = '{fecha_actual.isoformat()}'
    """
    
    rows_actual = _execute_readonly_query(query_actual)
    if rows_actual:
        result['dia_actual'] = {
            'ventas': float(rows_actual[0].get('ventas', 0) or 0),
            'pax': int(rows_actual[0].get('pax', 0) or 0),
            'cheques': int(rows_actual[0].get('cheques', 0) or 0)
        }
    
    # Obtener día anterior (de KPIs Diarios)
    # CORRECCIÓN: Si no existe el día exacto anterior, buscar el último día disponible
    # con una ventana máxima de 7 días para evitar mostrar datos muy antiguos
    query_anterior = f"""
    SELECT TOP 1
        ISNULL(ventas_sin_propina, 0) as ventas,
        ISNULL(pax_total, 0) as pax_total,
        ISNULL(tickets_total, 0) as cheques,
        anio, mes, dia
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE unidad_negocio_id = '{unidad_negocio_pk}'
      AND (
        -- Primero intentar día exacto anterior
        (anio = {fecha_anterior.year} AND mes = {fecha_anterior.month} AND dia = {fecha_anterior.day})
        OR
        -- Si no existe, buscar cualquier día en los últimos 7 días
        (anio * 10000 + mes * 100 + dia) >= ({fecha_anterior.year} * 10000 + {fecha_anterior.month} * 100 + {fecha_anterior.day} - 7)
        AND (anio * 10000 + mes * 100 + dia) < ({fecha_actual.year} * 10000 + {fecha_actual.month} * 100 + {fecha_actual.day})
      )
    ORDER BY anio DESC, mes DESC, dia DESC
    """
    
    rows_anterior = _execute_readonly_query(query_anterior)
    if rows_anterior:
        result['dia_anterior'] = {
            'ventas': float(rows_anterior[0].get('ventas', 0) or 0),
            'pax': int(rows_anterior[0].get('pax', 0) or 0),
            'cheques': int(rows_anterior[0].get('cheques', 0) or 0)
        }
        # Log si usamos un día diferente al exacto
        dia_usado = f"{rows_anterior[0].get('anio')}-{rows_anterior[0].get('mes'):02d}-{rows_anterior[0].get('dia'):02d}"
        dia_esperado = fecha_anterior.isoformat()
        if dia_usado != dia_esperado:
            logger.info(f"[COMPARATIVOS] {unidad_negocio_pk}: Usando {dia_usado} en lugar de {dia_esperado} (último disponible)")
    
    # Obtener mismo día año anterior (de KPIs Diarios)
    # CORRECCIÓN: Similar lógica de fallback para año anterior
    query_anio_ant = f"""
    SELECT TOP 1
        ISNULL(ventas_sin_propina, 0) as ventas,
        ISNULL(pax_total, 0) as pax_total,
        ISNULL(tickets_total, 0) as cheques,
        anio, mes, dia
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE unidad_negocio_id = '{unidad_negocio_pk}'
      AND (
        -- Primero intentar día exacto año anterior
        (anio = {fecha_anio_ant.year} AND mes = {fecha_anio_ant.month} AND dia = {fecha_anio_ant.day})
        OR
        -- Si no existe, buscar cualquier día en ±7 días del mismo período año anterior
        (anio * 10000 + mes * 100 + dia) >= ({fecha_anio_ant.year} * 10000 + {fecha_anio_ant.month} * 100 + {fecha_anio_ant.day} - 7)
        AND (anio * 10000 + mes * 100 + dia) <= ({fecha_anio_ant.year} * 10000 + {fecha_anio_ant.month} * 100 + {fecha_anio_ant.day} + 7)
      )
    ORDER BY 
        -- Priorizar día exacto, luego el más cercano
        CASE WHEN anio = {fecha_anio_ant.year} AND mes = {fecha_anio_ant.month} AND dia = {fecha_anio_ant.day} THEN 0 ELSE 1 END,
        ABS((anio * 10000 + mes * 100 + dia) - ({fecha_anio_ant.year} * 10000 + {fecha_anio_ant.month} * 100 + {fecha_anio_ant.day}))
    """
    
    rows_anio_ant = _execute_readonly_query(query_anio_ant)
    if rows_anio_ant:
        result['dia_anio_ant'] = {
            'ventas': float(rows_anio_ant[0].get('ventas', 0) or 0),
            'pax': int(rows_anio_ant[0].get('pax', 0) or 0),
            'cheques': int(rows_anio_ant[0].get('cheques', 0) or 0)
        }
    
    return result
