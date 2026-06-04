# EDARSA HUB - PRD (Product Requirements Document)
## CRM Comercial Enterprise + Módulos Satélite

**Última actualización:** 2026-06-04 (Sesión 6 - Migración SQL-First Modal Detalle Ventas)
**Estado:** En desarrollo activo - Modal Detalle Ventas migrado a SQL-First ✅

---

## 1. Problema Original

Construir el **CRM COMERCIAL ENTERPRISE** y módulos satélite (Comandero, Super Caja, Portal Inteligencia Comercial IA) integrados al ecosistema EDARSA HUB.

### Restricciones Fundamentales:
- **CERO dependencias de MongoDB** para datos comerciales
- **Arquitectura NO-LIVE**: Sincronización vía jobs y cachés locales
- **Inyección directa de scripts a SQL Server** de producción mediante `pyodbc`/`pymssql`
- **PROHIBIDO** usar `testing_agent_v3_fork` - Pruebas vía cURL, bash, python -c y screenshots

---

## 2. Arquitectura Canónica

```
Fuentes Externas (SoftRestaurant/MPRO/NetPay)
        ↓
   [Scheduler / Jobs]
        ↓
Tablas Sync_* y Comerciales en SQL Server
        ↓
Vistas/Agregados EDARSAHUB SQL
        ↓
   FastAPI Endpoints
        ↓
   React Dashboard
```

**PROHIBIDO:** Dashboard consultando MongoDB o sistemas externos en tiempo real.

---

## 3. Lo Implementado (Fase 1 Inteligencia Comercial)

### 3.1 Vistas SQL Canónicas
- [x] `Comercial_Inteligencia_VW_KPIsEjecutivos` - KPIs consolidados
- [x] `Comercial_Inteligencia_VW_SyncStatus` - Estado de sincronización
- [x] `Sistema_VW_Servidores_Conexiones_Publico` - Servidores sin credenciales
- [x] `Sistema_VW_PosiblesDuplicidadesTablas` - Auditoría duplicidades

### 3.2 Stored Procedures
- [x] `Sp_Validar_Inteligencia_Comercial_Status` - Validar frescura de fuentes

### 3.3 Tablas de Gobierno
- [x] `Sistema_Gobierno_Tablas` - Gobierno de datos (**27 registros** - actualizado)
- [x] `Sistema_Migracion_MongoSQL_Mapeo` - Plan migración MongoDB→SQL (8 registros)
- [x] ~~`Sistema_RBAC_Permisos`~~ - **TRANSICIONAL/DEPRECADA** → Usar `Usuario_Acciones`
- [x] ~~`Sistema_RBAC_Roles`~~ - **TRANSICIONAL/DEPRECADA** → Usar `Usuario_Roles`
- [x] ~~`Sistema_RBAC_RolesPermisos`~~ - **TRANSICIONAL/DEPRECADA** → Usar `Usuario_PermisosRolModulo`
- [x] `Comercial_Inteligencia_VentasDetalleProducto` - Detalle ventas (vacía)

### 3.3b RBAC Canónico (Usuario_*)
- [x] `Usuario_Modulos` - **55 módulos** (incluye INTELIGENCIA_COMERCIAL, ModuloID=59)
- [x] `Usuario_Roles` - **16 roles** (incluye CRM_ADMIN, CRM_EJEC, CRM_AUDIT)
- [x] `Usuario_Acciones` - **16 acciones** (VER, CREAR, EDITAR, ELIMINAR, etc.)
- [x] `Usuario_PermisosRolModulo` - Matriz de permisos

### 3.4 Endpoints FastAPI
- [x] `GET /api/comercial/inteligencia/kpis`
- [x] `GET /api/comercial/inteligencia/ventas-comparativo`
- [x] `GET /api/comercial/inteligencia/tendencia`
- [x] `GET /api/comercial/inteligencia/kpis-por-unidad`
- [x] `GET /api/comercial/inteligencia/unidades`
- [x] `GET /api/comercial/inteligencia/sync-status`
- [x] `GET /api/comercial/inteligencia/pax`

