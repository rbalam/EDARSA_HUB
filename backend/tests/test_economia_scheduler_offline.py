import ast
from pathlib import Path

from core.scheduler.config import SchedulerConfig


ROOT = Path(__file__).resolve().parents[1]
MANAGER = ROOT / "core" / "scheduler" / "scheduler_manager.py"


def _manager_source():
    return MANAGER.read_text(
        encoding="utf-8",
        errors="replace",
    )


def test_economia_scheduler_desactivado_por_default(monkeypatch):
    monkeypatch.delenv(
        "SCHEDULER_ECONOMIA_SYNC_ENABLED",
        raising=False,
    )
    monkeypatch.delenv(
        "SCHEDULER_ECONOMIA_SYNC_INTERVAL_SECONDS",
        raising=False,
    )

    config = SchedulerConfig.from_env()
    job = config.jobs["economia_sync"]

    assert job.enabled is False
    assert job.interval_seconds == 86400
    assert job.job_id == "economia_sync"


def test_economia_scheduler_tiene_registro_y_run_now():
    source = _manager_source()

    assert 'self.config.jobs.get("economia_sync")' in source
    assert 'id="economia_sync"' in source
    assert 'elif job_id == "economia_sync":' in source
    assert "await self._run_economia_sync_job()" in source


def test_economia_scheduler_wrapper_fail_closed():
    source = _manager_source()

    start = source.index(
        "async def _run_economia_sync_job"
    )
    end = source.index(
        "async def _run_inteligencia_comercial_sync_job",
        start,
    )

    block = source[start:end]

    assert 'self.config.jobs.get("economia_sync")' in block
    assert "if not job_config or not job_config.enabled:" in block

    disabled_pos = block.index(
        "if not job_config or not job_config.enabled:"
    )
    lock_pos = block.index("get_lock_manager(")

    assert disabled_pos < lock_pos


def test_economia_scheduler_no_hardcodea_series():
    source = _manager_source()

    start = source.index(
        "async def _run_economia_sync_job"
    )
    end = source.index(
        "async def _run_inteligencia_comercial_sync_job",
        start,
    )

    block = source[start:end]

    assert "EconomiaService.listar_series" in block
    assert "activo=True" in block
    assert "EconomiaService.sincronizar_serie" in block

    assert "Economia_Series" not in block
    assert "BANXICO" not in block.upper()
    assert "INEGI" not in block.upper()


def test_scheduler_manager_sintaxis_ast_valida():
    tree = ast.parse(_manager_source())

    methods = {
        node.name
        for node in ast.walk(tree)
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    }

    assert "_run_economia_sync_job" in methods
    assert "register_jobs" in methods
    assert "run_job_now" in methods
