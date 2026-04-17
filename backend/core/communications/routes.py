"""
EDARSA HUB - Notification API Routes
====================================
Subfase 2B.5 - Endpoints REST para sistema de notificaciones.

Endpoints:
- /api/v2/notificaciones/config - Configuraciones
- /api/v2/notificaciones/templates - Templates
- /api/v2/notificaciones/log - Logs de auditoría
- /api/v2/notificaciones/test - Prueba de envío
- /api/v2/notificaciones/reprocesar - Reprocesar cola
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/notificaciones-whatsapp", tags=["Notificaciones WhatsApp"])

# =============================================================================
# INYECCIÓN DE DEPENDENCIA: MongoDB
# =============================================================================

_db = None


def init_notifications_routes(database) -> None:
    """
    Inicializa las rutas con la conexión a MongoDB.
    
    Args:
        database: Instancia de AsyncIOMotorDatabase
    """
    global _db
    _db = database
    logger.info("Notification routes initialized")


def get_db():
    """Obtiene la conexión a MongoDB inyectada."""
    if _db is None:
        raise RuntimeError("Notification routes not initialized. Call init_notifications_routes(db) first.")
    return _db


# =============================================================================
# SCHEMAS DE REQUEST/RESPONSE
# =============================================================================

class ConfigCreateRequest(BaseModel):
    canal: str = "whatsapp"
    modulo: str = "inventarios"
    evento: str
    provider: str = "mock"
    modo_envio: str = "mock"
    template_codigo: str
    enviar_a_responsable: bool = True
    enviar_a_supervisor: bool = False
    enviar_a_gerente: bool = False
    ventana_duplicidad_minutos: int = 60


class ConfigUpdateRequest(BaseModel):
    activo: Optional[bool] = None
    modo_envio: Optional[str] = None
    template_codigo: Optional[str] = None
    enviar_a_responsable: Optional[bool] = None
    enviar_a_supervisor: Optional[bool] = None
    enviar_a_gerente: Optional[bool] = None
    ventana_duplicidad_minutos: Optional[int] = None


class TemplateCreateRequest(BaseModel):
    canal: str = "whatsapp"
    codigo: str
    nombre: str
    template_texto: str
    variables: List[str] = []
    idioma: str = "es"


class TemplateUpdateRequest(BaseModel):
    nombre: Optional[str] = None
    activo: Optional[bool] = None
    template_texto: Optional[str] = None
    variables: Optional[List[str]] = None


class TestNotificationRequest(BaseModel):
    template_codigo: str
    destinatario_telefono: str
    payload: dict = {}
    modo: str = "mock"


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

@router.get("/config")
async def list_configs(
    modulo: Optional[str] = None,
    canal: Optional[str] = None,
    activo: Optional[bool] = None
):
    """Lista configuraciones de notificación."""
    db = get_db()
    from core.communications.notifications.repository import NotificationRepository
    repo = NotificationRepository(db)
    
    configs = await repo.get_all_configs(modulo=modulo, canal=canal, activo=activo)
    return {"items": configs, "total": len(configs)}


@router.get("/config/{config_id}")
async def get_config(config_id: str):
    """Obtiene una configuración por ID."""
    db = get_db()
    config = await db.notification_config.find_one({"id": config_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return config


@router.post("/config")
async def create_config(request: ConfigCreateRequest):
    """Crea una nueva configuración."""
    db = get_db()
    from core.communications.notifications.schemas import NotificationConfig
    from core.communications.notifications.repository import NotificationRepository
    
    repo = NotificationRepository(db)
    
    # Verificar que no exista
    existing = await repo.get_config(request.canal, request.modulo, request.evento)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Ya existe configuración para {request.canal}/{request.modulo}/{request.evento}"
        )
    
    config = NotificationConfig(
        canal=request.canal,
        modulo=request.modulo,
        evento=request.evento,
        provider=request.provider,
        modo_envio=request.modo_envio,
        template_codigo=request.template_codigo,
        enviar_a_responsable=request.enviar_a_responsable,
        enviar_a_supervisor=request.enviar_a_supervisor,
        enviar_a_gerente=request.enviar_a_gerente,
        ventana_duplicidad_minutos=request.ventana_duplicidad_minutos
    )
    
    result = await repo.create_config(config)
    return {"success": True, "config": result}


@router.put("/config/{config_id}")
async def update_config(config_id: str, request: ConfigUpdateRequest):
    """Actualiza una configuración."""
    db = get_db()
    from core.communications.notifications.repository import NotificationRepository
    repo = NotificationRepository(db)
    
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    result = await repo.update_config(config_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    return {"success": True, "config": result}


# =============================================================================
# TEMPLATES
# =============================================================================

@router.get("/templates")
async def list_templates(
    canal: Optional[str] = None,
    activo: Optional[bool] = None
):
    """Lista templates de notificación."""
    db = get_db()
    from core.communications.notifications.repository import NotificationRepository
    repo = NotificationRepository(db)
    
    templates = await repo.get_all_templates(canal=canal, activo=activo)
    return {"items": templates, "total": len(templates)}


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Obtiene un template por ID."""
    db = get_db()
    from core.communications.notifications.repository import NotificationRepository
    repo = NotificationRepository(db)
    
    template = await repo.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    return template


