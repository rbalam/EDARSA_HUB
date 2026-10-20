import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_chapur_profile_is_allowlisted_and_select_only():
    profiles = _load(
        "readonly_audit_profiles",
        "tools/mirror_sync/readonly_audit_profiles.py",
    )
    assert profiles.is_allowed_readonly_audit_profile(
        "chapur_connection_discovery_v1"
    )
    checks = profiles.build_readonly_audit_checks(
        "chapur_connection_discovery_v1"
    )
    assert len(checks) == 1
    check = checks[0]
    assert check["type"] == "sql_readonly_audit"
    assert check["source"] == "EDARSAHUB"
    assert {q["name"] for q in check["queries"]} == {
        "chapur_enterprise_connections",
        "chapur_units",
        "chapur_company_candidates",
        "chapur_branch_candidates",
        "chapur_versions",
    }
    for query in check["queries"]:
        assert query["sql"].lstrip().upper().startswith("SELECT")
        upper = query["sql"].upper()
        assert "SOFTRESTAURANT" not in upper
        for forbidden in (
            " INSERT ",
            " UPDATE ",
            " DELETE ",
            " MERGE ",
            " DROP ",
            " ALTER ",
            " CREATE ",
            " EXEC ",
        ):
            assert forbidden not in f" {upper} "


def test_unknown_profile_is_rejected():
    profiles = _load(
        "readonly_audit_profiles_unknown",
        "tools/mirror_sync/readonly_audit_profiles.py",
    )
    assert not profiles.is_allowed_readonly_audit_profile("unknown")


def test_bridge_accepts_profile_without_inline_sql_checks():
    bridge = _load(
        "bridge_named_readonly",
        "tools/mirror_sync/universal_job_bridge.py",
    )
    job = {
        "schema": "edarsahub.worker-job.v2",
        "job_id": "chapur-profile-test",
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "production_allowed": False,
        "objective": "test",
        "human_summary_language": "es",
        "mode": "READ_ONLY_SQL",
        "actions": [],
        "audit_profile": "chapur_connection_discovery_v1",
        "checks": [],
    }
    assert bridge.validate(job) == []


def test_bridge_rejects_profile_plus_inline_checks():
    bridge = _load(
        "bridge_named_readonly_inline",
        "tools/mirror_sync/universal_job_bridge.py",
    )
    job = {
        "schema": "edarsahub.worker-job.v2",
        "job_id": "chapur-profile-inline-test",
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "production_allowed": False,
        "objective": "test",
        "human_summary_language": "es",
        "mode": "READ_ONLY_SQL",
        "actions": [],
        "audit_profile": "chapur_connection_discovery_v1",
        "checks": [
            {
                "type": "sql_readonly_audit",
                "queries": [{"name": "x", "sql": "SELECT 1"}],
            }
        ],
    }
    errors = bridge.validate(job)
    assert "READ_ONLY_SQL_AUDIT_PROFILE_WITH_INLINE_CHECKS_FORBIDDEN" in errors


def test_chapur_norte_visibility_profile_is_named_and_readonly():
    profiles = _load(
        "readonly_audit_profiles_chapur_norte",
        "tools/mirror_sync/readonly_audit_profiles.py",
    )
    assert profiles.is_allowed_readonly_audit_profile(
        "chapur_norte_operational_visibility_v1"
    )
    checks = profiles.build_readonly_audit_checks(
        "chapur_norte_operational_visibility_v1"
    )
    assert len(checks) == 1
    check = checks[0]
    assert check["type"] == "sql_readonly_audit"
    names = {query["name"] for query in check["queries"]}
    assert names == {"chapur_norte_connection", "chapur_norte_units"}
    for query in check["queries"]:
        upper = query["sql"].upper()
        assert "SELECT" in upper
        for forbidden in ("UPDATE ", "INSERT ", "DELETE ", "MERGE ", "DROP ", "ALTER ", "CREATE "):
            assert forbidden not in upper


def test_api_factory_persistence_profile_is_named_and_readonly():
    profiles = _load(
        "readonly_audit_profiles_api_factory",
        "tools/mirror_sync/readonly_audit_profiles.py",
    )
    assert profiles.is_allowed_readonly_audit_profile(
        "api_factory_persistence_state_v1"
    )
    checks = profiles.build_readonly_audit_checks(
        "api_factory_persistence_state_v1"
    )
    assert len(checks) == 1
    check = checks[0]
    assert check["type"] == "sql_readonly_audit"
    assert check["source"] == "EDARSAHUB"
    assert {query["name"] for query in check["queries"]} == {
        "api_factory_tables",
        "api_factory_columns",
    }
    for query in check["queries"]:
        upper = query["sql"].upper()
        assert "SELECT" in upper
        for forbidden in (
            " INSERT ",
            " UPDATE ",
            " DELETE ",
            " MERGE ",
            " DROP ",
            " ALTER ",
            " CREATE ",
            " EXEC ",
        ):
            assert forbidden not in f" {upper} "


def test_chapur_external_integration_readiness_profile_is_sanitized_and_readonly():
    profiles = _load("tools/mirror_sync/readonly_audit_profiles.py")
    checks = profiles.build_readonly_audit_checks("chapur_external_integration_readiness_v1")
    assert len(checks) == 1
    check = checks[0]
    assert check["type"] == "sql_readonly_audit"
    names = {query["name"] for query in check["queries"]}
    assert names == {"chapur_external_readiness", "chapur_external_health"}
    sql = "\n".join(query["sql"] for query in check["queries"]).lower()
    assert "api_key_configured" in sql
    assert "password_configured" in sql
    assert "api_key_encrypted" in sql
    assert "password_encrypted" in sql
    assert "select" in sql
    for forbidden in (" update ", " insert ", " delete ", " merge ", " drop ", " alter "):
        assert forbidden not in f" {sql} "
