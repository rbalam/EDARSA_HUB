from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "tools" / "mirror_sync" / "worker_runtime_fingerprint.py"
HEALTH = ROOT / "tools" / "mirror_sync" / "runtime_health_publisher.py"


def load_module():
    spec = spec_from_file_location("worker_runtime_fingerprint", TARGET)
    assert spec and spec.loader
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_runtime_fingerprint_contract_is_read_only_and_fail_closed():
    text = TARGET.read_text(encoding="utf-8")
    assert "edarsahub.worker-runtime-fingerprint.v1" in text
    assert "RuntimeFingerprintError" in text
    assert "RUNTIME_FINGERPRINT_WRONG_BRANCH" in text
    assert "RUNTIME_FINGERPRINT_HEAD_INVALID" in text
    assert "RUNTIME_FINGERPRINT_WORKER_TREE_INVALID" in text
    assert '"production_touched": False' in text
    assert "supervisorctl" not in text
    assert "pymssql" not in text
    assert "sql" not in text.lower()
    assert "mongo" not in text.lower()


def test_required_capabilities_are_canonical_and_explicit():
    mod = load_module()
    assert mod.REQUIRED_CAPABILITIES == (
        "canonical_git_guard_refresh",
        "runtime_code_tree_identity",
        "runtime_generation_identity",
        "worker_heartbeat",
        "startup_selfheal",
        "wake_proof",
        "production_fail_closed",
    )


def test_health_publisher_surfaces_canonical_fingerprint():
    text = HEALTH.read_text(encoding="utf-8")
    assert "worker_runtime_fingerprint.py" in text
    assert '"runtime_fingerprint"' in text
    assert "RUNTIME_FINGERPRINT_UNAVAILABLE" in text
