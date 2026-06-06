# FASE 4A — Diagnóstico Pasivo de Reglas Vivas de Negocio y Dependencias MongoDB

**Fecha:** 2026-05-14  
**Estado:** DIAGNÓSTICO COMPLETADO (SIN CAMBIOS DE CÓDIGO)  
**Autorización:** FASE 4A - Solo diagnóstico

---

## 1. RESUMEN EJECUTIVO

### Hallazgos Principales:
- **775 líneas** con referencias a MongoDB/Motor/PyMongo
- **568 líneas** con acceso directo a colecciones (`db.`)
- **41 archivos** importan activamente motor/pymongo
- **295 operaciones de lectura** (find, aggregate)
- **150 operaciones de escritura** (insert, update, delete)
- **~50 colecciones MongoDB** referenciadas
- **234 líneas** son solo comentarios/documentación (ya migrados)

### Módulos con Mayor Dependencia MongoDB:
| Módulo | Referencias | Estado |
|--------|-------------|--------|
| fase2_operativo | 118 | **ACTIVO - CRÍTICO** |
| finanzas | 93 | Mayormente comentarios |
| comercial | 79 | **ACTIVO - CACHE** |
| api_connections | 33 | ACTIVO |
| auth | 32 | **MIGRADO** (comentarios) |
| configuracion | 22 | ACTIVO |

### Estado General:
- **Módulos Auth/Contexto/RBAC core:** MIGRADOS a SQL
- **Comercial V2:** USA EDARSAHUB SQL
- **Ventas del Día:** MIGRADO a EDARSAHUB SQL
- **FASE2_OPERATIVO:** DEPENDENCIA FUERTE de MongoDB
- **RBAC repository:** DEPENDENCIA FUERTE de MongoDB

---

## 2. ESTADO GENERAL DE MONGODB EN EL SISTEMA

### Conexión Activa:
```python
# server.py líneas 17 y 49
from motor.motor_asyncio import AsyncIOMotorClient
client = AsyncIOMotorClient(mongo_url)
```

### Base de Datos:
- Variable: `MONGO_URL` desde `.env`
- Base de datos activa: `edarsa_db`

### Uso Actual:
| Tipo | Cantidad |
|------|----------|
| Colecciones activas | ~50 |
| Lecturas por request | Variable |
| Escrituras por request | Variable |
| Indices creados | Múltiples en RBAC, tareas, workflows |

---

## 3. MATRIZ COMPLETA DE DEPENDENCIAS MONGODB ACTIVAS

### 3.1 COLECCIONES POR FRECUENCIA DE USO

| Colección | Referencias | Tipo | Estado | Riesgo |
|-----------|-------------|------|--------|--------|
| `db.servers` | 174 | Config | **MIGRADO** (comentarios/scripts) | BAJO |
| `db.users` | 43 | Auth | **MIGRADO PARCIAL** | MEDIO |
| `db.informes_auditoria` | 26 | Auditoría | ACTIVO | MEDIO |
| `db.tareas_inventario` | 20 | Operativo | **ACTIVO** | ALTO |
| `db.portal_suppliers` | 16 | Portal | ACTIVO | MEDIO |
| `db.nomina_ciclos` | 15 | Nómina | ACTIVO | MEDIO |
| `db.kpis_comercial` | 15 | Analítico | **ACTIVO** | ALTO |
| `db.solicitudes_catalogos` | 14 | Catálogos | ACTIVO | MEDIO |
| `db.workflow_inventarios` | 13 | Operativo | **ACTIVO** | ALTO |
| `db.server_sucursales_config` | 12 | Config | Migración parcial | BAJO |
| `db.comercial_cache` | 12 | Cache | **ACTIVO** | ALTO |
| `db.consultas_custom` | 11 | Queries | ACTIVO | BAJO |
| `db.sec_bitacora_admin` | 10 | Seguridad | ACTIVO | MEDIO |
| `db.notificaciones_log` | 10 | Notificaciones | ACTIVO | BAJO |
| `db.tareas_sistema` | 9 | Sistema | ACTIVO | MEDIO |
| `db.rbac_roles` | 9 | RBAC | **ACTIVO** | ALTO |
| `db.empresas` | 9 | Config | **MIGRADO** | BAJO |
| `db.rbac_usuarios_roles` | 8 | RBAC | **ACTIVO** | ALTO |
| `db.queries` | 7 | Queries | ACTIVO | BAJO |
| `db.rbac_permisos` | 6 | RBAC | **ACTIVO** | ALTO |
| `db.rbac_audit_log` | 5 | Auditoría | **ACTIVO** | MEDIO |

