#!/usr/bin/env python3
"""Canonical batched, idempotent SQL projection & backfill for Universal Worker V4 (GATE-M1).

This module:
- NEVER runs raw INSERT/UPDATE/DDL; writes exclusively via the 4 narrow SPs:
  dbo.sp_Worker_UpsertJobState, dbo.sp_Worker_UpsertIncident,
  dbo.sp_Worker_RecordRecoveryEvent, dbo.sp_Worker_UpsertCapability.
- Enforces fail-closed environment identity (DB_NAME() == 'EDARSAHUB') and production_allowed=False.
- Reuses canonical readers: worker_result_reader, worker_result_status,
  worker_maintenance_runtime, worker_repair_capability_registry, worker_repair_auto_loop.
- Preserves SUBMITTED / INTEGRATED / CERTIFIED / ACTIVE_IN_PREVIEW separation without
  inventing Preview validation evidence or modifying historical files.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
for candidate in (str(ROOT), str(BACKEND), str(Path(__file__).resolve().parent)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from tools.mirror_sync import worker_maintenance_runtime as maintenance
from tools.mirror_sync import worker_repair_auto_loop as auto_loop
from tools.mirror_sync import worker_repair_capability_registry as learned_registry
from tools.mirror_sync.worker_result_integrity import validate_terminal_result_payload
from tools.mirror_sync.worker_result_status import build_differentiated_evidence

QUEUE_ROOT = ROOT / ".git" / "universal-worker-queue"
EXPECTED_DEV_DATABASE = "EDARSAHUB"
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA64_RE = re.compile(r"^[0-9a-f]{64}$")
_CERTIFIED_SET = frozenset(
    {
        "CERTIFIED",
        "CERTIFIED_READ_ONLY",
        "CERTIFIED_OPERATIONAL",
        "CERTIFIED_FRONTEND_BUILD",
    }
)


class WorkerSqlProjectionError(RuntimeError):
    """Fail-closed error for unauthorized or inconsistent SQL projection."""


def _clean_str(value: Any, max_len: int | None = None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:max_len] if max_len is not None else text


def _clean_sha(value: Any, length: int) -> str | None:
    text = _clean_str(value)
    if not text:
        return None
    low = text.lower()
    pattern = _SHA40_RE if length == 40 else _SHA64_RE
    return low if pattern.fullmatch(low) else None


def _parse_utc_timestamp(value: Any) -> str | None:
    text = _clean_str(value)
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        return None


def _load_json_dict(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _stream_git_tree_json(ref_prefix: str) -> dict[str, tuple[dict[str, Any] | None, str]]:
    """Read all JSON blobs under a git ref:dir using git ls-tree + cat-file --batch."""
    ref, subdir = ref_prefix.split(":", 1)
    ls = subprocess.run(
        ["git", "-C", str(ROOT), "ls-tree", "-r", ref, subdir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if ls.returncode != 0 or not ls.stdout:
        return {}

    entries: list[tuple[str, str]] = []
    for line in ls.stdout.splitlines():
        if "\t" not in line:
            continue
        meta, path = line.split("\t", 1)
        if not path.endswith(".json"):
            continue
        parts = meta.split()
        if len(parts) < 3 or parts[1] != "blob":
            continue
        blob_sha = parts[2]
        job_stem = Path(path).stem
        entries.append((job_stem, blob_sha))

    if not entries:
        return {}

    batch_input = "".join(f"{sha}\n" for _, sha in entries).encode("utf-8")
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "--batch"],
        input=batch_input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return {}

    raw = proc.stdout
    pos = 0
    parsed: dict[str, tuple[dict[str, Any] | None, str]] = {}
    for job_stem, blob_sha in entries:
        nl = raw.find(b"\n", pos)
        if nl == -1:
            break
        header = raw[pos:nl].decode("utf-8", errors="replace").split()
        pos = nl + 1
        if len(header) < 3 or header[1] == "missing":
            parsed[job_stem] = (None, "MISSING_BLOB")
            continue
        size = int(header[2])
        content = raw[pos : pos + size]
        pos += size + 1  # trailing newline
        if not content:
            parsed[job_stem] = (None, "EMPTY_BLOB")
            continue
        try:
            obj = json.loads(content.decode("utf-8"))
            if isinstance(obj, dict):
                parsed[job_stem] = (obj, "OK")
            else:
                parsed[job_stem] = (None, "NOT_OBJECT")
        except Exception:
            parsed[job_stem] = (None, "INVALID_JSON")
    return parsed


def _parse_published_marker(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                out[k.strip().lower()] = v.strip()
    except Exception:
        pass
    return out


def normalize_job_record(
    *,
    job_id: str,
    request_payload: dict[str, Any] | None = None,
    result_payload: dict[str, Any] | None = None,
    marker: dict[str, str] | None = None,
    preview_evidence: dict[str, Any] | None = None,
    local_state_hint: str | None = None,
    provenance_source: str = "GIT_RESULTS_BACKFILL",
) -> tuple[dict[str, Any] | None, str | None]:
    """Normalize one historical or runtime job into canonical sp_Worker_UpsertJobState params.

    Returns (record_dict, rejection_reason). Never invents Preview validation or sets ProductionTouched=1.
    """
    clean_job_id = _clean_str(job_id, 128)
    if not clean_job_id:
        return None, "EMPTY_JOB_ID"

    req = request_payload if isinstance(request_payload, dict) else {}
    res = result_payload if isinstance(result_payload, dict) else {}
    mk = marker if isinstance(marker, dict) else {}

    # Reject any record claiming production_touched=True (fail-closed)
    if res.get("production_touched") is True or req.get("production_allowed") is True:
        return None, "PRODUCTION_POLICY_VIOLATION"

    scheduling = req.get("scheduling") if isinstance(req.get("scheduling"), dict) else {}
    requester = req.get("requester") if isinstance(req.get("requester"), dict) else {}

    project_id = _clean_str(
        scheduling.get("project_id") or requester.get("project") or "UNSPECIFIED",
        100,
    ) or "UNSPECIFIED"
    bounded_context = _clean_str(
        scheduling.get("bounded_context") or "UNSPECIFIED",
        120,
    ) or "UNSPECIFIED"
    capability_code = _clean_str(req.get("capability") or res.get("capability"), 120)
    mode = _clean_str(res.get("slot_class") or res.get("mode") or req.get("mode") or "MUTATION", 40) or "MUTATION"
    objective = _clean_str(req.get("objective") or res.get("summary_es") or "", 1000) or ""
    priority_class = _clean_str(scheduling.get("priority_class") or "NORMAL", 20) or "NORMAL"
    requester_email = _clean_str(requester.get("email"), 255)
    requester_source = _clean_str(requester.get("source"), 120)
    schema_version = _clean_str(res.get("schema") or req.get("schema") or "edarsahub.worker-job.v2", 40) or "edarsahub.worker-job.v2"

    commit_sha = _clean_sha(
        res.get("certified_source_sha")
        or res.get("development_sha")
        or res.get("candidate_sha")
        or res.get("commit_sha"),
        40,
    )
    pub_commit = _clean_sha(
        res.get("published_result_commit") or mk.get("commit"),
        40,
    )
    res_sha256 = _clean_sha(res.get("published_result_sha256") or res.get("result_sha256"), 64)
    att_sha256 = _clean_sha(res.get("attestation_sha256"), 64)

    terminal_valid = False
    reconciliation_status = "RECONCILED"
    if res:
        try:
            validate_terminal_result_payload(res, expected_job_id=clean_job_id)
            terminal_valid = True
        except ValueError:
            terminal_valid = False
            reconciliation_status = "HISTORICAL_INVALID_RESULT"

        diff_ev = build_differentiated_evidence(
            res,
            job_id=clean_job_id,
            terminal_valid=terminal_valid,
            commit_sha=commit_sha,
            preview_evidence=preview_evidence,
        )
        lifecycle_stage = diff_ev["lifecycle_stage"]
        ev_break = diff_ev["evidence_breakdown"]
        execution_status = _clean_str(res.get("status") or "UNKNOWN", 60) or "UNKNOWN"
        cert_status = _clean_str(res.get("certification") or "NOT_CERTIFIED", 60) or "NOT_CERTIFIED"
        if cert_status == "PENDING_AUDIT_EVIDENCE" and mk.get("certification") in _CERTIFIED_SET:
            # Preserve exact factual reconciliation status without fabricating certification
            reconciliation_status = "MARKER_RESULT_DRIFT_PENDING_RECONCILE"
        elif cert_status == "PENDING_AUDIT_EVIDENCE":
            reconciliation_status = "HISTORICAL_PENDING_RECONCILIATION"
        elif not terminal_valid:
            reconciliation_status = "HISTORICAL_INVALID_RESULT"
        else:
            reconciliation_status = _clean_str(res.get("reconciliation_status") or "RECONCILED", 60) or "RECONCILED"

        raw_pct = res.get("percent_complete")
        pct = int(raw_pct) if isinstance(raw_pct, int) and not isinstance(raw_pct, bool) and 0 <= raw_pct <= 100 else 0
        raw_blockers = res.get("blockers")
        blockers_json = (
            json.dumps(raw_blockers, ensure_ascii=False)
            if isinstance(raw_blockers, list)
            else None
        )
        record = {
            "JobID": clean_job_id,
            "SchemaVersion": schema_version,
            "SourceJobID": _clean_str(res.get("source_job_id") or req.get("source_job_id"), 128),
            "ProjectID": project_id,
            "BoundedContext": bounded_context,
            "CapabilityCode": capability_code,
            "Mode": mode,
            "Objective": objective,
            "PriorityClass": priority_class,
            "RequesterUsuarioID": None,
            "RequesterEmail": requester_email,
            "RequesterSource": requester_source,
            "OwnerAgentOrDev": _clean_str(res.get("executor") or requester.get("chat"), 120),
            "ChainID": _clean_str(req.get("chain_id"), 120),
            "GateID": _clean_str(req.get("gate_id"), 120),
            "DependsOnJobID": _clean_str(req.get("depends_on_job_id"), 128),
            "LifecycleStage": lifecycle_stage,
            "ExecutionStatus": execution_status,
            "QualityGate": ev_break["quality_gate"][:20],
            "TestsStatus": ev_break["tests"][:20],
            "IntegrationStatus": "INTEGRATED" if execution_status == "INTEGRATED" else ("NOT_APPLICABLE" if mode == "READ_ONLY" else "PENDING"),
            "GitSyncStatus": _clean_str(ev_break["git_sync"], 60),
            "CertificationStatus": cert_status,
            "OperationalValidationStatus": diff_ev["operational_validation_status"],
            "PreviewActivated": 1 if diff_ev["operational_validated"] else 0,
            "OperationalTests": ev_break["operational_tests"][:20],
            "FunctionalResult": ev_break["functional_result"][:20],
            "TerminalResultValid": 1 if terminal_valid else 0,
            "PercentComplete": pct,
            "DevelopmentCommitSHA": commit_sha,
            "PublishedResultCommitSHA": pub_commit,
            "ResultSHA256": res_sha256,
            "AttestationSHA256": att_sha256,
            "ProductionTouched": 0,
            "RecoveryAttempts": 0,
            "BlockersJson": blockers_json,
            "NextRecommendedAction": _clean_str(res.get("next_allowed_step"), 120),
            "ReconciliationStatus": reconciliation_status,
            "ProvenanceSource": provenance_source,
            "SubmittedAtUtc": _parse_utc_timestamp(res.get("received_at_utc")),
            "StartedAtUtc": _parse_utc_timestamp(res.get("started_at_utc")),
            "CompletedAtUtc": _parse_utc_timestamp(res.get("completed_at_utc")),
            "PublishedAtUtc": _parse_utc_timestamp(res.get("published_at_utc") or mk.get("published")),
        }
        return record, None

    # No terminal result: classify strictly by hint (SUBMITTED / DRAFT / REJECTED / DONE_WITHOUT_RESULT)
    hint = str(local_state_hint or "SUBMITTED").strip().upper()
    if hint == "REJECTED":
        stage = "REJECTED"
        exec_status = "REJECTED"
        recon = "RECONCILED_REJECTED"
    elif hint == "DRAFT":
        stage = "DRAFT"
        exec_status = "DRAFT_ORPHAN"
        recon = "HISTORICAL_ORPHAN_DRAFT"
    elif hint == "DONE_WITHOUT_RESULT":
        stage = "BLOCKED"
        exec_status = "DONE_WITHOUT_RESULT"
        recon = "HISTORICAL_MISSING_RESULT"
    else:
        stage = "SUBMITTED"
        exec_status = hint
        recon = "HISTORICAL_PENDING_RECONCILIATION"

    record = {
        "JobID": clean_job_id,
        "SchemaVersion": schema_version,
        "SourceJobID": _clean_str(req.get("source_job_id"), 128),
        "ProjectID": project_id,
        "BoundedContext": bounded_context,
        "CapabilityCode": capability_code,
        "Mode": mode,
        "Objective": objective,
        "PriorityClass": priority_class,
        "RequesterUsuarioID": None,
        "RequesterEmail": requester_email,
        "RequesterSource": requester_source,
        "OwnerAgentOrDev": _clean_str(requester.get("chat"), 120),
        "ChainID": _clean_str(req.get("chain_id"), 120),
        "GateID": _clean_str(req.get("gate_id"), 120),
        "DependsOnJobID": _clean_str(req.get("depends_on_job_id"), 128),
        "LifecycleStage": stage,
        "ExecutionStatus": exec_status,
        "QualityGate": "FAIL" if stage == "REJECTED" else "PENDING",
        "TestsStatus": "FAIL" if stage == "REJECTED" else "PENDING",
        "IntegrationStatus": "PENDING",
        "GitSyncStatus": "UNVERIFIED",
        "CertificationStatus": "NOT_CERTIFIED",
        "OperationalValidationStatus": "NOT_APPLICABLE" if stage == "REJECTED" else "PENDING_PREVIEW_VALIDATION",
        "PreviewActivated": 0,
        "OperationalTests": "NOT_RUN",
        "FunctionalResult": "UNVERIFIED",
        "TerminalResultValid": 0,
        "PercentComplete": 0,
        "DevelopmentCommitSHA": None,
        "PublishedResultCommitSHA": None,
        "ResultSHA256": None,
        "AttestationSHA256": None,
        "ProductionTouched": 0,
        "RecoveryAttempts": 0,
        "BlockersJson": None,
        "NextRecommendedAction": None,
        "ReconciliationStatus": recon,
        "ProvenanceSource": provenance_source,
        "SubmittedAtUtc": None,
        "StartedAtUtc": None,
        "CompletedAtUtc": None,
        "PublishedAtUtc": None,
    }
    return record, None


def collect_canonical_backfill_dataset(
    *,
    queue_root: Path | None = None,
    include_remote_git: bool = True,
) -> dict[str, Any]:
    """Collect jobs, incidents, and capabilities from existing canonical Worker sources."""
    qroot = queue_root or QUEUE_ROOT
    remote_requests = (
        _stream_git_tree_json("origin/worker/requests:worker_queue/inbox")
        if include_remote_git
        else {}
    )
    remote_results = (
        _stream_git_tree_json("origin/worker/results:worker_queue/results")
        if include_remote_git
        else {}
    )

    local_results: dict[str, dict[str, Any]] = {}
    invalid_local_results: list[dict[str, str]] = []
    if (qroot / "results").is_dir():
        for path in sorted((qroot / "results").glob("*.json")):
            obj = _load_json_dict(path)
            if obj is None:
                invalid_local_results.append({"job_id": path.stem, "reason": "LOCAL_RESULT_CORRUPT_OR_EMPTY"})
                continue
            local_results[path.stem] = obj

    local_markers: dict[str, dict[str, str]] = {}
    if (qroot / "published").is_dir():
        for path in sorted((qroot / "published").glob("*.json")):
            local_markers[path.stem] = _parse_published_marker(path)

    preview_map: dict[str, dict[str, Any]] = {}
    if (qroot / "preview_validations").is_dir():
        for path in sorted((qroot / "preview_validations").glob("*.json")):
            obj = _load_json_dict(path)
            if obj is not None:
                preview_map[path.stem] = obj

    local_requests: dict[str, tuple[dict[str, Any] | None, str]] = {}
    for hint, dirname in (
        ("DONE_WITHOUT_RESULT", "done"),
        ("REJECTED", "rejected"),
        ("PROCESSING", "processing"),
        ("PENDING", "pending"),
        ("DRAFT", "drafts"),
    ):
        dpath = qroot / dirname
        if not dpath.is_dir():
            continue
        for path in sorted(dpath.glob("*.json")):
            if path.stem in local_requests:
                continue
            raw_obj = _load_json_dict(path)
            req_obj = raw_obj.get("job") if isinstance(raw_obj, dict) and isinstance(raw_obj.get("job"), dict) else raw_obj
            local_requests[path.stem] = (req_obj, hint)

    all_job_ids = sorted(
        set(remote_requests)
        | set(remote_results)
        | set(local_results)
        | set(local_requests)
    )

    jobs: list[dict[str, Any]] = []
    rejected_records: list[dict[str, str]] = list(invalid_local_results)
    inconsistent_count = 0

    for jid in all_job_ids:
        rem_req_obj, rem_req_state = remote_requests.get(jid, (None, "ABSENT"))
        rem_res_obj, rem_res_state = remote_results.get(jid, (None, "ABSENT"))
        loc_res_obj = local_results.get(jid)
        loc_req_obj, loc_hint = local_requests.get(jid, (None, "SUBMITTED"))

        if rem_res_state not in {"ABSENT", "OK"} and loc_res_obj is None:
            rejected_records.append({"job_id": jid, "reason": f"REMOTE_RESULT_{rem_res_state}"})
            continue

        # Prefer remote published result if certified or if local is missing; otherwise local
        chosen_res = rem_res_obj if (rem_res_obj is not None and (loc_res_obj is None or rem_res_obj.get("certification") in _CERTIFIED_SET)) else (loc_res_obj or rem_res_obj)
        chosen_req = rem_req_obj or loc_req_obj
        provenance = (
            "GIT_RESULTS_BACKFILL"
            if rem_res_obj is not None
            else ("LOCAL_RESULTS_BACKFILL" if loc_res_obj is not None else "GIT_REQUESTS_BACKFILL")
        )

        rec, err = normalize_job_record(
            job_id=jid,
            request_payload=chosen_req,
            result_payload=chosen_res,
            marker=local_markers.get(jid),
            preview_evidence=preview_map.get(jid),
            local_state_hint=loc_hint,
            provenance_source=provenance,
        )
        if err is not None or rec is None:
            rejected_records.append({"job_id": jid, "reason": err or "NORMALIZE_FAILED"})
            continue

        if rec["ReconciliationStatus"] in {
            "HISTORICAL_INVALID_RESULT",
            "MARKER_RESULT_DRIFT_PENDING_RECONCILE",
            "HISTORICAL_ORPHAN_DRAFT",
            "HISTORICAL_MISSING_RESULT",
        }:
            inconsistent_count += 1
        jobs.append(rec)

    # Collect maintenance incidents
    incidents: list[dict[str, Any]] = []
    inc_dir = qroot / "maintenance" / "incidents"
    if inc_dir.is_dir():
        for path in sorted(inc_dir.glob("*.json")):
            obj = _load_json_dict(path)
            if obj is None or obj.get("production_touched") is True:
                rejected_records.append({"job_id": path.stem, "reason": "INCIDENT_INVALID_OR_PRODUCTION"})
                continue
            req_meta = obj.get("requester") if isinstance(obj.get("requester"), dict) else {}
            incidents.append(
                {
                    "IncidentID": _clean_str(obj.get("incident_id") or path.stem, 128),
                    "IncidentCategory": "UNRECONCILED_HISTORICAL_RESULT",
                    "ErrorClass": "CONTRACTUAL",
                    "Severity": "HIGH" if obj.get("state") == "REPAIR_REQUIRED" else "MEDIUM",
                    "IncidentState": _clean_str(obj.get("state") or "OPEN", 40) or "OPEN",
                    "SourceJobID": _clean_str(obj.get("source_job_id"), 128),
                    "RepairJobID": _clean_str(obj.get("repair_job_id"), 128),
                    "ProjectID": _clean_str(req_meta.get("project") or "EDARSAHUB-BOS", 100),
                    "BoundedContext": "WORKER_OPERATIONS",
                    "ProblemSignature": _clean_str(obj.get("problem_signature"), 192),
                    "BlockerSignature": _clean_str(obj.get("blocker_signature"), 255),
                    "CapabilityCode": _clean_str(obj.get("capability_code"), 120),
                    "RootCause": _clean_str(obj.get("superseded_reason") or obj.get("problem_signature") or obj.get("blocker_signature") or "MAINTENANCE_INCIDENT", 1000) or "MAINTENANCE_INCIDENT",
                    "ImpactSummary": None,
                    "OwnerEmail": _clean_str(req_meta.get("email"), 255),
                    "EvidenceRef": _clean_str(obj.get("repair_result_sha256"), 500),
                    "RecommendedAction": "REVIEW_MAINTENANCE_INCIDENT",
                    "RecoveryAttempts": int(obj.get("attempts") or 0),
                    "CooldownUntilUtc": None,
                    "ProductionTouched": 0,
                }
            )

    # Collect capabilities (learned repair + Knowledge Loop lessons)
    capabilities: list[dict[str, Any]] = []
    seen_caps: set[str] = set()
    try:
        for cap in learned_registry.iter_learned_capabilities():
            if cap.code in seen_caps:
                continue
            seen_caps.add(cap.code)
            ev = cap.evidence or {}
            capabilities.append(
                {
                    "CapabilityCode": cap.code[:120],
                    "CapabilityKind": "LEARNED_REPAIR",
                    "ProblemSignature": _clean_str(cap.problem_signature, 192),
                    "AllowedModes": "MUTATION",
                    "BoundedContextRule": "WORKER_OPERATIONS",
                    "Reusable": 1 if cap.reusable else 0,
                    "SourceJobID": _clean_str(ev.get("source_job_id"), 128),
                    "CertifiedRepairJobID": _clean_str(ev.get("repair_job_id"), 128),
                    "CertifiedCommitSHA": _clean_sha(ev.get("repair_commit_sha"), 40),
                    "CertificationStatus": "CERTIFIED" if ev.get("certified", True) else "NOT_CERTIFIED",
                    "OperationalValidationStatus": "NOT_APPLICABLE",
                    "RootCause": _clean_str(cap.objective, 1000),
                    "PreventionRule": _clean_str(ev.get("blocker_signature"), 1000),
                    "ProductionTouched": 0,
                }
            )
    except Exception:
        pass

    for lesson in auto_loop.CANONICAL_KNOWLEDGE_LESSONS:
        code = str(lesson["lesson_id"])[:120]
        if code in seen_caps:
            continue
        seen_caps.add(code)
        capabilities.append(
            {
                "CapabilityCode": code,
                "CapabilityKind": "KNOWLEDGE_LESSON",
                "ProblemSignature": _clean_str(lesson.get("problem_signature"), 192),
                "AllowedModes": "READ_ONLY,MUTATION",
                "BoundedContextRule": "WORKER_OPERATIONS",
                "Reusable": 1,
                "SourceJobID": _clean_str(lesson.get("source_job_id"), 128),
                "CertifiedRepairJobID": _clean_str(lesson.get("certified_repair_job_id"), 128),
                "CertifiedCommitSHA": _clean_sha(lesson.get("certified_commit_sha"), 40),
                "CertificationStatus": _clean_str(lesson.get("certification") or "CERTIFIED", 60) or "CERTIFIED",
                "OperationalValidationStatus": _clean_str(lesson.get("operational_validation") or "NOT_APPLICABLE", 60) or "NOT_APPLICABLE",
                "RootCause": _clean_str(lesson.get("root_cause"), 1000),
                "PreventionRule": _clean_str(lesson.get("prevention_rule"), 1000),
                "ProductionTouched": 0,
            }
        )

    return {
        "jobs": jobs,
        "incidents": incidents,
        "capabilities": capabilities,
        "rejected_records": rejected_records,
        "inconsistent_count": inconsistent_count,
    }


def _verify_dev_database_identity(cursor) -> dict[str, Any]:
    cursor.execute(
        "SELECT @@SERVERNAME AS server_name, DB_NAME() AS db_name, SUSER_SNAME() AS login_name, USER_NAME() AS db_user"
    )
    row = cursor.fetchone()
    if not row:
        raise WorkerSqlProjectionError("SQL_IDENTITY_UNAVAILABLE")
    identity = row if isinstance(row, dict) else {
        "server_name": row[0],
        "db_name": row[1],
        "login_name": row[2],
        "db_user": row[3],
    }
    if str(identity.get("db_name") or "").strip().upper() != EXPECTED_DEV_DATABASE:
        raise WorkerSqlProjectionError(
            f"UNEXPECTED_DATABASE_FORBIDDEN:{identity.get('db_name')}"
        )
    return identity


def _query_table_counts(cursor) -> dict[str, int]:
    cursor.execute(
        """
        SELECT t.name AS table_name, SUM(p.rows) AS row_count
        FROM sys.tables t
        INNER JOIN sys.schemas s ON s.schema_id = t.schema_id
        INNER JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
        WHERE s.name = N'dbo'
          AND t.name IN (N'Sys_Worker_Jobs', N'Sys_Worker_Incidents', N'Sys_Worker_RecoveryEvents', N'Sys_Worker_Capabilities')
        GROUP BY t.name
        """
    )
    counts = {
        "Sys_Worker_Jobs": 0,
        "Sys_Worker_Incidents": 0,
        "Sys_Worker_RecoveryEvents": 0,
        "Sys_Worker_Capabilities": 0,
    }
    for row in cursor.fetchall() or []:
        if isinstance(row, dict):
            counts[str(row["table_name"])] = int(row["row_count"] or 0)
        else:
            counts[str(row[0])] = int(row[1] or 0)
    return counts


_JOB_SP_SQL = """
EXEC dbo.sp_Worker_UpsertJobState
    @JobID=%s, @SchemaVersion=%s, @SourceJobID=%s, @ProjectID=%s, @BoundedContext=%s,
    @CapabilityCode=%s, @Mode=%s, @Objective=%s, @PriorityClass=%s,
    @RequesterUsuarioID=%s, @RequesterEmail=%s, @RequesterSource=%s,
    @OwnerAgentOrDev=%s, @ChainID=%s, @GateID=%s, @DependsOnJobID=%s,
    @LifecycleStage=%s, @ExecutionStatus=%s, @QualityGate=%s, @TestsStatus=%s,
    @IntegrationStatus=%s, @GitSyncStatus=%s, @CertificationStatus=%s,
    @OperationalValidationStatus=%s, @PreviewActivated=%s, @OperationalTests=%s,
    @FunctionalResult=%s, @TerminalResultValid=%s, @PercentComplete=%s,
    @DevelopmentCommitSHA=%s, @PublishedResultCommitSHA=%s, @ResultSHA256=%s,
    @AttestationSHA256=%s, @ProductionTouched=%s, @RecoveryAttempts=%s,
    @BlockersJson=%s, @NextRecommendedAction=%s, @ReconciliationStatus=%s,
    @ProvenanceSource=%s, @SubmittedAtUtc=%s, @StartedAtUtc=%s,
    @CompletedAtUtc=%s, @PublishedAtUtc=%s
