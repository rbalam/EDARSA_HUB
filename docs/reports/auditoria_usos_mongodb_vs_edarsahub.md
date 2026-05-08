# AUDITORÍA: USOS DE MONGODB VS EDARSAHUB

**Fecha**: 01-Mayo-2026  
**Estado**: AUDITORÍA COMPLETADA — NO SE MODIFICÓ CÓDIGO  
**Autor**: E1 Agent

---

## 1. RESUMEN EJECUTIVO

El sistema EDARSA HUB utiliza **dos bases de datos** con propósitos distintos:

| Base de datos | Propósito principal | Estado |
|---------------|---------------------|--------|
| **EDARSAHUB** (SQL Server) | Fuente de verdad para datos de negocio | ✅ Cerebro del sistema |
| **MongoDB** | Infraestructura técnica + cache + legacy | ⚠️ Mixto (técnico + legacy) |

**Hallazgo crítico:** La autenticación de usuarios actualmente usa **MongoDB** como fuente, NO EDARSAHUB. Esto es un **uso legacy** que debería migrarse eventualmente.

---

## 2. COLECCIONES MONGODB ENCONTRADAS

**Total colecciones:** 66  
**Base de datos:** `edarsa_hub`

| Colección | Documentos | Clasificación |
|-----------|------------|---------------|
| alert_recipients | 2 | Técnico |
| alertas_sistema | 4 | Técnico |
| almacenes_catalogo | 11 | Cache/Config |
| api_connections | 0 | Legacy vacío |
| api_connections_cache | 2 | Cache |
| auditoria_compras_bitacora | 1,316 | Técnico/Auditoría |
| auditoria_financiera | 73 | ⚠️ Legacy (migrar a EDARSAHUB) |
| automatizaciones_bitacora | 25 | Técnico |
| automatizaciones_operativas_compras | 8 | Config/Operativo |
| bitacora_tecnica | 1 | Técnico |
| catalogos_sql | 1 | Config |
| **comercial_cache** | 60 | ⚠️ Cache V1 (deprecar con V2) |
| compras_historical_load_checkpoints | 209 | Técnico |
| config_asignaciones | 2 | Config |
| configuracion_operativo | 1 | Config |
| **dashboard_cache** | 48 | ⚠️ Cache V1 (deprecar con V2) |
| detalle_diferencias | 1,960 | Auditoría inventarios |
| empresas | 5 | Config |
| finanzas_historical_load_checkpoints | 48 | Técnico |
| historical_load_checkpoints | 33 | Técnico |
| inventario_diferencias_detalle | 22 | Operativo |
| inventarios_fisicos_procesados | 1 | Operativo |
| inventarios_procesados_auto | 158 | Operativo |
| inventarios_sin_asignar | 4 | Operativo |
| **kpis_cache** | 32 | ⚠️ Cache V1 (deprecar con V2) |
| **kpis_comercial** | 95 | ⚠️ Legacy (V2 usa EDARSAHUB) |
| manuales_operativos | 1 | Docs |
| notificaciones_log | 12 | Técnico |
| notification_config | 6 | Config |
| pedidos_procesados_automatizacion | 2 | Operativo |
| permisos_catalogos | 8 | Config |
| portal_suppliers | 3 | Operativo |
| propinas_cache_listado | 9 | Cache |
| propinas_cache_resumen | 6 | Cache |
| propinas_config | 1 | Config |
| propinas_control | 0 | Vacío |
| **rbac_audit_log** | 527 | Técnico (auditoría) |
| **rbac_permisos** | 43 | ⚠️ LEGACY RBAC |
| **rbac_roles** | 6 | ⚠️ LEGACY RBAC |
| **rbac_usuarios_roles** | 72 | ⚠️ LEGACY RBAC |
| responsabilidad_historial | 0 | Vacío |
| **roles** | 4 | ⚠️ LEGACY |
| **scheduler_job_log** | 7,805 | ✅ Técnico aceptable |
| **scheduler_locks** | 3 | ✅ Técnico aceptable |
| sec_bitacora_acceso | 25 | Técnico |
| sec_bitacora_admin | 61 | Técnico |
| sec_empresas | 1 | Config |
| sec_mapeo_servidor_sucursal | 7 | Config |
| sec_metadata | 1 | Config |
| sec_modulos_sistema | 10 | Config |
| sec_perfiles | 5 | Config |
| sec_permisos_catalogo | 90 | Config |
| sec_roles | 5 | Config |
| sec_sucursales | 7 | Config |
| sec_unidades_negocio | 7 | Config |
| server_connection_status | 1 | Técnico |
| server_status | 10 | Técnico |
| server_sucursales_config | 7 | Config |
| **servers** | 13 | ⚠️ Legacy (EDARSAHUB tiene Servidores_Conexiones) |
| sql_servers | 1 | Config |
| sucursal_servidor_map | 5 | Config |
| sucursales_catalogo | 5 | Config |
| sync_agent_registry | 1 | Técnico |
| tareas_inventario | 18 | Operativo |
| **users** | 15 | ⚠️ LEGACY (Auth usa esto) |
| workflow_inventarios | 18 | Operativo |

