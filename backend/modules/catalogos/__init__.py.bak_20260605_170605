from typing import Any
"""
EDARSA HUB - Módulo de Catálogos
================================
Módulo maestro centralizado para gestión de catálogos del sistema.

ARQUITECTURA:
- Catálogos NO duplicados por módulo
- Fuente única de verdad en EDARSA HUB (SQL Server)
- Acceso central desde menú Catálogos
- Acceso contextual desde módulos nativos (RH, Compras, etc.)

DOMINIOS:
- Generales (Empresas, Sucursales, Bancos, etc.)
- RH (Tipos contrato, Motivos baja, etc.)
- Nómina (Conceptos, Tipos periodo, etc.)
- Compras (Estatus órdenes, recepciones, etc.)
- Inventarios (Tipos movimiento, etc.)
- Activos (Tipos activo, ubicaciones, etc.)
- Finanzas (Cuentas bancarias, etc.)
- Seguridad (Roles, Módulos, etc.)
- Homologación (Equivalencias, etc.)

Diciembre 2025
"""


# Referencia global a MongoDB (para logging/auditoría)
_db: Any = None


def init_catalogos_module(db: Any):
    """Inicializa el módulo de catálogos con la conexión a MongoDB."""
    global _db
    _db = db


def get_db() -> Any:
    """Obtiene la conexión a MongoDB."""
    if _db is None:
        raise RuntimeError("Módulo de catálogos no inicializado. Llama a init_catalogos_module() primero.")
    return _db


def get_router():
    """Lazy import del router para evitar circular imports."""
    from modules.catalogos.routes import router
    return router


__all__ = ['get_router', 'init_catalogos_module', 'get_db']
