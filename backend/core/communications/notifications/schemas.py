"""
EDARSA HUB - Notification Schemas
=================================
Subfase 2B.5 - Modelos Pydantic para sistema de notificaciones.

Colecciones MongoDB:
- notification_config
- notification_provider_config
- notification_templates
- notification_queue
- notification_log
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
import uuid


# =============================================================================
# ENUMERACIONES
# =============================================================================

class EventType(str, Enum):
    """Tipos de eventos que disparan notificaciones."""
    # Tareas
    ASIGNACION_TAREA = "ASIGNACION_TAREA"
    DIFERENCIA_DETECTADA = "DIFERENCIA_DETECTADA"
    
    # SLA
    SLA_POR_VENCER = "SLA_POR_VENCER"
    SLA_VENCIDO = "SLA_VENCIDO"
    SLA_ESCALADO = "SLA_ESCALADO"
    
    # Auditoría
    JUSTIFICACION_RECHAZADA = "JUSTIFICACION_RECHAZADA"
    DECISION_AUDITORIA = "DECISION_AUDITORIA"
    
    # Workflow
    CIERRE_WORKFLOW = "CIERRE_WORKFLOW"
    
    # Responsabilidad Económica
    RESPONSABILIDAD_PROPUESTA = "RESPONSABILIDAD_PROPUESTA"
    RESPONSABILIDAD_APROBADA = "RESPONSABILIDAD_APROBADA"
    RESPONSABILIDAD_EN_DISPUTA = "RESPONSABILIDAD_EN_DISPUTA"


class ChannelType(str, Enum):
    """Canales de notificación soportados."""
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"  # Futuro
    PUSH = "push"  # Futuro


class NotificationStatus(str, Enum):
    """Estados de envío de notificación."""
    PENDIENTE = "pendiente"
    ENVIADO = "enviado"
    ENTREGADO = "entregado"
    FALLIDO = "fallido"
    OMITIDO = "omitido"
    DUPLICADO = "duplicado"
    CANCELADO = "cancelado"


class SendMode(str, Enum):
    """Modos de envío."""
    REAL = "real"
    MOCK = "mock"
    DRY_RUN = "dry_run"


class RecipientType(str, Enum):
    """Tipos de destinatario."""
    RESPONSABLE = "responsable"
    SUPERVISOR = "supervisor"
    GERENTE = "gerente"
    AUDITOR = "auditor"
    CUSTOM = "custom"


# =============================================================================
# MODELOS DE CONFIGURACIÓN
# =============================================================================

class NotificationConfig(BaseModel):
    """
    Configuración de notificaciones por evento/módulo.
    Colección: notification_config
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    canal: ChannelType = ChannelType.WHATSAPP
    modulo: str = "inventarios"  # inventarios, compras, cxp, etc.
    evento: EventType
    activo: bool = True
    provider: str = "twilio"  # twilio, meta, mock
    modo_envio: SendMode = SendMode.MOCK
    template_codigo: str
    
    # Destinatarios
    enviar_a_responsable: bool = True
    enviar_a_supervisor: bool = False
    enviar_a_gerente: bool = False
    
    # Control de envío
    permite_reintentos: bool = True
    max_reintentos: int = 3
    ventana_duplicidad_minutos: int = 60
    
    # Horarios permitidos
    horario_permitido_inicio: Optional[str] = "08:00"  # HH:MM
    horario_permitido_fin: Optional[str] = "20:00"
    timezone: str = "America/Mexico_City"
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    
    class Config:
        use_enum_values = True


class ProviderConfig(BaseModel):
    """
    Configuración de proveedor de mensajería.
    Colección: notification_provider_config
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    canal: ChannelType = ChannelType.WHATSAPP
    provider: str  # twilio, meta, sendgrid, mock
    activo: bool = True
    
    # Conexión (NO guardar secretos aquí - usar env vars)
    base_url: Optional[str] = None
    account_id: Optional[str] = None  # Twilio Account SID, Meta Business ID
    token_ref: str = "WHATSAPP_API_TOKEN"  # Nombre de variable de entorno
    remitente: Optional[str] = None  # Número WhatsApp remitente
    
    # Metadata
    metadata: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
    
    class Config:
        use_enum_values = True


# =============================================================================
# MODELOS DE TEMPLATES
# =============================================================================

class NotificationTemplate(BaseModel):
    """
    Template de mensaje de notificación.
    Colección: notification_templates
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    canal: ChannelType = ChannelType.WHATSAPP
    codigo: str  # inventarios_sla_vencido, inventarios_asignacion_tarea
    nombre: str
    activo: bool = True
    idioma: str = "es"
    
    # Contenido
    template_texto: str  # "EDARSA HUB: El caso {{folio}} en {{sucursal}}..."
    variables: List[str] = []  # ["folio", "sucursal", "fecha_limite"]
    
    # Versionamiento
    version: int = 1
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
    
    class Config:
        use_enum_values = True


# =============================================================================
# MODELOS DE COLA Y LOG
# =============================================================================

