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
from datetime import datetime, timezone, timedelta
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
from core.server_registry import resolve_unidad_by_server_sucursal

# BLOQUE 4: Import de queries centralizadas (Fase 1 Plan Migración)
from modules.comercial.queries.softrestaurant import query_ventas_periodo_sr
from modules.comercial.queries.mpro import query_ventas_periodo_mpro, query_ventas_por_sucursal_mpro

# ============================================================================
# FASE 5B: INTEGRACIÓN CON EmpresaResolver (Mayo 2026)
# ============================================================================
# Importar EmpresaResolver para resolución canónica
try:
    from core.empresa_resolver import (
        resolve_empresa_by_alias,
        resolve_empresa_by_id,
        get_connection_for_role,
        get_empresa_connections,
        get_system_branch_context,
        normalize_alias,
        EMPRESA_RESOLVER_AVAILABLE
    )
    _EMPRESA_RESOLVER_OK = True
except ImportError as e:
    logging.warning(f"[SERVICE] EmpresaResolver no disponible: {e}. Usando fallback legacy.")
    _EMPRESA_RESOLVER_OK = False
    EMPRESA_RESOLVER_AVAILABLE = False


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
    
    FASE 5B REFACTOR (Mayo 2026):
    - Usa EmpresaResolver como fuente primaria
    - Fallback a Unidades_Negocio (EDARSAHUB) si EmpresaResolver no resuelve
    - Fallback final hardcodeado solo si nada responde
    
    Args:
        server_id: ID del servidor MPRO
        sucursal_id: ID de la sucursal (ej: "0021", "0023")
        sucursal_nombre: Nombre visible de la sucursal (para fallback)
    
    Returns:
        Tuple (unidad_negocio_codigo, unidad_negocio_nombre)
    """
    # =========================================================================
    # FASE 5B: Intentar resolver con EmpresaResolver primero
    # =========================================================================
    if _EMPRESA_RESOLVER_OK and EMPRESA_RESOLVER_AVAILABLE:
        # Intentar resolver por nombre de sucursal
        empresa = resolve_empresa_by_alias(sucursal_nombre)
        if empresa:
            logging.debug(f"[SERVICE] _obtener_codigo_canonico_mpro: EmpresaResolver resolvió '{sucursal_nombre}' -> {empresa.codigo_empresa}")
            return empresa.codigo_empresa, empresa.nombre_comercial or empresa.codigo_empresa
        
        # Intentar resolver por código de sucursal (0021, 0023)
        # Los códigos MPRO deben estar en Sistema_EmpresasServidores
        try:
            # Buscar empresa por NumeroSucursalSistema
            from core.db import execute_sql_query
            query = f"""
            SELECT DISTINCT e.CodigoEmpresa, e.NombreComercial
            FROM Sistema_EmpresasServidores es
            JOIN Sistema_Empresas e ON es.EmpresaID = e.EmpresaID
            WHERE es.CodigoSucursalSistema = '{sucursal_id}'
              AND es.Activo = 1
              AND e.Activo = 1
            """
            from core.empresa_resolver import _execute_query
            rows = _execute_query(query)
            if rows:
                codigo = rows[0].get('CodigoEmpresa', '').strip()
                nombre = rows[0].get('NombreComercial', '').strip()
                if codigo:
                    logging.debug(f"[SERVICE] _obtener_codigo_canonico_mpro: Resuelto por CodigoSucursalSistema '{sucursal_id}' -> {codigo}")
                    return codigo, nombre
        except Exception as e:
            logging.warning(f"[SERVICE] Error buscando por CodigoSucursalSistema: {e}")
    
    # =========================================================================
    # Fallback: Buscar en Unidades_Negocio (EDARSAHUB)
    # =========================================================================
    unidad_edarsahub = obtener_unidad_negocio_edarsahub(server_id, sucursal=sucursal_id)
    
    codigo = unidad_edarsahub.get('codigo', '')
    nombre = unidad_edarsahub.get('nombre', '')
    
    if codigo and nombre:
        return codigo, nombre
    
    # =========================================================================
    # Fallback final: Mapeo hardcodeado (solo si nada responde)
    # NOTA: Este fallback se mantiene para resiliencia pero debe ser temporal
    # =========================================================================
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



def _mapear_codigo_a_unidad_negocio_id(codigo_empresa: str) -> str:
    """
    FIX IDENTIDAD CANÓNICA (2026-05-16):
    =====================================
    Esta función ahora retorna el CÓDIGO CANÓNICO sin traducción.
    
    REGLA DE NEGOCIO:
    - La identidad principal es unidad_negocio_id CANÓNICO (130MID, 130QRO, etc.)
    - Los aliases (130-MER, 130-QRO) son solo para compatibilidad de lectura histórica
    - NUNCA traducir el código canónico a un alias para ESCRITURA
    - Los datos en Comercial_KPIs_Diarios_v2 deben usar códigos canónicos
    
    CÓDIGOS CANÓNICOS OFICIALES (según Unidades_Negocio en EDARSAHUB):
    - 130MID (130° MÉRIDA)
    - 130QRO (130° QUERÉTARO)  
    - CIENFUEGOS
    - ESTELAR (LA ESTELAR)
    - ORIGEN
    
    Args:
        codigo_empresa: Código de empresa/unidad
    
    Returns:
        Código canónico SIN traducción a alias legacy
    """
    if not codigo_empresa:
        return codigo_empresa
    
    codigo_upper = codigo_empresa.upper().strip()
    
    # =========================================================================
    # FIX: Normalizar aliases LEGACY hacia códigos CANÓNICOS
    # NUNCA al revés (canónico -> legacy)
    # =========================================================================
    
    # Mapeo de aliases LEGACY hacia códigos CANÓNICOS
    # Esto permite que consultas con datos históricos que usan aliases
    # se resuelvan al código canónico correcto
    normalizacion_a_canonico = {
        # Mérida - todas las variantes resuelven a 130MID
        '130-MER': '130MID',
        '130-MID': '130MID',
        '130MER': '130MID',
        '130 MERIDA': '130MID',
        '130 MÉRIDA': '130MID',
        '130° MERIDA': '130MID',
        '130° MÉRIDA': '130MID',
        'MERIDA': '130MID',
        'MÉRIDA': '130MID',
        # Querétaro - todas las variantes resuelven a 130QRO
        '130-QRO': '130QRO',
        '130 QRO': '130QRO',
        '130 QUERETARO': '130QRO',
        '130 QUERÉTARO': '130QRO',
        '130° QUERETARO': '130QRO',
        '130° QUERÉTARO': '130QRO',
        'QUERETARO': '130QRO',
        'QUERÉTARO': '130QRO',
        # La Estelar
        'LA-ESTELAR': 'ESTELAR',
        'LA ESTELAR': 'ESTELAR',
        # Códigos canónicos (no cambiar)
        '130MID': '130MID',
        '130QRO': '130QRO',
        'CIENFUEGOS': 'CIENFUEGOS',
        'ESTELAR': 'ESTELAR',
        'ORIGEN': 'ORIGEN',
    }
    
    # Buscar en el mapa de normalización
    codigo_canonico = normalizacion_a_canonico.get(codigo_upper, codigo_upper)
    
    if codigo_canonico != codigo_upper:
        logging.info(f"[IDENTIDAD-CANONICA] Normalizado: '{codigo_empresa}' -> '{codigo_canonico}'")
    
    return codigo_canonico


def _obtener_sucursales_mpro_desde_resolver() -> List[Dict[str, Any]]:
    """
    FASE 5B HELPER: Obtiene la lista de sucursales MPRO desde EmpresaResolver.
    
    Lee de Sistema_EmpresasServidores las empresas que tienen conexión MPRO
    (RolConexion = PRINCIPAL_SQL o VENTAS_DIA_API_LOCAL) con NumeroSucursalSistema.
    
    Returns:
        Lista de dicts con: codigo, sucursal_id, server_id, empresa_id
    """
    sucursales = []
    
    # =========================================================================
    # FASE 5B: Intentar obtener desde EmpresaResolver
    # =========================================================================
    if _EMPRESA_RESOLVER_OK and EMPRESA_RESOLVER_AVAILABLE:
        try:
            from core.empresa_resolver import _execute_query
            
            # Buscar empresas con conexiones MPRO (tienen NumeroSucursalSistema)
            # Usar ROW_NUMBER para obtener solo una conexión por empresa, preferir VENTAS_DIA_API_LOCAL
            query = """
            WITH RankedConnections AS (
                SELECT 
                    e.EmpresaID,
                    e.CodigoEmpresa,
                    e.NombreComercial,
                    es.NumeroSucursalSistema,
                    es.CodigoSucursalSistema,
                    CONVERT(VARCHAR(36), es.ServidorID) as ServidorID,
                    sc.nombre as NombreServidor,
                    es.RolConexion,
                    ROW_NUMBER() OVER (
                        PARTITION BY e.EmpresaID 
                        ORDER BY 
                            CASE es.RolConexion 
                                WHEN 'VENTAS_DIA_API_LOCAL' THEN 1 
                                ELSE 2 
                            END
                    ) as rn
                FROM Sistema_EmpresasServidores es
                JOIN Sistema_Empresas e ON es.EmpresaID = e.EmpresaID
                JOIN Servidores_Conexiones sc ON es.ServidorID = sc.id
                WHERE es.NumeroSucursalSistema IS NOT NULL
                  AND es.RolConexion IN ('PRINCIPAL_SQL', 'VENTAS_DIA_API_LOCAL')
                  AND es.Activo = 1
                  AND e.Activo = 1
            )
            SELECT EmpresaID, CodigoEmpresa, NombreComercial, NumeroSucursalSistema,
                   CodigoSucursalSistema, ServidorID, NombreServidor, RolConexion
            FROM RankedConnections
            WHERE rn = 1
            ORDER BY EmpresaID
            """
            
            rows = _execute_query(query)
            
            for row in rows:
                codigo = row['CodigoEmpresa'].strip() if row['CodigoEmpresa'] else ''
                sucursal_id = row['CodigoSucursalSistema'].strip() if row['CodigoSucursalSistema'] else str(row['NumeroSucursalSistema'])
                server_id = row['ServidorID'].lower() if row['ServidorID'] else ''
                
                if codigo and sucursal_id and server_id:
                    sucursales.append({
                        "codigo": codigo,
                        "sucursal_id": sucursal_id,
                        "server_id": server_id,
                        "empresa_id": row['EmpresaID'],
                        "nombre_servidor": row['NombreServidor'],
                        "rol": row['RolConexion'],
                        "fuente": "EmpresaResolver"
                    })
            
            if sucursales:
                logging.info(f"[SERVICE] _obtener_sucursales_mpro_desde_resolver: {len(sucursales)} sucursales obtenidas via EmpresaResolver")
                return sucursales
                
        except Exception as e:
            logging.warning(f"[SERVICE] Error obteniendo sucursales MPRO desde EmpresaResolver: {e}")
    
    # =========================================================================
    # Fallback: Hardcodeado (temporal, para resiliencia)
    # =========================================================================
    logging.warning("[SERVICE] _obtener_sucursales_mpro_desde_resolver: Usando fallback hardcodeado")
    return [
        {
            "codigo": "ORIGEN",
            "sucursal_id": "0023",
            "server_id": "817a0aa8-6170-4738-a8f6-a72ac36ba0df",
            "empresa_id": 1,
            "fuente": "LEGACY_FALLBACK"
        },
        {
            "codigo": "130QRO",
            "sucursal_id": "0021",
            "server_id": "72f6e9a7-8ea2-4eb2-802e-4ee31753435e",
            "empresa_id": 2,
            "fuente": "LEGACY_FALLBACK"
        },
    ]



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
    sucursal_id: str = 'DEFAULT',
    unidad_negocio_id: str = None  # FIX: Agregar unidad_negocio_id como parámetro opcional
) -> Dict:
    """
    Obtiene KPIs agregados de Comercial_KPIs_Diarios_v2 para un período.
    
    FIX CIRCUIT BREAKER HUB (17-May-2026):
    - Si se proporciona unidad_negocio_id, filtrar por unidad_negocio_id + sucursal_id
    - Si no, usar server_id + sucursal_id (comportamiento legacy)
    
    RAZÓN: Para MPRO, los datos en Comercial_KPIs_Diarios_v2 tienen un server_id
    diferente al que está configurado en Servidores_Conexiones. Usar unidad_negocio_id
    es más confiable.
    
    Retorna:
        {
            'ventas': float,
            'pax': int,
            'cheques': int,
            'registros': int,
            'existe_data': bool
        }
    """
    # Determinar filtro a usar
    if unidad_negocio_id:
        # FIX: Usar unidad_negocio_id para MPRO
        filtro_principal = f"unidad_negocio_id = '{unidad_negocio_id}'"
        logging.info(f"[EDARSAHUB-QUERY] Usando unidad_negocio_id={unidad_negocio_id}, sucursal_id={sucursal_id}")
    else:
        # Legacy: Usar server_id
        filtro_principal = f"server_id = '{server_id}'"
    
    # Usar rangos semiabiertos: fecha >= ini AND fecha <= fin
    query = f"""
    SELECT 
        ISNULL(SUM(ventas_total), 0) as ventas,
        ISNULL(SUM(pax_total), 0) as pax_total,
        ISNULL(SUM(tickets_total), 0) as cheques,
        COUNT(*) as registros
    FROM Comercial_KPIs_Diarios_v2
    WHERE {filtro_principal}
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


