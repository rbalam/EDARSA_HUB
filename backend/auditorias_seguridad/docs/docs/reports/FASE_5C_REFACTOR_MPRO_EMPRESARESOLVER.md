# FASE 5C: Refactor Mínimo mpro.py con EmpresaResolver

**Fecha**: 2026-05-16  
**Estado**: ✅ COMPLETADO Y VALIDADO  
**Rol**: Arquitecto Senior EDARSAHUB / DBA SQL Server  
**Tipo de Documento**: Reporte de Refactorización

---

## 1. Resumen Ejecutivo

Se refactorizó exitosamente el archivo `mpro.py` para usar `EmpresaResolver` como fuente de resolución canónica, eliminando el uso de `LIKE '%{sucursal}%'` para identificar unidades MPRO.

### Resultado:
- ✅ LIKE por nombre eliminado de la ruta principal
- ✅ EmpresaResolver integrado como fuente primaria
- ✅ Resolución por CodigoSucursalSistema implementada
- ✅ 8/8 pruebas de resolución pasaron
- ✅ 6/6 pruebas de filtro SQL pasaron
- ✅ Backend funcionando correctamente

---

## 2. Archivo(s) Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/comercial/queries/mpro.py` | Refactorizado con EmpresaResolver |

---

## 3. Funciones Modificadas/Agregadas

| Función | Estado | Descripción |
|---------|--------|-------------|
| `_resolver_codigo_sucursal_mpro()` | **NUEVA** | Resuelve alias a CodigoSucursalSistema |
| `_build_sucursal_filter_mpro_flexible()` | MODIFICADA | Usa `_resolver_codigo_sucursal_mpro()` |
| `query_ventas_periodo_mpro_con_filtro_flexible()` | MODIFICADA | Usa `_resolver_codigo_sucursal_mpro()` |

---

## 4. Antes/Después de Lógica Eliminada

### 4.1 `query_ventas_periodo_mpro_con_filtro_flexible()`

**ANTES (LIKE por nombre):**
```python
if not skip_sucursal_filter:
    es_codigo = sucursal.isdigit() or (len(sucursal) == 4 and sucursal[0] == '0')
    
    if es_codigo:
        sucursal_filter = f" AND VE.Sc_Cve_Sucursal = '{sucursal}'"
    else:
        # PROBLEMA: LIKE por nombre
        sucursal_join = "INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal"
        sucursal_filter = f" AND S.Sc_Descripcion LIKE '%{sucursal}%'"
```

**DESPUÉS (EmpresaResolver primero):**
```python
if not skip_sucursal_filter:
    # FASE 5C: Intentar resolver con EmpresaResolver primero
    codigo_sucursal_resuelto = _resolver_codigo_sucursal_mpro(sucursal)
    
    if codigo_sucursal_resuelto:
        # Resuelto por EmpresaResolver - usar código exacto
        sucursal_filter = f" AND VE.Sc_Cve_Sucursal = '{codigo_sucursal_resuelto}'"
    else:
        # Fallback legacy (solo si EmpresaResolver no tiene el alias)
        ...
```

### 4.2 `_build_sucursal_filter_mpro_flexible()`

**ANTES:**
```python
return (
    f"({alias_sucursal}.Sc_Cve_Sucursal = '{sucursal}' "
    f"OR {alias_sucursal}.Sc_Descripcion LIKE '%{sucursal}%')"
)
```

**DESPUÉS:**
```python
codigo_resuelto = _resolver_codigo_sucursal_mpro(sucursal)

if codigo_resuelto:
    return f"{alias_venta}.Sc_Cve_Sucursal = '{codigo_resuelto}'"

# Fallback legacy
return (...)
```

---

## 5. Evidencia de Eliminación de LIKE por Nombre

| Función | LIKE Anterior | LIKE Actual |
|---------|---------------|-------------|
| `query_ventas_periodo_mpro_con_filtro_flexible()` | `LIKE '%{sucursal}%'` (línea 340) | Solo en fallback con warning |
| `_build_sucursal_filter_mpro_flexible()` | `LIKE '%{sucursal}%'` (línea 496) | Solo en fallback si EmpresaResolver falla |

