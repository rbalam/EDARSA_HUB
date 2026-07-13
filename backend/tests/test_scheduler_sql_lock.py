import asyncio
from pathlib import Path

import pytest

from core.scheduler.locks.distributed_lock import (
    DistributedLock,
    LockManager,
)
from core.scheduler.locks.sql_lock_repository import (
    SQLLockRepository,
)


class FakeRepository:
    def __init__(self):
        self.acquire_result = True
        self.release_result = True
        self.heartbeat_result = True
        self.active = False
        self.owner = None
        self.ensure_calls = 0

    def ensure_table_exists(self):
        self.ensure_calls += 1

    def acquire(
        self,
        job_name,
        owner_id,
        timeout_seconds,
    ):
        if not self.acquire_result:
            return False

        self.active = True
        self.owner = owner_id
        return True

    def release(self, job_name, owner_id):
        if (
            not self.release_result
            or not self.active
            or owner_id != self.owner
        ):
            return False

        self.active = False
        return True

    def heartbeat(
        self,
        job_name,
        owner_id,
        extend_seconds,
    ):
        return (
            self.heartbeat_result
            and self.active
            and owner_id == self.owner
        )

    def is_locked(self, job_name):
        return self.active

    def get_lock_info(self, job_name):
        if not self.active:
            return None

        return {
            "job_name": job_name,
            "owner": self.owner,
        }

    def force_release(self, job_name):
        existed = self.active
        self.active = False
        return existed

    def get_all_locks(self):
        if not self.active:
            return []

        return [{
            "job_name": "job-test",
            "owner": self.owner,
        }]

    def cleanup_expired(self):
        return 0


def test_sql_lock_acquire_heartbeat_release():
    async def scenario():
        repo = FakeRepository()
        lock = DistributedLock(
            job_name="job-test",
            repository=repo,
            owner_id="owner-test",
        )

        assert await lock.acquire(timeout_seconds=60)
        assert await lock.is_locked()
        assert await lock.heartbeat(extend_seconds=60)

        info = await lock.get_lock_info()

        assert info["job_name"] == "job-test"
        assert info["owner"] == "owner-test"

        assert await lock.release()
        assert not repo.active

    asyncio.run(scenario())


def test_sql_lock_fails_closed_when_acquire_denied():
    async def scenario():
        repo = FakeRepository()
        repo.acquire_result = False

        lock = DistributedLock(
            job_name="job-denied",
            repository=repo,
            owner_id="owner-test",
        )

        assert not await lock.acquire()
        assert not lock._locked

    asyncio.run(scenario())


def test_sql_lock_fails_closed_when_repository_raises():
    class BrokenRepository(FakeRepository):
        def acquire(
            self,
            job_name,
            owner_id,
            timeout_seconds,
        ):
            raise RuntimeError("SQL unavailable")

    async def scenario():
        lock = DistributedLock(
            job_name="job-broken",
            repository=BrokenRepository(),
            owner_id="owner-test",
        )

        assert not await lock.acquire()
        assert not lock._locked

    asyncio.run(scenario())


def test_sql_lock_is_locked_fails_closed():
    class BrokenRepository(FakeRepository):
        def is_locked(self, job_name):
            raise RuntimeError("SQL unavailable")

    async def scenario():
        lock = DistributedLock(
            job_name="job-broken",
            repository=BrokenRepository(),
            owner_id="owner-test",
        )

        assert await lock.is_locked()

    asyncio.run(scenario())


def test_lock_manager_returns_sql_lock():
    repo = FakeRepository()
    manager = LockManager(
        db=object(),
        repository=repo,
    )

    lock = manager.get_lock("job-test")

    assert isinstance(lock, DistributedLock)
    assert lock.repository is repo


def test_manager_validates_contract():
    async def scenario():
        repo = FakeRepository()
        manager = LockManager(repository=repo)

        await manager.ensure_indexes()

        assert repo.ensure_calls == 1

    asyncio.run(scenario())


class IdentityCursor:
    def __init__(self, identity):
        self.identity = identity
        self.closed = False

    def execute(self, sql, params=None):
        return None

    def fetchone(self):
        return dict(self.identity)

    def close(self):
        self.closed = True


class IdentityConnection:
    def __init__(self, identity):
        self.cursor_instance = IdentityCursor(identity)
        self.closed = False

    def cursor(self, as_dict=False):
        assert as_dict is True
        return self.cursor_instance

    def close(self):
        self.closed = True


def test_repository_rejects_wrong_login_and_closes():
    conn = IdentityConnection({
        "database_name": "EDARSAHUB",
        "login_name": "OtroLogin",
    })
    repo = SQLLockRepository(
        connection_factory=lambda: conn
    )

    with pytest.raises(RuntimeError):
        repo._open_connection()

    assert conn.closed


def test_lock_source_has_no_legacy_fallback():
    root = Path(__file__).resolve().parents[1]

    files = [
        root / "core/scheduler/locks/distributed_lock.py",
        root / "core/scheduler/locks/sql_lock_repository.py",
        root / "core/scheduler/locks/__init__.py",
    ]

    forbidden = [
        "mongo_stub",
        "StubDatabase",
        "NullLock",
        "find_one",
        "update_one",
        "delete_one",
        "delete_many",
        "count_documents",
        "create_index",
    ]

    for path in files:
        source = path.read_text(encoding="utf-8")

        for token in forbidden:
            assert token not in source, (
                f"{token!r} permanece en {path}"
            )


def test_repository_uses_atomic_sql_contract():
    root = Path(__file__).resolve().parents[1]
    path = (
        root
        / "core/scheduler/locks/sql_lock_repository.py"
    )
    source = path.read_text(encoding="utf-8")
    upper = source.upper()

    assert (
        "SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"
        in upper
    )
    assert "WITH (UPDLOCK, HOLDLOCK)" in upper
    assert "OWNERID = %S" in upper
    assert "LOCKUNTIL <= SYSUTCDATETIME()" in upper
    assert "CREATE TABLE" not in upper
    assert "ALTER TABLE" not in upper


def test_job_logger_has_no_db_dependency():
    root = Path(__file__).resolve().parents[1]
    path = root / "core/scheduler/job_logger.py"
    source = path.read_text(encoding="utf-8")

    assert "def __init__(self, db=None)" not in source
    assert "def get_job_logger(db=None)" not in source
    assert "self.db" not in source


def test_acquire_does_not_open_nested_transaction():
    """pymssql autocommit=False ya inicia la transaccion."""
    import inspect

    from core.scheduler.locks.sql_lock_repository import (
        SQLLockRepository,
    )

    source = inspect.getsource(
        SQLLockRepository.acquire
    ).upper()

    assert "BEGIN TRANSACTION" not in source
