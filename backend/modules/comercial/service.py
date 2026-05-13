"""
EDARSA HUB - Comercial Module Service
=====================================
Lógica de negocio para el módulo comercial.

FASE 5 DEL REFACTOR MODULAR (Diciembre 2025):
- Estructura base creada
- Funciones auxiliares de procesamiento

FASE 5B-2 DEL REFACTOR MODULAR (Abril 2026):
- Migrado: get_kpis_softrestaurant() desde server.py
- Migrado: get_kpis_mpro() desde server.py  
- Migrado: get_kpis_mpro_por_sucursal() desde server.py
- Compatibilidad 100%: server.py ahora importa desde aquí

FUNCIONES MIGRADAS PREVIAMENTE (FASE 5B-1):
- query_api_mpro_local() -> modules/comercial/adapters.py
- obtener_ventas_dia_api_local() -> modules/comercial/adapters.py
- sumar_ventas_api_local_a_sucursal() -> modules/comercial/adapters.py

FIX ESTRUCTURAL (Abril 2026):
- Integración con DateFilterPolicy para validación de rangos de fecha
- Eliminación de bugs por fechas inválidas

FASE 4.4 (Abril 2026):
- Aplicación de SourceQueryResult para distinguir consulta real de error de conexión
- REGLA: "Un cero solo es válido si hubo consulta real exitosa"
"""

from typing import Dict, List, Any, Optional
import logging
import calendar
from datetime import datetime, timezone
from fastapi import HTTPException

from core.db import execute_sql_query, check_column_exists, get_propina_safe_column, get_propina_safe_column_tempcheques
from core.utils.date_filters import DateFilterPolicy, to_yyyymmdd_range, is_valid_range
from core.source_resolver import (
    QueryStatus,
    SourceQueryResult,
    classify_sql_error
)
from modules.comercial.adapters import sumar_ventas_api_local_a_sucursal
from modules.comercial import repository as repo

# BLOQUE 4: Import de queries centralizadas (Fase 1 Plan Migración)
from modules.comercial.queries.softrestaurant import query_ventas_periodo_sr
from modules.comercial.queries.mpro import query_ventas_periodo_mpro, query_ventas_por_sucursal_mpro


# ============================================================================
# CONFIGURACIÓN EDARSAHUB - TABLERO EJECUTIVO (Mayo 2026)
# ============================================================================
# MÁXIMA: EDARSAHUB es el cerebro del sistema.
# Tablero Ejecutivo lee exclusivamente de Comercial_KPIs_Diarios_v2.
# NO consulta servidores locales ni MongoDB para KPIs.

EDARSAHUB_TABLERO_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'HRLectura',
    'password': 'National09$'
}


# ============================================================================
# CATÁLOGO MAESTRO DE UNIDADES DE NEGOCIO (EDARSAHUB)
# ============================================================================
# FUENTE MAESTRA: Unidades_Negocio.codigo
# CÓDIGOS OFICIALES: 130MID, 130QRO, CIENFUEGOS, ESTELAR, ORIGEN
# NO usar MongoDB como fuente funcional para unidades.

_CACHE_UNIDADES_NEGOCIO = None

def _cargar_catalogo_unidades_negocio() -> Dict:
    """
    Carga el catálogo maestro de Unidades de Negocio desde EDARSAHUB.
    
    FUENTE MAESTRA: Unidades_Negocio
    NO usa MongoDB.
    
    Retorna diccionario con dos mapeos:
    - por_server_id: {server_id: {codigo, nombre, sucursal_origen_id}}
    - por_server_sucursal: {server_id:sucursal: {codigo, nombre}}
    """
    global _CACHE_UNIDADES_NEGOCIO
    
    if _CACHE_UNIDADES_NEGOCIO is not None:
        return _CACHE_UNIDADES_NEGOCIO
    
    query = """
    SELECT 
        id,
        codigo,
        nombre,
        server_id,
        sucursal_origen_id,
        system_type,
        activo
    FROM Unidades_Negocio
    WHERE activo = 1
    ORDER BY orden
    """
    
    try:
        result = execute_sql_query(
            EDARSAHUB_TABLERO_CONFIG['host'],
            EDARSAHUB_TABLERO_CONFIG['port'],
            EDARSAHUB_TABLERO_CONFIG['database'],
            EDARSAHUB_TABLERO_CONFIG['username'],
            EDARSAHUB_TABLERO_CONFIG['password'],
            query
        )
        
        por_server_id = {}
        por_server_sucursal = {}
        
        for row in result or []:
            server_id = row.get('server_id', '')
            sucursal = row.get('sucursal_origen_id', '') or ''
            codigo = row.get('codigo', '')
            nombre = row.get('nombre', '')
            
            unidad_data = {
                'codigo': codigo,
                'nombre': nombre,
                'sucursal_origen_id': sucursal,
                'system_type': row.get('system_type', '')
            }
            
            # Mapeo por server_id (para SoftRestaurant sin sucursal)
            if not sucursal:
                por_server_id[server_id] = unidad_data
            
            # Mapeo por server_id:sucursal (para MPRO con sucursal)
            key = f"{server_id}:{sucursal}" if sucursal else server_id
            por_server_sucursal[key] = unidad_data
        
        _CACHE_UNIDADES_NEGOCIO = {
            'por_server_id': por_server_id,
            'por_server_sucursal': por_server_sucursal,
            'lista': result or []
        }
        
        logging.info(f"[UNIDADES_NEGOCIO] Catálogo cargado desde EDARSAHUB: {len(result or [])} unidades activas")
        return _CACHE_UNIDADES_NEGOCIO
        
    except Exception as e:
        logging.error(f"[UNIDADES_NEGOCIO] Error cargando catálogo desde EDARSAHUB: {e}")
        return {'por_server_id': {}, 'por_server_sucursal': {}, 'lista': []}


def obtener_unidad_negocio_edarsahub(server_id: str, sucursal: str = None) -> Dict:
    """
    Obtiene datos de una unidad de negocio desde el catálogo EDARSAHUB.
    
    FUENTE MAESTRA: Unidades_Negocio (EDARSAHUB SQL Server)
    NO usa MongoDB.
    
    Args:
        server_id: UUID del servidor
        sucursal: ID de sucursal (para MPRO)
    
    Returns:
        Dict con codigo, nombre, sucursal_origen_id o valores por defecto
    """
    catalogo = _cargar_catalogo_unidades_negocio()
    
    # Priorizar búsqueda por server_id:sucursal
    if sucursal:
        key = f"{server_id}:{sucursal}"
        if key in catalogo['por_server_sucursal']:
            return catalogo['por_server_sucursal'][key]
    
    # Fallback: búsqueda solo por server_id
    if server_id in catalogo['por_server_id']:
        return catalogo['por_server_id'][server_id]
    
    # Si no se encuentra, retornar estructura vacía (no usar MongoDB)
    logging.warning(f"[UNIDADES_NEGOCIO] No se encontró unidad para server_id={server_id}, sucursal={sucursal}")
    return {
        'codigo': server_id,  # Fallback al server_id
        'nombre': 'Unidad Desconocida',
        'sucursal_origen_id': sucursal,
        'system_type': ''
    }


def _obtener_codigo_canonico_mpro(server_id: str, sucursal_id: str, sucursal_nombre: str) -> tuple:
    """
    CAMBIO B HELPER: Obtiene código y nombre canónico para una sucursal MPRO.
    
    FUENTE MAESTRA: Unidades_Negocio (EDARSAHUB)
    NO usar MongoDB como fuente funcional.
    
    Args:
        server_id: ID del servidor MPRO
        sucursal_id: ID de la sucursal (ej: "0021", "0023")
        sucursal_nombre: Nombre visible de la sucursal (para fallback)
    
    Returns:
        Tuple (unidad_negocio_codigo, unidad_negocio_nombre)
    """
    unidad_edarsahub = obtener_unidad_negocio_edarsahub(server_id, sucursal=sucursal_id)
    
    codigo = unidad_edarsahub.get('codigo', '')
    nombre = unidad_edarsahub.get('nombre', '')
    
    if codigo and nombre:
        return codigo, nombre
    
    # Fallback: Mapeo hardcodeado solo si EDARSAHUB no responde
    fallback_map = {
        '0021': ('130QRO', '130° QUERETARO'),
        '0023': ('ORIGEN', 'ORIGEN'),
        'ORIGEN': ('ORIGEN', 'ORIGEN'),
        '130_QRO': ('130QRO', '130° QUERETARO'),
    }
    
    if sucursal_id in fallback_map:
        return fallback_map[sucursal_id]
    
    # Fallback final: usar nombre visible
    return (sucursal_id, sucursal_nombre)


def _query_edarsahub_tablero(query: str) -> List[Dict]:
    """
    Ejecuta query de SOLO LECTURA en EDARSAHUB para Tablero Ejecutivo.
    Fuente: Comercial_KPIs_Diarios_v2 y Comercial_Ventas_Dia_Abiertas_v2.
    NO usa MongoDB. NO usa servidores locales.
    """
    try:
        result = execute_sql_query(
            EDARSAHUB_TABLERO_CONFIG['host'],
            EDARSAHUB_TABLERO_CONFIG['port'],
            EDARSAHUB_TABLERO_CONFIG['database'],
            EDARSAHUB_TABLERO_CONFIG['username'],
            EDARSAHUB_TABLERO_CONFIG['password'],
            query
        )
        return result or []
    except Exception as e:
        logging.error(f"[TABLERO-EDARSAHUB] Error ejecutando query: {e}")
        return []