"""

_JOB_PARAM_KEYS = (
    "JobID", "SchemaVersion", "SourceJobID", "ProjectID", "BoundedContext",
    "CapabilityCode", "Mode", "Objective", "PriorityClass",
    "RequesterUsuarioID", "RequesterEmail", "RequesterSource",
    "OwnerAgentOrDev", "ChainID", "GateID", "DependsOnJobID",
    "LifecycleStage", "ExecutionStatus", "QualityGate", "TestsStatus",
    "IntegrationStatus", "GitSyncStatus", "CertificationStatus",
    "OperationalValidationStatus", "PreviewActivated", "OperationalTests",
    "FunctionalResult", "TerminalResultValid", "PercentComplete",
    "DevelopmentCommitSHA", "PublishedResultCommitSHA", "ResultSHA256",
    "AttestationSHA256", "ProductionTouched", "RecoveryAttempts",
    "BlockersJson", "NextRecommendedAction", "ReconciliationStatus",
    "ProvenanceSource", "SubmittedAtUtc", "StartedAtUtc",
    "CompletedAtUtc", "PublishedAtUtc",
)

_INCIDENT_SP_SQL = """
EXEC dbo.sp_Worker_UpsertIncident
    @IncidentID=%s, @IncidentCategory=%s, @ErrorClass=%s, @Severity=%s,
    @IncidentState=%s, @SourceJobID=%s, @RepairJobID=%s, @ProjectID=%s,
    @BoundedContext=%s, @ProblemSignature=%s, @BlockerSignature=%s,
    @CapabilityCode=%s, @RootCause=%s, @ImpactSummary=%s, @OwnerEmail=%s,
    @EvidenceRef=%s, @RecommendedAction=%s, @RecoveryAttempts=%s,
    @CooldownUntilUtc=%s, @ProductionTouched=%s
