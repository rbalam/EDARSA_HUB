"""Centro administrativo unificado de Conexiones y Comunicaciones.

Gate 5B: fachada de lectura que compone fuentes canonicas existentes.
No reemplaza Servidores_Conexiones, server_registry, resolvers ni RBAC.

Importar submodulos puros de integrations_center no debe montar routers ni
cargar dependencias de runtime. El router se resuelve de forma lazy para
preservar compatibilidad con from modules.integrations_center import router.
"""

from __future__ import annotations

from typing import Any

__all__ = ["router"]


def __getattr__(name: str) -> Any:
    if name == "router":
        from .routes import router as integrations_center_router

        return integrations_center_router
    raise AttributeError(name)
