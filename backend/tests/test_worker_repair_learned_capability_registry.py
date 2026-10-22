from __future__ import annotations

from types import SimpleNamespace

import pytest

from tools.mirror_sync import worker_repair_capability_registry as registry


def incident(paths=None):
    return SimpleNamespace(
        incident_id=(
            "EDARSAHUB-BOS-WORKER-MUTATION-LIFECYCLE-"
            "STALE-OWNERSHIP-R1"
        ),
        target_paths=tuple(
            paths
            or (
                "tools/mirror_sync/worker_control_plane.py",
                "backend/tests/test_worker_universal_queue_sla_contract.py",
                "backend/tests/test_worker_control_plane_contract.py",
            )
        ),
    )


def payload():
    return {
        "schema": registry.SCHEMA,
        "code": "MUTATION_LIFECYCLE_STALE_OWNERSHIP",
        "problem_signature": (
            "PROCESSING_STALE_WITH_LIVE_EXECUTION_OWNERSHIP"
        ),
        "incident_ids": [
            incident().incident_id,
        ],
        "incident_patterns": [
            "EDARSAHUB-BOS-WORKER-MUTATION-LIFECYCLE-*",
        ],
        "required_paths": list(incident().target_paths),
        "objective": (
            "Prevent stale requeue or terminalization while the same "
            "job still has live canonical execution ownership."
        ),
        "actions": [
            {
                "type": "replace_text",
                "path": "tools/mirror_sync/worker_control_plane.py",
                "old": "old-anchor",
                "new": "new-anchor",
                "expected_count": 1,
            },
        ],
        "checks": [
            {
                "type": "py_compile",
                "paths": [
                    "tools/mirror_sync/worker_control_plane.py",
                ],
            },
            {
                "type": "pytest",
                "paths": [
                    "backend/tests/test_worker_universal_queue_sla_contract.py",
                    "backend/tests/test_worker_control_plane_contract.py",
                ],
            },
            {"type": "git_diff_check"},
        ],
        "evidence": {
            "source_job_id": (
                "EDARSAHUB-BOS-CONEXIONES-COMUNICACIONES-"
                "SERVIDORES-CANONICAL-INVENTORY-UI-FIX-R1-20261022"
            ),
            "blocker_signature": (
                "processing_stale_after_single_requeue"
            ),
        },
        "learned_from_incident": incident().incident_id,
        "reusable": True,
        "production_allowed": False,
    }


def test_register_and_reuse_by_signature(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "REGISTRY_DIR", tmp_path)

    result = registry.register_learned_capability(
        payload(),
        incident=incident(),
    )

    assert result["status"] == "REGISTERED"
    assert result["production_touched"] is False

    learned = registry.resolve_learned_capability(
        incident_id="FUTURE-UNSEEN-INCIDENT",
        problem_signature=(
            "PROCESSING_STALE_WITH_LIVE_EXECUTION_OWNERSHIP"
        ),
    )

    assert learned is not None
    assert learned.code == "MUTATION_LIFECYCLE_STALE_OWNERSHIP"


def test_scope_escape_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "REGISTRY_DIR", tmp_path)
    value = payload()
    value["required_paths"].append("frontend/src/App.jsx")
    value["actions"][0]["path"] = "frontend/src/App.jsx"

    with pytest.raises(
        ValueError,
        match="LEARNED_CAPABILITY_SCOPE_NOT_AUTHORIZED",
    ):
        registry.register_learned_capability(
            value,
            incident=incident(),
        )


def test_shell_sql_and_production_are_forbidden():
    value = payload()
    value["actions"][0]["shell"] = "rm -rf /"

    with pytest.raises(
        ValueError,
        match="LEARNED_CAPABILITY_FORBIDDEN_RECIPE_KEY:shell",
    ):
        registry.normalize_learned_capability(value)

    value = payload()
    value["production_allowed"] = True

    with pytest.raises(
        ValueError,
        match="LEARNED_CAPABILITY_PRODUCTION_FORBIDDEN",
    ):
        registry.normalize_learned_capability(value)


def test_unknown_without_registry_remains_unknown(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "REGISTRY_DIR", tmp_path)

    assert registry.resolve_learned_capability(
        incident_id="UNKNOWN",
        problem_signature="UNKNOWN_SIGNATURE",
    ) is None


def test_registration_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "REGISTRY_DIR", tmp_path)

    first = registry.register_learned_capability(
        payload(),
        incident=incident(),
    )
    second = registry.register_learned_capability(
        payload(),
        incident=incident(),
    )

    assert first["status"] == "REGISTERED"
    assert second["status"] == "ALREADY_REGISTERED"
