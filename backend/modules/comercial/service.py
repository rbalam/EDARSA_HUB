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
    """
    now = datetime.now(timezone.utc).isoformat()
    
    # Generar unidad_key canónica
    server_id = server.get('id', '')
    server_name = server.get('name', '')
    unidad_key = f"{server_id}:{sucursal or 'default'}"
    
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
        # Identificadores
        "unidad_key": unidad_key,
        "unidad_negocio_id": server.get('unidad_negocio_id', server_id),
        "server_id": server_id,
        "unidad": sucursal or server_name,
        "nombre": sucursal or server_name,
        
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
# Estas funciones fueron migradas desde server.py sin cambios funcionales.
# Mantienen la misma firma, mismos nombres de campos, misma estructura JSON.

def get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia=False):
    """Query reutilizable para SoftRestaurant - misma lógica análisis inventarios
    
    FASE 3.1 - COMPORTAMIENTO:
    - solo_ventas_dia=True → SoftRestaurant NO tiene API local, usa SQL nube (ventas acumuladas)
    - solo_ventas_dia=False → Usa SQL nube del menú Servidores
    
    NOTA: SoftRestaurant no tiene API local configurada. Cuando se solicitan ventas del día,
    se muestran las ventas acumuladas del SQL nube en su lugar.
    PENDIENTE: Inspección local en servidores para revisar configuración de API local SoftRestaurant.
    """
    
    # ============================================================================
    # VENTAS DEL DÍA: Priorizar cheques cerrados del último turno, fallback a tempcheques
    # - Si hay turno cerrado en las últimas 24h → mostrar cheques de ese turno
    # - Si NO hay turno cerrado reciente → mostrar tempcheques (operación en curso)
    # ============================================================================
    if solo_ventas_dia:
        logging.info(f"SoftRestaurant {server['name']}: Modo Ventas del Día")
        
        ventas = 0
        cheques = 0
        pax = 0
        origen = None
        
        # Verificar si la tabla tempcheques tiene columna 'propina'
        has_propina_temp = check_column_exists(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], 'tempcheques', 'propina'
        )
        propina_expr_temp = get_propina_safe_column_tempcheques(has_propina_temp)
        
        # VENTAS DEL DÍA = SIEMPRE tempcheques (turno abierto actual)
        try:
            # NOTA: Se excluyen propinas de las ventas SI la columna existe
            query_temp = f"""
SELECT 
    COUNT(DISTINCT folio) as cheques,
    ISNULL(SUM(total{propina_expr_temp}), 0) as ventas,
    ISNULL(SUM(nopersonas), 0) as pax
