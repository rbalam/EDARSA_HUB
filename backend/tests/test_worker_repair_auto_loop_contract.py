from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CONTROL = ROOT / "tools/mirror_sync/worker_control_plane.py"
PLANNER = ROOT / "tools/mirror_sync/worker_repair_planner.py"
AUTO = ROOT / "tools/mirror_sync/worker_repair_auto_loop.py"


def test_control_plane_advances_repairs_outside_detector():
    text = CONTROL.read_text(encoding="utf-8")

    assert "automatic_repair = automatic_repair_orchestration()" in text
    assert (
        "automatic_repair_execution = advance_repair_automation("
        in text
    )
    assert '"automatic_repair_execution": automatic_repair_execution' in text


def test_detector_boundary_remains_separate():
    text = CONTROL.read_text(encoding="utf-8")

    start = text.index("def automatic_repair_orchestration(")
    end = text.index("def maintenance_runtime_summary(", start)

    helper = text[start:end]

    assert "publish_planned_repair(" not in helper
    assert "reconcile_repair_result(" not in helper
    assert "CERTIFIED_WORKER_REPAIR" not in helper


def test_auto_loop_only_orchestrates_existing_components():
    text = AUTO.read_text(encoding="utf-8")

    assert "planner.publish_planned_repair(" in text
    assert "execution.reconcile_repair_result(" in text
    assert "execution.read_repair_terminal_result(" in text
    assert "maintenance.audit_runtime_incident(" in text
    assert "ensure_submit_convergence(" in text
    assert "resolve_learned_capability(" in text

    assert "subprocess" not in text
    assert "shell=True" not in text
    assert "universal_job_dispatcher" not in text
    assert "worker/requests" not in text


def test_auto_loop_requires_certified_result_before_audit():
    text = AUTO.read_text(encoding="utf-8")

    assert 'certification != "CERTIFIED"' in text
    assert "WAIT_RESULT_CERTIFICATION" in text


def test_planner_uses_safe_convergence():
    text = PLANNER.read_text(encoding="utf-8")

    assert "ensure_submit_convergence" in text
    assert 'owner="worker-repair-planner"' in text
    assert "DEV_MIRROR_NOT_CONVERGED:" in text


def test_planner_accepts_inherited_requester():
    text = PLANNER.read_text(encoding="utf-8")

    assert "requester: dict[str, Any] | None = None" in text
    assert "_canonical_requester(requester)" in text


def test_production_remains_forbidden():
    control = CONTROL.read_text(encoding="utf-8")
    auto = AUTO.read_text(encoding="utf-8")

    assert '"production_touched": False' in control
    assert '"production_touched": False' in auto
    assert "Edarsahub_Produccion" not in auto
