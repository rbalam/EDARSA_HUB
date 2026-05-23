"""
EDARSA HUB - CRM Comercial Enterprise Routes
=============================================
Endpoints API para CRM Comercial completo.

Incluye:
- Cuentas CRM
- Clientes (lectura maestro)
- Solicitudes de alta de cliente
- Actividades
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, date
from decimal import Decimal
import logging
import os

from .comercial_service import CRMComercialService
from core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm", tags=["CRM Comercial"])

# Configuración DB
DB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_SQL_HOST', '54.39.104.176'),
    'port': int(os.environ.get('EDARSAHUB_SQL_PORT', 1433)),
    'database': os.environ.get('EDARSAHUB_SQL_DATABASE', 'EDARSAHUB'),
    'username': os.environ.get('EDARSAHUB_SQL_USER', 'HRLectura'),
    'password': os.environ.get('EDARSAHUB_SQL_PASSWORD', 'National09$')
}

def _get_service():
    return CRMComercialService(DB_CONFIG)


# ============================================================
# SCHEMAS
# ============================================================

class CuentaCreate(BaseModel):
    empresa_id: str
    sucursal_id: Optional[str] = None
    nombre_cuenta: str
    tipo_cuenta: Optional[str] = "PROSPECTO"
    razon_social: Optional[str] = None
    rfc: Optional[str] = None
    sector_id: Optional[int] = None
    tamano_cliente_id: Optional[int] = None
    ejecutivo_responsable_user_id: Optional[str] = None
    lead_origen_id: Optional[str] = None
    contacto_principal_nombre: Optional[str] = None
    contacto_principal_email: Optional[str] = None
    contacto_principal_telefono: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    pais: Optional[str] = "México"
    codigo_postal: Optional[str] = None
    sitio_web: Optional[str] = None
    descripcion: Optional[str] = None


class SolicitudAltaCreate(BaseModel):
    empresa_id: str
    sucursal_id: Optional[str] = None
    origen_entidad: Optional[str] = "DIRECTO"
    origen_entidad_id: Optional[str] = None
    cuenta_id: Optional[str] = None
    nombre_comercial: str
    razon_social: str
    rfc: str
    regimen_fiscal: Optional[str] = None
    uso_cfdi: Optional[str] = None
    email_facturacion: Optional[str] = None
    telefono_facturacion: Optional[str] = None
    calle: Optional[str] = None
    numero_exterior: Optional[str] = None
    numero_interior: Optional[str] = None
    colonia: Optional[str] = None
    municipio: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    pais: Optional[str] = "México"
    codigo_postal: Optional[str] = None
    contacto_principal_nombre: Optional[str] = None
    contacto_principal_email: Optional[str] = None
    contacto_principal_telefono: Optional[str] = None
    contacto_principal_puesto: Optional[str] = None
    requiere_credito: Optional[bool] = False
    limite_credito_solicitado: Optional[float] = None
    dias_credito_solicitados: Optional[int] = None
    condiciones_pago_solicitadas: Optional[str] = None
    observaciones_solicitante: Optional[str] = None


class ActividadCreate(BaseModel):
    empresa_id: str
    tipo_actividad_id: int
    entidad_tipo: str  # LEAD, CUENTA, OPORTUNIDAD, CONTACTO
    entidad_id: str
    titulo: str
    descripcion: Optional[str] = None
    prioridad: Optional[int] = 2
    fecha_programada: datetime
    fecha_fin: Optional[datetime] = None
    duracion: Optional[int] = None
    todo_el_dia: Optional[bool] = False
    asignado_a_user_id: Optional[str] = None
    tiene_recordatorio: Optional[bool] = False
    minutos_antes: Optional[int] = None


class LigarClienteRequest(BaseModel):
    cliente_id: int


class AutorizarSolicitudRequest(BaseModel):
    comentarios: Optional[str] = None


class RechazarSolicitudRequest(BaseModel):
    motivo: str


class CerrarActividadRequest(BaseModel):
    resultado_id: Optional[int] = None
    notas: Optional[str] = None


# ============================================================
# CUENTAS CRM
# ============================================================

@router.get("/cuentas")
async def listar_cuentas(
    empresa_id: Optional[str] = None,
    tipo_cuenta: Optional[str] = None,
    estatus: Optional[str] = None,
    ejecutivo_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Lista cuentas CRM con filtros"""
    try:
        service = _get_service()
        return service.listar_cuentas(
            empresa_id=empresa_id,
            tipo_cuenta=tipo_cuenta,
            estatus=estatus,
            ejecutivo_id=ejecutivo_id,
            search=search,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"[CRM] Error listando cuentas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cuentas")
