"""Dry-run canonico para migracion legacy CAVAS Cienfuegos.

Modulo puro: no abre conexiones, no ejecuta SQL y no escribe entidades
canonicas. Convierte snapshots ya extraidos por infraestructura externa en
ExternalRecord, ejecuta plan_dry_run y reconcilia conteos.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping
from zoneinfo import ZoneInfo

from .cienfuegos_legacy_adapter import (
    external_record,
    normalize_attendance,
    normalize_bottle,
    normalize_bottle_log,
    normalize_cellar,
    normalize_cellar_client,
    normalize_client,
)
from .migration_engine import (
    DryRunSummary,
    ExternalRecord,
    MappingDecision,
    MigrationMode,
    ReconciliationResult,
    plan_dry_run,
    reconcile_counts,
)


@dataclass(frozen=True)
class LegacySnapshot:
    clients: tuple[Mapping[str, Any], ...] = ()
    cellars: tuple[Mapping[str, Any], ...] = ()
    cellar_clients: tuple[Mapping[str, Any], ...] = ()
    bottles: tuple[Mapping[str, Any], ...] = ()
    bottle_logs: tuple[Mapping[str, Any], ...] = ()
    attendances: tuple[Mapping[str, Any], ...] = ()
    client_notes: tuple[Mapping[str, Any], ...] = ()
    media: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class DryRunResult:
    summary: DryRunSummary
    source_counts: Mapping[str, int]
    unsupported_timestamp_rows: int


def _localize_legacy_datetime(value: Any, timezone_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("CAVAS_LEGACY_TIMESTAMP_REQUIRED")
    zone = ZoneInfo(str(timezone_name or "").strip())
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=zone)
    return value.astimezone(zone)


def _timestamp(row: Mapping[str, Any], timezone_name: str) -> datetime:
    value = row.get("created") or row.get("modified")
    return _localize_legacy_datetime(value, timezone_name)


def _generic_payload(row: Mapping[str, Any]) -> dict[str, Any]:
    forbidden = {"password", "secret", "token", "api_key"}
    return {
        str(key): value
        for key, value in row.items()
        if str(key).lower() not in forbidden
    }


def build_external_records(
    snapshot: LegacySnapshot,
    *,
    source_instance_id: str,
    timezone_name: str,
) -> tuple[tuple[ExternalRecord, ...], int]:
    records: list[ExternalRecord] = []
    unsupported_timestamp_rows = 0
    current_bottles = {str(row.get("id")) for row in snapshot.bottles}

    def append(
        entity_type: str,
        row: Mapping[str, Any],
        payload: Mapping[str, Any],
        *,
        source_transaction_id: Any = None,
    ) -> None:
        nonlocal unsupported_timestamp_rows
        try:
            occurred_at = _timestamp(row, timezone_name)
        except ValueError:
            unsupported_timestamp_rows += 1
            return
        records.append(
            external_record(
                source_instance_id=source_instance_id,
                entity_type=entity_type,
                source_record_id=row.get("id"),
                source_transaction_id=source_transaction_id,
                payload=payload,
                original_occurred_at=occurred_at,
            )
        )

    for row in snapshot.clients:
        append("clients", row, normalize_client(row))
    for row in snapshot.cellars:
        append("cellars", row, normalize_cellar(row))
    for row in snapshot.cellar_clients:
        append("cellars_clients", row, normalize_cellar_client(row))
    for row in snapshot.bottles:
        append("bottles", row, normalize_bottle(row))
    for row in snapshot.bottle_logs:
        append(
            "bottle_logs",
            row,
            normalize_bottle_log(
                row,
                current_bottle_exists=str(row.get("bottle_id")) in current_bottles,
            ),
            source_transaction_id=row.get("attendance_id"),
        )
    for row in snapshot.attendances:
        append("attendances", row, normalize_attendance(row))
    for row in snapshot.client_notes:
        append("client_notes", row, _generic_payload(row))
    for row in snapshot.media:
        append("media", row, _generic_payload(row))

    return tuple(records), unsupported_timestamp_rows


def source_counts(snapshot: LegacySnapshot) -> dict[str, int]:
    return {
        "clients": len(snapshot.clients),
        "cellars": len(snapshot.cellars),
        "cellars_clients": len(snapshot.cellar_clients),
        "bottles": len(snapshot.bottles),
        "bottle_logs": len(snapshot.bottle_logs),
        "attendances": len(snapshot.attendances),
        "client_notes": len(snapshot.client_notes),
        "media": len(snapshot.media),
    }


def run_dry_run(
    snapshot: LegacySnapshot,
    *,
    source_instance_id: str,
    timezone_name: str,
    resolver: Callable[[ExternalRecord], MappingDecision],
) -> DryRunResult:
    records, unsupported = build_external_records(
        snapshot,
        source_instance_id=source_instance_id,
        timezone_name=timezone_name,
    )
    summary = plan_dry_run(
        records,
        mode=MigrationMode.HISTORICAL_MIGRATION,
        resolver=resolver,
    )
    return DryRunResult(
        summary=summary,
        source_counts=source_counts(snapshot),
        unsupported_timestamp_rows=unsupported,
    )


def reconcile_dry_run_counts(
    source: Mapping[str, int],
    projected: Mapping[str, int],
    *,
    approved_differences: Mapping[str, int] | None = None,
) -> ReconciliationResult:
    return reconcile_counts(
        source,
        projected,
        approved_differences=approved_differences,
    )
