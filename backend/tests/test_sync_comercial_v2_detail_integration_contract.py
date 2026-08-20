from pathlib import Path


JOB = Path(
    "/app/backend/core/scheduler/jobs/"
    "sync_comercial_v2_job.py"
)


def _source():
    return JOB.read_text(encoding="utf-8")


def test_scheduler_imports_canonical_detail_service():
    text = _source()

    assert (
        "sync_detalle_producto_canonico_dia"
        in text
    )


def test_scheduler_uses_runtime_v2_for_detail():
    text = _source()

    assert "_load_runtime_rows" in text
    assert "_runtime_for" in text


def test_scheduler_uses_canonical_pos_configuration():
    text = _source()

    assert "get_unidades_negocio_pos" in text
    assert "get_pos_config_for_unidad" in text


def test_detail_runs_only_after_successful_header_sync():
    text = _source()

    assert "resultado.success" in text
    assert "_sync_detalle_post_header" in text


def test_detail_commit_is_explicit():
    text = _source()

    assert "detail_commit: bool = True" in text
    assert "commit=detail_commit" in text


def test_detail_failure_is_recorded_separately():
    text = _source()

    assert "detalle_producto_status" in text
    assert "detalle_producto_error" in text


def test_no_hardcoded_unit_codes_added():
    text = _source()

    forbidden = [
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
    ]

    for value in forbidden:
        assert value not in text


def test_no_detail_subprocess_execution():
    text = _source()

    assert "subprocess" not in text
    assert "os.system(" not in text


def test_no_mongo_dependency_added():
    text = _source().lower()

    assert "pymongo" not in text
    assert "mongodb" not in text


def test_scheduler_detail_has_daily_traceability():
    text = _source()

    assert "detalle_producto_dias" in text
    assert '"fecha_operacion": dia.isoformat()' in text


def test_scheduler_detail_commit_is_injectable():
    text = _source()

    assert (
        "detail_commit: bool = True"
        in text
    )

    assert (
        "commit=detail_commit"
        in text
    )


def test_scheduler_has_no_hidden_env_for_detail_commit():
    text = _source()

    assert "DETAIL_COMMIT" not in text
    assert "SYNC_DETAIL_COMMIT" not in text
