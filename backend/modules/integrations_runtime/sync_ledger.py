from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID


def _valid_uuid(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


def _idempotency_key(sync_type: str, sync_run_id: str) -> str:
    return f"{sync_type}:{sync_run_id}"[:200]


def enrich_sync_start(
    cursor,
    *,
    sync_run_id: str,
    sync_type: str,
    server_id: Optional[str] = None,
    unidad_negocio_id: Optional[str] = None,
    codigo_sync: Optional[str] = None,
    started_at_utc: Optional[datetime] = None,
) -> None:
    """Enriquece una fila existente de Sync_Control_Ejecuciones.

    No inventa contexto: ConexionID/Unidad/CodigoSync solo se escriben cuando
    el valor existe en su fuente canonica. Siempre agrega UTC + idempotencia.
    """
    started = started_at_utc or datetime.now(timezone.utc)
    started_sql = started.astimezone(timezone.utc).replace(tzinfo=None)

    connection_id = _valid_uuid(server_id)
    if connection_id:
        cursor.execute(
            "SELECT TOP 1 id FROM dbo.Servidores_Conexiones WHERE id=%s",
            (connection_id,),
        )
        if not cursor.fetchone():
            connection_id = None

    unit_id = _valid_uuid(unidad_negocio_id)
    if unit_id:
        cursor.execute(
            "SELECT TOP 1 id FROM dbo.Unidades_Negocio WHERE id=%s",
            (unit_id,),
        )
        if not cursor.fetchone():
            unit_id = None

    sync_code = str(codigo_sync)[:100] if codigo_sync else None
    if sync_code:
        cursor.execute(
            "SELECT TOP 1 Codigo FROM dbo.Sistema_Sync_Catalogo WHERE Codigo=%s AND Activo=1",
            (sync_code,),
        )
        if not cursor.fetchone():
            sync_code = None

    cursor.execute(
        """
        UPDATE dbo.Sync_Control_Ejecuciones
        SET ConexionID=COALESCE(%s, ConexionID),
            UnidadNegocioID=COALESCE(%s, UnidadNegocioID),
            CodigoSync=COALESCE(%s, CodigoSync),
            StartedAtUTC=COALESCE(StartedAtUTC, %s),
            IdempotencyKey=COALESCE(IdempotencyKey, %s)
        WHERE SyncRunID=%s
        """,
        (
            connection_id,
            unit_id,
            sync_code,
            started_sql,
            _idempotency_key(sync_type, sync_run_id),
            sync_run_id,
        ),
    )


def mark_sync_finished(
    cursor,
    sync_run_id: str,
    *,
    finished_at_utc: Optional[datetime] = None,
) -> None:
    finished = finished_at_utc or datetime.now(timezone.utc)
    cursor.execute(
        """
        UPDATE dbo.Sync_Control_Ejecuciones
        SET FinishedAtUTC=COALESCE(FinishedAtUTC, %s)
        WHERE SyncRunID=%s
        """,
        (finished.astimezone(timezone.utc).replace(tzinfo=None), sync_run_id),
    )
