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
- [x] Usuario_EmpresasAsignacion sigue vacía
- [x] Reporte: `/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md`

### FASE 2-B2.1 - Mapeo Empresas MongoDB → SQL (Completada - 14-Dic-2025)
- [x] Tabla `Sistema_EmpresasMongoMap` creada
- [x] 5 mapeos creados por código exacto (ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID)
- [x] Sin ambigüedades ni conflictos
- [x] Usuario_EmpresasAsignacion sigue vacía
- [x] Reporte: `/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md`

### FASE 2-B3 - Poblado Usuario_EmpresasAsignacion (Completada - 14-Dic-2025)
- [x] 27 asignaciones insertadas para 7 usuarios con empresas_permitidas
- [x] 5 usuarios con 5 empresas cada uno (acceso global)
- [x] 2 usuarios con 1 empresa (CIENFUEGOS - acceso limitado)
- [x] 7 usuarios con empresa principal correcta
- [x] 4 usuarios omitidos (sin empresas_permitidas) - pendientes de decisión
- [x] Reporte: `/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md`

---

## ✅ FASE 2 COMPLETADA: Migración Base Auth/RBAC

| Tabla SQL | Registros | Estado |
|-----------|-----------|--------|
| Usuario_Catalogo | 11 | ✓ Completo |
| Usuario_Roles | 9 | ✓ Completo |
| Usuario_RolesAsignacion | 11 | ✓ Completo |
| Usuario_EmpresasAsignacion | 27 | ✓ Completo |
| Sistema_EmpresasMongoMap | 5 | ✓ Completo |
| Usuario_MigracionMongoTrace | 11 | ✓ Completo |

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

---

## Fases Pendientes (P0)

### FASE 2-D - Auth Repository SQL Paralelo
- [ ] Crear user_repository_sql.py
- [ ] Implementar funciones equivalentes a MongoDB
- [ ] Implementar regla SUPERADMIN (acceso global implícito)
- [ ] Usar PublicUUID como user['id'] en respuestas

### FASE 2-C - Validación Post-Migración
- [ ] Validar conteos MongoDB vs SQL
- [ ] Verificar hashes bcrypt
- [ ] Confirmar SuperAdministrador preservado

### FASE 2-D - Auth Repository SQL
- [ ] Crear user_repository_sql.py
- [ ] Implementar funciones equivalentes a MongoDB

### FASE 2-E - SQL-First con Fallback
- [ ] Modificar get_current_user() a SQL-first
- [ ] Mantener fallback a MongoDB

### FASE 2-F/G - Apagar MongoDB Auth
- [ ] Período de observación
- [ ] Eliminar fallback MongoDB

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

### Tablas SQL Auth/RBAC
| Tabla | Registros | Estado |
|-------|-----------|--------|
| Usuario_Catalogo | 11 | ✓ Completo con UUID y MongoID |
| Usuario_Roles | 9 | ✓ Completo con roles canónicos |
| Usuario_RolesAsignacion | 11 | ✓ Completo (4 ADMIN, 2 SUPERADMIN, 2 SUPERVISOR, 3 USUARIO) |
| Usuario_EmpresasAsignacion | 27 | ✓ Completo (7 usuarios con empresas) |
| Usuario_MigracionMongoTrace | 11 | ✓ Trazabilidad completa |
| Sistema_EmpresasMongoMap | 5 | ✓ Mapeo MongoDB→SQL completo |

### Usuarios pendientes de decisión (sin empresas_permitidas)
- ricardo@edarsa.com.mx (SUPERADMIN)
- david.ricardez@cienfuegos.mx (USUARIO)
- carlos@alpuntoycoma.mx (ADMIN)
- eduardo@alpuntoycoma.mx (ADMIN)

### Usuarios MongoDB vs SQL
- MongoDB: 17 (14 activos, 3 inactivos)
- SQL: 11 migrados (9 originales + 2 nuevos)
- Pendientes: 0 productivos (solo usuarios test)

### Decisiones Documentadas
- superadmin@test.com: Excluido (sin UUID en MongoDB)
- 3 usuarios @test.com activos: Excluidos (requieren decisión explícita)
- 3 usuarios inactivos: Excluidos (test/deshabilitados)

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
- `/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md`

---

*Última actualización: 14-Dic-2025 - FASE 2-C Completada (Migración Base Validada)*