FROM tempcheques
WHERE cancelado = 0
"""
            result_temp = execute_sql_query(server['host'], server['port'], server['database'], 
                                            server['username'], server['password'], query_temp)
            if result_temp and len(result_temp) > 0:
                ventas = float(result_temp[0]['ventas'] or 0)
                cheques = int(result_temp[0]['cheques'] or 0)
                pax = int(result_temp[0]['pax'] or 0)
                if cheques > 0 or ventas > 0:
                    origen = "tempcheques"
                    logging.info(f"SoftRestaurant {server['name']} - Tempcheques: ${ventas:,.2f}, {cheques} cheques")
        except Exception as e:
            logging.warning(f"SoftRestaurant {server['name']}: Error tempcheques: {e}")
        
        # Si no hay datos en tempcheques
        if origen is None:
            logging.warning(f"SoftRestaurant {server['name']}: Sin datos del día (tempcheques vacío)")
            return None
        
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
            "origen": origen
        }
    
    # ============================================================================
    # VENTAS HISTÓRICAS / ACUMULADAS: Usar SQL nube del menú Servidores
    # (Solo se ejecuta si solo_ventas_dia=False)
    # ============================================================================
    
    # VALIDACIÓN DE RANGO DE FECHAS (FIX ESTRUCTURAL)
    if not is_valid_range(fecha_ini, fecha_fin):
        logging.error(f"SoftRestaurant {server['name']}: Rango de fechas inválido ({fecha_ini} > {fecha_fin})")
        return None
    
    # Usar formato YYYYMMDD sin guiones para evitar problemas de conversión de fecha
    try:
        fi, ff = to_yyyymmdd_range(fecha_ini, fecha_fin)
    except ValueError as e:
        logging.error(f"SoftRestaurant {server['name']}: Error convirtiendo fechas: {e}")
        return None
    
    # VALIDACIÓN DE CONEXIÓN: Verificar que el servidor SQL responde antes de continuar
    # CORRECCIÓN 2026-04-29: Usar configuración de EDARSAHUB SQL (menú Servidores)
    logging.info(f"[TABLERO] SoftRestaurant {server['name']}: Iniciando consulta SQL - Host={server['host']}:{server['port']}, DB={server['database']}, config_origin={server.get('config_origin', 'EDARSAHUB_SQL')}")
    try:
        test_query = "SELECT 1 as test"
        test_result = execute_sql_query(server['host'], server['port'], server['database'], 
                                        server['username'], server['password'], test_query)
        if not test_result:
            # La conexión se estableció pero no devolvió datos - problema de configuración
            logging.warning(f"[TABLERO] SoftRestaurant {server['name']}: Conexión SQL establecida pero sin respuesta - posible problema de configuración")
            return {"error": "CONFIG_QUERY_ERROR", "mensaje": "Conexión establecida pero sin respuesta de la base de datos"}
    except Exception as conn_error:
        # Error de conexión - puede ser limitación del entorno o servidor caído
        error_msg = str(conn_error).lower()
        logging.warning(f"[TABLERO] SoftRestaurant {server['name']}: Error de conexión SQL - {conn_error}")
        
        # Clasificar el tipo de error para el frontend
        if 'timeout' in error_msg or 'timed out' in error_msg:
            return {"error": "SERVER_TIMEOUT", "mensaje": f"Timeout conectando a {server['host']} - verificar accesibilidad de red"}
        elif 'login' in error_msg or 'authentication' in error_msg or 'password' in error_msg:
            return {"error": "AUTH_ERROR", "mensaje": "Error de autenticación SQL - verificar credenciales en configuración"}
        elif 'does not exist' in error_msg or 'cannot open' in error_msg:
            return {"error": "DATABASE_NOT_FOUND", "mensaje": f"Base de datos {server['database']} no encontrada"}
        else:
            # Error genérico de conexión - probablemente red/DNS
            return {"error": "SERVER_UNREACHABLE", "mensaje": f"No fue posible conectar con {server['host']} - verificar desde entorno local/VPN"}
    
    # DEBUG: Log para verificar fechas recibidas
    logging.info(f"[TABLERO] SoftRestaurant {server['name']} - Conexión OK - Fechas: {fecha_ini} a {fecha_fin}")
    
    # Extraer mes y año de fecha_fin para usarlos en recálculos (importante para multiselección de meses)
    mes_final = int(fecha_fin[5:7])  # Mes de fecha_fin (ej: 04 para abril)
    anio_final = int(fecha_fin[:4])  # Año de fecha_fin
    
    # PASO 1: Detectar el último día real con ventas en el período
    # IMPORTANTE: Usar CONVERT con formato 112 para evitar problemas de configuración regional
    query_ultimo_dia = f"""
