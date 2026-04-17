"""
Endpoints de Dashboard
CAB-003 | EDARSA HUB - Fase 2A

Expone KPIs, resúmenes y alertas vía HTTP.
"""
from fastapi import APIRouter, HTTPException
from ..services.operativo_service import OperativoService
from ..services.workflow_service import WorkflowService
from ..services.tarea_service import TareaService
from ..db_utils import get_database

router = APIRouter()


def get_db():
    """Obtiene conexión a la base de datos."""
    return get_database()


@router.get("/resumen")
async def obtener_resumen_dashboard():
    """
    Obtiene un resumen completo para el dashboard.
    
    Incluye:
    - **workflows**: Conteos por estado y total
    - **tareas**: Conteos por estado y vencidas
    - **alertas**: Conteo de alertas activas
    - **parametros**: Configuración operativa actual
    """
    try:
        db = get_db()
        operativo_svc = OperativoService(db)
        
        resumen = await operativo_svc.obtener_resumen_dashboard()
        return resumen
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alertas")
async def obtener_alertas():
    """
    Obtiene las alertas activas del sistema.
    
    Tipos de alertas:
    - **TAREA_VENCIDA**: Tareas que excedieron su fecha límite
    - **WORKFLOW_ESCALADO**: Workflows que requieren atención especial
    """
    try:
        db = get_db()
        operativo_svc = OperativoService(db)
        
        alertas = await operativo_svc.obtener_alertas_activas()
        return {
            "alertas": alertas,
            "total": len(alertas),
            "tiene_alertas_criticas": any(a["severidad"] == "ALTA" for a in alertas)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/por-estado")
async def obtener_workflows_por_estado():
    """
    Obtiene conteo de workflows agrupados por estado.
    """
    try:
        db = get_db()
        workflow_svc = WorkflowService(db)
        
        resumen = await workflow_svc.resumen_por_estado()
        total = sum(resumen.values()) if resumen else 0
        
        return {
            "por_estado": resumen,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tareas/por-estado")
async def obtener_tareas_por_estado():
    """
    Obtiene conteo de tareas agrupadas por estado.
    """
    try:
        db = get_db()
        tarea_svc = TareaService(db)
        
        resumen = await tarea_svc.resumen_por_estado()
        total = sum(resumen.values()) if resumen else 0
        
        return {
            "por_estado": resumen,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tareas/vencidas/conteo")
async def obtener_conteo_tareas_vencidas():
    """
    Obtiene el conteo de tareas vencidas.
    """
    try:
        db = get_db()
        tarea_svc = TareaService(db)
        
        vencidas = await tarea_svc.obtener_tareas_vencidas()
        
        return {
            "tareas_vencidas": len(vencidas),
            "detalle": vencidas[:10] if vencidas else []  # Primeras 10
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpis")
async def obtener_kpis():
    """
    Obtiene KPIs principales del módulo operativo.
    """
    try:
        db = get_db()
        workflow_svc = WorkflowService(db)
        tarea_svc = TareaService(db)
        
        workflows_por_estado = await workflow_svc.resumen_por_estado()
        tareas_por_estado = await tarea_svc.resumen_por_estado()
        tareas_vencidas = await tarea_svc.obtener_tareas_vencidas()
        
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
            "tasa_cierre": round(cerrados / total_workflows * 100, 2) if total_workflows > 0 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
