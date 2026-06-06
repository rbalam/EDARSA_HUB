#!/usr/bin/env bash
set -euo pipefail

echo "=== EDARSAHUB WORKSPACE VALIDATION ==="
pwd || true
git status || true
git branch || true
git diff --stat || true

echo "=== Buscar inteligencia comercial ==="
find ./backend ./frontend ./docs -iname "*inteligencia*" -o -iname "*comercial*sync*" 2>/dev/null || true

echo "=== Grep referencias clave ==="
grep -Rni "inteligencia_comercial_sync\|Comercial_KPIs_Diarios_v2\|Comercial_Ventas_Dia_Abiertas_v2\|Sync_Sales\|Sync_PAX_Detalle\|View_Inteligencia_Comercial" ./backend ./frontend ./docs 2>/dev/null || true

echo "=== Scheduler jobs ==="
ls -la ./backend/core/scheduler/jobs || true

echo "=== Scheduler config ==="
grep -Rni "sla_processor\|notifications_dispatcher\|auditorias_scheduler\|pedidos_detector\|inteligencia" ./backend/core/scheduler 2>/dev/null || true

echo "=== Frontend BI ==="
grep -Rni "ReportesBI\|Inteligencia Comercial\|reportes-bi\|portal-proveedores" ./frontend/src 2>/dev/null || true