SELECT MAX(CONVERT(DATE, turnos.apertura)) as ultimo_dia_venta
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{fi}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{ff}'
  AND cheques.cancelado = 0
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
            
            logging.info(f"SoftRestaurant {server['name']} - Último día con ventas: {anio_ultimo}-{mes_ultimo:02d}-{dia_con_datos:02d}")
            
            # Actualizar fecha_fin usando el MES CORRECTO del último día con ventas
            # CORRECCIÓN: Usar el mes y año del último día con ventas, no del mes inicial
            ff = f"{anio_ultimo}{str(mes_ultimo).zfill(2)}{str(dia_con_datos).zfill(2)}"
            
            # Calcular días transcurridos desde fecha_ini hasta el último día con ventas
            fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
            fecha_ultimo_dt = datetime(anio_ultimo, mes_ultimo, dia_con_datos)
            dias_transcurridos = (fecha_ultimo_dt - fecha_ini_dt).days + 1
            
            logging.info(f"SoftRestaurant {server['name']} - Período ajustado: {fi} a {ff}, días: {dias_transcurridos}")
            
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
            
            # Año anterior - CORRECCIÓN: NO sobrescribir fecha_ini_año_ant
            # El Tablero Ejecutivo ya calcula correctamente el rango completo (ej: 01-ene-2025 a 08-abr-2025)
            # Solo ajustamos fecha_fin_año_ant al día correcto del mes final
            anio_pasado = anio_actual - 1
            max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_ultimo)[1]
            dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
            # PRESERVAR fecha_ini_año_ant original (viene del Tablero con el mes inicial correcto)
            # Solo actualizar fecha_fin_año_ant con el día ajustado del mes final
            fecha_fin_año_ant = f"{anio_pasado}-{str(mes_ultimo).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
            
            logging.info(f"Períodos ajustados - Actual: {fi[:4]}-{fi[4:6]}-01 a {ff}, Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
    except Exception as e:
        logging.warning(f"Error detectando último día: {e}")
        # Si falla, continuar con las fechas originales
    
    # Query principal
    # BLOQUE 4: Migrado a query centralizada query_ventas_periodo_sr()
    # ORIGEN ANTERIOR: SQL directo líneas 341-363 (ahora en queries/softrestaurant.py)
    result_principal = query_ventas_periodo_sr(server, fecha_ini, fecha_fin)
    
    if result_principal.success:
        ventas = result_principal.total_venta
        pax = result_principal.pax
        cheques = result_principal.cheques
    else:
        logging.warning(f"Error consultando {server['name']}: {result_principal.error}")
        return None
    
    # Verificar si las tablas tienen columna 'propina'
    has_propina_cheques = check_column_exists(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], 'cheques', 'propina'
    )
    has_propina_temp = check_column_exists(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], 'tempcheques', 'propina'
    )
    propina_expr = get_propina_safe_column(has_propina_cheques)
    propina_expr_temp = get_propina_safe_column_tempcheques(has_propina_temp)
    
    # SUMAR ventas del día sin corte (tempcheques) a las ventas históricas
    # NOTA: Se excluyen propinas de las ventas SI la columna existe
    try:
        query_temp = f"""
SELECT 
    COUNT(DISTINCT folio) as cheques,
    ISNULL(SUM(total{propina_expr_temp}), 0) as ventas,
    ISNULL(SUM(nopersonas), 0) as pax
FROM tempcheques
WHERE cancelado = 0
"""
        result_temp = execute_sql_query(server['host'], server['port'], server['database'], 
                                        server['username'], server['password'], query_temp)
        if result_temp and len(result_temp) > 0:
            ventas_temp = float(result_temp[0]['ventas'] or 0)
            pax_temp = int(result_temp[0]['pax'] or 0)
            cheques_temp = int(result_temp[0]['cheques'] or 0)
            # Sumar a los totales
            ventas += ventas_temp
            pax += pax_temp
            cheques += cheques_temp
            logging.info(f"SoftRestaurant {server['name']} - Tempcheques sumados: ventas={ventas_temp}, pax={pax_temp}, cheques={cheques_temp}")
    except Exception as e:
        logging.warning(f"Error consultando tempcheques {server['name']}: {e} - continuando sin ventas del día")
    
    # Mes anterior (mismos días) - Usar formato seguro
    # NOTA: Se excluyen propinas de las ventas SI la columna existe
    fia = fecha_ini_ant.replace('-', '')
    ffa = fecha_fin_ant.replace('-', '')
    query_ant = f"""
SELECT ISNULL(SUM(cheques.total{propina_expr}), 0) as ventas, ISNULL(SUM(cheques.nopersonas), 0) as pax, COUNT(DISTINCT cheques.folio) as cheques
FROM cheques INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{fia}' AND CONVERT(varchar, turnos.apertura, 112) <= '{ffa}' AND cheques.cancelado = 0
"""
    try:
        r_ant = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], query_ant)
        ventas_ant = float(r_ant[0]['ventas'] or 0) if r_ant else 0
        pax_ant = int(r_ant[0]['pax'] or 0) if r_ant else 0
        cheques_ant = int(r_ant[0]['cheques'] or 0) if r_ant else 0
    except Exception:
        ventas_ant, pax_ant, cheques_ant = 0, 0, 0
    
    # Año anterior (mismos días) - Usar formato seguro
    # NOTA: Se excluyen propinas de las ventas SI la columna existe
    fiaa = fecha_ini_año_ant.replace('-', '')
    ffaa = fecha_fin_año_ant.replace('-', '')
    query_año = f"""
SELECT ISNULL(SUM(cheques.total{propina_expr}), 0) as ventas, ISNULL(SUM(cheques.nopersonas), 0) as pax, COUNT(DISTINCT cheques.folio) as cheques
FROM cheques INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{fiaa}' AND CONVERT(varchar, turnos.apertura, 112) <= '{ffaa}' AND cheques.cancelado = 0
"""
    try:
        r_año = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], query_año)
        ventas_año = float(r_año[0]['ventas'] or 0) if r_año else 0
        pax_año = int(r_año[0]['pax'] or 0) if r_año else 0
        cheques_año = int(r_año[0]['cheques'] or 0) if r_año else 0
    except Exception:
        ventas_año, pax_año, cheques_año = 0, 0, 0
    
    # Cálculos
    ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
    cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
    
    # Proyección mes completo
    proyeccion = round((ventas / dias_transcurridos) * dias_mes, 2) if dias_transcurridos > 0 else 0
    
    # Variaciones %
    var_vs_mes_ant = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
    var_vs_año_ant = round(((ventas - ventas_año) / ventas_año * 100), 1) if ventas_año > 0 else 0
    var_pax_mes = round(((pax - pax_ant) / pax_ant * 100), 1) if pax_ant > 0 else 0
    var_pax_año = round(((pax - pax_año) / pax_año * 100), 1) if pax_año > 0 else 0
    var_cheques_mes = round(((cheques - cheques_ant) / cheques_ant * 100), 1) if cheques_ant > 0 else 0
    var_cheques_año = round(((cheques - cheques_año) / cheques_año * 100), 1) if cheques_año > 0 else 0
    
    return {
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
        "cheque_prom": cheque_prom
    }


