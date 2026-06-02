# EDARSAHUB - PRD (Product Requirements Document)
## CRM Comercial Enterprise + Módulos Satélite

**Última actualización:** 2026-06-02
**Estado:** En desarrollo activo

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
- [x] `Sistema_Gobierno_Tablas` - Gobierno de datos (21 registros)
- [x] `Sistema_Migracion_MongoSQL_Mapeo` - Plan migración MongoDB→SQL (8 registros)
- [x] `Sistema_RBAC_Permisos` - Permisos canónicos (5 permisos IC)
- [x] `Sistema_RBAC_Roles` - Roles canónicos (6 roles)
- [x] `Sistema_RBAC_RolesPermisos` - Asignaciones (18 registros)
- [x] `Comercial_Inteligencia_VentasDetalleProducto` - Detalle ventas (vacía)

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

| Fuente | Registros | Estado |
|--------|-----------|--------|
| Comercial_KPIs_Diarios_v2 | 3,373 | ✅ OK |
| Comercial_Ventas_Dia_Abiertas_v2 | 8 | ✅ OK |
| Sync_PAX_Detalle | 0 | 🔴 SIN_DATOS |
| Sync_Sales | 0 | 🔴 SIN_DATOS |

---

## 5. Backlog Priorizado

### P0 (Crítico)
- [ ] Ejecutar job `inteligencia_comercial_sync` para poblar `Sync_Sales`
- [ ] Ejecutar job para poblar `Sync_PAX_Detalle`

### P1 (Alto)
- [ ] Crear tablas RBAC usuarios (`Sistema_RBAC_Usuarios`, `Sistema_RBAC_UsuariosRoles`)
- [ ] Migrar usuarios MongoDB → SQL
- [ ] Módulo Pricing IA / Competidores Enterprise
- [ ] Motor de Rentabilidad (Costos y Márgenes)

### P2 (Medio)
- [ ] Deprecar RBAC MongoDB
- [ ] Desmockización total frontend restante
- [ ] Scripts Edge Offline
- [ ] Control RBAC por empresa/unidad/sucursal

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

---

*Documento actualizado automáticamente - E1 Agent*
