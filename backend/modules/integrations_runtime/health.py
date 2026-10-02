from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from core.sql_first.connection_factory import get_edarsahub_pymssql_connection


def _uuid_text(value: str) -> str:
    return str(UUID(str(value)))


def persist_connection_health(
    connection_id: str,
    *,
    success: bool,
    latency_ms: Optional[int] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    checked_at_utc: Optional[datetime] = None,
) -> None:
    """Persiste el ultimo estado real de una conexion canonica.

    Reusa dbo.Servidores_ConexionEstado. No crea un log paralelo.
    Una prueba ad-hoc sin ConexionID canonico no debe llamar este helper.
    """
    connection_id = _uuid_text(connection_id)
    checked = checked_at_utc or datetime.now(timezone.utc)
    checked_sql = checked.astimezone(timezone.utc).replace(tzinfo=None)
    latency = int(latency_ms) if latency_ms is not None else None
    code = (str(error_code)[:80] if error_code else None)
    message = (str(error_message)[:1000] if error_message else None)
    status = "CONNECTED" if success else "ERROR"
    legacy_mongo_id = f"SQLHEALTH:{connection_id}"

    conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=10)
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("SET XACT_ABORT ON")
        cur.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        cur.execute("BEGIN TRANSACTION")
        cur.execute(
            """
            SELECT TOP (1) Id
            FROM dbo.Servidores_ConexionEstado WITH (UPDLOCK, HOLDLOCK)
            WHERE ServidorID = %s OR ServerID = %s OR MongoId = %s
            ORDER BY COALESCE(FechaActualizacionUTC, UltimaPruebaUTC, UltimoCheck, FechaCreacion) DESC
            """,
            (connection_id, connection_id, legacy_mongo_id),
        )
        row = cur.fetchone()

        if row:
            if success:
                cur.execute(
                    """
                    UPDATE dbo.Servidores_ConexionEstado
                    SET ServidorID=%s, ServerID=%s, EstadoConexion=%s,
                        UltimoCheck=GETDATE(), ResponseTimeMs=%s, LatenciaMs=%s,
                        UltimaPruebaUTC=%s, UltimoExitoUTC=%s,
                        UltimoErrorCodigo=NULL, UltimoErrorMensaje=NULL,
                        FechaActualizacionUTC=%s, Activo=1
                    WHERE Id=%s
                    """,
                    (
                        connection_id, connection_id, status, latency, latency,
                        checked_sql, checked_sql, checked_sql, row["Id"],
                    ),
                )
            else:
                cur.execute(
                    """
                    UPDATE dbo.Servidores_ConexionEstado
                    SET ServidorID=%s, ServerID=%s, EstadoConexion=%s,
                        UltimoCheck=GETDATE(), ResponseTimeMs=%s, LatenciaMs=%s,
                        UltimaPruebaUTC=%s, UltimoErrorUTC=%s,
                        UltimoErrorCodigo=%s, UltimoErrorMensaje=%s,
                        FechaActualizacionUTC=%s, Activo=1
                    WHERE Id=%s
                    """,
                    (
                        connection_id, connection_id, status, latency, latency,
                        checked_sql, checked_sql, code, message, checked_sql, row["Id"],
                    ),
                )
        else:
            cur.execute(
                """
                INSERT INTO dbo.Servidores_ConexionEstado (
                    ServidorID, ServerID, EstadoConexion, UltimoCheck,
                    ResponseTimeMs, MongoId, ColeccionOrigen, MigradoDesdeMongo,
                    Activo, FechaCreacion, UltimaPruebaUTC, UltimoExitoUTC,
                    UltimoErrorUTC, UltimoErrorCodigo, UltimoErrorMensaje,
                    LatenciaMs, FechaActualizacionUTC
                ) VALUES (
                    %s,%s,%s,GETDATE(),%s,%s,'SQL_CANONICAL_HEALTH',0,
                    1,GETDATE(),%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    connection_id,
                    connection_id,
                    status,
                    latency,
                    legacy_mongo_id,
                    checked_sql,
                    checked_sql if success else None,
                    None if success else checked_sql,
                    None if success else code,
                    None if success else message,
                    latency,
                    checked_sql,
                ),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