def get_kpis_mpro(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes):
    """Query reutilizable para MPRO - ventas desde tabla Venta"""
    
    # Formato YYYYMMDD para MPRO
    fi = fecha_ini.replace('-', '')
    ff = fecha_fin.replace('-', '')
    
    # Extraer mes y año de fecha_fin para usarlos en recálculos (importante para multiselección de meses)
    mes_final = int(fecha_fin[5:7])  # Mes de fecha_fin (ej: 04 para abril)
    anio_final = int(fecha_fin[:4])  # Año de fecha_fin
    
    # PASO 1: Detectar el último día real con ventas en el período
    # IMPORTANTE: Usar CONVERT con formato 112 para evitar problemas de configuración regional
    query_ultimo_dia = f"""
SELECT MAX(CONVERT(DATE, Vn_Fecha)) as ultimo_dia_venta
FROM Venta
WHERE CONVERT(varchar, Vn_Fecha, 112) >= '{fi}' AND CONVERT(varchar, Vn_Fecha, 112) <= '{ff}'
  AND ISNULL(Es_Cve_Estado, '') <> 'CA'
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
            
            logging.info(f"MPRO {server['name']} - Último día con ventas: {anio_ultimo}-{mes_ultimo:02d}-{dia_con_datos:02d}")
            
            # CORRECCIÓN: Usar el mes y año del último día con ventas, no del mes inicial
            ff = f"{anio_ultimo}{str(mes_ultimo).zfill(2)}{str(dia_con_datos).zfill(2)}"
            
            # Calcular días transcurridos desde fecha_ini hasta el último día con ventas
            fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
            fecha_ultimo_dt = datetime(anio_ultimo, mes_ultimo, dia_con_datos)
            dias_transcurridos = (fecha_ultimo_dt - fecha_ini_dt).days + 1
            
            logging.info(f"MPRO {server['name']} - Período ajustado: {fi} a {ff}, días: {dias_transcurridos}")
            
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
            # Extraer mes_min de fecha_ini
            mes_min = int(fecha_ini[5:7])
            anio_pasado = int(fecha_ini[:4]) - 1
            
            # fecha_ini_año_ant: primer día del primer mes del año anterior
            fecha_ini_año_ant = f"{anio_pasado}-{str(mes_min).zfill(2)}-01"
            
            # fecha_fin_año_ant: mismo día del año anterior
            max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_ultimo)[1]
            dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
            fecha_fin_año_ant = f"{anio_pasado}-{str(mes_ultimo).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
            
            logging.info(f"MPRO Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
    except Exception as e:
        logging.warning(f"MPRO Error detectando último día: {e}")
    
    # MPRO usa Vn_Folio para identificar tickets y Vn_Precio_Neto_Importe para el monto de venta
    # IMPORTANTE: Usar CONVERT para evitar problemas de configuración regional
    query = f"""
