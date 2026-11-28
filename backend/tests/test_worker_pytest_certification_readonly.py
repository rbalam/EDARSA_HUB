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


EXPECTED_CAVA_SOCIOS_PATHS = [
    "backend/tests/test_cava_socios_domain.py",
    "backend/tests/test_cava_socios_adapter_sdk.py",
    "backend/tests/test_cava_socios_blind_audit.py",
    "backend/tests/test_cava_socios_blind_audit_operational_service.py",
    "backend/tests/test_cava_socios_cienfuegos_legacy_adapter.py",
    "backend/tests/test_cava_socios_cienfuegos_legacy_dryrun.py",
    "backend/tests/test_cava_socios_evidence_chain.py",
    "backend/tests/test_cava_socios_migration_engine.py",
    "backend/tests/test_cavas_gate12e_bos_persona_link_contract.py",
]

EXPECTED_CAVAS_CORPORATIVAS_PATHS = [
    "backend/tests/test_cavas_corporativas_domain.py",
    "backend/tests/test_cavas_corporativas_repository.py",
    "backend/tests/test_cavas_corporativas_routes.py",
    "backend/tests/test_cavas_corporativas_service.py",
]

EXCLUDED_UNSAFE_CAVA_FILES = (
    "test_cava_socios_gate12n_uat_controlled.py",
    "test_cava_socios_gate13b_e2e_controlled.py",
    "test_cava_socios_persona_link_gate12m_canary.py",
    "test_cava_socios.py",
    "test_cava_socios_persona_link.py",
)


def test_cava_socios_hermetic_readonly_suite():
    result = expand(bounded_context="CAVA_SOCIOS")
    assert result["actions"] == []
    assert result["checks"] == [{
        "type": "pytest",
        "paths": EXPECTED_CAVA_SOCIOS_PATHS,
        "isolation": "HERMETIC_READONLY",
    }]
    assert result["scheduling"]["bounded_context"] == "CAVA_SOCIOS"
    for forbidden in EXCLUDED_UNSAFE_CAVA_FILES:
        assert all(forbidden not in p for p in result["checks"][0]["paths"])


def test_cavas_corporativas_hermetic_readonly_suite():
    result = expand(bounded_context="CAVAS_CORPORATIVAS")
    assert result["actions"] == []
    assert result["checks"] == [{
        "type": "pytest",
        "paths": EXPECTED_CAVAS_CORPORATIVAS_PATHS,
        "isolation": "HERMETIC_READONLY",
    }]
    assert result["scheduling"]["bounded_context"] == "CAVAS_CORPORATIVAS"
    for forbidden in EXCLUDED_UNSAFE_CAVA_FILES:
        assert all(forbidden not in p for p in result["checks"][0]["paths"])


@pytest.mark.parametrize("domain", ["CAVA_SOCIOS", "CAVAS_CORPORATIVAS"])
@pytest.mark.parametrize("unsafe", [
    {"paths": ["backend/tests/test_anything.py"]},
    {"checks": [{"type": "pytest", "paths": ["backend/tests/test_anything.py"]}]},
    {"commands": ["python -m pytest"]},
    {"actions": []},
    {"production_allowed": True},
    {"isolation": "STANDARD_READONLY"},
])
def test_cava_domains_reject_caller_constraints(domain, unsafe):
    with pytest.raises(SemanticCapabilityError):
        expand(bounded_context=domain, constraints=unsafe)


def test_suite_registry_rejects_unsafe_or_duplicate_registrations():
    Suite = _module.PytestCertificationSuite
    register = _module.register_pytest_certification_suite

    with pytest.raises(SemanticCapabilityError, match="PYTEST_SUITE_DUPLICATE_DOMAIN"):
        register(Suite(bounded_context="CAVA_SOCIOS", paths=("backend/tests/test_x.py",)))

    with pytest.raises(SemanticCapabilityError, match="PYTEST_SUITE_SQL_FORBIDDEN"):
        register(Suite(bounded_context="NEW_DOM_1", paths=("backend/tests/test_x.py",), requires_sql=True))
    with pytest.raises(SemanticCapabilityError, match="PYTEST_SUITE_NETWORK_FORBIDDEN"):
        register(Suite(bounded_context="NEW_DOM_2", paths=("backend/tests/test_x.py",), requires_network=True))
    with pytest.raises(SemanticCapabilityError, match="PYTEST_SUITE_SERVER_IMPORT_FORBIDDEN"):
        register(Suite(bounded_context="NEW_DOM_3", paths=("backend/tests/test_x.py",), allows_server_import=True))

    for bad_path in (
        "backend/tests/test_cava_socios_gate12n_uat_controlled.py",
        "backend/tests/test_cava_socios_gate13b_e2e_controlled.py",
        "backend/tests/test_cava_socios_persona_link_gate12m_canary.py",
        "backend/modules/cava_socios/routes.py",
        "../secret.py",
    ):
        with pytest.raises(SemanticCapabilityError, match="PYTEST_SUITE_PATH_"):
            register(Suite(bounded_context="NEW_DOM_BAD", paths=(bad_path,)))


