#!/usr/bin/env python3

import hashlib
import json
import os
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/app")
REPORT_DIR = Path(
    os.environ.get(
        "MIRROR_SYNC_REPORT_STATE_DIR",
        "/app/.git/mirror-sync/reporting",
    )
)
LATEST = REPORT_DIR / "latest.json"
EXPORT_ROOT = Path(
    os.environ.get(
        "EDARSAHUB_AUDIT_EXPORT_ROOT",
        "/app/exports/mirror_sync",
    )
)
LAST_EXPORTED = REPORT_DIR / "last_audit_exported_head"
AUDIT_ID = os.environ.get("EDARSAHUB_MIRROR_AUDIT_ID", "MIRROR_0001")
SCHEMA = "edarsahub.work_completion.v1"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def valid_sha(value) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in value)


def read_last_exported():
    try:
        value = LAST_EXPORTED.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    return value if valid_sha(value) else None


def write_last_exported(head: str) -> None:
    atomic_write(LAST_EXPORTED, (head + "\n").encode("utf-8"))


def classify_completion(report: dict) -> tuple[str, list[str]]:
    blockers = []

    head = report.get("head_after")
    dev = report.get("development_head")
    mirror = report.get("mirror_head")

    if not valid_sha(head):
        blockers.append("invalid_source_sha")
    if dev != head:
        blockers.append("development_sha_mismatch")
    if mirror != head:
        blockers.append("mirror_sha_mismatch")
    if report.get("converged") is not True:
        blockers.append("remote_not_converged")
    if report.get("production_touched") is not False:
        blockers.append("production_touch_not_proven_false")
    if report.get("mongo_business_dependency") is not False:
        blockers.append("mongo_business_dependency")
    if report.get("live_business_connection") is not False:
        blockers.append("live_business_connection")

    # Mirror convergence is independently provable by the worker. Business/job
    # tests are not inferred. A separate SHA-bound test attestation is required
    # before a work item can be called CERTIFIED.
    attestation_path = REPORT_DIR / "test_attestations" / f"{head}.json"
    tests = "UNKNOWN"
    quality_gate = "UNKNOWN"

    if attestation_path.is_file():
        try:
            attestation = read_json(attestation_path)
        except Exception:
            blockers.append("invalid_test_attestation")
        else:
            if attestation.get("source_sha") != head:
                blockers.append("test_attestation_sha_mismatch")
            tests = str(attestation.get("tests", "UNKNOWN")).upper()
            quality_gate = str(attestation.get("quality_gate", "UNKNOWN")).upper()
            if tests != "PASS":
                blockers.append("tests_not_pass")
            if quality_gate != "PASS":
                blockers.append("quality_gate_not_pass")
    else:
        blockers.append("missing_sha_bound_test_attestation")

    status = "CERTIFIED" if not blockers else "NOT_CERTIFIED"
    return status, blockers, tests, quality_gate


def build_payload(report: dict) -> dict:
    status, blockers, tests, quality_gate = classify_completion(report)
    files = report.get("files") or {}
    changed_files = []
    for key in ("added", "modified", "deleted"):
        for value in files.get(key, []) or []:
            if isinstance(value, str):
                changed_files.append({"status": key, "path": value})
    for value in files.get("renamed", []) or []:
        if isinstance(value, dict):
            changed_files.append({"status": "renamed", **value})

    head = report.get("head_after")
    return {
        "schema": SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "job_id": report.get("request_id") or f"mirror-{head}",
        "agent": "edarsahub-mirror-worker",
        "source_repo": "rbalam/EDARSA_HUB",
        "source_branch": "Edarsahub_Desarrollo",
        "source_sha": head,
        "development_sha": report.get("development_head"),
        "mirror_sha": report.get("mirror_head"),
        "tests": tests,
        "quality_gate": quality_gate,
        "production_touched": report.get("production_touched"),
        "work_completion": status,
        "percent_complete": 100 if status == "CERTIFIED" else 95,
        "summary": report.get("summary"),
        "files_changed": changed_files,
        "blockers": blockers,
        "mirror_report_schema": report.get("schema"),
        "business_database_access": report.get("business_database_access"),
        "mongo_business_dependency": report.get("mongo_business_dependency"),
        "live_business_connection": report.get("live_business_connection"),
    }


def export_triplet(payload: dict) -> tuple[Path, Path, Path]:
    stamp = utc_stamp()
    destination = EXPORT_ROOT / AUDIT_ID
    destination.mkdir(parents=True, exist_ok=True)

    completion_name = "work_completion.json"
    summary_name = "summary.txt"
    completion_bytes = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    summary_bytes = ((payload.get("summary") or "") + "\n").encode("utf-8")

    package = destination / f"{AUDIT_ID}_{stamp}.tgz"
    manifest = destination / f"manifest_{stamp}.json"
    checksums = destination / f"checksums_{stamp}.sha256"

    with tempfile.TemporaryDirectory(prefix="edarsahub_mirror_audit_") as temp_dir:
        temp = Path(temp_dir)
        atomic_write(temp / completion_name, completion_bytes)
        atomic_write(temp / summary_name, summary_bytes)

        with tarfile.open(package, "w:gz") as archive:
            archive.add(temp / completion_name, arcname=completion_name)
            archive.add(temp / summary_name, arcname=summary_name)

    package_sha = hashlib.sha256(package.read_bytes()).hexdigest()
    manifest_payload = {
        "schema_version": 1,
        "audit_id": AUDIT_ID,
        "stamp": stamp,
        "package": package.name,
        "package_sha256": package_sha,
        "source_repo": payload["source_repo"],
        "source_branch": payload["source_branch"],
        "source_sha": payload["source_sha"],
        "work_completion": payload["work_completion"],
    }
    atomic_write(
        manifest,
        (json.dumps(manifest_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )

    checksum_lines = [
        f"{sha256_bytes(completion_bytes)}  {completion_name}",
        f"{sha256_bytes(summary_bytes)}  {summary_name}",
    ]
    atomic_write(checksums, ("\n".join(checksum_lines) + "\n").encode("utf-8"))
    return package, manifest, checksums


def main() -> int:
    if not LATEST.is_file():
        print("AUDIT_EXPORT=SKIP_NO_REPORT")
        return 0

    report = read_json(LATEST)
    current_head = report.get("head_after")
    if not valid_sha(current_head):
        print("AUDIT_EXPORT=SKIP_INVALID_HEAD")
        return 0

    if read_last_exported() == current_head:
        print("AUDIT_EXPORT=NONE")
        print("AUDIT_EXPORT_REASON=HEAD_ALREADY_EXPORTED")
        return 0

    if report.get("head_changed") is not True:
        print("AUDIT_EXPORT=NONE")
        print("AUDIT_EXPORT_REASON=NO_HEAD_CHANGE")
        return 0

    payload = build_payload(report)
    package, manifest, checksums = export_triplet(payload)
    write_last_exported(current_head)

    print(f"AUDIT_EXPORT=CREATED")
    print(f"AUDIT_EXPORT_PACKAGE={package}")
    print(f"AUDIT_EXPORT_MANIFEST={manifest}")
    print(f"AUDIT_EXPORT_CHECKSUMS={checksums}")
    print(f"WORK_COMPLETION={payload['work_completion']}")
    print(f"SOURCE_SHA={payload['source_sha']}")
    if payload["blockers"]:
        print("BLOCKERS=" + ",".join(payload["blockers"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
