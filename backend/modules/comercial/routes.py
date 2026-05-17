"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🔒 MÓDULO BLINDADO - NO MODIFICAR 🔒                    ║
╠════════════════════════════════════════════════════════════════════════════╣
║ ESTADO: FUNCIONAL Y OPERATIVO (Abril 2026)                                 ║
║                                                                            ║
║ Este módulo ha sido validado y estabilizado. Cualquier modificación        ║
║ debe ser aprobada por el equipo de arquitectura y probada en entorno       ║
║ de staging antes de aplicarse a producción.                                ║
║                                                                            ║
║ ENDPOINTS BLINDADOS:                                                       ║
║ - GET /comercial/tablero-ejecutivo                                         ║
║ - GET /comercial/dashboard/{server_id}                                     ║
║ - GET /comercial/sucursales/{server_id}                                    ║
║ - GET /comercial/metas/{server_id}                                         ║
║                                                                            ║
║ ÚLTIMA VALIDACIÓN: 24-Abril-2026                                           ║
╚════════════════════════════════════════════════════════════════════════════╝

EDARSA HUB - Comercial Module Routes
====================================
Endpoints del módulo comercial.

FASE 5B DEL REFACTOR MODULAR (Abril 2026):

ESTADO ACTUAL:
- ✅ Adapters (APIs locales MPRO) migrados a adapters.py
- ✅ Helpers del tablero migrados a service.py (Fase 5B-2)
- ✅ Endpoint /comercial/tablero-ejecutivo migrado (Fase 5B-3)
- ✅ Endpoints /comercial/sucursales y /comercial/metas migrados (Fase 5B-4A)
- ✅ Endpoints /comercial/ticket-perfecto y /comercial/ventas-tiempo migrados (Fase 5B-4C)
- ✅ Endpoints /comercial/mesas y /comercial/detalle-movimientos migrados (Fase 5B-4E)
- ✅ Endpoint /comercial/precios-constantes migrado (Fase 5B-4G)
- ✅ Endpoint /comercial/reporte-pax migrado (Fase 5B-4H)
- ✅ Endpoint /comercial/dashboard migrado (Fase 5B-5B) - CIERRE MÓDULO COMERCIAL
- ✅ SourceQueryResult aplicado a Dashboard (Abril 2026)

COMPONENTES MIGRADOS:
1. adapters.py:
   - APIS_MPRO_LOCALES (configuración)
   - query_api_mpro_local()
   - obtener_ventas_dia_api_local()
   - sumar_ventas_api_local_a_sucursal()

2. service.py:
   - get_kpis_softrestaurant()
   - get_kpis_mpro()
   - get_kpis_mpro_por_sucursal()

3. routes.py (este archivo):
   - GET /comercial/tablero-ejecutivo (Fase 5B-3)
   - GET /comercial/sucursales/{server_id} (Fase 5B-4A)
   - GET /comercial/metas/{server_id} (Fase 5B-4A)
   - GET /comercial/ticket-perfecto/{server_id} (Fase 5B-4C)
   - GET /comercial/ventas-tiempo/{server_id} (Fase 5B-4C)
   - GET /comercial/mesas/{server_id} (Fase 5B-4E)
   - GET /comercial/detalle-movimientos/{server_id} (Fase 5B-4E)
   - GET /comercial/precios-constantes/{server_id} (Fase 5B-4G)
   - GET /comercial/reporte-pax/{server_id} (Fase 5B-4H)
   - GET /comercial/dashboard/{server_id} (Fase 5B-5B)

ENDPOINTS PENDIENTES (0 en server.py):
- NINGUNO - Módulo Comercial 100% migrado
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Dict, List
import logging
import calendar
from datetime import datetime, timedelta, timezone

from core.db import execute_sql_query
from core.security import (
    get_current_user, 
    user_has_server_access,
    get_user_empresas_permitidas,
    get_servers_for_empresas,
)
from core.user_access_context import (
    resolve_user_access_context,
    has_server_access,
    has_empresa_access,
    has_permiso,
    UserAccessContext,
)
from core.source_resolver import QueryStatus, SourceQueryResult
from core.db import (
    check_column_exists, 
    get_propina_safe_column, 
    get_propina_safe_column_tempcheques,
    execute_sql_query_params  # FASE SQL-SAFE: Queries parametrizadas
)
from core.utils.date_filters import (
    DateFilterPolicy,
    to_yyyymmdd,
    build_sql_date_filter_safe,
    build_sql_date_equals_safe,
)
from modules.comercial.service import (
    get_kpis_softrestaurant,
    get_kpis_mpro,
    get_kpis_mpro_por_sucursal,
    # P0: Nuevas estructuras de respuesta
    build_unit_response,
    classify_connection_error,
    DataStatus,
    LiveStatus,
    CacheStatus,
    SourceUsed,
    SourceRealStatus,
)
# BLOQUE 5.1: Import de queries centralizadas para migración de dashboard
from modules.comercial.queries.softrestaurant import query_ventas_periodo_sr
# BLOQUE 5.2: Import de query MPRO centralizada con filtro flexible
from modules.comercial.queries.mpro import query_ventas_periodo_mpro_con_filtro_flexible
from modules.comercial.adapters import (
    sumar_ventas_api_local_a_sucursal,
    obtener_ventas_dia_api_local,
)
from modules.comercial.repository import (
    get_servers_for_tablero,
    get_server_by_id,
    get_cached_kpis,
    save_kpis_cache,
    get_cached_kpis_by_prefix,
    save_server_connection_status,
    get_server_connection_status,
    is_server_recently_offline,
    should_attempt_live_query,  # FASE P0: Clasificación LIVE-C/SYNC-S/HUB
    filtrar_unidades_por_visibilidad,
    get_sucursales_visibles_config,
    save_dashboard_cache,
    get_dashboard_cache,
    # FASE ARQUITECTURA: Resolución centralizada
    get_sucursal_nombre,
    get_api_config_from_server,
    EDARSAHUB_CONFIG,
    USE_SQL_FOR_SERVERS,
)

# =============================================================================
# FIX 2026-05-15: Import de Ventana Operativa para FechaOperacion correcta
# REGLA: El tablero debe mostrar FechaOperacion activa, NO fecha calendario
# =============================================================================
from core.utils.operational_window import get_operational_window
# FASE 3A.2: Import de utilidades de normalización de system_type
from core.server_registry import list_unidades_negocio
from core.system_type_utils import (
    normalize_system_type,
    is_mpro_system,
    is_softrestaurant_system,
    is_api_system,
    is_supported_system_type,
    get_system_type_label,
)

# Router - los endpoints serán migrados incrementalmente
router = APIRouter(tags=["comercial"])


# ============================================================================
# HELPER: Formato de fecha universal para SQL Server
# ============================================================================
def sql_fecha(fecha_str: str, con_hora: bool = True, hora: str = "00:00:00") -> str:
    """
    Convierte fecha a formato universal para SQL Server.
    Formato YYYYMMDD funciona en CUALQUIER configuración regional (español, inglés, etc.)
    
    Args:
        fecha_str: Fecha en formato YYYY-MM-DD
        con_hora: Si incluir hora (default True para compatibilidad)
        hora: Hora a usar (default 00:00:00)
    
    Returns:
        String formateado para SQL: 'YYYYMMDD HH:MM:SS' o 'YYYYMMDD'
        
    Ejemplos:
        sql_fecha('2026-04-01') -> '20260401 00:00:00'
        sql_fecha('2026-04-01', hora='23:59:59') -> '20260401 23:59:59'
        sql_fecha('2026-04-01', con_hora=False) -> '20260401'
    """
    fecha_limpia = fecha_str.replace('-', '')
    if con_hora:
        return f"{fecha_limpia} {hora}"
    return fecha_limpia


# ============================================================================
# BLINDAJE RBAC - VALIDACIÓN DE ACCESO A SERVIDORES (FASE 6-8 BARRIDO)
# ============================================================================

async def validate_server_access_rbac(current_user: Dict, server_id: str) -> UserAccessContext:
    """
    Validación unificada de acceso a servidor usando resolve_user_access_context().
    
    FASE 6-8: Esta función ahora usa la función centralizada de contexto de acceso.
    NUNCA confía en parámetros del frontend.
    
    Args:
        current_user: Usuario autenticado
        server_id: ID del servidor a validar
        
    Returns:
        UserAccessContext si tiene acceso
        
    Raises:
        HTTPException 403 si no tiene acceso
    """
    # Resolver contexto de acceso completo
    context = await resolve_user_access_context(current_user)
    
    # Validar acceso al servidor usando la función centralizada
    if has_server_access(context, server_id):
        return context
    
    # No tiene acceso
    logging.warning(
        f"[RBAC-DENEGADO] Usuario {current_user.get('email')} "
        f"sin acceso a servidor {server_id}. "
        f"Fuente: {context.fuente_acceso}, Servidores permitidos: {context.servers_ids}"
    )
    raise HTTPException(
        status_code=403, 
        detail=f"No tiene acceso a este servidor. Fuente de acceso: {context.fuente_acceso}"
    )


async def get_user_context_or_403(current_user: Dict) -> UserAccessContext:
    """
    Obtiene el contexto de acceso del usuario.
    Para endpoints que no requieren un server_id específico.
    """
    context = await resolve_user_access_context(current_user)
    
    # Verificar que el usuario tiene algún acceso (al menos un servidor o acceso global)
    if not context.tiene_acceso_global and not context.servers_ids:
        logging.warning(
            f"[RBAC-DENEGADO] Usuario {current_user.get('email')} "
            f"sin acceso a ningún servidor"
        )
        raise HTTPException(
            status_code=403, 
            detail="No tiene acceso a ningún servidor configurado"
        )
    
    return context


# =============================================================================
# FALLBACK EDARSAHUB: Snapshots de Ventas del Día (BUG-ARQUITECTONICO FIX)
# =============================================================================
# Cuando solo_ventas_dia=True y la conexión SQL falla, usamos el snapshot
# de Comercial_Ventas_Dia_Abiertas_v2 en EDARSAHUB como fallback.
# REGLA: NUNCA mostrar "Fuente no disponible" si hay snapshot válido.
# =============================================================================
# FIX 2026-05-15: Usar FechaOperacion activa, NO fecha calendario
# REGLA DE NEGOCIO: A las 00:30 del día 15, si el restaurante cierra a las 03:00,
# todavía pertenece a la jornada del día 14. El tablero debe mostrar ventas del 14.
# =============================================================================

def get_ventas_dia_snapshot_from_edarsahub(server_id: str, fecha_operacion: str = None, unidad_negocio_id: str = None) -> Dict:
    """
    Obtiene snapshot de ventas del día desde EDARSAHUB.
    Tabla: Comercial_Ventas_Dia_Abiertas_v2
    
    FIX 2026-05-15: Ahora calcula FechaOperacion usando operational_window.py
    en lugar de datetime.now().date() (fecha calendario).
    
    Args:
        server_id: ID del servidor
        fecha_operacion: Fecha en formato YYYY-MM-DD (si se provee explícitamente)
        unidad_negocio_id: ID de la unidad para calcular FechaOperacion (opcional, pero recomendado)
    
    Returns:
        Dict con datos del snapshot o None si no existe
        {
            'exists': True/False,
            'ventas': Decimal,
            'pax': int,
            'cheques': int,
            'ticket_promedio': Decimal,
            'snapshot_timestamp': datetime,
            'estado_dato': 'VIGENTE' | 'DESACTUALIZADO' | 'MUY_DESACTUALIZADO',
            'minutos_desde_sync': int,
            'fuente': 'EDARSAHUB_SNAPSHOT',
            'fecha_operacion_usada': str  # Para debug
        }
    """
    from datetime import datetime, timezone
    import pytz
    
    mexico_tz = pytz.timezone('America/Mexico_City')
    now_mx = datetime.now(mexico_tz)
    
    # =================================================================
    # FIX 2026-05-15: Calcular FechaOperacion activa
    # =================================================================
    if fecha_operacion is None:
        if unidad_negocio_id:
            # Usar ventana operativa de la unidad específica
            fecha_op_calc, hora_ini, hora_fin, cruza = get_operational_window(unidad_negocio_id, now_mx)
            fecha_operacion = fecha_op_calc.isoformat()
            logging.info(
                f"[EDARSAHUB-SNAPSHOT] {unidad_negocio_id}: FechaOperacion calculada = {fecha_operacion} "
                f"(hora actual = {now_mx.strftime('%H:%M')}, horario = {hora_ini}-{hora_fin})"
            )
        else:
            # Sin unidad específica: usar horario por defecto 13:00-06:00
            # ACTUALIZACIÓN 16-May-2026: Corte operativo cambiado de 03:00 a 06:00
            hora_actual = now_mx.time()
            from datetime import time as dt_time, timedelta
            hora_fin_default = dt_time(6, 0, 0)
            
            if hora_actual < hora_fin_default:
                # Estamos entre 00:00 y 06:00: pertenece al día anterior
                fecha_operacion = (now_mx.date() - timedelta(days=1)).isoformat()
            else:
                fecha_operacion = now_mx.date().isoformat()
            
            logging.info(
                f"[EDARSAHUB-SNAPSHOT] server_id={server_id}: FechaOperacion default = {fecha_operacion} "
                f"(hora actual = {now_mx.strftime('%H:%M')}, usando horario default 13:00-06:00)"
            )
    
    # Query a EDARSAHUB
    query = f"""
    SELECT 
        unidad_negocio_id,
        unidad_negocio_nombre,
        server_id,
        sucursal_id,
        sucursal_nombre,
        snapshot_timestamp,
        fecha_operacion,
        ventas_abiertas,
        tickets_abiertos,
        pax_abiertos,
        ventas_cerradas_dia,
        tickets_cerrados_dia,
        pax_cerrados_dia,
        total_estimado_dia,
        fecha_ultima_actualizacion
    FROM Comercial_Ventas_Dia_Abiertas_v2
    WHERE server_id = '{server_id}'
      AND fecha_operacion = '{fecha_operacion}'
    """
    
    try:
        # Usar configuración EDARSAHUB del repository
        result = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        if not result or len(result) == 0:
            logging.info(f"[EDARSAHUB-FALLBACK] Sin snapshot para server_id={server_id}, fecha={fecha_operacion}")
            return {'exists': False, 'estado_dato': 'SIN_DATOS_HOY'}
        
        # Agregar todos los registros de este servidor (puede haber múltiples sucursales)
        total_ventas = 0
        total_pax = 0
        total_cheques = 0
        ultima_sync = None
        
        for row in result:
            total_ventas += float(row.get('total_estimado_dia') or 0)
            total_pax += int(row.get('pax_abiertos') or 0) + int(row.get('pax_cerrados_dia') or 0)
            total_cheques += int(row.get('tickets_abiertos') or 0) + int(row.get('tickets_cerrados_dia') or 0)
            
            row_sync = row.get('fecha_ultima_actualizacion') or row.get('snapshot_timestamp')
            if row_sync and (ultima_sync is None or row_sync > ultima_sync):
                ultima_sync = row_sync
        
        # Calcular estado de frescura
        minutos_desde_sync = 0
        estado_dato = 'VIGENTE'
        
        if ultima_sync:
            now = datetime.now()
            if isinstance(ultima_sync, str):
                ultima_sync = datetime.fromisoformat(ultima_sync.replace('Z', '+00:00'))
            
            # Si tiene timezone, normalizar
            if ultima_sync.tzinfo is not None:
                now = datetime.now(timezone.utc)
            
            diff = now - ultima_sync
            minutos_desde_sync = int(diff.total_seconds() / 60)
            
            if minutos_desde_sync <= 15:
                estado_dato = 'VIGENTE'
            elif minutos_desde_sync <= 60:
                estado_dato = 'DESACTUALIZADO'
            else:
                estado_dato = 'MUY_DESACTUALIZADO'
        
        ticket_promedio = total_ventas / total_cheques if total_cheques > 0 else 0
        
        logging.info(
            f"[EDARSAHUB-FALLBACK] Snapshot encontrado para server_id={server_id}: "
            f"ventas=${total_ventas:,.2f}, cheques={total_cheques}, estado={estado_dato}, "
            f"minutos_desde_sync={minutos_desde_sync}"
        )
        
        return {
            'exists': True,
            'ventas': total_ventas,
            'pax': total_pax,
            'cheques': total_cheques,
            'ticket_promedio': ticket_promedio,
            'snapshot_timestamp': ultima_sync,
            'estado_dato': estado_dato,
            'minutos_desde_sync': minutos_desde_sync,
            'fuente': 'EDARSAHUB_SNAPSHOT',
            'fecha_operacion_usada': fecha_operacion  # FIX 2026-05-15: Para debug
        }
        
    except Exception as e:
        logging.error(f"[EDARSAHUB-FALLBACK] Error consultando snapshot: {e}")
        return {'exists': False, 'estado_dato': 'ERROR_QUERY', 'error': str(e)}



@router.get("/comercial/tablero-ejecutivo")
async def tablero_ejecutivo(
    mes: int = Query(default=0),  # 0 = mes actual (legacy, compatibilidad)
    anio: int = Query(default=0),  # 0 = año actual, -1 = ventas del día (legacy)
    meses: str = Query(default=""),  # "01,02,03" - Lista de meses (nuevo, multiselección)
    anios: str = Query(default=""),  # "2025,2024" - Lista de años (nuevo, multiselección)
    periodo: str = Query(default="mes"),  # dia, semana, mes (nuevo)
    tipo_comparacion: str = Query(default="dias_equiv"),  # dias_equiv o mes_completo (nuevo)
    current_user: Dict = Depends(get_current_user)
):
    """
    Tablero ejecutivo con KPIs de TODAS las unidades.
    Comparativo vs mes anterior y año anterior (mismos días).
    Soporta multiselección de meses y años (homologado con Dashboard Comercial).
    anio=-1 o anios="-1": Modo "Ventas del Día" - solo tempcheques (ventas sin corte).
    
    BLINDAJE (Abril 2026): Este endpoint NUNCA debe fallar. Siempre retorna una
    respuesta válida, incluso si todos los servidores están caídos.
    """
    # =========================================================================
    # BLINDAJE NIVEL 1: Try-catch global
    # =========================================================================
    try:
        return await _tablero_ejecutivo_internal(mes, anio, meses, anios, periodo, tipo_comparacion, current_user)
    except Exception as e:
        # BLINDAJE: Si todo falla, retornar respuesta de emergencia
        import traceback
        logging.error(f"[TABLERO-BLINDAJE] Error crítico en tablero ejecutivo: {e}")
        logging.error(f"[TABLERO-BLINDAJE] Traceback: {traceback.format_exc()}")
        hoy = datetime.now()
        return {
            "periodo": {
                "mes": hoy.month,
                "anio": hoy.year,
                "dias_transcurridos": hoy.day,
                "dias_mes": 30,
                "modo_ventas_dia": False,
                "error": True,
                "error_message": f"Error temporal del sistema: {str(e)[:100]}"
            },
            "comparativo_con": {"mes_anterior": "N/A", "año_anterior": "N/A"},
            "unidades": [],
            "totales": {
                "ventas": 0, "ventas_ant": 0, "ventas_año": 0, "ventas_año_completo": 0,
                "pax": 0, "pax_ant": 0, "pax_año": 0,
                "cheques": 0, "cheques_ant": 0, "cheques_año": 0,
                "proyeccion": 0, "pendiente_cerrar": 0, "tickets_abiertos": 0,
                "var_vs_mes_ant": 0, "var_vs_año_ant": 0, "var_pax_mes": 0, "var_pax_año": 0,
                "var_cheques_mes": 0, "var_cheques_año": 0, "ticket_prom": 0, "cheque_prom": 0,
                "var_proy_vs_año": 0, "unidades_año_ant": 0
            },
            "status": "error",
            "message": "El sistema experimentó un error temporal. Los datos se cargarán cuando la conexión se restablezca."
        }


