"""
Repositories para Fase 2A - Módulo Operativo
CAB-003 | EDARSA HUB

Exporta todos los repositories del módulo para facilitar imports.
"""

from .base_repository import BaseRepository
from .workflow_repository import WorkflowRepository
from .detalle_diferencias_repository import DetalleDiferenciasRepository
from .tarea_repository import TareaRepository
from .historial_repository import HistorialAsignacionRepository
from .justificacion_repository import JustificacionRepository
from .auditoria_repository import AuditoriaRepository
from .configuracion_repository import ConfiguracionRepository
from .responsabilidad_repository import ResponsabilidadRepository
from .historial_responsabilidad_repository import HistorialResponsabilidadRepository


__all__ = [
    "BaseRepository",
    "WorkflowRepository",
    "DetalleDiferenciasRepository",
    "TareaRepository",
    "HistorialAsignacionRepository",
    "JustificacionRepository",
    "AuditoriaRepository",
    "ConfiguracionRepository",
    "ResponsabilidadRepository",
    "HistorialResponsabilidadRepository",
]
