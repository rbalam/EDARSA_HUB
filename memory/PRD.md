# EDARSA HUB - Product Requirements Document

## Visión General
Sistema ERP operativo centralizado para EDARSA, actuando como "el cerebro" de operaciones de compras, inventarios, auditorías y flujos de aprobación.

## Estado Actual: FASE 3.1 - Migración RBAC por Módulo (COMPLETADA)

### CAMBIO QUIRÚRGICO: Ventas Históricas vs Ventas del Día
**Fecha**: 2026-04-19

**Archivos modificados:**
- `/app/backend/modules/comercial/service.py`

**Comportamiento actual:**
| Tipo de Consulta | Fuente de Datos | Estado |
|------------------|-----------------|--------|
| Ventas históricas / acumulados / comparativos / KPIs | SQL nube (menú Servidores) | ✅ Funcionando |
| Ventas del día MPRO | API local (`APIS_MPRO_LOCALES`) | ✅ Funcionando |
| Ventas del día SoftRestaurant | API local (NO configurada) | ⚠️ Retorna null |

**PENDIENTE - Inspección Local:**
> Inspección local en servidores para revisar por qué no levanta SQL local o por qué no responde la API local de SoftRestaurant.

---

### COMPLETADO - Fase 3.1: Módulo RH Migrado a RBAC
**Fecha**: 2026-04-19

(Ver detalles anteriores)

### COMPLETADO - Fase 3.1: Módulo Finanzas Migrado a RBAC
**Fecha**: 2026-04-19

(Ver detalles anteriores)

### COMPLETADO - Fase 3.1: Módulo Operaciones Migrado a RBAC
**Fecha**: 2026-04-19

(Ver detalles anteriores)

### Módulos YA Migrados a RBAC (Fase 3/3.1):
- [x] Tablero Ejecutivo
- [x] Compras
- [x] Comercial
- [x] Operaciones (2026-04-19)
- [x] Finanzas (2026-04-19)
- [x] Recursos Humanos (2026-04-19)

### Backlog P0 - PENDIENTES ESTRUCTURALES:
1. **RH mapeo empresa→sucursal_id**: Falta mapeo para filtrado granular en SQL Server RH
2. **SoftRestaurant API local**: No existe API local, ventas del día no disponibles
3. **Inspección servidores locales**: Revisar por qué no levanta SQL local / API local

### Backlog P1:
- Conectar SQL Server real en Finanzas (actualmente usa fallback demo)

### Backlog P2:
- Deprecación de campos legacy (`role`, `allowed_servers`, `allowed_sucursales`)
- Migración completa del Frontend al selector de contextos RBAC

---
*Última actualización: 19/04/2026 - Cambio quirúrgico ventas históricas vs ventas del día*
