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

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import date, datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import uuid
import time
import logging
import json

from core.security import get_current_user
from core.rbac.middleware import require_permission, require_explicit_permission
from core.server_registry import get_server_by_unidad_codigo
from core.system_type_utils import normalize_system_type

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/scheduler", tags=["Admin - Scheduler Resync"])


# =============================================================================
# CONFIGURACIÓN EDARSAHUB - USA VARIABLES DE ENTORNO
# =============================================================================

import os
from core.sql_first.db import get_sql_connection

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
        conn = get_sql_connection()
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
    detail_only: bool = Field(False, description="True=sincronizar solo detalle ISCAM sin reconsultar/regrabar el header comercial")


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
        'handler_implementado': True
    }
}

# Unidades de negocio - RESUELTAS DINAMICAMENTE desde catalogo central
# NO USAR HARDCODES - usar get_server_by_unidad_codigo()
UNIDADES_CONFIG = {}  # Deprecated - usar _get_unidad_config() que consulta BD


def _get_tipo_sync_config(codigo: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene configuración del tipo de sync.
    Fuente: catálogo canónico SQL (dbo.Sistema_Sync_Catalogo). Para el handler
    real existente se conserva la config de TIPOS_SYNC (que incluye campos
    específicos como separa_propinas).
    """
    if codigo in TIPOS_SYNC:
        return TIPOS_SYNC[codigo]
    try:
        from modules.sistema.sync_catalogo_service import get_tipo
        return get_tipo(codigo)
    except Exception as e:
        logger.error(f"[RESYNC] Error leyendo catálogo para '{codigo}': {e}")
        return None


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
        
        raw_sistema = str(
            server_data.get('servidor_system_type')
            or server_data.get('system_type')
            or 'UNKNOWN'
        ).strip().upper()
        if 'SOFT' in raw_sistema:
            sistema = 'SOFTRESTAURANT'
        elif 'MPRO' in raw_sistema or 'MANAG' in raw_sistema:
            sistema = 'MPRO'
        else:
            sistema = raw_sistema or 'UNKNOWN'

        return {
            'unidad_negocio_pk': str(server_data.get('unidad_negocio_pk', '')),
            'server_id': str(server_data.get('server_id', '')),
            'sistema': sistema,
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

def _validar_conectividad(
    server_id: str,
    unidad_negocio_pk: Optional[str] = None,
) -> Dict[str, Any]:
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
        
        config = get_server_connection_config(
            server_id,
            unidad_negocio_pk,
        )
        
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


NETPAY_REPORT_TYPES_BY_SYNC = {
    'finanzas_netpay': None,
    'finanzas_netpay_transacciones': ('DETALLE_TRANSACCIONES',),
    'finanzas_netpay_depositos': ('DETALLE_DEPOSITOS_MOVIMIENTOS',),
}


def _is_netpay_sync(tipo_sync: Dict[str, Any], codigo: str) -> bool:
    """Identifica el handler NetPay sin mezclarlo con conectores POS/SoftRestaurant/MPRO."""
    handler = (tipo_sync or {}).get('handler') or (tipo_sync or {}).get('Handler') or ''
    return codigo in NETPAY_REPORT_TYPES_BY_SYNC or handler == 'netpay_manual_background'


def _get_netpay_report_types(codigo: str):
    return NETPAY_REPORT_TYPES_BY_SYNC.get(codigo)


async def _run_netpay_resync_background(fecha_inicio: date, fecha_fin: date, report_types=None) -> None:
    """Ejecuta NetPay desde scheduler central en background; no usa Mongo ni conexiones POS live."""
    from core.scheduler.jobs.netpay_sync_job import execute_netpay_sync_diario

    try:
        result = await execute_netpay_sync_diario(
            date_from=fecha_inicio,
            date_to=fecha_fin,
            max_days=31,
            report_types=report_types,
        )
        logger.info(
            "[RESYNC_NETPAY_BG] Finalizado success=%s fecha_inicio=%s fecha_fin=%s message=%s",
            result.get("success"),
            fecha_inicio.isoformat(),
            fecha_fin.isoformat(),
            result.get("message"),
        )
    except Exception as e:
        logger.error(f"[RESYNC_NETPAY_BG] Error ejecutando NetPay: {e}")




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
    current_user: dict = Depends(require_explicit_permission("SCHEDULER_ADMIN"))
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

    if _is_netpay_sync(tipo_sync, request.tipo_sync):
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
            'conectividad': {
                'conectado': True,
                'tipo': 'NETPAY_PORTAL_ROBOT',
                'nota': 'NetPay no usa conectividad POS/SoftRestaurant/MPRO; se ejecuta por portal NetPay y persiste en SQL canónico.'
            },
            'dias_existentes': {
                'dias_existentes': [],
                'cantidad': 0,
                'nota': 'Validación NetPay sin consulta a tablas comerciales POS.'
            },
            'permite_dry_run': tipo_sync.get('permite_dry_run', True),
            'nivel_riesgo': tipo_sync.get('nivel_riesgo', 'MEDIO'),
            'propinas_separadas': False,
            'campo_venta_sin_propina': None
        }
    
    # Validar conectividad
    validacion_conectividad = _validar_conectividad(
        unidad['server_id'],
        unidad.get('unidad_negocio_pk'),
    )
    
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



def _registrar_resync_log(request, current_user, estado: str, mensaje: str, unidad: dict = None, registros: int = None):
    """Registra el resultado de un re-sync en Sistema_Sync_ResyncLog (para bandeja de tareas + reintento)."""
    try:
        import json as _json
        from core.sql_first.db import get_edarsahub_connection as _get_conn
        server_id = (unidad or {}).get('server_id') if unidad else None
        payload = _json.dumps({
            "tipo_sync": request.tipo_sync,
            "unidad_negocio_id": request.unidad_negocio_id,
            "fecha_inicio": str(getattr(request, 'fecha_inicio', '')),
            "fecha_fin": str(getattr(request, 'fecha_fin', '')),
            "motivo": getattr(request, 'motivo', None),
            "detail_only": bool(getattr(request, 'detail_only', False)),
        })
        conn = _get_conn(); cur = conn.cursor()
        cur.execute(
            """INSERT INTO dbo.Sistema_Sync_ResyncLog
               (TipoSync, ServerID, UnidadCodigo, Estado, Mensaje, Payload, RegistrosAfectados, SolicitadoPor)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (request.tipo_sync, str(server_id) if server_id else None, request.unidad_negocio_id,
             estado, (mensaje or "")[:1990], payload, registros, current_user.get('email', 'unknown')),
        )
        conn.commit(); conn.close()
    except Exception as _e:
        logger.warning(f"[RESYNC-LOG] No se pudo registrar: {_e}")


