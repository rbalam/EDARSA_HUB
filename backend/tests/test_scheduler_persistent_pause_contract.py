from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MANAGER = ROOT / "core/scheduler/scheduler_manager.py"

REPOSITORY = (
    ROOT
    / "core/scheduler/persistent_state_repository.py"
)

MIGRATION = (
    ROOT
    / "database/migrations/"
    "20260818_031_scheduler_persistent_pause.sql"
)

ROLLBACK = (
    ROOT
    / "database/rollback/"
    "20260818_031_scheduler_persistent_pause_rollback.sql"
)


def test_repository_uses_canonical_edarsahub_connection():
    text = REPOSITORY.read_text(
        encoding="utf-8"
    )

    assert (
        "from core.config.edarsahub_sql import "
        "get_edarsahub_connection"
    ) in text

    assert "pymssql.connect" not in text
    assert "from pymongo" not in text.lower()
    assert "import pymongo" not in text.lower()
    assert "mongo_client" not in text.lower()
    assert "get_stub_database" not in text


def test_repository_uses_dedicated_runtime_state_only():
    text = REPOSITORY.read_text(
        encoding="utf-8"
    )

    executable = text.lower()

    assert "Sys_Scheduler_RuntimeState" in text

    assert "from sys_scheduler_jobs" not in executable
    assert "join dbo.sys_scheduler_jobs" not in executable
    assert "update dbo.sys_scheduler_jobs" not in executable
    assert "insert into dbo.sys_scheduler_jobs" not in executable
    assert "delete from dbo.sys_scheduler_jobs" not in executable
    assert "select * from dbo.sys_scheduler_jobs" not in executable

    assert "CronExpression" not in text
    assert "JobType" not in text
    assert "SET Status" not in text


def test_repository_uses_controlled_write_procedure_only():
    text = REPOSITORY.read_text(
        encoding="utf-8"
    )

    assert (
        "EXEC dbo.sp_Scheduler_SetAdministrativePause"
        in text
    )

    assert "UPDATE dbo.Sys_Scheduler_RuntimeState" not in text

    assert "INSERT INTO dbo.Sys_Scheduler_RuntimeState" not in text


def test_manager_pause_resume_use_persistent_repository():
    text = MANAGER.read_text(
        encoding="utf-8"
    )

    assert (
        "SchedulerPersistentStateRepository.set_paused"
        in text
    )

    assert "self._scheduler.pause_job(job_id)" in text
    assert "self._scheduler.resume_job(job_id)" in text


def test_migration_creates_only_runtime_state_table():
    text = MIGRATION.read_text(
        encoding="utf-8"
    )

    assert (
        "CREATE TABLE dbo.Sys_Scheduler_RuntimeState"
        in text
    )

    assert "PausadoAdministrativo" in text

    assert (
        "ALTER TABLE dbo.Sys_Scheduler_Jobs"
        not in text
    )

    assert (
        "CREATE TABLE dbo.Sys_Scheduler_Jobs"
        not in text
    )


def test_runtime_state_has_no_fk_to_legacy_catalog():
    text = MIGRATION.read_text(
        encoding="utf-8"
    )

    assert "FOREIGN KEY" not in text.upper()

    assert "Sys_Scheduler_Jobs(" not in text


def test_rollback_only_drops_runtime_state():
    text = ROLLBACK.read_text(
        encoding="utf-8"
    )

    assert (
        "DROP TABLE dbo.Sys_Scheduler_RuntimeState"
        in text
    )

    assert "Sys_Scheduler_Jobs" not in text


def test_startup_restore_is_now_part_of_final_contract():
    text = MANAGER.read_text(
        encoding="utf-8"
    )

    register_pos = text.find(
        "self.register_jobs()"
    )

    persistent_read_pos = text.find(
        "SchedulerPersistentStateRepository."
        "get_paused_job_ids()"
    )

    runtime_pause_pos = text.find(
        "self._scheduler.pause_job(job_id)"
    )

    scheduler_start_pos = text.find(
        "self._scheduler.start()"
    )

    assert register_pos >= 0
    assert persistent_read_pos > register_pos
    assert runtime_pause_pos > persistent_read_pos
    assert scheduler_start_pos > runtime_pause_pos


def test_migration_exposes_narrow_scheduler_write_interface():
    text = MIGRATION.read_text(
        encoding="utf-8"
    )

    assert (
        "CREATE OR ALTER PROCEDURE "
        "dbo.sp_Scheduler_SetAdministrativePause"
        in text
    )

    assert (
        "GRANT EXECUTE"
        in text
    )

    assert (
        "ON OBJECT::dbo.sp_Scheduler_SetAdministrativePause"
        in text
    )

    assert (
        "TO HRLectura"
        in text
    )


def test_backend_does_not_require_general_table_write_for_pause():
    text = REPOSITORY.read_text(
        encoding="utf-8"
    ).upper()

    assert "INSERT INTO" not in text
    assert "UPDATE DBO." not in text
    assert "DELETE FROM" not in text
    assert (
        "EXEC DBO.SP_SCHEDULER_SETADMINISTRATIVEPAUSE"
        in text
    )
