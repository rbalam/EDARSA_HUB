#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

EXPECTED_ROOT="/app"
EXPECTED_BRANCH="Edarsahub_Desarrollo"
INTERPRETER="/root/.venv/bin/python"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="/var/tmp/edarsahub_mongo_impact_audit_${TIMESTAMP}"
mkdir -p "$OUT_DIR"
exec > >(tee "$OUT_DIR/execution.log") 2>&1

fail() {
  printf 'AUDIT_RESULT=BLOCKED\nBLOCK_REASON=%s\n' "$2"
  exit "$1"
}

printf 'AUDIT_NAME=EDARSAHUB_MONGO_IMPACT_AUDIT\n'
printf 'AUDIT_MODE=READ_ONLY\n'
printf 'OUTPUT_DIR=%s\n' "$OUT_DIR"
printf 'PACKAGES_INSTALLED=0\nPACKAGES_REMOVED=0\n'
printf 'ENV_FILES_READ=0\nPROC_ENVIRON_READ=0\nSQL_CONNECTIONS=0\n'
printf 'APPLICATION_IMPORTS=0\nAPPLICATION_PROCESSES_STARTED=0\n'

[[ -d "$EXPECTED_ROOT/.git" ]] || fail 10 '/app no es repositorio Git'
cd "$EXPECTED_ROOT"

BRANCH="$(git branch --show-current)"
HEAD_SHA="$(git rev-parse HEAD)"
STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"
printf 'CURRENT_BRANCH=%s\nCURRENT_HEAD=%s\n' "$BRANCH" "$HEAD_SHA"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail 20 "rama inesperada: $BRANCH"
[[ -z "$STATUS_BEFORE" ]] || fail 21 'worktree no limpio'
[[ -x "$INTERPRETER" ]] || fail 22 "interprete no ejecutable: $INTERPRETER"

SUPERVISOR_FILE="$OUT_DIR/supervisor_status.txt"
if command -v supervisorctl >/dev/null 2>&1; then
  supervisorctl status > "$SUPERVISOR_FILE" 2>&1 || true
else
  printf 'supervisorctl unavailable\n' > "$SUPERVISOR_FILE"
fi

BACKEND_PID="$(awk '$1=="backend" && $2=="RUNNING" {for(i=1;i<=NF;i++) if($i=="pid") {gsub(",","",$(i+1)); print $(i+1); exit}}' "$SUPERVISOR_FILE")"
if [[ -z "$BACKEND_PID" ]]; then
  BACKEND_PID="$(pgrep -af 'server:app' 2>/dev/null | awk '$0 !~ /plugins\.tools\.agent\.server:app/ {print $1; exit}')"
fi
[[ "$BACKEND_PID" =~ ^[0-9]+$ ]] || fail 23 'no se resolvio PID backend'
[[ -r "/proc/$BACKEND_PID/cmdline" ]] || fail 24 'cmdline backend no legible'

CMDLINE="$(tr '\0' ' ' < "/proc/$BACKEND_PID/cmdline")"
[[ "$CMDLINE" == *'server:app'* ]] || fail 25 'PID no contiene server:app'
[[ "$CMDLINE" != *'plugins.tools.agent.server:app'* ]] || fail 26 'PID corresponde al servidor de plugins'
printf 'EDARSAHUB_PROCESS_PID=%s\n' "$BACKEND_PID"
printf '%s\n' "$CMDLINE" | sed -E 's#(mongodb(\+srv)?://)[^[:space:]]+#\1<redacted>#g' > "$OUT_DIR/backend_cmdline_sanitized.txt"

: > "$OUT_DIR/runtime_loaded_mongo_paths.txt"
if [[ -r "/proc/$BACKEND_PID/maps" ]]; then
  awk '{print $NF}' "/proc/$BACKEND_PID/maps" \
    | grep -E '/site-packages/(pymongo|bson|motor|gridfs)(/|$)' \
    | sort -u > "$OUT_DIR/runtime_loaded_mongo_paths.txt" || true
fi

: > "$OUT_DIR/runtime_mongo_connections.txt"
if command -v ss >/dev/null 2>&1; then
  ss -Hntp 2>/dev/null \
    | grep -F "pid=$BACKEND_PID," \
    | awk '$4 ~ /:(27017|27018|27019)$/ || $5 ~ /:(27017|27018|27019)$/' \
    > "$OUT_DIR/runtime_mongo_connections.txt" || true
fi

"$INTERPRETER" -I - "$EXPECTED_ROOT" "$OUT_DIR" "$BACKEND_PID" <<'PY'
from __future__ import annotations

