#!/usr/bin/env python3
"""Bounded, non-mutating G4 Maintenance inventory for the existing Universal Worker.

No caller-supplied paths, commands, SQL, or raw incident payloads are accepted.
Only aggregate and pseudonymized evidence leaves the shared Git common directory.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync import worker_maintenance_runtime as maintenance
from tools.mirror_sync import worker_repair_capability_registry as registry
from tools.mirror_sync import worker_repair_planner as planner

MAX_FILES = 5000
MAX_BYTES = 1_000_000
SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_.:-]{2,119}$")
SAFE_JOB_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")
RESULTS_DIR = (
    maintenance.GIT_COMMON_DIR
    / "universal-worker-queue"
    / "results"
)


def _fingerprint(value: str) -> str:
    return sha256(value.encode("utf-8", errors="replace")).hexdigest()[:20]


def _bounded_code(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value if SAFE_CODE.fullmatch(value) else "HASH:" + _fingerprint(value)


def _safe_file(path: Path, directory: Path) -> dict:
    # Explicitly reject links and oversized/unparseable records; never follow arbitrary paths.
    if path.is_symlink() or not path.is_file() or path.parent != directory:
        raise ValueError("G4_UNSAFE_INCIDENT_PATH")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("G4_INCIDENT_TOO_LARGE")
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError("G4_INCIDENT_NOT_OBJECT")
    return payload



def _safe_result_summary(repair_job_id: object) -> dict | None:
    if not isinstance(repair_job_id, str) or not SAFE_JOB_ID.fullmatch(repair_job_id):
        return None
    path = RESULTS_DIR / f"{repair_job_id}.json"
    if (
        path.is_symlink()
        or not path.is_file()
        or path.parent != RESULTS_DIR
        or path.stat().st_size > MAX_BYTES
    ):
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    percent = payload.get("percent_complete")
    return {
        "status": _bounded_code(payload.get("status")),
        "certification": _bounded_code(payload.get("certification")),
        "quality_gate": _bounded_code(payload.get("quality_gate")),
        "tests": _bounded_code(payload.get("tests")),
        "percent_complete": (
            percent if type(percent) is int and 0 <= percent <= 100 else None
        ),
        "production_touched": payload.get("production_touched") is True,
    }



def _superseded_linkage(reason: object) -> dict | None:
    if not isinstance(reason, str) or not reason.strip():
        return None
    value = reason.strip()
    successor_prefix = "SUPERSEDED_BY_CERTIFIED_SUCCESSOR:"
    incident_prefix = "SUPERSEDED_BY_CERTIFIED_INCIDENT:"

    if value.startswith(successor_prefix):
        successor_job_id = value[len(successor_prefix):].strip()
        safe_job_id = (
            successor_job_id
            if SAFE_JOB_ID.fullmatch(successor_job_id)
            else None
        )
        result = _safe_result_summary(safe_job_id)
        return {
            "reason_class": "CERTIFIED_SUCCESSOR",
            "successor_job_fingerprint": (
                _fingerprint(safe_job_id)
                if safe_job_id
                else None
            ),
            "successor_result": result,
            "successor_certified": bool(
                result
                and result.get("certification") == "CERTIFIED"
                and result.get("quality_gate") == "PASS"
                and result.get("tests") == "PASS"
                and result.get("production_touched") is False
            ),
        }

    if value.startswith(incident_prefix):
        successor_incident_id = value[len(incident_prefix):].strip()
        return {
            "reason_class": "CERTIFIED_INCIDENT",
            "successor_incident_fingerprint": (
                _fingerprint(successor_incident_id)
                if successor_incident_id
                else None
            ),
        }

    return {
        "reason_class": "OTHER",
        "reason_fingerprint": _fingerprint(value),
    }


def _learned_registry_summary(
    *,
    files: list[Path],
    directory: Path,
    learned_capabilities: tuple,
) -> dict:
    rows: list[dict] = []
    for file in files:
        payload = _safe_file(file, directory)
        inner = payload.get("incident")
        incident = inner if isinstance(inner, dict) else payload
        incident_id = incident.get("incident_id") or payload.get("incident_id")
        if not isinstance(incident_id, str) or not incident_id:
            continue
        rows.append({
            "incident_id": incident_id,
            "problem_signature": (
                incident.get("problem_signature")
                or payload.get("problem_signature")
            ),
            "capability_code": (
                incident.get("capability_code")
                or payload.get("capability_code")
            ),
        })

    capabilities: list[dict] = []
    for capability in learned_capabilities:
        code = str(getattr(capability, "code", "") or "")
        problem_signature = str(
            getattr(capability, "problem_signature", "") or ""
        )
        learned_from = str(
            getattr(capability, "learned_from_incident", "") or ""
        )
        evidence = getattr(capability, "evidence", {}) or {}
        reuse_rows = [
            row
            for row in rows
            if row["incident_id"] != learned_from
            and (
                (code and row["capability_code"] == code)
                or (
                    problem_signature
                    and row["problem_signature"] == problem_signature
                )
            )
        ]
        source_job_id = evidence.get("source_job_id")
        repair_job_id = evidence.get("repair_job_id")
        capabilities.append({
            "code": _bounded_code(code),
            "problem_signature": (
                "SIG:" + _fingerprint(problem_signature)
                if problem_signature
                else None
            ),
            "learned_from_incident_fingerprint": (
                _fingerprint(learned_from)
                if learned_from
                else None
            ),
            "evidence_source_job_fingerprint": (
                _fingerprint(source_job_id)
                if isinstance(source_job_id, str) and source_job_id
                else None
            ),
            "evidence_repair_job_fingerprint": (
                _fingerprint(repair_job_id)
                if isinstance(repair_job_id, str) and repair_job_id
                else None
            ),
            "evidence_certified": (
                evidence.get("certified") is True
                and str(evidence.get("certification") or "").upper()
                == "CERTIFIED"
            ),
            "reusable": bool(
                getattr(capability, "reusable", False)
            ),
            "incident_pattern_count": len(
                tuple(getattr(capability, "incident_patterns", ()) or ())
            ),
            "registered_incident_count": len(
                tuple(getattr(capability, "incident_ids", ()) or ())
            ),
            "reuse_observed": bool(reuse_rows),
            "reuse_incident_count": len(reuse_rows),
            "reuse_incident_fingerprints": [
                _fingerprint(row["incident_id"])
                for row in reuse_rows[:10]
            ],
        })

    return {
        "count": len(capabilities),
        "reusable_count": sum(
            1 for item in capabilities if item["reusable"]
        ),
        "reuse_observed_count": sum(
            1 for item in capabilities if item["reuse_observed"]
        ),
        "capabilities": capabilities[:50],
        "raw_identifiers_exposed": False,
    }


def _focused_linkage(
    source_job_id: str,
    *,
    files: list[Path],
    directory: Path,
    learned_capabilities: tuple,
) -> dict:
    if not SAFE_JOB_ID.fullmatch(source_job_id):
        raise ValueError("G4_SOURCE_JOB_INVALID")

    rows: list[dict] = []
    by_incident: dict[str, dict] = {}
    for file in files:
        payload = _safe_file(file, directory)
        inner = payload.get("incident")
        incident = inner if isinstance(inner, dict) else payload
        incident_id = incident.get("incident_id") or payload.get("incident_id")
        if not isinstance(incident_id, str) or not incident_id:
            continue
        row = {
            "incident_id": incident_id,
            "source_job_id": (
                incident.get("source_job_id")
                or payload.get("source_job_id")
            ),
            "state": str(
                payload.get("state")
                or incident.get("state")
                or "UNKNOWN"
            ).upper(),
            "problem_signature": (
                incident.get("problem_signature")
                or payload.get("problem_signature")
            ),
            "capability_code": (
                incident.get("capability_code")
                or payload.get("capability_code")
            ),
            "repair_job_id": (
                payload.get("repair_job_id")
                or incident.get("repair_job_id")
            ),
            "superseded_reason": (
                payload.get("superseded_reason")
                or incident.get("superseded_reason")
            ),
        }
        rows.append(row)
        by_incident[incident_id] = row

    selected_ids = {
        row["incident_id"]
        for row in rows
        if row["source_job_id"] == source_job_id
    }
    for capability in learned_capabilities:
        evidence = getattr(capability, "evidence", {}) or {}
        learned_from = str(
            getattr(capability, "learned_from_incident", "") or ""
        )
        if evidence.get("source_job_id") == source_job_id and learned_from:
            selected_ids.add(learned_from)

    known_codes = set(planner.registered_capabilities()) | {
        str(getattr(capability, "code", "") or "")
        for capability in learned_capabilities
    }
    matches: list[dict] = []
    for incident_id in sorted(selected_ids):
        row = by_incident.get(incident_id)
        if row is None:
            continue

        capability_rows = []
        effective_repair_job_id = row["repair_job_id"]
        for capability in learned_capabilities:
            learned_from_match = (
                getattr(capability, "learned_from_incident", None)
                == incident_id
            )
            incident_ids = tuple(
                getattr(capability, "incident_ids", ()) or ()
            )
            if not learned_from_match and incident_id not in incident_ids:
                continue

            evidence = getattr(capability, "evidence", {}) or {}
            if not effective_repair_job_id:
                candidate_repair = evidence.get("repair_job_id")
                if (
                    isinstance(candidate_repair, str)
                    and SAFE_JOB_ID.fullmatch(candidate_repair)
                ):
                    effective_repair_job_id = candidate_repair

            code = str(getattr(capability, "code", "") or "")
            problem_signature = str(
                getattr(capability, "problem_signature", "") or ""
            )
            reuse_rows = [
                other
                for other in rows
                if other["incident_id"] != incident_id
                and (
                    other["capability_code"] == code
                    or (
                        problem_signature
                        and other["problem_signature"] == problem_signature
                    )
                )
            ]
            capability_rows.append({
                "code": _bounded_code(code),
                "learned_from_incident_match": learned_from_match,
                "evidence_source_job_match": (
                    evidence.get("source_job_id") == source_job_id
                ),
                "evidence_repair_job_match": (
                    isinstance(effective_repair_job_id, str)
                    and evidence.get("repair_job_id")
                    == effective_repair_job_id
                ),
                "evidence_certified": (
                    evidence.get("certified") is True
                    and str(evidence.get("certification") or "").upper()
                    == "CERTIFIED"
                ),
                "reusable": bool(getattr(capability, "reusable", False)),
                "reuse_observed": bool(reuse_rows),
                "reuse_incident_count": len(reuse_rows),
                "reuse_incident_fingerprints": [
                    _fingerprint(other["incident_id"])
                    for other in reuse_rows[:10]
                ],
            })

        repair_summary = _safe_result_summary(effective_repair_job_id)
        supersession = _superseded_linkage(
            row.get("superseded_reason")
        )
        signature = row["problem_signature"]
        capability_code = row["capability_code"]
        matches.append({
            "incident_fingerprint": _fingerprint(incident_id),
            "state": _bounded_code(row["state"]),
            "signature": (
                "SIG:" + _fingerprint(signature)
                if isinstance(signature, str) and signature
                else None
            ),
            "capability": (
                _bounded_code(capability_code)
                if isinstance(capability_code, str) and capability_code
                else None
            ),
            "capability_registered": (
                isinstance(capability_code, str)
                and capability_code in known_codes
            ),
            "repair_job_fingerprint": (
                _fingerprint(effective_repair_job_id)
                if isinstance(effective_repair_job_id, str)
                and effective_repair_job_id
                else None
            ),
            "repair_result": repair_summary,
            "supersession": supersession,
            "certified_successor_observed": bool(
                supersession
                and supersession.get("reason_class")
                == "CERTIFIED_SUCCESSOR"
                and supersession.get("successor_certified") is True
            ),
            "learned_capabilities": capability_rows,
            "linkage_certified": bool(
                repair_summary
                and repair_summary.get("certification") == "CERTIFIED"
                and repair_summary.get("quality_gate") == "PASS"
                and repair_summary.get("tests") == "PASS"
                and repair_summary.get("production_touched") is False
                and any(
                    item["learned_from_incident_match"]
                    and item["evidence_source_job_match"]
                    and item["evidence_certified"]
                    and item["evidence_repair_job_match"]
                    for item in capability_rows
                )
            ),
        })

    return {
        "source_job_fingerprint": _fingerprint(source_job_id),
        "match_count": len(matches),
        "matches": matches,
        "raw_identifiers_exposed": False,
    }


def collect(source_job_id: str | None = None) -> dict:
    directory = maintenance.INCIDENT_DIR
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("G4_CANONICAL_INCIDENT_DIR_UNAVAILABLE")
    files = sorted(directory.glob("*.json"))
    if len(files) > MAX_FILES:
        raise ValueError("G4_INCIDENT_LIMIT_EXCEEDED")

    # Reuse the registered Repair Planner and persistent Capability Registry.
    builtins = set(planner.registered_capabilities())
    learned_capabilities = tuple(
        registry.iter_learned_capabilities()
    )
    learned = {cap.code for cap in learned_capabilities}
    known = builtins | learned
    statuses: Counter[str] = Counter()
    signatures: Counter[str] = Counter()
    used_capabilities: Counter[str] = Counter()
    missing: Counter[str] = Counter()
    attempts: Counter[str] = Counter()
    repair_references: Counter[str] = Counter()
    source_refs: Counter[str] = Counter()
    pending: list[dict] = []
    production_flags = 0

    for file in files:
        payload = _safe_file(file, directory)
        inner = payload.get("incident")
        incident = inner if isinstance(inner, dict) else payload
        state = str(payload.get("state") or incident.get("state") or "UNKNOWN").upper()
        state = state if state in {"REPAIR_REQUIRED", "REJECTED", "SUPERSEDED", "REPAIRED_PENDING_AUDIT", "CERTIFIED", "AUDITED", "CLOSED"} else "UNKNOWN"
        statuses[state] += 1
        signature = incident.get("problem_signature") or payload.get("problem_signature")
        capability = incident.get("capability_code") or payload.get("capability_code")
        source_id = incident.get("source_job_id") or payload.get("source_job_id")
        repair_id = payload.get("repair_job_id") or incident.get("repair_job_id")
        incident_id = incident.get("incident_id") or payload.get("incident_id")
        if not isinstance(incident_id, str) or not incident_id:
            missing["incident_id"] += 1
        if not isinstance(signature, str) or not signature:
            missing["problem_signature"] += 1
        else:
            signatures["SIG:" + _fingerprint(signature)] += 1
        if not isinstance(capability, str) or not capability:
            missing["capability_code"] += 1
        else:
            used_capabilities[_bounded_code(capability) if capability in known else "UNKNOWN:" + _fingerprint(capability)] += 1
        if not isinstance(source_id, str) or not source_id:
            missing["source_job_id"] += 1
        else:
            source_refs[_fingerprint(source_id)] += 1
        if not isinstance(repair_id, str) or not repair_id:
            missing["repair_job_id"] += 1
        else:
            repair_references[_fingerprint(repair_id)] += 1
        raw_attempts = payload.get("attempts", incident.get("attempts", 0))
        if type(raw_attempts) is not int or raw_attempts < 0:
            missing["invalid_attempts"] += 1
        else:
            attempts[str(min(raw_attempts, 3)) if raw_attempts < 3 else "3_plus"] += 1
        if payload.get("production_touched") is True or incident.get("production_touched") is True:
            production_flags += 1
        if state in {"REPAIR_REQUIRED", "REJECTED"}:
            pending.append({
                "incident_fingerprint": _fingerprint(incident_id or file.stem),
                "state": state,
                "signature": ("SIG:" + _fingerprint(signature)) if isinstance(signature, str) else None,
                "capability": _bounded_code(capability) if isinstance(capability, str) and capability in known else None,
                "capability_registered": capability in known if isinstance(capability, str) else False,
                "source_job_fingerprint": _fingerprint(source_id) if isinstance(source_id, str) else None,
                "repair_job_fingerprint": _fingerprint(repair_id) if isinstance(repair_id, str) else None,
                "attempts": raw_attempts if type(raw_attempts) is int and 0 <= raw_attempts <= 100 else None,
            })

    return {
        "schema": "edarsahub.worker-maintenance-history-readonly.v1",
        "mode": "READ_ONLY",
        "status": "PASS",
        "certification": "EVIDENCE_ONLY_NOT_G4_CERTIFIED",
        "production_allowed": False,
        "incident_count": len(files),
        "states": dict(sorted(statuses.items())),
        "missing_fields": dict(sorted(missing.items())),
        "attempts": dict(sorted(attempts.items())),
        "recurring_signatures": [
            {"signature": key, "count": count}
            for key, count in signatures.most_common(25) if count > 1
        ],
        "duplicate_source_refs": sum(n - 1 for n in source_refs.values() if n > 1),
        "duplicate_repair_refs": sum(n - 1 for n in repair_references.values() if n > 1),
        "registry_builtin_count": len(builtins),
        "registry_learned_count": len(learned),
        "unregistered_referenced_capabilities": sorted(
            key for key in used_capabilities if key not in known
        )[:50],
        "pending_total": len(pending),
        "pending_sample": pending[:50],
        "production_touched_records": production_flags,
        "learned_registry": _learned_registry_summary(
            files=files,
            directory=directory,
            learned_capabilities=learned_capabilities,
        ),
        "focused_linkage": (
            _focused_linkage(
                source_job_id,
                files=files,
                directory=directory,
                learned_capabilities=learned_capabilities,
            )
            if source_job_id
            else None
        ),
        "limitations": [
            "SUPERSEDED does not prove a certified repair",
            "Missing repair_job_id does not prove that a repair was never attempted",
            "Result artifacts are read only for bounded sanitized summaries; they are never mutated",
            "Only hashes of incident and job identifiers are exported",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-job-id")
    args = parser.parse_args()
    try:
        result = collect(args.source_job_id)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        # Do not disclose local paths or contents on errors.
        print(json.dumps({"status": "FAIL", "error_code": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
