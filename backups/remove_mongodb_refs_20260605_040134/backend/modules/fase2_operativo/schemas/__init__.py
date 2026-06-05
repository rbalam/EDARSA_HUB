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

# Schemas de Responsabilidad Económica (Fase 2C.1)
from .responsabilidad_schemas import (
    EstadoResponsabilidad,
    AccionResponsabilidad,
    RolAutorizacion,
    ToleranciaAplicada,
    ResumenFaltantes,
    ResumenSobrantes,
    ResponsabilidadBase,
    ResponsabilidadCreate,
    ResponsabilidadInDB,
    ResponsabilidadResponse,
    ResponsabilidadListResponse,
    ResponsabilidadResumenCalculo,
    ConfiguracionResponsabilidadResponse,
    ConfiguracionResponsabilidadUpdate,
    # Fase 2C.2
    AccionResponsabilidadRequest,
    AccionResponsabilidadResponse,
    HistorialTransicionResponse,
    HistorialListResponse,
    ResponsabilidadPendienteResponse,
    PendientesAprobacionResponse,
    EnDisputaResponse,
    TRANSICIONES_VALIDAS,
)

# Schemas de Cargos Económicos (Fase 2C.3)
from .cargos_schemas import (
    EstatusCargo,
    AccionCargo,
    OrigenCargo,
    TRANSICIONES_CARGO_VALIDAS,
    CargoEconomicoCreate,
    CargoAccionRequest,
    CargoReversaRequest,
    CargoEconomicoResponse,
    CargoEconomicoListResponse,
    CargoAccionResponse,
    CargoLogResponse,
    CargoLogListResponse,
    CargosPendientesResponse,
    CargosAplicadosResponse,
    CargosMetricasResponse,
    ElegibilidadCargoResponse,
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
    # Responsabilidad Económica (Fase 2C.1 y 2C.2)
    "EstadoResponsabilidad",
    "AccionResponsabilidad",
    "RolAutorizacion",
    "ToleranciaAplicada",
    "ResumenFaltantes",
    "ResumenSobrantes",
    "ResponsabilidadBase",
    "ResponsabilidadCreate",
    "ResponsabilidadInDB",
    "ResponsabilidadResponse",
    "ResponsabilidadListResponse",
    "ResponsabilidadResumenCalculo",
    "ConfiguracionResponsabilidadResponse",
    "ConfiguracionResponsabilidadUpdate",
    # Fase 2C.2
    "AccionResponsabilidadRequest",
    "AccionResponsabilidadResponse",
    "HistorialTransicionResponse",
    "HistorialListResponse",
    "ResponsabilidadPendienteResponse",
    "PendientesAprobacionResponse",
    "EnDisputaResponse",
    "TRANSICIONES_VALIDAS",
    # Cargos Económicos (Fase 2C.3)
    "EstatusCargo",
    "AccionCargo",
    "OrigenCargo",
    "TRANSICIONES_CARGO_VALIDAS",
    "CargoEconomicoCreate",
    "CargoAccionRequest",
    "CargoReversaRequest",
    "CargoEconomicoResponse",
    "CargoEconomicoListResponse",
    "CargoAccionResponse",
    "CargoLogResponse",
    "CargoLogListResponse",
    "CargosPendientesResponse",
    "CargosAplicadosResponse",
    "CargosMetricasResponse",
    "ElegibilidadCargoResponse",
]
