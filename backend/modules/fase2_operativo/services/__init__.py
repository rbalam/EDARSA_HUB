"""
Services para Fase 2A - Módulo Operativo
CAB-003 | EDARSA HUB

Exporta todos los services del módulo para facilitar imports.
"""

from .workflow_service import (
    WorkflowService,
    WorkflowServiceError,
    WorkflowNoEncontradoError,
    TransicionInvalidaError,
    WorkflowYaExisteError,
)

from .tarea_service import (
    TareaService,
    TareaServiceError,
    TareaNoEncontradaError,
    TareaYaCompletadaError,
)

from .justificacion_service import (
    JustificacionService,
    JustificacionServiceError,
    JustificacionInvalidaError,
    EvidenciaRequeridaError,
    JustificacionYaExisteError,
)

from .auditoria_service import (
    AuditoriaService,
    AuditoriaServiceError,
    WorkflowNoEnAuditoriaError,
    DecisionInvalidaError,
)

from .configuracion_service import (
    ConfiguracionService,
    ConfiguracionServiceError,
    ConfiguracionNoEncontradaError,
    ValorInvalidoError,
)

from .operativo_service import (
    OperativoService,
    OperativoServiceError,
    FlujoInvalidoError,
)

from .orquestador_service import (
    OrquestadorService,
    get_orquestador_service,
)

from .email_service import (
    EmailService,
    EmailServiceError,
    get_email_service,
)

from .notification_service import (
    NotificationService,
    get_notification_service,
    EVENTO_WORKFLOW_CREADO,
    EVENTO_TAREA_ASIGNADA,
    EVENTO_TAREA_VENCIDA,
)


__all__ = [
    # Workflow Service
    "WorkflowService",
    "WorkflowServiceError",
    "WorkflowNoEncontradoError",
    "TransicionInvalidaError",
    "WorkflowYaExisteError",
    # Tarea Service
    "TareaService",
    "TareaServiceError",
    "TareaNoEncontradaError",
    "TareaYaCompletadaError",
    # Justificacion Service
    "JustificacionService",
    "JustificacionServiceError",
    "JustificacionInvalidaError",
    "EvidenciaRequeridaError",
    "JustificacionYaExisteError",
    # Auditoria Service
    "AuditoriaService",
    "AuditoriaServiceError",
    "WorkflowNoEnAuditoriaError",
    "DecisionInvalidaError",
    # Configuracion Service
    "ConfiguracionService",
    "ConfiguracionServiceError",
    "ConfiguracionNoEncontradaError",
    "ValorInvalidoError",
    # Operativo Service
    "OperativoService",
    "OperativoServiceError",
    "FlujoInvalidoError",
    # Orquestador Service
    "OrquestadorService",
    "get_orquestador_service",
    # Email Service
    "EmailService",
    "EmailServiceError",
    "get_email_service",
    # Notification Service
    "NotificationService",
    "get_notification_service",
    "EVENTO_WORKFLOW_CREADO",
    "EVENTO_TAREA_ASIGNADA",
    "EVENTO_TAREA_VENCIDA",
]
