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


def test_manual_uses_canonical_lock_manager():
    text = _source()

    assert (
        "from core.scheduler.locks "
        "import get_lock_manager"
        in text
    )

    assert (
        'lock_manager.get_lock(\n'
        '            "sync_comercial_v2"\n'
        '        )'
        in text
    )


def test_manual_lock_timeout_matches_scheduler_contract():
    text = _source()

    assert (
        "lock.acquire(\n"
        "            timeout_seconds=600\n"
        "        )"
        in text
    )


def test_manual_fails_closed_when_lock_not_acquired():
    text = _source()

    assert "if not acquired:" in text

    assert (
        "No se pudo adquirir el lock canónico "
        in text
    )


def test_manual_heartbeat_is_started():
    text = _source()

    assert (
        "lock.start_heartbeat_loop("
        in text
    )

    assert "interval_seconds=30" in text
    assert "extend_seconds=600" in text


def test_manual_releases_lock_in_finally():
    text = _source()

    assert "await lock.release()" in text


def test_manual_restores_incremental_days():
    import ast

    text = _source()
    tree = ast.parse(text)

    fn = None

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name
            == "run_sync_comercial_v2_manual"
        ):
            fn = node
            break

    assert fn is not None

    assignments = []

    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign):
            continue

        if len(node.targets) != 1:
            continue

        target = node.targets[0]

        if (
            isinstance(target, ast.Name)
            and target.id
            == "SYNC_INCREMENTAL_DAYS"
        ):
            assignments.append(
                ast.unparse(node.value)
            )

    assert "dias_atras" in assignments
    assert "previous_incremental_days" in assignments


def test_manual_propagates_single_unit_scope():
    text = _source()

    assert (
        "solo_unidades=solo_unidades"
        in text
    )


def test_no_alternate_lock_backend_added():
    text = _source()

    forbidden = (
        "MongoClient",
        "pymongo",
        "redis",
        "fcntl",
        "filelock",
        "/tmp/sync_comercial_v2.lock",
    )

    for token in forbidden:
        assert token not in text
