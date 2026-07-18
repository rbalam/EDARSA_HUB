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


def _sql_quote(value) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _unidad_filter_runtime(unidades_permitidas: Optional[List[str]]) -> Optional[str]:
    """
    Filtro canónico de unidad para vw_Comercial_KPIs_Diarios_v2_Runtime.
    RBAC entrega unidad_negocio_pk GUID.
    La vista conserva unidad_negocio_id/código legacy.
    """
    if not unidades_permitidas:
        return None

    ids_quoted = ",".join(_sql_quote(u) for u in unidades_permitidas if u)
    if not ids_quoted:
        return None

    return (
        f"(CONVERT(varchar(36), unidad_negocio_pk) IN ({ids_quoted}) "
        f"OR unidad_negocio_id IN ({ids_quoted}))"
    )


def _resolver_unidades_abiertas(unidades_permitidas: Optional[List[str]]):
    """
    Resuelve unidades para Comercial_Ventas_Dia_Abiertas_v2.

    La tabla abierta solo guarda unidad_negocio_id/codigo operativo.
    RBAC puede entregar GUID. Por eso:
    - codigos: se usan para filtrar a.unidad_negocio_id
    - codigo_to_pk: se usa para devolver unidad_negocio_pk alineado con runtime
    """
    codigos = set()
    codigo_to_pk = {}

    if not unidades_permitidas:
        return codigos, codigo_to_pk

    for valor in unidades_permitidas:
        if valor in (None, ""):
            continue

        raw = str(valor).strip()
        if not raw:
            continue

        raw_codigos = {raw}
        raw_pk = None

        try:
            from uuid import UUID
            UUID(raw)
            raw_pk = raw
        except Exception:
            pass

        try:
            info = CorporateFilterService.resolver_unidad(raw) or {}
            for pk_key in ("pk", "unidad_negocio_pk", "id"):
                v = info.get(pk_key)
                if v not in (None, ""):
                    raw_pk = str(v).strip()
                    break

            for key in ("codigo", "unidad_negocio_id", "unidad_codigo", "unidad_negocio_codigo"):
                v = info.get(key)
                if v not in (None, ""):
                    raw_codigos.add(str(v).strip())
        except Exception as exc:
            logger.debug("[COMERCIAL_V2] resolver_unidad fallo para abiertas %s: %s", raw, exc)

        try:
            pk = UnidadesService.resolver_pk(raw)
            if pk not in (None, ""):
                raw_pk = str(pk).strip()
        except Exception as exc:
            logger.debug("[COMERCIAL_V2] resolver_pk fallo para abiertas %s: %s", raw, exc)

        try:
            codigo = UnidadesService.resolver_codigo(raw)
            if codigo not in (None, ""):
                raw_codigos.add(str(codigo).strip())
        except Exception as exc:
            logger.debug("[COMERCIAL_V2] resolver_codigo fallo para abiertas %s: %s", raw, exc)

        for codigo in raw_codigos:
            if not codigo:
                continue
            codigos.add(codigo)
            if raw_pk:
                codigo_to_pk[codigo] = raw_pk

    return codigos, codigo_to_pk