def test_hermetic_pytest_dispatcher_blocks_credentials_network_and_sql(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    for p in (repo_root, repo_root / "tools" / "mirror_sync"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    from tools.mirror_sync import universal_job_bridge as ujb
    from tools.mirror_sync import universal_job_dispatcher as ujd

    assert ujb.validate_check({"type": "pytest", "paths": ["backend/tests/test_ok.py"], "isolation": "HERMETIC_READONLY"}, 0) == []
    assert ujb.validate_check({"type": "pytest", "paths": ["backend/tests/test_ok.py"], "isolation": "UNSAFE_MODE"}, 0) == ["CHECK_0_INVALID_PYTEST_ISOLATION"]

    wt = tmp_path / "wt"
    (wt / "backend" / "tests").mkdir(parents=True)
    (wt / "tools").symlink_to(repo_root / "tools")
    probe = wt / "backend" / "tests" / "test_hermetic_probe.py"
    probe.write_text(
        "\n".join([
            "import os, socket, pytest",
            "def test_hermetic_guards_active():",
            "    assert os.environ.get('EDARSAHUB_PYTEST_HERMETIC') == '1'",
            "    assert os.environ.get('EDARSAHUB_SQL_HOST') == 'hermetic-disabled.invalid'",
            "    assert os.environ.get('EDARSAHUB_SQL_PASSWORD') == 'HERMETIC_DISABLED'",
            "    assert 'OPENAI_API_KEY' not in os.environ",
            "    with pytest.raises(PermissionError, match='HERMETIC_NETWORK_DENIED'):",
            "        socket.create_connection(('1.1.1.1', 443), timeout=1)",
            "    try:",
            "        import pymssql",
            "    except ImportError:",
            "        pymssql = None",
            "    if pymssql is not None:",
            "        with pytest.raises(PermissionError, match='HERMETIC_SQL_DENIED'):",
            "            pymssql.connect(server='127.0.0.1', user='x', password='y', database='z')",
            "    try:",
            "        import dotenv",
            "        assert dotenv.load_dotenv() is False",
            "    except ImportError:",
            "        pass",
        ]) + "\n",
        encoding="utf-8",
    )

    res = ujd.run_check(
        wt,
        {"type": "pytest", "paths": ["backend/tests/test_hermetic_probe.py"], "isolation": "HERMETIC_READONLY"},
        readonly=True,
    )
    assert res["status"] == "PASS", res.get("output")
    assert res["isolation"] == "HERMETIC_READONLY"


def test_sec_rbac_hermetic_readonly_fixed_suite():
    result = expand(bounded_context="SEC_RBAC")
    assert result["actions"] == []
    assert result["checks"] == [{
        "type": "pytest",
        "paths": [
            "backend/tests/test_bos_usuarios_rbac_implementation_r1.py",
            "backend/tests/test_catalogos_workflow_privileged_routes_rbac.py",
        ],
        "isolation": "HERMETIC_READONLY",
    }]
    assert result["scheduling"]["bounded_context"] == "SEC_RBAC"


@pytest.mark.parametrize("unsafe", [
    {"paths": ["backend/tests/test_auth_session_revocation_p1_2.py"]},
    {"actions": []},
    {"checks": []},
    {"production_allowed": True},
])
def test_sec_rbac_rejects_caller_controlled_tests(unsafe):
    with pytest.raises(SemanticCapabilityError):
        expand(bounded_context="SEC_RBAC", constraints=unsafe)
