"""
EDARSA HUB - API Administrativa: Re-sincronización Controlada
=============================================================
Fase 0 mínima de la Consola General de Scheduler.
Permite re-sincronizar períodos históricos usando handlers oficiales.

MÁXIMAS CUMPLIDAS:
- #3: Usa scheduler oficial (handlers existentes)
- #6: Trazabilidad completa (RunID, usuario, motivo)
- #7: Motivo obligatorio
- #8: Dry run para alto riesgo
- #14: Credenciales desde Servidores_Conexiones
- #15: UPSERT idempotente (sin duplicados)
- #26: No duplicar lógica - usa handler oficial
- #28: Tablero sigue leyendo EDARSAHUB SQL
- #31: Propinas separadas del KPI

NO USA MONGODB - 100% SQL Server
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import date, datetime, timezone
from typing import Optional, Dict, Any, List
import uuid
import time
import logging
import json

from core.security import get_current_user
from core.rbac.middleware import require_permission
from core.server_registry import get_server_by_unidad_codigo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/scheduler", tags=["Admin - Scheduler Resync"])


# =============================================================================
# CONFIGURACIÓN EDARSAHUB - USA VARIABLES DE ENTORNO
# =============================================================================

import os

def _get_edarsahub_config():
    """Obtiene config EDARSAHUB desde variables de entorno."""
    return {
        'host': os.getenv('EDARSAHUB_SQL_HOST'),
        'port': int(os.getenv('EDARSAHUB_SQL_PORT', '1433')),
        'database': os.getenv('EDARSAHUB_SQL_DATABASE'),
        'username': os.getenv('EDARSAHUB_SQL_USER'),
        'password': os.getenv('EDARSAHUB_SQL_PASSWORD')
    }


def _execute_edarsahub_query(query: str, params: tuple = None, fetch: bool = True) -> List[Dict]:
    """Ejecuta query contra EDARSAHUB SQL Server."""
    import pymssql
    
    config = _get_edarsahub_config()
    
    if not config.get('host') or not config.get('password'):
        logger.error("[RESYNC] Faltan variables de entorno EDARSAHUB_SQL_*")
        raise RuntimeError("Configuración EDARSAHUB incompleta - verificar variables de entorno")
    
    try:
        conn = pymssql.connect(
            server=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['username'],
            password=config['password'],
            timeout=60,
            login_timeout=30
        )
        cursor = conn.cursor(as_dict=True)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            try:
                results = list(cursor.fetchall())
            except Exception:
                results = []
        else:
            conn.commit()
            results = []
        
        cursor.close()
        conn.close()
        return results
        
    except Exception as e:
        logger.error(f"[RESYNC] Error EDARSAHUB: {e}")
        raise


# =============================================================================
# SCHEMAS
# =============================================================================

class ResyncValidateRequest(BaseModel):
    """Request para validar re-sync antes de ejecutar."""
    tipo_sync: str = Field(..., description="Código del tipo de sync (comercial_ventas_cerradas)")
    unidad_negocio_id: str = Field(..., description="ID canónico de la unidad (CIENFUEGOS, 130MID, etc)")
    fecha_inicio: date = Field(..., description="Fecha inicio del rango")
    fecha_fin: date = Field(..., description="Fecha fin del rango")


class ResyncExecuteRequest(BaseModel):
    """Request para ejecutar re-sync."""
    tipo_sync: str = Field(..., description="Código del tipo de sync")
    unidad_negocio_id: str = Field(..., description="ID canónico de la unidad")
    fecha_inicio: date = Field(..., description="Fecha inicio del rango")
    fecha_fin: date = Field(..., description="Fecha fin del rango")
    motivo: str = Field(..., min_length=10, description="Motivo obligatorio (mín 10 caracteres)")
    dry_run: bool = Field(True, description="True=simular sin modificar, False=ejecutar real")


class ResyncResponse(BaseModel):
    """Response de re-sync."""
    success: bool
    ejecucion_id: str
    sync_run_id: str
    modo: str  # DRY_RUN o REAL
    tipo_sync: str
    unidad_negocio_id: str
    fecha_inicio: str
    fecha_fin: str
    validacion_previa: Dict[str, Any]
    resultado: Optional[Dict[str, Any]] = None
    validacion_posterior: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# =============================================================================
# CONFIGURACIÓN DE TIPOS DE SYNC Y UNIDADES
# =============================================================================

# Tipos de sync soportados
TIPOS_SYNC = {
    'comercial_ventas_cerradas': {
        'codigo': 'comercial_ventas_cerradas',
        'nombre': 'Sincronización Ventas Cerradas',
        'modulo': 'Comercial',
        'descripcion': 'Sincroniza cheques cerrados desde SoftRestaurant/MPRO hacia Comercial_KPIs_Diarios_v2',
        'handler': 'sync_softrestaurant_ventas_cerradas',
        'tabla_destino': 'Comercial_KPIs_Diarios_v2',
        'tabla_log': 'Comercial_SyncLog_v2',
        'sistemas_origen': ['SOFTRESTAURANT', 'MPRO'],
        'permite_resync': True,
        'permite_dry_run': True,
        'requiere_unidad': True,
        'requiere_rango_fechas': True,
        'rango_max_dias': 30,
        'nivel_riesgo': 'MEDIO',
        'separa_propinas': True,
        'campo_venta_sin_propina': 'ventas_sin_propina'
    }
}

# Unidades de negocio - RESUELTAS DINAMICAMENTE desde catalogo central
# NO USAR HARDCODES - usar get_server_by_unidad_codigo()
UNIDADES_CONFIG = {}  # Deprecated - usar _get_unidad_config() que consulta BD


def _get_tipo_sync_config(codigo: str) -> Optional[Dict[str, Any]]:
    """Obtiene configuración del tipo de sync."""
    return TIPOS_SYNC.get(codigo)


def _get_unidad_config(unidad_negocio_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene configuración de la unidad desde catálogo central.
    USA get_server_by_unidad_codigo() - NO hardcodes.
    """
    try:
        server_data = get_server_by_unidad_codigo(unidad_negocio_id)
        if not server_data:
            logger.warning(f"[RESYNC] Unidad {unidad_negocio_id} no encontrada en catálogo central")
            return None
        
        return {
            'server_id': str(server_data.get('server_id', '')),
            'sistema': server_data.get('servidor_system_type') or server_data.get('system_type') or 'UNKNOWN',
            'sucursal_id': server_data.get('sucursal_origen_id') or server_data.get('sucursal_id') or 'DEFAULT',
            'nombre': server_data.get('unidad_negocio_nombre') or unidad_negocio_id,
            'host': server_data.get('host'),
            'activo': server_data.get('servidor_activo', True)
        }
    except Exception as e:
        logger.error(f"[RESYNC] Error obteniendo config unidad {unidad_negocio_id}: {e}")
        return None


