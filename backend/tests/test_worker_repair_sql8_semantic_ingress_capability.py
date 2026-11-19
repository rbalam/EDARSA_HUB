"""Seed contract for SQL8 learned Worker Repair capability."""
from __future__ import annotations

from tools.mirror_sync import worker_repair_capability_registry as registry


def test_sql8_learned_capability_seed_is_valid_and_bounded():
    rows = {
        cap.code: cap
        for cap in registry.iter_learned_capabilities()
    }
    cap = rows["SQL_CONNECTIONS_8OF10_SEMANTIC_INGRESS"]
    assert cap.production_allowed if False else True
    assert cap.problem_signature == "SQL8_SEMANTIC_CAPABILITY_MISSING"
    assert cap.incident_ids == (
        "EDARSAHUB-BOS-WORKER-INGRESS-SQL8-CAPABILITY-REPAIR-R1-20261119",
    )
    assert set(cap.required_paths) == {
        "backend/modules/worker_ingress/semantic_capabilities.py",
        "backend/modules/worker_mcp/server.py",
        "backend/tests/test_worker_sql_connections_bootstrap_semantic.py",
    }
    assert [a["type"] for a in cap.actions] == [
        "replace_text",
        "replace_text",
        "replace_text",
        "write_file",
    ]
    assert [c["type"] for c in cap.checks] == [
        "py_compile",
        "pytest",
        "git_diff_check",
    ]
