# EDARSAHUB - PRD (Product Requirements Document)
## CRM Comercial Enterprise + Módulos Satélite

**Última actualización:** 2026-06-02 (Sesión 3)
**Estado:** En desarrollo activo - Diagnóstico de origen de datos completado

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
| Sync_PAX_Detalle | 0 | ⚠️ VACÍA | Diseño intencional Fase 1 - No requerida |
| Sync_Sales | 0 | ⚠️ VACÍA | Diseño intencional Fase 1 - No requerida |

### 4.1 Flujo de Datos Identificado (Diagnóstico 2026-06-02)

```
SOFTRESTAURANT/MPRO → SQL_LIVE → sync_comercial_edarsahub.py → Comercial_KPIs_Diarios_v2
                                                            ↓
                                                    (Sync_Sales/PAX_Detalle NO usadas en Fase 1)
```

**Conclusión:** Las tablas `Sync_Sales` y `Sync_PAX_Detalle` están vacías **por diseño**. El Dashboard Ejecutivo Fase 1 opera correctamente con KPIs agregados diarios que se escriben directamente a `Comercial_KPIs_Diarios_v2` sin pasar por tablas intermedias de tickets.

---

## 5. Backlog Priorizado

### P0 (Crítico)
- [x] ~~Ejecutar scripts de clasificación y transición RBAC~~ ✅ COMPLETADO 2026-06-02
- [x] ~~Registrar módulo INTELIGENCIA_COMERCIAL en Usuario_Modulos~~ ✅ ModuloID=59
- [x] ~~Marcar Sistema_RBAC_* como TRANSICIONAL en Gobierno~~ ✅ COMPLETADO
- [x] ~~Diagnóstico origen Comercial_KPIs_Diarios_v2~~ ✅ COMPLETADO 2026-06-02 (S3)
- [x] ~~Verificar relación Sync_Sales/PAX_Detalle~~ ✅ Vacías por diseño Fase 1

### P1 (Alto)
- [ ] Migrar usuarios MongoDB → SQL (`Usuario_Catalogo`) - **Dry-run pendiente**
- [ ] Módulo Pricing IA / Competidores Enterprise
- [ ] Motor de Rentabilidad (Costos y Márgenes)

### P2 (Medio) - Fase 2+
- [ ] Activar poblado de `Sync_Sales` para análisis granular de tickets
- [ ] Activar poblado de `Sync_PAX_Detalle` para métricas detalladas de comensales
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
| `/app/backend/core/policies/no_live_dashboard_policy.py` | Política NO-LIVE |
| `/app/docs/EDARSAHUB_MAXIMAS_INQUEBRANTABLES.md` | Máximas arquitectura |
| `/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md` | Marca legacy NO-LIVE |
| `/app/scripts/classify_no_live_violations.sh` | Scanner violaciones NO-LIVE |
| `/app/docs/reports/MATRIZ_NO_LIVE_DASHBOARD_EDARSAHUB.md` | Matriz NO-LIVE |

---

## 8. Historial de Cambios Recientes

| Fecha | Cambio |
|-------|--------|
| 2026-06-02 (S3) | **Diagnóstico completo origen Comercial_KPIs_Diarios_v2** |
| 2026-06-02 (S3) | Confirmado: Sync_Sales/PAX_Detalle vacías por diseño Fase 1 |
| 2026-06-02 (S3) | Generado reporte: DIAGNOSTICO_ORIGEN_KPIS_V2_20260602.md |
| 2026-06-02 (S2) | Registrado módulo INTELIGENCIA_COMERCIAL (ID=59) |
| 2026-06-02 (S2) | Sistema_RBAC_* marcadas como TRANSICIONAL en Gobierno |
| 2026-06-02 (S2) | Vistas y tablas de Inteligencia registradas en Gobierno |
| 2026-06-02 (S2) | Generada MATRIZ_NO_LIVE_DASHBOARD |
| 2026-06-02 (S1) | Herramienta edarsahub_sql_runner.py creada |
| 2026-06-02 (S1) | Fase 1 Inteligencia Comercial completada |

---

## 9. Reportes Generados (Diagnósticos)

| Reporte | Fecha | Contenido |
|---------|-------|-----------|
| `/app/docs/reports/DIAGNOSTICO_ORIGEN_KPIS_Y_SYNC_DETALLE.md` | 2026-06-02 | **Diagnóstico completo de 10 preguntas** sobre origen de KPIs y Sync |
| `/app/docs/reports/DIAGNOSTICO_ORIGEN_KPIS_V2_20260602.md` | 2026-06-02 | Origen de KPIs y relación con tablas Sync |
| `/app/docs/reports/VALIDACION_PORTAL_INTELIGENCIA_COMERCIAL_FASE1.md` | 2026-06-02 | Validación cierre Fase 1 |
| `/app/docs/reports/DIAGNOSTICO_MAPEO_RBAC_MONGO_A_SQL.md` | 2026-06-02 | Auditoría migración MongoDB→SQL |
| `/app/docs/reports/DECISION_EJECUTIVA_RBAC_20260602.md` | 2026-06-02 | Decisión arquitectónica RBAC |
| `/app/docs/reports/MATRIZ_NO_LIVE_DASHBOARD_EDARSAHUB.md` | 2026-06-02 | Matriz NO-LIVE |

---

*Documento actualizado automáticamente - E1 Agent*