async def crear_cuenta(
    data: CuentaCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Crea una nueva cuenta CRM"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.crear_cuenta(data.dict(), usuario_id)
        
        return {
            "success": True,
            "mensaje": f"Cuenta {result['codigo_cuenta']} creada exitosamente",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error creando cuenta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cuentas/{cuenta_id}")
async def obtener_cuenta(
    cuenta_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene detalle de una cuenta CRM"""
    try:
        service = _get_service()
        cuenta = service.obtener_cuenta(cuenta_id)
        
        if not cuenta:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")
        
        return cuenta
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CRM] Error obteniendo cuenta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cuentas/{cuenta_id}/ligar-cliente")
async def ligar_cliente(
    cuenta_id: str,
    data: LigarClienteRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Liga una cuenta CRM con un cliente del catálogo maestro"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.ligar_cliente(cuenta_id, data.cliente_id, usuario_id)
        
        return {
            "success": True,
            "mensaje": f"Cuenta ligada a cliente {data.cliente_id}",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error ligando cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# CLIENTES (MAESTRO)
# ============================================================

@router.get("/clientes")
async def listar_clientes(
    search: Optional[str] = None,
    activo: Optional[bool] = True,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Lista clientes del catálogo maestro"""
    try:
        service = _get_service()
        return service.listar_clientes(
            search=search,
            activo=activo,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"[CRM] Error listando clientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# SOLICITUDES ALTA CLIENTE
# ============================================================

@router.get("/clientes/solicitudes")
async def listar_solicitudes_alta(
    empresa_id: Optional[str] = None,
    estatus: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Lista solicitudes de alta de cliente"""
    try:
        service = _get_service()
        return service.listar_solicitudes_alta(
            empresa_id=empresa_id,
            estatus=estatus,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"[CRM] Error listando solicitudes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clientes/solicitudes")
async def crear_solicitud_alta(
    data: SolicitudAltaCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Crea una solicitud de alta de cliente"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.crear_solicitud_alta(data.dict(), usuario_id)
        
        return {
            "success": True,
            "mensaje": f"Solicitud {result['folio_solicitud']} creada",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error creando solicitud: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clientes/solicitudes/{solicitud_id}/enviar")
async def enviar_solicitud(
    solicitud_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Envía solicitud para revisión"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.enviar_solicitud(solicitud_id, usuario_id)
        
        return {
            "success": True,
            "mensaje": f"Solicitud {result['folio']} enviada",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error enviando solicitud: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clientes/solicitudes/{solicitud_id}/autorizar")
async def autorizar_solicitud(
    solicitud_id: str,
    data: Optional[AutorizarSolicitudRequest] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Autoriza solicitud y crea cliente en catálogo maestro"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.autorizar_solicitud(
            solicitud_id, 
            usuario_id, 
            comentarios=data.comentarios if data else None
        )
        
        return {
            "success": True,
            "mensaje": f"Solicitud aprobada. Cliente ID: {result['cliente_id']}",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error autorizando solicitud: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clientes/solicitudes/{solicitud_id}/rechazar")
async def rechazar_solicitud(
    solicitud_id: str,
    data: RechazarSolicitudRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Rechaza solicitud de alta"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.rechazar_solicitud(solicitud_id, usuario_id, data.motivo)
        
        return {
            "success": True,
            "mensaje": "Solicitud rechazada",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error rechazando solicitud: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ACTIVIDADES
# ============================================================

@router.get("/actividades")
async def listar_actividades(
    empresa_id: Optional[str] = None,
    entidad_tipo: Optional[str] = None,
    entidad_id: Optional[str] = None,
    asignado_a: Optional[str] = None,
    estatus: Optional[int] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Lista actividades con filtros"""
    try:
        service = _get_service()
        return service.listar_actividades(
            empresa_id=empresa_id,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            asignado_a=asignado_a,
            estatus=estatus,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"[CRM] Error listando actividades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actividades")
async def crear_actividad(
    data: ActividadCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Crea una actividad"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.crear_actividad(data.dict(), usuario_id)
        
        return {
            "success": True,
            "mensaje": f"Actividad '{result['titulo']}' creada",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error creando actividad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actividades/{actividad_id}/cerrar")
async def cerrar_actividad(
    actividad_id: str,
    data: Optional[CerrarActividadRequest] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Cierra una actividad"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.cerrar_actividad(
            actividad_id, 
            usuario_id,
            resultado_id=data.resultado_id if data else None,
            notas=data.notas if data else None
        )
        
        return {
            "success": True,
            "mensaje": "Actividad cerrada",
            **result
        }
    except Exception as e:
        logger.error(f"[CRM] Error cerrando actividad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# CATÁLOGOS CRM
# ============================================================

@router.get("/catalogos/tipos-actividad")
async def listar_tipos_actividad(current_user: Dict = Depends(get_current_user)):
    """Lista tipos de actividad"""
    service = _get_service()
    conn = service._get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT * FROM CRM_Cat_TiposActividad WHERE Activo = 1 ORDER BY TipoID")
        return {"tipos": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()


@router.get("/catalogos/estatus-actividad")
async def listar_estatus_actividad(current_user: Dict = Depends(get_current_user)):
    """Lista estatus de actividad"""
    service = _get_service()
    conn = service._get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT * FROM CRM_Cat_EstatusActividad WHERE Activo = 1 ORDER BY EstatusID")
        return {"estatus": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()


@router.get("/catalogos/estatus-remision")
async def listar_estatus_remision(current_user: Dict = Depends(get_current_user)):
    """Lista estatus de remisión"""
    service = _get_service()
    conn = service._get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT * FROM Venta_Cat_EstatusRemision WHERE Activo = 1 ORDER BY Orden")
        return {"estatus": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()


# ============================================================
# COTIZACIONES
# ============================================================

class CotizacionCreate(BaseModel):
    cliente_id: int
    serie: Optional[str] = "A"
    fecha_vigencia: Optional[date] = None
    cliente_direccion_id: Optional[int] = None
    lista_precio_id: Optional[int] = None
    condicion_pago_id: Optional[int] = None
    moneda_id: Optional[int] = 1
    tipo_cambio: Optional[float] = 1
    subtotal: Optional[float] = 0
    descuento_total: Optional[float] = 0
    impuesto_total: Optional[float] = 0
    total: Optional[float] = 0
    atencion_a: Optional[str] = None
    email_cliente: Optional[str] = None
    telefono_cliente: Optional[str] = None
    observaciones: Optional[str] = None
    terminos_condiciones: Optional[str] = None
    oportunidad_id: Optional[str] = None
    cuenta_id: Optional[str] = None
    lead_id: Optional[str] = None
    detalle: Optional[List[Dict]] = []


@router.get("/cotizaciones")
async def listar_cotizaciones(
    cliente_id: Optional[int] = None,
    cuenta_id: Optional[str] = None,
    estatus_id: Optional[int] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Lista cotizaciones comerciales"""
    try:
        service = _get_service()
        return service.listar_cotizaciones(
            cliente_id=cliente_id,
            cuenta_id=cuenta_id,
            estatus_id=estatus_id,
            fecha_desde=date.fromisoformat(fecha_desde) if fecha_desde else None,
            fecha_hasta=date.fromisoformat(fecha_hasta) if fecha_hasta else None,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"[CRM] Error listando cotizaciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cotizaciones/{cotizacion_id}")
async def obtener_cotizacion(
    cotizacion_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene detalle de una cotización"""
    try:
        service = _get_service()
        cot = service.obtener_cotizacion(cotizacion_id)
        if not cot:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        return cot
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CRM] Error obteniendo cotización: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cotizaciones")
async def crear_cotizacion(
    data: CotizacionCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Crea una cotización comercial"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.crear_cotizacion(data.dict(), usuario_id)
        
        return {
            "success": True,
            "mensaje": f"Cotización {result['folio_cotizacion']} creada",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error creando cotización: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cotizaciones/{cotizacion_id}/enviar")
async def enviar_cotizacion(
    cotizacion_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Envía cotización al cliente"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.enviar_cotizacion(cotizacion_id, usuario_id)
        
        return {"success": True, "mensaje": "Cotización enviada", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error enviando cotización: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cotizaciones/{cotizacion_id}/aprobar")
async def aprobar_cotizacion(
    cotizacion_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Aprueba cotización (cliente acepta)"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.aprobar_cotizacion(cotizacion_id, usuario_id)
        
        return {"success": True, "mensaje": "Cotización aprobada", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error aprobando cotización: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# PEDIDOS DE VENTA
# ============================================================

class PedidoCreate(BaseModel):
    cliente_id: int
    serie: Optional[str] = "A"
    fecha_compromiso: Optional[date] = None
    cliente_direccion_id: Optional[int] = None
    lista_precio_id: Optional[int] = None
    condicion_pago_id: Optional[int] = None
    moneda_id: Optional[int] = 1
    tipo_cambio: Optional[float] = 1
    subtotal: Optional[float] = 0
    descuento_total: Optional[float] = 0
    impuesto_total: Optional[float] = 0
    total: Optional[float] = 0
    cotizacion_id: Optional[int] = None
    atencion_a: Optional[str] = None
    observaciones: Optional[str] = None
    instrucciones_entrega: Optional[str] = None
    oportunidad_id: Optional[str] = None
    cuenta_id: Optional[str] = None
    detalle: Optional[List[Dict]] = []


@router.get("/pedidos-venta")
async def listar_pedidos(
    cliente_id: Optional[int] = None,
    cuenta_id: Optional[str] = None,
    estatus_id: Optional[int] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Lista pedidos de venta"""
    try:
        service = _get_service()
        return service.listar_pedidos(
            cliente_id=cliente_id,
            cuenta_id=cuenta_id,
            estatus_id=estatus_id,
            fecha_desde=date.fromisoformat(fecha_desde) if fecha_desde else None,
            fecha_hasta=date.fromisoformat(fecha_hasta) if fecha_hasta else None,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"[CRM] Error listando pedidos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pedidos-venta/{pedido_id}")
async def obtener_pedido(
    pedido_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene detalle de un pedido"""
    try:
        service = _get_service()
        ped = service.obtener_pedido(pedido_id)
        if not ped:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        return ped
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CRM] Error obteniendo pedido: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pedidos-venta")
async def crear_pedido(
    data: PedidoCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Crea un pedido de venta"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.crear_pedido(data.dict(), usuario_id)
        
        return {
            "success": True,
            "mensaje": f"Pedido {result['folio_pedido']} creado",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error creando pedido: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pedidos-venta/{pedido_id}/confirmar")
async def confirmar_pedido(
    pedido_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Confirma un pedido"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.confirmar_pedido(pedido_id, usuario_id)
        
        return {"success": True, "mensaje": "Pedido confirmado", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error confirmando pedido: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# REMISIONES DE VENTA
# ============================================================

class RemisionCreate(BaseModel):
    empresa_id: str
    cliente_id: int
    sucursal_id: Optional[str] = None
    almacen_id: Optional[int] = None
    pedido_id: Optional[int] = None
    cotizacion_id: Optional[int] = None
    oportunidad_id: Optional[str] = None
    cuenta_id: Optional[str] = None
    contacto_id: Optional[int] = None
    fecha_compromiso_entrega: Optional[date] = None
    direccion_entrega: Optional[str] = None
    moneda_id: Optional[int] = 1
    tipo_cambio: Optional[float] = 1
    subtotal: Optional[float] = 0
    descuento_total: Optional[float] = 0
    impuestos_total: Optional[float] = 0
    total: Optional[float] = 0
    observaciones: Optional[str] = None
    observaciones_internas: Optional[str] = None
    detalle: Optional[List[Dict]] = []


class RegistrarEntregaRequest(BaseModel):
    entregado_a: str
    recibido_por: str


@router.get("/remisiones-venta")
async def listar_remisiones(
    empresa_id: Optional[str] = None,
    cliente_id: Optional[int] = None,
    cuenta_id: Optional[str] = None,
    estatus_id: Optional[int] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Lista remisiones de venta"""
    try:
        service = _get_service()
        return service.listar_remisiones(
            empresa_id=empresa_id,
            cliente_id=cliente_id,
            cuenta_id=cuenta_id,
            estatus_id=estatus_id,
            fecha_desde=date.fromisoformat(fecha_desde) if fecha_desde else None,
            fecha_hasta=date.fromisoformat(fecha_hasta) if fecha_hasta else None,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"[CRM] Error listando remisiones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/remisiones-venta/{remision_id}")
async def obtener_remision(
    remision_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene detalle de una remisión"""
    try:
        service = _get_service()
        rem = service.obtener_remision(remision_id)
        if not rem:
            raise HTTPException(status_code=404, detail="Remisión no encontrada")
        return rem
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CRM] Error obteniendo remisión: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remisiones-venta")
async def crear_remision(
    data: RemisionCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Crea una remisión de venta"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.crear_remision(data.dict(), usuario_id)
        
        return {
            "success": True,
            "mensaje": f"Remisión {result['folio_remision']} creada",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error creando remisión: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remisiones-venta/{remision_id}/entregar")
async def registrar_entrega(
    remision_id: int,
    data: RegistrarEntregaRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Registra entrega de una remisión"""
    try:
        service = _get_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.registrar_entrega(
            remision_id, usuario_id, data.entregado_a, data.recibido_por
        )
        
        return {"success": True, "mensaje": "Entrega registrada", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error registrando entrega: {e}")
        raise HTTPException(status_code=500, detail=str(e))
