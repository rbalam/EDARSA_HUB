#!/usr/bin/env bash
set -euo pipefail
BACK_DIR="/app/backend"; OUT_DIR="/app/auditorias_p5"; TS="$(date +%Y%m%d_%H%M%S)"
RAW="$OUT_DIR/FASE12_FIX_MENOR_ROTATE_SECRET_${TS}.txt"
TARGET="$BACK_DIR/scripts/rotate_server_secret_key.py"
mkdir -p "$OUT_DIR" /app/scripts; cd /app || exit 1
[ -f "$TARGET" ] || { echo "ERROR: no existe $TARGET"; exit 1; }
echo "FASE 12 - FIX MENOR rotate_server_secret_key.py $(date)" | tee "$RAW"
echo "===== 1) AUDITORIA PREVIA =====" | tee -a "$RAW"
grep -n "get_mongo_db" "$TARGET" | tee -a "$RAW" || true
echo "===== 2) BACKUP =====" | tee -a "$RAW"
cp "$TARGET" "${TARGET}.bak_${TS}"; echo "BACKUP: ${TARGET}.bak_${TS}" | tee -a "$RAW"
echo "===== 3) PARCHE EXACTO =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
from pathlib import Path
p = Path("/app/backend/scripts/rotate_server_secret_key.py")
txt = p.read_text(encoding="utf-8")
old="from core.db import get_mongo_db"; new="from core.mongo_compat import get_mongo_db"
co=txt.count(old); cn=txt.count(new)
print(f"COUNT_OLD={co}"); print(f"COUNT_NEW={cn}")
if co==0 and cn==1: print("NO CHANGE: ya estaba corregido"); raise SystemExit(0)
if co!=1: print("ABORTADO: no hay exactamente 1 coincidencia"); raise SystemExit(2)
p.write_text(txt.replace(old,new,1),encoding="utf-8"); print("PATCHED")
PY
echo "===== 4) VALIDACION =====" | tee -a "$RAW"
python3 -m py_compile "$TARGET" | tee -a "$RAW"
grep -n "from core.mongo_compat import get_mongo_db" "$TARGET" | tee -a "$RAW" || true
echo "RAW_REPORT=$RAW"; echo "OK - FIX MENOR listo"
