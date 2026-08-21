#!/usr/bin/env python3

import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/app")
STATE_DIR = Path(
    os.environ.get(
        "MIRROR_SYNC_REPORT_STATE_DIR",
        "/app/.git/mirror-sync/reporting",
    )
)

OUTBOX_DIR = STATE_DIR / "outbox"
LATEST_FILE = STATE_DIR / "latest.json"
LAST_HEAD_FILE = STATE_DIR / "last_reported_head"

DEV_BRANCH = "Edarsahub_Desarrollo"
MIRROR_BRANCH = "mirror/emergent-live"


def run_git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic_json_write(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=str(path.parent),
        text=True,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(
                payload,
                fh,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())

        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, path)

    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def read_last_head():
    try:
        value = LAST_HEAD_FILE.read_text(encoding="utf-8").strip()
        if len(value) == 40:
            return value
    except FileNotFoundError:
        pass

    return None


def write_last_head(head):
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(
        prefix=".last_head.",
        dir=str(STATE_DIR),
        text=True,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(head + "\n")
            fh.flush()
            os.fsync(fh.fileno())

        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, LAST_HEAD_FILE)

    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def resolve_ref(ref):
    rc, out, _ = run_git("rev-parse", ref)
    return out if rc == 0 and len(out) == 40 else None


def classify_files(old_head, new_head):
    result = {
        "added": [],
        "modified": [],
        "deleted": [],
        "renamed": [],
        "other": [],
    }

    if not old_head or old_head == new_head:
        return result

    rc, out, _ = run_git(
        "diff",
        "--name-status",
        old_head,
        new_head,
    )

    if rc != 0:
        return result

    for line in out.splitlines():
        if not line.strip():
            continue

        parts = line.split("\t")
        code = parts[0]

        if code == "A" and len(parts) >= 2:
            result["added"].append(parts[1])

        elif code == "M" and len(parts) >= 2:
            result["modified"].append(parts[1])

        elif code == "D" and len(parts) >= 2:
            result["deleted"].append(parts[1])

        elif code.startswith("R") and len(parts) >= 3:
            result["renamed"].append(
                {
                    "from": parts[1],
                    "to": parts[2],
                }
            )

        elif len(parts) >= 2:
            result["other"].append(
                {
                    "status": code,
                    "file": parts[-1],
                }
            )

    return result


def build_summary(old_head, new_head, files, converged):
    if not old_head:
        return (
            "Mirror reporter inicializado. "
            f"HEAD actual {new_head[:12]}. "
            f"Convergencia remota={'SI' if converged else 'NO'}."
        )

    if old_head == new_head:
        return (
            "Ciclo autónomo completado sin cambios de HEAD. "
            f"HEAD {new_head[:12]}. "
            f"Convergencia remota={'SI' if converged else 'NO'}."
        )

    count = (
        len(files["added"])
        + len(files["modified"])
        + len(files["deleted"])
        + len(files["renamed"])
        + len(files["other"])
    )

    return (
        f"EDARSAHUB actualizado autónomamente "
        f"{old_head[:12]} -> {new_head[:12]}; "
        f"{count} archivo(s) afectados. "
        f"Convergencia local/desarrollo/mirror="
        f"{'SI' if converged else 'NO'}."
    )


def main():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)

    branch = resolve_ref("HEAD")

    rc, branch_name, _ = run_git("branch", "--show-current")
    if rc != 0:
        raise SystemExit(20)

    if branch_name != DEV_BRANCH:
        print("RESULT_REPORTER=SKIP_WRONG_BRANCH")
        return 0

    current_head = resolve_ref("HEAD")
    dev_head = resolve_ref(f"origin/{DEV_BRANCH}")
    mirror_head = resolve_ref(f"origin/{MIRROR_BRANCH}")

    if not current_head:
        raise SystemExit(21)

    previous_head = read_last_head()

    converged = (
        current_head is not None
        and dev_head == current_head
        and mirror_head == current_head
    )

    files = classify_files(previous_head, current_head)

    request_id = (
        os.environ.get("MIRROR_SYNC_REQUEST_ID")
        or os.environ.get("CHATGPT_REQUEST_ID")
        or None
    )

    changed = previous_head != current_head

    payload = {
        "schema": "edarsahub.mirror.result.v1",
        "generated_at_utc": utc_now(),
        "request_id": request_id,
        "domain": "git_mirror_infrastructure",
        "branch": branch_name,
        "head_before": previous_head,
        "head_after": current_head,
        "development_head": dev_head,
        "mirror_head": mirror_head,
        "head_changed": changed,
        "converged": converged,
        "files": files,
        "production_touched": False,
        "business_database_access": False,
        "mongo_business_dependency": False,
        "live_business_connection": False,
        "summary": build_summary(
            previous_head,
            current_head,
            files,
            converged,
        ),
    }

    # Baseline inicial y cada cambio de HEAD generan evento.
    # Ciclos sin cambio no generan spam de outbox.
    should_emit = previous_head is None or changed

    if should_emit:
        before_token = previous_head[:12] if previous_head else "baseline"
        event_name = f"{before_token}_{current_head[:12]}.json"
        event_path = OUTBOX_DIR / event_name

        if not event_path.exists():
            atomic_json_write(event_path, payload)

        atomic_json_write(LATEST_FILE, payload)

        print(f"RESULT_EVENT={event_path}")
        print(f"RESULT_LATEST={LATEST_FILE}")
        print(f"RESULT_SUMMARY={payload['summary']}")
    else:
        print("RESULT_EVENT=NONE")
        print("RESULT_REASON=NO_HEAD_CHANGE")

    write_last_head(current_head)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