**Ruta Principal**: Ahora usa `Sc_Cve_Sucursal = '{codigo}'` con código resuelto por EmpresaResolver.

---

## 6. Evidencia de Eliminación de Matching Textual

### Patrones Eliminados de la Ruta Principal:

| Patrón | Estado |
|--------|--------|
| `LIKE '%ORIGEN%'` | ✅ Reemplazado por `= '0023'` |
| `LIKE '%QRO%'` | ✅ Reemplazado por `= '0021'` |
| `LIKE '%QUERETARO%'` | ✅ Reemplazado por `= '0021'` |
| `contains('ORIGEN')` | N/A (no existía) |
| `split('ORIGEN')` | N/A (no existía) |

---

## 7. Evidencia de Uso de EmpresaResolver

```python
# Importación al inicio de mpro.py
from core.empresa_resolver import (
    resolve_empresa_by_alias,
    get_connection_for_role,
    normalize_alias,
    EMPRESA_RESOLVER_AVAILABLE
)
_EMPRESA_RESOLVER_OK = True

# Uso en _resolver_codigo_sucursal_mpro()
if _EMPRESA_RESOLVER_OK and EMPRESA_RESOLVER_AVAILABLE:
    empresa = resolve_empresa_by_alias(sucursal)
    if empresa:
        connection = get_connection_for_role(empresa.empresa_id, 'PRINCIPAL_SQL')
        if connection and connection.codigo_sucursal_sistema:
            return connection.codigo_sucursal_sistema
```

---

## 8. Validación ORIGEN

| Prueba | Resultado |
|--------|-----------|
| `resolve_empresa_by_alias('ORIGEN')` | EmpresaID=1 ✅ |
| `_resolver_codigo_sucursal_mpro('ORIGEN')` | '0023' ✅ |
| `get_connection_for_role(1, 'PRINCIPAL_SQL')` | NumeroSucursal=23, Codigo=0023 ✅ |
| ORIGEN NO usa `sucursal_id=0001` | ✅ CONFIRMADO (usa 0023) |

---

## 9. Validación 130QRO

| Prueba | Resultado |
|--------|-----------|
| `resolve_empresa_by_alias('130QRO')` | EmpresaID=2 ✅ |
| `resolve_empresa_by_alias('130-QRO')` | EmpresaID=2 ✅ |
| `resolve_empresa_by_alias('QRO')` | EmpresaID=2 ✅ |
| `resolve_empresa_by_alias('QUERETARO')` | EmpresaID=2 ✅ |
| `_resolver_codigo_sucursal_mpro('130QRO')` | '0021' ✅ |
| `_resolver_codigo_sucursal_mpro('QRO')` | '0021' ✅ |
| `get_connection_for_role(2, 'PRINCIPAL_SQL')` | NumeroSucursal=21, Codigo=0021 ✅ |

---

## 10. Validación MPRO por NumeroSucursalSistema

| Empresa | EmpresaID | NumeroSucursalSistema | CodigoSucursalSistema | Status |
|---------|-----------|----------------------|----------------------|--------|
| ORIGEN | 1 | 23 | 0023 | ✅ |
| 130QRO | 2 | 21 | 0021 | ✅ |

---

## 11. Confirmación: ORIGEN usa Sucursal 23/0023

```python
>>> get_connection_for_role(1, 'PRINCIPAL_SQL')
ConnectionInfo(
    empresa_id=1,
    numero_sucursal_sistema=23,
    codigo_sucursal_sistema='0023',
    nombre_sucursal_sistema='ORIGEN',
    ...
)
```

✅ **CONFIRMADO**: ORIGEN resuelve a NumeroSucursal=23, Codigo=0023

---

## 12. Confirmación: 130QRO usa Sucursal 21/0021

