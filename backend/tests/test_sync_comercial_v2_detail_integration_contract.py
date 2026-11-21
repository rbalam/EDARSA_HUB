from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JOB = ROOT / "backend" / "core" / "scheduler" / "jobs" / "sync_comercial_v2_job.py"


def _source():
    return JOB.read_text(encoding="utf-8")


def test_scheduler_imports_same_selective_backfill_used_by_manual_iscam_sync():
    text = _source()

    assert "from scripts.backfill_detalle_producto_pendientes import ejecutar_backfill" in text
    assert "ejecutar_backfill(" in text


def test_scheduler_detail_backfill_is_scoped_to_one_unit_and_one_day():
    text = _source()

    assert "fecha_inicio=dia" in text
    assert "fecha_fin=dia + timedelta(days=1)" in text
    assert "unidades=[unidad_codigo]" in text


def test_scheduler_skips_already_reconciled_detail_without_treating_it_as_failure():
    text = _source()

    assert '"YA_CONCILIADO"' in text


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


def test_detail_phase_does_not_spawn_a_subprocess():
    text = _source()
    detail_block = text.split("    def _sync_detalle_post_header(", 1)[1].split(
        "    def _sync_pagos_post_header(", 1
    )[0]

    assert "subprocess" not in detail_block
    assert "os.system(" not in detail_block


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
