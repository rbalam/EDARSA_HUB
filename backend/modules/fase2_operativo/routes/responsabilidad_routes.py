from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Endpoints de Responsabilidad Económica
CAB-003 | EDARSA HUB - Fase 2C.1 y 2C.2
PROTEGIDOS CON RBAC (Fase 2D)

Expone la funcionalidad de cálculo de impacto económico y aprobaciones vía HTTP.

Permisos requeridos por endpoint:
- POST /calcular - RESPONSABILIDAD_CALCULAR
- GET / - RESPONSABILIDAD_VER
- GET /workflow/{id} - RESPONSABILIDAD_VER
- GET /configuracion - RESPONSABILIDAD_VER
- PUT /configuracion - RESPONSABILIDAD_GESTIONAR
- POST /{id}/proponer - RESPONSABILIDAD_PROPONER
- POST /{id}/aprobar - RESPONSABILIDAD_APROBAR
- POST /{id}/rechazar - RESPONSABILIDAD_RECHAZAR
- POST /{id}/exonerar - RESPONSABILIDAD_EXONERAR
- POST /{id}/disputar - RESPONSABILIDAD_DISPUTAR
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from ..services.responsabilidad_service import (
    ResponsabilidadService,
    WorkflowNoEncontradoError,
    CalculoYaExisteError,
    ModuloDesactivadoError,
    SinDiferenciasError,
    AprobacionesDesactivadasError,
    ResponsabilidadNoEncontradaError,
    TransicionInvalidaError,
    PermisoInsuficienteError,
)
from ..schemas.responsabilidad_schemas import (
    ResponsabilidadResumenCalculo,
    ResponsabilidadResponse,
    ResponsabilidadListResponse,
    ConfiguracionResponsabilidadResponse,
    ConfiguracionResponsabilidadUpdate,
    AccionResponsabilidadRequest,
    AccionResponsabilidadResponse,
    HistorialListResponse,
    PendientesAprobacionResponse,
    EnDisputaResponse,
)
from ..api_schemas import OperacionResponse
from ..db_utils import get_database

# RBAC - Fase 2D
from core.rbac.middleware import require_permission, require_explicit_permission
from core.rbac_helper_sql import get_role_code

router = APIRouter()


def get_db():
    """Obtiene conexión a la base de datos."""
    return get_database()


# ==================== CÁLCULO ====================