import ast
import csv
import importlib.metadata as md
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
BACKEND = ROOT / "backend"
OUT = Path(sys.argv[2]).resolve()
PID = int(sys.argv[3])
MONGO_ROOTS = {"pymongo", "bson", "motor", "gridfs"}
COMPAT = {"core.mongo_stub", "core.sql_first.no_mongo"}
SKIP = {".git", "node_modules", "site-packages", "__pycache__", ".vendor", "vendor", "graphify-out"}
HIST = {"docs", "memory", "auditorias", "auditoria", "backups", "backup", "reports", "report"}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def scope(path: Path) -> str:
    parts = {p.lower() for p in path.relative_to(ROOT).parts}
    if parts & HIST:
        return "HISTORICAL_OR_DOCUMENTATION"
    if "tests" in parts or path.name.startswith("test_"):
        return "TEST"
    if "scripts" in parts:
        return "SCRIPT_OR_MAINTENANCE"
    if "tools" in parts:
        return "OPERATIONAL_TOOLING"
    if rel(path).startswith("backend/"):
        return "PRODUCTION_RUNTIME_CANDIDATE"
    return "OTHER"


def iter_python():
    for path in ROOT.rglob("*.py"):
        if not path.is_file():
            continue
        if set(path.relative_to(ROOT).parts) & SKIP:
            continue
        yield path


def module_name(path: Path):
    try:
        parts = list(path.relative_to(BACKEND).with_suffix("").parts)
    except ValueError:
        return None
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


files = list(iter_python())
module_paths = {module_name(p): p for p in files if module_name(p)}
imports = defaultdict(set)
hits = []
parse_errors = []

for path in files:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    except Exception as exc:
        parse_errors.append({"path": rel(path), "error": f"{type(exc).__name__}:{exc}"})
        continue
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            names = [base]
        for name in names:
            if not name:
                continue
            imports[path].add(name)
            root = name.split(".", 1)[0]
            if root in MONGO_ROOTS or any(name.startswith(x) for x in COMPAT):
                hits.append({
                    "path": rel(path),
                    "line": getattr(node, "lineno", 0),
                    "scope": scope(path),
                    "module": name,
                    "reachable_from_server_static": False,
                })

server = BACKEND / "server.py"
reachable = set()
queue = deque([server]) if server.exists() else deque()
while queue:
    path = queue.popleft()
    if path in reachable:
        continue
    reachable.add(path)
    for imported in imports.get(path, set()):
        candidate = module_paths.get(imported)
        if candidate and candidate not in reachable:
            queue.append(candidate)
        parts = imported.split(".")
        while len(parts) > 1:
            parts.pop()
            candidate = module_paths.get(".".join(parts))
            if candidate and candidate not in reachable:
                queue.append(candidate)

for row in hits:
    row["reachable_from_server_static"] = str(ROOT / row["path"] in reachable).lower()

