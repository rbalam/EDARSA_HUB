from __future__ import annotations

import importlib.util
import sys
import types
from datetime import datetime
from pathlib import Path

from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "backend" / "modules" / "cava_socios"


def _install_package():
    modules_pkg = sys.modules.get("modules")
    if modules_pkg is None:
        modules_pkg = types.ModuleType("modules")
        modules_pkg.__path__ = [str(ROOT / "backend" / "modules")]
        sys.modules["modules"] = modules_pkg
    package_name = "modules.cava_socios"
    if package_name not in sys.modules:
        package = types.ModuleType(package_name)
        package.__path__ = [str(MODULE_DIR)]
        sys.modules[package_name] = package


def _load(name: str, filename: str):
    fullname = "modules.cava_socios." + name
    if fullname in sys.modules:
        return sys.modules[fullname]
    spec = importlib.util.spec_from_file_location(fullname, MODULE_DIR / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
    return module


_install_package()
domain = _load("domain", "domain.py")
migration = _load("migration_engine", "migration_engine.py")
sdk = _load("adapter_sdk", "adapter_sdk.py")
adapter = _load("cienfuegos_legacy_adapter", "cienfuegos_legacy_adapter.py")
dryrun = _load("cienfuegos_legacy_dryrun", "cienfuegos_legacy_dryrun.py")


def _dt():
    return datetime(2026, 9, 9, 12, 0)


def _resolver(record):
    return migration.MappingDecision(
        status=migration.MappingStatus.PROBABLE_MATCH,
        canonical_entity_type=record.identity.entity_type,
        reason="Gate2 requiere resolucion canonica posterior",
    )


def test_builds_external_records_and_localizes_legacy_timestamp():
    snapshot = dryrun.LegacySnapshot(
        clients=(
            {
                "id": 74,
                "name": "Cliente",
                "email": "CLIENTE@EXAMPLE.COM",
                "created": _dt(),
            },
        ),
        bottles=(
            {
                "id": 884,
                "name": "Botella",
                "capacity": "750",
                "cellar_id": 70,
                "status": "in",
                "created": _dt(),
            },
        ),
    )

    records, unsupported = dryrun.build_external_records(
        snapshot,
        source_instance_id="server-cavas",
        timezone_name="America/Mexico_City",
    )

    assert unsupported == 0
    assert len(records) == 2
    assert all(record.original_occurred_at.tzinfo is not None for record in records)
    assert records[0].identity.source_instance_id == "server-cavas"
    assert records[0].payload["auto_merge_allowed"] is False


def test_deleted_bottle_reference_is_preserved_as_historical_evidence():
    snapshot = dryrun.LegacySnapshot(
        bottle_logs=(
            {
                "id": 38042,
                "bottle_id": 9000,
                "action": "out",
                "created": _dt(),
            },
        ),
    )

    records, unsupported = dryrun.build_external_records(
        snapshot,
        source_instance_id="server-cavas",
        timezone_name="America/Mexico_City",
    )

    assert unsupported == 0
    assert records[0].payload["historical_reference"] is True


def test_timeless_relation_is_not_fabricated():
    snapshot = dryrun.LegacySnapshot(
        cellar_clients=(
            {
                "id": 1,
                "cellar_id": 70,
                "client_id": 74,
            },
        ),
    )

    records, unsupported = dryrun.build_external_records(
        snapshot,
        source_instance_id="server-cavas",
        timezone_name="America/Mexico_City",
    )

    assert records == ()
    assert unsupported == 1


def test_dry_run_is_review_required_not_execution_ready():
    snapshot = dryrun.LegacySnapshot(
        clients=(
            {
                "id": 74,
                "name": "Cliente",
                "created": _dt(),
            },
        ),
    )

    result = dryrun.run_dry_run(
        snapshot,
        source_instance_id="server-cavas",
        timezone_name="America/Mexico_City",
        resolver=_resolver,
    )

    assert result.summary.received == 1
    assert result.summary.review_required == 1
    assert result.summary.execution_ready is False
    assert result.source_counts["clients"] == 1


def test_reconciliation_requires_explicit_approved_difference():
    result = dryrun.reconcile_dry_run_counts(
        {"clients": 376, "bottles": 884},
        {"clients": 375, "bottles": 884},
    )

    assert result.certifiable is False

    approved = dryrun.reconcile_dry_run_counts(
        {"clients": 376, "bottles": 884},
        {"clients": 375, "bottles": 884},
        approved_differences={"clients": -1},
    )

    assert approved.certifiable is True


def test_timezone_is_explicit_mexico_context():
    zone = ZoneInfo("America/Mexico_City")
    value = dryrun._localize_legacy_datetime(_dt(), "America/Mexico_City")
    assert value.tzinfo is not None
    assert value.utcoffset() == zone.utcoffset(value)
