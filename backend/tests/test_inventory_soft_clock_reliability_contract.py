"""Contract tests for the isolated SoftRestaurant MOVEMENTS GitHub owner.

This clock is not the physical inventory owner. Sales clocks and sync jobs are
intentionally outside the scope of this change.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
CLOCK = ROOT / ".github/workflows/inventory-softrestaurant-clock.yml"
JOB = ROOT / "backend/core/scheduler/jobs/sync_compras_job.py"


def _workflow_source():
    return CLOCK.read_text(encoding="utf-8")


def test_clock_never_cancels_in_flight_movements():
    source = _workflow_source()
    assert re.search(r"(?m)^  cancel-in-progress: false\s*$", source)
    assert not re.search(r"(?m)^  cancel-in-progress: true\s*$", source)
    match = re.search(r"(?m)^    timeout-minutes: (\d+)\s*$", source)
    assert match is not None
    assert int(match.group(1)) >= 90


def test_clock_is_explicitly_movements_only_and_softrestaurant():
    source = _workflow_source()
    assert 'SYNC_COMPRAS_SYSTEM_FILTER: "SOFT"' in source
    assert 'SYNC_COMPRAS_SCOPE: "INVENTORY_MOVEMENTS"' in source
    assert "PHYSICAL_INVENTORY_SCOPE=NOT_EXECUTED" in source


def test_physical_inventories_still_belong_to_full_compras_sync():
    source = JOB.read_text(encoding="utf-8")
    assert 'return _sync_compras_scope() == "INVENTORY_MOVEMENTS"' in source
    assert "if not _inventory_movements_only_scope():" in source
    assert "sync_inventarios_fisicos_from_server(" in source


def test_clock_does_not_trigger_commercial_sync():
    source = _workflow_source()
    assert "sync_comercial_v2" not in source
    assert "sync_comercial_abiertas_v2" not in source