"""

_INCIDENT_PARAM_KEYS = (
    "IncidentID", "IncidentCategory", "ErrorClass", "Severity",
    "IncidentState", "SourceJobID", "RepairJobID", "ProjectID",
    "BoundedContext", "ProblemSignature", "BlockerSignature",
    "CapabilityCode", "RootCause", "ImpactSummary", "OwnerEmail",
    "EvidenceRef", "RecommendedAction", "RecoveryAttempts",
    "CooldownUntilUtc", "ProductionTouched",
)

_CAPABILITY_SP_SQL = """
EXEC dbo.sp_Worker_UpsertCapability
    @CapabilityCode=%s, @CapabilityKind=%s, @ProblemSignature=%s,
    @AllowedModes=%s, @BoundedContextRule=%s, @Reusable=%s,
    @SourceJobID=%s, @CertifiedRepairJobID=%s, @CertifiedCommitSHA=%s,
    @CertificationStatus=%s, @OperationalValidationStatus=%s,
    @RootCause=%s, @PreventionRule=%s, @ProductionTouched=%s
"""

_CAPABILITY_PARAM_KEYS = (
    "CapabilityCode", "CapabilityKind", "ProblemSignature",
    "AllowedModes", "BoundedContextRule", "Reusable",
    "SourceJobID", "CertifiedRepairJobID", "CertifiedCommitSHA",
    "CertificationStatus", "OperationalValidationStatus",
    "RootCause", "PreventionRule", "ProductionTouched",
)


def execute_backfill(
    *,
    confirm: bool,
    production_allowed: bool = False,
    dry_run: bool = False,
    batch_size: int = 200,
    verify_idempotency: bool = True,
    queue_root: Path | None = None,
    include_remote_git: bool = True,
    connection_factory=None,
) -> dict[str, Any]:
    """Execute batched, idempotent historical backfill into dbo.Sys_Worker_* via narrow SPs."""
    if production_allowed is not False:
        raise WorkerSqlProjectionError("PRODUCTION_FORBIDDEN")
    if not dry_run and confirm is not True:
        raise WorkerSqlProjectionError("BACKFILL_CONFIRMATION_REQUIRED")
    if not isinstance(batch_size, int) or batch_size < 1 or batch_size > 1000:
        raise WorkerSqlProjectionError("INVALID_BATCH_SIZE")

    dataset = collect_canonical_backfill_dataset(
        queue_root=queue_root,
        include_remote_git=include_remote_git,
    )
    jobs = dataset["jobs"]
    incidents = dataset["incidents"]
    capabilities = dataset["capabilities"]
    rejected = dataset["rejected_records"]
    inconsistent_count = int(dataset["inconsistent_count"])

    if dry_run:
        return {
            "status": "PASS",
            "mode": "DRY_RUN",
            "jobs_prepared": len(jobs),
            "incidents_prepared": len(incidents),
            "capabilities_prepared": len(capabilities),
            "rejected_count": len(rejected),
            "inconsistent_count": inconsistent_count,
            "production_touched": False,
        }

    if connection_factory is None:
        from core.config.env_bootstrap import load_edarsahub_environment
        from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

        load_edarsahub_environment()
        conn = get_edarsahub_pymssql_connection(timeout=120, login_timeout=15, autocommit=False)
    else:
        conn = connection_factory()

    try:
        cur = conn.cursor(as_dict=True)
        identity = _verify_dev_database_identity(cur)
        counts_before = _query_table_counts(cur)

        def _apply_batches(sql: str, rows: list[dict[str, Any]], keys: tuple[str, ...]) -> int:
            written = 0
            for start in range(0, len(rows), batch_size):
                chunk = rows[start : start + batch_size]
                for item in chunk:
                    cur.execute(sql, tuple(item[k] for k in keys))
                    written += 1
                conn.commit()
            return written

        jobs_written = _apply_batches(_JOB_SP_SQL, jobs, _JOB_PARAM_KEYS)
        incidents_written = _apply_batches(_INCIDENT_SP_SQL, incidents, _INCIDENT_PARAM_KEYS)
        capabilities_written = _apply_batches(_CAPABILITY_SP_SQL, capabilities, _CAPABILITY_PARAM_KEYS)
        counts_after_pass1 = _query_table_counts(cur)

        idempotency_verified = False
        counts_after_pass2 = dict(counts_after_pass1)
        idempotency_delta: dict[str, int] = {}
        if verify_idempotency:
            # Re-run a deterministic bounded slice (up to 50 jobs + all incidents + all capabilities)
            sample_jobs = jobs[:50]
            _apply_batches(_JOB_SP_SQL, sample_jobs, _JOB_PARAM_KEYS)
            _apply_batches(_INCIDENT_SP_SQL, incidents, _INCIDENT_PARAM_KEYS)
            _apply_batches(_CAPABILITY_SP_SQL, capabilities, _CAPABILITY_PARAM_KEYS)
            counts_after_pass2 = _query_table_counts(cur)
            idempotency_delta = {
                tbl: counts_after_pass2[tbl] - counts_after_pass1[tbl]
                for tbl in counts_after_pass1
            }
            if any(delta != 0 for delta in idempotency_delta.values()):
                raise WorkerSqlProjectionError(f"IDEMPOTENCY_VIOLATION:{idempotency_delta}")
            idempotency_verified = True

        return {
            "status": "PASS",
            "mode": "BACKFILL_APPLIED",
            "database": identity["db_name"],
            "server_name": identity["server_name"],
            "login_name": identity["login_name"],
            "batch_size": batch_size,
            "counts_before": counts_before,
            "counts_after_pass1": counts_after_pass1,
            "counts_after_pass2": counts_after_pass2,
            "jobs_reconciled": jobs_written,
            "incidents_reconciled": incidents_written,
            "capabilities_reconciled": capabilities_written,
            "rejected_count": len(rejected),
            "rejected_sample": rejected[:20],
            "inconsistent_count": inconsistent_count,
            "idempotency_verified": idempotency_verified,
            "idempotency_delta": idempotency_delta,
            "production_touched": False,
        }
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _record_pending_projection(
    queue_root: Path,
    *,
    job_id: str,
    reason: str,
) -> None:
    """Registra fallo transitorio de proyección SQL sin bloquear la cola Git."""
    runtime_dir = queue_root / "runtime"
    pending_file = runtime_dir / "sql_projection_pending.json"
    try:
        runtime_dir.mkdir(parents=True, exist_ok=True)
        existing = _load_json_dict(pending_file) or {}
        pending_map = existing.get("pending") if isinstance(existing.get("pending"), dict) else {}
        pending_map[job_id] = {
            "job_id": job_id,
            "reason": str(reason)[:240],
            "recorded_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        # Mantener acotado a los últimos 100 registros
        if len(pending_map) > 100:
            oldest_keys = sorted(pending_map.keys())[:-100]
            for k in oldest_keys:
                pending_map.pop(k, None)
        payload = {
            "schema": "edarsahub.worker-sql-projection-pending.v1",
            "updated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "pending_count": len(pending_map),
            "pending": pending_map,
        }
        pending_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass


def _clear_pending_projection(queue_root: Path, *, job_id: str) -> None:
    pending_file = queue_root / "runtime" / "sql_projection_pending.json"
    if not pending_file.is_file():
        return
    try:
        existing = _load_json_dict(pending_file) or {}
        pending_map = existing.get("pending") if isinstance(existing.get("pending"), dict) else {}
        if job_id not in pending_map:
            return
        pending_map.pop(job_id, None)
        payload = {
            "schema": "edarsahub.worker-sql-projection-pending.v1",
            "updated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "pending_count": len(pending_map),
            "pending": pending_map,
        }
        pending_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass


def project_single_job_best_effort(
    *,
    job_id: str,
    result_payload: dict[str, Any],
    request_payload: dict[str, Any] | None = None,
    published_commit: str | None = None,
    queue_root: Path | None = None,
    connection_factory=None,
) -> dict[str, Any]:
    """Proyección incremental segura, idempotente y no bloqueante hacia dbo.Sys_Worker_Jobs.

    - Invoca únicamente dbo.sp_Worker_UpsertJobState (SP estrecho certificado en GATE-M1).
    - Valida DB_NAME() == 'EDARSAHUB' y rechaza production_touched=True (fail-closed).
    - Nunca lanza excepciones que bloqueen la publicación Git; cualquier error SQL queda
      trazado en runtime/sql_projection_pending.json para reintento idempotente.
    """
    qroot = queue_root or QUEUE_ROOT
    clean_job_id = _clean_str(job_id, 128) or ""
    if not clean_job_id:
        return {"projected": False, "pending_recorded": False, "reason": "EMPTY_JOB_ID"}

    marker = {"commit": published_commit} if published_commit else {}
    record, reject_reason = normalize_job_record(
        job_id=clean_job_id,
        request_payload=request_payload,
        result_payload=result_payload,
        marker=marker,
        provenance_source="RUNTIME_INCREMENTAL_PROJECTION",
    )
    if record is None:
        _record_pending_projection(qroot, job_id=clean_job_id, reason=reject_reason or "NORMALIZE_REJECTED")
        return {
            "projected": False,
            "pending_recorded": True,
            "reason": reject_reason or "NORMALIZE_REJECTED",
            "production_touched": False,
        }

    conn = None
    try:
        if connection_factory is None:
            from core.config.env_bootstrap import load_edarsahub_environment
            from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

            load_edarsahub_environment()
            conn = get_edarsahub_pymssql_connection(timeout=10, login_timeout=5, autocommit=False)
        else:
            conn = connection_factory()

        cur = conn.cursor(as_dict=True)
        identity = _verify_dev_database_identity(cur)
        cur.execute(_JOB_SP_SQL, tuple(record[k] for k in _JOB_PARAM_KEYS))
        conn.commit()
        _clear_pending_projection(qroot, job_id=clean_job_id)
        return {
            "projected": True,
            "pending_recorded": False,
            "job_id": clean_job_id,
            "database": identity["db_name"],
            "lifecycle_stage": record["LifecycleStage"],
            "certification_status": record["CertificationStatus"],
            "production_touched": False,
        }
    except Exception as exc:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        reason = f"{type(exc).__name__}:{str(exc)[:180]}"
        _record_pending_projection(qroot, job_id=clean_job_id, reason=reason)
        return {
            "projected": False,
            "pending_recorded": True,
            "job_id": clean_job_id,
            "reason": reason,
            "production_touched": False,
        }
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--verify-idempotency", action="store_true")
    parser.add_argument("--production-allowed", action="store_true")
    args = parser.parse_args()
    try:
        payload = execute_backfill(
            confirm=args.confirm,
            production_allowed=args.production_allowed,
            dry_run=args.dry_run,
            batch_size=args.batch_size,
            verify_idempotency=args.verify_idempotency,
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "error": f"{type(exc).__name__}:{exc}",
                    "production_touched": False,
                },
                ensure_ascii=False,
            )
        )
        return 1
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
