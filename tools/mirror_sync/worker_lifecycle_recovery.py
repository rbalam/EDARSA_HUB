"""Universal Preventive Lifecycle Detection & Authorized Autonomous Recovery.

Cohesive helper module invoked by the existing Control Plane cycle
(``tools/mirror_sync/worker_control_plane.py``). Does not create any secondary
worker, queue, scheduler, capability registry, or Knowledge Loop.

Safety invariants:
- Never touches Production (``production_allowed=False`` enforced fail-closed).
- Never mutates or deletes historical certified results or corrupt drafts.
- Never invents ``request_key`` for legacy drafts; preserves exact ``job_id``
  and canonical payload.
- Distinguishes 6 recovery categories and never disguises an operational
  idempotent recovery as an artificial code patch.
- Applies incremental scanning on 15s cycles with periodic full reconciliation,
  bounded exponential backoff, circuit breakers, max 1 recovery per cycle, and
  automatic suspension under system degradation.
"""
from __future__ import annotations

import fcntl
import hashlib
import hmac
import json
import os
import re
import secrets
import subprocess
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

try:
    from tools.mirror_sync import gate_chain_controller as policy_ctrl
    from tools.mirror_sync import gate_chain_publisher as gcp
    from tools.mirror_sync import universal_job_bridge as job_bridge
    from tools.mirror_sync import worker_maintenance_runtime as maintenance
    from tools.mirror_sync import worker_repair_auto_loop as auto_loop
    from tools.mirror_sync import worker_repair_capability_registry as learned_registry
    from tools.mirror_sync import worker_result_detail_read as detail_read
except ModuleNotFoundError:
    import gate_chain_controller as policy_ctrl
    import gate_chain_publisher as gcp
    import universal_job_bridge as job_bridge
    import worker_maintenance_runtime as maintenance
    import worker_repair_auto_loop as auto_loop
    import worker_repair_capability_registry as learned_registry
    import worker_result_detail_read as detail_read


SCHEMA_DETECTION = "edarsahub.worker-lifecycle-detection.v1"
SCHEMA_RECOVERY = "edarsahub.worker-lifecycle-recovery.v1"
SCHEMA_DIAGNOSTIC = "edarsahub.worker-unknown-incident-diagnostic.v1"
SCHEMA_FORENSIC = "edarsahub.worker-corrupt-draft-forensic.v1"
SCHEMA_MCP_CONNECTOR_INCIDENTS = "edarsahub.mcp-connector-incident-summary.v1"
SCHEMA_SESSION_INTERRUPTION = "edarsahub.agent-session-interruption-incident.v1"
SCHEMA_INTERRUPTED_RECOVERY_EVAL = "edarsahub.interrupted-objective-recovery-eval.v1"

MCP_INCIDENTS_FILENAME = "mcp_connector_incidents.jsonl"
SESSION_INTERRUPTION_INCIDENTS_FILENAME = "session_interruption_incidents.jsonl"
MCP_INCIDENT_WINDOW_SECONDS = int(os.environ.get("EDARSAHUB_MCP_INCIDENT_WINDOW_SECONDS", "3600"))

DRAFT_GRACE_SECONDS = int(os.environ.get("EDARSAHUB_DRAFT_PERSISTENCE_GRACE_SECONDS", "300"))
PENDING_AUDIT_GRACE_SECONDS = int(os.environ.get("EDARSAHUB_PENDING_AUDIT_GRACE_SECONDS", "180"))
FULL_RECONCILE_INTERVAL_SECONDS = int(os.environ.get("EDARSAHUB_LIFECYCLE_FULL_RECONCILE_SECONDS", "300"))
MAX_RECOVERIES_PER_CYCLE = max(1, int(os.environ.get("EDARSAHUB_MAX_LIFECYCLE_RECOVERIES_PER_CYCLE", "1")))
MAX_DIAGNOSTICS_PER_CYCLE = max(1, int(os.environ.get("EDARSAHUB_MAX_DIAGNOSTICS_PER_CYCLE", "2")))
BACKOFF_BASE_SECONDS = 60
BACKOFF_CAP_SECONDS = 3600

RECOVERY_CATEGORIES = frozenset({
    "OPERATIONAL_IDEMPOTENT_RECOVERY",
    "CODE_REPAIR",
    "SQL_OPERATION",
    "SECURITY_INCIDENT",
    "BUSINESS_ERROR",
    "UNKNOWN_INCIDENT",
})

_ORPHAN_BRANCH_PREFIXES = ("agent/queue-publisher/", "worker-queue-publish/")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_exponential_backoff(
    consecutive_failures: int,
    *,
    base_seconds: int = BACKOFF_BASE_SECONDS,
    cap_seconds: int = BACKOFF_CAP_SECONDS,
) -> int:
    """Bounded deterministic exponential backoff (never unbounded)."""
    failures = max(0, int(consecutive_failures))
    if failures <= 0:
        return 0
    return int(min(cap_seconds, base_seconds * (2 ** min(failures - 1, 10))))


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = handle.name
    os.replace(tmp, path)