def _get_ultimo_dia_con_datos_edarsahub(server_id: str, mes: int, anio: int) -> Optional[int]:
    """
    Obtiene el último día con ventas registradas en Comercial_KPIs_Diarios_v2.
    Retorna el día (1-31) o None si no hay datos.
    """
    query = f"""
    SELECT MAX(dia) as ultimo_dia
    FROM Comercial_KPIs_Diarios_v2
    WHERE server_id = '{server_id}'
      AND anio = {anio}
      AND mes = {mes}
      AND ventas_total > 0
    """
    result = _query_edarsahub_tablero(query)
    if result and result[0].get('ultimo_dia'):
        return int(result[0]['ultimo_dia'])
    return None


def _get_kpis_periodo_edarsahub(
    server_id: str,
    fecha_ini: str,  # YYYY-MM-DD
    fecha_fin: str,  # YYYY-MM-DD (inclusivo)
    sucursal_id: str = 'DEFAULT'
) -> Dict:
    """
    Obtiene KPIs agregados de Comercial_KPIs_Diarios_v2 para un período.
    
    Retorna:
        {
            'ventas': float,
            'pax': int,
            'cheques': int,
            'registros': int,
            'existe_data': bool
        }
    """
    # Usar rangos semiabiertos: fecha >= ini AND fecha < fin+1
    query = f"""
    SELECT 
        ISNULL(SUM(ventas_total), 0) as ventas,
        ISNULL(SUM(pax_total), 0) as pax,
        ISNULL(SUM(tickets_total), 0) as cheques,
        COUNT(*) as registros
    FROM Comercial_KPIs_Diarios_v2
    WHERE server_id = '{server_id}'
      AND sucursal_id = '{sucursal_id}'
      AND fecha_operacion >= '{fecha_ini}'
      AND fecha_operacion <= '{fecha_fin}'
      AND ventas_total > 0
    """
    result = _query_edarsahub_tablero(query)
    
    if result and len(result) > 0:
        row = result[0]
        ventas = float(row.get('ventas') or 0)
        pax = int(row.get('pax') or 0)
        cheques = int(row.get('cheques') or 0)
        registros = int(row.get('registros') or 0)
        
        return {
            'ventas': ventas,
            'pax': pax,
            'cheques': cheques,
            'registros': registros,
            'existe_data': registros > 0
        }
    
    return {
        'ventas': 0,
        'pax': 0,
        'cheques': 0,
        'registros': 0,
        'existe_data': False
    }


def _get_ventas_abiertas_edarsahub(server_id: str, sucursal_id: str = 'DEFAULT') -> Dict:
    """
    Obtiene ventas abiertas del día desde Comercial_Ventas_Dia_Abiertas_v2.
    Para modo "Ventas del Día" en Tablero Ejecutivo.
    """
    query = f"""
    SELECT TOP 1
        ventas_abiertas,
        tickets_abiertos,
        pax_abiertos,
        ventas_cerradas_dia,
        tickets_cerrados_dia,
        pax_cerrados_dia,
        total_estimado_dia,
        snapshot_timestamp,
        fecha_operacion
    FROM Comercial_Ventas_Dia_Abiertas_v2
    WHERE server_id = '{server_id}'
      AND sucursal_id = '{sucursal_id}'
    ORDER BY snapshot_timestamp DESC
    """
    result = _query_edarsahub_tablero(query)
    
    if result and len(result) > 0:
        row = result[0]
        return {
            'existe': True,
            'ventas': float(row.get('ventas_abiertas') or 0) + float(row.get('ventas_cerradas_dia') or 0),
            'pax': int(row.get('pax_abiertos') or 0) + int(row.get('pax_cerrados_dia') or 0),
            'cheques': int(row.get('tickets_abiertos') or 0) + int(row.get('tickets_cerrados_dia') or 0),
            'snapshot_timestamp': row.get('snapshot_timestamp'),
            'fecha_operacion': row.get('fecha_operacion')
        }
    
    return {
        'existe': False,
        'ventas': 0,
        'pax': 0,
        'cheques': 0,
        'snapshot_timestamp': None,
        'fecha_operacion': None
    }


def _calcular_variacion_pct(valor_actual: float, valor_comparativo: float) -> Optional[float]:
    """
    Calcula variación porcentual respetando reglas de negocio.
    
    Reglas:
    - Si valor_comparativo es None o no existe: retorna None (no 0)
    - Si valor_comparativo = 0 y valor_actual > 0: retorna None (evita división por cero)
    - Si valor_actual = 0 y valor_comparativo > 0: retorna -100%
    - Si ambos son 0 y existen registros: retorna 0%
    - No devolver 0% falso si no se pudo calcular
    """
    if valor_comparativo is None:
        return None
    
    if valor_comparativo == 0:
        if valor_actual > 0:
            return None  # No dividir entre cero
        else:
            return 0.0  # Ambos son 0
    
    variacion = ((valor_actual - valor_comparativo) / valor_comparativo) * 100
    return round(variacion, 1)


