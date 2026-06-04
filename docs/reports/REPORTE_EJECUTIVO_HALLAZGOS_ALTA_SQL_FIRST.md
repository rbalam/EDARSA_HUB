# Reporte Ejecutivo: Hallazgos ALTA - Migración SQL-First

**Fecha:** 2026-06-04  
**Alcance:** Módulos prioritarios (excluyendo Finanzas y PropinasTPV ya migrados)  
**Total hallazgos ALTA:** 619 (excl. Finanzas/PropinasTPV: ~580)

---

## 1. Resumen Ejecutivo

| Módulo | Hallazgos ALTA | Frontend | Backend | Tests (ignorar) | Prioridad |
|--------|----------------|----------|---------|-----------------|-----------|
| **Reportes** | 52 | 52 | 0 | 0 | 🔴 P1 |
| **ExploradorBD** | 5 | 5 | 0 | 0 | 🟡 P2 |
| **Compras** | 32 | 9 | 1 | 22 | 🟡 P2 |
| **Comercial** | 117 | 15 | 100 | 2 | 🔴 P1 |
| **Inventarios** | 5 | 0 | 0 | 5 | 🟢 P3 |
| **Dashboard** | 54 | 9 | 4 | 41 | 🟡 P2 |

---

## 2. Clasificación de Hallazgos

### 2.1 Frontend con `/api/servers` o `/api/sucursales` PROHIBIDOS

| Archivo | Hallazgos | Clasificación | Acción |
|---------|-----------|---------------|--------|
| `/app/frontend/src/services/serversService.js` | 4 | PROHIBIDO_FRONTEND_FILTROS | **MIGRAR** a Corporate Filters |
| `/app/frontend/src/filters/corporateFiltersApi.js` | 2 | PROHIBIDO_FRONTEND_FILTROS | Ya documentado como prohibido ✅ |
| `/app/frontend/src/components/tesoreria/useTesoreriaCorteZData.js` | 1 | PROHIBIDO_FRONTEND_FILTROS | **REVISAR** si usa Corporate Filters |

**Total:** 7 hallazgos reales (algunos son comentarios de documentación)

### 2.2 Backend/API que consulta servidores remotos para dashboards/KPIs

| Módulo | Archivo | Hallazgos | Descripción |
|--------|---------|-----------|-------------|
| Comercial | `routes.py` | 32 | Funciones `get_kpis_softrestaurant`, `get_kpis_mpro` |
| Comercial | `queries/mpro.py` | 10 | Queries MPRO para dashboard |
| Comercial | `queries/softrestaurant.py` | 3 | Queries SoftRestaurant |
| Comercial | `service.py` | 8 | Lógica de KPIs en vivo |
| Dashboard | `dashboard_service.py` | 1 | Servicio de tablajería |
| Dashboard | `no_live_dashboard_policy.py` | 3 | Política (documentación) |
| Compras | `historical_kpis_repository.py` | 1 | Consulta SQL directa |

**Total:** ~58 hallazgos en backend de producción

### 2.3 Conexiones PERMITIDAS (sync/backfill/jobs)

Los archivos en directorios `sync_*`, `jobs/`, `scheduler/` están **PERMITIDOS** porque:
- Son procesos batch que alimentan EDARSAHUB SQL
- No se ejecutan desde UI/dashboard
- Respetan arquitectura NO-LIVE

**Hallazgos en esta categoría:** ~0 (ya fueron filtrados)

### 2.4 Falsos Positivos

| Tipo | Ejemplos | Acción |
|------|----------|--------|
| Comentarios de documentación | `# Ejemplo para SoftRestaurant`, `// MPRO` | Ignorar |
| Referencias a tipos de sistema | `system_type === 'MPRO'` en UI (solo visual) | Revisar caso por caso |
| Tests | `test_*.py` | Ignorar |
| Constantes/Enums | `{ Codigo: 'MPRO', Descripcion: ... }` | Permitido |

**Total falsos positivos:** ~121 hallazgos

---

## 3. Análisis por Módulo Prioritario

### 🔴 3.1 Reportes (52 hallazgos) - PRIORIDAD ALTA

**Archivo principal:** `/app/frontend/src/pages/Reportes.js`

**Problema:**
- Usa condiciones basadas en `selectedServer?.system_type`
- Carga almacenes directamente desde SoftRestaurant
- Tiene lógica diferenciada MPRO vs SoftRestaurant

**Código problemático:**
```javascript
if (selectedServer?.system_type === 'SoftRestaurant') {...}
// Si es SoftRestaurant, cargar almacenes directamente (no tiene sucursales)
```

**Solución recomendada:**
1. Migrar a Corporate Filters para obtener almacenes
2. Eliminar condicionales `system_type` de la UI
3. Estandarizar lógica de reportes independiente del origen

---

### 🟡 3.2 ExploradorBD (5 hallazgos) - PRIORIDAD MEDIA

**Archivos:**
- `/app/frontend/src/pages/ExploradorBD.js` (2)
- `/app/frontend/src/services/exploradorService.js` (3)

**Problema:**
- Menciona códigos canónicos vs variantes (`SOFTRESTAURANT` vs `SoftRestaurant`)
- Documenta eliminación de hardcoding (ya migrado parcialmente)

**Análisis:**
- Mayoría son comentarios de documentación
- El servicio ya usa endpoint unificado
- **Bajo riesgo** - Solo requiere validación

