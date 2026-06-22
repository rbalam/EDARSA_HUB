"""
EDARSA HUB - Distributed Lock Manager
=====================================
Sistema de locks distribuidos para evitar ejecuciones concurrentes.

Clase legacy para locks persistentes. En operación SQL-only el LockManager usa NullLock.
"""

from typing import Optional, Dict
from datetime import datetime, timezone, timedelta
import logging
import uuid
import asyncio

logger = logging.getLogger(__name__)


class DistributedLock:
    """
    Lock distribuido legacy basado en una dependencia documental.
    
    Características:
    - Evita doble procesamiento de jobs
    - Expira por timeout de seguridad
    - Heartbeat para mantener lock activo
    - Liberación limpia al terminar
    """
    
    COLLECTION_NAME = "scheduler_locks"
    
    def __init__(self, db, job_name: str, owner_id: Optional[str] = None):
        """
        Args:
            db: Dependencia legacy compatible con colección documental
            job_name: Nombre del job a bloquear
            owner_id: Identificador único del proceso (auto-generado si None)
        """
        self.db = db
        self.job_name = job_name
        self.owner_id = owner_id or f"worker_{uuid.uuid4().hex[:8]}"
        self.collection = db[self.COLLECTION_NAME]
        self._locked = False
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    async def acquire(self, timeout_seconds: int = 600) -> bool:
        """
        Intenta adquirir el lock.
        
        Args:
            timeout_seconds: Tiempo máximo del lock
            
        Returns:
            True si se adquirió, False si ya está bloqueado
        """
        ahora = datetime.now(timezone.utc)
        lock_until = ahora + timedelta(seconds=timeout_seconds)
        
        try:
            # Intentar crear o actualizar lock si está expirado
            await self.collection.update_one(
                {
                    "job_name": self.job_name,
                    "$or": [
                        {"lock_until": {"$lt": ahora}},  # Lock expirado
                        {"lock_until": {"$exists": False}}  # Sin lock
                    ]
                },
                {
                    "$set": {
                        "job_name": self.job_name,
                        "owner": self.owner_id,
                        "locked_at": ahora,
                        "lock_until": lock_until,
                        "heartbeat_at": ahora
                    }
                },
                upsert=True
            )
            
            # Verificar si realmente obtuvimos el lock
            lock_doc = await self.collection.find_one({"job_name": self.job_name})
            if lock_doc and lock_doc.get("owner") == self.owner_id:
                self._locked = True
                logger.info(f"Lock adquirido: job={self.job_name}, owner={self.owner_id}")
                return True
            
            logger.debug(f"Lock no disponible: job={self.job_name}, owner_actual={lock_doc.get('owner') if lock_doc else 'N/A'}")
            return False
            
        except Exception as e:
            # Si hay error de duplicate key, otro proceso tomó el lock
            if "duplicate key" in str(e).lower():
                logger.debug(f"Lock ocupado por otro proceso: job={self.job_name}")
                return False
            logger.error(f"Error adquiriendo lock {self.job_name}: {e}")
            return False
    
    async def release(self) -> bool:
        """
        Libera el lock.
        
        Returns:
            True si se liberó correctamente
        """
        if not self._locked:
            return True
        
        try:
            # Detener heartbeat si está activo
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
                self._heartbeat_task = None
            
            # Solo liberar si somos el owner
            result = await self.collection.delete_one({
                "job_name": self.job_name,
                "owner": self.owner_id
            })
            
            self._locked = False
            
            if result.deleted_count > 0:
                logger.info(f"Lock liberado: job={self.job_name}, owner={self.owner_id}")
                return True
            
            logger.warning(f"Lock no encontrado para liberar: job={self.job_name}")
            return False
            
        except Exception as e:
            logger.error(f"Error liberando lock {self.job_name}: {e}")
            return False
    
    async def heartbeat(self, extend_seconds: int = 300) -> bool:
        """
        Actualiza el heartbeat y extiende el lock.
        
        Args:
            extend_seconds: Segundos adicionales de lock
            
        Returns:
            True si se actualizó correctamente
        """
        if not self._locked:
            return False
        
        ahora = datetime.now(timezone.utc)
        lock_until = ahora + timedelta(seconds=extend_seconds)
        
        try:
            result = await self.collection.update_one(
                {
                    "job_name": self.job_name,
                    "owner": self.owner_id
                },
                {
                    "$set": {
                        "heartbeat_at": ahora,
                        "lock_until": lock_until
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error en heartbeat {self.job_name}: {e}")
            return False
    
    async def start_heartbeat_loop(self, interval_seconds: int = 30, extend_seconds: int = 300):
        """
        Inicia loop de heartbeat en background.
        
        Args:
            interval_seconds: Intervalo entre heartbeats
            extend_seconds: Extensión del lock en cada heartbeat
        """
        async def _heartbeat_loop():
            while self._locked:
                await asyncio.sleep(interval_seconds)
                if self._locked:
                    await self.heartbeat(extend_seconds)
        
        self._heartbeat_task = asyncio.create_task(_heartbeat_loop())
    
    async def is_locked(self) -> bool:
        """Verifica si el job está bloqueado (por cualquier proceso)."""
        ahora = datetime.now(timezone.utc)
        lock_doc = await self.collection.find_one({
            "job_name": self.job_name,
            "lock_until": {"$gt": ahora}
        })
        return lock_doc is not None
    
    async def get_lock_info(self) -> Optional[Dict]:
        """Obtiene información del lock actual."""
        lock_doc = await self.collection.find_one(
            {"job_name": self.job_name},
            {"_id": 0}
        )
        return lock_doc
    
    async def force_release(self) -> bool:
        """
        Fuerza liberación del lock (para admin/emergencias).
        
        ADVERTENCIA: Usar solo cuando sea absolutamente necesario.
        """
        try:
            result = await self.collection.delete_one({"job_name": self.job_name})
            logger.warning(f"Lock forzado a liberar: job={self.job_name}")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error forzando liberación de lock {self.job_name}: {e}")
            return False
    
    async def __aenter__(self):
        """Context manager async entry."""
        acquired = await self.acquire()
        if not acquired:
            raise LockAcquisitionError(f"No se pudo adquirir lock para {self.job_name}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager async exit."""
        await self.release()
        return False  # No suprimir excepciones


class LockAcquisitionError(Exception):
    """Error cuando no se puede adquirir un lock."""
    pass


class LockManager:
    """
    Manager central de locks.
    
    NOTA: Con StubDatabase o db=None, retorna NullLock que siempre permite ejecución.
    """
    
    def __init__(self, db):
        self.db = db
        # Detectar si es StubDatabase
        self._is_stub = db is not None and hasattr(db, '_collections') and db.__class__.__name__ == 'StubDatabase'
        
        if db is not None and not self._is_stub:
            self.collection = db[DistributedLock.COLLECTION_NAME]
            logger.info("[LOCK_MANAGER] Inicializado con dependencia legacy documental")
        else:
            self.collection = None
            logger.info("[LOCK_MANAGER] Inicializado en modo SQL-only - Usando NullLock")
    
    def get_lock(self, job_name: str) -> DistributedLock:
        """Crea una instancia de lock para un job."""
        if self.db is None or self._is_stub:
            return NullLock(job_name)  # Retornar lock dummy
        return DistributedLock(self.db, job_name)
    
    async def get_all_locks(self) -> list:
        """Obtiene todos los locks activos."""
        if self.collection is None:
            return []
        ahora = datetime.now(timezone.utc)
        cursor = self.collection.find(
            {"lock_until": {"$gt": ahora}},
            {"_id": 0}
        )
        return await cursor.to_list(100)
    
    async def cleanup_expired(self) -> int:
        """Limpia locks expirados."""
        if self.collection is None:
            return 0
        ahora = datetime.now(timezone.utc)
        result = await self.collection.delete_many({
            "lock_until": {"$lt": ahora}
        })
        if result.deleted_count > 0:
            logger.info(f"Limpiados {result.deleted_count} locks expirados")
        return result.deleted_count
    
    async def ensure_indexes(self):
        """Crea índices necesarios."""
        if self.collection is None:
            return
        await self.collection.create_index("job_name", unique=True)
        await self.collection.create_index("lock_until")
        await self.collection.create_index("owner")


class NullLock:
    """
    Lock dummy que siempre permite ejecución.
    Se usa en modo SQL-only o cuando no hay dependencia legacy de locks.
    """
    
    def __init__(self, job_name: str):
        self.job_name = job_name
        self._locked = False
        self._heartbeat_task = None
    
    async def acquire(self, timeout_seconds: int = 600) -> bool:
        """Siempre retorna True (permite ejecución)."""
        self._locked = True
        logger.debug(f"[NULL_LOCK] Adquirido (dummy) para: {self.job_name}")
        return True
    
    async def release(self) -> bool:
        """No hace nada."""
        self._locked = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        return True
    
    async def is_locked(self) -> bool:
        return self._locked
    
    async def start_heartbeat_loop(self, interval_seconds: int = 30, extend_seconds: int = 300):
        """No hace nada - NullLock no necesita heartbeat."""
        logger.debug(f"[NULL_LOCK] Heartbeat ignorado para: {self.job_name}")
        pass
    
    async def stop_heartbeat_loop(self):
        """No hace nada."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
    
    async def extend(self, seconds: int = 300) -> bool:
        """Siempre retorna True."""
        return True
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()
        return False


# Singleton
_lock_manager: Optional[LockManager] = None


def get_lock_manager(db) -> LockManager:
    """Obtiene el manager de locks."""
    global _lock_manager
    if _lock_manager is None:
        _lock_manager = LockManager(db)
    return _lock_manager