---

## 3. CLASIFICACIÓN DE COLECCIONES

### A. USO ACEPTABLE / TÉCNICO (Mantener en MongoDB)

| Colección | Propósito | Justificación |
|-----------|-----------|---------------|
| `scheduler_locks` | Distributed locks | Requerido para coordinación de jobs |
| `scheduler_job_log` | Logs de ejecución | Datos técnicos, no de negocio |
| `auditoria_compras_bitacora` | Bitácora operativa | Auditoría técnica |
| `automatizaciones_bitacora` | Logs de automatizaciones | Técnico |
| `bitacora_tecnica` | Logs técnicos | Técnico |
| `notificaciones_log` | Logs de notificaciones | Técnico |
| `rbac_audit_log` | Auditoría RBAC | Técnico |
| `server_status` | Estado de servidores | Cache técnico |
| `server_connection_status` | Estado conexiones | Cache técnico |
| `historical_load_checkpoints` | Checkpoints de carga | Técnico |
| `sync_agent_registry` | Registro de agentes | Técnico |

### B. USO LEGACY A MIGRAR (Eventualmente a EDARSAHUB)

| Colección | Documentos | Módulo que la usa | Prioridad migración |
|-----------|------------|-------------------|---------------------|
| **users** | 15 | `modules/auth/repository.py` | 🔴 ALTA |
| **rbac_roles** | 6 | `modules/auth/context_service.py` | 🔴 ALTA |
| **rbac_permisos** | 43 | `modules/auth/context_service.py` | 🔴 ALTA |
| **rbac_usuarios_roles** | 72 | `modules/auth/context_service.py` | 🔴 ALTA |
| **servers** | 13 | `modules/comercial/repository.py` | 🟡 MEDIA |
| **kpis_comercial** | 95 | `modules/comercial/kpis_repository.py` | 🟢 BAJA (V2 ya migrado) |
| **comercial_cache** | 60 | `modules/comercial/cache_service.py` | 🟢 BAJA (deprecar con V2) |
| **dashboard_cache** | 48 | `modules/comercial/repository.py` | 🟢 BAJA (deprecar con V2) |
| **kpis_cache** | 32 | `modules/comercial/repository.py` | 🟢 BAJA (deprecar con V2) |
| **auditoria_financiera** | 73 | Finanzas | 🟡 MEDIA |

### C. USO NO ACEPTABLE (Debe prohibirse)

| Tipo de dato | Estado actual | Fuente correcta |
|--------------|---------------|-----------------|
| Ventas oficiales | ✅ EDARSAHUB | EDARSAHUB |
| Cortes Z | ✅ EDARSAHUB | EDARSAHUB |
| Propinas oficiales | ✅ EDARSAHUB | EDARSAHUB |
| KPIs Comercial V2 | ✅ EDARSAHUB | EDARSAHUB |
| Datos de tesorería | ✅ EDARSAHUB | EDARSAHUB |
| Credenciales de servidores | ✅ EDARSAHUB | EDARSAHUB (encriptadas) |

---

## 4. MÓDULOS QUE USAN CADA COLECCIÓN

### 4.1 Colección `users` (15 documentos)

