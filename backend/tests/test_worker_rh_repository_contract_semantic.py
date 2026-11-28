"""Security contract tests for bounded RH repository audit semantic ingress."""
from __future__ import annotations

import pytest

from modules.worker_ingress import service
from modules.worker_ingress.semantic_capabilities import (
    SemanticCapabilityError,
    registered_capabilities,
    resolve_capability,
)

USER = {"email": "admin@example.com"}
REQUEST = {
    "objective": "Audit existing RH offboarding, payroll and clearance contracts.",
    "bounded_context": "RH",
    "mode": "READ_ONLY",
    "capability": "REPOSITORY_CONTRACT_AUDIT",
    "request_key": "RH-OFFBOARDING-READONLY-20261105",
}


def test_capability_is_registered_and_read_only():
    assert "REPOSITORY_CONTRACT_AUDIT" in registered_capabilities()
    capability = resolve_capability("REPOSITORY_CONTRACT_AUDIT")
    assert capability.modes == ("READ_ONLY",)


def test_semantic_expansion_is_canonical_and_immutable_for_caller():
    job = service.build_semantic_job(REQUEST, current_user=USER)
    assert job["mode"] == "READ_ONLY"
    assert job["production_allowed"] is False
    assert job["actions"] == []
    assert job["target_branch"] == "Edarsahub_Desarrollo"
    assert len(job["checks"]) == 1
    check = job["checks"][0]
    assert check["type"] == "repository_contract_audit"
    assert check["request"]["paths"]
    assert check["request"]["search_terms"]
    assert job["requester"]["email"] == USER["email"]


@pytest.mark.parametrize("mode", ["WRITE", "EXECUTE", "PRODUCTION"])
def test_non_read_only_modes_fail_closed(mode):
    with pytest.raises(service.WorkerIngressError, match="SEMANTIC_CAPABILITY_MODE_MISMATCH"):
        service.build_semantic_job({**REQUEST, "mode": mode}, current_user=USER)


@pytest.mark.parametrize("constraints", [
    {"paths": [".git"]},
    {"actions": [{"type": "write_file"}]},
    {"checks": [{"type": "pytest"}]},
    {"production_allowed": True},
    ["unexpected"],
])
def test_caller_cannot_override_audit_contract(constraints):
    with pytest.raises(service.WorkerIngressError, match="SEMANTIC_CONSTRAINTS_UNSUPPORTED"):
        service.build_semantic_job(
            {**REQUEST, "constraints": constraints}, current_user=USER
        )


def test_other_bounded_context_rejected():
    with pytest.raises(service.WorkerIngressError, match="SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED"):
        service.build_semantic_job(
            {**REQUEST, "bounded_context": "FINANZAS"}, current_user=USER
        )


def test_stable_request_key_produces_same_job_id():
    a = service.build_semantic_job(REQUEST, current_user=USER)
    b = service.build_semantic_job(REQUEST, current_user=USER)
    assert a["job_id"] == b["job_id"]


def test_no_publisher_called_during_build(monkeypatch):
    def forbidden_submit(*args, **kwargs):
        raise AssertionError("Publisher must not run during build")
    monkeypatch.setattr(service.gate_chain_publisher, "submit", forbidden_submit)
    service.build_semantic_job(REQUEST, current_user=USER)
