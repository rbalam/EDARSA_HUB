from __future__ import annotations

from types import SimpleNamespace

import json
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
    registry_dir = tmp_path / "registry"
    seed_dir = tmp_path / "seed"

    monkeypatch.setattr(registry, "REGISTRY_DIR", registry_dir)
    monkeypatch.setattr(registry, "SEED_DIR", seed_dir)

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


def test_seed_registry_payload_conflict_fails_closed(
    tmp_path,
    monkeypatch,
):
    registry_dir = tmp_path / "registry"
    seed_dir = tmp_path / "seed"

    monkeypatch.setattr(
        registry,
        "REGISTRY_DIR",
        registry_dir,
    )
    monkeypatch.setattr(
        registry,
        "SEED_DIR",
        seed_dir,
    )

    result = registry.register_learned_capability(
        payload(),
        incident=incident(),
    )

    assert result["status"] == "REGISTERED"

    seed_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    conflicting = payload()
    conflicting["objective"] = (
        "Conflicting seed payload must fail closed."
    )

    (
        seed_dir
        / "MUTATION_LIFECYCLE_STALE_OWNERSHIP.json"
    ).write_text(
        json.dumps(
            conflicting,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="LEARNED_CAPABILITY_REGISTRY_CONFLICT",
    ):
        registry.iter_learned_capabilities()


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


def test_uncertified_evidence_or_incident_fails_closed(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(registry, "REGISTRY_DIR", tmp_path)

    uncertified_evidence = payload()
    uncertified_evidence["evidence"]["certified"] = False

    with pytest.raises(
        ValueError,
        match="LEARNED_CAPABILITY_EVIDENCE_NOT_CERTIFIED",
    ):
        registry.register_learned_capability(
            uncertified_evidence,
            incident=incident(),
        )

    pending_incident = incident()
    pending_incident.state = "REPAIRED_PENDING_AUDIT"

    with pytest.raises(
        ValueError,
        match="LEARNED_CAPABILITY_INCIDENT_NOT_CERTIFIED",
    ):
        registry.register_learned_capability(
            payload(),
            incident=pending_incident,
        )

    unverified_incident = incident()
    unverified_incident.state = "REPAIR_REQUIRED"

    with pytest.raises(
        ValueError,
        match="LEARNED_CAPABILITY_INCIDENT_NOT_CERTIFIED",
    ):
        registry.register_learned_capability(
            payload(),
            incident=unverified_incident,
            require_certified_incident=True,
        )

    certified_incident = incident()
    certified_incident.state = "CERTIFIED"
    certified_incident.production_touched = False

    registered = registry.register_learned_capability(
        payload(),
        incident=certified_incident,
        require_certified_incident=True,
    )
    assert registered["status"] == "REGISTERED"


def test_exact_incident_precedence_and_certified_supersession(
    tmp_path,
    monkeypatch,
):
    registry_dir = tmp_path / "registry"
    seed_dir = tmp_path / "seed"
    monkeypatch.setattr(registry, "REGISTRY_DIR", registry_dir)
    monkeypatch.setattr(registry, "SEED_DIR", seed_dir)

    base_cap = payload()
    registry.register_learned_capability(
        base_cap,
        incident=incident(),
    )

    successor_inc = SimpleNamespace(
        incident_id=(
            "EDARSAHUB-BOS-WORKER-MUTATION-LIFECYCLE-"
            "SLOT-HEARTBEAT-GAP-R2"
        ),
        target_paths=(
            "tools/mirror_sync/universal_job_dispatcher.py",
            "backend/tests/test_worker_universal_queue_sla_contract.py",
        ),
        state="CERTIFIED",
        production_touched=False,
    )
    successor_cap = payload()
    successor_cap["code"] = (
        "MUTATION_LIFECYCLE_SLOT_HEARTBEAT_V2"
    )
    successor_cap["problem_signature"] = (
        "PROCESSING_STALE_DURING_LONG_RUNNING_PYTEST_WITHOUT_SLOT_HEARTBEAT"
    )
    successor_cap["incident_ids"] = [
        successor_inc.incident_id,
    ]
    successor_cap["incident_patterns"] = [
        "EDARSAHUB-BOS-WORKER-MUTATION-LIFECYCLE-SLOT-HEARTBEAT-*",
    ]
    successor_cap["required_paths"] = list(
        successor_inc.target_paths
    )
    successor_cap["actions"] = [
        {
            "type": "replace_text",
            "path": (
                "tools/mirror_sync/universal_job_dispatcher.py"
            ),
            "old": "old-dispatcher",
            "new": "new-dispatcher",
            "expected_count": 1,
        }
    ]
    successor_cap["learned_from_incident"] = (
        successor_inc.incident_id
    )
    successor_cap["evidence"] = {
        "source_job_id": (
            "EDARSAHUB-BOS-CONEXIONES-COMUNICACIONES-"
            "SERVIDORES-CANONICAL-INVENTORY-UI-FIX-R3-20261022"
        ),
        "blocker_signature": (
            "processing_stale_after_single_requeue"
        ),
        "previous_capability": (
            "MUTATION_LIFECYCLE_STALE_OWNERSHIP"
        ),
        "previous_repair_certified": True,
    }

    registry.register_learned_capability(
        successor_cap,
        incident=successor_inc,
        require_certified_incident=True,
    )

    resolved_exact = registry.resolve_learned_capability(
        incident_id=successor_inc.incident_id,
    )
    assert resolved_exact is not None
    assert (
        resolved_exact.code
        == "MUTATION_LIFECYCLE_SLOT_HEARTBEAT_V2"
    )

    resolved_pattern = registry.resolve_learned_capability(
        incident_id=(
            "EDARSAHUB-BOS-WORKER-MUTATION-LIFECYCLE-"
            "SLOT-HEARTBEAT-FUTURE"
        ),
    )
    assert resolved_pattern is not None
    assert (
        resolved_pattern.code
        == "MUTATION_LIFECYCLE_SLOT_HEARTBEAT_V2"
    )

    resolved_blocker = (
        registry.resolve_learned_capability_for_blockers(
            {"processing_stale_after_single_requeue"}
        )
    )
    assert resolved_blocker is not None
    assert (
        resolved_blocker.code
        == "MUTATION_LIFECYCLE_SLOT_HEARTBEAT_V2"
    )

    uncertified_successor = dict(successor_cap)
    uncertified_successor["code"] = (
        "MUTATION_LIFECYCLE_CONFLICTING_V3"
    )
    uncertified_successor["evidence"] = {
        "source_job_id": "JOB-CONFLICT",
        "blocker_signature": (
            "processing_stale_after_single_requeue"
        ),
    }
    registry.register_learned_capability(
        uncertified_successor,
        incident=successor_inc,
    )

    with pytest.raises(
        ValueError,
        match="LEARNED_CAPABILITY_AMBIGUOUS",
    ):
        registry.resolve_learned_capability_for_blockers(
            {"processing_stale_after_single_requeue"}
        )
