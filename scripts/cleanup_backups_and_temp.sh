#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
TS="$(date +%Y%m%d_%H%M%S)"
REPORT_DIR="$ROOT/auditorias_p5"
REPORT_FILE="$REPORT_DIR/CLEANUP_BACKUPS_TEMP_${TS}.txt"

mkdir -p "$REPORT_DIR"

echo "==================================================" | tee "$REPORT_FILE"
echo "AUDITORIA Y LIMPIEZA DE RESPALDOS / TEMPORALES" | tee -a "$REPORT_FILE"
echo "Fecha: $(date)" | tee -a "$REPORT_FILE"
echo "Root: $ROOT" | tee -a "$REPORT_FILE"
echo "==================================================" | tee -a "$REPORT_FILE"

echo "" | tee -a "$REPORT_FILE"
echo "==== 1) AUDITORIA DE TAMAÑOS ====" | tee -a "$REPORT_FILE"
du -sh "$ROOT"/* 2>/dev/null | sort -h | tee -a "$REPORT_FILE" || true

echo "" | tee -a "$REPORT_FILE"
echo "==== 2) ARCHIVOS GRANDES (>20MB) ====" | tee -a "$REPORT_FILE"
find "$ROOT" -type f -size +20M \
  ! -path "$ROOT/backend/*" \
  ! -path "$ROOT/frontend/*" \
  2>/dev/null | sort | tee -a "$REPORT_FILE" || true

echo "" | tee -a "$REPORT_FILE"
echo "==== 3) ZIPS / BACKUPS / BSON ====" | tee -a "$REPORT_FILE"
find "$ROOT" -type f \( \
  -iname "*.zip" -o \
  -iname "*.bson" -o \
  -iname "*.tar" -o \
  -iname "*.gz" -o \
  -iname "backup_*" -o \
  -iname "*.bak" \
\) 2>/dev/null | sort | tee -a "$REPORT_FILE" || true

echo "" | tee -a "$REPORT_FILE"
echo "==== 4) TEMPORALES / CACHE ====" | tee -a "$REPORT_FILE"
find "$ROOT" \( \
  -type d -name "__pycache__" -o \
  -type d -name ".pytest_cache" -o \
  -type d -name ".mypy_cache" -o \
  -type d -name ".ruff_cache" -o \
  -type d -name "dist" -o \
  -type d -name "build" -o \
  -type d -name ".next" -o \
  -type d -name "coverage" -o \
  -type d -name ".cache" \
\) 2>/dev/null | sort | tee -a "$REPORT_FILE" || true

echo "" | tee -a "$REPORT_FILE"
echo "==== 5) LOGS / TMP / OLD ====" | tee -a "$REPORT_FILE"
find "$ROOT" -type f \( \
  -iname "*.log" -o \
  -iname "*.tmp" -o \
  -iname "*.temp" -o \
  -iname "*_old*" -o \
  -iname "*_backup*" -o \
  -iname "*_copy*" \
\) 2>/dev/null | sort | tee -a "$REPORT_FILE" || true

# --------------------------------------------------
# CONSERVAR EL ULTIMO BACKUP DE BD Y EL ULTIMO BACKUP DE CODIGO
# --------------------------------------------------
LATEST_DB_BACKUP="$(find "$ROOT" -type f \( -iname "*backup*db*.zip" -o -iname "*backup_db*.zip" -o -iname "*db*.zip" \) 2>/dev/null | sort | tail -n 1 || true)"
LATEST_CODE_BACKUP="$(find "$ROOT" -type f \( -iname "*backup*codigo*.zip" -o -iname "*backup_codigo*.zip" -o -iname "*codigo*.zip" \) 2>/dev/null | sort | tail -n 1 || true)"

echo "" | tee -a "$REPORT_FILE"
echo "==== 6) RESPALDOS A CONSERVAR ====" | tee -a "$REPORT_FILE"
echo "ULTIMO BACKUP BD: ${LATEST_DB_BACKUP:-NO ENCONTRADO}" | tee -a "$REPORT_FILE"
echo "ULTIMO BACKUP CODIGO: ${LATEST_CODE_BACKUP:-NO ENCONTRADO}" | tee -a "$REPORT_FILE"

# --------------------------------------------------
# LIMPIEZA SEGURA
# --------------------------------------------------
echo "" | tee -a "$REPORT_FILE"
echo "==== 7) LIMPIEZA DE CACHE / TEMPORALES ====" | tee -a "$REPORT_FILE"

find "$ROOT" \( \
  -type d -name "__pycache__" -o \
  -type d -name ".pytest_cache" -o \
  -type d -name ".mypy_cache" -o \
  -type d -name ".ruff_cache" -o \
  -type d -name "dist" -o \
  -type d -name "build" -o \
  -type d -name ".next" -o \
  -type d -name "coverage" -o \
  -type d -name ".cache" \
\) \
! -path "$ROOT/backend/*" \
! -path "$ROOT/frontend/*" \
-print -exec rm -rf {} + 2>/dev/null | tee -a "$REPORT_FILE" || true

find "$ROOT" -type f \( \
  -iname "*.log" -o \
  -iname "*.tmp" -o \
  -iname "*.temp" \
\) \
! -path "$ROOT/backend/*" \
! -path "$ROOT/frontend/*" \
-print -delete 2>/dev/null | tee -a "$REPORT_FILE" || true

# --------------------------------------------------
# LIMPIEZA DE RESPALDOS VIEJOS
# deja solo el último backup de BD y el último backup de código
# --------------------------------------------------
echo "" | tee -a "$REPORT_FILE"
echo "==== 8) LIMPIEZA DE RESPALDOS VIEJOS ====" | tee -a "$REPORT_FILE"

while IFS= read -r file; do
  [ -z "$file" ] && continue

  if [[ "$file" == "$LATEST_DB_BACKUP" ]] || [[ "$file" == "$LATEST_CODE_BACKUP" ]]; then
    echo "CONSERVADO: $file" | tee -a "$REPORT_FILE"
    continue
  fi

  # proteger código fuente activo
  if [[ "$file" == "$ROOT/backend/"* ]] || [[ "$file" == "$ROOT/frontend/"* ]]; then
    echo "PROTEGIDO: $file" | tee -a "$REPORT_FILE"
    continue
  fi

  echo "ELIMINADO: $file" | tee -a "$REPORT_FILE"
  rm -f "$file"
done < <(
  find "$ROOT" -type f \( \
    -iname "*.zip" -o \
    -iname "*.bson" -o \
    -iname "*.tar" -o \
    -iname "*.gz" -o \
    -iname "backup_*" -o \
    -iname "*.bak" \
  \) 2>/dev/null | sort
)

echo "" | tee -a "$REPORT_FILE"
echo "==== 9) ESPACIO FINAL ====" | tee -a "$REPORT_FILE"
du -sh "$ROOT" 2>/dev/null | tee -a "$REPORT_FILE" || true

echo "" | tee -a "$REPORT_FILE"
echo "OK - limpieza completada" | tee -a "$REPORT_FILE"
echo "Reporte: $REPORT_FILE" | tee -a "$REPORT_FILE"