### 3.2 DEPENDENCIAS POR MÓDULO

#### FASE2_OPERATIVO (118 refs) - **CRÍTICO**
| Colección | Archivos | Operaciones |
|-----------|----------|-------------|
| `tareas_inventario` | 8 | CRUD completo |
| `workflow_inventarios` | 6 | CRUD completo |
| `notificaciones_log` | 4 | INSERT |
| `documentos_generados` | 3 | CRUD |
| `configuracion_operativa` | 3 | READ |
| `justificaciones_inventario` | 2 | CRUD |

#### COMERCIAL (79 refs)
| Colección | Archivos | Operaciones |
|-----------|----------|-------------|
| `comercial_cache` | 1 | CRUD completo |
| `kpis_comercial` | 2 | READ (históricos) |
| `servers` | Múltiples | **MIGRADO** (comentarios) |

#### CORE/RBAC (40+ refs) - **CRÍTICO**
| Colección | Archivos | Operaciones |
|-----------|----------|-------------|
| `rbac_permisos` | 1 | CRUD |
| `rbac_roles` | 1 | CRUD |
| `rbac_usuarios_roles` | 1 | CRUD |
| `rbac_audit_log` | 1 | INSERT |

---

## 4. MATRIZ DE DEPENDENCIAS MONGODB LEGACY/FALLBACK

| Tipo | Cantidad | Descripción |
|------|----------|-------------|
| Comentarios documentales | 234 líneas | Explican migraciones previas |
| Scripts de migración | 15+ archivos | En `/app/backend/scripts/` |
| Tests con mocks | 20+ archivos | En `/app/backend/tests/` |
| Fallbacks cache | 10+ lugares | Cache como respaldo |
| Código legacy comentado | Múltiple | Referencias `# FASE X` |

### Archivos Legacy/Scripts (NO producción):
```
/app/backend/scripts/run_historical_load_finanzas.py
/app/backend/scripts/precheck_conectividad.py
/app/backend/scripts/reconcile_servers_sql_mongo.py
/app/backend/scripts/carga_historica_fase23.py
/app/backend/scripts/encrypt_existing_server_secrets.py
/app/backend/scripts/encrypt_core_server_secrets.py
/app/backend/scripts/run_historical_load_compras.py
/app/backend/scripts/run_historical_load_24_months.py
/app/backend/scripts/validar_post_carga.py
```

---

## 5. MATRIZ DE REGLAS VIVAS DE NEGOCIO FUERA DE EDARSAHUB SQL

### 5.1 REGLAS EN RBAC MongoDB

| Regla | Ubicación | Tipo |
|-------|-----------|------|
| Permisos por módulo | `db.rbac_permisos` | Configuración |
| Roles del sistema | `db.rbac_roles` | Configuración |
| Asignación usuario-rol-sucursal | `db.rbac_usuarios_roles` | Relación |
| Auditoría RBAC | `db.rbac_audit_log` | Log |

**Archivo principal:** `/app/backend/core/rbac/repository.py`

### 5.2 REGLAS EN WORKFLOWS/TAREAS

| Regla | Ubicación | Tipo |
|-------|-----------|------|
| Flujos de inventario | `db.workflow_inventarios` | Proceso |
| Tareas pendientes | `db.tareas_inventario` | Operativo |
| Configuración operativa | `db.configuracion_operativa` | Config |
| SLAs y alertas | `db.alertas_sistema` | Monitoreo |