| Módulo | Archivo | Operación |
|--------|---------|-----------|
| **auth** | `modules/auth/repository.py` | CRUD usuarios |
| **auth** | `modules/auth/service.py` | Login, registro |
| fase2_operativo | `services/cargos_service.py` | Lectura |
| fase2_operativo | `services/orquestador_service.py` | Lectura |
| fase2_operativo | `services/automatizacion_compras_service.py` | Lectura |
| configuracion | `repositories/config_asignaciones_repository.py` | Lectura |
| init_queries.py | Inicialización | Creación admin |

### 4.2 Colección `rbac_*` (RBAC Legacy)

| Módulo | Archivo | Operación |
|--------|---------|-----------|
| **auth** | `modules/auth/context_service.py` | Lectura permisos/roles |
| configuracion | `routes/config_asignaciones_routes.py` | Lectura roles |

### 4.3 Colección `servers` (13 documentos)

| Módulo | Archivo | Operación |
|--------|---------|-----------|
| comercial | `repository.py` | Lectura config servidores |
| comercial | `historical_kpis_repository.py` | Lectura |
| rh/importador | `repository.py` | Lectura |
| catalogos | `repository.py` | Lectura |
| configuracion | `services/almacenes_sync_service.py` | Lectura |

### 4.4 Colección `comercial_cache` (60 documentos)

| Módulo | Archivo | Operación |
|--------|---------|-----------|
| comercial | `cache_service.py` | CRUD cache |

### 4.5 Colección `scheduler_*` (Técnico)

| Módulo | Archivo | Operación |
|--------|---------|-----------|
| scheduler | `locks/distributed_lock.py` | Locks |
| scheduler | `job_logger.py` | Logs de jobs |
| scheduler_manager | Todos los jobs | Locks + logs |

---

## 5. RESPUESTAS A PREGUNTAS OBLIGATORIAS

### 5.1 - 5.5 Colecciones y clasificación

- **Total colecciones:** 66
- **Con documentos:** 62
- **Solo técnicas:** ~15 (scheduler, bitácoras, logs)
- **Cache:** ~8 (comercial_cache, dashboard_cache, kpis_cache, propinas_cache_*)
- **Legacy:** ~10 (users, rbac_*, servers, kpis_comercial)

### 5.6 - 5.8 Usuarios y RBAC

| Pregunta | Respuesta |
|----------|-----------|
| ¿Dónde viven usuarios reales? | **MongoDB** (`users` collection) |
| ¿Dónde vive RBAC real? | **MongoDB** (`rbac_roles`, `rbac_permisos`, `rbac_usuarios_roles`) |
| Fuente actual de auth | **MongoDB** (100%) |
| EDARSAHUB tiene usuarios? | Sí, tablas `Usuario_*` pero NO se usan para auth |

### 5.9 La autenticación actual usa EDARSAHUB o MongoDB?

**RESPUESTA: MongoDB**

```python
# /app/backend/modules/auth/repository.py línea 50
return await get_db().users.find_one({"email": email}, projection)
```

El login busca usuarios en `MongoDB.users`, NO en EDARSAHUB.

### 5.10 ¿Qué parte del código todavía busca usuarios en MongoDB?

| Archivo | Línea | Operación |
|---------|-------|-----------|
| `modules/auth/repository.py` | 50 | `find_user_by_email` |
| `modules/auth/repository.py` | 58 | `find_user_by_id` |
| `modules/auth/repository.py` | 63 | `get_all_users` |
| `modules/auth/repository.py` | 88 | `create_user` |
| `modules/fase2_operativo/*` | Varios | Lectura de usuarios |
| `init_queries.py` | 291, 306 | Crear admin inicial |

### 5.11 - 5.15 Endpoints y módulos

| Tipo | Usa MongoDB | Usa EDARSAHUB |
|------|-------------|---------------|
| Auth/Login | ✅ Sí | ❌ No |
| RBAC | ✅ Sí | ❌ No |
| Comercial V1 | ✅ Cache | ✅ Datos |
| Comercial V2 | ❌ No | ✅ 100% |
| Finanzas | ✅ Parcial | ✅ Datos |
| Propinas | ✅ Cache | ✅ Datos |
| Scheduler | ✅ Locks/Logs | ✅ SyncLog negocio |

### 5.16 - 5.18 Migración y prohibiciones

