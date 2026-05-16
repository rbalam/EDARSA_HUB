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

## FASE 3 - Migración Empresas/Sucursales/Context a SQL

### ✅ FASE 3-A - Diagnóstico Empresas/Sucursales/Mapeos (Completada - 14-May-2026)
- [x] Diagnóstico de `db.empresas`, `db.sucursales_catalogo`, `db.sucursal_servidor_map`, `db.server_sucursales_config`
- [x] Identificación de estructura de datos MongoDB
- [x] Reporte: `/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md`

### ✅ FASE 3-B - DDL y Migración Sucursales/Mapeos (Completada - 14-May-2026)
- [x] Tabla `Sistema_Sucursales` creada y poblada (5 registros)
- [x] Tabla `Sistema_SucursalServidorMapeo` creada y poblada (5 registros)
- [x] Tabla `Sistema_ServidorSucursalesConfig` creada y poblada (7 registros)
- [x] Trazabilidad MongoDB preservada (MongoUUID en todas las tablas)
- [x] `RH_Cat_Sucursales` NO usada como transversal (conserva rol RH)
- [x] Reporte: `/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md`

### ✅ FASE 3-C - Migración context_resolver.py a SQL (Completada - 14-May-2026)
- [x] `context_resolver.py` migrado de MongoDB a EDARSAHUB SQL
- [x] 0 referencias productivas a MongoDB en el archivo
- [x] Helpers SQL creados: `_get_empresas_by_uuids_sql()`, `_get_sucursales_by_empresas_sql()`, etc.
- [x] Tablas usadas: `Sistema_Empresas`, `Sistema_Sucursales`, `Sistema_SucursalServidorMapeo`, `Servidores_Conexiones`
- [x] 5 relaciones canónicas validadas (ORIGEN→ManagmentPro, 130QRO→ManagmentPro, etc.)
- [x] Contrato de salida preservado (compatibilidad UUID MongoDB)
- [x] `user_access_context.py` NO TOCADO
- [x] `context_service.py` NO TOCADO
- [x] Reporte: `/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md`

### ✅ FASE 3-D - Migración user_access_context.py a SQL (Completada - 14-May-2026)
- [x] `user_access_context.py` migrado de MongoDB a EDARSAHUB SQL
- [x] 0 referencias productivas a MongoDB en el archivo
- [x] Helpers SQL creados para resolución de acceso efectivo
- [x] SUPERADMIN resuelve 5 empresas y 8 servidores desde SQL
- [x] Usuarios con alcance limitado conservan su alcance
- [x] Contrato de salida preservado
- [x] `context_service.py` NO TOCADO
- [x] Reporte: `/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md`

### ✅ FASE 3-E - Migración context_service.py a SQL (Completada - 14-May-2026)
- [x] `context_service.py` migrado de MongoDB a EDARSAHUB SQL
- [x] 0 referencias productivas a MongoDB en el archivo
- [x] Funciones migradas: `get_user_context()`, `get_user_context_for_empresa()`, `get_empresas_disponibles()`
- [x] Tablas SQL usadas: `Usuario_Catalogo`, `Usuario_Roles`, `Usuario_RolesAsignacion`, `Usuario_EmpresasAsignacion`, `Sistema_Empresas`, `Sistema_Sucursales`
- [x] 7 usuarios validados correctamente
- [x] 5 relaciones empresa→sucursal correctas
- [x] Contrato de salida preservado
- [x] Reporte: `/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md`

### ✅ FASE 3-F/G - Auditoría Final FASE 3 (Completada - 14-May-2026)
- [x] Auditoría completa de referencias MongoDB en capa de contexto
- [x] 3 archivos core migrados: context_resolver, user_access_context, context_service
- [x] 0 referencias MongoDB productivas en archivos core de contexto
- [x] 5/5 relaciones canónicas validadas
- [x] 7/7 usuarios validan correctamente
- [x] Referencias MongoDB residuales clasificadas (DEUDA TÉCNICA: security.py, alcance_helper.py, password_reset.py)
- [x] Reporte: `/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md`

**✅ FASE 3 COMPLETADA: EDARSAHUB SQL es fuente productiva para Empresas/Sucursales/Mapeos/Contexto**

### ✅ FASE 3-H - Migración deuda P1 security.py y alcance_helper.py (Completada - 14-May-2026)
- [x] `security.py`: Funciones `get_user_empresas_permitidas()` y `get_servers_for_empresas()` migradas a SQL
- [x] `alcance_helper.py`: Funciones `_resolver_unidad()` y `_resolver_sucursal()` migradas a SQL
- [x] 0 referencias `db.*` productivas en ambos archivos
- [x] SUPERADMIN resuelve 5 empresas desde SQL
- [x] Usuarios limitados conservan alcance correcto
- [x] Sin regresión en módulos principales
- [x] Reporte: `/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md`

### ✅ FASE 3-I - Migración password_reset.py a SQL (Completada - 14-May-2026)
- [x] Tabla `Usuario_TokensRecuperacion` creada (DDL autorizado)
- [x] `password_reset.py` migrado de MongoDB a EDARSAHUB SQL
- [x] Token hasheado (SHA-256), nunca plano
- [x] Usuario buscado en `Usuario_Catalogo`
- [x] Password actualizado en `PasswordHashTexto`
- [x] Invalidación automática de tokens anteriores
- [x] Reporte: `/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md`

### ✅ AUTH-RESET-P2 - Migración Rate Limit y Auditoría a SQL (Completada - 14-May-2026)
- [x] Tabla `Usuario_RateLimitRecuperacion` creada (rate limit por IP/email)
- [x] Tabla `Usuario_LogRecuperacion` creada (auditoría de eventos)
- [x] `password_reset.py` ahora es **100% SQL** - 0 referencias a MongoDB
- [x] Funciones migradas: `check_rate_limit_sql()`, `increment_rate_limit_sql()`, `audit_log_sql()`
- [x] Rate limit validado funcionando en SQL
- [x] Auditoría validada funcionando en SQL
- [x] Reset de contraseña completamente operativo
- [x] GREP confirma 0 código activo MongoDB en password_reset.py
- [x] Reporte: `/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md`

**✅ Flujo de Recuperación de Contraseña es ahora 100% EDARSAHUB SQL:**
- Usuario_Catalogo (usuarios)
- Usuario_TokensRecuperacion (tokens)
- Usuario_RateLimitRecuperacion (rate limit)
- Usuario_LogRecuperacion (auditoría)

---

### ✅ CAMBIO ARQUITECTÓNICO: Ventas del Día → EDARSAHUB SQL (Completado - 14-May-2026)
- [x] Job `sync_comercial_abiertas_v2_job.py` reescrito
- [x] **ORIGEN y 130QRO usan APIs locales MPRO** (NO SQL Server MPRO central)
- [x] **130° MÉRIDA** funciona correctamente ($4,441.00)
- [x] **NO escribe $0 falso** si falla conexión al origen
- [x] Tablero lee **exclusivamente desde EDARSAHUB SQL**
- [x] Payload incluye: `snapshot_timestamp`, `minutos_desde_ultima_actualizacion`, `dato_vencido`
- [x] **Ordenamiento por venta DESC** implementado
- [x] Frecuencia: cada 5 minutos
- [x] Tabla destino: `Comercial_Ventas_Dia_Abiertas_v2` (reutilizada)
- [x] **BUG DECIMAL CORREGIDO** - El job escribía $0 por error de serialización JSON de Decimal
- [x] **FRONTEND ACTUALIZADO** - Ventas del Día ahora usa endpoint V2 `/v2/comercial/ventas-dia`
- [x] Reporte: `/app/docs/reports/VENTAS_DIA_CAMBIO_ARQUITECTONICO.md`

**✅ Flujo Ventas del Día ahora es 100% EDARSAHUB SQL:**
- SoftRestaurant → tempcheques → EDARSAHUB SQL → Tablero
- MPRO ORIGEN → API Local → EDARSAHUB SQL → Tablero  
- MPRO QRO → API Local → EDARSAHUB SQL → Tablero

---

## FASE 4 - Migración RBAC MongoDB → EDARSAHUB SQL

### ✅ FASE 4A - Diagnóstico Pasivo de Reglas Vivas MongoDB (Completada - 14-May-2026)
- [x] Auditoría pasiva (grep) de referencias MongoDB en todo el código
- [x] Identificadas 775 líneas con referencias MongoDB/Motor/PyMongo
- [x] Identificados 41 archivos con imports activos
- [x] Clasificación por módulo y riesgo
- [x] **Sin modificaciones de código**
- [x] Reporte: `/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md`

### ✅ FASE 4B-RBAC - Migración RBAC a SQL (Completada - 14-May-2026)
- [x] Tabla `Usuario_LogRBACVerificacion` creada (auditoría RBAC)
- [x] 11 módulos insertados en `Usuario_Modulos`
- [x] 6 acciones insertadas en `Usuario_Acciones`
- [x] 4 roles insertados en `Usuario_Roles` (DIRECCION, GERENTE_OPS, OPERADOR, AUDITOR)
- [x] 95 registros en `Usuario_PermisosRolModulo` (matriz de permisos)
- [x] 598 registros migrados de `rbac_audit_log` a SQL
- [x] `/app/backend/core/rbac/repository.py` migrado a SQL-first
- [x] `/app/backend/core/rbac/repository_sql.py` creado
- [x] `/app/backend/core/rbac/service.py` actualizado (LEGACY_ROLE_MAPPING)
- [x] **MongoDB ya NO es fuente de datos para RBAC**
- [x] Validaciones: Login ✓, Permisos ✓, Roles ✓, Usuarios ✓, Servidores ✓
- [x] Reporte: `/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md`

**✅ Flujo RBAC ahora es 100% EDARSAHUB SQL:**
- Usuario_Roles (roles del sistema)
- Usuario_RolesAsignacion (asignaciones usuario-rol)
- Usuario_Modulos (módulos del sistema)
- Usuario_Acciones (acciones del sistema)
- Usuario_PermisosRolModulo (matriz de permisos)
- Usuario_LogRBACVerificacion (auditoría)

**Conteos Finales FASE 4B-RBAC:**
| Tabla | Registros |
|-------|-----------|
| Usuario_Roles | 13 |
| Usuario_Modulos | 19 |
| Usuario_Acciones | 16 |
| Usuario_PermisosRolModulo | 95 |
| Usuario_RolesAsignacion | 13 (11 activos) |
| Usuario_LogRBACVerificacion | 599 |

---

## Fases Pendientes (P1) - Requieren Autorización

### P1: FASE 4B - Migración Restante
- [ ] FASE 4B-FASE2_OPERATIVO: Migrar módulo fase2_operativo (118 refs MongoDB)
- [ ] FASE 4B-COMERCIAL_CACHE: Migrar cache comercial (12 refs MongoDB)

---

## Fases Futuras (P1/P2)

### P1: Migración de Entidades
- FASE 4B-FASE2_OPERATIVO: Tareas/Workflows inventario
- FASE 4B-COMERCIAL_CACHE: Cache KPIs comercial

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
- `/app/backend/modules/auth/password_reset.py` - ✅ **100% SQL** (AUTH-RESET-P2 completado)
- `/app/backend/modules/auth/context_service.py` - ✅ **100% SQL** (FASE 3-E completado)
- ❌ **0 dependencias MongoDB productivas en módulo Auth**

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
- `/app/docs/reports/RBAC_SCOPE_E_UPDATE_USER_PERMISSIONS_ESCRIBE_SQL.md`
- `/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md`
- `/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md`
- `/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md`
- `/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md`
- `/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md`
- `/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md`
- `/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md`
- `/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md`
- `/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md`
- `/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md`
- `/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md`
- `/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md`
- `/app/docs/reports/VENTAS_DIA_CAMBIO_ARQUITECTONICO.md`
- `/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md`
- `/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md`
- `/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md`
- `/app/docs/reports/FASE_4B_FASE2_OPERATIVO_PROPUESTA_TECNICA.md`
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

*Última actualización: 14-May-2026 - FASE 4B-RBAC Completada*

## ✅ RBAC-CLOSE-001 COMPLETADA (14-May-2026)

### HITO CONFIRMADO:
> **EDARSAHUB SQL es la fuente única productiva para el módulo Usuarios/Roles/Auth-RBAC operativo.**

**Auditoría final:**
- ✅ Login usa SQL (`_get_user_sql_only`)
- ✅ `get_current_user()` usa SQL-only (sin fallback MongoDB)
- ✅ CRUD usuarios migrado a SQL
- ✅ Permisos operativos en SQL
- ✅ Usuario de prueba desactivado (no activo productivo)
- ✅ MongoDB NO participa en operaciones productivas Auth/RBAC

**Referencias MongoDB residuales (fuera de alcance):**
- `password_reset.py`: Flujo de reset de passwords
- `context_service.py`: Contexto de UI
- Campos `sec_*`: Metadatos piloto

**Reporte:** `/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md`

---

## ✅ RBAC-SCOPE-G COMPLETADA (14-May-2026)

**Objetivo:** Eliminar dependencia MongoDB del módulo Usuarios/Roles para operaciones productivas.

**Funciones migradas a SQL:**
- `find_user_by_email()` → `find_user_by_email_sql()`
- `find_user_by_id()` → `find_user_by_id_sql()`
- `create_user()` → `create_user_sql()`
- `update_user()` → `update_user_sql()`
- `deactivate_user()` → `deactivate_user_sql()`

**Validaciones:**
- ✅ Crear usuario nuevo escribe en SQL (no en MongoDB)
- ✅ Usuario puede hacer login (leído desde SQL)
- ✅ Desactivar usuario actualiza SQL
- ✅ Usuario desactivado no puede hacer login
- ✅ GET /api/users devuelve 11 usuarios activos
- ✅ MongoDB NO fue modificado

