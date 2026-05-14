# EDARSA HUB - Product Requirements Document

## Objetivo Principal
Eliminar progresivamente las dependencias funcionales de MongoDB y consolidar EDARSAHUB (SQL Server) como el cerebro real y única fuente de verdad del sistema.

## Régimen de Autorización Controlada
- Diagnóstico pasivo primero
- Los cambios DDL/DML/UI requieren autorización explícita del usuario
- Ningún DML/DDL sin bloque transaccional o validaciones previas

---

## Fases Completadas

### FASE P1.4 - Migración de Servidores (100% Completada)
- [x] P1.4-A: Diagnóstico de config servidores
- [x] P1.4-B: Endpoints de queries migrados a SQL
- [x] P1.4-C: Endpoints de inventario migrados a SQL
- [x] P1.4-D1: Diagnóstico de sucursales-config (no usa db.servers)
- [x] P1.4-E1: Auditoría operativa migrada a SQL
- [x] P1.4-E2: Dashboard inventory-summary migrado a SQL
- [x] P1.4-E3: Comparativo inventarios migrado a SQL
- [x] P1.4-E4: Explorador/Catálogo migrados a SQL
- [x] P1.4-F: Referencias en modules/configuracion migradas

### FASE 0 - Auditoría Global (Completada)
- [x] Documento de dependencias MongoDB generado

### FASE 2-A - Diseño DDL Auth/RBAC (Completada)
- [x] Propuesta de DDL generada: `/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md`

### FASE 2-A.1 - Validación DDL Pre-Migración (Completada - 14-Dic-2025)
- [x] Análisis de tablas SQL existentes
- [x] Mapeo de campos MongoDB vs SQL
- [x] Reporte: `/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md`

### FASE 2-A.2 - Precondiciones DDL (Completada - 14-Dic-2025)
- [x] Columnas creadas: PublicUUID, MongoLegacyID
- [x] Índices creados: IX_Usuario_PublicUUID, IX_Usuario_MongoLegacyID
- [x] Roles creados: SUPERADMIN, SUPERVISOR, USUARIO, VISOR
- [x] Script idempotente confirmado
- [x] Reporte: `/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md`

### FASE 2-B1 - Poblado Usuarios Base (Completada - 14-Dic-2025)
- [x] 9 usuarios existentes actualizados con PublicUUID y MongoLegacyID
- [x] 2 usuarios productivos insertados (carlos@, eduardo@alpuntoycoma.mx)
- [x] 6 usuarios omitidos (3 inactivos, 3 test/@test.com)
- [x] superadmin@test.com excluido (sin UUID - documentado)
- [x] Hashes bcrypt intactos
- [x] Reporte: `/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md`

### FASE 2-B2 - Poblado Roles Asignación (Completada - 14-Dic-2025)
- [x] 11 asignaciones insertadas en Usuario_RolesAsignacion
- [x] Mapeo: SuperAdministrador→SUPERADMIN, Administrador→ADMIN, Supervisor→SUPERVISOR, Usuario→USUARIO
- [x] 2 SuperAdministradores preservados (admin@inventario.com, ricardo@edarsa.com.mx)
- [x] 4 ADMIN, 2 SUPERVISOR, 3 USUARIO
- [x] Reporte: `/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md`

### FASE 2-B2.1 - Mapeo Empresas MongoDB → SQL (Completada - 14-Dic-2025)
- [x] Tabla `Sistema_EmpresasMongoMap` creada
- [x] 5 mapeos creados por código exacto (ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID)
- [x] Sin ambigüedades ni conflictos
- [x] Reporte: `/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md`

### FASE 2-B3 - Poblado Usuario_EmpresasAsignacion (Completada - 14-Dic-2025)
- [x] 27 asignaciones insertadas para 7 usuarios con empresas_permitidas
- [x] 5 usuarios con 5 empresas cada uno (acceso global)
- [x] 2 usuarios con 1 empresa (CIENFUEGOS - acceso limitado)
- [x] 7 usuarios con empresa principal correcta
- [x] 4 usuarios omitidos (sin empresas_permitidas) - pendientes de decisión
- [x] Reporte: `/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md`

