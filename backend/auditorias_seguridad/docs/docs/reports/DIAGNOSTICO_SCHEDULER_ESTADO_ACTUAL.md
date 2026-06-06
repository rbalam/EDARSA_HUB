# DIAGNÓSTICO PASIVO: Estado del Scheduler EDARSAHUB

**Fecha:** 2026-05-25  
**Objetivo:** Evaluar estado actual antes de implementar Consola Administrativa Scheduler

---

## 1. ESTRUCTURA BACKEND EXISTENTE

### 1.1 Directorios
```
/app/backend/core/scheduler/
├── __init__.py
├── config.py                   # Configuración de jobs
├── job_logger.py               # Logging de ejecuciones
├── jobs/                       # Handlers de jobs
│   ├── auditorias_job.py
│   ├── base_job.py
│   ├── cava_socios_monthly_job.py
│   ├── crm_sync_job.py
│   ├── detect_nuevos_compras_job.py
│   ├── inventarios_detector_job.py
│   ├── notifications_job.py
│   ├── pedidos_detector_job.py
│   ├── sla_job.py
│   ├── sync_comercial_abiertas_v2_job.py
│   ├── sync_comercial_v2_job.py       # ← Handler oficial para CIENFUEGOS
│   ├── sync_compras_job.py
│   ├── sync_ingresos_job.py
│   ├── sync_nightly_comercial_job.py
│   ├── sync_propinas_tpv_job.py
│   └── sync_short_comercial_job.py
├── locks/
│   └── distributed_lock.py
├── routes.py                   # Endpoints API v2/scheduler
├── scheduler_manager.py        # Manager central (APScheduler)
└── sql_repository.py           # Funciones SQL para scheduler
```

### 1.2 Archivos Clave
- **scheduler_manager.py**: Manager singleton, usa APScheduler, controla ciclo de vida
- **routes.py**: Endpoints bajo `/api/v2/scheduler/`
- **sql_repository.py**: Repositorio SQL para jobs (reemplaza MongoDB)
- **config.py**: Configuración de jobs (interval, enabled, etc.)

---

## 2. ENDPOINTS EXISTENTES

| Endpoint | Método | Permiso | Descripción |
|----------|--------|---------|-------------|
| `/api/v2/scheduler/status` | GET | SCHEDULER_VER | Estado del scheduler |
| `/api/v2/scheduler/jobs/{job_id}` | GET | SCHEDULER_VER | Info de un job |
| `/api/v2/scheduler/jobs/{job_id}/run` | POST | SCHEDULER_ADMIN | Ejecutar job manual |
| `/api/v2/scheduler/jobs/{job_id}/pause` | POST | SCHEDULER_GESTIONAR | Pausar job |
| `/api/v2/scheduler/jobs/{job_id}/resume` | POST | SCHEDULER_GESTIONAR | Reanudar job |
| `/api/v2/scheduler/logs` | GET | SCHEDULER_VER | Historial de ejecuciones |
| `/api/v2/scheduler/logs/stats` | GET | SCHEDULER_VER | Estadísticas |
| `/api/v2/scheduler/config` | GET | SCHEDULER_VER | Configuración |
| `/api/v2/scheduler/locks` | GET | SCHEDULER_VER | Locks activos |

---

## 3. JOBS REGISTRADOS

| Job ID | Handler | Módulo | Intervalo |
|--------|---------|--------|-----------|
| sla_processor | sla_job | SLA | - |
| notifications_dispatcher | notifications_job | Notificaciones | - |
| auditorias_scheduler | auditorias_job | Auditorías | - |
| pedidos_detector | pedidos_detector_job | Compras | - |
| inventarios_detector | inventarios_detector_job | Inventarios | - |
| sync_short_comercial | sync_short_comercial_job | Comercial | 15 min |
| sync_nightly_comercial | sync_nightly_comercial_job | Comercial | Nocturno |
| sync_ingresos_incremental | sync_ingresos_job | Finanzas | - |
| sync_propinas_tpv_incremental | sync_propinas_tpv_job | Finanzas | - |
| **sync_comercial_v2** | **sync_comercial_v2_job** | **Comercial V2** | **15 min** |
| sync_comercial_abiertas_v2 | sync_comercial_abiertas_v2_job | Comercial V2 | 5 min |
| cava_socios_monthly | cava_socios_monthly_job | Cava | Mensual |
| crm_sync | crm_sync_job | CRM | - |
| crm_sla_check | crm_sync_job | CRM | - |

---

## 4. TABLAS SQL EXISTENTES

### 4.1 Tablas del Scheduler
| Tabla | Propósito | Estado |
|-------|-----------|--------|
| `Scheduler_BitacoraJobs` | Log de acciones de jobs | ✅ EXISTE |
| `Scheduler_InventariosProcesados` | Inventarios detectados | ✅ EXISTE |
| `Scheduler_PedidosProcesados` | Pedidos detectados | ✅ EXISTE |

### 4.2 Tablas de Sync (por módulo)
| Tabla | Propósito | Estado |
|-------|-----------|--------|
| `Comercial_SyncLog_v2` | Log de sync comercial v2 | ✅ EXISTE |
| `Compras_Sync_Log` | Log de sync compras | ✅ EXISTE |
| `Compras_Sync_Checkpoint` | Checkpoints compras | ✅ EXISTE |
| `Finanzas_CortesCaja_SyncLog` | Log de sync finanzas | ✅ EXISTE |
| `Finanzas_CuadresZ_SyncLog` | Log de cuadres Z | ✅ EXISTE |
| `Finanzas_PropinasTPV_SyncLog` | Log de propinas | ✅ EXISTE |
| `Sync_Control_Ejecuciones` | Control general | ✅ EXISTE |

