#!/usr/bin/env bash
set -e

cd /app/backend

echo "=========================================="
echo "DRY-RUN BACKFILL GAPS JUNIO 2026"
echo "NO MODIFICA DATOS"
echo "=========================================="

TARGETS=(
  "130MID:2026-06-05"
  "130QRO:2026-06-05"
  "CIENFUEGOS:2026-06-04"
  "CIENFUEGOS:2026-06-05"
  "ORIGEN:2026-06-05"
)

for item in "${TARGETS[@]}"
do
  UNIDAD="${item%%:*}"
  FECHA="${item##*:}"

  echo ""
  echo "------------------------------------------"
  echo "Unidad: $UNIDAD Fecha: $FECHA"
  echo "------------------------------------------"

  if [ -f /app/backend/modules/comercial_v2/sync_comercial_edarsahub.py ]; then
    python /app/backend/modules/comercial_v2/sync_comercial_edarsahub.py \
      --unidad "$UNIDAD" \
      --fecha "$FECHA" \
      --dry-run \
    || true
  elif [ -f /app/backend/sync_comercial_edarsahub.py ]; then
    python /app/backend/sync_comercial_edarsahub.py \
      --unidad "$UNIDAD" \
      --fecha "$FECHA" \
      --dry-run \
    || true
  else
    echo "NO EXISTE SCRIPT sync_comercial_edarsahub.py"
  fi
done

echo ""
echo "DRY-RUN COMPLETADO"
