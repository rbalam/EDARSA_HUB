"""Gate G3 (Independent Agent Guard Supervision, Deduplication, Hysteresis, Cache & Telemetry) tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from modules.worker_console import contract as worker_console_contract
from tools.mirror_sync import agent_guard_telemetry as agt


def test_g3_hysteresis_prevents_storage_alert_flapping():
    # Rising edge: <80 OK, >=80 WARNING, >=90 BLOCK
    assert agt._evaluate_storage_status_with_hysteresis(79.5, "OK") == "OK"
    assert agt._evaluate_storage_status_with_hysteresis(80.1, "OK") == "WARNING"
    assert agt._evaluate_storage_status_with_hysteresis(90.0, "WARNING") == "BLOCK"

    # Hysteresis band on falling edge: stays WARNING down to 78.0%, clears below 78.0%
    assert agt._evaluate_storage_status_with_hysteresis(79.9, "WARNING") == "WARNING"
    assert agt._evaluate_storage_status_with_hysteresis(78.0, "WARNING") == "WARNING"
    assert agt._evaluate_storage_status_with_hysteresis(77.9, "WARNING") == "OK"

    # Block hysteresis: stays BLOCK down to 88.0%, drops to WARNING below 88.0%
    assert agt._evaluate_storage_status_with_hysteresis(88.5, "BLOCK") == "BLOCK"
    assert agt._evaluate_storage_status_with_hysteresis(87.9, "BLOCK") == "WARNING"


def test_g3_deduplication_interval_cache_and_worktree_size_cache(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    state_root = tmp_path / "queue"
    (repo_root / ".git" / "agent-guard" / "bin").mkdir(parents=True)
    (repo_root / ".git" / "agent-guard" / "hooks").mkdir(parents=True)
    (repo_root / ".git" / "agent-guard" / "state" / "claims").mkdir(parents=True)
    (repo_root / ".git" / "agent-guard" / "state" / "worktrees").mkdir(parents=True)
    (repo_root / ".git" / "agent-guard" / "bin" / "agent_guard.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    for hk in ("pre-commit", "pre-push"):
        p = repo_root / ".git" / "agent-guard" / "hooks" / hk
        p.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        p.chmod(0o755)

    wt = repo_root / ".agent-worktrees" / "sample-wt"
    wt.mkdir(parents=True)
    (wt / "data.bin").write_bytes(b"x" * 1024)

    scan_calls = {"count": 0}

    def fake_scan(_wt: Path) -> int:
        scan_calls["count"] += 1
        return 140 * 1024 * 1024  # 140 MiB -> oversized warning

    monkeypatch.setattr(agt, "_scan_worktree_apparent_bytes", fake_scan)
    monkeypatch.setattr(
        agt,
        "_disk_storage_snapshot",
        lambda _r: {
            "path": str(repo_root),
            "used_percent": 80.2,
            "bucket_percent": 80,
            "total_gib": 9.8,
            "used_gib": 7.86,
            "available_gib": 1.94,
            "warn_threshold_percent": 80.0,
            "block_threshold_percent": 90.0,
            "hysteresis_clear_delta_percent": 2.0,
        },
    )

    # 1. First evaluation runs scan and emits new alerts
    snap1 = agt.collect_agent_guard_supervision(
        repo_root=repo_root,
        state_root=state_root,
        now_epoch=1000.0,
        interval_seconds=60.0,
        size_cache_ttl_seconds=120.0,
    )
    assert snap1["supervision_mode"] == "CONTROL_PLANE_INDEPENDENT"
    assert snap1["vscode_dependency"] is False
    assert snap1["served_from_interval_cache"] is False
    assert snap1["storage"]["status"] == "WARNING"
    assert scan_calls["count"] == 1
    assert snap1["alert_summary"]["total_active"] >= 2
    assert snap1["alert_summary"]["emitted_notifications_this_cycle"] == snap1["alert_summary"]["total_active"]
    assert snap1["production_touched"] is False

    # 2. Within interval (<60s), served from interval cache without rescanning
    snap2 = agt.collect_agent_guard_supervision(
        repo_root=repo_root,
        state_root=state_root,
        now_epoch=1020.0,
        interval_seconds=60.0,
        size_cache_ttl_seconds=120.0,
    )
    assert snap2["served_from_interval_cache"] is True
    assert scan_calls["count"] == 1

    # 3. After interval (>=60s) but within size_cache_ttl (<120s), reuses size cache AND deduplicates alerts
    snap3 = agt.collect_agent_guard_supervision(
        repo_root=repo_root,
        state_root=state_root,
        now_epoch=1070.0,
        interval_seconds=60.0,
        size_cache_ttl_seconds=120.0,
    )
    assert snap3["served_from_interval_cache"] is False
    assert scan_calls["count"] == 1, "Worktree size cache must avoid redundant rglob scan within TTL"
    assert snap3["worktrees"]["size_cache_hits"] == 1
    assert snap3["alert_summary"]["suppressed_duplicates_this_cycle"] >= 2
    assert snap3["alert_summary"]["emitted_notifications_this_cycle"] == 0
    for alert in snap3["alerts"]:
        assert alert["state"] == "ACTIVE_DEDUPLICATED"
        assert alert["occurrences"] == 2
        assert alert["suppressed_duplicates"] == 1


def test_g3_worker_console_and_centro_control_expose_agent_guard_supervision(tmp_path):
    qroot = tmp_path / "queue"
    (qroot / "runtime").mkdir(parents=True)
    (qroot / "maintenance" / "handoffs").mkdir(parents=True)
    telemetry_sample = {
        "schema": agt.SCHEMA_AGENT_GUARD_TELEMETRY,
        "at_utc": "2026-11-27T03:00:00Z",
        "health": "HEALTHY",
        "supervision_mode": "CONTROL_PLANE_INDEPENDENT",
        "vscode_dependency": False,
        "optional_vscode_watch_active": False,
        "hooks": {"guard_script_present": True, "pre_commit_executable": True, "pre_push_executable": True},
        "storage": {"used_percent": 75.0, "status": "OK"},
        "worktrees": {"total_extra_worktrees": 0, "dirty_count": 0, "oversized_count": 0, "items": []},
        "claims": {"active_count": 0, "released_count": 10, "stale_active_count": 0},
        "alerts": [],
        "alert_summary": {"total_active": 0, "errors": 0, "warnings": 0, "suppressed_duplicates_this_cycle": 0},
        "production_touched": False,
    }
    (qroot / "runtime" / "control_plane_status.json").write_text(
        json.dumps(
            {
                "at_utc": "2026-11-27T03:00:00Z",
                "runtime": {"pid_alive": True, "runtime_repair_needed": False},
                "ff": {"ff": "UP_TO_DATE", "local": "a" * 40},
                "agent_guard": {"live": 0, "recent": 0, "quarantined": 0, "publisher_worktrees_cleaned": 0},
                "agent_guard_supervision": telemetry_sample,
                "lifecycle_detection": {"system_degraded": False, "counts": {}},
                "lifecycle_recovery": {"status": "IDLE"},
            }
        ),
        encoding="utf-8",
    )

    snap = worker_console_contract.get_worker_self_healing_snapshot(queue_root=qroot)
    assert "agent_guard" in snap
    assert snap["agent_guard"]["supervision_mode"] == "CONTROL_PLANE_INDEPENDENT"
    assert snap["agent_guard"]["vscode_dependency"] is False
    assert snap["agent_guard"]["storage"]["status"] == "OK"
    assert snap["agent_guard"]["production_touched"] is False
    assert snap["production_touched"] is False
