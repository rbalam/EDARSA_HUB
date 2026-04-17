"""
Schemas Pydantic para Fase 2A - Módulo Operativo
CAB-003 | EDARSA HUB

Exporta todos los schemas del módulo para facilitar imports.
"""

# Enumeraciones
from .enums import (
    EstadoWorkflow,
    TipoTarea,
    EstadoTarea,
    TipoJustificacion,
    DecisionAuditoria,
)

# Schemas de Workflow
from .workflow_schemas import (
    WorkflowBase,
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowInDB,
    WorkflowResponse,
    WorkflowListResponse,
)

# Schemas de Tareas
from .tarea_schemas import (
    TareaBase,
    TareaCreate,
    TareaAsignar,
    TareaReasignar,
    TareaInDB,
    TareaResponse,
    TareaListResponse,
    HistorialAsignacionBase,
    HistorialAsignacionCreate,
    HistorialAsignacionInDB,
    HistorialAsignacionResponse,
)

# Schemas de Justificaciones
from .justificacion_schemas import (
    JustificacionBase,
    JustificacionCreate,
    JustificacionInDB,
    JustificacionResponse,
    JustificacionListResponse,
    DetalleDiferenciaBase,
    DetalleDiferenciaCreate,
    DetalleDiferenciaInDB,
    DetalleDiferenciaResponse,
)

# Schemas de Auditoría
from .auditoria_schemas import (
    DecisionAuditoriaBase,
    DecisionAuditoriaCreate,
    DecisionAuditoriaInDB,
    DecisionAuditoriaResponse,
    DecisionAuditoriaListResponse,
)

# Schemas de Configuración
from .configuracion_schemas import (
    ConfiguracionBase,
    ConfiguracionCreate,
    ConfiguracionUpdate,
    ConfiguracionInDB,
    ConfiguracionResponse,
    ConfiguracionListResponse,
)


__all__ = [
    # Enums
    "EstadoWorkflow",
    "TipoTarea",
    "EstadoTarea",
    "TipoJustificacion",
    "DecisionAuditoria",
    # Workflow
    "WorkflowBase",
    "WorkflowCreate",
    "WorkflowUpdate",
    "WorkflowInDB",
    "WorkflowResponse",
    "WorkflowListResponse",
    # Tareas
    "TareaBase",
    "TareaCreate",
    "TareaAsignar",
    "TareaReasignar",
    "TareaInDB",
    "TareaResponse",
    "TareaListResponse",
    "HistorialAsignacionBase",
    "HistorialAsignacionCreate",
    "HistorialAsignacionInDB",
    "HistorialAsignacionResponse",
    # Justificaciones
    "JustificacionBase",
    "JustificacionCreate",
    "JustificacionInDB",
    "JustificacionResponse",
    "JustificacionListResponse",
    "DetalleDiferenciaBase",
    "DetalleDiferenciaCreate",
    "DetalleDiferenciaInDB",
    "DetalleDiferenciaResponse",
    # Auditoría
    "DecisionAuditoriaBase",
    "DecisionAuditoriaCreate",
    "DecisionAuditoriaInDB",
    "DecisionAuditoriaResponse",
    "DecisionAuditoriaListResponse",
    # Configuración
    "ConfiguracionBase",
    "ConfiguracionCreate",
    "ConfiguracionUpdate",
    "ConfiguracionInDB",
    "ConfiguracionResponse",
    "ConfiguracionListResponse",
]