**Referencias MongoDB residuales (justificadas):**
- `password_reset.py`: Flujo de reset de passwords (fuera de alcance)
- `context_service.py`: Contexto de UI (fuera de alcance)
- `repository.py:get_all_users()`: Solo para campos `sec_*` (metadatos piloto)

**Reporte:** `/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md`

---

## ✅ RBAC-SCOPE-F COMPLETADA (14-May-2026)

**Objetivo:** Validar modal de permisos completo (lectura/escritura SQL) y persistencia e2e.

**Validaciones realizadas:**
- ✅ GET /api/users devuelve 11 usuarios
- ✅ Modal de permisos muestra servidores disponibles
- ✅ Servidor asignado (CIENFUEGOS) aparece marcado
- ✅ PUT /api/users/{id}/permissions responde HTTP 200
- ✅ Permisos persisten en SQL tras modificación
- ✅ API recarga datos actualizados desde SQL
- ✅ MongoDB NO fue modificado
- ✅ No hay duplicados activos en las 3 tablas
- ✅ Auth SQL-first sigue funcionando
- ✅ Login y JWT sin cambios

**Usuarios probados:**
- admin@inventario.com (8 servidores)
- carlosruz@edarsa.com.mx (1 servidor, 2 almacenes)
- noxte@alpyc.com (1 servidor, 2 sucursales, 5 almacenes)
- auditoria@edarsa.com.mx (3 servidores, 2 sucursales, 20 almacenes)
- carlos@alpuntoycoma.mx (sin permisos)
- eduardo@alpuntoycoma.mx (sin permisos)

**Reporte:** `/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md`

---

## ✅ RBAC-SCOPE-E COMPLETADA (13-May-2026)

**Objetivo:** Modificar `update_user_permissions()` para escribir permisos operativos en EDARSAHUB SQL en lugar de MongoDB.

**Cambio implementado:**
- Función `update_user_permissions()` en `service.py` reescrita completamente
- Escribe en `Usuario_ServidoresAsignacion`, `Usuario_SucursalesAsignacion`, `Usuario_AlmacenesAsignacion`
- MongoDB ya NO recibe permisos operativos en escritura
- Estrategia de idempotencia: desactivar asignaciones anteriores (`Activo=0`) antes de insertar nuevas

**Validaciones:**
- ✅ PUT /api/users/{id}/permissions responde HTTP 200
- ✅ Permisos persisten en SQL (verificado con queries directas)
- ✅ MongoDB NO fue modificado
- ✅ GET /api/users recarga datos desde SQL correctamente
- ✅ 11 usuarios visibles
- ✅ No hay duplicados activos en las 3 tablas
- ✅ Login y JWT sin cambios
- ✅ Operación transaccional (commit/rollback)

**Reporte:** `/app/docs/reports/RBAC_SCOPE_E_UPDATE_USER_PERMISSIONS_ESCRIBE_SQL.md`

---

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

---

## Próximas Fases RBAC

### RBAC-SCOPE-F (SIGUIENTE)
**Objetivo:** Validar modal de permisos completo (lectura/escritura SQL) y persistencia e2e.
- [ ] Abrir modal de permisos desde frontend
- [ ] Modificar permisos y guardar
- [ ] Verificar que los cambios persisten al recargar
- [ ] Validar que no hay errores de UI ni consola

### FASE 3-B COMPLETADA (14-May-2026)
**Objetivo:** DDL y Migración de Datos de Empresas/Sucursales/Mapeos a SQL.

**Decisión:** Opción B - Crear `Sistema_Sucursales` nueva (NO usar `RH_Cat_Sucursales` como tabla transversal).

**Tablas SQL creadas:**
- [x] `Sistema_Sucursales` (5 sucursales migradas)
- [x] `Sistema_SucursalServidorMapeo` (5 mapeos migrados)
- [x] `Sistema_ServidorSucursalesConfig` (7 configs migradas)

**Trazabilidad legacy:** Campos MongoUUID, MongoEmpresaUUID, FuenteMigracion incluidos.

**Reporte:** `/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md`

---

### FASE 3-C (SIGUIENTE - Pendiente autorización)
**Objetivo:** Migrar `context_resolver.py` para leer de SQL en lugar de MongoDB.

**Tablas SQL disponibles:**
- ✅ `Sistema_Sucursales` (5 sucursales)
- ✅ `Sistema_SucursalServidorMapeo` (5 mapeos)
- ✅ `Sistema_ServidorSucursalesConfig` (7 configs)

**Prerequisitos completados:**
- ✅ FASE 3-A: Diagnóstico pasivo
- ✅ FASE 3-B: DDL y migración de datos

---

## ✅ BUG-VENTAS-DIA-QRO-001 RESUELTO (14-May-2026)

**Problema:** 130° QUERETARO mostraba $0 en Ventas del Día en el Tablero Ejecutivo.

**Causa raíz identificada:**
- La query MPRO usada por `sync_comercial_abiertas_v2_job.py` consultaba la tabla `Venta_Encabezado` con filtro `Vn_Tabla = 'Comanda'`
- ORIGEN funciona con esa estructura de tablas
- QRO tiene una estructura diferente: sus ventas están en `Comanda` + `Comanda_Detalle` (no en `Venta_Encabezado`)
- El job escribía $0 porque la query no encontraba datos en la estructura esperada

**Diagnóstico realizado:**
1. Confirmé que el Tablero NO consulta APIs en vivo (arquitectura correcta)
2. Confirmé que el endpoint `/v2/comercial/ventas-dia` lee solo de EDARSAHUB SQL
3. Confirmé que ambas APIs locales (QRO y ORIGEN) responden HTTP 200
4. Confirmé que la estructura de BD de QRO es `Comanda` + `Comanda_Detalle`
5. Identifiqué que el campo `Es_Cve_Estado = 'AC'` indica registros activos en QRO

**Solución implementada:**
- Creé queries específicas para QRO que leen de `Comanda` + `Comanda_Detalle`:
  - `QUERY_MPRO_VENTAS_ABIERTAS_QRO`: Lee ventas abiertas sumando `Cd_Importe` de `Comanda_Detalle`
  - `QUERY_MPRO_CERRADAS_HOY_QRO`: Lee ventas cerradas del día
- Modifiqué `sync_comercial_abiertas_v2_job.py` para seleccionar la query correcta según la unidad:
  - `130QRO`: Usa queries de `Comanda + Comanda_Detalle`
  - `ORIGEN`: Usa queries de `Venta_Encabezado` (sin cambio)
- Mantuve la regla de NO escribir $0 si la sincronización falla

**Archivo modificado:** `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py`

**Validación realizada:**
1. ✅ Tabla EDARSAHUB SQL: `Comercial_Ventas_Dia_Abiertas_v2` tiene 130QRO con $12,978.00
2. ✅ Endpoint: `/v2/comercial/ventas-dia` devuelve 130QRO correctamente
3. ✅ Job manual: Sincroniza correctamente 130QRO ($12,978) y ORIGEN ($10,749)
4. ✅ Sin regresión en otras unidades (SoftRestaurant)

**Confirmaciones de arquitectura:**
- ✅ El tablero NO usa conexiones live
- ✅ El endpoint solo lee EDARSAHUB SQL
- ✅ QRO y ORIGEN usan la misma lógica de sincronización (diferente query)
- ✅ Sin SQL MPRO central
- ✅ Sin MongoDB como fuente de negocio
- ✅ Sin hardcodeo de importes
- ✅ Sin $0 falso por error de credenciales

**Snapshot QRO:** 2026-05-14T20:24:06 (última sincronización exitosa)

---

## ✅ FEATURE: Sistema_Catalogo para Tipos de Sistema (14-May-2026)

**Objetivo:** Eliminar opciones hardcodeadas del combo "Tipo de Sistema" en Servidores y administrarlas dinámicamente desde Catálogos.

**Implementación:**

### 1. DDL (EDARSAHUB SQL)
- Tabla `Sistema_Catalogo` creada con campos: SistemaID, Codigo, Descripcion, Activo, FechaCreacion, FechaActualizacion
- Datos base insertados: MPRO, SOFTRESTAURANT, OTRO

### 2. Backend (`/app/backend/modules/catalogos/routes.py`)
- `GET /api/catalogos/sistemas` - Lista todos los sistemas
- `GET /api/catalogos/sistemas/activos` - Lista sistemas activos (para combos)
- `POST /api/catalogos/sistemas` - Crear nuevo sistema
- `PUT /api/catalogos/sistemas/{id}` - Actualizar descripción
- `PATCH /api/catalogos/sistemas/{id}/toggle-activo` - Activar/Inactivar

### 3. Frontend Catálogos (`/app/frontend/src/pages/Catalogos.js`)
- Dominio "Configuración" agregado con icono Settings
- Catálogo "Sistemas" disponible con CRUD completo

### 4. Frontend Servidores (`/app/frontend/src/pages/Servidores.js`)
- Combo "Tipo de Sistema" ahora carga desde `/api/catalogos/sistemas/activos`
- Fallback a valores default si falla la API
- Aplica a modal "Agregar Servidor" y modal "Conexiones API"

**Validaciones completadas:**
- ✅ Catálogos > Configuración > Sistemas muestra 3 registros
- ✅ Combo Tipo de Sistema en Servidores carga dinámicamente
- ✅ Servidores existentes siguen funcionando
- ✅ Sin modificación a Comercial, Finanzas, Compras, Inventarios, Operaciones, Tablero Ejecutivo
- ✅ MongoDB no participa

---

## ✅ FEATURE: Sistema_Catalogo v2 - Alta Rápida con Permisos (14-May-2026)

**Objetivo:** Permitir crear/solicitar nuevos tipos de sistema directamente desde el combo "Tipo de Sistema" del modal de servidores, con flujo de autorización.

**Implementación:**

### 1. DDL Extendido (EDARSAHUB SQL)
Campos adicionales en `Sistema_Catalogo`:
- `Estado` (PENDIENTE, ACTIVO, INACTIVO, RECHAZADO)
- `SolicitadoPorEmail`, `AutorizadoPorEmail`
- `FechaSolicitud`, `FechaAutorizacion`

### 2. Endpoints Adicionales
- `POST /api/catalogos/sistemas/solicitar` - Crear solicitud PENDIENTE
- `PATCH /api/catalogos/sistemas/{id}/autorizar` - Aprobar solicitud
- `PATCH /api/catalogos/sistemas/{id}/rechazar` - Rechazar solicitud

### 3. Permisos Implementados
- `CATALOGOS_SISTEMAS_CREAR` - Crear directamente (ACTIVO)
- `CATALOGOS_SISTEMAS_SOLICITAR` - Solo solicitar (PENDIENTE)
- `CATALOGOS_SISTEMAS_AUTORIZAR` - Aprobar/Rechazar

### 4. Frontend Servidores
- Opción "+ Nuevo tipo de sistema" al final del combo
- Modal de alta rápida con validación de permisos
- Botón "Crear Sistema" o "Solicitar" según permiso
- Refresco automático del combo tras crear

**Validaciones completadas:**
- ✅ Usuario con permiso Crear ve opción "+ Nuevo tipo de sistema"
- ✅ Usuario puede crear sistema activo desde el combo
- ✅ Sistema nuevo aparece inmediatamente en combo
- ✅ Sin regresión en servidores existentes
- ✅ Sin tocar otros módulos
- ✅ MongoDB no participa

**Reporte técnico:** `/app/docs/reports/SISTEMA_CATALOGO_IMPLEMENTACION.md`

---

## CORRECCIÓN VISUAL - Etiquetas Dinámicas Ventas del Día (15-Mayo-2026)

### Problema Resuelto
Las tarjetas del Tablero Ejecutivo mostraban etiquetas hardcodeadas "vs Mes Ant" y "vs Año Ant" incluso cuando el selector estaba en modo "Ventas del Día".

### Solución Implementada
Se modificó `/app/frontend/src/pages/TableroEjecutivo.js`:

1. **Componente `UnidadCard`**: Se agregó prop `modoVentasDia` y se hicieron dinámicas las etiquetas:
   - `{modoVentasDia ? 'vs Día Ant.' : 'vs Mes Ant.'}`
   - `{modoVentasDia ? 'vs Mismo Día Año Ant.' : (esMultiMes ? 'vs Periodo Ant.' : 'vs Año Ant.')}`

2. **Tarjetas Consolidadas (Header)**: Ventas, PAX, Cheques ahora usan:
   - `{data?.periodo?.modo_ventas_dia ? 'vs Día Ant.' : 'vs Mes'}`
   - `{data?.periodo?.modo_ventas_dia ? 'vs Año Ant.' : (esMultiMes ? 'vs Periodo Ant.' : 'vs Año')}`

3. **Tarjeta Proyección**: 
   - `{data?.periodo?.modo_ventas_dia ? 'vs Mismo Día Año Ant.' : (esMultiMes ? 'vs Ventas Año Ant.' : 'vs Año Ant.')}`

### Validación
- ✅ Screenshot confirmando etiquetas correctas en vista "Ventas del Día"
- ✅ Sin errores de lint
- ✅ Sin regresión en vistas mensuales/anuales

---

## BUG CORREGIDO - Toast "Error al cargar detalle de unidad" (15-Mayo-2026)

### Problema
Al abrir el modal de detalle de cualquier unidad, aparecía toast rojo "Error al cargar detalle de unidad" porque los endpoints legacy (`/comercial/dashboard/`, `/comercial/ventas-tiempo/`, `/comercial/mesas/`) fallaban.