def _get_ventas_abiertas_edarsahub(server_id: str, sucursal_id: str = 'DEFAULT', unidad_negocio_id: str = None) -> Dict:
    """
    Obtiene ventas abiertas del día desde Comercial_Ventas_Dia_Abiertas_v2.
    Para modo "Ventas del Día" en Tablero Ejecutivo.
    
    FIX 2026-05-15: Ahora calcula FechaOperacion usando operational_window.py
    en lugar de simplemente ordenar por snapshot_timestamp DESC.
    
    REGLA DE NEGOCIO:
    - A las 00:30 del día 15, si el restaurante cierra a las 03:00,
      todavía pertenece a la jornada del día 14.
    - No se debe mostrar $0 del día 15 si la jornada del 14 sigue abierta.
    
    TRANSICIÓN (mientras job se actualiza):
    - Busca en fecha_operacion calculada O fecha calendario siguiente
    - Toma el snapshot más reciente con ventas > 0
    """
    import pytz
    from datetime import datetime, time as dt_time, timedelta
    
    mexico_tz = pytz.timezone('America/Mexico_City')
    now_mx = datetime.now(mexico_tz)
    fecha_calendario = now_mx.date().isoformat()
    
    # =================================================================
    # FIX 2026-05-15: Calcular FechaOperacion activa
    # =================================================================
    if unidad_negocio_id:
        # Usar ventana operativa de la unidad específica
        from core.utils.operational_window import get_operational_window
        fecha_op_calc, hora_ini, hora_fin, cruza = get_operational_window(unidad_negocio_id, now_mx)
        fecha_operacion = fecha_op_calc.isoformat()
        logging.info(
            f"[TABLERO-EDARSAHUB] _get_ventas_abiertas: {unidad_negocio_id} FechaOperacion={fecha_operacion} "
            f"(hora actual={now_mx.strftime('%H:%M')}, horario={hora_ini}-{hora_fin})"
        )
    else:
        # Sin unidad específica: usar horario por defecto 13:00-06:00
        # ACTUALIZACIÓN 16-May-2026: Corte operativo cambiado de 03:00 a 06:00
        hora_actual = now_mx.time()
        hora_fin_default = dt_time(6, 0, 0)
        
        if hora_actual < hora_fin_default:
            # Estamos entre 00:00 y 06:00: pertenece al día anterior
            fecha_operacion = (now_mx.date() - timedelta(days=1)).isoformat()
        else:
            fecha_operacion = now_mx.date().isoformat()
        
        logging.info(
            f"[TABLERO-EDARSAHUB] _get_ventas_abiertas: server_id={server_id} FechaOperacion default={fecha_operacion} "
            f"(hora actual={now_mx.strftime('%H:%M')}, usando horario default 13:00-06:00)"
        )
    
    # =================================================================
    # QUERY ROBUSTA: Buscar en fecha_operacion calculada O fecha calendario
    # TRANSICIÓN: Mientras el job se actualiza, los datos pueden tener
    # fecha_operacion = fecha_calendario en lugar de fecha_operacion correcta
    # =================================================================
    # FIX P0 (15-May-2026): Buscar por unidad_negocio_id en lugar de server_id
    # FIX P0.H (20-May-2026): Si no hay datos para fecha exacta, buscar último
    # snapshot disponible y marcarlo como STALE
    # =================================================================
    is_stale = False
    fecha_usada = None
    
    if unidad_negocio_id:
        # Priorizar búsqueda por unidad_negocio_id (más confiable)
        # Primero intentar con fechas exactas
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
        WHERE unidad_negocio_id = '{unidad_negocio_id}'
          AND fecha_operacion IN ('{fecha_operacion}', '{fecha_calendario}')
        ORDER BY 
            CASE WHEN fecha_operacion = '{fecha_operacion}' THEN 0 ELSE 1 END,
            snapshot_timestamp DESC
        """
    else:
        # Fallback: buscar por server_id + sucursal_id
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
          AND fecha_operacion IN ('{fecha_operacion}', '{fecha_calendario}')
        ORDER BY 
            CASE WHEN fecha_operacion = '{fecha_operacion}' THEN 0 ELSE 1 END,
            snapshot_timestamp DESC
        """
    result = _query_edarsahub_tablero(query)
    
    # FIX P0.H: Si no hay datos para fecha exacta, buscar último snapshot disponible
    if (not result or len(result) == 0) and unidad_negocio_id:
        logging.warning(
            f"[TABLERO-EDARSAHUB] Sin datos para fecha exacta. Buscando último snapshot para {unidad_negocio_id}..."
        )
        # Buscar el registro más reciente de esta unidad (cualquier fecha)
        fallback_query = f"""
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
        WHERE unidad_negocio_id = '{unidad_negocio_id}'
        ORDER BY fecha_ultima_actualizacion DESC, snapshot_timestamp DESC
        """
        result = _query_edarsahub_tablero(fallback_query)
        if result and len(result) > 0:
            is_stale = True
            logging.warning(
                f"[TABLERO-EDARSAHUB] Usando snapshot STALE para {unidad_negocio_id}: "
                f"fecha_db={result[0].get('fecha_operacion')}, fecha_esperada={fecha_operacion}"
            )
    
    if result and len(result) > 0:
        row = result[0]
        ventas_total = float(row.get('ventas_abiertas') or 0) + float(row.get('ventas_cerradas_dia') or 0)
        fecha_op_usada = row.get('fecha_operacion')
        logging.info(
            f"[TABLERO-EDARSAHUB] _get_ventas_abiertas: server_id={server_id} "
            f"fecha_op_calculada={fecha_operacion}, fecha_op_db={fecha_op_usada}, ventas=${ventas_total:,.2f}, is_stale={is_stale}"
        )
        return {
            'existe': True,
            'ventas': ventas_total,
            'pax': int(row.get('pax_abiertos') or 0) + int(row.get('pax_cerrados_dia') or 0),
            'cheques': int(row.get('tickets_abiertos') or 0) + int(row.get('tickets_cerrados_dia') or 0),
            'snapshot_timestamp': row.get('snapshot_timestamp'),
            'fecha_operacion': fecha_op_usada,
            'fecha_operacion_usada': fecha_operacion,  # Para debug
            'is_stale': is_stale,
            'stale_reason': f'fecha_db={fecha_op_usada} != fecha_esperada={fecha_operacion}' if is_stale else None
        }
    
    logging.warning(
        f"[TABLERO-EDARSAHUB] _get_ventas_abiertas: Sin datos para server_id={server_id}, "
        f"sucursal={sucursal_id}, fecha_op={fecha_operacion}"
    )
    return {
        'existe': False,
        'ventas': 0,
        'pax': 0,
        'cheques': 0,
        'snapshot_timestamp': None,
        'fecha_operacion': None,
        'fecha_operacion_usada': fecha_operacion,
        'is_stale': False
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
    dias_transcurridos: int,
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
    
    ACTUALIZACIÓN 16-May-2026: REGLA CANÓNICA DE PROYECCIÓN
    - dias_transcurridos = FechaOperacionActual.day (con corte 06:00 AM)
    - NO usar dia_ultimo (último día con datos) como divisor
    - ProyecciónMensual = ventas / dias_transcurridos * dias_mes
    
    REGLA DE COMPARATIVOS:
    1. Mes parcial: compara mismos días
    2. Mes completo: compara mes vs mes completo
    
    Args:
        server_id: ID del servidor EDARSAHUB (para mapear unidad)
        unidad_negocio_id: ID de unidad (130MID, CIENFUEGOS, etc.)
        sucursal_id: ID de sucursal (DEFAULT, 0021, 0023)
        fecha_ini: Fecha inicio período actual (YYYY-MM-DD)
        fecha_fin: Fecha fin período actual (YYYY-MM-DD)
        dias_mes: Días totales del mes para proyección
        dias_transcurridos: Días operativos transcurridos (FechaOperacionActual.day)
        nombre_unidad: Nombre de la unidad (para logs)
    
    Returns:
        Dict con KPIs o None si hay error
    """
    logging.info(f"[TABLERO-EDARSAHUB] {nombre_unidad or unidad_negocio_id}: Consultando KPIs desde EDARSAHUB, dias_transcurridos={dias_transcurridos}")
    
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
    # FIX: Pasar unidad_negocio_id para filtro más confiable (especialmente para MPRO)
    kpis_actual = _get_kpis_periodo_edarsahub(server_id, fecha_ini, fecha_fin_real, sucursal_id, unidad_negocio_id=unidad_negocio_id)
    
    if not kpis_actual['existe_data']:
        logging.warning(f"[TABLERO-EDARSAHUB] {nombre_unidad}: Sin datos reales en período actual")
        return None
    
    ventas = kpis_actual['ventas']
    pax = kpis_actual['pax']
    cheques = kpis_actual['cheques']
    
    # =========================================================================
    # PROYECCIÓN MENSUAL: Usar ÚLTIMO DÍA CON VENTAS REGISTRADAS
    # =========================================================================
    # REGLA CANÓNICA: ProyecciónMensual con FechaOperacionActual.day
    # ACTUALIZACIÓN 16-May-2026: Usar días transcurridos operativos
    # =========================================================================
    # ProyeccionMensual = VentasAcumuladas / DiasTranscurridosOperativos * DiasMes
    #
    # Donde:
    # - DiasTranscurridosOperativos = parámetro dias_transcurridos (viene de FechaOperacionActual.day)
    # - NO usar dia_ultimo (último día con datos en EDARSAHUB)
    # - NO usar MAX(fecha) como divisor
    #
    # Ejemplo Mayo 2026, hora actual 08:15 AM México:
    # - FechaOperacionActual = 16 (porque >= 06:00)
    # - dias_transcurridos = 16
    # - proyección = ventas / 16 * 31
    #
    # El dia_ultimo se usa SOLO para diagnóstico de frescura de datos:
    # - sync_lag = dias_transcurridos - dia_ultimo
    # =========================================================================
    
    # Diagnóstico de frescura (no afecta la proyección)
    sync_lag = dias_transcurridos - dia_ultimo if dia_ultimo else dias_transcurridos
    estado_frescura = "SUCCESS" if sync_lag <= 0 else f"SYNC_LAG_{sync_lag}d"
    
    logging.info(f"[PROYECCION] {nombre_unidad}: dias_transcurridos={dias_transcurridos}, dia_ultimo_datos={dia_ultimo}, sync_lag={sync_lag}, dias_mes={dias_mes}")
    
    # 4. OBTENER KPIs MES ANTERIOR
    kpis_mes_ant = _get_kpis_periodo_edarsahub(server_id, fecha_ini_ant, fecha_fin_ant, sucursal_id, unidad_negocio_id=unidad_negocio_id)
    
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
    kpis_anio_ant = _get_kpis_periodo_edarsahub(server_id, fecha_ini_anio_ant, fecha_fin_anio_ant, sucursal_id, unidad_negocio_id=unidad_negocio_id)
    
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


# ============================================================================
# MAPEO DE UNIDADES EDARSAHUB - CÓDIGOS CANÓNICOS
# ============================================================================
# FIX IDENTIDAD CANÓNICA (2026-05-16):
# - Usar SIEMPRE códigos CANÓNICOS según tabla Unidades_Negocio en EDARSAHUB
# - NUNCA usar aliases legacy (130-MER, 130-QRO, LA-ESTELAR)
# - Los códigos canónicos son: 130MID, 130QRO, CIENFUEGOS, ESTELAR, ORIGEN
# ============================================================================
UNIDADES_EDARSAHUB_MAP = {
    # SoftRestaurant
    "a5547321-1139-4d2b-9d53-182ca737b6b6": {"unidad_negocio_id": "130MID", "nombre": "130° MÉRIDA", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
    "6d053c22-523e-48c0-b72b-96081e2d781b": {"unidad_negocio_id": "CIENFUEGOS", "nombre": "CIENFUEGOS", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
    "a5ff0e25-f029-43db-b634-d4ac814c904f": {"unidad_negocio_id": "ESTELAR", "nombre": "LA ESTELAR", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
    # MPRO (necesitan sucursal específica)
    "1b230a06-ffaf-4c70-bd27-b1be3579dea6": {
        "sucursales": {
            "0021": {"unidad_negocio_id": "130QRO", "nombre": "130° QUERÉTARO"},
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
    data_type: str = "HUB",  # P0: Nuevo campo de auditoría obligatorio
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
        
        # Información de fuente (P0 TAREA 5) + Auditoría SQL-Only
        "source_used": source_used,
        "source_real_attempted": source_real_attempted,
        "source_real_status": source_real_status,
        "source_period": source_period,
        "source_live": source_live,
        "data_type": data_type,  # P0: EDARSAHUB_VENTAS_DIA | HUB | LIVE-C
        
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
    
    # =========================================================================
    # FASE 5B: Usar EmpresaResolver para obtener mapeo de unidad_negocio_id
    # El mapeo traduce códigos canónicos (130MID) a formatos legacy (130-MER)
    # usados en Comercial_KPIs_Diarios_v2
    # =========================================================================
    unidad_negocio_id = _mapear_codigo_a_unidad_negocio_id(unidad_negocio_codigo)
    
    logging.info(f"[TABLERO-EDARSAHUB] {nombre}: Iniciando consulta - unidad={unidad_negocio_id}, sucursal={sucursal_id}")
    
    # ============================================================================
    # MODO VENTAS DEL DÍA: Leer de Comercial_Ventas_Dia_Abiertas_v2
    # ============================================================================
    if solo_ventas_dia:
        logging.info(f"[TABLERO-EDARSAHUB] {nombre}: Modo Ventas del Día - consultando snapshot EDARSAHUB")
        
        # FIX 2026-05-15: Pasar unidad_negocio_codigo para calcular FechaOperacion correcta
        ventas_abiertas = _get_ventas_abiertas_edarsahub(server_id, sucursal_id, unidad_negocio_id=unidad_negocio_codigo)
        
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
        dias_transcurridos=dias_transcurridos,
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
            dias_transcurridos=dias_transcurridos,
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
    
    # =========================================================================
    # FIX PROYECCIÓN MENSUAL MPRO: Usar días transcurridos OPERATIVOS
    # =========================================================================
    # REGLA CANÓNICA: Misma que SoftRestaurant
    # ProyeccionMensual = VentasAcumuladas / DiasTranscurridosOperativos * DiasMes
    # =========================================================================
    
    # Obtener fecha operativa actual en zona horaria México
    try:
        from zoneinfo import ZoneInfo
        tz_mexico = ZoneInfo('America/Mexico_City')
    except ImportError:
        import pytz
        tz_mexico = pytz.timezone('America/Mexico_City')
    
    ahora_mexico = datetime.now(tz_mexico)
    
    # =========================================================================
    # REGLA CANÓNICA: FechaOperacion con corte a las 06:00 AM
    # ACTUALIZACIÓN 16-May-2026: Corte operativo cambiado de 03:00 a 06:00
    # =========================================================================
    # Si hora < 06:00: pertenece al día operativo ANTERIOR
    # Si hora >= 06:00: pertenece al día operativo ACTUAL
    # =========================================================================
    hora_actual = ahora_mexico.hour
    if hora_actual < 6:
        fecha_operacion_actual = ahora_mexico.date() - timedelta(days=1)
    else:
        fecha_operacion_actual = ahora_mexico.date()
    
    # Calcular días transcurridos operativos
    fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d').date()
    fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    if fecha_operacion_actual > fecha_fin_dt:
        dias_transcurridos_calc = (fecha_fin_dt - fecha_ini_dt).days + 1
        logging.info(f"[PROYECCION-FIX-MPRO] {nombre}: Mes cerrado, días={dias_transcurridos_calc}")
    elif fecha_operacion_actual >= fecha_ini_dt:
        dias_transcurridos_calc = (fecha_operacion_actual - fecha_ini_dt).days + 1
        logging.info(f"[PROYECCION-FIX-MPRO] {nombre}: Mes actual, FechaOp={fecha_operacion_actual}, días={dias_transcurridos_calc}")
    else:
        dias_transcurridos_calc = 1
    
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
    
    FIX P0 (15-May-2026): REFACTORIZADO PARA LEER SOLO DE EDARSAHUB SQL
    =====================================================================
    REGLA ARQUITECTÓNICA OBLIGATORIA:
    - El tablero NO debe hacer conexiones LIVE a APIs locales
    - Ventas del día debe leerse desde Comercial_Ventas_Dia_Abiertas_v2 (EDARSAHUB SQL)
    - Las APIs locales SOLO pueden ser consultadas por jobs de sincronización
    
    COMPORTAMIENTO:
    - solo_ventas_dia=True → Lee de EDARSAHUB SQL (Comercial_Ventas_Dia_Abiertas_v2)
    - solo_ventas_dia=False → Lee de EDARSAHUB SQL (ventas históricas/acumuladas)
    """
    
    logging.debug(f"MPRO {server['name']}: solo_ventas_dia={solo_ventas_dia}, fecha_ini={fecha_ini}, fecha_fin={fecha_fin}")
    
    # ============================================================================
    # FIX P0 (15-May-2026): VENTAS DEL DÍA - LEER DE EDARSAHUB SQL
    # ============================================================================
    # PROHIBIDO: Llamar a APIs locales desde el tablero
    # OBLIGATORIO: Leer desde Comercial_Ventas_Dia_Abiertas_v2
    # ============================================================================
    if solo_ventas_dia:
        logging.info(f"[FIX-P0] MPRO {server['name']}: Modo Ventas del Día - LEYENDO DE EDARSAHUB SQL (NO API local)")
        
        # =====================================================================
        # FASE 5B: Obtener sucursales MPRO desde EmpresaResolver
        # Reemplaza el hardcoding de sucursales_mpro
        # =====================================================================
        sucursales_mpro = _obtener_sucursales_mpro_desde_resolver()
        
        unidades = []
        
        for suc in sucursales_mpro:
            # Resolver unidad desde EDARSAHUB
            unidad_edarsahub = resolve_unidad_by_server_sucursal(
                suc['server_id'], suc['sucursal_id']
            )
            
            codigo_canonico = unidad_edarsahub.get('codigo', suc['codigo']) if unidad_edarsahub else suc['codigo']
            nombre_canonico = unidad_edarsahub.get('nombre', suc['codigo']) if unidad_edarsahub else suc['codigo']
            
            # FIX P0: Leer de EDARSAHUB SQL usando _get_ventas_abiertas_edarsahub()
            datos_edarsahub = _get_ventas_abiertas_edarsahub(
                server_id=suc['server_id'],
                sucursal_id=suc['sucursal_id'],
                unidad_negocio_id=codigo_canonico
            )
            
            if datos_edarsahub.get('existe', False):
                ventas = datos_edarsahub.get('ventas', 0)
                cheques = datos_edarsahub.get('cheques', 0)
                pax = datos_edarsahub.get('pax', 0) or cheques
                
                ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
                cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
                
                unidades.append({
                    "unidad": nombre_canonico,
                    "server_id": suc['server_id'],
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
                    "origen": "EDARSAHUB_SQL",  # FIX P0: Indica que viene de EDARSAHUB
                    "source_status": "DATA_FROM_EDARSAHUB_SQL",
                    "snapshot_timestamp": datos_edarsahub.get('snapshot_timestamp'),
                    "fecha_operacion": datos_edarsahub.get('fecha_operacion'),
                    # Campos canónicos
                    "unidad_negocio_codigo": codigo_canonico,
                    "unidad_negocio_nombre": nombre_canonico,
                    "sucursal_origen_id": suc['sucursal_id'],
                })
                logging.info(
                    f"[FIX-P0] MPRO {nombre_canonico}: EDARSAHUB SQL OK - "
                    f"${ventas:,.2f}, fecha_op={datos_edarsahub.get('fecha_operacion')}"
                )
            else:
                # Sin datos en EDARSAHUB - mostrar estado claro, NO $0 falso
                unidades.append({
                    "unidad": nombre_canonico,
                    "server_id": suc['server_id'],
                    "system_type": "MPRO",
                    "ventas": None,  # None indica "sin dato", no $0
                    "ventas_ant": 0,
                    "ventas_año": 0,
                    "var_vs_mes_ant": 0,
                    "var_vs_año_ant": 0,
                    "proyeccion": 0,
                    "pax": None,
                    "pax_ant": 0,
                    "pax_año": 0,
                    "var_pax_mes": 0,
                    "var_pax_año": 0,
                    "cheques": None,
                    "cheques_ant": 0,
                    "cheques_año": 0,
                    "var_cheques_mes": 0,
                    "var_cheques_año": 0,
                    "ticket_prom": 0,
                    "cheque_prom": 0,
                    "es_ventas_dia": True,
                    "origen": "EDARSAHUB_SQL",
                    "source_status": "NO_SYNC_DATA",  # Estado claro: sin sincronización
                    "message": "Sin datos sincronizados para esta fecha operativa",
                    # Campos canónicos
                    "unidad_negocio_codigo": codigo_canonico,
                    "unidad_negocio_nombre": nombre_canonico,
                    "sucursal_origen_id": suc['sucursal_id'],
                })
                logging.warning(
                    f"[FIX-P0] MPRO {nombre_canonico}: Sin datos en EDARSAHUB SQL - "
                    f"fecha_op_buscada={datos_edarsahub.get('fecha_operacion_usada')}"
                )
        
        return unidades
    
    # ============================================================================
    # FIX CIRCUIT BREAKER HUB (17-May-2026):
    # VENTAS HISTÓRICAS / ACUMULADAS PARA MODO HUB
    # 
    # REGLA ARQUITECTÓNICA:
    # - Para modo HUB (Tablero Ejecutivo), MPRO debe leer de EDARSAHUB SQL
    # - NO consultar servidores MPRO directamente (bases QUERETARO, ORIGEN)
    # - Usar la misma fuente que SoftRestaurant: Comercial_KPIs_Diarios_v2
    # 
    # RAZÓN: EDARSAHUB SQL es la fuente consolidada y canónica.
    # Las bases MPRO (QUERETARO, ORIGEN) son fuentes de extracción, no de lectura.
    # ============================================================================
    
    logging.info(f"[FIX-HUB] MPRO {server['name']}: Modo Histórico/Acumulado - LEYENDO DE EDARSAHUB SQL (NO bases MPRO)")
    
    # Obtener sucursales MPRO desde EmpresaResolver
    sucursales_mpro = _obtener_sucursales_mpro_desde_resolver()
    
    unidades = []
    
    for suc in sucursales_mpro:
        # Resolver unidad desde EDARSAHUB
        unidad_edarsahub = resolve_unidad_by_server_sucursal(
            suc['server_id'], suc['sucursal_id']
        )
        
        codigo_canonico = unidad_edarsahub.get('codigo', suc['codigo']) if unidad_edarsahub else suc['codigo']
        nombre_canonico = unidad_edarsahub.get('nombre', suc['codigo']) if unidad_edarsahub else suc['codigo']
        sucursal_id = suc['sucursal_id']
        
        # Mapear código a unidad_negocio_id usado en Comercial_KPIs_Diarios_v2
        unidad_negocio_id = _mapear_codigo_a_unidad_negocio_id(codigo_canonico)
        
        # Usar la misma función que SoftRestaurant para leer de EDARSAHUB
        kpis = _obtener_kpis_tablero_desde_edarsahub(
            server_id=suc['server_id'],
            unidad_negocio_id=unidad_negocio_id,
            sucursal_id=sucursal_id,
            fecha_ini=fecha_ini,
            fecha_fin=fecha_fin,
            dias_mes=dias_mes,
            dias_transcurridos=dias_transcurridos,
            nombre_unidad=nombre_canonico
        )
        
        if kpis:
            # Datos encontrados en EDARSAHUB
            kpis['unidad'] = nombre_canonico
            kpis['server_id'] = suc['server_id']
            kpis['sucursal_id'] = sucursal_id
            kpis['sucursal_origen_id'] = sucursal_id
            kpis['system_type'] = "MPRO"
            kpis['origen'] = "EDARSAHUB_SQL"  # Indica fuente correcta
            kpis['source_status'] = "DATA_FROM_EDARSAHUB_SQL"
            kpis['unidad_negocio_codigo'] = codigo_canonico
            kpis['unidad_negocio_nombre'] = nombre_canonico
            
            unidades.append(kpis)
            logging.info(
                f"[FIX-HUB] MPRO {nombre_canonico}: EDARSAHUB SQL OK - "
                f"${kpis.get('ventas', 0):,.2f}"
            )
        else:
            # Sin datos en EDARSAHUB para este período
            unidades.append({
                "unidad": nombre_canonico,
                "server_id": suc['server_id'],
                "sucursal_id": sucursal_id,
                "sucursal_origen_id": sucursal_id,
                "system_type": "MPRO",
                "ventas": None,
                "ventas_ant": 0,
                "ventas_año": 0,
                "var_vs_mes_ant": 0,
                "var_vs_año_ant": 0,
                "proyeccion": 0,
                "pax": None,
                "pax_ant": 0,
                "pax_año": 0,
                "var_pax_mes": 0,
                "var_pax_año": 0,
                "cheques": None,
                "cheques_ant": 0,
                "cheques_año": 0,
                "var_cheques_mes": 0,
                "var_cheques_año": 0,
                "ticket_prom": 0,
                "cheque_prom": 0,
                "origen": "EDARSAHUB_SQL",
                "source_status": "NO_DATA_SQL",
                "message": "Sin datos en EDARSAHUB para este período",
                "unidad_negocio_codigo": codigo_canonico,
                "unidad_negocio_nombre": nombre_canonico,
            })
            logging.warning(
                f"[FIX-HUB] MPRO {nombre_canonico}: Sin datos en EDARSAHUB SQL para período {fecha_ini} a {fecha_fin}"
            )
    
    return unidades
    
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
        
        # =========================================================================
        # FIX P0 (Dic 2025): Filtrar por Unidades_Negocio activas en EDARSAHUB
        # REGLA: Solo mostrar sucursales registradas como unidades activas
        # Si no existe en EDARSAHUB.Unidades_Negocio → OMITIR (no mostrar como "Unidad Desconocida")
        # =========================================================================
        unidad_edarsahub = resolve_unidad_by_server_sucursal(server['id'], sucursal_id)
        if not unidad_edarsahub:
            logging.info(f"[MPRO] Sucursal no visible omitida: sucursal_origen_id={sucursal_id}, nombre={sucursal_nombre}")
            continue  # Omitir sucursal no registrada en Unidades_Negocio
        
        # Obtener código y nombre canónico desde EDARSAHUB
        codigo_canonico = unidad_edarsahub.get('codigo', sucursal_id)
        nombre_canonico = unidad_edarsahub.get('nombre', sucursal_nombre)
        
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
        
        # FIX P0: codigo_canonico y nombre_canonico ya resueltos al inicio del bucle
        # via resolve_unidad_by_server_sucursal() - NO usar _obtener_codigo_canonico_mpro()
        
        unidades.append({
            "unidad": nombre_canonico,  # Nombre canónico de EDARSAHUB
            "sucursal": nombre_canonico,  # Para filtrar en endpoints de detalle
            "server_id": server['id'],
            "sucursal_id": sucursal_id,
            "sucursal_origen_id": sucursal_id,  # Trazabilidad
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
            # FIX P0: Campos canónicos desde Unidades_Negocio EDARSAHUB
            "unidad_negocio_codigo": codigo_canonico,
            "unidad_negocio_nombre": nombre_canonico,
        })
        
        logging.info(f"MPRO {server['name']} - Sucursal '{nombre_canonico}' (origen_id={sucursal_id}): Ventas={ventas}, Cheques={cheques}")
    
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
    # FASE 7-FIX: Dashboard Comercial desde EDARSAHUB
    'get_dashboard_kpis_from_edarsahub',
]