### 3.5 Herramientas
- [x] `edarsahub_sql_runner.py` - Runner SQL controlado
- [x] `audit_mongodb_dependencies.sh` - Auditoría MongoDB
- [x] `audit_live_connections.sh` - Auditoría conexiones LIVE
- [x] `no_live_dashboard_policy.py` - Política NO-LIVE

### 3.6 Documentación
- [x] `EDARSAHUB_MAXIMAS_INQUEBRANTABLES.md` - 11 máximas de arquitectura
- [x] `MATRIZ_CANONICIDAD_TABLAS_EDARSAHUB.md` - Clasificación de tablas
- [x] `VALIDACION_PORTAL_INTELIGENCIA_COMERCIAL_FASE1.md` - Cierre Fase 1

---

## 4. Estado de Fuentes de Datos

| Fuente | Registros | Estado | Notas |
|--------|-----------|--------|-------|
| Comercial_KPIs_Diarios_v2 | **3,376** | ✅ OK | Poblada vía SQL_LIVE (SOFTRESTAURANT+MPRO) |
| Comercial_Ventas_Dia_Abiertas_v2 | 8 | ✅ OK | |
| Sync_PAX_Detalle | 0 | ⚠️ VACÍA | Fase 2 - Dry-run pendiente |
| Sync_Sales | 0 | ✅ DRY-RUN OK | **Listo para activación** (ver sección 4.2) |

### 4.1 Flujo de Datos Identificado (Diagnóstico 2026-06-02)

```
SOFTRESTAURANT/MPRO → SQL_LIVE → sync_comercial_edarsahub.py → Comercial_KPIs_Diarios_v2
                                                            ↓
                                                    (Sync_Sales/PAX_Detalle NO usadas en Fase 1)
```

**Conclusión:** Las tablas `Sync_Sales` y `Sync_PAX_Detalle` están vacías **por diseño**. El Dashboard Ejecutivo Fase 1 opera correctamente con KPIs agregados diarios que se escriben directamente a `Comercial_KPIs_Diarios_v2` sin pasar por tablas intermedias de tickets.

### 4.2 Dry-Run Sync_Sales EXITOSO (2026-06-02 Sesión 4)

| Unidad | Sistema | Tickets | Monto | Items JSON | Estado |
|--------|---------|---------|-------|------------|--------|
| **CIENFUEGOS** | SoftRestaurant | 19 | N/D | ✅ 19 válidos | ✅ EJECUTAR |
| **130QRO** | MPRO | 11 | $69,731 | ✅ 11 válidos | ✅ EJECUTAR |
| **ORIGEN** | MPRO | 20 | $56,232 | ✅ 20 válidos | ✅ EJECUTAR |

**Issues Resueltos:**
1. ✅ Incompatibilidad `FOR JSON PATH` en SQL Server legacy → Construcción JSON en Python
2. ✅ CLI con `choices` hardcodeados → Aceptación dinámica de unidades
3. ✅ Query MPRO incorrecta → Corregido JOIN Venta+Venta_Encabezado con Vn_Tabla='Comanda'

**Comando de Ejecución:**
```bash
export SERVER_SECRET_KEY="4HGEDzNpIv3pMoHXFtlXXYiTSt1SxU8dXHiTR5GOtd8="
cd /app/backend
python tools/sync_sales_dry_run.py --unidad CIENFUEGOS --fecha-inicio 2026-06-01 --fecha-fin 2026-06-01 --dry-run
```

---

## 5. Backlog Priorizado

