"""
EDARSA HUB - Compras Module Routes
==================================
Endpoints del módulo de compras.

FASE 4 DEL REFACTOR MODULAR (Diciembre 2025):
- Endpoints simples migrados: inventarios-fisicos, pedidos-vigentes, parametros, detalle-factura, facturas-proveedor
- Endpoints complejos permanecen temporalmente en server.py

ENDPOINTS MIGRADOS:
- GET /compras/inventarios-fisicos/{server_id}
- GET /compras/pedidos-vigentes/{server_id}
- GET /compras/parametros/{server_id}
- POST /compras/parametros
- GET /compras/detalle-factura/{server_id}/{folio}
- GET /compras/facturas-proveedor/{server_id}

ENDPOINTS PENDIENTES (en server.py por complejidad):
- POST /compras/calculo-pedido
- POST /compras/auditoria-operativa
- POST /compras/productos-para-captura
- GET /compras/dashboard/{server_id}
- POST /compras/analisis
- GET /compras/detalle-pedido/{server_id}/{folio}
- GET /compras/detalle-pedido-manual/{server_id}
- GET /compras/detalle-movimientos/{server_id}
- GET /compras/detalle-consumos/{server_id}
- POST /compras/detalle-movimientos
- POST /compras/detalle-consumos
"""

from typing import Dict
from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials

from core.security import security, verify_token, get_current_user
from modules.compras import service
from modules.compras.schemas import ParametrosCompra

# Router sin prefix - se agregará en server.py como /api
router = APIRouter(tags=["compras"])


# ============================================================================
# INVENTARIOS FÍSICOS
# ============================================================================

@router.get("/compras/inventarios-fisicos/{server_id}")
async def obtener_inventarios_fisicos(
    server_id: str,
    sucursal: str = None,
    sucursal_id: str = None,
    almacen: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene la lista de inventarios físicos disponibles."""
    verify_token(credentials.credentials)
    return await service.obtener_inventarios_fisicos(server_id, sucursal, sucursal_id, almacen)


# ============================================================================
# PEDIDOS VIGENTES
# ============================================================================

@router.get("/compras/pedidos-vigentes/{server_id}")
async def obtener_pedidos_vigentes(
    server_id: str,
    sucursal_id: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene pedidos/requisiciones vigentes."""
    verify_token(credentials.credentials)
    return await service.obtener_pedidos_vigentes(server_id, sucursal_id)


# ============================================================================
# PARÁMETROS DE COMPRAS
# ============================================================================

@router.get("/compras/parametros/{server_id}")
async def obtener_parametros(
    server_id: str,
    sucursal: str = Query(default=""),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene los parámetros de compras para un servidor/sucursal."""
    verify_token(credentials.credentials)
    return await service.obtener_parametros(server_id, sucursal)


@router.post("/compras/parametros")
async def guardar_parametros(
    params: Dict,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Guarda los parámetros de compras."""
    verify_token(credentials.credentials)
    server_id = params.get("server_id", "")
    sucursal = params.get("sucursal", "")
    return await service.guardar_parametros(server_id, sucursal, params)


# ============================================================================
# DETALLE DE FACTURA
# ============================================================================

@router.get("/compras/detalle-factura/{server_id}/{folio}")
async def obtener_detalle_factura(
    server_id: str,
    folio: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene el detalle de productos de una factura/entrada."""
    verify_token(credentials.credentials)
    return await service.obtener_detalle_factura(server_id, folio)


# ============================================================================
# FACTURAS DE PROVEEDOR
# ============================================================================

@router.get("/compras/facturas-proveedor/{server_id}")
async def obtener_facturas_proveedor(
    server_id: str,
    sucursal: str = Query(default=""),
    meses: str = Query(default=""),
    anio: str = Query(default=""),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene facturas de proveedores."""
    verify_token(credentials.credentials)
    return await service.obtener_facturas_proveedor(server_id, sucursal, meses, anio)


__all__ = ['router']
