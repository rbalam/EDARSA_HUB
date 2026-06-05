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
    role = user.get('role', '')
    
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
    
    # SuperAdmin / Admin - todos los permisos
    if role in ['SuperAdministrador', 'Administrador', 'admin', 'Admin']:
        return {k: True for k in permisos}
    
    # Gerente / Supervisor - puede aprobar/rechazar
    if role in ['Gerente', 'Supervisor']:
        permisos['simular_precio'] = True
        permisos['solicitar_cambio_precio'] = True
        permisos['ver_solicitudes_precio'] = True
        permisos['aprobar_cambio_precio'] = True
        permisos['rechazar_cambio_precio'] = True
        permisos['ver_historial_precios'] = True
        permisos['ver_costos'] = True
        return permisos
    
    # Comercial - puede solicitar, no aprobar
    if role in ['Comercial', 'Ventas']:
        permisos['simular_precio'] = True
        permisos['solicitar_cambio_precio'] = True
        permisos['ver_solicitudes_precio'] = True
        permisos['ver_historial_precios'] = True
        permisos['ver_costos'] = True
        return permisos
    
    # Usuario básico - solo ver
    if role in ['Usuario']:
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
    _require_permission(current_user, 'simular_precio')
    
    try:
        # Obtener datos actuales del producto
        datos_producto = obtener_datos_producto_para_simulacion(
            data.producto_id, 
            data.server_id
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
                data.server_id,
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
        raise HTTPException(status_code=500, detail=f"Error en simulación: {str(e)}")


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
    _require_permission(current_user, 'solicitar_cambio_precio')
    
    try:
        ip = request.client.host if request.client else None
        
        resultado = crear_solicitud_cambio_precio(
            producto_id=data.producto_id,
            server_id=data.server_id,
            precio_solicitado=data.precio_solicitado,
            motivo=data.motivo,
            justificacion=data.justificacion,
            usuario_id=current_user.get('id', ''),
            usuario_email=current_user.get('email', ''),
            usuario_nombre=current_user.get('nombre'),
            simulacion_id=data.simulacion_id,
            ip=ip
        )
        
        # Obtener solicitud completa
        solicitud = obtener_solicitud(resultado['solicitud_id'])
        solicitud['acciones_disponibles'] = _get_acciones_disponibles(solicitud, current_user)
        
        return SolicitudCambioPrecioResponse(**solicitud)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando solicitud: {str(e)}")


@router.get("/solicitudes-precio", response_model=SolicitudesListResponse)
async def listar_solicitudes_precio(
    current_user: dict = Depends(get_current_user),
    estatus: Optional[str] = Query(None, description="Filtrar por estatus"),
    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
    mis_solicitudes: bool = Query(False, description="Solo mis solicitudes"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Lista solicitudes de cambio de precio.
    
    **FASE 1C-3F**
    
    **Permisos**: comercial.costos_margenes.ver_solicitudes_precio
    """
    _require_permission(current_user, 'ver_solicitudes_precio')
    
    try:
        solicitante_id = current_user.get('id') if mis_solicitudes else None
        
        solicitudes, total = listar_solicitudes(
            estatus=estatus,
            server_id=server_id,
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
        raise HTTPException(status_code=500, detail=f"Error listando solicitudes: {str(e)}")


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
    _require_permission(current_user, 'ver_solicitudes_precio')
    
    try:
        solicitud = obtener_solicitud(solicitud_id)
        
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
        solicitud['acciones_disponibles'] = _get_acciones_disponibles(solicitud, current_user)
        
        return SolicitudCambioPrecioResponse(**solicitud)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo solicitud: {str(e)}")


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
    _require_permission(current_user, 'solicitar_cambio_precio')
    
    try:
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enviando solicitud: {str(e)}")


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
    _require_permission(current_user, 'aprobar_cambio_precio')
    
    try:
        # Verificar que la solicitud está en estado válido para aprobar
        solicitud = obtener_solicitud(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
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
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aprobando solicitud: {str(e)}")


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
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rechazando solicitud: {str(e)}")


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
    _require_permission(current_user, 'aplicar_cambio_precio')
    
    try:
        solicitud = obtener_solicitud(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
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
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aplicando solicitud: {str(e)}")


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
    _require_permission(current_user, 'solicitar_cambio_precio')
    
    try:
        solicitud = obtener_solicitud(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
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
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelando solicitud: {str(e)}")


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
    _require_permission(current_user, 'ver_historial_precios')
    
    try:
        solicitud = obtener_solicitud(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
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
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")
