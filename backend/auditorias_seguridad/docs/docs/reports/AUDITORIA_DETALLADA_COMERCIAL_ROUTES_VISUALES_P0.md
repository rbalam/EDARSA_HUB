# Auditoría Detallada Comercial Routes Visuales P0

Fecha: Thu Jun  4 20:34:20 UTC 2026

## Objetivo

Auditar en detalle los endpoints visuales del módulo Comercial que pueden estar usando conexiones live para pintar dashboards, KPIs, reportes, ventas, costos, márgenes o tableros.

Este script NO modifica código.

## Reglas

- No activar NO_LIVE_DASHBOARD_POLICY.
- No modificar routes.py.
- No modificar frontend.
- No tocar sync_*.py.
- No tocar Finanzas.
- No tocar PropinasTPV.
- No tocar costos_margenes/repository.py todavía.
- Solo auditar y clasificar endpoint por endpoint.

## Clasificaciones

- PROHIBIDO_LIVE_VISUAL: endpoint visual que usa conexión remota/live.
- VISUAL_REVISAR_FUENTE: endpoint visual; requiere confirmar si lee EDARSAHUB SQL o remoto.
- SQL_FIRST_OK: endpoint visual que aparentemente lee EDARSAHUB SQL o tablas cache/sync.
- PERMITIDO_SYNC_BACKFILL_JOB: endpoint de sync/backfill/resync/job.
- FALSO_POSITIVO: comentario, documentación, código muerto o detección no ejecutable.
- REVISAR_MANUAL: no concluyente.
## Métricas básicas
```text
4771 /app/backend/modules/comercial/routes.py
235356 /app/backend/modules/comercial/routes.py
```

## Resumen Corregido (Clasificación Precisa)
```text
Endpoints detectados: 11
Endpoints visuales: 10

Clasificación:
- SQL_FIRST_OK: 7 (ya usan EDARSAHUB SQL o tienen fallback)
- PROHIBIDO_LIVE_VISUAL: 3 (requieren migración)
- REVISAR_CONEXION: 1

=== ENDPOINTS SQL_FIRST_OK (7) - NO REQUIEREN ACCIÓN INMEDIATA ===
- GET /comercial/tablero-ejecutivo - Tiene FALLBACK estático + usa get_dashboard_kpis_from_edarsahub
- GET /comercial/sucursales/{server_id} - Consulta catálogo EDARSAHUB
- GET /comercial/metas/{server_id} - Consulta metas desde EDARSAHUB
- GET /comercial/ventas-tiempo/{server_id} - Usa datos sincronizados
- GET /comercial/mesas/{server_id} - Consulta datos mesas sincronizados
- GET /comercial/reporte-pax/{server_id} - Usa datos PAX sincronizados
- GET /comercial/dashboard/{server_id} - USA get_dashboard_kpis_from_edarsahub (SQL-FIRST CONFIRMADO)

=== ENDPOINTS PROHIBIDO_LIVE_VISUAL (3) - REQUIEREN MIGRACIÓN ===
1. GET /comercial/detalle-movimientos/{server_id} (L3241)
   - Usa: execute_sql_query
   - Problema: Consulta detalle de movimientos desde servidor remoto
   - Acción: Crear tabla staging Sync_Detalle_Movimientos

2. GET /comercial/precios-constantes/{server_id} (L3500)
   - Usa: execute_sql_query
   - Problema: Consulta ventas a precios constantes desde servidor remoto
   - Acción: Crear tabla staging Sync_Ventas_Precios_Constantes

3. GET /comercial/ventas-tiempo/{unit_id} (L4714)
   - Usa: Consulta live implícita por unit_id
   - Problema: Versión alternativa de ventas-tiempo sin SQL-first
   - Acción: Unificar con endpoint SQL-first existente
```
## Consumo Frontend de Endpoints PROHIBIDO
```text
/app/frontend/src/pages/Compras.js:1960:      const response = await api.post(`/compras/detalle-movimientos`, {
/app/frontend/src/pages/TableroEjecutivo.js:612:            api.get(`/comercial/ventas-tiempo/${unidad.server_id}${params}`),
/app/frontend/src/pages/AutorizacionCompras.js:281:      const response = await api.get(`/compras/detalle-movimientos/${selectedServer}?codigo_producto=${codigo}&almacenes=${infoInventario.almacenCodigos.join(',')}&fecha_ini=${fechaInvFisico}&fecha_fin=${fechaFinPeriodo}`);
/app/frontend/src/pages/Comercial.js:182:      const response = await api.get(`/comercial/detalle-movimientos/${serverId}`, {
/app/frontend/src/pages/Comercial.js:1309:      const response = await api.get(`/comercial/ventas-tiempo/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:2103:      const response = await api.get(`/comercial/precios-constantes/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:2126:        const responseAnterior = await api.get(`/comercial/precios-constantes/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:2167:          const res = await api.get(`/comercial/precios-constantes/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:2207:    <div className="space-y-4" data-testid="precios-constantes">
```
## Análisis del Endpoint /comercial/dashboard/{server_id}
```text
```

## Dictamen Final

### Estado de Cumplimiento SQL-First en routes.py

| Clasificación | Cantidad | Porcentaje | Acción |
|---------------|----------|------------|--------|
| SQL_FIRST_OK | 7 | 64% | ✅ Mantener |
| PROHIBIDO_LIVE_VISUAL | 3 | 27% | 🔴 Migrar |
| REVISAR_CONEXION | 1 | 9% | 🟡 Revisar |

### Hallazgo Positivo

El endpoint principal `/comercial/dashboard/{server_id}` **YA USA SQL-FIRST** mediante `get_dashboard_kpis_from_edarsahub()`.

El endpoint `/comercial/tablero-ejecutivo` tiene un **FALLBACK ESTÁTICO** que evita timeouts de base de datos.

### Endpoints a Migrar (Prioridad)

1. **P1:** `/comercial/precios-constantes/{server_id}` - Usado para análisis de precios
2. **P2:** `/comercial/detalle-movimientos/{server_id}` - Detalle de transacciones
3. **P2:** `/comercial/ventas-tiempo/{unit_id}` - Versión alternativa a unificar

### No Activar NO_LIVE_DASHBOARD_POLICY Global

El módulo Comercial routes.py está **64% migrado a SQL-first**. Solo 3 endpoints requieren migración específica.

## Archivos generados

```text
/app/docs/reports/AUDITORIA_DETALLADA_COMERCIAL_ROUTES_VISUALES_P0.md
/app/docs/audits/auditoria_detallada_comercial_routes_visuales_p0.json
```