### FASE 2-C - Validación Post-Migración (Completada - 14-Dic-2025)
- [x] Validación cruzada MongoDB vs SQL completada
- [x] 11/11 usuarios con integridad de datos
- [x] 11/11 hashes bcrypt válidos
- [x] 11/11 UUIDs y MongoLegacyID presentes
- [x] 5/5 empresas mapeadas correctamente
- [x] 27/27 asignaciones de empresas válidas
- [x] Sin duplicados ni inconsistencias críticas
- [x] 4 usuarios sin empresas documentados (consistente con MongoDB)
- [x] Recomendación SUPERADMIN: Opción B (acceso global implícito)
- [x] Reporte: `/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md`

### ✅ FASE 2-D - Auth Repository SQL Paralelo (Completada - 14-Dic-2025)
- [x] Archivo creado: `/app/backend/core/auth/user_repository_sql.py`
- [x] Clase `AuthRepositorySQL` con funciones equivalentes a MongoDB
- [x] Regla SUPERADMIN implementada (acceso global implícito a 5 empresas)
- [x] PublicUUID usado como `user['id']` para compatibilidad JWT
- [x] Funciones de comparación MongoDB vs SQL incluidas
- [x] Validación exitosa: 2 SUPERADMIN con acceso a 5/5 empresas
- [x] Código productivo (security.py, service.py) NO MODIFICADO
- [x] MongoDB sigue siendo la fuente productiva de Auth
- [x] Reporte: `/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md`

### ✅ FASE 2-D.1 - Preflight Auth SQL-First (Completada - 14-Dic-2025)
- [x] Feature flag agregado: `AUTH_SQL_FIRST_ENABLED=false`
- [x] Feature flag APAGADO por defecto (MongoDB productivo)
- [x] Funciones de comparación pasiva agregadas a `security.py`
- [x] 11/11 usuarios SQL validados contra MongoDB
- [x] UUIDs coinciden (normalización case-insensitive)
- [x] Regla SUPERADMIN validada (2/2 con acceso global)
- [x] 3 usuarios sin empresas documentados
- [x] Logging seguro (sin passwords/hashes/tokens)
- [x] JWT no modificado
- [x] `get_current_user()` no modificado
- [x] Endpoints críticos funcionan (/api/servers, /api/auth/me, dashboard)
- [x] Reporte: `/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md`

### ✅ FASE 2-E - Auth SQL-First con Fallback MongoDB (Completada - 14-Dic-2025)
- [x] `get_current_user()` modificado para SQL-first
- [x] `get_current_user_dual()` actualizado
- [x] Feature flag: `AUTH_SQL_FIRST_ENABLED=true`
- [x] Fallback MongoDB funcional
- [x] auth_source loggeado (EDARSAHUB_SQL, MONGODB_FALLBACK, SQL_ERROR_FALLBACK)
- [x] PublicUUID usado como user['id']
- [x] SUPERADMIN resuelve 5/5 empresas (ricardo@ ahora tiene acceso)
- [x] Usuarios no migrados (@test.com) usan fallback MongoDB
- [x] Rollback por feature flag validado
- [x] Endpoints críticos funcionan (/api/servers=8, dashboard=4 unidades)
- [x] JWT sin cambios
- [x] Reporte: `/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md`