# =============================================================================
# VALIDACIONES
# =============================================================================

def _validar_conectividad(server_id: str) -> Dict[str, Any]:
    """
    Valida conectividad al servidor origen usando el mismo método que el sync oficial.
    
    NOTA: Este pod de preview puede no tener la misma conectividad de red que
    el entorno de producción. Si la validación falla aquí pero el scheduler
    de producción sí sincroniza, es probable un issue de red del ambiente.
    """
    try:
        from modules.comercial_v2.sync_comercial_edarsahub import (
            get_server_connection_config,
            execute_query_on_server,
            ConnectionStatus
        )
        
        config = get_server_connection_config(server_id)
        
        if not config:
            return {'conectado': False, 'error': 'Servidor no encontrado en Servidores_Conexiones'}
        
        if not config.get('activo'):
            return {'conectado': False, 'error': 'Servidor marcado como inactivo'}
        
        # Usar el mismo método que el sync oficial para validar conectividad
        test_query = "SELECT 1 AS test"
        _, conn_status = execute_query_on_server(config, test_query)
        
        if conn_status == ConnectionStatus.ONLINE:
            return {
                'conectado': True,
                'host': config.get('host'),
                'host_raw': config.get('host_raw'),
                'database': config.get('database_name'),
                'config_origin': 'Servidores_Conexiones'
            }
        else:
            # Verificar si hay syncs recientes exitosos (otro ambiente tiene conectividad)
            recent_sync_ok = _verificar_syncs_recientes(server_id)
            
            return {
                'conectado': False, 
                'error': f'Conexión fallida desde este ambiente: {conn_status}',
                'host': config.get('host'),
                'host_raw': config.get('host_raw'),
                'syncs_recientes_exitosos': recent_sync_ok,
                'nota': 'Si hay syncs recientes exitosos, el servidor está UP pero este ambiente no tiene conectividad de red'
            }
            
    except Exception as e:
        return {'conectado': False, 'error': str(e)[:200]}


