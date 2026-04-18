"""
EDARSA HUB - Notification API Routes
====================================
Subfase 2B.5 + 2B.5.1 - Endpoints REST para sistema de notificaciones.
PROTEGIDO CON RBAC (Fase 2D)

Permisos requeridos:
- GET /config, /templates, /log, /stats - NOTIFICACIONES_VER
- POST /config, /templates - NOTIFICACIONES_CONFIGURAR
- PUT /config/*, /templates/* - NOTIFICACIONES_CONFIGURAR
- POST /test, /test-real - NOTIFICACIONES_ENVIAR
- POST /reprocesar, /inicializar - NOTIFICACIONES_CONFIGURAR

Endpoints:
- /api/v2/notificaciones-whatsapp/config - Configuraciones
- /api/v2/notificaciones-whatsapp/templates - Templates
- /api/v2/notificaciones-whatsapp/log - Logs de auditoría
- /api/v2/notificaciones-whatsapp/test - Prueba de envío (mock)
- /api/v2/notificaciones-whatsapp/test-real - Prueba de envío (Twilio real)
- /api/v2/notificaciones-whatsapp/provider-status - Estado de providers
"""

from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

import logging

# RBAC - Fase 2D
from core.rbac.middleware import require_permission

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
    activo: Optional[bool] = None,
    current_user: dict = Depends(require_permission("NOTIFICACIONES_VER"))
):
    """Lista configuraciones de notificación."""
    db = get_db()
    from core.communications.notifications.repository import NotificationRepository
    repo = NotificationRepository(db)
    
    configs = await repo.get_all_configs(modulo=modulo, canal=canal, activo=activo)
    return {"items": configs, "total": len(configs)}


@router.get("/config/{config_id}")
async def get_config(
    config_id: str,
    current_user: dict = Depends(require_permission("NOTIFICACIONES_VER"))
):
    """Obtiene una configuración por ID."""
    db = get_db()
    config = await db.notification_config.find_one({"id": config_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return config


@router.post("/config")
async def create_config(
    request: ConfigCreateRequest,
    current_user: dict = Depends(require_permission("NOTIFICACIONES_CONFIGURAR"))
):
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
async def update_config(
    config_id: str,
    request: ConfigUpdateRequest,
    current_user: dict = Depends(require_permission("NOTIFICACIONES_CONFIGURAR"))
):
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
    activo: Optional[bool] = None,
    current_user: dict = Depends(require_permission("NOTIFICACIONES_VER"))
):
    """Lista templates de notificación."""
    db = get_db()
    from core.communications.notifications.repository import NotificationRepository
    repo = NotificationRepository(db)
    
    templates = await repo.get_all_templates(canal=canal, activo=activo)
    return {"items": templates, "total": len(templates)}


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    current_user: dict = Depends(require_permission("NOTIFICACIONES_VER"))
):
    """Obtiene un template por ID."""
    db = get_db()
    from core.communications.notifications.repository import NotificationRepository
    repo = NotificationRepository(db)
    
    template = await repo.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    return template


@router.post("/templates")
async def create_template(
    request: TemplateCreateRequest,
    current_user: dict = Depends(require_permission("NOTIFICACIONES_CONFIGURAR"))
):
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
async def update_template(
    template_id: str,
    request: TemplateUpdateRequest,
    current_user: dict = Depends(require_permission("NOTIFICACIONES_CONFIGURAR"))
):
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
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_permission("NOTIFICACIONES_VER"))
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
    fecha_hasta: Optional[str] = None,
    current_user: dict = Depends(require_permission("NOTIFICACIONES_VER"))
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
async def get_queue_status(
    current_user: dict = Depends(require_permission("NOTIFICACIONES_VER"))
):
    """Obtiene estado actual de la cola."""
    db = get_db()
    from core.communications.audit.audit_service import NotificationAuditService
    audit_service = NotificationAuditService(db)
    
    return await audit_service.get_queue_status()


# =============================================================================
# ACCIONES
# =============================================================================

@router.post("/test")
async def test_notification(
    request: TestNotificationRequest,
    current_user: dict = Depends(require_permission("NOTIFICACIONES_ENVIAR"))
):
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
async def reprocess_queue(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_permission("NOTIFICACIONES_CONFIGURAR"))
):
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
async def initialize_notification_system(
    current_user: dict = Depends(require_permission("NOTIFICACIONES_CONFIGURAR"))
):
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
async def list_providers(
    current_user: dict = Depends(require_permission("NOTIFICACIONES_VER"))
):
    """Lista providers configurados."""
    db = get_db()
    
    providers = await db.notification_provider_config.find(
        {}, {"_id": 0}
    ).to_list(100)
    
    return {"items": providers, "total": len(providers)}


@router.get("/providers/{provider_id}")
async def get_provider(
    provider_id: str,
    current_user: dict = Depends(require_permission("NOTIFICACIONES_VER"))
):
    """Obtiene un provider por ID."""
    db = get_db()
    
    provider = await db.notification_provider_config.find_one(
        {"id": provider_id}, {"_id": 0}
    )
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider no encontrado")
    
    return provider


# =============================================================================
# SUBFASE 2B.5.1 - TWILIO WHATSAPP REAL
# =============================================================================