### P0 (Crítico)
- [x] ~~Ejecutar scripts de clasificación y transición RBAC~~ ✅ COMPLETADO 2026-06-02
- [x] ~~Registrar módulo INTELIGENCIA_COMERCIAL en Usuario_Modulos~~ ✅ ModuloID=59
- [x] ~~Marcar Sistema_RBAC_* como TRANSICIONAL en Gobierno~~ ✅ COMPLETADO
- [x] ~~Diagnóstico origen Comercial_KPIs_Diarios_v2~~ ✅ COMPLETADO 2026-06-02 (S3)
- [x] ~~Verificar relación Sync_Sales/PAX_Detalle~~ ✅ Vacías por diseño Fase 1
- [x] ~~Dry-run Sync_Sales (CIENFUEGOS, 130QRO, ORIGEN)~~ ✅ COMPLETADO 2026-06-02 (S4)
- [x] ~~Corregir mapeo importes SoftRestaurant legacy~~ ✅ COMPLETADO 2026-06-03 (S5)
- [x] ~~Establecer REGLA PERMANENTE Sync_Sales SoftRestaurant Legacy~~ ✅ COMPLETADO 2026-06-03
- [x] ~~**SYNC_SALES PILOTO 2026-06-01**~~ ✅ **COMPLETADO Y VALIDADO 2026-06-03**
  - 79 tickets insertados (5 unidades)
  - $309,092.31 MXN
  - 0 duplicados, 100% JSON válido
  - Validación cruzada vs KPIs aprobada

### P1 (Alto) - AWAITING USER APPROVAL
- [ ] **Ejecutar inserción real Sync_Sales** - Dry-run exitoso, pendiente aprobación
- [ ] Activar poblado de `Sync_PAX_Detalle` - Siguiente tabla de granularidad
- [ ] Migrar usuarios MongoDB → SQL (`Usuario_Catalogo`) - Dry-run pendiente
- [ ] Módulo Pricing IA / Competidores Enterprise
- [ ] Motor de Rentabilidad (Costos y Márgenes)

### P2 (Medio) - Fase 2+
- [ ] Desmockización total frontend restante
- [ ] Scripts Edge Offline
- [ ] Control RBAC por empresa/unidad/sucursal
- [ ] Eliminación física de colecciones MongoDB legado

---

## 6. Credenciales de Prueba

- **Usuario:** `admin@inventario.com`
- **Password:** `admin123`

---

## 7. Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/modules/comercial/inteligencia_comercial_routes.py` | Endpoints Fase 1 |
| `/app/backend/modules/comercial/inteligencia_repository.py` | Repository SQL |
| `/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py` | Job sincronización |
| `/app/backend/tools/edarsahub_sql_runner.py` | Runner SQL |
| `/app/backend/tools/sync_sales_dry_run.py` | **Dry-run Sync_Sales** ✅ |
| `/app/backend/core/policies/no_live_dashboard_policy.py` | Política NO-LIVE |
| `/app/docs/EDARSAHUB_MAXIMAS_INQUEBRANTABLES.md` | Máximas arquitectura |
| `/app/docs/rules/RULE_SYNC_SALES_SOFTRESTAURANT_LEGACY_AMOUNTS.md` | **REGLA PERMANENTE** ⚠️ |
| `/app/scripts/validate_sync_sales_softrestaurant_legacy_rules.sh` | Validador regla |
| `/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md` | Marca legacy NO-LIVE |
| `/app/scripts/classify_no_live_violations.sh` | Scanner violaciones NO-LIVE |
| `/app/docs/reports/MATRIZ_NO_LIVE_DASHBOARD_EDARSAHUB.md` | Matriz NO-LIVE |

---

## 8. Historial de Cambios Recientes

| Fecha | Cambio |
|-------|--------|
| 2026-06-03 (S5) | **✅ SYNC_SALES PILOTO 2026-06-01 COMPLETADO Y VALIDADO** |
| 2026-06-03 (S5) | Insertados 79 tickets en 5 unidades ($309,092.31 MXN) |
| 2026-06-03 (S5) | Validación post-insert aprobada (0 duplicados, 100% JSON válido) |
| 2026-06-03 (S5) | **REGLA PERMANENTE: Sync_Sales SoftRestaurant Legacy** establecida |
| 2026-06-03 (S5) | Función `calculate_softrestaurant_item_total()` implementada |
| 2026-06-03 (S5) | Validador `/app/scripts/validate_sync_sales_softrestaurant_legacy_rules.sh` creado |
| 2026-06-02 (S4) | Dry-run Sync_Sales exitoso - CIENFUEGOS, 130QRO, ORIGEN |
| 2026-06-02 (S4) | Corregido: FOR JSON PATH → JSON en Python (compatibilidad legacy) |
| 2026-06-02 (S3) | Diagnóstico completo origen Comercial_KPIs_Diarios_v2 |
| 2026-06-02 (S2) | Registrado módulo INTELIGENCIA_COMERCIAL (ID=59) |
| 2026-06-02 (S1) | Fase 1 Inteligencia Comercial completada |