async def _tablero_ejecutivo_internal(
    mes: int,
    anio: int,
    meses: str,
    anios: str,
    periodo: str,
    tipo_comparacion: str,
    current_user: Dict
):
    """Lógica interna del tablero ejecutivo (separada para blindaje)."""
    hoy = datetime.now()
    
    # Detectar modo "Ventas del Día" (anio=-1 legacy o anios="-1" nuevo o meses="ventas_dia")
    solo_ventas_dia = (anio == -1) or (anios == "-1") or (meses == "ventas_dia")
    
    # Procesar parámetros nuevos (multiselección) o legacy (simple)
    mes_min = None  # Para multiselección de meses
    mes_max = None
    
    logging.info(f"TABLERO DEBUG: anio={anio}, anios='{anios}', meses='{meses}', solo_ventas_dia={solo_ventas_dia}")
    
    # CORRECCIÓN: Asignar mes_min/mes_max para modo Ventas del Día
    if solo_ventas_dia:
        # Ventas del día usa el mes actual
        mes = hoy.month
        mes_min = mes
        mes_max = mes
    elif meses and meses != "ventas_dia":
        # Nuevo formato: multiselección de meses (solo si son números)
        try:
            lista_meses = [int(m.strip()) for m in meses.split(',') if m.strip() and m.strip().isdigit()]
            if lista_meses:
                mes_min = min(lista_meses)  # Primer mes del rango
                mes_max = max(lista_meses)  # Último mes del rango
                mes = mes_max  # Para compatibilidad con lógica existente
            else:
                # Si no hay meses válidos, usar mes actual
                mes = hoy.month
                mes_min = mes
                mes_max = mes
        except ValueError:
            # Si falla la conversión, usar mes actual
            mes = hoy.month
            mes_min = mes
            mes_max = mes
    elif mes == 0:
        mes = hoy.month
        mes_min = mes
        mes_max = mes
    else:
        mes_min = mes
        mes_max = mes
    
    if anios and anios != "-1":
        # Nuevo formato: multiselección de años
        lista_anios = [int(a.strip()) for a in anios.split(',') if a.strip()]
        anio = max(lista_anios)  # Usar el año más reciente
    elif anio == 0 or anio == -1:
        if not solo_ventas_dia:
            anio = hoy.year
        else:
            anio = hoy.year  # Para ventas del día, usar año actual
    
    # Fechas del período actual - CORREGIDO para multiselección de meses
    # VALIDACIÓN: Si el mes solicitado es FUTURO respecto al actual, ajustar al mes actual
    if mes_min is None:
        logging.warning(f"TABLERO: mes_min es None, asignando hoy.month={hoy.month}")
        mes_min = hoy.month
        mes_max = hoy.month
    if anio == hoy.year and mes_min > hoy.month:
        # El mes solicitado aún no ha llegado - ajustar al mes actual
        logging.info(f"Tablero: Mes solicitado {mes_min} es futuro (actual: {hoy.month}), ajustando a mes actual")
        mes_min = hoy.month
        mes_max = hoy.month
    elif anio == hoy.year and mes_max > hoy.month:
        # El rango incluye meses futuros - limitar al mes actual
        mes_max = hoy.month
    
    # fecha_ini: primer día del PRIMER mes seleccionado
    fecha_ini = f"{anio}-{mes_min:02d}-01"
    
    # =========================================================================
    # REGLA CANÓNICA: FechaOperacionActual con corte a las 06:00 AM
    # ACTUALIZACIÓN 16-May-2026: La proyección usa FechaOperacionActual.day
    # =========================================================================
    # ProyecciónMensual = VentasAcumuladas / DiasTranscurridosOperativos * DiasMes
    #
    # Donde:
    # - DiasTranscurridosOperativos = FechaOperacionActual.day
    # - FechaOperacionActual se calcula con timezone México y corte 06:00 AM
    #
    # Ejemplo: Hoy es 16 de mayo a las 05:30 AM México:
    # - FechaOperacionActual = 15 (porque < 06:00)
    # - DiasTranscurridosOperativos = 15
    #
    # Ejemplo: Hoy es 16 de mayo a las 08:00 AM México:
    # - FechaOperacionActual = 16 (porque >= 06:00)
    # - DiasTranscurridosOperativos = 16
    #
    # Queda PROHIBIDO usar:
    # - Último día con datos en EDARSAHUB como divisor
    # - MAX(fecha) como divisor
    # - Días con venta como divisor
    # =========================================================================
    try:
        from zoneinfo import ZoneInfo
        tz_mexico = ZoneInfo('America/Mexico_City')
    except ImportError:
        import pytz
        tz_mexico = pytz.timezone('America/Mexico_City')
    
    ahora_mexico = datetime.now(tz_mexico)
    hora_actual = ahora_mexico.hour
    
    # Calcular FechaOperacionActual con corte a las 06:00
    if hora_actual < 6:
        # Antes de las 06:00: FechaOperacion = día anterior
        fecha_operacion_actual = ahora_mexico.date() - timedelta(days=1)
    else:
        # Desde las 06:00: FechaOperacion = día actual
        fecha_operacion_actual = ahora_mexico.date()
    
    logging.info(f"[TABLERO-EJECUTIVO] Hora México={hora_actual}:xx, FechaOperacionActual={fecha_operacion_actual}")
    
    # fecha_fin: depende de si el último mes es el actual o ya pasó
    if anio == hoy.year and mes_max == hoy.month:
        # Mes actual - usar FechaOperacionActual
        fecha_fin = fecha_operacion_actual.strftime('%Y-%m-%d')
        fecha_inicio_dt = datetime(anio, mes_min, 1)
        # DiasTranscurridosOperativos = FechaOperacionActual.day
        dias_transcurridos = fecha_operacion_actual.day
        logging.info(f"[TABLERO-EJECUTIVO] Mes actual: fecha_fin={fecha_fin}, dias_transcurridos={dias_transcurridos}")
    else:
        # Todos los meses seleccionados ya pasaron - usar meses completos
        ultimo_dia = calendar.monthrange(anio, mes_max)[1]
        fecha_fin = f"{anio}-{mes_max:02d}-{ultimo_dia:02d}"
        # Calcular días totales del rango completo
        fecha_inicio_dt = datetime(anio, mes_min, 1)
        fecha_fin_dt = datetime(anio, mes_max, ultimo_dia)
        dias_transcurridos = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    # Calcular días totales del período (si todo el rango estuviera completo)
    if mes_max == 12:
        fecha_fin_completo = datetime(anio + 1, 1, 1) - timedelta(days=1)
    else:
        fecha_fin_completo = datetime(anio, mes_max + 1, 1) - timedelta(days=1)
    fecha_inicio_dt = datetime(anio, mes_min, 1)
    dias_mes = (fecha_fin_completo - fecha_inicio_dt).days + 1
    
    # Mes anterior (para comparar vs período anterior)
    if mes_min == 1:
        mes_ant_ini = 12 - (mes_max - mes_min)  # Mismo número de meses, pero del año anterior
        if mes_ant_ini < 1:
            mes_ant_ini = 1
        mes_ant_fin = 12
        anio_mes_ant = anio - 1
    else:
        # Período anterior del mismo año
        meses_en_rango = mes_max - mes_min + 1
        mes_ant_ini = mes_min - meses_en_rango
        if mes_ant_ini < 1:
            mes_ant_ini = 1
        mes_ant_fin = mes_min - 1
        anio_mes_ant = anio
    
    fecha_ini_ant = f"{anio_mes_ant}-{mes_ant_ini:02d}-01"
    # Para período anterior, usar mismos días transcurridos
    ultimo_dia_ant = calendar.monthrange(anio_mes_ant, mes_ant_fin)[1]
    fecha_fin_ant = f"{anio_mes_ant}-{mes_ant_fin:02d}-{ultimo_dia_ant:02d}"
    
    # Año anterior (MISMO RANGO DE MESES Y DÍAS - esto es lo que estaba mal)
    # Si estamos viendo 01-ene a 08-abr 2026, comparar con 01-ene a 08-abr 2025
    fecha_ini_año_ant = f"{anio-1}-{mes_min:02d}-01"
    
    # Calcular el día final del año anterior equivalente
    if anio == hoy.year and mes_max >= hoy.month:
        # Si estamos en el año actual y el mes actual está en el rango,
        # comparar hasta el mismo día del año anterior
        if mes_max == hoy.month:
            dia_fin_año_ant = min(hoy.day - 1, calendar.monthrange(anio-1, mes_max)[1])
        else:
            dia_fin_año_ant = min(hoy.day, calendar.monthrange(anio-1, mes_max)[1])
        fecha_fin_año_ant = f"{anio-1}-{mes_max:02d}-{dia_fin_año_ant:02d}"
    else:
        # Meses completos, comparar con meses completos del año anterior
        ultimo_dia_año_ant = calendar.monthrange(anio-1, mes_max)[1]
        fecha_fin_año_ant = f"{anio-1}-{mes_max:02d}-{ultimo_dia_año_ant:02d}"
    
    # Año anterior MES COMPLETO (para comparar proyección vs período completo)
    ultimo_dia_año_ant_completo = calendar.monthrange(anio-1, mes_max)[1]
    f"{anio-1}-{mes_max:02d}-{ultimo_dia_año_ant_completo:02d}"
    
    logging.info(f"Tablero Ejecutivo: {mes_min}-{mes_max}/{anio} ({fecha_ini} a {fecha_fin}), días: {dias_transcurridos}/{dias_mes}")
    logging.info(f"Tablero Ejecutivo - Año anterior: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
    
    # ============= GUARD CLAUSE: Rango invertido (primer día del mes actual) =============
    # EXCEPCIÓN: No aplicar si es modo Ventas del Día (debe consultar operación en curso)
    if fecha_fin < fecha_ini and not solo_ventas_dia:
        logging.warning(f"Tablero Ejecutivo: Rango invertido detectado ({fecha_ini} a {fecha_fin}). Sin días cerrados del mes actual.")
        return {
            "periodo": {
                "mes": mes,
                "anio": anio,
                "dias_transcurridos": 0,
                "dias_mes": dias_mes,
                "modo_ventas_dia": solo_ventas_dia,
                "motivo": "SIN_DIAS_CERRADOS_MES_ACTUAL",
                "mensaje": "Sin días cerrados del mes actual. La proyección iniciará cuando exista al menos un corte cerrado del mes."
            },
            "comparativo_con": {
                "mes_anterior": f"{mes_ant_ini}-{mes_ant_fin}/{anio_mes_ant}",
                "año_anterior": f"{mes_min}-{mes_max}/{anio-1}"
            },
            "unidades": [],
            "totales": {
                "ventas": 0, "ventas_ant": 0, "ventas_año": 0, "ventas_año_completo": 0,
                "pax": 0, "pax_ant": 0, "pax_año": 0,
                "cheques": 0, "cheques_ant": 0, "cheques_año": 0,
                "proyeccion": 0, "pendiente_cerrar": 0, "tickets_abiertos": 0,
                "var_vs_mes_ant": 0, "var_vs_año_ant": 0,
                "var_pax_mes": 0, "var_pax_año": 0,
                "var_cheques_mes": 0, "var_cheques_año": 0,
                "ticket_prom": 0, "cheque_prom": 0, "var_proy_vs_año": 0, "unidades_año_ant": 0
            },
            "status_summary": {
                "total_unidades": 0,
                "unidades_data_ok": 0,
                "unidades_data_cache": 0,
                "unidades_data_error": 0,
                "unidades_no_data": 0,
                "unidades_live_connected": 0,
                "unidades_live_unreachable": 0,
                "unidades_source_real": 0,
                "unidades_source_cache": 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    
    # Obtener todos los servidores activos Y visibles en operaciones
    servers = await get_servers_for_tablero()
    logging.info(f"Servidores encontrados: {len(servers)} - Tipos: {[s['system_type'] for s in servers]}")
    
    # FASE 6-8: Filtrar servidores usando resolve_user_access_context()
    # NUNCA confiar en parámetros del frontend
    context = await resolve_user_access_context(current_user)
    
    if not context.tiene_acceso_global:
        # Filtrar solo a los servidores del contexto del usuario
        servers = [s for s in servers if s['id'] in context.servers_ids]
        logging.info(
            f"[RBAC] Usuario {current_user.get('email')}: "
            f"{len(servers)} servidores permitidos "
            f"(Fuente: {context.fuente_acceso})"
        )
    else:
        logging.info(f"[RBAC] Usuario {current_user.get('email')}: Acceso global - todos los servidores")
    
    resultados = []
    totales = {"ventas": 0, "ventas_ant": 0, "ventas_año": 0, "ventas_año_completo": 0, "pax": 0, "pax_ant": 0, "pax_año": 0, 
               "cheques": 0, "cheques_ant": 0, "cheques_año": 0, "proyeccion": 0,
               "pendiente_cerrar": 0, "tickets_abiertos": 0}  # Agregado para ventas del día
    
    periodo_key = f"{anio}-{mes:02d}"
    
    for server in servers:
        # =========================================================================
        # BLINDAJE NIVEL 2: Try-catch por servidor individual
        # =========================================================================
        try:
            logging.info(f"Procesando servidor: {server['name']} - Tipo: {server['system_type']}")
            
            # FASE P0: Determinar tipo de dato según el modo
            # - solo_ventas_dia=True: LIVE-C (ventas sin corte, crítico al segundo)
            # - Solo mes actual (días cerrados): SYNC-S (tolera 15 min)
            # - Mes/año anterior: HUB (usar cache si disponible)
            if solo_ventas_dia:
                data_type = "LIVE-C"
            else:
                data_type = "HUB"  # El tablero normal usa datos consolidados
            
            # =================================================================
            # FIX CIRCUIT BREAKER HUB (2026-05-17):
            # Para modo HUB, SIEMPRE intentar leer de EDARSAHUB SQL.
            # 
            # RAZÓN: get_kpis_softrestaurant() lee de EDARSAHUB SQL (no del 
            # servidor local), por lo que el circuit breaker de servidor local
            # NO debe bloquear esta consulta.
            #
            # REGLA:
            # - HUB: should_try = True (EDARSAHUB SQL es la fuente)
            # - LIVE-C: Aplicar circuit breaker normal (conexión a servidor real)
            # =================================================================
            if data_type == "HUB":
                # EDARSAHUB SQL siempre disponible - no aplicar circuit breaker
                should_try = True
                logging.info(f"[HUB-EDARSAHUB] {server['name']}: Modo HUB - lectura directa desde EDARSAHUB SQL (circuit breaker ignorado)")
            else:
                # LIVE-C: Aplicar circuit breaker normal para conexiones reales
                should_try = await should_attempt_live_query(server['id'], data_type)
            
            # FASE 3A.2: Migrado a helper centralizado
            if is_softrestaurant_system(server.get('system_type')):
                kpis = None
                sr_error_captured = None
                
                if should_try:
                    try:
                        kpis = get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant,
                                                       fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia)
                    except Exception as sr_error:
                        logging.warning(f"[BLINDAJE] Error SoftRestaurant {server['name']}: {sr_error}")
                        sr_error_captured = sr_error
                        kpis = None
                    
                    # =================================================================
                    # FIX CIRCUIT BREAKER HUB (2026-05-17):
                    # Para modo HUB, NO guardar estado de conexión en MongoDB.
                    # La consulta es a EDARSAHUB SQL, no al servidor local.
                    # Solo guardar estado para modo LIVE-C (conexión real).
                    # =================================================================
                    if data_type != "HUB":
                        if kpis and not kpis.get('error'):
                            # LIVE-C: Conexión exitosa al servidor real
                            await save_server_connection_status(server['id'], True)
                        elif not solo_ventas_dia:
                            # LIVE-C: Marcar offline solo si NO es ventas del día
                            await save_server_connection_status(server['id'], False)
                else:
                    # Este bloque ya no se ejecuta para HUB (should_try siempre True)
                    logging.info(f"[FASE P0] Servidor {server['name']} offline - usando caché (tipo: {data_type})")
                
                # ================================================================
                # P0: CONSTRUIR RESPUESTA CON ESTRUCTURA ESTÁNDAR
                # ================================================================
                if kpis and not kpis.get('error'):
                    # CASO A: Consulta exitosa desde EDARSAHUB SQL
                    # FIX 2026-05-17: Para HUB, la fuente es EDARSAHUB_SQL, no servidor local
                    source_period = "EDARSAHUB_SQL" if data_type == "HUB" else "SQL"
                    source_live = "EDARSAHUB_SQL" if data_type == "HUB" else ("TEMPCHEQUES" if solo_ventas_dia else "SQL")
                    
                    logging.info(f"[P0-LOG] tablero_real_source_success: server={server['name']}, ventas={kpis.get('ventas', 0)}, source={source_period}")
                    
                    unit_response = build_unit_response(
                        server=server,
                        kpis=kpis,
                        data_status=DataStatus.DATA_OK,
                        live_status=LiveStatus.LIVE_NOT_APPLICABLE if data_type == "HUB" else LiveStatus.LIVE_CONNECTED,
                        cache_status=CacheStatus.NOT_USED,
                        source_used=SourceUsed.REAL_SOURCE,
                        source_real_attempted=True,
                        source_real_status=SourceRealStatus.SUCCESS,
                        source_period=source_period,
                        source_live=source_live,
                    )
                    resultados.append(unit_response)
                    
                    # Guardar en caché (solo si NO es ventas del día)
                    if not solo_ventas_dia:
                        await save_kpis_cache(server['id'], periodo_key, kpis)
                    
                    # Acumular totales
                    for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                              "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                        totales[k] += kpis.get(k, 0)
                    
                    # Acumular pendiente por cerrar (solo ventas del día)
                    if solo_ventas_dia:
                        totales["pendiente_cerrar"] += kpis.get("pendiente_cerrar", 0)
                        totales["tickets_abiertos"] += kpis.get("tickets_abiertos", 0)
                        
                elif kpis and kpis.get('error'):
                    # CASO E: Error específico devuelto por el servicio (query error, etc.)
                    error_code = kpis.get('error', 'UNKNOWN_ERROR')
                    error_mensaje = kpis.get('mensaje', 'Error desconocido')
                    logging.warning(f"[P0-LOG] tablero_real_source_query_error: server={server['name']}, error={error_code}")
                    
                    # P0 REGLA: NO usar caché si hay error de query/mapping/permisos
                    unit_response = build_unit_response(
                        server=server,
                        kpis=None,  # NO incluir KPIs por error de query
                        data_status=DataStatus.DATA_ERROR,
                        live_status=LiveStatus.LIVE_CONNECTED,  # Conectado pero error de query
                        cache_status=CacheStatus.NOT_USED,
                        source_used=SourceUsed.NONE,
                        source_real_attempted=True,
                        source_real_status=SourceRealStatus.QUERY_ERROR,
                        source_period="NONE",
                        source_live="ERROR",
                        error_code=error_code,
                        error_message=error_mensaje,
                    )
                    resultados.append(unit_response)
                    
                elif sr_error_captured:
                    # CASO con excepción capturada - determinar tipo de error
                    live_status, source_real_status = classify_connection_error(sr_error_captured, server)
                    logging.warning(f"[P0-LOG] tablero_real_source_connection_error: server={server['name']}, live_status={live_status}")
                    
                    if solo_ventas_dia:
                        # =================================================================
                        # BUG-ARQUITECTONICO FIX: Fallback a EDARSAHUB para Ventas del Día
                        # REGLA: Nunca mostrar "Fuente no disponible" si hay snapshot válido
                        # =================================================================
                        snapshot = get_ventas_dia_snapshot_from_edarsahub(server['id'])
                        
                        if snapshot.get('exists'):
                            # SNAPSHOT ENCONTRADO: Usar datos de EDARSAHUB
                            estado_dato = snapshot.get('estado_dato', 'DESACTUALIZADO')
                            minutos = snapshot.get('minutos_desde_sync', 0)
                            
                            # Construir KPIs desde el snapshot
                            kpis_snapshot = {
                                'ventas': snapshot.get('ventas', 0),
                                'pax': snapshot.get('pax', 0),
                                'cheques': snapshot.get('cheques', 0),
                                'ticket_promedio': snapshot.get('ticket_promedio', 0),
                                'pendiente_cerrar': snapshot.get('ventas', 0),  # Ventas abiertas = pendiente
                                'tickets_abiertos': snapshot.get('cheques', 0),
                                # Comparativos no disponibles en snapshot
                                'ventas_ant': 0,
                                'ventas_año': 0,
                                'pax_ant': 0,
                                'pax_año': 0,
                                'cheques_ant': 0,
                                'cheques_año': 0,
                                'proyeccion': 0,
                            }
                            
                            # Determinar mensaje según frescura
                            if estado_dato == 'VIGENTE':
                                cache_warning = f"Último dato sincronizado hace {minutos} min"
                                data_status_val = DataStatus.DATA_FROM_CACHE  # Reusamos el status
                            elif estado_dato == 'DESACTUALIZADO':
                                cache_warning = f"Última sincronización: hace {minutos} min (desactualizado)"
                                data_status_val = DataStatus.DATA_FROM_CACHE
                            else:
                                cache_warning = f"Última sincronización fallida, mostrando último dato válido ({minutos} min)"
                                data_status_val = DataStatus.DATA_FROM_CACHE
                            
                            logging.info(f"[EDARSAHUB-FALLBACK] Usando snapshot para {server['name']}: ventas=${kpis_snapshot['ventas']:,.2f}, estado={estado_dato}")
                            
                            unit_response = build_unit_response(
                                server=server,
                                kpis=kpis_snapshot,
                                data_status=data_status_val,
                                live_status=live_status,
                                cache_status=CacheStatus.USED_CONNECTION_FALLBACK,
                                source_used=SourceUsed.CACHE,  # Semánticamente es EDARSAHUB snapshot
                                source_real_attempted=True,
                                source_real_status=source_real_status,
                                source_period="EDARSAHUB_SNAPSHOT",
                                source_live="NOT_AVAILABLE",
                                cache_warning=cache_warning,
                            )
                            resultados.append(unit_response)
                            
                            # Acumular totales del snapshot
                            totales["ventas"] += kpis_snapshot.get('ventas', 0)
                            totales["pax"] += kpis_snapshot.get('pax', 0)
                            totales["cheques"] += kpis_snapshot.get('cheques', 0)
                            totales["pendiente_cerrar"] += kpis_snapshot.get('pendiente_cerrar', 0)
                            totales["tickets_abiertos"] += kpis_snapshot.get('tickets_abiertos', 0)
                        else:
                            # SIN SNAPSHOT: Mostrar mensaje específico (no genérico)
                            estado_sin_datos = snapshot.get('estado_dato', 'SIN_DATOS_HOY')
                            logging.warning(f"[EDARSAHUB-FALLBACK] Sin snapshot para {server['name']}: estado={estado_sin_datos}")
                            
                            unit_response = build_unit_response(
                                server=server,
                                kpis=None,
                                data_status=DataStatus.NO_DATA_CONFIRMED,
                                live_status=live_status,
                                cache_status=CacheStatus.MISSING,
                                source_used=SourceUsed.NONE,
                                source_real_attempted=True,
                                source_real_status=source_real_status,
                                source_period="NONE",
                                source_live="NOT_AVAILABLE",
                                error_code="NO_SNAPSHOT",
                                error_message="Sin datos del día en EDARSAHUB",
                            )
                            resultados.append(unit_response)
                    else:
                        # =================================================================
                        # FIX CIRCUIT BREAKER HUB (2026-05-17):
                        # Para modo HUB, NO usar caché MongoDB como fallback.
                        # Si EDARSAHUB SQL falla, reportar error SQL directamente.
                        # MongoDB NO debe ser fuente productiva de datos.
                        # =================================================================
                        if data_type == "HUB":
                            # HUB: Reportar error SQL, NO usar caché MongoDB
                            logging.warning(f"[HUB-EDARSAHUB-ERROR] {server['name']}: Error leyendo EDARSAHUB SQL - NO hay fallback MongoDB")
                            
                            unit_response = build_unit_response(
                                server=server,
                                kpis=None,
                                data_status=DataStatus.DATA_ERROR,
                                live_status=LiveStatus.LIVE_NOT_APPLICABLE,
                                cache_status=CacheStatus.NOT_USED,
                                source_used=SourceUsed.NONE,
                                source_real_attempted=True,
                                source_real_status=source_real_status,
                                source_period="EDARSAHUB_SQL_ERROR",
                                source_live="NOT_APPLICABLE",
                                error_code="EDARSAHUB_SQL_ERROR",
                                error_message=f"Error consultando EDARSAHUB SQL: {str(sr_error_captured)[:100]}",
                            )
                            resultados.append(unit_response)
                        else:
                            # LIVE-C: Mantener fallback a caché MongoDB (conexión real fallida)
                            cached = await get_cached_kpis(server['id'], periodo_key)
                            if cached and cached.get('kpis'):
                                kpis_cached = cached['kpis']
                                logging.info(f"[P0-LOG] tablero_cache_used_connection_fallback: server={server['name']}")
                                
                                unit_response = build_unit_response(
                                    server=server,
                                    kpis=kpis_cached,
                                    data_status=DataStatus.DATA_FROM_CACHE,
                                    live_status=live_status,
                                    cache_status=CacheStatus.USED_CONNECTION_FALLBACK,
                                    source_used=SourceUsed.CACHE,
                                    source_real_attempted=True,
                                    source_real_status=source_real_status,
                                    source_period="CACHE_VALIDATED",
                                    source_live="NOT_USED",
                                    cache_warning=f"Mostrando último dato disponible (cache: {cached.get('updated_at', 'N/A')})",
                                )
                                resultados.append(unit_response)
                                
                                # Acumular totales del caché
                                for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                                          "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                                    totales[k] += kpis_cached.get(k, 0)
                            else:
                                # Sin caché disponible
                                unit_response = build_unit_response(
                                    server=server,
                                    kpis=None,
                                    data_status=DataStatus.DATA_ERROR,
                                    live_status=live_status,
                                    cache_status=CacheStatus.MISSING,
                                    source_used=SourceUsed.NONE,
                                    source_real_attempted=True,
                                    source_real_status=source_real_status,
                                    source_period="NONE",
                                    source_live="ERROR",
                                    error_code="NO_CACHE",
                                    error_message="Conexión no disponible y sin datos en caché",
                                )
                                resultados.append(unit_response)
                            
                elif not should_try:
                    # CASO: No se intentó conexión (servidor marcado como offline)
                    logging.info(f"[P0-LOG] tablero_cache_lookup: server={server['name']}, reason=server_offline")
                    
                    cached = await get_cached_kpis(server['id'], periodo_key)
                    if cached and cached.get('kpis'):
                        kpis_cached = cached['kpis']
                        
                        unit_response = build_unit_response(
                            server=server,
                            kpis=kpis_cached,
                            data_status=DataStatus.DATA_FROM_CACHE,
                            live_status=LiveStatus.LIVE_UNREACHABLE_REAL,
                            cache_status=CacheStatus.USED_CONNECTION_FALLBACK,
                            source_used=SourceUsed.CACHE,
                            source_real_attempted=False,
                            source_real_status=SourceRealStatus.CONNECTION_ERROR,
                            source_period="CACHE_VALIDATED",
                            source_live="NOT_USED",
                            cache_warning=f"Servidor marcado offline - usando caché ({cached.get('updated_at', 'N/A')})",
                        )
                        resultados.append(unit_response)
                        
                        for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                                  "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                            totales[k] += kpis_cached.get(k, 0)
                    else:
                        unit_response = build_unit_response(
                            server=server,
                            kpis=None,
                            data_status=DataStatus.NO_DATA_CONFIRMED,
                            live_status=LiveStatus.LIVE_UNREACHABLE_REAL,
                            cache_status=CacheStatus.MISSING,
                            source_used=SourceUsed.NONE,
                            source_real_attempted=False,
                            source_real_status=SourceRealStatus.CONNECTION_ERROR,
                            source_period="NONE",
                            source_live="NOT_USED",
                            error_code="NO_DATA",
                            error_message="Sin datos disponibles - servidor offline y sin caché",
                        )
                        resultados.append(unit_response)
                else:
                    # CASO: kpis es None sin excepción (conexión fallida silenciosa)
                    logging.warning(f"[P0-LOG] tablero_real_source_connection_error: server={server['name']}, silent_fail=True")
                    
                    if solo_ventas_dia:
                        # =================================================================
                        # BUG-ARQUITECTONICO FIX: Fallback a EDARSAHUB (caso silent fail)
                        # =================================================================
                        snapshot = get_ventas_dia_snapshot_from_edarsahub(server['id'])
                        
                        if snapshot.get('exists'):
                            estado_dato = snapshot.get('estado_dato', 'DESACTUALIZADO')
                            minutos = snapshot.get('minutos_desde_sync', 0)
                            
                            kpis_snapshot = {
                                'ventas': snapshot.get('ventas', 0),
                                'pax': snapshot.get('pax', 0),
                                'cheques': snapshot.get('cheques', 0),
                                'ticket_promedio': snapshot.get('ticket_promedio', 0),
                                'pendiente_cerrar': snapshot.get('ventas', 0),
                                'tickets_abiertos': snapshot.get('cheques', 0),
                                'ventas_ant': 0, 'ventas_año': 0,
                                'pax_ant': 0, 'pax_año': 0,
                                'cheques_ant': 0, 'cheques_año': 0,
                                'proyeccion': 0,
                            }
                            
                            if estado_dato == 'VIGENTE':
                                cache_warning = f"Último dato sincronizado hace {minutos} min"
                            else:
                                cache_warning = f"Última sincronización: hace {minutos} min (desactualizado)"
                            
                            logging.info(f"[EDARSAHUB-FALLBACK] Usando snapshot (silent) para {server['name']}: ventas=${kpis_snapshot['ventas']:,.2f}")
                            
                            unit_response = build_unit_response(
                                server=server,
                                kpis=kpis_snapshot,
                                data_status=DataStatus.DATA_FROM_CACHE,
                                live_status=LiveStatus.LIVE_UNREACHABLE_PREVIEW_ENV,
                                cache_status=CacheStatus.USED_CONNECTION_FALLBACK,
                                source_used=SourceUsed.CACHE,
                                source_real_attempted=True,
                                source_real_status=SourceRealStatus.CONNECTION_ERROR,
                                source_period="EDARSAHUB_SNAPSHOT",
                                source_live="NOT_AVAILABLE",
                                cache_warning=cache_warning,
                            )
                            resultados.append(unit_response)
                            
                            totales["ventas"] += kpis_snapshot.get('ventas', 0)
                            totales["pax"] += kpis_snapshot.get('pax', 0)
                            totales["cheques"] += kpis_snapshot.get('cheques', 0)
                            totales["pendiente_cerrar"] += kpis_snapshot.get('pendiente_cerrar', 0)
                            totales["tickets_abiertos"] += kpis_snapshot.get('tickets_abiertos', 0)
                        else:
                            unit_response = build_unit_response(
                                server=server,
                                kpis=None,
                                data_status=DataStatus.NO_DATA_CONFIRMED,
                                live_status=LiveStatus.LIVE_UNREACHABLE_PREVIEW_ENV,
                                cache_status=CacheStatus.MISSING,
                                source_used=SourceUsed.NONE,
                                source_real_attempted=True,
                                source_real_status=SourceRealStatus.CONNECTION_ERROR,
                                source_period="NONE",
                                source_live="NOT_AVAILABLE",
                                error_code="NO_SNAPSHOT",
                                error_message="Sin datos del día en EDARSAHUB",
                            )
                            resultados.append(unit_response)
                    else:
                        # HUB: Intentar caché
                        cached = await get_cached_kpis(server['id'], periodo_key)
                        if cached and cached.get('kpis'):
                            kpis_cached = cached['kpis']
                            
                            unit_response = build_unit_response(
                                server=server,
                                kpis=kpis_cached,
                                data_status=DataStatus.DATA_FROM_CACHE,
                                live_status=LiveStatus.LIVE_UNREACHABLE_PREVIEW_ENV,
                                cache_status=CacheStatus.USED_CONNECTION_FALLBACK,
                                source_used=SourceUsed.CACHE,
                                source_real_attempted=True,
                                source_real_status=SourceRealStatus.CONNECTION_ERROR,
                                source_period="CACHE_VALIDATED",
                                source_live="NOT_USED",
                                cache_warning=f"Usando caché - conexión no disponible ({cached.get('updated_at', 'N/A')})",
                            )
                            resultados.append(unit_response)
                            
                            for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                                      "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                                totales[k] += kpis_cached.get(k, 0)
                        else:
                            unit_response = build_unit_response(
                                server=server,
                                kpis=None,
                                data_status=DataStatus.NO_DATA_CONFIRMED,
                                live_status=LiveStatus.LIVE_UNREACHABLE_PREVIEW_ENV,
                                cache_status=CacheStatus.MISSING,
                                source_used=SourceUsed.NONE,
                                source_real_attempted=True,
                                source_real_status=SourceRealStatus.CONNECTION_ERROR,
                                source_period="NONE",
                                source_live="NOT_USED",
                                error_code="NO_CACHE",
                                error_message="Sin datos disponibles - fuente caída y sin histórico",
                            )
                            resultados.append(unit_response)
            
            # FASE 3A.2: Migrado a helper centralizado
            elif is_mpro_system(server.get('system_type')):
                # MPRO: Dividir por sucursal (igual que en Inventarios)
                logging.info(f"Procesando servidor MPRO: {server['name']}")
                
                try:
                    unidades_mpro = get_kpis_mpro_por_sucursal(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant,
                                                               fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia)
                    logging.info(f"MPRO {server['name']}: Encontradas {len(unidades_mpro)} unidades")
                    
                    # FILTRAR por configuración de visibilidad de sucursales
                    unidades_mpro = await filtrar_unidades_por_visibilidad(unidades_mpro, server['id'])
                    logging.info(f"MPRO {server['name']}: {len(unidades_mpro)} unidades después de filtro de visibilidad")
                    
                    # Marcar estado de conexión exitosa
                    await save_server_connection_status(server['id'], True)
                    
                    for unidad in unidades_mpro:
                        # P0: Construir respuesta estándar para cada unidad MPRO
                        unidad_nombre = unidad.get('unidad', 'unknown')
                        
                        if unidad.get("source_status") == "NO_DATA" or unidad.get("status") == "offline":
                            # Unidad con datos desde caché o sin datos
                            logging.info(f"[P0-LOG] tablero_mpro_unit_cache: unidad={unidad_nombre}")
                            
                            unit_response = build_unit_response(
                                server=server,
                                kpis=unidad if unidad.get('ventas') else None,
                                data_status=DataStatus.DATA_FROM_CACHE if unidad.get('ventas') else DataStatus.NO_DATA_CONFIRMED,
                                live_status=LiveStatus.LIVE_API_UNREACHABLE if unidad.get("status") == "offline" else LiveStatus.LIVE_CONNECTED,
                                cache_status=CacheStatus.USED_CONNECTION_FALLBACK if unidad.get('ventas') else CacheStatus.MISSING,
                                source_used=SourceUsed.CACHE if unidad.get('ventas') else SourceUsed.NONE,
                                source_real_attempted=True,
                                source_real_status=SourceRealStatus.API_UNREACHABLE if unidad.get("status") == "offline" else SourceRealStatus.SUCCESS,
                                source_period="CACHE_VALIDATED" if unidad.get('ventas') else "NONE",
                                source_live="NOT_USED",
                                sucursal=unidad_nombre,
                                cache_warning=unidad.get('message') if unidad.get("status") == "offline" else None,
                            )
                        else:
                            # Unidad con datos reales
                            # FIX CIRCUIT BREAKER HUB (17-May-2026):
                            # Determinar source_period según el origen real de los datos
                            origen = unidad.get('origen', 'unknown')
                            if origen == 'api_local':
                                source_period_mpro = "MPRO_API_LOCAL"
                                source_live_mpro = "LOCAL_API"
                                live_status_mpro = LiveStatus.LIVE_CONNECTED
                            elif origen == 'EDARSAHUB_SQL':
                                source_period_mpro = "EDARSAHUB_SQL"
                                source_live_mpro = "EDARSAHUB_SQL"
                                live_status_mpro = LiveStatus.LIVE_NOT_APPLICABLE
                            else:
                                # SQL genérico (bases MPRO directas) - NO debe ocurrir en modo HUB
                                source_period_mpro = "MPRO_SQL_DIRECT"
                                source_live_mpro = "SQL_DIRECT"
                                live_status_mpro = LiveStatus.LIVE_CONNECTED
                            
                            logging.info(f"[P0-LOG] tablero_real_source_success: unidad={unidad_nombre}, ventas={unidad.get('ventas', 0)}, origen={origen}, source_period={source_period_mpro}")
                            
                            unit_response = build_unit_response(
                                server=server,
                                kpis=unidad,
                                data_status=DataStatus.DATA_OK,
                                live_status=live_status_mpro,
                                cache_status=CacheStatus.NOT_USED,
                                source_used=SourceUsed.REAL_SOURCE,
                                source_real_attempted=True,
                                source_real_status=SourceRealStatus.SUCCESS,
                                source_period=source_period_mpro,
                                source_live=source_live_mpro,
                                sucursal=unidad_nombre,
                            )
                        
                        resultados.append(unit_response)
                        
                        # Guardar en caché cada unidad (solo si tiene datos)
                        if unidad.get("source_status") != "NO_DATA" and unidad.get('ventas'):
                            unidad_cache_key = f"{periodo_key}-{unidad_nombre}"
                            await save_kpis_cache(server['id'], unidad_cache_key, unidad)
                        
                        # Acumular totales
                        for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                                  "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                            totales[k] += unidad.get(k, 0) or 0
                            
                except Exception as mpro_error:
                    logging.error(f"[P0-LOG] tablero_mpro_error: server={server['name']}, error={mpro_error}")
                    await save_server_connection_status(server['id'], False)
                    
                    live_status, source_real_status = classify_connection_error(mpro_error, server)
                    
                    if solo_ventas_dia:
                        # LIVE-C: Fuente no disponible, NO usar caché
                        unit_response = build_unit_response(
                            server=server,
                            kpis=None,
                            data_status=DataStatus.DATA_ERROR,
                            live_status=live_status,
                            cache_status=CacheStatus.NOT_USED,
                            source_used=SourceUsed.NONE,
                            source_real_attempted=True,
                            source_real_status=source_real_status,
                            source_period="NONE",
                            source_live="ERROR",
                            error_code="MPRO_ERROR",
                            error_message=f"Fuente MPRO no disponible: {str(mpro_error)[:100]}",
                        )
                        resultados.append(unit_response)
                    else:
                        # HUB: Buscar en caché para MPRO
                        cached_list = await get_cached_kpis_by_prefix(server['id'], periodo_key)
                        if cached_list:
                            for cached in cached_list:
                                if cached.get('kpis'):
                                    kpis_cached = cached['kpis']
                                    logging.info(f"[P0-LOG] tablero_cache_used_connection_fallback: server={server['name']}, unidad={kpis_cached.get('unidad')}")
                                    
                                    unit_response = build_unit_response(
                                        server=server,
                                        kpis=kpis_cached,
                                        data_status=DataStatus.DATA_FROM_CACHE,
                                        live_status=live_status,
                                        cache_status=CacheStatus.USED_CONNECTION_FALLBACK,
                                        source_used=SourceUsed.CACHE,
                                        source_real_attempted=True,
                                        source_real_status=source_real_status,
                                        source_period="CACHE_VALIDATED",
                                        source_live="NOT_USED",
                                        sucursal=kpis_cached.get('unidad'),
                                        cache_warning=f"Datos de caché - error: {str(mpro_error)[:50]}",
                                    )
                                    resultados.append(unit_response)
                                    
                                    for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                                              "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                                        totales[k] += kpis_cached.get(k, 0)
                        else:
                            # Sin caché disponible
                            unit_response = build_unit_response(
                                server=server,
                                kpis=None,
                                data_status=DataStatus.NO_DATA_CONFIRMED,
                                live_status=live_status,
                                cache_status=CacheStatus.MISSING,
                                source_used=SourceUsed.NONE,
                                source_real_attempted=True,
                                source_real_status=source_real_status,
                                source_period="NONE",
                                source_live="NOT_USED",
                                error_code="NO_CACHE",
                                error_message="Sin datos MPRO disponibles - fuente caída y sin histórico",
                            )
                            resultados.append(unit_response)
        except Exception as server_error:
            # =========================================================================
            # BLINDAJE NIVEL 2: Captura de error por servidor individual
            # =========================================================================
            logging.error(f"[P0-LOG] tablero_server_error: server={server.get('name', 'UNKNOWN')}, error={server_error}")
            
            # P0: Construir respuesta con estructura estándar
            live_status, source_real_status = classify_connection_error(server_error, server)
            
            unit_response = build_unit_response(
                server=server,
                kpis=None,  # NO incluir KPIs para evitar ceros falsos
                data_status=DataStatus.DATA_ERROR,
                live_status=live_status,
                cache_status=CacheStatus.NOT_USED,
                source_used=SourceUsed.NONE,
                source_real_attempted=True,
                source_real_status=source_real_status,
                source_period="NONE",
                source_live="ERROR",
                error_code="SERVER_ERROR",
                error_message=f"Error temporal: {str(server_error)[:80]}",
            )
            resultados.append(unit_response)
    
    # Calcular variaciones de totales
    totales["var_vs_mes_ant"] = round(((totales["ventas"] - totales["ventas_ant"]) / totales["ventas_ant"] * 100), 1) if totales["ventas_ant"] > 0 else 0
    totales["var_vs_año_ant"] = round(((totales["ventas"] - totales["ventas_año"]) / totales["ventas_año"] * 100), 1) if totales["ventas_año"] > 0 else 0
    totales["var_pax_mes"] = round(((totales["pax"] - totales["pax_ant"]) / totales["pax_ant"] * 100), 1) if totales["pax_ant"] > 0 else 0
    totales["var_pax_año"] = round(((totales["pax"] - totales["pax_año"]) / totales["pax_año"] * 100), 1) if totales["pax_año"] > 0 else 0
    totales["var_cheques_mes"] = round(((totales["cheques"] - totales["cheques_ant"]) / totales["cheques_ant"] * 100), 1) if totales["cheques_ant"] > 0 else 0
    totales["var_cheques_año"] = round(((totales["cheques"] - totales["cheques_año"]) / totales["cheques_año"] * 100), 1) if totales["cheques_año"] > 0 else 0
    totales["ticket_prom"] = round(totales["ventas"] / totales["pax"], 2) if totales["pax"] > 0 else 0
    totales["cheque_prom"] = round(totales["ventas"] / totales["cheques"], 2) if totales["cheques"] > 0 else 0
    
    # Estimar ventas del año anterior MES COMPLETO (proyección proporcional)
    # Si tenemos 7 días de año anterior con X ventas, el mes completo sería X * (días_mes / días_transcurridos)
    ventas_año_completo_estimado = (totales["ventas_año"] / dias_transcurridos * dias_mes) if dias_transcurridos > 0 and totales["ventas_año"] > 0 else 0
    totales["ventas_año_completo"] = round(ventas_año_completo_estimado, 0)
    
    # Proyección vs ventas año anterior MES COMPLETO (no solo los días equivalentes)
    totales["var_proy_vs_año"] = round(((totales["proyeccion"] - ventas_año_completo_estimado) / ventas_año_completo_estimado * 100), 1) if ventas_año_completo_estimado > 0 else 0
    
    # Contar unidades que tenían ventas el año anterior (ventas_año > 0)
    totales["unidades_año_ant"] = sum(1 for u in resultados if (u.get("ventas_año") or 0) > 0)
    
    # =========================================================================
    # P1 FIX (Dic 2025): DEDUPLICACIÓN POR unidad_negocio_codigo
    # REGLA: Cada unidad de negocio canónica debe aparecer UNA SOLA VEZ
    # CASO: LA ESTELAR aparecía 2 veces (caché válido + error de conexión)
    # =========================================================================
    
    # Construir mapa de server_id → codigo para resolver entradas con código vacío
    # FUENTE: EDARSAHUB.Unidades_Negocio (NO MongoDB)
    try:
        unidades_edarsahub = list_unidades_negocio(active_only=True)
        server_to_codigo_map = {}
        for u in unidades_edarsahub:
            sid = u.get('server_id', '')
            suc = u.get('sucursal_origen_id', '')
            codigo = u.get('codigo', '')
            # Para SoftRestaurant: 1 unidad por servidor (sucursal_origen_id es NULL)
            # Para MPRO: usar server_id + sucursal_origen_id (ya corregido en P0)
            if sid and not suc:  # SoftRestaurant
                server_to_codigo_map[sid] = codigo
    except Exception as e:
        logging.warning(f"[P1-DEDUP] Error cargando unidades EDARSAHUB: {e}")
        server_to_codigo_map = {}
    
    # Función para resolver código de deduplicación
    def resolver_codigo_dedup(unidad: Dict) -> str:
        """
        Resuelve el código canónico para deduplicación.
        Prioridad:
        1. unidad_negocio_codigo si existe
        2. Resolver desde EDARSAHUB por server_id (SoftRestaurant)
        3. Fallback defensivo: UNKNOWN:{server_id}
        """
        codigo = unidad.get('unidad_negocio_codigo', '').strip()
        if codigo:
            return codigo
        
        # Intentar resolver por server_id desde EDARSAHUB
        server_id = unidad.get('server_id', '')
        if server_id and server_id in server_to_codigo_map:
            codigo_resuelto = server_to_codigo_map[server_id]
            logging.info(f"[P1-DEDUP] Código resuelto via EDARSAHUB: server_id={server_id[:8]}... → {codigo_resuelto}")
            return codigo_resuelto
        
        # Fallback defensivo (no debería ocurrir si EDARSAHUB está bien configurado)
        logging.warning(f"[P1-DEDUP] No se pudo resolver código para server_id={server_id[:8]}...")
        return f"UNKNOWN:{server_id}" if server_id else "UNKNOWN"
    
    # Prioridad de estados para elegir la mejor entrada
    prioridad_status = {
        DataStatus.DATA_OK: 1,
        DataStatus.DATA_FROM_CACHE: 2,
        DataStatus.NO_DATA_CONFIRMED: 3,
        DataStatus.DATA_ERROR: 4,
    }
    
    # Deduplicar por código canónico
    resultados_dedup = {}
    for unidad in resultados:
        codigo_key = resolver_codigo_dedup(unidad)
        
        if codigo_key not in resultados_dedup:
            resultados_dedup[codigo_key] = unidad
        else:
            # Ya existe: comparar prioridad de data_status
            existente = resultados_dedup[codigo_key]
            prioridad_existente = prioridad_status.get(existente.get('data_status'), 99)
            prioridad_nueva = prioridad_status.get(unidad.get('data_status'), 99)
            
            if prioridad_nueva < prioridad_existente:
                # La nueva entrada tiene mejor estado → reemplazar
                logging.info(f"[P1-DEDUP] Reemplazando entrada: {codigo_key} ({existente.get('data_status')} → {unidad.get('data_status')})")
                resultados_dedup[codigo_key] = unidad
            else:
                # Conservar la existente (mejor o igual prioridad)
                # Opcionalmente guardar warning del error si la perdedora tiene error
                if unidad.get('data_status') == DataStatus.DATA_ERROR and unidad.get('error_message'):
                    logging.info(f"[P1-DEDUP] Descartando entrada duplicada con error: {codigo_key}")
    
    # Reemplazar resultados con lista deduplicada
    resultados_antes = len(resultados)
    resultados = list(resultados_dedup.values())
    if resultados_antes != len(resultados):
        logging.info(f"[P1-DEDUP] Deduplicación aplicada: {resultados_antes} → {len(resultados)} unidades")
    
    # =========================================================================
    # FIN P1 FIX DEDUPLICACIÓN
    # =========================================================================
    
    # ================================================================
    # P0 TAREA 9: CONSOLIDADO SUPERIOR CON ESTADOS SEPARADOS
    # ================================================================
    status_summary = {
        "total_unidades": len(resultados),
        "unidades_data_ok": sum(1 for u in resultados if u.get("data_status") == DataStatus.DATA_OK),
        "unidades_data_cache": sum(1 for u in resultados if u.get("data_status") == DataStatus.DATA_FROM_CACHE),
        "unidades_data_error": sum(1 for u in resultados if u.get("data_status") == DataStatus.DATA_ERROR),
        "unidades_no_data": sum(1 for u in resultados if u.get("data_status") == DataStatus.NO_DATA_CONFIRMED),
        "unidades_live_connected": sum(1 for u in resultados if u.get("live_status") == LiveStatus.LIVE_CONNECTED),
        "unidades_live_unreachable": sum(1 for u in resultados if u.get("live_status") in [
            LiveStatus.LIVE_UNREACHABLE_PREVIEW_ENV, 
            LiveStatus.LIVE_UNREACHABLE_REAL,
            LiveStatus.LIVE_API_UNREACHABLE
        ]),
        "unidades_source_real": sum(1 for u in resultados if u.get("source_used") == SourceUsed.REAL_SOURCE),
        "unidades_source_cache": sum(1 for u in resultados if u.get("source_used") == SourceUsed.CACHE),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Ordenar unidades de mayor a menor venta
    resultados_ordenados = sorted(resultados, key=lambda x: x.get('ventas') or 0, reverse=True)
    
    # Período para respuesta
    periodo_info = {
        "mes": mes, 
        "anio": anio, 
        "dias_transcurridos": dias_transcurridos, 
        "dias_mes": dias_mes,
        "modo_ventas_dia": solo_ventas_dia
    }
    
    # Si es modo ventas del día, ajustar el período para mostrarlo diferente
    if solo_ventas_dia:
        periodo_info["mes"] = 0
        periodo_info["anio"] = -1
        periodo_info["label"] = "Ventas del Día (sin corte)"
    
    logging.info(f"[P0-LOG] tablero_response_sent: unidades={len(resultados)}, data_ok={status_summary['unidades_data_ok']}, cache={status_summary['unidades_data_cache']}, error={status_summary['unidades_data_error']}")
    
    return {
        "periodo": periodo_info,
        "comparativo_con": {"mes_anterior": f"{mes_ant_ini}-{mes_ant_fin}/{anio_mes_ant}", "año_anterior": f"{mes_min}-{mes_max}/{anio-1}"},
        "unidades": resultados_ordenados,
        "totales": totales,
        "status_summary": status_summary,  # P0 TAREA 9: Resumen de estados
    }


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-4A (Abril 2026)
# ============================================================================

@router.get("/comercial/sucursales/{server_id}")
async def obtener_sucursales(
    server_id: str,
    include_hidden: bool = Query(default=False, description="Incluir sucursales ocultas (para admin)"),
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene las sucursales/empresas de un servidor, filtradas por configuración de visibilidad"""
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # BLINDAJE RBAC: Validar acceso unificado
    await validate_server_access_rbac(current_user, server_id)
    
    try:
        # FASE 3A.2: Migrado a helper centralizado
        if is_mpro_system(server.get('system_type')):
            # MPRO: Tabla sucursal (relacionada con venta por Sc_Cve_Sucursal)
            query = """
            SELECT Sc_Cve_Sucursal as id, Sc_Descripcion as nombre 
            FROM sucursal 
            WHERE Es_Cve_Estado = 'AC' 
            ORDER BY Sc_Descripcion
            """
        else:
            # SoftRestaurant: No tiene múltiples sucursales, devolver el servidor como única opción
            return {
                "servidor": server['name'],
                "sucursales": [{
                    "id": "all",
                    "nombre": server['name']
                }]
            }
        
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        ) or []
        
        sucursales = [{"id": r['id'], "nombre": r['nombre']} for r in result]
        
        # FILTRAR por configuración de visibilidad (si no es include_hidden)
        # FASE 3A.2: Migrado a helper centralizado
        if not include_hidden and is_mpro_system(server.get('system_type')):
            config = await get_sucursales_visibles_config(server_id)
            if config:  # Solo filtrar si hay configuración
                sucursales = [s for s in sucursales if config.get(s['nombre'], True)]
                logging.info(f"Sucursales filtradas por visibilidad: {len(sucursales)} de {len(result)}")
        
        # Agregar opción "Todas" al inicio
        sucursales.insert(0, {"id": "all", "nombre": "Todas las sucursales"})
        
        return {
            "servidor": server['name'],
            "system_type": server['system_type'],
            "sucursales": sucursales
        }
    except Exception as e:
        logging.error(f"Error obteniendo sucursales: {str(e)}")
        return {
            "servidor": server['name'],
            "sucursales": [{"id": "all", "nombre": server['name']}],
            "error": str(e)
        }


@router.get("/comercial/metas/{server_id}")
async def comercial_metas(
    server_id: str, 
    sucursal: str = Query(default=""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Metas de ventas por producto y vendedor.
    Nota: Las metas se configuran externamente, aquí mostramos ventas reales.
    
    RESPUESTA HOMOLOGADA:
    - source_status: SUCCESS | NO_DATA | DEGRADED_CACHE | SOURCE_UNREACHABLE | ERROR
    - cache_used: true/false
    - last_successful_sync: timestamp si se usó cache
    - data: {por_producto, por_vendedor}
    """
    from modules.comercial.cache_service import (
        SourceStatus, build_cache_key, get_cached_response, 
        save_to_cache, build_envelope_response
    )
    
    server = await get_server_by_id(server_id)
    if not server:
        return build_envelope_response(
            source_status=SourceStatus.ERROR,
            data={"por_producto": [], "por_vendedor": []},
            source_message="Servidor no encontrado"
        )
    
    # BLINDAJE RBAC: Validar acceso unificado
    await validate_server_access_rbac(current_user, server_id)
    
    # Construir clave de cache
    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
    hoy = datetime.now()
    cache_key = build_cache_key(
        modulo="comercial",
        endpoint="metas",
        server_id=server_id,
        sucursal=sucursal,
        fecha=hoy.strftime('%Y-%m-%d'),
        system_type=server.get('system_type', '')
    )
    
    # Función de respuesta vacía
    def empty_response():
        return {"por_producto": [], "por_vendedor": []}
    
    try:
        fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        
        metas_producto = []
        metas_vendedor = []
        query_success = False
        
        # FASE 3A.2: Migrado a helper centralizado
        if is_softrestaurant_system(server.get('system_type')):
            # Formato YYYYMMDD universal para SQL Server
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # Verificar si la tabla cheques tiene columna 'propina'
            has_propina = check_column_exists(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], 'cheques', 'propina'
            )
            propina_expr = get_propina_safe_column(has_propina)
            
            # Ventas por producto (top 10)
            query_productos = f"""
SELECT TOP 10
    p.descripcion as producto,
    SUM(cd.cantidad * cd.precio) as real_ventas
FROM cheqdet cd
INNER JOIN cheques ON cheques.folio = cd.foliodet
INNER JOIN productos p ON p.idproducto = cd.idproducto
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0
GROUP BY p.descripcion
ORDER BY SUM(cd.cantidad * cd.precio) DESC
"""
            result_prod = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_productos
            )
            
            if result_prod is not None:
                query_success = True
                for r in (result_prod or []):
                    real_ventas = float(r['real_ventas'] or 0)
                    meta_estimada = real_ventas * 1.1
                    cumplimiento = round((real_ventas / meta_estimada * 100), 0) if meta_estimada > 0 else 0
                    metas_producto.append({
                        "producto": r['producto'],
                        "meta": meta_estimada,
                        "real": real_ventas,
                        "cumplimiento": cumplimiento
                    })
            
            # Ventas por mesero/vendedor (excluyendo propinas SI existe la columna)
            query_vendedor = f"""
SELECT TOP 10
    ISNULL(m.nombre, 'Sin asignar') as vendedor,
    SUM(cheques.total{propina_expr}) as real_ventas
FROM cheques
LEFT JOIN meseros m ON m.idmesero = cheques.idmesero
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0
GROUP BY m.nombre
ORDER BY SUM(cheques.total{propina_expr}) DESC
"""
            result_vend = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_vendedor
            )
            
            if result_vend is not None:
                for r in (result_vend or []):
                    real_ventas = float(r['real_ventas'] or 0)
                    meta_estimada = real_ventas * 1.1
                    cumplimiento = round((real_ventas / meta_estimada * 100), 0) if meta_estimada > 0 else 0
                    metas_vendedor.append({
                        "vendedor": r['vendedor'],
                        "meta": meta_estimada,
                        "real": real_ventas,
                        "cumplimiento": cumplimiento
                    })
        
        # FASE 3A.2: Migrado a helper centralizado
        elif is_mpro_system(server.get('system_type')):
            # IMPLEMENTACIÓN MPRO (Abril 2026)
            # Formato YYYYMMDD para SQL Server
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # Filtro de sucursal para MPRO
            NOMBRE_A_CODIGO_SUCURSAL = {
                'ORIGEN': '0023',
                'QUERETARO': '0021',
                '130 QRO': '0021',
                'QRO': '0021',
            }
            sucursal_codigo = sucursal
            if sucursal and sucursal.upper() in NOMBRE_A_CODIGO_SUCURSAL:
                sucursal_codigo = NOMBRE_A_CODIGO_SUCURSAL[sucursal.upper()]
            filtro_sucursal = f"AND VE.Sc_Cve_Sucursal = '{sucursal_codigo}'" if sucursal and sucursal != 'all' else ""
            
            # Ventas por producto (top 10)
            # NOTA: En MPRO, la tabla Venta tiene Vn_Cantidad_1 y Vn_Precio_Neto_Importe
            query_productos = f"""
SELECT TOP 10
    P.Pr_Descripcion as producto,
    SUM(V.Vn_Precio_Neto_Importe) as real_ventas
FROM Venta V
INNER JOIN Venta_Encabezado VE ON VE.Vn_Folio = V.Vn_Folio AND VE.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
INNER JOIN Producto P ON P.Pr_Cve_Producto = V.Pr_Cve_Producto
WHERE CONVERT(varchar, VE.Vn_Fecha, 112) >= '{f_ini}'
  AND CONVERT(varchar, VE.Vn_Fecha, 112) <= '{f_fin}'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  AND V.Vn_Precio_Neto_Importe > 0
  {filtro_sucursal}
GROUP BY P.Pr_Descripcion
ORDER BY SUM(V.Vn_Precio_Neto_Importe) DESC
"""
            result_prod = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_productos
            )
            
            if result_prod is not None:
                query_success = True
                for r in (result_prod or []):
                    real_ventas = float(r['real_ventas'] or 0)
                    meta_estimada = real_ventas * 1.1
                    cumplimiento = round((real_ventas / meta_estimada * 100), 0) if meta_estimada > 0 else 0
                    metas_producto.append({
                        "producto": r['producto'],
                        "meta": meta_estimada,
                        "real": real_ventas,
                        "cumplimiento": cumplimiento
                    })
            
            # Ventas por vendedor (top 10) - En MPRO usar tabla Vendedor
            query_vendedor = f"""
SELECT TOP 10
    ISNULL(VND.Vn_Descripcion, 'Sin asignar') as vendedor,
    SUM(VE.Vn_Precio_Neto_Importe) as real_ventas
FROM Venta_Encabezado VE
LEFT JOIN Vendedor VND ON VND.Vn_Cve_Vendedor = VE.Vn_Cve_Vendedor
WHERE CONVERT(varchar, VE.Vn_Fecha, 112) >= '{f_ini}'
  AND CONVERT(varchar, VE.Vn_Fecha, 112) <= '{f_fin}'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {filtro_sucursal}
GROUP BY VND.Vn_Descripcion
ORDER BY SUM(VE.Vn_Precio_Neto_Importe) DESC
"""
            result_vend = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_vendedor
            )
            
            if result_vend is not None:
                if not query_success:
                    query_success = True
                for r in (result_vend or []):
                    real_ventas = float(r['real_ventas'] or 0)
                    meta_estimada = real_ventas * 1.1
                    cumplimiento = round((real_ventas / meta_estimada * 100), 0) if meta_estimada > 0 else 0
                    metas_vendedor.append({
                        "vendedor": r['vendedor'],
                        "meta": meta_estimada,
                        "real": real_ventas,
                        "cumplimiento": cumplimiento
                    })
        
        data = {"por_producto": metas_producto, "por_vendedor": metas_vendedor}
        
        if query_success:
            # Query exitosa - guardar en cache
            await save_to_cache(cache_key, data, "metas", server['name'], server['system_type'])
            
            has_data = len(metas_producto) > 0 or len(metas_vendedor) > 0
            return build_envelope_response(
                source_status=SourceStatus.SUCCESS if has_data else SourceStatus.NO_DATA,
                data=data,
                server_name=server['name'],
                server_type=server['system_type'],
                cache_used=False,
                fecha_inicio=fecha_ini,
                fecha_fin=fecha_fin
            )
        else:
            # Query falló - intentar cache
            raise Exception("Query no retornó datos válidos")
        
    except Exception as e:
        logging.warning(f"Error en metas para {server['name']}: {e}")
        
        # Intentar cache como fallback
        cached = await get_cached_response(cache_key)
        
        if cached and cached.get("data"):
            return build_envelope_response(
                source_status=SourceStatus.DEGRADED_CACHE,
                data=cached["data"],
                server_name=server['name'],
                server_type=server['system_type'],
                cache_used=True,
                last_successful_sync=cached.get("cached_at"),
                source_message=f"Datos de cache (última actualización: {cached.get('cached_at', 'desconocido')})"
            )
        
        # Sin cache - devolver estructura vacía controlada
        return build_envelope_response(
            source_status=SourceStatus.SOURCE_UNREACHABLE,
            data=empty_response(),
            server_name=server['name'],
            server_type=server['system_type'],
            cache_used=False,
            source_message=f"No se pudo conectar a {server['name']} y no hay cache disponible"
        )


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-4C (Abril 2026)
# ============================================================================

