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
