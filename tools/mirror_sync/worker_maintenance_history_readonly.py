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


def collect() -> dict:
    directory = maintenance.INCIDENT_DIR
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("G4_CANONICAL_INCIDENT_DIR_UNAVAILABLE")
    files = sorted(directory.glob("*.json"))
    if len(files) > MAX_FILES:
        raise ValueError("G4_INCIDENT_LIMIT_EXCEEDED")

    # Reuse the registered Repair Planner and persistent Capability Registry.
    builtins = set(planner.registered_capabilities())
    learned = {cap.code for cap in registry.iter_learned_capabilities()}
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
        state = _bounded_code(state) or "UNKNOWN"
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
        "limitations": [
            "SUPERSEDED does not prove a certified repair",
            "Missing repair_job_id does not prove that a repair was never attempted",
            "This inventory does not read or mutate repair result files",
            "Only hashes of incident and job identifiers are exported",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()  # no caller-controlled paths or selectors
    try:
        result = collect()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        # Do not disclose local paths or contents on errors.
        print(json.dumps({"status": "FAIL", "error_code": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
