"""
EDARSA HUB - Routes de Automatización Operativa de Compras
==========================================================
Endpoints para el flujo: Pedido → Gerencia → Tesorería → Aprobado
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
    pedido_id: str
    server_id: str
    sucursal_id: str
    sucursal_nombre: str
    almacen_id: str
    almacen_nombre: str
    productos: List[Dict]
    dias_objetivo: Optional[int] = 10
    origen_sistema: Optional[str] = "MPRO"


class AccionGerenciaRequest(BaseModel):
    """Acciones: aprobar, rechazar, ajuste"""
    accion: str  # "aprobar", "rechazar", "ajuste"
    comentario: Optional[str] = ""
    dias_objetivo: Optional[int] = None  # Solo para ajuste


class AccionTesoreriaRequest(BaseModel):
    """Acciones: aprobar, rechazar"""
    accion: str  # "aprobar", "rechazar"
    comentario: Optional[str] = ""


class ModificarDiasObjetivoRequest(BaseModel):
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
    """KPIs de automatizaciones operativas."""
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
    """Lista automatizaciones."""
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
        raise HTTPException(status_code=404, detail="No encontrada")
    
    return registro


@router.post("/compras/procesar")
async def procesar_pedido(
    request: ProcesarPedidoRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Procesa pedido capturado.
    Inicia flujo: Detección → Auditoría → EN_REVISION_GERENCIA
    """
    payload = verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    resultado = service.procesar_pedido_operativo(
        pedido_id=request.pedido_id,
        server_id=request.server_id,
        sucursal_id=request.sucursal_id,
        sucursal_nombre=request.sucursal_nombre,
        almacen_id=request.almacen_id,
        almacen_nombre=request.almacen_nombre,
        usuario_id=payload.get("user_id", ""),
        usuario_nombre=payload.get("email", ""),
        productos=request.productos,
        dias_objetivo=request.dias_objetivo,
        origen_sistema=request.origen_sistema or "MPRO"
    )
    
    return resultado


# ============================================================================
# FLUJO AUTORIZACIÓN GERENCIA
# ============================================================================

@router.post("/compras/{automatizacion_id}/gerencia")
async def autorizar_gerencia(
    automatizacion_id: str,
    request: AccionGerenciaRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Autorización de Gerencia.
    - aprobar → PENDIENTE_TESORERIA
    - rechazar → RECHAZADO
    - ajuste → recalcula y mantiene EN_REVISION_GERENCIA
    """
    payload = verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    # Obtener rol
    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
    usuario_rol = user.get("role", "") if user else ""
    
    resultado = service.autorizar_gerencia(
        automatizacion_id=automatizacion_id,
        usuario_id=payload.get("user_id", ""),
        usuario_rol=usuario_rol,
        accion=request.accion,
        comentario=request.comentario or "",
        nuevo_dias_objetivo=request.dias_objetivo
    )
    
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error"))
    
    return resultado


# ============================================================================
# FLUJO AUTORIZACIÓN TESORERÍA
# ============================================================================

@router.post("/compras/{automatizacion_id}/tesoreria")
async def autorizar_tesoreria(
    automatizacion_id: str,
    request: AccionTesoreriaRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Autorización Final de Tesorería.
    - aprobar → APROBADO
    - rechazar → RECHAZADO
    """
    payload = verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    # Obtener rol
    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
    usuario_rol = user.get("role", "") if user else ""
    
    resultado = service.autorizar_tesoreria(
        automatizacion_id=automatizacion_id,
        usuario_id=payload.get("user_id", ""),
        usuario_rol=usuario_rol,
        accion=request.accion,
        comentario=request.comentario or ""
    )
    
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error"))
    
    return resultado


# ============================================================================
# MODIFICAR DÍAS OBJETIVO
# ============================================================================

@router.post("/compras/{automatizacion_id}/dias-objetivo")
async def modificar_dias_objetivo(
    automatizacion_id: str,
    request: ModificarDiasObjetivoRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Modifica días objetivo y recalcula.
    Solo Gerencia/Director/Administrador.
    """
    payload = verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
    usuario_rol = user.get("role", "") if user else ""
    
    resultado = service.modificar_dias_objetivo(
        automatizacion_id=automatizacion_id,
        nuevo_dias_objetivo=request.dias_objetivo,
        usuario_id=payload.get("user_id", ""),
        usuario_rol=usuario_rol,
        motivo=request.motivo or ""
    )
    
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error"))
    
    return resultado


# ============================================================================
# BITÁCORA
# ============================================================================

@router.get("/compras/{automatizacion_id}/bitacora")
async def obtener_bitacora(
    automatizacion_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene bitácora de cambios."""
    verify_token(credentials.credentials)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    return service.obtener_bitacora(automatizacion_id)