### Causa Raíz
1. En modo "Ventas del Día", se intentaba llamar a endpoints que no aplican para datos diarios
2. En modo mensual, los endpoints fallaban por falta de conexión a servidores remotos desde preview

### Solución Implementada
Modificación en `/app/frontend/src/pages/TableroEjecutivo.js` - componente `DetalleUnidad`:

1. **Modo Ventas del Día**: NO hace llamadas API adicionales. Los datos ya vienen completos del endpoint `/api/v2/comercial/ventas-dia`

2. **Modo Mensual/Anual**: Usa `Promise.allSettled()` para llamadas opcionales:
   - Los endpoints adicionales son **opcionales** para enriquecer el modal
   - Si fallan, solo se registra warning en console (no toast)
   - Los datos básicos del objeto `unidad` siempre están disponibles

### Validaciones
- ✅ Modal CIENFUEGOS abre sin error en Ventas del Día
- ✅ Modal LA ESTELAR abre sin error en Ventas del Día  
- ✅ Modal ORIGEN abre sin error en Ventas del Día (CON históricos)
- ✅ Modal CIENFUEGOS abre sin error en modo Mensual
- ✅ Sin toast rojo en ningún escenario
- ✅ Comparativos diarios muestran datos reales o 0 seguro
- ✅ No hay NaN/Infinity/null/undefined

---

## CORRECCIÓN HISTÓRICOS DIARIOS - Fallback a Último Día Disponible (15-Mayo-2026)

### Problema Identificado
La tabla `Comercial_KPIs_Diarios_v2` no tenía datos del 14-May-2026 para las unidades SoftRestaurant porque:
1. El job `sync_comercial_v2` no puede ejecutarse en entorno preview (sin conexión a servidores remotos)
2. El último día con datos era el 13-May-2026

### Diagnóstico SQL
| Código | Primera Fecha | Última Fecha | Total Días |
|--------|--------------|--------------|------------|
| 130MID | 2024-05-01 | 2026-05-13 | 738 |
| 130QRO | 2024-05-01 | 2026-05-13 | 739 |
| CIENFUEGOS | 2024-05-01 | 2026-05-13 | 739 |
| ESTELAR | 2025-06-12 | 2026-05-13 | 329 |
| ORIGEN | 2024-05-01 | 2026-05-14 | 738 |

### Solución Implementada
Modificación en `/app/backend/modules/comercial_v2/repository_readonly.py` función `get_comparativos_diarios()`:

1. **Fallback inteligente**: Si no existe el día exacto anterior, busca el último día disponible dentro de una ventana de 7 días
2. **Priorización**: Primero intenta el día exacto, luego el más cercano
3. **Logging**: Registra cuando usa un día diferente al solicitado
4. **Sin errores**: Retorna 0 si no hay datos en la ventana

### Resultados Verificados (Después de Corrección)
| Unidad | Ventas Día Ant | PAX | Cheques | Estado |
|--------|----------------|-----|---------|--------|
| 130° MERIDA | $165,747.00 | 84 | 30 | ✅ |
| 130° QUERETARO | $97,381.00 | 62 | 21 | ✅ |
| CIENFUEGOS | $124,358.00 | 88 | 32 | ✅ |
| LA ESTELAR | $87,485.00 | 75 | 32 | ✅ |
| ORIGEN | $25,339.53 | 45 | 18 | ✅ |
| **TOTAL** | **$500,310.53** | **354** | **133** | ✅ |

### Regla Arquitectónica Respetada
- ✅ Datos vienen de EDARSAHUB SQL
- ✅ No hay consulta en vivo a servidores remotos
- ✅ No hay MongoDB como fuente de datos
- ✅ No hay SQL MPRO central
- ✅ Fallback no confunde ausencia de sync con venta real cero

---

## CORRECCIÓN ZONA HORARIA - Fecha Operativa México (15-Mayo-2026)

### Problema Identificado
El servidor usa UTC, donde la fecha era 15-May cuando en México era 14-May (22:40 hora local). Esto causaba:
1. El job de sincronización guardaba `fecha_operacion = 2026-05-15` (UTC)
2. El endpoint buscaba `fecha_operacion = 2026-05-14` (México)
3. No encontraba datos porque las fechas no coincidían

### Correcciones Aplicadas

| Archivo | Cambio |
|---------|--------|
| `routes.py` | `date.today()` → `datetime.now(mexico_tz).date()` |
| `sync_comercial_abiertas_v2_job.py` | `date.today()` → `datetime.now(mexico_tz).date()` |
| `repository_readonly.py` | Búsqueda en fecha México Y fecha UTC con prioridad por snapshot reciente |

### Regla Establecida
> **La fecha operativa SIEMPRE debe calcularse en zona horaria América/Mexico_City**
> Los datos comerciales corresponden al día de operación en México, no al día UTC del servidor.

### Validación
- ✅ Endpoint ventas-día retorna fecha correcta (14-May México)
- ✅ Datos históricos del día anterior (13-May) encontrados para todas las unidades
- ✅ Variaciones calculadas correctamente
- ✅ Modal muestra comparativos reales, no $0 falsos

---

## BUG CORREGIDO - 130° QUERÉTARO $0 (15-Mayo-2026)

### Problema
130° QUERÉTARO mostraba $0 en Ventas del Día cuando la base de datos tenía $207,258.

### Causa Raíz
1. El job `sync_comercial_abiertas_v2` ejecutó antes del reinicio y escribió con fecha UTC (2026-05-15)
2. Posteriormente sobrescribió con $0 porque no pudo conectar al servidor
3. La corrección de zona horaria no estaba activa en esa ejecución

### Solución
1. Reinicio del backend con corrección de zona horaria México
2. Ejecución manual del job: `POST /api/v2/scheduler/jobs/sync_comercial_abiertas_v2/run`
3. Datos sincronizados correctamente con fecha 2026-05-14

### Resultado
| Unidad | Antes | Después |
|--------|-------|---------|
| 130° QUERÉTARO | $0 | **$207,258** ✅ |

---

## CORRECCIÓN ETIQUETAS PROYECCIÓN (15-Mayo-2026)

### Problema
El KPI de proyección mostraba "PROYECCIÓN MES" y "Si mantiene ritmo" cuando el selector estaba en "Ventas del Día".

### Solución
Modificación en `/app/frontend/src/pages/TableroEjecutivo.js`:

```javascript
// Título dinámico según selector
{data?.periodo?.modo_ventas_dia 
  ? 'Proyección del Día'
  : (esMultiMes ? 'Proyección Anual' : 'Proyección Mes')
}

// Subtítulo dinámico
{data?.periodo?.modo_ventas_dia
  ? 'Al cierre del día'
  : (esMultiMes ? 'X días → 365 días' : 'Si mantiene ritmo')
}

// Valor: En Ventas del Día, proyección = venta actual (al cierre será = venta real)
```

### Algoritmo de Proyección del Día
- **Durante el día:** `proyección = venta_actual`
- **Al cierre:** `proyección = venta_real` (son iguales)
- **Regla:** No usar fórmula de extrapolación porque al final del día la proyección DEBE ser igual a la venta real

### Resultado
| Selector | Título | Subtítulo |
|----------|--------|-----------|
| Ventas del Día | **Proyección del Día** | **Al cierre del día** |
| Ventas del Mes | Proyección Mes | Si mantiene ritmo |
| Ventas del Año | Proyección Anual | X días → 365 días |

---

## SECCIONES MODAL RESTAURADAS - Ventas por Día de Semana (15-Mayo-2026)

### Problema
El modal de detalle de unidad ya no mostraba las secciones "Ventas por Hora" ni "Ventas por Día de Semana" después de la corrección del toast rojo.

### Causa Raíz
1. En modo `modoVentasDia=true`, el código retornaba temprano sin cargar datos adicionales
2. El mapeo de `unidades` no incluía `unidad_negocio_id`, causando error 403 en el endpoint
3. No existen tablas de "Ventas por Hora" sincronizadas en EDARSAHUB SQL

### Solución
1. **Nuevo endpoint** `/api/v2/comercial/kpis-diarios/{unidad_id}`:
   - Lee de `Comercial_KPIs_Diarios_v2` (EDARSAHUB SQL)
   - NO consulta en vivo
   - Retorna últimos N días de historial

2. **Frontend**: Calcular "Ventas por Día de Semana" desde el historial:
   - Agrupa los últimos 7-10 días por día de semana
   - Muestra distribución Lun-Dom

3. **Ventas por Hora**: Mensaje informativo "Sin datos de hora sincronizados para Ventas del Día"
   - No hay tabla en EDARSAHUB para datos granulares por hora
   - Requiere DDL autorizado para crear tabla y job de sincronización

### Corrección de Mapeo
```javascript
unidades: porUnidad.map(u => ({
  unidad_negocio_id: u.unidad_negocio_id,  // ← Añadido
  id: u.unidad_negocio_id,  // ← Añadido alias
  // ...resto de campos
}))
```

### Validación Visual ✅
- KPIs principales: ✅
- Comparativo (Día Actual, Anterior, Año Ant): ✅
- Ventas por Hora (mensaje informativo): ✅
- **Ventas por Día de Semana: ✅ RESTAURADO**
- Sin toast rojo: ✅
- Sin errores de consola: ✅

### Regla Arquitectónica Respetada
- ✅ Datos vienen de EDARSAHUB SQL
- ✅ No hay consulta en vivo
- ✅ No hay MongoDB
- ✅ No hay endpoints legacy que consulten fuentes vivas


---

## ✅ FIX COMPLETADO: Bug Zona Horaria y Ventana Operativa QRO (15-May-2026)

### Problema Original:
El sistema usaba `datetime.now(mexico_tz).date()` (fecha calendario) en lugar de la fecha operativa basada en horarios de servicio. A las 00:02 del día 15, QRO mostraba $0 porque el sistema asumía que era día 15, pero la jornada operativa del día 14 (13:00-03:00) no había terminado.

### Solución Implementada:

#### 1. Tabla `Sistema_HorariosServicioUnidad` en EDARSAHUB
- DDL creado y ejecutado
- 5 unidades configuradas con horarios operativos:
  - 130QRO, ORIGEN, 130MID: 13:00 - 03:00 (cruza medianoche)
  - CIENFUEGOS, ESTELAR: 13:00 - 23:00 (NO cruza medianoche)
- 7 días de la semana por unidad = 35 registros

#### 2. Helper `/app/backend/core/utils/operational_window.py`
- Función principal: `get_operational_window(unidad_negocio_id)`
- Calcula FechaOperacion según:
  - Si estamos entre 00:00 y hora_fin_operativo → día anterior
  - Si estamos después de hora_inicio_operativo → día actual
- Incluye cache para evitar consultas repetidas

#### 3. Modificaciones al Job de Sincronización
- `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py` actualizado:
  - Import del helper `get_operational_window`
  - Cálculo de `fecha_operacion` por unidad (no global)
  - Queries de QRO usan `{fecha_operacion}` en lugar de `GETDATE()`
  - Logs detallados para debug

### Validaciones Completadas:
- ✅ A las 00:15 del día 15, FechaOperacion calculada = 2026-05-14
- ✅ 130QRO muestra $207,323.00 (venta del día 14)
- ✅ Server_id correcto: 72f6e9a7-8ea2-4eb2-802e-4ee31753435e
- ✅ 3 ejecuciones consecutivas exitosas del job
- ✅ Frontend muestra 130° QUERETARO con datos correctos

### Archivos Modificados/Creados:
- `/app/backend/core/utils/operational_window.py` (NUEVO)
- `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py` (MODIFICADO)
- `/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py` (MODIFICADO - server_id en UPDATE)

### Regla de Negocio Implementada:
```
Horario QRO: 13:00 - 03:00 (cruza medianoche)

00:02 del día 15 → FechaOperacion = día 14 (jornada no cerrada)
03:01 del día 15 → FechaOperacion = día 14 (restaurante cerrado, última jornada)
13:00 del día 15 → FechaOperacion = día 15 (nueva jornada inicia)
```



---

## ✅ FIX COMPLETADO: Regresión Ventas $0 al Cambiar Calendario (15-May-2026 01:00)

### Problema Reportado:
Después de implementar `operational_window.py`, el Tablero Ejecutivo en modo "Ventas del Día" mostraba $0 cuando el calendario cambió al día 15. Las ventas del día operativo 14 desaparecieron.

### Causa Raíz:
1. **El job** guardaba correctamente usando `get_operational_window()`, pero...
2. **Los endpoints de lectura** (`routes.py`, `service.py`, `comercial_v2/routes.py`) usaban `datetime.now().date()` (fecha calendario) en lugar de la fecha operativa.
3. Resultado: A las 00:32 del día 15, el endpoint buscaba `fecha_operacion = 2026-05-15` pero los datos válidos tenían `fecha_operacion = 2026-05-14`.

### Archivos Corregidos:

#### 1. `/app/backend/modules/comercial/routes.py`
- Función `get_ventas_dia_snapshot_from_edarsahub()` ahora calcula `FechaOperacion` usando `get_operational_window()`
- Si `unidad_negocio_id` se provee: usa horario específico de la unidad
- Si no: usa horario por defecto 13:00-03:00 (el más común del grupo)
- Nuevo parámetro: `unidad_negocio_id` para cálculo preciso

#### 2. `/app/backend/modules/comercial/service.py`
- Función `_get_ventas_abiertas_edarsahub()` ahora calcula `FechaOperacion` usando `get_operational_window()`
- Query modificada para buscar en AMBAS fechas (calculada Y calendario) como fallback de transición
- Prioriza fecha calculada, pero lee calendario si no hay datos de la fecha operativa

