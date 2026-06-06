# EDARSA HUB - CRM COMERCIAL ENTERPRISE
## Product Requirements Document

### Original Problem Statement
Construir el CRM COMERCIAL ENTERPRISE y módulos satélite integrados al ecosistema EDARSA HUB.

### Core Requirements
- **ESTRICTA PROHIBICIÓN**: Uso del subagente `testing_agent_v3_fork` totalmente prohibido
- **MÁXIMA ARQUITECTÓNICA (NO-LIVE)**: EDARSAHUB SQL es la ÚNICA fuente de verdad productiva
- **MÁXIMA DE ORO**: NO DUPLICAR tablas, conexiones, filtros, flujos, usuarios, ni unidades de negocio

### User's Preferred Language
Spanish (Español)

---

## Architecture

### SQL-FIRST Architecture
- `core/sql_first/connection_factory.py` - Hub central para todas las conexiones SQL
- `core/sql_first/db.py` - Funciones base de conexión EDARSAHUB
- `core/db.py` - Wrapper de compatibilidad legacy (sin conexiones directas)
- `core/rbac_sql/service.py` - Servicio RBAC usando tablas canónicas

### Canonical SQL Tables
| Tabla | Propósito |
|-------|-----------|
| `Sys_Usuarios` | Fuente única de usuarios |
| `Usuario_Roles` | Catálogo de roles |
| `Usuario_RolesAsignacion` | Asignación usuario-rol |
| `Usuario_EmpresasAsignacion` | Asignación usuario-empresa |
| `Usuario_SucursalesAsignacion` | Asignación usuario-sucursal |
| `Usuario_ServidoresAsignacion` | Asignación usuario-servidor |
| `Sistema_DeudaTecnica_TablasDuplicadas` | Registro de tablas obsoletas |

### Technical Debt (Tracked)
- `RBAC_Roles` - 6 rows (datos de transición)
- `RBAC_Permisos` - 9 rows (datos de transición)

---

## Implementation Status

### Phase P4 - SQL-FIRST Migration ✅ COMPLETE
- [x] P4-02: Centralización conexiones SQL
- [x] P4-03: Ajuste schema canónico
- [x] P4-04/05/06/07: Config segura y RBAC SQL
- [x] P4-09/09B: Aplicación Máxima de Oro, roles canónicos
- [x] P4-10/11/12: Validación contexto e integridad
- [x] P4-13: Backup colecciones Mongo candidatas
- [x] P4-14: Corrección huérfanos/duplicados (0 encontrados)
- [x] P4-15: Validación Mongo vs SQL (9 candidatas, 7 pendientes)
- [x] P4-16: Eliminación tablas RBAC_* vacías (6 eliminadas)
- [x] P4-17/17B: Dictamen Final APROBADO, core/db.py refactorizado

### Phase P5 - MongoDB Sunset (PENDING)
- [ ] Migrar 7 colecciones Mongo pendientes a SQL
- [ ] Eliminar colecciones Mongo candidatas respaldadas
- [ ] Resolver RBAC_Roles/RBAC_Permisos
- [ ] Desconectar PyMongo

---

## Testing Protocol
- **Permitido**: bash, cURL, python -c, screenshots
- **PROHIBIDO**: testing_agent_v3_fork

---

## Key Files Reference
- `/app/backend/core/sql_first/db.py`
- `/app/backend/core/sql_first/connection_factory.py`
- `/app/backend/core/db.py` (wrapper legacy)
- `/app/backend/core/rbac_sql/service.py`
- `/app/backend/core/config/edarsahub_config.py`
- `/app/backend/auditorias_p4/` (logs y backups)

---

## Environment Variables
```
EDARSAHUB_SQL_HOST=54.39.104.176
EDARSAHUB_SQL_PORT=1433
EDARSAHUB_SQL_DATABASE=EDARSAHUB
EDARSAHUB_SQL_USER=HRLectura
EDARSAHUB_SQL_PASSWORD=******
```

---

*Last Updated: 2026-06-06*
*Phase: P4 Complete, P5 Pending*
