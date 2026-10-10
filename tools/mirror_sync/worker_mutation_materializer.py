from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

V2_ACTIONS = {
    "replace_text",
    "insert_before",
    "insert_after",
    "append_once",
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _valid_sha(value: Any) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    )


def _atomic_write(target: Path, raw: bytes) -> None:
    tmp = target.with_name(target.name + ".mutation-v2.tmp")
    try:
        tmp.write_bytes(raw)
        tmp.replace(target)
    finally:
        if tmp.exists():
            tmp.unlink()


def apply_mutation(target: Path, action: dict[str, Any]) -> dict[str, Any]:
    kind = str(action.get("type") or "")
    if kind not in V2_ACTIONS:
        raise RuntimeError("UNSUPPORTED_V2_ACTION")

    if not target.is_file():
        raise RuntimeError("MUTATION_TARGET_MISSING")

    raw_before = target.read_bytes()
    text_before = raw_before.decode("utf-8")

    source_actual = _sha(raw_before)
    source_expected = str(action.get("source_sha256") or "")
    replacement = action.get("replacement")
    expected = int(action.get("expected_occurrences", 1))

    if not isinstance(replacement, str):
        raise RuntimeError("REPLACEMENT_REQUIRED")

    anchor = action.get("anchor")
    old_text = action.get("old_text")

    already_applied = False

    if kind == "append_once":
        already_applied = replacement in text_before
    elif kind == "insert_before":
        already_applied = (
            isinstance(anchor, str)
            and replacement + anchor in text_before
        )
    elif kind == "insert_after":
        already_applied = (
            isinstance(anchor, str)
            and anchor + replacement in text_before
        )
    elif kind == "replace_text":
        already_applied = (
            isinstance(old_text, str)
            and old_text not in text_before
            and replacement in text_before
        )

    if already_applied:
        return {
            "operation": kind,
            "state": "ALREADY_APPLIED",
            "source_sha256_expected": source_expected,
            "source_sha256_actual": source_actual,
            "source_integrity_valid": source_actual == source_expected,
            "anchor_occurrences_expected": expected,
            "anchor_occurrences_actual": 0,
            "transformation_applied": False,
            "duplicate_mutation": False,
            "final_sha256": source_actual,
            "bytes_before": len(raw_before),
            "bytes_after": len(raw_before),
        }

    if not _valid_sha(source_expected):
        raise RuntimeError("SOURCE_SHA_INVALID")

    if source_actual != source_expected:
        raise RuntimeError("SOURCE_SHA_MISMATCH")

    if kind == "append_once":
        actual = text_before.count(replacement)
        if actual != 0:
            raise RuntimeError("APPEND_ONCE_OCCURRENCE_MISMATCH")
        text_after = text_before + replacement

    elif kind in {"insert_before", "insert_after"}:
        if not isinstance(anchor, str) or not anchor:
            raise RuntimeError("ANCHOR_REQUIRED")

        actual = text_before.count(anchor)

        if actual == 0:
            raise RuntimeError("ANCHOR_NOT_FOUND")

        if actual != expected:
            raise RuntimeError("ANCHOR_OCCURRENCE_MISMATCH")

        if kind == "insert_before":
            text_after = text_before.replace(
                anchor, replacement + anchor
            )
        else:
            text_after = text_before.replace(
                anchor, anchor + replacement
            )

    else:
        if not isinstance(old_text, str) or not old_text:
            raise RuntimeError("OLD_TEXT_REQUIRED")

        actual = text_before.count(old_text)

        if actual == 0:
            raise RuntimeError("OLD_TEXT_NOT_FOUND")

        if actual != expected:
            raise RuntimeError("OLD_TEXT_OCCURRENCE_MISMATCH")

        text_after = text_before.replace(old_text, replacement)

    raw_after = text_after.encode("utf-8")
    _atomic_write(target, raw_after)

    return {
        "operation": kind,
        "state": "APPLIED",
        "source_sha256_expected": source_expected,
        "source_sha256_actual": source_actual,
        "source_integrity_valid": True,
        "anchor_occurrences_expected": expected,
        "anchor_occurrences_actual": actual,
        "transformation_applied": True,
        "duplicate_mutation": False,
        "final_sha256": _sha(raw_after),
        "bytes_before": len(raw_before),
        "bytes_after": len(raw_after),
    }