class NotificationQueue(BaseModel):
    """
    Cola de notificaciones pendientes.
    Colección: notification_queue
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    canal: ChannelType = ChannelType.WHATSAPP
    modulo: str = "inventarios"
    evento_negocio: EventType
    
    # Referencias
    referencia_id: Optional[str] = None  # ID del objeto que disparó el evento
    workflow_id: Optional[str] = None
    tarea_id: Optional[str] = None
    
    # Prioridad (1=alta, 5=baja)
    prioridad: int = 3
    
    # Destinatarios
    destinatarios: List[Dict[str, Any]] = []  # [{user_id, telefono, tipo}]
    
    # Contenido
    template_codigo: str
    payload: Dict[str, Any] = {}  # Variables para interpolar
    payload_renderizado: Optional[str] = None
    
    # Estado
    estado: NotificationStatus = NotificationStatus.PENDIENTE
    intentos: int = 0
    proximo_intento: Optional[str] = None
    
    # Bloqueo para evitar procesamiento concurrente
    locked_at: Optional[str] = None
    locked_by: Optional[str] = None
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
    
    class Config:
        use_enum_values = True


class NotificationLog(BaseModel):
    """
    Log de auditoría de notificaciones enviadas.
    Colección: notification_log
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    canal: ChannelType = ChannelType.WHATSAPP
    modulo: str = "inventarios"
    evento_negocio: EventType
    
    # Referencias
    referencia_id: Optional[str] = None
    workflow_id: Optional[str] = None
    tarea_id: Optional[str] = None
    queue_id: Optional[str] = None
    
    # Destinatario
    destinatario: str  # Teléfono o email
    usuario_destino_id: Optional[str] = None
    usuario_destino_nombre: Optional[str] = None
    tipo_destinatario: Optional[str] = None  # responsable, supervisor, gerente
    
    # Template
    template_codigo: str
    payload_renderizado: str  # Mensaje final enviado
    
    # Provider
    provider: str  # twilio, meta, mock
    provider_message_id: Optional[str] = None  # ID devuelto por el provider
    
    # Estado
    estado_envio: NotificationStatus
    intentos: int = 1
    
    # Errores
    error_codigo: Optional[str] = None
    error_detalle: Optional[str] = None
    
    # Timestamps
    fecha_intento: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    fecha_envio: Optional[str] = None
    fecha_entrega: Optional[str] = None
    
    # Metadata adicional
    metadata: Dict[str, Any] = {}
    
    class Config:
        use_enum_values = True


# =============================================================================
# MODELOS DE EVENTOS (Input)
# =============================================================================

class NotificationEvent(BaseModel):
    """
    Evento de negocio que solicita notificación.
    Este es el input que recibe el orquestador.
    """
    evento: EventType
    modulo: str = "inventarios"
    canal: ChannelType = ChannelType.WHATSAPP
    
    # Referencias
    referencia_id: Optional[str] = None
    workflow_id: Optional[str] = None
    tarea_id: Optional[str] = None
    
    # Destinatarios
    responsable_id: Optional[str] = None
    supervisor_id: Optional[str] = None
    gerente_id: Optional[str] = None
    destinatarios_adicionales: List[str] = []  # Lista de user_ids
    
    # Datos para template
    payload: Dict[str, Any] = {}
    
    # Prioridad
    prioridad: int = 3
    
    # Metadata
    triggered_by: Optional[str] = None
    triggered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    class Config:
        use_enum_values = True


# =============================================================================
# MODELOS DE RESPUESTA
# =============================================================================

class NotificationResult(BaseModel):
    """Resultado de intento de notificación."""
    success: bool
    event_type: str
    channel: str
    destinatarios_enviados: int = 0
    destinatarios_fallidos: int = 0
    destinatarios_omitidos: int = 0
    log_ids: List[str] = []
    errors: List[str] = []
    duplicados: int = 0


# =============================================================================
# SCHEMAS PARA API
# =============================================================================

class NotificationConfigCreate(BaseModel):
    """Schema para crear configuración."""
    canal: ChannelType = ChannelType.WHATSAPP
    modulo: str = "inventarios"
    evento: EventType
    provider: str = "mock"
    modo_envio: SendMode = SendMode.MOCK
    template_codigo: str
    enviar_a_responsable: bool = True
    enviar_a_supervisor: bool = False
    enviar_a_gerente: bool = False
    ventana_duplicidad_minutos: int = 60
    
    class Config:
        use_enum_values = True


class NotificationConfigUpdate(BaseModel):
    """Schema para actualizar configuración."""
    activo: Optional[bool] = None
    modo_envio: Optional[SendMode] = None
    template_codigo: Optional[str] = None
    enviar_a_responsable: Optional[bool] = None
    enviar_a_supervisor: Optional[bool] = None
    enviar_a_gerente: Optional[bool] = None
    ventana_duplicidad_minutos: Optional[int] = None
    horario_permitido_inicio: Optional[str] = None
    horario_permitido_fin: Optional[str] = None
    
    class Config:
        use_enum_values = True


class NotificationTemplateCreate(BaseModel):
    """Schema para crear template."""
    canal: ChannelType = ChannelType.WHATSAPP
    codigo: str
    nombre: str
    template_texto: str
    variables: List[str] = []
    idioma: str = "es"
    
    class Config:
        use_enum_values = True


class NotificationTemplateUpdate(BaseModel):
    """Schema para actualizar template."""
    nombre: Optional[str] = None
    activo: Optional[bool] = None
    template_texto: Optional[str] = None
    variables: Optional[List[str]] = None
    
    class Config:
        use_enum_values = True


class NotificationTestRequest(BaseModel):
    """Schema para prueba de notificación."""
    template_codigo: str
    destinatario_telefono: str
    payload: Dict[str, Any] = {}
    modo: SendMode = SendMode.MOCK
    
    class Config:
        use_enum_values = True