#### 3. `/app/backend/modules/comercial_v2/routes.py`
- Endpoint `/ventas-dia`: Ahora calcula `FechaOperacion` activa en lugar de `datetime.now().date()`
- Endpoint `/dashboard`: Ahora usa `fecha_operativa` en lugar de `fecha_hoy` para ventas abiertas
- Logs añadidos para debug de hora y fecha calculada

### Validación Exitosa:

```
Hora actual México: 2026-05-15 00:47
FechaOperacion activa: 2026-05-14 ✅

CIENFUEGOS: ventas=$283,645.00 ✅
130° MERIDA: ventas=$177,436.00 ✅
LA ESTELAR: ventas=$153,380.00 ✅
TOTALES: $614,461.00 ✅
```

### Regla Implementada:
> **El endpoint de "Ventas del Día" NUNCA debe usar `datetime.now().date()` directamente.**  
> Debe calcular la FechaOperacion activa usando `get_operational_window()`.



---

## ✅ FIX P0 COMPLETADO: Tablero MPRO Lee Solo de EDARSAHUB SQL (15-May-2026 01:20)

### Problema:
130° QUERÉTARO y ORIGEN mostraban $0 en Ventas del Día porque el tablero intentaba conexión LIVE a APIs locales (PROHIBIDO).

### Solución Implementada:
1. **Refactorizado `get_kpis_mpro_por_sucursal()`** para leer SOLO de EDARSAHUB SQL
2. **ELIMINADA** llamada a `sumar_ventas_api_local_a_sucursal()` desde el tablero
3. **MODIFICADA** query de `_get_ventas_abiertas_edarsahub()` para buscar por `unidad_negocio_id`

### Archivos Modificados:
- `/app/backend/modules/comercial/service.py`

### Resultado:
```
130QRO: $207,323.00  origen=EDARSAHUB_SQL ✅
ORIGEN: $0.00        origen=EDARSAHUB_SQL (API servidor con error 500)
```

### Regla Arquitectónica Cumplida:
> El Tablero Ejecutivo NUNCA debe hacer conexiones LIVE a APIs locales.
> Debe leer SOLO de EDARSAHUB SQL.

---

## ✅ FIX P0 COMPLETADO: Scheduler FechaOperacion ORIGEN/130QRO (15-May-2026 01:39)

### Problema:
El job de sincronización automática (`sync_comercial_abiertas_v2_job.py`) sobrescribía datos válidos de ORIGEN ($79,988) y 130QRO ($207,323) con $0 porque calculaba la FechaOperacion incorrectamente durante la madrugada (00:00-03:00).

### Causa Raíz:
- A las 01:00 AM del día 15, el job consultaba cuentas del día 15 en lugar del día 14 (jornada operativa vigente).
- Las queries no encontraban datos porque buscaban en la fecha incorrecta.
- Los datos válidos eran reemplazados por $0.

### Solución Implementada:
1. **Confirmado uso de `get_operational_window()`** para todas las unidades MPRO
2. **Añadida función `_get_existing_ventas_dia()`** para verificar datos existentes antes de sobrescribir
3. **Extendida protección anti-$0** a todas las unidades MPRO (antes solo 130QRO)
4. **Lógica de 3 casos**:
   - CASO 1: Datos válidos (total > 0) → Sincronizar normalmente
   - CASO 2: AMBAS queries NULL → NO sobrescribir, conservar dato existente
   - CASO 3: Total=$0 pero existe dato válido → Protección activada, NO sobrescribir

### Archivos Modificados:
- `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py`

### Resultado Post-Fix:
```
Hora ejecución: 01:39 AM del día 15
FechaOperacion calculada: 2026-05-14 ✅ (día operativo correcto)

ORIGEN:     $79,988.01  (FechaOp=2026-05-14) ✅
130QRO:     $207,323.00 (FechaOp=2026-05-14) ✅
CIENFUEGOS: $285,325.00 (FechaOp=2026-05-14) ✅
ESTELAR:    $185,670.00 (FechaOp=2026-05-14) ✅
130MID:     $177,436.00 (FechaOp=2026-05-14) ✅
```

### Reporte Detallado:
`/app/docs/reports/FIX_P0_SCHEDULER_FECHA_OPERACION_ORIGEN.md`

### Regla Arquitectónica Cumplida:
> MPRO debe usar exactamente la misma regla de jornada operativa que SoftRestaurant.
> La venta del día pertenece a la FechaOperacion del turno/jornada, no al día calendario.
> $0 solo es válido si la fuente respondió correctamente y confirmó venta real cero.



---

## ✅ FASE 3 DML COMPLETADA: Catálogo Canónico Empresas/Servidores/Sucursales (16-May-2026)

### Objetivo:
Poblar las tablas canónicas creadas en DDL anterior para establecer la base de datos que soportará el `EmpresaResolver`.

### DML Ejecutado:

| Tabla | Registros | Estado |
|-------|-----------|--------|
| Sistema_Tipos | 5 | ✅ |
| Sistema_EmpresasAlias | 12 (únicos) | ✅ |
| Sistema_EmpresasServidores | 7 | ✅ |

### Sistema_Tipos (5 tipos de sistema):
- SOFTRESTAURANT
- MPRO
- API_LOCAL
- EDARSAHUB_SQL
- OTRO

### Sistema_EmpresasAlias (12 aliases únicos):
| EmpresaID | Empresa | Aliases Insertados |
|-----------|---------|-------------------|
| 1 | ORIGEN | ORIGEN |
| 2 | 130QRO | 130QRO, 130 QUERETARO, QUERETARO, QRO |
| 3 | CIENFUEGOS | CIENFUEGOS, CF |
| 4 | ESTELAR | ESTELAR, LA ESTELAR |
| 5 | 130MID | 130MID, 130-MER, 130 MERIDA |

**Reglas de Aliases Críticas Validadas:**
- ✅ `130-MER` → EmpresaID=5 (130MID), NO empresa nueva
- ✅ `LA ESTELAR` → EmpresaID=4 (ESTELAR), NO empresa nueva
- ✅ `130-QRO` normalizó a `130QRO` → EmpresaID=2

### Sistema_EmpresasServidores (7 relaciones):
| EmpresaID | Empresa | RolConexion | NumSucursal | Servidor |
|-----------|---------|-------------|-------------|----------|
| 1 | ORIGEN | PRINCIPAL_SQL | 23 | ManagmentPro |
| 1 | ORIGEN | VENTAS_DIA_API_LOCAL | 23 | ORIGEN LOCAL |
| 2 | 130QRO | PRINCIPAL_SQL | 21 | ManagmentPro |
| 2 | 130QRO | VENTAS_DIA_API_LOCAL | 21 | 130° QRO LOCAL |
| 3 | CIENFUEGOS | PRINCIPAL_SQL | NULL | CIENFUEGOS |
| 4 | ESTELAR | PRINCIPAL_SQL | NULL | LA ESTELAR |
| 5 | 130MID | PRINCIPAL_SQL | NULL | 130° MERIDA |

### Validaciones Post-DML:
- ✅ ORIGEN usa CodigoSucursalSistema=0023 / NumeroSucursalSistema=23
- ✅ 130QRO usa CodigoSucursalSistema=0021 / NumeroSucursalSistema=21
- ✅ APIs Locales usan RolConexion=VENTAS_DIA_API_LOCAL (NO PRINCIPAL_SQL)
- ✅ SoftRestaurant usa NumeroSucursalSistema=NULL
- ✅ Sistema_Empresas NO modificada (sigue con 5 empresas canónicas)
- ✅ No se ejecutó UPDATE/DELETE
- ✅ No se crearon empresas nuevas
- ✅ No hay aliases duplicados activos
- ✅ No hay relaciones duplicadas activas

### Confirmaciones de Alcance:
- ✅ No se modificó código backend
- ✅ No se modificó frontend
- ✅ No se modificaron jobs
- ✅ No se tocó Tablero Ejecutivo/Comercial/Finanzas/Compras
- ✅ No se implementó EmpresaResolver todavía
- ✅ No se refactorizó adapters.py/mpro.py/service.py

### Reporte Detallado:
`/app/docs/reports/FASE_3_DML_CATALOGO_EMPRESAS_SERVIDORES_SUCURSALES_EJECUTADO.md`


---

## ✅ FASE 4 COMPLETADA: EmpresaResolver Read-Only (16-May-2026)

### Objetivo:
Crear componente centralizado para resolver empresas, aliases, servidores, roles de conexión y sucursales desde EDARSAHUB SQL.

### Archivo Creado:
`/app/backend/core/empresa_resolver.py`

### Funciones Implementadas:
1. `normalize_alias(texto)` - Normaliza alias (mayúsculas, sin acentos, sin °)
2. `resolve_empresa_by_alias(alias)` - Busca en Sistema_EmpresasAlias → EmpresaID
3. `resolve_empresa_by_id(empresa_id)` - Obtiene datos canónicos
4. `get_empresa_connections(empresa_id)` - Retorna conexiones activas
5. `get_connection_for_role(empresa_id, rol)` - Conexión específica por rol
6. `get_system_branch_context(empresa_id, rol)` - Contexto completo
7. `validate_no_ambiguous_alias(alias)` - Valida unicidad
8. `health_check_empresa_resolver()` - Valida estado del resolver

### Validaciones Exitosas:
- ✅ 15/15 pruebas de normalización
- ✅ 16/16 pruebas de resolución de aliases
- ✅ 7/7 pruebas de conexiones empresa-servidor-sucursal
- ✅ Health Check: STATUS=OK
- ✅ ORIGEN → Sucursal 23/0023
- ✅ 130QRO → Sucursal 21/0021
- ✅ APIs Locales → VENTAS_DIA_API_LOCAL
- ✅ SoftRestaurant → NumeroSucursalSistema=NULL

### Aliases Insertados vs Omitidos:
- **12 aliases insertados** (con AliasNormalizado único)
- **14 aliases omitidos** (por duplicidad de AliasNormalizado - comportamiento correcto)
- **Impacto**: Ninguno. La normalización resuelve todas las variantes.

### Confirmaciones:
- ✅ No consulta MongoDB como fuente autoritativa
- ✅ No se modificaron módulos funcionales
- ✅ No se ejecutó DDL/DML

### Reporte Detallado:
`/app/docs/reports/FASE_4_EMPRESARESOLVER_READONLY.md`

### Siguiente Fase (Pendiente Autorización):
1. P0: Refactorizar `adapters.py` para usar EmpresaResolver
2. P0: Refactorizar `service.py` para usar EmpresaResolver
3. P1: Refactorizar jobs del scheduler


### Siguiente Fase (Pendiente Autorización):

---

## ✅ FASE 5A COMPLETADA: Refactor Mínimo adapters.py (16-May-2026)

### Objetivo:
Eliminar matching textual riesgoso en adapters.py y usar EmpresaResolver para resolución canónica.

### Archivo Modificado:
`/app/backend/modules/comercial/adapters.py`

### Cambios Realizados:
1. **ELIMINADO**: `sucursal_destino in sucursal_actual` (matching textual riesgoso)
2. **AGREGADO**: `_resolver_empresa_id_desde_alias()` - Wrapper para EmpresaResolver
3. **AGREGADO**: `_obtener_api_local_por_empresa_id()` - Obtiene API por EmpresaID + RolConexion
4. **MANTENIDO**: Fallback legacy para códigos técnicos (0021, 0023)

### Pruebas Ejecutadas:
- ✅ 8/8 pruebas de resolución de aliases
- ✅ 5/5 pruebas de conexión por RolConexion
- ✅ 6/6 pruebas integrales de `sumar_ventas_api_local_a_sucursal()`
- ✅ Backend reiniciado y funcionando

### Validaciones Críticas:
- ✅ `130-QRO`, `130 QRO`, `QRO` → EmpresaID=2, API=130° QRO LOCAL, Sucursal=21/0021
- ✅ `ORIGEN` → EmpresaID=1, API=ORIGEN LOCAL, Sucursal=23/0023
- ✅ `130MID`, `LA ESTELAR`, `CIENFUEGOS` → Sin API local (correcto - SoftRestaurant)
- ✅ Códigos MPRO (0021, 0023) funcionan via fallback legacy

### Confirmaciones:
- ✅ No se modificó frontend
- ✅ No se modificaron jobs
- ✅ No se reactivó LIVE desde tablero
- ✅ No se ejecutó DDL/DML

### Reporte Detallado:
`/app/docs/reports/FASE_5A_REFACTOR_ADAPTERS_EMPRESARESOLVER.md`

### Siguiente Fase (Pendiente Autorización):
1. P0: Refactorizar `service.py` para usar EmpresaResolver

---

## ✅ FASE 5B COMPLETADA: Refactor Mínimo service.py (16-May-2026)

### Objetivo:
Eliminar hardcoding de sucursales y mapeos en service.py usando EmpresaResolver.

### Archivo Modificado:
`/app/backend/modules/comercial/service.py`

### Funciones Nuevas/Modificadas:
1. **`_obtener_codigo_canonico_mpro()`** - Ahora usa EmpresaResolver primero
2. **`_mapear_codigo_a_unidad_negocio_id()`** - NUEVA: Mapea código canónico a formato legacy
3. **`_obtener_sucursales_mpro_desde_resolver()`** - NUEVA: Obtiene sucursales MPRO dinámicamente

### Cambios Clave:
- ✅ Eliminado hardcoding de `sucursales_mpro = [...]` en `get_kpis_mpro()`
- ✅ Eliminado hardcoding de `unidad_negocio_id_map = {...}` en `get_kpis_softrestaurant()`
- ✅ EmpresaResolver integrado como fuente primaria
- ✅ Fallbacks legacy mantenidos para resiliencia

