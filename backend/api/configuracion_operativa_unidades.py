"""
EDARSA HUB - API de Configuración Operativa de Unidades
=======================================================

Endpoints para administrar turnos operativos y reglas de Ventas del Día
por unidad de negocio.

UBICACIÓN FUNCIONAL:
    Catálogos → Unidades de Negocio → Configuración Operativa / Ventas del Día

TABLAS SQL:
    - Sistema_TurnosOperativosUnidad

ZONA HORARIA OFICIAL:
    America/Mexico_City

CREADO: Fase Configuración Operativa Unidades
"""

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, time, date, timedelta
from zoneinfo import ZoneInfo
import logging
import pymssql
import os

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/unidades-negocio",
    tags=["Admin Configuración Operativa"]
)

# Zona horaria oficial
MEXICO_TZ = ZoneInfo("America/Mexico_City")

# Configuración de conexión EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'user': 'HRLectura',
    'password': 'National09$'
}


# =============================================================================
# SCHEMAS
# =============================================================================

class TurnoOperativoSchema(BaseModel):
    """Schema de un turno operativo."""
    id: Optional[str] = None
    turno_codigo: str
    turno_nombre: str
    hora_inicio: str  # "HH:MM:SS"
    hora_fin: str
    cruza_medianoche: bool = False
    aplica_ventas_dia: bool = True
    es_turno_principal: bool = False
    orden: int = 0
    activo: bool = True


class ConfiguracionOperativaSchema(BaseModel):
    """Schema completo de configuración operativa por unidad."""
    unidad_negocio_id: str
    turnos: List[TurnoOperativoSchema]
    usa_configuracion_operativa: bool = True


class PruebaFechaOperacionRequest(BaseModel):
    """Request para probar cálculo de FechaOperacion."""
    fecha_hora_mexico: Optional[str] = None  # "YYYY-MM-DD HH:MM:SS" en hora México


class PruebaFechaOperacionResponse(BaseModel):
    """Response del cálculo de FechaOperacion."""
    unidad_negocio_id: str
    fecha_hora_input_mexico: str
    fecha_operacion_calculada: str
    turno_detectado: Optional[str]
    window_start: str
    window_end: str
    cruza_medianoche: bool
    timezone_usada: str = "America/Mexico_City"
    estado_operativo: str  # "ABIERTO", "CERRADO", "DESAYUNO", "COMIDA_CENA"


# =============================================================================
# FUNCIONES DE BASE DE DATOS
# =============================================================================

def get_connection():
    """Obtiene conexión a EDARSAHUB."""
    return pymssql.connect(
        server=EDARSAHUB_CONFIG['host'],
        port=EDARSAHUB_CONFIG['port'],
        database=EDARSAHUB_CONFIG['database'],
        user=EDARSAHUB_CONFIG['user'],
        password=EDARSAHUB_CONFIG['password'],
        as_dict=True
    )


def get_turnos_por_unidad(unidad_negocio_id: str) -> List[Dict]:
    """Obtiene turnos operativos de una unidad."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            CAST(id AS VARCHAR(50)) as id,
            unidad_negocio_id,
            turno_codigo,
            turno_nombre,
            CAST(hora_inicio AS VARCHAR(8)) as hora_inicio,
            CAST(hora_fin AS VARCHAR(8)) as hora_fin,
            cruza_medianoche,
            aplica_ventas_dia,
            es_turno_principal,
            orden,
            activo
        FROM Sistema_TurnosOperativosUnidad
        WHERE unidad_negocio_id = %s
        ORDER BY orden, turno_codigo
    """, (unidad_negocio_id,))
    
    turnos = cursor.fetchall()
    conn.close()
    return turnos


