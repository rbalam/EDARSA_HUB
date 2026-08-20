from pathlib import Path
import ast


ROUTES = Path(
    "/app/backend/core/scheduler/routes.py"
)


def _source():
    return ROUTES.read_text(
        encoding="utf-8",
        errors="strict",
    )


def test_scheduler_routes_compile_as_python():
    ast.parse(_source())


def test_scheduler_imports_dual_explicit_permission():
    text = _source()

    assert (
        "require_explicit_permission_dual"
        in text
    )


def test_scheduler_does_not_use_header_only_explicit_dependency():
    text = _source()

    assert 'require_explicit_permission("' not in text


def test_scheduler_admin_mutations_use_dual_auth():
    text = _source()

    assert text.count(
        'require_explicit_permission_dual("SCHEDULER_ADMIN")'
    ) == 3


def test_scheduler_manage_mutations_use_dual_auth():
    text = _source()

    assert text.count(
        'require_explicit_permission_dual("SCHEDULER_GESTIONAR")'
    ) == 2


def test_read_endpoints_keep_existing_permission_contract():
    text = _source()

    assert (
        'require_permission("SCHEDULER_VER")'
        in text
    )


def test_exact_mutating_routes_remain_present():
    text = _source()

    expected = (
        '@router.post("/jobs/{job_id}/run")',
        '@router.post("/netpay/run")',
        '@router.post("/jobs/{job_id}/pause")',
        '@router.post("/jobs/{job_id}/resume")',
        '@router.delete("/locks/{job_name}")',
    )

    for route in expected:
        assert route in text
