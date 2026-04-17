"""
FASE 2A - Router Principal Módulo Operativo
CAB-003 | EDARSA HUB

Prefijo: /api/v2
Agrupa todos los sub-routers del módulo operativo.
"""
from fastapi import APIRouter
from .routes.workflow_routes import router as workflow_router
from .routes.tarea_routes import router as tarea_router
from .routes.justificacion_routes import router as justificacion_router
from .routes.auditoria_routes import router as auditoria_router
from .routes.configuracion_routes import router as configuracion_router
from .routes.dashboard_routes import router as dashboard_router
from .routes.notificaciones_routes import router as notificaciones_router

router_fase2_operativo = APIRouter()


# Health check del módulo
@router_fase2_operativo.get("/health", tags=["Fase2-Health"])
async def health_check():
    """
    Health check del módulo operativo.
    Verifica que el módulo está correctamente cargado.
    """
    return {
        "status": "ok",
        "module": "fase2_operativo",
        "version": "2A",
        "description": "Módulo Operativo de Automatización de Inventarios"
    }


# Incluir sub-routers
router_fase2_operativo.include_router(
    workflow_router,
    prefix="/workflows",
    tags=["Fase2-Workflows"]
)

router_fase2_operativo.include_router(
    tarea_router,
    prefix="/tareas",
    tags=["Fase2-Tareas"]
)

router_fase2_operativo.include_router(
    justificacion_router,
    prefix="/justificaciones",
    tags=["Fase2-Justificaciones"]
)

router_fase2_operativo.include_router(
    auditoria_router,
    prefix="/auditoria",
    tags=["Fase2-Auditoria"]
)

router_fase2_operativo.include_router(
    configuracion_router,
    prefix="/configuracion",
    tags=["Fase2-Configuracion"]
)

router_fase2_operativo.include_router(
    dashboard_router,
    prefix="/dashboard",
    tags=["Fase2-Dashboard"]
)

router_fase2_operativo.include_router(
    notificaciones_router,
    tags=["Fase2-Notificaciones"]
)
