from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]

CONTROL = ROOT / "tools" / "mirror_sync" / "worker_control_plane.py"


def source():
    return CONTROL.read_text(encoding="utf-8")


def function_source(name: str) -> str:
    text = source()
    tree = ast.parse(text)

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            lines = text.splitlines()
            return "\n".join(
                lines[node.lineno - 1 : node.end_lineno]
            )

    raise AssertionError(f"missing function: {name}")


def test_automatic_repair_is_part_of_existing_control_plane():
    text = source()

    assert "def automatic_repair_orchestration(" in text
    assert '"automatic_repair": automatic_repair' in text
    assert "automatic_repair_orchestration()" in function_source("cycle")


def test_gate5l_readonly_summary_boundary_remains_intact():
    helper = function_source("maintenance_runtime_summary")

    assert "declare_runtime_incident(" not in helper
    assert "register_repair_attempt(" not in helper
    assert "register_repair_result(" not in helper
    assert "audit_runtime_incident(" not in helper


def test_automatic_repair_uses_existing_maintenance_runtime():
    helper = function_source("automatic_repair_orchestration")

    assert "declare_runtime_incident(" in helper
    assert "repair_attempt_allowed(" in helper

    assert "register_repair_attempt(" not in helper
    assert "register_repair_result(" not in helper
    assert "audit_runtime_incident(" not in helper


def test_automatic_repair_does_not_create_second_dispatcher_or_queue():
    helper = function_source("automatic_repair_orchestration")

    assert "universal_job_dispatcher" not in helper
    assert "dispatch(" not in helper
    assert "subprocess" not in helper
    assert "os.system" not in helper
    assert "shell=True" not in helper
    assert "worker/requests" not in helper


def test_automatic_repair_is_worker_infrastructure_only():
    helper = function_source("automatic_repair_orchestration")

    assert '"tools/mirror_sync/"' in helper
    assert '"backend/tests/test_worker_"' in helper
    assert "frontend/" not in helper
    assert "backend/modules/comercial/" not in helper
    assert "backend/modules/finanzas/" not in helper


def test_automatic_repair_is_fail_closed_for_production():
    helper = function_source("automatic_repair_orchestration")

    assert 'production_touched") is not False' in helper
    assert '"production_touched": False' in helper
    assert "Edarsahub_Produccion" not in helper


def test_incident_identity_is_deterministic_and_scope_bound():
    helper = function_source("automatic_repair_orchestration")

    assert "hashlib.sha256" in helper
    assert "source_job_id" in helper
    assert "status" in helper
    assert "target_paths" in helper


def test_detection_cycle_does_not_execute_or_certify_repair():
    helper = function_source("automatic_repair_orchestration")

    assert '"publication_required": allowed' in helper
    assert "CERTIFIED_WORKER_REPAIR" not in helper
    assert "REPAIRED_PENDING_AUDIT" not in helper

def test_automatic_repair_supports_supersession_before_publication():
    text = source()

    assert "def repair_incident_is_superseded(" in text

    helper = function_source("automatic_repair_orchestration")

    assert "repair_incident_is_superseded(" in helper
    assert "supersede_runtime_incident(" in helper
    assert '"publication_required": False' in helper
    assert '"repair_allowed": False' in helper

def test_automatic_repair_loads_result_corpus_once_per_cycle():
    helper = function_source(
        "automatic_repair_orchestration"
    )

    assert (
        helper.count(
            'results_root.glob("*.json")'
        )
        == 1
    )
    assert "result_corpus" in helper
    assert "result_corpus_tuple" in helper


def test_certified_successor_fallback_is_canonical():
    text = source()

    assert "def automatic_repair_source_anchor(" in text
    assert "def find_certified_successor_result(" in text
    assert (
        "CERTIFIED_SUCCESSOR_RESULT"
        in text
    )

    helper = function_source(
        "automatic_repair_orchestration"
    )

    assert (
        "result_corpus=result_corpus_tuple"
        in helper
    )

def test_git_lock_busy_is_a_repairable_worker_incident():
    text = source()
    helper = function_source("automatic_repair_orchestration")

    assert '"GIT_LOCK_BUSY"' in helper
    assert "GIT_LOCK_BUSY_REPAIR_PATHS" in helper
    assert (
        '"tools/mirror_sync/git_divergence_guard.py"'
        in text
    )
    assert (
        '"tools/mirror_sync/universal_job_dispatcher.py"'
        in text
    )
