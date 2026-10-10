from __future__ import annotations

from types import SimpleNamespace

import pytest

from tools.mirror_sync import worker_repair_planner as planner


def test_unknown_capability_fails_closed(
    monkeypatch,
):
    monkeypatch.setattr(
        planner.maintenance,
        "read_runtime_incident",
        lambda _incident_id: (
            SimpleNamespace(
                incident_id="UNKNOWN",
                state="REPAIR_REQUIRED",
                attempts=0,
                repair_job_id=None,
                target_paths=(
                    "tools/mirror_sync/"
                    "worker_repair.py",
                ),
            )
        ),
    )

    monkeypatch.setattr(
        planner,
        "convergence_state",
        lambda: {
            "local": "a" * 40,
            "development": "a" * 40,
            "mirror": "a" * 40,
            "converged": True,
        },
    )

    with pytest.raises(
        ValueError,
        match="REPAIR_CAPABILITY_UNKNOWN",
    ):
        planner.build_deterministic_repair_job(
            "UNKNOWN"
        )


def test_scope_escape_is_rejected():
    incident = SimpleNamespace(
        target_paths=(
            "tools/mirror_sync/"
            "worker_repair.py",
        )
    )

    capability = (
        planner.RepairCapability(
            code="TEST",
            incident_ids=(
                "TEST",
            ),
            required_paths=(
                "tools/mirror_sync/"
                "worker_repair.py",
            ),
            builder=lambda i, c: {},
        )
    )

    with pytest.raises(
        ValueError,
        match="REPAIR_ACTION_SCOPE_MISMATCH",
    ):
        planner._validate_scope(
            incident,
            capability,
            [
                {
                    "type": "write_file",
                    "path": (
                        "frontend/src/App.jsx"
                    ),
                    "content": "x",
                }
            ],
        )


def test_duplicate_capability_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        planner,
        "_CAPABILITIES",
        {},
    )

    capability = (
        planner.RepairCapability(
            code="TEST",
            incident_ids=(
                "TEST",
            ),
            required_paths=(
                "tools/mirror_sync/"
                "worker_repair.py",
            ),
            builder=lambda i, c: {},
        )
    )

    planner.register_capability(
        capability
    )

    with pytest.raises(
        ValueError,
        match="REPAIR_CAPABILITY_DUPLICATE",
    ):
        planner.register_capability(
            capability
        )


def test_persistent_specs_never_use_tmp():
    assert "/tmp" not in str(
        planner.REPAIR_SPECS
    )


def test_planner_has_no_direct_push_or_audit():
    source = planner.Path(
        planner.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "authorized_push(" not in source
    assert "git push" not in source
    assert "audit_runtime_incident(" not in source
    assert "shell=True" not in source


def test_job_identity_uses_canonical_repair_identity():
    first = (
        planner.deterministic_repair_job_id(
            "INCIDENT-X",
            1,
        )
    )

    second = (
        planner.deterministic_repair_job_id(
            "INCIDENT-X",
            1,
        )
    )

    assert first == second
    assert first.startswith(
        "WORKER-REPAIR-"
    )


def test_required_scope_must_be_authorized():
    incident = SimpleNamespace(
        target_paths=(
            "tools/mirror_sync/"
            "worker_repair.py",
        )
    )

    capability = (
        planner.RepairCapability(
            code="TEST",
            incident_ids=("TEST",),
            required_paths=(
                "tools/mirror_sync/"
                "worker_control_plane.py",
            ),
            builder=lambda i, c: {},
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "REPAIR_CAPABILITY_"
            "SCOPE_NOT_AUTHORIZED"
        ),
    ):
        planner._validate_scope(
            incident,
            capability,
            [
                {
                    "type": "write_file",
                    "path": (
                        "tools/mirror_sync/"
                        "worker_repair.py"
                    ),
                    "content": "x",
                }
            ],
        )
