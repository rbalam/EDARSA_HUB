"""
Módulo de Ventana Operativa para cálculo de FechaOperacion.

Este módulo implementa la lógica de negocio para calcular la fecha operativa
de una unidad de negocio basándose en sus horarios de servicio configurados.

REGLA DE NEGOCIO:
- El día operativo de un restaurante NO cambia automáticamente a las 00:00
- La jornada operativa cierra a las 06:00 AM del día siguiente
- Si una venta ocurre entre 00:00 y 05:59, pertenece al día operativo ANTERIOR

VENTANA OPERATIVA DEFAULT: 13:00 - 06:00 (cruza medianoche)
- ACTUALIZACIÓN 16-May-2026: Corte operativo cambiado de 11:00/03:00 a 06:00
- PREPARACIÓN: Futuro módulo de Horarios de Operación permitirá configurar por unidad

Ejemplo con horario 13:00 - 06:00:
- 14:00 del día 15 → fecha_operacion = 15 (dentro de jornada del 15)
- 02:00 del día 16 → fecha_operacion = 15 (jornada del 15 no ha cerrado)
- 05:30 del día 16 → fecha_operacion = 15 (jornada del 15 no ha cerrado)
- 06:00 del día 16 → fecha_operacion = 16 (nueva jornada del 16 inicia)
- 13:00 del día 16 → fecha_operacion = 16 (jornada del 16)

Autor: Sistema EDARSAHUB
Fecha: 2026-05-16
"""

import logging
from datetime import date, datetime, time, timedelta
from typing import Optional, Tuple, Dict, Any
import pytz

from core.db import execute_sql_query

logger = logging.getLogger(__name__)

# Configuración de conexión EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'HRLectura',
    'password': 'National09$'
}

# Zona horaria operativa
MEXICO_TZ = pytz.timezone('America/Mexico_City')

# Cache de horarios para evitar consultas repetidas
_horarios_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamp: Optional[datetime] = None
_CACHE_TTL_MINUTES = 30