@router.get("/provider-status")
async def get_provider_runtime_status(
    current_user: dict = Depends(require_permission("NOTIFICACIONES_VER"))
):
    """
    Obtiene estado en tiempo real de los providers disponibles.
    
    Muestra:
    - Providers cargados
    - Disponibilidad (credenciales configuradas)
    - Providers aptos para envío real
    """
    db = get_db()
    from core.communications.dispatcher.dispatcher import NotificationDispatcher
    
    dispatcher = NotificationDispatcher(db)
    await dispatcher.initialize_providers()
    
    return dispatcher.get_providers_status()


class TestRealNotificationRequest(BaseModel):
    """Schema para prueba de notificación real."""
    template_codigo: str
    destinatario_telefono: str
    payload: dict = {}
    provider: str = "twilio"  # twilio o mock


@router.post("/test-real")
async def test_real_notification(
    request: TestRealNotificationRequest,
    current_user: dict = Depends(require_permission("NOTIFICACIONES_ENVIAR"))
):
    """
    Envía una notificación de prueba usando provider REAL (Twilio).
    
    ADVERTENCIA: Este endpoint envía mensajes REALES si Twilio está configurado.
    Usar solo para pruebas controladas.
    
    Requiere variables de entorno:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN
    - TWILIO_WHATSAPP_FROM
    """
    db = get_db()
    from core.communications.dispatcher.dispatcher import NotificationDispatcher
    from core.communications.templates.template_service import TemplateService
    
    # Inicializar dispatcher y providers
    dispatcher = NotificationDispatcher(db)
    await dispatcher.initialize_providers()
    
    # Verificar que el provider solicitado esté disponible
    provider = dispatcher.get_provider(request.provider)
    if not provider:
        available_providers = list(dispatcher._providers.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{request.provider}' no disponible. Disponibles: {available_providers}"
        )
    
    # Verificar disponibilidad de Twilio
    if request.provider in ["twilio", "twilio_whatsapp", "twilio_sdk"]:
        if hasattr(provider, 'is_available') and not provider.is_available():
            raise HTTPException(
                status_code=400,
                detail="Twilio provider no está disponible. Verifica TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM"
            )
    
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
    
    # Validar destinatario
    validation = provider.validate_recipient(request.destinatario_telefono)
    if not validation.get("valid"):
        raise HTTPException(
            status_code=400,
            detail=f"Teléfono inválido: {validation.get('error')}"
        )
    
    # Enviar mensaje
    response = await provider.send_message(
        recipient=request.destinatario_telefono,
        message=mensaje,
        metadata={
            "test": True,
            "template": request.template_codigo,
            "payload": request.payload
        }
    )
    
    return {
        "success": response.success,
        "provider": request.provider,
        "provider_type": provider.__class__.__name__,
        "mensaje_renderizado": mensaje,
        "destinatario": validation.get("normalized") or request.destinatario_telefono,
        "twilio_format": validation.get("twilio_format"),
        "provider_response": response.to_dict(),
        "message_id": response.message_id
    }


@router.post("/config/set-twilio")
async def configure_twilio_provider(
    current_user: dict = Depends(require_permission("NOTIFICACIONES_CONFIGURAR"))
):
    """
    Crea o actualiza la configuración del provider Twilio en la BD.
    
    Esto permite cambiar eventos para usar Twilio en lugar de Mock.
    Las credenciales siguen viniendo de variables de entorno.
    """
    db = get_db()
    
    # Crear/actualizar config de provider Twilio
    twilio_config = {
        "id": "provider_twilio",
        "canal": "whatsapp",
        "provider": "twilio",
        "activo": True,
        "base_url": "https://api.twilio.com",
        "account_id": None,  # Se lee de env TWILIO_ACCOUNT_SID
        "token_ref": "TWILIO_AUTH_TOKEN",
        "remitente": None,  # Se lee de env TWILIO_WHATSAPP_FROM
        "metadata": {
            "description": "Twilio WhatsApp Business API (SDK oficial)",
            "tipo": "sdk",
            "documentacion": "https://www.twilio.com/docs/whatsapp"
        }
    }
    
    # Upsert
    result = await db.notification_provider_config.update_one(
        {"id": "provider_twilio"},
        {
            "$set": twilio_config,
            "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}
        },
        upsert=True
    )
    
    return {
        "success": True,
        "message": "Configuración de Twilio creada/actualizada",
        "config": twilio_config,
        "upserted": result.upserted_id is not None
    }


@router.put("/config/{config_id}/set-provider")
async def update_event_provider(
    config_id: str,
    provider: str = "twilio",
    modo: str = "real",
    current_user: dict = Depends(require_permission("NOTIFICACIONES_CONFIGURAR"))
):
    """
    Cambia el provider de un evento de notificación.
    
    Args:
        config_id: ID de la configuración del evento
        provider: "mock" o "twilio"
        modo: "mock" o "real"
    
    Ejemplo: Cambiar SLA_VENCIDO para usar Twilio real
    """
    db = get_db()
    
    if provider not in ["mock", "twilio"]:
        raise HTTPException(status_code=400, detail="Provider debe ser 'mock' o 'twilio'")
    
    if modo not in ["mock", "real"]:
        raise HTTPException(status_code=400, detail="Modo debe ser 'mock' o 'real'")
    
    result = await db.notification_config.update_one(
        {"id": config_id},
        {
            "$set": {
                "provider": provider,
                "modo_envio": modo,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Configuración no encontrada: {config_id}")
    
    # Obtener config actualizada
    config = await db.notification_config.find_one({"id": config_id}, {"_id": 0})
    
    return {
        "success": True,
        "message": f"Evento actualizado para usar {provider} en modo {modo}",
        "config": config
    }

