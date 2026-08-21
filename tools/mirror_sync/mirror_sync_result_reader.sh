#!/usr/bin/env bash
set -euo pipefail

LATEST="/app/.git/mirror-sync/reporting/latest.json"

if [ ! -f "$LATEST" ]; then
    echo "MIRROR_RESULT_AVAILABLE=NO"
    exit 0
fi

echo "MIRROR_RESULT_AVAILABLE=YES"

python3 - "$LATEST" <<'PY'
import json
import sys

path = sys.argv[1]

with open(path, "r", encoding="utf-8") as fh:
    data = json.load(fh)

print(f"REQUEST_ID={data.get('request_id') or ''}")
print(f"BRANCH={data.get('branch') or ''}")
print(f"HEAD_BEFORE={data.get('head_before') or ''}")
print(f"HEAD_AFTER={data.get('head_after') or ''}")
print(f"DEVELOPMENT_HEAD={data.get('development_head') or ''}")
print(f"MIRROR_HEAD={data.get('mirror_head') or ''}")
print(f"CONVERGED={'YES' if data.get('converged') else 'NO'}")
print(
    "PRODUCTION_TOUCHED="
    + ("YES" if data.get("production_touched") else "NO")
)

files = data.get("files") or {}

for key in ("added", "modified", "deleted"):
    values = files.get(key) or []
    print(f"{key.upper()}_COUNT={len(values)}")

print("SUMMARY=" + str(data.get("summary") or ""))
PY
