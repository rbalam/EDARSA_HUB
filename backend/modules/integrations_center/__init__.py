"""Centro administrativo unificado de Conexiones y Comunicaciones.

Gate 5B: fachada de lectura que compone fuentes canonicas existentes.
No reemplaza Servidores_Conexiones, server_registry, resolvers ni RBAC.
"""

from .routes import router

__all__ = ["router"]
