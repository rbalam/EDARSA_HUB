from __future__ import annotations

from types import SimpleNamespace

from tools.mirror_sync import worker_repair_planner as planner


def test_capability_registered():
    assert (
        "CANONICAL_JOB_INGRESS"
        in planner.registered_capabilities()
    )


def test_capability_scope():
    capability = (
        planner._CAPABILITIES[
            "CANONICAL_JOB_INGRESS"
        ]
    )

    assert set(
        capability.required_paths
    ) == {
        "tools/mirror_sync/gate_chain_publisher.py",
        (
            "backend/tests/"
            "test_worker_canonical_job_ingress_contract.py"
        ),
    }


def test_capability_bound_to_incident():
    capability = (
        planner._CAPABILITIES[
            "CANONICAL_JOB_INGRESS"
        ]
    )

    assert capability.incident_ids == (
        "EDARSAHUB-BOS-WORKER-V1.2-"
        "CANONICAL-JOB-INGRESS-R1",
    )


def test_recipe_scope_is_bounded():
    capability = (
        planner._CAPABILITIES[
            "CANONICAL_JOB_INGRESS"
        ]
    )

    incident = SimpleNamespace(
        target_paths=(
            "tools/mirror_sync/gate_chain_publisher.py",
            (
                "backend/tests/"
                "test_worker_canonical_job_ingress_contract.py"
            ),
        )
    )

    recipe = capability.builder(
        incident,
        {
            "base_sha": "a" * 40,
            "requester": {
                "email": "test@example.invalid",
                "source": "pytest",
            },
        },
    )

    paths = {
        action["path"]
        for action in recipe["actions"]
    }

    assert paths.issubset(
        set(incident.target_paths)
    )


def test_unknown_capability_fail_closed():
    try:
        planner._resolve_capability(
            "UNKNOWN",
            "NOT_REGISTERED",
        )
    except ValueError as exc:
        assert str(exc) == (
            "REPAIR_CAPABILITY_UNKNOWN"
        )
    else:
        raise AssertionError(
            "unknown capability accepted"
        )