---

## 9. Reportes Generados (Diagnósticos)

| Reporte | Fecha | Contenido |
|---------|-------|-----------|
| `/app/docs/reports/VALIDACION_REGLA_SYNC_SALES_SOFTRESTAURANT_LEGACY.md` | 2026-06-03 | **Validación regla permanente - OK** |
| `/app/docs/reports/DIAGNOSTICO_COLUMNAS_SOFTRESTAURANT_CIENFUEGOS.md` | 2026-06-02 | Diagnóstico columnas cheques/cheqdet |
| `/app/docs/reports/DRY_RUN_SYNC_SALES_EXITOSO_20260602.md` | 2026-06-02 | **Dry-run exitoso CIENFUEGOS, 130QRO, ORIGEN** |
| `/app/docs/reports/DIAGNOSTICO_ORIGEN_KPIS_Y_SYNC_DETALLE.md` | 2026-06-02 | **Diagnóstico completo de 10 preguntas** sobre origen de KPIs y Sync |
| `/app/docs/reports/DIAGNOSTICO_ORIGEN_KPIS_V2_20260602.md` | 2026-06-02 | Origen de KPIs y relación con tablas Sync |
| `/app/docs/reports/VALIDACION_PORTAL_INTELIGENCIA_COMERCIAL_FASE1.md` | 2026-06-02 | Validación cierre Fase 1 |
| `/app/docs/reports/DIAGNOSTICO_MAPEO_RBAC_MONGO_A_SQL.md` | 2026-06-02 | Auditoría migración MongoDB→SQL |
| `/app/docs/reports/DECISION_EJECUTIVA_RBAC_20260602.md` | 2026-06-02 | Decisión arquitectónica RBAC |
| `/app/docs/reports/MATRIZ_NO_LIVE_DASHBOARD_EDARSAHUB.md` | 2026-06-02 | Matriz NO-LIVE |

---

## 10. REGLAS PERMANENTES

### SYNC_SALES SOFTRESTAURANT LEGACY

**Documento rector:** `/app/docs/rules/RULE_SYNC_SALES_SOFTRESTAURANT_LEGACY_AMOUNTS.md`

**PROHIBIDO:**
- Usar `FOR JSON PATH` contra SoftRestaurant legacy
- Usar `cheqdet.totalsrx` como importe (puede ser -1)
- Usar `cheqdet.subtotalsrx` como importe (puede ser -1)

**OBLIGATORIO:**
- Calcular `item_total = cantidad * precio` con `calculate_softrestaurant_item_total()`
- Construir items JSON en Python con `json.dumps()`
- Validar monto > 0 antes de autorizar `--execute`

**Validador:**
```bash
bash /app/scripts/validate_sync_sales_softrestaurant_legacy_rules.sh /app
```

---

## 11. PENDIENTES BLOQUEANTES

### VALIDAR_COLUMNAS_DESTINO_SYNC_COMPRAS (P0)

**Documento:** `/app/docs/PENDIENTE_VALIDAR_COLUMNAS_DESTINO_SYNC_COMPRAS.md`  
**Estado:** ⏳ PENDIENTE - Requiere acceso SSMS/Producción

**Tablas a validar:**
- `Inventario_Movimientos` / `Inventario_MovimientosDetalle`
- `Compras_Pedidos` / `Compras_PedidosDetalle`
- `Compras_Ordenes` / `Compras_OrdenesDetalle`
- `Compras_Recepciones` / `Compras_RecepcionesDetalle`

**Restricciones activas:**
| Acción | Estado |
|--------|--------|
| `dry_run=false` | ❌ BLOQUEADO |
| `COMPRAS_SQL_FIRST_ENABLED=true` | ❌ BLOQUEADO |
| Refactor Frontend SQL-First | ❌ BLOQUEADO |

