import os
from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Módulo de Ventana Operativa y Cálculo de FechaOperacion
=====================================================================

FASE P0.3 (2026-05-20): Refactorización completa para soportar turnos operativos.

REGLAS DE NEGOCIO:
- La FechaOperacion se calcula según la configuración de turnos por unidad
- Turnos soportados: DESAYUNO, COMIDA, CENA
- Zona horaria obligatoria: America/Mexico_City
- NO usar fecha calendario, hora de servidor local, UTC ni GETDATE()
- Soporta cruza_medianoche
- Soporta tolerancias de inicio/fin

SALIDA ESTANDAR:
{
    "unidad_negocio_pk": str,
    "fecha_operacion": date,
    "turno_operativo_codigo": str,  # DESAYUNO, COMIDA, CENA, FUERA_HORARIO
    "window_start_mx": time,
    "window_end_mx": time,
    "timezone": "America/Mexico_City",
    "metodo_fecha_operacion": str,  # TURNO_ACTIVO, PRIMER_TURNO_DIA, ULTIMO_TURNO_DIA_ANTERIOR
    "alertas": List[str]
}

Autor: EDARSA HUB P0
Fecha: 2026-05-20
"""

import logging
from datetime import date, datetime, time, timedelta
from typing import Optional, Tuple, Dict, Any, List
from zoneinfo import ZoneInfo
from dataclasses import dataclass
from core.sql_first.db import get_sql_connection

logger = logging.getLogger(__name__)

# Zona horaria oficial
MEXICO_TZ = ZoneInfo("America/Mexico_City")

# Configuración de conexión EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': os.getenv('EDARSAHUB_SQL_HOST'),
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': os.getenv('EDARSAHUB_SQL_USER'),
    'password': os.getenv('EDARSAHUB_SQL_PASSWORD')
}

# Cache de configuración de turnos
_turnos_cache: Dict[str, List[Dict]] = {}
_cache_timestamp: Optional[datetime] = None
_CACHE_TTL_MINUTES = 15


def _resolver_unidad_turnos_id(unidad_negocio_pk: str) -> str:
    """
    Normaliza el identificador usado para buscar turnos operativos.

    Sistema_TurnosOperativosUnidad.unidad_negocio_id guarda el codigo operativo
    de unidad, por ejemplo: 130QRO, ORIGEN, CIENFUEGOS.

    Algunos flujos comerciales pasan unidad_negocio_pk como GUID canonico.
    Para evitar fallback operativo incorrecto, aqui se resuelve GUID -> codigo.
    """
    raw = str(unidad_negocio_pk or "").strip()
    if not raw:
        return raw

    def _extraer_codigo(info):
        if not isinstance(info, dict):
            return None

        for key in (
            "codigo",
            "unidad_codigo",
            "unidad_negocio_codigo",
            "unidad_negocio_id",
            "UnidadNegocioID",
            "UnidadCodigo",
            "Codigo",
        ):
            value = info.get(key)
            if value not in (None, ""):
                value = str(value).strip()
                if value:
                    return value

        return None

    # Resolver directo si el servicio ofrece una funcion canonica GUID -> codigo.
    try:
        resolver_codigo = getattr(UnidadesService, "resolver_codigo", None)
        if callable(resolver_codigo):
            codigo = resolver_codigo(raw)
            if codigo not in (None, ""):
                codigo = str(codigo).strip()
                if codigo:
                    return codigo
    except Exception as exc:
        logger.debug(
            "[OPERATIONAL_WINDOW] resolver_codigo fallo para %s: %s",
            raw,
            exc,
        )

    # Intentos por metodos de lectura conocidos.
    for method_name in ("get_by_pk", "get_by_id", "get_by_codigo"):
        try:
            method = getattr(UnidadesService, method_name, None)
            if not callable(method):
                continue
            info = method(raw) or {}
            codigo = _extraer_codigo(info)
            if codigo:
                return codigo
        except Exception as exc:
            logger.debug(
                "[OPERATIONAL_WINDOW] %s fallo para %s: %s",
                method_name,
                raw,
                exc,
            )

    # Fallback SQL defensivo: solo para resolver metadata canonica EDARSAHUB.
    try:
        conn = get_sql_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP 1
                COALESCE(
                    CAST(codigo AS varchar(100)),
                    CAST(unidad_codigo AS varchar(100)),
                    CAST(unidad_negocio_codigo AS varchar(100)),
                    CAST(unidad_negocio_id AS varchar(100))
                ) AS codigo
            FROM Unidades_Negocio
            WHERE CAST(id AS varchar(100)) = %s
               OR CAST(unidad_negocio_pk AS varchar(100)) = %s
               OR CAST(codigo AS varchar(100)) = %s
               OR CAST(unidad_codigo AS varchar(100)) = %s
               OR CAST(unidad_negocio_codigo AS varchar(100)) = %s
               OR CAST(unidad_negocio_id AS varchar(100)) = %s
        """, (raw, raw, raw, raw, raw, raw))

        row = cursor.fetchone()
        conn.close()

        if row:
            codigo = row[0] if not isinstance(row, dict) else row.get("codigo")
            if codigo not in (None, ""):
                return str(codigo).strip()

    except Exception as exc:
        logger.debug(
            "[OPERATIONAL_WINDOW] fallback SQL Unidades_Negocio fallo para %s: %s",
            raw,
            exc,
        )

    return raw


