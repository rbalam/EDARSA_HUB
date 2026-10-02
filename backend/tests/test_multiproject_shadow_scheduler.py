from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools" / "mirror_sync" / "multiproject_shadow_scheduler.py"

spec = spec_from_file_location("multiproject_shadow_scheduler", MODULE)
mod = module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def row(job):
    return {"job": job, "meta": mod.normalize_metadata(job)}


def test_legacy_jobs_are_conservative_and_global():
    meta = mod.normalize_metadata({"job_id": "OLD", "mode": "READ_ONLY"})
    assert meta.project_id == "LEGACY_GLOBAL"
    assert meta.conflict_domains == ("GLOBAL_GIT_WRITER",)
    assert meta.legacy_defaults is True


def test_disjoint_readonly_projects_can_shadow_parallel():
    a = mod.normalize_metadata({"mode": "READ_ONLY", "scheduling": {
        "project_id": "CAVAS", "bounded_context": "cavas",
        "resource_claims": ["backend/modules/cava_socios"], "conflict_domains": ["CAVAS"]}})
    b = mod.normalize_metadata({"mode": "READ_ONLY", "scheduling": {
        "project_id": "TABLAJERIAS", "bounded_context": "tablajerias",
        "resource_claims": ["backend/modules/tablajeria"], "conflict_domains": ["TABLAJERIAS"]}})
    assert mod.can_shadow_parallel(a, b) is True


def test_same_resource_blocks_parallelism():
    common = ["frontend/src/App.js"]
    a = mod.normalize_metadata({"mode": "MUTATION", "scheduling": {
        "project_id": "CAVAS", "resource_claims": common, "conflict_domains": ["CAVAS"]}})
    b = mod.normalize_metadata({"mode": "MUTATION", "scheduling": {
        "project_id": "TABLAJERIAS", "resource_claims": common, "conflict_domains": ["TABLAJERIAS"]}})
    assert mod.can_shadow_parallel(a, b) is False


def test_global_domain_serializes():
    a = mod.normalize_metadata({"mode": "READ_ONLY", "scheduling": {
        "project_id": "A", "conflict_domains": ["GLOBAL_NAVIGATION"]}})
    b = mod.normalize_metadata({"mode": "READ_ONLY", "scheduling": {
        "project_id": "B", "conflict_domains": ["GLOBAL_NAVIGATION"]}})
    assert mod.can_shadow_parallel(a, b) is False


def test_project_max_parallelism_is_respected():
    pending = [
        row({"job_id": "A1", "mode": "READ_ONLY", "scheduling": {
            "project_id": "A", "resource_claims": ["a1"], "conflict_domains": ["A1"], "max_parallelism": 1}}),
        row({"job_id": "A2", "mode": "READ_ONLY", "scheduling": {
            "project_id": "A", "resource_claims": ["a2"], "conflict_domains": ["A2"], "max_parallelism": 1}}),
    ]
    selected = mod.choose_shadow_slots(pending, [], max_slots=4)
    assert len(selected) == 1


def test_weighted_fairness_changes_order_without_starvation():
    a = row({"job_id": "A", "mode": "READ_ONLY", "scheduling": {
        "project_id": "A", "fairness_weight": 1, "resource_claims": ["a"], "conflict_domains": ["A"]}})
    b = row({"job_id": "B", "mode": "READ_ONLY", "scheduling": {
        "project_id": "B", "fairness_weight": 4, "resource_claims": ["b"], "conflict_domains": ["B"]}})
    ordered = sorted([a, b], key=lambda r: mod.fairness_key(r, {"A": 2, "B": 2}))
    assert ordered[0]["meta"].project_id == "B"


def test_shadow_payload_never_executes_or_mutates():
    payload = mod.decision_payload(max_slots=2)
    assert payload["mode"] == "SHADOW_ONLY"
    assert payload["authoritative_executor"] == "edarsahub-universal-worker"
    assert payload["executed_jobs"] == []
    assert payload["queue_mutations"] == 0
    assert payload["production_touched"] is False