**Módulo:** `/app/backend/modules/fase2_operativo/`

### 5.3 REGLAS EN CACHE COMERCIAL

| Regla | Ubicación | Tipo |
|-------|-----------|------|
| KPIs cacheados | `db.comercial_cache` | Cache |
| KPIs históricos | `db.kpis_comercial` | Analítico |

**Módulo:** `/app/backend/modules/comercial/cache_service.py`

---

## 6. MÓDULOS AFECTADOS

| Módulo | Dependencia MongoDB | Estado | Prioridad Migración |
|--------|---------------------|--------|---------------------|
| `core/rbac` | **FUERTE** | Activo | P0 |
| `modules/fase2_operativo` | **FUERTE** | Activo | P1 |
| `modules/comercial` | MEDIA (cache) | Activo | P2 |
| `modules/configuracion` | MEDIA | Activo | P2 |
| `modules/finanzas` | BAJA | Mayormente migrado | P3 |
| `modules/compras` | BAJA | Migrado | P3 |
| `modules/auth` | **MIGRADO** | Solo comentarios | DONE |
| `modules/comercial_v2` | **MIGRADO** | SQL | DONE |

---

## 7. ENDPOINTS AFECTADOS

### Endpoints con MongoDB Activo:

| Endpoint | Módulo | Colección | Operación |
|----------|--------|-----------|-----------|
| `/api/rbac/roles` | core/rbac | rbac_roles | CRUD |
| `/api/rbac/permisos` | core/rbac | rbac_permisos | CRUD |
| `/api/rbac/usuarios-roles` | core/rbac | rbac_usuarios_roles | CRUD |
| `/api/fase2/tareas` | fase2_operativo | tareas_inventario | CRUD |
| `/api/fase2/workflows` | fase2_operativo | workflow_inventarios | CRUD |
| `/api/comercial/cache/*` | comercial | comercial_cache | CRUD |
| `/api/configuracion/asignaciones` | configuracion | config_asignaciones | CRUD |
| `/api/notificaciones/*` | fase2_operativo | notificaciones_log | INSERT |

---

## 8. JOBS AFECTADOS

| Job | Archivo | Colecciones | Estado |
|-----|---------|-------------|--------|
| `sync_short_comercial_job` | scheduler/jobs/ | kpis_comercial | **ACTIVO** |
| `sync_comercial_v2_job` | scheduler/jobs/ | kpis_comercial | **ACTIVO** |
| `sync_nightly_comercial_job` | scheduler/jobs/ | kpis_comercial | **ACTIVO** |
| `notifications_job` | scheduler/jobs/ | notificaciones_log | **ACTIVO** |
| `inventarios_detector_job` | scheduler/jobs/ | tareas_inventario | **ACTIVO** |
| `pedidos_detector_job` | scheduler/jobs/ | tareas_operativas_compras | **ACTIVO** |
| `sla_job` | scheduler/jobs/ | alertas_sistema | **ACTIVO** |
| `sync_comercial_abiertas_v2_job` | scheduler/jobs/ | **NINGUNA** | MIGRADO |

---

## 9. PANTALLAS AFECTADAS

| Pantalla/Menú | Módulo Backend | Dependencia MongoDB |
|---------------|----------------|---------------------|
| Tablero Ejecutivo | comercial | cache_service (fallback) |
| Administración RBAC | core/rbac | **FUERTE** |
| Tareas de Inventario | fase2_operativo | **FUERTE** |
| Workflows Operativos | fase2_operativo | **FUERTE** |
| Configuración Sistema | configuracion | MEDIA |
| Notificaciones | fase2_operativo | MEDIA |
| KPIs Históricos | comercial | kpis_comercial |

---

## 10. COLECCIONES MONGODB AÚN UTILIZADAS

