# EDARSA HUB - Product Requirements Document

## Visión General
Sistema ERP operativo centralizado para EDARSA, actuando como "el cerebro" de operaciones de compras, inventarios, auditorías y flujos de aprobación.

## Estado Actual: FASE 3.1 - Migración RBAC por Módulo (EN PROGRESO)

### COMPLETADO - Fase 3.1: Módulo Finanzas Migrado a RBAC
**Fecha**: 2026-04-19

#### Archivos Modificados:
- `/app/backend/modules/finanzas/tesoreria.py` - RBAC + filtrado por códigos de empresa
- `/app/backend/modules/finanzas/cuentas_por_pagar.py` - RBAC + filtrado por códigos de empresa
- `/app/backend/modules/finanzas/ingresos.py` - RBAC + filtrado por códigos de empresa
- `/app/backend/modules/finanzas/propinas_tpv/routes.py` - RBAC + filtrado por códigos de empresa

#### Validaciones Realizadas:
- ✅ Endpoints sin token devuelven 403 "Not authenticated"
- ✅ Admin ve TODOS los cortes Z (4 en demo)
- ✅ Usuario restringido (almacen@cienfuegos.mx) ve SOLO cortes de CIENFUEGOS (2 de 4)
- ✅ Usuario restringido NO ve Finanzas en el menú (RBAC frontend funciona)
- ✅ Frontend Finanzas carga correctamente para admin

#### Endpoints Finanzas - Estado REAL vs MOCK:
| Endpoint | Estado | Notas |
|----------|--------|-------|
| `/api/finanzas/tesoreria/cortes-z` | DEMO/SQL | Fallback a demo si SQL no conecta |
| `/api/finanzas/tesoreria/cuadres/*` | REAL | MongoDB edarsa_hub.cuadres_z |
| `/api/finanzas/cuentas-por-pagar/*` | DEMO/SQL | Fallback a demo |
| `/api/finanzas/ingresos/*` | DEMO/SQL | Fallback a demo |
| `/api/finanzas/propinas/*` | REAL | MongoDB edarsa_hub.propinas_tpv |

### COMPLETADO - Fase 3.1: Módulo Operaciones Migrado a RBAC
**Fecha**: 2026-04-19

(Ver detalles en historial)

### Módulos YA Migrados a RBAC (Fase 3/3.1):
- [x] Tablero Ejecutivo
- [x] Compras
- [x] Comercial
- [x] Operaciones (2026-04-19)
- [x] **Finanzas** (NUEVO - 2026-04-19)

### Módulos Pendientes de Migrar (P1):
- [ ] Recursos Humanos

### Backlog P2:
- Deprecación de campos legacy (`role`, `allowed_servers`, `allowed_sucursales`)
- Migración completa del Frontend al selector de contextos RBAC

---
*Última actualización: 19/04/2026 - Finanzas migrado a RBAC*
