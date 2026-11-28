"""Contract tests for SQL connections 8/10 semantic READ_ONLY ingress."""
from __future__ import annotations

import pytest

from modules.worker_ingress import semantic_capabilities as caps
from modules.worker_ingress import service


USER = {
    "id": "1",
    "email": "ricardo@edarsa.com.mx",
    "role": "SuperAdministrador",
}

EXPECTED_PATHS = [
    "backend/core/centro_control/routes.py",
    "backend/core/config/edarsahub_config.py",
    "backend/core/sql_first/connection_factory.py",
    "backend/core/sql_first/db.py",
    "backend/core/connections/hrlectura_connection_factory.py",
    "backend/server.py",
]


def request(**overrides):
    payload = {
        "objective": "Auditar conexiones SQL 8/10.",
        "bounded_context": "SQL_CONNECTIONS_8OF10",
        "mode": "READ_ONLY",
        "capability": "SQL_CONNECTIONS_BOOTSTRAP_READONLY",
        "constraints": {},
    }
    payload.update(overrides)
    return payload


def test_capability_registered_and_readonly():
    assert "SQL_CONNECTIONS_BOOTSTRAP_READONLY" in caps.registered_capabilities()
    catalog = {row["code"]: row for row in caps.capability_catalog()}
    entry = catalog["SQL_CONNECTIONS_BOOTSTRAP_READONLY"]
    assert entry["modes"] == ["READ_ONLY"]
    assert entry["bounded_context_rule"] == "SQL_CONNECTIONS_8OF10"
    assert entry["allowed_constraints"] == []
    assert entry["raw_worker_fields_forbidden"] is True


def test_fixed_readonly_contract():
    job = service.build_semantic_job(request(), current_user=USER)
    assert job["mode"] == "READ_ONLY"
    assert job["production_allowed"] is False
    assert job["actions"] == []
    assert len(job["checks"]) == 1
    check = job["checks"][0]
    assert check["type"] == "repository_contract_audit"
    assert check["request"]["paths"] == EXPECTED_PATHS
    assert check["request"]["max_results"] == 200


def test_rejects_wrong_context():
    with pytest.raises(
        service.WorkerIngressError,
        match="SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED",
    ):
        service.build_semantic_job(
            request(bounded_context="OTHER"),
            current_user=USER,
        )


@pytest.mark.parametrize(
    "constraints",
    [
        {"paths": ["backend/core"]},
        {"actions": []},
        {"checks": [{"type": "git_diff_check"}]},
        {"production_allowed": False},
    ],
)
def test_rejects_caller_constraints(constraints):
    with pytest.raises(
        service.WorkerIngressError,
        match="SEMANTIC_CONSTRAINTS_UNSUPPORTED",
    ):
        service.build_semantic_job(
            request(constraints=constraints),
            current_user=USER,
        )
