from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Endpoints de Dashboard
CAB-003 | EDARSA HUB - Fase 2A / 2B.4
PROTEGIDO CON RBAC (Fase 3.1)

Expone KPIs, resúmenes y alertas vía HTTP.
Incluye métricas de SLA.

Permisos requeridos:
- Todos los endpoints requieren autenticación y filtran por empresas_permitidas del usuario
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from ..services.operativo_service import OperativoService
from ..services.workflow_service import WorkflowService
from ..services.tarea_service import TareaService
from ..services.sla_service import get_sla_service
from ..db_utils import get_database

# RBAC - Fase 3.1
from core.security import get_current_user, get_user_empresas_permitidas, get_servers_for_empresas
# P0 (2026-06): resolución canónica única de unidad (puerta única)
from core.corporate_filters.request_resolver import resolve_unidad_scope

router = APIRouter()


def get_db():
    """Obtiene conexión a la base de datos."""
    return get_database()


async def get_user_server_ids(current_user: Dict[str, Any]) -> list:
    """
    Obtiene los server_ids permitidos para el usuario basándose en sus empresas_permitidas.
    Retorna lista vacía si el usuario no tiene permisos.
    """
    empresas_permitidas = await get_user_empresas_permitidas(current_user)
    if not empresas_permitidas:
        return []
    server_ids = await get_servers_for_empresas(empresas_permitidas)
    return server_ids


