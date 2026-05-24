"""
EDARSA HUB - Job Execution Logger
=================================
Sistema de logging y métricas para ejecuciones de jobs.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
import logging
import uuid

logger = logging.getLogger(__name__)


class JobExecutionLog(BaseModel):
    """Registro de una ejecución de job."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_name: str
    run_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: str
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    status: str = "running"  # running, success, failed, skipped
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
    Logger de ejecuciones de jobs.
    
    Registra inicio, fin, métricas y errores de cada ejecución.
    
    NOTA: En modo SQL-only (db=None), opera en modo dummy sin persistencia.
    """
    
    COLLECTION_NAME = "scheduler_job_log"
    
    def __init__(self, db):
        self.db = db
        if db is not None:
            self.collection = db[self.COLLECTION_NAME]
        else:
            self.collection = None
            logger.warning("[JOB_LOGGER] Inicializado SIN MongoDB - Logs en memoria solamente")
    
    async def start_execution(
        self,
        job_name: str,
        metadata: Optional[Dict] = None
    ) -> JobExecutionLog:
        """
        Registra inicio de ejecución.
        
        Returns:
            JobExecutionLog para tracking
        """
        log_entry = JobExecutionLog(
            job_name=job_name,
            started_at=datetime.now(timezone.utc).isoformat(),
            status="running",
            metadata=metadata or {}
        )
        
        # MongoDB ELIMINADO - Solo persistir si db está disponible
        if self.collection is not None:
            await self.collection.insert_one(log_entry.model_dump())
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
        """
        Registra fin de ejecución.
        """
        finished_at = datetime.now(timezone.utc)
        started_at = datetime.fromisoformat(log_entry.started_at.replace("Z", "+00:00"))
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        
        updates = {
            "finished_at": finished_at.isoformat(),
            "duration_ms": duration_ms,
            "status": status,
            "processed_count": processed_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "message": message,
            "error_detail": error_detail
        }
        
        if extra_metadata:
            updates["metadata"] = {**log_entry.metadata, **extra_metadata}
        
        # MongoDB ELIMINADO - Solo persistir si db está disponible
        if self.collection is not None:
            await self.collection.update_one(
                {"id": log_entry.id},
                {"$set": updates}
            )
        
        log_msg = f"Job finalizado: {log_entry.job_name} (run_id={log_entry.run_id}) - " \
                  f"status={status}, duration={duration_ms}ms, " \
                  f"processed={processed_count}, success={success_count}, failed={failed_count}"
        
        if status == "success":
            logger.info(log_msg)
        elif status == "skipped":
            logger.info(log_msg)
        else:
            logger.warning(log_msg)
    
    async def log_skipped(
        self,
        job_name: str,
        reason: str
    ) -> JobExecutionLog:
        """
        Registra ejecución omitida (por lock, config, etc.).
        """
        log_entry = JobExecutionLog(
            job_name=job_name,
            started_at=datetime.now(timezone.utc).isoformat(),
            finished_at=datetime.now(timezone.utc).isoformat(),
            duration_ms=0,
            status="skipped",
            message=reason
        )
        
        # MongoDB ELIMINADO - Solo persistir si db está disponible
        if self.collection is not None:
            await self.collection.insert_one(log_entry.model_dump())
        logger.info(f"Job omitido: {job_name} - {reason}")
        
        return log_entry
    
    async def get_logs(
        self,
        job_name: Optional[str] = None,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Obtiene historial de ejecuciones.
        """
        # MongoDB ELIMINADO - Retornar lista vacía si no hay db
        if self.collection is None:
            return []
            
        filtro = {}
        if job_name:
            filtro["job_name"] = job_name
        if status:
            filtro["status"] = status
        if since:
            filtro["started_at"] = {"$gte": since.isoformat()}
        
        cursor = self.collection.find(
            filtro, {"_id": 0}
        ).sort("started_at", -1).limit(limit)
        
        return await cursor.to_list(limit)
    
    async def get_last_execution(self, job_name: str) -> Optional[Dict]:
        """Obtiene última ejecución de un job."""
        # MongoDB ELIMINADO - Retornar None si no hay db
        if self.collection is None:
            return None
        return await self.collection.find_one(
            {"job_name": job_name},
            {"_id": 0},
            sort=[("started_at", -1)]
        )
    
    async def get_stats(self, job_name: Optional[str] = None, hours: int = 24) -> Dict:
        """
        Obtiene estadísticas de ejecuciones.
        """
        # MongoDB ELIMINADO - Retornar stats vacío si no hay db
        if self.collection is None:
            return {}
            
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        
        match_stage = {"started_at": {"$gte": since}}
        if job_name:
            match_stage["job_name"] = job_name
        
        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": {"job_name": "$job_name", "status": "$status"},
                    "count": {"$sum": 1},
                    "avg_duration_ms": {"$avg": "$duration_ms"},
                    "total_processed": {"$sum": "$processed_count"},
                    "total_success": {"$sum": "$success_count"},
                    "total_failed": {"$sum": "$failed_count"}
                }
            }
        ]
        
        cursor = self.collection.aggregate(pipeline)
        
        stats = {}
        async for doc in cursor:
            job = doc["_id"]["job_name"]
            status = doc["_id"]["status"]
            
            if job not in stats:
                stats[job] = {
                    "executions": {},
                    "total_processed": 0,
                    "total_success": 0,
                    "total_failed": 0
                }
            
            stats[job]["executions"][status] = {
                "count": doc["count"],
                "avg_duration_ms": round(doc["avg_duration_ms"] or 0, 2)
            }
            stats[job]["total_processed"] += doc["total_processed"]
            stats[job]["total_success"] += doc["total_success"]
            stats[job]["total_failed"] += doc["total_failed"]
        
        return stats
    
    async def cleanup_old_logs(self, days: int = 30) -> int:
        """
        Limpia logs antiguos.
        """
        # MongoDB ELIMINADO - Retornar 0 si no hay db
        if self.collection is None:
            return 0
            
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = await self.collection.delete_many({
            "started_at": {"$lt": cutoff}
        })
        if result.deleted_count > 0:
            logger.info(f"Limpiados {result.deleted_count} logs de jobs antiguos")
        return result.deleted_count
    
    async def ensure_indexes(self):
        """Crea índices necesarios."""
        # MongoDB ELIMINADO - No hacer nada si no hay db
        if self.collection is None:
            return
            
        try:
            await self.collection.create_index([("job_name", 1), ("started_at", -1)])
        except Exception:
            pass  # Índice ya existe
        
        try:
            await self.collection.create_index("status")
        except Exception:
            pass
        
        # TTL index - eliminar logs después de 30 días
        # Primero intentar eliminar índice conflictivo si existe
        try:
            await self.collection.drop_index("started_at_1")
        except Exception:
            pass  # No existe
        
        try:
            await self.collection.create_index(
                "started_at",
                expireAfterSeconds=30 * 24 * 60 * 60,  # TTL 30 días
                name="ttl_cleanup"
            )
        except Exception:
            pass  # Ya existe o conflicto


# Singleton
_job_logger: Optional[JobLogger] = None


def get_job_logger(db) -> JobLogger:
    """Obtiene el logger de jobs."""
    global _job_logger
    if _job_logger is None:
        _job_logger = JobLogger(db)
    return _job_logger
