"""Fixed-target READ_ONLY pytest semantic capability contract."""

import pytest

import importlib.util
from pathlib import Path

_REGISTRY = (
    Path(__file__).resolve().parents[1]
    / "modules/worker_ingress/semantic_capabilities.py"
)
_spec = importlib.util.spec_from_file_location(
    "worker_pytest_semantic_registry",
    _REGISTRY,
)
_module = importlib.util.module_from_spec(_spec)
import sys
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)

SemanticCapabilityError = _module.SemanticCapabilityError
resolve_capability = _module.resolve_capability

CAPABILITY = "WORKER_PYTEST_CERTIFICATION_READONLY"
CONTEXT = "WORKER_REPAIR_KNOWLEDGE_LOOP"
TARGET = (
    "backend/tests/"
    "test_worker_repair_planner_canonical_ingress_capability.py"
)


def expand(**overrides):
    request = {
        "bounded_context": CONTEXT,
        "constraints": {},
    }
    request.update(overrides)
    capability = resolve_capability(CAPABILITY)
    return capability.builder(request)


def test_registered_readonly_only():
    capability = resolve_capability(CAPABILITY)
    assert capability.modes == ("READ_ONLY",)
    assert callable(capability.builder)


def test_fixed_target_and_no_actions():
    result = expand()
    assert result["actions"] == []
    assert result["checks"] == [
        {"type": "pytest", "paths": [TARGET]}
    ]


def test_context_is_bounded():
    with pytest.raises(
        SemanticCapabilityError,
        match="SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED",
    ):
        expand(bounded_context="RH")


@pytest.mark.parametrize(
    "constraints",
    [
        {"paths": ["backend"]},
        {"commands": ["echo unsafe"]},
        {"actions": ["write"]},
        {"checks": [{"type": "pytest"}]},
        {"production_allowed": True},
    ],
)
def test_arbitrary_constraints_fail_closed(constraints):
    with pytest.raises(SemanticCapabilityError):
        expand(constraints=constraints)


def test_scheduling_is_bounded():
    result = expand()
    assert result["scheduling"]["bounded_context"] == CONTEXT


def test_no_mutation_mode():
    capability = resolve_capability(CAPABILITY)
    assert "MUTATION" not in capability.modes


def test_ia_global_rbac_readonly_fixed_suite():
    result = expand(bounded_context="IA_ASSISTANT")
    assert result["actions"] == []
    assert result["checks"] == [{
        "type": "pytest",
        "paths": [
            "backend/tests/test_ia_global_rbac_data_scope_r14.py",
            "backend/tests/test_ia_global_authorized_contract.py",
            "backend/tests/test_ia_contextual_comercial_contract.py",
            "backend/tests/test_comercial_analytics_tickets.py",
        ],
    }]
    assert result["scheduling"]["bounded_context"] == "IA_ASSISTANT"


@pytest.mark.parametrize("unsafe", [
    {"paths": ["backend/tests/test_anything.py"]},
    {"checks": [{"type": "pytest", "paths": ["backend/tests/test_anything.py"]}]},
    {"commands": ["python -m pytest"]},
    {"actions": []},
    {"production_allowed": True},
])
def test_ia_global_rbac_rejects_caller_controlled_checks(unsafe):
    with pytest.raises(SemanticCapabilityError):
        expand(bounded_context="IA_ASSISTANT", constraints=unsafe)


def test_bos_executive_readonly_fixed_suite():
    result = expand(bounded_context="BOS_EXECUTIVE")
    assert result["actions"] == []
    assert result["checks"] == [{
        "type": "pytest",
        "paths": [
            "backend/tests/test_bos_executive_e3a.py",
            "backend/tests/test_bos_executive_e3b.py",
            "backend/tests/test_bos_executive_e3c.py",
            "backend/tests/test_bos_executive_e3d.py",
        ],
    }]
    assert result["scheduling"]["bounded_context"] == "BOS_EXECUTIVE"


@pytest.mark.parametrize("unsafe", [
    {"paths": ["backend/tests/test_anything.py"]},
    {"checks": [{"type": "pytest", "paths": ["backend/tests/test_anything.py"]}]},
    {"commands": ["python -m pytest"]},
    {"actions": []},
    {"production_allowed": True},
])
def test_bos_executive_rejects_caller_controlled_checks(unsafe):
    with pytest.raises(SemanticCapabilityError):
        expand(bounded_context="BOS_EXECUTIVE", constraints=unsafe)