def _verificar_syncs_recientes(server_id: str, minutos: int = 30) -> bool:
    """Verifica si hubo syncs exitosos recientes para este servidor."""
    try:
        query = f"""
        SELECT TOP 1 source_connection_status
        FROM Comercial_SyncLog_v2
        WHERE server_id = '{server_id}'
          AND source_connection_status = 'ONLINE'
          AND created_at > DATEADD(MINUTE, -{minutos}, GETUTCDATE())
        ORDER BY created_at DESC
        """
        resultado = _execute_edarsahub_query(query)
        return len(resultado) > 0
    except Exception:
        return False


def _validar_dias_existentes(unidad_negocio_id: str, fecha_inicio: date, fecha_fin: date) -> Dict[str, Any]:
    """Valida qué días ya existen en destino."""
    try:
        query = f"""
        SELECT 
            fecha_operacion,
            ventas_total,
            ventas_sin_propina,
            propinas_total,
            tickets_total,
            sync_run_id
        FROM Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id = '{unidad_negocio_id}'
          AND fecha_operacion BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
          AND activo = 1
        ORDER BY fecha_operacion
        """
        
        resultado = _execute_edarsahub_query(query)
        
        return {
            'dias_existentes': [
                {
                    'fecha': str(r['fecha_operacion']),
                    'ventas_total': float(r['ventas_total'] or 0),
                    'ventas_sin_propina': float(r['ventas_sin_propina'] or 0),
                    'propinas': float(r.get('propinas_total') or 0),
                    'tickets': int(r.get('tickets_total') or 0),
                    'sync_run_id': r.get('sync_run_id')
                }
                for r in resultado
            ],
            'cantidad': len(resultado)
        }
    except Exception as e:
        return {'error': str(e), 'dias_existentes': [], 'cantidad': 0}


def _validar_rango(fecha_inicio: date, fecha_fin: date, max_dias: int) -> Dict[str, Any]:
    """Valida que el rango no exceda el máximo."""
    dias = (fecha_fin - fecha_inicio).days + 1
    
    return {
        'dias_solicitados': dias,
        'max_permitido': max_dias,
        'valido': dias <= max_dias,
        'mensaje': f"Rango de {dias} días" + (f" (máximo: {max_dias})" if dias > max_dias else "")
    }


# =============================================================================
# REGISTRO DE EJECUCIONES
# =============================================================================