def calcular_fecha_operacion_por_unidad(
    unidad_negocio_id: str,
    fecha_hora_mexico: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calcula la FechaOperacion para una unidad usando America/Mexico_City.
    
    Reglas:
    1. Si hay turno de DESAYUNO activo y estamos en horario de desayuno → día actual
    2. Si solo COMIDA_CENA activo y estamos antes de su hora_inicio → día anterior
    3. Si estamos en horario de COMIDA_CENA → día actual (o anterior si cruza medianoche después de 00:00)
    """
    # Hora actual en México si no se proporciona
    if fecha_hora_mexico is None:
        fecha_hora_mexico = datetime.now(MEXICO_TZ)
    elif fecha_hora_mexico.tzinfo is None:
        fecha_hora_mexico = fecha_hora_mexico.replace(tzinfo=MEXICO_TZ)
    
    hora_actual = fecha_hora_mexico.time()
    fecha_calendario = fecha_hora_mexico.date()
    
    # Obtener turnos activos de la unidad
    turnos = get_turnos_por_unidad(unidad_negocio_id)
    turnos_activos = [t for t in turnos if t['activo']]
    
    if not turnos_activos:
        # Fallback: usar día calendario con warning
        logger.warning(
            f"[CONFIG_OPERATIVA] Unidad {unidad_negocio_id} sin turnos activos. "
            f"Usando fecha calendario como fallback."
        )
        return {
            'unidad_negocio_id': unidad_negocio_id,
            'fecha_hora_input_mexico': fecha_hora_mexico.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_operacion_calculada': str(fecha_calendario),
            'turno_detectado': None,
            'window_start': '00:00:00',
            'window_end': '23:59:59',
            'cruza_medianoche': False,
            'timezone_usada': 'America/Mexico_City',
            'estado_operativo': 'SIN_CONFIGURACION'
        }
    
    # Buscar turno DESAYUNO activo
    desayuno = next((t for t in turnos_activos if t['turno_codigo'] == 'DESAYUNO'), None)
    comida_cena = next((t for t in turnos_activos if t['turno_codigo'] == 'COMIDA_CENA'), None)
    
    # Convertir strings a time
    def str_to_time(s: str) -> time:
        parts = s.split(':')
        return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
    
    turno_detectado = None
    fecha_operacion = fecha_calendario
    window_start = '00:00:00'
    window_end = '23:59:59'
    cruza = False
    estado = 'CERRADO'
    
    # Caso 1: DESAYUNO activo
    if desayuno:
        desayuno_inicio = str_to_time(desayuno['hora_inicio'])
        desayuno_fin = str_to_time(desayuno['hora_fin'])
        
        if desayuno_inicio <= hora_actual < desayuno_fin:
            # Estamos en horario de desayuno
            turno_detectado = 'DESAYUNO'
            fecha_operacion = fecha_calendario
            window_start = desayuno['hora_inicio']
            window_end = desayuno['hora_fin']
            estado = 'DESAYUNO'
        elif hora_actual >= desayuno_inicio:
            # Ya pasó el desayuno, checar comida/cena
            pass
    
    # Caso 2: COMIDA_CENA
    if comida_cena and turno_detectado is None:
        cc_inicio = str_to_time(comida_cena['hora_inicio'])
        cc_fin = str_to_time(comida_cena['hora_fin'])
        cruza = comida_cena['cruza_medianoche']
        
        if cruza:
            # Turno que cruza medianoche (ej: 13:00 - 06:00)
            if hora_actual >= cc_inicio:
                # Después de la hora de inicio (ej: 14:00) → día actual
                turno_detectado = 'COMIDA_CENA'
                fecha_operacion = fecha_calendario
                estado = 'COMIDA_CENA'
            elif hora_actual < cc_fin:
                # Antes de la hora de fin (ej: 02:00) → día anterior
                turno_detectado = 'COMIDA_CENA'
                fecha_operacion = fecha_calendario - timedelta(days=1)
                estado = 'COMIDA_CENA'
            else:
                # Entre cc_fin y cc_inicio (ej: 08:00, cerrado)
                # Si hay desayuno activo, ya lo detectamos arriba
                # Si no, estamos cerrados
                if desayuno and desayuno['activo']:
                    # Ya debería haberse detectado arriba
                    pass
                else:
                    # Cerrado, usar día anterior
                    fecha_operacion = fecha_calendario - timedelta(days=1)
                    estado = 'CERRADO'
        else:
            # Turno que NO cruza medianoche (ej: 13:00 - 23:00)
            if cc_inicio <= hora_actual <= cc_fin:
                turno_detectado = 'COMIDA_CENA'
                fecha_operacion = fecha_calendario
                estado = 'COMIDA_CENA'
            elif hora_actual < cc_inicio:
                # Antes de abrir
                if desayuno and desayuno['activo']:
                    # Ya detectado arriba
                    pass
                else:
                    fecha_operacion = fecha_calendario - timedelta(days=1)
                    estado = 'CERRADO'
            else:
                # Después de cerrar
                fecha_operacion = fecha_calendario
                estado = 'CERRADO'
        
        window_start = comida_cena['hora_inicio']
        window_end = comida_cena['hora_fin']
    
    return {
        'unidad_negocio_id': unidad_negocio_id,
        'fecha_hora_input_mexico': fecha_hora_mexico.strftime('%Y-%m-%d %H:%M:%S'),
        'fecha_operacion_calculada': str(fecha_operacion),
        'turno_detectado': turno_detectado,
        'window_start': window_start,
        'window_end': window_end,
        'cruza_medianoche': cruza,
        'timezone_usada': 'America/Mexico_City',
        'estado_operativo': estado
    }


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/todas/configuracion-operativa")
async def get_todas_configuraciones():
    """
    Obtiene la configuración operativa de TODAS las unidades.
    
    Útil para el job de sincronización y para vista general.
    NOTA: Esta ruta debe estar ANTES de /{unidad_id} para evitar conflictos.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Obtener todas las unidades con turnos
        cursor.execute("""
            SELECT DISTINCT unidad_negocio_id
            FROM Sistema_TurnosOperativosUnidad
            ORDER BY unidad_negocio_id
        """)
        unidades = [r['unidad_negocio_id'] for r in cursor.fetchall()]
        
        resultado = {}
        for unidad in unidades:
            turnos = get_turnos_por_unidad(unidad)
            resultado[unidad] = {
                'turnos': turnos,
                'tiene_desayuno_activo': any(
                    t['turno_codigo'] == 'DESAYUNO' and t['activo'] 
                    for t in turnos
                ),
                'tiene_comida_cena_activo': any(
                    t['turno_codigo'] == 'COMIDA_CENA' and t['activo'] 
                    for t in turnos
                )
            }
        
        conn.close()
        
        return {
            'unidades': resultado,
            'total_unidades': len(resultado),
            'timezone_oficial': 'America/Mexico_City'
        }
        
    except Exception as e:
        logger.error(f"[CONFIG_OPERATIVA] Error obteniendo todas las configuraciones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.get("/{unidad_id}/configuracion-operativa")
async def get_configuracion_operativa(unidad_id: str):
    """
    Obtiene la configuración operativa de una unidad.
    
    Incluye turnos configurados (DESAYUNO, COMIDA_CENA).
    """
    try:
        turnos = get_turnos_por_unidad(unidad_id)
        
        return {
            'unidad_negocio_id': unidad_id,
            'turnos': turnos,
            'usa_configuracion_operativa': len(turnos) > 0,
            'timezone_oficial': 'America/Mexico_City'
        }
        
    except Exception as e:
        logger.error(f"[CONFIG_OPERATIVA] Error obteniendo configuración de {unidad_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo configuración: {str(e)}"
        )


@router.put("/{unidad_id}/configuracion-operativa")
async def update_configuracion_operativa(
    unidad_id: str,
    config: ConfiguracionOperativaSchema
):
    """
    Actualiza la configuración operativa de una unidad.
    
    Permite activar/desactivar turnos y cambiar horarios.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        for turno in config.turnos:
            # Verificar si existe
            cursor.execute("""
                SELECT COUNT(*) as existe
                FROM Sistema_TurnosOperativosUnidad
                WHERE unidad_negocio_id = %s AND turno_codigo = %s
            """, (unidad_id, turno.turno_codigo))
            
            existe = cursor.fetchone()['existe']
            
            if existe:
                # UPDATE
                cursor.execute("""
                    UPDATE Sistema_TurnosOperativosUnidad
                    SET 
                        turno_nombre = %s,
                        hora_inicio = %s,
                        hora_fin = %s,
                        cruza_medianoche = %s,
                        aplica_ventas_dia = %s,
                        es_turno_principal = %s,
                        orden = %s,
                        activo = %s,
                        fecha_modificacion = SYSUTCDATETIME(),
                        modificado_por = %s
                    WHERE unidad_negocio_id = %s AND turno_codigo = %s
                """, (
                    turno.turno_nombre,
                    turno.hora_inicio,
                    turno.hora_fin,
                    turno.cruza_medianoche,
                    turno.aplica_ventas_dia,
                    turno.es_turno_principal,
                    turno.orden,
                    turno.activo,
                    'API_UPDATE',
                    unidad_id,
                    turno.turno_codigo
                ))
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO Sistema_TurnosOperativosUnidad
                    (unidad_negocio_id, turno_codigo, turno_nombre, hora_inicio, hora_fin,
                     cruza_medianoche, aplica_ventas_dia, es_turno_principal, orden, activo,
                     creado_por)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    unidad_id,
                    turno.turno_codigo,
                    turno.turno_nombre,
                    turno.hora_inicio,
                    turno.hora_fin,
                    turno.cruza_medianoche,
                    turno.aplica_ventas_dia,
                    turno.es_turno_principal,
                    turno.orden,
                    turno.activo,
                    'API_INSERT'
                ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"[CONFIG_OPERATIVA] Configuración actualizada para {unidad_id}")
        
        return {
            'success': True,
            'message': f'Configuración actualizada para {unidad_id}',
            'turnos_procesados': len(config.turnos)
        }
        
    except Exception as e:
        logger.error(f"[CONFIG_OPERATIVA] Error actualizando configuración de {unidad_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando configuración: {str(e)}"
        )


@router.post("/{unidad_id}/probar-fecha-operacion")
async def probar_fecha_operacion(
    unidad_id: str,
    request: PruebaFechaOperacionRequest
):
    """
    Prueba el cálculo de FechaOperacion para una unidad.
    
    Permite simular cualquier fecha/hora para verificar qué FechaOperacion
    se calcularía según la configuración de turnos.
    """
    try:
        # Parsear fecha/hora si se proporciona
        fecha_hora_mexico = None
        if request.fecha_hora_mexico:
            try:
                fecha_hora_mexico = datetime.strptime(
                    request.fecha_hora_mexico, 
                    '%Y-%m-%d %H:%M:%S'
                ).replace(tzinfo=MEXICO_TZ)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de fecha inválido. Use: YYYY-MM-DD HH:MM:SS"
                )
        
        resultado = calcular_fecha_operacion_por_unidad(unidad_id, fecha_hora_mexico)
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CONFIG_OPERATIVA] Error probando FechaOperacion de {unidad_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculando FechaOperacion: {str(e)}"
        )


# =============================================================================
# FUNCIÓN EXPORTABLE PARA USO EN OTROS MÓDULOS
# =============================================================================

def get_fecha_operacion_para_unidad(unidad_negocio_id: str) -> date:
    """
    Función para usar en otros módulos (ej: sync_comercial_abiertas_v2_job).
    
    Retorna la FechaOperacion calculada según la configuración de turnos
    de la unidad, usando America/Mexico_City.
    """
    resultado = calcular_fecha_operacion_por_unidad(unidad_negocio_id)
    return datetime.strptime(resultado['fecha_operacion_calculada'], '%Y-%m-%d').date()

