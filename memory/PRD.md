# EDARSA HUB - Product Requirements Document

## Visión General
Sistema ERP operativo centralizado para EDARSA, actuando como "el cerebro" de operaciones de compras, inventarios, auditorías y flujos de aprobación.

## Estado Actual: FASE 3.1 - Migración RBAC por Módulo (COMPLETADA)

### COMPLETADO - Fase 3.1: Módulo RH Migrado a RBAC
**Fecha**: 2026-04-19

#### Archivos Modificados:
- `/app/backend/modules/rh/routes.py` - RBAC + helper `get_user_sucursales_permitidas_rh()`
- `/app/backend/modules/rh/importador/routes.py` - Documentación RBAC actualizada

#### Validaciones Realizadas:
- ✅ Endpoints sin token devuelven 403 "Not authenticated"
- ✅ Admin accede a dashboard y colaboradores (510 total)
- ✅ Usuario restringido NO ve RH en el menú (RBAC frontend funciona)

#### Endpoints RH - Estado REAL vs MOCK:
| Endpoint | Estado | Notas |
|----------|--------|-------|
| `/api/rrhh/colaboradores` | REAL | SQL Server HR2020 |
| `/api/rrhh/dashboard` | REAL | SQL Server HR2020 |
| `/api/rrhh/incidencias` | REAL | SQL Server HR2020 |
| `/api/rrhh/nominas/flujo` | REAL | SQL Server HR2020 |
| `/api/rrhh/asistencia` | REAL | SQL Server HR2020 |
| `/api/rrhh/reclutamiento/*` | REAL | SQL Server HR2020 |
| `/api/rrhh/catalogos/*` | REAL | SQL Server HR2020 |

**NOTA:** El filtrado por sucursales en RH requiere mapeo empresa→sucursal_id de SQL Server que aún no está implementado. La autenticación está activa pero el filtrado granular por empresa está pendiente de este mapeo.

### COMPLETADO - Fase 3.1: Módulo Finanzas Migrado a RBAC
**Fecha**: 2026-04-19

(Ver detalles en historial)

### COMPLETADO - Fase 3.1: Módulo Operaciones Migrado a RBAC
**Fecha**: 2026-04-19

(Ver detalles en historial)

### Módulos YA Migrados a RBAC (Fase 3/3.1):
- [x] Tablero Ejecutivo
- [x] Compras
- [x] Comercial
- [x] Operaciones (2026-04-19)
- [x] Finanzas (2026-04-19)
- [x] **Recursos Humanos** (NUEVO - 2026-04-19)

### Backlog P1:
- Implementar mapeo empresa→sucursal_id para filtrado granular en RH
- Conectar SQL Server real en Finanzas (actualmente usa fallback demo)

### Backlog P2:
- Deprecación de campos legacy (`role`, `allowed_servers`, `allowed_sucursales`)
- Migración completa del Frontend al selector de contextos RBAC

---
*Última actualización: 19/04/2026 - FASE 3.1 COMPLETADA (todos los módulos migrados a RBAC)*
