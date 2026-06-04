# Refactor system_type - Uso de Helpers Existentes

**Fecha:** 2026-06-05  
**Agente:** E1

## Objetivo

Eliminar hardcodes de `system_type` en archivos de sync y usar el helper centralizado existente en `core/system_type_utils.py`.

## Antes (Hardcodes locales)

```python
# En cada archivo de sync había listas duplicadas:
AND s.system_type IN ('SoftRestaurant', 'SOFTRESTAURANT', 'SR', 'SOFTRESTAURANT_PRO')
AND s.system_type IN ('MPRO', 'ManagementPro', 'MANAGEMENTPRO')
```

## Después (Helper centralizado)

```python
from core.system_type_utils import build_system_type_sql_filter

# Uso en query:
AND {sr_filter}
""".format(sr_filter=build_system_type_sql_filter('s.system_type', 'SOFTRESTAURANT'))
```

## Archivos Refactorizados

| Archivo | Cambio |
|---------|--------|
| `sync_propinas_softrestaurant.py` | Import + uso de helper SOFTRESTAURANT |
| `sync_cortes_softrestaurant.py` | Import + uso de helper SOFTRESTAURANT |
| `sync_propinas_mpro.py` | Import + uso de helper MANAGEMENTPRO |

## Función Agregada a `core/system_type_utils.py`

```python
def get_system_type_sql_values(target_type: str) -> list:
    """Obtiene todas las variantes conocidas para un tipo de sistema"""
    
def build_system_type_sql_filter(column_name: str, target_type: str) -> str:
    """Construye filtro SQL IN() usando variantes centralizadas"""
```

## Valores Generados

### SOFTRESTAURANT
```
'SOFT', 'SOFT RESTAURANT', 'SOFTREST', 'SOFTRESTAURANT', 'SOFTRESTAURANTPRO', 
'SOFTRESTAURANT_PRO', 'SOFT_RESTAURANT', 'SR', 'SR_PRO'
```

### MANAGEMENTPRO
```
'MANAG', 'MANAGEMENT PRO', 'MANAGEMENTPRO', 'MANAGEMENT_PRO', 
'MANAGMENT PRO', 'MANAGMENTPRO', 'MANAGMENT_PRO', 'MPRO'
```

## Validación

- ✅ Sintaxis Python correcta
- ✅ Imports funcionan
- ✅ Conexión a CIENFUEGOS funciona
- ✅ Conexión a LA ESTELAR funciona
- ✅ Backend reiniciado correctamente

## Beneficios

1. **Fuente única de verdad**: Todas las variantes de `system_type` se definen en un solo lugar
2. **Mantenimiento simplificado**: Agregar una nueva variante solo requiere modificar `SYSTEM_TYPE_MAP`
3. **Consistencia**: No hay riesgo de olvidar una variante en algún archivo
4. **Trazabilidad**: Fácil auditar qué valores se usan en cada filtro
