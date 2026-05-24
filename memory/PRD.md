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
- **Legacy (en deprecación)**: MongoDB

## Credenciales de Prueba
- Admin: `admin@edarsa.com` / `admin123`

---

## Estado Actual (24 Mayo 2026)

### ✅ Completado

#### Migración MongoDB → SQL Server
- [x] Auth/Login migrado a SQL (login < 1s)
- [x] RBAC migrado a SQL Server (Usuario_Roles, Usuario_RolesAsignacion)
- [x] Inicializaciones de módulos en server.py pasadas a `None`
- [x] Scheduler, Notificaciones, Locks, JobLogger operan en modo SQL-only

#### CRM Comercial Enterprise (Fase 4)
- [x] Backend endpoints creados (`/api/crm/*`)
- [x] Tablas SQL: CRM_Cuentas, CRM_Leads, CRM_Oportunidades, etc.
- [x] Datos iniciales cargados (18 cuentas, 2 cotizaciones)
- [x] Rutas frontend y submenús agregados

#### Tablajería
- [x] Diagnóstico Fase 6 (Inventarios/Costeo) documentado

### 🔄 En Progreso

#### Limpieza MongoDB
- [x] Inicializaciones en server.py (COMPLETADO)
- [ ] Referencias `await db.` en endpoints (165 restantes)
- [ ] Tabla `Sesiones` en EDARSAHUB para refresh tokens

### ⏳ Pendiente

#### P1 - Alta Prioridad
1. **Tablajería Fase 6**: Implementar Inventarios, Costeo y Contabilidad
2. **Seguridad**: Remover credenciales hardcodeadas en Tablajería

#### P2 - Media Prioridad
3. **CRM UI**: Completar vistas funcionales (Cuentas, Solicitudes, Cotizaciones)
4. **CRM Fase 3**: Tablas de Integraciones Externas

#### Backlog
- Tablajería Fase 4 (Captura Directa)
- Limpieza de módulos legacy mockeados
- Migración completa de colecciones MongoDB a SQL

---

## Archivos Clave

### Backend
- `/app/backend/server.py` - Router principal (17,926 líneas)
- `/app/backend/modules/crm/comercial_routes.py` - CRM Enterprise
- `/app/backend/modules/crm/comercial_service.py` - Lógica CRM
- `/app/backend/core/scheduler/scheduler_manager.py` - Scheduler
- `/app/backend/core/db.py` - Funciones SQL

### Frontend
- `/app/frontend/src/App.js` - Rutas principales
- `/app/frontend/src/pages/Layout.js` - Menú lateral
- `/app/frontend/src/pages/crm/` - Vistas CRM

### Documentación
- `/app/docs/reports/TABLAJERIA_FASE6_DIAGNOSTICO_INVENTARIOS_COSTEO.md`

---

## Integraciones Externas
- **VTiger CRM**: Credenciales activas en `modules/crm/service.py`

---

## Notas Técnicas

### Warnings Esperados (No son errores)
```
[COMERCIAL] Repository - MongoDB deprecado
[NOTIFICATIONS] Inicializado SIN MongoDB - Modo degradado SQL-only
[SCHEDULER] Inicializando SIN MongoDB - Locks distribuidos deshabilitados
Invalid object name 'Sesiones' - Tabla pendiente de crear
```

### Módulos en Modo Degradado
- `core/communications/routes.py` - Sin persistencia de templates
- `core/scheduler/` - Sin locks distribuidos MongoDB
- `modules/fase2_operativo/` - Workflows mockeados
