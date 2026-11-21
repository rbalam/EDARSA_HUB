"""Pruebas GATE-M1: DDL aditivo SQL canonico, rollback reversible, perfil HRLectura y backfill idempotente."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("JWT_SECRET", "unit-test-only-signing-material-gate-m1-0001")
os.environ.setdefault("EDARSAHUB_SQL_HOST", "127.0.0.1")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "HRLectura")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "unit-test-only-placeholder")

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "backend"), str(ROOT / "tools" / "mirror_sync")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest

from backend.tools import edarsahub_sql_runner as sql_runner
from tools.mirror_sync import readonly_audit_profiles as profiles
from tools.mirror_sync import universal_job_bridge as bridge
from tools.mirror_sync import worker_sql_projection as proj


MIGRATION_FILE = ROOT / "backend/database/migrations/20261120_001_worker_operations_canonical_state.sql"
VALIDATION_FILE = ROOT / "backend/database/validation/20261120_001_worker_operations_canonical_state_validation.sql"
ROLLBACK_FILE = ROOT / "backend/database/rollback/20261120_001_worker_operations_canonical_state_rollback.sql"


def test_gate_m1_sql_artifacts_exist_and_pass_sql_runner_safety(monkeypatch):
    assert MIGRATION_FILE.is_file()
    assert VALIDATION_FILE.is_file()
    assert ROLLBACK_FILE.is_file()

    mig_sql = MIGRATION_FILE.read_text(encoding="utf-8")
    val_sql = VALIDATION_FILE.read_text(encoding="utf-8")
    rb_sql = ROLLBACK_FILE.read_text(encoding="utf-8")

    # Migration passes runner safety in migrate mode (no DROP/TRUNCATE/DELETE)
    monkeypatch.setenv("EDARSAHUB_ALLOW_MIGRATIONS", "true")
    sql_runner.validate_sql_safety(mig_sql, "migrate")
    assert len(sql_runner.split_sql_batches(mig_sql)) >= 6
    assert "DB_NAME() <> N'EDARSAHUB'" in mig_sql
    assert "ProductionTouched = 0" in mig_sql
    for tbl in ("Sys_Worker_Jobs", "Sys_Worker_Incidents", "Sys_Worker_RecoveryEvents", "Sys_Worker_Capabilities"):
        assert f"dbo.{tbl}" in mig_sql
        assert f"GRANT SELECT ON OBJECT::dbo.{tbl} TO HRLectura" in mig_sql
    for sp in ("sp_Worker_UpsertJobState", "sp_Worker_UpsertIncident", "sp_Worker_RecordRecoveryEvent", "sp_Worker_UpsertCapability"):
        assert f"CREATE OR ALTER PROCEDURE dbo.{sp}" in mig_sql
        assert f"GRANT EXECUTE ON OBJECT::dbo.{sp} TO HRLectura" in mig_sql

    # Validation passes runner safety in read-only validate mode
    sql_runner.validate_sql_safety(val_sql, "validate")
    assert "SELECT 1 " not in val_sql

    # Rollback drops SPs before tables in reverse dependency order and guards DB_NAME()
    assert "DB_NAME() <> N'EDARSAHUB'" in rb_sql
    assert rb_sql.index("DROP PROCEDURE dbo.sp_Worker_UpsertCapability") < rb_sql.index("DROP TABLE dbo.Sys_Worker_Capabilities")
    assert rb_sql.index("DROP TABLE dbo.Sys_Worker_RecoveryEvents") < rb_sql.index("DROP TABLE dbo.Sys_Worker_Incidents")


def test_worker_operations_readonly_audit_profile_is_select_only():
    assert profiles.is_allowed_readonly_audit_profile("worker_operations_sql_state_v1")
    checks = profiles.build_readonly_audit_checks("worker_operations_sql_state_v1")
    assert len(checks) == 1
    assert checks[0]["type"] == "sql_readonly_audit"
    assert checks[0]["source"] == "EDARSAHUB"
    names = {q["name"] for q in checks[0]["queries"]}
    assert names == {
        "worker_sql_identity",
        "worker_sql_tables",
        "worker_sql_procedures",
        "worker_sql_hrlectura_permissions",
        "worker_sql_row_counts",
    }
    for q in checks[0]["queries"]:
        up = q["sql"].upper()
        assert up.lstrip().startswith("SELECT ")
        for forbidden in (" INSERT ", " UPDATE ", " DELETE ", " DROP ", " ALTER ", " CREATE ", " EXEC ", " MERGE "):
            assert forbidden not in f" {up} "


def test_bridge_validates_worker_sql_backfill_development_mode():
    valid = {
        "schema": "edarsahub.worker-job.v2",
        "job_id": "EDARSAHUB-BOS-GATE-M1-BACKFILL-TEST",
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "production_allowed": False,
        "objective": "Backfill canonico GATE-M1.",
        "human_summary_language": "es",
        "mode": "WORKER_SQL_BACKFILL_DEVELOPMENT",
        "actions": [],
        "confirm_sql_backfill": True,
        "batch_size": 200,
        "preflight_audit_profile": "worker_operations_sql_state_v1",
        "post_audit_profile": "worker_operations_sql_state_v1",
    }
    assert bridge.validate(valid) == []

    # Negativos: sql inline, sin confirmacion, acciones no vacias, produccion
    bad = dict(valid)
    bad["sql"] = "DELETE FROM dbo.Sys_Worker_Jobs"
    bad["confirm_sql_backfill"] = False
    bad["actions"] = [{"type": "write_file", "path": "a.txt", "content": "x"}]
    errs = bridge.validate(bad)
    assert "WORKER_SQL_BACKFILL_ACTIONS_FORBIDDEN" in errs
    assert "WORKER_SQL_BACKFILL_FORBIDDEN_FIELD:sql" in errs
    assert "WORKER_SQL_BACKFILL_CONFIRMATION_REQUIRED" in errs


class _FakeSqlCursor:
    def __init__(self, *, db_name: str = "EDARSAHUB"):
        self.db_name = db_name
        self.jobs: dict[str, tuple] = {}
        self.incidents: dict[str, tuple] = {}
        self.capabilities: dict[str, tuple] = {}
        self._last_rows: list[dict[str, Any]] = []
        self.exec_count = 0

    def execute(self, sql: str, params: tuple = ()):
        self.exec_count += 1
        up = " ".join(sql.split()).upper()
        if "SELECT @@SERVERNAME" in up:
            self._last_rows = [{
                "server_name": "ns559627",
                "db_name": self.db_name,
                "login_name": "HRLectura",
                "db_user": "HRLectura",
            }]
        elif "FROM SYS.TABLES" in up:
            self._last_rows = [
                {"table_name": "Sys_Worker_Jobs", "row_count": len(self.jobs)},
                {"table_name": "Sys_Worker_Incidents", "row_count": len(self.incidents)},
                {"table_name": "Sys_Worker_RecoveryEvents", "row_count": 0},
                {"table_name": "Sys_Worker_Capabilities", "row_count": len(self.capabilities)},
            ]
        elif "SP_WORKER_UPSERTJOBSTATE" in up:
            self.jobs[str(params[0])] = params
            self._last_rows = []
        elif "SP_WORKER_UPSERTINCIDENT" in up:
            self.incidents[str(params[0])] = params
            self._last_rows = []
        elif "SP_WORKER_UPSERTCAPABILITY" in up:
            self.capabilities[str(params[0])] = params
            self._last_rows = []
        else:
            raise AssertionError(f"Unexpected SQL in projection fake: {sql}")

    def fetchone(self):
        return self._last_rows[0] if self._last_rows else None

    def fetchall(self):
        return list(self._last_rows)


class _FakeSqlConn:
    def __init__(self, *, db_name: str = "EDARSAHUB"):
        self.cur = _FakeSqlCursor(db_name=db_name)
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self, as_dict: bool = False):
        return self.cur

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def test_worker_sql_projection_backfill_is_idempotent_batched_and_fail_closed(tmp_path):
    q = tmp_path / "queue"
    for d in ("results", "published", "preview_validations", "drafts", "maintenance/incidents"):
        (q / d).mkdir(parents=True, exist_ok=True)

    # 1. Valid certified job WITHOUT Preview evidence -> lifecycle CERTIFIED, preview_activated=0
    (q / "results" / "JOB-CERT-1.json").write_text(
        json.dumps(
            {
                "schema": "edarsahub.worker-result.v2",
                "job_id": "JOB-CERT-1",
                "status": "INTEGRATED",
                "quality_gate": "PASS",
                "tests": "PASS",
                "certification": "CERTIFIED",
                "percent_complete": 100,
                "blockers": [],
                "production_touched": False,
                "git_sync_status": "CERTIFIED_GIT_SYNC",
                "development_sha": "a" * 40,
                "completed_at_utc": "2026-11-20T16:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    # 2. Corrupt empty result -> counted in rejected_count
    (q / "results" / "JOB-EMPTY-2.json").write_bytes(b"")
    # 3. Orphan draft -> counted in inconsistent_count
    (q / "drafts" / "JOB-DRAFT-3.json").write_text(json.dumps({"job_id": "JOB-DRAFT-3", "objective": "draft"}), encoding="utf-8")
    # 4. Incident
    (q / "maintenance/incidents" / "INC-M1-1.json").write_text(
        json.dumps(
            {
                "incident_id": "INC-M1-1",
                "state": "CERTIFIED",
                "attempts": 1,
                "source_job_id": "JOB-CERT-1",
                "production_touched": False,
            }
        ),
        encoding="utf-8",
    )

    # Negativo 1: production_allowed=True -> bloqueado fail-closed
    with pytest.raises(proj.WorkerSqlProjectionError, match="PRODUCTION_FORBIDDEN"):
        proj.execute_backfill(confirm=True, production_allowed=True, queue_root=q, include_remote_git=False)

    # Negativo 2: DB_NAME() distinto a EDARSAHUB -> bloqueado fail-closed
    bad_conn = _FakeSqlConn(db_name="EDARSAHUB_PROD")
    with pytest.raises(proj.WorkerSqlProjectionError, match="UNEXPECTED_DATABASE_FORBIDDEN"):
        proj.execute_backfill(
            confirm=True,
            production_allowed=False,
            queue_root=q,
            include_remote_git=False,
            connection_factory=lambda: bad_conn,
        )
    assert bad_conn.closed is True
    assert bad_conn.cur.jobs == {}

    # Positivo: ejecucion por lotes + doble pasada idempotente (delta = 0)
    ok_conn = _FakeSqlConn(db_name="EDARSAHUB")
    res = proj.execute_backfill(
        confirm=True,
        production_allowed=False,
        batch_size=1,
        verify_idempotency=True,
        queue_root=q,
        include_remote_git=False,
        connection_factory=lambda: ok_conn,
    )
    assert res["status"] == "PASS"
    assert res["production_touched"] is False
    assert res["idempotency_verified"] is True
    assert all(v == 0 for v in res["idempotency_delta"].values())
    assert res["jobs_reconciled"] == 2
    assert res["rejected_count"] == 1
    assert res["inconsistent_count"] == 1
    assert res["incidents_reconciled"] == 1
    assert res["capabilities_reconciled"] >= 7
    assert ok_conn.commits >= 4
    assert ok_conn.closed is True