def _read_json_safe(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _safe_id(job_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(job_id or "").strip())[:80]


def _git_ls_tree_stems(repo_root: Path, ref: str, subdir: str) -> set[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "ls-tree", "--name-only", ref, subdir],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if proc.returncode != 0:
        return set()
    return {
        Path(line.strip()).stem
        for line in proc.stdout.splitlines()
        if line.strip().endswith(".json")
    }


def _list_orphan_publisher_branches(repo_root: Path, claims_dir: Path) -> list[dict[str, Any]]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "for-each-ref", "--format=%(refname:short)", "refs/heads/"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []
    orphans: list[dict[str, Any]] = []
    for raw in proc.stdout.splitlines():
        branch = raw.strip()
        if not any(branch.startswith(prefix) for prefix in _ORPHAN_BRANCH_PREFIXES):
            continue
        suffix = branch.split("/", 2)[-1]
        agent_id = f"queue-publisher-{suffix}"
        claim_path = claims_dir / f"{agent_id}.json"
        claim_active = False
        if claim_path.is_file():
            claim_data = _read_json_safe(claim_path) or {}
            claim_active = str(claim_data.get("status") or "").strip().upper() == "ACTIVE"
        if not claim_active:
            orphans.append({"branch": branch, "agent_id": agent_id})
    return orphans


def _active_publisher_claim_ids(claims_dir: Path) -> set[str]:
    active: set[str] = set()
    if not claims_dir.is_dir():
        return active
    for path in claims_dir.glob("*.json"):
        data = _read_json_safe(path)
        if not isinstance(data, dict):
            continue
        if str(data.get("status") or "").strip().upper() == "ACTIVE":
            active.add(path.stem)
            agent_id = str(data.get("agent_id") or "").strip()
            if agent_id:
                active.add(agent_id)
    return active


def _canonical_draft_fingerprint(payload: Mapping[str, Any]) -> str:
    """Deterministic content fingerprint without inventing request_key for legacy drafts."""
    basis = {
        "schema": payload.get("schema"),
        "job_id": payload.get("job_id"),
        "mode": payload.get("mode"),
        "target_repo": payload.get("target_repo"),
        "target_branch": payload.get("target_branch"),
        "base_sha": payload.get("base_sha"),
        "production_allowed": payload.get("production_allowed"),
        "objective": payload.get("objective"),
        "actions": payload.get("actions") or [],
        "checks": payload.get("checks") or [],
        "scheduling": payload.get("scheduling") or {},
    }
    raw = json.dumps(basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_corrupt_draft_forensic(draft_path: Path, error: Exception) -> dict[str, Any]:
    """Generate sanitized forensic evidence for a corrupt draft without reconstructing content."""
    raw_bytes = draft_path.read_bytes()
    return {
        "schema": SCHEMA_FORENSIC,
        "job_id": draft_path.stem,
        "draft_filename": draft_path.name,
        "size_bytes": len(raw_bytes),
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "error_class": type(error).__name__,
        "error_summary": str(error)[:200],
        "preserved_untouched": True,
        "reconstructed": False,
        "recommended_action": "ESCALATED_HUMAN_REQUIRED",
        "recorded_at_utc": utc_now(),
        "production_touched": False,
    }


def classify_recovery_category(
    *,
    blocker_type: str,
    mode: str = "",
    status: str = "",
    blockers: list[str] | tuple[str, ...] = (),
    error_code: str = "",
    actions_count: int = 0,
) -> dict[str, Any]:
    """Explicit 6-way classification separating operational recovery from code/SQL/security/business/unknown."""
    btype = str(blocker_type or "").strip().upper()
    m = str(mode or "").strip().upper()
    tax = auto_loop.classify_failure_taxonomy(
        status=status,
        blockers=blockers,
        error_code=error_code or btype,
        causal_evidence={"blocker_type": btype},
    )
    tax_cat = str(tax.get("category") or "").upper()

    if tax_cat == "SECURITY":
        category = "SECURITY_INCIDENT"
        auto_allowed = False
    elif tax_cat == "BUSINESS":
        category = "BUSINESS_ERROR"
        auto_allowed = False
    elif m == "READ_ONLY_SQL" or btype == "SQL_DRAFT":
        category = "SQL_OPERATION"
        auto_allowed = False
    elif btype in {
        "PERSISTENT_UNPUBLISHED_DRAFT",
        "PENDING_AUDIT_STALE",
        "ORPHAN_BRANCH",
        "ORPHAN_CLAIM",
        "STALE_PROCESSING",
    } and m in {"", "READ_ONLY"} and actions_count == 0:
        category = "OPERATIONAL_IDEMPOTENT_RECOVERY"
        auto_allowed = True
    elif btype in {"CODE_REPAIR_INCIDENT", "GIT_TESTS_FAILED", "WORKER_INFRA_REPAIR"} or (
        m in {"MUTATION", "DEVELOPMENT_REPO_CHANGE"} and actions_count > 0
    ):
        category = "CODE_REPAIR"
        auto_allowed = False
    else:
        category = "UNKNOWN_INCIDENT"
        auto_allowed = False

    return {
        "recovery_category": category,
        "taxonomy_class": tax.get("failure_class"),
        "taxonomy_category": tax_cat,
        "operational_auto_eligible": auto_allowed,
        "human_approval_required": bool(
            tax.get("human_approval_required")
            or category in {"SECURITY_INCIDENT", "BUSINESS_ERROR", "SQL_OPERATION", "UNKNOWN_INCIDENT"}
        ),
        "production_touched": False,
    }


def summarize_mcp_connector_incidents(
    *,
    state_root: Path,
    now_epoch: float | None = None,
    window_seconds: int = MCP_INCIDENT_WINDOW_SECONDS,
    max_recent: int = 25,
) -> dict[str, Any]:
    """Read and classify recent secret-free MCP connector internal errors without halting unrelated domains."""
    now_ts = float(now_epoch if now_epoch is not None else time.time())
    incidents_path = state_root / "maintenance" / MCP_INCIDENTS_FILENAME
    by_family: dict[str, int] = {}
    by_tool: dict[str, int] = {}
    recent: list[dict[str, Any]] = []
    total_recent = 0

    if incidents_path.is_file():
        try:
            lines = incidents_path.read_text(encoding="utf-8", errors="replace").splitlines()[-400:]
        except OSError:
            lines = []
        for raw_line in lines:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                ev = json.loads(raw_line)
            except Exception:
                continue
            if not isinstance(ev, dict):
                continue
            ts_val = ev.get("epoch")
            if isinstance(ts_val, (int, float)) and not isinstance(ts_val, bool):
                if (now_ts - float(ts_val)) > window_seconds:
                    continue
            else:
                raw_ts = str(ev.get("timestamp_utc") or "").strip()
                if raw_ts:
                    try:
                        dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                        if (now_ts - dt.timestamp()) > window_seconds:
                            continue
                    except ValueError:
                        pass
            err_code = str(ev.get("error_code") or "MCP_CONNECTOR_INTERNAL_ERROR").strip().upper()
            tool = str(ev.get("tool") or "mcp_gateway").strip()
            tax = auto_loop.classify_failure_taxonomy(
                error_code=err_code,
                blockers=[str(ev.get("incident_family") or "")],
                causal_evidence={"tool": tool, "http_status": ev.get("http_status")},
            )
            family = str(ev.get("incident_family") or tax.get("failure_class") or "MCP_CONNECTOR_INTERNAL_ERROR")
            by_family[family] = by_family.get(family, 0) + 1
            by_tool[tool] = by_tool.get(tool, 0) + 1
            total_recent += 1
            recent.append({
                "timestamp_utc": ev.get("timestamp_utc"),
                "tool": tool,
                "http_status": ev.get("http_status"),
                "error_code": err_code,
                "incident_family": family,
                "taxonomy_class": tax.get("failure_class"),
                "retryable": bool(ev.get("retryable", False)),
                "isolated_scope": ev.get("correlation_id") or tool,
            })

    health = "HEALTHY" if total_recent == 0 else ("DEGRADED" if total_recent >= 5 else "OBSERVED_ISOLATED")
    return {
        "schema": SCHEMA_MCP_CONNECTOR_INCIDENTS,
        "window_seconds": int(window_seconds),
        "total_recent": total_recent,
        "health": health,
        "non_blocking_isolation": True,
        "by_family": dict(sorted(by_family.items())),
        "by_tool": dict(sorted(by_tool.items())),
        "recent": recent[-max_recent:],
        "production_touched": False,
    }


def prune_settled_orphan_publisher_branches(
    *,
    repo_root: Path,
    state_root: Path,
    claims_dir: Path,
    remote_inbox_ids: set[str] | None = None,
    remote_result_ids: set[str] | None = None,
    max_prune_per_cycle: int = 5,
) -> dict[str, Any]:
    """Safely prune ONLY orphan agent/queue-publisher/* branches with no active claim/worktree and already settled."""
    orphans = _list_orphan_publisher_branches(repo_root, claims_dir)
    if not orphans:
        return {"pruned": [], "skipped": 0, "production_touched": False}

    # Discover branches currently attached to any git worktree (never touch active worktrees)
    wt_branches: set[str] = set()
    wt_proc = subprocess.run(
        ["git", "-C", str(repo_root), "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if wt_proc.returncode == 0:
        for line in wt_proc.stdout.splitlines():
            if line.startswith("branch refs/heads/"):
                wt_branches.add(line.split("branch refs/heads/", 1)[1].strip())

    settled_ids: set[str] = set()
    for sub in ("results", "done", "rejected"):
        d = state_root / sub
        if d.is_dir():
            settled_ids.update(p.stem for p in d.glob("*.json"))
    if remote_inbox_ids:
        settled_ids.update(remote_inbox_ids)
    if remote_result_ids:
        settled_ids.update(remote_result_ids)

    pruned: list[str] = []
    skipped = 0
    for item in orphans:
        if len(pruned) >= max(1, int(max_prune_per_cycle)):
            break
        branch = str(item.get("branch") or "").strip()
        if not branch.startswith("agent/queue-publisher/"):
            skipped += 1
            continue
        if branch in wt_branches:
            skipped += 1
            continue
        job_id = branch.split("agent/queue-publisher/", 1)[1]
        if job_id not in settled_ids:
            skipped += 1
            continue
        res = subprocess.run(
            ["git", "-C", str(repo_root), "branch", "-D", branch],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        if res.returncode == 0:
            pruned.append(branch)
        else:
            skipped += 1

    return {"pruned": pruned, "skipped": skipped, "production_touched": False}


def reconcile_converged_runtime_incidents(
    *,
    state_root: Path | None = None,
    convergence_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Supersede stale RUNTIME_NOT_CONVERGED incidents once runtime convergence is verified True."""
    qroot = state_root or (Path(os.environ.get("EDARSAHUB_ROOT", "/app")) / ".git" / "universal-worker-queue")
    incidents_dir = qroot / "maintenance" / "incidents"
    if not incidents_dir.is_dir():
        return {"superseded": [], "checked": 0, "production_touched": False}

    report = dict(convergence_report) if isinstance(convergence_report, Mapping) else None
    if report is None:
        try:
            from tools.mirror_sync import worker_runtime_fingerprint as fp
            report = fp.build_mcp_runtime_convergence_report()
        except Exception:
            report = {}

    if report.get("overall_converged") is not True:
        return {"superseded": [], "checked": 0, "converged": False, "production_touched": False}

    superseded: list[str] = []
    checked = 0
    for inc_path in sorted(incidents_dir.glob("*.json")):
        inc = _read_json_safe(inc_path)
        if not isinstance(inc, dict):
            continue
        checked += 1
        state = str(inc.get("state") or "").strip().upper()
        if state in {"CERTIFIED", "SUPERSEDED", "ESCALATED_HUMAN_REQUIRED"}:
            continue
        src_status = str(inc.get("source_status") or "").strip().upper()
        prob_sig = str(inc.get("problem_signature") or "").strip().upper()
        if src_status == "RUNTIME_NOT_CONVERGED" or "WORKER_CODE_TREE_DRIFT" in prob_sig:
            inc["state"] = "SUPERSEDED"
            inc["superseded_reason"] = "RUNTIME_CONVERGENCE_VERIFIED_ALIGNED"
            inc["superseded_at_utc"] = utc_now()
            inc["converged_head"] = report.get("local_head")
            inc["production_touched"] = False
            try:
                _atomic_write_json(inc_path, inc)
                superseded.append(str(inc.get("incident_id") or inc_path.stem))
            except OSError:
                continue

    return {"superseded": superseded, "checked": checked, "converged": True, "production_touched": False}


def scan_global_lifecycle_blockers(
    *,
    repo_root: Path | None = None,
    state_root: Path | None = None,
    claims_dir: Path | None = None,
    attestations_dir: Path | None = None,
    ff: Mapping[str, Any] | None = None,
    runtime: Mapping[str, Any] | None = None,
    claims_summary: Mapping[str, Any] | None = None,
    now_epoch: float | None = None,
    draft_grace_seconds: int = DRAFT_GRACE_SECONDS,
    pending_audit_grace_seconds: int = PENDING_AUDIT_GRACE_SECONDS,
    full_reconcile_interval: int = FULL_RECONCILE_INTERVAL_SECONDS,
    force_full: bool = False,
    remote_inbox_ids: set[str] | None = None,
    remote_result_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Incremental + periodic full global lifecycle scanner covering all domains and 12 blocker classes."""
    t0 = time.monotonic()
    root = repo_root or Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    qroot = state_root or (root / ".git" / "universal-worker-queue")
    cdir = claims_dir or (root / ".git" / "agent-guard" / "state" / "claims")
    adir = attestations_dir or (root / ".git" / "mirror-sync" / "reporting" / "test_attestations")
    now_ts = float(now_epoch if now_epoch is not None else time.time())

    scanner_state_path = qroot / "maintenance" / "lifecycle_scanner_state.json"
    prior_state = _read_json_safe(scanner_state_path) or {}
    last_full_epoch = float(prior_state.get("last_full_reconcile_epoch") or 0.0)

    drafts_dir = qroot / "drafts"
    pending_dir = qroot / "pending"
    processing_dir = qroot / "processing"
    done_dir = qroot / "done"
    rejected_dir = qroot / "rejected"
    results_dir = qroot / "results"
    published_dir = qroot / "published"
    incidents_dir = qroot / "maintenance" / "incidents"

    def _dir_sig(d: Path) -> str:
        if not d.is_dir():
            return "ABSENT"
        st = d.stat()
        return f"{st.st_mtime_ns}:{sum(1 for _ in d.iterdir())}"

    current_sigs = {
        "drafts": _dir_sig(drafts_dir),
        "pending": _dir_sig(pending_dir),
        "processing": _dir_sig(processing_dir),
        "results": _dir_sig(results_dir),
        "published": _dir_sig(published_dir),
        "incidents": _dir_sig(incidents_dir),
    }

    need_full = bool(
        force_full
        or not prior_state
        or (now_ts - last_full_epoch) >= full_reconcile_interval
        or current_sigs != (prior_state.get("dir_signatures") or {})
    )
    scan_mode = "FULL" if (force_full or not prior_state or (now_ts - last_full_epoch) >= full_reconcile_interval) else (
        "INCREMENTAL" if current_sigs != (prior_state.get("dir_signatures") or {}) else "CACHED_INCREMENTAL"
    )

    if scan_mode == "CACHED_INCREMENTAL" and isinstance(prior_state.get("last_report"), dict):
        cached = dict(prior_state["last_report"])
        cached["scan_mode"] = "CACHED_INCREMENTAL"
        cached["at_utc"] = utc_now()
        cached["duration_ms"] = round((time.monotonic() - t0) * 1000.0, 2)
        return cached

    results_ids = {p.stem for p in results_dir.glob("*.json")} if results_dir.is_dir() else set()
    done_ids = {p.stem for p in done_dir.glob("*.json")} if done_dir.is_dir() else set()
    rejected_ids = {p.stem for p in rejected_dir.glob("*.json")} if rejected_dir.is_dir() else set()
    pending_ids = {p.stem for p in pending_dir.glob("*.json")} if pending_dir.is_dir() else set()
    processing_ids = {p.stem for p in processing_dir.glob("*.json")} if processing_dir.is_dir() else set()
    settled_ids = results_ids | done_ids | rejected_ids | pending_ids | processing_ids

    rem_in = remote_inbox_ids if remote_inbox_ids is not None else _git_ls_tree_stems(root, "origin/worker/requests", "worker_queue/inbox/")
    rem_res = remote_result_ids if remote_result_ids is not None else _git_ls_tree_stems(root, "origin/worker/results", "worker_queue/results/")
    active_claims = _active_publisher_claim_ids(cdir)

    persistent_drafts: list[dict[str, Any]] = []
    transient_drafts: list[dict[str, Any]] = []
    corrupt_drafts: list[dict[str, Any]] = []

    if drafts_dir.is_dir():
        for path in sorted(drafts_dir.glob("*.json")):
            jid = path.stem
            if jid in settled_ids or jid in rem_res:
                continue
            try:
                st = path.stat()
            except OSError:
                continue
            age_s = max(0.0, now_ts - st.st_mtime)
            agent_id = f"queue-publisher-{_safe_id(jid)}"
            in_flight = (
                age_s < draft_grace_seconds
                or agent_id in active_claims
                or jid in rem_in
            )
            try:
                raw_obj = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(raw_obj, dict):
                    raise ValueError("DRAFT_NOT_JSON_OBJECT")
            except Exception as exc:
                forensic = build_corrupt_draft_forensic(path, exc)
                corrupt_drafts.append(forensic)
                continue

            mode = str(raw_obj.get("mode") or "UNKNOWN").upper()
            bc = str((raw_obj.get("scheduling") or {}).get("bounded_context") or "UNBOUNDED_LEGACY").strip().upper()
            actions = raw_obj.get("actions") if isinstance(raw_obj.get("actions"), list) else []
            entry = {
                "job_id": jid,
                "domain": bc,
                "mode": mode,
                "actions_count": len(actions),
                "age_seconds": int(age_s),
                "in_remote_inbox": jid in rem_in,
                "active_claim": agent_id in active_claims,
                "production_allowed": bool(raw_obj.get("production_allowed") is True),
                "fingerprint": _canonical_draft_fingerprint(raw_obj),
                "recovery_category": classify_recovery_category(
                    blocker_type="PERSISTENT_UNPUBLISHED_DRAFT",
                    mode=mode,
                    actions_count=len(actions),
                )["recovery_category"],
            }
            if in_flight:
                transient_drafts.append(entry)
            else:
                persistent_drafts.append(entry)

    # Stale processing
    stale_processing: list[dict[str, Any]] = []
    if processing_dir.is_dir():
        for path in sorted(processing_dir.glob("*.json")):
            age_s = max(0.0, now_ts - path.stat().st_mtime)
            if age_s >= 120:
                stale_processing.append({"job_id": path.stem, "age_seconds": int(age_s)})

    # Pending audit evidence certifications (excluding items already reconciled in the historical ledger)
    hist_ledger = _load_historical_reconciliation_ledger(qroot)
    hist_pa_map = hist_ledger.get("pending_audit_reconciled") if isinstance(hist_ledger.get("pending_audit_reconciled"), Mapping) else {}
    pending_audit_stale: list[dict[str, Any]] = []
    historical_reconciled_pa_count = 0
    if published_dir.is_dir():
        for path in sorted(published_dir.glob("*.json")):
            try:
                txt = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "certification=PENDING_AUDIT_EVIDENCE" not in txt:
                continue
            jid = path.stem
            if jid in hist_pa_map:
                historical_reconciled_pa_count += 1
                continue
            age_s = max(0.0, now_ts - path.stat().st_mtime)
            if age_s < pending_audit_grace_seconds:
                continue
            res_obj = _read_json_safe(results_dir / f"{jid}.json") or {}
            dev_sha = str(
                res_obj.get("development_sha")
                or res_obj.get("candidate_sha")
                or res_obj.get("commit_created")
                or ""
            ).strip()
            has_attest = bool(_SHA_RE.fullmatch(dev_sha) and (adir / f"{dev_sha}.json").is_file())
            pending_audit_stale.append({
                "job_id": jid,
                "status": res_obj.get("status"),
                "development_sha": dev_sha or None,
                "has_attestation": has_attest,
                "age_seconds": int(age_s),
            })

    # Orphan branches
    orphan_branches = _list_orphan_publisher_branches(root, cdir)

    # Orphan claims count from control plane or direct scan
    orphan_claims_count = int((claims_summary or {}).get("quarantined") or 0)

    # Classify recent failure signals (MCP, Git/Mirror, Runtime, Dependency, Known/Unknown)
    mcp_failures = 0
    git_mirror_failures = 0
    runtime_failures = 0
    dependency_failures = 0
    known_failures = 0
    unknown_failures = 0

    if isinstance(ff, Mapping) and str(ff.get("ff") or "") not in ("", "ALREADY_ALIGNED", "FAST_FORWARDED"):
        git_mirror_failures += 1
    if isinstance(runtime, Mapping) and runtime.get("runtime_repair_needed") is True:
        runtime_failures += 1

    if incidents_dir.is_dir():
        for inc_path in sorted(incidents_dir.glob("*.json")):
            inc = _read_json_safe(inc_path)
            if not isinstance(inc, dict):
                continue
            st_val = str(inc.get("state") or "").upper()
            if st_val in {"CERTIFIED", "SUPERSEDED", "ESCALATED_HUMAN_REQUIRED"}:
                continue
            src_id = str(inc.get("source_job_id") or "").strip()
            src_res = _read_json_safe(results_dir / f"{src_id}.json") if src_id else None
            tax = auto_loop.classify_failure_taxonomy(
                status=str((src_res or {}).get("status") or inc.get("source_status") or ""),
                blockers=list((src_res or {}).get("blockers") or []),
                error_code=str(inc.get("problem_signature") or ""),
                causal_evidence={"incident_id": inc_path.stem},
            )
            fc = str(tax.get("failure_class") or "")
            if fc == "UNCLASSIFIED_NON_RECOVERABLE":
                unknown_failures += 1
            else:
                known_failures += 1
            if fc in {"UNKNOWN_MCP_CAPABILITY", "CONNECTION_LOSS", "MCP_CONNECTOR_INTERNAL_ERROR", "MCP_CONNECTOR_UPSTREAM_TIMEOUT", "MCP_CONNECTOR_UPSTREAM_UNAVAILABLE", "MCP_CONNECTOR_PROTOCOL_ERROR"}:
                mcp_failures += 1
            if fc in {"GIT_MIRROR_DIVERGENCE", "CONCURRENCY_CONFLICT", "INCOMPLETE_PUBLICATION", "ORPHAN_PUBLISHER_CLAIM_DEADLOCK"}:
                git_mirror_failures += 1
            if fc in {"RUNTIME_RESTART_OR_TRANSIENT", "STUCK_OR_EXPIRED_JOB"}:
                runtime_failures += 1
            if fc == "MISSING_DEPENDENCY":
                dependency_failures += 1

    mcp_connector_summary = summarize_mcp_connector_incidents(
        state_root=qroot,
        now_epoch=now_ts,
    )
    mcp_failures += int(mcp_connector_summary.get("total_recent") or 0)
    session_interruption_incidents = list_agent_session_interruption_incidents(
        state_root=qroot,
        limit=25,
    )

    degraded = bool(
        (isinstance(runtime, Mapping) and runtime.get("runtime_repair_needed") is True)
        or (isinstance(ff, Mapping) and str(ff.get("ff") or "") not in ("", "ALREADY_ALIGNED", "FAST_FORWARDED"))
        or len(stale_processing) > 0
    )

    by_domain: dict[str, int] = {}
    for item in persistent_drafts:
        dom = item["domain"]
        by_domain[dom] = by_domain.get(dom, 0) + 1

    report: dict[str, Any] = {
        "schema": SCHEMA_DETECTION,
        "at_utc": utc_now(),
        "scan_mode": scan_mode,
        "duration_ms": round((time.monotonic() - t0) * 1000.0, 2),
        "system_degraded": degraded,
        "domain_isolation_active": True,
        "counts": {
            "persistent_drafts": len(persistent_drafts),
            "transient_drafts": len(transient_drafts),
            "corrupt_drafts": len(corrupt_drafts),
            "stale_processing": len(stale_processing),
            "orphan_claims": orphan_claims_count,
            "orphan_branches": len(orphan_branches),
            "pending_audit_stale": len(pending_audit_stale),
            "mcp_failures": mcp_failures,
            "mcp_connector_recent_incidents": int(mcp_connector_summary.get("total_recent") or 0),
            "git_mirror_failures": git_mirror_failures,
            "runtime_failures": runtime_failures,
            "dependency_failures": dependency_failures,
            "known_failures": known_failures,
            "unknown_failures": unknown_failures,
        },
        "mcp_connector_incidents": mcp_connector_summary,
        "agent_session_interruption_incidents": session_interruption_incidents,
        "persistent_drafts_by_domain": dict(sorted(by_domain.items())),
        "persistent_drafts": persistent_drafts[:100],
        "transient_drafts": transient_drafts[:50],
        "corrupt_drafts": corrupt_drafts[:50],
        "stale_processing": stale_processing[:50],
        "orphan_branches": orphan_branches[:50],
        "pending_audit_stale_count": len(pending_audit_stale),
        "pending_audit_with_attestation_count": sum(1 for x in pending_audit_stale if x["has_attestation"]),
        "historical_reconciled_pending_audit_count": historical_reconciled_pa_count,
        "historical_reconciled_drafts_count": int(hist_ledger.get("historical_drafts_classified_count") or 0),
        "production_touched": False,
    }

    try:
        _atomic_write_json(
            scanner_state_path,
            {
                "last_full_reconcile_epoch": now_ts if scan_mode == "FULL" else last_full_epoch,
                "dir_signatures": current_sigs,
                "last_report": report,
            },
        )
    except OSError:
        pass

    return report


def evaluate_draft_recovery_eligibility(
    draft_path: Path,
    *,
    repo_root: Path,
    state_root: Path,
    claims_dir: Path,
    circuit_state_dir: Path,
    remote_inbox_ids: set[str],
    remote_result_ids: set[str],
    authorization_context: Mapping[str, Any] | None = None,
    now_epoch: float | None = None,
    min_mtime_epoch: float | None = None,
    adopted_job_ids: set[str] | None = None,
    draft_grace_seconds: int = DRAFT_GRACE_SECONDS,
) -> dict[str, Any]:
    """9-point fail-closed eligibility gate before recovering any persistent READ_ONLY draft."""
    now_ts = float(now_epoch if now_epoch is not None else time.time())
    job_id = draft_path.stem

    if not draft_path.is_file():
        return {"eligible": False, "action": "SKIP_MISSING", "reason": "DRAFT_NOT_FOUND", "job_id": job_id, "production_touched": False}

    st = draft_path.stat()
    age_s = max(0.0, now_ts - st.st_mtime)
    if age_s < draft_grace_seconds:
        return {"eligible": False, "action": "DEFER_TRANSIENT", "reason": "TRANSIENT_DRAFT_WITHIN_GRACE", "job_id": job_id, "age_seconds": int(age_s), "production_touched": False}

    # Check active claim or existing lifecycle state (duplicate prevention + crash/restart safety)
    agent_id = f"queue-publisher-{_safe_id(job_id)}"
    if agent_id in _active_publisher_claim_ids(claims_dir):
        return {"eligible": False, "action": "DEFER_TRANSIENT", "reason": "ACTIVE_PUBLISHER_CLAIM", "job_id": job_id, "production_touched": False}

    for sub in ("pending", "processing", "done", "rejected", "results"):
        if (state_root / sub / f"{job_id}.json").is_file():
            return {"eligible": False, "action": "DUPLICATE_PREVENTED", "reason": f"ALREADY_IN_LOCAL_{sub.upper()}", "job_id": job_id, "production_touched": False}
    if job_id in remote_inbox_ids:
        return {"eligible": False, "action": "DUPLICATE_PREVENTED", "reason": "ALREADY_IN_REMOTE_INBOX", "job_id": job_id, "production_touched": False}
    if job_id in remote_result_ids:
        return {"eligible": False, "action": "DUPLICATE_PREVENTED", "reason": "ALREADY_IN_REMOTE_RESULTS", "job_id": job_id, "production_touched": False}

    # Parse JSON fail-closed (never reconstruct corrupt draft)
    try:
        payload = json.loads(draft_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("DRAFT_NOT_JSON_OBJECT")
    except Exception as exc:
        return {
            "eligible": False,
            "action": "ESCALATE_CORRUPT",
            "reason": "CORRUPT_DRAFT_JSON",
            "job_id": job_id,
            "forensic": build_corrupt_draft_forensic(draft_path, exc),
            "production_touched": False,
        }

    # Cutoff boundary: avoid mass-replaying historical backlog unless explicitly adopted
    adopted = adopted_job_ids or set()
    if min_mtime_epoch is not None and st.st_mtime < min_mtime_epoch and job_id not in adopted:
        return {"eligible": False, "action": "DEFER_HISTORICAL_UNADOPTED", "reason": "PRE_CUTOFF_HISTORICAL_DRAFT", "job_id": job_id, "production_touched": False}

    # Strict contract & mode checks
    if payload.get("production_allowed") is not False:
        return {"eligible": False, "action": "ESCALATE_POLICY", "reason": "PRODUCTION_FORBIDDEN", "job_id": job_id, "production_touched": False}
    if str(payload.get("job_id") or "").strip() != job_id:
        return {"eligible": False, "action": "ESCALATE_CONTRACT", "reason": "DRAFT_JOB_ID_MISMATCH", "job_id": job_id, "production_touched": False}

    mode = str(payload.get("mode") or "").strip().upper()
    actions = payload.get("actions")
    if mode != "READ_ONLY" or not isinstance(actions, list) or len(actions) > 0:
        cat = classify_recovery_category(
            blocker_type="PERSISTENT_UNPUBLISHED_DRAFT",
            mode=mode,
            actions_count=len(actions) if isinstance(actions, list) else 1,
        )
        return {
            "eligible": False,
            "action": "ESCALATE_HUMAN_REQUIRED",
            "reason": f"NON_READONLY_DRAFT:{cat['recovery_category']}",
            "recovery_category": cat["recovery_category"],
            "job_id": job_id,
            "production_touched": False,
        }

    # Explicit revoked/expired authorization always fails closed as policy denial
    if isinstance(authorization_context, dict) and authorization_context.get("revoked") is True:
        return {
            "eligible": False,
            "action": "ESCALATE_POLICY",
            "reason": "AUTHORIZATION_REVOKED",
            "job_id": job_id,
            "production_touched": False,
        }

    # Validate template contract via canonical bridge
    validation_errors = job_bridge.validate(payload)
    if validation_errors:
        return {
            "eligible": False,
            "action": "ESCALATE_CONTRACT",
            "reason": "INVALID_DRAFT_CONTRACT:" + ",".join(validation_errors[:5]),
            "job_id": job_id,
            "production_touched": False,
        }

    # Requester identity check (never invent requester or request_key)
    requester = payload.get("requester")
    req_email = str(requester.get("email") or "").strip().lower() if isinstance(requester, dict) else ""
    if not req_email or "@" not in req_email:
        return {"eligible": False, "action": "ESCALATE_RBAC", "reason": "REQUESTER_IDENTITY_MISSING", "job_id": job_id, "production_touched": False}

    # Autonomous Execution Policy check (canonical Tier 1 READ_ONLY + revocation/expiration)
    gate_spec = {
        "gate_id": f"RECOVER-{job_id[:40]}",
        "job_id": job_id,
        "mutation_class": "READ_ONLY",
        "production_allowed": False,
        "job_template": payload,
    }
    policy_eval = policy_ctrl.evaluate_autonomous_policy(
        gate_spec,
        authorization_classes=("READ_ONLY_AUTONOMOUS",),
        authorization_context=authorization_context,
    )
    if not policy_eval.get("allowed"):
        return {
            "eligible": False,
            "action": "ESCALATE_POLICY",
            "reason": str(policy_eval.get("reason") or "POLICY_DENIED"),
            "policy": policy_eval,
            "job_id": job_id,
            "production_touched": False,
        }

    # Circuit breaker + exponential backoff check
    cb_key = f"draft_recovery:{job_id[:80]}"
    cb_prior = _read_json_safe(auto_loop._circuit_path(cb_key, state_dir=circuit_state_dir)) or {}
    consec_fail = int(cb_prior.get("consecutive_failures") or 0)
    backoff_s = compute_exponential_backoff(consec_fail)
    circuit = auto_loop.evaluate_circuit_breaker(
        cb_key,
        max_failures=3,
        cooldown_seconds=max(300, backoff_s),
        now_epoch=now_ts,
        state_dir=circuit_state_dir,
    )
    if not circuit.get("allow_attempt"):
        return {
            "eligible": False,
            "action": "CIRCUIT_OPEN",
            "reason": str(circuit.get("reason") or "CIRCUIT_OPEN_MAX_FAILURES"),
            "circuit_breaker": circuit,
            "job_id": job_id,
            "production_touched": False,
        }
    last_fail_ts = float(cb_prior.get("last_failure_epoch") or 0.0)
    if consec_fail > 0 and backoff_s > 0 and (now_ts - last_fail_ts) < backoff_s:
        return {
            "eligible": False,
            "action": "BACKOFF_WAIT",
            "reason": "EXPONENTIAL_BACKOFF_ACTIVE",
            "backoff_remaining_seconds": int(backoff_s - (now_ts - last_fail_ts)),
            "job_id": job_id,
            "production_touched": False,
        }

    return {
        "eligible": True,
        "action": "READY_FOR_IDEMPOTENT_RECOVERY",
        "reason": "OPERATIONAL_IDEMPOTENT_RECOVERY_AUTHORIZED",
        "recovery_category": "OPERATIONAL_IDEMPOTENT_RECOVERY",
        "job_id": job_id,
        "fingerprint": _canonical_draft_fingerprint(payload),
        "circuit_key": cb_key,
        "payload": payload,
        "policy": policy_eval,
        "production_touched": False,
    }


def recover_persistent_readonly_draft(
    draft_path: Path,
    *,
    repo_root: Path,
    state_root: Path,
    claims_dir: Path,
    circuit_state_dir: Path,
    remote_inbox_ids: set[str],
    remote_result_ids: set[str],
    authorization_context: Mapping[str, Any] | None = None,
    submit_fn: Any = None,
    now_epoch: float | None = None,
    min_mtime_epoch: float | None = None,
    adopted_job_ids: set[str] | None = None,
    draft_grace_seconds: int = DRAFT_GRACE_SECONDS,
) -> dict[str, Any]:
    """Execute one idempotent operational recovery via canonical gate_chain_publisher.submit()."""
    check = evaluate_draft_recovery_eligibility(
        draft_path,
        repo_root=repo_root,
        state_root=state_root,
        claims_dir=claims_dir,
        circuit_state_dir=circuit_state_dir,
        remote_inbox_ids=remote_inbox_ids,
        remote_result_ids=remote_result_ids,
        authorization_context=authorization_context,
        now_epoch=now_epoch,
        min_mtime_epoch=min_mtime_epoch,
        adopted_job_ids=adopted_job_ids,
        draft_grace_seconds=draft_grace_seconds,
    )
    if not check.get("eligible"):
        if check.get("action") == "ESCALATE_CORRUPT" and isinstance(check.get("forensic"), dict):
            forensic_path = state_root / "maintenance" / "forensics" / f"{draft_path.stem}.json"
            try:
                _atomic_write_json(forensic_path, check["forensic"])
            except OSError:
                pass
        return check

    publisher_submit = submit_fn or gcp.submit
    cb_key = check["circuit_key"]
    original_payload = check["payload"]  # Exact original payload preserved; zero invented request_key!
    try:
        pub = publisher_submit(original_payload, require_convergence=False)
    except Exception as exc:
        auto_loop.record_circuit_outcome(
            cb_key,
            certified_success=False,
            failure_class=f"DRAFT_RECOVERY_SUBMIT_ERROR:{type(exc).__name__}",
            now_epoch=now_epoch,
            state_dir=circuit_state_dir,
        )
        return {
            "eligible": True,
            "recovered": False,
            "action": "RECOVERY_FAILED_RECORDED",
            "job_id": check["job_id"],
            "reason": f"{type(exc).__name__}:{str(exc)[:200]}",
            "production_touched": False,
        }

    pub_status = str((pub or {}).get("status") or "").upper()
    if pub_status in {"SUBMITTED", "PUBLISHED", "EXISTS"}:
        # Operational enqueue succeeded; independent certification stays with Worker + Publisher + Auditor.
        auto_loop.record_circuit_outcome(
            cb_key,
            certified_success=True,
            now_epoch=now_epoch,
            state_dir=circuit_state_dir,
        )
        return {
            "eligible": True,
            "recovered": True,
            "action": "RECOVERED_VIA_CANONICAL_PUBLISHER",
            "recovery_category": "OPERATIONAL_IDEMPOTENT_RECOVERY",
            "job_id": check["job_id"],
            "fingerprint": check["fingerprint"],
            "publication_status": pub_status,
            "independent_certification_pending": True,
            "production_touched": False,
        }

    pub_reason_raw = str((pub or {}).get("reason") or "").strip()
    pub_reason_safe = pub_reason_raw[:160] if pub_reason_raw and not any(
        tok in pub_reason_raw.lower() for tok in ("ghp_", "token", "password", "secret", "bearer ")
    ) else None

    auto_loop.record_circuit_outcome(
        cb_key,
        certified_success=False,
        failure_class=f"DRAFT_RECOVERY_STATUS:{pub_status or 'UNKNOWN'}",
        now_epoch=now_epoch,
        state_dir=circuit_state_dir,
    )
    return {
        "eligible": True,
        "recovered": False,
        "action": "RECOVERY_REJECTED",
        "job_id": check["job_id"],
        "publication_status": pub_status,
        "publication_reason": pub_reason_safe,
        "production_touched": False,
    }


def diagnose_unknown_incident(
    *,
    incident_id: str,
    source_job_id: str = "",
    status: str = "",
    blockers: list[str] | tuple[str, ...] = (),
    error_code: str = "",
    state_root: Path | None = None,
    detail_collector: Any = None,
) -> dict[str, Any]:
    """Governed 8-step READ_ONLY autonomous diagnostic pipeline for unknown incidents.

    Never applies mutations outside Autonomous Execution Policy; never fabricates evidence.
    """
    qroot = state_root or (Path(os.environ.get("EDARSAHUB_ROOT", "/app")) / ".git" / "universal-worker-queue")
    diag_dir = qroot / "maintenance" / "diagnostics"

    # 1. Collect sanitized causal evidence (READ_ONLY)
    causal_evidence: dict[str, Any] = {}
    if source_job_id:
        collector = detail_collector or detail_read.collect
        try:
            orig_results = detail_read.RESULTS
            try:
                detail_read.RESULTS = qroot / "results"
                ev = collector(source_job_id)
            finally:
                detail_read.RESULTS = orig_results
            if isinstance(ev, dict):
                causal_evidence = {
                    "source_job_id": ev.get("source_job_id"),
                    "result_status": ev.get("result_status"),
                    "failed_check_count": ev.get("failed_check_count"),
                    "blockers": ev.get("blockers") or [],
                    "evidence_status": ev.get("evidence_status"),
                    "assertion_sample": [
                        line
                        for chk in (ev.get("failed_checks") or [])[:3]
                        if isinstance(chk, dict)
                        for line in (chk.get("assertion_lines") or [])[:5]
                    ][:10],
                }
        except Exception as exc:
            causal_evidence = {"collection_error": type(exc).__name__}

    # 2-3. Classify taxonomy & risk
    effective_blockers = list(blockers) or list(causal_evidence.get("blockers") or [])
    effective_status = status or str(causal_evidence.get("result_status") or "")
    tax = auto_loop.classify_failure_taxonomy(
        status=effective_status,
        blockers=effective_blockers,
        error_code=error_code,
        causal_evidence=causal_evidence or {"incident_id": incident_id},
    )
    cat = tax.get("category") or "NON_RECOVERABLE"
    risk_level = (
        "CRITICAL" if cat == "SECURITY"
        else ("HIGH" if cat in {"BUSINESS", "NON_RECOVERABLE"} else ("MEDIUM" if cat == "CONTRACT" else "LOW"))
    )

    # 4. Consult Knowledge Loop lessons & learned capabilities
    lesson = auto_loop.lookup_canonical_lesson(
        failure_class=str(tax.get("failure_class") or ""),
        problem_signature=error_code,
        source_job_id=source_job_id,
    )
    matched_learned: list[str] = []
    try:
        for cap in learned_registry.iter_learned_capabilities():
            if (
                incident_id in cap.incident_ids
                or (error_code and cap.problem_signature == error_code.strip().upper())
            ):
                matched_learned.append(cap.code)
    except Exception:
        pass

    # 5. Formulate hypothesis & candidate action (strictly read-only proposal)
    if lesson is not None:
        hypothesis = f"Coincidencia con leccion canonica {lesson['lesson_id']}: {lesson['root_cause']}"
        candidate_proposal = f"Aplicar guardrail reutilizable: {lesson['reusable_guardrail']}"
    elif matched_learned:
        hypothesis = f"Coincidencia con capacidad aprendida registrada: {', '.join(matched_learned)}"
        candidate_proposal = f"Evaluar capacidad aprendida {matched_learned[0]} bajo politica autonoma y auditoria independiente."
    elif causal_evidence.get("assertion_sample"):
        hypothesis = f"Falla determinista observada en checks: {causal_evidence['assertion_sample'][0]}"
        candidate_proposal = "Requiere revision de contrato y pruebas aisladas antes de cualquier mutacion."
    else:
        hypothesis = f"Incidente sin firma conocida ({tax.get('failure_class')}); evidencia causal insuficiente para mutacion autonoma."
        candidate_proposal = "Escalar a revision humana con evidencia sanitaria; prohibida mutacion no autorizada."

    # 6-8. Policy boundary (never auto-apply unknown repair outside policy)
    auto_mutation_authorized = False
    dossier: dict[str, Any] = {
        "schema": SCHEMA_DIAGNOSTIC,
        "incident_id": incident_id,
        "source_job_id": source_job_id or None,
        "diagnosed_at_utc": utc_now(),
        "causal_evidence": causal_evidence,
        "classification": tax,
        "risk_level": risk_level,
        "matched_lesson_id": lesson["lesson_id"] if lesson else None,
        "matched_learned_capabilities": matched_learned,
        "hypothesis": hypothesis,
        "candidate_proposal": candidate_proposal,
        "auto_mutation_authorized": auto_mutation_authorized,
        "independent_certification_required": True,
        "learning_allowed_only_if_certified": True,
        "recommended_action": "ESCALATED_HUMAN_REQUIRED" if risk_level in {"CRITICAL", "HIGH"} else "PLAN_WITH_POLICY_GATE",
        "production_touched": False,
    }
    try:
        _atomic_write_json(diag_dir / f"{_safe_id(incident_id)}.json", dossier)
    except OSError:
        pass
    return dossier


def advance_lifecycle_recovery(
    detection: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
    state_root: Path | None = None,
    claims_dir: Path | None = None,
    automation_state: Mapping[str, Any] | None = None,
    authorization_context: Mapping[str, Any] | None = None,
    submit_fn: Any = None,
    now_epoch: float | None = None,
    max_recoveries_per_cycle: int = MAX_RECOVERIES_PER_CYCLE,
    remote_inbox_ids: set[str] | None = None,
    remote_result_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Bounded operational recovery pass (max 1/cycle, suspended on degradation)."""
    root = repo_root or Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    qroot = state_root or (root / ".git" / "universal-worker-queue")
    cdir = claims_dir or (root / ".git" / "agent-guard" / "state" / "claims")
    cb_dir = qroot / "maintenance" / "circuit_breakers"

    if detection.get("system_degraded") is True:
        return {
            "schema": SCHEMA_RECOVERY,
            "at_utc": utc_now(),
            "status": "SUSPENDED_DEGRADATION",
            "recoveries_attempted": 0,
            "recoveries_succeeded": 0,
            "actions": [],
            "production_touched": False,
        }

    auto_ok = bool(
        isinstance(automation_state, Mapping)
        and automation_state.get("valid") is True
        and automation_state.get("enabled") is True
        and automation_state.get("production_allowed") is False
    )
    if not auto_ok:
        return {
            "schema": SCHEMA_RECOVERY,
            "at_utc": utc_now(),
            "status": "OBSERVE_ONLY_AUTOMATION_DISABLED",
            "recoveries_attempted": 0,
            "recoveries_succeeded": 0,
            "actions": [],
            "production_touched": False,
        }

    min_mtime_epoch: float | None = None
    enabled_at_raw = str((automation_state or {}).get("enabled_at_utc") or "").strip()
    if enabled_at_raw:
        try:
            min_mtime_epoch = datetime.fromisoformat(enabled_at_raw.replace("Z", "+00:00")).timestamp()
        except ValueError:
            min_mtime_epoch = None
    adopted = set((automation_state or {}).get("adopted_job_ids") or ())

    # Record forensic artifacts for corrupt drafts without ever modifying/reconstructing them
    actions_log: list[dict[str, Any]] = []
    for corrupt in (detection.get("corrupt_drafts") or [])[:5]:
        if isinstance(corrupt, dict) and corrupt.get("job_id"):
            fpath = qroot / "maintenance" / "forensics" / f"{corrupt['job_id']}.json"
            if not fpath.is_file():
                try:
                    _atomic_write_json(fpath, corrupt)
                except OSError:
                    pass
            actions_log.append({
                "job_id": corrupt["job_id"],
                "action": "FORENSIC_RECORDED_ESCALATED",
                "recovery_category": "UNKNOWN_INCIDENT",
                "production_touched": False,
            })

    rem_in = remote_inbox_ids if remote_inbox_ids is not None else _git_ls_tree_stems(root, "origin/worker/requests", "worker_queue/inbox/")
    rem_res = remote_result_ids if remote_result_ids is not None else _git_ls_tree_stems(root, "origin/worker/results", "worker_queue/results/")

    attempted = 0
    succeeded = 0
    budget = max(1, int(max_recoveries_per_cycle))
    isolated_failed_domains: set[str] = set()

    # Order persistent drafts round-robin by domain so a failing domain never starves other domains
    by_dom_buckets: dict[str, list[dict[str, Any]]] = {}
    for item in detection.get("persistent_drafts") or []:
        if not isinstance(item, dict):
            continue
        if item.get("recovery_category") != "OPERATIONAL_IDEMPOTENT_RECOVERY":
            continue
        dom = str(item.get("domain") or "UNBOUNDED_LEGACY").strip().upper()
        by_dom_buckets.setdefault(dom, []).append(item)

    ordered_candidates: list[dict[str, Any]] = []
    dom_keys = sorted(by_dom_buckets)
    idx = 0
    while True:
        added_any = False
        for dom in dom_keys:
            bucket = by_dom_buckets[dom]
            if idx < len(bucket):
                ordered_candidates.append(bucket[idx])
                added_any = True
        if not added_any:
            break
        idx += 1

    for item in ordered_candidates:
        if attempted >= budget:
            break
        jid = str(item.get("job_id") or "").strip()
        dom = str(item.get("domain") or "UNBOUNDED_LEGACY").strip().upper()
        if not jid or dom in isolated_failed_domains:
            continue
        draft_path = qroot / "drafts" / f"{jid}.json"
        outcome = recover_persistent_readonly_draft(
            draft_path,
            repo_root=root,
            state_root=qroot,
            claims_dir=cdir,
            circuit_state_dir=cb_dir,
            remote_inbox_ids=rem_in,
            remote_result_ids=rem_res,
            authorization_context=authorization_context,
            submit_fn=submit_fn,
            now_epoch=now_epoch,
            min_mtime_epoch=min_mtime_epoch,
            adopted_job_ids=adopted,
        )
        if outcome.get("action") in {
            "RECOVERED_VIA_CANONICAL_PUBLISHER",
            "RECOVERY_FAILED_RECORDED",
            "RECOVERY_REJECTED",
        }:
            attempted += 1
            if outcome.get("recovered") is True:
                succeeded += 1
                rem_in.add(jid)
            else:
                isolated_failed_domains.add(dom)
            actions_log.append({**outcome, "domain": dom})

    # Bounded authorized auto-resume for concurrency-blocked objectives (shares cycle budget)
    resumable_candidates = scan_resumable_concurrency_blocked_objectives(
        repo_root=root,
        state_root=qroot,
        now_epoch=now_epoch,
    )
    authorized_resume_ids = set((automation_state or {}).get("authorized_resume_job_ids") or ())
    resumes_evaluated = 0
    for cand in resumable_candidates:
        if attempted >= budget:
            break
        if cand.get("already_has_resume"):
            continue
        resumes_evaluated += 1
        r_out = resume_authorized_concurrency_blocked_objective(
            str(cand["job_id"]),
            repo_root=root,
            state_root=qroot,
            circuit_state_dir=cb_dir,
            authorization_context=authorization_context,
            authorized_resume_job_ids=authorized_resume_ids,
            submit_fn=submit_fn,
            now_epoch=now_epoch,
        )
        if r_out.get("action") in {
            "RESUMED_VIA_CANONICAL_PUBLISHER",
            "RESUME_FAILED_RECORDED",
            "RESUME_REJECTED",
        }:
            attempted += 1
            if r_out.get("resumed") is True:
                succeeded += 1
            actions_log.append(r_out)

    return {
        "schema": SCHEMA_RECOVERY,
        "at_utc": utc_now(),
        "status": "ACTIVE",
        "domain_isolation_active": True,
        "isolated_failed_domains": sorted(isolated_failed_domains),
        "resumable_concurrency_candidates": len(resumable_candidates),
        "resumes_evaluated": resumes_evaluated,
        "max_recoveries_per_cycle": budget,
        "recoveries_attempted": attempted,
        "recoveries_succeeded": succeeded,
        "actions": actions_log,
        "production_touched": False,
    }


# ============================================================================
# Gate P2D — Canonical Gate Authorization & Authorized Concurrency Auto-Resume
# ============================================================================

SCHEMA_GATE_AUTHORIZATION = "edarsahub.gate-authorization.v1"
SCHEMA_CONCURRENCY_RESUME = "edarsahub.worker-concurrency-resume.v1"
SCHEMA_HISTORICAL_RECONCILIATION = "edarsahub.worker-historical-reconciliation.v1"
HISTORICAL_RECONCILIATION_FILENAME = "historical_reconciliation_ledger.json"
HISTORICAL_DRAFT_AGE_SECONDS = int(os.environ.get("EDARSAHUB_HISTORICAL_DRAFT_AGE_SECONDS", str(86400 * 3)))
CONCURRENCY_BLOCKED_STATUSES = frozenset({
    "GIT_WORKTREE_NOT_CLEAN",
    "BLOCKED_LOCAL_DIRTY",
    "CONCURRENT_SCOPE_CONFLICT",
    "GIT_LOCK_BUSY",
    "BLOCKED_CONVERGENCE",
    "RUNTIME_NOT_CONVERGED",
})
MAX_CONCURRENCY_RESUMES_PER_JOB = 2


def _authorization_dir(state_root: Path) -> Path:
    return state_root / "maintenance" / "authorizations"


def _parse_iso_utc_dt(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def list_active_gate_authorizations(
    *,
    state_root: Path | None = None,
    now_utc: datetime | None = None,
) -> list[dict[str, Any]]:
    """Return all currently valid, non-expired, non-revoked, non-production materialized Gate authorizations."""
    qroot = state_root or (Path(os.environ.get("EDARSAHUB_ROOT", "/app")) / ".git" / "universal-worker-queue")
    adir = _authorization_dir(qroot)
    if not adir.is_dir():
        return []
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    active: list[dict[str, Any]] = []
    for path in sorted(adir.glob("*.json")):
        raw = _read_json_safe(path)
        if not isinstance(raw, dict) or raw.get("schema") != SCHEMA_GATE_AUTHORIZATION:
            continue
        if raw.get("production_allowed") is not False:
            continue
        if raw.get("revoked") is True:
            continue
        auth_id = str(raw.get("authorization_id") or raw.get("authorization_ref") or "").strip()
        if not auth_id:
            continue
        expires_dt = _parse_iso_utc_dt(raw.get("expires_at_utc"))
        if expires_dt is None or expires_dt <= now:
            continue
        scope = raw.get("scope") if isinstance(raw.get("scope"), Mapping) else {}
        domains = [
            str(d).strip().upper()
            for d in (scope.get("domains") or ())
            if str(d).strip() and str(d).strip() != "*"
        ]
        if not domains:
            continue
        active.append({**raw, "authorization_path": str(path)})
    return active


def resolve_active_domain_authorization(
    domain: str,
    *,
    state_root: Path | None = None,
    required_class: str = "DEVELOPMENT_MUTATION",
    requested_paths: list[str] | tuple[str, ...] | set[str] | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any] | None:
    """Resolve the newest valid materialized Gate authorization matching a specific domain (fail-closed)."""
    dom = str(domain or "").strip().upper()
    if not dom or dom == "*":
        return None
    req_paths = {str(p).strip().lstrip("./") for p in (requested_paths or ()) if str(p).strip()}
    candidates: list[dict[str, Any]] = []
    for auth in list_active_gate_authorizations(state_root=state_root, now_utc=now_utc):
        scope = auth.get("scope") if isinstance(auth.get("scope"), Mapping) else {}
        domains = {str(d).strip().upper() for d in (scope.get("domains") or ()) if str(d).strip()}
        if dom not in domains or "*" in domains:
            continue
        allowed_paths = {str(p).strip().lstrip("./") for p in (scope.get("allowed_paths") or ()) if str(p).strip()}
        if req_paths and allowed_paths and not req_paths.issubset(allowed_paths):
            continue
        ver = verify_gate_authorization(
            str(auth.get("gate_id") or ""),
            domain=dom,
            required_class=required_class,
            state_root=state_root,
            now_utc=now_utc,
        )
        if ver.get("authorized") is True:
            candidates.append(auth)
    if not candidates:
        return None
    candidates.sort(key=lambda a: str(a.get("granted_at_utc") or ""), reverse=True)
    return candidates[0]


def _load_historical_reconciliation_ledger(state_root: Path) -> dict[str, Any]:
    path = state_root / "maintenance" / HISTORICAL_RECONCILIATION_FILENAME
    data = _read_json_safe(path)
    if isinstance(data, dict) and data.get("schema") == SCHEMA_HISTORICAL_RECONCILIATION:
        return data
    return {}


def reconcile_historical_queue_artifacts(
    *,
    repo_root: Path | None = None,
    state_root: Path | None = None,
    claims_dir: Path | None = None,
    attestations_dir: Path | None = None,
    now_epoch: float | None = None,
    historical_draft_age_seconds: int = HISTORICAL_DRAFT_AGE_SECONDS,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Non-destructive historical reconciliation ledger for superseded PENDING_AUDIT_EVIDENCE, legacy drafts, and abandoned publisher branches.

    Safety invariants:
    - NEVER deletes or alters historical results or corrupt drafts.
    - NEVER fabricates CERTIFIED status; records exact Git ancestry + attestation proof.
    - Only prunes abandoned local agent/queue-publisher/* branches with NO active claim and NO attached worktree,
      recording their commit SHA in the ledger first.
    """
    root = repo_root or Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    qroot = state_root or (root / ".git" / "universal-worker-queue")
    cdir = claims_dir or (root / ".git" / "agent-guard" / "state" / "claims")
    adir = attestations_dir or (root / ".git" / "mirror-sync" / "reporting" / "test_attestations")
    now_ts = float(now_epoch if now_epoch is not None else time.time())

    ledger_path = qroot / "maintenance" / HISTORICAL_RECONCILIATION_FILENAME
    pub_dir = qroot / "published"
    res_dir = qroot / "results"
    drafts_dir = qroot / "drafts"
    done_dir = qroot / "done"
    rejected_dir = qroot / "rejected"
    pending_dir = qroot / "pending"
    processing_dir = qroot / "processing"

    def _dsig(d: Path) -> str:
        if not d.is_dir():
            return "ABSENT"
        st = d.stat()
        return f"{st.st_mtime_ns}:{sum(1 for _ in d.iterdir())}"

    sigs = {
        "published": _dsig(pub_dir),
        "drafts": _dsig(drafts_dir),
        "results": _dsig(res_dir),
    }
    prior = _load_historical_reconciliation_ledger(qroot)
    if not force_refresh and prior and prior.get("dir_signatures") == sigs:
        return {**prior, "ledger_path": str(ledger_path), "cached": True}

    def _is_ancestor(sha: str, ref: str) -> bool:
        proc = subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", sha, ref],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        return proc.returncode == 0

    def _files_identical(sha: str, ref: str, files: list[str]) -> bool:
        if not files:
            return False
        proc = subprocess.run(
            ["git", "-C", str(root), "diff", "--quiet", sha, ref, "--", *files],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        return proc.returncode == 0

    # 1. Reconcile historical PENDING_AUDIT_EVIDENCE markers
    pending_reconciled: dict[str, dict[str, Any]] = {}
    live_pending_audit: list[str] = []
    if pub_dir.is_dir():
        for p in sorted(pub_dir.glob("*.json")):
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "certification=PENDING_AUDIT_EVIDENCE" not in txt:
                continue
            jid = p.stem
            res_obj = _read_json_safe(res_dir / f"{jid}.json") or {}
            dev_sha = str(
                res_obj.get("development_sha")
                or res_obj.get("candidate_sha")
                or res_obj.get("commit_created")
                or ""
            ).strip().lower()
            files_changed = [str(f).strip() for f in (res_obj.get("files_changed") or []) if str(f).strip()]
            if not _SHA_RE.fullmatch(dev_sha):
                pending_reconciled[jid] = {
                    "classification": "HISTORICAL_LEGACY_NO_SHA",
                    "development_sha": None,
                    "has_attestation": False,
                    "reconciled_at_utc": utc_now(),
                }
                continue
            in_dev = _is_ancestor(dev_sha, "origin/Edarsahub_Desarrollo")
            in_mir = _is_ancestor(dev_sha, "origin/mirror/emergent-live")
            has_att = (adir / f"{dev_sha}.json").is_file()
            if in_dev and in_mir:
                if has_att and not _files_identical(dev_sha, "origin/Edarsahub_Desarrollo", files_changed):
                    pending_reconciled[jid] = {
                        "classification": "HISTORICAL_SUPERSEDED_ATTESTED",
                        "development_sha": dev_sha,
                        "in_development_history": True,
                        "in_mirror_history": True,
                        "has_attestation": True,
                        "files_superseded_by_later_commits": True,
                        "reconciled_at_utc": utc_now(),
                    }
                elif not has_att:
                    pending_reconciled[jid] = {
                        "classification": "HISTORICAL_INTEGRATED_PRE_ATTESTATION",
                        "development_sha": dev_sha,
                        "in_development_history": True,
                        "in_mirror_history": True,
                        "has_attestation": False,
                        "reconciled_at_utc": utc_now(),
                    }
                else:
                    live_pending_audit.append(jid)
            else:
                live_pending_audit.append(jid)

    # 2. Classify historical abandoned drafts (> historical_draft_age_seconds, no active claim, untouched on disk)
    settled_ids: set[str] = set()
    for d in (res_dir, done_dir, rejected_dir, pending_dir, processing_dir):
        if d.is_dir():
            settled_ids.update(p.stem for p in d.glob("*.json"))
    active_claims = _active_publisher_claim_ids(cdir)

    historical_drafts: dict[str, dict[str, Any]] = {}
    if drafts_dir.is_dir():
        for dp in sorted(drafts_dir.glob("*.json")):
            jid = dp.stem
            if jid in settled_ids:
                continue
            try:
                age_s = max(0.0, now_ts - dp.stat().st_mtime)
            except OSError:
                continue
            if age_s < historical_draft_age_seconds:
                continue
            if f"queue-publisher-{_safe_id(jid)}" in active_claims:
                continue
            raw_obj = _read_json_safe(dp)
            if not isinstance(raw_obj, dict):
                continue
            mode = str(raw_obj.get("mode") or "UNKNOWN").upper()
            dom = str((raw_obj.get("scheduling") or {}).get("bounded_context") or "UNBOUNDED_LEGACY").strip().upper()
            historical_drafts[jid] = {
                "classification": "HISTORICAL_ABANDONED_DRAFT_PRESERVED",
                "domain": dom,
                "mode": mode,
                "age_seconds": int(age_s),
                "preserved_untouched": True,
                "reconciled_at_utc": utc_now(),
            }

    # 3. Safely prune abandoned orphan publisher branches (no active claim, no attached worktree, draft > historical_draft_age_seconds or settled)
    abandoned_branches_pruned: list[dict[str, Any]] = list(prior.get("abandoned_branches_pruned") or [])
    wt_branches: set[str] = set()
    wt_proc = subprocess.run(
        ["git", "-C", str(root), "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if wt_proc.returncode == 0:
        for line in wt_proc.stdout.splitlines():
            if line.startswith("branch refs/heads/"):
                wt_branches.add(line.split("branch refs/heads/", 1)[1].strip())

    for item in _list_orphan_publisher_branches(root, cdir):
        branch = str(item.get("branch") or "").strip()
        if not branch.startswith("agent/queue-publisher/") or branch in wt_branches:
            continue
        jid = branch.split("agent/queue-publisher/", 1)[1]
        if jid not in settled_ids and jid not in historical_drafts:
            continue
        sha_proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", branch],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        branch_sha = (sha_proc.stdout or "").strip()
        del_proc = subprocess.run(
            ["git", "-C", str(root), "branch", "-D", branch],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        if del_proc.returncode == 0:
            abandoned_branches_pruned.append({
                "branch": branch,
                "job_id": jid,
                "preserved_sha": branch_sha or None,
                "reason": "SETTLED" if jid in settled_ids else "HISTORICAL_ABANDONED_NO_CLAIM_NO_WORKTREE",
                "pruned_at_utc": utc_now(),
            })

    ledger: dict[str, Any] = {
        "schema": SCHEMA_HISTORICAL_RECONCILIATION,
        "reconciled_at_utc": utc_now(),
        "dir_signatures": sigs,
        "pending_audit_reconciled": pending_reconciled,
        "pending_audit_reconciled_count": len(pending_reconciled),
        "live_pending_audit_remaining": live_pending_audit,
        "historical_drafts_classified": historical_drafts,
        "historical_drafts_classified_count": len(historical_drafts),
        "abandoned_branches_pruned": abandoned_branches_pruned[-100:],
        "abandoned_branches_pruned_count": len(abandoned_branches_pruned),
        "production_touched": False,
    }
    try:
        _atomic_write_json(ledger_path, ledger)
    except OSError:
        pass
    return {**ledger, "ledger_path": str(ledger_path), "cached": False}


def materialize_gate_authorization(
    *,
    gate_id: str,
    authorization_id: str,
    granted_by: str,
    domains: list[str] | tuple[str, ...],
    allowed_paths: list[str] | tuple[str, ...] = (),
    authorization_classes: list[str] | tuple[str, ...] = ("DEVELOPMENT_MUTATION",),
    actor_roles: list[str] | tuple[str, ...] = ("SUPERADMIN",),
    actor_permissions: list[str] | tuple[str, ...] = ("*",),
    ttl_hours: int = 24,
    base_head_sha: str = "",
    state_root: Path | None = None,
    production_allowed: bool = False,
) -> dict[str, Any]:
    """Materialize a traceable, time-bounded, fail-closed Gate authorization artifact."""
    if production_allowed is not False:
        raise ValueError("PRODUCTION_AUTHORIZATION_FORBIDDEN")
    clean_gate = _safe_id(gate_id)
    clean_auth = str(authorization_id or "").strip()
    if not clean_gate or not clean_auth:
        raise ValueError("GATE_AUTHORIZATION_ID_REQUIRED")
    clean_domains = sorted({str(d).strip().upper() for d in domains if str(d).strip() and str(d).strip() != "*"})
    if not clean_domains:
        raise ValueError("EXPLICIT_NON_WILDCARD_DOMAIN_REQUIRED")
    clean_classes = sorted({str(c).strip().upper() for c in authorization_classes if str(c).strip() and str(c).strip().upper() != "PRODUCTION"})
    if not clean_classes:
        raise ValueError("AUTHORIZATION_CLASSES_REQUIRED")

    now_dt = datetime.now(timezone.utc)
    expires_dt = now_dt + timedelta(hours=max(1, min(int(ttl_hours), 168)))
    qroot = state_root or (Path(os.environ.get("EDARSAHUB_ROOT", "/app")) / ".git" / "universal-worker-queue")
    payload: dict[str, Any] = {
        "schema": SCHEMA_GATE_AUTHORIZATION,
        "gate_id": clean_gate,
        "authorization_id": clean_auth,
        "authorization_ref": clean_auth,
        "authorization_classes": clean_classes,
        "mutation_authorized": bool(set(clean_classes) & {"DEVELOPMENT_MUTATION", "PREAUTHORIZED_CODE_MUTATION"}),
        "production_allowed": False,
        "revoked": False,
        "granted_by": str(granted_by or "").strip() or "human_responsible_explicit_go",
        "granted_at_utc": now_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at_utc": expires_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "base_head_sha": str(base_head_sha or "").strip(),
        "target_branch": "Edarsahub_Desarrollo",
        "actor_roles": [str(r).strip() for r in actor_roles if str(r).strip()],
        "actor_permissions": [str(p).strip() for p in actor_permissions if str(p).strip()],
        "scope": {
            "domains": clean_domains,
            "allowed_paths": sorted({str(p).strip() for p in allowed_paths if str(p).strip()}),
        },
        "production_touched": False,
    }
    path = _authorization_dir(qroot) / f"{clean_gate}.json"
    _atomic_write_json(path, payload)
    return {**payload, "authorization_path": str(path)}


def verify_gate_authorization(
    gate_id: str,
    *,
    domain: str,
    required_class: str = "DEVELOPMENT_MUTATION",
    mutation_class: str = "CODE_MUTATION",
    state_root: Path | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Fail-closed verification of a materialized Gate authorization via gate_chain_controller."""
    qroot = state_root or (Path(os.environ.get("EDARSAHUB_ROOT", "/app")) / ".git" / "universal-worker-queue")
    clean_gate = _safe_id(gate_id)
    path = _authorization_dir(qroot) / f"{clean_gate}.json"
    raw = _read_json_safe(path)
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA_GATE_AUTHORIZATION:
        return {"authorized": False, "reason": "GATE_AUTHORIZATION_NOT_FOUND", "gate_id": clean_gate, "production_touched": False}
    if raw.get("production_allowed") is True:
        return {"authorized": False, "reason": "PRODUCTION_FORBIDDEN", "gate_id": clean_gate, "production_touched": False}
    gate_spec = {
        "gate_id": clean_gate,
        "mutation_class": mutation_class,
        "authorization_class": required_class,
        "require_traceable_authorization": True,
        "production_allowed": False,
        "required_scope": {"domain": [str(domain or "").strip().upper()]},
    }
    ok, reason = policy_ctrl.evaluate_gate_authorization(
        gate_spec,
        authorization_classes=raw.get("authorization_classes") or (),
        authorization_context=raw,
        now_utc=now_utc,
    )
    return {
        "authorized": bool(ok),
        "reason": str(reason),
        "gate_id": clean_gate,
        "authorization_id": raw.get("authorization_id"),
        "authorization_path": str(path),
        "production_touched": False,
    }


SCHEMA_GATE_CONSENT = "edarsahub.gate-consent.v1"
SCHEMA_HUMAN_APPROVAL = "edarsahub.gate-human-approval.v1"
SCHEMA_AUTH_LIFECYCLE_PREFLIGHT = "edarsahub.gate-authorization-preflight.v1"

ALLOWED_MUTATION_OPERATIONS = frozenset({
    "replace_text",
    "insert_before",
    "insert_after",
    "append_once",
    "write_file",
})

_AUTH_SYNTHETIC_EMAILS = frozenset({
    "worker@edarsahub.local",
    "worker-publisher@edarsahub.local",
    "system@edarsahub.local",
    "noreply@edarsahub.local",
})

_AUTH_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?\b"),
    re.compile(r"(?i)\bbypass\s+(?:rbac|auth|authentication|authorization|guardrails?|security)\b"),
    re.compile(r"(?i)\bproduction_allowed\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bedarsahub_produccion\b"),
    re.compile(r"(?i)\bgit\s+push\s+(?:--force|-f)\b"),
    re.compile(r"(?i)\bgit\s+reset\s+--hard\b"),
)


class GateAuthorizationError(ValueError):
    """Fail-closed error for autonomous Gate authorization lifecycle violations."""


class GateAuthorizationConflictError(GateAuthorizationError):
    """Fail-closed conflict when materializing a diverging scope for an existing gate_id."""


def _approvals_dir(state_root: Path) -> Path:
    return state_root / "maintenance" / "approvals"


def _consent_signing_secret() -> bytes:
    secret = str(
        os.environ.get("EDARSAHUB_CONSENT_SIGNING_SECRET")
        or os.environ.get("JWT_SECRET")
        or ""
    ).strip()
    if len(secret) < 16:
        raise GateAuthorizationError("CONSENT_SIGNING_SECRET_UNAVAILABLE")
    return secret.encode("utf-8")


def _assert_no_auth_prompt_injection(value: Any, path: str = "authorization") -> None:
    if isinstance(value, Mapping):
        for k, v in value.items():
            _assert_no_auth_prompt_injection(v, f"{path}.{k}")
    elif isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            _assert_no_auth_prompt_injection(item, f"{path}[{idx}]")
    elif isinstance(value, str):
        for pat in _AUTH_INJECTION_PATTERNS:
            if pat.search(value):
                raise GateAuthorizationError(f"AUTHORIZATION_UNTRUSTED_PROMPT_BLOCKED:{path}")


def compute_authorization_scope_digest(
    *,
    domain: str,
    gate_id: str,
    objective: str,
    authorized_operations: list[str] | tuple[str, ...],
    allowed_paths: list[str] | tuple[str, ...],
    source_sha256: Mapping[str, str],
    base_head_sha: str,
    ttl_hours: int,
    verification_tests: list[str] | tuple[str, ...],
    rollback_plan: Mapping[str, Any] | str,
    production_allowed: bool = False,
) -> str:
    """Compute canonical SHA-256 scope digest binding verifiable consent to exact Gate scope."""
    if production_allowed is not False:
        raise GateAuthorizationError("PRODUCTION_AUTHORIZATION_FORBIDDEN")
    basis = {
        "domain": str(domain or "").strip().upper(),
        "gate_id": _safe_id(gate_id),
        "objective": str(objective or "").strip(),
        "authorized_operations": sorted({str(op).strip() for op in authorized_operations if str(op).strip()}),
        "allowed_paths": sorted({str(p).strip().lstrip("./") for p in allowed_paths if str(p).strip()}),
        "source_sha256": {
            str(k).strip().lstrip("./"): str(v).strip().lower()
            for k, v in sorted((source_sha256 or {}).items())
        },
        "base_head_sha": str(base_head_sha or "").strip().lower(),
        "ttl_hours": int(ttl_hours),
        "verification_tests": sorted({str(t).strip().lstrip("./") for t in verification_tests if str(t).strip()}),
        "rollback_plan": (
            dict(rollback_plan)
            if isinstance(rollback_plan, Mapping)
            else str(rollback_plan or "").strip()
        ),
        "production_allowed": False,
    }
    return hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def issue_verifiable_consent_attestation(
    *,
    usuario_id: int,
    email: str,
    gate_id: str,
    domain: str,
    scope_digest: str,
    session_id: str | None = None,
    ttl_minutes: int = 30,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Issue a server-signed human consent attestation bound to SQL user + exact scope digest."""
    clean_email = str(email or "").strip().lower()
    if not clean_email or "@" not in clean_email or clean_email in _AUTH_SYNTHETIC_EMAILS:
        raise GateAuthorizationError("CONSENT_IDENTITY_INVALID")
    if isinstance(usuario_id, bool) or int(usuario_id) <= 0:
        raise GateAuthorizationError("CONSENT_SQL_USER_REQUIRED")
    clean_gate = _safe_id(gate_id)
    clean_dom = str(domain or "").strip().upper()
    if not clean_gate or not clean_dom or clean_dom == "*" or "PRODUCTION" in clean_dom or "PRODUCCION" in clean_dom:
        raise GateAuthorizationError("CONSENT_SCOPE_INVALID")
    clean_digest = str(scope_digest or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", clean_digest):
        raise GateAuthorizationError("CONSENT_SCOPE_DIGEST_INVALID")

    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    exp = now + timedelta(minutes=max(1, min(int(ttl_minutes), 1440)))
    nonce = secrets.token_hex(16)
    claims = {
        "schema": SCHEMA_GATE_CONSENT,
        "channel": "OAUTH_VERIFIED_CONSENT_TOKEN",
        "usuario_id": int(usuario_id),
        "email": clean_email,
        "gate_id": clean_gate,
        "domain": clean_dom,
        "scope_digest": clean_digest,
        "session_id": str(session_id or "").strip() or None,
        "nonce": nonce,
        "issued_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at_utc": exp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "production_allowed": False,
    }
    canonical_msg = json.dumps(claims, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(_consent_signing_secret(), canonical_msg, hashlib.sha256).hexdigest()
    return {**claims, "signature": sig}


def record_human_approval_artifact(
    *,
    approval_id: str,
    usuario_id: int,
    email: str,
    gate_id: str,
    domain: str,
    scope_digest: str,
    ttl_hours: int = 24,
    state_root: Path | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Record an out-of-band canonical human approval artifact bound to exact scope_digest."""
    clean_app = _safe_id(approval_id)
    clean_email = str(email or "").strip().lower()
    clean_gate = _safe_id(gate_id)
    clean_dom = str(domain or "").strip().upper()
    clean_digest = str(scope_digest or "").strip().lower()
    if not clean_app or not clean_gate or not clean_dom or clean_dom == "*":
        raise GateAuthorizationError("APPROVAL_FIELDS_INVALID")
    if not clean_email or "@" not in clean_email or clean_email in _AUTH_SYNTHETIC_EMAILS:
        raise GateAuthorizationError("APPROVAL_IDENTITY_INVALID")
    if isinstance(usuario_id, bool) or int(usuario_id) <= 0:
        raise GateAuthorizationError("APPROVAL_SQL_USER_REQUIRED")
    if not re.fullmatch(r"[0-9a-f]{64}", clean_digest):
        raise GateAuthorizationError("APPROVAL_SCOPE_DIGEST_INVALID")

    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    exp = now + timedelta(hours=max(1, min(int(ttl_hours), 168)))
    qroot = state_root or (Path(os.environ.get("EDARSAHUB_ROOT", "/app")) / ".git" / "universal-worker-queue")
    doc = {
        "schema": SCHEMA_HUMAN_APPROVAL,
        "channel": "CANONICAL_APPROVAL_RECORD",
        "approval_id": clean_app,
        "usuario_id": int(usuario_id),
        "email": clean_email,
        "gate_id": clean_gate,
        "domain": clean_dom,
        "scope_digest": clean_digest,
        "approved_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at_utc": exp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "revoked": False,
        "production_allowed": False,
        "production_touched": False,
    }
    path = _approvals_dir(qroot) / f"{clean_app}.json"
    _atomic_write_json(path, doc)
    return {**doc, "approval_path": str(path)}


def verify_consent_attestation(
    consent_evidence: Any,
    *,
    expected_usuario_id: int,
    expected_email: str,
    expected_gate_id: str,
    expected_domain: str,
    expected_scope_digest: str,
    state_root: Path,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Verify cryptographic or canonical out-of-band human consent fail-closed.

    NEVER accepts free-text agent-invented strings, missing evidence, forged signatures,
    mismatched scopes, expired approvals, or Worker self-grants.
    """
    if not isinstance(consent_evidence, Mapping) or not consent_evidence:
        raise GateAuthorizationError("CONSENT_VERIFICATION_REQUIRED")
    if consent_evidence.get("production_allowed") is True:
        raise GateAuthorizationError("PRODUCTION_AUTHORIZATION_FORBIDDEN")

    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    channel = str(consent_evidence.get("channel") or "").strip().upper()
    if channel == "OAUTH_VERIFIED_CONSENT_TOKEN":
        if consent_evidence.get("schema") != SCHEMA_GATE_CONSENT:
            raise GateAuthorizationError("CONSENT_SCHEMA_INVALID")
        supplied_sig = str(consent_evidence.get("signature") or "").strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", supplied_sig):
            raise GateAuthorizationError("CONSENT_SIGNATURE_INVALID")
        unsigned = {k: v for k, v in consent_evidence.items() if k != "signature"}
        canonical_msg = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        expected_sig = hmac.new(_consent_signing_secret(), canonical_msg, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(supplied_sig, expected_sig):
            raise GateAuthorizationError("CONSENT_SIGNATURE_INVALID")

        if int(consent_evidence.get("usuario_id") or 0) != int(expected_usuario_id):
            raise GateAuthorizationError("CONSENT_IDENTITY_MISMATCH")
        if str(consent_evidence.get("email") or "").strip().lower() != str(expected_email).strip().lower():
            raise GateAuthorizationError("CONSENT_IDENTITY_MISMATCH")
        if _safe_id(str(consent_evidence.get("gate_id") or "")) != _safe_id(expected_gate_id):
            raise GateAuthorizationError("CONSENT_GATE_MISMATCH")
        if str(consent_evidence.get("domain") or "").strip().upper() != str(expected_domain).strip().upper():
            raise GateAuthorizationError("CONSENT_DOMAIN_MISMATCH")
        if str(consent_evidence.get("scope_digest") or "").strip().lower() != expected_scope_digest:
            raise GateAuthorizationError("CONSENT_SCOPE_MISMATCH")
        exp_dt = _parse_iso_utc_dt(consent_evidence.get("expires_at_utc"))
        if exp_dt is None or exp_dt <= now:
            raise GateAuthorizationError("CONSENT_EXPIRED")

        return {
            "verified": True,
            "channel": channel,
            "verified_usuario_id": int(expected_usuario_id),
            "verified_email": str(expected_email).strip().lower(),
            "scope_digest": expected_scope_digest,
            "nonce": str(consent_evidence.get("nonce") or ""),
            "session_id": consent_evidence.get("session_id"),
            "issued_at_utc": consent_evidence.get("issued_at_utc"),
            "expires_at_utc": consent_evidence.get("expires_at_utc"),
            "verified_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    if channel == "CANONICAL_APPROVAL_RECORD":
        approval_id = _safe_id(str(consent_evidence.get("approval_id") or ""))
        if not approval_id:
            raise GateAuthorizationError("CONSENT_APPROVAL_ID_REQUIRED")
        path = _approvals_dir(state_root) / f"{approval_id}.json"
        doc = _read_json_safe(path)
        if not isinstance(doc, dict) or doc.get("schema") != SCHEMA_HUMAN_APPROVAL:
            raise GateAuthorizationError("CONSENT_APPROVAL_NOT_FOUND")
        if doc.get("production_allowed") is True:
            raise GateAuthorizationError("PRODUCTION_AUTHORIZATION_FORBIDDEN")
        if doc.get("revoked") is True:
            raise GateAuthorizationError("CONSENT_APPROVAL_REVOKED")
        if int(doc.get("usuario_id") or 0) != int(expected_usuario_id):
            raise GateAuthorizationError("CONSENT_IDENTITY_MISMATCH")
        if str(doc.get("email") or "").strip().lower() != str(expected_email).strip().lower():
            raise GateAuthorizationError("CONSENT_IDENTITY_MISMATCH")
        if _safe_id(str(doc.get("gate_id") or "")) != _safe_id(expected_gate_id):
            raise GateAuthorizationError("CONSENT_GATE_MISMATCH")
        if str(doc.get("domain") or "").strip().upper() != str(expected_domain).strip().upper():
            raise GateAuthorizationError("CONSENT_DOMAIN_MISMATCH")
        if str(doc.get("scope_digest") or "").strip().lower() != expected_scope_digest:
            raise GateAuthorizationError("CONSENT_SCOPE_MISMATCH")
        exp_dt = _parse_iso_utc_dt(doc.get("expires_at_utc"))
        if exp_dt is None or exp_dt <= now:
            raise GateAuthorizationError("CONSENT_EXPIRED")

        return {
            "verified": True,
            "channel": channel,
            "approval_id": approval_id,
            "verified_usuario_id": int(expected_usuario_id),
            "verified_email": str(expected_email).strip().lower(),
            "scope_digest": expected_scope_digest,
            "approved_at_utc": doc.get("approved_at_utc"),
            "expires_at_utc": doc.get("expires_at_utc"),
            "verified_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    raise GateAuthorizationError("CONSENT_CHANNEL_UNVERIFIABLE_FAIL_CLOSED")


def _validate_authorized_actor_identity(
    current_user: Mapping[str, Any] | None,
    *,
    identity_resolver: Any = None,
) -> dict[str, Any]:
    """Validate canonical authenticated human/service actor without wildcard or synthetic fallback."""
    if not isinstance(current_user, Mapping):
        raise GateAuthorizationError("AUTHORIZATION_ACTOR_IDENTITY_REQUIRED")
    if current_user.get("active") is False:
        raise GateAuthorizationError("AUTHORIZATION_ACTOR_INACTIVE")
    if current_user.get("self_granted") is True or str(current_user.get("source") or "").lower() in {"universal-worker", "worker-self"}:
        raise GateAuthorizationError("SELF_PRIVILEGE_ESCALATION_FORBIDDEN")

    email = str(current_user.get("email") or "").strip().lower()
    if not email or "@" not in email or email in _AUTH_SYNTHETIC_EMAILS:
        raise GateAuthorizationError("AUTHORIZATION_ACTOR_IDENTITY_UNVERIFIABLE")

    raw_perms = current_user.get("permissions") or current_user.get("permisos") or ()
    perms_list = [str(p).strip() for p in raw_perms if str(p).strip()] if isinstance(raw_perms, (list, tuple, set, frozenset)) else []
    if "*" in perms_list:
        raise GateAuthorizationError("AUTHORIZATION_WILDCARD_PERMISSION_FORBIDDEN")

    if identity_resolver is not None:
        resolved = identity_resolver(email)
        if not isinstance(resolved, Mapping) or resolved.get("active") is False:
            raise GateAuthorizationError("AUTHORIZATION_SQL_IDENTITY_UNVERIFIABLE")
        actor = dict(resolved)
    else:
        sql_uid = current_user.get("usuario_id") or current_user.get("_sql_usuario_id") or current_user.get("UsuarioID")
        if sql_uid is None:
            # Resolve canonically from SQL RBAC when caller dict only carries email
            try:
                from tools.mirror_sync import worker_cross_domain_handoff as _hm
                actor = _hm._resolve_canonical_sql_service_identity(email)
            except Exception as exc:
                raise GateAuthorizationError(f"AUTHORIZATION_SQL_IDENTITY_UNVERIFIABLE:{type(exc).__name__}") from exc
        else:
            actor = dict(current_user)

    raw_uid = actor.get("usuario_id") or actor.get("_sql_usuario_id") or actor.get("UsuarioID")
    if isinstance(raw_uid, bool):
        raise GateAuthorizationError("AUTHORIZATION_SQL_USER_INVALID")
    try:
        usuario_id = int(raw_uid)
    except (TypeError, ValueError):
        raise GateAuthorizationError("AUTHORIZATION_SQL_USER_INVALID") from None
    if usuario_id <= 0:
        raise GateAuthorizationError("AUTHORIZATION_SQL_USER_INVALID")

    eff_perms = [
        str(p).strip()
        for p in (actor.get("permissions") or actor.get("permisos") or ())
        if str(p).strip()
    ]
    if "*" in eff_perms:
        raise GateAuthorizationError("AUTHORIZATION_WILDCARD_PERMISSION_FORBIDDEN")
    eff_scopes = [
        str(s).strip()
        for s in (actor.get("scopes") or ())
        if str(s).strip()
    ]
    if not eff_scopes:
        eff_scopes = [p for p in eff_perms if p.startswith("worker:")]

    perms_lower = {p.lower() for p in eff_perms}
    scopes_lower = {s.lower() for s in eff_scopes}
    role_text = str(actor.get("role_code") or actor.get("role") or "").strip().upper()
    if "rbac_admin" not in perms_lower:
        raise GateAuthorizationError("AUTHORIZATION_RBAC_ADMIN_REQUIRED")
    if "worker:submit" not in scopes_lower and "worker:submit" not in perms_lower:
        raise GateAuthorizationError("AUTHORIZATION_WORKER_SUBMIT_SCOPE_REQUIRED")

    return {
        "usuario_id": usuario_id,
        "id": str(actor.get("id") or usuario_id),
        "email": str(actor.get("email") or email).strip().lower(),
        "role": str(actor.get("role") or role_text).strip(),
        "role_code": str(actor.get("role_code") or role_text).strip().upper(),
        "auth_source": str(actor.get("auth_source") or "SQL_CANONICAL_RBAC"),
        "effective_permissions": sorted(set(eff_perms)),
        "effective_scopes": sorted(set(eff_scopes)),
    }


def _validate_gate_paths_and_hashes(
    *,
    domain: str,
    allowed_paths: list[str] | tuple[str, ...],
    source_sha256: Mapping[str, str],
    verification_tests: list[str] | tuple[str, ...],
    base_head_sha: str,
    repo_root: Path,
) -> tuple[list[str], dict[str, str], list[str], str]:
    """Validate exact paths (no global root expansion), existing file SHA-256, tests, and live HEAD."""
    from modules.worker_ingress import semantic_capabilities as sem_caps

    if not isinstance(allowed_paths, (list, tuple)) or not allowed_paths:
        raise GateAuthorizationError("AUTHORIZATION_EXACT_PATHS_REQUIRED")
    if len(allowed_paths) > 30:
        raise GateAuthorizationError("AUTHORIZATION_TOO_MANY_PATHS")

    clean_paths: list[str] = []
    for raw_p in allowed_paths:
        p = str(raw_p or "").strip().lstrip("./")
        if not p or "*" in p or p.endswith("/"):
            raise GateAuthorizationError(f"AUTHORIZATION_PATH_NOT_EXACT:{raw_p}")
        try:
            sem_caps._dev_validate_path(p, context=domain)
        except Exception as exc:
            raise GateAuthorizationError(f"AUTHORIZATION_PATH_FORBIDDEN:{p}") from exc
        if p not in clean_paths:
            clean_paths.append(p)
    clean_paths.sort()

    if not isinstance(verification_tests, (list, tuple)) or not verification_tests:
        raise GateAuthorizationError("AUTHORIZATION_VERIFICATION_TESTS_REQUIRED")
    clean_tests: list[str] = []
    for raw_t in verification_tests:
        t = str(raw_t or "").strip().lstrip("./")
        if not t or not t.endswith(".py"):
            raise GateAuthorizationError(f"AUTHORIZATION_TEST_PATH_INVALID:{raw_t}")
        try:
            sem_caps._dev_validate_path(t, allowed_roots=sem_caps._DEV_TEST_ROOTS)
        except Exception as exc:
            raise GateAuthorizationError(f"AUTHORIZATION_TEST_PATH_FORBIDDEN:{t}") from exc
        if t not in clean_tests:
            clean_tests.append(t)
    clean_tests.sort()

    clean_head = str(base_head_sha or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", clean_head):
        raise GateAuthorizationError("AUTHORIZATION_BASE_HEAD_INVALID")
    if (repo_root / ".git").exists():
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if proc.returncode == 0:
            live_head = proc.stdout.strip().lower()
            if live_head and live_head != clean_head:
                raise GateAuthorizationError(f"AUTHORIZATION_HEAD_DIVERGED:{clean_head}!={live_head}")

    supplied_sha = {
        str(k).strip().lstrip("./"): str(v).strip().lower()
        for k, v in (source_sha256.items() if isinstance(source_sha256, Mapping) else ())
    }
    verified_sha: dict[str, str] = {}
    for rel in clean_paths:
        target = repo_root / rel
        if target.is_file():
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            exp = supplied_sha.get(rel)
            if not exp or not re.fullmatch(r"[0-9a-f]{64}", exp):
                raise GateAuthorizationError(f"AUTHORIZATION_SOURCE_SHA256_REQUIRED:{rel}")
            if exp != actual:
                raise GateAuthorizationError(f"AUTHORIZATION_SOURCE_SHA256_STALE:{rel}")
            verified_sha[rel] = actual
        else:
            if rel in supplied_sha and supplied_sha[rel]:
                raise GateAuthorizationError(f"AUTHORIZATION_NEW_FILE_SHA256_UNEXPECTED:{rel}")

    return clean_paths, verified_sha, clean_tests, clean_head


def preflight_gate_authorization_lifecycle(
    request: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any] | None,
    state_root: Path | None = None,
    repo_root: Path | None = None,
    identity_resolver: Any = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """READ_ONLY fail-closed preflight for autonomous Gate authorization materialization/revocation."""
    qroot = state_root or (Path(os.environ.get("EDARSAHUB_ROOT", "/app")) / ".git" / "universal-worker-queue")
    rroot = repo_root or Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    _assert_no_auth_prompt_injection(request, "authorization_request")

    if request.get("production_allowed") is True:
        raise GateAuthorizationError("PRODUCTION_AUTHORIZATION_FORBIDDEN")

    domain = str(request.get("bounded_context") or request.get("domain") or "").strip().upper()
    if not domain or domain == "*" or "PRODUCTION" in domain or "PRODUCCION" in domain:
        raise GateAuthorizationError("AUTHORIZATION_DOMAIN_INVALID")

    constraints = request.get("constraints") if isinstance(request.get("constraints"), Mapping) else request
    if constraints.get("production_allowed") is True:
        raise GateAuthorizationError("PRODUCTION_AUTHORIZATION_FORBIDDEN")

    action = str(constraints.get("action") or "PREFLIGHT").strip().upper()
    if action not in {"PREFLIGHT", "INSPECT", "MATERIALIZE", "REVOKE"}:
        raise GateAuthorizationError(f"AUTHORIZATION_ACTION_UNSUPPORTED:{action}")

    gate_id = _safe_id(str(constraints.get("gate_id") or ""))
    if not gate_id:
        raise GateAuthorizationError("GATE_AUTHORIZATION_ID_REQUIRED")

    actor = _validate_authorized_actor_identity(current_user, identity_resolver=identity_resolver)

    if action == "INSPECT":
        return {
            "schema": SCHEMA_AUTH_LIFECYCLE_PREFLIGHT,
            "ok": True,
            "status": "PREFLIGHT_READY",
            "action": "INSPECT",
            "gate_id": gate_id,
            "domain": domain,
            "actor_email": actor["email"],
            "sql_usuario_id": actor["usuario_id"],
            "production_allowed": False,
            "production_touched": False,
        }

    if action == "REVOKE":
        existing = _read_json_safe(_authorization_dir(qroot) / f"{gate_id}.json")
        if not isinstance(existing, dict) or existing.get("schema") != SCHEMA_GATE_AUTHORIZATION:
            raise GateAuthorizationError("GATE_AUTHORIZATION_NOT_FOUND")
        existing_domains = {
            str(d).strip().upper()
            for d in ((existing.get("scope") or {}).get("domains") or ())
            if str(d).strip()
        }
        if domain not in existing_domains:
            raise GateAuthorizationError("AUTHORIZATION_DOMAIN_MISMATCH")
        return {
            "schema": SCHEMA_AUTH_LIFECYCLE_PREFLIGHT,
            "ok": True,
            "status": "PREFLIGHT_READY",
            "action": "REVOKE",
            "gate_id": gate_id,
            "authorization_id": existing.get("authorization_id"),
            "domain": domain,
            "already_revoked": bool(existing.get("revoked", False)),
            "production_allowed": False,
            "production_touched": False,
        }

    # PREFLIGHT or MATERIALIZE: validate all 18 bound invariants!
    objective = str(request.get("objective") or constraints.get("objective") or "").strip()
    if len(objective) < 10 or len(objective) > 2000:
        raise GateAuthorizationError("AUTHORIZATION_OBJECTIVE_INVALID")

    auth_id = str(constraints.get("authorization_id") or f"GO-{gate_id}").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{2,120}", auth_id):
        raise GateAuthorizationError("AUTHORIZATION_ID_INVALID")

    raw_ops = constraints.get("authorized_operations")
    if not isinstance(raw_ops, (list, tuple)) or not raw_ops:
        raise GateAuthorizationError("AUTHORIZATION_OPERATIONS_REQUIRED")
    clean_ops = sorted({str(op).strip() for op in raw_ops if str(op).strip()})
    if not clean_ops or set(clean_ops) - ALLOWED_MUTATION_OPERATIONS:
        raise GateAuthorizationError("AUTHORIZATION_OPERATION_FORBIDDEN")

    ttl_hours = int(constraints.get("ttl_hours") or 24)
    if not 1 <= ttl_hours <= 168:
        raise GateAuthorizationError("AUTHORIZATION_TTL_INVALID")

    rollback_plan = constraints.get("rollback_plan")
    if isinstance(rollback_plan, Mapping):
        if not rollback_plan:
            raise GateAuthorizationError("AUTHORIZATION_ROLLBACK_PLAN_REQUIRED")
    elif not isinstance(rollback_plan, str) or len(rollback_plan.strip()) < 10:
        raise GateAuthorizationError("AUTHORIZATION_ROLLBACK_PLAN_REQUIRED")

    clean_paths, verified_sha, clean_tests, clean_head = _validate_gate_paths_and_hashes(
        domain=domain,
        allowed_paths=constraints.get("allowed_paths") or (),
        source_sha256=constraints.get("source_sha256") or {},
        verification_tests=constraints.get("verification_tests") or (),
        base_head_sha=str(constraints.get("base_head_sha") or ""),
        repo_root=rroot,
    )

    scope_digest = compute_authorization_scope_digest(
        domain=domain,
        gate_id=gate_id,
        objective=objective,
        authorized_operations=clean_ops,
        allowed_paths=clean_paths,
        source_sha256=verified_sha,
        base_head_sha=clean_head,
        ttl_hours=ttl_hours,
        verification_tests=clean_tests,
        rollback_plan=rollback_plan,
        production_allowed=False,
    )

    consent_verified = verify_consent_attestation(
        constraints.get("consent_evidence"),
        expected_usuario_id=actor["usuario_id"],
        expected_email=actor["email"],
        expected_gate_id=gate_id,
        expected_domain=domain,
        expected_scope_digest=scope_digest,
        state_root=qroot,
        now_utc=now_utc,
    )

    existing = _read_json_safe(_authorization_dir(qroot) / f"{gate_id}.json")
    duplicate_match = False
    if isinstance(existing, dict) and existing.get("schema") == SCHEMA_GATE_AUTHORIZATION:
        if existing.get("revoked") is not True and existing.get("scope_digest") == scope_digest:
            duplicate_match = True
        elif existing.get("revoked") is not True:
            raise GateAuthorizationConflictError("AUTHORIZATION_CONFLICT_SCOPE_DRIFT")

    return {
        "schema": SCHEMA_AUTH_LIFECYCLE_PREFLIGHT,
        "ok": True,
        "status": "EXISTS" if duplicate_match else "PREFLIGHT_READY",
        "action": action,
        "duplicate_detected": duplicate_match,
        "gate_id": gate_id,
        "authorization_id": auth_id,
        "domain": domain,
        "objective": objective,
        "authorized_operations": clean_ops,
        "allowed_paths": clean_paths,
        "source_sha256": verified_sha,
        "base_head_sha": clean_head,
        "ttl_hours": ttl_hours,
        "verification_tests": clean_tests,
        "rollback_plan": dict(rollback_plan) if isinstance(rollback_plan, Mapping) else str(rollback_plan).strip(),
        "scope_digest": scope_digest,
        "actor": actor,
        "consent_verified": consent_verified,
        "production_allowed": False,
        "production_touched": False,
    }


def materialize_gate_authorization_authorized(
    request: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any] | None,
    state_root: Path | None = None,
    repo_root: Path | None = None,
    identity_resolver: Any = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Idempotent, concurrency-safe, consent-verified Gate authorization materialization."""
    qroot = state_root or (Path(os.environ.get("EDARSAHUB_ROOT", "/app")) / ".git" / "universal-worker-queue")
    adir = _authorization_dir(qroot)
    adir.mkdir(parents=True, exist_ok=True)
    lock_path = adir / ".authorizations.lock"

    with open(lock_path, "a+", encoding="utf-8") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        try:
            pf = preflight_gate_authorization_lifecycle(
                request,
                current_user=current_user,
                state_root=qroot,
                repo_root=repo_root,
                identity_resolver=identity_resolver,
                now_utc=now_utc,
            )
            gate_id = pf["gate_id"]
            path = adir / f"{gate_id}.json"
            if pf.get("duplicate_detected") is True:
                existing = _read_json_safe(path) or {}
                return {
                    **existing,
                    "status": "EXISTS",
                    "duplicate_prevented": True,
                    "authorization_path": str(path),
                    "production_touched": False,
                }

            now = now_utc or datetime.now(timezone.utc)
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            expires_dt = now + timedelta(hours=int(pf["ttl_hours"]))
            now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            actor = pf["actor"]

            payload: dict[str, Any] = {
                "schema": SCHEMA_GATE_AUTHORIZATION,
                "gate_id": gate_id,
                "authorization_id": pf["authorization_id"],
                "authorization_ref": pf["authorization_id"],
                "authorization_classes": ["DEVELOPMENT_MUTATION"],
                "mutation_authorized": True,
                "production_allowed": False,
                "production_touched": False,
                "revoked": False,
                "revoked_at_utc": None,
                "revoked_by": None,
                "revocation_reason": None,
                "granted_by": actor["email"],
                "granted_at_utc": now_str,
                "expires_at_utc": expires_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "target_branch": "Edarsahub_Desarrollo",
                "base_head_sha": pf["base_head_sha"],
                "objective": pf["objective"],
                "authorized_operations": pf["authorized_operations"],
                "source_sha256": pf["source_sha256"],
                "verification_tests": pf["verification_tests"],
                "rollback_plan": pf["rollback_plan"],
                "scope_digest": pf["scope_digest"],
                "authenticated_identity": {
                    "id": actor["id"],
                    "email": actor["email"],
                    "auth_source": actor["auth_source"],
                },
                "sql_usuario_id": actor["usuario_id"],
                "actor_roles": [actor["role_code"] or actor["role"]],
                "actor_permissions": actor["effective_permissions"],
                "effective_scopes": actor["effective_scopes"],
                "consent_evidence": pf["consent_verified"],
                "scope": {
                    "domains": [pf["domain"]],
                    "allowed_paths": pf["allowed_paths"],
                },
                "audit_trail": [
                    {
                        "event": "MATERIALIZED_AUTHORIZED",
                        "at_utc": now_str,
                        "actor_email": actor["email"],
                        "sql_usuario_id": actor["usuario_id"],
                        "scope_digest": pf["scope_digest"],
                    }
                ],
            }
            _atomic_write_json(path, payload)
            return {
                **payload,
                "status": "MATERIALIZED",
                "duplicate_prevented": False,
                "authorization_path": str(path),
                "production_touched": False,
            }
        finally:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)


def inspect_gate_authorization(
    gate_id_or_ref: str,
    *,
    domain: str | None = None,
    state_root: Path | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Read-only inspection of active, expired, or revoked materialized Gate authorization."""
    qroot = state_root or (Path(os.environ.get("EDARSAHUB_ROOT", "/app")) / ".git" / "universal-worker-queue")
    adir = _authorization_dir(qroot)
    token = str(gate_id_or_ref or "").strip()
    doc: dict[str, Any] | None = None
    doc_path: Path | None = None
    if adir.is_dir() and token:
        direct = adir / f"{_safe_id(token)}.json"
        if direct.is_file():
            cand = _read_json_safe(direct)
            if isinstance(cand, dict) and cand.get("schema") == SCHEMA_GATE_AUTHORIZATION:
                doc = cand
                doc_path = direct
        if doc is None:
            for p in sorted(adir.glob("*.json")):
                cand = _read_json_safe(p)
                if not isinstance(cand, dict) or cand.get("schema") != SCHEMA_GATE_AUTHORIZATION:
                    continue
                if token in {
                    str(cand.get("gate_id") or "").strip(),
                    str(cand.get("authorization_id") or "").strip(),
                    str(cand.get("authorization_ref") or "").strip(),
                }:
                    doc = cand
                    doc_path = p
                    break
    if doc is None:
        return {
            "found": False,
            "status": "NOT_FOUND",
            "active": False,
            "production_touched": False,
        }
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    exp_dt = _parse_iso_utc_dt(doc.get("expires_at_utc"))
    expired = exp_dt is None or exp_dt <= now
    revoked = doc.get("revoked") is True
    domains = list(((doc.get("scope") or {}).get("domains") or []))
    domain_matches = True if not domain else (str(domain).strip().upper() in {str(d).upper() for d in domains})
    active = (not revoked) and (not expired) and (doc.get("production_allowed") is False) and domain_matches
    status = "REVOKED" if revoked else ("EXPIRED" if expired else ("ACTIVE" if active else "DOMAIN_MISMATCH"))
    return {
        "found": True,
        "status": status,
        "active": active,
        "revoked": revoked,
        "expired": expired,
        "gate_id": doc.get("gate_id"),
        "authorization_id": doc.get("authorization_id"),
        "domains": domains,
        "allowed_paths": list(((doc.get("scope") or {}).get("allowed_paths") or [])),
        "authorized_operations": list(doc.get("authorized_operations") or []),
        "base_head_sha": doc.get("base_head_sha"),
        "granted_at_utc": doc.get("granted_at_utc"),
        "expires_at_utc": doc.get("expires_at_utc"),
        "revoked_at_utc": doc.get("revoked_at_utc"),
        "revoked_by": doc.get("revoked_by"),
        "revocation_reason": doc.get("revocation_reason"),
        "scope_digest": doc.get("scope_digest"),
        "authorization_path": str(doc_path) if doc_path else None,
        "production_allowed": False,
        "production_touched": False,
    }


def revoke_gate_authorization(
    gate_id_or_ref: str,
    *,
    domain: str,
    revocation_reason: str,
    current_user: Mapping[str, Any] | None,
    state_root: Path | None = None,
    identity_resolver: Any = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Concurrency-safe, auditable revocation of a materialized Gate authorization."""
    qroot = state_root or (Path(os.environ.get("EDARSAHUB_ROOT", "/app")) / ".git" / "universal-worker-queue")
    actor = _validate_authorized_actor_identity(current_user, identity_resolver=identity_resolver)
    clean_dom = str(domain or "").strip().upper()
    reason = str(revocation_reason or "").strip()
    if len(reason) < 3 or len(reason) > 300:
        raise GateAuthorizationError("AUTHORIZATION_REVOCATION_REASON_REQUIRED")

    adir = _authorization_dir(qroot)
    adir.mkdir(parents=True, exist_ok=True)
    lock_path = adir / ".authorizations.lock"
    with open(lock_path, "a+", encoding="utf-8") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        try:
            info = inspect_gate_authorization(gate_id_or_ref, state_root=qroot, now_utc=now_utc)
            if not info.get("found") or not info.get("authorization_path"):
                raise GateAuthorizationError("GATE_AUTHORIZATION_NOT_FOUND")
            path = Path(info["authorization_path"])
            doc = _read_json_safe(path)
            if not isinstance(doc, dict):
                raise GateAuthorizationError("GATE_AUTHORIZATION_NOT_FOUND")
            domains = {str(d).strip().upper() for d in ((doc.get("scope") or {}).get("domains") or ()) if str(d).strip()}
            if clean_dom not in domains:
                raise GateAuthorizationError("AUTHORIZATION_DOMAIN_MISMATCH")

            now = now_utc or datetime.now(timezone.utc)
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            already = doc.get("revoked") is True
            doc["revoked"] = True
            doc["revoked_at_utc"] = doc.get("revoked_at_utc") or now_str
            doc["revoked_by"] = doc.get("revoked_by") or actor["email"]
            doc["revocation_reason"] = doc.get("revocation_reason") or reason
            trail = doc.get("audit_trail") if isinstance(doc.get("audit_trail"), list) else []
            if not already:
                trail.append({
                    "event": "REVOKED",
                    "at_utc": now_str,
                    "actor_email": actor["email"],
                    "sql_usuario_id": actor["usuario_id"],
                    "reason": reason,
                })
                doc["audit_trail"] = trail[-50:]
                _atomic_write_json(path, doc)
            return {
                "status": "ALREADY_REVOKED" if already else "REVOKED",
                "revoked": True,
                "gate_id": doc.get("gate_id"),
                "authorization_id": doc.get("authorization_id"),
                "revoked_at_utc": doc.get("revoked_at_utc"),
                "revoked_by": doc.get("revoked_by"),
                "revocation_reason": doc.get("revocation_reason"),
                "production_touched": False,
            }
        finally:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)


def revalidate_gate_authorization_for_mutation(
    authorization_ref: str,
    *,
    domain: str,
    requested_paths: list[str] | tuple[str, ...] | set[str] = (),
    requested_operations: list[str] | tuple[str, ...] | set[str] = (),
    expected_base_head_sha: str | None = None,
    state_root: Path | None = None,
    repo_root: Path | None = None,
    verify_live_sha: bool = False,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Fail-closed revalidation executed before publish, before execute, and before integrate."""
    qroot = state_root or (Path(os.environ.get("EDARSAHUB_ROOT", "/app")) / ".git" / "universal-worker-queue")
    rroot = repo_root or Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    ref = str(authorization_ref or "").strip()
    dom = str(domain or "").strip().upper()
    if not ref:
        return {"authorized": False, "reason": "AUTHORIZATION_REF_REQUIRED", "production_touched": False}
    if not dom or dom == "*" or "PRODUCTION" in dom or "PRODUCCION" in dom:
        return {"authorized": False, "reason": "AUTHORIZATION_DOMAIN_INVALID", "production_touched": False}

    info = inspect_gate_authorization(ref, state_root=qroot, now_utc=now_utc)
    if not info.get("found") or not info.get("authorization_path"):
        return {"authorized": False, "reason": "GATE_AUTHORIZATION_NOT_FOUND", "production_touched": False}
    doc = _read_json_safe(Path(info["authorization_path"]))
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA_GATE_AUTHORIZATION:
        return {"authorized": False, "reason": "GATE_AUTHORIZATION_NOT_FOUND", "production_touched": False}
    if doc.get("production_allowed") is not False:
        return {"authorized": False, "reason": "PRODUCTION_FORBIDDEN", "production_touched": False}
    if doc.get("revoked") is True:
        return {"authorized": False, "reason": "AUTHORIZATION_REVOKED", "production_touched": False}

    ver = verify_gate_authorization(
        str(doc.get("gate_id") or ""),
        domain=dom,
        required_class="DEVELOPMENT_MUTATION",
        mutation_class="CODE_MUTATION",
        state_root=qroot,
        now_utc=now_utc,
    )
    if ver.get("authorized") is not True:
        return {
            "authorized": False,
            "reason": str(ver.get("reason") or "AUTHORIZATION_DENIED"),
            "gate_id": doc.get("gate_id"),
            "authorization_id": doc.get("authorization_id"),
            "production_touched": False,
        }

    allowed_paths = {
        str(p).strip().lstrip("./")
        for p in ((doc.get("scope") or {}).get("allowed_paths") or ())
        if str(p).strip()
    }
    req_paths = {str(p).strip().lstrip("./") for p in requested_paths if str(p).strip()}
    if allowed_paths and req_paths and not req_paths.issubset(allowed_paths):
        unauthorized = sorted(req_paths - allowed_paths)
        return {
            "authorized": False,
            "reason": f"AUTHORIZATION_PATH_NOT_ALLOWED:{unauthorized[0]}",
            "gate_id": doc.get("gate_id"),
            "authorization_id": doc.get("authorization_id"),
            "production_touched": False,
        }

    allowed_ops = {str(op).strip() for op in (doc.get("authorized_operations") or ()) if str(op).strip()}
    req_ops = {str(op).strip() for op in requested_operations if str(op).strip()}
    if allowed_ops and req_ops and not req_ops.issubset(allowed_ops):
        bad_ops = sorted(req_ops - allowed_ops)
        return {
            "authorized": False,
            "reason": f"AUTHORIZATION_OPERATION_NOT_ALLOWED:{bad_ops[0]}",
            "gate_id": doc.get("gate_id"),
            "authorization_id": doc.get("authorization_id"),
            "production_touched": False,
        }

    auth_head = str(doc.get("base_head_sha") or "").strip().lower()
    if expected_base_head_sha and auth_head and str(expected_base_head_sha).strip().lower() != auth_head:
        return {
            "authorized": False,
            "reason": "AUTHORIZATION_BASE_HEAD_MISMATCH",
            "gate_id": doc.get("gate_id"),
            "authorization_id": doc.get("authorization_id"),
            "production_touched": False,
        }

    if verify_live_sha:
        bound_shas = doc.get("source_sha256")
        if isinstance(bound_shas, Mapping):
            for rel, expected_sha in bound_shas.items():
                if req_paths and rel not in req_paths:
                    continue
                target = rroot / rel
                if not target.is_file():
                    return {
                        "authorized": False,
                        "reason": f"AUTHORIZATION_SOURCE_FILE_MISSING:{rel}",
                        "gate_id": doc.get("gate_id"),
                        "authorization_id": doc.get("authorization_id"),
                        "production_touched": False,
                    }
                actual_sha = hashlib.sha256(target.read_bytes()).hexdigest()
                if actual_sha != str(expected_sha).strip().lower():
                    return {
                        "authorized": False,
                        "reason": f"AUTHORIZATION_SOURCE_SHA256_STALE:{rel}",
                        "gate_id": doc.get("gate_id"),
                        "authorization_id": doc.get("authorization_id"),
                        "production_touched": False,
                    }

    return {
        "authorized": True,
        "reason": "AUTHORIZED",
        "gate_id": doc.get("gate_id"),
        "authorization_id": doc.get("authorization_id"),
        "expires_at_utc": doc.get("expires_at_utc"),
        "production_touched": False,
    }


def _extract_job_requested_paths(payload: Mapping[str, Any]) -> list[str]:
    paths: set[str] = set()
    for action in payload.get("actions") or ():
        if isinstance(action, Mapping):
            p = str(action.get("path") or "").strip()
            if p:
                paths.add(p)
    return sorted(paths)


def _git_diff_names_between(repo_root: Path, base_sha: str, target_ref: str = "HEAD") -> set[str] | None:
    if not base_sha or len(base_sha) != 40:
        return None
    anc = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", base_sha, target_ref],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if anc.returncode != 0:
        return None
    diff = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--name-only", f"{base_sha}..{target_ref}"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if diff.returncode != 0:
        return None
    return {ln.strip() for ln in (diff.stdout or "").splitlines() if ln.strip()}


def scan_resumable_concurrency_blocked_objectives(
    *,
    repo_root: Path | None = None,
    state_root: Path | None = None,
    max_age_seconds: int = 86400 * 7,
    now_epoch: float | None = None,
) -> list[dict[str, Any]]:
    """Find recent terminal results blocked strictly by multiagent concurrency/dirty worktree."""
    root = repo_root or Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    qroot = state_root or (root / ".git" / "universal-worker-queue")
    now_ts = float(now_epoch if now_epoch is not None else time.time())
    results_dir = qroot / "results"
    drafts_dir = qroot / "drafts"
    if not results_dir.is_dir():
        return []

    # Collect existing resumed_from_job_id links and active pending/processing stems
    active_ids = (
        {p.stem for p in (qroot / "pending").glob("*.json")}
        | {p.stem for p in (qroot / "processing").glob("*.json")}
    )
    resumed_parents: set[str] = set()
    for p in list(drafts_dir.glob("*.json")) + list(results_dir.glob("*.json")):
        if "-RESUME-" in p.stem:
            parent = p.stem.split("-RESUME-", 1)[0]
            resumed_parents.add(parent)

    candidates: list[dict[str, Any]] = []
    for rp in sorted(results_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            age = now_ts - rp.stat().st_mtime
        except OSError:
            continue
        if age > max_age_seconds:
            continue
        res = _read_json_safe(rp)
        if not isinstance(res, dict):
            continue
        status = str(res.get("status") or "").strip().upper()
        if status not in CONCURRENCY_BLOCKED_STATUSES:
            continue
        if str(res.get("certification") or "").strip().upper().startswith("CERTIFIED"):
            continue
        if res.get("production_touched") is not False:
            continue
        jid = str(res.get("job_id") or rp.stem).strip()
        if not jid or "-RESUME-" in jid:
            continue
        draft_path = drafts_dir / f"{jid}.json"
        if not draft_path.is_file():
            continue
        if jid in active_ids or any(a.startswith(f"{jid}-RESUME-") for a in active_ids):
            continue
        candidates.append({
            "job_id": jid,
            "blocked_status": status,
            "completed_at_utc": res.get("completed_at_utc"),
            "base_sha": res.get("execution_base_sha") or res.get("base_sha") or res.get("local_at_start") or res.get("remote_at_start") or "",
            "already_has_resume": jid in resumed_parents,
            "draft_path": str(draft_path),
            "production_touched": False,
        })
    return candidates


def resume_authorized_concurrency_blocked_objective(
    source_job_id: str,
    *,
    repo_root: Path | None = None,
    state_root: Path | None = None,
    circuit_state_dir: Path | None = None,
    authorization_context: Mapping[str, Any] | None = None,
    authorized_resume_job_ids: set[str] | None = None,
    git_state_override: Mapping[str, Any] | None = None,
    submit_fn: Any = None,
    now_epoch: float | None = None,
) -> dict[str, Any]:
    """Fail-closed idempotent resumption of an explicitly authorized concurrency-blocked job."""
    root = repo_root or Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    qroot = state_root or (root / ".git" / "universal-worker-queue")
    now_ts = float(now_epoch if now_epoch is not None else time.time())
    cb_dir = circuit_state_dir or (qroot / "maintenance" / "circuit_breakers")

    result_path = qroot / "results" / f"{source_job_id}.json"
    draft_path = qroot / "drafts" / f"{source_job_id}.json"
    source_result = _read_json_safe(result_path)
    payload = _read_json_safe(draft_path)
    if not isinstance(source_result, dict) or not isinstance(payload, dict):
        return {"resumed": False, "action": "ESCALATE_MISSING_ARTIFACT", "reason": "SOURCE_RESULT_OR_DRAFT_MISSING", "source_job_id": source_job_id, "production_touched": False}

    blocked_status = str(source_result.get("status") or "").strip().upper()
    if blocked_status not in CONCURRENCY_BLOCKED_STATUSES:
        return {"resumed": False, "action": "SKIP_NOT_CONCURRENCY_BLOCKED", "reason": f"STATUS_NOT_RESUMABLE:{blocked_status}", "source_job_id": source_job_id, "production_touched": False}
    if payload.get("production_allowed") is not False:
        return {"resumed": False, "action": "ESCALATE_POLICY", "reason": "PRODUCTION_FORBIDDEN", "source_job_id": source_job_id, "production_touched": False}

    # Explicit revocation check always fails closed
    if isinstance(authorization_context, Mapping) and authorization_context.get("revoked") is True:
        return {"resumed": False, "action": "ESCALATE_POLICY", "reason": "AUTHORIZATION_REVOKED", "source_job_id": source_job_id, "production_touched": False}

    # Contract & requester validation
    validation_errors = job_bridge.validate(payload)
    if validation_errors:
        return {"resumed": False, "action": "ESCALATE_CONTRACT", "reason": "INVALID_DRAFT_CONTRACT:" + ",".join(validation_errors[:5]), "source_job_id": source_job_id, "production_touched": False}
    requester = payload.get("requester")
    req_email = str(requester.get("email") or "").strip().lower() if isinstance(requester, Mapping) else ""
    if not req_email or "@" not in req_email:
        return {"resumed": False, "action": "ESCALATE_RBAC", "reason": "REQUESTER_IDENTITY_MISSING", "source_job_id": source_job_id, "production_touched": False}

    mode = str(payload.get("mode") or "MUTATION").strip().upper()
    req_paths = _extract_job_requested_paths(payload)

    # Non-READ_ONLY mutations require explicit traceable authorization (inline, active materialized Gate, or explicit authorized_resume_job_ids)
    effective_auth = authorization_context
    if mode != "READ_ONLY":
        explicit_id_ok = bool(authorized_resume_job_ids and source_job_id in authorized_resume_job_ids)
        dom = str((payload.get("scheduling") or {}).get("bounded_context") or "WORKER_CONTROL_PLANE").strip().upper()
        if effective_auth is None:
            effective_auth = resolve_active_domain_authorization(
                dom,
                state_root=qroot,
                required_class="DEVELOPMENT_MUTATION",
                requested_paths=req_paths,
            )
        auth_ok = False
        auth_reason = "EXPLICIT_MUTATION_AUTHORIZATION_REQUIRED"
        if isinstance(effective_auth, Mapping) and effective_auth:
            gate_spec = {
                "gate_id": f"RESUME-{source_job_id[:36]}",
                "mutation_class": "CODE_MUTATION",
                "authorization_class": "DEVELOPMENT_MUTATION",
                "require_traceable_authorization": True,
                "production_allowed": False,
                "required_scope": {"domain": [dom]},
            }
            auth_ok, auth_reason = policy_ctrl.evaluate_gate_authorization(
                gate_spec,
                authorization_classes=effective_auth.get("authorization_classes") or (),
                authorization_context=effective_auth,
            )
            if auth_ok:
                allowed_paths = {
                    str(p).strip().lstrip("./")
                    for p in ((effective_auth.get("scope") or {}).get("allowed_paths") or ())
                    if str(p).strip()
                }
                if req_paths and allowed_paths:
                    norm_req = {str(p).strip().lstrip("./") for p in req_paths if str(p).strip()}
                    if not norm_req.issubset(allowed_paths):
                        auth_ok = False
                        auth_reason = "SCOPE_PATHS_OUTSIDE_GATE_AUTHORIZATION"
        if not auth_ok and not explicit_id_ok:
            return {"resumed": False, "action": "ESCALATE_POLICY", "reason": str(auth_reason), "source_job_id": source_job_id, "production_touched": False}

    # Check if already certified or already resumed up to max attempts
    existing_resumes = sorted(
        {
            p.stem
            for sub in ("drafts", "pending", "processing", "results", "published")
            for p in (qroot / sub).glob(f"{source_job_id}-RESUME-*.json")
        }
    )
    for r_id in existing_resumes:
        rp = qroot / "results" / f"{r_id}.json"
        if rp.is_file():
            rr = _read_json_safe(rp) or {}
            if str(rr.get("status") or "").upper() in {"INTEGRATED", "READ_ONLY_COMPLETE", "OPERATIONAL_COMPLETE"}:
                return {"resumed": False, "action": "ALREADY_SUPERSEDED_OR_RESUMED", "reason": f"EXISTING_SUCCESSOR:{r_id}", "source_job_id": source_job_id, "production_touched": False}
        if (qroot / "pending" / f"{r_id}.json").is_file() or (qroot / "processing" / f"{r_id}.json").is_file():
            return {"resumed": False, "action": "SKIP_RESUME_IN_FLIGHT", "reason": f"RESUME_IN_FLIGHT:{r_id}", "source_job_id": source_job_id, "production_touched": False}

    next_attempt = len(existing_resumes) + 1
    if next_attempt > MAX_CONCURRENCY_RESUMES_PER_JOB:
        return {"resumed": False, "action": "ESCALATE_MAX_RESUMES_EXCEEDED", "reason": f"MAX_CONCURRENCY_RESUMES_EXCEEDED:{MAX_CONCURRENCY_RESUMES_PER_JOB}", "source_job_id": source_job_id, "production_touched": False}

    # Circuit breaker + exponential backoff check
    cb_key = f"concurrency_resume:{source_job_id[:72]}"
    cb_prior = _read_json_safe(auto_loop._circuit_path(cb_key, state_dir=cb_dir)) or {}
    consec_fail = int(cb_prior.get("consecutive_failures") or 0)
    backoff_s = compute_exponential_backoff(consec_fail)
    circuit = auto_loop.evaluate_circuit_breaker(
        cb_key,
        max_failures=MAX_CONCURRENCY_RESUMES_PER_JOB,
        cooldown_seconds=max(120, backoff_s),
        now_epoch=now_ts,
        state_dir=cb_dir,
    )
    if not circuit.get("allow_attempt"):
        return {"resumed": False, "action": "CIRCUIT_OPEN", "reason": str(circuit.get("reason") or "CIRCUIT_OPEN"), "source_job_id": source_job_id, "production_touched": False}

    # Check live git concurrency state (either clean or isolated disjoint from local dirty)
    try:
        from tools.mirror_sync import git_divergence_guard as gdg
    except ModuleNotFoundError:
        import git_divergence_guard as gdg
    git_state = dict(git_state_override) if isinstance(git_state_override, Mapping) else gdg.inspect_repository(root, fetch=False)
    policy = gdg.mutation_policy(git_state, requested_paths=req_paths, isolated_worktree=(mode != "READ_ONLY"))
    if mode != "READ_ONLY" and not policy.get("allowed"):
        return {
            "resumed": False,
            "action": "DEFER_CONCURRENCY_STILL_ACTIVE",
            "reason": str(policy.get("reason") or "GIT_WORKTREE_NOT_CLEAN"),
            "scope_conflicts": policy.get("scope_conflicts") or [],
            "source_job_id": source_job_id,
            "production_touched": False,
        }

    # Scope drift check: if target files changed between original base_sha and current HEAD, fail closed!
    orig_base = str(payload.get("base_sha") or source_result.get("execution_base_sha") or source_result.get("local_at_start") or source_result.get("remote_at_start") or "").strip()
    current_head = str(git_state.get("remote_head") or git_state.get("local_head") or "").strip()
    if mode != "READ_ONLY" and orig_base and current_head and orig_base != current_head and req_paths:
        changed_since_base = _git_diff_names_between(root, orig_base, current_head)
        if changed_since_base is None:
            return {"resumed": False, "action": "ESCALATE_SCOPE_DRIFT", "reason": "RESUME_BLOCKED_BASE_NOT_ANCESTOR", "source_job_id": source_job_id, "production_touched": False}
        drift = sorted(changed_since_base & set(req_paths))
        if drift:
            return {
                "resumed": False,
                "action": "ESCALATE_SCOPE_DRIFT",
                "reason": "RESUME_BLOCKED_SCOPE_DRIFT",
                "drifted_paths": drift,
                "source_job_id": source_job_id,
                "production_touched": False,
            }

    resume_job_id = f"{source_job_id}-RESUME-{next_attempt}"
    resumed_payload = dict(payload)
    resumed_payload["job_id"] = resume_job_id
    if current_head and len(current_head) == 40:
        resumed_payload["base_sha"] = current_head
    resumed_payload["production_allowed"] = False
    meta = dict(resumed_payload.get("metadata") or {}) if isinstance(resumed_payload.get("metadata"), Mapping) else {}
    meta["resumed_from_job_id"] = source_job_id
    meta["resume_reason"] = blocked_status
    meta["resume_attempt"] = next_attempt
    resumed_payload["metadata"] = meta

    publisher = submit_fn or gcp.submit
    try:
        pub_out = publisher(resumed_payload, require_convergence=False)
    except Exception as exc:
        auto_loop.record_circuit_outcome(cb_key, certified_success=False, failure_class=f"RESUME_SUBMIT_EXC:{type(exc).__name__}", now_epoch=now_ts, state_dir=cb_dir)
        return {"resumed": False, "action": "RESUME_FAILED_RECORDED", "reason": f"SUBMIT_EXCEPTION:{type(exc).__name__}", "source_job_id": source_job_id, "resume_job_id": resume_job_id, "production_touched": False}

    pub_status = str((pub_out or {}).get("status") or "").strip().upper()
    if pub_status in {"SUBMITTED", "ALREADY_SUBMITTED", "PUBLISHED"}:
        auto_loop.record_circuit_outcome(cb_key, certified_success=True, now_epoch=now_ts, state_dir=cb_dir)
        return {
            "schema": SCHEMA_CONCURRENCY_RESUME,
            "resumed": True,
            "action": "RESUMED_VIA_CANONICAL_PUBLISHER",
            "source_job_id": source_job_id,
            "resume_job_id": resume_job_id,
            "publication_status": pub_status,
            "independent_certification_pending": True,
            "production_touched": False,
        }
    auto_loop.record_circuit_outcome(cb_key, certified_success=False, failure_class=f"RESUME_STATUS:{pub_status or 'UNKNOWN'}", now_epoch=now_ts, state_dir=cb_dir)
    return {
        "schema": SCHEMA_CONCURRENCY_RESUME,
        "resumed": False,
        "action": "RESUME_REJECTED",
        "source_job_id": source_job_id,
        "resume_job_id": resume_job_id,
        "publication_status": pub_status,
        "production_touched": False,
    }


def record_agent_session_interruption_incident(
    *,
    incident_id: str,
    interrupted_session_id: str,
    base_head_sha: str,
    checkpoint_ref: str,
    prepared_paths: list[str] | tuple[str, ...] = (),
    authorization_id: str | None = None,
    interrupted_command_class: str = "SESSION_INTERRUPTED",
    remediation_channel: str = "gate_chain_publisher.submit",
    status: str = "RECORDED",
    state_root: Path | None = None,
) -> dict[str, Any]:
    """Record a transversal, secret-free agent session interruption incident in canonical maintenance storage."""
    root = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    qroot = state_root or (root / ".git" / "universal-worker-queue")
    log_path = qroot / "maintenance" / SESSION_INTERRUPTION_INCIDENTS_FILENAME
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "schema": SCHEMA_SESSION_INTERRUPTION,
        "incident_id": str(incident_id or "").strip(),
        "incident_class": "AGENT_SESSION_INTERRUPTION",
        "scope": "TRANSVERSAL",
        "interrupted_session_id": str(interrupted_session_id or "").strip(),
        "recorded_at_utc": utc_now(),
        "base_head_sha": str(base_head_sha or "").strip(),
        "checkpoint_ref": str(checkpoint_ref or "").strip(),
        "prepared_paths": sorted({str(p).strip().lstrip("./") for p in prepared_paths if str(p).strip()}),
        "authorization_id": str(authorization_id or "").strip() or None,
        "interrupted_command_class": str(interrupted_command_class or "SESSION_INTERRUPTED").strip(),
        "remediation_channel": str(remediation_channel or "gate_chain_publisher.submit").strip(),
        "non_destructive_preservation": True,
        "status": str(status or "RECORDED").strip().upper(),
        "production_touched": False,
    }
    if not record["incident_id"]:
        raise ValueError("SESSION_INTERRUPTION_INCIDENT_ID_REQUIRED")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


def list_agent_session_interruption_incidents(
    *,
    state_root: Path | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Return most recent transversal agent session interruption incidents (deduplicated by incident_id)."""
    root = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    qroot = state_root or (root / ".git" / "universal-worker-queue")
    log_path = qroot / "maintenance" / SESSION_INTERRUPTION_INCIDENTS_FILENAME
    if not log_path.is_file():
        return []
    by_id: dict[str, dict[str, Any]] = {}
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        iid = str(item.get("incident_id") or "").strip()
        if iid:
            by_id[iid] = item
    ordered = sorted(
        by_id.values(),
        key=lambda x: str(x.get("recorded_at_utc") or ""),
        reverse=True,
    )
    return ordered[: max(1, int(limit))]


def evaluate_interrupted_objective_recovery(
    *,
    domain: str,
    checkpoint_path: Path,
    prepared_paths: list[str] | tuple[str, ...] = (),
    base_sha: str | None = None,
    production_allowed: bool = False,
    repo_root: Path | None = None,
    state_root: Path | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate fail-closed automatic recovery eligibility of an interrupted objective from persistent checkpoint + materialized authorization."""
    root = repo_root or Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    qroot = state_root or (root / ".git" / "universal-worker-queue")
    norm_domain = str(domain or "").strip().upper()
    norm_paths = sorted({str(p).strip().lstrip("./") for p in prepared_paths if str(p).strip()})

    if production_allowed is not False:
        return {
            "schema": SCHEMA_INTERRUPTED_RECOVERY_EVAL,
            "recoverable": False,
            "action": "BLOCK_PRODUCTION_FORBIDDEN",
            "reason": "PRODUCTION_FORBIDDEN",
            "remediation_channel": "NONE",
            "production_touched": False,
        }
    if not checkpoint_path.is_file():
        return {
            "schema": SCHEMA_INTERRUPTED_RECOVERY_EVAL,
            "recoverable": False,
            "action": "ESCALATE_CHECKPOINT_MISSING",
            "reason": "PERSISTENT_CHECKPOINT_MISSING",
            "remediation_channel": "HUMAN_AUDIT",
            "production_touched": False,
        }

    auth = resolve_active_domain_authorization(
        norm_domain,
        state_root=qroot,
        required_class="DEVELOPMENT_MUTATION",
        requested_paths=norm_paths or None,
        now_utc=now_utc,
    )
    if not auth:
        return {
            "schema": SCHEMA_INTERRUPTED_RECOVERY_EVAL,
            "recoverable": False,
            "action": "ESCALATE_AUTHORIZATION_REQUIRED",
            "reason": "ACTIVE_GATE_AUTHORIZATION_REQUIRED",
            "domain": norm_domain,
            "prepared_paths": norm_paths,
            "remediation_channel": "HUMAN_GO_REQUIRED",
            "production_touched": False,
        }

    # Check base drift on prepared paths when base_sha is provided
    drifted_paths: list[str] = []
    if base_sha and norm_paths:
        changed = _git_diff_names_between(root, base_sha, "HEAD")
        if changed is None:
            return {
                "schema": SCHEMA_INTERRUPTED_RECOVERY_EVAL,
                "recoverable": False,
                "action": "ESCALATE_BASE_UNVERIFIABLE",
                "reason": "CHECKPOINT_BASE_NOT_ANCESTOR",
                "domain": norm_domain,
                "remediation_channel": "HUMAN_AUDIT",
                "production_touched": False,
            }
        drifted_paths = sorted(changed & set(norm_paths))
        if drifted_paths:
            return {
                "schema": SCHEMA_INTERRUPTED_RECOVERY_EVAL,
                "recoverable": False,
                "action": "ESCALATE_SCOPE_DRIFT",
                "reason": "PREPARED_PATHS_DRIFTED_SINCE_INTERRUPTION",
                "domain": norm_domain,
                "drifted_paths": drifted_paths,
                "remediation_channel": "REBASE_ON_CANONICAL_HEAD",
                "production_touched": False,
            }

    return {
        "schema": SCHEMA_INTERRUPTED_RECOVERY_EVAL,
        "recoverable": True,
        "action": "RECOVER_VIA_CANONICAL_PUBLISHER",
        "reason": "CHECKPOINT_AND_AUTHORIZATION_VERIFIED",
        "domain": norm_domain,
        "authorization_id": auth.get("authorization_id"),
        "gate_id": auth.get("gate_id"),
        "prepared_paths": norm_paths,
        "remediation_channel": "gate_chain_publisher.submit",
        "direct_push_allowed": False,
        "destructive_git_allowed": False,
        "production_touched": False,
    }