---

### 🟡 3.3 Compras (32 hallazgos) - PRIORIDAD MEDIA

**Archivos:**
- `/app/frontend/src/pages/Compras.js` (8)
- `/app/frontend/src/components/compras/operativas/AutomatizacionesTable.jsx` (1)
- `/app/backend/modules/compras/historical_kpis_repository.py` (1)
- Tests: 22 (ignorar)

**Problema:**
- Frontend tiene referencia a `sucursal_origen_id` para MPRO
- Badge muestra `origen_sistema || 'MPRO'`

**Análisis:**
- Backend de producción tiene 1 solo hallazgo real
- Frontend usa datos ya sincronizados
- **Riesgo medio** - Revisar si hay llamadas live

---

### 🔴 3.4 Comercial (117 hallazgos) - PRIORIDAD ALTA

**Archivos críticos:**
| Archivo | Hallazgos | Criticidad |
|---------|-----------|------------|
| `routes.py` | 32 | 🔴 ALTA |
| `queries/mpro.py` | 10 | 🔴 ALTA |
| `queries/softrestaurant.py` | 3 | 🔴 ALTA |
| `service.py` | 8 | 🔴 ALTA |
| `adapters.py` | 1 | 🟡 MEDIA |
| `cache_service.py` | 1 | 🟡 MEDIA |

**Problema:**
- Funciones `get_kpis_softrestaurant()`, `get_kpis_mpro()`, `get_kpis_mpro_por_sucursal()`
- Dashboard MPRO consulta en vivo
- Tablero ejecutivo con datos live

**Frontend:**
- `/app/frontend/src/pages/Comercial.js` (3)
- `/app/frontend/src/pages/comercial/CostosMargenes.jsx` (12)

**Solución recomendada:**
1. Activar feature flag `NO_LIVE_DASHBOARD_POLICY` 
2. Migrar endpoints a consumir `Comercial_KPIs_Diarios_v2`
3. Eliminar llamadas directas a servidores remotos

---

### 🟢 3.5 Inventarios (5 hallazgos) - PRIORIDAD BAJA

**Archivos:**
- Solo tests (`test_comparativo_inventarios.py`)

**Análisis:**
- **Sin hallazgos en producción**
- Tests pueden ignorarse
- Módulo ya cumple arquitectura SQL-First

---

### 🟡 3.6 Dashboard/Tablero Ejecutivo (54 hallazgos) - PRIORIDAD MEDIA

**Archivos:**
- `/app/frontend/src/portal/pages/DashboardPage.jsx` (9)
- `/app/backend/core/policies/no_live_dashboard_policy.py` (3)
- `/app/backend/modules/tablajeria/dashboard_service.py` (1)
- Tests: 41 (ignorar)

**Problema:**
- DashboardPage tiene estilos diferenciados por `system_type`
- Colores AZUL para MPRO, VIOLETA para SoftRestaurant

**Análisis:**
- La diferenciación visual por tipo de sistema es **cosmética**, no funcional
- La política `no_live_dashboard_policy.py` ya existe
- **Riesgo medio** - Validar que dashboard use datos cacheados

---

## 4. Orden Recomendado de Corrección

### Fase 1 - Crítica (Comercial)
1. **Auditar `routes.py`** - Identificar endpoints que llaman `get_kpis_*` en vivo
2. **Activar `NO_LIVE_DASHBOARD_POLICY`** si no está activa
3. **Migrar KPIs a `Comercial_KPIs_Diarios_v2`**

### Fase 2 - Alta (Reportes)
1. **Migrar `Reportes.js`** a usar Corporate Filters para almacenes/sucursales
2. **Eliminar condicionales `system_type`** de la lógica de reportes

### Fase 3 - Media (Dashboard, Compras, ExploradorBD)
1. **Dashboard** - Validar que usa datos cacheados
2. **Compras** - Revisar `historical_kpis_repository.py`
3. **ExploradorBD** - Validación de migración existente

### Fase 4 - Baja (Inventarios)
- No requiere acción - Solo tests

---

## 5. Archivos Específicos a NO Modificar

| Archivo | Razón |
|---------|-------|
| `/app/frontend/src/pages/Finanzas.js` | ✅ Ya migrado |
| `/app/frontend/src/components/PropinasTPV.jsx` | ✅ Ya migrado |
| `/app/backend/modules/finanzas/*` | ✅ Ya usa EDARSAHUB SQL |
| `**/sync_*.py` | Permitido - Son jobs de sincronización |
| `**/test_*.py` | Tests - Ignorar |

---

## 6. Métricas de Éxito

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Hallazgos ALTA en producción | ~580 | < 50 |
| Módulos con llamadas LIVE | 4 | 0 |
| Frontend usando `/api/servers` | ~7 | 0 |
| Build sin warnings SQL-First | No | Sí |

---

## 7. Próximos Pasos

1. ✅ **Completado:** Hook `useFinanzasCorporateFilters` integrado en Finanzas.js
2. ⏳ **Pendiente:** Auditoría detallada de `routes.py` en Comercial
3. ⏳ **Pendiente:** Migración de `Reportes.js` a Corporate Filters
4. ⏳ **Pendiente:** Validación de Dashboard con política NO-LIVE

---

*Reporte generado automáticamente - E1 Agent*