def _registrar_en_bitacora(
    job_name: str,
    run_id: str,
    accion: str,
    server_id: str = None,
    detalles: Dict = None,
    exito: bool = True,
    error_mensaje: str = None
) -> bool:
    """Registra la ejecución en Scheduler_BitacoraJobs."""
    try:
        detalles_json = json.dumps(detalles, default=str) if detalles else None
        
        query = """
        INSERT INTO Scheduler_BitacoraJobs (
            JobName, RunID, Accion, ServerID, DetallesJSON, Exito, MensajeError
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        )
        """
        params = (
            job_name, run_id, accion, server_id,
            detalles_json,
            1 if exito else 0,
            error_mensaje[:500] if error_mensaje else None
        )
        
        _execute_edarsahub_query(query, params, fetch=False)
        return True
    except Exception as e:
        logger.error(f"[RESYNC] Error registrando bitácora: {e}")
        return False


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/resync/validate")
async def validar_resync(
    request: ResyncValidateRequest,
    current_user: dict = Depends(require_permission("SCHEDULER_ADMIN"))
):
    """
    Valida parámetros de re-sincronización antes de ejecutar.
    Solo lectura, no modifica datos.
    
    Permisos: SCHEDULER_ADMIN
    """
    logger.info(f"[RESYNC] Validando: {request.tipo_sync} / {request.unidad_negocio_id} / {request.fecha_inicio} a {request.fecha_fin}")
    
    # Validar tipo_sync
    tipo_sync = _get_tipo_sync_config(request.tipo_sync)
    if not tipo_sync:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de sync '{request.tipo_sync}' no encontrado. Disponibles: {list(TIPOS_SYNC.keys())}"
        )
    
    if not tipo_sync.get('permite_resync'):
        raise HTTPException(status_code=400, detail=f"Tipo de sync '{request.tipo_sync}' no permite re-sincronización")
    
    # Validar unidad usando catálogo central
    unidad = _get_unidad_config(request.unidad_negocio_id)
    if not unidad:
        raise HTTPException(
            status_code=400, 
            detail=f"Unidad '{request.unidad_negocio_id}' no encontrada en catálogo central. Verificar Unidades_Negocio + Servidores_Conexiones."
        )
    
    # Validar rango
    validacion_rango = _validar_rango(
        request.fecha_inicio, 
        request.fecha_fin, 
        tipo_sync.get('rango_max_dias', 30)
    )
    
    if not validacion_rango['valido']:
        raise HTTPException(status_code=400, detail=validacion_rango['mensaje'])
    
    # Validar conectividad
    validacion_conectividad = _validar_conectividad(unidad['server_id'])
    
    # Validar días existentes
    validacion_dias = _validar_dias_existentes(
        request.unidad_negocio_id,
        request.fecha_inicio,
        request.fecha_fin
    )
    
    return {
        'success': True,
        'source': 'EDARSAHUB_SQL',
        'tipo_sync': tipo_sync,
        'unidad': {
            'id': request.unidad_negocio_id,
            'nombre': unidad['nombre'],
            'server_id': unidad['server_id'],
            'sistema': unidad['sistema']
        },
        'rango': validacion_rango,
        'conectividad': validacion_conectividad,
        'dias_existentes': validacion_dias,
        'permite_dry_run': tipo_sync.get('permite_dry_run', True),
        'nivel_riesgo': tipo_sync.get('nivel_riesgo', 'MEDIO'),
        'propinas_separadas': tipo_sync.get('separa_propinas', False),
        'campo_venta_sin_propina': tipo_sync.get('campo_venta_sin_propina')
    }


