# BUG-COSTOS-001: Filtrado de Productos Inactivos/Baja en Costos y Márgenes

**Fecha de Reporte:** 2025-05-25  
**Estado:** RESUELTO (Fix adicional aplicado)  
**Severidad:** ALTA  
**Módulo Afectado:** Costos y Márgenes

---

## 1. Descripción del Problema

El módulo "Costos y Márgenes" no filtraba correctamente los productos dados de baja o inactivos:

1. **Problema Original:** El checkbox "Incluir inactivos/baja" no funcionaba porque el campo `Activo` siempre era `1`.
2. **Causa Raíz:** El job `sync_recetas.py` NO sincronizaba el campo `Suspendido` de SoftRestaurant.
3. **Resultado:** Productos como "CLAM CHOWDER" (con Precio $0 y Suspendido=SI) aparecían en la lista.

## 2. Solución Implementada (Dos niveles)

### Nivel A: Filtro Inmediato por Precio (Workaround)

Además de `p.Activo = 1`, ahora se filtra también `p.PrecioVenta > 0` porque productos con precio $0 típicamente están suspendidos.

**Archivos modificados:**
- `/app/backend/modules/costos_margenes/repository.py` (línea 122-126)
- `/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py` (línea 142-148)

```python
# BUG-COSTOS-001-FIX: Filtrar productos activos Y con precio > 0 por defecto
if not incluir_inactivos:
    where_clauses = ["p.Activo = 1", "p.PrecioVenta > 0"]
else:
    where_clauses = ["1=1"]
```

### Nivel B: Sincronización del Campo Suspendido (Fix Definitivo)

Se modificó `sync_recetas.py` para traer y sincronizar el campo `Suspendido` de SoftRestaurant.

**Archivos modificados:**
- `/app/backend/modules/sync_recetas/models.py` - Nuevo campo `activo` en `ProductoSync`
- `/app/backend/modules/sync_recetas/sync_recetas.py`:
  - Query `_obtener_productos_sr` ahora incluye `ISNULL(pd.suspendido, 0) as suspendido`
  - MERGE `_guardar_productos` ahora actualiza el campo `Activo` en UPDATE y INSERT

```sql
-- Query actualizado
SELECT p.idproducto, p.descripcion, ...,
       ISNULL(pd.suspendido, 0) as suspendido
FROM productos p
LEFT JOIN productosdetalle pd ON p.idproducto = pd.idproducto
...

-- MERGE actualizado
WHEN MATCHED THEN
    UPDATE SET 
        ...
        Activo = {activo_bit},  -- Ahora se actualiza
        ...
```

## 3. Criterio de Activación del Filtro

| Checkbox | Filtro SQL Aplicado |
|----------|---------------------|
| ☐ Sin marcar | `p.Activo = 1 AND p.PrecioVenta > 0` |
| ☑ Marcado | `1=1` (sin filtro) |

## 4. Flujo de Sincronización (Después del Fix)

```
SoftRestaurant                    EDARSAHUB SQL
productosdetalle.suspendido  -->  Sync_Productos.Activo
         0 (NO)              -->       1
         1 (SI)              -->       0
```

## 5. Validación Pendiente

⚠️ **IMPORTANTE:** Para que el fix definitivo (Nivel B) surta efecto, se debe ejecutar una resincronización de productos:

```bash
# Ejecutar sync de recetas para actualizar campo Activo
POST /api/sync-recetas/ejecutar?dry_run=false&server_ids=<SERVER_ID>
```

Esto actualizará el campo `Activo` en `Sync_Productos` basado en el campo `Suspendido` de SoftRestaurant.

## 6. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `repository.py` | Filtro adicional `PrecioVenta > 0` |
| `precios_sugeridos_consolidado_service.py` | Filtro adicional `PrecioVenta > 0` |
| `sync_recetas/models.py` | Nuevo campo `activo: bool` en `ProductoSync` |
| `sync_recetas/sync_recetas.py` | Query y MERGE actualizados para `Suspendido` → `Activo` |

---

**Resuelto por:** Agente E1  
**Fecha del Fix Adicional:** 2025-05-25
