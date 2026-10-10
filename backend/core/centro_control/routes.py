from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
from core.sql_first.connection_factory import get_edarsahub_pymssql_connection
"""
CENTRO DE CONTROL EDARSA - API Routes
======================================
Módulo central de monitoreo, estabilidad, detección de regresiones 
y control técnico del sistema EDARSA HUB.

COMPONENTES INTEGRADOS:
1. Estado General del Sistema
2. Salud por Módulo
3. Alertas de Regresión
4. Conectividad de Fuentes
5. Jobs y Automatizaciones
6. Bitácora de Cambios
7. Métricas de Estabilidad

ENDPOINTS:
- GET  /api/centro-control/estado              → Estado general consolidado
- GET  /api/centro-control/salud               → Reporte completo de salud
- GET  /api/centro-control/salud/resumen       → Resumen ejecutivo (semáforos)
- POST /api/centro-control/regresiones         → Ejecutar checks de regresión
- GET  /api/centro-control/regresiones/{modulo}→ Checks de un módulo
- GET  /api/centro-control/fuentes             → Estado de fuentes de datos
- GET  /api/centro-control/alertas             → Alertas activas
- POST /api/centro-control/alertas/acknowledge → Reconocer una alerta
- GET  /api/centro-control/jobs                → Estado de jobs/automatizaciones
- GET  /api/centro-control/bitacora            → Bitácora de cambios del sistema
- POST /api/centro-control/bitacora            → Registrar cambio en bitácora
- GET  /api/centro-control/metricas            → Métricas de estabilidad
- GET  /api/centro-control/historial           → Historial de eventos
- GET  /api/centro-control/matriz-resolucion   → Documentación de arquitectura

ACCESO:
- Roles: Administrador, Supervisor, Director
- Uso: Control técnico/directivo (NO operativo)

CREADO: 2026-04-19
ACTUALIZADO: 2026-04-19
"""

import logging
import os
import json
import uuid
import asyncio
import subprocess
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from core.security import get_current_user
from core.rbac.middleware import require_explicit_permission
from core.health_checker import (
    get_system_health,
    create_health_summary,
    get_health_checker,
    HealthStatus
)
from core.regression_checker import (
    run_regression_checks,
    run_module_regression_checks,
    get_regression_checker,
    ModuleName,
    CheckStatus
)
from core.centro_control.websocket import get_notification_manager, NotificationManager
from core.centro_control.email_notifications import (
    send_critical_alert_email,
    send_test_email,
    get_email_config_status,
    is_email_configured
)
from core.centro_control.whatsapp_notifications import (
    send_critical_alert_whatsapp,
    send_test_whatsapp,
    get_whatsapp_config_status,
    is_whatsapp_configured
)
from core.centro_control.recipients_manager import (
    get_all_recipients,
    add_recipient,
    update_recipient,
    delete_recipient,
    get_recipients_summary
)
from core.centro_control import sql_store as cc_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/centro-control", tags=["Centro de Control"])


# ============================================================================
# HELPERS SQL-FIRST PARA JOBS DEL CENTRO DE CONTROL
# ============================================================================



def _cc_sql_connection():
    """Abrir EDARSAHUB mediante la factory pymssql canónica."""
    return get_edarsahub_pymssql_connection(autocommit=False)


def _cc_execute(sql: str, params: tuple = ()):
    conn = _cc_sql_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def _cc_fetchall(sql: str, params: tuple = ()):
    conn = _cc_sql_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def _ensure_scheduler_job_config_table():
    """Extiende scheduler sin romper dbo.Sys_Scheduler_Jobs."""
    _cc_execute("""
    IF NOT EXISTS (
        SELECT 1
        FROM sys.objects
        WHERE object_id = OBJECT_ID(N'[dbo].[Sys_Scheduler_JobConfig]')
          AND type = 'U'
    )
    BEGIN
        CREATE TABLE dbo.Sys_Scheduler_JobConfig (
            JobID VARCHAR(50) NOT NULL PRIMARY KEY,
            Modulo VARCHAR(50) NOT NULL,
            Handler VARCHAR(80) NOT NULL,
            ParametrosJSON NVARCHAR(MAX) NULL,
            ModoEjecucion VARCHAR(30) NOT NULL DEFAULT('MANUAL'),
            TimeoutSegundos INT NOT NULL DEFAULT(1800),
            ReintentosMaximos INT NOT NULL DEFAULT(0),
            PermiteEjecucionManual BIT NOT NULL DEFAULT(1),
            CreadoPorUsuarioID VARCHAR(100) NULL,
            FechaCreacion DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
            FechaActualizacion DATETIME2 NULL,
            CONSTRAINT FK_SchedulerJobConfig_Jobs
                FOREIGN KEY (JobID) REFERENCES dbo.Sys_Scheduler_Jobs(JobID)
        );
    END
    """)
    for col, ddl in {
        "InstruccionEjecucion": "NVARCHAR(MAX) NULL",
        "ComandoPreview": "NVARCHAR(MAX) NULL",
        "ParametrosEditablesJSON": "NVARCHAR(MAX) NULL",
        "GrupoEjecucion": "NVARCHAR(100) NULL",
        "DependenciasJSON": "NVARCHAR(MAX) NULL",
        "AdvertenciaManual": "NVARCHAR(MAX) NULL",
    }.items():
        _cc_execute(f"""
            IF COL_LENGTH('dbo.Sys_Scheduler_JobConfig', '{col}') IS NULL
            BEGIN
                ALTER TABLE dbo.Sys_Scheduler_JobConfig ADD {col} {ddl}
            END
        """)


def _safe_job_id(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9_\-]", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise HTTPException(status_code=400, detail="job_id requerido")
    if len(value) > 50:
        raise HTTPException(status_code=400, detail="job_id excede 50 caracteres")
    return value


def _validate_handler(handler: str) -> str:
    allowed = {"NETPAY_BACKFILL", "SCHEDULER_JOB"}
    handler = (handler or "").strip().upper()
    if handler not in allowed:
        raise HTTPException(status_code=400, detail=f"Handler no permitido: {handler}")
    return handler