@router.post("/resync/execute", response_model=ResyncResponse)
async def ejecutar_resync(
    request: ResyncExecuteRequest,
    current_user: dict = Depends(require_permission("SCHEDULER_ADMIN"))
):
    """
    Ejecuta re-sincronización controlada.
    
    MÁXIMAS CUMPLIDAS:
    - Usa handler oficial (#3, #26)
    - Motivo obligatorio (#7)
    - Dry run disponible (#8)
    - Trazabilidad completa (#6)
    - Credenciales desde EDARSAHUB (#14)
    - UPSERT idempotente (#15)
    - Propinas separadas (#31)
    
    Permisos: SCHEDULER_ADMIN
    """
    start_time = time.time()
    
    user_email = current_user.get('email', 'unknown')
    
    logger.info(f"[RESYNC] Usuario: {user_email}")
    logger.info(f"[RESYNC] Ejecutando: {request.tipo_sync} / {request.unidad_negocio_id}")
    logger.info(f"[RESYNC] Rango: {request.fecha_inicio} a {request.fecha_fin}")
    logger.info(f"[RESYNC] Modo: {'DRY_RUN' if request.dry_run else 'REAL'}")
    logger.info(f"[RESYNC] Motivo: {request.motivo}")
    
    # Validaciones previas
    tipo_sync = _get_tipo_sync_config(request.tipo_sync)
    if not tipo_sync:
        raise HTTPException(status_code=400, detail=f"Tipo de sync '{request.tipo_sync}' no encontrado")
    
    unidad = _get_unidad_config(request.unidad_negocio_id)
    if not unidad:
        raise HTTPException(status_code=400, detail=f"Unidad '{request.unidad_negocio_id}' no encontrada")
    
    # Generar IDs
    ejecucion_id = str(uuid.uuid4())
    sync_run_id = f"RESYNC-{request.unidad_negocio_id}-{request.fecha_inicio.strftime('%Y%m%d')}-{request.fecha_fin.strftime('%Y%m%d')}-{str(uuid.uuid4())[:4]}"
    
    # Validación previa
    validacion_previa = {
        'conectividad': _validar_conectividad(unidad['server_id']),
        'dias_existentes': _validar_dias_existentes(
            request.unidad_negocio_id,
            request.fecha_inicio,
            request.fecha_fin
        )
    }
    
    # Si no hay conectividad desde este ambiente
    conectividad = validacion_previa['conectividad']
    if not conectividad.get('conectado'):
        # Verificar si hay syncs recientes exitosos (servidor está UP, solo este ambiente no conecta)
        syncs_recientes = conectividad.get('syncs_recientes_exitosos', False)
        
        if syncs_recientes:
            # El servidor está UP pero este ambiente no tiene red
            error_msg = (
                f"Este ambiente de preview no tiene conectividad de red hacia el servidor. "
                f"PERO el servidor está ONLINE (hay syncs exitosos recientes). "
                f"El resync debe ejecutarse desde el entorno de producción o un ambiente con conectividad adecuada."
            )
            accion = 'RESYNC_AMBIENTE_SIN_RED'
        else:
            error_msg = f"Sin conectividad: {conectividad.get('error')}"
            accion = 'RESYNC_FAILED'
        
        _registrar_en_bitacora(
            job_name=f"RESYNC_{request.tipo_sync}",
            run_id=sync_run_id,
            accion=accion,
            server_id=unidad['server_id'],
            detalles={
                'unidad': request.unidad_negocio_id,
                'fecha_inicio': str(request.fecha_inicio),
                'fecha_fin': str(request.fecha_fin),
                'motivo': request.motivo,
                'dry_run': request.dry_run,
                'usuario': user_email,
                'syncs_recientes_exitosos': syncs_recientes,
                'servidor_status': 'ONLINE_PERO_AMBIENTE_SIN_RED' if syncs_recientes else 'OFFLINE_O_INACCESIBLE'
            },
            exito=False,
            error_mensaje=error_msg
        )
        
        return ResyncResponse(
            success=False,
            ejecucion_id=ejecucion_id,
            sync_run_id=sync_run_id,
            modo='DRY_RUN' if request.dry_run else 'REAL',
            tipo_sync=request.tipo_sync,
            unidad_negocio_id=request.unidad_negocio_id,
            fecha_inicio=request.fecha_inicio.isoformat(),
            fecha_fin=request.fecha_fin.isoformat(),
            validacion_previa=validacion_previa,
            error_message=error_msg
        )
    
    # Si es dry_run, simular
    if request.dry_run:
        resultado_simulado = await _ejecutar_dry_run(
            request.unidad_negocio_id,
            unidad,
            request.fecha_inicio,
            request.fecha_fin
        )
        
        _registrar_en_bitacora(
            job_name=f"RESYNC_{request.tipo_sync}",
            run_id=sync_run_id,
            accion='DRY_RUN_SUCCESS',
            server_id=unidad['server_id'],
            detalles={
                'unidad': request.unidad_negocio_id,
                'fecha_inicio': str(request.fecha_inicio),
                'fecha_fin': str(request.fecha_fin),
                'motivo': request.motivo,
                'registros_encontrados': resultado_simulado.get('records_processed', 0),
                'usuario': user_email
            },
            exito=True
        )
        
        return ResyncResponse(
            success=True,
            ejecucion_id=ejecucion_id,
            sync_run_id=sync_run_id,
            modo='DRY_RUN',
            tipo_sync=request.tipo_sync,
            unidad_negocio_id=request.unidad_negocio_id,
            fecha_inicio=request.fecha_inicio.isoformat(),
            fecha_fin=request.fecha_fin.isoformat(),
            validacion_previa=validacion_previa,
            resultado=resultado_simulado
        )
    
    # Ejecución REAL usando handler oficial
    resultado = await _ejecutar_sync_real(
        request.unidad_negocio_id,
        unidad,
        request.fecha_inicio,
        request.fecha_fin,
        sync_run_id
    )
    
    # Validación posterior
    validacion_posterior = {
        'dias_existentes': _validar_dias_existentes(
            request.unidad_negocio_id,
            request.fecha_inicio,
            request.fecha_fin
        )
    }
    
    duracion_ms = int((time.time() - start_time) * 1000)
    
    _registrar_en_bitacora(
        job_name=f"RESYNC_{request.tipo_sync}",
        run_id=sync_run_id,
        accion='RESYNC_REAL_SUCCESS' if resultado.get('success') else 'RESYNC_REAL_FAILED',
        server_id=unidad['server_id'],
        detalles={
            'unidad': request.unidad_negocio_id,
            'fecha_inicio': str(request.fecha_inicio),
            'fecha_fin': str(request.fecha_fin),
            'motivo': request.motivo,
            'resultado': resultado,
            'duracion_ms': duracion_ms,
            'usuario': user_email
        },
        exito=resultado.get('success', False),
        error_mensaje=resultado.get('error_message')
    )
    
    logger.info(f"[RESYNC] Completado: {resultado}")
    
    return ResyncResponse(
        success=resultado.get('success', False),
        ejecucion_id=ejecucion_id,
        sync_run_id=sync_run_id,
        modo='REAL',
        tipo_sync=request.tipo_sync,
        unidad_negocio_id=request.unidad_negocio_id,
        fecha_inicio=request.fecha_inicio.isoformat(),
        fecha_fin=request.fecha_fin.isoformat(),
        validacion_previa=validacion_previa,
        resultado=resultado,
        validacion_posterior=validacion_posterior,
        error_message=resultado.get('error_message')
    )