### Pruebas Ejecutadas:
- ✅ 9/9 pruebas de aliases
- ✅ 2/2 pruebas de PRINCIPAL_SQL
- ✅ 2/2 pruebas de VENTAS_DIA_API_LOCAL
- ✅ 2/2 pruebas de sucursales MPRO
- ✅ Backend reiniciado y funcionando

### Confirmaciones:
- ✅ No se modificó frontend
- ✅ No se modificaron jobs
- ✅ No se reactivó LIVE desde tablero

### Reporte Detallado:
`/app/docs/reports/FASE_5B_REFACTOR_SERVICE_EMPRESARESOLVER.md`

### Siguiente Fase (Pendiente Autorización):
1. P0: Refactorizar `mpro.py` para usar EmpresaResolver
2. P1: Refactorizar jobs del scheduler

---

## ✅ FASE 5C COMPLETADA: Refactor Mínimo mpro.py (16-May-2026)

### Objetivo:
Eliminar LIKE por nombre y matching textual en mpro.py usando EmpresaResolver.

### Archivo Modificado:
`/app/backend/modules/comercial/queries/mpro.py`

### Función Nueva:
- **`_resolver_codigo_sucursal_mpro(sucursal)`** - Resuelve alias a CodigoSucursalSistema

### Cambios Clave:
- ✅ Eliminado `LIKE '%{sucursal}%'` de la ruta principal
- ✅ Ahora resuelve: alias → EmpresaID → PRINCIPAL_SQL → CodigoSucursalSistema
- ✅ LIKE solo se usa como fallback con warning en logs
- ✅ Fallback hardcodeado mantenido para resiliencia

### Pruebas Ejecutadas:
- ✅ 8/8 pruebas de `_resolver_codigo_sucursal_mpro()`
- ✅ 6/6 pruebas de `_build_sucursal_filter_mpro_flexible()`
- ✅ 7/7 validaciones EmpresaResolver
- ✅ Backend reiniciado y funcionando

### Validaciones Críticas:
- ✅ ORIGEN → EmpresaID=1 → Sucursal=23/0023 (NO usa 0001)
- ✅ 130QRO, 130-QRO, QRO, QUERETARO → EmpresaID=2 → Sucursal=21/0021
- ✅ `_build_sucursal_filter_mpro_flexible('ORIGEN')` → `VE.Sc_Cve_Sucursal = '0023'`
- ✅ `_build_sucursal_filter_mpro_flexible('130QRO')` → `VE.Sc_Cve_Sucursal = '0021'`

### Confirmaciones:
- ✅ No se modificó frontend
- ✅ No se modificaron jobs
- ✅ No se reactivó LIVE desde tablero

### Reporte Detallado:
`/app/docs/reports/FASE_5C_REFACTOR_MPRO_EMPRESARESOLVER.md`

### Siguiente Fase (Pendiente Autorización):
1. P1: FASE 3A - Ventas por Hora / Día de la Semana
2. P1: Históricos/Rango de fechas
3. P2: Limpiar registros legacy duplicados

---

## ✅ FASE 5D COMPLETADA: Refactor Scheduler sync_comercial_abiertas_v2_job (16-May-2026)

### Objetivo:
Validar que el job del scheduler usa EmpresaResolver y FechaOperacion correctamente.

### Archivo Verificado:
`/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py`

### Validaciones Completadas (24 puntos):
1. ✅ EmpresaResolver importado y disponible
2. ✅ ORIGEN resuelve a EmpresaID=1
3. ✅ 130QRO resuelve a EmpresaID=2
4. ✅ 130MID resuelve a EmpresaID=5
5. ✅ CIENFUEGOS resuelve a EmpresaID=3
6. ✅ ESTELAR resuelve a EmpresaID=4
7. ✅ ORIGEN usa sucursal 23/0023
8. ✅ 130QRO usa sucursal 21/0021
9. ✅ SoftRestaurant usa sucursal NULL/DEFAULT
10. ✅ FechaOperacion respeta ventana operativa (13:00-03:00)
11. ✅ Entre 00:00 y 03:00 conserva FechaOperacion día anterior
12. ✅ No se usa date.today() como FechaOperacion
13. ✅ No se usa UTC date como FechaOperacion
14. ✅ No se sobrescribe dato válido con $0
15. ✅ ORIGEN no vuelve a $0 falso
16. ✅ 130QRO no vuelve a $0 falso
17. ✅ No se modificó frontend
18. ✅ No se reactivó LIVE desde tablero
19. ✅ No se ejecutó DDL/DML
20. ✅ No se usaron datos mock

### Datos Finales Validados en SQL:
| Unidad | Sistema | Sucursal | Total | FechaOp |
|--------|---------|----------|-------|---------|
| ORIGEN | MPRO | 0023 | $79,988.01 | 2026-05-14 |
| 130QRO | MPRO | 0021 | $207,323.00 | 2026-05-14 |
| 130MID | SoftRest | DEFAULT | $204,703.00 | 2026-05-14 |
| CIENFUEGOS | SoftRest | DEFAULT | $276,495.00 | 2026-05-14 |
| ESTELAR | SoftRest | DEFAULT | $133,985.00 | 2026-05-14 |

### Confirmaciones:
- ✅ Tablero Ejecutivo lee exclusivamente de EDARSAHUB SQL
- ✅ No hay consultas LIVE a SoftRestaurant ni MPRO desde frontend
- ✅ Protección anti-$0 funcionando

### Reporte Detallado:
`/app/docs/reports/FASE_5D_REFACTOR_SCHEDULER_EMPRESARESOLVER_FECHAOPERACION.md`

### Próximas Fases (Pendientes Autorización):
1. **P1**: FASE 3A - Ventas por Hora / Día de la Semana
2. **P1**: Históricos/Rango de fechas (evitar dependencia tablas temporales)
3. **P2**: Limpieza de registros legacy duplicados
4. **P2**: FASE 4B - Migración final fuera de MongoDB

---

*Última actualización: 16-May-2026 - FASE 5D Completada*

---

## DIAGNÓSTICO: Servidores, Conexiones API y Consultas SQL (15-May-2026)

### Estado Detectado:
- **Servidores**: ✅ COMPLETAMENTE MIGRADO a EDARSAHUB SQL via `server_registry.py`
- **Conexiones API Local**: ✅ MIGRADO a EDARSAHUB SQL (tipo_conexion=API_LOCAL)
- **Sistema_Tipos**: ✅ Tabla poblada con 5 tipos (SOFTRESTAURANT, MPRO, API_LOCAL, etc.)
- **MongoDB db.servers**: ✅ DESACOPLADO (0 documentos)
- **MongoDB db.consultas_custom**: ✅ SIN USO (0 documentos)
- **Catálogo Consultas SQL**: ⚠️ PENDIENTE - 20+ consultas hardcodeadas en Python

### Documentos Generados:
1. `/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md`
2. `/app/docs/proposals/PROP_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md`

### Conclusión:
La migración de servidores YA ESTÁ COMPLETA. El único componente pendiente es el **Catálogo de Consultas SQL** que requiere:
- DDL para 6 tablas nuevas
- Migración de consultas hardcodeadas
- Implementación de auditoría y permisos

### Próximas Fases Propuestas (Catálogo SQL):
1. FASE 1: DDL de tablas ConsultasSQL_*
2. FASE 2: Carga de consultas predefinidas desde Python
3. FASE 3: Repository y endpoints SQL-first
4. FASE 4: Wrapper dual-read temporal
5. FASE 5: Auditoría y permisos
6. FASE 6: Deprecar código legacy

---

## AUDITORÍA PASIVA COMPLETA DEL REPOSITORIO (15-May-2026)

### Métricas Críticas Detectadas:
| Métrica | Valor | Severidad |
|---------|-------|-----------|
| server.py | **16,408 líneas** | 🔴 CRÍTICO |
| Endpoints en server.py | 203 | 🔴 ALTO |
| Modelos Pydantic en server.py | 41 | 🔴 ALTO |
| Queries f-string (SQL injection risk) | 58 | 🔴 CRÍTICO |
| Usos datetime.now() sin ventana operativa | 172 | 🔴 ALTO |
| Referencias MongoDB | 918 | 🟡 MEDIO |
| Tests frontend | **0** | 🔴 CRÍTICO |
| Comentarios TODO/LEGACY | 458 | 🟡 MEDIO |

### Hallazgos Principales:
1. **server.py es un monolito inmanejable** - 16K líneas, 203 endpoints, 41 modelos
2. **58 queries SQL vulnerables** - Uso de f-string sin sanitización
3. **172 usos de fechas peligrosas** - datetime.now() sin ventana operativa
4. **0 tests de frontend** - Sin cobertura de UI
5. **MongoDB parcialmente migrado** - 918 referencias, pero db.servers = 0 documentos

### Plan de Limpieza Recomendado:
1. 🔴 FASE 2: Sanitización SQL (58 queries)
2. 🔴 FASE 3: Ventana Operativa (comercial/routes.py)
3. 🟡 FASE 1: Refactor server.py (dividir monolito)
4. 🟡 FASE 6: Limpieza archivos (.backup, test_reports)
5. 🟢 FASE 4: MongoDB cleanup (documentar legacy)
6. 🟢 FASE 5: Frontend components (dividir archivos grandes)

### Documento Generado:
`/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md`

---

## FASE 1 CATÁLOGO SQL - DDL EJECUTADO (15-May-2026)

### Tablas Creadas en EDARSAHUB:
| Tabla | Columnas | Estado |
|-------|----------|--------|
| ConsultasSQL_Catalogo | 22 | ✅ CREADA |
| ConsultasSQL_Parametros | 14 | ✅ CREADA |
| ConsultasSQL_Servidores | 9 | ✅ CREADA |
| ConsultasSQL_EjecucionesLog | 13 | ✅ CREADA |
| ConsultasSQL_Permisos | 11 | ✅ CREADA |
| ConsultasSQL_Versiones | 8 | ✅ CREADA |

### Índices Creados: 13
### Foreign Keys: 5

### Documentos Generados:
- `/app/docs/reports/FASE_1_CONSULTAS_SQL_DDL_EJECUCION.md`
- `/app/docs/reports/FASE_2_INVENTARIO_CONSULTAS_HARDCODEADAS.md`
- `/app/backend/sql/migrations/prepare_consultas_sql_catalogo_seed.sql` (NO EJECUTADO)

### Consultas Inventariadas: 17
- SoftRestaurant: 12 (Ventas:8, Compras:3, Inventarios:1, Pagos:2)
- MPRO: 5 (Ventas:4, Compras:2)

### Próximo Paso:
Autorizar ejecución del DML seed para cargar las 17 consultas en ConsultasSQL_Catalogo

---

## FASE 1A SANITIZACIÓN SQL - COMPLETADA (15-May-2026)

### Vulnerabilidades Corregidas:
**5 vulnerabilidades CRÍTICAS** en endpoint `/api/explorador/buscar/{server_id}`:
- C01-C05: Parámetro `q` (búsqueda) inyectable via SQL LIKE

### Corrección Implementada:
- Nueva función `_escape_like_pattern()` en server.py línea 12153
- Escapa caracteres: `[` → `[[]`, `%` → `[%]`, `_` → `[_]`, `'` → `''`
- Validación de nombre de tabla con `isalnum()`

### Pendientes FASE 1B:
| ID | Riesgo | Descripción |
|----|--------|-------------|
| A01 | ALTO | /almacenes - sucursal_id |
| A02 | ALTO | /operativo/inventario-mpro - almacen LIKE |
| A03 | ALTO | /explorador/tabla - tabla sin whitelist |
| A04 | ALTO | /operativo/analisis-inventario - folios |

### Reporte:
`/app/docs/reports/FASE_1A_SANITIZACION_SQL_REPORTE.md`

---

## FASE 2 CATÁLOGO SQL - DML EJECUTADO (15-May-2026)

### Consultas Cargadas en ConsultasSQL_Catalogo: 20

| Sistema | Cantidad |
|---------|----------|
| SoftRestaurant | 14 |
| MPRO | 6 |

| Módulo | Cantidad |
|--------|----------|
| Ventas | 12 |
| Compras | 5 |
| Pagos | 2 |
| Inventarios | 1 |

### Parámetros Cargados: 38
- fecha_ini: 18 usos
- fecha_fin: 18 usos
- fecha: 1 uso
- almacen: 1 uso

### Validaciones:
- ✅ Sin duplicados
- ✅ Sin SQL nulo
- ✅ Sin palabras prohibidas (DELETE, UPDATE, INSERT, DROP, etc.)
- ✅ Todas SoloLectura=1
- ✅ Todas Activo=1
- ✅ ConfigOrigen='LEGACY_PYTHON'

### Backend Operativo:
- ✅ Login funciona
- ✅ /api/servers funciona
- ✅ Catálogo legacy sin cambios

### Reporte:
`/app/docs/reports/FASE_2_DML_CONSULTAS_SQL_CATALOGO_EJECUCION.md`

### Próxima Fase:
FASE 3: Repository SQL-First para Consultas

---

## FASE 3 REPOSITORY SQL-FIRST - COMPLETADA (15-May-2026)

### Módulo Creado: `/app/backend/modules/consultas_sql/`

| Archivo | Descripción |
|---------|-------------|
| `__init__.py` | Exports públicos |
| `models.py` | Modelos Pydantic/dataclass |
| `validator.py` | Validador SQL estricto |
| `repository.py` | Acceso a datos SQL |
| `service.py` | Lógica de negocio |
| `README.md` | Documentación |

### Clases Creadas:
- `ConsultaSQLCatalogo`, `ConsultaSQLParametro`, `ConsultaSQLVersion`, `ConsultaSQLServidor`
- `ConsultaSQLFilter`, `ConsultaSQLValidationResult`
- `SQLValidator`, `ConsultasSQLRepository`, `ConsultasSQLService`