with (OUT / "python_mongo_imports.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=["path", "line", "scope", "module", "reachable_from_server_static"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(sorted(hits, key=lambda r: (r["scope"], r["path"], r["line"])))

manifest_rows = []
manifest_names = {"requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile", "poetry.lock"}
for path in ROOT.rglob("*"):
    if not path.is_file() or path.name not in manifest_names:
        continue
    if set(path.relative_to(ROOT).parts) & SKIP:
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    for number, line in enumerate(text.splitlines(), 1):
        if re.search(r"\b(pymongo|motor|bson)\b", line, re.I):
            manifest_rows.append({"path": rel(path), "line": number, "scope": scope(path), "text": line.strip()[:500]})

with (OUT / "mongo_manifest_declarations.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=["path", "line", "scope", "text"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(manifest_rows)

try:
    pymongo_dist = md.distribution("pymongo")
    package = {
        "installed": True,
        "name": pymongo_dist.metadata.get("Name", "pymongo"),
        "version": pymongo_dist.version,
        "location": str(pymongo_dist.locate_file("")),
        "requires": sorted(pymongo_dist.requires or []),
    }
except md.PackageNotFoundError:
    package = {"installed": False, "name": "pymongo", "version": None, "location": None, "requires": []}

reverse = []
for dist in md.distributions():
    for requirement in dist.requires or []:
        if re.match(r"\s*pymongo(?:\s|\[|[<>=!~;]|$)", requirement, re.I):
            reverse.append({
                "distribution": dist.metadata.get("Name", ""),
                "version": dist.version,
                "requirement": requirement,
            })

with (OUT / "pymongo_reverse_dependencies.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=["distribution", "version", "requirement"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(sorted(reverse, key=lambda x: x["distribution"].lower()))

loaded = [x for x in (OUT / "runtime_loaded_mongo_paths.txt").read_text(encoding="utf-8").splitlines() if x]
connections = [x for x in (OUT / "runtime_mongo_connections.txt").read_text(encoding="utf-8").splitlines() if x]
active_direct = [r for r in hits if r["scope"] == "PRODUCTION_RUNTIME_CANDIDATE" and r["module"].split(".", 1)[0] in MONGO_ROOTS]
active_reachable = [r for r in active_direct if r["reachable_from_server_static"] == "true"]
active_manifest = [r for r in manifest_rows if r["scope"] == "PRODUCTION_RUNTIME_CANDIDATE"]

if reverse:
    provenance = "REQUIRED_BY_INSTALLED_DISTRIBUTION"
elif active_manifest:
    provenance = "DECLARED_BY_ACTIVE_PROJECT_MANIFEST"
else:
    provenance = "NOT_DECLARED_OR_REVERSE_REQUIRED_IN_AUDITED_SCOPE"

if loaded:
    usage = "POSITIVE_PACKAGE_PATH_EVIDENCE_IN_PROCESS"
elif connections:
    usage = "POSITIVE_MONGO_PORT_CONNECTION_EVIDENCE"
else:
    usage = "NO_POSITIVE_LIVE_USE_EVIDENCE_OBSERVED_NOT_CONCLUSIVE"

summary = {
    "result": "PASS",
    "runtime": {
        "pid": PID,
        "interpreter": sys.executable,
        "loaded_mongo_paths": len(loaded),
        "mongo_port_connections": len(connections),
        "usage_evidence": usage,
    },
    "package": package,
    "provenance": {
        "reverse_dependencies": len(reverse),
        "active_manifest_declarations": len(active_manifest),
        "assessment": provenance,
    },
    "repository": {
        "python_files_scanned": len(files),
        "static_reachable_files_from_server": len(reachable),
        "mongo_import_hits_total": len(hits),
        "active_direct_mongo_import_hits": len(active_direct),
        "active_reachable_mongo_import_hits": len(active_reachable),
        "parse_errors": len(parse_errors),
    },
    "decision": {
        "pymongo_removal_safe": False,
        "package_removal_authorized": False,
        "template_removal_authorized": False,
        "repository_change_authorized": False,
        "recommended_action": "KEEP_INSTALLED_PENDING_PLATFORM_OWNERSHIP_AND_STARTUP_IMPACT_PROOF",
        "priority": "EDARSAHUB_STABILITY_AND_OPERATION",
    },
    "safety": {
        "packages_installed": 0,
        "packages_removed": 0,
        "environment_files_read": 0,
        "proc_environ_read": 0,
        "sql_connections": 0,
        "application_imports": 0,
        "application_processes_started": 0,
    },
}

(OUT / "mongo_package_provenance.json").write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(OUT / "mongo_impact_audit.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(OUT / "parse_errors.json").write_text(json.dumps(parse_errors, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

lines = [
    "# EDARSAHUB Mongo Impact Audit",
    "",
    f"- Result: `{summary['result']}`",
    f"- Runtime PID: `{PID}`",
    f"- PyMongo installed: `{package['installed']}`",
    f"- PyMongo version: `{package['version']}`",
    f"- Provenance assessment: `{provenance}`",
    f"- Runtime usage evidence: `{usage}`",
    f"- Reverse dependencies: `{len(reverse)}`",
    f"- Active direct Mongo imports: `{len(active_direct)}`",
    f"- Active reachable Mongo imports: `{len(active_reachable)}`",
    "- Package removal authorized: `False`",
    "- Template removal authorized: `False`",
    "- Priority: `EDARSAHUB_STABILITY_AND_OPERATION`",
    "",
    "## Decision",
    "",
    "Do not uninstall `pymongo`, remove `bson`, delete Emergent templates, or change runtime compatibility code based only on package presence.",
    "Any cleanup requires platform ownership proof, startup and endpoint validation, and an exact rollback.",
]
(OUT / "mongo_impact_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
PY

STATUS_AFTER="$(git status --porcelain=v1 --untracked-files=all)"
[[ "$STATUS_AFTER" == "$STATUS_BEFORE" ]] || fail 40 'el estado del repositorio cambio durante la auditoria'

(
  cd "$OUT_DIR"
  find . -maxdepth 1 -type f ! -name checksums.sha256 -printf '%f\n' \
    | LC_ALL=C sort \
    | xargs sha256sum > checksums.sha256
  sha256sum -c checksums.sha256
)

printf 'REPOSITORY_STATE_UNCHANGED=true\n'
printf 'AUDIT_RESULT=PASS\n'
printf 'REMOVAL_AUTHORIZED=false\n'
printf 'RECOMMENDED_ACTION=KEEP_INSTALLED_PENDING_PLATFORM_OWNERSHIP_AND_STARTUP_IMPACT_PROOF\n'
printf 'REPORT_MD=%s/mongo_impact_audit.md\n' "$OUT_DIR"
printf 'REPORT_JSON=%s/mongo_impact_audit.json\n' "$OUT_DIR"
printf 'CHECKSUMS=%s/checksums.sha256\n' "$OUT_DIR"
