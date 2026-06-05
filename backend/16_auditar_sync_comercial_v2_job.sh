#!/usr/bin/env bash
set -e

FILE="/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py"

echo "=== P1 - AUDITORIA sync_comercial_v2_job.py ==="

if [ ! -f "$FILE" ]; then
  echo "ERROR: No existe $FILE"
  exit 1
fi

echo ""
echo "=== HARDCODES UNIDADES ==="
grep -nE "130MID|130QRO|ESTELAR|CIENFUEGOS|ORIGEN|130° MERIDA|130° QUERETARO|LA ESTELAR" "$FILE" || echo "(ninguno)"

echo ""
echo "=== DRY RUN ==="
grep -nEi "dry_run|DRY_RUN|--dry|simulate|preview" "$FILE" || echo "(ninguno)"

echo ""
echo "=== REFERENCIAS A UNIDADES SERVICE ==="
grep -nE "UnidadesService|unidades_service|unidad_negocio_id|Unidades_Negocio" "$FILE" || echo "(ninguno)"

echo ""
echo "=== RESUMEN ==="
python3 - <<'PY'
from pathlib import Path

p = Path("/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py")
txt = p.read_text(errors="ignore")

terms = [
    "130MID",
    "130QRO",
    "ESTELAR",
    "CIENFUEGOS",
    "ORIGEN",
    "130° MERIDA",
    "130° QUERETARO",
    "LA ESTELAR",
]

print("HARDCODES:")
for t in terms:
    c = txt.count(t)
    if c:
        print(f"  {t}: {c}")

print()
print("OTROS:")
print(f"  dry_run: {txt.lower().count('dry_run')}")
print(f"  unidad_negocio_id: {txt.count('unidad_negocio_id')}")
print(f"  UnidadesService: {txt.count('UnidadesService')}")
PY

echo ""
echo "=== FIN AUDITORIA ==="
