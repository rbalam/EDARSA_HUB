"""
EDARSA HUB - Compras Routes
===========================
Endpoints del módulo de compras.

Endpoints a migrar desde server.py:
- GET /api/compras/pedidos-vigentes/{server_id}
- GET /api/compras/requisiciones/{server_id}
- GET /api/compras/inventarios/{server_id}
- GET /api/compras/facturas-proveedor/{server_id}
"""

from fastapi import APIRouter

router = APIRouter(prefix="/compras", tags=["Compras"])
