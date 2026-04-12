"""
EDARSA HUB - Módulo de Recursos Humanos
=======================================
Gestión de colaboradores, nóminas, incidencias y catálogos RH.

FASE 6B DEL REFACTOR MODULAR (Diciembre 2025):
- Catálogos RH: Puestos, Sucursales, Tipos de Incidencias
- 10 endpoints migrados desde server.py
- Queries parametrizados (seguridad SQL Injection)
- Validación con Pydantic

Componentes:
- routes.py: Endpoints del módulo (prefijo /rrhh/)
- schemas.py: Modelos Pydantic para validación
- service.py: Lógica de negocio
- repository.py: Acceso a datos parametrizado

Tablas reutilizadas (NO duplicadas):
- RH_Cat_Puestos
- RH_Cat_Sucursales
- RH_Cat_SucursalesFiscal
- RH_Cat_Tipos_Incidencias

Inicialización:
    from modules.rh import init_rh_module
    init_rh_module(db)
"""

from modules.rh.routes import router
from modules.rh.repository import init_rh_repository
from modules.rh.schemas import (
    PuestoCreate,
    PuestoUpdate,
    PuestosListResponse,
    SucursalesListResponse,
    TipoIncidenciaCreate,
    TipoIncidenciaUpdate,
    TiposIncidenciasListResponse,
    SuccessResponse,
    ScriptInicializacionResponse,
)
from modules.rh.service import rh_catalogos_service


def init_rh_module(database) -> None:
    """
    Inicializa el módulo de Recursos Humanos.
    
    Args:
        database: Instancia de AsyncIOMotorDatabase
    """
    init_rh_repository(database)


__all__ = [
    'router',
    'init_rh_module',
    # Schemas - Puestos
    'PuestoCreate',
    'PuestoUpdate',
    'PuestosListResponse',
    # Schemas - Sucursales
    'SucursalesListResponse',
    # Schemas - Tipos Incidencias
    'TipoIncidenciaCreate',
    'TipoIncidenciaUpdate',
    'TiposIncidenciasListResponse',
    # Schemas - Genéricos
    'SuccessResponse',
    'ScriptInicializacionResponse',
    # Service
    'rh_catalogos_service',
]
