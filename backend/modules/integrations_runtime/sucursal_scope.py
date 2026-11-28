from __future__ import annotations

from uuid import UUID


class SucursalScopeConflict(ValueError):
    """El scope externo entra en conflicto con un mapping canonico existente."""


def _canonical_uuid(value: str, field_name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"{field_name} invalido") from exc


def _canonical_origin_id(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized or len(normalized) > 100:
        raise ValueError("SucursalOrigenID invalido")
    return normalized


def _require_server(cursor, servidor_id: str) -> None:
    cursor.execute(
        "SELECT TOP 1 id FROM dbo.Servidores_Conexiones WHERE id=%s",
        (servidor_id,),
    )
    if not cursor.fetchone():
        raise ValueError("ServidorID no existe en Servidores_Conexiones")


def _require_sucursal(cursor, sucursal_id: int) -> None:
    cursor.execute(
        "SELECT TOP 1 SucursalID FROM dbo.Sistema_Sucursales WHERE SucursalID=%s",
        (sucursal_id,),
    )
    if not cursor.fetchone():
        raise ValueError("SucursalID no existe en Sistema_Sucursales")


def ensure_sucursal_server_mapping(
    cursor,
    *,
    servidor_id: str,
    sucursal_id: int,
    sucursal_origen_id: str,
    created_by: str | None = None,
) -> int:
    """Materializa un mapping servidor/sucursal de forma idempotente.

    El caller controla la transaccion y es responsable de commit/rollback.
    HOLDLOCK aplica semantica SERIALIZABLE al acceso de la tabla durante
    esta transaccion; UPDLOCK evita carreras entre lectores que pretenden
    materializar la misma clave logica.
    """
    server_id = _canonical_uuid(servidor_id, "ServidorID")
    try:
        branch_id = int(sucursal_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("SucursalID invalido") from exc
    if branch_id <= 0:
        raise ValueError("SucursalID invalido")

    origin_id = _canonical_origin_id(sucursal_origen_id)
    actor = str(created_by).strip()[:100] if created_by else None

    _require_server(cursor, server_id)
    _require_sucursal(cursor, branch_id)

    cursor.execute(
        """
        SELECT MapeoID, SucursalID, Activo
        FROM dbo.Sistema_SucursalServidorMapeo WITH (UPDLOCK, HOLDLOCK)
        WHERE ServidorID=%s
          AND SucursalOrigenID=%s
        ORDER BY MapeoID
        """,
        (server_id, origin_id),
    )
    by_origin = cursor.fetchall()

    if len(by_origin) > 1:
        raise SucursalScopeConflict(
            "Duplicidad preexistente para ServidorID + SucursalOrigenID"
        )
    if by_origin:
        mapping_id, existing_branch_id, active = by_origin[0]
        if int(existing_branch_id) != branch_id:
            raise SucursalScopeConflict(
                "SucursalOrigenID ya pertenece a otra SucursalID"
            )
        if not bool(active):
            raise SucursalScopeConflict(
                "Mapping canonico existente esta inactivo"
            )
        return int(mapping_id)

    cursor.execute(
        """
        SELECT MapeoID, SucursalOrigenID, Activo
        FROM dbo.Sistema_SucursalServidorMapeo WITH (UPDLOCK, HOLDLOCK)
        WHERE ServidorID=%s
          AND SucursalID=%s
        ORDER BY MapeoID
        """,
        (server_id, branch_id),
    )
    by_branch = cursor.fetchall()

    if len(by_branch) > 1:
        raise SucursalScopeConflict(
            "Duplicidad preexistente para ServidorID + SucursalID"
        )
    if by_branch:
        mapping_id, existing_origin_id, active = by_branch[0]
        if str(existing_origin_id or "").strip() != origin_id:
            raise SucursalScopeConflict(
                "SucursalID ya pertenece a otro SucursalOrigenID en este servidor"
            )
        if not bool(active):
            raise SucursalScopeConflict(
                "Mapping canonico existente esta inactivo"
            )
        return int(mapping_id)

    cursor.execute(
        """
        INSERT INTO dbo.Sistema_SucursalServidorMapeo (
            SucursalID,
            ServidorID,
            SucursalOrigenID,
            Activo,
            FechaCreacion,
            CreatedBy
        )
        OUTPUT INSERTED.MapeoID
        VALUES (%s,%s,%s,1,SYSUTCDATETIME(),%s)
        """,
        (branch_id, server_id, origin_id, actor),
    )
    inserted = cursor.fetchone()
    if not inserted:
        raise RuntimeError("No se pudo materializar mapping de sucursal")
    return int(inserted[0])
