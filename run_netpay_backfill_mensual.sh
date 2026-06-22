#!/usr/bin/env bash
set -euo pipefail

cd /app/netpay_robot_edarsahub/netpay_robot_edarsahub || exit 1

PY="/usr/local/bin/python"
LOG="/app/netpay_backfill_mensual_$(date +%Y%m%d_%H%M%S).log"

echo "LOG=$LOG"

{
  echo "===== INICIO BACKFILL MENSUAL NETPAY $(date) ====="
  echo "RANGO REAL CON DATOS NETPAY: 2025-12-18 a 2026-06-17"

  "$PY" - <<'PY'
import sys
print("PYTHON:", sys.executable)
import click, dotenv, openpyxl, pymssql
print("DEPENDENCIAS_OK")
PY

  for RANGE in \
    "2025-12-18 2025-12-31" \
    "2026-01-01 2026-01-31" \
    "2026-02-01 2026-02-28" \
    "2026-03-01 2026-03-31" \
    "2026-04-01 2026-04-30" \
    "2026-05-01 2026-05-31" \
    "2026-06-01 2026-06-17"
  do
    FROM=$(echo "$RANGE" | awk '{print $1}')
    TO=$(echo "$RANGE" | awk '{print $2}')

    echo ""
    echo "============================================================"
    echo "BLOQUE MENSUAL: $FROM a $TO"
    echo "============================================================"

    echo ""
    echo "===== DETALLE_TRANSACCIONES $FROM a $TO ====="
    "$PY" -B -m netpay_robot.cli run \
      --report-type DETALLE_TRANSACCIONES \
      --date-from "$FROM" \
      --date-to "$TO"

    STATUS=$?
    if [ $STATUS -ne 0 ]; then
      echo "ERROR_BACKFILL_TRANSACCIONES rango=$FROM..$TO status=$STATUS"
      exit $STATUS
    fi

    echo ""
    echo "===== DETALLE_DEPOSITOS_MOVIMIENTOS $FROM a $TO ====="
    "$PY" -B -m netpay_robot.cli run \
      --report-type DETALLE_DEPOSITOS_MOVIMIENTOS \
      --date-from "$FROM" \
      --date-to "$TO"

    STATUS=$?
    if [ $STATUS -ne 0 ]; then
      echo "ERROR_BACKFILL_DEPOSITOS rango=$FROM..$TO status=$STATUS"
      exit $STATUS
    fi

    echo "BLOQUE_OK $FROM a $TO"
  done

  echo ""
  echo "===== FIN BACKFILL MENSUAL NETPAY $(date) ====="
} 2>&1 | tee "$LOG"
