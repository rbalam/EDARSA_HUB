"""
EDARSA HUB - Job Execution Logger
=================================
SQL-only logger para ejecuciones de jobs.
Fuente canónica: dbo.Scheduler_BitacoraJobs.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
import logging
import uuid
import json

logger = logging.getLogger(__name__)


class JobExecutionLog(BaseModel):
    """Registro de una ejecución de job."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_name: str
    run_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: str
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    status: str = "running"
    processed_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    message: Optional[str] = None
    error_detail: Optional[str] = None
    metadata: Dict[str, Any] = {}

    class Config:
        extra = "allow"


class JobLogger:
    """
    Logger SQL-only de ejecuciones de jobs.
    No usa almacén legacy ni fallback.
    """

    def __init__(self):
        logger.info("[JOB_LOGGER] Inicializado SQL-only → dbo.Scheduler_BitacoraJobs")

    def _insert_bitacora(
        self,
        job_name: str,
        run_id: str,
        accion: str,
        detalles: Optional[Dict[str, Any]] = None,
        exito: Optional[bool] = None,
        mensaje_error: Optional[str] = None,
        server_id: Optional[str] = None,
    ) -> None:
        """Inserta evento en Scheduler_BitacoraJobs."""
        from core.sql_first.db import get_sql_connection

        conn = None
        try:
            conn = get_sql_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO dbo.Scheduler_BitacoraJobs
                    (JobName, RunID, Accion, FechaAccion, ServerID, DetallesJSON, Exito, MensajeError)
                VALUES
                    (%s, %s, %s, SYSUTCDATETIME(), %s, %s, %s, %s)
            """, (
                job_name,
                run_id,
                accion,
                server_id,
                json.dumps(detalles or {}, ensure_ascii=False, default=str),
                exito,
                mensaje_error,
            ))
            conn.commit()
            cur.close()
        except Exception as e:
            logger.warning(f"[JOB_LOGGER][SQL_ERROR] No se pudo registrar bitácora: {e}")
        finally:
            if conn:
                conn.close()

    async def start_execution(self, job_name: str, metadata: Optional[Dict] = None) -> JobExecutionLog:
        """Registra inicio de ejecución."""
        log_entry = JobExecutionLog(
            job_name=job_name,
            started_at=datetime.now(timezone.utc).isoformat(),
            status="running",
            metadata=metadata or {}
        )

        self._insert_bitacora(
            job_name=job_name,
            run_id=log_entry.run_id,
            accion="START",
            detalles=log_entry.model_dump(),
            exito=None
        )

        logger.info(f"Job iniciado: {job_name} (run_id={log_entry.run_id})")
        return log_entry

    async def finish_execution(
        self,
        log_entry: JobExecutionLog,
        status: str = "success",
        processed_count: int = 0,
        success_count: int = 0,
        failed_count: int = 0,
        skipped_count: int = 0,
        message: Optional[str] = None,
        error_detail: Optional[str] = None,
        extra_metadata: Optional[Dict] = None
    ):
        """Registra fin de ejecución."""
        finished_at = datetime.now(timezone.utc)
        started_at = datetime.fromisoformat(log_entry.started_at.replace("Z", "+00:00"))
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)

        detalles = {
            **log_entry.model_dump(),
            "finished_at": finished_at.isoformat(),
            "duration_ms": duration_ms,
            "status": status,
            "processed_count": processed_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "message": message,
            "error_detail": error_detail,
            "metadata": {**(log_entry.metadata or {}), **(extra_metadata or {})}
        }

        self._insert_bitacora(
            job_name=log_entry.job_name,
            run_id=log_entry.run_id,
            accion="FINISH",
            detalles=detalles,
            exito=(status in {"success", "completed"}),
            mensaje_error=error_detail
        )

        logger.info(
            f"Job finalizado: {log_entry.job_name} (run_id={log_entry.run_id}) - "
            f"status={status}, duration={duration_ms}ms, "
            f"processed={processed_count}, success={success_count}, failed={failed_count}"
        )

    async def log_skipped(self, job_name: str, reason: str) -> JobExecutionLog:
        """Registra ejecución omitida."""
        now = datetime.now(timezone.utc).isoformat()
        log_entry = JobExecutionLog(
            job_name=job_name,
            started_at=now,
            finished_at=now,
            duration_ms=0,
            status="skipped",
            message=reason
        )

        self._insert_bitacora(
            job_name=job_name,
            run_id=log_entry.run_id,
            accion="SKIPPED",
            detalles=log_entry.model_dump(),
            exito=True,
            mensaje_error=None
        )

        logger.info(f"Job omitido: {job_name} - {reason}")
        return log_entry

    async def get_logs(
        self,
        job_name: Optional[str] = None,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Obtiene historial desde SQL."""
        from core.sql_first.db import get_sql_connection

        where = ["1=1"]
        params = []

        if job_name:
            where.append("JobName = %s")
            params.append(job_name)
        if since:
            where.append("FechaAccion >= %s")
            params.append(since)
        if status:
            if status == "success":
                where.append("Exito = 1")
            elif status == "failed":
                where.append("Exito = 0")
            elif status == "skipped":
                where.append("Accion = 'SKIPPED'")
            elif status == "running":
                where.append("Accion = 'START'")

        sql = f"""
            SELECT TOP {int(limit)}
                JobName AS job_name,
                RunID AS run_id,
                Accion AS accion,
                FechaAccion AS fecha_accion,
                ServerID AS server_id,
                DetallesJSON AS detalles_json,
                Exito AS exito,
                MensajeError AS mensaje_error
            FROM dbo.Scheduler_BitacoraJobs
            WHERE {' AND '.join(where)}
            ORDER BY FechaAccion DESC
        """

        conn = None
        try:
            conn = get_sql_connection()
            cur = conn.cursor(as_dict=True)
            cur.execute(sql, tuple(params))
            rows = list(cur.fetchall())
            cur.close()
            return rows
        except Exception as e:
            logger.warning(f"[JOB_LOGGER][SQL_ERROR] get_logs falló: {e}")
            return []
        finally:
            if conn:
                conn.close()

    async def get_last_execution(self, job_name: str) -> Optional[Dict]:
        """Obtiene última ejecución desde SQL."""
        logs = await self.get_logs(job_name=job_name, limit=1)
        return logs[0] if logs else None

    async def get_stats(self, job_name: Optional[str] = None, hours: int = 24) -> Dict:
        """Obtiene estadísticas básicas desde SQL."""
        from core.sql_first.db import get_sql_connection

        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        where = ["FechaAccion >= %s"]
        params = [since]

        if job_name:
            where.append("JobName = %s")
            params.append(job_name)

        sql = f"""
            SELECT
                JobName,
                Accion,
                Exito,
                COUNT(*) AS total
            FROM dbo.Scheduler_BitacoraJobs
            WHERE {' AND '.join(where)}
            GROUP BY JobName, Accion, Exito
        """

        conn = None
        try:
            conn = get_sql_connection()
            cur = conn.cursor(as_dict=True)
            cur.execute(sql, tuple(params))
            rows = list(cur.fetchall())
            cur.close()

            stats = {}
            for r in rows:
                job = r["JobName"]
                stats.setdefault(job, {"executions": {}, "total_processed": 0, "total_success": 0, "total_failed": 0})
                key = f"{r['Accion']}_{r['Exito']}"
                stats[job]["executions"][key] = {"count": r["total"], "avg_duration_ms": 0}
                if r["Exito"] is True:
                    stats[job]["total_success"] += r["total"]
                elif r["Exito"] is False:
                    stats[job]["total_failed"] += r["total"]

            return stats
        except Exception as e:
            logger.warning(f"[JOB_LOGGER][SQL_ERROR] get_stats falló: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    async def cleanup_old_logs(self, days: int = 30) -> int:
        """No-op conservador: no borra bitácora SQL automáticamente."""
        logger.info("[JOB_LOGGER] cleanup_old_logs omitido por seguridad SQL-only")
        return 0

# =============================================================================
# Compatibilidad SQL-only para imports existentes del scheduler
# =============================================================================

_job_logger_instance = None


def get_job_logger() -> JobLogger:
    """
    Factory singleton esperado por scheduler_manager y jobs.
    Retorna el singleton SQL de bitácora.
    """
    global _job_logger_instance
    if _job_logger_instance is None:
        _job_logger_instance = JobLogger()
    return _job_logger_instance


async def _ensure_indexes_noop(self):
    """
    Compatibilidad legacy: antes creaba índices Mongo.
    SQL-only: no-op; índices/tablas deben gestionarse por migraciones SQL.
    """
    return None


async def _log_execution_compat(self, job_name: str, status: str = "success", message: str = None, **kwargs):
    """
    Compatibilidad para jobs legacy que llaman log_execution().
    Registra START + FINISH en bitácora SQL.
    """
    log_entry = await self.start_execution(job_name, metadata=kwargs or {})
    await self.finish_execution(
        log_entry=log_entry,
        status=status,
        message=message,
        processed_count=kwargs.get("processed_count", 0) or kwargs.get("processed", 0) or 0,
        success_count=kwargs.get("success_count", 0) or kwargs.get("success", 0) or 0,
        failed_count=kwargs.get("failed_count", 0) or kwargs.get("failed", 0) or 0,
        skipped_count=kwargs.get("skipped_count", 0) or kwargs.get("skipped", 0) or 0,
        error_detail=kwargs.get("error_detail") or kwargs.get("error"),
        extra_metadata=kwargs,
    )
    return log_entry


JobLogger.ensure_indexes = _ensure_indexes_noop
JobLogger.log_execution = _log_execution_compat