**Debe migrarse a EDARSAHUB:**
1. `users` → Tabla de usuarios en EDARSAHUB
2. `rbac_*` → Tablas RBAC en EDARSAHUB
3. `servers` → `Servidores_Conexiones` (ya existe)
4. `auditoria_financiera` → Tabla auditoría EDARSAHUB

**Puede quedarse en MongoDB (técnico):**
- `scheduler_locks`
- `scheduler_job_log`
- Bitácoras técnicas
- Logs de notificaciones

**Debe prohibirse:**
- Guardar ventas, KPIs, cortes, propinas oficiales en MongoDB
- Usar MongoDB como fuente de verdad financiera/comercial

### 5.19 - 5.20 Riesgos y plan gradual

**Riesgo de quitar MongoDB de golpe:** 🔴 CRÍTICO
- Sistema de autenticación fallaría
- RBAC fallaría
- Scheduler perdería locks
- Jobs fallarían

**Plan gradual seguro:**
1. Documentar estado actual (✅ Este documento)
2. Migrar `servers` a usar `Servidores_Conexiones` de EDARSAHUB
3. Migrar RBAC a EDARSAHUB (crear tablas si no existen)
4. Migrar `users` a EDARSAHUB
5. Deprecar cache comercial V1 cuando V2 esté activo
6. Mantener MongoDB solo para infraestructura técnica

---

## 6. USUARIOS Y RBAC — ANÁLISIS DETALLADO

### 6.1 ¿Dónde viven usuarios reales?

| Ubicación | Tabla/Colección | Documentos | Usado por auth? |
|-----------|-----------------|------------|-----------------|
| **MongoDB** | `users` | 15 | ✅ SÍ (actual) |
| EDARSAHUB | `Usuario_Catalogo` | ? | ❌ NO |
| EDARSAHUB | `Usuario_Roles` | ? | ❌ NO |

**Conclusión:** Los usuarios reales viven en **MongoDB**. EDARSAHUB tiene tablas de usuarios pero NO se usan para autenticación.

### 6.2 ¿Dónde vive RBAC real?

| Ubicación | Tablas/Colecciones | Usado? |
|-----------|-------------------|--------|
| **MongoDB** | `rbac_roles`, `rbac_permisos`, `rbac_usuarios_roles` | ✅ SÍ |
| EDARSAHUB | `Usuario_Roles`, `Usuario_PermisosRolModulo` | ❌ NO |

**Conclusión:** RBAC vive en **MongoDB**.

### 6.3 ¿Por qué un script buscó usuarios en MongoDB?

El script de diagnóstico ejecutado buscó en MongoDB porque:
1. El sistema de auth usa MongoDB para usuarios
2. El repositorio `modules/auth/repository.py` está configurado para MongoDB
3. NO hay fallback a EDARSAHUB para auth

### 6.4 ¿Ese script está obsoleto?

No, el script refleja la realidad del sistema. El auth **actualmente** usa MongoDB.

### 6.5 ¿Hay endpoints de auth que todavía consultan MongoDB?

**SÍ, TODOS:**

| Endpoint | Consulta MongoDB |
|----------|------------------|
| `POST /api/auth/login` | ✅ `users.find_one` |
| `POST /api/auth/register` | ✅ `users.insert_one` |
| `GET /api/auth/users` | ✅ `users.find` |
| `GET /api/auth/me` | ✅ `users.find_one` |

### 6.6 ¿Hay fallback de auth a MongoDB?

No hay fallback porque MongoDB **ES** la fuente primaria de auth. No hay fuente secundaria.

### 6.7 ¿Hay riesgo de crear usuarios temporales en MongoDB otra vez?

**SÍ.** Cualquier llamada a `create_user()` en `modules/auth/repository.py` crea usuarios en MongoDB.

### 6.8 ¿Cómo se debe bloquear esa práctica?

1. NO crear usuarios manualmente en scripts de diagnóstico
2. Migrar auth a EDARSAHUB eventualmente
3. Documentar que MongoDB es temporal para auth

---

