from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .external_ids import ensure_external_identifier
from .sucursal_scope import ensure_sucursal_server_mapping


@dataclass(frozen=True)
class MaterializedSucursalScope:
    external_identifier_id: int
    mapping_id: int


def materialize_external_sucursal_scope_atomic(
    connection,
    *,
    sistema_tipo_id: int,
    tipo_identificador: str,
    valor_externo: str,
    servidor_id: str,
    sucursal_id: int,
    sucursal_origen_id: str,
    unidad_negocio_id: Optional[str] = None,
    sistema_version_id: Optional[str] = None,
    created_by: Optional[str] = None,
) -> MaterializedSucursalScope:
    """Materializa identidad externa y mapping de sucursal atomicamente.

    La conexion EDARSAHUB debe ser provista por el caller mediante el helper
    canonico correspondiente y con capacidad de escritura autorizada.

    Este orquestador no abre conexiones, no consulta sistemas externos y no
    contiene SQL propio. Ambos writers usan el mismo cursor/transaccion.
    """
    if connection is None:
        raise ValueError("Conexion EDARSAHUB requerida")

    cursor = connection.cursor()
    try:
        external_identifier_id = ensure_external_identifier(
            cursor,
            sistema_tipo_id=sistema_tipo_id,
            tipo_identificador=tipo_identificador,
            valor_externo=valor_externo,
            unidad_negocio_id=unidad_negocio_id,
            sistema_version_id=sistema_version_id,
            conexion_id=servidor_id,
        )

        mapping_id = ensure_sucursal_server_mapping(
            cursor,
            servidor_id=servidor_id,
            sucursal_id=sucursal_id,
            sucursal_origen_id=sucursal_origen_id,
            created_by=created_by,
        )

        connection.commit()

        return MaterializedSucursalScope(
            external_identifier_id=int(external_identifier_id),
            mapping_id=int(mapping_id),
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        close = getattr(cursor, "close", None)
        if callable(close):
            close()