@dataclass
class ResultadoVentanaOperativa:
    """Estructura de resultado del cálculo de ventana operativa."""
    unidad_negocio_pk: str
    fecha_operacion: date
    turno_operativo_codigo: str
    turno_nombre: str
    window_start_mx: time
    window_end_mx: time
    cruza_medianoche: bool
    timezone: str
    metodo_fecha_operacion: str
    alertas: List[str]
    timestamp_consulta: datetime


def _get_turnos_unidad(unidad_negocio_pk: str) -> List[Dict]:
    """
    Obtiene los turnos operativos activos de una unidad desde EDARSAHUB SQL.

    La tabla Sistema_TurnosOperativosUnidad.unidad_negocio_id guarda codigo
    operativo de unidad, no GUID. Este metodo acepta ambos:
    - codigo: 130QRO, ORIGEN, CIENFUEGOS
    - GUID canonico de Unidades_Negocio
    """
    global _turnos_cache, _cache_timestamp

    unidad_turnos_id = _resolver_unidad_turnos_id(unidad_negocio_pk)

    now = datetime.now(MEXICO_TZ)

    # Verificar cache por identificador operativo real.
    if _cache_timestamp and (now - _cache_timestamp).total_seconds() < _CACHE_TTL_MINUTES * 60:
        if unidad_turnos_id in _turnos_cache:
            return _turnos_cache[unidad_turnos_id]
    else:
        _turnos_cache = {}
        _cache_timestamp = now

    try:
        conn = get_sql_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                turno_codigo,
                turno_nombre,
                CAST(hora_inicio AS VARCHAR(8)) AS hora_inicio,
                CAST(hora_fin AS VARCHAR(8)) AS hora_fin,
                cruza_medianoche,
                aplica_ventas_dia,
                es_turno_principal,
                orden
            FROM Sistema_TurnosOperativosUnidad
            WHERE unidad_negocio_id = %s
              AND activo = 1
              AND aplica_ventas_dia = 1
            ORDER BY orden
        """, (unidad_turnos_id,))

        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description] if cursor.description else []
        conn.close()

        def _parse_time(v):
            if isinstance(v, time):
                return v
            if isinstance(v, timedelta):
                total_sec = int(v.total_seconds())
                return time(total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60)
            parts = str(v).split(":")
            return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)

        turnos: List[Dict] = []
        for r in rows:
            t = r if isinstance(r, dict) else dict(zip(cols, r))
            t["hora_inicio"] = _parse_time(t["hora_inicio"])
            t["hora_fin"] = _parse_time(t["hora_fin"])
            t["cruza_medianoche"] = bool(t.get("cruza_medianoche"))
            t["aplica_ventas_dia"] = bool(t.get("aplica_ventas_dia"))
            t["es_turno_principal"] = bool(t.get("es_turno_principal"))
            t["tolerancia_inicio_minutos"] = 5
            t["tolerancia_fin_minutos"] = 30
            turnos.append(t)

        _turnos_cache[unidad_turnos_id] = turnos
        logger.debug(
            "[OPERATIONAL_WINDOW] %s -> %s: %s turnos cargados",
            unidad_negocio_pk,
            unidad_turnos_id,
            len(turnos),
        )
        return turnos

    except Exception as e:
        logger.error(
            "[OPERATIONAL_WINDOW] Error consultando turnos para %s -> %s: %s",
            unidad_negocio_pk,
            unidad_turnos_id,
            e,
        )
        return []


def clear_turnos_cache():
    """Invalida el cache de turnos (usar tras editar la configuración operativa)."""
    global _turnos_cache, _cache_timestamp
    _turnos_cache = {}
    _cache_timestamp = None


def _hora_en_rango(hora: time, inicio: time, fin: time, cruza_medianoche: bool, 
                   tolerancia_inicio: int = 0) -> bool:
    """
    Verifica si una hora está dentro de un rango horario.
    
    NOTA: Solo se aplica tolerancia al INICIO para permitir que ventas
    capturadas un poco antes del inicio oficial se clasifiquen correctamente.
    La tolerancia de FIN NO se usa aquí para evitar que un turno "invada"
    el siguiente turno.
    
    Args:
        hora: Hora a verificar
        inicio: Hora de inicio del turno
        fin: Hora de fin del turno
        cruza_medianoche: Si el turno cruza medianoche
        tolerancia_inicio: Minutos de tolerancia antes del inicio
    
    Returns:
        True si la hora está en el rango
    """
    # Aplicar tolerancia al inicio (restar minutos)
    inicio_dt = datetime(2000, 1, 1, inicio.hour, inicio.minute)
    inicio_con_tolerancia = (inicio_dt - timedelta(minutes=tolerancia_inicio)).time()
    
    if cruza_medianoche:
        # Turno cruza medianoche (ej: 19:00-05:59)
        # Está en rango si: hora >= inicio OR hora <= fin
        return hora >= inicio_con_tolerancia or hora <= fin
    else:
        # Turno NO cruza medianoche (ej: 13:01-18:59)
        return inicio_con_tolerancia <= hora <= fin


def get_operational_window(
    unidad_negocio_pk: str,
    timestamp: Optional[datetime] = None
) -> ResultadoVentanaOperativa:
    """
    Calcula la FechaOperacion y turno operativo para una unidad.
    
    Esta es la función principal para determinar a qué día operativo
    y turno pertenece un momento dado.
    
    Args:
        unidad_negocio_pk: ID de la unidad (ej: '130QRO', 'ORIGEN')
        timestamp: Momento a evaluar (default: ahora en México)
    
    Returns:
        ResultadoVentanaOperativa con todos los datos del cálculo
    
    REGLAS:
    1. Si hay un turno activo que cubra la hora actual → usar ese turno
    2. Si estamos antes del primer turno del día → pertenecer al último turno del día anterior
    3. Si estamos entre turnos → usar el siguiente turno del día actual
    """
    # Normalizar timestamp a México
    if timestamp is None:
        timestamp = datetime.now(MEXICO_TZ)
    elif timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=MEXICO_TZ)
    else:
        timestamp = timestamp.astimezone(MEXICO_TZ)
    
    fecha_calendario = timestamp.date()
    hora_actual = timestamp.time()
    alertas = []
    
    # Obtener turnos configurados
    turnos = _get_turnos_unidad(unidad_negocio_pk)
    
    if not turnos:
        # Sin configuración: ALERTA y usar default 13:00-06:00
        alertas.append("SIN_CONFIGURACION_TURNOS")
        logger.warning(f"[OPERATIONAL_WINDOW] {unidad_negocio_pk}: Sin turnos configurados")
        
        # Fallback: 13:00-06:00 cruza medianoche
        hora_inicio = time(13, 0)
        hora_fin = time(6, 0)
        
        if hora_actual < hora_fin:
            # Antes del cierre (madrugada): día anterior
            fecha_operacion = fecha_calendario - timedelta(days=1)
            metodo = "FALLBACK_CRUZA_MEDIANOCHE"
        elif hora_actual >= hora_inicio:
            # Después de apertura: día actual
            fecha_operacion = fecha_calendario
            metodo = "FALLBACK_DIA_ACTUAL"
        else:
            # Entre cierre y apertura: día anterior
            fecha_operacion = fecha_calendario - timedelta(days=1)
            metodo = "FALLBACK_ENTRE_TURNOS"
        
        return ResultadoVentanaOperativa(
            unidad_negocio_pk=unidad_negocio_pk,
            fecha_operacion=fecha_operacion,
            turno_operativo_codigo="FALLBACK",
            turno_nombre="Sin Configuración",
            window_start_mx=hora_inicio,
            window_end_mx=hora_fin,
            cruza_medianoche=True,
            timezone="America/Mexico_City",
            metodo_fecha_operacion=metodo,
            alertas=alertas,
            timestamp_consulta=timestamp
        )
    
    # Buscar turno activo actual
    for turno in turnos:
        tolerancia_inicio = turno.get('tolerancia_inicio_minutos', 5)
        
        if _hora_en_rango(
            hora_actual, 
            turno['hora_inicio'], 
            turno['hora_fin'],
            turno['cruza_medianoche'],
            tolerancia_inicio
        ):
            # Encontramos el turno activo
            if turno['cruza_medianoche'] and hora_actual < turno['hora_fin']:
                # Estamos en la madrugada (00:00 - hora_fin): pertenece al día ANTERIOR
                fecha_operacion = fecha_calendario - timedelta(days=1)
                metodo = "TURNO_CRUZA_MEDIANOCHE_MADRUGADA"
            else:
                # Estamos en horario normal del turno: día actual
                fecha_operacion = fecha_calendario
                metodo = "TURNO_ACTIVO"
            
            logger.info(
                f"[OPERATIONAL_WINDOW] {unidad_negocio_pk}: "
                f"turno={turno['turno_codigo']}, hora={hora_actual.strftime('%H:%M')}, "
                f"fecha_operacion={fecha_operacion}, metodo={metodo}"
            )
            
            return ResultadoVentanaOperativa(
                unidad_negocio_pk=unidad_negocio_pk,
                fecha_operacion=fecha_operacion,
                turno_operativo_codigo=turno['turno_codigo'],
                turno_nombre=turno['turno_nombre'],
                window_start_mx=turno['hora_inicio'],
                window_end_mx=turno['hora_fin'],
                cruza_medianoche=turno['cruza_medianoche'],
                timezone="America/Mexico_City",
                metodo_fecha_operacion=metodo,
                alertas=alertas,
                timestamp_consulta=timestamp
            )
    
    # No estamos en ningún turno activo
    # Determinar si estamos ANTES del primer turno o DESPUÉS del último
    primer_turno = turnos[0]
    ultimo_turno = turnos[-1]
    
    if hora_actual < primer_turno['hora_inicio']:
        # Antes del primer turno del día
        if ultimo_turno['cruza_medianoche']:
            # El último turno del día anterior aún podría estar activo
            # (ya se manejó arriba), pero si llegamos aquí, estamos
            # en el "gap" entre turnos
            fecha_operacion = fecha_calendario - timedelta(days=1)
            metodo = "ANTES_PRIMER_TURNO_CRUZA"
        else:
            # No hay turno que cruce medianoche
            fecha_operacion = fecha_calendario - timedelta(days=1)
            metodo = "ANTES_PRIMER_TURNO"
        
        alertas.append("FUERA_HORARIO_OPERATIVO")
        
        return ResultadoVentanaOperativa(
            unidad_negocio_pk=unidad_negocio_pk,
            fecha_operacion=fecha_operacion,
            turno_operativo_codigo="FUERA_HORARIO",
            turno_nombre="Fuera de Horario",
            window_start_mx=primer_turno['hora_inicio'],
            window_end_mx=ultimo_turno['hora_fin'],
            cruza_medianoche=ultimo_turno['cruza_medianoche'],
            timezone="America/Mexico_City",
            metodo_fecha_operacion=metodo,
            alertas=alertas,
            timestamp_consulta=timestamp
        )
    
    # Estamos ENTRE turnos o DESPUÉS del último turno del día
    # (sin turno que cruce medianoche activo)
    fecha_operacion = fecha_calendario
    metodo = "ENTRE_TURNOS_DIA_ACTUAL"
    alertas.append("ENTRE_TURNOS")
    
    # Buscar el siguiente turno para window_start
    siguiente_turno = None
    for turno in turnos:
        if turno['hora_inicio'] > hora_actual:
            siguiente_turno = turno
            break
    
    if siguiente_turno:
        return ResultadoVentanaOperativa(
            unidad_negocio_pk=unidad_negocio_pk,
            fecha_operacion=fecha_operacion,
            turno_operativo_codigo=siguiente_turno['turno_codigo'],
            turno_nombre=f"Esperando {siguiente_turno['turno_nombre']}",
            window_start_mx=siguiente_turno['hora_inicio'],
            window_end_mx=siguiente_turno['hora_fin'],
            cruza_medianoche=siguiente_turno['cruza_medianoche'],
            timezone="America/Mexico_City",
            metodo_fecha_operacion=metodo,
            alertas=alertas,
            timestamp_consulta=timestamp
        )
    else:
        # Después del último turno del día
        return ResultadoVentanaOperativa(
            unidad_negocio_pk=unidad_negocio_pk,
            fecha_operacion=fecha_operacion,
            turno_operativo_codigo="DESPUES_CIERRE",
            turno_nombre="Después del Cierre",
            window_start_mx=ultimo_turno['hora_inicio'],
            window_end_mx=ultimo_turno['hora_fin'],
            cruza_medianoche=ultimo_turno['cruza_medianoche'],
            timezone="America/Mexico_City",
            metodo_fecha_operacion="DESPUES_ULTIMO_TURNO",
            alertas=alertas + ["DESPUES_HORARIO_OPERATIVO"],
            timestamp_consulta=timestamp
        )


def get_fecha_operacion(
    unidad_negocio_pk: str,
    timestamp: Optional[datetime] = None
) -> date:
    """
    Obtiene solo la FechaOperacion para una unidad.
    
    Función de conveniencia para casos donde solo se necesita la fecha.
    """
    resultado = get_operational_window(unidad_negocio_pk, timestamp)
    return resultado.fecha_operacion


def get_turno_operativo(
    unidad_negocio_pk: str,
    timestamp: Optional[datetime] = None
) -> str:
    """
    Obtiene solo el código del turno operativo.
    
    Returns:
        'DESAYUNO', 'COMIDA', 'CENA', 'FUERA_HORARIO', etc.
    """
    resultado = get_operational_window(unidad_negocio_pk, timestamp)
    return resultado.turno_operativo_codigo


def get_mexico_now() -> datetime:
    """Obtiene el timestamp actual en zona horaria México."""
    return datetime.now(MEXICO_TZ)


def get_fecha_operacion_now(unidad_negocio_pk: str) -> date:
    """Calcula la fecha operativa para el momento actual."""
    return get_fecha_operacion(unidad_negocio_pk, get_mexico_now())


def is_within_operational_hours(
    unidad_negocio_pk: str,
    timestamp: Optional[datetime] = None
) -> bool:
    """
    Verifica si un timestamp está dentro del horario operativo de la unidad.
    """
    resultado = get_operational_window(unidad_negocio_pk, timestamp)
    return "FUERA_HORARIO" not in resultado.turno_operativo_codigo


def debug_operational_window(unidad_negocio_pk: str):
    """Imprime información de debug sobre la ventana operativa actual."""
    resultado = get_operational_window(unidad_negocio_pk)
    
    print(f"\n=== DEBUG VENTANA OPERATIVA: {unidad_negocio_pk} ===")
    print(f"  Timestamp (México): {resultado.timestamp_consulta.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Fecha calendario: {resultado.timestamp_consulta.date()}")
    print(f"  FechaOperacion: {resultado.fecha_operacion}")
    print(f"  Turno: {resultado.turno_operativo_codigo} ({resultado.turno_nombre})")
    print(f"  Ventana: {resultado.window_start_mx} - {resultado.window_end_mx}")
    print(f"  Cruza medianoche: {resultado.cruza_medianoche}")
    print(f"  Método: {resultado.metodo_fecha_operacion}")
    print(f"  Alertas: {resultado.alertas}")
    
    return resultado




def get_operational_datetime_range_for_fecha_operacion(
    unidad_negocio_pk: str,
    fecha_operacion: date
) -> Tuple[datetime, datetime, Dict[str, Any]]:
    """
    Retorna el rango datetime canónico completo para consultar POS por FechaOperacion.

    Usa todos los turnos activos con aplica_ventas_dia=1 desde
    Sistema_TurnosOperativosUnidad. No usa día civil ni Mongo.
    """
    turnos = _get_turnos_unidad(unidad_negocio_pk)
    if not turnos:
        raise RuntimeError(
            f"Sin turnos operativos activos para unidad {unidad_negocio_pk}"
        )

    ordenados = sorted(turnos, key=lambda t: int(t.get("orden") or 0))
    primer_turno = ordenados[0]
    ultimo_turno = ordenados[-1]

    hora_inicio = primer_turno["hora_inicio"]
    hora_fin = ultimo_turno["hora_fin"]

    inicio = datetime.combine(fecha_operacion, hora_inicio)
    fin = datetime.combine(fecha_operacion, hora_fin)

    if bool(ultimo_turno.get("cruza_medianoche")) or fin <= inicio:
        fin = fin + timedelta(days=1)

    metadata = {
        "unidad_negocio_pk": unidad_negocio_pk,
        "turno_inicio_codigo": primer_turno.get("turno_codigo"),
        "turno_fin_codigo": ultimo_turno.get("turno_codigo"),
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "cruza_medianoche": bool(ultimo_turno.get("cruza_medianoche")) or fin.date() > fecha_operacion,
        "turnos_count": len(ordenados),
        "turnos": ordenados,
    }

    return inicio, fin, metadata


# =============================================================================
# FUNCIONES LEGACY PARA COMPATIBILIDAD
# =============================================================================

def get_query_date_range(
    unidad_negocio_pk: str,
    timestamp: Optional[datetime] = None
) -> Tuple[str, str]:
    """
    Obtiene el rango de fechas para queries SQL.
    
    LEGACY: Mantener para compatibilidad con código existente.
    """
    resultado = get_operational_window(unidad_negocio_pk, timestamp)
    fecha_operacion = resultado.fecha_operacion
    
    if resultado.cruza_medianoche:
        fecha_inicio = fecha_operacion.isoformat()
        fecha_fin = (fecha_operacion + timedelta(days=1)).isoformat()
    else:
        fecha_inicio = fecha_operacion.isoformat()
        fecha_fin = fecha_operacion.isoformat()
    
    return fecha_inicio, fecha_fin


def get_sync_operational_window(
    timestamp: datetime,
    ventana_inicio_hora: int = 13,
    ventana_fin_hora: int = 6,
    cruza_medianoche: bool = True
) -> Tuple[date, time, time, bool]:
    """
    LEGACY: Función para procesos de sincronización sin unidad específica.
    
    NOTA: Preferir usar get_operational_window(unidad_id) para cálculos
    correctos basados en configuración por unidad.
    """
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=MEXICO_TZ)
    else:
        timestamp = timestamp.astimezone(MEXICO_TZ)
    
    fecha_calendario = timestamp.date()
    hora_actual = timestamp.time()
    
    hora_inicio = time(ventana_inicio_hora, 0, 0)
    hora_fin = time(ventana_fin_hora, 0, 0)
    
    if cruza_medianoche:
        if hora_actual < hora_fin:
            fecha_operacion = fecha_calendario - timedelta(days=1)
        elif hora_actual >= hora_inicio:
            fecha_operacion = fecha_calendario
        else:
            fecha_operacion = fecha_calendario - timedelta(days=1)
    else:
        if hora_actual < hora_inicio:
            fecha_operacion = fecha_calendario - timedelta(days=1)
        else:
            fecha_operacion = fecha_calendario
    
    return fecha_operacion, hora_inicio, hora_fin, cruza_medianoche


# Mantener constantes legacy para compatibilidad
DEFAULT_VENTANA_INICIO_HORA = 13
DEFAULT_VENTANA_FIN_HORA = 6
DEFAULT_CRUZA_MEDIANOCHE = True


# =============================================================================
# WRAPPER LEGACY PARA COMPATIBILIDAD CON sync_comercial_abiertas_v2_job
# =============================================================================

def get_operational_window_legacy(
    unidad_negocio_pk: str,
    timestamp: Optional[datetime] = None
) -> Tuple[date, time, time, bool]:
    """
    LEGACY WRAPPER: Retorna tupla (fecha_operacion, hora_inicio, hora_fin, cruza_medianoche)
    
    Esta función existe SOLO para compatibilidad con código existente.
    Nuevas implementaciones deben usar get_operational_window() que retorna
    ResultadoVentanaOperativa con toda la información.
    """
    resultado = get_operational_window(unidad_negocio_pk, timestamp)
    return (
        resultado.fecha_operacion,
        resultado.window_start_mx,
        resultado.window_end_mx,
        resultado.cruza_medianoche
    )