## 7. COMERCIAL V2 — CONFIRMACIÓN

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| Endpoints v2 leen solo EDARSAHUB | ✅ CONFIRMADO | `repository_readonly.py` usa `execute_sql_query` hacia EDARSAHUB |
| Scheduler Comercial v2 escribe solo EDARSAHUB | ✅ CONFIRMADO | `sync_comercial_edarsahub.py` escribe en tablas `_v2` |
| Comercial v2 no usa MongoDB cache | ✅ CONFIRMADO | No hay imports de `get_db()` en módulo v2 |
| Comercial v2 solo usa MongoDB para lock técnico | ✅ CONFIRMADO | Scheduler usa `DistributedLock` de MongoDB |
| Frontend v2 no depende de MongoDB | ✅ CONFIRMADO | Frontend llama a `/api/v2/comercial/*` que lee EDARSAHUB |
| Feature flag no depende de MongoDB | ✅ CONFIRMADO | Flag es variable de entorno |

**Grep de verificación:**
```bash
grep -rn "get_db()" /app/backend/modules/comercial_v2 --include="*.py"
# Resultado: 0 líneas (no usa MongoDB)
```

---

## 8. FINANZAS — ESTADO

| Módulo | Fuente principal | MongoDB usado para |
|--------|------------------|-------------------|
| Cuadres Z | EDARSAHUB | N/A |
| Control Ingresos | EDARSAHUB | N/A |
| Propinas | EDARSAHUB | Cache listado/resumen |
| Tesorería | EDARSAHUB | N/A |

**Nota:** `auditoria_financiera` (73 docs) en MongoDB es legacy y debería evaluarse para migración.

---

## 9. SCHEDULER — CONFIRMACIÓN

| Aspecto | MongoDB | EDARSAHUB |
|---------|---------|-----------|
| DistributedLock | ✅ `scheduler_locks` | ❌ |
| Job execution log técnico | ✅ `scheduler_job_log` | ❌ |
| SyncLog de negocio | ❌ | ✅ `Comercial_SyncLog_v2` |
| Configuración de jobs | ✅ (variables env) | ❌ |

**Esta separación está correcta:**
- MongoDB: Infraestructura técnica de coordinación
- EDARSAHUB: Datos de negocio (qué se sincronizó)

---

## 10. RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Quitar MongoDB sin migrar auth | Alta | 🔴 Crítico | NO quitar MongoDB |
| Inconsistencia usuarios MongoDB vs EDARSAHUB | Media | 🟡 Alto | Migrar auth a EDARSAHUB |
| Cache V1 obsoleto con datos viejos | Baja | 🟢 Bajo | V2 no usa cache |
| Crear usuarios en MongoDB accidentalmente | Media | 🟡 Alto | Documentar, no crear en scripts |

---

## 11. PLAN GRADUAL DE MIGRACIÓN

### Fase 1: Documentación (✅ COMPLETADA)
- Auditoría de colecciones
- Clasificación de usos
- Este documento

### Fase 2: Migrar `servers` (PENDIENTE AUTORIZACIÓN)
- Usar `Servidores_Conexiones` de EDARSAHUB
- Mantener `servers` de MongoDB como fallback temporal
- Verificar que todos los módulos usen EDARSAHUB

### Fase 3: Migrar RBAC (BACKLOG P0 FUTURO)
- **NO INICIAR** hasta cerrar Comercial V2 en producción
- Requiere fase específica con plan detallado
- Crear/verificar tablas RBAC en EDARSAHUB
- Migrar datos de `rbac_*`
- Actualizar `context_service.py`
- Fase espejo antes de corte

### Fase 4: Migrar Auth/Users (BACKLOG P0 FUTURO)
- **NO INICIAR** hasta cerrar Comercial V2 en producción
- Requiere fase específica con plan detallado
- Crear tabla usuarios en EDARSAHUB (si no existe)
- Migrar datos de `users`
- Actualizar `modules/auth/repository.py`
- Rollback inmediato garantizado

### Fase 5: Deprecar Cache V1 (CUANDO V2 ESTÉ ACTIVO)
- Desactivar escritura en `comercial_cache`
- Desactivar escritura en `kpis_cache`
- Desactivar escritura en `dashboard_cache`

### Fase 6: Limpieza (FUTURO)
- Eliminar colecciones vacías
- Eliminar colecciones legacy no usadas
- Documentar estado final