### 4.3 Tablas Sistema_Scheduler_* 
| Tabla | Estado |
|-------|--------|
| `Sistema_Scheduler_Jobs` | ❌ NO EXISTE |
| `Sistema_Scheduler_Ejecuciones` | ❌ NO EXISTE |
| `Sistema_Scheduler_Logs` | ❌ NO EXISTE |
| `Sistema_Scheduler_Config` | ❌ NO EXISTE |

---

## 5. FRONTEND EXISTENTE

### 5.1 Página Scheduler
- **Ubicación:** `/app/frontend/src/pages/Scheduler.jsx`
- **Estado:** ✅ EXISTE
- **Funcionalidades:**
  - Dashboard con KPIs
  - Lista de jobs con estados
  - Historial de ejecuciones con filtros
  - Acciones: Ejecutar, Pausar, Reanudar
  - Auto-refresh configurable
  - RBAC integrado

### 5.2 Endpoints Frontend Consume
- `GET /api/v2/scheduler/status`
- `GET /api/v2/scheduler/config`
- `GET /api/v2/scheduler/logs`
- `GET /api/v2/scheduler/logs/stats`
- `POST /api/v2/scheduler/jobs/{id}/run`
- `POST /api/v2/scheduler/jobs/{id}/pause`
- `POST /api/v2/scheduler/jobs/{id}/resume`

---

## 6. DEPENDENCIAS MONGODB

### 6.1 Estado Actual
- **MongoDB ELIMINADO del sistema**
- Se usa `StubDatabase` para compatibilidad
- `job_logger.py` detecta StubDatabase y retorna vacío
- `scheduler_manager.py` opera sin persistencia real en MongoDB

### 6.2 Archivos con Referencias MongoDB (Comentarios Legacy)
- `scheduler_manager.py`: Comentarios mencionan MongoDB para locks
- `job_logger.py`: Usa StubDatabase
- `sync_comercial_v2_job.py`: Menciona "MongoDB solo para locks técnicos"

---

## 7. HANDLER PARA CIENFUEGOS

### 7.1 Handler Oficial
- **Archivo:** `/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py`
- **Función:** `sync_softrestaurant_ventas_cerradas()`
- **Tabla Destino:** `Comercial_KPIs_Diarios_v2`
- **Log:** `Comercial_SyncLog_v2`
- **Características:**
  - Usa credenciales de `Servidores_Conexiones`
  - Separa propinas del KPI de ventas
  - UPSERT idempotente (evita duplicados)

### 7.2 Configuración de Unidades
```python
CIENFUEGOS = {
    'unidad_negocio_id': 'CIENFUEGOS',
    'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b',
    'sistema': 'SOFTRESTAURANT',
    'sucursal_id': 'DEFAULT'
}
```

---

## 8. BRECHAS IDENTIFICADAS

### 8.1 Tablas Faltantes
1. ❌ `Sistema_Scheduler_Jobs` - Catálogo de jobs administrable
2. ❌ `Sistema_Scheduler_Ejecuciones` - Historial detallado
3. ❌ `Sistema_Scheduler_Logs` - Logs por ejecución
4. ❌ `Sistema_Scheduler_Config` - Configuración global
5. ❌ `Sistema_Scheduler_ReSyncSolicitudes` - Solicitudes de re-sync

### 8.2 Endpoints Faltantes
1. ❌ `POST /api/admin/scheduler/resync/validate` - Validar re-sync
2. ❌ `POST /api/admin/scheduler/resync/execute` - Ejecutar re-sync
3. ❌ `GET /api/admin/scheduler/dashboard` - Dashboard administrativo
4. ❌ `GET /api/admin/scheduler/diagnostics` - Diagnóstico

### 8.3 Frontend Faltante
1. ❌ Pestaña "Re-sync Manual" con dry_run
2. ❌ Pestaña "Diagnóstico" del sistema
3. ❌ Panel de configuración avanzada

---

## 9. ELEMENTOS A REUTILIZAR

| Elemento | Ubicación | Acción |
|----------|-----------|--------|
| `sync_softrestaurant_ventas_cerradas()` | sync_comercial_edarsahub.py | REUTILIZAR |
| `Comercial_SyncLog_v2` | EDARSAHUB | REUTILIZAR |
| `Scheduler_BitacoraJobs` | EDARSAHUB | EXTENDER |
| `Scheduler.jsx` | Frontend | EXTENDER |
| `/api/v2/scheduler/*` | routes.py | EXTENDER |

---

## 10. PLAN DE IMPLEMENTACIÓN

### Fase 0 (Mínima para CIENFUEGOS)
1. Crear endpoint `/api/admin/scheduler/resync/validate`
2. Crear endpoint `/api/admin/scheduler/resync/execute`
3. Integrar con `sync_softrestaurant_ventas_cerradas()`
4. Soportar `dry_run`
5. Registrar en `Comercial_SyncLog_v2` y `Scheduler_BitacoraJobs`

### Fase 1 (Consola Completa)
1. Crear tablas `Sistema_Scheduler_*`
2. Migrar configuración de jobs a SQL
3. Crear endpoints de administración
4. Extender frontend con pestañas

---

**Firmado:** E1 Agent  
**Estado:** DIAGNÓSTICO COMPLETO - LISTO PARA IMPLEMENTAR
