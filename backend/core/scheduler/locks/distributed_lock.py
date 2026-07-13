"""
Locks distribuidos del scheduler respaldados por EDARSAHUB SQL.

Toda falla de persistencia deniega la adquisicion del lock.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import uuid
from typing import Dict, Optional

from .sql_lock_repository import SQLLockRepository


logger = logging.getLogger(__name__)


class LockAcquisitionError(Exception):
    """No fue posible adquirir el lock distribuido."""


class DistributedLock:
    """Lock distribuido respaldado por EDARSAHUB SQL."""

    def __init__(
        self,
        job_name: str,
        repository: SQLLockRepository,
        owner_id: Optional[str] = None,
    ) -> None:
        self.job_name = job_name
        self.repository = repository
        self.owner_id = owner_id or self._build_owner_id()
        self._locked = False
        self._heartbeat_task: Optional[asyncio.Task] = None

    @staticmethod
    def _build_owner_id() -> str:
        return (
            f"{socket.gethostname()}:{os.getpid()}:"
            f"{uuid.uuid4().hex}"
        )

    async def acquire(
        self,
        timeout_seconds: int = 600,
    ) -> bool:
        try:
            acquired = await asyncio.to_thread(
                self.repository.acquire,
                self.job_name,
                self.owner_id,
                timeout_seconds,
            )
            self._locked = bool(acquired)

            if acquired:
                logger.info(
                    "Lock SQL adquirido: job=%s owner=%s",
                    self.job_name,
                    self.owner_id,
                )
            else:
                logger.info(
                    "Lock SQL ocupado: job=%s owner=%s",
                    self.job_name,
                    self.owner_id,
                )

            return self._locked

        except Exception as exc:
            self._locked = False
            logger.error(
                "Fallo cerrado adquiriendo lock SQL %s: %s",
                self.job_name,
                exc,
            )
            return False

    async def release(self) -> bool:
        await self.stop_heartbeat_loop()

        if not self._locked:
            return False

        try:
            released = await asyncio.to_thread(
                self.repository.release,
                self.job_name,
                self.owner_id,
            )
            self._locked = False

            if released:
                logger.info(
                    "Lock SQL liberado: job=%s owner=%s",
                    self.job_name,
                    self.owner_id,
                )
            else:
                logger.warning(
                    "Lock SQL no pertenecia al owner: "
                    "job=%s owner=%s",
                    self.job_name,
                    self.owner_id,
                )

            return bool(released)

        except Exception as exc:
            self._locked = False
            logger.error(
                "Error liberando lock SQL %s: %s",
                self.job_name,
                exc,
            )
            return False

    async def heartbeat(
        self,
        extend_seconds: int = 300,
    ) -> bool:
        if not self._locked:
            return False

        try:
            renewed = await asyncio.to_thread(
                self.repository.heartbeat,
                self.job_name,
                self.owner_id,
                extend_seconds,
            )

            if not renewed:
                self._locked = False
                logger.error(
                    "Se perdio el lock SQL durante heartbeat: "
                    "job=%s owner=%s",
                    self.job_name,
                    self.owner_id,
                )

            return bool(renewed)

        except Exception as exc:
            self._locked = False
            logger.error(
                "Fallo cerrado en heartbeat SQL %s: %s",
                self.job_name,
                exc,
            )
            return False

    async def extend(self, seconds: int = 300) -> bool:
        return await self.heartbeat(seconds)

    async def start_heartbeat_loop(
        self,
        interval_seconds: int = 30,
        extend_seconds: int = 300,
    ) -> None:
        await self.stop_heartbeat_loop()

        async def _loop() -> None:
            try:
                while self._locked:
                    await asyncio.sleep(interval_seconds)

                    if not self._locked:
                        break

                    renewed = await self.heartbeat(
                        extend_seconds
                    )

                    if not renewed:
                        break

            except asyncio.CancelledError:
                raise

        self._heartbeat_task = asyncio.create_task(_loop())

    async def stop_heartbeat_loop(self) -> None:
        task = self._heartbeat_task
        self._heartbeat_task = None

        if task is None:
            return

        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

    async def is_locked(self) -> bool:
        try:
            return await asyncio.to_thread(
                self.repository.is_locked,
                self.job_name,
            )
        except Exception as exc:
            logger.error(
                "No se pudo consultar lock SQL %s: %s",
                self.job_name,
                exc,
            )
            return True

    async def get_lock_info(self) -> Optional[Dict]:
        try:
            return await asyncio.to_thread(
                self.repository.get_lock_info,
                self.job_name,
            )
        except Exception as exc:
            logger.error(
                "No se pudo consultar detalle del lock SQL %s: %s",
                self.job_name,
                exc,
            )
            return None

    async def force_release(self) -> bool:
        try:
            released = await asyncio.to_thread(
                self.repository.force_release,
                self.job_name,
            )
            self._locked = False
            await self.stop_heartbeat_loop()

            if released:
                logger.warning(
                    "Lock SQL liberado administrativamente: %s",
                    self.job_name,
                )

            return bool(released)

        except Exception as exc:
            logger.error(
                "Error forzando liberacion SQL %s: %s",
                self.job_name,
                exc,
            )
            return False

    async def __aenter__(self):
        acquired = await self.acquire()

        if not acquired:
            raise LockAcquisitionError(
                f"No se pudo adquirir lock para {self.job_name}"
            )

        return self

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        await self.release()
        return False


class LockManager:
    """Factory y operaciones administrativas de locks SQL."""

    def __init__(
        self,
        db=None,
        repository: Optional[SQLLockRepository] = None,
    ) -> None:
        # db permanece temporalmente en la firma para compatibilidad.
        # No se almacena ni se utiliza.
        self.repository = repository or SQLLockRepository()

    def get_lock(self, job_name: str) -> DistributedLock:
        return DistributedLock(
            job_name=job_name,
            repository=self.repository,
        )

    async def get_all_locks(self) -> list:
        try:
            return await asyncio.to_thread(
                self.repository.get_all_locks
            )
        except Exception as exc:
            logger.error(
                "No se pudieron consultar locks SQL: %s",
                exc,
            )
            return []

    async def cleanup_expired(self) -> int:
        try:
            deleted = await asyncio.to_thread(
                self.repository.cleanup_expired
            )

            if deleted:
                logger.info(
                    "Locks SQL expirados eliminados: %s",
                    deleted,
                )

            return int(deleted)

        except Exception as exc:
            logger.error(
                "No se pudieron limpiar locks SQL: %s",
                exc,
            )
            return 0

    async def ensure_indexes(self) -> None:
        # El nombre se conserva por compatibilidad.
        # La operacion solo valida el contrato SQL.
        await asyncio.to_thread(
            self.repository.ensure_table_exists
        )


_lock_manager_instance: Optional[LockManager] = None


def get_lock_manager(
    db=None,
    repository: Optional[SQLLockRepository] = None,
) -> LockManager:
    global _lock_manager_instance

    if _lock_manager_instance is None:
        _lock_manager_instance = LockManager(
            repository=repository
        )

    return _lock_manager_instance


def reset_lock_manager() -> None:
    global _lock_manager_instance
    _lock_manager_instance = None