**Criterio de desbloqueo:** Usuario valida columnas en SSMS → Agente verifica compatibilidad → Autoriza ejecución.

---

## 12. SESIÓN 5 - Cambios (2026-06-04)

| Hora | Cambio |
|------|--------|
| 07:20 | Auditoría de integración `sync_compras_job.py` |
| 07:24 | Integración de 6 funciones adicionales al job (almacenes, existencias, movimientos, pedidos, ordenes, recepciones) |
| 07:27 | Corrección import `Callable` en `sync_service.py` |
| 07:30 | Documentación pendiente `VALIDAR_COLUMNAS_DESTINO_SYNC_COMPRAS` |

---

## 13. SESIÓN 6 - Cambios (2026-06-05)

| Hora | Cambio |
|------|--------|
| -- | **CORRECCIÓN P0: Conexión SoftRestaurant para Sync Propinas TPV** |
| -- | **Causa raíz identificada:** Filtro `system_type` incompleto en `get_unidad_connection_info()` |
| -- | **Archivos corregidos:** `sync_propinas_softrestaurant.py`, `sync_cortes_softrestaurant.py` |
| -- | **Cambio:** Agregado `SOFTRESTAURANT_PRO` al filtro IN() de system_type |
| -- | **Backfill ejecutado:** 2026-05-17 a 2026-06-05, 1,186 registros, $544,866 en propinas |
| -- | **Validación:** Conexiones pytds exitosas a CIENFUEGOS, LA ESTELAR, 130° MERIDA |
| -- | **Reporte:** `/app/docs/reports/CORRECCION_CONEXION_SOFTRESTAURANT_SYNC_PROPINAS.md` |

### Estado Actual Sync Propinas TPV

| Unidad | Conexión | Última Sync | Registros |
|--------|----------|-------------|-----------|
| CIENFUEGOS | ✅ pytds | 2026-06-05 | 405 |
| LA ESTELAR | ✅ pytds | 2026-06-05 | 550 |
| 130° MERIDA | ✅ pytds | 2026-06-05 | 231 |

### Correcciones API Propinas v2

| Cambio | Archivo | Estado |
|--------|---------|--------|
| Filtro system_type | `sync_propinas_softrestaurant.py` | ✅ |
| Filtro system_type | `sync_cortes_softrestaurant.py` | ✅ |
| Filtro system_type | `sync_propinas_mpro.py` | ✅ |
| Filtro UUID/nombre | `repository_edarsahub.py` | ✅ |
| Helper SQL centralizado | `core/system_type_utils.py` | ✅ |

---

## 14. SESIÓN 7 - Cambios (2026-06-05)

| Hora | Cambio |
|------|--------|
| -- | **P1 VALIDACIÓN VISUAL PROPINAS TPV: COMPLETADA** |
| -- | **Frontend corregido:** `CorporateFiltersProvider.jsx` - control de montaje con useRef |
| -- | **Frontend corregido:** `previewCacheUtils.js` - excluir tokens de cache reset |
| -- | **Resultado:** KPIs muestran datos reales desde EDARSAHUB SQL |
| -- | **Reporte:** `/app/docs/reports/VALIDACION_VISUAL_PROPINAS_TPV_COMPLETADA.md` |

### Validación Visual Propinas TPV

| KPI | Valor Observado |
|-----|-----------------|
| Propinas TPV | $45,393.78 |
| Comisión (2%) | $907.88 |
| A Pagar Meseros | $44,485.90 |
| Fuente | EDARSAHUB_REAL ✅ |

### Migración Finanzas.js a Corporate Filters

| Cambio | Estado |
|--------|--------|
| Eliminado `fetchUnidadesNegocio` | ✅ |
| Agregado `CorporateFiltersProvider` | ✅ |
| Agregado `useCorporateFilters()` | ✅ |
| Build exitoso | ✅ |

---

## 15. SESIÓN 8 - Cambios (2026-06-04)