### ✅ FASE 2-F - Observación SQL-First Auth (Completada - 14-Dic-2025)
- [x] 8 usuarios productivos resuelven desde EDARSAHUB_SQL
- [x] 1 usuario @test.com usa MongoDB fallback (esperado)
- [x] 0 SQL_ERROR_FALLBACK
- [x] SUPERADMIN (admin@inventario.com, ricardo@edarsa.com.mx) = 5 empresas ✓
- [x] Dashboard 4 unidades (LA ESTELAR sin datos KPIs - NO es regresión Auth)
- [x] /api/servers = 8 servidores ✓
- [x] Rollback por feature flag validado
- [x] Diagnóstico 4 vs 5 unidades completado: LA ESTELAR no tiene datos en Comercial_KPIs_Diarios_v2 para dic 2024
- [x] Reporte: `/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md`

### ✅ FASE 2-F.1 - Cierre Pendientes Auth/RBAC (Completada - 14-Dic-2025)
- [x] Auditados 9 usuarios pendientes (5 @test.com + 3 sin empresas + 1 especial)
- [x] 3 usuarios @test.com activos dependen de MongoDB fallback
- [x] 3 usuarios productivos sin empresas ya usan EDARSAHUB_SQL (no dependen de fallback)
- [x] Recomendaciones por usuario documentadas
- [x] Impacto de eliminar fallback: BAJO (solo afecta usuarios @test.com de prueba)
- [x] Prerrequisitos para FASE 2-G identificados
- [x] Reporte: `/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md`

### ✅ FASE 2-F.2 - Saneamiento Usuarios Pre-Fallback Off (Completada - 14-Dic-2025)
- [x] Desactivados 3 usuarios @test.com en MongoDB (superadmin@, superadmin2@, usuario_test_portal@)
- [x] david.ricardez@cienfuegos.mx: Asignada empresa CIENFUEGOS (1 empresa)
- [x] carlos@alpuntoycoma.mx: Asignadas 5 empresas (ORIGEN principal)
- [x] eduardo@alpuntoycoma.mx: Asignadas 5 empresas (ORIGEN principal)
- [x] 11/11 usuarios productivos: EDARSAHUB_SQL
- [x] MONGODB_FALLBACK productivos: 0
- [x] SQL_ERROR_FALLBACK: 0
- [x] Sistema listo para FASE 2-G
- [x] Reporte: `/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md`

### ✅ FASE 2-G - Eliminación Fallback MongoDB Auth (Completada - 14-Dic-2025)
- [x] Eliminado `_get_user_sql_first_with_fallback()` de security.py
- [x] Creado `_get_user_sql_only()` sin fallback MongoDB
- [x] `get_current_user()` y `get_current_user_dual()` usan SQL-only
- [x] 11/11 usuarios productivos: EDARSAHUB_SQL
- [x] 3/3 usuarios @test.com: RECHAZADOS (401)
- [x] MONGODB_FALLBACK: ELIMINADO
- [x] SQL_ERROR_FALLBACK: 0
- [x] SUPERADMIN: 5 empresas cada uno ✓
- [x] JWT sin cambios, PublicUUID como user['id']
- [x] Endpoints críticos funcionan (servers=8, dashboard=4)
- [x] Reporte: `/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md`

---

## ✅ FASE 2 COMPLETADA: Migración Auth/RBAC a EDARSAHUB SQL

**EDARSAHUB SQL es ahora la ÚNICA fuente de autenticación productiva.**

| Tabla SQL | Registros | Estado |
|-----------|-----------|--------|
| Usuario_Catalogo | 11 | ✓ Completo |
| Usuario_Roles | 9 | ✓ Completo |
| Usuario_RolesAsignacion | 11 | ✓ Completo |
| Usuario_EmpresasAsignacion | 38 | ✓ Completo |
| Sistema_EmpresasMongoMap | 5 | ✓ Completo |

### MongoDB en Auth:
- `db.users` ya no se usa para autenticación
- Fallback MongoDB: ELIMINADO
- Referencias residuales: `password_reset.py`, `context_service.py` (deuda técnica)

---

## ✅ FASE 2 BASE COMPLETADA: Migración Auth/RBAC a SQL

