from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEALTH = ROOT / "tools" / "mirror_sync" / "runtime_health_publisher.py"


def test_operational_jobs_have_longer_stale_threshold():
    text = HEALTH.read_text(encoding="utf-8")
    assert 'EDARSAHUB_OPERATIONAL_JOB_STALE_SECONDS' in text
    assert '21600' in text
    assert 'SOFTRESTAURANT_FULL_HISTORY_RESYNC' in text
    assert 'ISCAM_DETAIL_BACKFILL' in text
    assert 'processing_stale_seconds(path)' in text
    assert 'age >= stale_seconds' in text


def test_default_stale_threshold_remains_for_normal_jobs():
    text = HEALTH.read_text(encoding="utf-8")
    assert 'EDARSAHUB_JOB_STALE_SECONDS' in text
    assert '"180"' in text
    assert 'else STALE_SECONDS' in text
