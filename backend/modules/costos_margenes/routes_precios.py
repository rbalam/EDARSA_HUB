from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
from core.rbac_helper_sql import (
    es_admin, get_role_code,
    ROLES_APROBADORES, ROLES_COMERCIAL_OPERATIVO, ROLES_LECTORES,
)
"""
Endpoints para Simulación de Precios y Solicitudes de Cambio
FASE 1C-3F - Costos y Márgenes

IMPORTANTE:
- NO se modifican precios oficiales directamente
- El flujo de autorización es OBLIGATORIO
- Toda acción queda registrada en historial
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
import math

from modules.costos_margenes.schemas_precios import (
    SimulacionPrecioRequest,
    SimulacionPrecioResponse,
    SolicitudCambioPrecioCreate,
    SolicitudCambioPrecioUpdate,
    SolicitudCambioPrecioResponse,
    SolicitudCambioPrecioListItem,
    SolicitudesListResponse,
    AccionSolicitudRequest,
    AccionSolicitudResponse,
    HistorialSolicitudItem,
    HistorialSolicitudResponse,
    EstatusSolicitud,
    AccionSolicitud,
    RecomendacionPrecio,
)
from modules.costos_margenes.routes import (
    COSTOS_MARGENES_VER,
    _resolve_servidor_filtro,
    _verify_costos_margenes_access,
)
from modules.costos_margenes.repository_precios import (
    obtener_datos_producto_para_simulacion,
    calcular_simulacion,
    guardar_simulacion,
    crear_solicitud_cambio_precio,
    obtener_solicitud,
    listar_solicitudes,
    cambiar_estatus_solicitud,
    obtener_historial_solicitud,
)
from core.security import get_current_user


router = APIRouter(prefix="/costos-margenes", tags=["Costos y Márgenes - Precios"])


# ==================== RBAC HELPERS ====================

def _get_user_permissions(user: dict) -> dict:
    """
    FASE 1C-3F: Determina permisos del usuario para el flujo de precios.
    """
    # CodigoRol canónico (normaliza NombreRol legacy desde dbo.Usuario_Roles)
    codigo = get_role_code(user)
    
    # Permisos por rol
    permisos = {
        'simular_precio': False,
        'solicitar_cambio_precio': False,
        'ver_solicitudes_precio': False,
        'aprobar_cambio_precio': False,
        'rechazar_cambio_precio': False,
        'aplicar_cambio_precio': False,
        'ver_historial_precios': False,
        'ver_costos': False,
    }
    
    # SuperAdmin / Admin - todos los permisos (RBAC canónico)
    if es_admin(user):
        return {k: True for k in permisos}
    
    # Aprobadores (Gerencias / Supervisión) - puede aprobar/rechazar (canónico)
    if codigo in ROLES_APROBADORES:
        permisos['simular_precio'] = True
        permisos['solicitar_cambio_precio'] = True
        permisos['ver_solicitudes_precio'] = True
        permisos['aprobar_cambio_precio'] = True
        permisos['rechazar_cambio_precio'] = True
        permisos['ver_historial_precios'] = True
        permisos['ver_costos'] = True
        return permisos
    
    # Comercial operativo / Ventas - puede solicitar, no aprobar (canónico)
    if codigo in ROLES_COMERCIAL_OPERATIVO:
        permisos['simular_precio'] = True
        permisos['solicitar_cambio_precio'] = True
        permisos['ver_solicitudes_precio'] = True
        permisos['ver_historial_precios'] = True
        permisos['ver_costos'] = True
        return permisos
    
    # Lectores (Usuario / Visores) - solo ver (canónico)
    if codigo in ROLES_LECTORES:
        permisos['ver_solicitudes_precio'] = True
        permisos['ver_historial_precios'] = True
        return permisos
    
    return permisos


def _require_permission(user: dict, permiso: str) -> None:
    """Verifica permiso específico."""
    permisos = _get_user_permissions(user)
    if not permisos.get(permiso, False):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "PERMISO_DENEGADO",
                "mensaje": f"No tiene permiso para: {permiso}",
                "permiso_requerido": f"comercial.costos_margenes.{permiso}"
            }
        )


async def _resolve_precio_scope(
    current_user: dict,
    unidad: Optional[str],
    unidad_negocio_pk: Optional[str],
    server_id: Optional[str],
    permission: Optional[dict] = None,
    require_server: bool = False,
    raise_on_denied: bool = True,
):
    """Resuelve alcance canónico para simulación y solicitudes de precio."""
    servidor_id_filtro, _, access_denied, unidad_pk = await _resolve_servidor_filtro(
        current_user,
        unidad or unidad_negocio_pk,
        server_id,
        permission,
    )
    if access_denied:
        if raise_on_denied:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "ALCANCE_DENEGADO",
                    "mensaje": "No tiene acceso a la unidad solicitada",
                    "permiso_requerido": COSTOS_MARGENES_VER,
                },
            )
        return None, None, True

    if require_server and not servidor_id_filtro:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "UNIDAD_CANONICA_REQUERIDA",
                "mensaje": "Seleccione una unidad canónica para operar precios",
            },
        )

    return servidor_id_filtro, unidad_pk, False


async def _assert_solicitud_scope(
    current_user: dict,
    solicitud: dict,
    permission: Optional[dict] = None,
) -> None:
    """Valida que la solicitud pertenezca al alcance RBAC del usuario."""
    unidad_pk = solicitud.get('unidad_negocio_pk')
    server_id = solicitud.get('server_id')

    if unidad_pk:
        resolved_server_id, _, _ = await _resolve_precio_scope(
            current_user,
            unidad_pk,
            None,
            None,
            permission,
            require_server=True,
        )
        if server_id and str(resolved_server_id).lower() != str(server_id).lower():
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "ALCANCE_DENEGADO",
                    "mensaje": "La solicitud no corresponde a la unidad autorizada",
                },
            )
        return

    if server_id:
        await _resolve_precio_scope(
            current_user,
            None,
            None,
            server_id,
            permission,
            require_server=True,
        )
        return

    raise HTTPException(
        status_code=403,
        detail={
            "error": "ALCANCE_CANONICO_INCOMPLETO",
            "mensaje": "La solicitud no tiene unidad canónica ni servidor asociado",
        },
    )


def _get_acciones_disponibles(solicitud: dict, user: dict) -> list:
    """Determina acciones disponibles según estado y permisos."""
    permisos = _get_user_permissions(user)
    estatus = solicitud['estatus']
    es_solicitante = solicitud['solicitante_usuario_id'] == user.get('id')
    
    acciones = []
    
    if estatus == 'BORRADOR':
        if es_solicitante or permisos.get('aprobar_cambio_precio'):
            acciones.extend(['editar', 'enviar', 'cancelar'])
    
    elif estatus == 'SOLICITADA':
        if permisos.get('aprobar_cambio_precio'):
            acciones.append('revisar')
        if es_solicitante:
            acciones.append('cancelar')
    
    elif estatus == 'EN_REVISION':
        if permisos.get('aprobar_cambio_precio'):
            acciones.extend(['aprobar', 'rechazar', 'devolver'])
    
    elif estatus == 'APROBADA':
        if permisos.get('aplicar_cambio_precio'):
            acciones.append('aplicar')
        if permisos.get('aprobar_cambio_precio'):
            acciones.append('cancelar')
    
    elif estatus == 'ERROR_APLICACION':
        if permisos.get('aplicar_cambio_precio'):
            acciones.append('reintentar')
    
    return acciones


# ==================== SIMULACIÓN ====================

@router.post("/simulacion", response_model=SimulacionPrecioResponse)
async def simular_precio(
    request: Request,
    data: SimulacionPrecioRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Simula un cambio de precio sin modificar datos oficiales.
    
    **FASE 1C-3F**
    
    **Permisos**: comercial.costos_margenes.simular_precio
    
    **Fuente**: EDARSAHUB SQL (NO-LIVE)
    
    **Importante**: La simulación NO modifica ningún precio oficial.
    Solo calcula el impacto de un cambio hipotético.
    """
    permission = _verify_costos_margenes_access(current_user)
    _require_permission(current_user, 'simular_precio')
    server_id_filtro, _, _ = await _resolve_precio_scope(
        current_user,
        data.unidad,
        data.unidad_negocio_pk,
        data.server_id,
        permission,
        require_server=True,
    )
    
    try:
        # Obtener datos actuales del producto
        datos_producto = obtener_datos_producto_para_simulacion(
            data.producto_id, 
            server_id_filtro
        )
        
        if not datos_producto:
            raise HTTPException(
                status_code=404,
                detail=f"Producto no encontrado: {data.producto_id}"
            )
        
        # Calcular simulación
        simulacion = calcular_simulacion(
            datos_producto['precio_actual'],
            datos_producto['costo_actual'],
            data.precio_nuevo,
            datos_producto.get('margen_objetivo')
        )
        
        # Guardar simulación si se solicita
        simulacion_id = None
        if data.guardar_simulacion:
            ip = request.client.host if request.client else None
            simulacion_id = guardar_simulacion(
                data.producto_id,
                server_id_filtro,
                datos_producto,
                simulacion,
                current_user.get('id', ''),
                current_user.get('email', ''),
                ip
            )
        
        return SimulacionPrecioResponse(
            producto_id=datos_producto['producto_id'],
            codigo_producto=datos_producto['codigo_producto'],
            nombre_producto=datos_producto['nombre_producto'],
            server_id=datos_producto['server_id'],
            system_type=datos_producto['system_type'],
            familia=datos_producto.get('familia_nombre'),
            precio_actual=datos_producto['precio_actual'],
            costo_actual=datos_producto['costo_actual'],
            margen_actual_pesos=datos_producto['margen_actual_pesos'],
            margen_actual_porcentaje=datos_producto['margen_actual_porcentaje'],
            precio_simulado=simulacion['precio_simulado'],
            margen_simulado_pesos=simulacion['margen_simulado_pesos'],
            margen_simulado_porcentaje=simulacion['margen_simulado_porcentaje'],
            variacion_pesos=simulacion['variacion_pesos'],
            variacion_porcentaje=simulacion['variacion_porcentaje'],
            margen_objetivo=datos_producto.get('margen_objetivo'),
            recomendacion=RecomendacionPrecio(simulacion['recomendacion']),
            impacto_estimado=simulacion['impacto_estimado'],
            sync_run_id=datos_producto.get('sync_run_id'),
            fecha_datos_costo=datos_producto.get('fecha_datos_costo'),
            simulacion_id=simulacion_id,
            source_type="EDARSAHUB_SQL"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en simulación")


# ==================== SOLICITUDES CRUD ====================

@router.post("/solicitudes-precio", response_model=SolicitudCambioPrecioResponse)
async def crear_solicitud(
    request: Request,
    data: SolicitudCambioPrecioCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Crea una nueva solicitud de cambio de precio.
    
    **FASE 1C-3F**
    
    **Estado inicial**: BORRADOR
    
    **Permisos**: comercial.costos_margenes.solicitar_cambio_precio
    
    **Importante**: La solicitud NO modifica precios. 
    Debe pasar por el flujo de autorización.
    """
    permission = _verify_costos_margenes_access(current_user)
    _require_permission(current_user, 'solicitar_cambio_precio')
    server_id_filtro, unidad_pk, _ = await _resolve_precio_scope(
        current_user,
        data.unidad,
        data.unidad_negocio_pk,
        data.server_id,
        permission,
        require_server=True,
    )
    
    try:
        ip = request.client.host if request.client else None
        
        resultado = crear_solicitud_cambio_precio(
            producto_id=data.producto_id,
            server_id=server_id_filtro,
            precio_solicitado=data.precio_solicitado,
            motivo=data.motivo,
            justificacion=data.justificacion,
            usuario_id=current_user.get('id', ''),
            usuario_email=current_user.get('email', ''),
            usuario_nombre=current_user.get('nombre'),
            simulacion_id=data.simulacion_id,
            ip=ip,
            unidad_negocio_pk=unidad_pk
        )
        
        # Obtener solicitud completa
        solicitud = obtener_solicitud(resultado['solicitud_id'])
        solicitud['acciones_disponibles'] = _get_acciones_disponibles(solicitud, current_user)
        
        return SolicitudCambioPrecioResponse(**solicitud)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando solicitud")


@router.get("/solicitudes-precio", response_model=SolicitudesListResponse)
async def listar_solicitudes_precio(
    current_user: dict = Depends(get_current_user),
    estatus: Optional[str] = Query(None, description="Filtrar por estatus"),
    unidad: Optional[str] = Query(None, description="CANÓNICO: unidad de negocio (codigo o id)"),
    unidad_negocio_pk: Optional[str] = Query(None, description="DEPRECATED: usar unidad"),
    server_id: Optional[str] = Query(None, description="DEPRECATED: usar unidad"),
    mis_solicitudes: bool = Query(False, description="Solo mis solicitudes"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Lista solicitudes de cambio de precio.
    
    **FASE 1C-3F**
    
    **Permisos**: comercial.costos_margenes.ver_solicitudes_precio
    """
    permission = _verify_costos_margenes_access(current_user)
    _require_permission(current_user, 'ver_solicitudes_precio')
    server_id_filtro, unidad_pk, access_denied = await _resolve_precio_scope(
        current_user,
        unidad,
        unidad_negocio_pk,
        server_id,
        permission,
        raise_on_denied=False,
    )
    if access_denied:
        return SolicitudesListResponse(
            solicitudes=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
            source_type="EDARSAHUB_SQL"
        )
    
    try:
        solicitante_id = current_user.get('id') if mis_solicitudes else None
        
        solicitudes, total = listar_solicitudes(
            estatus=estatus,
            server_id=server_id_filtro,
            unidad_negocio_pk=unidad_pk,
            solicitante_id=solicitante_id,
            page=page,
            page_size=page_size
        )
        
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        
        return SolicitudesListResponse(
            solicitudes=[SolicitudCambioPrecioListItem(**s) for s in solicitudes],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            source_type="EDARSAHUB_SQL"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando solicitudes")


@router.get("/solicitudes-precio/{solicitud_id}", response_model=SolicitudCambioPrecioResponse)
async def obtener_solicitud_precio(
    solicitud_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene detalle de una solicitud de cambio de precio.
    
    **FASE 1C-3F**
    
    **Permisos**: comercial.costos_margenes.ver_solicitudes_precio
    """
    permission = _verify_costos_margenes_access(current_user)
    _require_permission(current_user, 'ver_solicitudes_precio')
    
    try:
        solicitud = obtener_solicitud(solicitud_id)
        
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        await _assert_solicitud_scope(current_user, solicitud, permission)
        
        solicitud['acciones_disponibles'] = _get_acciones_disponibles(solicitud, current_user)
        
        return SolicitudCambioPrecioResponse(**solicitud)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo solicitud")


# ==================== ACCIONES DEL FLUJO ====================

@router.post("/solicitudes-precio/{solicitud_id}/enviar", response_model=AccionSolicitudResponse)
async def enviar_solicitud(
    solicitud_id: str,
    request: Request,
    data: AccionSolicitudRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Envía una solicitud para revisión.
    
    **Transición**: BORRADOR → SOLICITADA
    
    **Permisos**: comercial.costos_margenes.solicitar_cambio_precio
    """
    permission = _verify_costos_margenes_access(current_user)
    _require_permission(current_user, 'solicitar_cambio_precio')
    
    try:
        solicitud = obtener_solicitud(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        await _assert_solicitud_scope(current_user, solicitud, permission)

        ip = request.client.host if request.client else None
        comentario = data.comentario if data else None
        
        resultado = cambiar_estatus_solicitud(
            solicitud_id=solicitud_id,
            nuevo_estatus='SOLICITADA',
            usuario_id=current_user.get('id', ''),
            usuario_email=current_user.get('email', ''),
            usuario_nombre=current_user.get('nombre'),
            comentario=comentario,
            ip=ip
        )
        
        return AccionSolicitudResponse(
            solicitud_id=solicitud_id,
            accion=AccionSolicitud.ENVIAR,
            estatus_anterior=EstatusSolicitud(resultado['estatus_anterior']),
            estatus_nuevo=EstatusSolicitud(resultado['estatus_nuevo']),
            mensaje="Solicitud enviada para revisión",
            fecha_accion=__import__('datetime').datetime.now(),
            source_type="EDARSAHUB_SQL"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enviando solicitud")


@router.post("/solicitudes-precio/{solicitud_id}/aprobar", response_model=AccionSolicitudResponse)
async def aprobar_solicitud(
    solicitud_id: str,
    request: Request,
    data: AccionSolicitudRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Aprueba una solicitud de cambio de precio.
    
    **Transición**: EN_REVISION → APROBADA
    
    **Permisos**: comercial.costos_margenes.aprobar_cambio_precio
    
    **Importante**: La aprobación NO aplica el cambio automáticamente.
    El cambio debe ser aplicado por un Modificador autorizado.
    """
    permission = _verify_costos_margenes_access(current_user)
    _require_permission(current_user, 'aprobar_cambio_precio')
    
    try:
        # Verificar que la solicitud está en estado válido para aprobar
        solicitud = obtener_solicitud(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        await _assert_solicitud_scope(current_user, solicitud, permission)
        
        # Si está en SOLICITADA, primero pasar a EN_REVISION
        if solicitud['estatus'] == 'SOLICITADA':
            cambiar_estatus_solicitud(
                solicitud_id=solicitud_id,
                nuevo_estatus='EN_REVISION',
                usuario_id=current_user.get('id', ''),
                usuario_email=current_user.get('email', ''),
                ip=request.client.host if request.client else None
            )
        elif solicitud['estatus'] != 'EN_REVISION':
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede aprobar una solicitud en estado {solicitud['estatus']}"
            )
        
        ip = request.client.host if request.client else None
        comentario = data.comentario if data else None
        
        resultado = cambiar_estatus_solicitud(
            solicitud_id=solicitud_id,
            nuevo_estatus='APROBADA',
            usuario_id=current_user.get('id', ''),
            usuario_email=current_user.get('email', ''),
            usuario_nombre=current_user.get('nombre'),
            comentario=comentario,
            ip=ip
        )
        
        return AccionSolicitudResponse(
            solicitud_id=solicitud_id,
            accion=AccionSolicitud.APROBAR,
            estatus_anterior=EstatusSolicitud(resultado['estatus_anterior']),
            estatus_nuevo=EstatusSolicitud.APROBADA,
            mensaje="Solicitud aprobada. Pendiente de aplicación por Modificador autorizado.",
            fecha_accion=__import__('datetime').datetime.now(),
            source_type="EDARSAHUB_SQL"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aprobando solicitud")


@router.post("/solicitudes-precio/{solicitud_id}/rechazar", response_model=AccionSolicitudResponse)
async def rechazar_solicitud(
    solicitud_id: str,
    request: Request,
    data: AccionSolicitudRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Rechaza una solicitud de cambio de precio.
    
    **Transición**: EN_REVISION → RECHAZADA
    
    **Permisos**: comercial.costos_margenes.rechazar_cambio_precio
    
    **Nota**: El comentario/motivo de rechazo es obligatorio.
    """
    permission = _verify_costos_margenes_access(current_user)
    _require_permission(current_user, 'rechazar_cambio_precio')
    
    if not data or not data.comentario:
        raise HTTPException(
            status_code=400, 
            detail="El motivo de rechazo es obligatorio"
        )
    
    try:
        # Verificar y transicionar si es necesario
        solicitud = obtener_solicitud(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        await _assert_solicitud_scope(current_user, solicitud, permission)
        
        if solicitud['estatus'] == 'SOLICITADA':
            cambiar_estatus_solicitud(
                solicitud_id=solicitud_id,
                nuevo_estatus='EN_REVISION',
                usuario_id=current_user.get('id', ''),
                usuario_email=current_user.get('email', ''),
                ip=request.client.host if request.client else None
            )
        
        ip = request.client.host if request.client else None
        
        resultado = cambiar_estatus_solicitud(
            solicitud_id=solicitud_id,
            nuevo_estatus='RECHAZADA',
            usuario_id=current_user.get('id', ''),
            usuario_email=current_user.get('email', ''),
            usuario_nombre=current_user.get('nombre'),
            comentario=data.comentario,
            ip=ip
        )
        
        return AccionSolicitudResponse(
            solicitud_id=solicitud_id,
            accion=AccionSolicitud.RECHAZAR,
            estatus_anterior=EstatusSolicitud(resultado['estatus_anterior']),
            estatus_nuevo=EstatusSolicitud.RECHAZADA,
            mensaje="Solicitud rechazada",
            fecha_accion=__import__('datetime').datetime.now(),
            source_type="EDARSAHUB_SQL"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rechazando solicitud")


@router.post("/solicitudes-precio/{solicitud_id}/aplicar", response_model=AccionSolicitudResponse)
async def aplicar_solicitud(
    solicitud_id: str,
    request: Request,
    data: AccionSolicitudRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Marca una solicitud como aplicada.
    
    **Transición**: APROBADA → APLICADA
    
    **Permisos**: comercial.costos_margenes.aplicar_cambio_precio
    
    **FASE 1C-3F NOTA**: En esta fase, el endpoint solo registra la aplicación.
    La modificación real del precio en sistema origen (SoftRestaurant/MPRO)
    se realizará en una fase posterior con diseño de sincronización.
    
    **El precio queda registrado como "aplicado" para auditoría.**
    """
    permission = _verify_costos_margenes_access(current_user)
    _require_permission(current_user, 'aplicar_cambio_precio')
    
    try:
        solicitud = obtener_solicitud(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        await _assert_solicitud_scope(current_user, solicitud, permission)
        
        if solicitud['estatus'] != 'APROBADA':
            raise HTTPException(
                status_code=400, 
                detail=f"Solo se pueden aplicar solicitudes aprobadas. Estado actual: {solicitud['estatus']}"
            )
        
        ip = request.client.host if request.client else None
        comentario = data.comentario if data else "Aplicación registrada (pendiente sincronización con origen)"
        
        resultado = cambiar_estatus_solicitud(
            solicitud_id=solicitud_id,
            nuevo_estatus='APLICADA',
            usuario_id=current_user.get('id', ''),
            usuario_email=current_user.get('email', ''),
            usuario_nombre=current_user.get('nombre'),
            comentario=comentario,
            ip=ip
        )
        
        return AccionSolicitudResponse(
            solicitud_id=solicitud_id,
            accion=AccionSolicitud.APLICAR,
            estatus_anterior=EstatusSolicitud.APROBADA,
            estatus_nuevo=EstatusSolicitud.APLICADA,
            mensaje=(
                f"Solicitud marcada como aplicada. "
                f"Precio registrado: ${solicitud['precio_solicitado']:.2f}. "
                f"Nota: La sincronización con sistema origen se realizará en fase posterior."
            ),
            fecha_accion=__import__('datetime').datetime.now(),
            source_type="EDARSAHUB_SQL"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aplicando solicitud")


@router.post("/solicitudes-precio/{solicitud_id}/cancelar", response_model=AccionSolicitudResponse)
async def cancelar_solicitud(
    solicitud_id: str,
    request: Request,
    data: AccionSolicitudRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancela una solicitud de cambio de precio.
    
    **Transiciones válidas**: BORRADOR/SOLICITADA/APROBADA → CANCELADA
    
    **Permisos**: comercial.costos_margenes.solicitar_cambio_precio
    """
    permission = _verify_costos_margenes_access(current_user)
    _require_permission(current_user, 'solicitar_cambio_precio')
    
    try:
        solicitud = obtener_solicitud(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        await _assert_solicitud_scope(current_user, solicitud, permission)
        
        estados_cancelables = ['BORRADOR', 'SOLICITADA', 'APROBADA']
        if solicitud['estatus'] not in estados_cancelables:
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede cancelar una solicitud en estado {solicitud['estatus']}"
            )
        
        ip = request.client.host if request.client else None
        comentario = data.comentario if data else "Solicitud cancelada por el usuario"
        
        resultado = cambiar_estatus_solicitud(
            solicitud_id=solicitud_id,
            nuevo_estatus='CANCELADA',
            usuario_id=current_user.get('id', ''),
            usuario_email=current_user.get('email', ''),
            usuario_nombre=current_user.get('nombre'),
            comentario=comentario,
            ip=ip
        )
        
        return AccionSolicitudResponse(
            solicitud_id=solicitud_id,
            accion=AccionSolicitud.CANCELAR,
            estatus_anterior=EstatusSolicitud(resultado['estatus_anterior']),
            estatus_nuevo=EstatusSolicitud.CANCELADA,
            mensaje="Solicitud cancelada",
            fecha_accion=__import__('datetime').datetime.now(),
            source_type="EDARSAHUB_SQL"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelando solicitud")


# ==================== HISTORIAL ====================

@router.get("/solicitudes-precio/{solicitud_id}/historial", response_model=HistorialSolicitudResponse)
async def obtener_historial(
    solicitud_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene el historial completo de una solicitud.
    
    **FASE 1C-3F**
    
    **Permisos**: comercial.costos_margenes.ver_historial_precios
    """
    permission = _verify_costos_margenes_access(current_user)
    _require_permission(current_user, 'ver_historial_precios')
    
    try:
        solicitud = obtener_solicitud(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        await _assert_solicitud_scope(current_user, solicitud, permission)
        
        historial = obtener_historial_solicitud(solicitud_id)
        
        return HistorialSolicitudResponse(
            solicitud_id=solicitud_id,
            folio_solicitud=solicitud['folio_solicitud'],
            historial=[HistorialSolicitudItem(**h) for h in historial],
            total_acciones=len(historial),
            source_type="EDARSAHUB_SQL"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial")
