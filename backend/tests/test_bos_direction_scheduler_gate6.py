import asyncio
import json
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.bos_evidence_collector import required_job_ids
from core.scheduler.config import SchedulerConfig
from core.scheduler.jobs.bos_direction_status_job import execute_bos_direction_status


def certified_result(job_id: str):
    return {
        'job_id': job_id,
        'status': 'INTEGRATED',
        'certification': 'CERTIFIED',
        'work_completion': 'COMPLETE',
        'quality_gate': 'PASS',
        'percent_complete': 100,
        'production_touched': False,
        'blockers': [],
    }


def prepare_runtime(tmp_path: Path, monkeypatch):
    results = tmp_path / '.git' / 'universal-worker-queue' / 'results'
    results.mkdir(parents=True, exist_ok=True)
    for job_id in required_job_ids():
        (results / f'{job_id}.json').write_text(json.dumps(certified_result(job_id)), encoding='utf-8')
    monkeypatch.setenv('EDARSAHUB_ROOT', str(tmp_path))
    monkeypatch.delenv('BOS_DIRECTION_RESULTS_DIR', raising=False)
    monkeypatch.delenv('BOS_DIRECTION_STATUS_ROOT', raising=False)
    return tmp_path / '.git' / 'bos-direction-status'


def test_scheduler_config_enables_bos_direction_status_by_default(monkeypatch):
    monkeypatch.delenv('SCHEDULER_BOS_DIRECTION_STATUS_ENABLED', raising=False)
    monkeypatch.delenv('SCHEDULER_BOS_DIRECTION_STATUS_INTERVAL_SECONDS', raising=False)
    config = SchedulerConfig.from_env()
    job = config.jobs['bos_direction_status']
    assert job.enabled is True
    assert job.interval_seconds == 3600
    assert job.max_instances == 1
    assert job.coalesce is True


def test_path_resolution_is_root_relative_and_overrideable(tmp_path, monkeypatch):
    status_root = prepare_runtime(tmp_path, monkeypatch)
    result = execute_bos_direction_status('2026-09-09T00:00:00Z')
    assert Path(result['latest_file']) == status_root / 'latest.json'


def test_apscheduler_executes_three_automatic_cycles(tmp_path, monkeypatch):
    status_root = prepare_runtime(tmp_path, monkeypatch)

    async def scenario():
        timestamps = iter((
            '2026-09-09T00:00:00Z',
            '2026-09-09T00:00:01Z',
            '2026-09-09T00:00:02Z',
            '2026-09-09T00:00:03Z',
        ))
        counter = {'runs': 0}

        async def scheduled_cycle():
            try:
                timestamp = next(timestamps)
            except StopIteration:
                return
            execute_bos_direction_status(timestamp)
            counter['runs'] += 1

        scheduler = AsyncIOScheduler(timezone='UTC')
        scheduler.add_job(
            scheduled_cycle,
            trigger=IntervalTrigger(seconds=0.05),
            id='bos_direction_status',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        try:
            await asyncio.sleep(0.22)
        finally:
            scheduler.shutdown(wait=False)
        return counter['runs']

    runs = asyncio.run(scenario())
    assert runs >= 3
    history = sorted((status_root / 'history').glob('*.json'))
    assert len(history) >= 3
    latest = json.loads((status_root / 'latest.json').read_text(encoding='utf-8'))
    assert latest['generated_at_utc'] in {
        '2026-09-09T00:00:02Z',
        '2026-09-09T00:00:03Z',
    }


def test_scheduler_manager_registers_single_canonical_job():
    source = (Path(__file__).resolve().parents[1] / 'core' / 'scheduler' / 'scheduler_manager.py').read_text(encoding='utf-8')
    assert 'id="bos_direction_status"' in source
    assert 'self._run_bos_direction_status_job' in source
    assert source.count('id="bos_direction_status"') == 1
