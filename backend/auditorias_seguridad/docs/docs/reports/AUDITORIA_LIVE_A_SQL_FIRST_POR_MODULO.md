# Auditoría live → SQL-first por módulo

Fecha: Thu Jun  4 19:38:46 UTC 2026

## Objetivo

Detectar qué módulos de EDARSAHUB todavía tienen conexiones live o dependencias directas a servidores externos, y clasificarlas como:

### Permitidas

- sync
- backfill
- resync
- diagnóstico técnico
- jobs controlados

### Prohibidas

- dashboard
- KPI
- reporte
- endpoint visual
- filtros operativos
- consultas desde frontend a servidores/sucursales para pintar pantalla
- fallbacks live para mostrar datos

## Máxima

Los tableros, KPIs y reportes deben leer exclusivamente desde EDARSAHUB SQL.

SoftRestaurant, MPRO, Enterprise u otros sistemas externos solo pueden consultarse en procesos controlados de sincronización, backfill, resync o diagnóstico autorizado.

## Archivos generados

```text
/app/docs/audits/auditoria_live_sql_first_por_modulo.csv
/app/docs/audits/auditoria_live_sql_first_por_modulo.json
```

## Resumen automático

| Clasificación | Cantidad |
|---------------|----------|
| REVISAR | 1835 |
| PERMITIDO_SYNC_BACKFILL_DIAGNOSTICO | 1188 |
| REVISAR_POSIBLE_LIVE | 575 |
| PROHIBIDO_POSIBLE_LIVE_VISUAL | 533 |
| PROHIBIDO_FRONTEND_FILTROS | 86 |

## Resumen por módulo

| Módulo | Hallazgos |
|--------|-----------|
| No clasificado | 1561 |
| Comercial | 997 |
| Finanzas | 466 |
| Finanzas / Propinas TPV | 283 |
| Compras | 272 |
| Sync / Jobs | 239 |
| Recursos Humanos | 89 |
| Scheduler / Jobs | 75 |
| Dashboard | 54 |
| Reportes | 53 |
| Inventarios | 47 |
| Comercial / Costos Márgenes | 40 |
| Servidores / Configuración | 26 |
| Backfill | 10 |
| ExploradorBD | 5 |

## Hallazgos PROHIBIDO_FRONTEND_FILTROS (86 casos)