@router.post("/resync/execute", response_model=ResyncResponse)
async def ejecutar_resync(
    request: ResyncExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_explicit_permission("SCHEDULER_ADMIN"))
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

    validacion_rango = _validar_rango(
        request.fecha_inicio,
        request.fecha_fin,
        tipo_sync.get('rango_max_dias') or tipo_sync.get('RangoMaxDias') or 31,
    )
    if not validacion_rango['valido']:
        raise HTTPException(status_code=400, detail=validacion_rango['mensaje'])
    
    # Generar IDs
    ejecucion_id = str(uuid.uuid4())
    sync_run_id = f"RESYNC-{request.unidad_negocio_id}-{request.fecha_inicio.strftime('%Y%m%d')}-{request.fecha_fin.strftime('%Y%m%d')}-{str(uuid.uuid4())[:4]}"

    # ISCAM detalle-only: cuando el header canónico ya está actualizado no se debe
    # bloquear la reparación del detalle por la conectividad del DRY RUN del header.
    # El backfill mantiene su propia validación contra Runtime V2 y solo escribe días
    # que cuadran; commit=False sigue siendo estrictamente de solo lectura.
    if request.detail_only:
        if request.tipo_sync != 'comercial_ventas_cerradas':
            raise HTTPException(status_code=400, detail='detail_only solo aplica a comercial_ventas_cerradas')

        resultado_detalle = _ejecutar_backfill_detalle_iscam(
            request.unidad_negocio_id,
            request.fecha_inicio,
            request.fecha_fin,
            commit=not request.dry_run,
        )
        resumen_detalle = resultado_detalle.get('resumen') or {}
        registros_detalle = int(
            resumen_detalle.get('filas_insertadas')
            or resumen_detalle.get('dias_reparables')
            or 0
        )
        accion_detalle = (
            'ISCAM_DETAIL_DRY_RUN_SUCCESS' if request.dry_run and resultado_detalle.get('success')
            else 'ISCAM_DETAIL_DRY_RUN_FAILED' if request.dry_run
            else 'ISCAM_DETAIL_REAL_SUCCESS' if resultado_detalle.get('success')
            else 'ISCAM_DETAIL_REAL_FAILED'
        )
        _registrar_en_bitacora(
            job_name='RESYNC_ISCAM_DETAIL',
            run_id=sync_run_id,
            accion=accion_detalle,
            server_id=unidad.get('server_id', ''),
            detalles={
                'unidad': request.unidad_negocio_id,
                'fecha_inicio': str(request.fecha_inicio),
                'fecha_fin': str(request.fecha_fin),
                'motivo': request.motivo,
                'dry_run': request.dry_run,
                'detail_only': True,
                'header_resync_skipped': True,
                'usuario': user_email,
                'resultado': resultado_detalle,
            },
            exito=bool(resultado_detalle.get('success')),
            error_mensaje=resultado_detalle.get('error_message'),
        )
        _registrar_resync_log(
            request,
            current_user,
            'SUCCESS' if resultado_detalle.get('success') else 'FAILED',
            resultado_detalle.get('error_message')
            or ('Detalle ISCAM sincronizado' if not request.dry_run else 'DRY RUN detalle ISCAM aprobado'),
            unidad,
            registros_detalle,
        )
        return ResyncResponse(
            success=bool(resultado_detalle.get('success')),
            ejecucion_id=ejecucion_id,
            sync_run_id=sync_run_id,
            modo='DRY_RUN' if request.dry_run else 'REAL',
            tipo_sync=request.tipo_sync,
            unidad_negocio_id=request.unidad_negocio_id,
            fecha_inicio=request.fecha_inicio.isoformat(),
            fecha_fin=request.fecha_fin.isoformat(),
            validacion_previa={
                'rango': validacion_rango,
                'detail_only': True,
                'header_resync_skipped': True,
            },
            resultado=resultado_detalle,
            error_message=resultado_detalle.get('error_message'),
        )

    if _is_netpay_sync(tipo_sync, request.tipo_sync):
        modo = 'DRY_RUN' if request.dry_run else 'REAL'
        report_types = _get_netpay_report_types(request.tipo_sync)
        selected_report_types = list(report_types) if report_types else ['DETALLE_TRANSACCIONES', 'DETALLE_DEPOSITOS_MOVIMIENTOS']
        resultado = {
            'records_processed': 0,
            'records_inserted': 0,
            'records_updated': 0,
            'report_types': selected_report_types,
            'status': 'validated' if request.dry_run else 'accepted',
            'message': (
                'DRY RUN NetPay validado. No se descargaron archivos ni se modificó SQL.'
                if request.dry_run
                else 'Ejecución NetPay iniciada en segundo plano.'
            ),
        }

        if not request.dry_run:
            background_tasks.add_task(
                _run_netpay_resync_background,
                request.fecha_inicio,
                request.fecha_fin,
                report_types,
            )

        _registrar_en_bitacora(
            job_name=f"RESYNC_{request.tipo_sync}",
            run_id=sync_run_id,
            accion='DRY_RUN_SUCCESS' if request.dry_run else 'NETPAY_BACKGROUND_ACCEPTED',
            server_id=unidad.get('server_id', ''),
            detalles={
                'unidad': request.unidad_negocio_id,
                'fecha_inicio': str(request.fecha_inicio),
                'fecha_fin': str(request.fecha_fin),
                'motivo': request.motivo,
                'dry_run': request.dry_run,
                'usuario': user_email,
                'source': 'NETPAY_PORTAL_ROBOT_SQL_CANONICO',
                'report_types': selected_report_types,
            },
            exito=True,
        )

        return ResyncResponse(
            success=True,
            ejecucion_id=ejecucion_id,
            sync_run_id=sync_run_id,
            modo=modo,
            tipo_sync=request.tipo_sync,
            unidad_negocio_id=request.unidad_negocio_id,
            fecha_inicio=request.fecha_inicio.isoformat(),
            fecha_fin=request.fecha_fin.isoformat(),
            validacion_previa={
                'rango': validacion_rango,
                'netpay': True,
                'nota': 'NetPay no usa conectividad POS/SoftRestaurant/MPRO; usa portal NetPay y persistencia SQL canónica.',
            },
            resultado=resultado,
        )

    # GUARD HONESTO: tipo registrado en el catálogo canónico pero sin handler real
    # cableado todavía. No simulamos ni ejecutamos (sin mocks): estado PENDIENTE claro.
    if not tipo_sync.get('handler_implementado'):
        _registrar_en_bitacora(
            job_name=f"RESYNC_{request.tipo_sync}",
            run_id=sync_run_id,
            accion='HANDLER_NO_IMPLEMENTADO',
            server_id=(unidad or {}).get('server_id', ''),
            detalles={
                'unidad': request.unidad_negocio_id,
                'fecha_inicio': str(request.fecha_inicio),
                'fecha_fin': str(request.fecha_fin),
                'motivo': request.motivo,
                'dry_run': request.dry_run,
                'usuario': user_email,
            },
            exito=False,
            error_mensaje='Handler de re-sync no implementado'
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
            validacion_previa={'pendiente_handler': True},
            error_message=(
                f"El tipo '{tipo_sync.get('nombre', request.tipo_sync)}' está registrado en el "
                f"catálogo canónico, pero su handler de re-sincronización aún NO está implementado. "
                f"Disponible próximamente (sin simulación para no mostrar datos falsos)."
            )
        )

    # Validación previa
    validacion_previa = {
        'conectividad': _validar_conectividad(
            unidad['server_id'],
            unidad.get('unidad_negocio_pk'),
        ),
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
        
        _registrar_resync_log(request, current_user, "FAILED", error_msg, unidad)
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

        if not resultado_simulado.get('success'):
            error_msg = (
                resultado_simulado.get('error_message')
                or 'El DRY RUN no pudo consultar el servidor origen.'
            )
            _registrar_en_bitacora(
                job_name=f"RESYNC_{request.tipo_sync}",
                run_id=sync_run_id,
                accion='DRY_RUN_FAILED',
                server_id=unidad['server_id'],
                detalles={
                    'unidad': request.unidad_negocio_id,
                    'fecha_inicio': str(request.fecha_inicio),
                    'fecha_fin': str(request.fecha_fin),
                    'motivo': request.motivo,
                    'usuario': user_email,
                },
                exito=False,
                error_mensaje=error_msg,
            )
            _registrar_resync_log(
                request, current_user, 'FAILED', error_msg, unidad, 0
            )
            return ResyncResponse(
                success=False,
                ejecucion_id=ejecucion_id,
                sync_run_id=sync_run_id,
                modo='DRY_RUN',
                tipo_sync=request.tipo_sync,
                unidad_negocio_id=request.unidad_negocio_id,
                fecha_inicio=request.fecha_inicio.isoformat(),
                fecha_fin=request.fecha_fin.isoformat(),
                validacion_previa=validacion_previa,
                resultado=resultado_simulado,
                error_message=error_msg,
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
    
    _registrar_resync_log(
        request, current_user,
        "SUCCESS" if resultado.get('success') else "FAILED",
        resultado.get('error_message') or resultado.get('message') or ("OK" if resultado.get('success') else "Fallo en re-sync"),
        unidad,
        resultado.get('records_synced') or resultado.get('records_processed'),
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
                except Exception:
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
    
    # Tipos de sync desde el CATÁLOGO CANÓNICO (dbo.Sistema_Sync_Catalogo)
    tipos_sync = []
    catalogo_agrupado = []
    try:
        from modules.sistema.sync_catalogo_service import get_catalogo, get_catalogo_agrupado
        for t in get_catalogo(incluir_inactivos=False):
            tipos_sync.append({
                'codigo': t['codigo'],
                'nombre': t['nombre'],
                'grupo': t['grupo'],
                'modulo': t['grupo'],
                'descripcion': t['descripcion'],
                'permite_resync': t['permite_resync'],
                'permite_dry_run': t['permite_dry_run'],
                'requiere_unidad': t['requiere_unidad'],
                'requiere_rango_fechas': t['requiere_rango_fechas'],
                'rango_max_dias': t['rango_max_dias'],
                'nivel_riesgo': t['nivel_riesgo'],
                'handler_implementado': t['handler_implementado'],
                'dependencias': t['dependencias'],
            })
        catalogo_agrupado = get_catalogo_agrupado(incluir_inactivos=False)
    except Exception as e:
        logger.error(f"[RESYNC] Error leyendo catálogo canónico: {e}")

    return {
        'success': True,
        'source': 'EDARSAHUB_SQL',
        'tipos_sync': tipos_sync,
        'grupos': catalogo_agrupado,
        'unidades': unidades_list
    }


# =============================================================================
# CATÁLOGO CANÓNICO DE SINCRONIZACIONES (CRUD + RESOLVE DEPENDENCIAS)
# =============================================================================

class SyncTipoUpsert(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    grupo: Optional[str] = None
    descripcion: Optional[str] = None
    orden: Optional[int] = None
    nivel_riesgo: Optional[str] = None
    permite_resync: Optional[bool] = None
    permite_dry_run: Optional[bool] = None
    requiere_unidad: Optional[bool] = None
    requiere_rango_fechas: Optional[bool] = None
    rango_max_dias: Optional[int] = None
    handler: Optional[str] = None
    handler_implementado: Optional[bool] = None
    tabla_destino: Optional[str] = None
    dependencias: Optional[List[Dict[str, Any]]] = None
    activo: Optional[bool] = None


class ResolveRequest(BaseModel):
    codigos: List[str] = Field(..., description="Códigos seleccionados por el usuario")


@router.get("/resync/catalogo")
async def listar_catalogo_sync(
    incluir_inactivos: bool = False,
    current_user: dict = Depends(require_permission("SCHEDULER_VER"))
):
    """Lista el catálogo canónico de sincronizaciones, agrupado por tipo."""
    from modules.sistema.sync_catalogo_service import get_catalogo_agrupado, get_catalogo
    return {
        'success': True,
        'source': 'EDARSAHUB_SQL',
        'grupos': get_catalogo_agrupado(incluir_inactivos),
        'tipos': get_catalogo(incluir_inactivos),
    }


@router.post("/resync/retry/{log_id}")
def listar_resync_fallidos_pendientes(
    limite: int = 100,
) -> List[Dict[str, Any]]:
    """Lista re-sync fallidos pendientes de resolución."""
    safe_limit = max(1, min(int(limite), 500))

    rows = _execute_edarsahub_query(
        """
        SELECT TOP (%s)
            ResyncLogID,
            TipoSync,
            ServerID,
            UnidadCodigo,
            Estado,
            Mensaje,
            Payload,
            FechaEjecucion
        FROM dbo.Sistema_Sync_ResyncLog
        WHERE
            Estado = 'FAILED'
            AND ISNULL(Resuelto, 0) = 0
        ORDER BY FechaEjecucion DESC
        """,
        (safe_limit,),
        fetch=True,
    )

    return rows or []


async def reintentar_resync_fallido(
    log_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_explicit_permission("SCHEDULER_ADMIN"))
):
    """Reintenta un re-sync previamente FALLIDO (desde la bandeja Mis Tareas)."""
    import json as _json
    from datetime import date as _date, timedelta as _td
    from core.sql_first.db import get_edarsahub_connection as _get_conn

    conn = _get_conn(); cur = conn.cursor(as_dict=True)
    cur.execute("SELECT * FROM dbo.Sistema_Sync_ResyncLog WHERE ResyncLogID = %s", (log_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Registro de re-sync no encontrado")

    payload = _json.loads(row.get("Payload") or "{}")

    def _parse_fecha(v, default):
        try:
            return _date.fromisoformat(str(v)[:10])
        except Exception:
            return default

    hoy = _date.today()
    fi = _parse_fecha(payload.get("fecha_inicio"), hoy - _td(days=60))
    ff = _parse_fecha(payload.get("fecha_fin"), hoy)
    motivo_orig = payload.get("motivo") or ""
    motivo = f"Reintento desde Mis Tareas (log {log_id}). {motivo_orig}".strip()
    if len(motivo) < 10:
        motivo = f"Reintento manual de re-sync fallido (log {log_id})."

    req = ResyncExecuteRequest(
        tipo_sync=payload.get("tipo_sync") or row.get("TipoSync"),
        unidad_negocio_id=payload.get("unidad_negocio_id") or row.get("UnidadCodigo"),
        fecha_inicio=fi,
        fecha_fin=ff,
        motivo=motivo,
        dry_run=False,
    )

    resp = await ejecutar_resync(req, background_tasks, current_user)

    # Marcar el log original como resuelto si el reintento fue exitoso
    if getattr(resp, "success", False):
        try:
            conn2 = _get_conn(); cur2 = conn2.cursor()
            cur2.execute(
                """UPDATE dbo.Sistema_Sync_ResyncLog
                   SET Resuelto = 1, ResueltoPor = %s, FechaResuelto = SYSUTCDATETIME()
                   WHERE ResyncLogID = %s""",
                (current_user.get("email", "unknown"), log_id),
            )
            conn2.commit(); conn2.close()
        except Exception as _e:
            logger.warning(f"[RESYNC-RETRY] No se pudo marcar resuelto: {_e}")

    return resp



class RetryAllRequest(BaseModel):
    unidad_negocio_id: Optional[str] = None


@router.post("/resync/retry-all")
async def reintentar_todos_resync_fallidos(
    body: RetryAllRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_explicit_permission("SCHEDULER_ADMIN"))
):
    """Reintenta TODOS los re-syncs FALLIDOS no resueltos (opcionalmente de una unidad)."""
    from core.sql_first.db import get_edarsahub_connection as _get_conn

    conn = _get_conn(); cur = conn.cursor(as_dict=True)
    if body.unidad_negocio_id:
        cur.execute(
            "SELECT ResyncLogID FROM dbo.Sistema_Sync_ResyncLog WHERE Estado='FAILED' AND ISNULL(Resuelto,0)=0 AND UnidadCodigo=%s ORDER BY FechaEjecucion DESC",
            (body.unidad_negocio_id,),
        )
    else:
        cur.execute(
            "SELECT ResyncLogID FROM dbo.Sistema_Sync_ResyncLog WHERE Estado='FAILED' AND ISNULL(Resuelto,0)=0 ORDER BY FechaEjecucion DESC"
        )
    ids = [r["ResyncLogID"] for r in (cur.fetchall() or [])]
    conn.close()

    resultados = {"total": len(ids), "exitosos": 0, "fallidos": 0, "detalle": []}
    for lid in ids:
        try:
            resp = await reintentar_resync_fallido(lid, background_tasks, current_user)
            ok = bool(getattr(resp, "success", False))
            resultados["exitosos" if ok else "fallidos"] += 1
            resultados["detalle"].append({"log_id": lid, "success": ok})
        except Exception as e:
            resultados["fallidos"] += 1
            resultados["detalle"].append({"log_id": lid, "success": False, "error": str(e)[:200]})

    return {"success": resultados["fallidos"] == 0, **resultados}



@router.post("/resync/catalogo")
async def crear_tipo_sync(
    body: SyncTipoUpsert,
    current_user: dict = Depends(require_explicit_permission("SCHEDULER_ADMIN"))
):
    """Crea un nuevo tipo de sincronización canónico."""
    from modules.sistema.sync_catalogo_service import crear_tipo
    try:
        creado = crear_tipo(body.dict(exclude_none=True))
        return {'success': True, 'tipo': creado}
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")


@router.put("/resync/catalogo/{codigo}")
async def actualizar_tipo_sync(
    codigo: str,
    body: SyncTipoUpsert,
    current_user: dict = Depends(require_explicit_permission("SCHEDULER_ADMIN"))
):
    """Edita un tipo de sincronización canónico existente."""
    from modules.sistema.sync_catalogo_service import actualizar_tipo
    try:
        actualizado = actualizar_tipo(codigo, body.dict(exclude_none=True))
        return {'success': True, 'tipo': actualizado}
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Error interno del servidor")


@router.patch("/resync/catalogo/{codigo}/toggle")
async def toggle_tipo_sync(
    codigo: str,
    current_user: dict = Depends(require_explicit_permission("SCHEDULER_ADMIN"))
):
    """Activa/Inactiva un tipo de sincronización."""
    from modules.sistema.sync_catalogo_service import toggle_activo
    try:
        return {'success': True, 'tipo': toggle_activo(codigo)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Error interno del servidor")


@router.post("/resync/resolve")
async def resolver_dependencias_sync(
    body: ResolveRequest,
    current_user: dict = Depends(require_permission("SCHEDULER_VER"))
):
    """
    Expande dependencias de los tipos seleccionados y devuelve el conjunto
    ORDENADO para ejecutar (dependencias primero). Marca cuáles se agregaron por
    dependencia y cuáles son obligatorias (no des-seleccionables).
    """
    from modules.sistema.sync_catalogo_service import resolver_dependencias
    if not body.codigos:
        raise HTTPException(status_code=400, detail="Debe seleccionar al menos un tipo")
    return {'success': True, **resolver_dependencias(body.codigos)}


# =============================================================================
# FUNCIONES DE EJECUCIÓN
# =============================================================================

def _ejecutar_backfill_detalle_iscam(
    unidad_negocio_id: str, fecha_inicio: date, fecha_fin: date, commit: bool
) -> Dict[str, Any]:
    """Replica en el resync manual la fase de detalle del scheduler canónico."""
    from scripts.backfill_detalle_producto_pendientes import ejecutar_backfill

    code, resumen = ejecutar_backfill(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin + timedelta(days=1),
        unidades=[unidad_negocio_id],
        commit=commit,
    )
    return {
        'success': code == 0,
        'exit_code': code,
        'modo': 'REAL' if commit else 'DRY_RUN',
        'resumen': resumen,
        'error_message': None if code == 0 else 'El detalle ISCAM tiene días bloqueados que no conciliaron contra Runtime V2.',
    }


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
    from modules.comercial_v2.sync_comercial_edarsahub import (
        ConnectionStatus,
        QUERY_MPRO_VENTAS_CERRADAS,
        _agrupar_ventas_cerradas_por_fecha_operacion,
        build_softrestaurant_ventas_cerradas_query,
        execute_query_on_server,
        get_server_connection_config,
    )
    from modules.comercial_v2.schemas import (
        SistemaOrigen,
        UnidadNegocioConfig,
    )
    from core.query_catalog import get_query_for_server
    
    try:
        config = get_server_connection_config(
            unidad_config['server_id'],
            unidad_config.get('unidad_negocio_pk'),
        )
        
        if not config:
            return {'success': False, 'error_message': 'Config de servidor no encontrada'}
        
        sistema_raw = str(
            unidad_config.get('sistema') or ''
        ).strip()
        sistema_normalizado = normalize_system_type(sistema_raw)
        sistema = (
            'SOFTRESTAURANT'
            if sistema_normalizado == 'SOFTRESTAURANT'
            else 'MPRO'
            if sistema_normalizado == 'MANAGEMENTPRO'
            else 'UNKNOWN'
        )

        if sistema == 'SOFTRESTAURANT':
            # DRY RUN y REAL comparten el contrato oficial por turnos.
            query = build_softrestaurant_ventas_cerradas_query(
                config,
                fecha_inicio,
                fecha_fin,
            )
            query_source = 'SOFTRESTAURANT_REPORTE_TURNOS'
        elif sistema == 'MPRO':
            # DRY RUN y REAL deben consultar exactamente el mismo contrato MPRO.
            sucursal_id = unidad_config.get('sucursal_id', 'DEFAULT')
            query = QUERY_MPRO_VENTAS_CERRADAS.format(
                fecha_inicio=fecha_inicio.isoformat(),
                fecha_fin=fecha_fin.isoformat(),
                sucursal_id=sucursal_id,
            )
            query_source = 'MPRO_HANDLER_OFICIAL'
        else:
            return {
                'success': False,
                'error_message': f'Sistema origen no soportado: {sistema}',
            }
        
        datos, connection_status = execute_query_on_server(config, query)
        if connection_status != ConnectionStatus.ONLINE:
            return {
                'success': False,
                'modo': 'DRY_RUN',
                'records_processed': 0,
                'registros_afectados': 0,
                'connection_status': str(connection_status),
                'error_message': (
                    'No fue posible consultar el servidor origen durante el DRY RUN: '
                    f'{connection_status}'
                ),
            }
        
        if sistema in {'SOFTRESTAURANT', 'MPRO'}:
            dry_config = UnidadNegocioConfig(
                unidad_negocio_pk=str(
                    unidad_config.get('unidad_negocio_pk') or ''
                ),
                unidad_negocio_nombre=unidad_config['nombre'],
                server_id=unidad_config['server_id'],
                sucursal_id=unidad_config.get(
                    'sucursal_id',
                    'DEFAULT',
                ),
                sucursal_nombre=unidad_config['nombre'],
                sistema_origen=(
                    SistemaOrigen.SOFTRESTAURANT
                    if sistema == 'SOFTRESTAURANT'
                    else SistemaOrigen.MPRO
                ),
                activo=True,
            )
            datos = _agrupar_ventas_cerradas_por_fecha_operacion(
                datos,
                dry_config,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
            )

        detalle = []
        for d in datos:
            fecha_detalle = (
                d.get('fecha_operacion')
                or d.get('fecha')
            )
            ventas_detalle = float(
                d.get('ventas_total')
                if d.get('ventas_total') is not None
                else d.get('Vn_Precio_Neto_Importe') or 0
            )
            propinas_detalle = float(
                d.get('propinas_total')
                if d.get('propinas_total') is not None
                else d.get('propinas') or 0
            )
            tickets_detalle = int(
                d.get('tickets_total')
                if d.get('tickets_total') is not None
                else d.get('num_cheques')
                if d.get('num_cheques') is not None
                else d.get('num_folios') or 0
            )
            pax_detalle = int(
                d.get('pax_total')
                if d.get('pax_total') is not None
                else d.get('num_personas')
                if d.get('num_personas') is not None
                else d.get('total_personas') or 0
            )
            detalle.append({
                'fecha': str(fecha_detalle),
                'accion': 'INSERT/UPDATE',
                'ventas_total': ventas_detalle,
                'propinas_total': propinas_detalle,
                'total_con_propina': float(
                    d.get('total_con_propina')
                    or ventas_detalle + propinas_detalle
                ),
                'tickets_total': tickets_detalle,
                'pax_total': pax_detalle,
                'alimentos': float(d.get('alimentos') or 0),
                'bebidas': float(d.get('bebidas') or 0),
                'otros': float(d.get('otros') or 0),
                'cortesias': float(d.get('cortesias') or 0),
                'descuentos': float(d.get('descuentos') or 0),
                'subtotal': float(d.get('subtotal') or 0),
                'iva': float(d.get('iva') or 0),
            })
        
        # El item de catalogo 'Ventas Cerradas (KPIs)' valida primero el header KPI.
        # El detalle ISCAM es una etapa auxiliar: si falla no debe falsear que el
        # servidor origen estuvo OFFLINE ni convertir un header valido en fallo.
        try:
            detalle_producto = _ejecutar_backfill_detalle_iscam(
                unidad_negocio_id, fecha_inicio, fecha_fin, commit=False
            )
        except Exception as detalle_exc:
            detalle_producto = {
                'success': False,
                'modo': 'DRY_RUN',
                'error_message': f'Fallo en validacion auxiliar DETALLE_ISCAM: {detalle_exc}',
            }

        detalle_success = bool(detalle_producto.get('success'))
        detalle_warning = (
            None
            if detalle_success
            else detalle_producto.get('error_message')
            or 'HEADER_KPI validado; DETALLE_ISCAM requiere revision.'
        )

        return {
            'success': True,
            'modo': 'DRY_RUN',
            'stage': 'HEADER_KPI',
            'header_success': True,
            'detail_success': detalle_success,
            'warning_message': detalle_warning,
            'mensaje': 'Simulación de Ventas Cerradas (KPIs) completada - NO se modificaron datos',
            'records_processed': len(detalle),
            'registros_que_se_sincronizarian': len(detalle),
            'registros_extraidos': len(detalle),
            'registros_afectados': 0,
            'query_source': query_source,
            'system_type_raw': sistema_raw,
            'system_type_normalized': sistema_normalizado,
            'backend_contract_version': (
                'softrestaurant-turnos-v2'
                if sistema == 'SOFTRESTAURANT'
                else 'mpro-handler-oficial-v1'
            ),
            'detalle': detalle,
            'detalle_producto': detalle_producto
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
        
        # Crear config usando identificadores y sistema canónicos.
        unidad_negocio_pk = str(
            unidad_config.get('unidad_negocio_pk') or ''
        ).strip()
        if not unidad_negocio_pk:
            return {
                'success': False,
                'error_message': 'unidad_negocio_pk canónica no disponible',
            }

        sistema_raw = str(unidad_config.get('sistema') or '').strip()
        sistema_normalizado = normalize_system_type(sistema_raw)
        sistema = (
            'SOFTRESTAURANT'
            if sistema_normalizado == 'SOFTRESTAURANT'
            else 'MPRO'
            if sistema_normalizado == 'MANAGEMENTPRO'
            else 'UNKNOWN'
        )
        if sistema not in {'SOFTRESTAURANT', 'MPRO'}:
            return {
                'success': False,
                'error_message': f'Sistema origen no soportado: {sistema}',
            }

        config = UnidadNegocioConfig(
            unidad_negocio_pk=unidad_negocio_pk,
            unidad_negocio_nombre=unidad_config['nombre'],
            server_id=unidad_config['server_id'],
            sucursal_id=unidad_config['sucursal_id'],
            sucursal_nombre=unidad_config['nombre'],
            sistema_origen=(
                SistemaOrigen.SOFTRESTAURANT
                if sistema == 'SOFTRESTAURANT'
                else SistemaOrigen.MPRO
            ),
            activo=True
        )
        
        # Ejecutar handler oficial según sistema
        if sistema == 'SOFTRESTAURANT':
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
        
        if resultado.success:
            try:
                detalle_producto = _ejecutar_backfill_detalle_iscam(
                    unidad_negocio_id, fecha_inicio, fecha_fin, commit=True
                )
            except Exception as detalle_exc:
                detalle_producto = {
                    'success': False,
                    'modo': 'REAL',
                    'error_message': f'HEADER_KPI sincronizado; fallo auxiliar DETALLE_ISCAM: {detalle_exc}',
                }

            try:
                from core.scheduler.jobs.inteligencia_comercial_enrich import (
                    resync_pagos_unidad,
                )
                pagos_ticket = resync_pagos_unidad(
                    unidad_negocio_id,
                    fecha_inicio,
                    fecha_fin + timedelta(days=1),
                    dry_run=False,
                )
            except Exception as pagos_exc:
                pagos_ticket = {
                    'unidad': unidad_negocio_id,
                    'error': f'HEADER_KPI sincronizado; fallo PAGOS_TICKET: {pagos_exc}',
                }
        else:
            detalle_producto = {
                'success': False,
                'modo': 'NO_EJECUTADO',
                'error_message': 'DETALLE_ISCAM no ejecutado porque HEADER_KPI no fue exitoso',
            }
            pagos_ticket = {
                'unidad': unidad_negocio_id,
                'error': 'PAGOS_TICKET no ejecutado porque HEADER_KPI no fue exitoso',
            }

        detalle_success = bool(detalle_producto.get('success'))
        pagos_success = not bool(pagos_ticket.get('error'))
        warnings = []
        if resultado.success and not detalle_success:
            warnings.append(
                detalle_producto.get('error_message')
                or 'HEADER_KPI sincronizado; DETALLE_ISCAM requiere revision.'
            )
        if resultado.success and not pagos_success:
            warnings.append(
                pagos_ticket.get('error')
                or 'HEADER_KPI sincronizado; PAGOS_TICKET requiere revision.'
            )
        detalle_warning = ' | '.join(warnings) or None

        return {
            'success': bool(resultado.success),
            'stage': 'HEADER_KPI' if resultado.success else 'HEADER_KPI_FAILED',
            'header_success': bool(resultado.success),
            'detail_success': detalle_success,
            'payments_success': pagos_success,
            'warning_message': detalle_warning,
            'pagos_ticket': pagos_ticket,
            'records_processed': resultado.records_processed,
            'records_inserted': resultado.records_inserted,
            'records_updated': resultado.records_updated,
            'records_skipped': resultado.records_skipped,
            'records_errored': resultado.records_errored,
            'duration_seconds': resultado.duration_seconds,
            'detalle_producto': detalle_producto,
            'error_message': resultado.error_message
        }
        
    except Exception as e:
        logger.error(f"[RESYNC] Error en sync real: {e}")
        return {'success': False, 'error_message': str(e)}
