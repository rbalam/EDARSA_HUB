"""
Repositorio SQL para locks distribuidos del scheduler.

Fuente canonica:
    dbo.Scheduler_DistributedLocks

Reglas:
- No crea tablas ni indices durante el runtime.
- No usa almacenes alternos ni fallback silencioso.
- Verifica EDARSAHUB y el login canonico HRLectura.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


EXPECTED_DATABASE = "EDARSAHUB"
EXPECTED_LOGIN = "HRLectura"

ConnectionFactory = Callable[[], Any]


class SQLLockRepository:
    """Persistencia SQL Server para locks distribuidos."""

    def __init__(
        self,
        connection_factory: Optional[ConnectionFactory] = None,
    ) -> None:
        self._connection_factory = (
            connection_factory or self._default_connection_factory
        )

    @staticmethod
    def _default_connection_factory():
        from core.sql_first.db import get_sql_connection

        return get_sql_connection()

    def _open_connection(self):
        conn = self._connection_factory()
        cur = None

        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT
                    DB_NAME() AS database_name,
                    SUSER_SNAME() AS login_name
                """
            )
            identity = cur.fetchone() or {}

            database_name = str(
                identity.get("database_name") or ""
            ).strip()
            login_name = str(
                identity.get("login_name") or ""
            ).strip()

            if database_name.lower() != EXPECTED_DATABASE.lower():
                raise RuntimeError(
                    "Base SQL incorrecta para scheduler locks: "
                    f"{database_name!r}"
                )

            if login_name.lower() != EXPECTED_LOGIN.lower():
                raise RuntimeError(
                    "Login SQL incorrecto para scheduler locks: "
                    f"{login_name!r}; esperado {EXPECTED_LOGIN!r}"
                )

            return conn

        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            raise

        finally:
            if cur is not None:
                try:
                    cur.close()
                except Exception:
                    pass

    @staticmethod
    def _affected_rows(cur) -> int:
        rowcount = getattr(cur, "rowcount", None)

        if rowcount is not None and int(rowcount) >= 0:
            return int(rowcount)

        cur.execute("SELECT @@ROWCOUNT AS affected_rows")
        row = cur.fetchone() or {}
        return int(row.get("affected_rows") or 0)

    def ensure_table_exists(self) -> None:
        conn = self._open_connection()
        cur = None

        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT
                    OBJECT_ID(
                        'dbo.Scheduler_DistributedLocks',
                        'U'
                    ) AS object_id
                """
            )
            row = cur.fetchone() or {}

            if row.get("object_id") is None:
                raise RuntimeError(
                    "Falta dbo.Scheduler_DistributedLocks. "
                    "Debe aplicarse la migracion antes de iniciar "
                    "el scheduler."
                )

            cur.execute(
                """
                SELECT
                    c.name AS column_name
                FROM sys.columns AS c
                WHERE c.object_id = OBJECT_ID(
                    'dbo.Scheduler_DistributedLocks',
                    'U'
                )
                """
            )

            actual = {
                str(item["column_name"])
                for item in cur.fetchall()
            }
            required = {
                "JobName",
                "OwnerID",
                "AcquiredAt",
                "HeartbeatAt",
                "LockUntil",
            }

            missing = sorted(required - actual)

            if missing:
                raise RuntimeError(
                    "Contrato incompleto en "
                    "dbo.Scheduler_DistributedLocks: "
                    f"faltan {missing}"
                )

        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def acquire(
        self,
        job_name: str,
        owner_id: str,
        timeout_seconds: int,
    ) -> bool:
        if not job_name:
            raise ValueError("job_name es obligatorio")

        if not owner_id:
            raise ValueError("owner_id es obligatorio")

        timeout_seconds = max(1, int(timeout_seconds))

        conn = self._open_connection()
        cur = None

        try:
            cur = conn.cursor(as_dict=True)
            cur.execute("SET XACT_ABORT ON")
            cur.execute(
                "SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"
            )
            # pymssql con autocommit=False ya mantiene una transaccion.
            # Un BEGIN adicional deja @@TRANCOUNT=2 y el commit solo
            # reduce el contador a 1; al cerrar se revierte el INSERT.
            cur.execute(
                """
                SELECT
                    JobName,
                    OwnerID,
                    LockUntil
                FROM dbo.Scheduler_DistributedLocks
                    WITH (UPDLOCK, HOLDLOCK)
                WHERE JobName = %s
                """,
                (job_name,),
            )
            current = cur.fetchone()

            if current is None:
                cur.execute(
                    """
                    INSERT INTO dbo.Scheduler_DistributedLocks
                    (
                        JobName,
                        OwnerID,
                        AcquiredAt,
                        HeartbeatAt,
                        LockUntil
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        SYSUTCDATETIME(),
                        SYSUTCDATETIME(),
                        DATEADD(
                            SECOND,
                            %s,
                            SYSUTCDATETIME()
                        )
                    )
                    """,
                    (
                        job_name,
                        owner_id,
                        timeout_seconds,
                    ),
                )
                conn.commit()
                return True

            cur.execute(
                """
                UPDATE dbo.Scheduler_DistributedLocks
                SET
                    OwnerID = %s,
                    AcquiredAt = SYSUTCDATETIME(),
                    HeartbeatAt = SYSUTCDATETIME(),
                    LockUntil = DATEADD(
                        SECOND,
                        %s,
                        SYSUTCDATETIME()
                    )
                WHERE JobName = %s
                  AND
                  (
                      OwnerID = %s
                      OR LockUntil <= SYSUTCDATETIME()
                  )
                """,
                (
                    owner_id,
                    timeout_seconds,
                    job_name,
                    owner_id,
                ),
            )
            affected = self._affected_rows(cur)

            if affected != 1:
                conn.rollback()
                return False

            conn.commit()
            return True

        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise

        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def release(
        self,
        job_name: str,
        owner_id: str,
    ) -> bool:
        conn = self._open_connection()
        cur = None

        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                DELETE FROM dbo.Scheduler_DistributedLocks
                WHERE JobName = %s
                  AND OwnerID = %s
                """,
                (job_name, owner_id),
            )
            affected = self._affected_rows(cur)
            conn.commit()
            return affected == 1

        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise

        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def heartbeat(
        self,
        job_name: str,
        owner_id: str,
        extend_seconds: int,
    ) -> bool:
        extend_seconds = max(1, int(extend_seconds))

        conn = self._open_connection()
        cur = None

        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                UPDATE dbo.Scheduler_DistributedLocks
                SET
                    HeartbeatAt = SYSUTCDATETIME(),
                    LockUntil = DATEADD(
                        SECOND,
                        %s,
                        SYSUTCDATETIME()
                    )
                WHERE JobName = %s
                  AND OwnerID = %s
                  AND LockUntil > SYSUTCDATETIME()
                """,
                (
                    extend_seconds,
                    job_name,
                    owner_id,
                ),
            )
            affected = self._affected_rows(cur)
            conn.commit()
            return affected == 1

        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise

        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def is_locked(self, job_name: str) -> bool:
        conn = self._open_connection()
        cur = None

        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT TOP 1
                    1 AS is_locked
                FROM dbo.Scheduler_DistributedLocks
                WHERE JobName = %s
                  AND LockUntil > SYSUTCDATETIME()
                """,
                (job_name,),
            )
            return cur.fetchone() is not None

        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def get_lock_info(
        self,
        job_name: str,
    ) -> Optional[Dict[str, Any]]:
        conn = self._open_connection()
        cur = None

        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT
                    JobName AS job_name,
                    OwnerID AS owner,
                    AcquiredAt AS acquired_at,
                    HeartbeatAt AS heartbeat_at,
                    LockUntil AS lock_until
                FROM dbo.Scheduler_DistributedLocks
                WHERE JobName = %s
                """,
                (job_name,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def force_release(self, job_name: str) -> bool:
        conn = self._open_connection()
        cur = None

        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                DELETE FROM dbo.Scheduler_DistributedLocks
                WHERE JobName = %s
                """,
                (job_name,),
            )
            affected = self._affected_rows(cur)
            conn.commit()
            return affected > 0

        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise

        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def get_all_locks(self) -> List[Dict[str, Any]]:
        conn = self._open_connection()
        cur = None

        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT
                    JobName AS job_name,
                    OwnerID AS owner,
                    AcquiredAt AS acquired_at,
                    HeartbeatAt AS heartbeat_at,
                    LockUntil AS lock_until
                FROM dbo.Scheduler_DistributedLocks
                WHERE LockUntil > SYSUTCDATETIME()
                ORDER BY JobName
                """
            )
            return [
                dict(row)
                for row in cur.fetchall()
            ]

        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def cleanup_expired(self) -> int:
        conn = self._open_connection()
        cur = None

        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                DELETE FROM dbo.Scheduler_DistributedLocks
                WHERE LockUntil <= SYSUTCDATETIME()
                """
            )
            affected = self._affected_rows(cur)
            conn.commit()
            return affected

        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise

        finally:
            if cur is not None:
                cur.close()
            conn.close()