def _obtener_kpis_tablero_desde_edarsahub(
    server_id: str,
    unidad_negocio_id: str,
    sucursal_id: str,
    fecha_ini: str,
    fecha_fin: str,
    dias_mes: int,
    nombre_unidad: str = ''
) -> Optional[Dict]:
    """
    FUNCIÓN PRINCIPAL - TABLERO EJECUTIVO DESDE EDARSAHUB
    =====================================================
    Obtiene KPIs para Tablero Ejecutivo EXCLUSIVAMENTE desde EDARSAHUB.
    
    MÁXIMA: EDARSAHUB es el cerebro del sistema.
    - NO consulta servidores locales
    - NO consulta MongoDB
    - Lee de Comercial_KPIs_Diarios_v2
    
    REGLA DE COMPARATIVOS:
    1. Mes parcial: compara mismos días
    2. Mes completo: compara mes vs mes completo
    
    Args:
        server_id: ID del servidor EDARSAHUB (para mapear unidad)
        unidad_negocio_id: ID de unidad (130-MER, CIENFUEGOS, etc.)
        sucursal_id: ID de sucursal (DEFAULT, 0021, 0023)
        fecha_ini: Fecha inicio período actual (YYYY-MM-DD)
        fecha_fin: Fecha fin período actual (YYYY-MM-DD)
        dias_mes: Días totales del mes para proyección
        nombre_unidad: Nombre de la unidad (para logs)
    
    Returns:
        Dict con KPIs o None si hay error
    """
    logging.info(f"[TABLERO-EDARSAHUB] {nombre_unidad or unidad_negocio_id}: Consultando KPIs desde EDARSAHUB")
    
    # Parsear fechas
    anio_ini = int(fecha_ini[:4])
    mes_ini = int(fecha_ini[5:7])
    anio_fin = int(fecha_fin[:4])
    mes_fin = int(fecha_fin[5:7])
    dia_fin = int(fecha_fin[8:10])
    
    # 1. DETECTAR ÚLTIMO DÍA CON VENTAS EN EL PERÍODO ACTUAL
    query_ultimo_dia = f"""
    SELECT MAX(fecha_operacion) as ultimo_dia_venta, MAX(dia) as dia_max
    FROM Comercial_KPIs_Diarios_v2
    WHERE unidad_negocio_id = '{unidad_negocio_id}'
      AND sucursal_id = '{sucursal_id}'
      AND fecha_operacion >= '{fecha_ini}'
      AND fecha_operacion <= '{fecha_fin}'
      AND ventas_total > 0
    """
    result_ultimo = _query_edarsahub_tablero(query_ultimo_dia)
    
    if not result_ultimo or not result_ultimo[0].get('ultimo_dia_venta'):
        logging.warning(f"[TABLERO-EDARSAHUB] {nombre_unidad}: Sin datos en período {fecha_ini} a {fecha_fin}")
        return None
    
    ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
    if isinstance(ultimo_dia_venta, str):
        partes = ultimo_dia_venta.split('T')[0].split('-') if 'T' in ultimo_dia_venta else ultimo_dia_venta.split('-')
        anio_ultimo = int(partes[0])
        mes_ultimo = int(partes[1])
        dia_ultimo = int(partes[2])
    else:
        anio_ultimo = ultimo_dia_venta.year
        mes_ultimo = ultimo_dia_venta.month
        dia_ultimo = ultimo_dia_venta.day
    
    # Determinar si el mes está completo o parcial
    ultimo_dia_mes = calendar.monthrange(anio_ultimo, mes_ultimo)[1]
    mes_completo = (dia_ultimo >= ultimo_dia_mes)
    
    logging.info(f"[TABLERO-EDARSAHUB] {nombre_unidad}: Último día con datos: {anio_ultimo}-{mes_ultimo:02d}-{dia_ultimo:02d}, Mes completo: {mes_completo}")
    
    # 2. CALCULAR RANGOS DE FECHAS PARA COMPARATIVOS
    # Período actual: desde inicio hasta último día con ventas
    fecha_fin_real = f"{anio_ultimo}-{mes_ultimo:02d}-{dia_ultimo:02d}"
    
    # Mes anterior
    if mes_ultimo == 1:
        mes_ant = 12
        anio_ant = anio_ultimo - 1
    else:
        mes_ant = mes_ultimo - 1
        anio_ant = anio_ultimo
    
    ultimo_dia_mes_ant = calendar.monthrange(anio_ant, mes_ant)[1]
    
    if mes_completo:
        # Mes completo: comparar mes vs mes completo
        fecha_ini_ant = f"{anio_ant}-{mes_ant:02d}-01"
        fecha_fin_ant = f"{anio_ant}-{mes_ant:02d}-{ultimo_dia_mes_ant:02d}"
    else:
        # Mes parcial: comparar mismos días
        dia_comparar_ant = min(dia_ultimo, ultimo_dia_mes_ant)
        fecha_ini_ant = f"{anio_ant}-{mes_ant:02d}-01"
        fecha_fin_ant = f"{anio_ant}-{mes_ant:02d}-{dia_comparar_ant:02d}"
    
    # Año anterior
    anio_pasado = anio_ultimo - 1
    ultimo_dia_mes_anio_ant = calendar.monthrange(anio_pasado, mes_ultimo)[1]
    
    if mes_completo:
        # Mes completo: comparar mes vs mes completo del año anterior
        fecha_ini_anio_ant = f"{anio_pasado}-{mes_ultimo:02d}-01"
        fecha_fin_anio_ant = f"{anio_pasado}-{mes_ultimo:02d}-{ultimo_dia_mes_anio_ant:02d}"
    else:
        # Mes parcial: comparar mismos días del año anterior
        dia_comparar_anio_ant = min(dia_ultimo, ultimo_dia_mes_anio_ant)
        fecha_ini_anio_ant = f"{anio_pasado}-{mes_ultimo:02d}-01"
        fecha_fin_anio_ant = f"{anio_pasado}-{mes_ultimo:02d}-{dia_comparar_anio_ant:02d}"
    
    logging.info(f"[TABLERO-EDARSAHUB] {nombre_unidad}: Rangos - Actual: {fecha_ini} a {fecha_fin_real}, Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_anio_ant} a {fecha_fin_anio_ant}")
    
    # 3. OBTENER KPIs PERÍODO ACTUAL
    kpis_actual = _get_kpis_periodo_edarsahub(server_id, fecha_ini, fecha_fin_real, sucursal_id)
    
    if not kpis_actual['existe_data']:
        logging.warning(f"[TABLERO-EDARSAHUB] {nombre_unidad}: Sin datos reales en período actual")
        return None
    
    ventas = kpis_actual['ventas']
    pax = kpis_actual['pax']
    cheques = kpis_actual['cheques']
    
    # Calcular días transcurridos para proyección
    fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
    fecha_fin_dt = datetime(anio_ultimo, mes_ultimo, dia_ultimo)
    dias_transcurridos = (fecha_fin_dt - fecha_ini_dt).days + 1
    
    # 4. OBTENER KPIs MES ANTERIOR
    kpis_mes_ant = _get_kpis_periodo_edarsahub(server_id, fecha_ini_ant, fecha_fin_ant, sucursal_id)
    
    if kpis_mes_ant['existe_data']:
        ventas_ant = kpis_mes_ant['ventas']
        pax_ant = kpis_mes_ant['pax']
        cheques_ant = kpis_mes_ant['cheques']
    else:
        ventas_ant = None
        pax_ant = None
        cheques_ant = None
        logging.info(f"[TABLERO-EDARSAHUB] {nombre_unidad}: Sin datos de mes anterior ({fecha_ini_ant} a {fecha_fin_ant})")
    
    # 5. OBTENER KPIs AÑO ANTERIOR
    kpis_anio_ant = _get_kpis_periodo_edarsahub(server_id, fecha_ini_anio_ant, fecha_fin_anio_ant, sucursal_id)
    
    if kpis_anio_ant['existe_data']:
        ventas_año = kpis_anio_ant['ventas']
        pax_año = kpis_anio_ant['pax']
        cheques_año = kpis_anio_ant['cheques']
    else:
        ventas_año = None
        pax_año = None
        cheques_año = None
        logging.info(f"[TABLERO-EDARSAHUB] {nombre_unidad}: Sin datos de año anterior ({fecha_ini_anio_ant} a {fecha_fin_anio_ant})")
    
    # 6. CALCULAR MÉTRICAS DERIVADAS
    ticket_prom = round(ventas / pax, 2) if pax and pax > 0 else 0
    cheque_prom = round(ventas / cheques, 2) if cheques and cheques > 0 else 0
    proyeccion = round((ventas / dias_transcurridos) * dias_mes, 2) if dias_transcurridos > 0 else 0
    
    # 7. CALCULAR VARIACIONES (respetando reglas de null)
    var_vs_mes_ant = _calcular_variacion_pct(ventas, ventas_ant)
    var_vs_año_ant = _calcular_variacion_pct(ventas, ventas_año)
    var_pax_mes = _calcular_variacion_pct(pax, pax_ant)
    var_pax_año = _calcular_variacion_pct(pax, pax_año)
    var_cheques_mes = _calcular_variacion_pct(cheques, cheques_ant)
    var_cheques_año = _calcular_variacion_pct(cheques, cheques_año)
    
    logging.info(f"[TABLERO-EDARSAHUB] {nombre_unidad}: Ventas=${ventas:,.0f}, vs Mes Ant={var_vs_mes_ant}%, vs Año Ant={var_vs_año_ant}%")
    
    # =========================================================================
    # REGLA: Si NO existe base comparativa válida, devolver null (no 0 falso)
    # Frontend debe mostrar "-" cuando recibe null
    # Si existe base y la variación es 0.0%, devolver 0.0 (cero real)
    # =========================================================================
    return {
        "ventas": ventas,
        "ventas_ant": ventas_ant,  # null si no existe
        "ventas_año": ventas_año,  # null si no existe
        "var_vs_mes_ant": var_vs_mes_ant,  # null si no existe base
        "var_vs_año_ant": var_vs_año_ant,  # null si no existe base
        "proyeccion": proyeccion,
        "pax": pax,
        "pax_ant": pax_ant,  # null si no existe
        "pax_año": pax_año,  # null si no existe
        "var_pax_mes": var_pax_mes,  # null si no existe base
        "var_pax_año": var_pax_año,  # null si no existe base
        "cheques": cheques,
        "cheques_ant": cheques_ant,  # null si no existe
        "cheques_año": cheques_año,  # null si no existe
        "var_cheques_mes": var_cheques_mes,  # null si no existe base
        "var_cheques_año": var_cheques_año,  # null si no existe base
        "ticket_prom": ticket_prom,
        "cheque_prom": cheque_prom,
        "fuente": "EDARSAHUB",
        "_meta": {
            "tabla": "Comercial_KPIs_Diarios_v2",
            "ultimo_dia_con_datos": f"{anio_ultimo}-{mes_ultimo:02d}-{dia_ultimo:02d}",
            "mes_completo": mes_completo,
            "dias_transcurridos": dias_transcurridos,
            "rango_actual": f"{fecha_ini} a {fecha_fin_real}",
            "rango_mes_ant": f"{fecha_ini_ant} a {fecha_fin_ant}",
            "rango_anio_ant": f"{fecha_ini_anio_ant} a {fecha_fin_anio_ant}",
            "tiene_datos_mes_ant": ventas_ant is not None,
            "tiene_datos_anio_ant": ventas_año is not None
        }
    }


