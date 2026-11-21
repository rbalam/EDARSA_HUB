from __future__ import annotations

import importlib.util
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = (
    ROOT
    / "backend"
    / "modules"
    / "cava_socios"
)


def _install_package():
    """Load pure cava_socios modules without executing package __init__."""

    modules_pkg = sys.modules.get(
        "modules"
    )

    if modules_pkg is None:
        modules_pkg = types.ModuleType(
            "modules"
        )
        modules_pkg.__path__ = [
            str(
                ROOT
                / "backend"
                / "modules"
            )
        ]
        sys.modules[
            "modules"
        ] = modules_pkg

    package_name = (
        "modules.cava_socios"
    )

    package = sys.modules.get(
        package_name
    )

    if package is None:
        package = types.ModuleType(
            package_name
        )
        package.__path__ = [
            str(MODULE_DIR)
        ]
        sys.modules[
            package_name
        ] = package


def _load(
    name: str,
    filename: str,
):
    fullname = (
        "modules.cava_socios."
        + name
    )

    if fullname in sys.modules:
        return sys.modules[
            fullname
        ]

    spec = (
        importlib.util.spec_from_file_location(
            fullname,
            MODULE_DIR / filename,
        )
    )

    assert spec is not None
    assert spec.loader is not None

    module = (
        importlib.util.module_from_spec(
            spec
        )
    )

    sys.modules[
        fullname
    ] = module

    spec.loader.exec_module(
        module
    )

    return module


_install_package()

migration_engine = _load(
    "migration_engine",
    "migration_engine.py",
)

adapter_sdk = _load(
    "adapter_sdk",
    "adapter_sdk.py",
)

adapter = _load(
    "cienfuegos_legacy_adapter",
    "cienfuegos_legacy_adapter.py",
)


def test_adapter_reuses_canonical_sdk():
    instance = (
        adapter.CienfuegosLegacyAdapter()
    )

    assert (
        instance.adapter_code()
        == "CAVAS_CIENFUEGOS"
    )

    capabilities = (
        instance.capabilities()
    )

    assert (
        capabilities.full_extract
        is True
    )
    assert (
        capabilities.delta_extract
        is False
    )


def test_identity_uses_canonical_source_identity():
    value = adapter.source_identity(
        source_instance_id="server-1",
        entity_type="clients",
        source_record_id=74,
    )

    assert isinstance(
        value,
        migration_engine.SourceIdentity,
    )

    assert (
        value.source_instance_id
        == "server-1"
    )
    assert (
        value.entity_type
        == "clients"
    )
    assert (
        value.source_record_id
        == "74"
    )

    assert value.idempotency_key()


def test_identity_key_is_stable():
    first = adapter.source_identity(
        source_instance_id="server-1",
        entity_type="clients",
        source_record_id=74,
    )

    second = adapter.source_identity(
        source_instance_id="server-1",
        entity_type="clients",
        source_record_id="74",
    )

    assert (
        first.idempotency_key()
        == second.idempotency_key()
    )


def test_duplicate_email_never_authorizes_auto_merge():
    result = (
        adapter.normalize_client(
            {
                "id": 1,
                "name": "Ana",
                "email": (
                    " DUPLICATE@EXAMPLE.COM "
                ),
            }
        )
    )

    assert (
        result["email"]
        == "duplicate@example.com"
    )
    assert (
        result[
            "auto_merge_allowed"
        ]
        is False
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("350", 350),
        ("375", 375),
        ("500", 500),
        ("695", 695),
        ("700", 700),
        ("750", 750),
        ("1000", 1000),
        ("1250", 1250),
    ],
)
def test_observed_capacities(
    raw,
    expected,
):
    assert (
        adapter.normalize_capacity_ml(
            raw
        )
        == expected
    )


def test_deleted_bottle_is_historical_evidence():
    result = (
        adapter.normalize_bottle_log(
            {
                "id": 38042,
                "bottle_id": 9000,
                "action": "out",
            },
            current_bottle_exists=False,
        )
    )

    assert (
        result[
            "historical_reference"
        ]
        is True
    )


def test_unknown_bottle_action_fails_closed():
    with pytest.raises(
        ValueError,
        match=(
            "CAVAS_BOTTLE_ACTION_"
            "UNSUPPORTED"
        ),
    ):
        adapter.normalize_bottle_log(
            {
                "id": 1,
                "bottle_id": 2,
                "action": "destroy",
            },
            current_bottle_exists=True,
        )


def test_attendance_is_not_canonical_sale():
    result = (
        adapter.normalize_attendance(
            {
                "id": 4017,
                "client_id": 74,
                "ticket_total": (
                    "1250.50"
                ),
            }
        )
    )

    assert (
        str(
            result[
                "ticket_total_evidence"
            ]
        )
        == "1250.50"
    )

    assert (
        result["canonical_sale"]
        is False
    )


def test_legacy_rbac_is_not_migrated():
    for entity in (
        "users",
        "roles",
        "acos",
        "aros",
        "aros_acos",
    ):
        assert (
            adapter.entity_disposition(
                entity
            )
            == "DO_NOT_MIGRATE"
        )


def test_external_record_uses_canonical_contract():
    occurred = datetime(
        2026,
        9,
        9,
        12,
        0,
        tzinfo=timezone.utc,
    )

    record = (
        adapter.external_record(
            source_instance_id=(
                "server-1"
            ),
            entity_type="bottles",
            source_record_id=884,
            payload={
                "legacy_status": "in",
            },
            original_occurred_at=(
                occurred
            ),
        )
    )

    assert isinstance(
        record,
        migration_engine.ExternalRecord,
    )

    assert (
        record.source_system
        == "CAVAS_CIENFUEGOS"
    )

    assert (
        record.original_occurred_at
        == occurred
    )


def test_naive_timestamp_fails_closed():
    with pytest.raises(
        ValueError,
        match=(
            "CAVAS_ORIGINAL_OCCURRED_AT_"
            "TIMEZONE_REQUIRED"
        ),
    ):
        adapter.external_record(
            source_instance_id=(
                "server-1"
            ),
            entity_type="clients",
            source_record_id=1,
            payload={},
            original_occurred_at=(
                datetime(
                    2026,
                    9,
                    9,
                    12,
                    0,
                )
            ),
        )
