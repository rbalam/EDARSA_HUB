#!/usr/bin/env bash
set -uo pipefail

OUTDIR="/app/auditorias_p5"
TS="$(date +%Y%m%d_%H%M%S)"
REPORT="$OUTDIR/P0_AUDITORIA_MONGO_RESIDUAL_VIVO_${TS}.txt"
mkdir -p "$OUTDIR"
cd /app/backend || exit 1

{
  echo "=================================================="
  echo "P0 AUDITORIA MONGO RESIDUAL VIVO  |  $(date)"
  echo "=================================================="
  echo

  echo "===== 1) IMPORTS / CLIENTES MONGO ACTIVOS ====="
  grep -RniE "from pymongo|import pymongo|MongoClient|motor\.|AsyncIOMotor" . --include="*.py" || true
  echo

  echo "===== 6) MONGO RESIDUAL POR MODULO (db.<col>) ====="
  python3 - <<'PY'
from pathlib import Path
import re
from collections import defaultdict
root = Path("/app/backend")
hits = defaultdict(set)
for p in root.rglob("*.py"):
    try: txt = p.read_text(encoding="utf-8")
    except Exception: continue
    for r in set(re.findall(r'db\.([A-Za-z_][A-Za-z0-9_]*)', txt)):
        hits[str(p).replace("/app/backend/","")].add(r)
for mod in sorted(hits):
    print(f"[{mod}]")
    for r in sorted(hits[mod]):
        print(f"  - {r}")
PY
  echo

  echo "===== 7) COLECCIONES MAS REFERENCIADAS ====="
  python3 - <<'PY'
from pathlib import Path
import re
from collections import Counter
root = Path("/app/backend")
c = Counter()
for p in root.rglob("*.py"):
    try: txt = p.read_text(encoding="utf-8")
    except Exception: continue
    c.update(re.findall(r'db\.([A-Za-z_][A-Za-z0-9_]*)', txt))
for name, qty in c.most_common(120):
    print(f"{name}: {qty}")
PY
  echo
  echo "===== FIN ====="
} > "$REPORT" 2>&1

echo "REPORTE=$REPORT"
wc -l "$REPORT"