### Activamente Usadas en Producción:
```
rbac_permisos           - Permisos RBAC
rbac_roles              - Roles del sistema
rbac_usuarios_roles     - Asignaciones usuario-rol
rbac_audit_log          - Auditoría RBAC
tareas_inventario       - Tareas operativas
workflow_inventarios    - Flujos de trabajo
comercial_cache         - Cache de KPIs
kpis_comercial          - KPIs históricos
notificaciones_log      - Log de notificaciones
configuracion_operativa - Config operativa
```

### Posiblemente Activas (requiere validación):
```
portal_suppliers        - Portal proveedores
nomina_ciclos          - Nómina
solicitudes_catalogos   - Catálogos
consultas_custom        - Queries custom
informes_auditoria     - Auditorías
sec_bitacora_admin     - Bitácora seguridad
```

### Legacy/Migradas (solo scripts/comentarios):
```
servers                 - MIGRADO a Servidores_Conexiones
users                   - MIGRADO a Usuario_Catalogo
empresas                - MIGRADO a Empresas
sucursales              - MIGRADO a Sucursales
```

---

## 11. TABLAS EDARSAHUB SQL DESTINO SUGERIDAS

| Colección MongoDB | Tabla SQL Sugerida | Existe |
|-------------------|-------------------|--------|
| `rbac_permisos` | `RBAC_Permisos` | NO |
| `rbac_roles` | `RBAC_Roles` | NO |
| `rbac_usuarios_roles` | `RBAC_UsuariosRoles` | NO |
| `rbac_audit_log` | `RBAC_AuditLog` | NO |
| `tareas_inventario` | `Operativo_Tareas` | NO |
| `workflow_inventarios` | `Operativo_Workflows` | NO |
| `comercial_cache` | `Comercial_Cache` | NO |
| `kpis_comercial` | `Comercial_KPIs_Historicos` | PARCIAL |
| `notificaciones_log` | `Sistema_NotificacionesLog` | NO |
| `configuracion_operativa` | `Sistema_ConfiguracionOperativa` | NO |

---

## 12. RIESGO DE MIGRACIÓN POR DEPENDENCIA

### RIESGO ALTO (Bloquean operación):
| Dependencia | Riesgo | Razón |
|-------------|--------|-------|
| RBAC MongoDB | **CRÍTICO** | Login y permisos dependen de esto |
| tareas_inventario | **ALTO** | Operación diaria de inventarios |
| workflow_inventarios | **ALTO** | Flujos de auditoría activos |

### RIESGO MEDIO (Funcionalidad degradada):
| Dependencia | Riesgo | Razón |
|-------------|--------|-------|
| comercial_cache | MEDIO | Fallback, no crítico |
| kpis_comercial | MEDIO | Solo históricos |
| notificaciones_log | MEDIO | Log, no bloquea |

### RIESGO BAJO (Sin impacto operativo):
| Dependencia | Riesgo | Razón |
|-------------|--------|-------|
| servers (legacy) | BAJO | Ya migrado |
| scripts de carga | BAJO | No producción |
| tests | BAJO | Solo desarrollo |

---

## 13. PRIORIZACIÓN RECOMENDADA PARA FASE 4B

### P0 - CRÍTICO (Bloquea eliminación MongoDB):
1. **RBAC MongoDB** (`rbac_permisos`, `rbac_roles`, `rbac_usuarios_roles`)
   - Migrar a tablas SQL: `RBAC_Permisos`, `RBAC_Roles`, `RBAC_UsuariosRoles`
   - Riesgo: ALTO (afecta login y permisos)
   
### P1 - ALTO (Dependencia operativa):
2. **Tareas/Workflows** (`tareas_inventario`, `workflow_inventarios`)
   - Migrar a tablas SQL: `Operativo_Tareas`, `Operativo_Workflows`
   - Riesgo: ALTO (operación diaria)

### P2 - MEDIO (Funcionalidad secundaria):
3. **Cache Comercial** (`comercial_cache`)
   - Evaluar si eliminar o migrar
   - Alternativa: Usar Redis o tabla temporal SQL

4. **KPIs Históricos** (`kpis_comercial`)
   - Ya existe parcialmente en EDARSAHUB
   - Consolidar en tabla única