| Tabla SQL | Registros | Estado |
|-----------|-----------|--------|
| Usuario_Catalogo | 11 | ✓ Completo |
| Usuario_Roles | 9 | ✓ Completo |
| Usuario_RolesAsignacion | 11 | ✓ Completo |
| Usuario_EmpresasAsignacion | 27 | ✓ Completo |
| Sistema_EmpresasMongoMap | 5 | ✓ Completo |
| Usuario_MigracionMongoTrace | 11 | ✓ Completo |

### Repositorio SQL Paralelo:
- `AuthRepositorySQL.get_user_by_email_sql()` ✓
- `AuthRepositorySQL.get_user_by_public_uuid_sql()` ✓
- `validate_superadmin_rule()` ✓ (2 SUPERADMIN = 5/5 empresas)

---

## Fases Pendientes (P1) - Requieren Autorización

### FASE 3 - Migración Empresas/Sucursales a SQL (SIGUIENTE)
- [ ] Migrar `db.empresas` a `Sistema_Empresas`
- [ ] Migrar `db.sucursales` a `Sistema_Sucursales`
- [ ] Actualizar endpoints que leen de MongoDB
- [ ] Mantener Sistema_EmpresasMongoMap como puente
- **Prerequisito:** FASE 2 ✅ COMPLETADA

---

## Fases Futuras (P1/P2)

### P1: Migración de Entidades
- P1.4-D2: server_sucursales_config
- FASE 3: Empresas/Sucursales/Mapeos
- FASE 4: Reglas de negocio

### P2: Hardening y Limpieza
- FASE 5-6: Eliminación total de fallback MongoDB
- SECURITY-P1: Hardening Universal Query

---

## Estado Actual del Sistema

### Flujo de Autenticación (FASE 2-G COMPLETADA):
```
[PRODUCTIVO - SQL-ONLY]
POST /api/auth/login → service.py → MongoDB (login) → JWT creado
GET /api/auth/me → security.py → SQL ONLY (sin fallback)
                                 └─ auth_source: EDARSAHUB_SQL
                                                 SQL_NOT_FOUND → 401
                                                 SQL_ERROR → 401
```

### Feature Flag (Legacy):
```
AUTH_SQL_FIRST_ENABLED=true  (ya no controla fallback, SQL es único)
```

### Deuda Técnica Auth (MongoDB residual):
- `/app/backend/modules/auth/password_reset.py` - usa db.users
- `/app/backend/modules/auth/context_service.py` - usa db.users

### Usuarios @test.com:
| Email | Rol SQL | Empresas SQL |
|-------|---------|--------------|
| ricardo@edarsa.com.mx | SUPERADMIN | 5 (regla implícita) ✅ |
| david.ricardez@cienfuegos.mx | USUARIO | 0 |
| carlos@alpuntoycoma.mx | ADMIN | 0 |
| eduardo@alpuntoycoma.mx | ADMIN | 0 |

### Usuarios MongoDB vs SQL:
- MongoDB: 17 (14 activos, 3 inactivos)
- SQL: 11 migrados (9 originales + 2 nuevos)
- Pendientes: 0 productivos (solo usuarios test)

---

## Documentos de Referencia
- `/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md`
- `/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md`
- `/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md`
- `/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md`
- `/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md`
- `/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md`
- `/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md`
- `/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md`
- `/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md`
- `/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md`
- `/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md`
- `/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md`
- `/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md`
- `/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md`
- `/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md`
- `/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md`

---

## Hallazgos Documentados

### LA ESTELAR - Sin datos KPIs (Dic 2024)
- **Problema:** LA ESTELAR no aparece en Tablero Ejecutivo (4 unidades vs 5 esperadas)
- **Causa:** No hay registros en `Comercial_KPIs_Diarios_v2` para dic 2024
- **NO es regresión de Auth/RBAC**
- **Acción requerida:** Carga de datos históricos (fuera del scope de FASE 2)

