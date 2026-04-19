"""
EDARSA HUB - Routes de Automatización Operativa de Compras
==========================================================
Endpoints para el módulo de automatizaciones operativas.
"""

from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from core.security import security, verify_token
from ..db_utils import get_database
from modules.fase2_operativo.services.automatizacion_compras_service import (
    get_automatizacion_compras_service,
    EstadoAutomatizacion,
)

router = APIRouter(prefix="/automatizaciones/operativas", tags=["automatizaciones-operativas"])


# ============================================================================
# SCHEMAS
# ============================================================================

class ProcesarPedidoRequest(BaseModel):
    """Request para procesar pedido operativo."""
    pedido_id: str
    server_id: str
    sucursal_id: str
    sucursal_nombre: str
    almacen_id: str
    almacen_nombre: str
    productos: List[Dict]
    dias_objetivo: Optional[int] = 10


class AccionRevisionRequest(BaseModel):
    """Request para acciones de revisión."""
    tipo_revision: Optional[str] = None  # "gerencia" o "tesoreria"
    comentario: Optional[str] = ""
    motivo: Optional[str] = ""


class ModificarDiasObjetivoRequest(BaseModel):
    """Request para modificar días objetivo."""
    dias_objetivo: int
    motivo: Optional[str] = ""


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/compras/kpis")
async def obtener_kpis(
    server_id: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene KPIs de automatizaciones operativas de compras."""
    verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    return service.obtener_kpis(server_id)


@router.get("/compras")
async def listar_automatizaciones(
    server_id: Optional[str] = Query(None),
    sucursal_id: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    limite: int = Query(50, le=200),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Lista automatizaciones operativas de compras."""
    verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    return service.listar_automatizaciones(server_id, sucursal_id, estado, limite)


@router.get("/compras/{automatizacion_id}")
async def obtener_automatizacion(
    automatizacion_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene detalle de una automatización."""
    verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    registro = service.obtener_automatizacion(automatizacion_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    
    return registro


@router.post("/compras/procesar")
async def procesar_pedido(
    request: ProcesarPedidoRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Procesa un pedido/requisición capturado.
    Inicia el flujo de automatización operativa.
    """
    payload = verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    resultado = await service.procesar_pedido_operativo(
        pedido_id=request.pedido_id,
        server_id=request.server_id,
        sucursal_id=request.sucursal_id,
        sucursal_nombre=request.sucursal_nombre,
        almacen_id=request.almacen_id,
        almacen_nombre=request.almacen_nombre,
        usuario_id=payload.get("user_id", ""),
        usuario_nombre=payload.get("email", ""),
        productos=request.productos,
        dias_objetivo=request.dias_objetivo
    )
    
    return resultado


@router.post("/compras/{automatizacion_id}/enviar-revision")
async def enviar_a_revision(
    automatizacion_id: str,
    request: AccionRevisionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Envía automatización a revisión (gerencia o tesorería)."""
    payload = verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    if not request.tipo_revision:
        raise HTTPException(status_code=400, detail="tipo_revision requerido")
    
    resultado = await service.enviar_a_revision(
        automatizacion_id=automatizacion_id,
        tipo_revision=request.tipo_revision,
        usuario_id=payload.get("user_id", "")
    )
    
    if not resultado.get("success"):
        raise HTTPException(status_code=404, detail=resultado.get("error"))
    
    return resultado


@router.post("/compras/{automatizacion_id}/aprobar")
async def aprobar_automatizacion(
    automatizacion_id: str,
    request: AccionRevisionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Aprueba una automatización."""
    payload = verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    resultado = await service.aprobar(
        automatizacion_id=automatizacion_id,
        usuario_id=payload.get("user_id", ""),
        comentario=request.comentario or ""
    )
    
    if not resultado.get("success"):
        raise HTTPException(status_code=404, detail=resultado.get("error"))
    
    return resultado


@router.post("/compras/{automatizacion_id}/rechazar")
async def rechazar_automatizacion(
    automatizacion_id: str,
    request: AccionRevisionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Rechaza una automatización."""
    payload = verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    if not request.motivo:
        raise HTTPException(status_code=400, detail="motivo requerido")
    
    resultado = await service.rechazar(
        automatizacion_id=automatizacion_id,
        usuario_id=payload.get("user_id", ""),
        motivo=request.motivo
    )
    
    if not resultado.get("success"):
        raise HTTPException(status_code=404, detail=resultado.get("error"))
    
    return resultado


@router.post("/compras/{automatizacion_id}/dias-objetivo")
async def modificar_dias_objetivo(
    automatizacion_id: str,
    request: ModificarDiasObjetivoRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Modifica días objetivo y recalcula automáticamente.
    Solo Gerencia/Director/Administrador.
    """
    payload = verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    # Obtener rol del usuario
    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
    usuario_rol = user.get("role", "") if user else ""
    
    resultado = await service.modificar_dias_objetivo(
        automatizacion_id=automatizacion_id,
        nuevo_dias_objetivo=request.dias_objetivo,
        usuario_id=payload.get("user_id", ""),
        usuario_rol=usuario_rol,
        motivo=request.motivo or ""
    )
    
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error"))
    
    return resultado


@router.get("/compras/{automatizacion_id}/bitacora")
async def obtener_bitacora(
    automatizacion_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene bitácora de cambios de una automatización."""
    verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    return service.obtener_bitacora(automatizacion_id)

