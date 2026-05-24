# AUDITORÍA DE DEPENDENCIAS MONGODB - EDARSA HUB
## Fecha: 2026-05-24

---

## 📊 RESUMEN EJECUTIVO

| Métrica | Valor |
|---------|-------|
| Referencias `self.db.*` | 80 |
| Imports de MongoDB | 100 |
| Archivos Afectados (Prod) | ~15 |
| Colecciones Usadas | 30 |

---

## 🔴 MÓDULOS CRÍTICOS (Producción Activa)

### 1. **SLA Service** (17 referencias) - IMPACTO ALTO
- Archivo: `/app/backend/modules/fase2_operativo/services/sla_service.py`
- Colecciones: `tareas_inventario`, `workflows_inventario`, `configuracion_operativo`
- **Funcionalidad Afectada**: Dashboard de SLAs, monitoreo de tareas, alertas de vencimiento

### 2. **Orquestador Service** (11 referencias) - IMPACTO ALTO
- Archivo: `/app/backend/modules/fase2_operativo/services/orquestador_service.py`
- Colecciones: `workflow_inventarios`, `users`, `config_asignaciones`, `detalle_diferencias`, `tareas_inventario`, `alertas_sistema`, `inventarios_sin_asignar`, `configuracion_operativa`
- **Funcionalidad Afectada**: Creación de workflows, asignación automática de tareas, alertas del sistema

### 3. **Config Asignaciones Repository** (8 referencias) - IMPACTO MEDIO
- Archivo: `/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py`
- Colecciones: `empresas`, `sucursales_catalogo`, `sucursal_servidor_map`, `users`, `almacenes_catalogo`
- **Funcionalidad Afectada**: Pantalla de configuración de asignaciones

### 4. **Estructura Service** (6 referencias) - IMPACTO MEDIO
- Archivo: `/app/backend/modules/sistema/estructura_service.py`
- Colecciones: `sec_empresas`, `sec_unidades_negocio`, `sec_sucursales`, `sec_mapeo_servidor_sucursal`, `sec_permisos_catalogo`, `sec_bitacora_acceso`
- **Funcionalidad Afectada**: Árbol organizacional, permisos, bitácora de accesos

### 5. **Automatización Compras Service** (5 referencias) - IMPACTO MEDIO
- Archivo: `/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py`
- Colecciones: `inventarios_fisicos_procesados`, `users`
- **Funcionalidad Afectada**: Auditoría operativa de compras

---

## 🟡 MÓDULOS SECUNDARIOS (Core Backend)

### Scheduler Jobs (3 referencias total)
- `inventarios_detector_job.py` - 1 ref (usa `_is_stub_db()`)
- `pedidos_detector_job.py` - 1 ref (usa `_is_stub_db()`)
- `notifications_job.py` - 1 ref

### Communications (3 referencias total)
- `dispatcher.py` - 1 ref (`notification_provider_config`)
- `service.py` - 1 ref (`users`)
- `audit_service.py` - 1 ref (`notification_log`)

---

## 🔵 ARCHIVOS IGNORABLES (No producción)

### Scripts de carga histórica
- `/app/backend/scripts/carga_historica_fase23.py` - 8 refs

### Tests
- `/app/backend/tests/test_e2e_flujo_completo.py` - 15 refs

---

## 🖥️ PANTALLAS FRONTEND AFECTADAS

| Pantalla | Endpoint Dependiente | Riesgo |
|----------|---------------------|--------|
| Dashboard SLA | `/api/sla/*` | 🔴 Alto |
| Orquestador | `/api/orquestador/*` | 🔴 Alto |
| Config Asignaciones | `/api/config-asignaciones/*` | 🟡 Medio |
| Auditorías Programadas | `/api/v2/auditorias-programadas/*` | 🟡 Medio |
| Autorización Compras | `/api/compras/auditoria-operativa` | 🟡 Medio |
| Estructura Organizacional | `/api/sistema/estructura/*` | 🟡 Medio |

---

## 📋 COLECCIONES MONGODB → TABLAS SQL REQUERIDAS

