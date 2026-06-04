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

---

## Validación Final (2026-06-05)

### Estado del Refactor

| Archivo | Estado | Método |
|---------|--------|--------|
| `sync_propinas_softrestaurant.py` | ✅ Refactorizado | `.format(sr_filter=build_system_type_sql_filter(...))` |
| `sync_cortes_softrestaurant.py` | ✅ Refactorizado | `.format(sr_filter=build_system_type_sql_filter(...))` |
| `sync_propinas_mpro.py` | ✅ Refactorizado | `.format(mpro_filter=build_system_type_sql_filter(...))` |

### Validación API

| Unidad | Registros | Propinas TPV | Fuente |
|--------|-----------|--------------|--------|
| CIENFUEGOS | 405 | $241,766.84 | EDARSAHUB_REAL |
| LA ESTELAR | 550 | $101,627.24 | EDARSAHUB_REAL |

### Archivos Audit-Only (No Modificados)

| Archivo | Razón |
|---------|-------|
| `server.py` | Solo comentarios y imports, no filtros SQL |
| `api/catalogos_sistemas.py` | CASE WHEN para display, no filtros de query |
| `sync_compras_job.py` | Ya tiene filtro completo |
| `detect_nuevos_compras_job.py` | Ya tiene filtro completo |

### Conclusión

El refactor está **COMPLETO** para los archivos de sincronización de propinas/cortes.
No hay placeholders `{softrestaurant_filter}` sin interpolar.
