from pathlib import Path

import pytest

from tools.mirror_sync.worker_job_factory import canonicalize_job
from tools.mirror_sync.gate_chain_publisher import validate_template


def minimal_job():
    return {
        "job_id": "CANONICAL-1",
        "objective": "Validar frontera canonica",
        "mode": "READ_ONLY",
        "actions": [],
        "checks": [{"type": "git_diff_check"}],
        "requester": {
            "email": "ricardo@edarsa.com.mx",
            "source": "chatgpt-classic",
            "project": "Cavas Personales 7",
            "chat": "Cavas Personales 7",
        },
    }


def test_factory_supplies_transport_invariants_for_every_chat():
    job = canonicalize_job(minimal_job())

    assert job["schema"] == "edarsahub.worker-job.v2"
    assert job["target_repo"] == "rbalam/EDARSA_HUB"
    assert job["target_branch"] == "Edarsahub_Desarrollo"
    assert job["production_allowed"] is False
    assert job["human_summary_language"] == "es"
    assert job["scheduling"]["project_id"] == "Cavas Personales 7"
    assert job["scheduling"]["conflict_domains"] == ["GLOBAL_GIT_WRITER"]


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("target_repo", "other/repo"),
        ("target_branch", "main"),
        ("production_allowed", True),
        ("human_summary_language", "en"),
        ("schema", "other.schema"),
    ],
)
def test_factory_rejects_chat_specific_transport_drift(field, bad):
    job = minimal_job()
    job[field] = bad

    with pytest.raises(ValueError, match="CANONICAL_FIELD_CONFLICT"):
        canonicalize_job(job)


def test_publisher_uses_factory_instead_of_requiring_each_chat_to_align():
    job = minimal_job()
    normalized = validate_template(job)

    assert normalized["target_repo"] == "rbalam/EDARSA_HUB"
    assert normalized["target_branch"] == "Edarsahub_Desarrollo"
    assert normalized["human_summary_language"] == "es"


def test_requester_identity_is_preserved_as_metadata_not_transport_policy():
    job = minimal_job()
    job["requester"]["project"] = "Tablajeria"
    job["requester"]["chat"] = "Tablajerias 4"

    normalized = canonicalize_job(job)

    assert normalized["requester"]["project"] == "Tablajeria"
    assert normalized["requester"]["chat"] == "Tablajerias 4"
    assert normalized["target_repo"] == "rbalam/EDARSA_HUB"


def test_canonical_factory_is_wired_to_single_request_writer():
    root = Path(__file__).resolve().parents[2]
    publisher = (
        root / "tools/mirror_sync/gate_chain_publisher.py"
    ).read_text(encoding="utf-8")

    assert "from tools.mirror_sync.worker_job_factory import canonicalize_job" in publisher
    assert "template = canonicalize_job(template)" in publisher
