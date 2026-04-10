"""
EDARSA HUB - Compras Module
===========================
Módulo de compras, pedidos e inventarios.

FASE 4 DEL REFACTOR MODULAR (Diciembre 2025)

Componentes:
- routes.py: Endpoints FastAPI (6 migrados, 11 pendientes en server.py)
- schemas.py: Modelos Pydantic
- service.py: Lógica de negocio
- repository.py: Acceso a MongoDB y SQL Server

Inicialización:
    from modules.compras import init_compras_module
    init_compras_module(db)

NOTA: Los endpoints complejos (calculo-pedido, auditoria-operativa, dashboard)
permanecen en server.py por su complejidad y dependencias cruzadas.
"""

from modules.compras.routes import router
from modules.compras.repository import init_compras_repository
from modules.compras.schemas import (
    ParametrosCompra,
    CalculoPedidoRequest,
    AuditoriaOperativaRequest,
    ProductosParaCapturaRequest,
    DetalleMovimientosRequest,
    DetalleConsumosRequest,
    AnalisisComprasRequest,
)


def init_compras_module(database) -> None:
    """
    Inicializa el módulo de compras con la conexión a MongoDB.
    
    Args:
        database: Instancia de AsyncIOMotorDatabase
    """
    init_compras_repository(database)


__all__ = [
    'router',
    'init_compras_module',
    # Schemas re-exportados para compatibilidad con server.py
    'ParametrosCompra',
    'CalculoPedidoRequest',
    'AuditoriaOperativaRequest',
    'ProductosParaCapturaRequest',
    'DetalleMovimientosRequest',
    'DetalleConsumosRequest',
    'AnalisisComprasRequest',
]
