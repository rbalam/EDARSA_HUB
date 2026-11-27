#!/usr/bin/env python3
"""Independent Agent Guard supervision, compact telemetry, deduplication, hysteresis, and size caching.

Reused directly by the supervised Worker Control Plane (tools/mirror_sync/worker_control_plane.py)
and exposed READ_ONLY via Worker Console (/api/worker/console/self-healing) and Centro de Control
(/api/centro-control/worker-salud) without creating any parallel daemon or service.

Invariants:
- Strictly READ_ONLY over Git, worktrees, hooks, and credentials (writes only its compact
  runtime telemetry/cache state file under .git/universal-worker-queue/runtime/).
- Does NOT depend on VS Code / code-server; VS Code task watch remains purely optional.
- Preserves all existing Agent Guard hooks (pre-commit, pre-push) and policies.
- Never touches Production (production_touched=False).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_AGENT_GUARD_TELEMETRY = "edarsahub.agent-guard-telemetry.v1"
TELEMETRY_STATE_FILENAME = "agent_guard_telemetry_state.json"

STORAGE_WARN_PERCENT = 80.0
STORAGE_BLOCK_PERCENT = 90.0
STORAGE_HYSTERESIS_CLEAR_DELTA = 2.0
WORKTREE_WARN_BYTES = 128 * 1024 * 1024
DEFAULT_SUPERVISION_INTERVAL_SECONDS = max(
    15.0,
    min(float(os.environ.get("EDARSAHUB_AGENT_GUARD_SUPERVISION_INTERVAL_SECONDS", "60.0")), 600.0),
)
DEFAULT_SIZE_CACHE_TTL_SECONDS = max(
    15.0,
    min(float(os.environ.get("EDARSAHUB_AGENT_GUARD_SIZE_CACHE_TTL_SECONDS", "60.0")), 600.0),
)
STALE_CLAIM_SECONDS = 15 * 60


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = handle.name
    os.replace(tmp, path)


def _read_json_safe(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _disk_storage_snapshot(root: Path) -> dict[str, Any]:
    try:
        st = os.statvfs(root)
        total = int(st.f_blocks * st.f_frsize)
        avail = int(st.f_bavail * st.f_frsize)
        used = max(0, total - avail)
        pct = round((used / total) * 100.0, 2) if total > 0 else 0.0
        return {
            "path": str(root),
            "used_percent": pct,
            "bucket_percent": int(pct),
            "total_gib": round(total / (1024 ** 3), 2),
            "used_gib": round(used / (1024 ** 3), 2),
            "available_gib": round(avail / (1024 ** 3), 2),
            "warn_threshold_percent": STORAGE_WARN_PERCENT,
            "block_threshold_percent": STORAGE_BLOCK_PERCENT,
            "hysteresis_clear_delta_percent": STORAGE_HYSTERESIS_CLEAR_DELTA,
        }
    except OSError:
        return {
            "path": str(root),
            "used_percent": 0.0,
            "bucket_percent": 0,
            "total_gib": 0.0,
            "used_gib": 0.0,
            "available_gib": 0.0,
            "warn_threshold_percent": STORAGE_WARN_PERCENT,
            "block_threshold_percent": STORAGE_BLOCK_PERCENT,
            "hysteresis_clear_delta_percent": STORAGE_HYSTERESIS_CLEAR_DELTA,
        }


def _evaluate_storage_status_with_hysteresis(
    used_percent: float,
    previous_status: str | None,
) -> str:
    """Apply hysteresis so oscillations like 79.9% <-> 80.1% never cause alert flapping."""
    prev = str(previous_status or "OK").strip().upper()
    if used_percent >= STORAGE_BLOCK_PERCENT:
        return "BLOCK"
    if prev == "BLOCK":
        if used_percent >= (STORAGE_BLOCK_PERCENT - STORAGE_HYSTERESIS_CLEAR_DELTA):
            return "BLOCK"
        return "WARNING" if used_percent >= (STORAGE_WARN_PERCENT - STORAGE_HYSTERESIS_CLEAR_DELTA) else "OK"
    if used_percent >= STORAGE_WARN_PERCENT:
        return "WARNING"
    if prev == "WARNING" and used_percent >= (STORAGE_WARN_PERCENT - STORAGE_HYSTERESIS_CLEAR_DELTA):
        return "WARNING"
    return "OK"


def _inspect_hooks(root: Path) -> dict[str, Any]:
    guard_home = root / ".git" / "agent-guard"
    guard_script = guard_home / "bin" / "agent_guard.py"
    pre_commit = guard_home / "hooks" / "pre-commit"
    pre_push = guard_home / "hooks" / "pre-push"
    hooks_path = ""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "config", "--get", "core.hooksPath"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if proc.returncode == 0:
            hooks_path = proc.stdout.strip()
    except Exception:
        hooks_path = ""

    return {
        "guard_script_present": guard_script.is_file(),
        "pre_commit_executable": pre_commit.is_file() and os.access(pre_commit, os.X_OK),
        "pre_push_executable": pre_push.is_file() and os.access(pre_push, os.X_OK),
        "core_hooks_path": hooks_path or None,
        "core_hooks_path_aligned": hooks_path.endswith("/.git/agent-guard/hooks"),
    }


def _inspect_claims_and_registrations(root: Path, *, now_epoch: float) -> dict[str, Any]:
    state_dir = root / ".git" / "agent-guard" / "state"
    claims_dir = state_dir / "claims"
    wt_dir = state_dir / "worktrees"

    total_claims = 0
    active_claims = 0
    released_claims = 0
    stale_active_claims = 0
    active_ids: list[str] = []

    if claims_dir.is_dir():
        for path in claims_dir.glob("*.json"):
            total_claims += 1
            doc = _read_json_safe(path)
            if not isinstance(doc, dict):
                continue
            status = str(doc.get("status") or "").strip().upper()
            if status == "ACTIVE":
                active_claims += 1
                aid = str(doc.get("agent_id") or path.stem)
                active_ids.append(aid)
                hb_raw = str(doc.get("heartbeat") or doc.get("created_at") or "").strip()
                try:
                    hb_ts = datetime.fromisoformat(hb_raw.replace("Z", "+00:00")).timestamp() if hb_raw else 0.0
                except ValueError:
                    hb_ts = 0.0
                if hb_ts and (now_epoch - hb_ts) > STALE_CLAIM_SECONDS:
                    stale_active_claims += 1
            elif status == "RELEASED":
                released_claims += 1

    wt_reg_total = 0
    wt_reg_existing = 0
    wt_reg_orphaned = 0
    if wt_dir.is_dir():
        for path in wt_dir.glob("*.json"):
            wt_reg_total += 1
            doc = _read_json_safe(path)
            wt_path = str((doc or {}).get("worktree") or "").strip()
            if wt_path and Path(wt_path).exists():
                wt_reg_existing += 1
            else:
                wt_reg_orphaned += 1

    return {
        "total_claim_files": total_claims,
        "active_count": active_claims,
        "released_count": released_claims,
        "stale_active_count": stale_active_claims,
        "active_agent_ids": sorted(active_ids)[:20],
        "worktree_registrations_total": wt_reg_total,
        "worktree_registrations_existing": wt_reg_existing,
        "worktree_registrations_orphaned": wt_reg_orphaned,
    }


def _scan_worktree_apparent_bytes(worktree: Path) -> int:
    total = 0
    try:
        for item in worktree.rglob("*"):
            try:
                if item.is_file() and not item.is_symlink():
                    total += item.stat().st_size
            except OSError:
                continue
    except OSError:
        return total
    return total


def _inspect_worktrees_with_cache(
    root: Path,
    *,
    previous_size_cache: Mapping[str, Any],
    now_epoch: float,
    size_cache_ttl_seconds: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    wt_root = root / ".agent-worktrees"
    items: list[dict[str, Any]] = []
    new_cache: dict[str, Any] = {}
    dirty_count = 0
    oversized_count = 0
    cache_hits = 0
    cache_misses = 0

    if wt_root.is_dir():
        for wt in sorted(wt_root.iterdir()):
            if not wt.is_dir():
                continue
            status_out = ""
            branch = ""
            head_sha = ""
            try:
                status_out = subprocess.run(
                    ["git", "-C", str(wt), "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                ).stdout
                branch = subprocess.run(
                    ["git", "-C", str(wt), "branch", "--show-current"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=5,
                ).stdout.strip()
                head_sha = subprocess.run(
                    ["git", "-C", str(wt), "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=5,
                ).stdout.strip()
            except Exception:
                pass

            dirty = bool(status_out.strip())
            status_digest = hashlib.sha256(status_out.encode("utf-8")).hexdigest()[:16]
            try:
                dir_mtime_ns = wt.stat().st_mtime_ns
            except OSError:
                dir_mtime_ns = 0

            key = str(wt.resolve())
            cached_entry = previous_size_cache.get(key) if isinstance(previous_size_cache, Mapping) else None
            use_cache = (
                isinstance(cached_entry, Mapping)
                and cached_entry.get("dir_mtime_ns") == dir_mtime_ns
                and cached_entry.get("status_digest") == status_digest
                and isinstance(cached_entry.get("apparent_bytes"), int)
                and isinstance(cached_entry.get("cached_at_epoch"), (int, float))
                and (now_epoch - float(cached_entry["cached_at_epoch"])) < size_cache_ttl_seconds
            )
            if use_cache:
                apparent_bytes = int(cached_entry["apparent_bytes"])
                cached_at = float(cached_entry["cached_at_epoch"])
                cache_hits += 1
            else:
                apparent_bytes = _scan_worktree_apparent_bytes(wt)
                cached_at = now_epoch
                cache_misses += 1

            new_cache[key] = {
                "dir_mtime_ns": dir_mtime_ns,
                "status_digest": status_digest,
                "apparent_bytes": apparent_bytes,
                "cached_at_epoch": cached_at,
            }

            oversized = apparent_bytes >= WORKTREE_WARN_BYTES
            if dirty:
                dirty_count += 1
            if oversized:
                oversized_count += 1

            items.append({
                "name": wt.name,
                "path": str(wt),
                "branch": branch or None,
                "head_sha": head_sha or None,
                "dirty": dirty,
                "apparent_bytes": apparent_bytes,
                "apparent_mib": round(apparent_bytes / 1048576.0, 1),
                "oversized": oversized,
                "size_cached": use_cache,
            })

    summary = {
        "total_extra_worktrees": len(items),
        "dirty_count": dirty_count,
        "oversized_count": oversized_count,
        "size_cache_hits": cache_hits,
        "size_cache_misses": cache_misses,
        "items": items,
    }
    return summary, new_cache


def _build_raw_alerts(
    *,
    storage: Mapping[str, Any],
    storage_status: str,
    hooks: Mapping[str, Any],
    claims: Mapping[str, Any],
    worktrees: Mapping[str, Any],
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    if storage_status == "BLOCK":
        alerts.append({
            "alert_key": "AGENT_STORAGE_POLICY_V1:storage:block",
            "code": "AGENT_STORAGE_POLICY_V1",
            "severity": "error",
            "resource": str(storage.get("path") or "/app"),
            "bucket": storage.get("bucket_percent"),
            "message": f"/app al {storage.get('used_percent')}% (>= {STORAGE_BLOCK_PERCENT}% bloqueo)",
        })
    elif storage_status == "WARNING":
        alerts.append({
            "alert_key": "AGENT_STORAGE_POLICY_V1:storage:warning",
            "code": "AGENT_STORAGE_POLICY_V1",
            "severity": "warning",
            "resource": str(storage.get("path") or "/app"),
            "bucket": storage.get("bucket_percent"),
            "message": f"/app al {storage.get('used_percent')}% (>= {STORAGE_WARN_PERCENT}% warning)",
        })

    if not hooks.get("guard_script_present") or not hooks.get("pre_commit_executable") or not hooks.get("pre_push_executable"):
        alerts.append({
            "alert_key": "AGENT_GUARD_HOOKS_DEGRADED:hooks:error",
            "code": "AGENT_GUARD_HOOKS_DEGRADED",
            "severity": "error",
            "resource": ".git/agent-guard/hooks",
            "bucket": None,
            "message": "Hooks o binario de Agent Guard ausentes o sin permisos de ejecucion",
        })

    if int(claims.get("stale_active_count") or 0) > 0:
        alerts.append({
            "alert_key": "AGENT_GUARD_STALE_CLAIM:claims:warning",
            "code": "AGENT_GUARD_STALE_CLAIM",
            "severity": "warning",
            "resource": ".git/agent-guard/state/claims",
            "bucket": int(claims.get("stale_active_count") or 0),
            "message": f"Claims activos sin heartbeat reciente: {claims.get('stale_active_count')}",
        })

    for wt in worktrees.get("items") or ():
        name = str(wt.get("name") or "")
        if wt.get("dirty"):
            alerts.append({
                "alert_key": f"AGENT_WORKTREE_LIFECYCLE:{name}:dirty",
                "code": "AGENT_WORKTREE_LIFECYCLE",
                "severity": "warning",
                "resource": name,
                "bucket": "dirty",
                "message": f"Worktree {name} contiene cambios locales; prohibido eliminar automaticamente",
            })
        if wt.get("oversized"):
            alerts.append({
                "alert_key": f"AGENT_WORKTREE_LIFECYCLE:{name}:oversized",
                "code": "AGENT_WORKTREE_LIFECYCLE",
                "severity": "warning",
                "resource": name,
                "bucket": int(round(float(wt.get("apparent_mib") or 0.0))),
                "message": f"Worktree {name} usa {wt.get('apparent_mib')} MiB (>= 128 MiB); reconciliar cuando corresponda",
            })

    return alerts


def _deduplicate_alerts(
    raw_alerts: list[dict[str, Any]],
    previous_alerts_map: Mapping[str, Any],
    *,
    now_str: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    """Deduplicate repeated alerts by structural key while tracking occurrences and suppressed duplicates."""
    active_list: list[dict[str, Any]] = []
    new_map: dict[str, Any] = {}
    suppressed_this_cycle = 0

    for item in raw_alerts:
        key = str(item["alert_key"])
        prev = previous_alerts_map.get(key) if isinstance(previous_alerts_map, Mapping) else None
        if isinstance(prev, Mapping):
            same_bucket = prev.get("bucket") == item.get("bucket")
            occurrences = int(prev.get("occurrences") or 1) + 1
            suppressed = int(prev.get("suppressed_duplicates") or 0) + (1 if same_bucket else 0)
            if same_bucket:
                suppressed_this_cycle += 1
            entry = {
                "alert_key": key,
                "code": item["code"],
                "severity": item["severity"],
                "resource": item["resource"],
                "bucket": item.get("bucket"),
                "message": item["message"],
                "state": "ACTIVE_DEDUPLICATED" if same_bucket else "ACTIVE_UPDATED",
                "first_seen_at_utc": str(prev.get("first_seen_at_utc") or now_str),
                "last_seen_at_utc": now_str,
                "occurrences": occurrences,
                "suppressed_duplicates": suppressed,
                "emit_notification": not same_bucket,
            }
        else:
            entry = {
                "alert_key": key,
                "code": item["code"],
                "severity": item["severity"],
                "resource": item["resource"],
                "bucket": item.get("bucket"),
                "message": item["message"],
                "state": "ACTIVE_NEW",
                "first_seen_at_utc": now_str,
                "last_seen_at_utc": now_str,
                "occurrences": 1,
                "suppressed_duplicates": 0,
                "emit_notification": True,
            }
        active_list.append(entry)
        new_map[key] = entry

    return active_list, new_map, suppressed_this_cycle


def _detect_optional_vscode_watch() -> bool:
    """Detect whether the optional VS Code task watch process is running (purely informational)."""
    proc = Path("/proc")
    if not proc.is_dir():
        return False
    for child in proc.iterdir():
        if not child.name.isdigit():
            continue
        try:
            cmd = (child / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
        except Exception:
            continue
        if "agent_guard.py" in cmd and " watch" in cmd:
            return True
    return False


def collect_agent_guard_supervision(
    *,
    repo_root: Path | None = None,
    state_root: Path | None = None,
    now_epoch: float | None = None,
    interval_seconds: float | None = None,
    size_cache_ttl_seconds: float | None = None,
    force: bool = False,
    persist: bool = True,
) -> dict[str, Any]:
    """Run interval-gated independent Agent Guard supervision and return compact telemetry."""
    rroot = repo_root or Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    qroot = state_root or (rroot / ".git" / "universal-worker-queue")
    state_file = qroot / "runtime" / TELEMETRY_STATE_FILENAME
    now_ts = float(time.time() if now_epoch is None else now_epoch)
    interval = DEFAULT_SUPERVISION_INTERVAL_SECONDS if interval_seconds is None else max(1.0, float(interval_seconds))
    cache_ttl = DEFAULT_SIZE_CACHE_TTL_SECONDS if size_cache_ttl_seconds is None else max(1.0, float(size_cache_ttl_seconds))

    prev_state = _read_json_safe(state_file) or {}
    last_eval = prev_state.get("last_evaluated_epoch")
    last_snapshot = prev_state.get("snapshot")
    if (
        not force
        and isinstance(last_eval, (int, float))
        and isinstance(last_snapshot, dict)
        and (now_ts - float(last_eval)) < interval
    ):
        cached = dict(last_snapshot)
        cached["served_from_interval_cache"] = True
        return cached

    now_str = utc_now()
    storage = _disk_storage_snapshot(rroot)
    prev_storage_status = (
        (last_snapshot.get("storage") or {}).get("status")
        if isinstance(last_snapshot, dict)
        else None
    )
    storage_status = _evaluate_storage_status_with_hysteresis(
        float(storage["used_percent"]),
        prev_storage_status,
    )
    storage["status"] = storage_status

    hooks = _inspect_hooks(rroot)
    claims = _inspect_claims_and_registrations(rroot, now_epoch=now_ts)
    worktrees, new_size_cache = _inspect_worktrees_with_cache(
        rroot,
        previous_size_cache=prev_state.get("worktree_size_cache") or {},
        now_epoch=now_ts,
        size_cache_ttl_seconds=cache_ttl,
    )

    raw_alerts = _build_raw_alerts(
        storage=storage,
        storage_status=storage_status,
        hooks=hooks,
        claims=claims,
        worktrees=worktrees,
    )
    alerts, new_alerts_map, suppressed_this_cycle = _deduplicate_alerts(
        raw_alerts,
        prev_state.get("alerts_by_key") or {},
        now_str=now_str,
    )

    has_error = any(a.get("severity") == "error" for a in alerts)
    has_warning = any(a.get("severity") == "warning" for a in alerts)
    overall_health = "DEGRADED" if has_error else ("ATTENTION_REQUIRED" if has_warning else "HEALTHY")

    snapshot: dict[str, Any] = {
        "schema": SCHEMA_AGENT_GUARD_TELEMETRY,
        "at_utc": now_str,
        "health": overall_health,
        "supervision_mode": "CONTROL_PLANE_INDEPENDENT",
        "vscode_dependency": False,
        "optional_vscode_watch_active": _detect_optional_vscode_watch(),
        "supervision_interval_seconds": interval,
        "size_cache_ttl_seconds": cache_ttl,
        "served_from_interval_cache": False,
        "source_distribution": {
            "canonical_supervision_module": "tools/mirror_sync/agent_guard_telemetry.py",
            "installed_guard_script": ".git/agent-guard/bin/agent_guard.py",
            "legacy_repo_installer_present": False,
        },
        "hooks": hooks,
        "storage": storage,
        "worktrees": worktrees,
        "claims": claims,
        "alerts": alerts,
        "alert_summary": {
            "total_active": len(alerts),
            "errors": sum(1 for a in alerts if a.get("severity") == "error"),
            "warnings": sum(1 for a in alerts if a.get("severity") == "warning"),
            "suppressed_duplicates_this_cycle": suppressed_this_cycle,
            "emitted_notifications_this_cycle": sum(1 for a in alerts if a.get("emit_notification") is True),
        },
        "production_touched": False,
    }

    if persist:
        _atomic_write_json(
            state_file,
            {
                "schema": SCHEMA_AGENT_GUARD_TELEMETRY,
                "last_evaluated_epoch": now_ts,
                "last_evaluated_utc": now_str,
                "worktree_size_cache": new_size_cache,
                "alerts_by_key": new_alerts_map,
                "snapshot": snapshot,
            },
        )

    return snapshot


def load_agent_guard_telemetry(
    *,
    repo_root: Path | None = None,
    state_root: Path | None = None,
) -> dict[str, Any]:
    """Read-only telemetry accessor for Worker Console and Centro de Control."""
    rroot = repo_root or Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    qroot = state_root or (rroot / ".git" / "universal-worker-queue")
    state_file = qroot / "runtime" / TELEMETRY_STATE_FILENAME
    stored = _read_json_safe(state_file)
    if isinstance(stored, dict) and isinstance(stored.get("snapshot"), dict):
        snap = dict(stored["snapshot"])
        snap["production_touched"] = False
        return snap
    return collect_agent_guard_supervision(
        repo_root=rroot,
        state_root=qroot,
        persist=False,
    )