| Hora | Cambio |
|------|--------|
| -- | **VALIDACIÓN POST-MIGRACIÓN FINANZAS CORPORATE FILTERS** |
| -- | **Fix Backend:** `get_unidades_negocio()` prioriza columnas reales (`id`, `nombre`, `codigo`) |
| -- | **Corporate Filters:** 5 empresas, 5 unidades de negocio cargadas desde SQL |
| -- | **Build Frontend:** EXITOSO |
| -- | **Validación Visual:** 8 tabs verificados (Dashboard, Propinas TPV, Tesorería, etc.) |
| -- | **Reporte:** `/app/docs/reports/VALIDACION_POST_MIGRACION_FINANZAS_CORPORATE_FILTERS.md` |
| -- | **Hook Adapter:** `useFinanzasCorporateFilters` creado e integrado en `Finanzas.js` |

### Corporate Filters Bootstrap (scope=finanzas)

| Catálogo | Registros | Estado |
|----------|-----------|--------|
| Empresas | 5 | ✅ |
| Unidades de Negocio | 5 | ✅ |
| Servidores | Variable | ✅ |

### Unidades de Negocio Cargadas

| ID | Nombre | Código |
|----|--------|--------|
| 19E076FB... | 130° MERIDA | 130MID |
| 9BC05CED... | 130° QUERETARO | 130QRO |
| B06EE652... | CIENFUEGOS | CIENFUEGOS |
| DFB86008... | LA ESTELAR | ESTELAR |
| 23CA0B76... | ORIGEN | ORIGEN |

### Tabs Finanzas Validados

| Tab | Estado |
|-----|--------|
| Dashboard | ✅ |
| Control de Ingresos | ✅ |
| Cuentas por Pagar | ✅ |
| Propinas TPV | ✅ |
| Tesorería | ✅ |
| Cuentas Bancarias | ⏳ Pendiente |
| Presupuestos | ⏳ Pendiente |
| Reportes | ⏳ Pendiente |

### Integración useFinanzasCorporateFilters

| Cambio | Estado |
|--------|--------|
| Hook `useFinanzasCorporateFilters.js` creado | ✅ |
| Exportado desde `filters/index.js` | ✅ |
| Integrado en `Finanzas.js` | ✅ |
| Props a hijos mantenidos | ✅ |
| Hijos NO modificados | ✅ |
| Build exitoso | ✅ |

---

## 16. Backlog Priorizado

### P1 - Alta Prioridad
- [x] Crear hook adapter `useFinanzasCorporateFilters` ✅
- [x] Integrar hook en `Finanzas.js` ✅
- [x] **MIGRACIÓN SQL-FIRST Modal Detalle Ventas Comercial** ✅ (Sesión 6)
  - Backend: `GET /comercial/detalle-movimientos/{server_id}` ahora lee de `Comercial_KPIs_Diarios_v2`
  - Frontend: `Comercial.js` actualizado para pasar `selectedMeses` y `selectedAnios` al modal
  - Validado: 130° MÉRIDA Junio 2026 muestra 18 tickets, 36 PAX correctamente
- [ ] Auditar hallazgos "ALTA" en módulos Reportes, ExploradorBD, Compras, Comercial, Inventarios (ver `/app/docs/reports/AUDITORIA_LIVE_A_SQL_FIRST_POR_MODULO.md`)
- [ ] Migrar `/comercial/precios-constantes/{server_id}` a SQL-First (requiere tabla `Sync_Ventas_Precios_Constantes`)
- [ ] Auditar y corregir `costos_margenes/repository.py` (18 hallazgos de conexiones live prohibidas)
- [ ] Migrar adapters de componentes financieros hijos (`FinanzasDashboard`, `FinanzasPresupuestos`, etc.) para usar Corporate Filters nativamente

### P2 - Media Prioridad
- [ ] Validar columnas destino de `sync_compras` en SSMS (bloqueante para dry_run=false)
- [ ] Centralizar configuración conexión EDARSAHUB (~91 archivos con credenciales hardcodeadas)
- [ ] Eliminación física de colecciones MongoDB restantes

### P3 - Backlog
- [ ] Módulo Pricing IA / Competidores Enterprise
- [ ] Backfill de Ventas Históricas

---

*Documento actualizado automáticamente - E1 Agent*