def _run_netpay_backfill_sync(params: Dict[str, Any], timeout: int = 1800) -> Dict[str, Any]:
    report_type = (params.get("report_type") or "").strip().upper()
    date_from = (params.get("date_from") or "").strip()
    date_to = (params.get("date_to") or "").strip()

    if report_type not in {"DETALLE_TRANSACCIONES", "DETALLE_DEPOSITOS_MOVIMIENTOS"}:
        raise HTTPException(status_code=400, detail="report_type NetPay inválido")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_from):
        raise HTTPException(status_code=400, detail="date_from requerido YYYY-MM-DD")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_to):
        raise HTTPException(status_code=400, detail="date_to requerido YYYY-MM-DD")

    try:
        date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Fechas NetPay inválidas")

    if date_to_obj < date_from_obj:
        raise HTTPException(status_code=400, detail="date_to no puede ser menor que date_from")
    if date_to_obj > datetime.now().date():
        raise HTTPException(status_code=400, detail="date_to no puede ser una fecha futura")

    days = (date_to_obj - date_from_obj).days + 1
    if days > 31:
        raise HTTPException(status_code=400, detail=f"Rango NetPay excede maximo permitido de 31 dias: {days}")

    working_directory = params.get("working_directory") or "/app/netpay_robot_edarsahub/netpay_robot_edarsahub"
    allowed_wd = "/app/netpay_robot_edarsahub/netpay_robot_edarsahub"
    if working_directory != allowed_wd:
        raise HTTPException(status_code=400, detail="working_directory no permitido")

    python_bin = os.environ.get("NETPAY_ROBOT_PYTHON", "/usr/local/bin/python")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = f"{working_directory}/.vendor:{working_directory}"

    cmd = [
        python_bin, "-B", "-m", "netpay_robot.cli", "run",
        "--report-type", report_type,
        "--date-from", date_from,
        "--date-to", date_to,
    ]

    proc = subprocess.run(
        cmd,
        cwd=working_directory,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )

    output = proc.stdout or ""
    return {
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "output_tail": output[-12000:],
        "command": " ".join(cmd),
    }

# ============================================================================
# MODELOS DE REQUEST/RESPONSE
# ============================================================================

class RecipientCreateRequest(BaseModel):
    """Request para crear un destinatario"""
    tipo: str  # "email" o "whatsapp"
    destinatario: str  # Email o número de teléfono
    nombre: Optional[str] = None

class RecipientUpdateRequest(BaseModel):
    """Request para actualizar un destinatario"""
    activo: Optional[bool] = None
    nombre: Optional[str] = None

class RegressionCheckRequest(BaseModel):
    """Request para ejecutar checks de regresión"""
    modulos: Optional[List[str]] = None  # Si None, ejecuta todos
    force: bool = False  # Forzar incluso si hay check reciente

class AlertAcknowledgeRequest(BaseModel):
    """Request para reconocer una alerta"""
    alert_id: str
    comentario: Optional[str] = None

class BitacoraEntryRequest(BaseModel):
    """Request para registrar entrada en bitácora"""
    tipo: str  # "cambio_codigo", "deploy", "config", "incidente", "hotfix"
    modulo: str
    descripcion: str
    impacto: Optional[str] = None
    autor: Optional[str] = None
    referencias: Optional[List[str]] = None  # PRs, tickets, docs


class SchedulerJobCreateRequest(BaseModel):
    """Request para crear job desde Centro de Control."""
    job_id: str
    job_name: str
    cron_expression: str = "MANUAL"
    job_type: str = "NETPAY"
    status: str = "activo"
    modulo: str = "FINANZAS"
    handler: str = "NETPAY_BACKFILL"
    parametros: Dict[str, Any] = {}
    timeout_segundos: int = 1800
    reintentos_maximos: int = 0
    permite_ejecucion_manual: bool = True


class SchedulerJobRunRequest(BaseModel):
    """Request para ejecutar job manual con parámetros opcionales."""
    parametros: Optional[Dict[str, Any]] = None

# ============================================================================
# PERSISTENCIA SQL CANÓNICA - Gate 2 P2B
# ============================================================================

def _registrar_evento(tipo: str, modulo: str, mensaje: str, severidad: str = "info", data: Dict = None):
    return cc_store.record_event(tipo, modulo, mensaje, severidad, data)

def _crear_alerta(titulo: str, modulo: str, severidad: str, detalle: str):
    """Persiste alerta en SQL y conserva notificación en tiempo real."""
    alerta = cc_store.create_alert(titulo, modulo, severidad, detalle)
    try:
        manager = get_notification_manager()
        if severidad == "critical":
            asyncio.create_task(manager.broadcast_alerta_critica(alerta))
            asyncio.create_task(_enviar_email_alerta_critica(alerta))
            asyncio.create_task(_enviar_whatsapp_alerta_critica(alerta))
        else:
            asyncio.create_task(manager.broadcast_alerta_nueva(alerta))
    except Exception as e:
        logger.warning(f"[ALERTA] No se pudo notificar via WS: {e}")
    return alerta


async def _enviar_email_alerta_critica(alerta: Dict[str, Any]):
    """Envía email para alertas críticas en background"""
    try:
        if is_email_configured():
            result = await send_critical_alert_email(alerta)
            if result.get("success"):
                logger.info(f"[EMAIL] Alerta crítica notificada por email: {result.get('message')}")
            else:
                logger.warning(f"[EMAIL] No se pudo enviar email: {result.get('message')}")
    except Exception as e:
        logger.error(f"[EMAIL] Error enviando email de alerta: {e}")


async def _enviar_whatsapp_alerta_critica(alerta: Dict[str, Any]):
    """Envía WhatsApp para alertas críticas en background"""
    try:
        if is_whatsapp_configured():
            result = await send_critical_alert_whatsapp(alerta)
            if result.get("success"):
                logger.info(f"[WHATSAPP] Alerta crítica notificada por WhatsApp: {result.get('message')}")
            else:
                logger.warning(f"[WHATSAPP] No se pudo enviar WhatsApp: {result.get('message')}")
    except Exception as e:
        logger.error(f"[WHATSAPP] Error enviando WhatsApp de alerta: {e}")

# ============================================================================
# ENDPOINTS: SALUD DEL SISTEMA
# ============================================================================

