# Auditoría Comercial routes.py SQL-first

Fecha: Thu Jun  4 20:20:30 UTC 2026

## Objetivo

Auditar el módulo Comercial para identificar endpoints que todavía puedan usar conexiones live para pintar tableros, KPIs o reportes.

Este script no modifica código.

## Reglas

- No activar políticas todavía.
- No modificar routes.py.
- No modificar Comercial.js.
- No tocar frontend.
- No tocar sync/backfill/jobs.
- Separar conexiones permitidas de conexiones prohibidas.

## Clasificación

Permitido:
- sync
- backfill
- resync
- job
- diagnóstico técnico autorizado

Prohibido:
- dashboard
- KPI
- resumen
- tablero
- reporte visual
- endpoint usado por frontend para pintar pantalla con conexión live
## Resumen automático
```text
Archivos escaneados: 89
Endpoints detectados: 170
Hallazgos de conexión: 297

Archivos:
- /app/backend/core/policies/no_live_dashboard_policy.py
- /app/backend/core/scheduler/jobs/inteligencia_comercial_status_job.py
- /app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py
- /app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py
- /app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py
- /app/backend/core/scheduler/jobs/sync_comercial_v2_job.py
- /app/backend/core/scheduler/jobs/sync_nightly_comercial_job.py
- /app/backend/core/scheduler/jobs/sync_short_comercial_job.py
- /app/backend/modules/comercial/__init__.py
- /app/backend/modules/comercial/adapters.py
- /app/backend/modules/comercial/alertas_margen_repository.py
- /app/backend/modules/comercial/alertas_margen_service.py
- /app/backend/modules/comercial/cache_service.py
- /app/backend/modules/comercial/crm_router.py
- /app/backend/modules/comercial/historical_kpis_repository.py
- /app/backend/modules/comercial/inteligencia_comercial_routes.py
- /app/backend/modules/comercial/inteligencia_repository.py
- /app/backend/modules/comercial/kpis_repository.py
- /app/backend/modules/comercial/queries/__init__.py
- /app/backend/modules/comercial/queries/hub.py
- /app/backend/modules/comercial/queries/mpro.py
- /app/backend/modules/comercial/queries/softrestaurant.py
- /app/backend/modules/comercial/rentabilidad.py
- /app/backend/modules/comercial/repository.py
- /app/backend/modules/comercial/routes.py
- /app/backend/modules/comercial/routes_alertas_margen.py
- /app/backend/modules/comercial/routes_competidores_enterprise.py
- /app/backend/modules/comercial/routes_listas_competidores.py
- /app/backend/modules/comercial/routes_precios_sugeridos.py
- /app/backend/modules/comercial/routes_pricing_ai.py
... y 59 más

Endpoints por clasificación:
- REVISAR: 94
- VISUAL_REVISAR_FUENTE: 73
- PERMITIDO_SYNC_BACKFILL_JOB: 3

Hallazgos por clasificación:
- REVISAR_CONEXION: 205
- PROHIBIDO_LIVE_VISUAL: 56
- PERMITIDO_SYNC_BACKFILL_JOB: 36
```
## Endpoints visuales con posible live
```text

=== VISUAL_REVISAR_FUENTE (73 endpoints) ===
GET /kpis | crm_router.py | UNKNOWN
GET /kpis | inteligencia_comercial_routes.py | UNKNOWN
GET /ventas-comparativo | inteligencia_comercial_routes.py | UNKNOWN
GET /kpis-por-unidad | inteligencia_comercial_routes.py | UNKNOWN
GET /comercial/tablero-ejecutivo | routes.py | UNKNOWN
GET /comercial/ventas-tiempo/{server_id} | routes.py | UNKNOWN
GET /comercial/reporte-pax/{server_id} | routes.py | UNKNOWN
GET /comercial/dashboard/{server_id} | routes.py | UNKNOWN
GET /comercial/ventas-tiempo/{unit_id} | routes.py | UNKNOWN
POST /analizar-producto | routes_pricing_ai.py | UNKNOWN
POST /sugerir-comparables | routes_pricing_ai.py | UNKNOWN
POST /generar-justificacion | routes_pricing_ai.py | UNKNOWN
POST /analizar-benchmark | routes_pricing_ai.py | UNKNOWN
GET /analisis/{analisis_id} | routes_pricing_ai.py | UNKNOWN
GET /health | routes_pricing_ai.py | UNKNOWN
GET /dashboard/metricas | routes_pricing_ai.py | UNKNOWN
GET /dashboard/estadisticas-competidores | routes_pricing_ai.py | UNKNOWN
GET /perfil-unidad | routes_pricing_ia.py | UNKNOWN
GET /perfil-unidad/{unidad_negocio_id} | routes_pricing_ia.py | UNKNOWN
POST /perfil-unidad | routes_pricing_ia.py | UNKNOWN
... y 53 más
```
## Endpoints permitidos sync/backfill/job
```text
GET /sync-status | /app/backend/modules/comercial/inteligencia_comercial_routes.py | UNKNOWN
GET /sync-status | /app/backend/modules/comercial_v2/routes.py | UNKNOWN
GET /sync-status | /app/backend/modules/costos_margenes/routes.py | UNKNOWN
```
## Hallazgos de conexión por archivo (PROHIBIDO_LIVE_VISUAL)
```text
=== PROHIBIDO_LIVE_VISUAL: 56 hallazgos en 14 archivos ===

===== /app/backend/core/policies/no_live_dashboard_policy.py (2 hallazgos) =====
L13 | pyodbc.connect | "pyodbc.connect(",
L14 | pymssql.connect | "pymssql.connect(",

===== /app/backend/modules/comercial/historical_kpis_repository.py (1 hallazgos) =====
L95 | execute_sql_query | return execute_sql_query(

===== /app/backend/modules/comercial/routes.py (4 hallazgos) =====
L3598 | execute_sql_query | result_ventas_reales = execute_sql_query(
L3646 | execute_sql_query | ventas_actual = execute_sql_query(
L3884 | execute_sql_query | result_ventas_reales = execute_sql_query(
L3924 | execute_sql_query | ventas_actual = execute_sql_query(

===== /app/backend/modules/comercial/services/pricing_ai_service.py (4 hallazgos) =====
L151 | execute_sql_query | execute_sql_query(*conn, ddl)
L185 | execute_sql_query | result = execute_sql_query(*conn, query)
L478 | execute_sql_query | execute_sql_query(*conn, insert_query)
L525 | execute_sql_query | result = execute_sql_query(*conn, query)

===== /app/backend/modules/comercial/services/pricing_sugerido_service.py (5 hallazgos) =====
L99 | execute_sql_query | result = execute_sql_query(*conn, query_receta)
L118 | execute_sql_query | result_insumos = execute_sql_query(*conn, query_insumos)
L149 | execute_sql_query | result = execute_sql_query(*conn, query)
L178 | execute_sql_query | result = execute_sql_query(*conn, query)
L541 | execute_sql_query | result = execute_sql_query(*conn, query)

===== /app/backend/modules/compras/historical_kpis_repository.py (1 hallazgos) =====
L50 | pytds.connect | return pytds.connect(

===== /app/backend/modules/costos_margenes/repository.py (18 hallazgos) =====
L60 | execute_sql_query | productos_result = execute_sql_query(*conn, productos_query)
L64 | execute_sql_query | insumos_result = execute_sql_query(*conn, insumos_query)
L68 | execute_sql_query | recetas_result = execute_sql_query(*conn, recetas_query)
L72 | execute_sql_query | elaborados_result = execute_sql_query(*conn, elaborados_query)
L186 | execute_sql_query | count_result = execute_sql_query(*conn, count_query)
L232 | execute_sql_query | data_result = execute_sql_query(*conn, data_query) or []
L318 | execute_sql_query | result = execute_sql_query(*conn, query)
L348 | execute_sql_query | result = execute_sql_query(*conn, query)
L378 | execute_sql_query | receta_result = execute_sql_query(*conn, receta_query) or []
L444 | execute_sql_query | insumo_result = execute_sql_query(*conn, insumo_query)
L463 | execute_sql_query | insumo_result = execute_sql_query(*conn, producto_query)
L499 | execute_sql_query | elaborado_result = execute_sql_query(*conn, elaborado_query) or []
L615 | execute_sql_query | result = execute_sql_query(*conn, count_query)
L626 | execute_sql_query | sistema_result = execute_sql_query(*conn, sistema_query) or []
L638 | execute_sql_query | servidor_result = execute_sql_query(*conn, servidor_query) or []
... 3 adicionales

===== /app/backend/modules/costos_margenes/repository_precios.py (9 hallazgos) =====
L103 | execute_sql_query | result = execute_sql_query(*conn, query)
L246 | execute_sql_query | execute_sql_query(*conn, query)
L330 | execute_sql_query | execute_sql_query(*conn, query)
L355 | execute_sql_query | result = execute_sql_query(*conn, query)
L385 | execute_sql_query | count_result = execute_sql_query(*conn, count_query)
L400 | execute_sql_query | result = execute_sql_query(*conn, query)
L512 | execute_sql_query | execute_sql_query(*conn, update_query)
L543 | execute_sql_query | result = execute_sql_query(*conn, query)
L649 | execute_sql_query | execute_sql_query(*conn, query)

===== /app/backend/modules/costos_margenes/routes.py (2 hallazgos) =====
L101 | execute_sql_query | user_result = execute_sql_query(*conn, user_query)
L116 | execute_sql_query | servers_result = execute_sql_query(*conn, servers_query) or []

===== /app/backend/modules/finanzas/historical_kpis_repository.py (1 hallazgos) =====
L49 | pytds.connect | return pytds.connect(

===== /app/backend/modules/tablajeria/dashboard_service.py (1 hallazgos) =====
L27 | pymssql.connect | return pymssql.connect(

===== /app/backend/scripts/actualizacion_kpi_proyeccion_comercial.py (1 hallazgos) =====
L25 | pymssql.connect | conn = pymssql.connect(

===== /app/backend/scripts/ddl_costos_alertas_001b.py (6 hallazgos) =====
L526 | execute_sql_query | execute_sql_query(*conn, ddl)
L530 | execute_sql_query | result = execute_sql_query(*conn, check_query)
L551 | execute_sql_query | execute_sql_query(*conn, DDL_UMBRALES_SEMILLA)
L555 | execute_sql_query | result = execute_sql_query(*conn, check_umbrales)
L591 | execute_sql_query | result = execute_sql_query(*conn, query)
L601 | execute_sql_query | umbrales = execute_sql_query(*conn, query_umbrales)

===== /app/backend/scripts/seed_ventas_consolidadas.py (1 hallazgos) =====
L33 | pymssql.connect | conn = pymssql.connect(

```
## Recomendación

