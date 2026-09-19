"""Runtime universal de integraciones EDARSAHUB.

Gate 5C: helpers comunes para health persistido y contexto universal de sync.
No crea tablas ni reemplaza registry/resolvers/RBAC.
"""

from .health import persist_connection_health
from .sync_ledger import enrich_sync_start, mark_sync_finished

__all__ = ["persist_connection_health", "enrich_sync_start", "mark_sync_finished"]
