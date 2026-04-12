"""
EDARSA HUB - Módulo de Recursos Humanos
=======================================
Gestión de colaboradores, nóminas, incidencias y catálogos RH.

FASE 6B DEL REFACTOR MODULAR (Diciembre 2025):
- Catálogos RH: Puestos, Sucursales, Tipos de Incidencias
- 10 endpoints migrados desde server.py

FASE 6C-B DEL REFACTOR MODULAR (Diciembre 2025):
- Colaboradores RH: CRUD completo
- 5 endpoints migrados desde server.py
- Queries parametrizados nativos (prevención SQL Injection)
- Validación Pydantic para CURP, RFC, CLABE

FASE 6D-B DEL REFACTOR MODULAR (Diciembre 2025):
- Incidencias RH: Listado, creación, importación Excel
- 4 endpoints migrados desde server.py
- Validación de tipos contra catálogo RH_Cat_Tipos_Incidencias
- Importación PARCIAL (no transaccional) documentada

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
- RH_Colaboradores_Expediente
- RH_Incidencias_Nomina
- RH_Reloj_Checador (solo lectura)
- RH_Auditoria_Fiscal (solo lectura)

Inicialización:
    from modules.rh import init_rh_module
    init_rh_module(db)
"""

from modules.rh.routes import router
from modules.rh.repository import init_rh_repository
from modules.rh.schemas import (
    # Catálogos - Puestos
    PuestoCreate,
    PuestoUpdate,
    PuestosListResponse,
    # Catálogos - Sucursales
    SucursalesListResponse,
    # Catálogos - Tipos Incidencias
    TipoIncidenciaCreate,
    TipoIncidenciaUpdate,
    TiposIncidenciasListResponse,
    # Colaboradores
    ColaboradorCreate,
    ColaboradorUpdate,
    ColaboradorResponse,
    ColaboradorDetalleResponse,
    ColaboradoresListResponse,
    # Incidencias
    IncidenciaCreate,
    IncidenciaResponse,
    IncidenciasListResponse,
    ImportacionExcelResponse,
    # Genéricos
    SuccessResponse,
    SuccessWithIdResponse,
    ScriptInicializacionResponse,
)
from modules.rh.service import rh_catalogos_service, rh_colaboradores_service, rh_incidencias_service


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
    # Schemas - Colaboradores
    'ColaboradorCreate',
    'ColaboradorUpdate',
    'ColaboradorResponse',
    'ColaboradorDetalleResponse',
    'ColaboradoresListResponse',
    # Schemas - Incidencias
    'IncidenciaCreate',
    'IncidenciaResponse',
    'IncidenciasListResponse',
    'ImportacionExcelResponse',
    # Schemas - Genéricos
    'SuccessResponse',
    'SuccessWithIdResponse',
    'ScriptInicializacionResponse',
    # Services
    'rh_catalogos_service',
    'rh_colaboradores_service',
    'rh_incidencias_service',
]