```python
>>> get_connection_for_role(2, 'PRINCIPAL_SQL')
ConnectionInfo(
    empresa_id=2,
    numero_sucursal_sistema=21,
    codigo_sucursal_sistema='0021',
    nombre_sucursal_sistema='130° QUERETARO',
    ...
)
```

✅ **CONFIRMADO**: 130QRO resuelve a NumeroSucursal=21, Codigo=0021

---

## 13. Confirmación: No se Tocó Frontend

```bash
find /app/frontend -name "*.js" -newer /app/backend/modules/comercial/queries/mpro.py 2>/dev/null
# Resultado: 0 archivos modificados
```

✅ **CONFIRMADO**: Frontend no modificado.

---

## 14. Confirmación: No se Tocaron Jobs

| Archivo | Modificado |
|---------|------------|
| `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py` | ❌ NO |
| `/app/backend/core/scheduler/` | ❌ NO |

✅ **CONFIRMADO**: Jobs no modificados.

---

## 15. Confirmación: No se Reactivó LIVE desde Tablero

- `mpro.py` contiene funciones de query que son llamadas por jobs de sincronización
- El Tablero Ejecutivo no llama directamente a estas funciones
- No hay cambios que permitan conexiones LIVE desde endpoints funcionales

✅ **CONFIRMADO**: No se reactivó LIVE desde tablero.

---

## 16. Riesgos Pendientes

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Jobs aún no usan EmpresaResolver | Alta | Alto | Siguiente fase: refactorizar jobs |
| LIKE legacy aún existe como fallback | Baja | Bajo | Se activa solo si EmpresaResolver falla |
| Aliases no cubiertos podrían usar LIKE | Baja | Bajo | Agregar aliases faltantes a BD |

---

## 17. Fallbacks Legacy que Permanecen

| Función | Fallback | Condición |
|---------|----------|-----------|
| `_resolver_codigo_sucursal_mpro()` | Mapeo hardcodeado ORIGEN→0023, QRO→0021 | Si EmpresaResolver falla |
| `_build_sucursal_filter_mpro_flexible()` | LIKE por nombre | Si EmpresaResolver no resuelve alias |
| `query_ventas_periodo_mpro_con_filtro_flexible()` | LIKE por nombre con warning | Si EmpresaResolver no resuelve alias |

**NOTA**: Los fallbacks generan warnings en logs para identificar aliases faltantes.

---

## 18. Siguiente Fase Recomendada

1. **P1**: Refactorizar jobs del scheduler para usar EmpresaResolver
2. **P2**: Agregar aliases faltantes a Sistema_EmpresasAlias si se detectan en logs
3. **P2**: Limpiar registros legacy duplicados en tablas operativas

**NOTA**: Estas fases requieren autorización explícita antes de proceder.

---

## 19. Resumen de Pruebas

| Categoría | Pasaron | Total |
|-----------|---------|-------|
| `_resolver_codigo_sucursal_mpro()` | 8 | 8 |
| `_build_sucursal_filter_mpro_flexible()` | 6 | 6 |
| Validación EmpresaResolver | 7 | 7 |
| **TOTAL** | **21** | **21** |

---

## 20. Función Nueva: `_resolver_codigo_sucursal_mpro()`

```python
def _resolver_codigo_sucursal_mpro(sucursal: str) -> Optional[str]:
    """
    FASE 5C HELPER: Resuelve un alias/nombre de sucursal a CodigoSucursalSistema MPRO.
    
    MAPEO CRÍTICO:
    - ORIGEN → EmpresaID=1 → CodigoSucursalSistema=0023
    - 130QRO → EmpresaID=2 → CodigoSucursalSistema=0021
    
    Prioridad:
    1. Si ya es código (4 dígitos), retornar
    2. EmpresaResolver: alias → EmpresaID → PRINCIPAL_SQL → CodigoSucursal
    3. Fallback hardcodeado
    """
```

---

**FIN DEL REPORTE**

Refactorización de mpro.py completada. Esperando autorización para siguiente fase.
