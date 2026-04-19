"""
Módulo de Manuales Operativos - EDARSA HUB

Generación automática de documentación operativa en formato Cienfuegos
cuando los procesos llegan a estado COMPLETADA o CERRADO.
"""

from .schemas import (
    ModuloOrigen,
    FormatoManual,
    ResponsableManual,
    PasoOperativo,
    EvidenciaGenerada,
    ContenidoManualCienfuegos,
    ManualOperativoBase,
    ManualOperativoCreate,
    ManualOperativoDB,
    ManualOperativoResponse,
    ManualOperativoListResponse,
    EVENTO_A_PASO_OPERATIVO,
)

from .service import ManualOperativoService
from .routes import router, init_manuales_module

__all__ = [
    'ModuloOrigen',
    'FormatoManual',
    'ResponsableManual',
    'PasoOperativo',
    'EvidenciaGenerada',
    'ContenidoManualCienfuegos',
    'ManualOperativoBase',
    'ManualOperativoCreate',
    'ManualOperativoDB',
    'ManualOperativoResponse',
    'ManualOperativoListResponse',
    'EVENTO_A_PASO_OPERATIVO',
    'ManualOperativoService',
    'router',
    'init_manuales_module',
]
