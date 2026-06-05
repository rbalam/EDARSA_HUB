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

FASE IMPORTACIÓN (Diciembre 2025):
- Importador controlado de empleados desde Excel Cienfuegos
- Flujo: staging → validación → clasificación → aprobación → carga
- Tablas de apoyo: RH_Importacion_Staging, RH_Importacion_Bitacora
- Deduplicación por CURP/RFC con niveles de confianza

Componentes:
- routes.py: Endpoints del módulo (prefijo /rrhh/)
- schemas.py: Modelos Pydantic para validación
- service.py: Lógica de negocio
- repository.py: Acceso a datos parametrizado
- importador/: Submódulo de importación controlada

Tablas reutilizadas (NO duplicadas):
- RH_Cat_Puestos
- RH_Cat_Sucursales
- RH_Cat_SucursalesFiscal
- RH_Cat_Tipos_Incidencias
- RH_Colaboradores_Expediente
- RH_Incidencias_Nomina
- RH_Reloj_Checador (solo lectura)
- RH_Auditoria_Fiscal (solo lectura)

Tablas de apoyo (NUEVAS):
- RH_Importacion_Staging (registros pendientes)
- RH_Importacion_Bitacora (historial de importaciones)

Inicialización:
    from modules.rh import init_rh_module
    init_rh_module(db)
"""

from modules.rh.repository import init_rh_repository
from modules.rh.importador.repository import init_importador_repository
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


def get_router():
    """Lazy import del router para evitar circular imports."""
    from modules.rh.routes import router
    return router


def get_importador_router():
    """Lazy import del router de importación."""
    from modules.rh.importador.routes import router
    return router


def init_rh_module(database) -> None:
    """
    Inicializa el módulo de Recursos Humanos.
    
    Args:
        database: Instancia de Any
    """
    init_rh_repository(database)
    init_importador_repository(database)


__all__ = [
    'get_router',
    'get_importador_router',
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