@router.get("/resumen")
async def obtener_resumen_dashboard(
    unidad: Optional[str] = Query(None, description="Unidad de negocio canónica (unidad_codigo o id). Contrato nuevo."),
    server_id: Optional[str] = Query(None, description="DEPRECATED: usar 'unidad'. Compatibilidad temporal."),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene un resumen completo para el dashboard.
    PROTEGIDO: Filtra por empresas_permitidas del usuario.
    
    Contrato canónico: el frontend envía **unidad** (codigo o id). El backend
    valida permisos y resuelve server_id/sucursal. `server_id` queda deprecated.
    """
    try:
        db = get_db()
        
        # Puerta única: resolver unidad canónica (valida permiso + server_id/sucursal)
        scope = await resolve_unidad_scope(current_user, unidad=unidad, server_id_legacy=server_id)
        
        operativo_svc = OperativoService(db)
        resumen = await operativo_svc.obtener_resumen_dashboard(
            server_ids=scope.effective_server_ids,
            sucursal_ids=scope.sucursal_labels
        )
        return resumen
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alertas")
async def obtener_alertas(
    unidad: Optional[str] = Query(None, description="Unidad de negocio canónica (unidad_codigo o id). Contrato nuevo."),
    server_id: Optional[str] = Query(None, description="DEPRECATED: usar 'unidad'. Compatibilidad temporal."),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene las alertas activas del sistema.
    PROTEGIDO: Filtra por empresas_permitidas del usuario.
    Acepta filtro opcional por unidad de negocio (server_id).
    
    Tipos de alertas:
    - **TAREA_VENCIDA**: Tareas que excedieron su fecha límite
    - **WORKFLOW_ESCALADO**: Workflows que requieren atención especial
    """
    try:
        db = get_db()
        
        # Puerta única: resolver unidad canónica (valida permiso + server_id/sucursal)
        scope = await resolve_unidad_scope(current_user, unidad=unidad, server_id_legacy=server_id)
        
        operativo_svc = OperativoService(db)
        alertas = await operativo_svc.obtener_alertas_activas(
            server_ids=scope.effective_server_ids,
            sucursal_ids=scope.sucursal_labels
        )
        return {
            "alertas": alertas,
            "total": len(alertas),
            "tiene_alertas_criticas": any(a["severidad"] == "ALTA" for a in alertas)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/por-estado")
async def obtener_workflows_por_estado(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene conteo de workflows agrupados por estado.
    PROTEGIDO: Filtra por empresas_permitidas del usuario.
    """
    try:
        db = get_db()
        
        # Obtener server_ids permitidos para el usuario
        server_ids = await get_user_server_ids(current_user)
        
        workflow_svc = WorkflowService(db)
        resumen = await workflow_svc.resumen_por_estado(server_ids=server_ids)
        total = sum(resumen.values()) if resumen else 0
        
        return {
            "por_estado": resumen,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tareas/por-estado")
async def obtener_tareas_por_estado(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene conteo de tareas agrupadas por estado.
    PROTEGIDO: Filtra por empresas_permitidas del usuario.
    """
    try:
        db = get_db()
        
        # Obtener server_ids permitidos para el usuario
        server_ids = await get_user_server_ids(current_user)
        
        tarea_svc = TareaService(db)
        resumen = await tarea_svc.resumen_por_estado(server_ids=server_ids)
        total = sum(resumen.values()) if resumen else 0
        
        return {
            "por_estado": resumen,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tareas/vencidas/conteo")
async def obtener_conteo_tareas_vencidas(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene el conteo de tareas vencidas.
    PROTEGIDO: Filtra por empresas_permitidas del usuario.
    """
    try:
        db = get_db()
        
        # Obtener server_ids permitidos para el usuario
        server_ids = await get_user_server_ids(current_user)
        
        tarea_svc = TareaService(db)
        vencidas = await tarea_svc.obtener_tareas_vencidas(server_ids=server_ids)
        
        return {
            "tareas_vencidas": len(vencidas),
            "detalle": vencidas[:10] if vencidas else []  # Primeras 10
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpis")
async def obtener_kpis(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene KPIs principales del módulo operativo.
    PROTEGIDO: Filtra por empresas_permitidas del usuario.
    Incluye métricas de cumplimiento SLA.
    """
    try:
        db = get_db()
        
        # Obtener server_ids permitidos para el usuario
        server_ids = await get_user_server_ids(current_user)
        
        workflow_svc = WorkflowService(db)
        tarea_svc = TareaService(db)
        sla_svc = get_sla_service(db)
        
        workflows_por_estado = await workflow_svc.resumen_por_estado(server_ids=server_ids)
        tareas_por_estado = await tarea_svc.resumen_por_estado(server_ids=server_ids)
        tareas_vencidas = await tarea_svc.obtener_tareas_vencidas(server_ids=server_ids)
        
        # Métricas SLA (por ahora sin filtro de server_ids en SLA service)
        metricas_sla = await sla_svc.obtener_metricas_globales()
        
        total_workflows = sum(workflows_por_estado.values()) if workflows_por_estado else 0
        cerrados = workflows_por_estado.get("CERRADO", 0)
        
        return {
            "total_workflows": total_workflows,
            "workflows_cerrados": cerrados,
            "workflows_activos": total_workflows - cerrados,
            "workflows_pendientes_asignacion": workflows_por_estado.get("PENDIENTE_ASIGNACION", 0),
            "workflows_en_auditoria": workflows_por_estado.get("EN_AUDITORIA", 0),
            "workflows_escalados": workflows_por_estado.get("ESCALADO", 0),
            "tareas_pendientes": tareas_por_estado.get("PENDIENTE", 0) + tareas_por_estado.get("EN_PROGRESO", 0),
            "tareas_vencidas": len(tareas_vencidas),
            "tasa_cierre": round(cerrados / total_workflows * 100, 2) if total_workflows > 0 else 0,
            # Métricas SLA
            "sla": {
                "cumplimiento_porcentaje": metricas_sla["cumplimiento"]["porcentaje"],
                "tareas_en_tiempo": metricas_sla["activas"]["por_estado"].get("EN_TIEMPO", 0),
                "tareas_advertencia": metricas_sla["activas"]["por_estado"].get("ADVERTENCIA", 0),
                "tareas_urgentes": metricas_sla["activas"]["por_estado"].get("URGENTE", 0),
                "tareas_vencidas_sla": metricas_sla["activas"]["por_estado"].get("VENCIDA", 0),
                "promedio_respuesta_horas": metricas_sla["tiempos_promedio"]["respuesta_horas"],
                "promedio_resolucion_horas": metricas_sla["tiempos_promedio"]["resolucion_horas"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
