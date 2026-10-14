from __future__ import annotations

from typing import Optional
from uuid import UUID


class ExternalIdentifierConflict(ValueError):
    """Indica que un identificador externo ya pertenece a otro scope canonico."""


def _uuid(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("UUID canonico invalido") from exc


def _normalized_scope(
    *,
    unidad_negocio_id: Optional[str],
    sistema_version_id: Optional[str],
    conexion_id: Optional[str],
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    return (
        _uuid(unidad_negocio_id),
        _uuid(sistema_version_id),
        _uuid(conexion_id),
    )


def ensure_external_identifier(
    cursor,
    *,
    sistema_tipo_id: int,
    tipo_identificador: str,
    valor_externo: str,
    unidad_negocio_id: Optional[str] = None,
    sistema_version_id: Optional[str] = None,
    conexion_id: Optional[str] = None,
) -> int:
    """Materializa un identificador externo de forma idempotente y fail-closed.

    El caller controla la transaccion. Este helper no hace commit/rollback.
    La unicidad canonica esta definida por:
    SistemaTipoID + TipoIdentificador + ValorExterno.
    """
    tipo = str(tipo_identificador or "").strip()
    valor = str(valor_externo or "").strip()

    if not tipo or len(tipo) > 80:
        raise ValueError("TipoIdentificador invalido")
    if not valor or len(valor) > 300:
        raise ValueError("ValorExterno invalido")

    unidad, version, conexion = _normalized_scope(
        unidad_negocio_id=unidad_negocio_id,
        sistema_version_id=sistema_version_id,
        conexion_id=conexion_id,
    )

    cursor.execute(
        """
        SELECT
            IdentificadorExternoID,
            UnidadNegocioID,
            SistemaVersionID,
            ConexionID
        FROM dbo.Sistema_IdentificadoresExternos
            WITH (UPDLOCK, HOLDLOCK)
        WHERE SistemaTipoID=%s
          AND TipoIdentificador=%s
          AND ValorExterno=%s
        """,
        (int(sistema_tipo_id), tipo, valor),
    )
    row = cursor.fetchone()

    if row:
        existing = tuple(
            str(value).lower() if value is not None else None
            for value in row[1:4]
        )
        requested = tuple(
            value.lower() if value is not None else None
            for value in (unidad, version, conexion)
        )
        if existing != requested:
            raise ExternalIdentifierConflict(
                "Identificador externo ya ligado a otro scope canonico"
            )
        return int(row[0])

    cursor.execute(
        """
        INSERT INTO dbo.Sistema_IdentificadoresExternos (
            UnidadNegocioID,
            SistemaTipoID,
            SistemaVersionID,
            ConexionID,
            TipoIdentificador,
            ValorExterno,
            Activo,
            FechaAlta
        )
        OUTPUT INSERTED.IdentificadorExternoID
        VALUES (%s,%s,%s,%s,%s,%s,1,SYSUTCDATETIME())
        """,
        (
            unidad,
            int(sistema_tipo_id),
            version,
            conexion,
            tipo,
            valor,
        ),
    )
    inserted = cursor.fetchone()
    if not inserted:
        raise RuntimeError("No se pudo materializar identificador externo")
    return int(inserted[0])
