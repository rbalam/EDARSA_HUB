# BUG-COSTOS-001: Filtrado de Productos Inactivos/Baja en Costos y Márgenes

**Fecha de Reporte:** 2025-05-25  
**Estado:** RESUELTO  
**Severidad:** ALTA  
**Módulo Afectado:** Costos y Márgenes

---

## 1. Descripción del Problema

El módulo "Costos y Márgenes" no filtraba por defecto los productos dados de baja o inactivos, causando:

- Cálculo de márgenes en productos descontinuados
- Uso innecesario de tokens de IA en productos no comercializados
- Datos erróneos en reportes de análisis de costos

## 2. Análisis de Causa Raíz

### Tablas Afectadas
- `Sync_Productos`: Campo `Activo` (BIT) indica estado del producto
- `Sync_Productos_Recetas`: Relación con productos

### Queries Afectadas
- `get_productos_con_costos()` en `repository.py`
- `obtener_precios_sugeridos()` en `precios_sugeridos_consolidado_service.py`

## 3. Solución Implementada

### Backend (repository.py)

```python
# Línea 106-123 - Nuevo parámetro y filtro
def get_productos_con_costos(
    ...
    incluir_inactivos: bool = False,  # BUG-COSTOS-001: Por defecto excluir inactivos
    ...
) -> Tuple[List[Dict], int]:
    # BUG-COSTOS-001: Filtrar solo productos activos por defecto
    where_clauses = ["p.Activo = 1"] if not incluir_inactivos else ["1=1"]
```

### Backend (routes.py)

```python
# Nuevo query parameter en endpoints
@router.get("/productos")
async def get_productos(
    ...
    incluir_inactivos: bool = Query(False, description="Incluir productos inactivos/baja"),
):
```

### Frontend (CostosMargenes.jsx)

```jsx
// Línea 1346 - Nuevo estado
const [incluirInactivos, setIncluirInactivos] = useState(false); // BUG-COSTOS-001

// Línea 1482 - Inclusión en parámetros de API
if (incluirInactivos) params.append('incluir_inactivos', 'true');

// Línea ~1691 - Checkbox en UI
<label className="flex items-center gap-2 text-sm text-gray-600">
  <input 
    type="checkbox"
    checked={incluirInactivos}
    onChange={(e) => setIncluirInactivos(e.target.checked)}
    className="rounded border-gray-300"
  />
  Incluir inactivos/baja
</label>
```

## 4. Archivos Modificados

| Archivo | Tipo de Cambio |
|---------|----------------|
| `/app/backend/modules/costos_margenes/repository.py` | Parámetro y filtro SQL |
| `/app/backend/modules/costos_margenes/routes.py` | Query parameter en endpoint |
| `/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py` | Parámetro y filtro SQL |
| `/app/backend/modules/comercial/routes_precios_sugeridos.py` | Query parameter en endpoint |
| `/app/frontend/src/pages/comercial/CostosMargenes.jsx` | Estado y checkbox UI |

## 5. Validación

### Backend (cURL)
```bash
# Endpoint productos - Por defecto solo activos
GET /api/costos-margenes/productos

# Endpoint productos - Incluir inactivos
GET /api/costos-margenes/productos?incluir_inactivos=true

# Endpoint precios sugeridos - Por defecto solo activos
GET /api/comercial/pricing/precios-sugeridos

# Endpoint precios sugeridos - Incluir inactivos
GET /api/comercial/pricing/precios-sugeridos?incluir_inactivos=true
```

### Frontend (Screenshot)
- Verificado que el checkbox "Incluir inactivos/baja" renderiza correctamente
- Ubicado en la barra de filtros junto a "Solo con receta" y "Margen bajo (<20%)"

## 6. Criterios de Aceptación Cumplidos

| # | Criterio | Estado |
|---|----------|--------|
| 1 | Por defecto NO mostrar productos inactivos | ✅ |
| 2 | Checkbox opcional para mostrar inactivos | ✅ |
| 3 | Filtro aplicado en todos los endpoints de costos | ✅ |
| 4 | Sin regresiones en funcionalidad existente | ✅ |
| 5 | CERO MongoDB | ✅ |

## 7. Evidencias

### Query SQL Aplicada
```sql
SELECT ...
FROM Sync_Productos p
WHERE p.Activo = 1  -- BUG-COSTOS-001: Por defecto solo activos
AND ...
```

### Comportamiento

| Checkbox | Comportamiento |
|----------|----------------|
| ☐ Sin marcar | Solo productos con `Activo = 1` |
| ☑ Marcado | Todos los productos (`1=1`) |

## 8. Impacto

- **Rendimiento:** Mejora al reducir procesamiento de productos irrelevantes
- **Tokens IA:** Ahorro al no analizar productos inactivos
- **Precisión:** Datos de margen más relevantes para productos activos
- **UX:** Control explícito del usuario sobre qué productos ver

## 9. Notas Adicionales

- El campo `Activo` proviene de SoftRestaurant/ManagementPro
- La sincronización (`sync_recetas`) actualiza este campo periódicamente
- NO se modifican datos originales en sistemas fuente

---

**Resuelto por:** Agente E1  
**Validado:** Frontend funcional, Backend testeado vía cURL
