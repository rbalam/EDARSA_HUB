"""
EDARSA HUB - RH Routes (Catálogos)
==================================
Endpoints del módulo de Recursos Humanos.

FASE 6B DEL REFACTOR MODULAR (Diciembre 2025):
Catálogos migrados desde server.py:
- GET    /rrhh/catalogos/puestos
- POST   /rrhh/catalogos/puestos
- PUT    /rrhh/catalogos/puestos/{puesto_id}
- DELETE /rrhh/catalogos/puestos/{puesto_id}
- GET    /rrhh/catalogos/sucursales
- GET    /rrhh/catalogos/tipos-incidencias
- POST   /rrhh/catalogos/tipos-incidencias
- PUT    /rrhh/catalogos/tipos-incidencias/{tipo_id}
- DELETE /rrhh/catalogos/tipos-incidencias/{tipo_id}
- GET    /rrhh/catalogos/script-inicializacion

CONTRATOS MANTENIDOS:
- Prefijo: /rrhh/ (NO /rh/)
- Formatos de respuesta idénticos a los originales
- Compatibilidad total con frontend existente

SEGURIDAD:
- Operaciones de escritura requieren rol Administrador
- Validación de datos con Pydantic
- Queries parametrizados en repository
"""

from fastapi import APIRouter, Depends
from typing import Dict

from core.security import get_current_user
from modules.rh.service import rh_catalogos_service
from modules.rh.schemas import (
    PuestoCreate,
    PuestoUpdate,
    TipoIncidenciaCreate,
    TipoIncidenciaUpdate,
    PuestosListResponse,
    SucursalesListResponse,
    TiposIncidenciasListResponse,
    SuccessResponse,
    ScriptInicializacionResponse,
)


# Router con prefijo /rrhh para mantener compatibilidad
router = APIRouter(prefix="/rrhh", tags=["Recursos Humanos - Catálogos"])


# ============================================================================
# ENDPOINTS DE PUESTOS
# ============================================================================

@router.get("/catalogos/puestos")
async def rrhh_listar_puestos(
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista catálogo de puestos desde RH_Cat_Puestos.
    
    Requiere autenticación.
    """
    return await rh_catalogos_service.listar_puestos()


@router.post("/catalogos/puestos", response_model=SuccessResponse)
async def rrhh_crear_puesto(
    body: PuestoCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo puesto en el catálogo.
    
    Requiere rol: Administrador
    """
    return await rh_catalogos_service.crear_puesto(body, current_user)


@router.put("/catalogos/puestos/{puesto_id}", response_model=SuccessResponse)
async def rrhh_actualizar_puesto(
    puesto_id: int,
    body: PuestoUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualiza un puesto existente.
    
    Requiere rol: Administrador
    """
    return await rh_catalogos_service.actualizar_puesto(puesto_id, body, current_user)


@router.delete("/catalogos/puestos/{puesto_id}", response_model=SuccessResponse)
async def rrhh_eliminar_puesto(
    puesto_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Elimina un puesto del catálogo.
    
    Requiere rol: Administrador.
    Falla si hay colaboradores asignados al puesto.
    """
    return await rh_catalogos_service.eliminar_puesto(puesto_id, current_user)


# ============================================================================
# ENDPOINTS DE SUCURSALES
# ============================================================================

@router.get("/catalogos/sucursales")
async def rrhh_listar_sucursales(
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista catálogo de sucursales desde RH_Cat_Sucursales.
    
    Incluye datos fiscales de RH_Cat_SucursalesFiscal.
    Requiere autenticación.
    """
    return await rh_catalogos_service.listar_sucursales()


# ============================================================================
# ENDPOINTS DE TIPOS DE INCIDENCIAS
# ============================================================================

@router.get("/catalogos/tipos-incidencias")
async def rrhh_listar_tipos_incidencias(
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista catálogo de tipos de incidencias activos.
    
    Si la tabla no existe, retorna tipos por defecto con nota explicativa.
    Requiere autenticación.
    """
    return await rh_catalogos_service.listar_tipos_incidencias()


@router.post("/catalogos/tipos-incidencias", response_model=SuccessResponse)
async def rrhh_crear_tipo_incidencia(
    body: TipoIncidenciaCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo tipo de incidencia.
    
    Requiere rol: Administrador
    """
    return await rh_catalogos_service.crear_tipo_incidencia(body, current_user)


@router.put("/catalogos/tipos-incidencias/{tipo_id}", response_model=SuccessResponse)
async def rrhh_actualizar_tipo_incidencia(
    tipo_id: int,
    body: TipoIncidenciaUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualiza un tipo de incidencia existente.
    
    Requiere rol: Administrador
    """
    return await rh_catalogos_service.actualizar_tipo_incidencia(tipo_id, body, current_user)


@router.delete("/catalogos/tipos-incidencias/{tipo_id}", response_model=SuccessResponse)
async def rrhh_eliminar_tipo_incidencia(
    tipo_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Desactiva un tipo de incidencia (soft delete para mantener histórico).
    
    Requiere rol: Administrador
    """
    return await rh_catalogos_service.eliminar_tipo_incidencia(tipo_id, current_user)


# ============================================================================
# ENDPOINT DE UTILIDAD - SCRIPT INICIALIZACIÓN
# ============================================================================

@router.get("/catalogos/script-inicializacion")
async def rrhh_catalogos_script(
    current_user: Dict = Depends(get_current_user)
):
    """
    Retorna el script SQL para crear/actualizar las tablas de catálogos RRHH.
    
    Incluye instrucciones de uso y compatibilidad con NomiPAQ, MPRO y Excel.
    Requiere autenticación.
    """
    return rh_catalogos_service.obtener_script_inicializacion()