No activar todavía una política global sin revisar endpoint por endpoint.

## Análisis de Hallazgos PROHIBIDO_LIVE_VISUAL

### Archivos Críticos (requieren migración a SQL-first):

| Archivo | Hallazgos | Tipo | Prioridad |
|---------|-----------|------|-----------|
| `costos_margenes/repository.py` | 18 | Backend visual | 🔴 P0 |
| `costos_margenes/repository_precios.py` | 9 | Backend visual | 🔴 P0 |
| `comercial/services/pricing_sugerido_service.py` | 5 | Backend visual | 🟡 P1 |
| `comercial/services/pricing_ai_service.py` | 4 | Backend visual | 🟡 P1 |
| `comercial/routes.py` | 4 | Backend visual | 🔴 P0 |
| `costos_margenes/routes.py` | 2 | Backend visual | 🟡 P1 |

### Archivos Permitidos (sync/scripts):

| Archivo | Hallazgos | Tipo | Acción |
|---------|-----------|------|--------|
| `no_live_dashboard_policy.py` | 2 | Política (documentación) | ✅ OK |
| `scripts/ddl_*.py` | 6 | DDL/Migración | ✅ OK |
| `scripts/seed_*.py` | 1 | Seed | ✅ OK |
| `scripts/actualizacion_*.py` | 1 | Script batch | ✅ OK |

