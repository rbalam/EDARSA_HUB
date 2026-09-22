import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync.gate_chain_publisher import (
    build_plan,
    validate_template,
)

PUBLISHER = ROOT / "tools" / "mirror_sync" / "gate_chain_publisher.py"


def template(job="job-next"):
    return {
        "schema": "edarsahub.worker-job.v2",
        "job_id": job,
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "production_allowed": False,
        "objective": "test",
        "mode": "READ_ONLY",
        "actions": [],
        "checks": [
            {
                "type": "git_diff_check",
            }
        ],
    }


def chain(t=None):
    return {
        "schema": "edarsahub.gate-chain.v1",
        "chain_id": "T",
        "enabled": True,
        "max_hops": 5,
        "start_gate_id": "A",
        "gates": [
            {
                "gate_id": "A",
                "job_id": "done-a",
                "mutation_class": "READ_ONLY",
                "next_gate_ids": ["B"],
            },
            {
                "gate_id": "B",
                "job_id": "job-next",
                "mutation_class": "READ_ONLY",
                "next_gate_ids": [],
                "job_template": t or template(),
            },
        ],
    }


def decision(state="READY"):
    return {
        "state": state,
        "next_gate_id": "B",
    }


def source():
    return PUBLISHER.read_text(encoding="utf-8")


def test_plan_ready():
    result = build_plan(
        chain(),
        decision(),
        set(),
    )

    assert result["status"] == "READY_TO_PUBLISH"


def test_duplicate_is_exists():
    result = build_plan(
        chain(),
        decision(),
        {"job-next"},
    )

    assert result["status"] == "EXISTS"
    assert result["publish"] is False


def test_nonready_rejected():
    with pytest.raises(
        ValueError,
        match="DECISION_NOT_READY",
    ):
        build_plan(
            chain(),
            decision("WAIT"),
            set(),
        )


def test_production_forbidden():
    value = template()
    value["production_allowed"] = True

    with pytest.raises(
        ValueError,
        match="PRODUCTION_FORBIDDEN",
    ):
        build_plan(
            chain(value),
            decision(),
            set(),
        )


def test_invalid_schema():
    value = template()
    value["schema"] = "x"

    with pytest.raises(
        ValueError,
        match="INVALID_JOB_TEMPLATE_SCHEMA",
    ):
        validate_template(value)


def test_arbitrary_shell_forbidden():
    value = template()
    value["command"] = "rm -rf /"

    with pytest.raises(
        ValueError,
        match="FORBIDDEN_TEMPLATE_KEY:command",
    ):
        validate_template(value)


def test_arbitrary_sql_forbidden():
    value = template()
    value["sql"] = "DELETE FROM x"

    with pytest.raises(
        ValueError,
        match="FORBIDDEN_TEMPLATE_KEY:sql",
    ):
        validate_template(value)


def test_unsupported_action_rejected():
    value = template()
    value["actions"] = [
        {
            "type": "run_shell",
        }
    ]

    with pytest.raises(
        ValueError,
        match="UNSUPPORTED_ACTION",
    ):
        validate_template(value)


def test_repository_contract_audit_supported():
    value = template()

    value["checks"] = [
        {
            "type": "repository_contract_audit",
            "request": {
                "paths": ["backend"],
                "search_terms": ["finanzas"],
                "max_results": 10,
            },
        }
    ]

    assert validate_template(value) is value


def test_unsupported_check_rejected():
    value = template()
    value["checks"] = [
        {
            "type": "execute_sql",
        }
    ]

    with pytest.raises(
        ValueError,
        match="UNSUPPORTED_CHECK",
    ):
        validate_template(value)


def test_publisher_uses_registered_agent_guard_worktree():
    text = source()

    assert '"worktree-create"' in text
    assert '"worker_queue_publication"' in text
    assert 'f"agent/queue-publisher/{safe_id}"' in text
    assert 'f"queue-publisher-{safe_id}"' in text

    assert "tempfile.mkdtemp" not in text
    assert '"worktree", "add"' not in text


def test_publisher_claim_scope_is_exact_job_request():
    text = source()

    assert '"--path",' in text
    assert "rel," in text
    assert 'f"worker_queue/inbox/{job_id}.json"' in text
    assert "STAGED_SCOPE_MISMATCH" in text
    assert "validate_commit_scope(" in text


def test_publisher_uses_canonical_authorized_push():
    text = source()

    assert "authorized_push(" in text
    assert "scoped_push_env(" not in text

    assert "EDARSA_ALLOW_PUSH" not in text
    assert "EDARSA_PUSH_JOB_ID" not in text
    assert "EDARSA_PUSH_OWNER" not in text


def test_publisher_never_bypasses_hooks_or_force_pushes():
    text = source().lower()

    assert "--no-verify" not in text
    assert "--force" not in text
    assert "force-with-lease" not in text


def test_publisher_has_optimistic_queue_concurrency_guard():
    text = source()

    assert "_queue_remote_head(" in text
    assert "REMOTE_MOVED_RETRY_REQUIRED" in text
    assert "QUEUE_PUBLISHER_LINEAGE_INVALID" in text


def test_publisher_releases_agent_guard_claim():
    text = source()

    assert '"release"' in text
    assert "_release_agent_guard(" in text
    assert "_cleanup_queue_worktree(" in text


def test_publisher_preserves_failure_evidence():
    text = source()

    assert "QUEUE_PUBLISHER_WORKTREE_DIRTY_PRESERVED" in text

    # Branch cleanup occurs only on successful publication.
    assert "if success and not worktree.exists():" in text


def test_publisher_is_idempotent():
    text = source()

    assert "REMOTE_JOB=EXISTS" in text
    assert '"cat-file",' in text


def test_plan_only_remains_non_mutating():
    text = source()

    assert "publish(plan)" in text
    assert "if args.publish" in text


def test_publisher_explicitly_reports_production_untouched():
    text = source()

    assert '"production_touched": False' in text