# Mapeo de unidades EDARSAHUB (equivalente a la configuración de los jobs de sync)
UNIDADES_EDARSAHUB_MAP = {
    # SoftRestaurant
    "a5547321-1139-4d2b-9d53-182ca737b6b6": {"unidad_negocio_id": "130-MER", "nombre": "130° MÉRIDA", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
    "6d053c22-523e-48c0-b72b-96081e2d781b": {"unidad_negocio_id": "CIENFUEGOS", "nombre": "CIENFUEGOS", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
    "a5ff0e25-f029-43db-b634-d4ac814c904f": {"unidad_negocio_id": "LA-ESTELAR", "nombre": "LA ESTELAR", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
    # MPRO (necesitan sucursal específica)
    "1b230a06-ffaf-4c70-bd27-b1be3579dea6": {
        "sucursales": {
            "0021": {"unidad_negocio_id": "130-QRO", "nombre": "130° QUERETARO"},
            "0023": {"unidad_negocio_id": "ORIGEN", "nombre": "ORIGEN"}
        },
        "sistema": "MPRO"
    }
}


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def calcular_ticket_promedio(ventas: float, cheques: int) -> float:
    """Calcula el ticket promedio."""
    return round(ventas / cheques, 2) if cheques > 0 else 0.0


def calcular_consumo_promedio(ventas: float, pax: int) -> float:
    """Calcula el consumo promedio por persona."""
    return round(ventas / pax, 2) if pax > 0 else 0.0


def calcular_porcentaje_cumplimiento(actual: float, meta: float) -> float:
    """Calcula el porcentaje de cumplimiento de una meta."""
    return round((actual / meta) * 100, 2) if meta > 0 else 0.0


# ============================================================================
# PROCESAMIENTO DE DATOS
# ============================================================================

def procesar_ventas_sucursal(data: Dict, nombre_sucursal: str = "") -> Dict:
    """
    Procesa y normaliza datos de ventas de una sucursal.
    """
    ventas = float(data.get('ventas', 0) or 0)
    pax = int(data.get('pax', 0) or 0)
    cheques = int(data.get('cheques', 0) or 0)
    
    return {
        "nombre": nombre_sucursal or data.get('nombre', ''),
        "ventas": ventas,
        "pax": pax,
        "cheques": cheques,
        "ticket_promedio": calcular_ticket_promedio(ventas, cheques),
        "consumo_promedio": calcular_consumo_promedio(ventas, pax),
        "status": data.get('status', 'online'),
        "origen": data.get('origen', 'nube')
    }


def agregar_totales(sucursales: List[Dict]) -> Dict:
    """
    Calcula totales agregados de una lista de sucursales.
    """
    total_ventas = sum(s.get('ventas', 0) for s in sucursales)
    total_pax = sum(s.get('pax', 0) for s in sucursales)
    total_cheques = sum(s.get('cheques', 0) for s in sucursales)
    
    return {
        "ventas": total_ventas,
        "pax": total_pax,
        "cheques": total_cheques,
        "ticket_promedio": calcular_ticket_promedio(total_ventas, total_cheques),
        "consumo_promedio": calcular_consumo_promedio(total_ventas, total_pax),
        "num_sucursales": len(sucursales)
    }


# ============================================================================
# P0: ESTRUCTURA ESTÁNDAR DE RESPUESTA PARA TABLERO EJECUTIVO
# ============================================================================
# Implementa TAREA 2 y TAREA 5 del requerimiento P0
# Separa data_status, live_status y cache_status

# Constantes de estado
class DataStatus:
    DATA_OK = "DATA_OK"
    DATA_FROM_CACHE = "DATA_FROM_CACHE"
    NO_DATA_CONFIRMED = "NO_DATA_CONFIRMED"
    DATA_ERROR = "DATA_ERROR"
    LOADING = "LOADING"

class LiveStatus:
    LIVE_CONNECTED = "LIVE_CONNECTED"
    LIVE_UNREACHABLE_PREVIEW_ENV = "LIVE_UNREACHABLE_PREVIEW_ENV"
    LIVE_UNREACHABLE_REAL = "LIVE_UNREACHABLE_REAL"
    LIVE_API_UNREACHABLE = "LIVE_API_UNREACHABLE"
    LIVE_NOT_APPLICABLE = "LIVE_NOT_APPLICABLE"
    LIVE_UNKNOWN = "LIVE_UNKNOWN"

class CacheStatus:
    NOT_USED = "NOT_USED"
    USED_CONNECTION_FALLBACK = "USED_CONNECTION_FALLBACK"
    AVAILABLE_NOT_USED = "AVAILABLE_NOT_USED"
    STALE = "STALE"
    INVALID = "INVALID"
    MISSING = "MISSING"

class SourceUsed:
    REAL_SOURCE = "REAL_SOURCE"
    CACHE = "CACHE"
    NONE = "NONE"

class SourceRealStatus:
    SUCCESS = "SUCCESS"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    TIMEOUT = "TIMEOUT"
    API_UNREACHABLE = "API_UNREACHABLE"
    QUERY_ERROR = "QUERY_ERROR"
    MAPPING_ERROR = "MAPPING_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    SCHEMA_ERROR = "SCHEMA_ERROR"

def build_unit_response(
    server: Dict,
    kpis: Optional[Dict] = None,
    data_status: str = DataStatus.DATA_OK,
    live_status: str = LiveStatus.LIVE_CONNECTED,
    cache_status: str = CacheStatus.NOT_USED,
    source_used: str = SourceUsed.REAL_SOURCE,
    source_real_attempted: bool = True,
    source_real_status: str = SourceRealStatus.SUCCESS,
    source_period: str = "SQL",
    source_live: str = "TEMPCHEQUES",
    cache_warning: Optional[str] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    sucursal: Optional[str] = None,
) -> Dict:
    """
    Construye la respuesta estándar de una unidad para el Tablero Ejecutivo.
    Implementa TAREA 5 del requerimiento P0.
    
    CAMBIO C (Junio 2026):
    - Extrae unidad_negocio_codigo y unidad_negocio_nombre de kpis
    - FUENTE MAESTRA: Unidades_Negocio (EDARSAHUB)
    - NO usa MongoDB servers.name como nombre oficial
    - Retorna unidad_negocio_codigo para que el frontend cruce por código canónico
    """
    now = datetime.now(timezone.utc).isoformat()
    
    # Generar unidad_key canónica
    server_id = server.get('id', '')
    server_name = server.get('name', '')
    
    # =========================================================================
    # CAMBIO C: Extraer código y nombre canónico desde kpis (que viene de EDARSAHUB)
    # FUENTE MAESTRA: Unidades_Negocio.codigo y Unidades_Negocio.nombre
    # NO usar MongoDB servers.name como nombre funcional/oficial
    # =========================================================================
    unidad_negocio_codigo = kpis.get('unidad_negocio_codigo', '') if kpis else ''
    unidad_negocio_nombre = kpis.get('unidad_negocio_nombre', '') if kpis else ''
    
    # Usar nombre canónico de EDARSAHUB para los campos unidad/nombre
    # Prioridad: 1) nombre canónico EDARSAHUB, 2) sucursal param, 3) server.name (legacy)
    nombre_oficial = unidad_negocio_nombre or sucursal or server_name
    
    unidad_key = f"{server_id}:{unidad_negocio_codigo or sucursal or 'default'}"
    
    # Determinar connection_type basado en system_type
    system_type = server.get('system_type', 'UNKNOWN')
    if system_type.upper() in ['MPRO', 'MANAGEMENTPRO']:
        connection_type = "LOCAL_API"
    elif system_type.upper() in ['SOFTRESTAURANT', 'SR']:
        connection_type = "SQL_SERVER"
    else:
        connection_type = "UNKNOWN"
    
    # Compatibilidad: mantener campo "status" para frontend actual
    # Mapear data_status a status legacy
    if data_status == DataStatus.DATA_OK:
        legacy_status = "online"
    elif data_status == DataStatus.DATA_FROM_CACHE:
        legacy_status = "offline"  # Cache = offline visualmente para compatibilidad
    elif data_status == DataStatus.DATA_ERROR:
        legacy_status = "error"
    else:
        legacy_status = "no_data"
    
    response = {
        # Identificadores - CAMBIO C: Usar código canónico de EDARSAHUB
        "unidad_key": unidad_key,
        "unidad_negocio_id": unidad_negocio_codigo or server_id,  # Código canónico, no server_id
        "unidad_negocio_codigo": unidad_negocio_codigo,  # NUEVO: Código canónico oficial
        "unidad_negocio_nombre": unidad_negocio_nombre,  # NUEVO: Nombre oficial EDARSAHUB
        "server_id": server_id,  # Mantener server_id solo como identificador técnico
        "unidad": nombre_oficial,  # Usar nombre canónico de EDARSAHUB
        "nombre": nombre_oficial,  # Usar nombre canónico de EDARSAHUB
        
        # Tipo de sistema
        "system_type": system_type,
        "connection_type": connection_type,
        
        # Estados separados (P0 TAREA 2)
        "data_status": data_status,
        "live_status": live_status,
        "cache_status": cache_status,
        
        # Información de fuente (P0 TAREA 5)
        "source_used": source_used,
        "source_real_attempted": source_real_attempted,
        "source_real_status": source_real_status,
        "source_period": source_period,
        "source_live": source_live,
        
        # Timestamps
        "last_data_refresh_at": now,
        "last_live_check_at": now if live_status == LiveStatus.LIVE_CONNECTED else None,
        "status_ttl_seconds": 120,
        "updated_at": now,
        
        # KPIs - Solo incluir si hay datos válidos
        "ventas": kpis.get('ventas', 0) if kpis else None,
        "ventas_ant": kpis.get('ventas_ant', 0) if kpis else None,
        "ventas_año": kpis.get('ventas_año', 0) if kpis else None,
        "pax": kpis.get('pax', 0) if kpis else None,
        "pax_ant": kpis.get('pax_ant', 0) if kpis else None,
        "pax_año": kpis.get('pax_año', 0) if kpis else None,
        "cheques": kpis.get('cheques', 0) if kpis else None,
        "cheques_ant": kpis.get('cheques_ant', 0) if kpis else None,
        "cheques_año": kpis.get('cheques_año', 0) if kpis else None,
        "ticket_prom": kpis.get('ticket_prom', 0) if kpis else None,
        "proyeccion": kpis.get('proyeccion', 0) if kpis else None,
        
        # Variaciones
        "var_vs_mes_ant": kpis.get('var_vs_mes_ant', 0) if kpis else None,
        "var_vs_año_ant": kpis.get('var_vs_año_ant', 0) if kpis else None,
        
        # Advertencias y errores
        "cache_warning": cache_warning,
        "error_code": error_code,
        "error_message": error_message,
        
        # Compatibilidad con frontend actual
        "status": legacy_status,
        "source_status": source_real_status if source_used == SourceUsed.REAL_SOURCE else "FALLBACK",
        "config_origin": "EDARSAHUB_SQL",
    }
    
    # Copiar campos adicionales de kpis si existen
    if kpis:
        for key in ['pendiente_cerrar', 'tickets_abiertos', 'fallback_from', 'message', 'origen']:
            if key in kpis:
                response[key] = kpis[key]
    
    return response


def classify_connection_error(error: Exception, server: Dict) -> tuple:
    """
    Clasifica el error de conexión para determinar live_status y source_real_status.
    """
    error_str = str(error).lower()
    
    # Errores de conexión de red
    if any(x in error_str for x in ['connection refused', 'network', 'unreachable', 'timeout', 'timed out']):
        # Detectar si es ambiente Preview (DDNS no accesible)
        host = server.get('host', '')
        if 'ddns' in host.lower() or any(p in host for p in [',6669', ',6969', ',6668']):
            return LiveStatus.LIVE_UNREACHABLE_PREVIEW_ENV, SourceRealStatus.CONNECTION_ERROR
        return LiveStatus.LIVE_UNREACHABLE_REAL, SourceRealStatus.CONNECTION_ERROR
    
    # Errores de timeout
    if 'timeout' in error_str:
        return LiveStatus.LIVE_UNREACHABLE_REAL, SourceRealStatus.TIMEOUT
    
    # Errores de API
    if any(x in error_str for x in ['api', 'http', '500', '502', '503', '504']):
        return LiveStatus.LIVE_API_UNREACHABLE, SourceRealStatus.API_UNREACHABLE
    
    # Errores de query/schema
    if any(x in error_str for x in ['invalid object', 'column', 'syntax', 'permission']):
        return LiveStatus.LIVE_CONNECTED, SourceRealStatus.QUERY_ERROR  # Conectado pero error de query
    
    # Error desconocido
    return LiveStatus.LIVE_UNKNOWN, SourceRealStatus.CONNECTION_ERROR


# ============================================================================
# OBTENER DATOS BÁSICOS
# ============================================================================

async def obtener_sucursales_servidor(server_id: str) -> List[Dict]:
    """
    Obtiene las sucursales de un servidor.
    """
    server = await repo.get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    return server.get('sucursales', [])


async def obtener_metas(server_id: str, sucursal: str, mes: int, anio: int) -> Dict:
    """
    Obtiene las metas de una sucursal.
    """
    metas = await repo.get_metas_sucursal(server_id, sucursal, mes, anio)
    return metas or {"meta_ventas": 0, "meta_pax": 0, "meta_cheques": 0}


async def guardar_metas(server_id: str, sucursal: str, mes: int, anio: int, metas: Dict) -> Dict:
    """
    Guarda las metas de una sucursal.
    """
    await repo.save_metas_sucursal(server_id, sucursal, mes, anio, metas)
    return {"message": "Metas guardadas correctamente"}


# ============================================================================
# HELPERS DEL TABLERO EJECUTIVO - MIGRADOS FASE 5B-2 (Abril 2026)
# ============================================================================
# ACTUALIZACIÓN MAYO 2026 - MIGRACIÓN A EDARSAHUB:
# Estas funciones ahora leen EXCLUSIVAMENTE de EDARSAHUB SQL Server.
# - Fuente: Comercial_KPIs_Diarios_v2
# - NO consultan servidores locales para KPIs del Tablero Ejecutivo
# - NO consultan MongoDB como fuente de datos
# MÁXIMA: EDARSAHUB es el cerebro del sistema.

def get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia=False):
    """
    TABLERO EJECUTIVO - KPIs SoftRestaurant desde EDARSAHUB
    =======================================================
    
    ACTUALIZACIÓN MAYO 2026:
    - Lee EXCLUSIVAMENTE de EDARSAHUB (Comercial_KPIs_Diarios_v2)
    - NO consulta servidores SQL locales para históricos
    - NO consulta MongoDB
    
    ACTUALIZACIÓN JUNIO 2026:
    - Obtiene nombre y código canónico desde Unidades_Negocio (EDARSAHUB)
    - NO usa MongoDB servers.name como nombre oficial
    - Retorna unidad_negocio_codigo y unidad_negocio_nombre en el payload
    
    Para solo_ventas_dia=True:
    - Lee de Comercial_Ventas_Dia_Abiertas_v2 en EDARSAHUB
    
    Mantiene la misma firma y estructura de respuesta para compatibilidad.
    """
    server_id = server.get('id', '')
    
    # =========================================================================
    # CAMBIO A: Obtener datos canónicos desde Unidades_Negocio (EDARSAHUB)
    # FUENTE MAESTRA: Unidades_Negocio.codigo y Unidades_Negocio.nombre
    # NO usar MongoDB servers.name como nombre oficial
    # =========================================================================
    unidad_edarsahub = obtener_unidad_negocio_edarsahub(server_id, sucursal=None)
    unidad_negocio_codigo = unidad_edarsahub.get('codigo', '')
    unidad_negocio_nombre = unidad_edarsahub.get('nombre', '')
    sucursal_id = unidad_edarsahub.get('sucursal_origen_id', '') or 'DEFAULT'
    
    # Usar nombre canónico de EDARSAHUB, fallback a server.name solo si no existe
    nombre = unidad_negocio_nombre or server.get('name', 'SoftRestaurant')
    
    if not unidad_negocio_codigo:
        logging.warning(f"[TABLERO-EDARSAHUB] server_id {server_id} no encontrado en Unidades_Negocio EDARSAHUB")
        return None
    
    # Mapear código canónico a unidad_negocio_id usado en Comercial_KPIs_Diarios_v2
    # NOTA: La tabla usa formatos como "130-MER", "CIENFUEGOS", etc.
    unidad_negocio_id_map = {
        '130MID': '130-MER',
        'CIENFUEGOS': 'CIENFUEGOS',
        'ESTELAR': 'LA-ESTELAR',
        '130QRO': '130-QRO',
        'ORIGEN': 'ORIGEN'
    }
    unidad_negocio_id = unidad_negocio_id_map.get(unidad_negocio_codigo, unidad_negocio_codigo)
    
    logging.info(f"[TABLERO-EDARSAHUB] {nombre}: Iniciando consulta - unidad={unidad_negocio_id}, sucursal={sucursal_id}")
    
    # ============================================================================
    # MODO VENTAS DEL DÍA: Leer de Comercial_Ventas_Dia_Abiertas_v2
    # ============================================================================
    if solo_ventas_dia:
        logging.info(f"[TABLERO-EDARSAHUB] {nombre}: Modo Ventas del Día - consultando snapshot EDARSAHUB")
        
        ventas_abiertas = _get_ventas_abiertas_edarsahub(server_id, sucursal_id)
        
        if ventas_abiertas['existe']:
            ventas = ventas_abiertas['ventas']
            pax = ventas_abiertas['pax']
            cheques = ventas_abiertas['cheques']
            
            if pax == 0 and cheques > 0:
                pax = cheques
            
            ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
            cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
            
            return {
                "ventas": ventas,
                "ventas_ant": 0,
                "ventas_año": 0,
                "var_vs_mes_ant": 0,
                "var_vs_año_ant": 0,
                "proyeccion": 0,
                "pax": pax,
                "pax_ant": 0,
                "pax_año": 0,
                "var_pax_mes": 0,
                "var_pax_año": 0,
                "cheques": cheques,
                "cheques_ant": 0,
                "cheques_año": 0,
                "var_cheques_mes": 0,
                "var_cheques_año": 0,
                "ticket_prom": ticket_prom,
                "cheque_prom": cheque_prom,
                "es_ventas_dia": True,
                "origen": "EDARSAHUB_snapshot",
                "fuente": "EDARSAHUB",
                # CAMBIO A: Campos canónicos desde Unidades_Negocio EDARSAHUB
                "unidad_negocio_codigo": unidad_negocio_codigo,
                "unidad_negocio_nombre": unidad_negocio_nombre,
            }
        else:
            logging.warning(f"[TABLERO-EDARSAHUB] {nombre}: Sin snapshot de ventas abiertas disponible")
            return None
    
    # ============================================================================
    # MODO KPIs HISTÓRICOS/ACUMULADOS: Leer de Comercial_KPIs_Diarios_v2
    # ============================================================================
    
    # VALIDACIÓN DE RANGO DE FECHAS
    if not is_valid_range(fecha_ini, fecha_fin):
        logging.error(f"[TABLERO-EDARSAHUB] {nombre}: Rango de fechas inválido ({fecha_ini} > {fecha_fin})")
        return None
    
    # Obtener KPIs desde EDARSAHUB
    kpis = _obtener_kpis_tablero_desde_edarsahub(
        server_id=server_id,
        unidad_negocio_id=unidad_negocio_id,
        sucursal_id=sucursal_id,
        fecha_ini=fecha_ini,
        fecha_fin=fecha_fin,
        dias_mes=dias_mes,
        nombre_unidad=nombre
    )
    
    if kpis is None:
        logging.warning(f"[TABLERO-EDARSAHUB] {nombre}: Sin datos disponibles en EDARSAHUB")
        return None
    
    # CAMBIO A: Agregar campos canónicos desde Unidades_Negocio EDARSAHUB
    kpis['unidad_negocio_codigo'] = unidad_negocio_codigo
    kpis['unidad_negocio_nombre'] = unidad_negocio_nombre
    
    return kpis


def get_kpis_mpro(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes):
    """
    TABLERO EJECUTIVO - KPIs MPRO desde EDARSAHUB
    ==============================================
    
    ACTUALIZACIÓN MAYO 2026:
    - Lee EXCLUSIVAMENTE de EDARSAHUB (Comercial_KPIs_Diarios_v2)
    - NO consulta servidores SQL locales para históricos
    - NO consulta MongoDB
    
    NOTA: MPRO tiene múltiples sucursales (0021 = 130° QUERETARO, 0023 = ORIGEN).
    Esta función consolida todas las sucursales del servidor.
    Para KPIs por sucursal individual, usar get_kpis_mpro_por_sucursal.
    
    Mantiene la misma firma y estructura de respuesta para compatibilidad.
    """
    server_id = server.get('id', '')
    nombre = server.get('name', 'MPRO')
    
    # Obtener configuración de unidades MPRO
    mpro_config = UNIDADES_EDARSAHUB_MAP.get(server_id, {})
    
    if not mpro_config or 'sucursales' not in mpro_config:
        logging.warning(f"[TABLERO-EDARSAHUB] {nombre}: server_id {server_id} no tiene mapeo de unidad MPRO")
        return None
    
    sucursales = mpro_config.get('sucursales', {})
    
    logging.info(f"[TABLERO-EDARSAHUB] {nombre}: Iniciando consulta consolidada de {len(sucursales)} sucursales desde EDARSAHUB")
    
    # VALIDACIÓN DE RANGO DE FECHAS
    if not is_valid_range(fecha_ini, fecha_fin):
        logging.error(f"[TABLERO-EDARSAHUB] {nombre}: Rango de fechas inválido ({fecha_ini} > {fecha_fin})")
        return None
    
    # Agregar KPIs de todas las sucursales MPRO
    ventas_total = 0
    pax_total = 0
    cheques_total = 0
    ventas_ant_total = 0
    pax_ant_total = 0
    cheques_ant_total = 0
    ventas_año_total = 0
    pax_año_total = 0
    cheques_año_total = 0
    sucursales_con_datos = 0
    tiene_datos_mes_ant = False
    tiene_datos_anio_ant = False
    
    for sucursal_id, sucursal_config in sucursales.items():
        unidad_negocio_id = sucursal_config.get('unidad_negocio_id', '')
        nombre_sucursal = sucursal_config.get('nombre', sucursal_id)
        
        kpis = _obtener_kpis_tablero_desde_edarsahub(
            server_id=server_id,
            unidad_negocio_id=unidad_negocio_id,
            sucursal_id=sucursal_id,
            fecha_ini=fecha_ini,
            fecha_fin=fecha_fin,
            dias_mes=dias_mes,
            nombre_unidad=nombre_sucursal
        )
        
        if kpis:
            sucursales_con_datos += 1
            ventas_total += kpis.get('ventas', 0)
            pax_total += kpis.get('pax', 0)
            cheques_total += kpis.get('cheques', 0)
            
            # Comparativos mes anterior
            if kpis.get('_meta', {}).get('tiene_datos_mes_ant', False):
                tiene_datos_mes_ant = True
                ventas_ant_total += kpis.get('ventas_ant', 0)
                pax_ant_total += kpis.get('pax_ant', 0)
                cheques_ant_total += kpis.get('cheques_ant', 0)
            
            # Comparativos año anterior
            if kpis.get('_meta', {}).get('tiene_datos_anio_ant', False):
                tiene_datos_anio_ant = True
                ventas_año_total += kpis.get('ventas_año', 0)
                pax_año_total += kpis.get('pax_año', 0)
                cheques_año_total += kpis.get('cheques_año', 0)
    
    if sucursales_con_datos == 0:
        logging.warning(f"[TABLERO-EDARSAHUB] {nombre}: Sin datos en ninguna sucursal")
        return None
    
    # Calcular métricas derivadas
    ticket_prom = round(ventas_total / pax_total, 2) if pax_total > 0 else 0
    cheque_prom = round(ventas_total / cheques_total, 2) if cheques_total > 0 else 0
    
    # Proyección (calculamos días transcurridos basado en el último día con datos)
    fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
    fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
    dias_transcurridos_calc = (fecha_fin_dt - fecha_ini_dt).days + 1
    proyeccion = round((ventas_total / dias_transcurridos_calc) * dias_mes, 2) if dias_transcurridos_calc > 0 else 0
    
    # Variaciones (respetando reglas de null)
    var_vs_mes_ant = _calcular_variacion_pct(ventas_total, ventas_ant_total if tiene_datos_mes_ant else None)
    var_vs_año_ant = _calcular_variacion_pct(ventas_total, ventas_año_total if tiene_datos_anio_ant else None)
    var_pax_mes = _calcular_variacion_pct(pax_total, pax_ant_total if tiene_datos_mes_ant else None)
    var_pax_año = _calcular_variacion_pct(pax_total, pax_año_total if tiene_datos_anio_ant else None)
    var_cheques_mes = _calcular_variacion_pct(cheques_total, cheques_ant_total if tiene_datos_mes_ant else None)
    var_cheques_año = _calcular_variacion_pct(cheques_total, cheques_año_total if tiene_datos_anio_ant else None)
    
    logging.info(f"[TABLERO-EDARSAHUB] {nombre}: Consolidado ${ventas_total:,.0f}, vs Mes Ant={var_vs_mes_ant}%, vs Año Ant={var_vs_año_ant}%")
    
    return {
        "ventas": ventas_total,
        "ventas_ant": ventas_ant_total if tiene_datos_mes_ant else 0,
        "ventas_año": ventas_año_total if tiene_datos_anio_ant else 0,
        "var_vs_mes_ant": var_vs_mes_ant if var_vs_mes_ant is not None else 0,
        "var_vs_año_ant": var_vs_año_ant if var_vs_año_ant is not None else 0,
        "proyeccion": proyeccion,
        "pax": pax_total,
        "pax_ant": pax_ant_total if tiene_datos_mes_ant else 0,
        "pax_año": pax_año_total if tiene_datos_anio_ant else 0,
        "var_pax_mes": var_pax_mes if var_pax_mes is not None else 0,
        "var_pax_año": var_pax_año if var_pax_año is not None else 0,
        "cheques": cheques_total,
        "cheques_ant": cheques_ant_total if tiene_datos_mes_ant else 0,
        "cheques_año": cheques_año_total if tiene_datos_anio_ant else 0,
        "var_cheques_mes": var_cheques_mes if var_cheques_mes is not None else 0,
        "var_cheques_año": var_cheques_año if var_cheques_año is not None else 0,
        "ticket_prom": ticket_prom,
        "cheque_prom": cheque_prom,
        "fuente": "EDARSAHUB",
        "_meta": {
            "sucursales_consolidadas": sucursales_con_datos,
            "tiene_datos_mes_ant": tiene_datos_mes_ant,
            "tiene_datos_anio_ant": tiene_datos_anio_ant
        }
    }


def get_kpis_mpro_por_sucursal(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia=False):
    """
    Query para MPRO que devuelve KPIs DIVIDIDOS POR SUCURSAL (como en Inventarios).
    Retorna una lista de unidades, no un solo bloque.
    
    FASE 3.1 - COMPORTAMIENTO:
    - solo_ventas_dia=True → Intenta API local. Si falla, usa SQL nube (ventas acumuladas sin ventas del día)
    - solo_ventas_dia=False → Usa SQL nube del menú Servidores
    
    NOTA: Si API local no responde, se muestran ventas acumuladas.
    PENDIENTE: Inspección local en servidores para revisar por qué no levanta SQL local o API local.
    """
    
    logging.debug(f"MPRO {server['name']}: solo_ventas_dia={solo_ventas_dia}, fecha_ini={fecha_ini}, fecha_fin={fecha_fin}")
    
    # ============================================================================
    # VENTAS DEL DÍA: Intentar API local primero
    # ============================================================================
    if solo_ventas_dia:
        logging.info(f"MPRO {server['name']}: Modo Ventas del Día - intentando API local")
        
        # NOTA: sumar_ventas_api_local_a_sucursal se importa globalmente en la línea 29
        from datetime import datetime as dt_local
        
        hoy = dt_local.now()
        
        # Mapeo de sucursales MPRO conocidas para buscar en APIs locales
        # IMPORTANTE: Los nombres deben coincidir EXACTAMENTE con server_sucursales_config
        sucursales_mpro = [
            {"nombre": "ORIGEN", "sucursal_id": "ORIGEN", "api_key": "origen"},
            {"nombre": "130° QUERETARO", "sucursal_id": "130_QRO", "api_key": "130_qro"},
        ]
        
        unidades = []
        api_local_funciono = False
        
        for suc in sucursales_mpro:
            try:
                ventas_api = sumar_ventas_api_local_a_sucursal(
                    server_host=server['host'],
                    sucursal_nombre=suc['nombre'],
                    fecha_fin=fecha_fin,
                    mes_solicitado=hoy.month,
                    anio_solicitado=hoy.year,
                    solo_ventas_dia=True
                )
                
                if ventas_api.get("aplicado", False) and ventas_api.get("ventas", 0) > 0:
                    # Solo contar como éxito si realmente hay ventas
                    api_local_funciono = True
                    ventas = ventas_api.get("ventas", 0)
                    cheques = ventas_api.get("cheques", 0)
                    pax = ventas_api.get("pax", 0) or cheques
                    
                    ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
                    cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
                    
                    # CAMBIO B: Obtener código canónico desde EDARSAHUB
                    codigo_canonico, nombre_canonico = _obtener_codigo_canonico_mpro(
                        server['id'], suc['sucursal_id'], suc['nombre']
                    )
                    
                    unidades.append({
                        "unidad": nombre_canonico,  # Usar nombre canónico de EDARSAHUB
                        "server_id": server['id'],
                        "system_type": "MPRO",
                        "ventas": ventas,
                        "ventas_ant": 0,
                        "ventas_año": 0,
                        "var_vs_mes_ant": 0,
                        "var_vs_año_ant": 0,
                        "proyeccion": 0,
                        "pax": pax,
                        "pax_ant": 0,
                        "pax_año": 0,
                        "var_pax_mes": 0,
                        "var_pax_año": 0,
                        "cheques": cheques,
                        "cheques_ant": 0,
                        "cheques_año": 0,
                        "var_cheques_mes": 0,
                        "var_cheques_año": 0,
                        "ticket_prom": ticket_prom,
                        "cheque_prom": cheque_prom,
                        "es_ventas_dia": True,
                        "origen": "api_local",
                        # CAMBIO B: Campos canónicos desde Unidades_Negocio EDARSAHUB
                        "unidad_negocio_codigo": codigo_canonico,
                        "unidad_negocio_nombre": nombre_canonico,
                    })
                    logging.info(f"MPRO {server['name']} - {suc['nombre']}: API local OK - ${ventas:,.2f}")
            except Exception as e:
                logging.warning(f"MPRO {server['name']} - {suc['nombre']}: API local error - {e}")
        
        if api_local_funciono and unidades:
            return unidades
        
        # ============================================================================
        # API LOCAL FALLÓ EN MODO VENTAS DEL DÍA
        # ============================================================================
        # REGLA: Si es "ventas del día" y la API local no funciona,
        # Mostrar las sucursales con source_status="NO_DATA" para que el usuario
        # sepa que existen pero no hay conexión.
        logging.warning(f"MPRO {server['name']}: API local no disponible - mostrando sucursales como offline")
        
        unidades_offline = []
        for suc in sucursales_mpro:
            # CAMBIO B: Obtener código canónico desde EDARSAHUB
            codigo_canonico, nombre_canonico = _obtener_codigo_canonico_mpro(
                server['id'], suc['sucursal_id'], suc['nombre']
            )
            
            unidades_offline.append({
                "unidad": nombre_canonico,  # Usar nombre canónico de EDARSAHUB
                "server_id": server['id'],
                "system_type": "MPRO",
                "ventas": 0,
                "ventas_ant": 0,
                "ventas_año": 0,
                "var_vs_mes_ant": 0,
                "var_vs_año_ant": 0,
                "proyeccion": 0,
                "pax": 0,
                "pax_ant": 0,
                "pax_año": 0,
                "var_pax_mes": 0,
                "var_pax_año": 0,
                "cheques": 0,
                "cheques_ant": 0,
                "cheques_año": 0,
                "var_cheques_mes": 0,
                "var_cheques_año": 0,
                "ticket_prom": 0,
                "cheque_prom": 0,
                "es_ventas_dia": True,
                "origen": "api_local",
                "status": "offline",
                "source_status": "NO_DATA",
                "message": "API local no disponible - Sin datos de ventas del día",
                # CAMBIO B: Campos canónicos desde Unidades_Negocio EDARSAHUB
                "unidad_negocio_codigo": codigo_canonico,
                "unidad_negocio_nombre": nombre_canonico,
            })
        return unidades_offline
    
    # ============================================================================
    # VENTAS HISTÓRICAS / ACUMULADAS: Usar SQL nube del menú Servidores
    # (Solo se ejecuta si solo_ventas_dia=False)
    # ============================================================================
    
    # VALIDACIÓN DE CONEXIÓN: Verificar que el servidor SQL responde
    logging.info(f"[TABLERO] MPRO {server['name']}: Iniciando consulta SQL - Host={server['host']}:{server['port']}, DB={server['database']}")
    
    # VALIDACIÓN DE RANGO DE FECHAS (FIX ESTRUCTURAL)
    # Usar helper centralizado para evitar rangos inválidos
    if not is_valid_range(fecha_ini, fecha_fin):
        logging.error(f"MPRO {server['name']}: Rango de fechas inválido ({fecha_ini} > {fecha_fin})")
        return []
    
    # Formato YYYYMMDD para MPRO (SQL Server con configuración regional español)
    try:
        fi, ff = to_yyyymmdd_range(fecha_ini, fecha_fin)
    except ValueError as e:
        logging.error(f"MPRO {server['name']}: Error convirtiendo fechas: {e}")
        return []
    
    logging.info(f"[TABLERO] MPRO {server['name']}: Conexión OK - Fechas: {fecha_ini} a {fecha_fin}")
    
    # Extraer mes y año de fecha_fin para usarlos en recálculos (importante para multiselección de meses)
    mes_final = int(fecha_fin[5:7])  # Mes de fecha_fin (ej: 04 para abril)
    anio_final = int(fecha_fin[:4])  # Año de fecha_fin
    
    # PASO 1: Detectar el último día real con ventas en el período
    query_ultimo_dia = f"""
SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
FROM Venta_Encabezado VE
WHERE VE.Vn_Fecha >= '{fi}' AND VE.Vn_Fecha <= '{ff}'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""
    try:
        result_ultimo = execute_sql_query(server['host'], server['port'], server['database'], 
                                          server['username'], server['password'], query_ultimo_dia)
        if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
            ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
            if isinstance(ultimo_dia_venta, str):
                # Parsear la fecha completa (YYYY-MM-DD)
                partes = ultimo_dia_venta.split('-') if '-' in ultimo_dia_venta else None
                if partes and len(partes) == 3:
                    anio_ultimo = int(partes[0])
                    mes_ultimo = int(partes[1])
                    dia_con_datos = int(partes[2])
                else:
                    dia_con_datos = int(ultimo_dia_venta[-2:])
                    mes_ultimo = mes_final
                    anio_ultimo = anio_final
            else:
                dia_con_datos = ultimo_dia_venta.day
                mes_ultimo = ultimo_dia_venta.month
                anio_ultimo = ultimo_dia_venta.year
            
            logging.debug(f"MPRO por sucursal {server['name']} - Ultimo dia con ventas: {anio_ultimo}-{mes_ultimo:02d}-{dia_con_datos:02d}")
            
            # CORRECCIÓN: Usar el mes y año del último día con ventas, no del mes inicial
            ff = f"{anio_ultimo}{str(mes_ultimo).zfill(2)}{str(dia_con_datos).zfill(2)}"
            
            # Calcular días transcurridos desde fecha_ini hasta el último día con ventas
            fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
            fecha_ultimo_dt = datetime(anio_ultimo, mes_ultimo, dia_con_datos)
            dias_transcurridos = (fecha_ultimo_dt - fecha_ini_dt).days + 1
            
            logging.debug(f"MPRO por sucursal {server['name']} - Período ajustado: {fi} a {ff}, días: {dias_transcurridos}")
            
            # Recalcular fechas de comparación basadas en días reales
            mes_actual = mes_ultimo  # Usar el mes del último día con ventas
            anio_actual = anio_ultimo
            
            # Mes anterior
            if mes_actual == 1:
                mes_ant = 12
                anio_ant = anio_actual - 1
            else:
                mes_ant = mes_actual - 1
                anio_ant = anio_actual
            
            max_dia_mes_ant = calendar.monthrange(anio_ant, mes_ant)[1]
            dia_comparar = min(dia_con_datos, max_dia_mes_ant)
            fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
            fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
            
            # Año anterior - usar el RANGO completo de meses (desde mes_min hasta mes_max)
            mes_min = int(fecha_ini[5:7])
            anio_pasado = int(fecha_ini[:4]) - 1
            
            fecha_ini_año_ant = f"{anio_pasado}-{str(mes_min).zfill(2)}-01"
            
            max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_ultimo)[1]
            dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
            fecha_fin_año_ant = f"{anio_pasado}-{str(mes_ultimo).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
            
            logging.info(f"MPRO por sucursal Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
    except Exception as e:
        logging.warning(f"MPRO por sucursal Error detectando último día: {e}")
    
    fia = fecha_ini_ant.replace('-', '')
    ffa = fecha_fin_ant.replace('-', '')
    fiaa = fecha_ini_año_ant.replace('-', '')
    ffaa = fecha_fin_año_ant.replace('-', '')
    
    logging.info(f"MPRO {server['name']}: Consultando ventas del {fi} al {ff}")
    
    # BLOQUE 4: Migrado a query centralizada query_ventas_por_sucursal_mpro()
    # ORIGEN ANTERIOR: SQL directo líneas 862-875 (ahora en queries/mpro.py)
    result_principal = query_ventas_por_sucursal_mpro(server, fecha_ini, fecha_fin)
    
    if not result_principal.success:
        # FASE 4.4: Registrar como SOURCE_UNREACHABLE
        error_status = classify_sql_error(Exception(result_principal.error or "Error desconocido"))
        logging.warning(
            f"Error consultando MPRO por sucursal {server['name']}: {result_principal.error} "
            f"[Status: {error_status.value}]"
        )
        return []
    
    if not result_principal.sucursales:
        logging.warning(f"MPRO {server['name']}: No se encontraron sucursales con ventas")
        return []
    
    logging.info(f"MPRO {server['name']}: Query retornó {len(result_principal.sucursales)} sucursales")
    
    unidades = []
    
    for row in result_principal.sucursales:
        sucursal_id = row.get('sucursal_id', '')
        sucursal_nombre = row.get('sucursal_nombre', 'Sin nombre')
        ventas = float(row.get('ventas') or 0)
        cheques = int(row.get('cheques') or 0)
        pax = int(row.get('pax') or 0)  # PAX real desde Comanda.Co_Personas
        
        # Si PAX es 0 pero hay cheques, estimamos PAX = cheques (1 persona por ticket mínimo)
        if pax == 0 and cheques > 0:
            pax = cheques
        
        # PASO 2: Detectar el último día con ventas PARA ESTA SUCURSAL específica
        query_ultimo_dia_suc = f"""
SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
FROM Venta_Encabezado VE
WHERE VE.Sc_Cve_Sucursal = '{sucursal_id}'
  AND VE.Vn_Fecha >= '{fi}' AND VE.Vn_Fecha <= '{ff}'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""
        try:
            result_ultimo_suc = execute_sql_query(server['host'], server['port'], server['database'], 
                                                  server['username'], server['password'], query_ultimo_dia_suc)
            if result_ultimo_suc and result_ultimo_suc[0]['ultimo_dia_venta']:
                ultimo_dia_suc = result_ultimo_suc[0]['ultimo_dia_venta']
                if isinstance(ultimo_dia_suc, str):
                    dia_suc = int(ultimo_dia_suc.split('-')[2]) if '-' in ultimo_dia_suc else int(ultimo_dia_suc[-2:])
                else:
                    dia_suc = ultimo_dia_suc.day
                
                logging.debug(f"MPRO {sucursal_nombre} - Ultimo dia con ventas: dia {dia_suc}")
                
                # Recalcular fechas de comparación para esta sucursal
                mes_actual = int(fi[4:6])
                anio_actual = int(fi[:4])
                
                # Mes anterior
                if mes_actual == 1:
                    mes_ant = 12
                    anio_ant = anio_actual - 1
                else:
                    mes_ant = mes_actual - 1
                    anio_ant = anio_actual
                
                max_dia_mes_ant = calendar.monthrange(anio_ant, mes_ant)[1]
                dia_comparar = min(dia_suc, max_dia_mes_ant)
                fia_suc = f"{anio_ant}{str(mes_ant).zfill(2)}01"
                ffa_suc = f"{anio_ant}{str(mes_ant).zfill(2)}{str(dia_comparar).zfill(2)}"
                
                # Año anterior - CORRECCIÓN: Usar el RANGO COMPLETO de meses
                # fiaa y ffaa ya están calculadas correctamente a nivel global (desde mes_min hasta mes_max del año anterior)
                # Solo necesitamos ajustar ffaa al día correcto de esta sucursal específica
                anio_pasado = anio_actual - 1
                # Obtener el mes final del rango (mes del último día con ventas global)
                mes_final_rango = int(ffaa[4:6])  # ffaa tiene formato YYYYMMDD
                max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_final_rango)[1]
                dia_ano_ant = min(dia_suc, max_dia_ano_ant)
                # PRESERVAR el mes inicial de fiaa (rango completo desde enero o el mes inicial seleccionado)
                fiaa_suc = fiaa  # Ya tiene el formato correcto con mes inicial
                ffaa_suc = f"{anio_pasado}{str(mes_final_rango).zfill(2)}{str(dia_ano_ant).zfill(2)}"
            else:
                # Si no hay datos, usar fechas globales
                fia_suc, ffa_suc = fia, ffa
                fiaa_suc, ffaa_suc = fiaa, ffaa
                dia_suc = dias_transcurridos
        except Exception as e:
            logging.warning(f"Error detectando ultimo dia para {sucursal_nombre}: {e}")
            fia_suc, ffa_suc = fia, ffa
            fiaa_suc, ffaa_suc = fiaa, ffaa
            dia_suc = dias_transcurridos
        
        # Query mes anterior para esta sucursal - con PAX (formato seguro con CONVERT)
        query_ant = f"""
SELECT 
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas, 
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Sc_Cve_Sucursal = '{sucursal_id}'
  AND CONVERT(varchar, VE.Vn_Fecha, 112) >= '{fia_suc}' AND CONVERT(varchar, VE.Vn_Fecha, 112) <= '{ffa_suc}'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""
        try:
            r_ant = execute_sql_query(server['host'], server['port'], server['database'], 
                                      server['username'], server['password'], query_ant)
            ventas_ant = float(r_ant[0]['ventas'] or 0) if r_ant else 0
            cheques_ant = int(r_ant[0]['cheques'] or 0) if r_ant else 0
            pax_ant = int(r_ant[0]['pax'] or 0) if r_ant else 0
            if pax_ant == 0 and cheques_ant > 0:
                pax_ant = cheques_ant
        except Exception:
            ventas_ant, cheques_ant, pax_ant = 0, 0, 0
        
        # Query año anterior para esta sucursal - con PAX (formato seguro con CONVERT)
        query_año = f"""
SELECT 
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas, 
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Sc_Cve_Sucursal = '{sucursal_id}'
  AND CONVERT(varchar, VE.Vn_Fecha, 112) >= '{fiaa_suc}' AND CONVERT(varchar, VE.Vn_Fecha, 112) <= '{ffaa_suc}'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""
        try:
            r_año = execute_sql_query(server['host'], server['port'], server['database'], 
                                      server['username'], server['password'], query_año)
            ventas_año = float(r_año[0]['ventas'] or 0) if r_año else 0
            cheques_año = int(r_año[0]['cheques'] or 0) if r_año else 0
            pax_año = int(r_año[0]['pax'] or 0) if r_año else 0
            if pax_año == 0 and cheques_año > 0:
                pax_año = cheques_año
        except Exception:
            ventas_año, cheques_año, pax_año = 0, 0, 0
        
        # ============= INTEGRACIÓN API LOCAL =============
        # Sumar ventas del día desde API local si aplica
        # Solo se suma si: el período incluye HOY y estamos ANTES de la hora de réplica
        # En modo "Ventas del Día" (solo_ventas_dia=True): las ventas de API local REEMPLAZAN las de nube
        ventas_api_local = sumar_ventas_api_local_a_sucursal(
            server_host=server['host'],
            sucursal_nombre=sucursal_nombre,
            fecha_fin=fecha_fin,  # fecha_fin original en formato YYYY-MM-DD
            mes_solicitado=mes_final,
            anio_solicitado=anio_final,
            solo_ventas_dia=solo_ventas_dia  # Pasar flag para modo Ventas del Día
        )
        
        if ventas_api_local.get("aplicado", False):
            if ventas_api_local.get("reemplazar", False):
                # Modo "Ventas del Día": REEMPLAZAR datos de nube con API local
                # Si hay ventas reales en la API local, usar esas
                if ventas_api_local["ventas"] > 0 or ventas_api_local["cheques"] > 0:
                    ventas = ventas_api_local["ventas"]
                    cheques = ventas_api_local["cheques"]
                    pax = ventas_api_local["pax"]
                    logging.info(f"API Local REEMPLAZÓ datos de {sucursal_nombre}: ${ventas_api_local['ventas']:,.2f} de {ventas_api_local.get('api', 'N/A')}")
                else:
                    # API local retornó $0 - en modo Ventas del Día, usar $0 (no hay ventas hoy)
                    ventas = 0
                    cheques = 0
                    pax = 0
                    logging.info(f"API Local retornó $0 para {sucursal_nombre} - Ventas del día = $0")
            else:
                # Modo normal: SUMAR ventas de API local a las de nube
                ventas += ventas_api_local["ventas"]
                cheques += ventas_api_local["cheques"]
                pax += ventas_api_local["pax"]
                logging.info(f"API Local sumada a {sucursal_nombre}: +${ventas_api_local['ventas']:,.2f} de {ventas_api_local.get('api', 'N/A')}")
        elif solo_ventas_dia:
            # Modo "Ventas del Día" pero no hay API local configurada o no aplicó
            # Las ventas deben ser $0 (no mostrar el acumulado del mes)
            ventas = 0
            cheques = 0
            pax = 0
            logging.info(f"Modo Ventas del Día pero sin API local para {sucursal_nombre} - Ventas = $0")
        # Si no es modo ventas del día y no hay API local, mantener datos de la nube (ya asignados)
        # ============= FIN INTEGRACIÓN API LOCAL =============
        
        # Cálculos
        ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
        cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
        proyeccion = round((ventas / dias_transcurridos) * dias_mes, 2) if dias_transcurridos > 0 else 0
        
        # Variaciones %
        var_vs_mes_ant = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
        var_vs_año_ant = round(((ventas - ventas_año) / ventas_año * 100), 1) if ventas_año > 0 else 0
        
        logging.debug(f"MPRO {sucursal_nombre}: Dia={dia_suc}, Actual={ventas:.2f}, MesAnt({fia_suc}-{ffa_suc})={ventas_ant:.2f} -> {var_vs_mes_ant}%, AnoAnt({fiaa_suc}-{ffaa_suc})={ventas_año:.2f} -> {var_vs_año_ant}%")
        var_pax_mes = round(((pax - pax_ant) / pax_ant * 100), 1) if pax_ant > 0 else 0
        var_pax_año = round(((pax - pax_año) / pax_año * 100), 1) if pax_año > 0 else 0
        var_cheques_mes = round(((cheques - cheques_ant) / cheques_ant * 100), 1) if cheques_ant > 0 else 0
        var_cheques_año = round(((cheques - cheques_año) / cheques_año * 100), 1) if cheques_año > 0 else 0
        
        # CAMBIO B: Obtener código canónico desde EDARSAHUB
        codigo_canonico, nombre_canonico = _obtener_codigo_canonico_mpro(
            server['id'], sucursal_id, sucursal_nombre
        )
        
        unidades.append({
            "unidad": nombre_canonico,  # Usar nombre canónico de EDARSAHUB
            "sucursal": nombre_canonico,  # Para filtrar en endpoints de detalle
            "server_id": server['id'],
            "sucursal_id": sucursal_id,
            "system_type": "MPRO",
            "parent_server": server['name'],
            "ventas": ventas,
            "ventas_ant": ventas_ant,
            "ventas_año": ventas_año,
            "var_vs_mes_ant": var_vs_mes_ant,
            "var_vs_año_ant": var_vs_año_ant,
            "proyeccion": proyeccion,
            "pax": pax,
            "pax_ant": pax_ant,
            "pax_año": pax_año,
            "var_pax_mes": var_pax_mes,
            "var_pax_año": var_pax_año,
            "cheques": cheques,
            "cheques_ant": cheques_ant,
            "cheques_año": cheques_año,
            "var_cheques_mes": var_cheques_mes,
            "var_cheques_año": var_cheques_año,
            "ticket_prom": ticket_prom,
            "cheque_prom": cheque_prom,
            # CAMBIO B: Campos canónicos desde Unidades_Negocio EDARSAHUB
            "unidad_negocio_codigo": codigo_canonico,
            "unidad_negocio_nombre": nombre_canonico,
        })
        
        logging.info(f"MPRO {server['name']} - Sucursal '{sucursal_nombre}': Ventas={ventas}, Cheques={cheques}")
    
    return unidades


# ============================================================================
# FASE 4.4: FUNCIONES CON SourceQueryResult
# ============================================================================

def get_kpis_mpro_con_estado(
    server: Dict,
    fecha_ini: str,
    fecha_fin: str,
    solo_ventas_dia: bool = False
) -> Dict:
    """
    FASE 4.4: Obtiene KPIs de MPRO con envelope de estado.
    
    Distingue claramente:
    - SUCCESS_WITH_DATA: Consulta exitosa con ventas
    - SUCCESS_EMPTY: Consulta exitosa, sin ventas (cero real)
    - SOURCE_UNREACHABLE: Error de conexión (NUNCA se reporta como cero)
    
    Returns:
        Dict con:
        - data: Lista de unidades con KPIs
        - status: QueryStatus
        - query_executed: bool
        - error_message: str (si aplica)
    """
    import time
    start_time = time.time()
    
    try:
        # Llamar a la función existente
        unidades = get_kpis_mpro_por_sucursal(server, fecha_ini, fecha_fin, solo_ventas_dia)
        duration_ms = int((time.time() - start_time) * 1000)
        
        if unidades and len(unidades) > 0:
            return {
                "data": unidades,
                "status": QueryStatus.SUCCESS_WITH_DATA.value,
                "query_executed": True,
                "row_count": len(unidades),
                "duration_ms": duration_ms,
                "error_message": None
            }
        else:
            return {
                "data": [],
                "status": QueryStatus.SUCCESS_EMPTY.value,
                "query_executed": True,
                "row_count": 0,
                "duration_ms": duration_ms,
                "error_message": None
            }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_status = classify_sql_error(e)
        
        return {
            "data": [],
            "status": error_status.value,
            "query_executed": False,
            "row_count": 0,
            "duration_ms": duration_ms,
            "error_message": str(e)
        }


__all__ = [
    # Auxiliares
    'calcular_ticket_promedio',
    'calcular_consumo_promedio',
    'calcular_porcentaje_cumplimiento',
    # Procesamiento
    'procesar_ventas_sucursal',
    'agregar_totales',
    # Datos
    'obtener_sucursales_servidor',
    'obtener_metas',
    'guardar_metas',
    # Helpers del Tablero Ejecutivo (Migrados FASE 5B-2)
    'get_kpis_softrestaurant',
    'get_kpis_mpro',
    'get_kpis_mpro_por_sucursal',
    # FASE 4.4: Con SourceQueryResult
    'get_kpis_mpro_con_estado',
]
