from __future__ import annotations

from pathlib import Path

import pytest

from tools.mirror_sync import gate_chain_publisher as ingress


def requester():
    return {
        "email": "test@example.invalid",
        "source": "pytest",
        "project": "EDARSAHUB",
        "chat": "canonical-ingress",
    }


def readonly_job(job_id):
    return {
        "job_id": job_id,
        "objective": "Test canonical ingress.",
        "requester": requester(),
        "mode": "READ_ONLY",
        "actions": [],
        "checks": [
            {
                "type": "git_diff_check",
            }
        ],
    }


def readonly_sql_job(job_id):
    return {
        "job_id": job_id,
        "objective": "Test READ_ONLY_SQL ingress.",
        "requester": requester(),
        "mode": "READ_ONLY_SQL",
        "actions": [],
        "checks": [
            {
                "type": "sql_readonly_audit",
                "source": "EDARSAHUB",
                "queries": [
                    {
                        "name": "identity",
                        "sql": (
                            "SELECT DB_NAME() "
                            "AS database_name"
                        ),
                    }
                ],
            }
        ],
    }


def redirect_state(
    tmp_path,
    monkeypatch,
):
    for name in (
        "DRAFTS",
        "PENDING",
        "PROCESSING",
        "RESULTS",
        "DONE",
        "REJECTED",
    ):
        path = (
            tmp_path
            / name.lower()
        )

        path.mkdir()

        monkeypatch.setattr(
            ingress,
            name,
            path,
        )


def test_submit_exists():
    assert callable(
        ingress.submit
    )


def test_readonly_sql_allowed_only_in_query():
    result = ingress.validate_template(
        readonly_sql_job(
            "INGRESS-SQL-1"
        )
    )

    assert (
        result["mode"]
        == "READ_ONLY_SQL"
    )

    bad = readonly_sql_job(
        "INGRESS-SQL-2"
    )

    bad["requester"]["sql"] = (
        "SELECT 1"
    )

    with pytest.raises(
        ValueError,
        match="FORBIDDEN_TEMPLATE_KEY:sql",
    ):
        ingress.validate_template(
            bad
        )


def test_completed_idempotency(
    tmp_path,
    monkeypatch,
):
    redirect_state(
        tmp_path,
        monkeypatch,
    )

    (
        ingress.RESULTS
        / "INGRESS-DONE.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = ingress.submit(
        readonly_job(
            "INGRESS-DONE"
        )
    )

    assert (
        result["status"]
        == "ALREADY_COMPLETED"
    )


def test_processing_idempotency(
    tmp_path,
    monkeypatch,
):
    redirect_state(
        tmp_path,
        monkeypatch,
    )

    (
        ingress.PROCESSING
        / "INGRESS-PROCESSING.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = ingress.submit(
        readonly_job(
            "INGRESS-PROCESSING"
        )
    )

    assert (
        result["status"]
        == "ALREADY_PROCESSING"
    )


def test_pending_idempotency(
    tmp_path,
    monkeypatch,
):
    redirect_state(
        tmp_path,
        monkeypatch,
    )

    (
        ingress.PENDING
        / "INGRESS-PENDING.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = ingress.submit(
        readonly_job(
            "INGRESS-PENDING"
        )
    )

    assert (
        result["status"]
        == "ALREADY_SUBMITTED"
    )


def test_queue_paths_are_repo_scoped():
    assert "universal-worker-queue" in str(
        ingress.DRAFTS
    )
    assert str(ingress.DRAFTS).endswith(
        ".git/universal-worker-queue/drafts"
    )


def test_submit_reuses_canonical_publisher():
    source = Path(
        ingress.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "def submit(" in source
    assert "publication = publish(" in source