@router.post(
    "/calcular/{workflow_id}",
    response_model=ResponsabilidadResumenCalculo,
    summary="Calcular impacto económico",
    description="""
    Ejecuta el cálculo de responsabilidad económica para un workflow.
    Requiere permiso RESPONSABILIDAD_CALCULAR.
    
    Flujo:
    1. Lee las diferencias del workflow
    2. Clasifica faltantes y sobrantes
    3. Aplica tolerancias configurables
    4. Calcula monto propuesto (solo faltantes fuera de tolerancia)
    5. Persiste con estado CALCULADO
    6. Actualiza workflow a EN_REVISION_FINANCIERA
    
    **Nota:** Los sobrantes se registran pero NO compensan faltantes.
    """
)
async def calcular_responsabilidad(
    workflow_id: str,
    usuario_id: str = Query(..., description="ID del usuario que ejecuta el cálculo"),
    forzar_recalculo: bool = Query(False, description="Forzar recálculo si ya existe"),
    current_user: dict = Depends(require_explicit_permission("RESPONSABILIDAD_CALCULAR"))
):
    """Calcula el impacto económico de un workflow."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        resultado = await service.calcular_responsabilidad(
            workflow_id=workflow_id,
            usuario_id=usuario_id,
            forzar_recalculo=forzar_recalculo
        )
        
        return resultado
        
    except ModuloDesactivadoError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except WorkflowNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CalculoYaExisteError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except SinDiferenciasError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==================== CONSULTAS ====================

@router.get(
    "/workflow/{workflow_id}",
    response_model=ResponsabilidadResponse,
    summary="Obtener cálculo por workflow",
    description="Obtiene el cálculo de responsabilidad económica de un workflow específico. Requiere RESPONSABILIDAD_VER."
)
async def obtener_por_workflow(
    workflow_id: str,
    current_user: dict = Depends(require_permission("RESPONSABILIDAD_VER"))
):
    """Obtiene el cálculo de responsabilidad de un workflow."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        resultado = await service.obtener_por_workflow(workflow_id)
        
        if not resultado:
            raise HTTPException(
                status_code=404,
                detail=f"No existe cálculo de responsabilidad para el workflow {workflow_id}"
            )
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "",
    response_model=ResponsabilidadListResponse,
    summary="Listar cálculos de responsabilidad",
    description="Lista todos los cálculos de responsabilidad económica con filtros opcionales. Requiere RESPONSABILIDAD_VER."
)
async def listar_responsabilidades(
    sucursal_id: Optional[str] = Query(None, description="Filtrar por sucursal"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (CALCULADO)"),
    excede_minimo: Optional[bool] = Query(None, description="Filtrar por si excede mínimo"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=200, description="Límite de registros"),
    current_user: dict = Depends(require_permission("RESPONSABILIDAD_VER"))
):
    """Lista cálculos de responsabilidad con filtros."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        resultado = await service.listar(
            sucursal_id=sucursal_id,
            estado=estado,
            excede_minimo=excede_minimo,
            skip=skip,
            limit=limit
        )
        
        return ResponsabilidadListResponse(
            items=resultado["items"],
            total=resultado["total"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==================== CONFIGURACIÓN ====================

@router.get(
    "/configuracion",
    response_model=ConfiguracionResponsabilidadResponse,
    summary="Obtener configuración de responsabilidad",
    description="""
    Obtiene la configuración actual del módulo de responsabilidad económica.
    Requiere permiso RESPONSABILIDAD_VER.
    
    Incluye:
    - cargo_minimo_mxn: Monto mínimo para generar cargo
    - tolerancia_unidades: Tolerancia absoluta en unidades
    - tolerancia_porcentaje_diferencia: Tolerancia relativa (%)
    - precio_faltante_default: Precio unitario por defecto
    - modulo_responsabilidad_activo: Si el módulo está habilitado
    - permitir_compensacion_faltantes_sobrantes: Si se permite compensación (default: false)
    """
)
async def obtener_configuracion(
    current_user: dict = Depends(require_permission("RESPONSABILIDAD_VER"))
):
    """Obtiene la configuración de responsabilidad."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        return await service.obtener_configuracion()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put(
    "/configuracion",
    response_model=ConfiguracionResponsabilidadResponse,
    summary="Actualizar configuración de responsabilidad",
    description="Actualiza los parámetros de configuración del módulo de responsabilidad económica. Requiere RESPONSABILIDAD_GESTIONAR."
)
async def actualizar_configuracion(
    request: ConfiguracionResponsabilidadUpdate,
    current_user: dict = Depends(require_explicit_permission("RESPONSABILIDAD_GESTIONAR"))
):
    """Actualiza la configuración de responsabilidad."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        return await service.actualizar_configuracion(
            cargo_minimo_mxn=request.cargo_minimo_mxn,
            tolerancia_unidades=request.tolerancia_unidades,
            tolerancia_porcentaje_diferencia=request.tolerancia_porcentaje_diferencia,
            precio_faltante_default=request.precio_faltante_default,
            modulo_responsabilidad_activo=request.modulo_responsabilidad_activo,
            permitir_compensacion_faltantes_sobrantes=request.permitir_compensacion_faltantes_sobrantes
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==================== INICIALIZACIÓN ====================

@router.post(
    "/inicializar-configuracion",
    response_model=OperacionResponse,
    summary="Inicializar configuración",
    description="Inicializa las claves de configuración del módulo si no existen. Requiere permiso RESPONSABILIDAD_GESTIONAR."
)
async def inicializar_configuracion(
    current_user: dict = Depends(require_explicit_permission("RESPONSABILIDAD_GESTIONAR"))
):
    """Inicializa la configuración del módulo."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        resultado = await service.inicializar_configuracion()
        
        return OperacionResponse(
            success=True,
            message=resultado["mensaje"],
            data=resultado
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==================== MÉTRICAS DASHBOARD ====================

@router.get(
    "/metricas",
    summary="Métricas de responsabilidad económica",
    description="""
    Obtiene métricas agregadas para el dashboard de responsabilidad económica.
    Requiere permiso RESPONSABILIDAD_VER.
    
    Incluye:
    - Total de cálculos
    - Monto total propuesto
    - Cálculos que exceden mínimo
    - Workflows en revisión financiera
    - Top sucursales por monto
    """
)
async def obtener_metricas(
    current_user: dict = Depends(require_permission("RESPONSABILIDAD_VER"))
):
    """Obtiene métricas agregadas de responsabilidad."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        metricas = await service.obtener_metricas_dashboard()
        return metricas
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


def _get_authenticated_responsabilidad_actor(current_user: dict):
    """Deriva identidad real desde JWT/RBAC, no desde el body del cliente."""
    usuario_id = str(
        current_user.get("id")
        or current_user.get("user_id")
        or current_user.get("sub")
        or current_user.get("email")
        or ""
    ).strip()
    usuario_rol = get_role_code(current_user)

    if not usuario_id or not usuario_rol:
        raise HTTPException(
            status_code=403,
            detail="No fue posible resolver identidad RBAC del usuario autenticado"
        )

    return usuario_id, usuario_rol


# ==================== FASE 2C.2: APROBACIONES ====================

def _handle_aprobacion_error(e: Exception):
    """Maneja errores comunes de aprobaciones."""
    if isinstance(e, AprobacionesDesactivadasError):
        raise HTTPException(status_code=503, detail=str(e))
    elif isinstance(e, ResponsabilidadNoEncontradaError):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, TransicionInvalidaError):
        raise HTTPException(status_code=400, detail=str(e))
    elif isinstance(e, PermisoInsuficienteError):
        raise HTTPException(status_code=403, detail=str(e))
    elif isinstance(e, ValueError):
        raise HTTPException(status_code=422, detail=str(e))
    else:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post(
    "/{responsabilidad_id}/proponer",
    response_model=AccionResponsabilidadResponse,
    summary="Proponer monto para revisión",
    description="""
    Propone formalmente un monto calculado para revisión y aprobación.
    Requiere permiso RESPONSABILIDAD_PROPONER.
    
    **Transición:** CALCULADO → PROPUESTO
    
    **Requiere:** Comentario obligatorio (mínimo 10 caracteres)
    """
)
async def proponer(
    responsabilidad_id: str,
    request: AccionResponsabilidadRequest,
    current_user: dict = Depends(require_explicit_permission("RESPONSABILIDAD_PROPONER"))
):
    """Propone un monto para revisión."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        usuario_id, usuario_rol = _get_authenticated_responsabilidad_actor(current_user)

        return await service.proponer(
            responsabilidad_id=responsabilidad_id,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=request.comentario,
            motivo_codigo=request.motivo_codigo
        )
    except Exception as e:
        _handle_aprobacion_error(e)


@router.post(
    "/{responsabilidad_id}/aprobar",
    response_model=AccionResponsabilidadResponse,
    summary="Aprobar monto propuesto",
    description="""
    Aprueba un monto propuesto. El cargo queda pendiente de aplicación (Fase 2C.3).
    Requiere permiso RESPONSABILIDAD_APROBAR.
    
    **Transición:** PROPUESTO → APROBADO
    
    **Requiere:** 
    - Comentario obligatorio (mínimo 10 caracteres)
    - Nivel de autorización según monto
    
    **Nota:** El workflow permanece en EN_REVISION_FINANCIERA
    """
)
async def aprobar(
    responsabilidad_id: str,
    request: AccionResponsabilidadRequest,
    current_user: dict = Depends(require_explicit_permission("RESPONSABILIDAD_APROBAR"))
):
    """Aprueba un monto propuesto."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        usuario_id, usuario_rol = _get_authenticated_responsabilidad_actor(current_user)

        return await service.aprobar(
            responsabilidad_id=responsabilidad_id,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=request.comentario,
            motivo_codigo=request.motivo_codigo
        )
    except Exception as e:
        _handle_aprobacion_error(e)


@router.post(
    "/{responsabilidad_id}/rechazar",
    response_model=AccionResponsabilidadResponse,
    summary="Rechazar cargo",
    description="""
    Rechaza un cargo propuesto. El monto NO procedía como fue planteado.
    Requiere permiso RESPONSABILIDAD_RECHAZAR.
    
    **Transición:** PROPUESTO/EN_DISPUTA → RECHAZADO
    
    **Requiere:** Comentario obligatorio explicando por qué no procede
    
    **Diferencia con Exonerar:** Rechazado significa que el cargo no tenía base válida.
    """
)
async def rechazar(
    responsabilidad_id: str,
    request: AccionResponsabilidadRequest,
    current_user: dict = Depends(require_explicit_permission("RESPONSABILIDAD_RECHAZAR"))
):
    """Rechaza un cargo propuesto."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        usuario_id, usuario_rol = _get_authenticated_responsabilidad_actor(current_user)

        return await service.rechazar(
            responsabilidad_id=responsabilidad_id,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=request.comentario,
            motivo_codigo=request.motivo_codigo
        )
    except Exception as e:
        _handle_aprobacion_error(e)


@router.post(
    "/{responsabilidad_id}/exonerar",
    response_model=AccionResponsabilidadResponse,
    summary="Exonerar cargo",
    description="""
    Exonera al responsable del cargo. El cargo TENÍA base válida, pero se libera al responsable.
    Requiere permiso RESPONSABILIDAD_EXONERAR.
    
    **Transición:** PROPUESTO/EN_DISPUTA → EXONERADO
    
    **Requiere:** 
    - Comentario obligatorio explicando el motivo de exoneración
    - Nivel de autorización superior (GERENTE_OPS o DIRECCION)
    
    **Diferencia con Rechazar:** Exonerado significa que el cargo era válido pero se perdona.
    """
)
async def exonerar(
    responsabilidad_id: str,
    request: AccionResponsabilidadRequest,
    current_user: dict = Depends(require_explicit_permission("RESPONSABILIDAD_EXONERAR"))
):
    """Exonera un cargo."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        usuario_id, usuario_rol = _get_authenticated_responsabilidad_actor(current_user)

        return await service.exonerar(
            responsabilidad_id=responsabilidad_id,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=request.comentario,
            motivo_codigo=request.motivo_codigo
        )
    except Exception as e:
        _handle_aprobacion_error(e)


@router.post(
    "/{responsabilidad_id}/disputar",
    response_model=AccionResponsabilidadResponse,
    summary="Iniciar disputa",
    description="""
    Inicia una disputa sobre el monto propuesto.
    Requiere permiso RESPONSABILIDAD_DISPUTAR.
    
    **Transición:** PROPUESTO → EN_DISPUTA
    
    **Quién puede disputar:**
    - El afectado directo
    - Un supervisor o nivel superior
    
    **Requiere:** Comentario obligatorio explicando el motivo de la disputa
    """
)
async def disputar(
    responsabilidad_id: str,
    request: AccionResponsabilidadRequest,
    current_user: dict = Depends(require_explicit_permission("RESPONSABILIDAD_DISPUTAR"))
):
    """Inicia una disputa."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        usuario_id, usuario_rol = _get_authenticated_responsabilidad_actor(current_user)

        return await service.disputar(
            responsabilidad_id=responsabilidad_id,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=request.comentario,
            motivo_codigo=request.motivo_codigo
        )
    except Exception as e:
        _handle_aprobacion_error(e)


@router.post(
    "/{responsabilidad_id}/resolver-disputa",
    response_model=AccionResponsabilidadResponse,
    summary="Resolver disputa",
    description="""
    Resuelve una disputa, devolviendo el registro a estado PROPUESTO para revisión.
    Requiere permiso RESPONSABILIDAD_GESTIONAR.
    
    **Transición:** EN_DISPUTA → PROPUESTO
    
    **Requiere:** Comentario obligatorio con la resolución de la disputa
    """
)
async def resolver_disputa(
    responsabilidad_id: str,
    request: AccionResponsabilidadRequest,
    current_user: dict = Depends(require_explicit_permission("RESPONSABILIDAD_GESTIONAR"))
):
    """Resuelve una disputa."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        usuario_id, usuario_rol = _get_authenticated_responsabilidad_actor(current_user)

        return await service.resolver_disputa(
            responsabilidad_id=responsabilidad_id,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=request.comentario,
            motivo_codigo=request.motivo_codigo
        )
    except Exception as e:
        _handle_aprobacion_error(e)


# ==================== CONSULTAS 2C.2 ====================

@router.get(
    "/pendientes-aprobacion",
    response_model=PendientesAprobacionResponse,
    summary="Listar pendientes de aprobación",
    description="Obtiene la lista de responsabilidades pendientes de aprobación (CALCULADO o PROPUESTO). Requiere RESPONSABILIDAD_VER."
)
async def listar_pendientes_aprobacion(
    current_user: dict = Depends(require_permission("RESPONSABILIDAD_VER"))
):
    """Lista responsabilidades pendientes de aprobación."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        return await service.obtener_pendientes_aprobacion()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/en-disputa",
    response_model=EnDisputaResponse,
    summary="Listar en disputa",
    description="Obtiene la lista de responsabilidades actualmente en disputa. Requiere RESPONSABILIDAD_VER."
)
async def listar_en_disputa(
    current_user: dict = Depends(require_permission("RESPONSABILIDAD_VER"))
):
    """Lista responsabilidades en disputa."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        return await service.obtener_en_disputa()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/{responsabilidad_id}/historial",
    response_model=HistorialListResponse,
    summary="Obtener historial de transiciones",
    description="Obtiene el historial completo de transiciones de una responsabilidad. Requiere RESPONSABILIDAD_VER."
)
async def obtener_historial(
    responsabilidad_id: str,
    current_user: dict = Depends(require_permission("RESPONSABILIDAD_VER"))
):
    """Obtiene el historial de una responsabilidad."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        return await service.obtener_historial(responsabilidad_id)
        
    except ResponsabilidadNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