### Archivos a Validar (pueden ser sync):

| Archivo | Hallazgos | Análisis |
|---------|-----------|----------|
| `compras/historical_kpis_repository.py` | 1 | Revisar si es para sync o dashboard |
| `finanzas/historical_kpis_repository.py` | 1 | Revisar si es para sync o dashboard |
| `tablajeria/dashboard_service.py` | 1 | 🔴 Nombre indica visual → MIGRAR |

## Siguiente paso recomendado:

1. **Fase 1:** Auditar `costos_margenes/repository.py` (18 hallazgos) - Mayor impacto.
2. **Fase 2:** Auditar `comercial/routes.py` líneas 3598, 3646, 3884, 3924.
3. **Fase 3:** Confirmar qué tabla EDARSAHUB SQL debe alimentar cada endpoint.
4. **Fase 4:** Si ya existe tabla SQL-first, cambiar endpoint a esa tabla.
5. **Fase 5:** Si no existe tabla SQL-first, crear/sincronizar tabla staging/canónica.
6. **Fase 6:** Dejar conexión remota solo en sync/backfill/job.
7. **Fase 7:** Después activar política NO_LIVE_DASHBOARD por endpoint o módulo.

## Archivos generados

```text

/app/docs/reports/AUDITORIA_COMERCIAL_ROUTES_SQL_FIRST.md
```
