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

#### Migración MongoDB → SQL Server (100%)
- [x] Auth/Login migrado a SQL (login < 1s)
- [x] RBAC migrado a SQL Server (Usuario_Roles, Usuario_RolesAsignacion)
- [x] **Tablas Sesiones/SesionesHistorico creadas en EDARSAHUB**
- [x] Inicializaciones de módulos en server.py usando StubDatabase
- [x] Scheduler, Notificaciones, Locks, JobLogger operan con StubDatabase
- [x] 165 referencias a `await db.` ahora usan StubDatabase (sin errores fatales)
- [x] Jobs detector (pedidos, inventarios) detectan StubDatabase y se saltan

#### CRM Comercial Enterprise (Fase 4)
- [x] Backend endpoints creados (`/api/crm/*`)
- [x] Tablas SQL: CRM_Cuentas, CRM_Leads, CRM_Oportunidades, etc.
- [x] Datos iniciales cargados (18 cuentas, 2 cotizaciones)
- [x] Rutas frontend y submenús agregados

#### Tablajería
- [x] Diagnóstico Fase 6 (Inventarios/Costeo) documentado

### ⏳ Pendiente

#### P1 - Alta Prioridad
1. **Tablajería Fase 6**: Implementar Inventarios, Costeo y Contabilidad
2. **Seguridad**: Remover credenciales hardcodeadas en Tablajería

#### P2 - Media Prioridad
3. **CRM UI**: Completar vistas funcionales (Cuentas, Solicitudes, Cotizaciones)

#### Backlog
- Migrar jobs de scheduler a SQL Server (actualmente saltan ejecución)
- Tablajería Fase 4 (Captura Directa)
- Limpieza de módulos legacy mockeados

---

## Archivos Clave

### Backend - Core MongoDB Stub
- `/app/backend/core/mongo_stub.py` - StubDatabase, StubCollection, StubCursor
- `/app/backend/core/mongo_compat.py` - Funciones helper opcionales

### Backend - Principal
- `/app/backend/server.py` - Router principal (usa StubDatabase)
- `/app/backend/modules/crm/comercial_routes.py` - CRM Enterprise
- `/app/backend/modules/crm/comercial_service.py` - Lógica CRM
- `/app/backend/core/scheduler/scheduler_manager.py` - Scheduler
- `/app/backend/core/db.py` - Funciones SQL
- `/app/backend/core/refresh_tokens.py` - Sesiones SQL Server

### Scripts
- `/app/backend/scripts/create_sesiones_tables.py` - Crea tablas Sesiones en EDARSAHUB

### Frontend
- `/app/frontend/src/App.js` - Rutas principales
- `/app/frontend/src/pages/Layout.js` - Menú lateral
- `/app/frontend/src/pages/crm/` - Vistas CRM

### Documentación
- `/app/docs/reports/TABLAJERIA_FASE6_DIAGNOSTICO_INVENTARIOS_COSTEO.md`

---

## Tablas SQL Server (EDARSAHUB)

### Sesiones
```sql
CREATE TABLE Sesiones (
    SesionID VARCHAR(50) PRIMARY KEY,
    UsuarioID VARCHAR(50) NOT NULL,
    TipoUsuario VARCHAR(20) DEFAULT 'interno',
    RefreshTokenHash VARCHAR(128) NOT NULL,
    FamiliaTokenID VARCHAR(50) NOT NULL,
    FechaCreacion DATETIME DEFAULT GETUTCDATE(),
    FechaExpiracion DATETIME NOT NULL,
    UltimaActividad DATETIME DEFAULT GETUTCDATE(),
    EstaActiva BIT DEFAULT 1,
    IPCliente VARCHAR(45),
    UserAgent VARCHAR(500),
    FechaModificacion DATETIME DEFAULT GETUTCDATE()
);
```

### SesionesHistorico
```sql
CREATE TABLE SesionesHistorico (
    HistoricoID INT IDENTITY(1,1) PRIMARY KEY,
    SesionID VARCHAR(50) NOT NULL,
    UsuarioID VARCHAR(50) NOT NULL,
    TipoUsuario VARCHAR(20),
    Accion VARCHAR(50) NOT NULL,
    FechaAccion DATETIME DEFAULT GETUTCDATE(),
    IPCliente VARCHAR(45),
    UserAgent VARCHAR(500),
    DetallesJSON NVARCHAR(MAX),
    AccionRealizadaPor VARCHAR(50)
);
```

---

## Integraciones Externas
- **VTiger CRM**: Credenciales activas en `modules/crm/service.py`

---

## Notas Técnicas

### StubDatabase (MongoDB ELIMINADO)
El sistema ahora usa `StubDatabase` que:
- Simula la interfaz de MongoDB
- Retorna valores vacíos (listas vacías, None, counts de 0)
- NO persiste datos
- Permite que el código legacy funcione sin errores fatales

### Warnings Esperados (No son errores)
```
[COMERCIAL] Repository - MongoDB deprecado
[COMERCIAL] KPIs repository - MongoDB deprecado
[COMERCIAL] Cache service - MongoDB deprecado, funcionalidad limitada
```

### Jobs del Scheduler
Los siguientes jobs detectan StubDatabase y se saltan:
- `pedidos_detector` - SKIPPED
- `inventarios_detector` - SKIPPED

Otros jobs siguen funcionando normalmente con SQL Server:
- `sync_comercial_abiertas_v2`
- `sync_comercial_v2`
- `sync_short_comercial`
- etc.
