from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLISHER = (
    ROOT
    / "tools"
    / "mirror_sync"
    / "universal_job_result_publisher.py"
)


def source():
    return PUBLISHER.read_text(encoding="utf-8")


def test_certification_requires_sha_bound_attestation():
    text = source()

    assert 'ATTESTATIONS / f"{source_sha}.json"' in text
    assert 'attestation.get("source_sha") != source_sha' in text
    assert 'attestation.get("job_id") != result.get("job_id")' in text

    assert (
        'str(attestation.get("tests", "")).upper() != "PASS"'
        in text
    )
    assert (
        'str(attestation.get("quality_gate", "")).upper() != "PASS"'
        in text
    )
    assert (
        'attestation.get("production_touched") is not False'
        in text
    )


def test_certification_requires_dev_mirror_convergence():
    text = source()

    assert 'development_head != mirror_head' in text
    assert '"merge-base",' in text
    assert '"--is-ancestor",' in text


def test_certification_requires_job_files_unchanged():
    text = source()

    assert '"diff",' in text
    assert '"--quiet",' in text
    assert 'source_sha,' in text
    assert 'development_head,' in text
    assert '*files_changed,' in text


def test_certified_contract_is_explicit():
    text = source()

    assert '"certification": "CERTIFIED"' in text
    assert '"work_completion": "COMPLETE"' in text
    assert '"percent_complete": 100' in text
    assert (
        '"SHA_BOUND_ATTESTATION_PLUS_DESCENDANT_CONVERGENCE"'
        in text
    )


def test_pending_result_remains_95_without_evidence():
    text = source()

    assert '"certification": "PENDING_AUDIT_EVIDENCE"' in text
    assert '"work_completion": "PENDING_CERTIFICATION"' in text
    assert '"percent_complete": 95' in text


def test_published_marker_does_not_block_later_certification():
    text = source()

    assert 'desired = public.get("certification")' in text
    assert '"certification=CERTIFIED" in marker_text' in text
    assert "marker.write_text(" in text
    assert "public.get('certification')" in text
    assert "certification=" in text


def test_production_false_is_mandatory():
    text = source()

    assert 'result.get("production_touched") is not False' in text