# ============================================================================
# FASE 7-FIX: Dashboard Comercial desde EDARSAHUB
# ============================================================================
# OBJETIVO: Corregir Dashboard Comercial que mostraba "Sin Datos" cuando
# EDARSAHUB SÍ tiene datos en Comercial_KPIs_Diarios_v2.
# 
# PROBLEMA: Dashboard Comercial consultaba directamente al servidor remoto
# SoftRestaurant. Si la conexión fallaba, mostraba "Sin Datos" aunque EDARSAHUB
# tiene datos consolidados.
#
# SOLUCIÓN: Usar la MISMA fuente que Tablero Ejecutivo (Comercial_KPIs_Diarios_v2)
# como fuente PRINCIPAL para Dashboard Comercial.
#
# MÁXIMA: EDARSAHUB SQL es el cerebro del sistema.
# ============================================================================

def get_dashboard_kpis_from_edarsahub(
    server_id: str,
    fecha_ini: str,  # YYYY-MM-DD
    fecha_fin: str,  # YYYY-MM-DD
    fecha_ini_ant: str = None,
    fecha_fin_ant: str = None,
    fecha_ini_ano_ant: str = None,
    fecha_fin_ano_ant: str = None,
    sucursal_id: str = 'DEFAULT'
) -> Dict:
    """
    DASHBOARD COMERCIAL - KPIs desde EDARSAHUB (Comercial_KPIs_Diarios_v2)
    ======================================================================
    
    Usa la MISMA fuente que el Tablero Ejecutivo para garantizar consistencia.
    
    FUENTE: Comercial_KPIs_Diarios_v2 en EDARSAHUB
    NO consulta: Servidores remotos SoftRestaurant
    NO consulta: MongoDB
    
    Args:
        server_id: UUID del servidor
        fecha_ini, fecha_fin: Período actual (YYYY-MM-DD)
        fecha_ini_ant, fecha_fin_ant: Período anterior para comparativo
        fecha_ini_ano_ant, fecha_fin_ano_ant: Año anterior para comparativo
        sucursal_id: ID de sucursal (DEFAULT si no se especifica)
    
    Returns:
        Dict con KPIs o None si no hay datos
    """
    logging.info(
        f"[DASHBOARD-EDARSAHUB] server_id={server_id[:8]}... "
        f"período={fecha_ini} a {fecha_fin} sucursal={sucursal_id}"
    )
    
    # 1. OBTENER DATOS DEL PERÍODO ACTUAL
    # Primero intentar sin filtro de sucursal (para detectar si hay datos)
    kpis_actual = _get_kpis_periodo_edarsahub_flexible(server_id, fecha_ini, fecha_fin, sucursal_id)
    
    if not kpis_actual['existe_data']:
        logging.warning(
            f"[DASHBOARD-EDARSAHUB] Sin datos para server_id={server_id[:8]}... "
            f"en período {fecha_ini} a {fecha_fin} (sucursal={sucursal_id})"
        )
        return None
    
    ventas = kpis_actual['ventas']
    pax = kpis_actual['pax']
    cheques = kpis_actual['cheques']
    
    logging.info(
        f"[DASHBOARD-EDARSAHUB] Datos encontrados: "
        f"ventas=${ventas:,.2f}, pax={pax}, cheques={cheques}"
    )
    
    # 2. CALCULAR MÉTRICAS DERIVADAS
    ticket_promedio = ventas / cheques if cheques > 0 else 0
    pax_promedio = pax / cheques if cheques > 0 else 0
    consumo_persona = ventas / pax if pax > 0 else 0
    
    # 3. OBTENER DATOS DEL PERÍODO ANTERIOR (si se proporcionan fechas)
    ventas_ant = 0
    pax_ant = 0
    cheques_ant = 0
    
    if fecha_ini_ant and fecha_fin_ant and fecha_ini_ant != "PENDIENTE":
        kpis_ant = _get_kpis_periodo_edarsahub_flexible(server_id, fecha_ini_ant, fecha_fin_ant, sucursal_id)
        if kpis_ant['existe_data']:
            ventas_ant = kpis_ant['ventas']
            pax_ant = kpis_ant['pax']
            cheques_ant = kpis_ant['cheques']
    
    # 4. OBTENER DATOS DEL AÑO ANTERIOR (si se proporcionan fechas)
    ventas_ano_ant = 0
    pax_ano_ant = 0
    cheques_ano_ant = 0
    
    if fecha_ini_ano_ant and fecha_fin_ano_ant:
        kpis_ano = _get_kpis_periodo_edarsahub_flexible(server_id, fecha_ini_ano_ant, fecha_fin_ano_ant, sucursal_id)
        if kpis_ano['existe_data']:
            ventas_ano_ant = kpis_ano['ventas']
            pax_ano_ant = kpis_ano['pax']
            cheques_ano_ant = kpis_ano['cheques']
    
    # 5. CALCULAR COMPARATIVOS
    vs_periodo_anterior = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
    vs_ano_anterior = round(((ventas - ventas_ano_ant) / ventas_ano_ant * 100), 1) if ventas_ano_ant > 0 else 0
    
    # 6. CONSTRUIR RESPUESTA
    return {
        'ventas_periodo': ventas,
        'pax_total': pax,
        'cheques_total': cheques,
        'ticket_promedio': ticket_promedio,
        'pax_promedio': pax_promedio,
        'consumo_persona': consumo_persona,
        'mesas_atendidas': cheques,  # Aproximación
        'rotacion_mesas': 1.0,  # No disponible en datos consolidados
        'venta_por_hora': 0,  # No disponible en datos consolidados
        # Comparativos
        'ventas_anterior': ventas_ant,
        'pax_anterior': pax_ant,
        'cheques_anterior': cheques_ant,
        'ventas_ano_anterior': ventas_ano_ant,
        'pax_ano_anterior': pax_ano_ant,
        'cheques_ano_anterior': cheques_ano_ant,
        'vs_periodo_anterior': vs_periodo_anterior,
        'vs_ano_anterior': vs_ano_anterior,
        'vs_presupuesto': 0,  # No disponible en EDARSAHUB
        # Metadata
        'source': 'EDARSAHUB_SQL',
        'source_table': 'Comercial_KPIs_Diarios_v2',
        'registros_consultados': kpis_actual['registros'],
    }