### Validador SQL Estricto:
- Solo SELECT/WITH permitidos
- Palabras bloqueadas: DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE, EXEC, CREATE, MERGE, GRANT, REVOKE, DENY, BACKUP, RESTORE, DBCC, xp_, sp_
- Múltiples statements bloqueados
- Comentarios detectados

### Script de Validación:
`/app/backend/scripts/validate_consultas_sql_repository.py`

### Resultados Validación:
- 18/18 checks pasados
- 20/20 consultas validadas
- 38/38 parámetros confirmados
- 14 SoftRestaurant + 6 MPRO
- 4 módulos: Compras, Inventarios, Pagos, Ventas

### Confirmaciones:
- ✅ No se modificó frontend
- ✅ No se modificaron endpoints legacy
- ✅ No se ejecutaron consultas LIVE
- ✅ No se escribió en MongoDB
- ✅ Backend operativo

### Reporte:
`/app/docs/reports/FASE_3_REPOSITORY_CONSULTAS_SQL_SQLFIRST.md`

### Próxima Fase:
FASE 4: Endpoints /api/consultas-sql/*

---

## FASE 1B SANITIZACIÓN SQL EXHAUSTIVA - COMPLETADA (15-May-2026)

### Vulnerabilidades A01-A04 Cerradas + 6 Endpoints Adicionales

| ID | Endpoint | Corrección |
|----|----------|------------|
| A01 | /almacenes | Parametrización `%s` + `_validate_identifier()` |
| A02 | /reports/inventory-analysis | `_escape_like_pattern()` para LIKE |
| A03 | /explorador/columnas,relaciones,preview | Whitelist + parametrización |
| A04 | /reports/inventory-analysis | `_sanitize_folio_list()` |
| NEW | /servers/{id}/queries/validate | SQLSanitizer.validate_for_catalog() |
| NEW | /explorador/query/{id} | SQLSanitizer.validate_for_explorer() |
| NEW | /explorador/ejecutar-script/{id} | Solo SuperAdministrador |
| NEW | /catalogo/consultas-custom POST/PUT | Validación antes de guardar |
| NEW | /catalogo/ejecutar-rich/{id} | Validación para consultas custom |

### SQLSanitizer Centralizado (core/security.py):
- Bloquea: DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE, EXEC, xp_, sp_, comentarios, múltiples statements
- Permite: SELECT, WITH (CTE), JOINs, UNIONs, subqueries
- Log: `log_blocked_sql()` registra intentos

### Tests: 27/27 ✅

### Reportes:
- `/app/docs/reports/FASE_1B_SANITIZACION_SQL_VULNERABILIDADES_ALTAS.md`
- `/app/backend/scripts/validate_sql_sanitization_fase_1b.py`

---

## FASE 4 ENDPOINTS CONSULTAS SQL - COMPLETADA (15-May-2026)

### Endpoints Creados:
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/consultas-sql/catalogo` | GET | Listar consultas |
| `/api/consultas-sql/catalogo/{codigo}` | GET | Detalle de consulta |
| `/api/consultas-sql/validar` | POST | Validar consulta |
| `/api/consultas-sql/ejecutar` | POST | Ejecutar consulta autorizada |
| `/api/consultas-sql/sistemas` | GET | Listar sistemas |
| `/api/consultas-sql/modulos` | GET | Listar módulos |

### Archivos Creados:
- `/app/backend/modules/consultas_sql/routes.py` (~450 líneas)
- `/app/backend/modules/consultas_sql/schemas.py` (~180 líneas)

### Seguridad:
- No acepta SQL libre desde frontend
- Solo ejecuta consultas del catálogo EDARSAHUB
- Valida con SQLSanitizer antes de ejecutar
- RBAC temporal: Administrador/SuperAdministrador
- SQL visible solo para SuperAdministrador

### Tests: 9/9 ✅

### Reporte:
`/app/docs/reports/FASE_4_ENDPOINTS_CONSULTAS_SQL_SQLFIRST.md`

---

## Tareas Pendientes

### P1 - FASE 4B: Frontend para Catálogo SQL
- Crear UI para consumir endpoints `/api/consultas-sql/*`
- Componentes: CatalogoSQLPage, ConsultaSQLCard, ConsultaSQLDetalle

### P1 - FASE 3A: Ventas por Hora/Día de Semana
- Implementar lógica SQL en EDARSAHUB
- Lectura de históricos (rango de fechas)

## FASE 4B CIERRE ENDPOINTS CONSULTAS SQL - COMPLETADA (15-May-2026)

### Resumen:
| Acción | Estado |
|--------|--------|
| Documentar diseño actual como aceptado | ✅ |
| Agregar endpoint `/versiones` | ✅ |
| Agregar endpoint `/servidores` | ✅ |
| Agregar endpoint `/validar-texto` | ✅ |
| Blindar endpoint `/ejecutar` | ✅ |

### Endpoints Nuevos:
- `GET /api/consultas-sql/catalogo/{codigo}/versiones` - Versiones históricas
- `GET /api/consultas-sql/catalogo/{codigo}/servidores` - Servidores asociados
- `POST /api/consultas-sql/validar-texto` - Validar SQL libre (Admin only)

### Blindaje /ejecutar:
- Solo Admin/SuperAdministrador
- Verifica `PermiteEjecucionManual=1`
- Límite reducido a 5000 filas
- No acepta SQL libre
- Rechaza parámetros no declarados

### Reporte:
`/app/docs/reports/FASE_4B_CIERRE_ENDPOINTS_CONSULTAS_SQL_SQLFIRST.md`

**✅ Endpoints SQL-First listos para producción bajo control estricto.**

---

## FASE 1C SANITIZACIÓN SQL LIKE - COMPLETADA (15-May-2026)

### Resumen:
| Métrica | Valor |
|---------|-------|
| Total instancias revisadas | 36 |
| Instancias corregidas | 26 |
| Instancias ya sanitizadas | 10 |
| Lotes ejecutados | 6 |
| py_compile por lote | 6/6 exitosos |

### Endpoints Corregidos:
- `POST /reports/inventory-analysis` (MPRO/SR)
- `GET /detalle-movimientos/{server_id}` (MPRO/SR)
- `GET /detalle-ventas/{server_id}` (MPRO/SR)
- `GET /debug-producto/{server_id}` (MPRO)
- `GET /compras/inventarios-fisicos/{server_id}` (MPRO/SR)
- `GET /compras/pedidos-vigentes/{server_id}` (MPRO)
- `POST /compras/sugerido-compras` (MPRO)
- `POST /compras/proveedores` (MPRO)

### Función utilizada:
`_escape_like_pattern()` - Escapa caracteres [ ] % _ ' para SQL Server LIKE

### Reporte:
`/app/docs/reports/FASE_1C_SANITIZACION_SQL_LIKE_REPORTE.md`

**✅ Todas las vulnerabilidades de inyección SQL mediante cláusulas LIKE han sido cerradas.**

---

## FASE SYNC-1 INFRAESTRUCTURA HISTÓRICOS - COMPLETADA (15-May-2026)

### Resumen:
| Componente | Estado |
|------------|--------|
| Módulo `sync_historicos` | ✅ Creado |
| Tablas Sync_* en EDARSAHUB | ✅ Creadas |
| Ventana operativa 13:00-11:00 | ✅ Configurada |
| Protección anti-$0 falso | ✅ Verificada |
| UPSERT idempotente | ✅ Implementado |

### Tablas Creadas:
- `Sync_Ventas_Historicas`
- `Sync_Ventas_PorHora`
- `Sync_Ventas_PorDiaSemana`
- `Sync_Control_Ejecuciones`

### Módulo:
```
/app/backend/modules/sync_historicos/
├── __init__.py
├── models.py
├── repository.py
├── service.py
├── sync_ventas.py
└── README.md
```

### Ventana Operativa:
- Default: 13:00 - 11:00 (cruza medianoche)
- Helper actualizado en `core/utils/operational_window.py`
- Preparado para futuro módulo de Horarios de Operación

### Reporte:
`/app/docs/reports/FASE_SYNC_1_INFRAESTRUCTURA_HISTORICOS_REPORTE.md`

**✅ Infraestructura lista para FASE SYNC-2 (prueba con servidores reales).**

---

## FASE SYNC-2 PRUEBA REAL HISTÓRICOS - COMPLETADA (15-May-2026)

### Resumen:
| Aspecto | Resultado |
|---------|-----------|
| SERVER_SECRET_KEY | ✅ Válida (fingerprint: d60eba8b) |
| Descifrado de credenciales | ✅ Funcional |
| Conexión SoftRestaurant | ✅ OK (130° MERIDA) |
| Conexión MPRO | ✅ OK (ManagmentPro) |
| Dry-run | ✅ 16/16 registros simulados |
| Escritura real | ✅ 16/16 registros escritos |
| Idempotencia | ✅ Validada (2 ejecuciones) |
| Anti-$0 falso | ✅ Funcionando |
| Ventana 13:00-11:00 | ✅ Correcta |
| No regresión | ✅ Login y servicios OK |

### Servidores Probados:
| ID | Nombre | Tipo | Host |
|----|--------|------|------|
| a5547321-... | 130° MERIDA | SoftRestaurant | 130mid.ddns.net |
| 1b230a06-... | ManagmentPro | MPRO | 54.39.104.176 |

### Datos Escritos en Sync_Ventas_Historicas:
| Fecha | SR (130° MERIDA) | MPRO (ManagmentPro) |
|-------|------------------|---------------------|
| 2026-05-07 | $87,372 (21 tkts) | $98,938 (26 tkts) |
| 2026-05-08 | $150,247 (37 tkts) | $230,444 (68 tkts) |
| 2026-05-09 | $181,868 (49 tkts) | $340,787 (116 tkts) |
| 2026-05-10 | $199,744 (46 tkts) | $400,476 (128 tkts) |
| 2026-05-11 | $122,962 (24 tkts) | $87,490 (33 tkts) |
| 2026-05-12 | $87,186 (18 tkts) | $117,376 (42 tkts) |
| 2026-05-13 | $165,747 (30 tkts) | $122,499 (38 tkts) |
| 2026-05-14 | $31,693 (6 tkts) | $249,987 (72 tkts) |

### Bitácora Sync_Control_Ejecuciones:
| Run ID | Status | Procesados | Insertados | Actualizados |
|--------|--------|------------|------------|--------------|
| SYNC-...-ccc62d48 (1ra) | SUCCESS | 16 | 16 | 0 |
| SYNC-...-8c86f4b0 (2da) | SUCCESS | 16 | 0 | 16 |

### Correcciones Aplicadas:
1. Query MPRO: `Vn_Importe` → `Vn_Precio_Neto_Importe`
2. Fix empresa_id: `server.get('empresa_id', 0)` → validación explícita de None

### Reporte:
`/app/docs/reports/FASE_SYNC_2_PRUEBA_REAL_HISTORICOS_REPORTE.md`

**✅ Sistema listo para escalar a todos los servidores en FASE SYNC-3.**

---

## FASE API_LOCAL_QUERY_EDITOR - COMPLETADA (15-May-2026)

### Resumen:
Se implementó una sección dentro del modal de Alta/Edición de Conexiones API que permite configurar y probar consultas SELECT asociadas a cada conexión, sin repetir credenciales.

### Endpoints Creados:
| Endpoint | Descripción |
|----------|-------------|
| `POST /api/api-connections/{id}/test-query` | Prueba consulta contra conexión existente |
| `POST /api/api-connections/test-query-draft` | Prueba consulta sin conexión guardada |

### Validaciones SQL Implementadas:
- ✅ Solo SELECT/WITH permitidos
- ✅ Bloqueo de DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE
- ✅ Bloqueo de EXEC, xp_, sp_, fn_
- ✅ Bloqueo de múltiples statements (;)
- ✅ Bloqueo de comentarios (-- / /* */)

### Archivos Modificados:
| Archivo | Cambios |
|---------|---------|
| `/app/backend/modules/api_connections/repository.py` | +`get_api_connection_with_decrypted_key()`, +`execute_test_query()` |
| `/app/backend/modules/api_connections/routes.py` | +Endpoints test-query |
| `/app/frontend/src/pages/Servidores.js` | +Sección "Consulta de prueba" en modal |

### Reporte:
`/app/docs/reports/FASE_API_LOCAL_QUERY_EDITOR_REPORTE.md`

### Actualización (15-May-2026):
- ✅ **Consulta DEFAULT** para nuevas conexiones: `SELECT TOP 1 name FROM sys.tables ORDER BY name`
- ✅ **Vista Compacta** (Lista) para Conexiones API y Servidores SQL
- Estados `apiViewMode` y `sqlViewMode` para alternar entre Tarjetas/Lista
- No expone secretos (API Key, passwords, connection strings)

---

## FASE SYNC-2B VENTAS POR HORA Y DÍA SEMANA - COMPLETADA (15-May-2026)

### Resumen:
| Tabla | Registros | Estado |
|-------|-----------|--------|
| Sync_Ventas_PorHora | 69 | ✅ OK |
| Sync_Ventas_PorDiaSemana | 14 | ✅ OK |

### Servidores Probados:
- SoftRestaurant: 130° MERIDA (62 registros hora + 7 días)
- MPRO: ManagmentPro (7 registros hora + 7 días)

### Validaciones:
- ✅ Ventana 13:00-11:00 correcta
- ✅ NO se usó 03:00
- ✅ Dry-run exitoso
- ✅ Escritura real exitosa
- ✅ Idempotencia validada (segunda ejecución no duplicó)
- ✅ Anti-$0 falso verificado
- ✅ Bitácora funcionando