@router.get("/resync/history")
async def obtener_historial_resync(
    tipo_sync: Optional[str] = None,
    unidad_negocio_id: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(require_permission("SCHEDULER_VER"))
):
    """
    Obtiene historial de re-sincronizaciones.
    
    Permisos: SCHEDULER_VER
    """
    try:
        where_clauses = ["JobName LIKE 'RESYNC_%'"]
        if tipo_sync:
            where_clauses.append(f"JobName = 'RESYNC_{tipo_sync}'")
        
        query = f"""
        SELECT TOP {limit}
            ID,
            JobName,
            RunID,
            Accion,
            FechaAccion,
            ServerID,
            DetallesJSON,
            Exito,
            MensajeError
        FROM Scheduler_BitacoraJobs
        WHERE {' AND '.join(where_clauses)}
        ORDER BY FechaAccion DESC
        """
        
        resultado = _execute_edarsahub_query(query)
        
        # Parsear JSON de detalles
        ejecuciones = []
        for r in resultado:
            detalles = {}
            if r.get('DetallesJSON'):
                try:
                    detalles = json.loads(r['DetallesJSON'])
                except:
                    detalles = {}
            
            # Filtrar por unidad si se especificó
            if unidad_negocio_id and detalles.get('unidad') != unidad_negocio_id:
                continue
            
            ejecuciones.append({
                'id': r.get('ID'),
                'job_name': r.get('JobName'),
                'run_id': r.get('RunID'),
                'accion': r.get('Accion'),
                'fecha': str(r.get('FechaAccion')),
                'server_id': r.get('ServerID'),
                'exito': bool(r.get('Exito')),
                'error': r.get('MensajeError'),
                'detalles': detalles
            })
        
        return {
            'success': True,
            'source': 'EDARSAHUB_SQL',
            'ejecuciones': ejecuciones[:limit],
            'total': len(ejecuciones)
        }
        
    except Exception as e:
        logger.error(f"[RESYNC] Error obteniendo historial: {e}")
        return {'success': False, 'ejecuciones': [], 'total': 0, 'error': str(e)}


