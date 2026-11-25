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

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
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

MCP_INCIDENTS_FILENAME = "mcp_connector_incidents.jsonl"
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

    # Pending audit evidence certifications
    pending_audit_stale: list[dict[str, Any]] = []
    if published_dir.is_dir():
        for path in sorted(published_dir.glob("*.json")):
            try:
                txt = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "certification=PENDING_AUDIT_EVIDENCE" not in txt:
                continue
            age_s = max(0.0, now_ts - path.stat().st_mtime)
            if age_s < pending_audit_grace_seconds:
                continue
            jid = path.stem
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
        "persistent_drafts_by_domain": dict(sorted(by_domain.items())),
        "persistent_drafts": persistent_drafts[:100],
        "transient_drafts": transient_drafts[:50],
        "corrupt_drafts": corrupt_drafts[:50],
        "stale_processing": stale_processing[:50],
        "orphan_branches": orphan_branches[:50],
        "pending_audit_stale_count": len(pending_audit_stale),
        "pending_audit_with_attestation_count": sum(1 for x in pending_audit_stale if x["has_attestation"]),
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

    return {
        "schema": SCHEMA_RECOVERY,
        "at_utc": utc_now(),
        "status": "ACTIVE",
        "domain_isolation_active": True,
        "isolated_failed_domains": sorted(isolated_failed_domains),
        "max_recoveries_per_cycle": budget,
        "recoveries_attempted": attempted,
        "recoveries_succeeded": succeeded,
        "actions": actions_log,
        "production_touched": False,
    }
