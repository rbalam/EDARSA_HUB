import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUB = (
    ROOT
    / "tools"
    / "mirror_sync"
    / "universal_job_result_publisher.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "worker_result_publisher_marker_contract",
        PUB,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_missing_marker_is_not_satisfied(tmp_path):
    module = load_module()

    marker = tmp_path / "job.json"

    assert not module.marker_satisfied(
        marker,
        {"certification": "NOT_CERTIFIED"},
    )


def test_noncertified_existing_marker_is_terminal(tmp_path):
    module = load_module()

    marker = tmp_path / "job.json"
    marker.write_text(
        "published=2026-08-30T00:00:00Z\n"
        "certification=NOT_CERTIFIED\n",
        encoding="utf-8",
    )

    assert module.marker_satisfied(
        marker,
        {"certification": "NOT_CERTIFIED"},
    )


def test_blocked_existing_marker_is_terminal(tmp_path):
    module = load_module()

    marker = tmp_path / "job.json"
    marker.write_text(
        "published=2026-08-30T00:00:00Z\n"
        "certification=BLOCKED\n",
        encoding="utf-8",
    )

    assert module.marker_satisfied(
        marker,
        {"certification": "BLOCKED"},
    )


def test_certified_existing_certified_marker_is_terminal(tmp_path):
    module = load_module()

    marker = tmp_path / "job.json"
    marker.write_text(
        "published=2026-08-30T00:00:00Z\n"
        "certification=CERTIFIED\n",
        encoding="utf-8",
    )

    assert module.marker_satisfied(
        marker,
        {"certification": "CERTIFIED"},
    )


def test_certified_can_upgrade_old_noncertified_marker(tmp_path):
    module = load_module()

    marker = tmp_path / "job.json"
    marker.write_text(
        "published=2026-08-30T00:00:00Z\n"
        "certification=NOT_CERTIFIED\n",
        encoding="utf-8",
    )

    assert not module.marker_satisfied(
        marker,
        {"certification": "CERTIFIED"},
    )
