from pathlib import Path


JOB = Path(
    "/app/backend/core/scheduler/jobs/"
    "sync_comercial_v2_job.py"
)


def _source():
    return JOB.read_text(
        encoding="utf-8",
        errors="replace",
    )


def test_execute_accepts_single_unit_scope():
    text = _source()

    assert (
        "solo_unidades: Optional[List[str]] = None"
        in text
    )


def test_scope_is_applied_after_canonical_unit_load():
    text = _source()

    assert "if solo_unidades:" in text
    assert "unidades_sr = [" in text
    assert "unidades_mpro = [" in text
    assert "_unit_selected" in text


def test_unresolved_requested_unit_fails_closed():
    text = _source()

    assert "unresolved = sorted(" in text
    assert (
        "Unidades solicitadas no resueltas"
        in text
    )


def test_manual_runner_propagates_scope():
    text = _source()

    assert (
        "execute_sync_comercial_v2(\n"
        "                solo_unidades=solo_unidades,"
        in text
    )


def test_result_records_requested_scope():
    text = _source()

    assert '"solo_unidades":' in text


def test_no_hardcoded_business_units_added():
    text = _source()

    forbidden = (
        '"130MID"',
        '"130QRO"',
        '"CIENFUEGOS"',
        '"ESTELAR"',
        '"ORIGEN"',
        "'130MID'",
        "'130QRO'",
        "'CIENFUEGOS'",
        "'ESTELAR'",
        "'ORIGEN'",
    )

    for token in forbidden:
        assert token not in text
