#!/usr/bin/env bash
set -e

OUT="/app/auditorias_canonicas/RESULTADO_CANONICAS_$(date +%Y%m%d_%H%M%S).txt"

{
echo "===== STATUS ====="
git status --short

echo
echo "===== TABLAS/VISTAS CANONICAS USADAS EN CODIGO ====="
grep -RniE "vw_|Sistema_|Servidores_|Comercial_KPIs|Comercial_SyncLog|Unidad|unidad_negocio_pk|Corporate|Catalogo|RBAC|Roles|Permisos|Compras_|Finanzas_|Inventarios_|Alertas_|Scheduler_" backend frontend/src \
  --exclude-dir=__pycache__ \
  --exclude-dir=node_modules \
  --exclude-dir=graphify-out \
  --exclude-dir=auditorias_p1 \
  --exclude-dir=auditorias_p2 \
  --exclude-dir=auditorias_p3 \
  --exclude-dir=auditorias_p4 \
  --exclude-dir=auditorias_p5 \
  --exclude-dir=htmlcov \
  --exclude-dir=.ruff_cache \
  --exclude='*.bak*' \
  --exclude='*.backup*' \
  --exclude='*backup*' \
  --exclude='*.zip' \
  --exclude='*.pyc' | head -500 || true

echo
echo "===== POSIBLES TABLAS LEGACY / NO CANONICAS ACTIVAS ====="
grep -RniE "db\.|db\[|server_sucursales_config|kpis_cache|server_status|alerts|script_logs|inventario_diferencias_detalle|consultas_custom|scripts_pendientes|users\.find|roles\.find|empresas\.find" backend \
  --exclude-dir=__pycache__ \
  --exclude-dir=graphify-out \
  --exclude-dir=auditorias_p1 \
  --exclude-dir=auditorias_p2 \
  --exclude-dir=auditorias_p3 \
  --exclude-dir=auditorias_p4 \
  --exclude-dir=auditorias_p5 \
  --exclude-dir=htmlcov \
  --exclude-dir=.ruff_cache \
  --exclude='*.bak*' \
  --exclude='*.backup*' \
  --exclude='*backup*' \
  --exclude='*.zip' \
  --exclude='*.pyc' | head -500 || true

echo
echo "===== CONEXIONES DIRECTAS / NO CENTRALIZADAS ====="
grep -RniE "pymssql\.connect|pyodbc\.connect|execute_sql_query\(|execute_sql_query_params\(|get_edarsahub_connection|EDARSAHUB_SQL_HOST|EDARSAHUB_SQL_USER|EDARSAHUB_SQL_PASSWORD" backend \
  --exclude-dir=__pycache__ \
  --exclude-dir=graphify-out \
  --exclude-dir=auditorias_p1 \
  --exclude-dir=auditorias_p2 \
  --exclude-dir=auditorias_p3 \
  --exclude-dir=auditorias_p4 \
  --exclude-dir=auditorias_p5 \
  --exclude-dir=htmlcov \
  --exclude-dir=.ruff_cache \
  --exclude='*.bak*' \
  --exclude='*.backup*' \
  --exclude='*backup*' \
  --exclude='*.zip' \
  --exclude='*.pyc' | head -500 || true

echo
echo "===== COMPILACION IMPACTO ====="
python3 -m py_compile \
backend/server.py \
backend/modules/comercial/repository.py \
backend/modules/comercial/kpis_repository.py \
backend/modules/comercial/cache_service.py \
backend/core/scheduler/scheduler_manager.py \
backend/core/scheduler/routes.py

echo "COMPILE_OK"

echo
echo "===== LOG ====="
git log --oneline -8
} | tee "$OUT"

echo
echo "REPORTE_GENERADO=$OUT"