@router.get("/resync/options")
async def obtener_opciones_resync(
    current_user: dict = Depends(require_permission("SCHEDULER_VER"))
):
    """
    Obtiene las opciones disponibles para re-sync.
    
    Permisos: SCHEDULER_VER
    """
    # Obtener unidades desde catálogo central
    unidades_list = []
    try:
        query = """
        SELECT 
            u.codigo,
            u.nombre,
            s.system_type AS sistema
        FROM Unidades_Negocio u
        INNER JOIN Servidores_Conexiones s ON s.id = u.server_id
        WHERE ISNULL(u.activo, 1) = 1
          AND ISNULL(s.activo, 1) = 1
        ORDER BY u.codigo
        """
        resultado = _execute_edarsahub_query(query)
        for r in resultado:
            unidades_list.append({
                'id': r['codigo'],
                'nombre': r['nombre'],
                'sistema': r['sistema'] or 'UNKNOWN'
            })
    except Exception as e:
        logger.error(f"[RESYNC] Error obteniendo unidades: {e}")
    
    return {
        'success': True,
        'source': 'EDARSAHUB_SQL',
        'tipos_sync': [
            {
                'codigo': k,
                'nombre': v['nombre'],
                'modulo': v['modulo'],
                'descripcion': v['descripcion'],
                'permite_resync': v['permite_resync'],
                'permite_dry_run': v['permite_dry_run'],
                'rango_max_dias': v['rango_max_dias'],
                'nivel_riesgo': v['nivel_riesgo']
            }
            for k, v in TIPOS_SYNC.items()
        ],
        'unidades': unidades_list
    }


# =============================================================================
# FUNCIONES DE EJECUCIÓN
# =============================================================================

async def _ejecutar_dry_run(
    unidad_negocio_id: str,
    unidad_config: Dict[str, Any],
    fecha_inicio: date,
    fecha_fin: date
) -> Dict[str, Any]:
    """
    Ejecuta simulación de sync (extrae datos pero NO escribe).
    P2-21: Usa catálogo central de queries.
    """
    from modules.comercial_v2.sync_comercial_edarsahub import get_server_connection_config
    from core.query_catalog import get_query_for_server
    import pymssql
    
    try:
        config = get_server_connection_config(unidad_config['server_id'])
        
        if not config:
            return {'success': False, 'error_message': 'Config de servidor no encontrada'}
        
        # P2-21: Obtener query desde catálogo central
        query_template = get_query_for_server(config, 'comercial_ventas_cerradas')
        
        if not query_template:
            # Fallback a queries legacy si no está en catálogo
            sistema = unidad_config.get('sistema', '').upper()
            if 'SOFT' in sistema:
                query_template = """
                SELECT 
                    CAST(fecha AS DATE) AS fecha_operacion,
                    SUM(total) AS ventas_total,
                    SUM(total - ISNULL(propina, 0)) AS ventas_sin_propina,
                    SUM(ISNULL(propina, 0)) AS propinas_total,
                    COUNT(DISTINCT folio) AS tickets_total,
                    SUM(ISNULL(nopersonas, 1)) AS pax_total
                FROM cheques
                WHERE CAST(fecha AS DATE) BETWEEN @fecha_inicio AND @fecha_fin
                  AND cancelado = 0
                  AND cierre IS NOT NULL
                GROUP BY CAST(fecha AS DATE)
                ORDER BY fecha_operacion
                """
            else:  # MPRO
                query_template = """
                SELECT 
                    CAST(ve.Vn_Fecha AS DATE) AS fecha_operacion,
                    SUM(ve.Vn_Precio_Neto_Importe) AS ventas_total,
                    SUM(ve.Vn_Precio_Neto_Importe) AS ventas_sin_propina,
                    0 AS propinas_total,
                    COUNT(DISTINCT ve.Vn_Folio) AS tickets_total,
                    SUM(ISNULL(c.Co_Personas, 1)) AS pax_total
                FROM Venta_Encabezado ve
                LEFT JOIN Comanda c ON ve.Vn_Documento = c.Co_Folio AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
                WHERE CAST(ve.Vn_Fecha AS DATE) BETWEEN @fecha_inicio AND @fecha_fin
                  AND ve.Sc_Cve_Sucursal = @sucursal_id
                GROUP BY CAST(ve.Vn_Fecha AS DATE)
                ORDER BY fecha_operacion
                """
        
        # Reemplazar parámetros
        query = query_template.replace('@fecha_inicio', f"'{fecha_inicio}'")
        query = query.replace('@fecha_fin', f"'{fecha_fin}'")
        sucursal_id = unidad_config.get('sucursal_id', 'DEFAULT')
        query = query.replace('@sucursal_id', f"'{sucursal_id}'")
        
        conn = pymssql.connect(
            server=config['host'],
            port=config['port'],
            database=config['database_name'],
            user=config['username'],
            password=config['password'],
            login_timeout=30,
            tds_version="7.0"  # P2-22: Compatibilidad con SQL Server antiguos
        )
        cursor = conn.cursor(as_dict=True)
        
        cursor.execute(query)
        datos = cursor.fetchall()
        conn.close()
        
        detalle = []
        for d in datos:
            detalle.append({
                'fecha': str(d['fecha_operacion']),
                'accion': 'INSERT/UPDATE',
                'ventas_total': float(d['ventas_total'] or 0),
                'ventas_sin_propina': float(d['ventas_sin_propina'] or 0),
                'propinas_total': float(d['propinas_total'] or 0),
                'tickets_total': int(d['tickets_total'] or 0),
                'pax_total': int(d['pax_total'] or 0)
            })
        
        return {
            'success': True,
            'modo': 'DRY_RUN',
            'mensaje': 'Simulación completada - NO se modificaron datos',
            'records_processed': len(detalle),
            'registros_que_se_sincronizarian': len(detalle),
            'registros_extraidos': len(detalle),
            'registros_afectados': 0,
            'query_source': 'CATALOGO' if get_query_for_server(config, 'comercial_ventas_cerradas') else 'LEGACY_FALLBACK',
            'detalle': detalle
        }
        
    except Exception as e:
        return {'success': False, 'error_message': str(e)}


