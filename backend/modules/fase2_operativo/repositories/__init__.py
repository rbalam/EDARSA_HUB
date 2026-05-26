"""
Repositories para Fase 2A - Módulo Operativo
CAB-003 | EDARSA HUB

FASE B-P0-C: Migrado a EDARSAHUB SQL Server
- BaseRepository ahora usa SQLBaseRepository internamente
- CERO MongoDB productivo
- CERO conexiones LIVE

Exporta todos los repositories del módulo para facilitar imports.
"""

from .base_repository import (
    BaseRepository,
    SQLBaseRepository,
    SQLRepositoryNotImplementedError,
    COLLECTION_TO_TABLE_MAP,
    get_sql_repository,
)
from .workflow_repository import WorkflowRepository
from .detalle_diferencias_repository import DetalleDiferenciasRepository
from .tarea_repository import TareaRepository
from .historial_repository import HistorialAsignacionRepository
from .justificacion_repository import JustificacionRepository
from .auditoria_repository import AuditoriaRepository
from .configuracion_repository import ConfiguracionRepository
from .responsabilidad_repository import ResponsabilidadRepository
from .historial_responsabilidad_repository import HistorialResponsabilidadRepository
from .cargos_repository import CargosEconomicosRepository, CargosLogRepository


__all__ = [
    # SQL Base (FASE B-P0-C)
    "BaseRepository",
    "SQLBaseRepository",
    "SQLRepositoryNotImplementedError",
    "COLLECTION_TO_TABLE_MAP",
    "get_sql_repository",
    # Repositories específicos
    "WorkflowRepository",
    "DetalleDiferenciasRepository",
    "TareaRepository",
    "HistorialAsignacionRepository",
    "JustificacionRepository",
    "AuditoriaRepository",
    "ConfiguracionRepository",
    "ResponsabilidadRepository",
    "HistorialResponsabilidadRepository",
    # Cargos Económicos (Fase 2C.3)
    "CargosEconomicosRepository",
    "CargosLogRepository",
]