SELECT 
    COUNT(DISTINCT Vn_Folio) as cheques,
    ISNULL(SUM(Vn_Precio_Neto_Importe), 0) as ventas
FROM Venta
WHERE CONVERT(varchar, Vn_Fecha, 112) >= '{fi}' AND CONVERT(varchar, Vn_Fecha, 112) <= '{ff}'
  AND ISNULL(Es_Cve_Estado, '') <> 'CA'
"""
    try:
        result = execute_sql_query(server['host'], server['port'], server['database'], 
                                   server['username'], server['password'], query)
        if result and len(result) > 0:
            ventas = float(result[0]['ventas'] or 0)
            cheques = int(result[0]['cheques'] or 0)
        else:
            ventas, cheques = 0, 0
        logging.info(f"MPRO {server['name']}: Ventas={ventas}, Cheques={cheques}")
    except Exception as e:
        logging.warning(f"Error consultando MPRO {server['name']}: {e}")
        return None
    
    # MPRO no tiene PAX normalmente, estimamos como cheques
    pax = cheques
    
    # Mes anterior - Usar CONVERT para compatibilidad
    fia = fecha_ini_ant.replace('-', '')
    ffa = fecha_fin_ant.replace('-', '')
    query_ant = f"""
SELECT ISNULL(SUM(Vn_Precio_Neto_Importe), 0) as ventas, COUNT(DISTINCT Vn_Folio) as cheques
FROM Venta WHERE CONVERT(varchar, Vn_Fecha, 112) >= '{fia}' AND CONVERT(varchar, Vn_Fecha, 112) <= '{ffa}' AND ISNULL(Es_Cve_Estado, '') <> 'CA'
"""
    try:
        r_ant = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], query_ant)
        ventas_ant = float(r_ant[0]['ventas'] or 0) if r_ant else 0
        cheques_ant = int(r_ant[0]['cheques'] or 0) if r_ant else 0
    except Exception:
        ventas_ant, cheques_ant = 0, 0
    pax_ant = cheques_ant
    
    # Año anterior - Usar CONVERT para compatibilidad
    fiaa = fecha_ini_año_ant.replace('-', '')
    ffaa = fecha_fin_año_ant.replace('-', '')
    query_año = f"""
SELECT ISNULL(SUM(Vn_Precio_Neto_Importe), 0) as ventas, COUNT(DISTINCT Vn_Folio) as cheques
FROM Venta WHERE CONVERT(varchar, Vn_Fecha, 112) >= '{fiaa}' AND CONVERT(varchar, Vn_Fecha, 112) <= '{ffaa}' AND ISNULL(Es_Cve_Estado, '') <> 'CA'
"""
    try:
        r_año = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], query_año)
        ventas_año = float(r_año[0]['ventas'] or 0) if r_año else 0
        cheques_año = int(r_año[0]['cheques'] or 0) if r_año else 0
    except Exception:
        ventas_año, cheques_año = 0, 0
    pax_año = cheques_año
    
    # Cálculos
    ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
    cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
    proyeccion = round((ventas / dias_transcurridos) * dias_mes, 2) if dias_transcurridos > 0 else 0
    
    # Variaciones %
    var_vs_mes_ant = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
    var_vs_año_ant = round(((ventas - ventas_año) / ventas_año * 100), 1) if ventas_año > 0 else 0
    var_pax_mes = round(((pax - pax_ant) / pax_ant * 100), 1) if pax_ant > 0 else 0
    var_pax_año = round(((pax - pax_año) / pax_año * 100), 1) if pax_año > 0 else 0
    var_cheques_mes = round(((cheques - cheques_ant) / cheques_ant * 100), 1) if cheques_ant > 0 else 0
    var_cheques_año = round(((cheques - cheques_año) / cheques_año * 100), 1) if cheques_año > 0 else 0
    
    return {
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
        "cheque_prom": cheque_prom
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
                    
                    unidades.append({
                        "unidad": suc['nombre'],
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
                        "origen": "api_local"
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
            unidades_offline.append({
                "unidad": suc['nombre'],
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
                "message": "API local no disponible - Sin datos de ventas del día"
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
        
        unidades.append({
            "unidad": sucursal_nombre,
            "sucursal": sucursal_nombre,  # Para filtrar en endpoints de detalle
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
            "cheque_prom": cheque_prom
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