def _unidad_filter_abiertas(unidades_permitidas: Optional[List[str]]) -> Optional[str]:
    """
    Filtro canonico para Comercial_Ventas_Dia_Abiertas_v2.

    No referencia columnas de Unidades_Negocio. Solo filtra contra
    a.unidad_negocio_id, que si existe en Comercial_Ventas_Dia_Abiertas_v2.
    """
    codigos, _ = _resolver_unidades_abiertas(unidades_permitidas)

    if not codigos:
        return None

    codigos_quoted = ",".join(_sql_quote(v) for v in sorted(codigos) if v)
    if not codigos_quoted:
        return None

    return f"a.unidad_negocio_id IN ({codigos_quoted})"


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
    
    unidad_filter = _unidad_filter_runtime(unidades_permitidas)
    if unidad_filter:
        where_clauses.append(unidad_filter)
    
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
        propinas_total,
        tickets_total,
        pax_total,
        ticket_promedio,
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

    MÁXIMA: KPI visible de ventas = ventas_total con IVA incluido;
    propinas_total se informa por separado. Filtro por unidad_negocio_id canónico.
    Fuente: vw_Comercial_KPIs_Diarios_v2_Runtime (EDARSAHUB SQL, NO live, NO Mongo).
    """
    where_clauses = [
        f"fecha_operacion BETWEEN '{fecha_inicio.isoformat()}' AND '{fecha_fin.isoformat()}'"
    ]
    
    unidad_filter = _unidad_filter_runtime(unidades_permitidas)
    if unidad_filter:
        where_clauses.append(unidad_filter)
    
    # FIX 2026-06-08: Sumar EXACTAMENTE los meses seleccionados (no el rango intermedio)
    if meses:
        meses_str = ','.join(str(int(m)) for m in meses)
        where_clauses.append(f"MONTH(fecha_operacion) IN ({meses_str})")
    
    query = f"""
    SELECT 
        COUNT(*) as total_registros,
        COUNT(DISTINCT unidad_negocio_pk) as total_unidades,
        COUNT(DISTINCT fecha_operacion) as total_dias,
        SUM(ISNULL(ventas_total, 0)) as ventas_total,
        SUM(ISNULL(propinas_total, 0)) as propinas_total,
        SUM(ISNULL(tickets_total, 0)) as tickets_total,
        SUM(ISNULL(pax_total, 0)) as pax_total,
        CASE WHEN SUM(ISNULL(tickets_total, 0)) > 0
             THEN SUM(ISNULL(ventas_total, 0)) / SUM(ISNULL(tickets_total, 0))
             ELSE 0 END as ticket_promedio,
        CASE WHEN SUM(ISNULL(tickets_total, 0)) > 0
             THEN SUM(ISNULL(ventas_total, 0)) / SUM(ISNULL(tickets_total, 0))
             ELSE 0 END as cheque_promedio,
        CASE WHEN SUM(ISNULL(pax_total, 0)) > 0
             THEN SUM(ISNULL(ventas_total, 0)) / SUM(ISNULL(pax_total, 0))
             ELSE 0 END as pax_promedio,
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
    - KPI visible de ventas = ventas_total con IVA incluido.
    - propinas_total permanece separado de ventas_total.
    - Fuente: vw_Comercial_KPIs_Diarios_v2_Runtime (NO live, NO Mongo).
    """
    where_clauses = [
        f"fecha_operacion BETWEEN '{fecha_inicio.isoformat()}' AND '{fecha_fin.isoformat()}'"
    ]

    unidad_filter = _unidad_filter_runtime(unidades_permitidas)
    if unidad_filter:
        where_clauses.append(unidad_filter)

    # FIX 2026-06-08: Sumar EXACTAMENTE los meses seleccionados (no el rango intermedio)
    if meses:
        meses_str = ','.join(str(int(m)) for m in meses)
        where_clauses.append(f"MONTH(fecha_operacion) IN ({meses_str})")

    query = f"""
    SELECT 
        CONVERT(varchar(36), unidad_negocio_pk) as unidad_negocio_pk,
        MAX(unidad_negocio_id) as unidad_negocio_codigo,
        MAX(unidad_negocio_nombre) as unidad_negocio_nombre,
        MAX(sistema_origen) as sistema_origen,
        COUNT(DISTINCT fecha_operacion) as dias,
        SUM(ISNULL(ventas_total, 0)) as ventas_total,
        SUM(ISNULL(propinas_total, 0)) as propinas_total,
        SUM(ISNULL(tickets_total, 0)) as tickets_total,
        SUM(ISNULL(pax_total, 0)) as pax_total,
        CASE WHEN SUM(ISNULL(tickets_total, 0)) > 0
             THEN SUM(ISNULL(ventas_total, 0)) / SUM(ISNULL(tickets_total, 0))
             ELSE 0 END as ticket_promedio,
        CASE WHEN SUM(ISNULL(tickets_total, 0)) > 0
             THEN SUM(ISNULL(ventas_total, 0)) / SUM(ISNULL(tickets_total, 0))
             ELSE 0 END as cheque_promedio,
        CASE WHEN SUM(ISNULL(pax_total, 0)) > 0
             THEN SUM(ISNULL(ventas_total, 0)) / SUM(ISNULL(pax_total, 0))
             ELSE 0 END as pax_promedio,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE {' AND '.join(where_clauses)}
    GROUP BY unidad_negocio_pk
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
    Obtiene ventas abiertas del dia operativo desde Comercial_Ventas_Dia_Abiertas_v2.

    Reglas:
    - La tabla abierta guarda unidad_negocio_id/codigo operativo.
    - RBAC puede entregar GUID.
    - El filtro SQL se hace por codigo operativo.
    - La respuesta intenta devolver unidad_negocio_pk canonico para poder unir
      correctamente abiertas + cerradas en routes.py.
    - No se consulta fecha siguiente; FechaOperacion ya viene resuelta por caller.
    """
    where_clauses = [
        f"a.fecha_operacion = '{fecha.isoformat()}'"
    ]

    codigos_filter, codigo_to_pk = _resolver_unidades_abiertas(unidades_permitidas)

    unidad_filter = _unidad_filter_abiertas(unidades_permitidas)
    if unidad_filter:
        where_clauses.append(unidad_filter)

    query = f"""
    WITH RankedData AS (
        SELECT
            a.id,
            a.unidad_negocio_id AS unidad_negocio_pk,
            a.unidad_negocio_id AS unidad_negocio_codigo,
            a.unidad_negocio_nombre,
            a.server_id,
            a.sucursal_id,
            a.sucursal_nombre,
            a.sistema_origen,
            a.snapshot_timestamp,
            a.fecha_operacion,
            a.ventas_abiertas,
            a.tickets_abiertos,
            a.pax_abiertos,
            a.ventas_cerradas_dia,
            a.tickets_cerrados_dia,
            a.pax_cerrados_dia,
            a.total_estimado_dia,
            a.fuente_original,
            a.sync_run_id,
            a.fecha_ultima_actualizacion,
            ROW_NUMBER() OVER (
                PARTITION BY a.unidad_negocio_id
                ORDER BY a.snapshot_timestamp DESC
            ) AS rn
        FROM dbo.Comercial_Ventas_Dia_Abiertas_v2 a
        WHERE {' AND '.join(where_clauses)}
    )
    SELECT
        id,
        unidad_negocio_pk,
        unidad_negocio_codigo,
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

    rows = _execute_readonly_query(query)

    for row in rows:
        codigo = str(
            row.get("unidad_negocio_codigo")
            or row.get("unidad_negocio_pk")
            or ""
        ).strip()

        resolved_pk = codigo_to_pk.get(codigo)

        if not resolved_pk:
            try:
                pk = UnidadesService.resolver_pk(codigo)
                if pk not in (None, ""):
                    resolved_pk = str(pk).strip()
            except Exception as exc:
                logger.debug("[COMERCIAL_V2] resolver_pk post-query fallo para %s: %s", codigo, exc)

        if not resolved_pk:
            try:
                info = CorporateFilterService.resolver_unidad(codigo) or {}
                pk = info.get("pk") or info.get("unidad_negocio_pk") or info.get("id")
                if pk not in (None, ""):
                    resolved_pk = str(pk).strip()
            except Exception as exc:
                logger.debug("[COMERCIAL_V2] resolver_unidad post-query fallo para %s: %s", codigo, exc)

        if resolved_pk:
            row["unidad_negocio_pk"] = resolved_pk

    return rows


