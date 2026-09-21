from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "tools/mirror_sync/worker_slot_runtime.py"


def text() -> str:
    return TARGET.read_text(encoding="utf-8")


def test_slot_runtime_schema_and_allowlist():
    value = text()
    assert "edarsahub.worker-slot-runtime.v1" in value
    for slot_id in (
        "readonly-1",
        "readonly-2",
        "readonly-3",
        "readonly-4",
        "mutation-1",
    ):
        assert slot_id in value


def test_gate4b1_effective_capacity_remains_serial_per_class():
    value = text()
    assert '"readonly-1"' in value
    assert '"mutation-1"' in value
    assert '"readonly_slots_capacity": 1' in value
    assert '"mutation_slots_capacity": 1' in value


def test_slot_runtime_is_fail_closed_and_atomic():
    value = text()
    assert "CORRUPT_SLOT_RUNTIME" in value
    assert "LEGACY_CURRENT_JOB_PROJECTION_CONFLICT" in value
    assert "tempfile.NamedTemporaryFile" in value
    assert "handle.flush()" in value
    assert "os.fsync" in value
    assert "os.replace" in value


def test_slot_runtime_has_no_git_sql_or_shell():
    value = text()
    assert "subprocess" not in value
    assert "git(" not in value
    assert "sql" not in value.lower()
    assert "shell=True" not in value
