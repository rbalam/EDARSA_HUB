
---

## SQLFIRST-LEGACY-001

**Fecha:** 2026-06-04
**Estado:** PENDIENTE
**Prioridad:** MEDIA

### Descripción

Se estandarizaron los nombres de tablas sync mediante vistas de compatibilidad:

| Vista Nueva | Tabla Legacy |
|-------------|--------------|
| `dbo.Inventario_Sync` | `dbo.Sync_Inventory` |
| `dbo.Compras_Sync` | `dbo.Sync_Purchases` |

### Decisión Arquitectónica

- ❌ NO eliminar tablas legacy
- ❌ NO migrar físicamente datos todavía
- ❌ NO modificar dashboards actuales

### Regla para Desarrollo Nuevo

A partir de este momento todo desarrollo nuevo deberá utilizar:

```sql
-- USAR:
dbo.Inventario_Sync
dbo.Compras_Sync

-- EVITAR:
dbo.Sync_Inventory
dbo.Sync_Purchases
```

### Próximos Pasos

La migración física definitiva queda pendiente para una fase posterior, después de completar:

1. Auditoría de dependencias
2. Migración SQL-First de Compras e Inventarios
3. Validación de datos sincronizados

### Script DDL

Ubicación: `/app/backend/scripts/ddl_vistas_sync_legacy.sql`

