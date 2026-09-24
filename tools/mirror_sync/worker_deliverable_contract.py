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



MAX_DELIVERABLE_SELECTOR_DEPTH: Final[int] = 32


def normalize_deliverable_specs(
    value: Any,
    required_deliverables: Any,
) -> dict[str, dict[str, Any]]:
    if value is None:
        return {}

    if not isinstance(value, dict):
        raise ValueError("DELIVERABLE_SPECS_NOT_OBJECT")

    required = set(
        normalize_required_deliverables(
            required_deliverables
        )
    )

    normalized: dict[str, dict[str, Any]] = {}

    for raw_name, raw_spec in value.items():
        if not isinstance(raw_name, str):
            raise ValueError(
                "DELIVERABLE_SPEC_INVALID_NAME"
            )

        name = raw_name.strip().upper()

        if not DELIVERABLE_NAME_RE.fullmatch(name):
            raise ValueError(
                "DELIVERABLE_SPEC_INVALID_NAME"
            )

        if name not in required:
            raise ValueError(
                "DELIVERABLE_SPEC_NOT_REQUIRED"
            )

        if name in normalized:
            raise ValueError(
                "DELIVERABLE_SPEC_DUPLICATED"
            )

        if not isinstance(raw_spec, dict):
            raise ValueError(
                "DELIVERABLE_SPEC_NOT_OBJECT"
            )

        source = raw_spec.get("source")
        selector = raw_spec.get("selector")

        if not isinstance(source, dict):
            raise ValueError(
                "DELIVERABLE_SOURCE_NOT_OBJECT"
            )

        if not isinstance(selector, dict):
            raise ValueError(
                "DELIVERABLE_SELECTOR_NOT_OBJECT"
            )

        check_type = str(
            source.get("check_type") or ""
        ).strip()

        if not check_type:
            raise ValueError(
                "DELIVERABLE_SOURCE_CHECK_TYPE_REQUIRED"
            )

        occurrence = source.get("occurrence")

        if (
            not isinstance(occurrence, int)
            or isinstance(occurrence, bool)
            or occurrence < 1
        ):
            raise ValueError(
                "DELIVERABLE_SOURCE_OCCURRENCE_INVALID"
            )

        selector_type = str(
            selector.get("type") or ""
        ).strip()

        if selector_type != "json_path":
            raise ValueError(
                "DELIVERABLE_SELECTOR_TYPE_UNSUPPORTED"
            )

        path = selector.get("path")

        if not isinstance(path, list):
            raise ValueError(
                "DELIVERABLE_SELECTOR_PATH_NOT_LIST"
            )

        if (
            not path
            or len(path)
            > MAX_DELIVERABLE_SELECTOR_DEPTH
        ):
            raise ValueError(
                "DELIVERABLE_SELECTOR_PATH_INVALID"
            )

        normalized_path: list[str | int] = []

        for item in path:
            if isinstance(item, bool):
                raise ValueError(
                    "DELIVERABLE_SELECTOR_PATH_ITEM_INVALID"
                )

            if isinstance(item, int):
                if item < 0:
                    raise ValueError(
                        "DELIVERABLE_SELECTOR_PATH_ITEM_INVALID"
                    )
                normalized_path.append(item)
                continue

            if isinstance(item, str):
                key = item.strip()

                if not key:
                    raise ValueError(
                        "DELIVERABLE_SELECTOR_PATH_ITEM_INVALID"
                    )

                normalized_path.append(key)
                continue

            raise ValueError(
                "DELIVERABLE_SELECTOR_PATH_ITEM_INVALID"
            )

        normalized[name] = {
            "source": {
                "check_type": check_type,
                "occurrence": occurrence,
            },
            "selector": {
                "type": "json_path",
                "path": normalized_path,
            },
        }

    return normalized


def resolve_check_source(
    checks: Any,
    source: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(checks, list):
        raise ValueError(
            "DELIVERABLE_CHECKS_NOT_LIST"
        )

    check_type = source["check_type"]
    occurrence = source["occurrence"]

    matches = [
        check
        for check in checks
        if isinstance(check, dict)
        and str(
            check.get("type") or ""
        ).strip() == check_type
    ]

    if len(matches) < occurrence:
        raise ValueError(
            "DELIVERABLE_SOURCE_CHECK_NOT_FOUND"
        )

    return matches[occurrence - 1]


def resolve_json_path(
    payload: Any,
    path: list[str | int],
) -> Any:
    current = payload

    for item in path:
        if isinstance(item, int):
            if not isinstance(current, list):
                raise ValueError(
                    "DELIVERABLE_SELECTOR_PATH_NOT_FOUND"
                )

            if item >= len(current):
                raise ValueError(
                    "DELIVERABLE_SELECTOR_PATH_NOT_FOUND"
                )

            current = current[item]
            continue

        if not isinstance(current, dict):
            raise ValueError(
                "DELIVERABLE_SELECTOR_PATH_NOT_FOUND"
            )

        if item not in current:
            raise ValueError(
                "DELIVERABLE_SELECTOR_PATH_NOT_FOUND"
            )

        current = current[item]

    return current


def materialize_deliverables(
    required_deliverables: Any,
    deliverable_specs: Any,
    checks: Any,
) -> dict[str, Any]:
    specs = normalize_deliverable_specs(
        deliverable_specs,
        required_deliverables,
    )

    materialized: dict[str, Any] = {}

    for name, spec in specs.items():
        source_check = resolve_check_source(
            checks,
            spec["source"],
        )

        payload = resolve_json_path(
            source_check,
            spec["selector"]["path"],
        )

        if deliverable_payload_present(payload):
            materialized[name] = payload

    return materialized


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