def get_ultimas_fechas_operacion_abiertas(
    unidades_permitidas: Optional[List[str]] = None
) -> Dict[str, date]:
    """
    Obtiene la última fecha_operacion almacenada por unidad desde
    Comercial_Ventas_Dia_Abiertas_v2.

    Uso:
    - Fallback controlado cuando falla el motor de ventana operativa.
    - Nunca usa fecha civil.
    - Respeta el contexto de unidades recibido por RBAC.
    """
    unidad_filter = _unidad_filter_abiertas(unidades_permitidas)

    if not unidad_filter:
        return {}

    query = f"""
    SELECT
        a.unidad_negocio_id,
        MAX(a.fecha_operacion) AS ultima_fecha_operacion
    FROM dbo.Comercial_Ventas_Dia_Abiertas_v2 a
    WHERE {unidad_filter}
      AND a.fecha_operacion IS NOT NULL
    GROUP BY a.unidad_negocio_id
    """

    rows = _execute_readonly_query(query)
    fechas: Dict[str, date] = {}

    for row in rows:
        codigo = str(
            row.get("unidad_negocio_id") or ""
        ).strip().upper()

        raw_fecha = row.get("ultima_fecha_operacion")

        if not codigo or raw_fecha in (None, ""):
            continue

        try:
            if type(raw_fecha) is date:
                fecha_normalizada = raw_fecha
            elif isinstance(raw_fecha, date):
                fecha_normalizada = raw_fecha.date()
            else:
                fecha_normalizada = date.fromisoformat(
                    str(raw_fecha).strip()[:10]
                )
        except Exception as exc:
            logger.warning(
                "[COMERCIAL_V2] fecha_operacion SQL inválida "
                "para unidad=%s valor=%r error=%s",
                codigo,
                raw_fecha,
                exc,
            )
            continue

        fechas[codigo] = fecha_normalizada

    return fechas


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
    if unidades_permitidas == []:
        return []

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
    if unidades_permitidas == []:
        return []

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
    if unidades_permitidas == []:
        return []

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
        SUM(ISNULL(ventas_total, 0)) as ventas_historicas
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
    unidad_negocio_codigo: str,
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

    # Manejar 29 de febrero antes de construir la fecha del año anterior.
    try:
        fecha_anio_ant = fecha_actual.replace(year=fecha_actual.year - 1)
    except ValueError:
        fecha_anio_ant = fecha_actual.replace(
            year=fecha_actual.year - 1,
            day=28
        )

    fecha_anterior_inicio = fecha_actual - timedelta(days=7)
    fecha_anio_ant_inicio = fecha_anio_ant - timedelta(days=7)
    fecha_anio_ant_fin = fecha_anio_ant + timedelta(days=7)
    
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
    WHERE unidad_negocio_id = '{unidad_negocio_codigo}'
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
        ISNULL(ventas_total, 0) as ventas,
        ISNULL(pax_total, 0) as pax_total,
        ISNULL(tickets_total, 0) as cheques,
        anio, mes, dia
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE unidad_negocio_id = '{unidad_negocio_codigo}'
      AND fecha_operacion BETWEEN
          '{fecha_anterior_inicio.isoformat()}'
          AND '{fecha_anterior.isoformat()}'
    ORDER BY
        CASE
            WHEN fecha_operacion = '{fecha_anterior.isoformat()}'
                THEN 0
            ELSE 1
        END,
        fecha_operacion DESC
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
            logger.info(f"[COMPARATIVOS] {unidad_negocio_codigo}: Usando {dia_usado} en lugar de {dia_esperado} (último disponible)")
    
    # Obtener mismo día año anterior (de KPIs Diarios)
    # CORRECCIÓN: Similar lógica de fallback para año anterior
    query_anio_ant = f"""
    SELECT TOP 1
        ISNULL(ventas_total, 0) as ventas,
        ISNULL(pax_total, 0) as pax_total,
        ISNULL(tickets_total, 0) as cheques,
        anio, mes, dia
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE unidad_negocio_id = '{unidad_negocio_codigo}'
      AND fecha_operacion BETWEEN
          '{fecha_anio_ant_inicio.isoformat()}'
          AND '{fecha_anio_ant_fin.isoformat()}'
    ORDER BY
        CASE
            WHEN fecha_operacion = '{fecha_anio_ant.isoformat()}'
                THEN 0
            ELSE 1
        END,
        ABS(DATEDIFF(
            day,
            fecha_operacion,
            '{fecha_anio_ant.isoformat()}'
        )),
        fecha_operacion DESC
    """
    
    rows_anio_ant = _execute_readonly_query(query_anio_ant)
    if rows_anio_ant:
        result['dia_anio_ant'] = {
            'ventas': float(rows_anio_ant[0].get('ventas', 0) or 0),
            'pax': int(rows_anio_ant[0].get('pax', 0) or 0),
            'cheques': int(rows_anio_ant[0].get('cheques', 0) or 0)
        }
    
    return result
