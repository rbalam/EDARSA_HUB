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
from core.sql_first.db import get_sql_connection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/unidades-negocio",
    tags=["Admin Configuración Operativa"]
)

# Zona horaria oficial
MEXICO_TZ = ZoneInfo("America/Mexico_City")

# Configuración de conexión EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': os.getenv('EDARSAHUB_SQL_HOST'),
    'port': 1433,
    'database': 'EDARSAHUB',
    'user': os.getenv('EDARSAHUB_SQL_USER'),
    'password': os.getenv('EDARSAHUB_SQL_PASSWORD')
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
    return get_sql_connection()


# FASE3 P0-3: helpers dict-cursor (PyMSSQL devuelve tuplas por defecto)
def _rows_dicts(cursor) -> List[Dict]:
    """Convierte fetchall() (tuplas) a lista de dicts usando description."""
    rows = cursor.fetchall()
    if not rows:
        return []
    if isinstance(rows[0], dict):
        return rows
    cols = [c[0] for c in cursor.description] if cursor.description else []
    return [dict(zip(cols, r)) for r in rows]


def _one_dict(cursor) -> Optional[Dict]:
    """Convierte fetchone() (tupla) a dict usando description."""
    row = cursor.fetchone()
    if not row:
        return None
    if isinstance(row, dict):
        return row
    cols = [c[0] for c in cursor.description] if cursor.description else []
    return dict(zip(cols, row))


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
    
    turnos = _rows_dicts(cursor)
    conn.close()
    return turnos


def calcular_fecha_operacion_por_unidad(
    unidad_negocio_id: str,
    fecha_hora_mexico: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calcula la FechaOperacion para una unidad usando el MOTOR CANÓNICO ÚNICO
    (core.utils.operational_window.get_operational_window): la MISMA lógica que
    usa el sync de ventas. Soporta los turnos canónicos DESAYUNO/COMIDA/CENA y
    cruza_medianoche, leyendo dinámicamente de Sistema_TurnosOperativosUnidad.

    (Antes esta función tenía lógica DUPLICADA y hardcodeada a DESAYUNO +
    COMIDA_CENA legacy; se eliminó para que exista una sola fuente de verdad.)
    """
    from core.utils.operational_window import get_operational_window

    resultado = get_operational_window(unidad_negocio_id, fecha_hora_mexico)

    TURNOS_REALES = {'DESAYUNO', 'COMIDA', 'CENA'}
    codigo = resultado.turno_operativo_codigo
    en_turno = codigo in TURNOS_REALES

    return {
        'unidad_negocio_id': unidad_negocio_id,
        'fecha_hora_input_mexico': resultado.timestamp_consulta.strftime('%Y-%m-%d %H:%M:%S'),
        'fecha_operacion_calculada': str(resultado.fecha_operacion),
        'turno_detectado': codigo if en_turno else None,
        'window_start': resultado.window_start_mx.strftime('%H:%M:%S'),
        'window_end': resultado.window_end_mx.strftime('%H:%M:%S'),
        'cruza_medianoche': bool(resultado.cruza_medianoche),
        'timezone_usada': 'America/Mexico_City',
        'estado_operativo': codigo if en_turno else 'CERRADO'
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
        unidades = [r['unidad_negocio_id'] for r in _rows_dicts(cursor)]
        
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
                    t['turno_codigo'] in ('COMIDA', 'CENA', 'COMIDA_CENA') and t['activo']
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
            detail=f"Error"
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
            detail=f"Error obteniendo configuración"
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
            
            existe = _one_dict(cursor)['existe']
            
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

        # Invalidar cache del motor canónico para que el sync/"Probar" usen lo recién guardado.
        try:
            from core.utils.operational_window import clear_turnos_cache
            clear_turnos_cache()
        except Exception as _e:
            logger.warning(f"[CONFIG_OPERATIVA] No se pudo invalidar cache de turnos: {_e}")

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
            detail=f"Error actualizando configuración"
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
            detail=f"Error calculando FechaOperacion"
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