async def _ejecutar_sync_real(
    unidad_negocio_id: str,
    unidad_config: Dict[str, Any],
    fecha_inicio: date,
    fecha_fin: date,
    sync_run_id: str
) -> Dict[str, Any]:
    """
    Ejecuta sync real usando el handler oficial.
    MÁXIMA #26: No duplicar lógica, usar handler oficial.
    """
    try:
        from modules.comercial_v2.sync_comercial_edarsahub import (
            sync_softrestaurant_ventas_cerradas,
            sync_mpro_ventas_cerradas
        )
        from modules.comercial_v2.schemas import (
            UnidadNegocioConfig,
            SistemaOrigen
        )
        
        # Crear config usando el formato oficial
        config = UnidadNegocioConfig(
            unidad_negocio_id=unidad_negocio_id,
            unidad_negocio_nombre=unidad_config['nombre'],
            server_id=unidad_config['server_id'],
            sucursal_id=unidad_config['sucursal_id'],
            sucursal_nombre=unidad_config['nombre'],
            sistema_origen=SistemaOrigen.SOFTRESTAURANT if unidad_config['sistema'] == 'SOFTRESTAURANT' else SistemaOrigen.MPRO,
            activo=True
        )
        
        # Ejecutar handler oficial según sistema
        if unidad_config['sistema'] == 'SOFTRESTAURANT':
            resultado = sync_softrestaurant_ventas_cerradas(
                config=config,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                run_id=sync_run_id
            )
        else:  # MPRO
            resultado = sync_mpro_ventas_cerradas(
                config=config,
                sucursal_id=unidad_config['sucursal_id'],
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                run_id=sync_run_id
            )
        
        return {
            'success': resultado.success,
            'records_processed': resultado.records_processed,
            'records_inserted': resultado.records_inserted,
            'records_updated': resultado.records_updated,
            'records_skipped': resultado.records_skipped,
            'records_errored': resultado.records_errored,
            'duration_seconds': resultado.duration_seconds,
            'error_message': resultado.error_message
        }
        
    except Exception as e:
        logger.error(f"[RESYNC] Error en sync real: {e}")
        return {'success': False, 'error_message': str(e)}
