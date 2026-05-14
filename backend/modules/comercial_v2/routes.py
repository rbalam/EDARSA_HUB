"""
ROUTES V2 - COMERCIAL V2
=========================

Endpoints v2 aislados para Comercial.
Leen EXCLUSIVAMENTE desde EDARSAHUB v2.

NO consultan:
- SQL vivo a SoftRestaurant/MPRO
- MongoDB cache
- Datos demo

FEATURE FLAG:
- COMERCIAL_V2_ENABLED=false (default OFF)
- Endpoints existen pero no reemplazan v1

RBAC:
- Respeta unidades permitidas por usuario
- No hardcodea unidades
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
import logging

# SUBFASE 5 FIX: Usar get_current_user_dual para soportar cookie httpOnly
from core.security import get_current_user_dual_dependency
from core.context_resolver import get_user_unidades_negocio

from .feature_flag import is_comercial_v2_enabled, get_v2_status
from .repository_readonly import (
    check_v2_health,
    get_kpis_diarios,
    get_kpis_diarios_agregados,
    get_kpis_por_unidad,
    get_kpis_mensuales,
    get_ventas_dia_abiertas,
    get_sync_status,
    get_last_sync_by_unidad,
    get_unidades_disponibles,
    _execute_readonly_query
)
from .schemas_api import (
    HealthResponse,
    DashboardResponse,
    KPIsDiariosResponse,
    KPIsMensualesResponse,
    VentasDiaResponse,
    UnidadesResponse,
    SyncStatusResponse,
    MetadataV2
)

logger = logging.getLogger(__name__)

# Router v2 aislado
router = APIRouter(prefix="/comercial", tags=["Comercial V2"])


# =============================================================================
# MAPEO DE CÓDIGOS: FASE T1 COMPLETADA - CÓDIGOS CANÓNICOS UNIFICADOS
# =============================================================================
# POST FASE T1 (2026-05-13): Las tablas KPI ahora usan códigos canónicos oficiales.
# Este mapeo se mantiene solo como compatibilidad defensiva (identidad).
# Los códigos legacy (130-MER, 130-QRO, LA-ESTELAR) ya no existen en las tablas.

MAPEO_KPI_A_CODIGO_CANONICO = {
    # Códigos canónicos oficiales (identidad)
    '130MID': '130MID',
    '130QRO': '130QRO',
    'CIENFUEGOS': 'CIENFUEGOS',
    'ESTELAR': 'ESTELAR',
    'ORIGEN': 'ORIGEN',
    # Legacy (compatibilidad defensiva - no deberían existir en BD)
    '130-MER': '130MID',
    '130-QRO': '130QRO',
    'LA-ESTELAR': 'ESTELAR',
}

MAPEO_CODIGO_CANONICO_A_KPI = {v: k for k, v in MAPEO_KPI_A_CODIGO_CANONICO.items() if '-' not in k}


# =============================================================================
# HELPERS: CÁLCULO DE VARIACIONES (FASE 2)
# =============================================================================

def _calcular_dias_periodo(fecha_inicio: date, fecha_fin: date, fecha_max_datos: date) -> int:
    """
    Calcula días efectivos del período basado en último día con datos.
    
    REGLA: Si el mes está parcial, usar hasta el último día con ventas.
    """
    fecha_efectiva = min(fecha_fin, fecha_max_datos)
    dias = (fecha_efectiva - fecha_inicio).days + 1
    return max(0, dias)


def _get_variaciones_comparativas(
    unidad_negocio_id: str,
    fecha_inicio: date,
    fecha_fin: date,
    fecha_max_datos: date
) -> dict:
    """
    FASE 2: Calcula variaciones vs mes anterior y año anterior.
    
    FUENTE: EDARSAHUB.Comercial_KPIs_Diarios_v2
    
    REGLAS:
    - Usa rangos semiabiertos: fecha >= inicio AND fecha < fin_exclusiva
    - Si mes actual parcial: compara mismos días del mes anterior
    - Si no hay datos comparativos: devuelve null (NO 0 falso)
    - Si variación real es 0.0%: devuelve 0.0
    
    Args:
        unidad_negocio_id: ID en tabla KPI (ej: '130-MER', 'LA-ESTELAR')
        fecha_inicio: Inicio del período actual
        fecha_fin: Fin del período actual
        fecha_max_datos: Último día con datos en el período actual
    
    Returns:
        dict con variaciones o null si no hay base comparativa
    """
    try:
        # Calcular días efectivos del período actual
        dias_efectivos = _calcular_dias_periodo(fecha_inicio, fecha_fin, fecha_max_datos)
        
        if dias_efectivos <= 0:
            return {
                'ventas_ant': None,
                'ventas_año': None,
                'pax_ant': None,
                'pax_año': None,
                'cheques_ant': None,
                'cheques_año': None,
                'var_vs_mes_ant': None,
                'var_vs_año_ant': None,
                'var_pax_mes': None,
                'var_pax_año': None,
                'var_cheques_mes': None,
                'var_cheques_año': None,
                '_meta_variaciones': {'error': 'Sin días efectivos'}
            }
        
        # =====================================================================
        # CALCULAR RANGOS DE COMPARACIÓN
        # =====================================================================
        
        # Período actual efectivo (hasta último día con datos)
        fecha_fin_efectiva = min(fecha_fin, fecha_max_datos)
        
        # Mes anterior: mismo rango de días
        from dateutil.relativedelta import relativedelta
        fecha_inicio_mes_ant = fecha_inicio - relativedelta(months=1)
        fecha_fin_mes_ant = fecha_fin_efectiva - relativedelta(months=1)
        
        # Año anterior: mismo rango de días
        fecha_inicio_año_ant = fecha_inicio - relativedelta(years=1)
        fecha_fin_año_ant = fecha_fin_efectiva - relativedelta(years=1)
        
        # =====================================================================
        # CONSULTAR DATOS DE PERÍODO ACTUAL (ya tenemos, pero necesitamos PAX)
        # =====================================================================
        
        query_actual = f"""
        SELECT 
            SUM(ventas_total) as ventas,
            SUM(pax_total) as pax,
            SUM(tickets_total) as cheques
        FROM Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id = '{unidad_negocio_id}'
          AND fecha_operacion >= '{fecha_inicio.isoformat()}'
          AND fecha_operacion < '{(fecha_fin_efectiva + timedelta(days=1)).isoformat()}'
          AND activo = 1
          AND es_demo = 0
        """
        
        result_actual = _execute_readonly_query(query_actual)
        ventas_actual = float(result_actual[0].get('ventas') or 0) if result_actual else 0
        pax_actual = int(result_actual[0].get('pax') or 0) if result_actual else 0
        cheques_actual = int(result_actual[0].get('cheques') or 0) if result_actual else 0
        
        # =====================================================================
        # CONSULTAR DATOS DE MES ANTERIOR
        # =====================================================================
        
        query_mes_ant = f"""
        SELECT 
            SUM(ventas_total) as ventas,
            SUM(pax_total) as pax,
            SUM(tickets_total) as cheques,
            COUNT(*) as dias
        FROM Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id = '{unidad_negocio_id}'
          AND fecha_operacion >= '{fecha_inicio_mes_ant.isoformat()}'
          AND fecha_operacion < '{(fecha_fin_mes_ant + timedelta(days=1)).isoformat()}'
          AND activo = 1
          AND es_demo = 0
        """
        
        result_mes_ant = _execute_readonly_query(query_mes_ant)
        
        # Verificar si hay datos del mes anterior
        tiene_datos_mes_ant = result_mes_ant and result_mes_ant[0].get('dias', 0) > 0
        ventas_ant = float(result_mes_ant[0].get('ventas') or 0) if tiene_datos_mes_ant else None
        pax_ant = int(result_mes_ant[0].get('pax') or 0) if tiene_datos_mes_ant else None
        cheques_ant = int(result_mes_ant[0].get('cheques') or 0) if tiene_datos_mes_ant else None
        
        # =====================================================================
        # CONSULTAR DATOS DE AÑO ANTERIOR
        # =====================================================================
        
        query_año_ant = f"""
        SELECT 
            SUM(ventas_total) as ventas,
            SUM(pax_total) as pax,
            SUM(tickets_total) as cheques,
            COUNT(*) as dias
        FROM Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id = '{unidad_negocio_id}'
          AND fecha_operacion >= '{fecha_inicio_año_ant.isoformat()}'
          AND fecha_operacion < '{(fecha_fin_año_ant + timedelta(days=1)).isoformat()}'
          AND activo = 1
          AND es_demo = 0
        """
        
        result_año_ant = _execute_readonly_query(query_año_ant)
        
        # Verificar si hay datos del año anterior
        tiene_datos_año_ant = result_año_ant and result_año_ant[0].get('dias', 0) > 0
        ventas_año = float(result_año_ant[0].get('ventas') or 0) if tiene_datos_año_ant else None
        pax_año = int(result_año_ant[0].get('pax') or 0) if tiene_datos_año_ant else None
        cheques_año = int(result_año_ant[0].get('cheques') or 0) if tiene_datos_año_ant else None
        
        # =====================================================================
        # CALCULAR VARIACIONES
        # REGLA: Si no hay base, devolver null. Si variación real es 0, devolver 0.0
        # =====================================================================
        
        # Variación vs mes anterior
        if ventas_ant is not None and ventas_ant > 0:
            var_vs_mes_ant = round(((ventas_actual - ventas_ant) / ventas_ant) * 100, 1)
        elif ventas_ant is not None and ventas_ant == 0:
            var_vs_mes_ant = 0.0 if ventas_actual == 0 else None  # División por cero
        else:
            var_vs_mes_ant = None  # Sin base comparativa
        
        # Variación vs año anterior
        if ventas_año is not None and ventas_año > 0:
            var_vs_año_ant = round(((ventas_actual - ventas_año) / ventas_año) * 100, 1)
        elif ventas_año is not None and ventas_año == 0:
            var_vs_año_ant = 0.0 if ventas_actual == 0 else None
        else:
            var_vs_año_ant = None  # Sin base comparativa
        
        # Variaciones de PAX
        if pax_ant is not None and pax_ant > 0:
            var_pax_mes = round(((pax_actual - pax_ant) / pax_ant) * 100, 1)
        elif pax_ant is not None and pax_ant == 0:
            var_pax_mes = 0.0 if pax_actual == 0 else None
        else:
            var_pax_mes = None
        
        if pax_año is not None and pax_año > 0:
            var_pax_año = round(((pax_actual - pax_año) / pax_año) * 100, 1)
        elif pax_año is not None and pax_año == 0:
            var_pax_año = 0.0 if pax_actual == 0 else None
        else:
            var_pax_año = None
        
        # Variaciones de cheques
        if cheques_ant is not None and cheques_ant > 0:
            var_cheques_mes = round(((cheques_actual - cheques_ant) / cheques_ant) * 100, 1)
        elif cheques_ant is not None and cheques_ant == 0:
            var_cheques_mes = 0.0 if cheques_actual == 0 else None
        else:
            var_cheques_mes = None
        
        if cheques_año is not None and cheques_año > 0:
            var_cheques_año = round(((cheques_actual - cheques_año) / cheques_año) * 100, 1)
        elif cheques_año is not None and cheques_año == 0:
            var_cheques_año = 0.0 if cheques_actual == 0 else None
        else:
            var_cheques_año = None
        
        return {
            'ventas_ant': ventas_ant,
            'ventas_año': ventas_año,
            'pax_ant': pax_ant,
            'pax_año': pax_año,
            'cheques_ant': cheques_ant,
            'cheques_año': cheques_año,
            'var_vs_mes_ant': var_vs_mes_ant,
            'var_vs_año_ant': var_vs_año_ant,
            'var_pax_mes': var_pax_mes,
            'var_pax_año': var_pax_año,
            'var_cheques_mes': var_cheques_mes,
            'var_cheques_año': var_cheques_año,
            '_meta_variaciones': {
                'fecha_inicio_actual': fecha_inicio.isoformat(),
                'fecha_fin_efectiva': fecha_fin_efectiva.isoformat(),
                'dias_efectivos': dias_efectivos,
                'rango_mes_ant': f"{fecha_inicio_mes_ant.isoformat()} a {fecha_fin_mes_ant.isoformat()}",
                'rango_año_ant': f"{fecha_inicio_año_ant.isoformat()} a {fecha_fin_año_ant.isoformat()}",
                'tiene_datos_mes_ant': tiene_datos_mes_ant,
                'tiene_datos_año_ant': tiene_datos_año_ant
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculando variaciones para {unidad_negocio_id}: {e}")
        return {
            'ventas_ant': None,
            'ventas_año': None,
            'pax_ant': None,
            'pax_año': None,
            'cheques_ant': None,
            'cheques_año': None,
            'var_vs_mes_ant': None,
            'var_vs_año_ant': None,
            'var_pax_mes': None,
            'var_pax_año': None,
            'var_cheques_mes': None,
            'var_cheques_año': None,
            '_meta_variaciones': {'error': str(e)}
        }


def _calcular_totales_variaciones(
    totales_actual: dict,
    fecha_inicio: date,
    fecha_fin: date,
    fecha_max_datos: date,
    unidades_permitidas: List[str]
) -> dict:
    """
    FASE 2: Calcula variaciones agregadas para totales del dashboard.
    
    Args:
        totales_actual: Totales del período actual
        fecha_inicio: Inicio del período
        fecha_fin: Fin del período
        fecha_max_datos: Último día con datos
        unidades_permitidas: Lista de unidades a incluir
    
    Returns:
        dict con totales enriquecidos con variaciones
    """
    try:
        from dateutil.relativedelta import relativedelta
        
        # Período efectivo
        fecha_fin_efectiva = min(fecha_fin, fecha_max_datos) if fecha_max_datos else fecha_fin
        
        # Rangos de comparación
        fecha_inicio_mes_ant = fecha_inicio - relativedelta(months=1)
        fecha_fin_mes_ant = fecha_fin_efectiva - relativedelta(months=1)
        fecha_inicio_año_ant = fecha_inicio - relativedelta(years=1)
        fecha_fin_año_ant = fecha_fin_efectiva - relativedelta(years=1)
        
        # IDs en formato de tabla KPI
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        
        # Query mes anterior
        query_mes_ant = f"""
        SELECT 
            SUM(ventas_total) as ventas,
            SUM(pax_total) as pax,
            SUM(tickets_total) as cheques,
            COUNT(DISTINCT fecha_operacion) as dias
        FROM Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id IN ({ids_quoted})
          AND fecha_operacion >= '{fecha_inicio_mes_ant.isoformat()}'
          AND fecha_operacion < '{(fecha_fin_mes_ant + timedelta(days=1)).isoformat()}'
          AND activo = 1
          AND es_demo = 0
        """
        
        result_mes_ant = _execute_readonly_query(query_mes_ant)
        tiene_datos_mes_ant = result_mes_ant and result_mes_ant[0].get('dias', 0) > 0
        
        ventas_ant = float(result_mes_ant[0].get('ventas') or 0) if tiene_datos_mes_ant else None
        pax_ant = int(result_mes_ant[0].get('pax') or 0) if tiene_datos_mes_ant else None
        cheques_ant = int(result_mes_ant[0].get('cheques') or 0) if tiene_datos_mes_ant else None
        
        # Query año anterior
        query_año_ant = f"""
        SELECT 
            SUM(ventas_total) as ventas,
            SUM(pax_total) as pax,
            SUM(tickets_total) as cheques,
            COUNT(DISTINCT fecha_operacion) as dias
        FROM Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id IN ({ids_quoted})
          AND fecha_operacion >= '{fecha_inicio_año_ant.isoformat()}'
          AND fecha_operacion < '{(fecha_fin_año_ant + timedelta(days=1)).isoformat()}'
          AND activo = 1
          AND es_demo = 0
        """
        
        result_año_ant = _execute_readonly_query(query_año_ant)
        tiene_datos_año_ant = result_año_ant and result_año_ant[0].get('dias', 0) > 0
        
        ventas_año = float(result_año_ant[0].get('ventas') or 0) if tiene_datos_año_ant else None
        pax_año = int(result_año_ant[0].get('pax') or 0) if tiene_datos_año_ant else None
        cheques_año = int(result_año_ant[0].get('cheques') or 0) if tiene_datos_año_ant else None
        
        # Calcular variaciones
        ventas_actual = float(totales_actual.get('ventas_total') or 0)
        pax_actual = int(totales_actual.get('pax_total') or 0)
        cheques_actual = int(totales_actual.get('tickets_total') or 0)
        
        # Variaciones de ventas
        if ventas_ant is not None and ventas_ant > 0:
            var_vs_mes_ant = round(((ventas_actual - ventas_ant) / ventas_ant) * 100, 1)
        else:
            var_vs_mes_ant = None if ventas_ant is None else 0.0
        
        if ventas_año is not None and ventas_año > 0:
            var_vs_año_ant = round(((ventas_actual - ventas_año) / ventas_año) * 100, 1)
        else:
            var_vs_año_ant = None if ventas_año is None else 0.0
        
        # Variaciones de PAX
        if pax_ant is not None and pax_ant > 0:
            var_pax_mes = round(((pax_actual - pax_ant) / pax_ant) * 100, 1)
        else:
            var_pax_mes = None if pax_ant is None else 0.0
        
        if pax_año is not None and pax_año > 0:
            var_pax_año = round(((pax_actual - pax_año) / pax_año) * 100, 1)
        else:
            var_pax_año = None if pax_año is None else 0.0
        
        # Variaciones de cheques
        if cheques_ant is not None and cheques_ant > 0:
            var_cheques_mes = round(((cheques_actual - cheques_ant) / cheques_ant) * 100, 1)
        else:
            var_cheques_mes = None if cheques_ant is None else 0.0
        
        if cheques_año is not None and cheques_año > 0:
            var_cheques_año = round(((cheques_actual - cheques_año) / cheques_año) * 100, 1)
        else:
            var_cheques_año = None if cheques_año is None else 0.0
        
        return {
            **totales_actual,
            'ventas_ant': ventas_ant,
            'ventas_año': ventas_año,
            'pax_ant': pax_ant,
            'pax_año': pax_año,
            'cheques_ant': cheques_ant,
            'cheques_año': cheques_año,
            'var_vs_mes_ant': var_vs_mes_ant,
            'var_vs_año_ant': var_vs_año_ant,
            'var_pax_mes': var_pax_mes,
            'var_pax_año': var_pax_año,
            'var_cheques_mes': var_cheques_mes,
            'var_cheques_año': var_cheques_año
        }
        
    except Exception as e:
        logger.error(f"Error calculando totales variaciones: {e}")
        return totales_actual


# =============================================================================
# HELPERS
# =============================================================================

async def get_unidades_permitidas_v2(current_user: dict) -> List[str]:
    """
    Obtiene las unidades de negocio permitidas por RBAC.
    
    POST FASE T1 (2026-05-13): Ahora usa códigos canónicos oficiales de EDARSAHUB.
    FUENTE: Unidades_Negocio.codigo
    CÓDIGOS: 130MID, 130QRO, CIENFUEGOS, ESTELAR, ORIGEN
    
    MÁXIMA: EDARSAHUB es el cerebro del sistema.
    """
    # Códigos canónicos oficiales (desde EDARSAHUB)
    CODIGOS_CANONICOS_OFICIALES = ['CIENFUEGOS', 'ESTELAR', '130MID', '130QRO', 'ORIGEN']
    
    try:
        # Si es SuperAdmin o Director, dar acceso a todas las unidades
        if current_user.get('role') in ['SuperAdministrador', 'Director']:
            return CODIGOS_CANONICOS_OFICIALES
        
        # Obtener unidades asignadas al usuario desde el contexto
        unidades_mongo = await get_user_unidades_negocio(current_user)
        
        # Mapear a códigos canónicos oficiales
        unidades_v2 = []
        
        for u in unidades_mongo:
            codigo = u.get('codigo', '').upper()
            nombre = u.get('nombre', '').upper()
            
            # Mapeo por código directo (preferido)
            if codigo in CODIGOS_CANONICOS_OFICIALES:
                unidades_v2.append(codigo)
            # Mapeo por nombre (fallback)
            elif 'CIENFUEGOS' in nombre and 'TABLAJERIA' not in nombre:
                unidades_v2.append('CIENFUEGOS')
            elif 'ESTELAR' in nombre:
                unidades_v2.append('ESTELAR')
            elif 'MERIDA' in nombre or '130MID' in codigo or 'MID' in codigo:
                unidades_v2.append('130MID')
            elif 'QUERETARO' in nombre or '130QRO' in codigo or 'QRO' in codigo:
                unidades_v2.append('130QRO')
            elif 'ORIGEN' in nombre:
                unidades_v2.append('ORIGEN')
        
        return list(set(unidades_v2)) if unidades_v2 else []
        
    except Exception as e:
        logger.warning(f"Error obteniendo unidades permitidas: {e}")
        return []


def serialize_response(data: any) -> any:
    """Serializa datos para respuesta JSON."""
    if isinstance(data, dict):
        return {k: serialize_response(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_response(item) for item in data]
    elif isinstance(data, (date, datetime)):
        return data.isoformat()
    elif hasattr(data, '__float__'):
        return float(data)
    else:
        return data


# =============================================================================
# ENDPOINT: HEALTH
# =============================================================================

@router.get("/health", response_model=HealthResponse)
async def comercial_v2_health():
    """
    Estado de salud de Comercial v2.
    
    Verifica:
    - Conexión a EDARSAHUB
    - Datos disponibles en tablas v2
    - Feature flag status
    """
    try:
        health = check_v2_health()
        health['feature_flag'] = get_v2_status()
        return health
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "error", "message": str(e)}


# =============================================================================
# ENDPOINT: DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=DashboardResponse)
async def comercial_v2_dashboard(
    fecha_inicio: date = Query(..., description="Fecha inicio del período"),
    fecha_fin: date = Query(..., description="Fecha fin del período"),
    unidad_negocio_id: Optional[str] = Query(None, description="Filtrar por unidad"),
    current_user: dict = Depends(get_current_user_dual_dependency())
):
    """
    Dashboard de KPIs comerciales v2.
    
    Lee desde: 
    - Comercial_KPIs_Diarios_v2 (ventas cerradas)
    - Comercial_Ventas_Dia_Abiertas_v2 (ventas del día en curso)
    
    Fuente: EDARSAHUB (NO SQL vivo, NO MongoDB)
    
    REGLA DE NEGOCIO:
    - Si fecha_fin >= hoy: incluye ventas abiertas del día actual
    - Las ventas abiertas se suman a los totales pero se identifican como estimadas
    - No hay duplicación: ventas_cerradas_dia + ventas_abiertas = total_estimado_dia
    """
    try:
        # Obtener unidades permitidas
        unidades_permitidas = await get_unidades_permitidas_v2(current_user)
        
        if not unidades_permitidas:
            raise HTTPException(
                status_code=403, 
                detail="No tiene unidades de negocio asignadas"
            )
        
        # Filtrar por unidad específica si se solicita
        if unidad_negocio_id:
            if unidad_negocio_id not in unidades_permitidas:
                raise HTTPException(
                    status_code=403,
                    detail=f"No tiene acceso a la unidad {unidad_negocio_id}"
                )
            unidades_permitidas = [unidad_negocio_id]
        
        # Obtener datos agregados de ventas cerradas
        totales = get_kpis_diarios_agregados(fecha_inicio, fecha_fin, unidades_permitidas)
        
        # Obtener datos por unidad (cerradas)
        por_unidad_cerradas = get_kpis_por_unidad(fecha_inicio, fecha_fin, unidades_permitidas)
        
        # =====================================================================
        # COMBINAR CON VENTAS ABIERTAS DEL DÍA ACTUAL
        # =====================================================================
        
        fecha_hoy = date.today()
        incluye_hoy = fecha_fin >= fecha_hoy
        ventas_abiertas_hoy = []
        
        if incluye_hoy:
            # Obtener ventas abiertas del día (actualizadas cada 5 min)
            ventas_abiertas_hoy = get_ventas_dia_abiertas(fecha_hoy, unidades_permitidas)
        
        # =====================================================================
        # UNIÓN DE UNIDADES: CERRADAS + ABIERTAS
        # Regla: Incluir unidad si tiene cerradas O abiertas O SyncLog exitoso
        # =====================================================================
        
        # Indexar unidades cerradas por ID
        cerradas_por_unidad = {
            u['unidad_negocio_id']: u for u in por_unidad_cerradas
        }
        
        # Indexar unidades abiertas por ID
        abiertas_por_unidad = {
            v['unidad_negocio_id']: v for v in ventas_abiertas_hoy
        } if ventas_abiertas_hoy else {}
        
        # Unión de todas las unidades (cerradas + abiertas)
        todas_unidades_ids = set(cerradas_por_unidad.keys()) | set(abiertas_por_unidad.keys())
        
        # Si no hay ninguna unidad con datos, incluir todas las permitidas (mostrar como "sin operación")
        if not todas_unidades_ids and unidades_permitidas:
            todas_unidades_ids = set(unidades_permitidas)
        
        # Construir lista combinada de unidades
        por_unidad = []
        for uid in sorted(todas_unidades_ids):
            tiene_cerradas = uid in cerradas_por_unidad
            tiene_abiertas = uid in abiertas_por_unidad
            
            if tiene_cerradas:
                # Usar datos de cerradas como base
                u = cerradas_por_unidad[uid].copy()
            elif tiene_abiertas:
                # Crear registro base desde abiertas
                ab = abiertas_por_unidad[uid]
                u = {
                    'unidad_negocio_id': uid,
                    'unidad_negocio_nombre': ab.get('unidad_negocio_nombre', uid),
                    'sistema_origen': ab.get('sistema_origen', 'DESCONOCIDO'),
                    'ventas_total': 0,
                    'ventas_sin_propina': 0,
                    'propinas_total': 0,
                    'tickets_total': 0,
                    'pax_total': 0,
                    'ticket_promedio_avg': 0,
                    'dias': 0,
                    'fecha_min': None,
                    'fecha_max': None
                }
            else:
                # Unidad sin datos (mostrar como "sin operación")
                u = {
                    'unidad_negocio_id': uid,
                    'unidad_negocio_nombre': uid,
                    'sistema_origen': 'DESCONOCIDO',
                    'ventas_total': 0,
                    'ventas_sin_propina': 0,
                    'propinas_total': 0,
                    'tickets_total': 0,
                    'pax_total': 0,
                    'ticket_promedio_avg': 0,
                    'dias': 0,
                    'fecha_min': None,
                    'fecha_max': None
                }
            
            # Enriquecer con datos de abiertas si existen
            if tiene_abiertas:
                ab = abiertas_por_unidad[uid]
                u['_ventas_abiertas_hoy'] = float(ab.get('ventas_abiertas') or 0)
                u['_ventas_cerradas_hoy'] = float(ab.get('ventas_cerradas_dia') or 0)
                u['_total_estimado_hoy'] = float(ab.get('total_estimado_dia') or 0)
                u['_tickets_abiertos_hoy'] = int(ab.get('tickets_abiertos') or 0)
                u['_pax_abiertos_hoy'] = int(ab.get('pax_abiertos') or 0)
                u['_snapshot_timestamp'] = str(ab.get('snapshot_timestamp') or '')
                u['_incluye_ventas_abiertas'] = True
                
                # Si NO tiene cerradas, sumar abiertas al total de la unidad
                if not tiene_cerradas:
                    total_dia = float(ab.get('total_estimado_dia') or 0)
                    tickets = int(ab.get('tickets_abiertos') or 0) + int(ab.get('tickets_cerrados_dia') or 0)
                    pax = int(ab.get('pax_abiertos') or 0) + int(ab.get('pax_cerrados_dia') or 0)
                    
                    u['ventas_total'] = total_dia
                    u['tickets_total'] = tickets
                    u['pax_total'] = pax
                    u['dias'] = 1 if total_dia > 0 else 0
                    u['fecha_min'] = fecha_hoy.isoformat()
                    u['fecha_max'] = fecha_hoy.isoformat()
            else:
                u['_ventas_abiertas_hoy'] = 0
                u['_ventas_cerradas_hoy'] = 0
                u['_total_estimado_hoy'] = 0
                u['_tickets_abiertos_hoy'] = 0
                u['_pax_abiertos_hoy'] = 0
                u['_snapshot_timestamp'] = ''
                u['_incluye_ventas_abiertas'] = False
            
            # =====================================================================
            # ESTADO V2 DE LA UNIDAD
            # =====================================================================
            ventas_total_unidad = float(u.get('ventas_total') or 0) + float(u.get('_total_estimado_hoy') or 0)
            
            if tiene_cerradas or (tiene_abiertas and ventas_total_unidad > 0):
                u['_status_v2'] = 'ACTUALIZADO'
                u['_status_v2_desc'] = 'Datos vigentes de EDARSAHUB'
            elif tiene_abiertas and ventas_total_unidad == 0:
                u['_status_v2'] = 'SIN_OPERACION'
                u['_status_v2_desc'] = 'Sin ventas pero sync exitoso'
            else:
                u['_status_v2'] = 'SIN_DATOS'
                u['_status_v2_desc'] = 'Sin registros en período'
            
            por_unidad.append(u)
        
        # =====================================================================
        # RECALCULAR TOTALES INCLUYENDO ABIERTAS
        # =====================================================================
        
        # Sumar totales de unidades que SOLO tienen abiertas (no están en cerradas)
        if incluye_hoy and ventas_abiertas_hoy:
            for venta in ventas_abiertas_hoy:
                uid = venta['unidad_negocio_id']
                # Solo sumar si la unidad NO tiene datos cerrados en el período
                if uid not in cerradas_por_unidad:
                    total_dia = float(venta.get('total_estimado_dia') or 0)
                    tickets = int(venta.get('tickets_abiertos') or 0) + int(venta.get('tickets_cerrados_dia') or 0)
                    pax = int(venta.get('pax_abiertos') or 0) + int(venta.get('pax_cerrados_dia') or 0)
                    
                    totales['ventas_total'] = float(totales.get('ventas_total') or 0) + total_dia
                    totales['tickets_total'] = int(totales.get('tickets_total') or 0) + tickets
                    totales['pax_total'] = int(totales.get('pax_total') or 0) + pax
        
        # Actualizar conteo de unidades
        totales['total_unidades'] = len(por_unidad)
        
        # =====================================================================
        # FASE 2: CALCULAR VARIACIONES Y ENRIQUECER CON CÓDIGO CANÓNICO
        # =====================================================================
        
        # Determinar último día con datos para rangos de comparación
        fecha_max_datos = None
        for u in por_unidad:
            if u.get('fecha_max'):
                try:
                    fm = u['fecha_max']
                    if isinstance(fm, str):
                        fm = datetime.strptime(fm, '%Y-%m-%d').date()
                    elif isinstance(fm, datetime):
                        fm = fm.date()
                    if fecha_max_datos is None or fm > fecha_max_datos:
                        fecha_max_datos = fm
                except:
                    pass
        
        if fecha_max_datos is None:
            fecha_max_datos = fecha_fin
        
        # Calcular variaciones por unidad
        for u in por_unidad:
            uid = u['unidad_negocio_id']
            
            # FASE 2: Agregar código canónico oficial
            u['unidad_negocio_codigo'] = MAPEO_KPI_A_CODIGO_CANONICO.get(uid, uid)
            
            # Calcular variaciones comparativas
            variaciones = _get_variaciones_comparativas(
                uid, 
                fecha_inicio, 
                fecha_fin,
                fecha_max_datos
            )
            
            # Agregar variaciones al diccionario de la unidad
            u['ventas_ant'] = variaciones.get('ventas_ant')
            u['ventas_año'] = variaciones.get('ventas_año')
            u['pax_ant'] = variaciones.get('pax_ant')
            u['pax_año'] = variaciones.get('pax_año')
            u['cheques_ant'] = variaciones.get('cheques_ant')
            u['cheques_año'] = variaciones.get('cheques_año')
            u['var_vs_mes_ant'] = variaciones.get('var_vs_mes_ant')
            u['var_vs_año_ant'] = variaciones.get('var_vs_año_ant')
            u['var_pax_mes'] = variaciones.get('var_pax_mes')
            u['var_pax_año'] = variaciones.get('var_pax_año')
            u['var_cheques_mes'] = variaciones.get('var_cheques_mes')
            u['var_cheques_año'] = variaciones.get('var_cheques_año')
            u['_meta_variaciones'] = variaciones.get('_meta_variaciones', {})
        
        # Calcular variaciones para totales
        totales_con_variaciones = _calcular_totales_variaciones(
            totales, 
            fecha_inicio, 
            fecha_fin, 
            fecha_max_datos,
            unidades_permitidas
        )
        
        # Ordenar unidades por ventas_total DESC (corrección bug ordenamiento)
        por_unidad.sort(key=lambda x: float(x.get('ventas_total') or 0), reverse=True)
        
        # Construir respuesta
        response_data = {
            "totales": serialize_response({
                "ventas_total": totales_con_variaciones.get('ventas_total', 0),
                "tickets_total": totales_con_variaciones.get('tickets_total', 0),
                "pax_total": totales_con_variaciones.get('pax_total', 0),
                "total_registros": totales_con_variaciones.get('total_registros', 0),
                "total_unidades": totales_con_variaciones.get('total_unidades', 0),
                "total_dias": totales_con_variaciones.get('total_dias', 0),
                # FASE 2: Variaciones en totales
                "ventas_ant": totales_con_variaciones.get('ventas_ant'),
                "ventas_año": totales_con_variaciones.get('ventas_año'),
                "pax_ant": totales_con_variaciones.get('pax_ant'),
                "pax_año": totales_con_variaciones.get('pax_año'),
                "cheques_ant": totales_con_variaciones.get('cheques_ant'),
                "cheques_año": totales_con_variaciones.get('cheques_año'),
                "var_vs_mes_ant": totales_con_variaciones.get('var_vs_mes_ant'),
                "var_vs_año_ant": totales_con_variaciones.get('var_vs_año_ant'),
                "var_pax_mes": totales_con_variaciones.get('var_pax_mes'),
                "var_pax_año": totales_con_variaciones.get('var_pax_año'),
                "var_cheques_mes": totales_con_variaciones.get('var_cheques_mes'),
                "var_cheques_año": totales_con_variaciones.get('var_cheques_año'),
                "_incluye_ventas_abiertas": incluye_hoy and len(ventas_abiertas_hoy) > 0
            }),
            "unidades": serialize_response([
                {
                    "unidad_negocio_id": u['unidad_negocio_id'],
                    "unidad_negocio_codigo": u.get('unidad_negocio_codigo', u['unidad_negocio_id']),  # FASE 2
                    "unidad_negocio_nombre": u['unidad_negocio_nombre'],
                    "sistema_origen": u['sistema_origen'],
                    "ventas_total": u['ventas_total'],
                    "ventas_sin_propina": u.get('ventas_sin_propina'),
                    "propinas_total": u.get('propinas_total'),
                    "tickets_total": u['tickets_total'],
                    "pax_total": u['pax_total'],
                    "ticket_promedio": u.get('ticket_promedio_avg'),
                    "dias": u['dias'],
                    "fecha_min": u['fecha_min'],
                    "fecha_max": u['fecha_max'],
                    # FASE 2: Variaciones por unidad
                    "ventas_ant": u.get('ventas_ant'),
                    "ventas_año": u.get('ventas_año'),
                    "pax_ant": u.get('pax_ant'),
                    "pax_año": u.get('pax_año'),
                    "cheques_ant": u.get('cheques_ant'),
                    "cheques_año": u.get('cheques_año'),
                    "var_vs_mes_ant": u.get('var_vs_mes_ant'),
                    "var_vs_año_ant": u.get('var_vs_año_ant'),
                    "var_pax_mes": u.get('var_pax_mes'),
                    "var_pax_año": u.get('var_pax_año'),
                    "var_cheques_mes": u.get('var_cheques_mes'),
                    "var_cheques_año": u.get('var_cheques_año'),
                    # Datos de ventas abiertas del día (si aplica)
                    "_ventas_abiertas_hoy": u.get('_ventas_abiertas_hoy', 0),
                    "_ventas_cerradas_hoy": u.get('_ventas_cerradas_hoy', 0),
                    "_total_estimado_hoy": u.get('_total_estimado_hoy', 0),
                    "_tickets_abiertos_hoy": u.get('_tickets_abiertos_hoy', 0),
                    "_pax_abiertos_hoy": u.get('_pax_abiertos_hoy', 0),
                    "_snapshot_timestamp": u.get('_snapshot_timestamp', ''),
                    "_incluye_ventas_abiertas": u.get('_incluye_ventas_abiertas', False),
                    # Estado V2 de la unidad
                    "_status_v2": u.get('_status_v2', 'DESCONOCIDO'),
                    "_status_v2_desc": u.get('_status_v2_desc', ''),
                    "_v2_fuente": "EDARSAHUB",
                    "_v2_tabla": "Comercial_KPIs_Diarios_v2" if u.get('dias', 0) > 0 else "Comercial_Ventas_Dia_Abiertas_v2",
                    "_meta_variaciones": u.get('_meta_variaciones', {})  # FASE 2
                }
                for u in por_unidad
            ]),
            # Resumen de ventas abiertas del día
            "ventas_dia_actual": serialize_response({
                "fecha": fecha_hoy.isoformat(),
                "incluido_en_periodo": incluye_hoy,
                "unidades_con_datos": len(ventas_abiertas_hoy),
                "detalle": [
                    {
                        "unidad_negocio_id": v['unidad_negocio_id'],
                        "unidad_negocio_nombre": v['unidad_negocio_nombre'],
                        "ventas_abiertas": float(v.get('ventas_abiertas') or 0),
                        "ventas_cerradas_dia": float(v.get('ventas_cerradas_dia') or 0),
                        "total_estimado_dia": float(v.get('total_estimado_dia') or 0),
                        "tickets_abiertos": int(v.get('tickets_abiertos') or 0),
                        "pax_abiertos": int(v.get('pax_abiertos') or 0),
                        "snapshot_timestamp": str(v.get('snapshot_timestamp') or ''),
                        "_fuente": "Comercial_Ventas_Dia_Abiertas_v2"
                    }
                    for v in ventas_abiertas_hoy
                ] if ventas_abiertas_hoy else []
            }) if incluye_hoy else None,
            "periodo": {
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat()
            },
            "filtros_aplicados": {
                "unidades": unidades_permitidas,
                "unidad_especifica": unidad_negocio_id
            }
        }
        
        return DashboardResponse(
            success=True,
            data=response_data,
            metadata=MetadataV2()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard v2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINT: KPIS DIARIOS
# =============================================================================

@router.get("/kpis-diarios", response_model=KPIsDiariosResponse)
async def comercial_v2_kpis_diarios(
    fecha_inicio: date = Query(..., description="Fecha inicio"),
    fecha_fin: date = Query(..., description="Fecha fin"),
    unidad_negocio_id: Optional[str] = Query(None, description="Filtrar por unidad"),
    current_user: dict = Depends(get_current_user_dual_dependency())
):
    """
    KPIs diarios detallados v2.
    
    Lee desde: Comercial_KPIs_Diarios_v2
    """
    try:
        unidades_permitidas = await get_unidades_permitidas_v2(current_user)
        
        if not unidades_permitidas:
            raise HTTPException(status_code=403, detail="No tiene unidades asignadas")
        
        if unidad_negocio_id:
            if unidad_negocio_id not in unidades_permitidas:
                raise HTTPException(status_code=403, detail="No tiene acceso a esa unidad")
            unidades_permitidas = [unidad_negocio_id]
        
        # Obtener datos
        datos = get_kpis_diarios(fecha_inicio, fecha_fin, unidades_permitidas)
        
        return KPIsDiariosResponse(
            success=True,
            data=serialize_response(datos),
            total=len(datos),
            periodo={
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat()
            },
            metadata=MetadataV2()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"KPIs diarios v2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINT: KPIS MENSUALES
# =============================================================================

@router.get("/kpis-mensuales", response_model=KPIsMensualesResponse)
async def comercial_v2_kpis_mensuales(
    anio: int = Query(..., description="Año"),
    mes_inicio: int = Query(1, ge=1, le=12, description="Mes inicio"),
    mes_fin: int = Query(12, ge=1, le=12, description="Mes fin"),
    unidad_negocio_id: Optional[str] = Query(None, description="Filtrar por unidad"),
    current_user: dict = Depends(get_current_user_dual_dependency())
):
    """
    KPIs mensuales v2.
    
    Lee desde: Comercial_KPIs_Mensuales_v2
    """
    try:
        unidades_permitidas = await get_unidades_permitidas_v2(current_user)
        
        if not unidades_permitidas:
            raise HTTPException(status_code=403, detail="No tiene unidades asignadas")
        
        if unidad_negocio_id:
            if unidad_negocio_id not in unidades_permitidas:
                raise HTTPException(status_code=403, detail="No tiene acceso a esa unidad")
            unidades_permitidas = [unidad_negocio_id]
        
        # Obtener datos
        datos = get_kpis_mensuales(anio, mes_inicio, mes_fin, unidades_permitidas)
        
        return KPIsMensualesResponse(
            success=True,
            data=serialize_response(datos),
            total=len(datos),
            anio=anio,
            metadata=MetadataV2()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"KPIs mensuales v2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINT: VENTAS DIA
# =============================================================================

@router.get("/ventas-dia", response_model=VentasDiaResponse)
async def comercial_v2_ventas_dia(
    fecha: date = Query(default=None, description="Fecha (default: hoy)"),
    current_user: dict = Depends(get_current_user_dual_dependency())
):
    """
    Ventas del día v2.
    
    Lee desde: Comercial_Ventas_Dia_Abiertas_v2 (EDARSAHUB SQL)
    Actualizado cada 5 minutos por sync_comercial_abiertas_v2_job.py
    
    REGLAS IMPLEMENTADAS:
    - Tablero lee SOLO desde EDARSAHUB SQL (no conexiones live)
    - Muestra última actualización (snapshot_timestamp)
    - Ordenamiento por venta DESC (mayor a menor)
    - dato_vencido si última actualización > 10 minutos
    - NO mostrar $0 falso si no hay dato sincronizado válido
    
    Retorna:
    - total_estimado_dia: Total del día (abiertas + cerradas)
    - snapshot_timestamp: Última actualización del dato
    - minutos_desde_ultima_actualizacion
    - dato_vencido: true si > 10 minutos sin actualizar
    """
    try:
        if fecha is None:
            fecha = date.today()
        
        unidades_permitidas = await get_unidades_permitidas_v2(current_user)
        
        if not unidades_permitidas:
            raise HTTPException(status_code=403, detail="No tiene unidades asignadas")
        
        # Obtener datos de ventas desde EDARSAHUB SQL
        datos = get_ventas_dia_abiertas(fecha, unidades_permitidas)
        
        # Hora actual para calcular frescura
        ahora = datetime.now(timezone.utc)
        
        # Procesar y enriquecer datos
        datos_enriquecidos = []
        for d in datos:
            # Calcular minutos desde última actualización
            snapshot = d.get('snapshot_timestamp')
            minutos_desde_actualizacion = None
            dato_vencido = False
            
            if snapshot:
                try:
                    if isinstance(snapshot, str):
                        snapshot_dt = datetime.fromisoformat(snapshot.replace('Z', '+00:00'))
                    else:
                        snapshot_dt = snapshot
                    
                    if snapshot_dt.tzinfo is None:
                        snapshot_dt = snapshot_dt.replace(tzinfo=timezone.utc)
                    
                    diff = ahora - snapshot_dt
                    minutos_desde_actualizacion = int(diff.total_seconds() / 60)
                    dato_vencido = minutos_desde_actualizacion > 10
                except:
                    minutos_desde_actualizacion = None
                    dato_vencido = True
            else:
                dato_vencido = True
            
            total_dia = float(d.get('total_estimado_dia') or 0)
            
            datos_enriquecidos.append({
                "unidad_negocio_id": d['unidad_negocio_id'],
                "unidad_negocio_nombre": d['unidad_negocio_nombre'],
                "server_id": d.get('server_id'),
                "sistema_origen": d['sistema_origen'],
                "ventas_abiertas": float(d.get('ventas_abiertas') or 0),
                "tickets_abiertos": int(d.get('tickets_abiertos') or 0),
                "pax_abiertos": int(d.get('pax_abiertos') or 0),
                "ventas_cerradas_dia": float(d.get('ventas_cerradas_dia') or 0),
                "tickets_cerrados_dia": int(d.get('tickets_cerrados_dia') or 0),
                "pax_cerrados_dia": int(d.get('pax_cerrados_dia') or 0),
                "total_estimado_dia": total_dia,
                # Campos de última actualización (REGLA PRINCIPAL)
                "snapshot_timestamp": str(d.get('snapshot_timestamp') or ''),
                "minutos_desde_ultima_actualizacion": minutos_desde_actualizacion,
                "dato_vencido": dato_vencido,
                # Campos técnicos opcionales
                "fuente_original": d.get('fuente_original'),
                "sync_run_id": d.get('sync_run_id'),
                "_fuente": "EDARSAHUB_SQL"
            })
        
        # ORDENAMIENTO: Mayor venta a menor venta
        # Regla: Ventas positivas primero (DESC), luego ceros, luego sin dato/vencido
        def sort_key(item):
            venta = item.get('total_estimado_dia', 0)
            vencido = item.get('dato_vencido', True)
            # Prioridad: 
            # 1. Ventas positivas válidas (orden desc)
            # 2. Ventas en cero válidas
            # 3. Sin dato o vencido
            if vencido and venta == 0:
                return (2, 0, item.get('unidad_negocio_nombre', ''))
            elif venta == 0:
                return (1, 0, item.get('unidad_negocio_nombre', ''))
            else:
                return (0, -venta, item.get('unidad_negocio_nombre', ''))
        
        datos_ordenados = sorted(datos_enriquecidos, key=sort_key)
        
        # Calcular totales (solo de datos válidos)
        total_ventas_abiertas = sum(d['ventas_abiertas'] for d in datos_ordenados)
        total_ventas_cerradas = sum(d['ventas_cerradas_dia'] for d in datos_ordenados)
        total_estimado = sum(d['total_estimado_dia'] for d in datos_ordenados)
        total_tickets = sum(d['tickets_abiertos'] + d['tickets_cerrados_dia'] for d in datos_ordenados)
        total_pax = sum(d['pax_abiertos'] + d['pax_cerrados_dia'] for d in datos_ordenados)
        
        return VentasDiaResponse(
            success=True,
            data=serialize_response({
                "resumen": {
                    "fecha": fecha.isoformat(),
                    "total_ventas_abiertas": total_ventas_abiertas,
                    "total_ventas_cerradas_dia": total_ventas_cerradas,
                    "total_estimado_dia": total_estimado,
                    "total_tickets": total_tickets,
                    "total_pax": total_pax,
                    "unidades_con_datos": len(datos_ordenados),
                    "unidades_dato_vencido": sum(1 for d in datos_ordenados if d['dato_vencido'])
                },
                "por_unidad": datos_ordenados,
                "_info": {
                    "fuente": "EDARSAHUB_SQL",
                    "tabla": "Comercial_Ventas_Dia_Abiertas_v2",
                    "frecuencia_sync": "5 minutos",
                    "ordenamiento": "venta_desc"
                }
            }),
            fecha=fecha.isoformat(),
            metadata=MetadataV2()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ventas día v2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINT: UNIDADES
# =============================================================================

@router.get("/unidades", response_model=UnidadesResponse)
async def comercial_v2_unidades(
    current_user: dict = Depends(get_current_user_dual_dependency())
):
    """
    Unidades de negocio disponibles en v2.
    
    Lee desde: Comercial_KPIs_Diarios_v2 (DISTINCT)
    """
    try:
        unidades_permitidas = await get_unidades_permitidas_v2(current_user)
        
        # Obtener unidades con datos
        unidades = get_unidades_disponibles(unidades_permitidas if unidades_permitidas else None)
        
        return UnidadesResponse(
            success=True,
            unidades=serialize_response(unidades),
            total=len(unidades),
            metadata=MetadataV2()
        )
        
    except Exception as e:
        logger.error(f"Unidades v2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINT: SYNC STATUS
# =============================================================================

@router.get("/sync-status", response_model=SyncStatusResponse)
async def comercial_v2_sync_status(
    limit: int = Query(50, ge=1, le=200, description="Límite de registros"),
    current_user: dict = Depends(get_current_user_dual_dependency())
):
    """
    Estado de sincronización v2.
    
    Lee desde: Comercial_SyncLog_v2
    """
    try:
        unidades_permitidas = await get_unidades_permitidas_v2(current_user)
        
        # Obtener logs
        logs = get_sync_status(unidades_permitidas, limit)
        
        # Obtener última sync por unidad
        ultima_sync = get_last_sync_by_unidad(unidades_permitidas)
        
        return SyncStatusResponse(
            success=True,
            logs=serialize_response(logs),
            ultima_sync_por_unidad=serialize_response(ultima_sync),
            metadata=MetadataV2()
        )
        
    except Exception as e:
        logger.error(f"Sync status v2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GETTER DEL ROUTER
# =============================================================================

def get_comercial_v2_router():
    """Retorna el router de Comercial v2."""
    return router
