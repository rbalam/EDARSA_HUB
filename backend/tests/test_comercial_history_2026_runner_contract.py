from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "backend" / "scripts" / "run_comercial_history_2026.py"


def text():
    return RUNNER.read_text(encoding="utf-8")


def test_reuses_certified_entrypoint_and_same_lock():
    body = text()
    assert 'with_name("resync_comercial_range_worker.py")' in body
    assert 'LOCK_NAME = "sync_comercial_v2"' in body
    assert "start_heartbeat_loop" in body
    assert "await lock.release()" in body
    assert "force_release" not in body


def test_checkpoint_log_and_sha_guard_are_external_and_persistent():
    body = text()
    assert "/var/lib/edarsahub-bootstrap/comercial-history-2026/state.json" in body
    assert "/var/log/edarsahub/comercial-history-2026.log" in body
    assert "HISTORY_WORKTREE_SHA_MISMATCH" in body
    assert "STATE_CODE_SHA_MISMATCH" in body


def test_starts_at_september_11_and_never_reprocesses_sep_01_10():
    body = text()
    assert "date(2026, 9, 11), date(2026, 9, 15)" in body
    assert "date(2026, 9, 16), date(2026, 9, 20)" in body
    assert "date(2026, 9, 21), date(2026, 9, 25)" in body
    assert "date(2026, 9, 26), date(2026, 9, 30)" in body
    assert "date(2026, 9, 1)" not in body
    assert "date(2026, 9, 6)" not in body


def test_five_units_retry_limit_and_130qro_june_guard():
    body = text()
    assert 'UNITS = ("ESTELAR", "CIENFUEGOS", "130MID", "ORIGEN", "130QRO")' in body
    assert 'choices=(1, 2, 3)' in body
    assert "PENDING_RECOVERY" in body
    assert "130QRO_JUNE_2026_REQUIRES_ISOLATED_AUDIT_KNOWN_17_DAY_DIFFERENCE" in body


def test_low_priority_yield_and_no_open_sales_touch():
    body = text()
    assert 'default=120' in body
    assert "sync_comercial_abiertas_v2" not in body