### Usuarios @test.com:
| Usuario | Estado |
|---------|--------|
| superadmin@test.com | ✅ Desactivado, rechazado |
| superadmin2@test.com | ✅ Desactivado, rechazado |
| usuario_test_portal@test.com | ✅ Desactivado, rechazado |
| test_validacion@test.com | Ya inactivo |
| test_rbac_val@test.com | Ya inactivo |

### Usuarios Productivos:
| Usuario | Empresas | Status |
|---------|----------|--------|
| admin@inventario.com | 5 (SUPERADMIN) | ✅ SQL |
| ricardo@edarsa.com.mx | 5 (SUPERADMIN) | ✅ SQL |
| david.ricardez@cienfuegos.mx | 1 | ✅ SQL |
| carlos@alpuntoycoma.mx | 5 | ✅ SQL |
| eduardo@alpuntoycoma.mx | 5 | ✅ SQL |
| (otros 6) | 1-5 | ✅ SQL |

---

*Última actualización: 14-Dic-2025 - FASE RBAC-SCOPE-D Completada*

## ✅ RBAC-SCOPE-D COMPLETADA (14-Dic-2025)

**Objetivo:** Modificar `get_all_users()` para leer permisos operativos desde EDARSAHUB SQL.

**Cambio implementado:**
- `allowed_servers` → Lee de `Usuario_ServidoresAsignacion`
- `allowed_sucursales` → Lee de `Usuario_SucursalesAsignacion`
- `allowed_warehouses` → Lee de `Usuario_AlmacenesAsignacion`

**MongoDB ya NO alimenta permisos operativos productivos.**
Solo se usa para campos RBAC piloto (`sec_*`, `telefono`) como metadatos.

**Validaciones:**
- ✅ 11 usuarios visibles
- ✅ SQL y MongoDB coinciden 100%
- ✅ Usuarios sin permisos = arrays vacíos
- ✅ admin@inventario.com: 8 servidores
- ✅ carlosruz@edarsa.com.mx: 1 servidor, 2 almacenes
- ✅ Sin regresión

**Reporte:** `/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md`

---

## ✅ BUG-USERS-LIST-002 CORREGIDO (14-Dic-2025)

**Problema:** Los usuarios carlos@alpuntoycoma.mx y eduardo@alpuntoycoma.mx mostraban `empresas_permitidas: []` aunque tenían 5 empresas en SQL.

**Causa raíz:** El modelo Pydantic `User` no incluía los campos `empresas_permitidas` ni `empresa_default_id`. Con `extra="ignore"`, estos campos se eliminaban de la respuesta JSON.

**Solución:** Agregados campos al modelo `User` en `/app/backend/modules/auth/schemas.py`:
- `empresas_permitidas: List[str] = []`
- `empresa_default_id: Optional[str] = None`

**Resultado:** Los 11 usuarios ahora muestran correctamente sus empresas asignadas desde EDARSAHUB SQL.

**Reporte:** `/app/docs/reports/BUG_USERS_LIST_002_USUARIOS_SQL_NO_VISIBLES.md`

---

## ✅ RBAC-SCOPE-C COMPLETADA (14-Dic-2025)

**Objetivo:** Migrar permisos legacy de MongoDB a tablas SQL creadas en RBAC-SCOPE-B.

**Datos migrados:**
- `allowed_servers` → `Usuario_ServidoresAsignacion`: **19 registros**
- `allowed_sucursales` → `Usuario_SucursalesAsignacion`: **5 registros**
- `allowed_warehouses` → `Usuario_AlmacenesAsignacion`: **52 registros**

**Usuarios migrados:** 7 (con permisos configurados)

**Validaciones:**
- ✅ admin@inventario.com: 8 servidores
- ✅ carlosruz@edarsa.com.mx: 1 servidor, 2 almacenes
- ✅ noxte@alpyc.com: 1 servidor, 2 sucursales, 5 almacenes
- ✅ auditoria@edarsa.com.mx: 3 servidores, 2 sucursales, 20 almacenes
- ✅ almacen@cienfuegos.mx: 1 servidor, 10 almacenes

