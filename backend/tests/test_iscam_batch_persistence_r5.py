from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend' / 'api' / 'admin_scheduler_resync.py'


def _create_block():
    text = BACKEND.read_text(encoding='utf-8')
    return text.split('def _iscam_batch_create(', 1)[1].split('def _iscam_batch_day_outcome', 1)[0]


def test_batch_job_insert_is_committed_before_returning_job_id():
    block = _create_block()
    assert 'conn = get_sql_connection()' in block
    assert 'OUTPUT INSERTED.ResyncLogID AS job_id' in block
    assert 'row = cursor.fetchone()' in block
    assert "payload['job_id'] = int(row['job_id'])" in block
    assert 'conn.commit()' in block
    assert block.index('conn.commit()') < block.index('return payload')


def test_batch_job_insert_rolls_back_and_closes_on_failure():
    block = _create_block()
    assert 'conn.rollback()' in block
    assert 'cursor.close()' in block
    assert 'conn.close()' in block


def test_batch_job_create_no_longer_uses_fetch_without_commit_helper():
    block = _create_block()
    assert '_execute_edarsahub_query(' not in block
