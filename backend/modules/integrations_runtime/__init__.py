"""Runtime universal de integraciones EDARSAHUB.

Gate 5C: helpers comunes para health persistido y contexto universal de sync.
No crea tablas ni reemplaza registry/resolvers/RBAC.
"""

from .external_ids import ExternalIdentifierConflict, ensure_external_identifier
from .health import persist_connection_health
from .sucursal_scope import SucursalScopeConflict, ensure_sucursal_server_mapping
from .scope_materializer import (
    MaterializedSucursalScope,
    materialize_external_sucursal_scope_atomic,
)
from .sync_ledger import enrich_sync_start, mark_sync_finished

__all__ = [
    "ExternalIdentifierConflict",
    "ensure_external_identifier",
    "SucursalScopeConflict",
    "ensure_sucursal_server_mapping",
    "MaterializedSucursalScope",
    "materialize_external_sucursal_scope_atomic",
    "persist_connection_health",
    "enrich_sync_start",
    "mark_sync_finished",
]