---

## 12. QUÉ NO DEBE TOCARSE

| Elemento | Razón |
|----------|-------|
| `scheduler_locks` | Infraestructura crítica |
| `scheduler_job_log` | Logs técnicos en uso |
| Auth actual | Sistema en producción |
| Comercial V1 | Activo hasta migración completa a V2 |
| Módulos blindados | Prohibido por máximas |

---

## 13. CONFIRMACIÓN

**NO SE MODIFICÓ CÓDIGO EN ESTA AUDITORÍA.**

| Archivo | Estado |
|---------|--------|
| `/app/backend/modules/auth/*` | ✅ INTACTO |
| `/app/backend/modules/comercial/*` | ✅ INTACTO |
| `/app/backend/modules/comercial_v2/*` | ✅ INTACTO |
| `/app/backend/core/scheduler/*` | ✅ INTACTO |
| `/app/backend/core/db.py` | ✅ INTACTO |
| Colecciones MongoDB | ✅ SIN CAMBIOS |
| EDARSAHUB | ✅ SIN CAMBIOS |

---

*Auditoría completada - 01-Mayo-2026*
*Pendiente autorización para migración gradual*

---

## 14. DECISIÓN DE CIERRE — AUTH/RBAC QUEDA EN MONGODB TEMPORALMENTE

**Fecha de decisión**: 01-Mayo-2026  
**Autorizado por**: Usuario  
**Estado**: ✅ ACEPTADO — NO MIGRAR AUTH/RBAC AHORA

---

### 14.1 RIESGO DE MIGRAR AUTH/RBAC AHORA

| Riesgo | Probabilidad | Impacto | Justificación |
|--------|--------------|---------|---------------|
| Romper acceso a todo el sistema | Alta | 🔴 CRÍTICO | Auth es transversal |
| Usuarios no pueden ingresar | Alta | 🔴 CRÍTICO | Login depende de MongoDB |
| Permisos incorrectos | Media | 🔴 CRÍTICO | RBAC controla acceso a módulos |
| Rollback complejo | Alta | 🟡 Alto | Requiere sincronizar datos |
| Afectar módulos blindados | Media | 🔴 CRÍTICO | Todo depende de auth |

**Conclusión:** Migrar Auth/RBAC requiere una fase específica con plan detallado, pruebas exhaustivas y rollback inmediato garantizado.

---

### 14.2 DECISIÓN DE NO TOCAR

**NO AUTORIZADO modificar:**

| Componente | Estado |
|------------|--------|
| `modules/auth/*` | ❌ NO TOCAR |
| `users` collection | ❌ NO TOCAR |
| `rbac_*` collections | ❌ NO TOCAR |
| Login/Logout | ❌ NO TOCAR |
| Tokens/Sesiones | ❌ NO TOCAR |
| Middleware de seguridad | ❌ NO TOCAR |
| `servers` collection | ❌ NO TOCAR |
| Cache V1 | ❌ NO BORRAR |

**Razón:** Auth/RBAC es de alto riesgo y transversal. Primero cerrar Comercial V2 en producción.

---

### 14.3 PRIORIDAD ACTUAL: CERRAR COMERCIAL V2

| Prioridad | Tarea | Estado |
|-----------|-------|--------|
| 1 | Cerrar Comercial V2 en producción | ⏳ Pendiente validación |
| 2 | Mantener Comercial V2 usando EDARSAHUB | ✅ Implementado |
| 3 | Mantener MongoDB para Auth/RBAC | ✅ Temporal aceptado |
| 4 | Mantener MongoDB para locks/logs | ✅ Técnico aceptado |
| 5 | No tocar servidores legacy | ✅ Bloqueado |

---

### 14.4 BACKLOG: FASE AUTH/RBAC EDARSAHUB

**Agregado al backlog como P0 FUTURO:**

```
FASE: Migración Auth/RBAC a EDARSAHUB
ESTADO: BACKLOG (no iniciar hasta cerrar Comercial V2)
PRIORIDAD: P0 cuando se autorice
```

**Requisitos de la fase:**