def _get_kpis_periodo_edarsahub_flexible(
    server_id: str,
    fecha_ini: str,
    fecha_fin: str,
    sucursal_id: str = 'DEFAULT'
) -> Dict:
    """
    Obtiene KPIs de EDARSAHUB con lógica flexible de sucursal.
    
    Si sucursal_id='DEFAULT' y no hay datos, intenta sin filtro de sucursal.
    Esto maneja casos donde los datos no tienen sucursal_id configurada.
    
    FIX MPRO: Si no encuentra por server_id, intenta buscar por unidad_negocio_id
    derivado del nombre del servidor. Esto maneja casos donde los datos MPRO
    tienen un server_id diferente al de Servidores_Conexiones.
    """
    # Primer intento: con sucursal específica
    kpis = _get_kpis_periodo_edarsahub(server_id, fecha_ini, fecha_fin, sucursal_id)
    
    if kpis['existe_data']:
        return kpis
    
    # Si no hay datos con sucursal DEFAULT, intentar SIN filtro de sucursal
    if sucursal_id == 'DEFAULT':
        query = f"""
        SELECT 
            ISNULL(SUM(ventas_total), 0) as ventas,
            ISNULL(SUM(pax_total), 0) as pax_total,
            ISNULL(SUM(tickets_total), 0) as cheques,
            COUNT(*) as registros
        FROM Comercial_KPIs_Diarios_v2
        WHERE server_id = '{server_id}'
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
            
            if registros > 0:
                logging.info(
                    f"[DASHBOARD-EDARSAHUB] Datos encontrados SIN filtro sucursal: "
                    f"ventas=${ventas:,.2f}, registros={registros}"
                )
                return {
                    'ventas': ventas,
                    'pax': pax,
                    'cheques': cheques,
                    'registros': registros,
                    'existe_data': True
                }
    
    # =========================================================================
    # FIX MPRO: Buscar por unidad_negocio_id si no encontramos por server_id
    # =========================================================================
    # Este fallback maneja el caso donde los datos MPRO en Comercial_KPIs_Diarios_v2
    # tienen un server_id diferente (ej: ManagmentPro) pero el unidad_negocio_id
    # corresponde a la unidad correcta (ORIGEN, 130QRO, etc.)
    
    # Obtener nombre del servidor para derivar unidad_negocio_id
    unidad_ids = _obtener_unidad_ids_desde_servidor(server_id)
    
    if unidad_ids:
        logging.info(f"[DASHBOARD-EDARSAHUB-MPRO-FIX] Intentando búsqueda por unidad_negocio_id: {unidad_ids}")
        
        # Construir condición IN para múltiples posibles IDs
        ids_str = ", ".join([f"'{uid}'" for uid in unidad_ids])
        
        query_mpro = f"""
        SELECT 
            ISNULL(SUM(ventas_total), 0) as ventas,
            ISNULL(SUM(pax_total), 0) as pax_total,
            ISNULL(SUM(tickets_total), 0) as cheques,
            COUNT(*) as registros
        FROM Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id IN ({ids_str})
          AND fecha_operacion >= '{fecha_ini}'
          AND fecha_operacion <= '{fecha_fin}'
          AND ventas_total > 0
        """
        
        result_mpro = _query_edarsahub_tablero(query_mpro)
        
        if result_mpro and len(result_mpro) > 0:
            row = result_mpro[0]
            ventas = float(row.get('ventas') or 0)
            pax = int(row.get('pax') or 0)
            cheques = int(row.get('cheques') or 0)
            registros = int(row.get('registros') or 0)
            
            if registros > 0:
                logging.info(
                    f"[DASHBOARD-EDARSAHUB-MPRO-FIX] Datos MPRO encontrados por unidad_negocio_id: "
                    f"ventas=${ventas:,.2f}, registros={registros}"
                )
                return {
                    'ventas': ventas,
                    'pax': pax,
                    'cheques': cheques,
                    'registros': registros,
                    'existe_data': True
                }
    
    return {
        'ventas': 0,
        'pax': 0,
        'cheques': 0,
        'registros': 0,
        'existe_data': False
    }


def _obtener_unidad_ids_desde_servidor(server_id: str) -> List[str]:
    """
    Obtiene posibles unidad_negocio_id a partir del server_id.
    
    Mapeo basado en nombres de servidor:
    - ORIGEN LOCAL -> ['ORIGEN']
    - 130° QRO LOCAL -> ['130QRO', '130-QRO']
    - etc.
    """
    # Mapeo de server_id a posibles unidad_negocio_id
    mapeo_servidor_unidad = {
        # ORIGEN LOCAL
        '817a0aa8-6170-4738-a8f6-a72ac36ba0df': ['ORIGEN'],
        # 130° QRO LOCAL
        '72f6e9a7-8ea2-4eb2-802e-4ee31753435e': ['130QRO', '130-QRO'],
        # ManagmentPro (servidor MPRO principal) - no necesita fallback
        '1b230a06-ffaf-4c70-bd27-b1be3579dea6': [],
    }
    
    return mapeo_servidor_unidad.get(server_id, [])



def get_last_valid_snapshot_edarsahub(server_id: str) -> Dict:
    """
    FASE 1B-R1: Obtener último snapshot válido de EDARSAHUB aunque sea antiguo (STALE)
    
    Busca en Comercial_KPIs_Diarios_v2 el registro más reciente para el servidor,
    sin importar la fecha. Usado como fallback cuando no hay datos del período actual.
    
    Returns:
        Dict con fecha_snapshot, kpis y comparativo, o None si no existe ningún dato.
    """
    import pymssql
    import logging
    
    try:
        conn = pymssql.connect(
            server='54.39.104.176',
            user='HRLectura',
            password='National09$',
            database='EDARSAHUB',
            port=1433,
            timeout=10
        )
        cursor = conn.cursor(as_dict=True)
        
        # Buscar el registro más reciente para este servidor
        cursor.execute("""
            SELECT TOP 1
                server_id,
                unidad_negocio_nombre,
                fecha_operacion,
                fecha_sincronizacion,
                ventas_total,
                ventas_sin_propina,
                tickets_total,
                pax_total,
                ticket_promedio,
                pax_promedio
            FROM Comercial_KPIs_Diarios_v2
            WHERE server_id = %s
            ORDER BY fecha_operacion DESC
        """, (server_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            logging.warning(f"[STALE-SNAPSHOT] Sin datos históricos para server_id={server_id[:8]}...")
            return None
        
        # Construir respuesta como snapshot STALE
        fecha_snapshot = row['fecha_sincronizacion'] or row['fecha_operacion']
        if hasattr(fecha_snapshot, 'strftime'):
            fecha_snapshot = fecha_snapshot.strftime('%Y-%m-%d %H:%M')
        
        logging.info(f"[STALE-SNAPSHOT] Encontrado snapshot de {fecha_snapshot} para server_id={server_id[:8]}...")
        
        return {
            'fecha_snapshot': fecha_snapshot,
            'kpis': {
                'ventas_periodo': float(row['ventas_sin_propina'] or row['ventas_total'] or 0),
                'ticket_promedio': float(row['ticket_promedio'] or 0),
                'cheques_total': int(row['tickets_total'] or 0),
                'pax_total': int(row['pax_total'] or 0),
                'pax_promedio': float(row['pax_promedio'] or 0),
                'consumo_persona': 0,
                'mesas_atendidas': int(row['tickets_total'] or 0),
                'rotacion_mesas': 0,
                'venta_por_hora': 0
            },
            'comparativo': {
                'vs_periodo_anterior': 0,
                'vs_ano_anterior': 0,
                'vs_presupuesto': 0,
                'tipo_comparacion': 'N/A (snapshot histórico)',
                'ventas_anterior': 0,
                'ventas_ano_anterior': 0
            }
        }
        
    except Exception as e:
        logging.error(f"[STALE-SNAPSHOT] Error obteniendo snapshot: {e}")
        return None
