"""GitHub Actions commercial clock recovery gate (no business writes).

The cron event is only a backup.  It must never bypass the existing
commercial owner lock or silently run if the GitHub API cannot be read.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

WORKFLOWS = frozenset({
    "commercial-open-sales-clock.yml",
    "commercial-closed-sales-clock.yml",
})
EXPECTED_REPO = "rbalam/EDARSA_HUB"
EXPECTED_REF = "refs/heads/Edarsahub_Desarrollo"
ACTIVE = frozenset({"queued", "in_progress", "waiting", "pending", "requested"})


def decision(event: str, runs: list[dict], now: dt.datetime, stale_seconds: int) -> tuple[bool, str]:
    """Return run decision and an auditable reason; only dispatch runs are owners."""
    if event != "schedule":
        return True, "NORMAL_DISPATCH"
    relevant = [r for r in runs if r.get("event") == "workflow_dispatch"]
    if not relevant:
        return True, "NO_PREVIOUS_DISPATCH"
    # Never race an already running owner. GitHub concurrency + SQL owner lock
    # provide additional protection against concurrent writes.
    if any(r.get("status") in ACTIVE for r in relevant):
        return False, "OWNER_RUN_ACTIVE"
    latest = max(relevant, key=lambda r: r.get("created_at") or "")
    timestamp = dt.datetime.fromisoformat(latest["created_at"].replace("Z", "+00:00"))
    age_seconds = (now - timestamp).total_seconds()
    if age_seconds < 0:
        return False, "CLOCK_SKEW"
    if latest.get("conclusion") == "startup_failure":
        return True, "PREVIOUS_STARTUP_FAILURE"
    if age_seconds < stale_seconds:
        return False, "DISPATCH_RECENT"
    return True, "DISPATCH_STALE"


def load_runs(repository: str, workflow: str, token: str) -> list[dict]:
    if repository != EXPECTED_REPO or workflow not in WORKFLOWS:
        raise ValueError("UNAUTHORIZED_REPOSITORY_OR_WORKFLOW")
    url = (
        f"https://api.github.com/repos/{repository}/actions/workflows/{workflow}/runs"
        "?branch=Edarsahub_Desarrollo&per_page=30"
    )
    req = Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(req, timeout=15) as res:
        body = json.load(res)
    if not isinstance(body.get("workflow_runs"), list):
        raise ValueError("WORKFLOW_RUNS_MISSING")
    return body["workflow_runs"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", choices=sorted(WORKFLOWS), required=True)
    parser.add_argument("--stale-seconds", type=int, required=True)
    args = parser.parse_args()
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    ref = os.environ.get("GITHUB_REF", "")
    output = os.environ.get("GITHUB_OUTPUT")
    if repo != EXPECTED_REPO or ref != EXPECTED_REF or not output or args.stale_seconds < 60:
        raise SystemExit("RECOVERY_FAIL_CLOSED_BAD_CONTEXT")
    if os.environ.get("EDARSA_ENV") != "DEVELOPMENT":
        raise SystemExit("RECOVERY_FAIL_CLOSED_BAD_ENV")
    if event not in ("push", "workflow_dispatch", "schedule"):
        raise SystemExit("RECOVERY_FAIL_CLOSED_BAD_EVENT")
    try:
        runs = load_runs(repo, args.workflow, os.environ["GH_TOKEN"]) if event == "schedule" else []
        run, reason = decision(event, runs, dt.datetime.now(dt.timezone.utc), args.stale_seconds)
    except (OSError, ValueError, KeyError, TimeoutError) as exc:
        # No fallback that might create a second owner.
        print(f"RECOVERY_GATE_FAILED={type(exc).__name__}")
        return 2
    Path(output).open("a", encoding="utf-8").write(f"should_run={str(run).lower()}\n")
    print(f"RECOVERY_GATE={reason}; SHOULD_RUN={str(run).lower()}")
    if reason in ("PREVIOUS_STARTUP_FAILURE", "DISPATCH_STALE", "NO_PREVIOUS_DISPATCH"):
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with Path(summary).open("a", encoding="utf-8") as f:
                f.write(f"### Commercial automatic recovery\nReason: {reason}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