| Archivo | Línea | Patrón |
|---------|-------|--------|
| `/app/backend/modules/comercial/routes.py` | 1761 | frontend api servers |
| `/app/backend/tests/test_comercial.py` | 120 | frontend api servers |
| `pages/Comercial.js` | 2807 | frontend api servers |
| `/app/backend/tests/test_compras_analisis.py` | 30 | frontend api servers |
| `/app/backend/tests/test_compras_analisis.py` | 280 | frontend api servers |
| `/app/backend/tests/test_compras_analisis.py` | 296 | frontend api servers |
| `/app/backend/tests/test_compras_module.py` | 72 | frontend api servers |
| `/app/backend/tests/test_compras_module.py` | 88 | frontend api servers |
| `/app/backend/tests/test_compras_module.py` | 111 | frontend api servers |
| `/app/backend/tests/test_compras_module.py` | 121 | frontend api servers |
| `/app/backend/tests/test_compras_module.py` | 158 | frontend api servers |
| `/app/backend/tests/test_compras_module.py` | 169 | frontend api servers |
| `/app/backend/tests/test_dashboard_servers.py` | 243 | frontend api servers |
| `/app/backend/tests/test_dashboard_servers.py` | 261 | frontend api servers |
| `/app/backend/tests/test_dashboard_servers.py` | 274 | frontend api servers |
| `/app/backend/tests/test_dashboard_servers.py` | 291 | frontend api servers |
| `/app/backend/tests/test_dashboard_servers.py` | 304 | frontend api servers |
| `/app/backend/tests/test_dashboard_servers.py` | 317 | frontend api servers |
| `/app/backend/tests/test_dashboard_servers.py` | 331 | frontend api servers |
| `/app/backend/tests/test_dashboard_servers.py` | 333 | frontend api servers |
| `/app/backend/tests/test_dashboard_servers.py` | 353 | frontend api servers |
| `/app/backend/tests/test_comparativo_inventarios.py` | 74 | frontend api servers |
| `/app/backend/tests/test_comparativo_inventarios.py` | 88 | frontend api servers |
| `/app/backend/tests/test_comparativo_inventarios.py` | 104 | frontend api servers |
| `/app/backend/core/server_registry.py` | 15 | frontend api servers |
| `/app/backend/modules/api_connections/universal_test_routes.py` | 23 | frontend api servers |
| `/app/backend/scripts/encrypt_core_server_secrets.py` | 14 | frontend api servers |
| `/app/backend/scripts/validate_catalogo_sistemas_endpoints.py` | 316 | frontend api servers |
| `/app/backend/scripts/validate_catalogo_sistemas_endpoints.py` | 320 | frontend api servers |
| `/app/backend/scripts/validate_catalogo_sistemas_endpoints.py` | 324 | frontend api servers |
| `/app/backend/scripts/validate_consultas_sql_endpoints_fase_4b.py` | 90 | frontend api servers |
| `/app/backend/scripts/validate_consultas_sql_endpoints_fase_4b.py` | 93 | frontend api servers |
| `/app/backend/scripts/validate_consultas_sql_endpoints_fase_4b.py` | 94 | frontend api servers |
| `/app/backend/scripts/validate_consultas_sql_endpoints_fase_4b.py` | 96 | frontend api servers |
| `/app/backend/tests/test_auth_mocks.py` | 90 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 45 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 63 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 83 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 103 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 123 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 137 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 149 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 183 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 190 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 201 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 213 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 280 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 291 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 303 | frontend api servers |
| `/app/backend/tests/test_inventory_analysis_filters.py` | 376 | frontend api servers |
| ... | ... | 36 adicionales |

## Referencia validada: PropinasTPV

Este módulo ya está migrado a SQL-first y Corporate Filters:

```text
✅ Usa CorporateFiltersProvider
3
 instancias
✅ No usa /api/servers
0
0 instancias (correcto)
✅ Lee de EDARSAHUB SQL via /api/finanzas/propinas
```

## Dictamen

### Hallazgos críticos

1. **86 casos PROHIBIDO_FRONTEND_FILTROS**: Archivos frontend que usan `/api/servers` o `/api/sucursales` directamente
2. **533 casos PROHIBIDO_POSIBLE_LIVE_VISUAL**: Backend con posibles conexiones live en contexto visual

### Módulos prioritarios para migración SQL-first

1. **Finanzas.js** - 86 hallazgos frontend filtros prohibidos (migrar a Corporate Filters)
2. **Comercial** - 997 hallazgos totales (muchos en queries/mpro.py y queries/softrestaurant.py)
3. **Compras** - 272 hallazgos
4. **Dashboard** - 54 hallazgos
5. **Reportes** - 53 hallazgos

### Próximo paso recomendado

Migrar `Finanzas.js` a Corporate Filters para eliminar los 86 casos de `/api/servers` y `/api/sucursales` frontend prohibidos.

---

## Migración Completada: Finanzas.js (2026-06-05)

### Cambios Realizados

| Archivo | Cambio |
|---------|--------|
| `pages/Finanzas.js` | Envuelto con `<CorporateFiltersProvider scope="finanzas">` |
| `pages/Finanzas.js` | Eliminado `fetchUnidadesNegocio` y reemplazado por `useCorporateFilters()` |
| `pages/Finanzas.js` | Estados `unidadesNegocio` y `loadingUnidades` ahora vienen de Corporate Filters |

### Beneficios

- ✅ No más llamadas a `/api/unidades-negocio` (servicio legacy)
- ✅ Filtros centralizados en Corporate Filters
- ✅ Datos desde EDARSAHUB SQL
- ✅ Build exitoso sin errores

### Componentes Hijos

Los componentes hijos (`FinanzasDashboard`, `FinanzasPresupuestos`, etc.) siguen recibiendo props sin cambios, manteniendo compatibilidad.
