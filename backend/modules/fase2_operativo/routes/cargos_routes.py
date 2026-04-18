"""
Rutas API para Cargos Económicos
CAB-003 | EDARSA HUB - Fase 2C.3

Endpoints REST para gestión del ciclo de vida de cargos económicos.
PROTEGIDOS CON RBAC (Fase 2D)

Endpoints:
- POST /api/v2/cargos                     - Crear propuesta (CARGOS_CREAR)
- GET /api/v2/cargos                      - Listar con filtros (CARGOS_VER)
- GET /api/v2/cargos/pendientes           - Pendientes de autorización (CARGOS_VER)
- GET /api/v2/cargos/aplicados            - Cargos aplicados (CARGOS_VER)
- GET /api/v2/cargos/metricas             - Métricas agregadas (CARGOS_VER)
- GET /api/v2/cargos/elegibilidad/{id}    - Evaluar elegibilidad (CARGOS_VER)
- GET /api/v2/cargos/{id}                 - Obtener cargo (CARGOS_VER)
- GET /api/v2/cargos/{id}/log             - Historial de log (CARGOS_VER)
- POST /api/v2/cargos/{id}/autorizar      - Autorizar cargo (CARGOS_AUTORIZAR)
- POST /api/v2/cargos/{id}/aplicar        - Aplicar cargo (CARGOS_APLICAR)
- POST /api/v2/cargos/{id}/rechazar       - Rechazar cargo (CARGOS_RECHAZAR)
- POST /api/v2/cargos/{id}/revertir       - Revertir cargo (CARGOS_REVERTIR)
- POST /api/v2/cargos/{id}/cancelar       - Cancelar cargo (CARGOS_CANCELAR)
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import logging

from ..services.cargos_service import (
    CargosService,
    CargosServiceError,
    ResponsabilidadNoEncontradaError,
    CargoNoEncontradoError,
    CargoYaExisteError,
    NoElegibleParaCargoError,
    TransicionInvalidaError,
    PermisoInsuficienteError,
)
from ..schemas.cargos_schemas import (
    CargoEconomicoCreate,
    CargoAccionRequest,
    CargoReversaRequest,
    CargoEconomicoResponse,
    CargoEconomicoListResponse,
    CargoAccionResponse,
    CargoLogListResponse,
    CargosPendientesResponse,
    CargosAplicadosResponse,
    CargosMetricasResponse,
    ElegibilidadCargoResponse,
)
from ..db_utils import get_database

# RBAC - Fase 2D
from core.rbac.middleware import require_permission

router = APIRouter(prefix="/cargos", tags=["Cargos Económicos"])
logger = logging.getLogger(__name__)


def get_cargos_service():
    """Dependency injection para CargosService."""
    db = get_database()
    return CargosService(db)


# ==================== CREACIÓN ====================

@router.post(
    "",
    response_model=CargoAccionResponse,
    summary="Crear propuesta de cargo",
    description="Crea una propuesta de cargo económico desde una responsabilidad aprobada. Requiere permiso CARGOS_CREAR."
)
async def crear_propuesta_cargo(
    request: CargoEconomicoCreate,
    current_user: dict = Depends(require_permission("CARGOS_CREAR")),
    service: CargosService = Depends(get_cargos_service)
):
    """
    Crea una propuesta de cargo económico.
    
    Requiere que la responsabilidad esté en estado APROBADO
    y no tenga controversia activa, exoneración, ni cargo previo.
    """
    try:
        resultado = await service.crear_propuesta_cargo(
            responsabilidad_id=request.responsabilidad_id,
            usuario_id=request.usuario_id,
            usuario_rol=request.usuario_rol,
            comentario=request.comentario
        )
        return resultado
    except NoElegibleParaCargoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResponsabilidadNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CargosServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== CONSULTAS ====================

@router.get(
    "",
    response_model=CargoEconomicoListResponse,
    summary="Listar cargos",
    description="Lista cargos económicos con filtros opcionales. Requiere permiso CARGOS_VER."
)
async def listar_cargos(
    estatus: Optional[str] = Query(None, description="Filtrar por estatus"),
    sucursal_id: Optional[str] = Query(None, description="Filtrar por sucursal"),
    responsable_id: Optional[str] = Query(None, description="Filtrar por responsable"),
    workflow_id: Optional[str] = Query(None, description="Filtrar por workflow"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_permission("CARGOS_VER")),
    service: CargosService = Depends(get_cargos_service)
):
    """Lista cargos económicos con filtros opcionales."""
    resultado = await service.listar_cargos(
        estatus=estatus,
        sucursal_id=sucursal_id,
        responsable_id=responsable_id,
        workflow_id=workflow_id,
        skip=skip,
        limit=limit
    )
    return CargoEconomicoListResponse(
        total=resultado["total"],
        items=resultado["items"]
    )


@router.get(
    "/pendientes",
    response_model=CargosPendientesResponse,
    summary="Cargos pendientes",
    description="Lista cargos pendientes de autorización"
)
async def obtener_pendientes(
    service: CargosService = Depends(get_cargos_service)
):
    """Obtiene cargos pendientes de autorización."""
    return await service.obtener_pendientes_autorizacion()


@router.get(
    "/aplicados",
    response_model=CargosAplicadosResponse,
    summary="Cargos aplicados",
    description="Lista cargos que han sido aplicados"
)
async def obtener_aplicados(
    service: CargosService = Depends(get_cargos_service)
):
    """Obtiene cargos aplicados."""
    return await service.obtener_aplicados()


@router.get(
    "/metricas",
    response_model=CargosMetricasResponse,
    summary="Métricas de cargos",
    description="Obtiene métricas agregadas de cargos económicos"
)
async def obtener_metricas(
    service: CargosService = Depends(get_cargos_service)
):
    """Obtiene métricas agregadas de cargos."""
    return await service.obtener_metricas()


@router.get(
    "/elegibilidad/{responsabilidad_id}",
    response_model=ElegibilidadCargoResponse,
    summary="Evaluar elegibilidad",
    description="Evalúa si una responsabilidad es elegible para generar cargo"
)
async def evaluar_elegibilidad(
    responsabilidad_id: str,
    service: CargosService = Depends(get_cargos_service)
):
    """
    Evalúa si una responsabilidad es elegible para generar cargo.
    
    Criterios:
    - Estado APROBADO
    - Sin controversia activa
    - Sin exoneración
    - Sin cargo previo activo
    """
    return await service.evaluar_elegibilidad(responsabilidad_id)


@router.get(
    "/{cargo_id}",
    response_model=CargoEconomicoResponse,
    summary="Obtener cargo",
    description="Obtiene un cargo económico por su ID"
)
async def obtener_cargo(
    cargo_id: str,
    service: CargosService = Depends(get_cargos_service)
):
    """Obtiene un cargo por su ID."""
    try:
        return await service.obtener_cargo(cargo_id)
    except CargoNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{cargo_id}/log",
    response_model=CargoLogListResponse,
    summary="Historial de cargo",
    description="Obtiene el historial completo de un cargo"
)
async def obtener_log_cargo(
    cargo_id: str,
    service: CargosService = Depends(get_cargos_service)
):
    """Obtiene el historial de log de un cargo."""
    try:
        return await service.obtener_log_cargo(cargo_id)
    except CargoNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== ACCIONES ====================

@router.post(
    "/{cargo_id}/autorizar",
    response_model=CargoAccionResponse,
    summary="Autorizar cargo",
    description="Autoriza un cargo pendiente (PENDIENTE → AUTORIZADO). Requiere permiso CARGOS_AUTORIZAR."
)
async def autorizar_cargo(
    cargo_id: str,
    request: CargoAccionRequest,
    current_user: dict = Depends(require_permission("CARGOS_AUTORIZAR")),
    service: CargosService = Depends(get_cargos_service)
):
    """
    Autoriza un cargo pendiente.
    
    Validaciones:
    - Cargo debe estar en estado PENDIENTE
    - Usuario debe tener rol suficiente según monto
    - Requiere permiso CARGOS_AUTORIZAR
    """
    try:
        return await service.autorizar_cargo(
            cargo_id=cargo_id,
            usuario_id=request.usuario_id,
            usuario_rol=request.usuario_rol,
            comentario=request.comentario,
            motivo_codigo=request.motivo_codigo
        )
    except CargoNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TransicionInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermisoInsuficienteError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/{cargo_id}/aplicar",
    response_model=CargoAccionResponse,
    summary="Aplicar cargo",
    description="Aplica formalmente un cargo autorizado (AUTORIZADO → APLICADO). Requiere permiso CARGOS_APLICAR."
)
async def aplicar_cargo(
    cargo_id: str,
    request: CargoAccionRequest,
    current_user: dict = Depends(require_permission("CARGOS_APLICAR")),
    service: CargosService = Depends(get_cargos_service)
):
    """
    Aplica formalmente un cargo autorizado.
    
    Este es el punto de no retorno. El cargo queda registrado
    para integración con nómina/ERP.
    Requiere permiso CARGOS_APLICAR.
    """
    try:
        return await service.aplicar_cargo(
            cargo_id=cargo_id,
            usuario_id=request.usuario_id,
            usuario_rol=request.usuario_rol,
            comentario=request.comentario,
            motivo_codigo=request.motivo_codigo
        )
    except CargoNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TransicionInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermisoInsuficienteError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/{cargo_id}/rechazar",
    response_model=CargoAccionResponse,
    summary="Rechazar cargo",
    description="Rechaza un cargo pendiente (PENDIENTE → RECHAZADO). Requiere permiso CARGOS_RECHAZAR."
)
async def rechazar_cargo(
    cargo_id: str,
    request: CargoAccionRequest,
    current_user: dict = Depends(require_permission("CARGOS_RECHAZAR")),
    service: CargosService = Depends(get_cargos_service)
):
    """
    Rechaza un cargo pendiente.
    
    El cargo no procedía según la evaluación.
    Requiere permiso CARGOS_RECHAZAR.
    """
    try:
        return await service.rechazar_cargo(
            cargo_id=cargo_id,
            usuario_id=request.usuario_id,
            usuario_rol=request.usuario_rol,
            comentario=request.comentario,
            motivo_codigo=request.motivo_codigo
        )
    except CargoNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TransicionInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermisoInsuficienteError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/{cargo_id}/revertir",
    response_model=CargoAccionResponse,
    summary="Revertir cargo",
    description="Revierte un cargo ya aplicado (APLICADO → REVERTIDO). Requiere permiso CARGOS_REVERTIR."
)
async def revertir_cargo(
    cargo_id: str,
    request: CargoReversaRequest,
    current_user: dict = Depends(require_permission("CARGOS_REVERTIR")),
    service: CargosService = Depends(get_cargos_service)
):
    """
    Revierte un cargo ya aplicado.
    
    Operación crítica que requiere:
    - Motivo detallado (mínimo 20 caracteres)
    - Rol GERENTE_OPS o superior
    - Permiso CARGOS_REVERTIR
    """
    try:
        return await service.revertir_cargo(
            cargo_id=cargo_id,
            usuario_id=request.usuario_id,
            usuario_rol=request.usuario_rol,
            motivo_reversa=request.motivo_reversa,
            motivo_codigo=request.motivo_codigo
        )
    except CargoNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TransicionInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermisoInsuficienteError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/{cargo_id}/cancelar",
    response_model=CargoAccionResponse,
    summary="Cancelar cargo",
    description="Cancela un cargo antes de ser aplicado (PENDIENTE/AUTORIZADO → CANCELADO). Requiere permiso CARGOS_CANCELAR."
)
async def cancelar_cargo(
    cargo_id: str,
    request: CargoAccionRequest,
    current_user: dict = Depends(require_permission("CARGOS_CANCELAR")),
    service: CargosService = Depends(get_cargos_service)
):
    """
    Cancela un cargo antes de ser aplicado.
    
    Solo válido para cargos en estado PENDIENTE o AUTORIZADO.
    Requiere permiso CARGOS_CANCELAR.
    """
    try:
        return await service.cancelar_cargo(
            cargo_id=cargo_id,
            usuario_id=request.usuario_id,
            usuario_rol=request.usuario_rol,
            comentario=request.comentario,
            motivo_codigo=request.motivo_codigo
        )
    except CargoNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TransicionInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermisoInsuficienteError as e:
        raise HTTPException(status_code=403, detail=str(e))