**Comportamiento productivo:** Sin cambios. Hotfix MongoDB sigue activo.

**Reporte:** `/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md`

---

## ✅ RBAC-SCOPE-B COMPLETADA (14-Dic-2025)

**Objetivo:** Crear tablas SQL para migrar permisos operativos legacy de MongoDB.

**Tablas creadas en EDARSAHUB:**
1. `Usuario_ServidoresAsignacion` — Reemplazará `allowed_servers`
2. `Usuario_SucursalesAsignacion` — Reemplazará `allowed_sucursales`
3. `Usuario_AlmacenesAsignacion` — Reemplazará `allowed_warehouses`

**Características:**
- DDL idempotente (IF NOT EXISTS)
- FK hacia Usuario_Catalogo y Servidores_Conexiones
- Índices para rendimiento
- Constraints únicos para evitar duplicados activos
- Campo `LegacyMongoValue` para trazabilidad
- Campos de auditoría completos

**Estado:** Tablas vacías. Datos se migrarán en RBAC-SCOPE-C.

**Reporte:** `/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md`

---

## 🎉 HITO: FASE 2 COMPLETADA
**EDARSAHUB SQL es ahora la ÚNICA fuente de autenticación productiva.**

---

## ✅ BUG-RBAC-PERM-001 RESUELTO (14-Dic-2025)

**Problema:** Modal de permisos en Usuarios y Roles:
1. Departamentos sin labels visibles (checkboxes vacíos)
2. Error al guardar permisos (404 "Usuario no encontrado")

**Causas raíz:**
1. Endpoint `/api/servers/{id}/departamentos` devolvía strings (`["002"]`) en lugar de objetos (`[{codigo, descripcion}]`)
2. `find_user_by_id()` y `update_user()` hacían búsqueda case-sensitive, fallando porque SQL devuelve UUIDs en mayúsculas y MongoDB los tiene en minúsculas

**Solución:**
- Normalización de respuesta de departamentos a objetos `{codigo, descripcion}`
- Búsqueda case-insensitive en `find_user_by_id()` y `update_user()`
- Enriquecimiento de `get_all_users()` con permisos legacy de MongoDB

**Resultado:** Modal de permisos funciona correctamente, permisos persisten.

**Reporte:** `/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md`

---

## ✅ BUG-AUTH-USERS-001 RESUELTO (14-Dic-2025)

**Problema:** La pantalla Usuarios y Roles → pestaña Usuarios mostraba "Error al cargar usuarios".

**Causa raíz:** La función `get_all_users()` en `repository.py` consultaba MongoDB mientras que `get_current_user()` ya usaba SQL-only (FASE 2-G). MongoDB retornaba datos con `None` en campos que Pydantic esperaba como `List[str]`.

**Solución:**
- `get_all_users()` migrado a EDARSAHUB SQL via `AuthRepositorySQL.list_all_users_sql()`
- `get_users_by_empresas()` migrado a filtrar sobre datos SQL
- NO se reactivó MongoDB como fuente primaria
- NO se exponen hashes, passwords ni tokens

**Resultado:** 11 usuarios productivos cargan correctamente desde EDARSAHUB SQL.

**Reporte:** `/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md`

### Deuda Técnica Post-Fix (repository.py):
Las siguientes funciones SIGUEN usando MongoDB y deben migrarse en fases futuras:
- `create_user()` - Escribe en db.users
- `update_user()` - Actualiza db.users (case-insensitive fix aplicado)
- `deactivate_user()` - Actualiza db.users
- `find_user_by_email()` - Lee de db.users (usado por login)
- `find_user_by_id()` - Lee de db.users (case-insensitive fix aplicado)
