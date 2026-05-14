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

---

## Fases Pendientes (P0)

### FASE 2-B - Poblar Tablas SQL desde MongoDB
- [ ] Poblar PublicUUID y MongoLegacyID para 9 usuarios existentes
- [ ] Insertar 5 usuarios productivos faltantes
- [ ] Poblar Usuario_RolesAsignacion
- [ ] Poblar Usuario_EmpresasAsignacion
- [ ] Validar conteos y hashes

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
| Usuario_Catalogo | 9 | +2 columnas nuevas |
| Usuario_Roles | 9 | +4 roles nuevos |
| Usuario_RolesAsignacion | 0 | Vacía (poblar en 2-B) |
| Usuario_EmpresasAsignacion | 0 | Vacía (poblar en 2-B) |

### Usuarios MongoDB vs SQL
- MongoDB: 17 (14 activos, 3 inactivos)
- SQL: 9 migrados
- Pendientes: 5 productivos + decisión sobre 3 test

### Decisiones Documentadas
- superadmin@test.com: Excluir (sin UUID)
- 3 usuarios test inactivos: Excluir

---

## Documentos de Referencia
- `/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md`
- `/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md`
- `/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md`
- `/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md`

---

*Última actualización: 14-Dic-2025 - FASE 2-A.2 Completada*