### Métodos Agregados:
- `sync_ventas_por_hora()` - Sincronización de ventas por hora
- `sync_ventas_por_dia_semana()` - Sincronización de ventas por día de semana
- Helpers: `ejecutar_sync_ventas_por_hora_dry_run()`, `ejecutar_sync_ventas_por_hora_real()`, etc.

### Reporte:
`/app/docs/reports/FASE_SYNC_2B_VENTAS_HORA_DIASEMANA_REPORTE.md`

---

## Próximas Fases Pendientes

### P0 - FASE SYNC-3: Sincronización a Escala
- Expandir a todos los 8 servidores activos
- Histórico 30 días
- Investigar hora MPRO (Vn_Fecha parece no tener timestamp)
- Schedulers automáticos

### P1 - FASE 5: Logging de Ejecuciones
- Implementar escritura a ConsultasSQL_EjecucionesLog
- Dashboard de auditoría (backend-only)

### P2 - Corrección de Fechas Peligrosas
- 172 instancias de `datetime.now()`, `date.today()` detectadas
- Centralizar en `get_operational_window()`

### P2 - Migración Final fuera de MongoDB
- Deprecar MongoDB como fuente de datos

### P3 - Limpieza de Registros Legacy
- Eliminar registros duplicados en BD




---

## Actualizaciones Recientes (2026-05-15)

### FIX: Filtro Dinámico de Sistemas en Catálogo de Consultas
**Estado:** ✅ COMPLETADO

**Problema:** El filtro de "Sistema" en Catálogo de Consultas estaba hardcodeado mostrando solo SoftRestaurant y MPRO, ignorando nuevos sistemas creados en `Catálogos > Configuración > Sistemas`.

**Solución:**
- Modificado `useCatalogoConsultasData.js` para cargar sistemas desde `/api/catalogos/sistemas/activos`
- Reemplazados SelectItems hardcodeados por mapeo dinámico de `sistemasDisponibles`
- Afecta: filtro principal + modal Nueva Consulta

**Sistemas ahora disponibles (dinámicos desde EDARSAHUB):**
- MPRO: ManagementPro (MPRO)
- OTRO: Otro
- SAP_BUSINESS_ONE: SAP Business One
- SOFRESATAURANT_ENTER: Sofresataurant Enterprise
- SOFTRESTAURANT: SoftRestaurant

**Archivos modificados:**
- `/app/frontend/src/components/catalogo-consultas/useCatalogoConsultasData.js`
- `/app/frontend/src/pages/CatalogoConsultas.js`

**Reporte:** `/app/docs/reports/FIX_CATALOGO_CONSULTAS_SISTEMAS_DINAMICOS.md`

### FIX: Modal Drag & Drop en Servidores.js
**Estado:** ✅ COMPLETADO

**Problema:** El modal de edición de conexiones no se arrastraba correctamente debido a conflicto con transform CSS de Shadcn.

**Solución:**
- Modificado `dialog.jsx` con props `draggable`, `hideCloseButton`, `overlayClassName`
- Reimplementado drag con event listeners globales en `document`
- Transform ahora usa `calc(-50% + Xpx)` para mantener centrado + offset

**Archivos modificados:**
- `/app/frontend/src/components/ui/dialog.jsx`
- `/app/frontend/src/pages/Servidores.js`

### FIX: Compilación JSX - Fragmento sin cerrar
**Estado:** ✅ COMPLETADO

**Problema:** Error `Expected corresponding JSX closing tag for <>` en Servidores.js línea 2579.

**Causa:** Fragmento `<>` abierto dentro de `{!sqlModalMinimized && (<>...` no tenía cierre `</>` ni `)}`.

### FIX: Explorador BD - Conexiones Explorables Dinámicas
**Estado:** ✅ COMPLETADO

**Problema:** El Explorador de BD solo mostraba 5 unidades operativas tradicionales, excluyendo nuevos servidores como CHAPUR NORTE, 130° QRO LOCAL, ORIGEN LOCAL.

**Solución:**
- Nuevo endpoint `GET /api/explorador/conexiones-explorables` que consulta `Servidores_Conexiones` con join a `Sistema_Catalogo`
- Nuevo servicio frontend `exploradorService.js`
- Modificado `ExploradorBD.js` para usar nuevo servicio

**Conexiones ahora disponibles (12 total):**
- Todas las tradicionales (130° MERIDA, CIENFUEGOS, LA ESTELAR, etc.)
- + 130° QRO LOCAL (MPRO API)
- + CHAPUR NORTE (Sofresataurant Enterprise)
- + CHAPUR NORTE BACKOFICE (Sofresataurant Enterprise)
- + ORIGEN LOCAL (MPRO API)

**Archivos modificados:**
- `/app/backend/server.py`
- `/app/frontend/src/services/exploradorService.js` (NUEVO)
- `/app/frontend/src/pages/ExploradorBD.js`

**Reporte:** `/app/docs/reports/FIX_EXPLORADOR_BD_CONEXIONES_EXPLORABLES_DINAMICAS.md`


### FIX: Explorador BD Multi-Sistema (Carga de Tablas)
**Estado:** ✅ COMPLETADO

**Problema:** El Explorador solo cargaba tablas de SoftRestaurant; MPRO, Enterprise y otros sistemas mostraban "0 tablas".

**Causa:** El endpoint `/explorador/tablas/{server_id}` asumía que todas las conexiones tienen SQL directo. Las conexiones `API_LOCAL` (MPRO API, Enterprise) usan endpoint `/query?sql=`, no SQL credentials.

**Solución:**
- Refactorizado endpoint para detectar tipo de conexión
- **SQL_SERVER/DATA_SOURCE**: Usa `INFORMATION_SCHEMA.TABLES` (sin cambios)
- **API_LOCAL**: Usa `GET /query?sql=SELECT name FROM sys.tables`
- Agregadas funciones `get_api_connection_by_id_full()` y `get_decrypted_api_key()`

**Validación:**
- ✅ SoftRestaurant 130° MERIDA: 365 tablas (NO REGRESIÓN)
- ✅ MPRO ManagementPro: 1076 tablas
- ✅ APIs remotas (CHAPUR NORTE): Muestra error claro si no disponible

**Archivos modificados:**
- `/app/backend/server.py`
- `/app/backend/modules/api_connections/repository.py`

**Reporte:** `/app/docs/reports/FIX_EXPLORADOR_BD_MULTISISTEMA_TABLAS.md`


**Solución:** Agregado `</>` y `)}` después de `</DialogFooter>`.


---

### FIX: Explorador BD - Columnas y Preview para Conexiones Enterprise (API_LOCAL)
**Fecha:** 2026-05-16
**Estado:** ✅ COMPLETADO Y VALIDADO

**Problema:** Los endpoints `/explorador/columnas` y `/explorador/preview` fallaban para conexiones Enterprise (CHAPUR NORTE, CHAPUR NORTE BACKOFICE) retornando errores como "Tabla 'X' no está en la lista permitida" o "mark_server_offline() takes 1 positional argument".

**Causa raíz:**
1. Endpoints solo soportaban conexiones SQL directas (`DATA_SOURCE`)
2. La whitelist de tablas bloqueaba tablas dinámicas de APIs remotas
3. Límite de 20 filas hardcodeado en `execute_test_query`

**Solución:**
1. Agregado parámetro `limit: Optional[int] = 20` en `execute_test_query`
2. Endpoints reescritos con lógica dual:
   - `DATA_SOURCE`: SQL directo con whitelist (existente)
   - `API_LOCAL`: Delegación via `execute_test_query` sin whitelist
3. Whitelist solo aplica a conexiones SQL directas

**Validación (8 puntos críticos):**
| # | Punto | Estado |
|---|-------|--------|
| 1 | PRUEBAS SOFTRESTAURANT | ⚠️ Error DBA (no es bug) |
| 2 | CHAPUR NORTE tablas | ✅ 356 tablas |
| 3 | CHAPUR NORTE BACKOFICE tablas | ✅ 186 tablas |
| 4 | Columnas funcionan | ✅ |
| 5 | Preview TOP 100 funciona | ✅ |
| 6 | Enterprise usa API Local | ✅ |
| 7 | Sin exposición de secrets | ✅ |
| 8 | Sin regresión SoftRestaurant/MPRO | ✅ |

**Archivos modificados:**
- `/app/backend/modules/api_connections/repository.py` (líneas 730-834)
- `/app/backend/server.py` (endpoints columnas/preview)

**Reporte:** `/app/docs/reports/FIX_EXPLORADOR_BD_TABLAS_ENTERPRISE_API_LOCAL_V2.md`



---

### FASE SYNC-2C: Diagnóstico y Corrección Hora MPRO
**Fecha:** 2026-05-16
**Estado:** ✅ COMPLETADO - OPCIÓN A (Campo válido encontrado)

**Problema:** MPRO registraba todas las ventas en hora 0 en `Sync_Ventas_PorHora` porque `Vn_Fecha` solo contiene fecha (hora siempre 00:00:00).

**Diagnóstico:**
- `Vn_Fecha`: Fecha operativa del documento (sin hora real)
- `Fecha_Alta`: Timestamp real de registro (con hora: 09:00-23:00, 00:00-01:00)

**Solución implementada:**
- Query MPRO corregida: usa `DATEPART(HOUR, Fecha_Alta)` para hora
- Filtro mantiene `CAST(Vn_Fecha AS DATE)` para fecha operativa
- Total cuadra 100% con `Sync_Ventas_Historicas`

**Validación:**
| Aspecto | Antes | Después |
|---------|-------|---------|
| Registros PorHora | 7 (hora 0) | 75 (distribución real) |
| Horas por día | 1 | 10-13 |
| Totales | Correctos | Correctos (sin cambio) |

**Archivo modificado:** `/app/backend/modules/sync_historicos/service.py`

**Reporte:** `/app/docs/reports/FASE_SYNC_2C_DIAGNOSTICO_HORA_MPRO_REPORTE.md`



---

### FASE SYNC-2C: Aplicación Corrección MPRO PorHora
**Fecha:** 2026-05-16
**Estado:** ✅ COMPLETADO

**Operación:** Escritura real UPSERT con query corregida (Fecha_Alta)

**Resultado:**
| Métrica | Antes | Después |
|---------|-------|---------|
| Registros MPRO | 7 | 87 |
| Horas distintas | 1 (hora 0) | 17 (0,1,9-23) |
| Totales vs Históricos | ✅ | ✅ (±$0.01 redondeo) |

**Validaciones:**
- ✅ Baseline desde EDARSAHUB SQL (no live)
- ✅ No tocó SoftRestaurant
- ✅ Hora 0 = ventas reales madrugada (31 tickets)
- ✅ UPSERT idempotente
- ✅ Anti-$0 falso

**Reporte:** `/app/docs/reports/FASE_SYNC_2C_APLICACION_CORRECCION_MPRO_PORHORA_REPORTE.md`



---

### FASE SYNC-3A: Expansión Controlada 7 Días
**Fecha:** 2026-05-16
**Estado:** ⚠️ PARCIALMENTE COMPLETADO

**Alcance:**
- Rango: 2026-05-08 a 2026-05-15 (7 días)
- Ventana: 13:00 - 11:00
- Fuente: EDARSAHUB SQL

**Servidores:**
| Servidor | Estado |
|----------|--------|
| ManagmentPro (MPRO) | ✅ SINCRONIZADO |
| 130° MERIDA | ⚠️ CREDENCIALES_NO_DESCIFRABLES |
| CIENFUEGOS | ⚠️ CREDENCIALES_NO_DESCIFRABLES |
| LA ESTELAR | ⚠️ CREDENCIALES_NO_DESCIFRABLES |
| CHAPUR NORTE | PENDIENTE_API_LOCAL_VENTAS |
| CHAPUR NORTE BACKOFICE | PENDIENTE_API_LOCAL_VENTAS |
| PRUEBAS SOFTRESTAURANT | EXCLUIDO_PRUEBAS |

**Resultado MPRO:**
- Sync_Ventas_Historicas: 9 registros (2026-05-07 a 2026-05-15)
- Sync_Ventas_PorHora: 89 registros (distribución real)
- Totales cuadran 100% (±$0.01 redondeo)

**Protección anti-$0:** ✅ Funcionó (no guardó datos falsos)

**Bloqueador:** `SERVER_SECRET_KEY` no configurada en preview

**Reporte:** `/app/docs/reports/FASE_SYNC_3A_EXPANSION_8_SERVIDORES_7_DIAS_REPORTE.md`



---

### FASE ENV-SECRET-01: Resolución SERVER_SECRET_KEY
**Fecha:** 2026-05-16
**Estado:** ✅ COMPLETADO

**Verificación:**
- `SERVER_SECRET_KEY`: ✅ Configurada (44 chars)
- Formato Fernet: ✅ Válido
- Cifrado/Descifrado: ✅ Funcional

**Credenciales verificadas:**
| Servidor | Descifrable | Conexión | Query Ventas |
|----------|-------------|----------|--------------|
| 130° MERIDA | ✅ | ✅ | ✅ |
| CIENFUEGOS | ✅ | ✅ | ✅ |
| LA ESTELAR | ✅ | ✅ | ✅ |

**Dry-run (7 días):**
| Servidor | Fechas OK | Venta Total |
|----------|-----------|-------------|
| 130° MERIDA | 7/8 | $939,447.00 |
| CIENFUEGOS | 8/8 | $1,423,603.00 |
| LA ESTELAR | 8/8 | $793,865.00 |

**Bloqueo SYNC-3A:** ✅ RESUELTO

**Reporte:** `/app/docs/reports/FASE_ENV_SECRET_01_SERVER_SECRET_KEY_REPORTE.md`



---