@router.get("/comercial/ticket-perfecto/{server_id}")
async def comercial_ticket_perfecto(
    server_id: str, 
    sucursal: str = Query(default=""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Análisis de ticket perfecto y rentabilidad por producto.
    Solo SoftRestaurant tiene los datos necesarios.
    
    RESPUESTA HOMOLOGADA:
    - source_status: SUCCESS | NO_DATA | DEGRADED_CACHE | SOURCE_UNREACHABLE | ERROR
    - cache_used: true/false
    - last_successful_sync: timestamp si se usó cache
    - data: {ticket, rentabilidad}
    """
    from modules.comercial.cache_service import (
        SourceStatus, build_cache_key, get_cached_response, 
        save_to_cache, build_envelope_response
    )
    
    server = await get_server_by_id(server_id)
    if not server:
        return build_envelope_response(
            source_status=SourceStatus.ERROR,
            data={"ticket": {}, "rentabilidad": []},
            source_message="Servidor no encontrado"
        )
    
    # FASE 6-8: Validación centralizada de acceso
    await validate_server_access_rbac(current_user, server_id)
    
    # Construir clave de cache
    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
    hoy = datetime.now()
    cache_key = build_cache_key(
        modulo="comercial",
        endpoint="ticket_perfecto",
        server_id=server_id,
        sucursal=sucursal,
        fecha=hoy.strftime('%Y-%m-%d'),
        system_type=server.get('system_type', '')
    )
    
    def empty_response():
        return {
            "ticket": {"tickets_totales": 0, "tickets_completos": 0, "pct_completos": 0},
            "rentabilidad": []
        }
    
    try:
        fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        
        ticket_data = empty_response()["ticket"]
        rentabilidad = []
        query_success = False
        
        # FASE 3A.2: Migrado a helper centralizado
        if is_softrestaurant_system(server.get('system_type')):
            # Formato YYYYMMDD universal para SQL Server
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # =========================================================================
            # BLINDAJE: Query de ticket perfecto con manejo de columnas opcionales
            # clasificacionventa puede no existir en algunas versiones de SoftRestaurant
            # =========================================================================
            try:
                query_categorias = f"""
SELECT 
    COUNT(DISTINCT cheques.folio) as tickets_totales,
    COUNT(DISTINCT CASE WHEN p.clasificacionventa = 1 THEN cheques.folio END) as con_alimentos,
    COUNT(DISTINCT CASE WHEN p.clasificacionventa = 2 THEN cheques.folio END) as con_bebidas
FROM cheques
INNER JOIN cheqdet cd ON cd.foliodet = cheques.folio
INNER JOIN productos p ON p.idproducto = cd.idproducto
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0
  AND cheques.total > 0
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_categorias
                )
                
                if result is not None:
                    query_success = True
                    tickets_totales = int(result[0]['tickets_totales'] or 0) if result else 0
                    con_alimentos = int(result[0]['con_alimentos'] or 0) if result else 0
                    con_bebidas = int(result[0]['con_bebidas'] or 0) if result else 0
                    tickets_completos = min(con_alimentos, con_bebidas)
                    
                    ticket_data = {
                        "tickets_totales": tickets_totales,
                        "tickets_completos": tickets_completos,
                        "pct_completos": round((tickets_completos / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
                        "con_entrada": con_alimentos,
                        "pct_entrada": round((con_alimentos / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
                        "con_plato_fuerte": con_alimentos,
                        "pct_plato_fuerte": round((con_alimentos / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
                        "con_postre": 0,
                        "pct_postre": 0,
                        "con_digestivo": con_bebidas,
                        "pct_digestivo": round((con_bebidas / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
                        "oportunidad_perdida": 0
                    }
            except Exception as cat_error:
                # Si clasificacionventa no existe, usar query simplificada
                logging.warning(f"[BLINDAJE] Ticket perfecto {server['name']}: columna opcional no existe ({cat_error})")
                try:
                    query_simple = f"""
SELECT COUNT(DISTINCT cheques.folio) as tickets_totales
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0 AND cheques.total > 0
"""
                    result_simple = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_simple
                    )
                    if result_simple:
                        tickets_totales = int(result_simple[0]['tickets_totales'] or 0)
                        ticket_data = {
                            "tickets_totales": tickets_totales,
                            "tickets_completos": 0,
                            "pct_completos": 0,
                            "con_entrada": 0, "pct_entrada": 0,
                            "con_plato_fuerte": 0, "pct_plato_fuerte": 0,
                            "con_postre": 0, "pct_postre": 0,
                            "con_digestivo": 0, "pct_digestivo": 0,
                            "oportunidad_perdida": 0
                        }
                        query_success = True
                except Exception as simple_error:
                    logging.warning(f"[BLINDAJE] Query simplificada también falló: {simple_error}")
            
            # Top productos por rentabilidad - TAMBIÉN CORREGIR FORMATO DE FECHA
            query_rentabilidad = f"""
SELECT TOP 20
    p.idproducto as codigo,
    p.descripcion as producto,
    SUM(cd.cantidad * cd.precio) as ventas,
    SUM(cd.cantidad * ISNULL(p.costo, 0)) as costo
FROM cheqdet cd
INNER JOIN cheques ON cheques.folio = cd.foliodet
INNER JOIN productos p ON p.idproducto = cd.idproducto
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0
GROUP BY p.idproducto, p.descripcion
HAVING SUM(cd.cantidad * cd.precio) > 0
ORDER BY SUM(cd.cantidad * cd.precio) DESC
"""
            result_rent = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_rentabilidad
            )
            
            if result_rent is not None:
                for r in (result_rent or []):
                    ventas = float(r['ventas'] or 0)
                    costo = float(r['costo'] or 0)
                    margen = round(((ventas - costo) / ventas * 100), 0) if ventas > 0 else 0
                    categoria = 'A' if margen >= 60 else ('B' if margen >= 40 else 'C')
                    rentabilidad.append({
                        "codigo": str(r['codigo']),
                        "producto": r['producto'],
                        "ventas": ventas,
                        "costo": costo,
                        "margen": margen,
                        "categoria": categoria
                    })
        
        data = {"ticket": ticket_data, "rentabilidad": rentabilidad}
        
        if query_success:
            await save_to_cache(cache_key, data, "ticket_perfecto", server['name'], server['system_type'])
            
            has_data = ticket_data.get("tickets_totales", 0) > 0 or len(rentabilidad) > 0
            return build_envelope_response(
                source_status=SourceStatus.SUCCESS if has_data else SourceStatus.NO_DATA,
                data=data,
                server_name=server['name'],
                server_type=server['system_type'],
                cache_used=False,
                fecha_inicio=fecha_ini,
                fecha_fin=fecha_fin
            )
        else:
            raise Exception("Query no retornó datos válidos")
        
    except Exception as e:
        logging.warning(f"Error en ticket perfecto para {server['name']}: {e}")
        
        cached = await get_cached_response(cache_key)
        
        if cached and cached.get("data"):
            return build_envelope_response(
                source_status=SourceStatus.DEGRADED_CACHE,
                data=cached["data"],
                server_name=server['name'],
                server_type=server['system_type'],
                cache_used=True,
                last_successful_sync=cached.get("cached_at"),
                source_message=f"Datos de cache (última actualización: {cached.get('cached_at', 'desconocido')})"
            )
        
        return build_envelope_response(
            source_status=SourceStatus.SOURCE_UNREACHABLE,
            data=empty_response(),
            server_name=server['name'],
            server_type=server['system_type'],
            cache_used=False,
            source_message=f"No se pudo conectar a {server['name']} y no hay cache disponible"
        )


@router.get("/comercial/ventas-tiempo/{server_id}")
async def comercial_ventas_tiempo(
    server_id: str, 
    sucursal: str = Query(default=""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Ventas por hora y día de la semana.
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # FASE 6-8: Validación centralizada de acceso
    await validate_server_access_rbac(current_user, server_id)
    
    try:
        hoy = datetime.now()
        # Última semana
        fecha_ini = (hoy - timedelta(days=7)).strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        
        # FASE 3A.2: Migrado a helper centralizado
        if is_softrestaurant_system(server.get('system_type')):
            # Formato YYYYMMDD universal para SQL Server
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # Verificar si la tabla cheques tiene columna 'propina'
            has_propina = check_column_exists(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], 'cheques', 'propina'
            )
            propina_expr = get_propina_safe_column(has_propina)
            
            # Ventas por hora (excluyendo propinas SI existe la columna)
            # BUG-RUZ-002 FIX: Agrupa por hora del cheque, NO por apertura del turno
            query_hora = f"""
SELECT 
    DATEPART(HOUR, cheques.fecha) as hora,
    SUM(cheques.total{propina_expr}) as ventas,
    SUM(cheques.nopersonas) as pax
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0
GROUP BY DATEPART(HOUR, cheques.fecha)
ORDER BY SUM(cheques.total{propina_expr}) DESC
"""
            result_hora = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_hora
            )
            
            ventas_por_hora = []
            for r in (result_hora or [])[:6]:  # Top 6 horas
                hora_int = int(r['hora'] or 0)
                ventas_por_hora.append({
                    "hora": f"{hora_int:02d}:00",
                    "ventas": float(r['ventas'] or 0),
                    "pax": int(r['pax'] or 0)
                })
            
            # Ventas por día de la semana (excluyendo propinas SI existe la columna)
            query_dia = f"""
SELECT 
    DATEPART(WEEKDAY, turnos.apertura) as dia_num,
    SUM(cheques.total{propina_expr}) as ventas
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0
GROUP BY DATEPART(WEEKDAY, turnos.apertura)
ORDER BY DATEPART(WEEKDAY, turnos.apertura)
"""
            result_dia = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_dia
            )
            
            # Mapeo SQL Server DATEPART(WEEKDAY): 1=Domingo, 2=Lunes, ..., 7=Sábado
            # Reordenamos para que sea Lunes a Domingo (2,3,4,5,6,7,1)
            dias_semana = {1: 'Dom', 2: 'Lun', 3: 'Mar', 4: 'Mié', 5: 'Jue', 6: 'Vie', 7: 'Sáb'}
            
            # Crear diccionario con todos los días inicializados en 0
            ventas_dict = {dia: 0 for dia in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']}
            
            for r in (result_dia or []):
                dia_num = int(r['dia_num'] or 1)
                dia_nombre = dias_semana.get(dia_num, 'Otro')
                if dia_nombre in ventas_dict:
                    ventas_dict[dia_nombre] = float(r['ventas'] or 0)
            
            # Convertir a lista ordenada de Lunes a Domingo
            ventas_por_dia = [{"dia": dia, "ventas": ventas_dict[dia]} for dia in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']]
            
            # NUEVO: PAX del día actual desde tempcheques (ventas sin corte)
            pax_hoy = 0
            ventas_hoy = 0
            cheques_hoy = 0
            try:
                # Verificar si tempcheques tiene columna propina
                has_propina_temp = check_column_exists(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], 'tempcheques', 'propina'
                )
                propina_expr_temp = get_propina_safe_column_tempcheques(has_propina_temp)
                
                query_pax_hoy = f"""
SELECT 
    ISNULL(SUM(nopersonas), 0) as pax,
    ISNULL(SUM(total{propina_expr_temp}), 0) as ventas,
    COUNT(*) as cheques
FROM tempcheques
WHERE total > 0
"""
                result_pax_hoy = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_pax_hoy
                )
                if result_pax_hoy and len(result_pax_hoy) > 0:
                    row = result_pax_hoy[0]
                    pax_hoy = int(row.get('pax', 0) or 0)
                    ventas_hoy = float(row.get('ventas', 0) or 0)
                    cheques_hoy = int(row.get('cheques', 0) or 0)
                    logging.info(f"ventas-tiempo SoftRestaurant {server['name']}: PAX HOY (tempcheques) = {pax_hoy}, Ventas = ${ventas_hoy:,.2f}, Cheques = {cheques_hoy}")
            except Exception as e:
                logging.warning(f"ventas-tiempo SoftRestaurant {server['name']}: Error obteniendo PAX del día: {e}")
            
            return {
                "por_hora": ventas_por_hora,
                "por_dia": ventas_por_dia,
                "pax_hoy": pax_hoy,
                "ventas_hoy": ventas_hoy,
                "cheques_hoy": cheques_hoy,
                "fuente_pax_hoy": "tempcheques",
                # METADATOS ARQUITECTURA
                "connection_source": "EDARSAHUB",
                "server_id": server_id,
                "system_type": server['system_type'],
                "sucursal_id": sucursal or "default",
                "source_status": "SUCCESS"
            }
        
        # FASE 3A.2: Migrado a helper centralizado
        elif is_mpro_system(server.get('system_type')):
            # BLINDAJE: Definir f_fin para MPRO (igual que en SoftRestaurant)
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # Filtro de sucursal para MPRO - no filtrar si es "default" o nombre del servidor
            sucursal_filter = ""
            nombre_servidor_1 = server.get('name', '').lower()
            sucursal_lower_1 = (sucursal or '').lower()
            skip_filter_1 = (not sucursal or sucursal_lower_1 == 'default' or sucursal_lower_1 == nombre_servidor_1)
            if sucursal and not skip_filter_1:
                # BLINDAJE: Detectar si es código o nombre de sucursal
                es_codigo_1 = sucursal.isdigit() or (len(sucursal) == 4 and sucursal[0] == '0')
                if es_codigo_1:
                    sucursal_filter = f"AND VE.Sc_Cve_Sucursal = '{sucursal}'"
                else:
                    sucursal_filter = f"AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            # Ventas por hora para MPRO
            query_hora = f"""
SELECT 
    DATEPART(HOUR, VE.Vn_Fecha) as hora,
    SUM(VE.Vn_Precio_Neto_Importe) as ventas,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{fecha_ini} 00:00:00', 120)
  AND VE.Vn_Fecha <= CONVERT(datetime, '{fecha_fin} 23:59:59', 120)
  AND VE.Es_Cve_Estado <> 'CA'
  {sucursal_filter}
GROUP BY DATEPART(HOUR, VE.Vn_Fecha)
ORDER BY SUM(VE.Vn_Precio_Neto_Importe) DESC
"""
            result_hora = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_hora
            )
            
            ventas_por_hora = []
            for r in (result_hora or [])[:6]:  # Top 6 horas
                hora_int = int(r['hora'] or 0)
                ventas_por_hora.append({
                    "hora": f"{hora_int:02d}:00",
                    "ventas": float(r['ventas'] or 0),
                    "pax": int(r['pax'] or 0)
                })
            
            # Ventas por día de la semana para MPRO
            query_dia = f"""
SELECT 
    DATEPART(WEEKDAY, VE.Vn_Fecha) as dia_num,
    SUM(VE.Vn_Precio_Neto_Importe) as ventas
FROM Venta_Encabezado VE
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{fecha_ini} 00:00:00', 120)
  AND VE.Vn_Fecha <= CONVERT(datetime, '{fecha_fin} 23:59:59', 120)
  AND VE.Es_Cve_Estado <> 'CA'
  {sucursal_filter}
GROUP BY DATEPART(WEEKDAY, VE.Vn_Fecha)
ORDER BY DATEPART(WEEKDAY, VE.Vn_Fecha)
"""
            result_dia = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_dia
            )
            
            # Mapeo SQL Server DATEPART(WEEKDAY): 1=Domingo, 2=Lunes, ..., 7=Sábado
            # Reordenamos para que sea Lunes a Domingo
            dias_semana = {1: 'Dom', 2: 'Lun', 3: 'Mar', 4: 'Mié', 5: 'Jue', 6: 'Vie', 7: 'Sáb'}
            
            # Crear diccionario con todos los días inicializados en 0
            ventas_dict = {dia: 0 for dia in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']}
            
            for r in (result_dia or []):
                dia_num = int(r['dia_num'] or 1)
                dia_nombre = dias_semana.get(dia_num, 'Otro')
                if dia_nombre in ventas_dict:
                    ventas_dict[dia_nombre] = float(r['ventas'] or 0)
            
            # Convertir a lista ordenada de Lunes a Domingo
            ventas_por_dia = [{"dia": dia, "ventas": ventas_dict[dia]} for dia in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']]
            
            # NUEVO: PAX del día actual desde API local MPRO
            # ARQUITECTURA: EDARSAHUB-first, sin dependencia directa de MongoDB
            pax_hoy = 0
            ventas_hoy = 0
            cheques_hoy = 0
            fuente_pax = "EDARSAHUB"
            pax_hoy_source = "sql_server"
            
            try:
                # FUENTE PRIMARIA: Configuración de API desde datos del servidor (EDARSAHUB)
                api_config = get_api_config_from_server(server)
                
                if api_config and api_config.get('activo'):
                    # Usar la función de API local para obtener ventas del día
                    resultado_api = obtener_ventas_dia_api_local(api_config, forzar_consulta=True)
                    if not resultado_api.get("omitido", False):
                        pax_hoy = resultado_api.get("pax", 0)
                        ventas_hoy = resultado_api.get("ventas", 0)
                        cheques_hoy = resultado_api.get("cheques", 0)
                        pax_hoy_source = "api_local"
                        logging.info(f"[EDARSAHUB] ventas-tiempo MPRO {server['name']}: PAX HOY (API) = {pax_hoy}")
                    else:
                        logging.info(f"[EDARSAHUB] ventas-tiempo MPRO {server['name']}: API omitida ({resultado_api.get('razon', 'desconocido')})")
                else:
                    # Sin configuración de API activa, usar query directa a SQL Server del día actual
                    pax_hoy_source = "sql_server"
                    hoy_str = hoy.strftime('%Y-%m-%d')
                    query_pax_hoy = f"""
SELECT 
    ISNULL(SUM(C.Co_Personas), 0) as pax,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
    COUNT(DISTINCT VE.Vn_Folio) as cheques
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{hoy_str} 00:00:00', 120)
  AND VE.Vn_Fecha <= CONVERT(datetime, '{hoy_str} 23:59:59', 120)
  AND VE.Es_Cve_Estado <> 'CA'
  {sucursal_filter}
"""
                    result_pax_hoy = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_pax_hoy
                    )
                    if result_pax_hoy and len(result_pax_hoy) > 0:
                        row = result_pax_hoy[0]
                        pax_hoy = int(row.get('pax', 0) or 0)
                        ventas_hoy = float(row.get('ventas', 0) or 0)
                        cheques_hoy = int(row.get('cheques', 0) or 0)
                        logging.info(f"[EDARSAHUB] ventas-tiempo MPRO {server['name']}: PAX HOY (SQL) = {pax_hoy}")
            except Exception as e:
                logging.warning(f"[EDARSAHUB] ventas-tiempo MPRO {server['name']}: Error PAX del día: {e}")
            
            return {
                "por_hora": ventas_por_hora,
                "por_dia": ventas_por_dia,
                "pax_hoy": pax_hoy,
                "ventas_hoy": ventas_hoy,
                "cheques_hoy": cheques_hoy,
                "fuente_pax_hoy": pax_hoy_source,
                # METADATOS ARQUITECTURA
                "connection_source": fuente_pax,
                "server_id": server_id,
                "system_type": server['system_type'],
                "sucursal_id": sucursal or "default",
                "source_status": "SUCCESS"
            }
        
        return {
            "por_hora": [], 
            "por_dia": [], 
            "pax_hoy": 0, 
            "ventas_hoy": 0, 
            "cheques_hoy": 0,
            "fuente_pax_hoy": "none",
            # METADATOS ARQUITECTURA
            "connection_source": "EDARSAHUB",
            "server_id": server_id,
            "system_type": server.get('system_type', 'unknown') if server else 'unknown',
            "sucursal_id": sucursal or "default",
            "source_status": "NO_DATA"
        }
        
    except Exception as e:
        logging.error(f"Error en ventas tiempo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-4E (Abril 2026)
# ============================================================================

@router.get("/comercial/mesas/{server_id}")
async def comercial_mesas(
    server_id: str, 
    sucursal: str = Query(default=""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Análisis de mesas y comensales.
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # FASE 6-8: Validación centralizada de acceso
    await validate_server_access_rbac(current_user, server_id)
    
    # ARQUITECTURA: Obtener nombre de unidad desde EDARSAHUB (primario) o MongoDB (LEGACY_FALLBACK)
    nombre_unidad_mostrar, nombre_source = await get_sucursal_nombre(server_id, sucursal, server['name'])
    if nombre_source == 'MONGO_LEGACY_FALLBACK':
        logging.warning(f"[LEGACY_FALLBACK] Mesas: Nombre de sucursal {sucursal} obtenido de MongoDB")
    
    try:
        hoy = datetime.now()
        fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        
        # FASE 3A.2: Migrado a helper centralizado
        if is_softrestaurant_system(server.get('system_type')):
            # Formato YYYYMMDD universal para SQL Server
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # Verificar si la tabla cheques tiene columna 'propina'
            has_propina = check_column_exists(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], 'cheques', 'propina'
            )
            propina_expr = get_propina_safe_column(has_propina)
            
            # KPIs generales de mesas - sin usar numcuenta que no existe en todas las instalaciones
            # NOTA: Se excluyen propinas de las ventas SI existe la columna
            query_unidad = f"""
SELECT 
    COUNT(DISTINCT cheques.folio) as cheques_mes,
    ISNULL(SUM(cheques.nopersonas), 0) as comensales_mes,
    AVG(cheques.total{propina_expr}) as ticket_promedio,
    ISNULL(AVG(CAST(cheques.nopersonas as float)), 0) as pax_promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0
  AND cheques.total > 0
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_unidad
            )
            
            if result and len(result) > 0:
                row = result[0]
                cheques_mes = int(row['cheques_mes'] or 0)
                comensales_mes = int(row['comensales_mes'] or 0)
                ticket_promedio = float(row['ticket_promedio'] or 0)
                pax_promedio = float(row['pax_promedio'] or 0)
                # Estimamos mesas únicas como cheques / 2 (asumiendo 2 servicios por mesa por día en promedio)
                total_mesas = max(1, cheques_mes // max(1, hoy.day * 2))
            else:
                total_mesas = 0
                cheques_mes = 0
                comensales_mes = 0
                ticket_promedio = 0
                pax_promedio = 0
            
            rotacion_promedio = round(cheques_mes / total_mesas, 1) if total_mesas > 0 else 0
            
            # Obtener número de días del mes hasta hoy
            dias_mes = hoy.day
            vueltas_por_dia = round(cheques_mes / dias_mes, 0) if dias_mes > 0 else 0
            
            # BLINDAJE: Usar nombre obtenido de MongoDB
            unidad_data = {
                "nombre": nombre_unidad_mostrar,
                "total_mesas": total_mesas,
                "capacidad_total": total_mesas * 4,  # Estimado 4 personas por mesa
                "mesas_atendidas_mes": cheques_mes,
                "comensales_mes": comensales_mes,
                "rotacion_promedio": rotacion_promedio,
                "ticket_promedio": round(ticket_promedio, 2),
                "cheque_promedio": round(ticket_promedio * pax_promedio, 2) if pax_promedio > 0 else ticket_promedio,
                "pax_promedio": round(pax_promedio, 1),
                "vueltas_por_dia": vueltas_por_dia,
                "vueltas_por_hora_pico": round(vueltas_por_dia / 4, 0)  # Estimado 4 horas pico
            }
            
            # Rotación por hora - más útil sin numcuenta
            query_rotacion = f"""
SELECT TOP 15
    DATEPART(HOUR, turnos.apertura) as hora,
    COUNT(*) as vueltas,
    ISNULL(AVG(CAST(cheques.nopersonas as float)), 2) as capacidad_promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0
  AND cheques.total > 0
GROUP BY DATEPART(HOUR, turnos.apertura)
ORDER BY COUNT(*) DESC
"""
            result_rot = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_rotacion
            )
            
            max_vueltas = max([int(r['vueltas'] or 0) for r in result_rot]) if result_rot else 1
            
            rotacion_por_mesa = []
            for r in result_rot:
                vueltas = int(r['vueltas'] or 0)
                ocupacion = round((vueltas / max_vueltas * 100), 0) if max_vueltas > 0 else 0
                hora = int(r['hora'] or 0)
                rotacion_por_mesa.append({
                    "mesa": f"Hora {hora:02d}:00",
                    "capacidad": int(r['capacidad_promedio'] or 2),
                    "vueltas": vueltas,
                    "ocupacion": ocupacion
                })
            
            return {
                "unidad": unidad_data,
                "rotacion": rotacion_por_mesa
            }
        
        # FASE 3A.2: Migrado a helper centralizado
        elif is_mpro_system(server.get('system_type')):
            # BLINDAJE: Definir f_fin para MPRO
            f_fin = fecha_fin.replace('-', '')
            
            # Filtro de sucursal para MPRO - no filtrar si es "default" o nombre del servidor
            sucursal_filter = ""
            nombre_servidor_2 = server.get('name', '').lower()
            sucursal_lower_2 = (sucursal or '').lower()
            skip_filter_2 = (not sucursal or sucursal_lower_2 == 'default' or sucursal_lower_2 == nombre_servidor_2)
            if sucursal and not skip_filter_2:
                # BLINDAJE: Detectar si es código o nombre de sucursal
                es_codigo_2 = sucursal.isdigit() or (len(sucursal) == 4 and sucursal[0] == '0')
                if es_codigo_2:
                    sucursal_filter = f"AND VE.Sc_Cve_Sucursal = '{sucursal}'"
                else:
                    sucursal_filter = f"AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            # KPIs generales de mesas para MPRO
            query_unidad = f"""
SELECT 
    COUNT(DISTINCT VE.Vn_Folio) as cheques_mes,
    ISNULL(SUM(C.Co_Personas), 0) as comensales_mes,
    AVG(VE.Vn_Precio_Neto_Importe) as ticket_promedio,
    ISNULL(AVG(CAST(C.Co_Personas as float)), 0) as pax_promedio
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{fecha_ini} 00:00:00', 120)
  AND VE.Vn_Fecha <= CONVERT(datetime, '{f_fin} 23:59:59', 120)
  AND VE.Es_Cve_Estado <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {sucursal_filter}
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_unidad
            )
            
            if result and len(result) > 0:
                row = result[0]
                cheques_mes = int(row['cheques_mes'] or 0)
                comensales_mes = int(row['comensales_mes'] or 0)
                ticket_promedio = float(row['ticket_promedio'] or 0)
                pax_promedio = float(row['pax_promedio'] or 0)
                total_mesas = max(1, cheques_mes // max(1, hoy.day * 2))
            else:
                total_mesas = 0
                cheques_mes = 0
                comensales_mes = 0
                ticket_promedio = 0
                pax_promedio = 0
            
            rotacion_promedio = round(cheques_mes / total_mesas, 1) if total_mesas > 0 else 0
            dias_mes = hoy.day
            vueltas_por_dia = round(cheques_mes / dias_mes, 0) if dias_mes > 0 else 0
            
            # BLINDAJE MPRO: Usar nombre de MongoDB (ya obtenido arriba), con fallback a SQL si no se encontró
            nombre_final_mpro = nombre_unidad_mostrar
            # Si MongoDB no encontró el nombre (aún es server['name']), intentar con SQL
            if nombre_final_mpro == server['name'] and sucursal:
                es_codigo_suc = sucursal.isdigit() or (len(sucursal) == 4 and sucursal[0] == '0')
                if es_codigo_suc:
                    query_nombre = f"""
SELECT TOP 1 Sc_Descripcion as nombre FROM Sucursal WHERE Sc_Cve_Sucursal = '{sucursal}'
"""
                    try:
                        result_nombre = execute_sql_query(
                            server['host'], server['port'], server['database'],
                            server['username'], server['password'], query_nombre
                        )
                        if result_nombre and len(result_nombre) > 0 and result_nombre[0].get('nombre'):
                            nombre_final_mpro = result_nombre[0]['nombre']
                    except Exception as e:
                        logging.warning(f"No se pudo obtener nombre de sucursal {sucursal} desde SQL: {e}")
            
            unidad_data = {
                "nombre": nombre_final_mpro,
                "total_mesas": total_mesas,
                "capacidad_total": total_mesas * 4,
                "mesas_atendidas_mes": cheques_mes,
                "comensales_mes": comensales_mes,
                "rotacion_promedio": rotacion_promedio,
                "ticket_promedio": round(ticket_promedio, 2),
                "cheque_promedio": round(ticket_promedio * pax_promedio, 2) if pax_promedio > 0 else ticket_promedio,
                "pax_promedio": round(pax_promedio, 1),
                "vueltas_por_dia": vueltas_por_dia,
                "vueltas_por_hora_pico": round(vueltas_por_dia / 4, 0)
            }
            
            # Rotación por hora para MPRO
            query_rotacion = f"""
SELECT TOP 15
    DATEPART(HOUR, VE.Vn_Fecha) as hora,
    COUNT(*) as vueltas,
    ISNULL(AVG(CAST(C.Co_Personas as float)), 2) as capacidad_promedio
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{fecha_ini} 00:00:00', 120)
  AND VE.Vn_Fecha <= CONVERT(datetime, '{f_fin} 23:59:59', 120)
  AND VE.Es_Cve_Estado <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {sucursal_filter}
GROUP BY DATEPART(HOUR, VE.Vn_Fecha)
ORDER BY COUNT(*) DESC
"""
            result_rotacion = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_rotacion
            )
            
            rotacion_por_mesa = []
            for r in (result_rotacion or []):
                hora = int(r['hora'] or 0)
                vueltas = int(r['vueltas'] or 0)
                ocupacion = min(100, round((vueltas / max(1, vueltas_por_dia)) * 100, 1)) if vueltas_por_dia > 0 else 0
                rotacion_por_mesa.append({
                    "mesa": f"Hora {hora:02d}:00",
                    "capacidad": int(r['capacidad_promedio'] or 2),
                    "vueltas": vueltas,
                    "ocupacion": ocupacion
                })
            
            return {
                "unidad": unidad_data,
                "rotacion": rotacion_por_mesa
            }
        
        return {
            "unidad": {"nombre": server['name'], "total_mesas": 0},
            "rotacion": []
        }
        
    except Exception as e:
        logging.error(f"Error en mesas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comercial/detalle-movimientos/{server_id}")
async def comercial_detalle_movimientos(
    server_id: str, 
    sucursal: str = Query(default=""),
    tipo: str = Query(default="ventas"),  # ventas, pax, cheques
    periodo: str = Query(default="mes"),  # dia, semana, mes
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200),
    current_user: Dict = Depends(get_current_user)
):
    """
    Detalle de movimientos para drill-down en KPIs.
    Devuelve cheques/facturas individuales con su detalle.
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # FASE 6-8: Validación centralizada de acceso
    await validate_server_access_rbac(current_user, server_id)
    
    try:
        hoy = datetime.now()
        
        # Calcular fechas según período
        if periodo == "dia":
            fecha_ini = hoy.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
        elif periodo == "semana":
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fecha_ini = inicio_semana.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
        else:  # mes
            fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
        
        offset = (page - 1) * limit
        
        # FASE 3A.2: Migrado a helper centralizado
        if is_softrestaurant_system(server.get('system_type')):
            # Formato de fecha para SoftRestaurant (YYYYMMDD)
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # Verificar si la tabla cheques tiene columna 'propina'
            has_propina = check_column_exists(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], 'cheques', 'propina'
            )
            
            # Query para obtener detalle de cheques - Sin columnas opcionales que pueden no existir
            # NOTA: importe excluye propinas SI existe la columna
            if has_propina:
                query_detalle = f"""
SELECT 
    cheques.folio,
    turnos.apertura as fecha,
    cheques.total - ISNULL(cheques.propina, 0) as importe,
    ISNULL(cheques.nopersonas, 0) as pax,
    ISNULL(cheques.descuento, 0) as descuento,
    ISNULL(cheques.propina, 0) as propina,
    'Comedor' as tipo_servicio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0
  AND cheques.total > 0
ORDER BY turnos.apertura DESC
OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
"""
            else:
                # Sin columna propina
                query_detalle = f"""
SELECT 
    cheques.folio,
    turnos.apertura as fecha,
    cheques.total as importe,
    ISNULL(cheques.nopersonas, 0) as pax,
    ISNULL(cheques.descuento, 0) as descuento,
    0 as propina,
    'Comedor' as tipo_servicio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0
  AND cheques.total > 0
ORDER BY turnos.apertura DESC
OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_detalle
            )
            
            # Query para contar total
            query_total = f"""
SELECT COUNT(*) as total
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0
  AND cheques.total > 0
"""
            result_total = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_total
            )
            total = int(result_total[0]['total']) if result_total else 0
            
            movimientos = []
            for row in result or []:
                fecha_val = row.get('fecha')
                fecha_str = fecha_val.strftime('%Y-%m-%d %H:%M') if hasattr(fecha_val, 'strftime') else str(fecha_val) if fecha_val else ''
                movimientos.append({
                    "folio": str(row.get('folio', '')),
                    "fecha": fecha_str,
                    "importe": float(row.get('importe') or 0),
                    "pax": int(row.get('pax') or 0),
                    "descuento": float(row.get('descuento') or 0),
                    "propina": float(row.get('propina') or 0),
                    "tipo_servicio": row.get('tipo_servicio', 'Comedor'),
                    "num_productos": 0
                })
            
            return {
                "movimientos": movimientos,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit,
                "periodo": {"inicio": fecha_ini, "fin": fecha_fin},
                "servidor": server['name']
            }
        
        # FASE 3A.2: Migrado a helper centralizado (eliminada comparación redundante)
        elif is_mpro_system(server.get('system_type')):
            # Formato de fecha para MPRO (YYYYMMDD)
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # Filtro de sucursal si viene - no filtrar si es "default" o nombre del servidor
            sucursal_filter = ""
            nombre_servidor = server.get('name', '').lower()
            sucursal_lower = (sucursal or '').lower()
            skip_sucursal_filter = (
                not sucursal or 
                sucursal_lower == 'default' or 
                sucursal_lower == nombre_servidor or
                sucursal_lower == 'managmentpro' or
                sucursal_lower == 'mpro'
            )
            
            if sucursal and not skip_sucursal_filter:
                # Detectar si es un código de sucursal (4 dígitos como "0021") o un nombre
                if len(sucursal) == 4 and sucursal.isdigit():
                    # Es un código de sucursal - buscar por Sc_Cve_Sucursal
                    sucursal_filter = f"AND VE.Sc_Cve_Sucursal = '{sucursal}'"
                else:
                    # Es un nombre - buscar por descripción parcial
                    sucursal_filter = f"AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            logging.info(f"Detalle MPRO: f_ini={f_ini}, f_fin={f_fin}, sucursal={sucursal}, skip_filter={skip_sucursal_filter}, sucursal_filter={sucursal_filter}")
            
            # Query para MPRO - usa Venta_Encabezado con Comanda para PAX
            query_detalle = f"""
SELECT 
    VE.Vn_Folio as folio,
    VE.Vn_Fecha as fecha,
    VE.Vn_Precio_Neto_Importe as importe,
    ISNULL(C.Co_Personas, 0) as pax,
    'Comedor' as tipo_servicio
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{f_ini} 00:00:00', 120)
  AND VE.Vn_Fecha <= CONVERT(datetime, '{f_fin} 23:59:59', 120)
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {sucursal_filter}
ORDER BY VE.Vn_Fecha DESC
OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
"""
            logging.info(f"Query MPRO detalle: {query_detalle[:200]}...")
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_detalle
            )
            
            # Query para contar total
            query_total = f"""
SELECT COUNT(*) as total
FROM Venta_Encabezado VE
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{f_ini} 00:00:00', 120)
  AND VE.Vn_Fecha <= CONVERT(datetime, '{f_fin} 23:59:59', 120)
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {sucursal_filter}
"""
            result_total = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_total
            )
            total = int(result_total[0]['total']) if result_total else 0
            
            movimientos = []
            for row in result or []:
                fecha_val = row.get('fecha')
                fecha_str = fecha_val.strftime('%Y-%m-%dT%H:%M:%S') if hasattr(fecha_val, 'strftime') else str(fecha_val) if fecha_val else ''
                movimientos.append({
                    "folio": str(row.get('folio', '')),
                    "fecha": fecha_str,
                    "importe": float(row.get('importe') or 0),
                    "pax": int(row.get('pax') or 0),
                    "descuento": 0,
                    "propina": 0,
                    "tipo_servicio": row.get('tipo_servicio', 'Comedor'),
                    "num_productos": 0
                })
            
            return {
                "movimientos": movimientos,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if total > 0 else 0,
                "periodo": {"inicio": fecha_ini, "fin": fecha_fin},
                "servidor": server['name']
            }
        
        return {"movimientos": [], "total": 0, "page": 1, "limit": limit, "pages": 0}
        
    except Exception as e:
        logging.error(f"Error en detalle movimientos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-4G (Abril 2026)
# ============================================================================

@router.get("/comercial/precios-constantes/{server_id}")
async def ventas_precios_constantes(
    server_id: str,
    periodo_actual: str = Query(..., description="Período actual: YYYY-MM o YYYY-MM,YYYY-MM"),
    periodo_base: str = Query(..., description="Período base para precios: YYYY-MM o YYYY-MM,YYYY-MM"),
    granularidad: str = Query(default="categoria", description="categoria, familia, producto"),
    sucursal: str = Query(default="all", description="ID de sucursal o 'all' para todas"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Análisis de ventas valuando a precios constantes de un período base.
    Permite comparar ventas eliminando el efecto inflacionario.
    
    - periodo_actual: Mes(es) de ventas a analizar (ej: "2025-03" o "2025-01,2025-02,2025-03")
    - periodo_base: Período de donde tomar los precios de referencia (ej: "2024-03")
    - granularidad: Nivel de detalle (categoria, familia, producto)
    - sucursal: ID de la sucursal a filtrar o 'all' para todas
    
    Productos In/Out:
    - Nuevos (no existían en período base): Usan precio actual
    - Descontinuados (no existen en período actual): Usan último precio conocido
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # FASE 6-8: Validación centralizada de acceso
    await validate_server_access_rbac(current_user, server_id)
    
    try:
        # Parsear períodos (pueden ser múltiples meses separados por coma)
        def parse_periodos(periodo_str):
            meses = [m.strip() for m in periodo_str.split(',')]
            fechas = []
            for mes in meses:
                year, month = mes.split('-')
                year, month = int(year), int(month)
                ultimo_dia = calendar.monthrange(year, month)[1]
                fechas.append({
                    'mes': mes,
                    'year': year,
                    'month': month,
                    'fecha_ini': f"{year}-{month:02d}-01",
                    'fecha_fin': f"{year}-{month:02d}-{ultimo_dia:02d}"
                })
            return fechas
        
        periodos_actual = parse_periodos(periodo_actual)
        periodos_base = parse_periodos(periodo_base)
        
        # Fechas consolidadas
        fecha_ini_actual = min(p['fecha_ini'] for p in periodos_actual)
        fecha_fin_actual = max(p['fecha_fin'] for p in periodos_actual)
        fecha_ini_base = min(p['fecha_ini'] for p in periodos_base)
        fecha_fin_base = max(p['fecha_fin'] for p in periodos_base)
        
        logging.info(f"Precios Constantes - Actual: {fecha_ini_actual} a {fecha_fin_actual}, Base: {fecha_ini_base} a {fecha_fin_base}")
        
        # FASE 3A.2: Migrado a helper centralizado
        if is_softrestaurant_system(server.get('system_type')):
            # Formato YYYYMMDD para SoftRestaurant - usando CONVERT para evitar errores de conversión
            f_ini_actual = fecha_ini_actual.replace('-', '')
            f_fin_actual = fecha_fin_actual.replace('-', '')
            f_ini_base = fecha_ini_base.replace('-', '')
            f_fin_base = fecha_fin_base.replace('-', '')
            
            # Verificar si la tabla cheques tiene columna 'propina'
            has_propina = check_column_exists(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], 'cheques', 'propina'
            )
            propina_expr = get_propina_safe_column(has_propina)
            
            # PASO 1: Obtener VENTAS REALES del período (misma lógica que Dashboard)
            # Esto asegura que los totales coincidan con el Tablero Ejecutivo
            # BLINDAJE: Usamos CONVERT(varchar, turnos.apertura, 112) para consistencia
            # NOTA: Se excluyen propinas de las ventas SI existe la columna
            query_ventas_reales = f"""
SELECT SUM(cheques.total{propina_expr}) as ventas_reales
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini_actual}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin_actual}'
  AND cheques.cancelado = 0
"""
            result_ventas_reales = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_reales
            )
            ventas_reales_periodo = float(result_ventas_reales[0]['ventas_reales'] or 0) if result_ventas_reales else 0
            
            # Query para ventas del período ACTUAL con precios actuales
            # Agrupa por producto y calcula precio promedio
            # NOTA: En SoftRestaurant la tabla de detalle es 'cheqdet' (no 'chequedetalle')
            # BLINDAJE: Usamos CONVERT para fechas
            query_ventas_actual = f"""
SELECT 
    p.idproducto as producto_id,
    p.descripcion as producto,
    'SoftRestaurant' as categoria,
    'Productos' as familia,
    SUM(cd.cantidad) as cantidad,
    SUM(cd.precio * cd.cantidad) as importe_actual,
    AVG(cd.precio) as precio_promedio_actual
FROM cheqdet cd
INNER JOIN cheques c ON c.folio = cd.foliodet
INNER JOIN turnos t ON t.idturno = c.idturno
INNER JOIN productos p ON p.idproducto = cd.idproducto
WHERE CONVERT(varchar, t.apertura, 112) >= '{f_ini_actual}'
  AND CONVERT(varchar, t.apertura, 112) <= '{f_fin_actual}'
  AND c.cancelado = 0
  AND cd.cantidad > 0
GROUP BY p.idproducto, p.descripcion
"""
            
            # Query para precios del período BASE - BLINDAJE: Usamos CONVERT
            query_precios_base = f"""
SELECT 
    p.idproducto as producto_id,
    p.descripcion as producto,
    AVG(cd.precio) as precio_promedio_base
FROM cheqdet cd
INNER JOIN cheques c ON c.folio = cd.foliodet
INNER JOIN turnos t ON t.idturno = c.idturno
INNER JOIN productos p ON p.idproducto = cd.idproducto
WHERE CONVERT(varchar, t.apertura, 112) >= '{f_ini_base}'
  AND CONVERT(varchar, t.apertura, 112) <= '{f_fin_base}'
  AND c.cancelado = 0
  AND cd.cantidad > 0
GROUP BY p.idproducto, p.descripcion
"""
            
            # Ejecutar queries
            ventas_actual = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_actual
            ) or []
            
            precios_base = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_precios_base
            ) or []
            
            # VALIDACIÓN (Abril 2026): Si no hay datos en el período base, no se puede hacer análisis
            # porque no hay precios de referencia con los cuales comparar
            if not precios_base or len(precios_base) == 0:
                logging.warning(f"Precios Constantes SoftRestaurant {server['name']}: Sin datos en período base {periodo_base}")
                return {
                    "servidor": server['name'],
                    "system_type": server['system_type'],
                    "periodo_actual": periodo_actual,
                    "periodo_base": periodo_base,
                    "granularidad": granularidad,
                    "error": f"Sin datos de ventas en el período base ({periodo_base}). No es posible calcular precios constantes sin un período de referencia con ventas.",
                    "kpis": {
                        "ventas_actuales": ventas_reales_periodo,
                        "ventas_constantes": 0,
                        "efecto_precio": 0,
                        "efecto_inflacion_pct": 0,
                        "variacion_real_pct": 0,
                        "productos_analizados": 0,
                        "productos_nuevos": 0,
                        "productos_descontinuados": 0
                    },
                    "datos": [],
                    "detalle_productos": None
                }
            
            # Crear diccionario de precios base
            precios_base_dict = {str(p['producto_id']): float(p['precio_promedio_base'] or 0) for p in precios_base}
            
            # PASO 2: Calcular suma de productos para obtener factor de ajuste
            suma_productos_actual = sum(float(v['importe_actual'] or 0) for v in ventas_actual)
            
            # Factor de ajuste: ventas reales / suma de productos
            # Esto distribuye propinas, impuestos, descuentos proporcionalmente
            factor_ajuste = ventas_reales_periodo / suma_productos_actual if suma_productos_actual > 0 else 1
            logging.info(f"SoftRestaurant - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
            
            # Procesar resultados aplicando factor de ajuste
            productos_detalle = []
            total_actual = 0
            total_constante = 0
            
            for venta in ventas_actual:
                producto_id = str(venta['producto_id'])
                cantidad = float(venta['cantidad'] or 0)
                precio_actual = float(venta['precio_promedio_actual'] or 0)
                # Aplicar factor de ajuste al importe para que coincida con ventas reales
                importe_actual = float(venta['importe_actual'] or 0) * factor_ajuste
                
                # Determinar precio a usar para valuación constante
                if producto_id in precios_base_dict:
                    precio_base = precios_base_dict[producto_id]
                    es_nuevo = False
                else:
                    # Producto nuevo - usar precio actual
                    precio_base = precio_actual
                    es_nuevo = True
                
                # El importe constante también debe ajustarse con el factor
                importe_constante = (cantidad * precio_base) * factor_ajuste
                efecto_precio = importe_actual - importe_constante
                variacion_precio_pct = ((precio_actual - precio_base) / precio_base * 100) if precio_base > 0 else 0
                
                productos_detalle.append({
                    'producto_id': producto_id,
                    'producto': venta['producto'],
                    'categoria': venta['categoria'],
                    'familia': venta['familia'],
                    'cantidad': cantidad,
                    'precio_actual': precio_actual,
                    'precio_base': precio_base,
                    'importe_actual': importe_actual,
                    'importe_constante': importe_constante,
                    'efecto_precio': efecto_precio,
                    'variacion_precio_pct': round(variacion_precio_pct, 2),
                    'es_nuevo': es_nuevo,
                    'es_descontinuado': False
                })
                
                total_actual += importe_actual
                total_constante += importe_constante
            
            # Buscar productos descontinuados (estaban en base pero no en actual)
            productos_actuales_ids = {str(v['producto_id']) for v in ventas_actual}
            for producto_id, precio_base in precios_base_dict.items():
                if producto_id not in productos_actuales_ids:
                    # Obtener info del producto descontinuado
                    # CORRECCIÓN SQL-SAFE (Abril 2026): Query parametrizada para prevenir SQL injection
                    # y manejar correctamente IDs alfanuméricos como 'A090035'
                    query_info = "SELECT TOP 1 descripcion FROM productos WHERE idproducto = %s"
                    info_result = execute_sql_query_params(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], 
                        query_info,
                        params=(str(producto_id),)  # Parámetro nativo - el driver maneja el tipo
                    )
                    nombre_producto = info_result[0]['descripcion'] if info_result else f'Producto {producto_id}'
                    
                    productos_detalle.append({
                        'producto_id': producto_id,
                        'producto': nombre_producto,
                        'categoria': 'Descontinuado',
                        'familia': '-',
                        'cantidad': 0,
                        'precio_actual': 0,
                        'precio_base': precio_base,
                        'importe_actual': 0,
                        'importe_constante': 0,
                        'efecto_precio': 0,
                        'variacion_precio_pct': 0,
                        'es_nuevo': False,
                        'es_descontinuado': True
                    })
            
            # Agrupar según granularidad
            if granularidad == 'categoria':
                agrupado = {}
                for p in productos_detalle:
                    key = p['categoria']
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                    if p['es_descontinuado']:
                        agrupado[key]['productos_descontinuados'] += 1
                
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            
            elif granularidad == 'familia':
                agrupado = {}
                for p in productos_detalle:
                    key = f"{p['categoria']} > {p['familia']}"
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'categoria': p['categoria'],
                            'familia': p['familia'],
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                    if p['es_descontinuado']:
                        agrupado[key]['productos_descontinuados'] += 1
                
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            
            else:  # producto
                datos_agrupados = sorted(productos_detalle, key=lambda x: x['importe_actual'], reverse=True)
            
            # Calcular métricas resumen
            efecto_precio_total = total_actual - total_constante
            variacion_real = round(((total_constante - total_actual) / total_actual * 100), 2) if total_actual > 0 else 0
            efecto_inflacion_pct = round((efecto_precio_total / total_constante * 100), 2) if total_constante > 0 else 0
            
            return {
                'servidor': server['name'],
                'system_type': server['system_type'],
                'periodo_actual': periodo_actual,
                'periodo_base': periodo_base,
                'granularidad': granularidad,
                'kpis': {
                    'ventas_actuales': round(total_actual, 2),
                    'ventas_constantes': round(total_constante, 2),
                    'efecto_precio': round(efecto_precio_total, 2),
                    'efecto_inflacion_pct': efecto_inflacion_pct,
                    'variacion_real_pct': variacion_real,
                    'productos_analizados': len([p for p in productos_detalle if not p['es_descontinuado']]),
                    'productos_nuevos': len([p for p in productos_detalle if p.get('es_nuevo')]),
                    'productos_descontinuados': len([p for p in productos_detalle if p.get('es_descontinuado')])
                },
                'datos': datos_agrupados,
                'detalle_productos': productos_detalle if granularidad == 'producto' else None
            }
        
        # FASE 3A.2: Migrado a helper centralizado
        elif is_mpro_system(server.get('system_type')):
            # Para MPRO - Las ventas están en la tabla 'venta' directamente
            # La sucursal está en la tabla 'sucursal' relacionada por Sc_Cve_Sucursal
            
            # BLINDAJE (Abril 2026): Mapeo de nombres de sucursal a códigos
            # El frontend envía nombres (ORIGEN, QUERETARO) pero MPRO usa códigos (0023, 0021)
            NOMBRE_A_CODIGO_SUCURSAL = {
                'ORIGEN': '0023',
                'QUERETARO': '0021',
                '130 QRO': '0021',
                'QRO': '0021',
            }
            
            # Convertir nombre de sucursal a código si es necesario
            sucursal_codigo = sucursal
            if sucursal and sucursal.upper() in NOMBRE_A_CODIGO_SUCURSAL:
                sucursal_codigo = NOMBRE_A_CODIGO_SUCURSAL[sucursal.upper()]
                logging.info(f"Precios Constantes MPRO: Traduciendo sucursal '{sucursal}' -> '{sucursal_codigo}'")
            
            # Filtro de sucursal - en MPRO se relaciona venta con sucursal
            filtro_sucursal = f"AND V.Sc_Cve_Sucursal = '{sucursal_codigo}'" if sucursal != 'all' and sucursal_codigo else ""
            filtro_sucursal_ve = f"AND VE.Sc_Cve_Sucursal = '{sucursal_codigo}'" if sucursal != 'all' and sucursal_codigo else ""
            
            # PASO 1: Obtener VENTAS REALES del período (misma lógica que Dashboard)
            # Esto asegura que los totales coincidan con el Tablero Ejecutivo
            query_ventas_reales_mpro = f"""
SELECT ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas_reales
FROM Venta_Encabezado VE
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{fecha_ini_actual} 00:00:00', 120)
  AND VE.Vn_Fecha <= CONVERT(datetime, '{fecha_fin_actual} 23:59:59', 120)
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {filtro_sucursal_ve}
"""
            result_ventas_reales = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_reales_mpro
            )
            ventas_reales_periodo = float(result_ventas_reales[0]['ventas_reales'] or 0) if result_ventas_reales else 0
            
            query_ventas_actual = f"""
SELECT 
    V.Pr_Cve_Producto as producto_id,
    P.Pr_Descripcion as producto,
    ISNULL(S.Sc_Descripcion, 'Sin Sucursal') as categoria,
    'Productos' as familia,
    SUM(V.Vn_Cantidad_Control_1) as cantidad,
    SUM(V.Vn_Precio_Lista * V.Vn_Cantidad_Control_1) as importe_actual,
    AVG(V.Vn_Precio_Lista) as precio_promedio_actual
FROM venta V
INNER JOIN Producto P ON P.Pr_Cve_Producto = V.Pr_Cve_Producto
LEFT JOIN sucursal S ON S.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
WHERE V.Vn_Fecha >= CONVERT(datetime, '{fecha_ini_actual} 00:00:00', 120)
  AND V.Vn_Fecha <= CONVERT(datetime, '{fecha_fin_actual} 23:59:59', 120)
  AND ISNULL(V.Es_Cve_Estado, '') <> 'CA'
  AND V.Vn_Cantidad_Control_1 > 0
  {filtro_sucursal}
GROUP BY V.Pr_Cve_Producto, P.Pr_Descripcion, S.Sc_Descripcion
"""
            
            query_precios_base = f"""
SELECT 
    V.Pr_Cve_Producto as producto_id,
    AVG(V.Vn_Precio_Lista) as precio_promedio_base
FROM venta V
WHERE V.Vn_Fecha >= CONVERT(datetime, '{fecha_ini_base} 00:00:00', 120)
  AND V.Vn_Fecha <= CONVERT(datetime, '{fecha_fin_base} 23:59:59', 120)
  AND ISNULL(V.Es_Cve_Estado, '') <> 'CA'
  AND V.Vn_Cantidad_Control_1 > 0
  {filtro_sucursal}
GROUP BY V.Pr_Cve_Producto
"""
            
            # Ejecutar queries
            ventas_actual = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_actual
            ) or []
            
            precios_base = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_precios_base
            ) or []
            
            # VALIDACIÓN (Abril 2026): Si no hay datos en el período base, no se puede hacer análisis
            # porque no hay precios de referencia con los cuales comparar
            if not precios_base or len(precios_base) == 0:
                logging.warning(f"Precios Constantes MPRO {server['name']}: Sin datos en período base {periodo_base}")
                return {
                    "servidor": server['name'],
                    "system_type": server['system_type'],
                    "periodo_actual": periodo_actual,
                    "periodo_base": periodo_base,
                    "granularidad": granularidad,
                    "error": f"Sin datos de ventas en el período base ({periodo_base}). No es posible calcular precios constantes sin un período de referencia con ventas.",
                    "kpis": {
                        "ventas_actuales": ventas_reales_periodo,
                        "ventas_constantes": 0,
                        "efecto_precio": 0,
                        "efecto_inflacion_pct": 0,
                        "variacion_real_pct": 0,
                        "productos_analizados": 0,
                        "productos_nuevos": 0,
                        "productos_descontinuados": 0
                    },
                    "datos": [],
                    "detalle_productos": None
                }
            
            # Crear diccionario de precios base
            precios_base_dict = {str(p['producto_id']): float(p['precio_promedio_base'] or 0) for p in precios_base}
            
            # PASO 2: Calcular suma de productos para obtener factor de ajuste
            suma_productos_actual = sum(float(v['importe_actual'] or 0) for v in ventas_actual)
            
            # Factor de ajuste: ventas reales / suma de productos
            factor_ajuste = ventas_reales_periodo / suma_productos_actual if suma_productos_actual > 0 else 1
            logging.info(f"MPRO - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
            
            productos_detalle = []
            total_actual = 0
            total_constante = 0
            
            for venta in ventas_actual:
                producto_id = str(venta['producto_id'])
                cantidad = float(venta['cantidad'] or 0)
                precio_actual = float(venta['precio_promedio_actual'] or 0)
                # Aplicar factor de ajuste al importe para que coincida con ventas reales
                importe_actual = float(venta['importe_actual'] or 0) * factor_ajuste
                
                if producto_id in precios_base_dict:
                    precio_base = precios_base_dict[producto_id]
                    es_nuevo = False
                else:
                    precio_base = precio_actual
                    es_nuevo = True
                
                # El importe constante también debe ajustarse con el factor
                importe_constante = (cantidad * precio_base) * factor_ajuste
                efecto_precio = importe_actual - importe_constante
                variacion_precio_pct = ((precio_actual - precio_base) / precio_base * 100) if precio_base > 0 else 0
                
                productos_detalle.append({
                    'producto_id': producto_id,
                    'producto': venta['producto'],
                    'categoria': venta['categoria'],
                    'familia': venta['familia'],
                    'cantidad': cantidad,
                    'precio_actual': precio_actual,
                    'precio_base': precio_base,
                    'importe_actual': importe_actual,
                    'importe_constante': importe_constante,
                    'efecto_precio': efecto_precio,
                    'variacion_precio_pct': round(variacion_precio_pct, 2),
                    'es_nuevo': es_nuevo,
                    'es_descontinuado': False
                })
                
                total_actual += importe_actual
                total_constante += importe_constante
            
            # Agrupar según granularidad (mismo código)
            if granularidad == 'categoria':
                agrupado = {}
                for p in productos_detalle:
                    key = p['categoria']
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            elif granularidad == 'familia':
                agrupado = {}
                for p in productos_detalle:
                    key = f"{p['categoria']} > {p['familia']}"
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'categoria': p['categoria'],
                            'familia': p['familia'],
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            else:
                datos_agrupados = sorted(productos_detalle, key=lambda x: x['importe_actual'], reverse=True)
            
            efecto_precio_total = total_actual - total_constante
            variacion_real = round(((total_constante - total_actual) / total_actual * 100), 2) if total_actual > 0 else 0
            efecto_inflacion_pct = round((efecto_precio_total / total_constante * 100), 2) if total_constante > 0 else 0
            
            return {
                'servidor': server['name'],
                'system_type': server['system_type'],
                'periodo_actual': periodo_actual,
                'periodo_base': periodo_base,
                'granularidad': granularidad,
                'kpis': {
                    'ventas_actuales': round(total_actual, 2),
                    'ventas_constantes': round(total_constante, 2),
                    'efecto_precio': round(efecto_precio_total, 2),
                    'efecto_inflacion_pct': efecto_inflacion_pct,
                    'variacion_real_pct': variacion_real,
                    'productos_analizados': len([p for p in productos_detalle if not p['es_descontinuado']]),
                    'productos_nuevos': len([p for p in productos_detalle if p.get('es_nuevo')]),
                    'productos_descontinuados': len([p for p in productos_detalle if p.get('es_descontinuado')])
                },
                'datos': datos_agrupados,
                'detalle_productos': productos_detalle if granularidad == 'producto' else None
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Sistema no soportado: {server['system_type']}")
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error en precios constantes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-4H (Abril 2026)
# ============================================================================

@router.get("/comercial/reporte-pax/{server_id}")
async def comercial_reporte_pax(
    server_id: str, 
    sucursal: str = Query(default=""),
    fecha: str = Query(default=""),  # Formato YYYY-MM-DD
    agrupacion: str = Query(default="vendedor"),  # vendedor o ticket
    current_user: Dict = Depends(get_current_user)
):
    """
    Reporte de PAX con drill-down por vendedor o ticket.
    Incluye comparativas vs día/mes/año anterior.
    
    RESPUESTA HOMOLOGADA:
    - source_status: SUCCESS | NO_DATA | DEGRADED_CACHE | SOURCE_UNREACHABLE | ERROR
    - cache_used: true/false
    - last_successful_sync: timestamp si se usó cache
    - data: {items, resumen, comparativo, fecha, servidor}
    """
    from modules.comercial.cache_service import (
        SourceStatus, build_cache_key, get_cached_response, 
        save_to_cache, build_envelope_response
    )
    
    server = await get_server_by_id(server_id)
    if not server:
        return build_envelope_response(
            source_status=SourceStatus.ERROR,
            data={"items": [], "resumen": {}, "comparativo": {}},
            source_message="Servidor no encontrado"
        )
    
    # FASE 6-8: Validación centralizada de acceso
    await validate_server_access_rbac(current_user, server_id)
    
    # Fecha seleccionada o hoy
    if fecha:
        fecha_sel = datetime.strptime(fecha, '%Y-%m-%d')
    else:
        fecha_sel = datetime.now()
    
    fecha_str = fecha_sel.strftime('%Y-%m-%d')
    
    # Construir clave de cache
    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
    cache_key = build_cache_key(
        modulo="comercial",
        endpoint="reporte_pax",
        server_id=server_id,
        sucursal=sucursal,
        fecha=fecha_str,
        system_type=server.get('system_type', ''),
        agrupacion=agrupacion
    )
    
    def empty_response():
        return {
            "items": [],
            "resumen": {"pax_total": 0, "ventas_total": 0, "total_cheques": 0, "pax_promedio": 0, "cheque_promedio": 0},
            "comparativo": {"vs_dia_anterior": 0, "vs_mes_anterior": 0, "vs_ano_anterior": 0},
            "fecha": fecha_str,
            "servidor": server['name']
        }
    
    try:
        # Fechas para comparativos
        fecha_dia_ant = (fecha_sel - timedelta(days=1)).strftime('%Y-%m-%d')
        fecha_mes_ant = (fecha_sel.replace(day=1) - timedelta(days=1)).replace(day=min(fecha_sel.day, 28)).strftime('%Y-%m-%d')
        fecha_ano_ant = fecha_sel.replace(year=fecha_sel.year - 1).strftime('%Y-%m-%d')
        
        items = []
        resumen = {"pax_total": 0, "ventas_total": 0, "total_cheques": 0, "pax_promedio": 0, "cheque_promedio": 0}
        comparativo = {"vs_dia_anterior": 0, "vs_mes_anterior": 0, "vs_ano_anterior": 0}
        query_success = False
        
        # FASE 3A.2: Migrado a helper centralizado
        if is_softrestaurant_system(server.get('system_type')):
            f_fmt = fecha_str.replace('-', '')
            
            if agrupacion == 'vendedor':
                # Agrupar por vendedor con detalle de cheques
                query = f"""
SELECT 
    ISNULL(m.nombre, 'Sin Vendedor') as vendedor,
    COUNT(DISTINCT ch.folio) as num_cheques,
    ISNULL(SUM(ch.nopersonas), 0) as pax,
    ISNULL(SUM(ch.total), 0) as total
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
LEFT JOIN meseros m ON m.idmesero = ch.idmesero
WHERE CONVERT(varchar, t.apertura, 112) >= '{f_fmt}'
  AND CONVERT(varchar, t.apertura, 112) <= '{f_fmt}'
  AND ch.cancelado = 0
  AND ch.total > 0
GROUP BY m.nombre
ORDER BY SUM(ch.total) DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
                
                if result is not None:
                    query_success = True
                
                for idx, row in enumerate(result or []):
                    vendedor = row.get('vendedor', 'Sin Vendedor')
                    pax = int(row.get('pax') or 0)
                    total = float(row.get('total') or 0)
                    num_cheques = int(row.get('num_cheques') or 0)
                    
                    # Obtener detalle de cheques por vendedor
                    query_detalle = f"""
SELECT 
    ch.folio,
    ISNULL(ch.nopersonas, 0) as pax,
    ch.total
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
LEFT JOIN meseros m ON m.idmesero = ch.idmesero
WHERE CONVERT(varchar, t.apertura, 112) >= '{f_fmt}'
  AND CONVERT(varchar, t.apertura, 112) <= '{f_fmt}'
  AND ch.cancelado = 0
  AND ch.total > 0
  AND ISNULL(m.nombre, 'Sin Vendedor') = '{vendedor.replace("'", "''")}'
ORDER BY ch.total DESC
"""
                    detalle_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_detalle
                    )
                    
                    detalle = []
                    for det in detalle_result or []:
                        det_pax = int(det.get('pax') or 0)
                        det_total = float(det.get('total') or 0)
                        detalle.append({
                            "folio": str(det.get('folio', '')),
                            "pax": det_pax,
                            "total": det_total,
                            "pax_promedio": det_total / det_pax if det_pax > 0 else det_total
                        })
                    
                    items.append({
                        "id": f"v_{idx}",
                        "nombre": vendedor,
                        "pax": pax,
                        "total": total,
                        "num_cheques": num_cheques,
                        "pax_promedio": total / pax if pax > 0 else total,
                        "detalle": detalle
                    })
            else:
                # Agrupar por ticket/cheque con detalle de vendedor
                query = f"""
SELECT 
    ch.folio,
    ISNULL(m.nombre, 'Sin Vendedor') as vendedor,
    ISNULL(ch.nopersonas, 0) as pax,
    ch.total
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
LEFT JOIN meseros m ON m.idmesero = ch.idmesero
WHERE CONVERT(varchar, t.apertura, 112) >= '{f_fmt}'
  AND CONVERT(varchar, t.apertura, 112) <= '{f_fmt}'
  AND ch.cancelado = 0
  AND ch.total > 0
ORDER BY ch.total DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
                
                if result is not None:
                    query_success = True
                
                for idx, row in enumerate(result or []):
                    pax = int(row.get('pax') or 0)
                    total = float(row.get('total') or 0)
                    items.append({
                        "id": f"t_{idx}",
                        "folio": str(row.get('folio', '')),
                        "nombre": str(row.get('folio', '')),
                        "vendedor": row.get('vendedor', 'Sin Vendedor'),
                        "pax": pax,
                        "total": total,
                        "pax_promedio": total / pax if pax > 0 else total,
                        "detalle": [{
                            "vendedor": row.get('vendedor', 'Sin Vendedor'),
                            "pax": pax,
                            "total": total,
                            "pax_promedio": total / pax if pax > 0 else total
                        }]
                    })
            
            # Calcular totales
            resumen["pax_total"] = sum(i['pax'] for i in items)
            resumen["ventas_total"] = sum(i['total'] for i in items)
            resumen["total_cheques"] = len(items) if agrupacion == 'ticket' else sum(i.get('num_cheques', 1) for i in items)
            resumen["pax_promedio"] = resumen["ventas_total"] / resumen["pax_total"] if resumen["pax_total"] > 0 else 0
            resumen["cheque_promedio"] = resumen["ventas_total"] / resumen["total_cheques"] if resumen["total_cheques"] > 0 else 0
            
            # Comparativos - helper interno
            def get_pax_fecha(f):
                f_q = f.replace('-', '')
                q = f"""
SELECT ISNULL(SUM(ch.nopersonas), 0) as pax, ISNULL(SUM(ch.total), 0) as total
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
WHERE CONVERT(varchar, t.apertura, 112) = '{f_q}'
  AND ch.cancelado = 0 AND ch.total > 0
"""
                r = execute_sql_query(server['host'], server['port'], server['database'], 
                                      server['username'], server['password'], q)
                return int(r[0]['pax'] or 0) if r else 0, float(r[0]['total'] or 0) if r else 0
            
            pax_ant, total_ant = get_pax_fecha(fecha_dia_ant)
            pax_mes, total_mes = get_pax_fecha(fecha_mes_ant)
            pax_ano, total_ano = get_pax_fecha(fecha_ano_ant)
            
            pax_prom_actual = resumen["pax_promedio"]
            pax_prom_ant = total_ant / pax_ant if pax_ant > 0 else 0
            pax_prom_mes = total_mes / pax_mes if pax_mes > 0 else 0
            pax_prom_ano = total_ano / pax_ano if pax_ano > 0 else 0
            
            comparativo["vs_dia_anterior"] = ((pax_prom_actual - pax_prom_ant) / pax_prom_ant * 100) if pax_prom_ant > 0 else 0
            comparativo["vs_mes_anterior"] = ((pax_prom_actual - pax_prom_mes) / pax_prom_mes * 100) if pax_prom_mes > 0 else 0
            comparativo["vs_ano_anterior"] = ((pax_prom_actual - pax_prom_ano) / pax_prom_ano * 100) if pax_prom_ano > 0 else 0
        
        # FASE 3A.2: Migrado a helper centralizado
        elif is_mpro_system(server.get('system_type')):
            # Implementación para MPRO
            # IMPORTANTE: Usar formato seguro de fecha con CONVERT para evitar errores regionales
            fecha_filter = build_sql_date_equals_safe('V.Vn_Fecha', fecha_str)
            # BLINDAJE (Abril 2026): Campo de cancelación en MPRO es Es_Cve_Estado, NO Vn_Cancelacion
            cancelacion_filter = "ISNULL(V.Es_Cve_Estado, '') <> 'CA'"
            
            if agrupacion == 'vendedor':
                # CORRECCIÓN (Abril 2026): En MPRO, el nombre del vendedor está en tabla Vendedor, NO en Empleado
                # El campo Vn_Cve_Vendedor en Venta_Encabezado se relaciona con Vendedor.Vn_Cve_Vendedor
                query = f"""
SELECT 
    ISNULL(VND.Vn_Descripcion, 'Sin Vendedor') as vendedor,
    COUNT(DISTINCT V.Vn_Folio) as num_cheques,
    ISNULL(SUM(C.Co_Personas), 0) as pax,
    SUM(V.Vn_Precio_Neto_Importe) as total
FROM Venta_Encabezado V
LEFT JOIN Comanda C ON C.Co_Folio = V.Vn_Folio AND C.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
LEFT JOIN Vendedor VND ON VND.Vn_Cve_Vendedor = V.Vn_Cve_Vendedor
WHERE {fecha_filter}
  AND {cancelacion_filter}
  AND V.Vn_Precio_Neto_Importe > 0
GROUP BY VND.Vn_Descripcion
ORDER BY SUM(V.Vn_Precio_Neto_Importe) DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
                
                if result is not None:
                    query_success = True
                
                for idx, row in enumerate(result or []):
                    vendedor = row.get('vendedor', 'Sin Vendedor')
                    pax = int(row.get('pax') or 0)
                    total = float(row.get('total') or 0)
                    num_cheques = int(row.get('num_cheques') or 0)
                    
                    # Detalle por vendedor
                    # CORRECCIÓN (Abril 2026): Usar tabla Vendedor en lugar de Empleado
                    query_det = f"""
SELECT V.Vn_Folio as folio, ISNULL(C.Co_Personas, 0) as pax, V.Vn_Precio_Neto_Importe as total
FROM Venta_Encabezado V
LEFT JOIN Comanda C ON C.Co_Folio = V.Vn_Folio AND C.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
LEFT JOIN Vendedor VND ON VND.Vn_Cve_Vendedor = V.Vn_Cve_Vendedor
WHERE {fecha_filter} AND {cancelacion_filter} AND V.Vn_Precio_Neto_Importe > 0
  AND ISNULL(VND.Vn_Descripcion, 'Sin Vendedor') = '{vendedor.replace("'", "''")}'
ORDER BY V.Vn_Precio_Neto_Importe DESC
"""
                    det_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_det
                    )
                    
                    detalle = []
                    for det in det_result or []:
                        det_pax = int(det.get('pax') or 0)
                        det_total = float(det.get('total') or 0)
                        detalle.append({
                            "folio": str(det.get('folio', '')),
                            "pax": det_pax,
                            "total": det_total,
                            "pax_promedio": det_total / det_pax if det_pax > 0 else det_total
                        })
                    
                    items.append({
                        "id": f"v_{idx}",
                        "nombre": vendedor,
                        "pax": pax,
                        "total": total,
                        "num_cheques": num_cheques,
                        "pax_promedio": total / pax if pax > 0 else total,
                        "detalle": detalle
                    })
            else:
                # Por ticket
                # CORRECCIÓN (Abril 2026): Usar tabla Vendedor en lugar de Empleado
                query = f"""
SELECT 
    V.Vn_Folio as folio,
    ISNULL(VND.Vn_Descripcion, 'Sin Vendedor') as vendedor,
    ISNULL(C.Co_Personas, 0) as pax,
    V.Vn_Precio_Neto_Importe as total
FROM Venta_Encabezado V
LEFT JOIN Comanda C ON C.Co_Folio = V.Vn_Folio AND C.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
LEFT JOIN Vendedor VND ON VND.Vn_Cve_Vendedor = V.Vn_Cve_Vendedor
WHERE {fecha_filter}
  AND {cancelacion_filter}
  AND V.Vn_Precio_Neto_Importe > 0
ORDER BY V.Vn_Precio_Neto_Importe DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
                
                if result is not None:
                    query_success = True
                
                for idx, row in enumerate(result or []):
                    pax = int(row.get('pax') or 0)
                    total = float(row.get('total') or 0)
                    items.append({
                        "id": f"t_{idx}",
                        "folio": str(row.get('folio', '')),
                        "nombre": str(row.get('folio', '')),
                        "vendedor": row.get('vendedor', 'Sin Vendedor'),
                        "pax": pax,
                        "total": total,
                        "pax_promedio": total / pax if pax > 0 else total,
                        "detalle": [{
                            "vendedor": row.get('vendedor', 'Sin Vendedor'),
                            "pax": pax,
                            "total": total,
                            "pax_promedio": total / pax if pax > 0 else total
                        }]
                    })
            
            # Calcular resumen
            resumen["pax_total"] = sum(i['pax'] for i in items)
            resumen["ventas_total"] = sum(i['total'] for i in items)
            resumen["total_cheques"] = len(items) if agrupacion == 'ticket' else sum(i.get('num_cheques', 1) for i in items)
            resumen["pax_promedio"] = resumen["ventas_total"] / resumen["pax_total"] if resumen["pax_total"] > 0 else 0
            resumen["cheque_promedio"] = resumen["ventas_total"] / resumen["total_cheques"] if resumen["total_cheques"] > 0 else 0
            
            # Comparativos para MPRO - helper interno
            # BLINDAJE (Abril 2026): Usar filtro correcto de cancelación y formato de fecha seguro
            def get_pax_mpro(f):
                fecha_f = build_sql_date_equals_safe('V.Vn_Fecha', f)
                q = f"""
SELECT ISNULL(SUM(C.Co_Personas), 0) as pax, SUM(V.Vn_Precio_Neto_Importe) as total
FROM Venta_Encabezado V
LEFT JOIN Comanda C ON C.Co_Folio = V.Vn_Folio AND C.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
WHERE {fecha_f} AND ISNULL(V.Es_Cve_Estado, '') <> 'CA' AND V.Vn_Precio_Neto_Importe > 0
"""
                r = execute_sql_query(server['host'], server['port'], server['database'],
                                      server['username'], server['password'], q)
                return int(r[0]['pax'] or 0) if r else 0, float(r[0]['total'] or 0) if r else 0
            
            pax_ant, total_ant = get_pax_mpro(fecha_dia_ant)
            pax_mes, total_mes = get_pax_mpro(fecha_mes_ant)
            pax_ano, total_ano = get_pax_mpro(fecha_ano_ant)
            
            pax_prom_actual = resumen["pax_promedio"]
            pax_prom_ant = total_ant / pax_ant if pax_ant > 0 else 0
            pax_prom_mes = total_mes / pax_mes if pax_mes > 0 else 0
            pax_prom_ano = total_ano / pax_ano if pax_ano > 0 else 0
            
            comparativo["vs_dia_anterior"] = ((pax_prom_actual - pax_prom_ant) / pax_prom_ant * 100) if pax_prom_ant > 0 else 0
            comparativo["vs_mes_anterior"] = ((pax_prom_actual - pax_prom_mes) / pax_prom_mes * 100) if pax_prom_mes > 0 else 0
            comparativo["vs_ano_anterior"] = ((pax_prom_actual - pax_prom_ano) / pax_prom_ano * 100) if pax_prom_ano > 0 else 0
        
        # Construir respuesta
        data = {
            "items": items,
            "resumen": resumen,
            "comparativo": comparativo,
            "fecha": fecha_str,
            "servidor": server['name']
        }
        
        if query_success:
            # Query exitosa - guardar en cache
            await save_to_cache(cache_key, data, "reporte_pax", server['name'], server['system_type'])
            
            has_data = len(items) > 0 or resumen.get("pax_total", 0) > 0
            return build_envelope_response(
                source_status=SourceStatus.SUCCESS if has_data else SourceStatus.NO_DATA,
                data=data,
                server_name=server['name'],
                server_type=server['system_type'],
                cache_used=False,
                fecha=fecha_str
            )
        else:
            raise Exception("Query no retornó datos válidos")
        
    except Exception as e:
        logging.warning(f"Error en reporte PAX para {server['name']}: {e}")
        
        # Intentar cache como fallback
        cached = await get_cached_response(cache_key)
        
        if cached and cached.get("data"):
            return build_envelope_response(
                source_status=SourceStatus.DEGRADED_CACHE,
                data=cached["data"],
                server_name=server['name'],
                server_type=server['system_type'],
                cache_used=True,
                last_successful_sync=cached.get("cached_at"),
                source_message=f"Datos de cache (última actualización: {cached.get('cached_at', 'desconocido')})"
            )
        
        # Sin cache - devolver estructura vacía controlada
        return build_envelope_response(
            source_status=SourceStatus.SOURCE_UNREACHABLE,
            data=empty_response(),
            server_name=server['name'],
            server_type=server['system_type'],
            cache_used=False,
            source_message=f"No se pudo conectar a {server['name']} y no hay cache disponible"
        )


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-5B (Abril 2026)
# ============================================================================

@router.get("/comercial/dashboard/{server_id}")
async def comercial_dashboard(
    server_id: str, 
    sucursal: str = Query(default=""), 
    periodo: str = Query(default="dia"),  # dia, semana, mes
    meses: str = Query(default=""),  # "01,02,03" - Lista de meses separados por coma
    anio: str = Query(default=""),  # "2025" - Año específico (compatibilidad)
    anios: str = Query(default=""),  # "2025,2024" - Múltiples años separados por coma
    tipo_comparacion: str = Query(default="dias_equiv"),  # dias_equiv o mes_completo
    current_user: Dict = Depends(get_current_user)
):
    """
    Dashboard principal de ventas con KPIs y comparativos.
    Soporta SoftRestaurant y MPRO.
    Ahora soporta multiselección de meses y múltiples años.
    tipo_comparacion: 'dias_equiv' compara días 1-N vs días 1-N del período anterior
                      'mes_completo' compara vs el mes completo anterior
    
    RESPUESTA INCLUYE:
    - source_status: 'SUCCESS' | 'NO_DATA' | 'SOURCE_UNREACHABLE' | 'ERROR'
    - source_message: Mensaje descriptivo del estado
    """
    server = await get_server_by_id(server_id)
    if not server:
        return {
            "source_status": "ERROR",
            "source_message": "Servidor no encontrado en configuración",
            "kpis": None,
            "comparativo": None,
            "alertas": []
        }
    
    # FASE 6-8: Validación centralizada de acceso
    await validate_server_access_rbac(current_user, server_id)
    
    # ============================================================================
    # NOTA: La verificación de conectividad se realiza implícitamente cuando
    # se ejecutan las queries de datos reales. Si hay error de conexión, se
    # captura en el bloque except y se retorna SOURCE_UNREACHABLE.
    # ============================================================================
    
    try:
        # Calcular fechas según período
        hoy = datetime.now()
        
        # Obtener lista de años (priorizar 'anios' sobre 'anio')
        if anios:
            lista_anios = [int(a.strip()) for a in anios.split(',') if a.strip()]
        elif anio:
            lista_anios = [int(anio)]
        else:
            lista_anios = [hoy.year]
        
        # Si se proporcionan meses y años específicos, usar esos
        # BLINDAJE: Definir variables al inicio para evitar errores de variable no definida
        year = hoy.year  # Default: año actual
        mes_min = hoy.month
        mes_max = hoy.month
        lista_meses = [str(hoy.month)]  # Default para logging
        if meses and lista_anios:
            lista_meses = [m.strip() for m in meses.split(',') if m.strip()]
            
            # Usar el año más reciente para la consulta principal
            year = max(lista_anios)
            
            # Para múltiples meses, calcular rango de fechas
            mes_min = min([int(m) for m in lista_meses])
            mes_max = max([int(m) for m in lista_meses])
            
            # Verificar si estamos consultando el mes actual
            es_mes_actual = (year == hoy.year and mes_max == hoy.month)
            
            fecha_ini = f"{year}-{str(mes_min).zfill(2)}-01"
            
            # ============= HOMOLOGACIÓN: Usar fecha_fin = AYER para mes actual (igual que Tablero Ejecutivo) =============
            if es_mes_actual:
                ayer = hoy - timedelta(days=1)
                fecha_fin = ayer.strftime('%Y-%m-%d')
                logging.info(f"Dashboard Comercial: Mes actual - usando fecha_fin=AYER ({fecha_fin}) para homologar con Tablero Ejecutivo")
            else:
                if mes_max == 12:
                    ultimo_dia = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    ultimo_dia = datetime(year, mes_max + 1, 1) - timedelta(days=1)
                fecha_fin = ultimo_dia.strftime('%Y-%m-%d')
            
            if tipo_comparacion == "mes_completo" or not es_mes_actual:
                if mes_min == 1:
                    fecha_ini_ant = f"{year - 1}-12-01"
                    fecha_fin_ant = f"{year - 1}-12-31"
                else:
                    mes_ant = mes_min - 1
                    fecha_ini_ant = f"{year}-{str(mes_ant).zfill(2)}-01"
                    if mes_ant == 12:
                        ultimo_dia_ant = datetime(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        ultimo_dia_ant = datetime(year, mes_ant + 1, 1) - timedelta(days=1)
                    fecha_fin_ant = ultimo_dia_ant.strftime('%Y-%m-%d')
                
                fecha_ini_ano_ant = f"{year - 1}-{str(mes_min).zfill(2)}-01"
                if mes_max == 12:
                    ultimo_dia_ano_ant = datetime(year, 1, 1) - timedelta(days=1)
                else:
                    ultimo_dia_ano_ant = datetime(year - 1, mes_max + 1, 1) - timedelta(days=1)
                fecha_fin_ano_ant = ultimo_dia_ano_ant.strftime('%Y-%m-%d')
            else:
                fecha_ini_ant = "PENDIENTE"
                fecha_fin_ant = "PENDIENTE"
                fecha_ini_ano_ant = "PENDIENTE"
                fecha_fin_ano_ant = "PENDIENTE"
            
            logging.info(f"Comercial Dashboard (multiselección): {server['name']} - Meses: {lista_meses} Año: {year} ({fecha_ini} a {fecha_fin}) - Tipo: {tipo_comparacion}")
            
            # ============= GUARD CLAUSE: Rango invertido (primer día del mes actual) =============
            if fecha_fin < fecha_ini:
                logging.warning(f"Dashboard Comercial: Rango invertido detectado ({fecha_ini} a {fecha_fin}). Sin días cerrados del mes actual.")
                return {
                    "source_status": "NO_DATA",
                    "source_message": "Sin días cerrados del mes actual. La proyección iniciará cuando exista al menos un corte cerrado del mes.",
                    "server_name": server.get('name', 'Desconocido'),
                    "server_type": server.get('system_type', 'Desconocido'),
                    "fecha_inicio": fecha_ini,
                    "fecha_fin": fecha_ini,
                    "kpis": {
                        "ventas_periodo": 0,
                        "ticket_promedio": 0,
                        "cheques_total": 0,
                        "pax_total": 0,
                        "pax_promedio": 0,
                        "consumo_persona": 0,
                        "mesas_atendidas": 0,
                        "rotacion_mesas": 0,
                        "venta_por_hora": 0
                    },
                    "comparativo": {
                        "vs_periodo_anterior": 0,
                        "vs_ano_anterior": 0,
                        "vs_presupuesto": 0,
                        "tipo_comparacion": tipo_comparacion,
                        "motivo": "SIN_DIAS_CERRADOS_MES_ACTUAL"
                    },
                    "alertas": []
                }
            
        elif periodo == "dia":
            fecha_ini = hoy.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
            fecha_ini_ant = (hoy - timedelta(days=1)).strftime('%Y-%m-%d')
            fecha_fin_ant = fecha_ini_ant
            try:
                fecha_ini_ano_ant = hoy.replace(year=hoy.year - 1).strftime('%Y-%m-%d')
                fecha_fin_ano_ant = fecha_ini_ano_ant
            except ValueError:
                fecha_ini_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-28"
                fecha_fin_ano_ant = fecha_ini_ano_ant
        elif periodo == "semana":
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fecha_ini = inicio_semana.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
            fecha_ini_ant = (inicio_semana - timedelta(days=7)).strftime('%Y-%m-%d')
            fecha_fin_ant = (inicio_semana - timedelta(days=1)).strftime('%Y-%m-%d')
            try:
                fecha_ini_ano_ant = inicio_semana.replace(year=hoy.year - 1).strftime('%Y-%m-%d')
                fecha_fin_ano_ant = hoy.replace(year=hoy.year - 1).strftime('%Y-%m-%d')
            except ValueError:
                fecha_ini_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-01"
                fecha_fin_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-07"
        else:  # mes
            ayer_periodo = hoy - timedelta(days=1)
            fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
            fecha_fin = ayer_periodo.strftime('%Y-%m-%d')
            dia_actual = ayer_periodo.day
            logging.info(f"Dashboard Comercial período 'mes': usando fecha_fin=AYER ({fecha_fin}) para homologar con Tablero Ejecutivo")
            
            primer_dia_mes = hoy.replace(day=1)
            ultimo_dia_mes_ant = primer_dia_mes - timedelta(days=1)
            
            if tipo_comparacion == "dias_equiv":
                fecha_ini_ant = ultimo_dia_mes_ant.replace(day=1).strftime('%Y-%m-%d')
                dia_max_mes_ant = ultimo_dia_mes_ant.day
                dia_comparar = min(dia_actual - 1, dia_max_mes_ant)
                if dia_comparar < 1:
                    dia_comparar = 1
                fecha_fin_ant = ultimo_dia_mes_ant.replace(day=dia_comparar).strftime('%Y-%m-%d')
                
                try:
                    fecha_ini_ano_ant = hoy.replace(year=hoy.year - 1, day=1).strftime('%Y-%m-%d')
                    ano_ant_ultimo_dia = (datetime(hoy.year - 1, hoy.month + 1, 1) - timedelta(days=1)).day if hoy.month < 12 else 31
                    dia_ano_ant = min(dia_actual - 1, ano_ant_ultimo_dia)
                    if dia_ano_ant < 1:
                        dia_ano_ant = 1
                    fecha_fin_ano_ant = hoy.replace(year=hoy.year - 1, day=dia_ano_ant).strftime('%Y-%m-%d')
                except ValueError:
                    fecha_ini_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-01"
                    fecha_fin_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-28"
            else:
                fecha_ini_ant = ultimo_dia_mes_ant.replace(day=1).strftime('%Y-%m-%d')
                fecha_fin_ant = ultimo_dia_mes_ant.strftime('%Y-%m-%d')
                
                try:
                    fecha_ini_ano_ant = hoy.replace(year=hoy.year - 1, day=1).strftime('%Y-%m-%d')
                    if hoy.month == 12:
                        ultimo_dia_ano_ant = datetime(hoy.year, 1, 1) - timedelta(days=1)
                    else:
                        ultimo_dia_ano_ant = datetime(hoy.year - 1, hoy.month + 1, 1) - timedelta(days=1)
                    fecha_fin_ano_ant = ultimo_dia_ano_ant.strftime('%Y-%m-%d')
                except ValueError:
                    fecha_ini_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-01"
                    fecha_fin_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-28"
        
        logging.info(f"Comercial Dashboard: {server['name']} - Período: {periodo} ({fecha_ini} a {fecha_fin}) - Tipo: {tipo_comparacion}")
        logging.info(f"Comparación mes ant: {fecha_ini_ant} a {fecha_fin_ant}")
        logging.info(f"Comparación año ant: {fecha_ini_ano_ant} a {fecha_fin_ano_ant}")
        
        # FASE 3A.2: Migrado a helper centralizado
        if is_softrestaurant_system(server.get('system_type')):
            # Usar formato YYYYMMDD universal (funciona en cualquier configuración regional)
            f_ini = sql_fecha(fecha_ini, con_hora=False)
            f_fin = sql_fecha(fecha_fin, con_hora=False)
            f_ini_ant = sql_fecha(fecha_ini_ant, con_hora=False) if fecha_ini_ant != "PENDIENTE" else "PENDIENTE"
            f_fin_ant = sql_fecha(fecha_fin_ant, con_hora=False) if fecha_fin_ant != "PENDIENTE" else "PENDIENTE"
            f_ini_ano_ant = sql_fecha(fecha_ini_ano_ant, con_hora=False)
            f_fin_ano_ant = sql_fecha(fecha_fin_ano_ant, con_hora=False)
            
            if tipo_comparacion == "dias_equiv" and fecha_ini_ant == "PENDIENTE":
                query_ultimo_dia = f"""
SELECT MAX(CONVERT(DATE, turnos.apertura)) as ultimo_dia_venta
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
  AND cheques.cancelado = 0
"""
                result_ultimo = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_ultimo_dia
                )
                
                if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
                    ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
                    if isinstance(ultimo_dia_venta, str):
                        dia_con_datos = int(ultimo_dia_venta.split('-')[2]) if '-' in ultimo_dia_venta else int(ultimo_dia_venta[-2:])
                    else:
                        dia_con_datos = ultimo_dia_venta.day
                    
                    logging.info(f"SoftRestaurant - Último día con ventas: {ultimo_dia_venta} (día {dia_con_datos})")
                    
                    f_fin = f"{year}{str(mes_max).zfill(2)}{str(dia_con_datos).zfill(2)}"
                    
                    mes_actual = mes_max
                    anio_actual = year
                    if mes_actual == 1:
                        mes_ant = 12
                        anio_ant = anio_actual - 1
                    else:
                        mes_ant = mes_actual - 1
                        anio_ant = anio_actual
                    
                    if mes_ant == 12:
                        max_dia_mes_ant = 31
                    elif mes_ant in [4, 6, 9, 11]:
                        max_dia_mes_ant = 30
                    elif mes_ant == 2:
                        max_dia_mes_ant = 29 if (anio_ant % 4 == 0 and (anio_ant % 100 != 0 or anio_ant % 400 == 0)) else 28
                    else:
                        max_dia_mes_ant = 31
                    
                    dia_comparar = min(dia_con_datos, max_dia_mes_ant)
                    fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
                    fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
                    
                    anio_pasado = year - 1
                    fecha_ini_ano_ant = f"{anio_pasado}-{str(mes_min).zfill(2)}-01"
                    
                    if mes_max == 2:
                        max_dia_ano_ant = 29 if (anio_pasado % 4 == 0 and (anio_pasado % 100 != 0 or anio_pasado % 400 == 0)) else 28
                    elif mes_max in [4, 6, 9, 11]:
                        max_dia_ano_ant = 30
                    else:
                        max_dia_ano_ant = 31
                    
                    dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
                    fecha_fin_ano_ant = f"{anio_pasado}-{str(mes_max).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
                    
                    logging.info(f"Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_ano_ant} a {fecha_fin_ano_ant} (multiselección: {mes_min}-{mes_max})")
                else:
                    dia_con_datos = 1
                    fecha_ini_ant = fecha_ini.replace(f"-{str(mes_max).zfill(2)}-", f"-{str(mes_max-1).zfill(2)}-") if mes_max > 1 else fecha_ini.replace(f"{year}-01-", f"{year-1}-12-")
                    fecha_fin_ant = fecha_ini_ant
                    fecha_ini_ano_ant = fecha_ini.replace(str(year), str(year-1))
                    fecha_fin_ano_ant = fecha_ini_ano_ant
            
            # Las fechas ya están en formato YYYYMMDD desde sql_fecha()
            # Solo convertir las que fueron recalculadas arriba (tienen guiones)
            if '-' in str(f_ini_ant):
                f_ini_ant = f_ini_ant.replace('-', '')
            if '-' in str(f_fin_ant):
                f_fin_ant = f_fin_ant.replace('-', '')
            if '-' in str(f_ini_ano_ant):
                f_ini_ano_ant = f_ini_ano_ant.replace('-', '')
            if '-' in str(f_fin_ano_ant):
                f_fin_ano_ant = f_fin_ano_ant.replace('-', '')
            
            logging.info(f"SoftRestaurant Query - Período: {f_ini} a {f_fin}, Mes ant: {f_ini_ant} a {f_fin_ant}, Año ant: {f_ini_ano_ant} a {f_fin_ano_ant}")
            
            # ============================================================================
            # FASE 7-FIX: EDARSAHUB COMO FUENTE PRINCIPAL
            # ============================================================================
            # PROBLEMA: Dashboard mostraba "Sin Datos" cuando servidor remoto fallaba
            # PERO EDARSAHUB sí tiene datos en Comercial_KPIs_Diarios_v2.
            #
            # SOLUCIÓN: Usar EDARSAHUB primero (igual que Tablero Ejecutivo).
            # MÁXIMA: EDARSAHUB SQL es el cerebro del sistema.
            # Solo ir a servidor remoto si EDARSAHUB no tiene datos.
            # ============================================================================
            
            from .service import get_dashboard_kpis_from_edarsahub
            
            # Intentar obtener datos de EDARSAHUB primero
            edarsahub_kpis = get_dashboard_kpis_from_edarsahub(
                server_id=server_id,
                fecha_ini=fecha_ini,
                fecha_fin=fecha_fin,
                fecha_ini_ant=fecha_ini_ant if fecha_ini_ant != "PENDIENTE" else None,
                fecha_fin_ant=fecha_fin_ant if fecha_fin_ant != "PENDIENTE" else None,
                fecha_ini_ano_ant=fecha_ini_ano_ant,
                fecha_fin_ano_ant=fecha_fin_ano_ant,
                sucursal_id=sucursal if sucursal else 'DEFAULT'
            )
            
            if edarsahub_kpis:
                # EDARSAHUB tiene datos - usar estos como fuente principal
                logging.info(f"[DASHBOARD-FIX] {server['name']}: Usando datos de EDARSAHUB (ventas=${edarsahub_kpis['ventas_periodo']:,.2f})")
                
                return {
                    "source_status": "SUCCESS",
                    "source_message": f"Datos consolidados de EDARSAHUB ({edarsahub_kpis['registros_consultados']} días)",
                    "source_type": edarsahub_kpis['source'],
                    "server_name": server.get('name', 'Desconocido'),
                    "server_type": server.get('system_type', 'Desconocido'),
                    "fecha_inicio": fecha_ini,
                    "fecha_fin": fecha_fin,
                    "kpis": {
                        "ventas_periodo": edarsahub_kpis['ventas_periodo'],
                        "ticket_promedio": edarsahub_kpis['ticket_promedio'],
                        "cheques_total": edarsahub_kpis['cheques_total'],
                        "pax_total": edarsahub_kpis['pax_total'],
                        "pax_promedio": edarsahub_kpis['pax_promedio'],
                        "consumo_persona": edarsahub_kpis['consumo_persona'],
                        "mesas_atendidas": edarsahub_kpis['mesas_atendidas'],
                        "rotacion_mesas": edarsahub_kpis['rotacion_mesas'],
                        "venta_por_hora": edarsahub_kpis['venta_por_hora']
                    },
                    "comparativo": {
                        "vs_periodo_anterior": edarsahub_kpis['vs_periodo_anterior'],
                        "vs_ano_anterior": edarsahub_kpis['vs_ano_anterior'],
                        "vs_presupuesto": edarsahub_kpis['vs_presupuesto'],
                        "tipo_comparacion": tipo_comparacion,
                        "ventas_anterior": edarsahub_kpis['ventas_anterior'],
                        "ventas_ano_anterior": edarsahub_kpis['ventas_ano_anterior']
                    },
                    "alertas": []
                }
            
            # Si EDARSAHUB no tiene datos, verificar estado del servidor y luego intentar conexión remota
            logging.info(f"[DASHBOARD-FIX] {server['name']}: EDARSAHUB sin datos, verificando servidor remoto")
            
            # ============================================================================
            # VERIFICACIÓN DE ESTADO: Usar la misma fuente que el menú de Servidores
            # ============================================================================
            # Consultar el estado guardado por el endpoint /servers/{id}/ping
            server_status_doc = await get_server_connection_status(server['id'])
            
            # Si el servidor está marcado como offline, usar caché directamente
            # NO hacer consulta propia - confiar en el estado del menú de Servidores
            if server_status_doc and not server_status_doc.get('is_online'):
                logging.warning(f"Dashboard {server['name']}: Servidor marcado offline por menú Servidores - buscando caché")
                
                periodo_key = f"dashboard_{f_ini}_{f_fin}"
                cached = await get_dashboard_cache(server['id'], periodo_key)
                
                if cached and cached.get('data'):
                    cached_data = cached['data']
                    cached_data['source_status'] = "FALLBACK"
                    cached_data['source_message'] = f"Servidor offline. Mostrando última información conocida ({cached.get('updated_at', 'N/A')})"
                    cached_data['alertas'] = [{"tipo": "warning", "mensaje": f"Servidor offline - Datos de caché: {cached.get('updated_at', 'N/A')}"}]
                    return cached_data
                
                return {
                    "source_status": "SOURCE_UNREACHABLE",
                    "source_message": f"Servidor {server['name']} está offline. Verifique el estado en el menú Servidores.",
                    "server_name": server['name'],
                    "server_type": server['system_type'],
                    "fecha_inicio": fecha_ini,
                    "fecha_fin": fecha_fin,
                    "kpis": None,
                    "comparativo": None,
                    "alertas": [{"tipo": "error", "mensaje": "Servidor offline. Verifique el estado en el menú Servidores."}]
                }
            
            # Si el servidor está online o no hay registro de estado, intentar consulta al servidor remoto
            
            # ============================================================================
            # BLOQUE 5.1: MIGRACIÓN A QUERIES CENTRALIZADAS (SoftRestaurant)
            # ============================================================================
            # ORIGEN: SQL directo líneas 2877-2961 (ahora usa queries/softrestaurant.py)
            # FECHA MIGRACIÓN: 2026-04-23
            # MÉTRICAS: ventas, pax, cheques del período actual, mes anterior y año anterior
            # MANTIENE: tempcheques (query específica), cálculos derivados
            # ============================================================================
            
            # Verificar si la tabla tempcheques tiene columna 'propina'
            has_propina_temp = check_column_exists(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], 'tempcheques', 'propina'
            )
            propina_expr_temp = get_propina_safe_column_tempcheques(has_propina_temp)
            
            # --- PERÍODO ACTUAL ---
            result_actual = query_ventas_periodo_sr(server, fecha_ini, fecha_fin)
            
            if result_actual.success:
                cheques_total = result_actual.cheques
                ventas_periodo = result_actual.total_venta
                pax_total = result_actual.pax
                # Calcular promedios localmente (no están en query centralizada)
                ticket_promedio = ventas_periodo / cheques_total if cheques_total > 0 else 0
                pax_promedio = pax_total / cheques_total if cheques_total > 0 else 0
            else:
                cheques_total = 0
                ventas_periodo = 0
                ticket_promedio = 0
                pax_total = 0
                pax_promedio = 0
            
            mesas_atendidas = cheques_total
            rotacion_mesas = round(cheques_total / mesas_atendidas, 2) if mesas_atendidas > 0 else 0
            
            # --- MES ANTERIOR ---
            result_anterior = query_ventas_periodo_sr(server, fecha_ini_ant, fecha_fin_ant)
            
            if result_anterior.success:
                ventas_anterior = result_anterior.total_venta
                pax_anterior = result_anterior.pax
            else:
                ventas_anterior = 0
                pax_anterior = 0
            
            vs_periodo_anterior = round(((ventas_periodo - ventas_anterior) / ventas_anterior * 100), 1) if ventas_anterior > 0 else 0
            
            # Cálculo de pax vs mes anterior (lógica original preservada)
            ventas_pax_ant = ventas_anterior
            pax_promedio_anterior = ventas_pax_ant / pax_anterior if pax_anterior > 0 else 0
            pax_promedio_actual = ventas_periodo / pax_total if pax_total > 0 else 0
            vs_pax_mes_anterior = round(((pax_promedio_actual - pax_promedio_anterior) / pax_promedio_anterior * 100), 1) if pax_promedio_anterior > 0 else 0
            
            # --- AÑO ANTERIOR ---
            result_ano_ant = query_ventas_periodo_sr(server, fecha_ini_ano_ant, fecha_fin_ano_ant)
            
            if result_ano_ant.success:
                ventas_ano_anterior = result_ano_ant.total_venta
                pax_ano_anterior = result_ano_ant.pax
                cheques_ano_anterior = result_ano_ant.cheques
            else:
                ventas_ano_anterior = 0
                pax_ano_anterior = 0
                cheques_ano_anterior = 0
            
            vs_ano_anterior = round(((ventas_periodo - ventas_ano_anterior) / ventas_ano_anterior * 100), 1) if ventas_ano_anterior > 0 else 0
            pax_vs_ano_anterior = round(((pax_total - pax_ano_anterior) / pax_ano_anterior * 100), 1) if pax_ano_anterior > 0 else 0
            
            pax_total_vs_ano = round(((pax_total - pax_ano_anterior) / pax_ano_anterior * 100), 1) if pax_ano_anterior > 0 else 0
            cheques_total_vs_ano = round(((cheques_total - cheques_ano_anterior) / cheques_ano_anterior * 100), 1) if cheques_ano_anterior > 0 else 0
            ticket_ano_anterior = ventas_ano_anterior / cheques_ano_anterior if cheques_ano_anterior > 0 else 0
            cheque_vs_ano_anterior = round(((ticket_promedio - ticket_ano_anterior) / ticket_ano_anterior * 100), 1) if ticket_ano_anterior > 0 else 0
            rotacion_ano_anterior = pax_ano_anterior / cheques_ano_anterior if cheques_ano_anterior > 0 else 0
            rotacion_vs_ano = round(((rotacion_mesas - rotacion_ano_anterior) / rotacion_ano_anterior * 100), 1) if rotacion_ano_anterior > 0 else 0
            
            # ============= HOMOLOGACIÓN: SUMAR TEMPCHEQUES (igual que Tablero Ejecutivo) =============
            # NOTA: Esta query se mantiene sin migrar - es específica del dashboard
            # NOTA: Se excluyen propinas de las ventas SI existe la columna
            try:
                query_temp = f"""
SELECT 
    COUNT(DISTINCT folio) as cheques,
    ISNULL(SUM(total{propina_expr_temp}), 0) as ventas,
    ISNULL(SUM(nopersonas), 0) as pax
FROM tempcheques
WHERE cancelado = 0
"""
                result_temp = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_temp
                )
                if result_temp and len(result_temp) > 0:
                    ventas_temp = float(result_temp[0]['ventas'] or 0)
                    pax_temp = int(result_temp[0]['pax'] or 0)
                    cheques_temp = int(result_temp[0]['cheques'] or 0)
                    ventas_periodo += ventas_temp
                    pax_total += pax_temp
                    cheques_total += cheques_temp
                    logging.info(f"Dashboard Comercial SoftRestaurant {server['name']} - Tempcheques sumados: ventas=${ventas_temp:,.2f}, pax={pax_temp}, cheques={cheques_temp}")
            except Exception as e:
                logging.warning(f"Dashboard Comercial SoftRestaurant {server['name']} - Error consultando tempcheques: {e}")
            # ============= FIN HOMOLOGACIÓN TEMPCHEQUES =============
            
            ticket_promedio = ventas_periodo / cheques_total if cheques_total > 0 else 0
            mesas_atendidas = cheques_total
            rotacion_mesas = round(cheques_total / mesas_atendidas, 2) if mesas_atendidas > 0 else 0
            
            kpis = {
                "ventas_periodo": ventas_periodo,
                "ticket_promedio": round(ticket_promedio, 2),
                "cheques_total": cheques_total,
                "pax_total": pax_total,
                "pax_promedio": round(pax_promedio, 1),
                "consumo_persona": round(ventas_periodo / pax_total, 2) if pax_total > 0 else 0,
                "mesas_atendidas": mesas_atendidas,
                "rotacion_mesas": rotacion_mesas,
                "venta_por_hora": round(ventas_periodo / 12, 2) if ventas_periodo > 0 else 0
            }
            
            comparativo = {
                "vs_periodo_anterior": vs_periodo_anterior,
                "vs_ano_anterior": vs_ano_anterior,
                "vs_presupuesto": 0,
                "pax_vs_mes_anterior": vs_pax_mes_anterior,
                "pax_vs_ano_anterior": pax_vs_ano_anterior,
                "pax_total_vs_ano": pax_total_vs_ano,
                "cheques_total_vs_ano": cheques_total_vs_ano,
                "cheque_vs_ano_anterior": cheque_vs_ano_anterior,
                "rotacion_vs_ano": rotacion_vs_ano,
                "tipo_comparacion": tipo_comparacion,
                "periodo_anterior": f"{fecha_ini_ant} a {fecha_fin_ant}",
                "periodo_ano_ant": f"{fecha_ini_ano_ant} a {fecha_fin_ano_ant}",
                # Banderas para indicar si hay datos históricos (para tooltips en UI)
                "sin_datos_periodo_anterior": ventas_anterior == 0,
                "sin_datos_ano_anterior": ventas_ano_anterior == 0
            }
            
            # Determinar estado de fuente
            if ventas_periodo > 0 or cheques_total > 0:
                source_status = "SUCCESS"
                source_message = f"Datos obtenidos correctamente de {server['name']}"
            else:
                source_status = "NO_DATA"
                source_message = f"Conexión exitosa a {server['name']} pero no hay datos en el período seleccionado ({fecha_ini} a {fecha_fin})"
            
            result_data = {
                "source_status": source_status,
                "source_message": source_message,
                "server_name": server['name'],
                "server_type": server['system_type'],
                "fecha_inicio": fecha_ini,
                "fecha_fin": fecha_fin,
                "kpis": kpis,
                "comparativo": comparativo,
                "alertas": []
            }
            
            # Guardar en caché para fallback futuro
            if source_status == "SUCCESS":
                periodo_key = f"dashboard_{f_ini}_{f_fin}"
                await save_dashboard_cache(server['id'], periodo_key, result_data)
            
            return result_data
        
        # FASE 3A.2: Migrado a helper centralizado
        elif is_mpro_system(server.get('system_type')):
            # ============================================================================
            # FASE 7-FIX: EDARSAHUB COMO FUENTE PRINCIPAL PARA MPRO
            # ============================================================================
            # MISMO FIX que SoftRestaurant: Usar EDARSAHUB primero.
            # MÁXIMA: EDARSAHUB SQL es el cerebro del sistema.
            # ============================================================================
            
            from .service import get_dashboard_kpis_from_edarsahub
            
            # Intentar obtener datos de EDARSAHUB primero
            edarsahub_kpis_mpro = get_dashboard_kpis_from_edarsahub(
                server_id=server_id,
                fecha_ini=fecha_ini,
                fecha_fin=fecha_fin,
                fecha_ini_ant=fecha_ini_ant if fecha_ini_ant != "PENDIENTE" else None,
                fecha_fin_ant=fecha_fin_ant if fecha_fin_ant != "PENDIENTE" else None,
                fecha_ini_ano_ant=fecha_ini_ano_ant if fecha_ini_ano_ant != "PENDIENTE" else None,
                fecha_fin_ano_ant=fecha_fin_ano_ant if fecha_fin_ano_ant != "PENDIENTE" else None,
                sucursal_id=sucursal if sucursal else 'DEFAULT'
            )
            
            if edarsahub_kpis_mpro:
                # EDARSAHUB tiene datos MPRO - usar estos como fuente principal
                logging.info(f"[DASHBOARD-FIX-MPRO] {server['name']}: Usando datos de EDARSAHUB (ventas=${edarsahub_kpis_mpro['ventas_periodo']:,.2f})")
                
                return {
                    "source_status": "SUCCESS",
                    "source_message": f"Datos consolidados de EDARSAHUB ({edarsahub_kpis_mpro['registros_consultados']} días)",
                    "source_type": edarsahub_kpis_mpro['source'],
                    "server_name": server.get('name', 'Desconocido'),
                    "server_type": server.get('system_type', 'Desconocido'),
                    "fecha_inicio": fecha_ini,
                    "fecha_fin": fecha_fin,
                    "kpis": {
                        "ventas_periodo": edarsahub_kpis_mpro['ventas_periodo'],
                        "ticket_promedio": edarsahub_kpis_mpro['ticket_promedio'],
                        "cheques_total": edarsahub_kpis_mpro['cheques_total'],
                        "pax_total": edarsahub_kpis_mpro['pax_total'],
                        "pax_promedio": edarsahub_kpis_mpro['pax_promedio'],
                        "consumo_persona": edarsahub_kpis_mpro['consumo_persona'],
                        "mesas_atendidas": edarsahub_kpis_mpro['mesas_atendidas'],
                        "rotacion_mesas": edarsahub_kpis_mpro['rotacion_mesas'],
                        "venta_por_hora": edarsahub_kpis_mpro['venta_por_hora']
                    },
                    "comparativo": {
                        "vs_periodo_anterior": edarsahub_kpis_mpro['vs_periodo_anterior'],
                        "vs_ano_anterior": edarsahub_kpis_mpro['vs_ano_anterior'],
                        "vs_presupuesto": edarsahub_kpis_mpro['vs_presupuesto'],
                        "tipo_comparacion": tipo_comparacion,
                        "ventas_anterior": edarsahub_kpis_mpro['ventas_anterior'],
                        "ventas_ano_anterior": edarsahub_kpis_mpro['ventas_ano_anterior']
                    },
                    "alertas": []
                }
            
            # Si EDARSAHUB no tiene datos, verificar estado del servidor e intentar conexión MPRO
            logging.info(f"[DASHBOARD-FIX-MPRO] {server['name']}: EDARSAHUB sin datos, verificando servidor remoto")
            
            # ============================================================================
            # VERIFICACIÓN DE ESTADO MPRO: Usar la misma fuente que el menú de Servidores
            # ============================================================================
            server_status_doc_mpro = await get_server_connection_status(server['id'])
            
            # Si el servidor está marcado como offline, usar caché directamente
            if server_status_doc_mpro and not server_status_doc_mpro.get('is_online'):
                logging.warning(f"Dashboard MPRO {server['name']}: Servidor marcado offline por menú Servidores - buscando caché")
                
                periodo_key = f"dashboard_mpro_{fecha_ini}_{fecha_fin}"
                cached = await get_dashboard_cache(server['id'], periodo_key)
                
                if cached and cached.get('data'):
                    cached_data = cached['data']
                    cached_data['source_status'] = "FALLBACK"
                    cached_data['source_message'] = f"Servidor offline. Mostrando última información conocida ({cached.get('updated_at', 'N/A')})"
                    cached_data['alertas'] = [{"tipo": "warning", "mensaje": f"Servidor offline - Datos de caché: {cached.get('updated_at', 'N/A')}"}]
                    return cached_data
                
                return {
                    "source_status": "SOURCE_UNREACHABLE",
                    "source_message": f"Servidor {server['name']} está offline. Verifique el estado en el menú Servidores.",
                    "server_name": server['name'],
                    "server_type": server['system_type'],
                    "fecha_inicio": fecha_ini,
                    "fecha_fin": fecha_fin,
                    "kpis": None,
                    "comparativo": None,
                    "alertas": [{"tipo": "error", "mensaje": "Servidor offline. Verifique el estado en el menú Servidores."}]
                }
            
            # MPRO usa formato YYYY-MM-DD directamente
            # Ajustar períodos de comparación si es días equivalentes
            if tipo_comparacion == "dias_equiv":
                # BLINDAJE: Detectar si es código o nombre de sucursal
                if sucursal:
                    es_codigo = sucursal.isdigit() or (len(sucursal) == 4 and sucursal[0] == '0')
                    if es_codigo:
                        sucursal_filter_check = f" AND VE.Sc_Cve_Sucursal = '{sucursal}'"
                    else:
                        sucursal_filter_check = f" AND VE.Sc_Cve_Sucursal IN (SELECT Sc_Cve_Sucursal FROM Sucursal WHERE Sc_Descripcion LIKE '%{sucursal}%')"
                else:
                    sucursal_filter_check = ""
                
                # BLINDAJE: Usar formato de fecha explícito para evitar problemas de configuración regional
                query_ultimo_dia_mpro = f"""
SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
FROM Venta_Encabezado VE
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{fecha_ini} 00:00:00', 120)
  AND VE.Vn_Fecha <= CONVERT(datetime, '{fecha_fin} 23:59:59', 120)
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter_check}
"""
                result_ultimo = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_ultimo_dia_mpro
                )
                
                if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
                    ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
                    if isinstance(ultimo_dia_venta, str):
                        dia_con_datos = int(ultimo_dia_venta.split('-')[2]) if '-' in ultimo_dia_venta else int(ultimo_dia_venta[-2:])
                    else:
                        dia_con_datos = ultimo_dia_venta.day
                    
                    logging.info(f"MPRO - Último día con ventas: {ultimo_dia_venta} (día {dia_con_datos})")
                    
                    fecha_fin = f"{year}-{str(mes_max).zfill(2)}-{str(dia_con_datos).zfill(2)}"
                    
                    mes_actual = mes_max
                    anio_actual = year
                    if mes_actual == 1:
                        mes_ant = 12
                        anio_ant = anio_actual - 1
                    else:
                        mes_ant = mes_actual - 1
                        anio_ant = anio_actual
                    
                    if mes_ant == 12:
                        max_dia_mes_ant = 31
                    elif mes_ant in [4, 6, 9, 11]:
                        max_dia_mes_ant = 30
                    elif mes_ant == 2:
                        max_dia_mes_ant = 29 if (anio_ant % 4 == 0 and (anio_ant % 100 != 0 or anio_ant % 400 == 0)) else 28
                    else:
                        max_dia_mes_ant = 31
                    
                    dia_comparar = min(dia_con_datos, max_dia_mes_ant)
                    fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
                    fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
                    
                    anio_pasado = year - 1
                    fecha_ini_ano_ant = f"{anio_pasado}-{str(mes_min).zfill(2)}-01"
                    
                    if mes_max == 2:
                        max_dia_ano_ant = 29 if (anio_pasado % 4 == 0 and (anio_pasado % 100 != 0 or anio_pasado % 400 == 0)) else 28
                    elif mes_max in [4, 6, 9, 11]:
                        max_dia_ano_ant = 30
                    else:
                        max_dia_ano_ant = 31
                    
                    dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
                    fecha_fin_ano_ant = f"{anio_pasado}-{str(mes_max).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
                    
                    logging.info(f"MPRO Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_ano_ant} a {fecha_fin_ano_ant} (multiselección: {mes_min}-{mes_max})")
            
            sucursal_join = ""
            sucursal_filter = ""
            nombre_servidor = server.get('name', '').lower()
            sucursal_lower = (sucursal or '').lower()
            skip_sucursal_filter = (
                not sucursal or 
                sucursal == 'all' or 
                sucursal_lower == 'default' or 
                sucursal_lower == nombre_servidor
            )
            
            if not skip_sucursal_filter:
                if sucursal.isdigit() or (len(sucursal) == 4 and sucursal[0] == '0'):
                    sucursal_join = ""
                    sucursal_filter = f" AND VE.Sc_Cve_Sucursal = '{sucursal}'"
                else:
                    sucursal_join = "INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal"
                    sucursal_filter = f" AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            query_ultimo_dia_suc = f"""
SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
FROM Venta_Encabezado VE
{sucursal_join}
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{fecha_ini} 00:00:00', 120)
  AND VE.Vn_Fecha <= CONVERT(datetime, '{fecha_fin} 23:59:59', 120)
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter}
"""
            try:
                result_ultimo_suc = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_ultimo_dia_suc
                )
                if result_ultimo_suc and result_ultimo_suc[0]['ultimo_dia_venta']:
                    ultimo_dia_suc = result_ultimo_suc[0]['ultimo_dia_venta']
                    if isinstance(ultimo_dia_suc, str):
                        dia_con_datos = int(ultimo_dia_suc.split('-')[2]) if '-' in ultimo_dia_suc else int(ultimo_dia_suc[-2:])
                    else:
                        dia_con_datos = ultimo_dia_suc.day
                    
                    print(f"*** MPRO Dashboard {sucursal} - Ultimo dia con ventas: dia {dia_con_datos} ***")
                    
                    fecha_fin = f"{year}-{str(mes_max).zfill(2)}-{str(dia_con_datos).zfill(2)}"
                    
                    mes_actual = mes_max
                    anio_actual = year
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
                    
                    anio_pasado = year - 1
                    max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_max)[1]
                    dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
                    fecha_ini_ano_ant = f"{anio_pasado}-{str(mes_min).zfill(2)}-01"
                    fecha_fin_ano_ant = f"{anio_pasado}-{str(mes_max).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
                    
                    print(f"*** Fechas ajustadas: Actual hasta {fecha_fin}, MesAnt {fecha_ini_ant} a {fecha_fin_ant}, AnoAnt {fecha_ini_ano_ant} a {fecha_fin_ano_ant} ***")
            except Exception as e:
                print(f"Error detectando ultimo dia para sucursal {sucursal}: {e}")
            
            # =====================================================================
            # SUB-BLOQUE 5.2: Query centralizada para métricas del período actual
            # REEMPLAZA: query_kpis SQL directo (líneas 3205-3221 original)
            # NOTA: Las variables fi_mpro, ff_mpro, etc. fueron eliminadas porque
            #       la función centralizada hace la conversión de fechas internamente.
            # =====================================================================
            print(f"*** MPRO Dashboard: Llamando query_ventas_periodo_mpro_con_filtro_flexible sucursal={sucursal}, fi={fecha_ini}, ff={fecha_fin} ***")
            result_kpis = query_ventas_periodo_mpro_con_filtro_flexible(
                server=server,
                fecha_ini=fecha_ini,
                fecha_fin=fecha_fin,
                sucursal=sucursal,
                excluir_cancelados=False  # La query original no excluía cancelados en query_kpis
            )
            
            print(f"*** MPRO Dashboard: result_kpis.success={result_kpis.success}, ventas={result_kpis.total_venta}, pax={result_kpis.pax}, cheques={result_kpis.cheques} ***")
            
            if result_kpis.success:
                cheques = result_kpis.cheques
                ventas = result_kpis.total_venta
                pax = result_kpis.pax
                
                # NOTA: El fallback PAX ya está aplicado dentro de la función centralizada
                # pero se mantiene el log por consistencia
                if pax == cheques and pax > 0:
                    logging.debug(f"Dashboard Comercial MPRO: PAX = cheques ({pax}) posible fallback aplicado por función centralizada")
                
                # ============= INTEGRACIÓN API LOCAL HOMOLOGADA =============
                sucursal_para_api = sucursal if sucursal else server.get('name', '')
                
                if periodo == "dia":
                    print(f"*** Dashboard Comercial MPRO HOY: Buscando API local para '{sucursal_para_api}' ***")
                    ventas_api_local = sumar_ventas_api_local_a_sucursal(
                        server_host=server['host'],
                        sucursal_nombre=sucursal_para_api,
                        fecha_fin=fecha_fin,
                        mes_solicitado=hoy.month,
                        anio_solicitado=hoy.year,
                        solo_ventas_dia=True
                    )
                    
                    if ventas_api_local.get("aplicado", False):
                        ventas = ventas_api_local["ventas"]
                        cheques = ventas_api_local["cheques"]
                        pax = ventas_api_local["pax"]
                        print(f"*** Dashboard Comercial MPRO HOY: API Local REEMPLAZÓ - ${ventas:,.2f}, {cheques} cheques, {pax} pax ***")
                    elif ventas_api_local.get("reemplazar", False) and not ventas_api_local.get("aplicado", False):
                        # BLINDAJE (Abril 2026): Si la API local falló (aplicado=False), NO reemplazar
                        # los datos SQL válidos con $0.00 - mantener las ventas de la nube
                        print(f"*** Dashboard Comercial MPRO HOY: API Local FALLÓ - MANTENIENDO datos SQL: ${ventas:,.2f}, {cheques} cheques, {pax} pax ***")
                else:
                    print(f"*** Dashboard Comercial MPRO MES: Buscando API local para '{sucursal_para_api}' ***")
                    ventas_api_local = sumar_ventas_api_local_a_sucursal(
                        server_host=server['host'],
                        sucursal_nombre=sucursal_para_api,
                        fecha_fin=fecha_fin,
                        mes_solicitado=hoy.month,
                        anio_solicitado=hoy.year,
                        solo_ventas_dia=False
                    )
                    
                    if ventas_api_local.get("aplicado", False):
                        ventas += ventas_api_local["ventas"]
                        cheques += ventas_api_local["cheques"]
                        pax += ventas_api_local["pax"]
                        print(f"*** Dashboard Comercial MPRO MES: API Local SUMÓ +${ventas_api_local['ventas']:,.2f}, +{ventas_api_local['cheques']} cheques, +{ventas_api_local['pax']} pax ***")
                # ============= FIN INTEGRACIÓN API LOCAL =============
                
                ticket_promedio = ventas / cheques if cheques > 0 else 0
                consumo_persona = ventas / pax if pax > 0 else 0
                pax_promedio = pax / cheques if cheques > 0 else 0
                
                # =====================================================================
                # SUB-BLOQUE 5.2: Query centralizada para métricas del MES ANTERIOR
                # REEMPLAZA: query_pax_ant_mpro SQL directo (líneas 3277-3292 original)
                # =====================================================================
                result_mes_ant = query_ventas_periodo_mpro_con_filtro_flexible(
                    server=server,
                    fecha_ini=fecha_ini_ant,
                    fecha_fin=fecha_fin_ant,
                    sucursal=sucursal,
                    excluir_cancelados=True  # La query original SÍ excluía cancelados
                )
                
                pax_ant = result_mes_ant.pax if result_mes_ant.success else 0
                ventas_ant = result_mes_ant.total_venta if result_mes_ant.success else 0
                pax_promedio_anterior = ventas_ant / pax_ant if pax_ant > 0 else 0
                pax_promedio_actual = ventas / pax if pax > 0 else 0
                vs_pax_mes_anterior = round(((pax_promedio_actual - pax_promedio_anterior) / pax_promedio_anterior * 100), 1) if pax_promedio_anterior > 0 else 0
                vs_periodo_anterior = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
                
                # =====================================================================
                # SUB-BLOQUE 5.2: Query centralizada para métricas del AÑO ANTERIOR
                # REEMPLAZA: query_ano_ant_mpro SQL directo (líneas 3301-3317 original)
                # =====================================================================
                result_ano_ant = query_ventas_periodo_mpro_con_filtro_flexible(
                    server=server,
                    fecha_ini=fecha_ini_ano_ant,
                    fecha_fin=fecha_fin_ano_ant,
                    sucursal=sucursal,
                    excluir_cancelados=True  # La query original SÍ excluía cancelados
                )
                
                pax_ano_ant = result_ano_ant.pax if result_ano_ant.success else 0
                ventas_ano_ant = result_ano_ant.total_venta if result_ano_ant.success else 0
                cheques_ano_ant = result_ano_ant.cheques if result_ano_ant.success else 0
                vs_ano_anterior = round(((ventas - ventas_ano_ant) / ventas_ano_ant * 100), 1) if ventas_ano_ant > 0 else 0
                pax_vs_ano_anterior = round(((pax - pax_ano_ant) / pax_ano_ant * 100), 1) if pax_ano_ant > 0 else 0
                
                pax_total_vs_ano = round(((pax - pax_ano_ant) / pax_ano_ant * 100), 1) if pax_ano_ant > 0 else 0
                cheques_total_vs_ano = round(((cheques - cheques_ano_ant) / cheques_ano_ant * 100), 1) if cheques_ano_ant > 0 else 0
                ticket_ano_ant = ventas_ano_ant / cheques_ano_ant if cheques_ano_ant > 0 else 0
                cheque_vs_ano_anterior = round(((ticket_promedio - ticket_ano_ant) / ticket_ano_ant * 100), 1) if ticket_ano_ant > 0 else 0
                
                kpis = {
                    "ventas_periodo": round(ventas, 2),
                    "ticket_promedio": round(ticket_promedio, 2),
                    "cheques_total": cheques,
                    "pax_total": pax,
                    "pax_promedio": round(pax_promedio, 2),
                    "consumo_persona": round(consumo_persona, 2),
                    "rotacion_mesas": 0,
                    "mesas_atendidas": 0
                }
                
                comparativo = {
                    "vs_periodo_anterior": vs_periodo_anterior,
                    "vs_ano_anterior": vs_ano_anterior,
                    "vs_presupuesto": 0,
                    "pax_vs_mes_anterior": vs_pax_mes_anterior,
                    "pax_vs_ano_anterior": pax_vs_ano_anterior,
                    "pax_total_vs_ano": pax_total_vs_ano,
                    "cheques_total_vs_ano": cheques_total_vs_ano,
                    "cheque_vs_ano_anterior": cheque_vs_ano_anterior,
                    "rotacion_vs_ano": 0,
                    "tipo_comparacion": tipo_comparacion,
                    "periodo_anterior": f"{fecha_ini_ant} a {fecha_fin_ant}",
                    "periodo_ano_ant": f"{fecha_ini_ano_ant} a {fecha_fin_ano_ant}",
                    # Banderas para indicar si hay datos históricos (para tooltips en UI)
                    "sin_datos_periodo_anterior": ventas_ant == 0,
                    "sin_datos_ano_anterior": ventas_ano_ant == 0
                }
                
                # Determinar estado de fuente MPRO
                if ventas > 0 or cheques > 0:
                    source_status = "SUCCESS"
                    source_message = f"Datos obtenidos correctamente de {server['name']}"
                    
                    result_data_mpro = {
                        "source_status": source_status,
                        "source_message": source_message,
                        "server_name": server['name'],
                        "server_type": server['system_type'],
                        "fecha_inicio": fecha_ini,
                        "fecha_fin": fecha_fin,
                        "kpis": kpis,
                        "comparativo": comparativo,
                        "alertas": []
                    }
                    
                    # Guardar en caché para fallback futuro
                    periodo_key = f"dashboard_mpro_{fecha_ini}_{fecha_fin}"
                    await save_dashboard_cache(server['id'], periodo_key, result_data_mpro)
                    
                    return result_data_mpro
                else:
                    # =====================================================================
                    # FASE DASHBOARD-COMERCIAL-FALLBACK-MPRO-02 (Diciembre 2025)
                    # MPRO: result_kpis.success == True PERO ventas == 0
                    # 
                    # Esto puede ocurrir cuando:
                    # 1. La query SQL retorna vacío (sin datos en el período)
                    # 2. La query falla silenciosamente (retorna None que se convierte en 0)
                    # 3. CONFIG-SECURITY-01 causa que la conexión no funcione correctamente
                    #
                    # ACCIÓN: Intentar fallback a caché antes de devolver NO_DATA
                    # =====================================================================
                    logging.warning(
                        f"[DASHBOARD-COMERCIAL-FALLBACK-MPRO] SQL retornó ventas=0 para {server['name']}. "
                        f"Verificando caché antes de devolver NO_DATA..."
                    )
                    
                    # --- PASO 1: Buscar en caché de dashboard específico ---
                    periodo_key_dashboard = f"dashboard_mpro_{fecha_ini}_{fecha_fin}"
                    cached_dashboard = await get_dashboard_cache(server['id'], periodo_key_dashboard)
                    
                    if cached_dashboard and cached_dashboard.get('data'):
                        cached_data = cached_dashboard['data']
                        cached_kpis = cached_data.get('kpis', {})
                        # Solo usar caché si tiene datos reales
                        if cached_kpis.get('ventas_periodo', 0) > 0:
                            cached_data['source_status'] = "CACHE"
                            cached_data['source_message'] = (
                                f"SQL retornó vacío para {server['name']}. "
                                f"Usando caché de dashboard (última actualización: {cached_dashboard.get('updated_at', 'N/A')})"
                            )
                            cached_data['cache_used'] = True
                            cached_data['fallback_reason'] = "SQL retornó ventas=0"
                            cached_data['alertas'] = [{
                                "tipo": "info", 
                                "mensaje": f"Datos de caché - SQL retornó vacío ({cached_dashboard.get('updated_at', 'N/A')})"
                            }]
                            logging.info(
                                f"[DASHBOARD-COMERCIAL-FALLBACK-MPRO] Usando caché de dashboard para {server['name']} "
                                f"(ventas: ${cached_kpis.get('ventas_periodo', 0):,.2f})"
                            )
                            return cached_data
                    
                    # --- PASO 2: Buscar en caché de KPIs del Tablero Ejecutivo ---
                    periodo_key_tablero = f"{year}-{mes_max:02d}"
                    cached_kpis_list = await get_cached_kpis_by_prefix(server['id'], periodo_key_tablero)
                    
                    if cached_kpis_list and len(cached_kpis_list) > 0:
                        # Buscar por sucursal si se especificó
                        sucursal_lower = (sucursal or '').lower()
                        cached_kpis_match = None
                        
                        # Estrategia de matching mejorada:
                        # 1. Buscar match exacto primero
                        # 2. Buscar match parcial (substring)
                        # 3. Si hay múltiples matches, preferir el que tenga más ventas
                        matches_found = []
                        
                        for cached_item in cached_kpis_list:
                            kpis_data = cached_item.get('kpis', {})
                            unidad_nombre = (kpis_data.get('unidad', '') or '').lower()
                            sucursal_nombre = (kpis_data.get('sucursal', '') or '').lower()
                            ventas_item = kpis_data.get('ventas', 0)
                            
                            if sucursal_lower:
                                # Match exacto (prioridad máxima)
                                if unidad_nombre == sucursal_lower or sucursal_nombre == sucursal_lower:
                                    matches_found.append((cached_item, ventas_item, 'exact'))
                                # Match parcial (prioridad media)
                                elif (sucursal_lower in unidad_nombre or 
                                      sucursal_lower in sucursal_nombre or
                                      unidad_nombre in sucursal_lower or
                                      sucursal_nombre in sucursal_lower):
                                    matches_found.append((cached_item, ventas_item, 'partial'))
                        
                        # Seleccionar el mejor match
                        if matches_found:
                            # Priorizar matches exactos
                            exact_matches = [m for m in matches_found if m[2] == 'exact']
                            if exact_matches:
                                # Si hay múltiples exactos, elegir el de mayor ventas
                                cached_kpis_match = max(exact_matches, key=lambda x: x[1])[0]
                            else:
                                # Si solo hay parciales, elegir el de mayor ventas
                                cached_kpis_match = max(matches_found, key=lambda x: x[1])[0]
                        
                        # Si no hubo match y no se especificó sucursal, usar el de mayor ventas
                        if not cached_kpis_match and not sucursal_lower:
                            cached_kpis_match = max(cached_kpis_list, key=lambda x: x.get('kpis', {}).get('ventas', 0))
                        elif not cached_kpis_match:
                            # Último recurso: usar el primero disponible
                            cached_kpis_match = cached_kpis_list[0]
                        
                        kpis_cached = cached_kpis_match.get('kpis', {})
                        cached_updated_at = cached_kpis_match.get('updated_at', 'N/A')
                        
                        # Solo usar si tiene datos reales
                        if kpis_cached.get('ventas', 0) > 0:
                            logging.info(
                                f"[DASHBOARD-COMERCIAL-FALLBACK-MPRO] Usando KPIs de Tablero Ejecutivo para {server['name']} "
                                f"(unidad: {kpis_cached.get('unidad', 'N/A')}, ventas: ${kpis_cached.get('ventas', 0):,.2f})"
                            )
                            
                            fallback_kpis = {
                                "ventas_periodo": kpis_cached.get('ventas', 0),
                                "ticket_promedio": kpis_cached.get('ticket_prom', 0),
                                "cheques_total": kpis_cached.get('cheques', 0),
                                "pax_total": kpis_cached.get('pax', 0),
                                "pax_promedio": round(kpis_cached.get('pax', 0) / kpis_cached.get('cheques', 1), 2) if kpis_cached.get('cheques', 0) > 0 else 0,
                                "consumo_persona": round(kpis_cached.get('ventas', 0) / kpis_cached.get('pax', 1), 2) if kpis_cached.get('pax', 0) > 0 else 0,
                                "rotacion_mesas": 0,
                                "mesas_atendidas": 0
                            }
                            
                            fallback_comparativo = {
                                "vs_periodo_anterior": kpis_cached.get('var_vs_mes_ant', 0),
                                "vs_ano_anterior": kpis_cached.get('var_vs_año_ant', 0),
                                "vs_presupuesto": 0,
                                "pax_vs_mes_anterior": kpis_cached.get('var_pax_mes', 0),
                                "pax_vs_ano_anterior": kpis_cached.get('var_pax_año', 0),
                                "pax_total_vs_ano": kpis_cached.get('var_pax_año', 0),
                                "cheques_total_vs_ano": kpis_cached.get('var_cheques_año', 0),
                                "cheque_vs_ano_anterior": 0,
                                "rotacion_vs_ano": 0,
                                "tipo_comparacion": tipo_comparacion,
                                "periodo_anterior": f"{fecha_ini_ant} a {fecha_fin_ant}",
                                "periodo_ano_ant": f"{fecha_ini_ano_ant} a {fecha_fin_ano_ant}",
                                "sin_datos_periodo_anterior": kpis_cached.get('ventas_ant', 0) == 0,
                                "sin_datos_ano_anterior": kpis_cached.get('ventas_año', 0) == 0
                            }
                            
                            return {
                                "source_status": "CACHE",
                                "source_message": (
                                    f"SQL retornó vacío para {server['name']}. "
                                    f"Usando datos de caché del Tablero Ejecutivo (última actualización: {cached_updated_at})"
                                ),
                                "server_name": server['name'],
                                "server_type": server['system_type'],
                                "fecha_inicio": fecha_ini,
                                "fecha_fin": fecha_fin,
                                "cache_used": True,
                                "fallback_reason": "SQL retornó ventas=0",
                                "fallback_source": "TABLERO_EJECUTIVO_CACHE",
                                "kpis": fallback_kpis,
                                "comparativo": fallback_comparativo,
                                "alertas": [{
                                    "tipo": "info", 
                                    "mensaje": f"Datos de caché (Tablero Ejecutivo) - SQL retornó vacío. Última actualización: {cached_updated_at}"
                                }]
                            }
                    
                    # --- PASO 3: Sin caché con datos válidos - devolver NO_DATA controlado ---
                    logging.warning(
                        f"[DASHBOARD-COMERCIAL-FALLBACK-MPRO] Sin caché válida para {server['name']}. "
                        f"Devolviendo NO_DATA."
                    )
                    
                    return {
                        "source_status": "NO_DATA",
                        "source_message": f"Conexión exitosa a {server['name']} pero no hay datos en el período seleccionado. Sin caché disponible.",
                        "server_name": server['name'],
                        "server_type": server['system_type'],
                        "fecha_inicio": fecha_ini,
                        "fecha_fin": fecha_fin,
                        "cache_used": False,
                        "fallback_attempted": True,
                        "kpis": kpis,
                        "comparativo": comparativo,
                        "alertas": [{"tipo": "warning", "mensaje": "No hay datos disponibles para este período. SQL retornó vacío y no hay caché válida."}]
                    }
            else:
                # =====================================================================
                # FASE DASHBOARD-COMERCIAL-FALLBACK-MPRO-01 (Diciembre 2025)
                # MPRO: result_kpis.success == False - IMPLEMENTAR FALLBACK A CACHÉ
                # 
                # CAUSA RAÍZ: CONFIG-SECURITY-01 - Sin SERVER_SECRET_KEY, el password
                # SQL no se puede descifrar y la query falla. Sin embargo, el Tablero
                # Ejecutivo YA tiene datos cacheados de MPRO sincronizados desde EDARSAHUB.
                #
                # FLUJO:
                # 1. SQL directo falla (error de auth, timeout, conectividad)
                # 2. Buscar en caché de dashboard (save_dashboard_cache/get_dashboard_cache)
                # 3. Si hay caché válida, retornar con source="CACHE" o "FALLBACK"
                # 4. Si no hay caché, buscar en kpis_cache (del Tablero Ejecutivo)
                # 5. Si no hay nada, retornar NO_DATA_NO_CACHE (no $0 falso)
                # =====================================================================
                error_msg = result_kpis.error if result_kpis.error else "Error desconocido en query centralizada"
                logging.warning(
                    f"[DASHBOARD-COMERCIAL-FALLBACK-MPRO] SQL falló para {server['name']}: {error_msg}. "
                    f"Intentando fallback a caché..."
                )
                
                # --- PASO 1: Buscar en caché de dashboard específico ---
                periodo_key_dashboard = f"dashboard_mpro_{fecha_ini}_{fecha_fin}"
                cached_dashboard = await get_dashboard_cache(server['id'], periodo_key_dashboard)
                
                if cached_dashboard and cached_dashboard.get('data'):
                    cached_data = cached_dashboard['data']
                    # Enriquecer con información de fallback
                    cached_data['source_status'] = "CACHE"
                    cached_data['source_message'] = (
                        f"SQL falló ({error_msg[:80]}). "
                        f"Mostrando datos de caché (última actualización: {cached_dashboard.get('updated_at', 'N/A')})"
                    )
                    cached_data['cache_used'] = True
                    cached_data['fallback_reason'] = error_msg[:100]
                    cached_data['alertas'] = [{
                        "tipo": "warning", 
                        "mensaje": f"Datos de caché - SQL no disponible ({cached_dashboard.get('updated_at', 'N/A')})"
                    }]
                    logging.info(
                        f"[DASHBOARD-COMERCIAL-FALLBACK-MPRO] Usando caché de dashboard para {server['name']} "
                        f"(actualizado: {cached_dashboard.get('updated_at')})"
                    )
                    return cached_data
                
                # --- PASO 2: Buscar en caché de KPIs del Tablero Ejecutivo ---
                # Construir periodo_key compatible con el formato del Tablero Ejecutivo
                # El Tablero usa formato: "YYYY-MM" para el periodo_key base
                periodo_key_tablero = f"{year}-{mes_max:02d}"
                
                # Para MPRO con sucursales, buscar por prefijo (puede haber múltiples)
                cached_kpis_list = await get_cached_kpis_by_prefix(server['id'], periodo_key_tablero)
                
                if cached_kpis_list and len(cached_kpis_list) > 0:
                    # Intentar encontrar la sucursal específica o usar la primera disponible
                    sucursal_lower = (sucursal or '').lower()
                    cached_kpis_match = None
                    
                    for cached_item in cached_kpis_list:
                        kpis_data = cached_item.get('kpis', {})
                        unidad_nombre = (kpis_data.get('unidad', '') or '').lower()
                        sucursal_nombre = (kpis_data.get('sucursal', '') or '').lower()
                        
                        # Matching por nombre de sucursal (si se especificó)
                        if sucursal_lower and (
                            sucursal_lower in unidad_nombre or 
                            sucursal_lower in sucursal_nombre or
                            unidad_nombre in sucursal_lower or
                            sucursal_nombre in sucursal_lower
                        ):
                            cached_kpis_match = cached_item
                            break
                    
                    # Si no hubo match exacto, usar el primero disponible
                    if not cached_kpis_match:
                        cached_kpis_match = cached_kpis_list[0]
                    
                    kpis_cached = cached_kpis_match.get('kpis', {})
                    cached_updated_at = cached_kpis_match.get('updated_at', 'N/A')
                    
                    logging.info(
                        f"[DASHBOARD-COMERCIAL-FALLBACK-MPRO] Usando KPIs de Tablero Ejecutivo para {server['name']} "
                        f"(unidad: {kpis_cached.get('unidad', 'N/A')}, actualizado: {cached_updated_at})"
                    )
                    
                    # Construir respuesta compatible con formato de dashboard
                    fallback_kpis = {
                        "ventas_periodo": kpis_cached.get('ventas', 0),
                        "ticket_promedio": kpis_cached.get('ticket_prom', 0),
                        "cheques_total": kpis_cached.get('cheques', 0),
                        "pax_total": kpis_cached.get('pax', 0),
                        "pax_promedio": round(kpis_cached.get('pax', 0) / kpis_cached.get('cheques', 1), 2) if kpis_cached.get('cheques', 0) > 0 else 0,
                        "consumo_persona": round(kpis_cached.get('ventas', 0) / kpis_cached.get('pax', 1), 2) if kpis_cached.get('pax', 0) > 0 else 0,
                        "rotacion_mesas": 0,
                        "mesas_atendidas": 0
                    }
                    
                    fallback_comparativo = {
                        "vs_periodo_anterior": kpis_cached.get('var_vs_mes_ant', 0),
                        "vs_ano_anterior": kpis_cached.get('var_vs_año_ant', 0),
                        "vs_presupuesto": 0,
                        "pax_vs_mes_anterior": kpis_cached.get('var_pax_mes', 0),
                        "pax_vs_ano_anterior": kpis_cached.get('var_pax_año', 0),
                        "pax_total_vs_ano": kpis_cached.get('var_pax_año', 0),
                        "cheques_total_vs_ano": kpis_cached.get('var_cheques_año', 0),
                        "cheque_vs_ano_anterior": 0,
                        "rotacion_vs_ano": 0,
                        "tipo_comparacion": tipo_comparacion,
                        "periodo_anterior": f"{fecha_ini_ant} a {fecha_fin_ant}",
                        "periodo_ano_ant": f"{fecha_ini_ano_ant} a {fecha_fin_ano_ant}",
                        "sin_datos_periodo_anterior": kpis_cached.get('ventas_ant', 0) == 0,
                        "sin_datos_ano_anterior": kpis_cached.get('ventas_año', 0) == 0
                    }
                    
                    return {
                        "source_status": "CACHE",
                        "source_message": (
                            f"SQL falló ({error_msg[:60]}...). "
                            f"Mostrando datos de caché del Tablero Ejecutivo (última actualización: {cached_updated_at})"
                        ),
                        "server_name": server['name'],
                        "server_type": server['system_type'],
                        "fecha_inicio": fecha_ini,
                        "fecha_fin": fecha_fin,
                        "cache_used": True,
                        "fallback_reason": error_msg[:100],
                        "fallback_source": "TABLERO_EJECUTIVO_CACHE",
                        "kpis": fallback_kpis,
                        "comparativo": fallback_comparativo,
                        "alertas": [{
                            "tipo": "warning", 
                            "mensaje": f"Datos de caché (Tablero Ejecutivo) - SQL no disponible. Última actualización: {cached_updated_at}"
                        }]
                    }
                
                # --- PASO 3: Sin caché disponible - NO_DATA controlado ---
                logging.warning(
                    f"[DASHBOARD-COMERCIAL-FALLBACK-MPRO] Sin caché disponible para {server['name']}. "
                    f"Error SQL original: {error_msg}"
                )
                
                return {
                    "source_status": "NO_DATA_NO_CACHE",
                    "source_message": (
                        f"SQL falló ({error_msg[:80]}) y no hay caché disponible. "
                        f"Posible causa: CONFIG-SECURITY-01 (SERVER_SECRET_KEY faltante)"
                    ),
                    "server_name": server['name'],
                    "server_type": server['system_type'],
                    "fecha_inicio": fecha_ini,
                    "fecha_fin": fecha_fin,
                    "cache_used": False,
                    "fallback_attempted": True,
                    "fallback_reason": error_msg[:100],
                    "kpis": None,
                    "comparativo": None,
                    "alertas": [{
                        "tipo": "error", 
                        "mensaje": f"Sin datos disponibles. Error SQL: {error_msg[:100]}. Sin caché."
                    }]
                }
        
        # Si llegamos aquí, el sistema no está soportado
        return {
            "source_status": "ERROR",
            "source_message": f"Tipo de sistema no soportado: {server.get('system_type', 'desconocido')}",
            "server_name": server.get('name', 'N/A'),
            "kpis": None,
            "comparativo": None,
            "alertas": []
        }
        
    except Exception as e:
        logging.error(f"Error en comercial dashboard: {e}")
        return {
            "source_status": "ERROR",
            "source_message": f"Error interno: {str(e)[:200]}",
            "server_name": server.get('name', 'N/A') if server else 'N/A',
            "kpis": None,
            "comparativo": None,
            "alertas": []
        }


__all__ = ['router']