### P3 - BAJO (Sin urgencia):
5. **Configuración operativa**
6. **Notificaciones**
7. **Portal proveedores**
8. **Nómina**

---

## 14. DEPENDENCIAS QUE BLOQUEAN ELIMINACIÓN FUTURA DE MONGODB

### BLOQUEADORES ABSOLUTOS:
1. **`core/rbac/repository.py`**
   - Todas las operaciones RBAC usan MongoDB
   - Sin migración, no se puede eliminar MongoDB
   
2. **`modules/fase2_operativo/*`**
   - 20+ colecciones activas
   - Workflows y tareas en producción

3. **`core/db.py`**
   - Inicializa conexión MongoDB global
   - Usado por ~40 módulos

### NO BLOQUEADORES (pero con referencias):
- Scripts de migración (eliminar después de migrar)
- Tests (actualizar mocks)
- Comentarios/documentación (actualizar texto)

---

## 15. ACCIONES QUE REQUIEREN AUTORIZACIÓN EXPLÍCITA

| Acción | Prioridad | Riesgo | Autorización Requerida |
|--------|-----------|--------|------------------------|
| Crear tablas RBAC_* en SQL | P0 | ALTO | SÍ |
| Migrar rbac/repository.py | P0 | ALTO | SÍ |
| Crear tablas Operativo_* | P1 | ALTO | SÍ |
| Migrar fase2_operativo | P1 | ALTO | SÍ |
| Eliminar comercial_cache | P2 | MEDIO | SÍ |
| Consolidar kpis_comercial | P2 | MEDIO | SÍ |
| Eliminar colecciones legacy | P3 | BAJO | SÍ |
| Actualizar tests | P3 | BAJO | NO |
| Limpiar comentarios | P3 | BAJO | NO |

---

## 16. CONFIRMACIÓN DE DIAGNÓSTICO PASIVO

### ✅ CONFIRMACIONES:

| Aspecto | Estado |
|---------|--------|
| Código modificado | ❌ NO |
| Tablas creadas | ❌ NO |
| Datos alterados | ❌ NO |
| Datos migrados | ❌ NO |
| Colecciones eliminadas | ❌ NO |
| Endpoints cambiados | ❌ NO |
| Frontend modificado | ❌ NO |
| Jobs alterados | ❌ NO |
| Filtros cambiados | ❌ NO |
| Lógica de negocio modificada | ❌ NO |

### METODOLOGÍA USADA:
- `grep -rn` para búsqueda de patrones
- Análisis de archivos sin modificación
- Conteo de referencias
- Clasificación manual
- No se ejecutaron scripts de migración

---

## RESUMEN EJECUTIVO FINAL

### MongoDB aún es REQUERIDO para:
1. **RBAC** - Permisos, roles, asignaciones
2. **Fase2 Operativo** - Tareas, workflows, inventarios
3. **Comercial Cache** - Fallback de KPIs
4. **Configuración** - Algunas configuraciones operativas

### MongoDB ya NO es requerido para:
1. ✅ Auth/Login (Usuario_Catalogo SQL)
2. ✅ Contexto de usuario (EDARSAHUB SQL)
3. ✅ Servidores (Servidores_Conexiones SQL)
4. ✅ Empresas/Sucursales (EDARSAHUB SQL)
5. ✅ Ventas del Día (Comercial_Ventas_Dia_Abiertas_v2 SQL)
6. ✅ Password Reset (Usuario_TokensRecuperacion SQL)
7. ✅ Rate Limit (Usuario_RateLimitRecuperacion SQL)

### Para eliminar MongoDB completamente se requiere:
1. Migrar RBAC a SQL (P0)
2. Migrar Fase2 Operativo a SQL (P1)
3. Decidir destino de Cache Comercial (P2)
4. Consolidar KPIs históricos (P2)
5. Limpiar scripts y tests (P3)

---

**Reporte generado:** 2026-05-14  
**Sin modificaciones de código**  
**Pendiente autorización para FASE 4B**