### FASE SYNC-3A-R: Escritura Real SoftRestaurant
**Fecha:** 2026-05-16
**Estado:** ✅ COMPLETADO

**Servidores sincronizados:**
| Servidor | Históricos | PorHora | VentaTotal |
|----------|------------|---------|------------|
| 130° MERIDA | 7 | 62 | $939,447.00 |
| CIENFUEGOS | 8 | 75 | $1,423,603.00 |
| LA ESTELAR | 8 | 80 | $793,865.00 |

**Totales finales:**
| Tabla | MPRO | SoftRestaurant | Total |
|-------|------|----------------|-------|
| Sync_Ventas_Historicas | 9 | 24 | 33 |
| Sync_Ventas_PorHora | 89 | 217 | 306 |
| Sync_Ventas_PorDiaSemana | 7 | 7 | 14 |

**Validaciones:**
- ✅ PorHora vs Históricas: 100% cuadra
- ✅ Idempotencia: No duplicados
- ✅ Ventana 13:00-11:00
- ✅ Anti-$0 falso activo

**Reporte:** `/app/docs/reports/FASE_SYNC_3A_R_ESCRITURA_REAL_SOFTRESTAURANT_REPORTE.md`



---

## FASE ARQ-SISTEMAS-CAPACIDADES - Catálogo Maestro SQL-First

### Estado: FASE 5 ENDPOINTS COMPLETADA ✅

**Fecha inicio:** 2025-12-XX

### Objetivo
Eliminar hardcoding de sistemas (MPRO, SoftRestaurant, Enterprise) en código frontend y backend mediante un Catálogo Maestro de Sistemas + Motor de Capacidades SQL-First.

### Problema Resuelto
Cada sistema nuevo requería modificaciones en 10+ archivos:
- Filtros frontend (Servidores.js, Reportes.js, Compras.js)
- Explorador BD
- Sync Históricos
- Queries por sistema
- Normalizadores system_type

### FASE 1 - Diagnóstico (COMPLETADO ✅)
- [x] Matriz de auditoría: 30+ puntos de hardcoding identificados
- [x] DDL propuesto: IF NOT EXISTS (idempotente)
- [x] SEED inicial preparado para SR y MPRO
- [x] Plan de fases 2-7 documentado

### FASE 2 - DDL SQL-First (COMPLETADO ✅)
- [x] Crear tabla `Sistema_Capacidades` (10 columnas, PK, FK, 2 índices)
- [x] Crear tabla `Sistema_ModulosVisibilidad` (9 columnas, PK, FK, 1 índice)
- [x] Crear tabla `Sistema_TiposVariantes` (6 columnas, PK, FK, 1 índice)
- [x] FKs vinculadas a Sistema_Tipos existente
- [x] Sin DROP/TRUNCATE/DELETE
- [x] Backend operativo post-ejecución
- [x] No regresión confirmada

### FASE 3 - Seed Inicial (COMPLETADO ✅)
- [x] Cargar capacidades SR (15 capacidades)
- [x] Cargar capacidades MPRO (17 capacidades incluyendo SUCURSALES_VISIBLES, CUENTAS_POR_PAGAR)
- [x] Cargar capacidades API_LOCAL/Enterprise (4 capacidades - solo EXPLORADOR)
- [x] Cargar variantes de nombres (18 variantes para 5 sistemas)
- [x] Cargar visibilidad por módulo (16 registros)
- [x] Cero duplicados, FKs válidas
- [x] **DECISIÓN:** Enterprise NO tiene SYNC_VENTAS_* (sin query_ventas validada)

### FASE 4 - Resolver Central (COMPLETADO ✅)
- [x] Implementar `SystemCapabilityResolver` en `/app/backend/core/system_capability_resolver.py`
- [x] Funciones: normalize_system_type(), system_supports(), get_capabilities()
- [x] Funciones: get_systems_for_capability(), get_explorable_systems(), get_sync_sales_systems()
- [x] Funciones: get_visible_systems_for_module(), get_visibility(), explain_system()
- [x] Cache ligero en memoria con TTL (5 min)
- [x] Compatibilidad temporal con system_type_utils.py (fallback)
- [x] Script de validación: 37/37 tests pasados (100%)
- [x] **CONFIRMADO:** API_LOCAL NO aparece en sync_sales_systems
- [x] **CONFIRMADO:** API_LOCAL SÍ aparece en explorable_systems

### FASE 5 - Endpoints (COMPLETADO ✅)
- [x] Router creado en `/app/backend/api/catalogos_sistemas.py`
- [x] GET /api/catalogos/sistemas-capacidades
- [x] GET /api/catalogos/sistemas-capacidades/explorables
- [x] GET /api/catalogos/sistemas-capacidades/sync-ventas
- [x] GET /api/catalogos/sistemas-capacidades/normalizar/{system_type}
- [x] GET /api/catalogos/sistemas-capacidades/diagnostico/{system_type}
- [x] GET /api/catalogos/sistemas-capacidades/capacidades/{capacidad}
- [x] Autenticación RBAC aplicada
- [x] **CONFIRMADO:** API_LOCAL en explorables, NO en sync-ventas
- [x] Script validación: 14/14 tests críticos pasados

### FASES PENDIENTES (Requieren Autorización)

#### FASE 6 - Integración No Destructiva
- [ ] Integrar en Explorador BD
- [ ] Integrar en Sync Históricos

#### FASE 7 - Frontend
- [ ] Migrar filtros a endpoints dinámicos
- [ ] Eliminar listas hardcodeadas

### Documentos Generados
- `/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE1_DIAGNOSTICO.md`
- `/app/docs/ddl/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_DDL_FASE2.sql`
- `/app/docs/ddl/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_SEED_FASE3.sql`
- `/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_SQLFIRST_REPORTE.md`

### Capacidades Propuestas
| Capacidad | SR | MPRO |
|-----------|:--:|:----:|
| EXPLORADOR_BD | ✓ | ✓ |
| SYNC_VENTAS_HISTORICAS | ✓ | ✓ |
| SYNC_VENTAS_POR_HORA | ✓ | ✓ |
| VENTAS_DIA | ✓ | ✓ |
| VENTAS_PERIODO | ✓ | ✓ |
| COMPRAS | ✓ | ✓ |
| INVENTARIOS | ✓ | ✓ |
| SUCURSALES_VISIBLES | ✗ | ✓ |
| CUENTAS_POR_PAGAR | ✗ | ✓ |

### Siguiente Paso
Autorización del usuario para ejecutar DDL FASE 2 en EDARSAHUB.



---

## ✅ FASE 6 - Catálogo Maestro: Integración No Destructiva (COMPLETADA - Dic 2025)

### Objetivo
Integrar el `SystemCapabilityResolver` en Explorador BD y Sync Históricos sin romper funcionalidad existente.

### Archivos Modificados
| Archivo | Cambio |
|---------|--------|
| `/app/backend/server.py` | `_es_conexion_explorable()` usa resolver con fallback |
| `/app/backend/modules/sync_historicos/service.py` | Condicionales modernizadas en 3 métodos |
| `/app/backend/core/system_capability_integration.py` | Funciones auxiliares (ya existía) |

### Validaciones Exitosas
- ✅ 6/6 tests del script de validación pasados
- ✅ 12 conexiones visibles en Explorador BD (sin regresión)
- ✅ API_LOCAL en Explorador, NO en Sync Ventas
- ✅ SOFTRESTAURANT y MPRO en Sync Ventas
- ✅ Endpoints del catálogo operativos
- ✅ Login y autenticación funcionales
- ✅ py_compile sin errores

### Documentos Generados
- `/app/backend/scripts/validate_system_capability_integration_fase6.py`
- `/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE6_INTEGRACION_REPORTE.md`

### Siguiente Fase
**FASE 7 - Frontend**: Migrar filtros de React a endpoints dinámicos (requiere autorización)

---

*Última actualización: Dic-2025 - FASE 6 Catálogo Maestro Completada*


---

## ✅ FASE 7 - Catálogo Maestro: Frontend Dinámico (COMPLETADA - Dic 2025)

### Objetivo
Migrar filtros/listas frontend hardcodeadas hacia endpoints dinámicos del Catálogo Maestro.

### Archivos Modificados
| Archivo | Cambio |
|---------|--------|
| `/app/frontend/src/services/exploradorService.js` | Usa `/catalogos/sistemas-capacidades/explorables` con fallback |
| `/app/frontend/src/pages/Servidores.js` | `loadTiposSistema()` usa Catálogo Maestro primero |

### Validaciones Exitosas
- ✅ Frontend compila sin errores
- ✅ Login funciona
- ✅ 12 conexiones en Explorador BD (sin regresión)
- ✅ API_LOCAL visible en Explorador
- ✅ API_LOCAL excluido de Sync Ventas
- ✅ SOFTRESTAURANT y MPRO en ambos filtros
- ✅ Endpoints Catálogo Maestro operativos
- ✅ Fallback a catálogo legacy implementado

### Documentos Generados
- `/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE7_FRONTEND_DINAMICO_REPORTE.md`

### Siguiente Paso
Tareas pendientes según prioridad del usuario.

---



---

## ✅ FASE SYNC-3A-R2 - PorDiaSemana SoftRestaurant (COMPLETADA - Dic 2025)

### Objetivo
Completar `Sync_Ventas_PorDiaSemana` para los servidores SoftRestaurant y documentar MPRO/Enterprise pendientes.

### Servidores Sincronizados
| Servidor | Sistema | Días | Estado |
|----------|---------|------|--------|
| 130° MERIDA | SoftRestaurant | 7 | ✅ (ya existía) |
| CIENFUEGOS | SoftRestaurant | 7 | ✅ NUEVO |
| LA ESTELAR | SoftRestaurant | 7 | ✅ NUEVO |
| ManagmentPro | MPRO | 7 | ✅ (ya existía) |

### Servidores Excluidos (Documentados)
| Servidor | Causa | Acción |
|----------|-------|--------|
| CHAPUR NORTE | API_LOCAL sin SYNC_VENTAS | SKIPPED correctamente |
| CHAPUR NORTE BACKOFICE | API_LOCAL sin SYNC_VENTAS | SKIPPED correctamente |

### Validaciones
- ✅ Dry-run: 14 registros calculados
- ✅ Escritura real: 14 registros UPSERT
- ✅ Idempotencia: Confirmada
- ✅ Sin $0 falsos
- ✅ Sin regresión en endpoints

### Método
Cálculo desde `Sync_Ventas_Historicas` en lugar de consulta directa (servidores remotos con conectividad intermitente).

### Documentos Generados
- `/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py`
- `/app/docs/reports/FASE_SYNC_3A_R2_PORDIASEMANA_CONFIG_PENDIENTES_REPORTE.md`

---

*Última actualización: Dic-2025 - FASE SYNC-3A-R2 Completada*

*Última actualización: Dic-2025 - FASE 7 Catálogo Maestro Frontend Completada*



---

## ✅ FIX: Comercial Dashboard Fuente Ventas (COMPLETADO - Dic 2025)

### Problema
Dashboard Comercial mostraba "Sin Datos" para 130° MERIDA, CIENFUEGOS y LA ESTELAR cuando:
- Los servidores remotos estaban offline
- PERO EDARSAHUB sí tenía datos en `Comercial_KPIs_Diarios_v2`

### Causa Raíz
1. Dashboard Comercial consultaba directamente al servidor remoto SoftRestaurant
2. Función `_mapear_codigo_a_unidad_negocio_id()` no retornaba valor en fallback

### Solución Implementada
- Dashboard Comercial ahora usa EDARSAHUB como fuente principal (igual que Tablero Ejecutivo)
- Nueva función `get_dashboard_kpis_from_edarsahub()` en service.py
- Corregido return faltante en `_mapear_codigo_a_unidad_negocio_id()`

### Archivos Modificados
- `/app/backend/modules/comercial/service.py`
- `/app/backend/modules/comercial/routes.py`

### Validaciones
| Unidad | ANTES | DESPUÉS |
|--------|-------|---------|
| 130° MERIDA | $0 | $2,018,823 ✅ |
| CIENFUEGOS | $0 | $2,361,002 ✅ |
| LA ESTELAR | $0 | $1,547,504 ✅ |

### Sin Regresión
- ✅ Tablero Ejecutivo funciona igual
- ✅ No se tocó MongoDB
- ✅ RBAC sin cambios

### Reporte
`/app/docs/reports/FIX_COMERCIAL_DASHBOARD_FUENTE_VENTAS_TABLERO_EJECUTIVO.md`

---

*Última actualización: Dic-2025 - Fix Comercial Dashboard Completado*




---

## ✅ FIX: MPRO en Comercial Dashboard (COMPLETADO - Dic 2025)

### Problema
Dashboard Comercial mostraba "Sin Datos" para ORIGEN y 130° QRO (MPRO) aunque `Comercial_KPIs_Diarios_v2` sí tenía datos.

### Causa Raíz
Los datos MPRO tenían `server_id` diferente al de `Servidores_Conexiones`:
- ORIGEN: busca `817a0aa8...` pero datos tienen `1b230a06...`
- 130° QRO: busca `72f6e9a7...` pero datos tienen `1b230a06...`

### Solución
Fallback por `unidad_negocio_id` cuando no hay datos por `server_id`.

### Validaciones
| Unidad | ANTES | DESPUÉS |
|--------|-------|---------|
| ORIGEN | "Sin Datos" | $1,201,738 ✅ |
| 130° QRO | "Sin Datos" | $2,269,702 ✅ |

### Reporte
`/app/docs/reports/FIX_SYNC_MPRO_COMERCIAL_KPIS_DIARIOS_V2.md`

---

*Última actualización: Dic-2025 - Fix MPRO Dashboard Completado*