@router.post("/templates")
async def create_template(request: TemplateCreateRequest):
    """Crea un nuevo template."""
    db = get_db()
    from core.communications.notifications.schemas import NotificationTemplate
    from core.communications.notifications.repository import NotificationRepository
    
    repo = NotificationRepository(db)
    
    # Verificar que no exista
    existing = await repo.get_template(request.canal, request.codigo)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Ya existe template con código {request.codigo}"
        )
    
    template = NotificationTemplate(
        canal=request.canal,
        codigo=request.codigo,
        nombre=request.nombre,
        template_texto=request.template_texto,
        variables=request.variables,
        idioma=request.idioma
    )
    
    result = await repo.create_template(template)
    return {"success": True, "template": result}


@router.put("/templates/{template_id}")
async def update_template(template_id: str, request: TemplateUpdateRequest):
    """Actualiza un template."""
    db = get_db()
    from core.communications.notifications.repository import NotificationRepository
    repo = NotificationRepository(db)
    
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    result = await repo.update_template(template_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    
    return {"success": True, "template": result}


# =============================================================================
# LOG / AUDITORÍA
# =============================================================================

@router.get("/log")
async def get_notification_logs(
    workflow_id: Optional[str] = None,
    referencia_id: Optional[str] = None,
    evento_negocio: Optional[str] = None,
    destinatario: Optional[str] = None,
    estado_envio: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Consulta logs de notificaciones."""
    db = get_db()
    from core.communications.audit.audit_service import NotificationAuditService
    audit_service = NotificationAuditService(db)
    
    result = await audit_service.get_logs(
        workflow_id=workflow_id,
        referencia_id=referencia_id,
        evento_negocio=evento_negocio,
        destinatario=destinatario,
        estado_envio=estado_envio,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=limit
    )
    
    return result


@router.get("/stats")
async def get_notification_stats(
    modulo: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
):
    """Obtiene estadísticas de notificaciones."""
    db = get_db()
    from core.communications.audit.audit_service import NotificationAuditService
    audit_service = NotificationAuditService(db)
    
    return await audit_service.get_stats(
        modulo=modulo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )


@router.get("/queue-status")
async def get_queue_status():
    """Obtiene estado actual de la cola."""
    db = get_db()
    from core.communications.audit.audit_service import NotificationAuditService
    audit_service = NotificationAuditService(db)
    
    return await audit_service.get_queue_status()


# =============================================================================
# ACCIONES
# =============================================================================

@router.post("/test")
async def test_notification(request: TestNotificationRequest):
    """
    Envía una notificación de prueba.
    
    Útil para verificar configuración y templates.
    """
    db = get_db()
    from core.communications.templates.template_service import TemplateService
    from core.communications.dispatcher.dispatcher import NotificationDispatcher
    
    # Renderizar template
    template_service = TemplateService(db)
    mensaje = await template_service.render_template(
        codigo=request.template_codigo,
        variables=request.payload,
        canal="whatsapp"
    )
    
    if not mensaje:
        raise HTTPException(
            status_code=404, 
            detail=f"Template no encontrado: {request.template_codigo}"
        )
    
    # Enviar usando dispatcher
    dispatcher = NotificationDispatcher(db)
    await dispatcher.initialize_providers()
    
    # Usar mock provider para pruebas
    provider = dispatcher.get_provider("mock")
    if not provider:
        raise HTTPException(status_code=500, detail="Mock provider no disponible")
    
    response = await provider.send_message(
        recipient=request.destinatario_telefono,
        message=mensaje,
        metadata={"test": True, "payload": request.payload}
    )
    
    return {
        "success": response.success,
        "mensaje_renderizado": mensaje,
        "destinatario": request.destinatario_telefono,
        "provider_response": response.to_dict()
    }


@router.post("/reprocesar")
async def reprocess_queue(limit: int = Query(50, ge=1, le=200)):
    """
    Reprocesa items pendientes de la cola.
    
    Útil para despachar manualmente en pruebas controladas.
    """
    db = get_db()
    from core.communications.dispatcher.dispatcher import NotificationDispatcher
    
    dispatcher = NotificationDispatcher(db)
    await dispatcher.initialize_providers()
    
    result = await dispatcher.process_queue(limit=limit)
    
    return {
        "success": True,
        "resultado": result
    }


@router.post("/inicializar")
async def initialize_notification_system():
    """
    Inicializa/reinicializa el sistema de notificaciones.
    
    Crea índices y siembra datos iniciales.
    """
    db = get_db()
    from core.communications.scripts import init_notification_system
    
    await init_notification_system(db)
    
    return {
        "success": True,
        "mensaje": "Sistema de notificaciones inicializado correctamente"
    }


# =============================================================================
# PROVIDERS
# =============================================================================

@router.get("/providers")
async def list_providers():
    """Lista providers configurados."""
    db = get_db()
    
    providers = await db.notification_provider_config.find(
        {}, {"_id": 0}
    ).to_list(100)
    
    return {"items": providers, "total": len(providers)}


@router.get("/providers/{provider_id}")
async def get_provider(provider_id: str):
    """Obtiene un provider por ID."""
    db = get_db()
    
    provider = await db.notification_provider_config.find_one(
        {"id": provider_id}, {"_id": 0}
    )
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider no encontrado")
    
    return provider