| Colección MongoDB | Tabla SQL Propuesta | Estado |
|-------------------|---------------------|--------|
| `workflow_inventarios` | `Workflow_Inventarios` | ⏳ Pendiente |
| `tareas_inventario` | `Tareas_Inventario` | ⏳ Pendiente |
| `detalle_diferencias` | `Workflow_DetalleDiferencias` | ⏳ Pendiente |
| `config_asignaciones` | `Config_Asignaciones` | ⏳ Pendiente |
| `alertas_sistema` | `Alertas_Sistema` | ⏳ Pendiente |
| `inventarios_sin_asignar` | `Inventarios_SinAsignar` | ⏳ Pendiente |
| `configuracion_operativa` | `Configuracion_Operativa` | ⏳ Pendiente |
| `notification_queue` | `Notification_Queue` | ⏳ Pendiente |
| `notification_provider_config` | `Notification_Providers` | ⏳ Pendiente |
| `notification_log` | `Notification_Log` | ⏳ Pendiente |

---

## 📈 PLAN DE MIGRACIÓN RECOMENDADO

### Fase 1 (Scheduler - COMPLETADO ✅)
- `Scheduler_InventariosProcesados` - ✅
- `Scheduler_PedidosProcesados` - ✅
- `Scheduler_BitacoraJobs` - ✅
- `Sesiones` - ✅

### Fase 2 (Orquestador/SLA - SIGUIENTE)
- Crear `Workflow_Inventarios`
- Crear `Tareas_Inventario`
- Crear `Workflow_DetalleDiferencias`
- Migrar `orquestador_service.py`
- Migrar `sla_service.py`

### Fase 3 (Configuración)
- Crear tablas `Config_*`
- Migrar `config_asignaciones_repository.py`
- Migrar `estructura_service.py`

### Fase 4 (Notificaciones)
- Crear tablas `Notification_*`
- Migrar módulo `communications`

---

## ⚠️ NOTAS IMPORTANTES

1. **StubDatabase activo**: Las 80 referencias actuales pasan por `mongo_stub.py` que retorna datos vacíos silenciosamente. No hay crashes, pero tampoco funcionalidad real.

2. **Scheduler funcionando**: Los jobs `inventarios_detector` y `pedidos_detector` ya usan `sql_repository.py` para tracking.

3. **Traceback fantasma resuelto**: Después de purgar `__pycache__` y reiniciar, los logs están limpios.


---

## 🔄 ACTUALIZACIÓN POST-MIGRACIÓN (24 Mayo 2026 - 02:20)

### Servicios Migrados a SQL Server

| Servicio | Referencias Antes | Referencias Después | Reducción |
|----------|------------------|--------------------| ----------|
| OrquestadorService | 11 | 0 | ✅ -11 |
| SLA Service | 17 | 0 | ✅ -17 |
| **TOTAL** | **80** | **52** | **-28** |

### Tablas SQL Creadas

| Tabla | Estado |
|-------|--------|
| `Workflow_Inventarios` | ✅ Creada |
| `Tareas_Inventario` | ✅ Creada |
| `Workflow_DetalleDiferencias` | ✅ Creada |
| `Inventarios_SinAsignar` | ✅ Creada |
| `Alertas_Sistema` | ✅ Creada |
| `Configuracion_Operativa` | ✅ Creada (con valores SLA por defecto) |
| `Config_Asignaciones` | ✅ Creada |

### Archivos Creados/Modificados

1. `/app/backend/modules/fase2_operativo/sql_repository.py` - **NUEVO**
   - Funciones SQL para workflows, tareas, alertas, configuración
   
2. `/app/backend/modules/fase2_operativo/services/orquestador_service.py` - **MIGRADO**
   - Ya no usa MongoDB
   - Usa sql_repository.py para todas las operaciones

3. `/app/backend/modules/fase2_operativo/services/sla_service.py` - **MIGRADO**
   - Ya no usa MongoDB
   - Usa sql_repository.py para todas las operaciones

4. `/app/backend/scripts/create_workflow_tables.sql` - **NUEVO**
   - Script de creación de tablas en EDARSAHUB

### Referencias MongoDB Restantes (52)

| Archivo | Refs | Prioridad |
|---------|------|-----------|
| automatizacion_compras_service.py | 5 | P2 |
| config_asignaciones_repository.py | 8 | P2 |
| estructura_service.py | 6 | P2 |
| scripts/carga_historica_fase23.py | 8 | P3 (scripts) |
| tests/test_e2e_flujo_completo.py | 15 | P3 (tests) |
| Otros (scheduler, communications) | 10 | P3 |
