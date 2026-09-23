"""Canonical required-deliverables contract for Universal Worker jobs.

Validates declared deliverable names and evaluates whether required outputs
have actually been materialized.

This helper performs no repository scan, shell, Git, SQL, network, Production,
queue, dispatcher, control-plane or AI-model operation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Final


MAX_REQUIRED_DELIVERABLES: Final[int] = 128
DELIVERABLE_NAME_RE: Final = re.compile(r"^[A-Z][A-Z0-9_]{1,127}$")


@dataclass(frozen=True)
class DeliverableEvaluation:
    required: tuple[str, ...]
    completed: tuple[str, ...]
    missing: tuple[str, ...]
    complete: bool


def normalize_required_deliverables(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()

    if not isinstance(value, list):
        raise ValueError("REQUIRED_DELIVERABLES_NOT_LIST")

    if not value:
        raise ValueError("REQUIRED_DELIVERABLES_EMPTY")

    if len(value) > MAX_REQUIRED_DELIVERABLES:
        raise ValueError("REQUIRED_DELIVERABLES_TOO_MANY")

    normalized: list[str] = []

    for raw in value:
        if not isinstance(raw, str):
            raise ValueError("REQUIRED_DELIVERABLE_INVALID")

        name = raw.strip().upper()

        if not DELIVERABLE_NAME_RE.fullmatch(name):
            raise ValueError("REQUIRED_DELIVERABLE_INVALID")

        if name in normalized:
            raise ValueError("REQUIRED_DELIVERABLE_DUPLICATED")

        normalized.append(name)

    return tuple(normalized)


def normalize_materialized_deliverables(value: Any) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, dict):
        raise ValueError("DELIVERABLES_NOT_OBJECT")

    normalized: dict[str, Any] = {}

    for raw_name, payload in value.items():
        if not isinstance(raw_name, str):
            raise ValueError("DELIVERABLE_INVALID_NAME")

        name = raw_name.strip().upper()

        if not DELIVERABLE_NAME_RE.fullmatch(name):
            raise ValueError("DELIVERABLE_INVALID_NAME")

        normalized[name] = payload

    return normalized


def deliverable_payload_present(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)

    return True


def evaluate_deliverables(
    required_deliverables: Any,
    deliverables: Any,
) -> DeliverableEvaluation:
    required = normalize_required_deliverables(required_deliverables)

    if not required:
        return DeliverableEvaluation(
            required=(),
            completed=(),
            missing=(),
            complete=True,
        )

    materialized = normalize_materialized_deliverables(deliverables)

    completed = tuple(
        name
        for name in required
        if name in materialized
        and deliverable_payload_present(materialized[name])
    )

    missing = tuple(
        name
        for name in required
        if name not in completed
    )

    return DeliverableEvaluation(
        required=required,
        completed=completed,
        missing=missing,
        complete=not missing,
    )
