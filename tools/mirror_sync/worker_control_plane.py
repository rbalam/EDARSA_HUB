#!/usr/bin/env python3
"""Autonomous control plane for the EDARSAHUB universal worker.

This process is intentionally independent from the deterministic job executor.
It repairs recoverable runtime/control-plane failures without routing the repair
through the same job/claim path that may be unhealthy.

Safety invariants:
- never touches Production;
- never force-pushes;
- never destroys local changes (dirty state is stashed before safe FF only);
- Agent Guard orphan claims are quarantined, never deleted;
- live PIDs are always preserved;
- stale processing jobs are requeued only after a conservative grace period.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.mirror_sync.worker_maintenance_runtime import (
    audit_runtime_incident,
    declare_runtime_incident,
    read_runtime_incident,
    register_repair_attempt,
    register_repair_result,
    repair_attempt_allowed,
    supersede_runtime_incident,
)

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
GIT = ROOT / ".git"
STATE = GIT / "universal-worker-queue"
RUNTIME = STATE / "runtime"
PROCESSING = STATE / "processing"
PENDING = STATE / "pending"
RESULTS = STATE / "results"
REJECTED = STATE / "rejected"
PUBLISHED = STATE / "published"
AGENT_GUARD = GIT / "agent-guard"
AGENT_QUARANTINE = GIT / "agent-guard-quarantine"
AUDIT = STATE / "control-plane-audit.jsonl"
STATUS = RUNTIME / "control_plane_status.json"
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
DEV_BRANCH = "Edarsahub_Desarrollo"
INTERVAL = int(os.environ.get("EDARSAHUB_CONTROL_PLANE_INTERVAL", "15"))
HEARTBEAT_STALE = int(os.environ.get("EDARSAHUB_WORKER_HEARTBEAT_STALE_SECONDS", "60"))
CLAIM_GRACE = int(os.environ.get("EDARSAHUB_AGENT_CLAIM_GRACE_SECONDS", "90"))
PROCESSING_GRACE = int(os.environ.get("EDARSAHUB_PROCESSING_REQUEUE_SECONDS", "120"))
WORKER_SERVICE = os.environ.get("EDARSAHUB_UNIVERSAL_WORKER_SERVICE", "edarsahub-universal-worker")
EXPECTED_GENERATION_RE = re.compile(r'^RUNTIME_GENERATION="([^"]+)"', re.MULTILINE)
PID_RE = re.compile(r'(?i)["\']?pid["\']?\s*[:=]\s*["\']?(\d+)')
WORKER_TOKEN_RE = re.compile(r"worker-[A-Za-z0-9._-]{3,160}")

BOOTSTRAP_STATE = Path(
    os.environ.get(
        "EDARSAHUB_BOOTSTRAP_STATE",
        "/var/lib/edarsahub-bootstrap",
    )
)
CONTROL_PLANE_RUNTIME_MARKER = (
    BOOTSTRAP_STATE / "control_plane_active_runtime.json"
)
CONTROL_PLANE_IDENTITY_PATHS = (
    "tools/mirror_sync/worker_control_plane.py",
    "tools/mirror_sync/worker_maintenance_runtime.py",
    "tools/mirror_sync/worker_maintenance_controller.py",
    "tools/mirror_sync/worker_maintenance_contract.py",
    "tools/mirror_sync/worker_auditor.py",
    "tools/mirror_sync/worker_repair.py",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def epoch() -> float:
    return time.time()


def run(args: list[str], timeout: int = 30, check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"COMMAND_FAILED:{args}:{result.stdout[-1500:]}")
    return result


def control_plane_runtime_identity() -> str:
    components: list[str] = []

    for rel in CONTROL_PLANE_IDENTITY_PATHS:
        blob = git_output(
            "rev-parse",
            f"HEAD:{rel}",
        ).strip()

        if not re.fullmatch(r"[0-9a-f]{40}", blob):
            raise RuntimeError(
                f"CONTROL_PLANE_IDENTITY_INVALID:{rel}"
            )

        components.append(f"{rel}={blob}")

    return hashlib.sha256(
        ("\\n".join(components) + "\\n").encode("utf-8")
    ).hexdigest()


def write_control_plane_runtime_marker() -> dict[str, Any]:
    identity = control_plane_runtime_identity()
    development_sha = git_output(
        "rev-parse",
        "HEAD",
    ).strip()

    if not re.fullmatch(
        r"[0-9a-f]{40}",
        development_sha,
    ):
        raise RuntimeError(
            "CONTROL_PLANE_DEVELOPMENT_SHA_INVALID"
        )

    payload = {
        "schema": (
            "edarsahub.control-plane-active-runtime.v1"
        ),
        "active_identity": identity,
        "development_sha": development_sha,
        "pid": os.getpid(),
        "started_at_utc": utc_now(),
        "production_touched": False,
    }

    atomic_json(
        CONTROL_PLANE_RUNTIME_MARKER,
        payload,
    )

    return payload


def audit(event: str, **fields: Any) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    payload = {"at_utc": utc_now(), "event": event, **fields, "production_touched": False}
    with AUDIT.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = handle.name
    os.replace(tmp, path)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def pid_alive(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def parse_iso_age(value: str) -> float | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return max(0.0, epoch() - dt.timestamp())
    except ValueError:
        return None


def expected_generation() -> str:
    script = ROOT / "tools" / "mirror_sync" / "universal_job_worker.sh"
    match = EXPECTED_GENERATION_RE.search(read_text(script))
    return match.group(1) if match else ""


def request_universal_restart(reason: str) -> bool:
    env_name = (
        os.environ.get("EDARSA_ENV")
        or os.environ.get("APP_ENV")
        or os.environ.get("ENVIRONMENT")
        or "PREVIEW"
    ).upper()
    if "PROD" in env_name:
        audit("UNIVERSAL_RESTART_BLOCKED_PRODUCTION_ENV", reason=reason, environment=env_name)
        return False
    result = run(["supervisorctl", "restart", WORKER_SERVICE], timeout=30)
    ok = result.returncode == 0
    audit(
        "UNIVERSAL_RESTART_REQUESTED",
        reason=reason,
        service=WORKER_SERVICE,
        ok=ok,
        output=result.stdout[-1000:],
    )
    return ok


def heal_runtime_generation_and_heartbeat() -> dict[str, Any]:
    expected = expected_generation()
    actual = read_text(RUNTIME / "generation")
    pid_raw = read_text(RUNTIME / "pid")
    pid = int(pid_raw) if pid_raw.isdigit() else 0
    receive = read_text(RUNTIME / "last_receive_utc")
    receive_age = parse_iso_age(receive)

    generation_stale = bool(expected and actual != expected)
    heartbeat_stale = receive_age is None or receive_age > HEARTBEAT_STALE
    pid_dead = not pid_alive(pid)

    if generation_stale or heartbeat_stale or pid_dead:
        reason = ",".join(
            name
            for name, active in (
                ("GENERATION_STALE", generation_stale),
                ("HEARTBEAT_STALE", heartbeat_stale),
                ("PID_DEAD", pid_dead),
            )
            if active
        )
        request_universal_restart(reason)

    return {
        "expected_generation": expected,
        "actual_generation": actual,
        "pid": pid,
        "pid_alive": not pid_dead,
        "last_receive_utc": receive or None,
        "last_receive_age_seconds": receive_age,
        "runtime_repair_needed": generation_stale or heartbeat_stale or pid_dead,
    }


def git_output(*args: str) -> str:
    result = run(["git", *args], timeout=45)
    if result.returncode != 0:
        raise RuntimeError(f"GIT_FAILED:{args}:{result.stdout[-1200:]}")
    return result.stdout.strip()


def preserve_and_fast_forward() -> dict[str, Any]:
    """Converge only when remote is a strict FF and local has no unique commits."""
    try:
        run(["git", "fetch", "--quiet", REMOTE, DEV_BRANCH], timeout=60, check=True)
        branch = git_output("branch", "--show-current")
        if branch != DEV_BRANCH:
            return {"ff": "SKIP_WRONG_BRANCH", "branch": branch}
        local = git_output("rev-parse", "HEAD")
        remote = git_output("rev-parse", f"{REMOTE}/{DEV_BRANCH}")
        if local == remote:
            return {"ff": "ALREADY_ALIGNED", "local": local}
        counts = git_output("rev-list", "--left-right", "--count", f"HEAD...{REMOTE}/{DEV_BRANCH}").split()
        local_ahead, remote_ahead = (int(counts[0]), int(counts[1]))
        if local_ahead != 0 or remote_ahead <= 0:
            return {"ff": "SKIP_NON_FF", "local_ahead": local_ahead, "remote_ahead": remote_ahead}

        dirty = run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            timeout=20,
        ).stdout.strip()
        stash_ref = None
        if dirty:
            audit("FAST_FORWARD_DEFERRED_LOCAL_DIRTY")
            return {"ff": "DEFER_LOCAL_DIRTY"}

        ff = run(["git", "merge", "--ff-only", f"{REMOTE}/{DEV_BRANCH}"], timeout=60)
        if ff.returncode != 0:
            audit("FAST_FORWARD_FAILED", output=ff.stdout[-1200:], stash=stash_ref)
            return {"ff": "FAILED", "stash": stash_ref}
        new_head = git_output("rev-parse", "HEAD")
        audit("FAST_FORWARD_APPLIED", from_sha=local, to_sha=new_head)
        return {"ff": "APPLIED", "from": local, "to": new_head}
    except Exception as exc:
        audit("FAST_FORWARD_EXCEPTION", error=str(exc))
        return {"ff": "ERROR", "error": str(exc)}


def claim_candidates() -> list[Path]:
    if not AGENT_GUARD.is_dir():
        return []
    candidates: list[Path] = []
    for path in AGENT_GUARD.rglob("*"):
        if not path.is_file():
            continue
        lowered = "/".join(part.lower() for part in path.parts)
        if not any(token in lowered for token in ("claim", "claims", "lock", "locks")):
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
        except OSError:
            continue
        text = read_text(path)
        if WORKER_TOKEN_RE.search(path.name) or WORKER_TOKEN_RE.search(text):
            candidates.append(path)
    return candidates


def reconcile_agent_guard_orphans() -> dict[str, int]:
    live = recent = quarantined = 0
    now_ts = epoch()
    for path in claim_candidates():
        try:
            age = now_ts - path.stat().st_mtime
        except OSError:
            continue
        text = read_text(path)
        pids = {int(value) for value in PID_RE.findall(text)}
        if any(pid_alive(pid) for pid in pids):
            live += 1
            continue
        if age < CLAIM_GRACE:
            recent += 1
            continue
        try:
            rel = path.relative_to(AGENT_GUARD)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
            destination = AGENT_QUARANTINE / stamp / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(destination))
            quarantined += 1
            audit(
                "AGENT_GUARD_ORPHAN_QUARANTINED",
                source=str(path),
                destination=str(destination),
                age_seconds=int(age),
                pids=sorted(pids),
            )
        except Exception as exc:
            audit("AGENT_GUARD_QUARANTINE_FAILED", source=str(path), error=str(exc))
    return {"live": live, "recent": recent, "quarantined": quarantined}


def requeue_stale_processing() -> int:
    PENDING.mkdir(parents=True, exist_ok=True)
    PROCESSING.mkdir(parents=True, exist_ok=True)
    REJECTED.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    requeued = 0
    for path in PROCESSING.glob("*.json"):
        try:
            age = epoch() - path.stat().st_mtime
        except OSError:
            continue
        if age < PROCESSING_GRACE:
            continue
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            audit("STALE_PROCESSING_INVALID_ENVELOPE", job_file=path.name, error=str(exc))
            continue
        retry_count = int(envelope.get("_worker_stale_requeue_count") or 0)
        if retry_count >= 1:
            job = envelope.get("job") if isinstance(envelope.get("job"), dict) else {}
            job_id = str(job.get("job_id") or path.stem)
            completed = utc_now()
            result = {
                "schema": "edarsahub.worker-result.v2",
                "job_id": job_id,
                "status": "BLOCKED",
                "quality_gate": "FAIL",
                "certification": "NOT_CERTIFIED",
                "percent_complete": 0,
                "production_touched": False,
                "blockers": ["processing_stale_after_single_requeue"],
                "completed_at_utc": completed,
                "summary_es": "El job excedio el SLA de processing despues de un unico reintento seguro y fue cerrado terminalmente para no bloquear la cola."
            }
            atomic_json(RESULTS / path.name, result)
            os.replace(path, REJECTED / path.name)
            (RUNTIME / "last_terminal_utc").write_text(completed + "\n", encoding="utf-8")
            audit("STALE_PROCESSING_TERMINATED", job_file=path.name, age_seconds=int(age))
            continue
        target = PENDING / path.name
        if target.exists():
            continue
        envelope["_worker_stale_requeue_count"] = retry_count + 1
        atomic_json(path, envelope)
        os.replace(path, target)
        requeued += 1
        audit("STALE_PROCESSING_REQUEUED", job_file=path.name, age_seconds=int(age), retry_count=retry_count + 1)
    return requeued




AUTOMATION_STATE_SCHEMA = "edarsahub.worker-repair-automation-state.v1"


def _parse_canonical_utc(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return None

    return parsed.astimezone(timezone.utc)


def repair_automation_state_path() -> Path:
    return (
        ROOT
        / ".git"
        / "universal-worker-queue"
        / "maintenance"
        / "automation_state.json"
    )


def load_repair_automation_state() -> dict[str, Any]:
    path = repair_automation_state_path()

    fail_closed = {
        "schema": AUTOMATION_STATE_SCHEMA,
        "enabled": False,
        "enabled_at_utc": None,
        "enabled_from_development_sha": None,
        "adopted_job_ids": [],
        "production_allowed": False,
        "valid": False,
    }

    if not path.is_file():
        return fail_closed

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fail_closed

    if not isinstance(payload, dict):
        return fail_closed

    enabled_at = _parse_canonical_utc(payload.get("enabled_at_utc"))
    development_sha = str(
        payload.get("enabled_from_development_sha") or ""
    ).strip()

    adopted = payload.get("adopted_job_ids")

    valid = (
        payload.get("schema") == AUTOMATION_STATE_SCHEMA
        and payload.get("enabled") is True
        and payload.get("production_allowed") is False
        and enabled_at is not None
        and bool(re.fullmatch(r"[0-9a-f]{40}", development_sha))
        and isinstance(adopted, list)
        and all(
            isinstance(job_id, str) and job_id.strip()
            for job_id in adopted
        )
    )

    if not valid:
        return fail_closed

    return {
        "schema": AUTOMATION_STATE_SCHEMA,
        "enabled": True,
        "enabled_at_utc": enabled_at.isoformat().replace("+00:00", "Z"),
        "enabled_from_development_sha": development_sha,
        "adopted_job_ids": sorted(set(adopted)),
        "production_allowed": False,
        "valid": True,
    }


def automatic_repair_result_is_eligible(
    result: dict[str, Any],
    automation_state: dict[str, Any],
) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "RESULT_INVALID"

    if automation_state.get("valid") is not True:
        return False, "AUTOMATION_STATE_INVALID"

    if automation_state.get("enabled") is not True:
        return False, "AUTOMATION_DISABLED"

    if automation_state.get("production_allowed") is not False:
        return False, "AUTOMATION_PRODUCTION_POLICY_INVALID"

    if result.get("production_touched") is not False:
        return False, "PRODUCTION_TOUCHED"

    job_id = str(result.get("job_id") or "").strip()

    adopted = set(automation_state.get("adopted_job_ids") or [])

    if job_id and job_id in adopted:
        return True, "EXPLICITLY_ADOPTED"

    completed_at = _parse_canonical_utc(result.get("completed_at_utc"))
    enabled_at = _parse_canonical_utc(
        automation_state.get("enabled_at_utc")
    )

    if completed_at is None:
        return False, "RESULT_COMPLETED_AT_INVALID"

    if enabled_at is None:
        return False, "AUTOMATION_ENABLED_AT_INVALID"

    if completed_at <= enabled_at:
        return False, "HISTORICAL_RESULT"

    return True, "POST_ACTIVATION_RESULT"



def _valid_git_sha(value: Any) -> str | None:
    text = str(value or "").strip().lower()

    if re.fullmatch(r"[0-9a-f]{40}", text):
        return text

    return None


def automatic_repair_source_anchor(
    source_result: dict[str, Any],
) -> tuple[str | None, str]:
    for field in (
        "candidate_sha",
        "execution_base_sha",
        "base_sha",
        "initial_base_sha",
        "remote_at_start",
        "local_at_start",
    ):
        value = _valid_git_sha(
            source_result.get(field)
        )

        if value is not None:
            return value, field

    return None, "SOURCE_ANCHOR_UNAVAILABLE"


def automatic_repair_result_commit(
    result: dict[str, Any],
) -> str | None:
    return (
        _valid_git_sha(result.get("development_sha"))
        or _valid_git_sha(result.get("candidate_sha"))
    )


def automatic_repair_result_is_certified_successor(
    result: dict[str, Any],
) -> bool:
    blockers = result.get("blockers")

    return (
        result.get("status") == "INTEGRATED"
        and result.get("quality_gate") == "PASS"
        and result.get("tests") == "PASS"
        and result.get("git_sync_status")
        == "CERTIFIED_GIT_SYNC"
        and result.get("production_touched") is False
        and blockers in (None, [])
        and automatic_repair_result_commit(result)
        is not None
    )


def _git_is_ancestor(
    ancestor_sha: str,
    descendant_sha: str,
) -> bool:
    proc = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            ancestor_sha,
            descendant_sha,
        ],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )

    return proc.returncode == 0


def _target_diff_paths(
    base_sha: str,
    head_sha: str,
    target_paths: tuple[str, ...],
) -> set[str] | None:
    try:
        return {
            line.strip()
            for line in git_output(
                "diff",
                "--name-only",
                base_sha,
                head_sha,
                "--",
                *target_paths,
            ).splitlines()
            if line.strip()
        }
    except Exception:
        return None


def find_certified_successor_result(
    source_result: dict[str, Any],
    target_paths: tuple[str, ...],
    result_corpus: tuple[dict[str, Any], ...],
    *,
    current_head: str,
) -> dict[str, Any] | None:
    source_anchor, _anchor_field = (
        automatic_repair_source_anchor(
            source_result
        )
    )

    if source_anchor is None:
        return None

    if not _valid_git_sha(current_head):
        return None

    source_job_id = str(
        source_result.get("job_id") or ""
    ).strip()

    source_completed = _parse_canonical_utc(
        source_result.get("completed_at_utc")
    )

    required_paths = set(target_paths)

    if not required_paths:
        return None

    candidates: list[
        tuple[datetime, str, dict[str, Any]]
    ] = []

    for candidate in result_corpus:
        if candidate is source_result:
            continue

        candidate_job_id = str(
            candidate.get("job_id") or ""
        ).strip()

        if (
            source_job_id
            and candidate_job_id == source_job_id
        ):
            continue

        if not automatic_repair_result_is_certified_successor(
            candidate
        ):
            continue

        successor_sha = (
            automatic_repair_result_commit(candidate)
        )

        if successor_sha is None:
            continue

        candidate_completed = _parse_canonical_utc(
            candidate.get("completed_at_utc")
        )

        if (
            source_completed is not None
            and candidate_completed is not None
            and candidate_completed <= source_completed
        ):
            continue

        candidate_paths_raw = (
            candidate.get("files_changed") or []
        )

        if not isinstance(candidate_paths_raw, list):
            continue

        candidate_paths = {
            str(path).strip()
            for path in candidate_paths_raw
            if isinstance(path, str)
            and str(path).strip()
        }

        if not required_paths.issubset(
            candidate_paths
        ):
            continue

        if not _git_is_ancestor(
            source_anchor,
            successor_sha,
        ):
            continue

        if not _git_is_ancestor(
            successor_sha,
            current_head,
        ):
            continue

        changed = _target_diff_paths(
            source_anchor,
            successor_sha,
            target_paths,
        )

        if changed is None:
            continue

        if not required_paths.issubset(changed):
            continue

        sort_time = (
            candidate_completed
            or datetime.min.replace(
                tzinfo=timezone.utc
            )
        )

        candidates.append(
            (
                sort_time,
                successor_sha,
                candidate,
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
            str(
                item[2].get("job_id") or ""
            ),
        )
    )

    return candidates[0][2]


def repair_incident_is_superseded(
    source_result: dict[str, Any],
    target_paths: tuple[str, ...],
    *,
    result_corpus: tuple[dict[str, Any], ...] = (),
) -> tuple[bool, str]:
    development_sha = _valid_git_sha(
        source_result.get("development_sha")
    )

    try:
        current_head = git_output(
            "rev-parse",
            "HEAD",
        ).strip()
    except Exception:
        return False, "CURRENT_HEAD_UNAVAILABLE"

    if not _valid_git_sha(current_head):
        return False, "CURRENT_HEAD_INVALID"

    if development_sha is not None:
        if development_sha == current_head:
            return False, "SOURCE_IS_CURRENT_HEAD"

        if not _git_is_ancestor(
            development_sha,
            current_head,
        ):
            return False, "SOURCE_NOT_ANCESTOR"

        changed_after = _target_diff_paths(
            development_sha,
            current_head,
            target_paths,
        )

        if changed_after is None:
            return False, "TARGET_DIFF_UNAVAILABLE"

        if not changed_after:
            return False, "TARGETS_UNCHANGED"

        if not set(target_paths).issubset(
            changed_after
        ):
            return (
                False,
                "NOT_ALL_TARGETS_SUPERSEDED",
            )

        return True, "SUPERSEDED_BY_CURRENT_HEAD"

    successor = find_certified_successor_result(
        source_result,
        target_paths,
        result_corpus,
        current_head=current_head,
    )

    if successor is None:
        anchor, anchor_reason = (
            automatic_repair_source_anchor(
                source_result
            )
        )

        if anchor is None:
            return False, anchor_reason

        return (
            False,
            "CERTIFIED_SUCCESSOR_NOT_FOUND",
        )

    return True, "CERTIFIED_SUCCESSOR_RESULT"


def automatic_repair_orchestration() -> dict[str, Any]:
    """Detect bounded Worker-infrastructure repair incidents only.

    Detection and incident declaration occur here.
    Mutation execution remains exclusively in Universal Worker.
    Independent certification remains exclusively in Worker Auditor.
    """
    results_root = ROOT / ".git" / "universal-worker-queue" / "results"
    automation_state = load_repair_automation_state()

    observed = 0
    eligible = 0
    declared = 0
    blocked = 0
    incidents: list[dict[str, Any]] = []

    repairable_statuses = {
        "GIT_TESTS_FAILED",
        "GIT_SCOPE_VIOLATION",
        "GIT_DIVERGENCE_BLOCKED",
        "GIT_PUSH_FAILED",
        "BLOCKED",
    }

    worker_roots = (
        "tools/mirror_sync/",
        "backend/modules/worker_runtime_wake/",
        "backend/tests/test_worker_",
        ".github/workflows/universal-worker-",
        ".github/workflows/worker-",
    )

    if not results_root.is_dir():
        return {
            "schema": "edarsahub.worker-automatic-repair.v1",
            "observed_terminal_results": 0,
            "eligible_incidents": 0,
            "declared_incidents": 0,
            "blocked_incidents": 0,
            "incidents": [],
            "production_touched": False,
        }

    result_corpus: list[dict[str, Any]] = []

    for result_path in sorted(results_root.glob("*.json")):
        try:
            result = json.loads(
                result_path.read_text(encoding="utf-8")
            )
        except Exception:
            continue

        if not isinstance(result, dict):
            continue

        result_corpus.append(result)

    result_corpus_tuple = tuple(result_corpus)

    for result in result_corpus_tuple:
        observed += 1

        status = str(result.get("status") or "").strip()
        certification = str(
            result.get("certification") or ""
        ).strip()

        if status not in repairable_statuses:
            continue

        if certification not in {
            "",
            "NOT_CERTIFIED",
            "PENDING_AUDIT_EVIDENCE",
        }:
            continue

        if result.get("production_touched") is not False:
            continue

        boundary_allowed, boundary_reason = (
            automatic_repair_result_is_eligible(
                result,
                automation_state,
            )
        )

        raw_paths = (
            result.get("files_changed")
            or result.get("expected_scope")
            or []
        )

        if not isinstance(raw_paths, list):
            continue

        normalized = {
            str(path).strip()
            for path in raw_paths
            if isinstance(path, str) and str(path).strip()
        }

        target_paths = tuple(
            sorted(
                path
                for path in normalized
                if any(
                    path.startswith(root)
                    for root in worker_roots
                )
            )
        )

        if not target_paths:
            continue

        # Mixed Worker/application scope fails closed.
        if len(target_paths) != len(normalized):
            continue

        source_job_id = str(
            result.get("job_id") or result_path.stem
        ).strip()

        if not boundary_allowed:
            incidents.append(
                {
                    "incident_id": None,
                    "source_job_id": source_job_id,
                    "source_status": status,
                    "state": "OBSERVED_NOT_ELIGIBLE",
                    "target_paths": list(target_paths),
                    "repair_allowed": False,
                    "repair_reason": boundary_reason,
                    "publication_required": False,
                }
            )
            continue

        eligible += 1

        source_job_id = str(
            result.get("job_id") or result_path.stem
        ).strip()

        digest = hashlib.sha256(
            (
                source_job_id
                + "\n"
                + status
                + "\n"
                + "\n".join(target_paths)
            ).encode("utf-8")
        ).hexdigest()[:20]

        incident_id = f"WORKER-{digest}"

        try:
            incident = declare_runtime_incident(
                incident_id,
                list(target_paths),
            )
        except ValueError as exc:
            blocked += 1

            incidents.append(
                {
                    "incident_id": incident_id,
                    "source_job_id": source_job_id,
                    "state": "BLOCKED",
                    "reason": str(exc),
                    "target_paths": list(target_paths),
                }
            )
            continue

        superseded, superseded_reason = (
            repair_incident_is_superseded(
                result,
                target_paths,
                result_corpus=result_corpus_tuple,
            )
        )

        if superseded:
            incident = supersede_runtime_incident(
                incident_id,
                reason=superseded_reason,
            )

            incidents.append(
                {
                    "incident_id": incident.incident_id,
                    "source_job_id": source_job_id,
                    "source_status": status,
                    "state": incident.state,
                    "target_paths": list(target_paths),
                    "repair_allowed": False,
                    "repair_reason": superseded_reason,
                    "publication_required": False,
                }
            )
            continue

        allowed, reason = repair_attempt_allowed(
            incident_id
        )

        incidents.append(
            {
                "incident_id": incident.incident_id,
                "source_job_id": source_job_id,
                "source_status": status,
                "state": incident.state,
                "target_paths": list(target_paths),
                "repair_allowed": allowed,
                "repair_reason": reason,
                "publication_required": allowed,
            }
        )

        if allowed:
            declared += 1
        else:
            blocked += 1

    return {
        "schema": "edarsahub.worker-automatic-repair.v1",
        "observed_terminal_results": observed,
        "eligible_incidents": eligible,
        "declared_incidents": declared,
        "blocked_incidents": blocked,
        "incidents": incidents,
        "production_touched": False,
    }


def maintenance_runtime_summary() -> dict[str, Any]:
    """Read-only maintenance-plane visibility for the canonical control plane."""
    maintenance_root = ROOT / ".git" / "universal-worker-queue" / "maintenance" / "incidents"

    incidents: list[dict[str, Any]] = []

    if maintenance_root.is_dir():
        for path in sorted(maintenance_root.glob("*.json")):
            try:
                incident = read_runtime_incident(path.stem)
            except Exception as exc:
                incidents.append(
                    {
                        "incident_id": path.stem,
                        "state": "INVALID",
                        "error": type(exc).__name__,
                    }
                )
                continue

            if incident is None:
                continue

            incidents.append(
                {
                    "incident_id": incident.incident_id,
                    "state": incident.state,
                    "attempts": incident.attempts,
                    "cooldown_until_epoch": incident.cooldown_until_epoch,
                    "target_paths": list(incident.target_paths),
                    "production_touched": incident.production_touched,
                }
            )

    return {
        "schema": "edarsahub.worker-maintenance-summary.v1",
        "incident_count": len(incidents),
        "incidents": incidents,
        "production_touched": False,
    }

def cycle() -> dict[str, Any]:
    ff = preserve_and_fast_forward()
    runtime = heal_runtime_generation_and_heartbeat()
    claims = reconcile_agent_guard_orphans()
    requeued = requeue_stale_processing()
    automatic_repair = automatic_repair_orchestration()
    payload = {
        "schema": "edarsahub.worker-control-plane.v1",
        "at_utc": utc_now(),
        "ff": ff,
        "runtime": runtime,
        "agent_guard": claims,
        "stale_processing_requeued": requeued,
        "maintenance": maintenance_runtime_summary(),
        "automatic_repair": automatic_repair,
        "production_touched": False,
    }
    atomic_json(STATUS, payload)
    return payload


def main() -> int:
    once = "--once" in os.sys.argv

    try:
        active_runtime = (
            write_control_plane_runtime_marker()
        )
        audit(
            "CONTROL_PLANE_RUNTIME_ACTIVE",
            active_identity=active_runtime[
                "active_identity"
            ],
            development_sha=active_runtime[
                "development_sha"
            ],
            pid=active_runtime["pid"],
        )
    except Exception as exc:
        audit(
            "CONTROL_PLANE_RUNTIME_IDENTITY_FAILED",
            error=str(exc),
        )

    while True:
        try:
            payload = cycle()
            print("CONTROL_PLANE_STATE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
        except Exception as exc:
            audit("CONTROL_PLANE_CYCLE_EXCEPTION", error=str(exc))
            print(f"CONTROL_PLANE_ERROR={exc}", flush=True)
        if once:
            return 0
        time.sleep(max(5, INTERVAL))


if __name__ == "__main__":
    raise SystemExit(main())