def _get_horario_unidad(unidad_negocio_id: str, dia_semana: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene el horario operativo de una unidad para un día específico.
    
    Args:
        unidad_negocio_id: ID de la unidad (ej: '130QRO')
        dia_semana: 0=Lunes, 1=Martes, ..., 6=Domingo
    
    Returns:
        Dict con hora_inicio_operativo, hora_fin_operativo, cruza_medianoche
        o None si no existe configuración
    """
    global _horarios_cache, _cache_timestamp
    
    # Verificar cache
    cache_key = f"{unidad_negocio_id}_{dia_semana}"
    now = datetime.now(MEXICO_TZ)
    
    if _cache_timestamp and (now - _cache_timestamp).total_seconds() < _CACHE_TTL_MINUTES * 60:
        if cache_key in _horarios_cache:
            return _horarios_cache[cache_key]
    else:
        # Cache expirado, limpiar
        _horarios_cache = {}
        _cache_timestamp = now
    
    # Consultar base de datos
    query = f"""
    SELECT 
        hora_inicio_operativo,
        hora_fin_operativo,
        cruza_medianoche
    FROM Sistema_HorariosServicioUnidad
    WHERE unidad_negocio_id = '{unidad_negocio_id}'
      AND dia_semana = {dia_semana}
      AND activo = 1
    """
    
    try:
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        if results:
            horario = {
                'hora_inicio': results[0]['hora_inicio_operativo'],
                'hora_fin': results[0]['hora_fin_operativo'],
                'cruza_medianoche': bool(results[0]['cruza_medianoche'])
            }
            _horarios_cache[cache_key] = horario
            return horario
        
        return None
        
    except Exception as e:
        logger.error(f"[OPERATIONAL_WINDOW] Error consultando horario para {unidad_negocio_id}: {e}")
        return None


def get_operational_window(
    unidad_negocio_id: str,
    timestamp: Optional[datetime] = None
) -> Tuple[date, time, time, bool]:
    """
    Calcula la FechaOperacion y ventana operativa para una unidad.
    
    Esta es la función principal que DEBE usarse en lugar de datetime.now().date()
    para determinar a qué día operativo pertenece un momento dado.
    
    Args:
        unidad_negocio_id: ID de la unidad (ej: '130QRO', 'ORIGEN')
        timestamp: Momento a evaluar (default: ahora en México)
    
    Returns:
        Tuple con:
        - fecha_operacion: La fecha operativa calculada
        - hora_inicio: Hora de inicio de la jornada
        - hora_fin: Hora de fin de la jornada
        - cruza_medianoche: Si la jornada cruza la medianoche
    
    Ejemplo:
        # A las 02:00 del 15-May con horario 13:00-03:00
        fecha_op, inicio, fin, cruza = get_operational_window('130QRO')
        # fecha_op = 2026-05-14 (todavía en jornada del 14)
    """
    # Obtener timestamp en zona México
    if timestamp is None:
        timestamp = datetime.now(MEXICO_TZ)
    elif timestamp.tzinfo is None:
        timestamp = MEXICO_TZ.localize(timestamp)
    else:
        timestamp = timestamp.astimezone(MEXICO_TZ)
    
    fecha_calendario = timestamp.date()
    hora_actual = timestamp.time()
    
    # Obtener día de la semana (Python: 0=Lunes)
    dia_semana = fecha_calendario.weekday()
    
    # Obtener horario configurado
    horario = _get_horario_unidad(unidad_negocio_id, dia_semana)
    
    if horario is None:
        # Sin configuración: usar horario por defecto (13:00 - 06:00)
        # ACTUALIZACIÓN 16-May-2026: Corte operativo cambiado de 11:00 a 06:00
        logger.warning(
            f"[OPERATIONAL_WINDOW] {unidad_negocio_id}: Sin horario configurado, "
            f"usando default 13:00-06:00"
        )
        horario = {
            'hora_inicio': time(13, 0, 0),
            'hora_fin': time(6, 0, 0),
            'cruza_medianoche': True
        }
    
    hora_inicio = horario['hora_inicio']
    hora_fin = horario['hora_fin']
    cruza_medianoche = horario['cruza_medianoche']
    
    # Convertir a time si viene como timedelta
    if isinstance(hora_inicio, timedelta):
        total_seconds = int(hora_inicio.total_seconds())
        hora_inicio = time(total_seconds // 3600, (total_seconds % 3600) // 60)
    if isinstance(hora_fin, timedelta):
        total_seconds = int(hora_fin.total_seconds())
        hora_fin = time(total_seconds // 3600, (total_seconds % 3600) // 60)
    
    # Calcular FechaOperacion
    if cruza_medianoche:
        # Jornada cruza medianoche (ej: 13:00 - 03:00)
        # Si estamos entre 00:00 y hora_fin, pertenecemos al día ANTERIOR
        if hora_actual < hora_fin:
            fecha_operacion = fecha_calendario - timedelta(days=1)
            logger.debug(
                f"[OPERATIONAL_WINDOW] {unidad_negocio_id} @ {timestamp.strftime('%H:%M')}: "
                f"Antes de cierre ({hora_fin}), fecha_operacion = {fecha_operacion} (día anterior)"
            )
        elif hora_actual >= hora_inicio:
            # Después de hora_inicio: día actual
            fecha_operacion = fecha_calendario
            logger.debug(
                f"[OPERATIONAL_WINDOW] {unidad_negocio_id} @ {timestamp.strftime('%H:%M')}: "
                f"Después de apertura ({hora_inicio}), fecha_operacion = {fecha_operacion}"
            )
        else:
            # Entre hora_fin y hora_inicio (restaurante cerrado)
            # Pertenece al día anterior (última jornada que cerró)
            fecha_operacion = fecha_calendario - timedelta(days=1)
            logger.debug(
                f"[OPERATIONAL_WINDOW] {unidad_negocio_id} @ {timestamp.strftime('%H:%M')}: "
                f"Cerrado (entre {hora_fin} y {hora_inicio}), fecha_operacion = {fecha_operacion}"
            )
    else:
        # Jornada NO cruza medianoche (ej: 13:00 - 23:00)
        # Si estamos antes de hora_inicio, pertenecemos al día anterior
        if hora_actual < hora_inicio:
            fecha_operacion = fecha_calendario - timedelta(days=1)
        else:
            fecha_operacion = fecha_calendario
    
    logger.info(
        f"[OPERATIONAL_WINDOW] {unidad_negocio_id}: "
        f"timestamp={timestamp.strftime('%Y-%m-%d %H:%M')}, "
        f"fecha_operacion={fecha_operacion}, "
        f"horario={hora_inicio}-{hora_fin}, "
        f"cruza_medianoche={cruza_medianoche}"
    )
    
    return fecha_operacion, hora_inicio, hora_fin, cruza_medianoche


def get_query_date_range(
    unidad_negocio_id: str,
    timestamp: Optional[datetime] = None
) -> Tuple[str, str]:
    """
    Obtiene el rango de fechas para usar en queries SQL a las APIs locales.
    
    Para jornadas que cruzan medianoche, la query debe considerar registros
    de la fecha_operacion Y la fecha_calendario (para capturas después de 00:00).
    
    Args:
        unidad_negocio_id: ID de la unidad
        timestamp: Momento a evaluar (default: ahora en México)
    
    Returns:
        Tuple con (fecha_inicio, fecha_fin) en formato ISO para SQL
    """
    fecha_operacion, hora_inicio, hora_fin, cruza_medianoche = get_operational_window(
        unidad_negocio_id, timestamp
    )
    
    if cruza_medianoche:
        # La query debe cubrir fecha_operacion Y el día siguiente (hasta hora_fin)
        fecha_inicio = fecha_operacion.isoformat()
        fecha_fin = (fecha_operacion + timedelta(days=1)).isoformat()
    else:
        # La query solo necesita la fecha_operacion
        fecha_inicio = fecha_operacion.isoformat()
        fecha_fin = fecha_operacion.isoformat()
    
    return fecha_inicio, fecha_fin


def is_within_operational_hours(
    unidad_negocio_id: str,
    timestamp: Optional[datetime] = None
) -> bool:
    """
    Verifica si un timestamp está dentro del horario operativo de la unidad.
    
    Útil para decidir si hacer sync o esperar.
    
    Args:
        unidad_negocio_id: ID de la unidad
        timestamp: Momento a evaluar (default: ahora en México)
    
    Returns:
        True si está dentro del horario operativo
    """
    if timestamp is None:
        timestamp = datetime.now(MEXICO_TZ)
    elif timestamp.tzinfo is None:
        timestamp = MEXICO_TZ.localize(timestamp)
    else:
        timestamp = timestamp.astimezone(MEXICO_TZ)
    
    hora_actual = timestamp.time()
    fecha_calendario = timestamp.date()
    dia_semana = fecha_calendario.weekday()
    
    horario = _get_horario_unidad(unidad_negocio_id, dia_semana)
    
    if horario is None:
        # Sin config, asumir siempre operativo
        return True
    
    hora_inicio = horario['hora_inicio']
    hora_fin = horario['hora_fin']
    cruza_medianoche = horario['cruza_medianoche']
    
    # Convertir si es timedelta
    if isinstance(hora_inicio, timedelta):
        total_seconds = int(hora_inicio.total_seconds())
        hora_inicio = time(total_seconds // 3600, (total_seconds % 3600) // 60)
    if isinstance(hora_fin, timedelta):
        total_seconds = int(hora_fin.total_seconds())
        hora_fin = time(total_seconds // 3600, (total_seconds % 3600) // 60)
    
    if cruza_medianoche:
        # Operativo si: hora >= inicio OR hora < fin
        return hora_actual >= hora_inicio or hora_actual < hora_fin
    else:
        # Operativo si: inicio <= hora <= fin
        return hora_inicio <= hora_actual <= hora_fin


# Función de conveniencia para testing
def debug_operational_window(unidad_negocio_id: str):
    """Imprime información de debug sobre la ventana operativa actual."""
    now = datetime.now(MEXICO_TZ)
    fecha_op, inicio, fin, cruza = get_operational_window(unidad_negocio_id, now)
    dentro = is_within_operational_hours(unidad_negocio_id, now)
    
    print(f"\n=== DEBUG VENTANA OPERATIVA: {unidad_negocio_id} ===")
    print(f"  Timestamp actual (México): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Fecha calendario: {now.date()}")
    print(f"  FechaOperacion calculada: {fecha_op}")
    print(f"  Horario: {inicio} - {fin}")
    print(f"  Cruza medianoche: {cruza}")
    print(f"  Dentro de horario operativo: {dentro}")
    
    return fecha_op


# ============================================================================
# FASE SYNC-1: Funciones para sincronización histórica
# ============================================================================

# Constantes de ventana operativa default
# NOTA: Preparado para futuro módulo de Horarios de Operación por unidad
DEFAULT_VENTANA_INICIO_HORA = 13  # 13:00
DEFAULT_VENTANA_FIN_HORA = 11     # 11:00 del día siguiente
DEFAULT_CRUZA_MEDIANOCHE = True


def get_sync_operational_window(
    timestamp: datetime,
    ventana_inicio_hora: int = DEFAULT_VENTANA_INICIO_HORA,
    ventana_fin_hora: int = DEFAULT_VENTANA_FIN_HORA,
    cruza_medianoche: bool = DEFAULT_CRUZA_MEDIANOCHE
) -> Tuple[date, time, time, bool]:
    """
    Calcula la ventana operativa para sincronización histórica.
    
    FASE SYNC-1: Función específica para procesos de sincronización.
    Permite pasar parámetros explícitos de ventana para preparar
    futuro módulo de Horarios de Operación por unidad.
    
    Args:
        timestamp: Momento a evaluar (debe tener timezone México)
        ventana_inicio_hora: Hora de inicio (default 13)
        ventana_fin_hora: Hora de fin (default 11)
        cruza_medianoche: Si la jornada cruza medianoche (default True)
    
    Returns:
        Tuple con:
        - fecha_operacion: La fecha operativa calculada
        - hora_inicio: time de inicio de jornada
        - hora_fin: time de fin de jornada
        - cruza_medianoche: bool
    
    Ejemplo con ventana 13:00-11:00:
        timestamp = 2026-05-15 02:00:00 México
        → fecha_operacion = 2026-05-14 (jornada del 14 no ha cerrado a las 11:00)
    """
    # Asegurar timezone México
    if timestamp.tzinfo is None:
        timestamp = MEXICO_TZ.localize(timestamp)
    else:
        timestamp = timestamp.astimezone(MEXICO_TZ)
    
    fecha_calendario = timestamp.date()
    hora_actual = timestamp.time()
    
    hora_inicio = time(ventana_inicio_hora, 0, 0)
    hora_fin = time(ventana_fin_hora, 0, 0)
    
    # Calcular FechaOperacion
    if cruza_medianoche:
        # Jornada cruza medianoche (ej: 13:00 - 11:00)
        if hora_actual < hora_fin:
            # Antes del cierre: pertenece al día ANTERIOR
            fecha_operacion = fecha_calendario - timedelta(days=1)
        elif hora_actual >= hora_inicio:
            # Después de apertura: día actual
            fecha_operacion = fecha_calendario
        else:
            # Entre cierre (11:00) y apertura (13:00): cerrado
            # Pertenece al día anterior (última jornada que cerró)
            fecha_operacion = fecha_calendario - timedelta(days=1)
    else:
        # Jornada NO cruza medianoche
        if hora_actual < hora_inicio:
            fecha_operacion = fecha_calendario - timedelta(days=1)
        else:
            fecha_operacion = fecha_calendario
    
    return fecha_operacion, hora_inicio, hora_fin, cruza_medianoche


def get_mexico_now() -> datetime:
    """
    Obtiene el timestamp actual en zona horaria México.
    
    FASE SYNC-1: Usar en lugar de datetime.now() o datetime.utcnow().
    """
    return datetime.now(MEXICO_TZ)


def get_fecha_operacion_now(
    ventana_inicio_hora: int = DEFAULT_VENTANA_INICIO_HORA,
    ventana_fin_hora: int = DEFAULT_VENTANA_FIN_HORA
) -> date:
    """
    Calcula la fecha operativa para el momento actual.
    
    FASE SYNC-1: Conveniencia para obtener fecha_operacion sin crear timestamp.
    """
    now = get_mexico_now()
    fecha_op, _, _, _ = get_sync_operational_window(
        now, ventana_inicio_hora, ventana_fin_hora
    )
    return fecha_op

