# EDARSA HUB - Product Requirements Document

## Problema Original
Sistema ERP integrado para EDARSA con CRM Comercial Enterprise, conectado a múltiples fuentes de datos SQL Server (MPRO, SoftRestaurant, EDARSAHUB).

## Máximas del Proyecto
1. **EDARSAHUB SQL Server es el cerebro absoluto** - CERO dependencias de MongoDB
2. **Política de Autorización Controlada** - No asumir reglas; esperar autorización explícita
3. **No Testing Agent** - Pruebas exclusivas vía cURL, bash, python -c

## Arquitectura Técnica
- **Frontend**: React (`/app/frontend/src/`)
- **Backend**: FastAPI (`/app/backend/`)
- **Base de Datos Principal**: EDARSAHUB SQL Server (54.39.104.176)
- **Legacy (ELIMINADO)**: MongoDB → Reemplazado por StubDatabase

## Credenciales de Prueba
- Admin: `admin@edarsa.com` / `admin123`

---

## Estado Actual (24 Mayo 2026)

### ✅ Completado

#### Migración MongoDB → SQL Server (COMPLETA)
- [x] Auth/Login migrado a SQL (login < 1s)
- [x] RBAC migrado a SQL Server (Usuario_Roles)
- [x] **Tablas Sesiones/SesionesHistorico creadas**
- [x] Scheduler usa StubDatabase para operaciones no críticas
- [x] **Tablas Scheduler_* creadas para tracking de jobs**
- [x] `sql_repository.py` creado con funciones SQL

#### CRM Comercial Enterprise (Fase 4)
- [x] Backend endpoints creados (`/api/crm/*`)
- [x] Datos: 18 cuentas, 2 cotizaciones
- [x] Rutas frontend y submenús agregados

#### Traceback Fantasma Resuelto (24 Mayo 2026)
- [x] **PROBLEMA**: Jobs del scheduler reportaban `AttributeError: 'NoneType' object has no attribute 'servers'`
- [x] **CAUSA**: Bytecode cacheado (archivos `.pyc` y `__pycache__`) ejecutando código viejo
- [x] **SOLUCIÓN**: Purga completa de `__pycache__` + reinicio de backend
- [x] **ESTADO**: Backend limpio, sin errores de traceback

#### Migración P0 Workflows/SLA (24 Mayo 2026)
- [x] **OrquestadorService migrado a SQL** (11 → 0 refs MongoDB)
- [x] **SLA Service migrado a SQL** (17 → 0 refs MongoDB)
- [x] **Tablas creadas en EDARSAHUB**:
  - `Workflow_Inventarios`
  - `Tareas_Inventario`
  - `Workflow_DetalleDiferencias`
  - `Inventarios_SinAsignar`
  - `Alertas_Sistema`
  - `Configuracion_Operativa`
  - `Config_Asignaciones`
- [x] **sql_repository.py creado** en `/app/backend/modules/fase2_operativo/`

#### Migración Referencias MongoDB Restantes (24 Mayo 2026)
- [x] **config_asignaciones_repository.py migrado a SQL** (8 → 0 refs)
- [x] **cargos_service.py protegido con stub** (2 refs protegidas)
- [x] **automatizacion_compras_service.py protegido** (5 refs protegidas)
- [x] **document_data_service.py protegido** (1 ref protegida)
- [x] **auditoria_programada_service.py protegido** (1 ref protegida)
- [x] **estructura_service.py ya tenía protección** (6 refs protegidas)
- [x] **Core Communications protegidos** (service, dispatcher, audit_service)
- [x] **Scripts deprecated marcados** (carga_historica, test_e2e)
- [x] **Referencias MongoDB reducidas**: 80 → 21 en producción (-74%)
- [x] **Total deprecated/tests**: 25 refs (no afectan producción)

### 🔄 En Progreso

#### Jobs del Scheduler
- [x] `inventarios_detector` y `pedidos_detector` con protección `_is_stub_db()`
- [x] 9 jobs funcionando (sync_comercial, notificaciones, etc.)

### ⏳ Pendiente

#### P1 - Alta Prioridad
1. **Tablajería Fase 6**: Inventarios, Costeo y Contabilidad
2. **Seguridad**: Remover credenciales hardcodeadas en Tablajería

#### P2 - Media Prioridad
3. **CRM UI**: Completar vistas funcionales

---

## Archivos Clave - Scheduler

### SQL Repository (Nuevo)
- `/app/backend/core/scheduler/sql_repository.py` - Funciones SQL para jobs

### Jobs Modificados
- `/app/backend/core/scheduler/jobs/inventarios_detector_job.py`
- `/app/backend/core/scheduler/jobs/pedidos_detector_job.py`

### Scripts
- `/app/backend/scripts/create_scheduler_tables.py`

---

## Tablas SQL Server (EDARSAHUB)

### Scheduler_InventariosProcesados
```sql
CREATE TABLE Scheduler_InventariosProcesados (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    SistemaOrigen VARCHAR(50) NOT NULL,
    ServerID VARCHAR(50) NOT NULL,
    SucursalID VARCHAR(50) NOT NULL,
    AlmacenID VARCHAR(50) NOT NULL,
    FolioInventario VARCHAR(100) NOT NULL,
    Estado VARCHAR(20) DEFAULT 'EN_PROCESO',
    ...
);
```

### Scheduler_PedidosProcesados
```sql
CREATE TABLE Scheduler_PedidosProcesados (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    SistemaOrigen VARCHAR(50) NOT NULL,
    ServerID VARCHAR(50) NOT NULL,
    EmpresaID VARCHAR(50) NOT NULL,
    FolioPedido VARCHAR(100) NOT NULL,
    ...
);
```

### Scheduler_BitacoraJobs
```sql
CREATE TABLE Scheduler_BitacoraJobs (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    JobName VARCHAR(100) NOT NULL,
    RunID VARCHAR(50) NOT NULL,
    Accion VARCHAR(50) NOT NULL,
    ...
);
```

---

## Configuración Scheduler (.env)

```bash
# Jobs deshabilitados temporalmente
SCHEDULER_INVENTARIOS_ENABLED=false
SCHEDULER_PEDIDOS_ENABLED=false
```

---

## Notas Técnicas

### Jobs Funcionando (9)
- sync_comercial_abiertas_v2
- sync_comercial_v2
- sync_short_comercial
- notifications_dispatcher
- sla_processor
- sync_propinas_tpv_incremental
- sync_nomina_ciclos
- sync_ingresos
- cleanup_locks

### Jobs Deshabilitados (2)
- inventarios_detector - Requiere migración completa
- pedidos_detector - Requiere migración completa