| # | Requisito |
|---|-----------|
| 1 | Auditoría de usuarios MongoDB vs EDARSAHUB |
| 2 | Auditoría de roles |
| 3 | Auditoría de permisos |
| 4 | Mapeo `MongoDB.users` → `EDARSAHUB.Usuario_*` |
| 5 | Mapeo `MongoDB.rbac_*` → `EDARSAHUB.Usuario_Roles/Permisos` |
| 6 | Pruebas de login con usuarios existentes |
| 7 | Pruebas de permisos por módulo |
| 8 | Pruebas con usuarios administradores |
| 9 | Pruebas con usuarios restringidos |
| 10 | Rollback inmediato a MongoDB (< 1 min) |
| 11 | Fase espejo antes de corte (dual write) |
| 12 | No afectar Comercial, Finanzas, CxP, Propinas, Tesorería, Scheduler |

---

### 14.5 MONGODB PERMITIDO TEMPORALMENTE

**Uso temporal aceptado:**

| Colección | Uso | Duración |
|-----------|-----|----------|
| `users` | Auth actual | Hasta Fase Auth/RBAC |
| `rbac_roles` | Roles | Hasta Fase Auth/RBAC |
| `rbac_permisos` | Permisos | Hasta Fase Auth/RBAC |
| `rbac_usuarios_roles` | Asignaciones | Hasta Fase Auth/RBAC |
| `scheduler_locks` | Locks técnicos | Permanente |
| `scheduler_job_log` | Logs técnicos | Permanente |
| `comercial_cache` | Cache V1 | Hasta deprecar V1 |
| `kpis_cache` | Cache V1 | Hasta deprecar V1 |
| `dashboard_cache` | Cache V1 | Hasta deprecar V1 |

---

### 14.6 MONGODB PROHIBIDO PARA NUEVOS DATOS DE NEGOCIO

**PROHIBIDO usar MongoDB como fuente para:**

| Tipo de dato | Fuente correcta |
|--------------|-----------------|
| Ventas oficiales | EDARSAHUB |
| KPIs comerciales directivos | EDARSAHUB (V2) |
| Cortes Z | EDARSAHUB |
| Propinas oficiales | EDARSAHUB |
| Datos de tesorería | EDARSAHUB |
| Pagos oficiales | EDARSAHUB |
| Cualquier dato financiero nuevo | EDARSAHUB |
| Cualquier dato comercial nuevo | EDARSAHUB |
| Credenciales de servidores | EDARSAHUB (encriptadas) |

**Regla:** Todo nuevo módulo de negocio debe usar EDARSAHUB como fuente de verdad.

---

### 14.7 CONFIRMACIÓN DE QUE NO SE MODIFICÓ CÓDIGO

**Estado de archivos:**

| Archivo/Módulo | Estado |
|----------------|--------|
| `/app/backend/modules/auth/*` | ✅ INTACTO |
| `/app/backend/modules/comercial/*` | ✅ INTACTO |
| `/app/backend/modules/comercial_v2/*` | ✅ INTACTO |
| `/app/backend/core/scheduler/*` | ✅ INTACTO |
| `/app/backend/core/db.py` | ✅ INTACTO |
| `/app/backend/core/security.py` | ✅ INTACTO |
| `/app/backend/core/rbac_helper.py` | ✅ INTACTO |
| Colecciones MongoDB | ✅ SIN CAMBIOS |
| EDARSAHUB | ✅ SIN CAMBIOS |
| Frontend | ✅ INTACTO |

**NO SE MODIFICÓ ningún archivo de Auth, RBAC, seguridad ni middleware.**

---

### 14.8 RESUMEN EJECUTIVO DE LA DECISIÓN

```
┌─────────────────────────────────────────────────────────────┐
│                    DECISIÓN FINAL                           │
├─────────────────────────────────────────────────────────────┤
│  Auth/RBAC: QUEDA EN MONGODB (temporal)                    │
│  Comercial V2: USA EDARSAHUB (correcto)                    │
│  Scheduler: MONGODB para locks/logs (correcto)             │
│  Migración Auth: BACKLOG P0 FUTURO                         │
│  Código modificado: NINGUNO                                 │
└─────────────────────────────────────────────────────────────┘
```

---

*Decisión de cierre documentada - 01-Mayo-2026*
*NO migrar Auth/RBAC sin autorización explícita y plan detallado*