@router.get("/salud")
async def obtener_salud_sistema(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Obtiene el reporte completo de salud del sistema.
    
    Incluye:
    - Estado general (healthy/degraded/critical)
    - Estado de cada módulo
    - Estado de cada fuente de datos
    - Regresiones recientes
    - Eventos recientes
    """
    logger.info(f"[CENTRO CONTROL] Usuario {current_user.get('email')} solicitó reporte de salud")
    
    try:
        # Obtener reporte de salud
        reporte = get_system_health()
        
        # Registrar evento
        _registrar_evento(
            tipo="health_check",
            modulo="sistema",
            mensaje=f"Reporte de salud generado: {reporte.get('summary', {}).get('overall_status', 'unknown')}",
            severidad="info"
        )
        
        # Agregar metadatos adicionales desde SQL canónico
        reporte["centro_control"] = {
            "version": "1.0.0",
            "alertas_activas": cc_store.active_alert_count(),
            "ultimo_check": datetime.now(timezone.utc).isoformat()
        }
        
        return reporte
        
    except Exception as e:
        logger.error(f"[CENTRO CONTROL] Error obteniendo salud: {e}")
        _registrar_evento(
            tipo="error",
            modulo="sistema",
            mensaje=f"Error generando reporte de salud: {str(e)[:200]}",
            severidad="critical"
        )
        raise HTTPException(status_code=500, detail=f"Error obteniendo salud del sistema")


@router.get("/salud/resumen")
async def obtener_resumen_ejecutivo(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Obtiene un resumen ejecutivo de salud para el dashboard.
    
    Optimizado para visualización rápida:
    - Semáforo general (emoji + status)
    - KPIs principales
    - Lista de módulos con estado
    - Lista de fuentes con estado
    """
    try:
        resumen = create_health_summary()
        
        # Agregar alertas activas
        alertas_no_reconocidas = cc_store.list_alerts(active_only=True, limit=100)
        resumen["alertas"] = {
            "activas": len(alertas_no_reconocidas),
            "criticas": len([a for a in alertas_no_reconocidas if a.get("severidad") == "critical"]),
            "lista": alertas_no_reconocidas[:5]  # Top 5
        }
        
        return resumen
        
    except Exception as e:
        logger.error(f"[CENTRO CONTROL] Error en resumen ejecutivo: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando resumen")

# ============================================================================
# ENDPOINTS: DETECCIÓN DE REGRESIONES
# ============================================================================

@router.post("/regresiones")
async def ejecutar_checks_regresion(
    request: RegressionCheckRequest = None,
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Ejecuta los checks de regresión para todos los módulos o los especificados.
    
    Regresiones detectadas:
    - Ventas acumuladas en $0 con unidades online
    - Fuentes de datos mal configuradas
    - Comparativos no disponibles
    - ConnectionResolver no operativo
    """
    logger.info(f"[CENTRO CONTROL] Usuario {current_user.get('email')} ejecutó checks de regresión")
    
    try:
        # Ejecutar checks
        if request and request.modulos:
            # Ejecutar solo módulos especificados
            resultados = []
            for modulo_str in request.modulos:
                try:
                    modulo = ModuleName(modulo_str)
                    reporte = run_module_regression_checks(modulo)
                    resultados.append(reporte.to_dict())
                except ValueError:
                    logger.warning(f"Módulo desconocido: {modulo_str}")
            
            response = {
                "tipo": "parcial",
                "modulos_ejecutados": request.modulos,
                "resultados": resultados
            }
        else:
            # Ejecutar todos
            reporte = run_regression_checks()
            response = {
                "tipo": "completo",
                "reporte": reporte.to_dict()
            }
            
            # Crear alertas para fallas críticas
            for result in reporte.results:
                if result.status in [CheckStatus.FAIL, CheckStatus.ERROR]:
                    if result.severity.value in ["critical", "high"]:
                        _crear_alerta(
                            titulo=f"Regresión detectada: {result.check_name}",
                            modulo=result.module.value,
                            severidad=result.severity.value,
                            detalle=result.message
                        )
        
        # Registrar evento persistente en SQL
        # Registrar evento
        _registrar_evento(
            tipo="regression_check",
            modulo="sistema",
            mensaje=f"Checks de regresión ejecutados",
            severidad="info",
            data={"tipo": response.get("tipo")}
        )
        
        return response
        
    except Exception as e:
        logger.error(f"[CENTRO CONTROL] Error en checks de regresión: {e}")
        raise HTTPException(status_code=500, detail=f"Error ejecutando checks")


@router.get("/regresiones/{modulo}")
async def obtener_regresiones_modulo(
    modulo: str,
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Ejecuta checks de regresión para un módulo específico.
    
    Módulos disponibles:
    - tablero_ejecutivo
    - auditoria_compras
    - operaciones_analisis
    - finanzas
    - compras
    - rh
    """
    try:
        modulo_enum = ModuleName(modulo)
        reporte = run_module_regression_checks(modulo_enum)
        
        return {
            "modulo": modulo,
            "reporte": reporte.to_dict()
        }
        
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Módulo inválido. Opciones: {[m.value for m in ModuleName]}"
        )
    except Exception as e:
        logger.error(f"[CENTRO CONTROL] Error en regresiones de {modulo}: {e}")
        raise HTTPException(status_code=500, detail=f"Error")

# ============================================================================
# ENDPOINTS: FUENTES DE DATOS
# ============================================================================

@router.get("/fuentes")
async def obtener_estado_fuentes(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Obtiene el estado de todas las fuentes de datos configuradas.
    
    Fuentes monitoreadas:
    - MongoDB (EDARSA HUB)
    - SQL Servers (desde menú Servidores)
    - APIs locales MPRO
    """
    try:
        checker = get_health_checker()
        reporte = checker.get_health_report()
        
        # Formatear fuentes
        fuentes = []
        for source in reporte.sources:
            fuentes.append({
                "nombre": source.name,
                "tipo": source.source_type.value,
                "estado": source.status.value,
                "emoji": "✅" if source.status == HealthStatus.HEALTHY else ("⚠️" if source.status == HealthStatus.DEGRADED else "❌"),
                "tiempo_respuesta_ms": source.response_time_ms,
                "ultimo_exito": source.last_success.isoformat() if source.last_success else None,
                "ultimo_error": source.last_error,
                "errores_24h": source.error_count_24h
            })
        
        return {
            "total": len(fuentes),
            "conectadas": sum(1 for f in fuentes if f["estado"] == "healthy"),
            "con_problemas": sum(1 for f in fuentes if f["estado"] != "healthy"),
            "fuentes": fuentes
        }
        
    except Exception as e:
        logger.error(f"[CENTRO CONTROL] Error obteniendo fuentes: {e}")
        raise HTTPException(status_code=500, detail=f"Error")

# ============================================================================
# ENDPOINTS: ALERTAS
# ============================================================================

@router.get("/alertas")
async def obtener_alertas(
    solo_activas: bool = Query(True, description="Solo alertas no reconocidas"),
    limite: int = Query(20, ge=1, le=100),
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Obtiene las alertas del sistema.
    
    Las alertas se generan automáticamente cuando:
    - Un check de regresión falla con severidad critical/high
    - Una fuente de datos cae
    - Un módulo entra en estado degradado/crítico
    """
    alertas = cc_store.list_alerts(active_only=solo_activas, limit=limite)
    return {
        "total": len(alertas),
        "alertas": alertas
    }


@router.post("/alertas/acknowledge")
async def reconocer_alerta(
    request: AlertAcknowledgeRequest,
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Reconoce (acknowledge) una alerta para indicar que fue revisada.
    """
    alerta = cc_store.acknowledge_alert(request.alert_id, current_user.get("email"), request.comentario)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    _registrar_evento(
        tipo="alert_acknowledged",
        modulo=alerta.get("modulo", "sistema"),
        mensaje=f"Alerta reconocida: {alerta.get('titulo')}",
        severidad="info",
        data={"alert_id": request.alert_id, "usuario": current_user.get("email")}
    )
    return {"success": True, "message": "Alerta reconocida", "alerta": alerta}

# ============================================================================
# ENDPOINTS: HISTORIAL
# ============================================================================

@router.get("/historial")
async def obtener_historial(
    limite: int = Query(50, ge=1, le=200),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de evento"),
    modulo: Optional[str] = Query(None, description="Filtrar por módulo"),
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Obtiene el historial de eventos del Centro de Control.
    
    Tipos de eventos:
    - health_check: Checks de salud ejecutados
    - regression_check: Checks de regresión ejecutados
    - alert_created: Alerta creada
    - alert_acknowledged: Alerta reconocida
    - error: Errores del sistema
    """
    eventos = cc_store.list_events(limit=limite, tipo=tipo, modulo=modulo)
    return {
        "total": len(eventos),
        "eventos": eventos
    }

# ============================================================================
# ENDPOINTS: MATRIZ DE RESOLUCIÓN
# ============================================================================

@router.get("/matriz-resolucion")
async def obtener_matriz_resolucion(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Obtiene la matriz de resolución de conexiones.
    
    Documenta cómo se resuelven las fuentes de datos:
    - Por tipo de sistema (SoftRestaurant, MPRO)
    - Por tipo de métrica (acumulados, diarios, comparativos)
    """
    try:
        from core.connection_resolver import get_resolution_matrix
        
        matriz = get_resolution_matrix()
        
        return {
            "descripcion": "Matriz de resolución de conexiones y fuentes de datos",
            "principios": [
                "EDARSA HUB es el cerebro - Backend manda",
                "Menú 'Servidores SQL' es la fuente oficial de configuración",
                "MPRO usa SQL para acumulados, API local para diarios",
                "SoftRestaurant usa SQL para todo"
            ],
            "matriz": matriz
        }
        
    except Exception as e:
        logger.error(f"[CENTRO CONTROL] Error obteniendo matriz: {e}")
        raise HTTPException(status_code=500, detail=f"Error")

# ============================================================================
# ENDPOINTS: ESTADO GENERAL (PING)
# ============================================================================

@router.get("/ping")
async def ping_centro_control():
    """
    Endpoint de health check para el Centro de Control.
    No requiere autenticación.
    """
    return {
        "status": "ok",
        "service": "CENTRO DE CONTROL EDARSA",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alertas_activas": cc_store.active_alert_count(),
        "ultimo_check_salud": cc_store.latest_event_timestamp("health_check"),
        "ultimo_check_regresion": cc_store.latest_event_timestamp("regression_check")
    }

# ============================================================================
# ENDPOINTS: ESTADO GENERAL CONSOLIDADO
# ============================================================================

@router.get("/estado")
async def obtener_estado_general(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Obtiene el estado general consolidado del CENTRO DE CONTROL EDARSA.
    
    Incluye resumen de TODOS los componentes:
    - Salud del sistema
    - Alertas activas
    - Estado de fuentes
    - Jobs activos
    - Métricas de estabilidad
    - Últimos cambios en bitácora
    """
    try:
        # 1. Salud del sistema
        health_summary = create_health_summary()
        
        # 2. Alertas desde SQL canónico
        alertas_activas = cc_store.list_alerts(active_only=True, limit=100)
        
        # 3. Jobs (si scheduler disponible)
        jobs_status = {"running": False, "jobs_activos": 0, "proxima_ejecucion": None}
        try:
            from core.scheduler.scheduler_manager import get_scheduler_manager
            scheduler = get_scheduler_manager()
            if scheduler:
                jobs_status["running"] = scheduler.running if hasattr(scheduler, 'running') else False
                jobs_status["jobs_activos"] = len(scheduler.get_jobs()) if hasattr(scheduler, 'get_jobs') else 0
        except Exception:
            pass
        
        # 4. Métricas derivadas de evidencia SQL persistente
        metricas_sql = cc_store.metrics()
        bitacora_sql = cc_store.bitacora_summary()
        
        return {
            "centro_control": "CENTRO DE CONTROL EDARSA",
            "version": "2.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "estado_general": health_summary.get("status", "unknown"),
            "estado_emoji": health_summary.get("status_emoji", "❓"),
            "componentes": {
                "salud": {
                    "status": health_summary.get("status"),
                    "modulos_sanos_pct": health_summary.get("kpis", {}).get("modules_healthy_pct", 0),
                    "fuentes_conectadas_pct": health_summary.get("kpis", {}).get("sources_connected_pct", 0)
                },
                "alertas": {
                    "activas": len(alertas_activas),
                    "criticas": len([a for a in alertas_activas if a.get("severidad") == "critical"])
                },
                "regresiones": {
                    "ultimas_24h": health_summary.get("kpis", {}).get("regressions_24h", 0),
                    "ultimo_check": cc_store.latest_event_timestamp("regression_check")
                },
                "jobs": jobs_status,
                "bitacora": bitacora_sql,
                "metricas": metricas_sql
            },
            "modulos": health_summary.get("modules_summary", []),
            "fuentes": health_summary.get("sources_summary", [])
        }
        
    except Exception as e:
        logger.error(f"[CENTRO CONTROL] Error en estado general: {e}")
        raise HTTPException(status_code=500, detail=f"Error")

# ============================================================================
# ENDPOINTS: JOBS Y AUTOMATIZACIONES
# ============================================================================

@router.get("/jobs")
async def obtener_estado_jobs(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Obtiene el estado de jobs y automatizaciones del sistema.
    
    Integra con el scheduler de EDARSA HUB para mostrar:
    - Jobs registrados
    - Estado de ejecución
    - Próximas ejecuciones
    - Historial reciente
    """
    try:
        from core.scheduler.scheduler_manager import get_scheduler_manager
        
        scheduler = get_scheduler_manager()
        
        if not scheduler:
            return {
                "scheduler_status": "not_initialized",
                "jobs": [],
                "message": "Scheduler no inicializado"
            }
        
        # Obtener jobs desde API real del SchedulerManager
        scheduler_status_data = scheduler.get_status() if hasattr(scheduler, 'get_status') else {}
        jobs = scheduler_status_data.get("jobs", []) if isinstance(scheduler_status_data, dict) else []
        scheduler_running = bool(scheduler_status_data.get("running")) if isinstance(scheduler_status_data, dict) else False
        
        # Complementar con jobs registrados en SQL para que el menú muestre también jobs manuales/configurados.
        try:
            _ensure_scheduler_job_config_table()
            sql_jobs = _cc_fetchall("""
                SELECT
                    j.JobID,
                    j.JobName,
                    j.CronExpression,
                    j.JobType,
                    j.Status,
                    j.LastRunDate,
                    c.Modulo,
                    c.Handler,
                    c.ParametrosJSON,
                    c.ModoEjecucion,
                    c.PermiteEjecucionManual
                FROM dbo.Sys_Scheduler_Jobs j
                LEFT JOIN dbo.Sys_Scheduler_JobConfig c
                    ON c.JobID = j.JobID
                ORDER BY j.JobName
            """)
            existing_ids = {str(j.get("id")) for j in jobs}
            for row in sql_jobs:
                job_id = row.get("JobID")
                if job_id in existing_ids:
                    continue
                jobs.append({
                    "id": job_id,
                    "name": row.get("JobName"),
                    "next_run": None,
                    "trigger": row.get("CronExpression"),
                    "job_type": row.get("JobType"),
                    "status": row.get("Status"),
                    "handler": row.get("Handler"),
                    "modulo": row.get("Modulo"),
                    "manual": bool(row.get("PermiteEjecucionManual")) if row.get("PermiteEjecucionManual") is not None else False,
                    "last_run": row.get("LastRunDate").isoformat() if row.get("LastRunDate") else None,
                })
        except Exception as sql_exc:
            logger.warning(f"[CENTRO CONTROL] No se pudieron cargar jobs SQL: {sql_exc}")

        return {
            "scheduler_status": "running" if scheduler_running else "stopped",
            "jobs_total": len(jobs),
            "jobs": jobs,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except ImportError:
        return {
            "scheduler_status": "not_available",
            "jobs": [],
            "message": "Módulo de scheduler no disponible"
        }
    except Exception as e:
        logger.error(f"[CENTRO CONTROL] Error obteniendo jobs: {e}")
        return {
            "scheduler_status": "error",
            "jobs": [],
            "error": str(e)[:200]
        }


@router.post("/jobs")
async def crear_scheduler_job(
    payload: SchedulerJobCreateRequest,
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """Crea/actualiza un job SQL-first visible desde Centro de Control."""
    try:
        _ensure_scheduler_job_config_table()

        job_id = _safe_job_id(payload.job_id)
        handler = _validate_handler(payload.handler)

        job_name = (payload.job_name or "").strip()
        if not job_name:
            raise HTTPException(status_code=400, detail="job_name requerido")
        if len(job_name) > 100:
            raise HTTPException(status_code=400, detail="job_name excede 100 caracteres")

        cron = (payload.cron_expression or "MANUAL").strip()
        if len(cron) > 50:
            raise HTTPException(status_code=400, detail="cron_expression excede 50 caracteres")

        job_type = (payload.job_type or "NETPAY").strip().upper()
        if len(job_type) > 20:
            raise HTTPException(status_code=400, detail="job_type excede 20 caracteres")

        status = (payload.status or "activo").strip()
        if status.lower() not in {"activo", "active", "inactivo", "inactive", "paused", "pausado"}:
            raise HTTPException(status_code=400, detail="status inválido")

        user_id = str(
            current_user.get("PublicUUID")
            or current_user.get("id")
            or current_user.get("email")
            or current_user.get("username")
            or "unknown"
        )

        parametros = dict(payload.parametros or {})
        if handler == "NETPAY_BACKFILL":
            parametros.setdefault("working_directory", "/app/netpay_robot_edarsahub/netpay_robot_edarsahub")
            if "report_type" in parametros:
                parametros["report_type"] = str(parametros["report_type"]).upper()

        parametros_json = json.dumps(parametros, ensure_ascii=False)

        _cc_execute("""
            IF EXISTS (SELECT 1 FROM dbo.Sys_Scheduler_Jobs WHERE JobID=%s)
            BEGIN
                UPDATE dbo.Sys_Scheduler_Jobs
                SET JobName=%s,
                    CronExpression=%s,
                    JobType=%s,
                    Status=%s
                WHERE JobID=%s
            END
            ELSE
            BEGIN
                INSERT INTO dbo.Sys_Scheduler_Jobs (
                    JobID, JobName, CronExpression, JobType, Status, LastRunDate
                )
                VALUES (%s, %s, %s, %s, %s, NULL)
            END
        """, (
            job_id, job_name, cron, job_type, status, job_id,
            job_id, job_name, cron, job_type, status
        ))

        _cc_execute("""
            IF EXISTS (SELECT 1 FROM dbo.Sys_Scheduler_JobConfig WHERE JobID=%s)
            BEGIN
                UPDATE dbo.Sys_Scheduler_JobConfig
                SET Modulo=%s,
                    Handler=%s,
                    ParametrosJSON=%s,
                    ModoEjecucion=%s,
                    TimeoutSegundos=%s,
                    ReintentosMaximos=%s,
                    PermiteEjecucionManual=%s,
                    FechaActualizacion=SYSUTCDATETIME()
                WHERE JobID=%s
            END
            ELSE
            BEGIN
                INSERT INTO dbo.Sys_Scheduler_JobConfig (
                    JobID, Modulo, Handler, ParametrosJSON, ModoEjecucion,
                    TimeoutSegundos, ReintentosMaximos, PermiteEjecucionManual,
                    CreadoPorUsuarioID
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            END
        """, (
            job_id, payload.modulo, handler, parametros_json, "MANUAL",
            int(payload.timeout_segundos), int(payload.reintentos_maximos),
            1 if payload.permite_ejecucion_manual else 0, job_id,
            job_id, payload.modulo, handler, parametros_json, "MANUAL",
            int(payload.timeout_segundos), int(payload.reintentos_maximos),
            1 if payload.permite_ejecucion_manual else 0, user_id
        ))

        return {
            "ok": True,
            "job_id": job_id,
            "job_name": job_name,
            "handler": handler,
            "message": "Job creado/actualizado correctamente"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CENTRO CONTROL] Error creando job: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor"[:500])


@router.post("/jobs/{job_id}/run")
async def ejecutar_scheduler_job_manual(
    job_id: str,
    payload: SchedulerJobRunRequest = SchedulerJobRunRequest(),
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """Ejecuta manualmente un job permitido desde Centro de Control."""
    try:
        _ensure_scheduler_job_config_table()
        job_id = _safe_job_id(job_id)

        rows = _cc_fetchall("""
            SELECT
                j.JobID,
                j.JobName,
                j.Status,
                c.Handler,
                c.ParametrosJSON,
                c.TimeoutSegundos,
                c.PermiteEjecucionManual
            FROM dbo.Sys_Scheduler_Jobs j
            INNER JOIN dbo.Sys_Scheduler_JobConfig c
                ON c.JobID = j.JobID
            WHERE j.JobID=%s
        """, (job_id,))

        if not rows:
            raise HTTPException(status_code=404, detail=f"Job no encontrado: {job_id}")

        row = rows[0]
        if not row.get("PermiteEjecucionManual"):
            raise HTTPException(status_code=400, detail="Job no permite ejecución manual")

        handler = _validate_handler(row.get("Handler"))
        base_params = json.loads(row.get("ParametrosJSON") or "{}")
        run_params = dict(base_params)
        if payload and payload.parametros:
            run_params.update(payload.parametros)

        run_id = str(uuid.uuid4())[:8]
        _cc_execute("""
            INSERT INTO dbo.Scheduler_BitacoraJobs (
                JobName, RunID, Accion, DetallesJSON, Exito
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            row.get("JobName"), run_id, "INICIO_MANUAL",
            json.dumps({"job_id": job_id, "params": run_params}, ensure_ascii=False), 1
        ))

        if handler == "NETPAY_BACKFILL":
            result = await asyncio.to_thread(
                _run_netpay_backfill_sync,
                run_params,
                int(row.get("TimeoutSegundos") or 1800)
            )
        else:
            raise HTTPException(status_code=400, detail=f"Handler sin ejecutor: {handler}")

        _cc_execute("""
            UPDATE dbo.Sys_Scheduler_Jobs
            SET LastRunDate=GETDATE()
            WHERE JobID=%s
        """, (job_id,))

        _cc_execute("""
            INSERT INTO dbo.Scheduler_BitacoraJobs (
                JobName, RunID, Accion, DetallesJSON, Exito, MensajeError
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            row.get("JobName"), run_id, "EJECUCION_MANUAL_COMPLETADA",
            json.dumps(result, ensure_ascii=False), 1 if result.get("ok") else 0,
            None if result.get("ok") else result.get("output_tail", "")[-500:]
        ))

        return {
            "ok": bool(result.get("ok")),
            "job_id": job_id,
            "run_id": run_id,
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CENTRO CONTROL] Error ejecutando job manual: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor"[:500])


# ============================================================================
# ENDPOINTS: BITÁCORA DE CAMBIOS
# ============================================================================

@router.get("/bitacora")
async def obtener_bitacora(
    limite: int = Query(50, ge=1, le=200),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: cambio_codigo, deploy, config, incidente, hotfix"),
    modulo: Optional[str] = Query(None, description="Filtrar por módulo"),
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Obtiene la bitácora de cambios del sistema.
    
    La bitácora registra:
    - Cambios de código significativos
    - Deploys
    - Cambios de configuración
    - Incidentes y resoluciones
    - Hotfixes
    """
    entradas = cc_store.list_bitacora(limit=limite, tipo=tipo, modulo=modulo)
    return {
        "total": len(entradas),
        "entradas": entradas,
        "tipos_disponibles": ["cambio_codigo", "deploy", "config", "incidente", "hotfix"]
    }


@router.post("/bitacora")
async def registrar_cambio_bitacora(
    request: BitacoraEntryRequest,
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Registra un cambio en la bitácora del sistema.
    
    Tipos permitidos:
    - cambio_codigo: Modificación de código fuente
    - deploy: Despliegue a producción/staging
    - config: Cambio de configuración
    - incidente: Incidente detectado
    - hotfix: Corrección urgente
    """
    tipos_validos = ["cambio_codigo", "deploy", "config", "incidente", "hotfix"]
    if request.tipo not in tipos_validos:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo inválido. Opciones: {tipos_validos}"
        )
    
    entrada = cc_store.record_bitacora(
        request.tipo, request.modulo, request.descripcion, request.impacto,
        request.autor or current_user.get("email"), request.referencias or [], current_user.get("email")
    )
    
    # Registrar también en historial de eventos
    _registrar_evento(
        tipo="bitacora",
        modulo=request.modulo,
        mensaje=f"[{request.tipo.upper()}] {request.descripcion[:100]}",
        severidad="info",
        data={"bitacora_id": entrada["id"]}
    )
    
    return {"success": True, "entrada": entrada}

# ============================================================================
# ENDPOINTS: MÉTRICAS DE ESTABILIDAD
# ============================================================================

@router.get("/metricas")
async def obtener_metricas_estabilidad(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Obtiene métricas de estabilidad del sistema.
    
    Métricas incluidas:
    - Uptime del monitoreo
    - Checks ejecutados y tasa de éxito
    - Alertas generadas vs reconocidas
    - Última regresión detectada
    - Score de estabilidad
    """
    metricas_sql = cc_store.metrics()
    score_estabilidad = metricas_sql.get("score_estabilidad")
    if score_estabilidad is None:
        interpretacion_score = "sin_evidencia_canonica_suficiente"
    else:
        interpretacion_score = "excelente" if score_estabilidad >= 90 else (
            "bueno" if score_estabilidad >= 70 else (
                "regular" if score_estabilidad >= 50 else "crítico"
            )
        )
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metricas": metricas_sql,
        "interpretacion": {
            "score_estabilidad": interpretacion_score,
            "recomendaciones": []
        }
    }


# ============================================================================
# ENDPOINTS: BLINDAJE - VERDAD SQL, SIN MOCK
# ============================================================================

@router.get("/blindaje/modulos")
async def obtener_modulos_blindados(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """No inventa módulos: reporta el estado real del registro SQL de blindaje."""
    return cc_store.blindaje_registry_status()

# ============================================================================
# ENDPOINTS: WEBSOCKET PARA NOTIFICACIONES EN TIEMPO REAL
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket para notificaciones en tiempo real del Centro de Control.
    
    Mensajes que puede recibir el cliente:
    - conexion_establecida: Confirmación de conexión
    - heartbeat: Ping cada 30 segundos
    - alerta_critica: Alerta de severidad crítica (con sonido)
    - alerta_nueva: Nueva alerta de cualquier severidad
    - estado_cambio: Cambio en el estado general del sistema
    - fuente_caida: Una fuente de datos dejó de responder
    
    Ejemplo de mensaje:
    {
        "tipo": "alerta_critica",
        "data": {
            "alerta": {...},
            "timestamp": "2026-04-19T16:45:00Z",
            "prioridad": "alta",
            "sonido": true
        }
    }
    """
    manager = get_notification_manager()
    connection_id = await manager.connect(websocket)
    
    try:
        while True:
            # Esperar mensajes del cliente (para keep-alive o comandos)
            data = await websocket.receive_text()
            
            # Procesar comandos del cliente si es necesario
            try:
                message = json.loads(data)
                if message.get("tipo") == "ping":
                    await websocket.send_json({
                        "tipo": "pong",
                        "data": {"timestamp": datetime.now(timezone.utc).isoformat()}
                    })
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"[WS] Error en conexión {connection_id}: {e}")
        manager.disconnect(connection_id)


@router.get("/ws/status")
async def websocket_status(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Obtiene el estado del sistema de notificaciones WebSocket.
    """
    manager = get_notification_manager()
    return manager.get_status()


@router.post("/notificar/alerta-critica")
async def notificar_alerta_critica(
    alerta: Dict[str, Any],
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Envía una notificación de alerta crítica a todos los clientes conectados.
    Uso interno para testing o integración con otros sistemas.
    """
    manager = get_notification_manager()
    await manager.broadcast_alerta_critica(alerta)
    return {
        "success": True,
        "message": "Notificación enviada",
        "conexiones_notificadas": manager.connection_count
    }


@router.post("/notificar/test")
async def notificar_test(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Envía una notificación de prueba a todos los clientes conectados.
    """
    manager = get_notification_manager()
    
    test_alerta = {
        "id": f"test_{datetime.now(timezone.utc).strftime('%H%M%S')}",
        "titulo": "🔔 Notificación de Prueba",
        "severidad": "medium",
        "modulo": "Centro de Control",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mensaje": "Esta es una notificación de prueba del sistema de alertas en tiempo real."
    }
    
    await manager.broadcast_alerta_nueva(test_alerta)
    
    return {
        "success": True,
        "message": "Notificación de prueba enviada",
        "conexiones_notificadas": manager.connection_count,
        "alerta": test_alerta
    }


# Importar json para el WebSocket


# ============================================================================
# ENDPOINTS: NOTIFICACIONES POR EMAIL
# ============================================================================

@router.get("/email/config")
async def obtener_config_email(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Obtiene el estado de configuración del servicio de notificaciones por email.
    """
    return {
        "service": "Email Notifications",
        "config": get_email_config_status()
    }


@router.post("/email/test")
async def enviar_email_prueba(
    recipient: Optional[str] = None,
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Envía un email de prueba para verificar la configuración SMTP.
    
    Si no se especifica destinatario, usa el primero configurado en ALERT_EMAIL_TO.
    """
    if not is_email_configured():
        return {
            "success": False,
            "message": "Email no configurado. Verificar variables en .env",
            "config": get_email_config_status()
        }
    
    result = await send_test_email(recipient)
    return result


@router.post("/email/alerta-critica")
async def enviar_alerta_critica_email(
    alerta: Dict[str, Any],
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Envía una alerta crítica por email a todos los destinatarios configurados.
    
    Body:
    {
        "titulo": "Título de la alerta",
        "modulo": "Nombre del módulo",
        "severidad": "critical",
        "detalle": "Descripción detallada"
    }
    """
    if not is_email_configured():
        return {
            "success": False,
            "message": "Email no configurado",
            "config": get_email_config_status()
        }
    
    # Asegurar campos requeridos
    if "id" not in alerta:
        alerta["id"] = f"manual_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    if "timestamp" not in alerta:
        alerta["timestamp"] = datetime.now(timezone.utc).isoformat()
    if "severidad" not in alerta:
        alerta["severidad"] = "critical"
    
    result = await send_critical_alert_email(alerta)
    return result


# ============================================================================
# ENDPOINTS: NOTIFICACIONES POR WHATSAPP
# ============================================================================

@router.get("/whatsapp/config")
async def obtener_config_whatsapp(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Obtiene el estado de configuración del servicio de notificaciones por WhatsApp.
    """
    return {
        "service": "WhatsApp Notifications (Twilio)",
        "config": get_whatsapp_config_status()
    }


@router.post("/whatsapp/test")
async def enviar_whatsapp_prueba(
    recipient: Optional[str] = None,
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Envía un mensaje WhatsApp de prueba para verificar la configuración de Twilio.
    
    IMPORTANTE: Para WhatsApp Sandbox de Twilio, el destinatario debe haber enviado
    primero un mensaje "join <sandbox-keyword>" al número de WhatsApp de Twilio.
    
    Si no se especifica destinatario, usa el primero configurado en ALERT_WHATSAPP_TO.
    """
    if not is_whatsapp_configured():
        return {
            "success": False,
            "message": "WhatsApp no configurado. Verificar variables en .env",
            "config": get_whatsapp_config_status()
        }
    
    result = await send_test_whatsapp(recipient)
    return result


@router.post("/whatsapp/alerta-critica")
async def enviar_alerta_critica_whatsapp(
    alerta: Dict[str, Any],
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Envía una alerta crítica por WhatsApp a todos los destinatarios configurados.
    
    Body:
    {
        "titulo": "Título de la alerta",
        "modulo": "Nombre del módulo",
        "severidad": "critical",
        "detalle": "Descripción detallada"
    }
    """
    if not is_whatsapp_configured():
        return {
            "success": False,
            "message": "WhatsApp no configurado",
            "config": get_whatsapp_config_status()
        }
    
    # Asegurar campos requeridos
    if "id" not in alerta:
        alerta["id"] = f"manual_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    if "timestamp" not in alerta:
        alerta["timestamp"] = datetime.now(timezone.utc).isoformat()
    if "severidad" not in alerta:
        alerta["severidad"] = "critical"
    
    result = await send_critical_alert_whatsapp(alerta)
    return result


@router.get("/notificaciones/config")
async def obtener_config_notificaciones(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Obtiene el estado de configuración de TODOS los servicios de notificaciones:
    - Email (SMTP EDARSA)
    - WhatsApp (Twilio)
    - WebSocket (tiempo real)
    """
    manager = get_notification_manager()
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "servicios": {
            "email": {
                "nombre": "Email (SMTP EDARSA)",
                "config": get_email_config_status()
            },
            "whatsapp": {
                "nombre": "WhatsApp (Twilio)",
                "config": get_whatsapp_config_status()
            },
            "websocket": {
                "nombre": "WebSocket (Tiempo Real)",
                "config": {
                    "enabled": True,
                    "connections": manager.connection_count,
                    "status": manager.get_status()
                }
            }
        },
        "flujo_alertas_criticas": {
            "descripcion": "Cuando se crea una alerta con severidad 'critical', se notifica por todos los canales configurados",
            "canales": ["WebSocket (instantáneo)", "Email (async)", "WhatsApp (async)"]
        }
    }


# ============================================================================
# ENDPOINTS: GESTIÓN DE DESTINATARIOS DE ALERTAS
# ============================================================================

@router.get("/destinatarios")
async def listar_destinatarios(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: email o whatsapp"),
    solo_activos: bool = Query(False, description="Solo mostrar destinatarios activos"),
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Lista todos los destinatarios de alertas configurados.
    
    Los destinatarios se almacenan en MongoDB y son utilizados por los
    servicios de email y WhatsApp para enviar alertas críticas.
    """
    try:
        recipients = get_all_recipients(tipo=tipo, solo_activos=solo_activos)
        return {
            "total": len(recipients),
            "destinatarios": recipients
        }
    except Exception as e:
        logger.error(f"[RECIPIENTS] Error listando destinatarios: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/destinatarios/resumen")
async def resumen_destinatarios(current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))):
    """
    Obtiene un resumen de los destinatarios configurados por tipo.
    """
    try:
        return get_recipients_summary()
    except Exception as e:
        logger.error(f"[RECIPIENTS] Error obteniendo resumen: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/destinatarios")
async def crear_destinatario(
    request: RecipientCreateRequest,
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Agrega un nuevo destinatario de alertas.
    
    Tipos válidos:
    - email: Dirección de correo electrónico
    - whatsapp: Número de teléfono en formato E.164 (+521234567890)
    
    Para WhatsApp con Twilio Sandbox, el destinatario debe haber enviado
    primero "join <sandbox-keyword>" al número de Twilio.
    """
    try:
        recipient = add_recipient(
            tipo=request.tipo,
            destinatario=request.destinatario,
            nombre=request.nombre,
            created_by=current_user.get("email")
        )
        return {
            "success": True,
            "message": f"Destinatario {request.tipo} agregado correctamente",
            "destinatario": recipient
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[RECIPIENTS] Error creando destinatario: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/destinatarios/{recipient_id}")
async def actualizar_destinatario(
    recipient_id: str,
    request: RecipientUpdateRequest,
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Actualiza un destinatario existente.
    
    Permite:
    - Activar/desactivar el destinatario
    - Cambiar el nombre
    """
    try:
        recipient = update_recipient(
            recipient_id=recipient_id,
            activo=request.activo,
            nombre=request.nombre
        )
        return {
            "success": True,
            "message": "Destinatario actualizado correctamente",
            "destinatario": recipient
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[RECIPIENTS] Error actualizando destinatario: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete("/destinatarios/{recipient_id}")
async def eliminar_destinatario(
    recipient_id: str,
    current_user: Dict = Depends(require_explicit_permission("CENTRO_CONTROL_VER"))
):
    """
    Elimina un destinatario de alertas.
    """
    try:
        delete_recipient(recipient_id)
        return {
            "success": True,
            "message": "Destinatario eliminado correctamente"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[RECIPIENTS] Error eliminando destinatario: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
