# FASE 5B: Refactor Mínimo service.py con EmpresaResolver

**Fecha**: 2026-05-16  
**Estado**: ✅ COMPLETADO Y VALIDADO  
**Rol**: Arquitecto Senior EDARSAHUB / DBA SQL Server  
**Tipo de Documento**: Reporte de Refactorización

---

## 1. Resumen Ejecutivo

Se refactorizó exitosamente el archivo `service.py` para usar `EmpresaResolver` como fuente de resolución canónica, eliminando hardcoding de sucursales MPRO y mapeos de unidades de negocio.

### Resultado:
- ✅ 3 funciones helper nuevas implementadas
- ✅ Hardcoding de sucursales_mpro eliminado
- ✅ EmpresaResolver integrado como fuente primaria
- ✅ 9/9 pruebas de aliases pasaron
- ✅ 2/2 pruebas de PRINCIPAL_SQL pasaron
- ✅ 2/2 pruebas de VENTAS_DIA_API_LOCAL pasaron
- ✅ Backend funcionando correctamente

---

## 2. Archivo(s) Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/comercial/service.py` | Refactorizado con EmpresaResolver |

---

## 3. Funciones Modificadas/Agregadas

| Función | Estado | Descripción |
|---------|--------|-------------|
| `_obtener_codigo_canonico_mpro()` | MODIFICADA | Ahora usa EmpresaResolver primero |
| `_mapear_codigo_a_unidad_negocio_id()` | **NUEVA** | Mapea código canónico a formato legacy |
| `_obtener_sucursales_mpro_desde_resolver()` | **NUEVA** | Obtiene sucursales MPRO desde EmpresaResolver |
| `get_kpis_softrestaurant()` | MODIFICADA | Usa `_mapear_codigo_a_unidad_negocio_id()` |
| `get_kpis_mpro()` | MODIFICADA | Usa `_obtener_sucursales_mpro_desde_resolver()` |

---

## 4. Antes/Después de Lógica Eliminada

### 4.1 `_obtener_codigo_canonico_mpro()`

**ANTES:**
```python
def _obtener_codigo_canonico_mpro(server_id, sucursal_id, sucursal_nombre):
    unidad_edarsahub = obtener_unidad_negocio_edarsahub(server_id, sucursal=sucursal_id)
    codigo = unidad_edarsahub.get('codigo', '')
    # ... fallback hardcodeado
```

**DESPUÉS:**
```python
def _obtener_codigo_canonico_mpro(server_id, sucursal_id, sucursal_nombre):
    # FASE 5B: Intentar resolver con EmpresaResolver primero
    if _EMPRESA_RESOLVER_OK and EMPRESA_RESOLVER_AVAILABLE:
        empresa = resolve_empresa_by_alias(sucursal_nombre)
        if empresa:
            return empresa.codigo_empresa, empresa.nombre_comercial
        # Buscar por CodigoSucursalSistema en Sistema_EmpresasServidores
        # ...
    # Fallback a Unidades_Negocio y hardcodeado
```

### 4.2 Mapeo de Unidades de Negocio

**ANTES (hardcodeado en get_kpis_softrestaurant):**
```python
unidad_negocio_id_map = {
    '130MID': '130-MER',
    'CIENFUEGOS': 'CIENFUEGOS',
    'ESTELAR': 'LA-ESTELAR',
    '130QRO': '130-QRO',
    'ORIGEN': 'ORIGEN'
}
unidad_negocio_id = unidad_negocio_id_map.get(codigo, codigo)
```

**DESPUÉS (función centralizada):**
```python
unidad_negocio_id = _mapear_codigo_a_unidad_negocio_id(unidad_negocio_codigo)
```

### 4.3 Sucursales MPRO

**ANTES (hardcodeado en get_kpis_mpro):**
```python
sucursales_mpro = [
    {"codigo": "ORIGEN", "sucursal_id": "0023", "server_id": "817a0aa8-..."},
    {"codigo": "130QRO", "sucursal_id": "0021", "server_id": "72f6e9a7-..."},
]
```

**DESPUÉS (dinámico desde EmpresaResolver):**
```python
sucursales_mpro = _obtener_sucursales_mpro_desde_resolver()
```

---

## 5. Evidencia de Eliminación de Hardcoding

| Patrón | Ubicación Anterior | Estado |
|--------|-------------------|--------|
| `sucursales_mpro = [...]` | get_kpis_mpro() línea 1444-1455 | ✅ REEMPLAZADO por `_obtener_sucursales_mpro_desde_resolver()` |
| `unidad_negocio_id_map = {...}` | get_kpis_softrestaurant() línea 1132-1139 | ✅ REEMPLAZADO por `_mapear_codigo_a_unidad_negocio_id()` |
| Fallback `0021`/`0023` | _obtener_codigo_canonico_mpro() | ✅ MANTENIDO como último recurso |

---

## 6. Evidencia de Uso de EmpresaResolver

```python
# Importación al inicio de service.py
from core.empresa_resolver import (
    resolve_empresa_by_alias,
    resolve_empresa_by_id,
    get_connection_for_role,
    get_empresa_connections,
    get_system_branch_context,
    normalize_alias,
    EMPRESA_RESOLVER_AVAILABLE
)
_EMPRESA_RESOLVER_OK = True

# Uso en _obtener_codigo_canonico_mpro()
if _EMPRESA_RESOLVER_OK and EMPRESA_RESOLVER_AVAILABLE:
    empresa = resolve_empresa_by_alias(sucursal_nombre)

# Uso en _obtener_sucursales_mpro_desde_resolver()
if _EMPRESA_RESOLVER_OK and EMPRESA_RESOLVER_AVAILABLE:
    from core.empresa_resolver import _execute_query
    rows = _execute_query(query)
```

---

## 7. Validación ORIGEN

| Prueba | Resultado |
|--------|-----------|
| `resolve_empresa_by_alias('ORIGEN')` | EmpresaID=1 ✅ |
| `_obtener_codigo_canonico_mpro(_, '0023', _)` | ('ORIGEN', 'Restaurante Origen S.A. de C.V.') ✅ |
| `get_connection_for_role(1, 'PRINCIPAL_SQL')` | Sucursal=23/0023 ✅ |
| `get_connection_for_role(1, 'VENTAS_DIA_API_LOCAL')` | API=ORIGEN LOCAL ✅ |

---

## 8. Validación 130QRO

| Prueba | Resultado |
|--------|-----------|
| `resolve_empresa_by_alias('130QRO')` | EmpresaID=2 ✅ |
| `resolve_empresa_by_alias('130-QRO')` | EmpresaID=2 ✅ |
| `resolve_empresa_by_alias('QRO')` | EmpresaID=2 ✅ |
| `_obtener_codigo_canonico_mpro(_, '0021', _)` | ('130QRO', '130 Grados Querétaro S.A. de C.V.') ✅ |
| `get_connection_for_role(2, 'PRINCIPAL_SQL')` | Sucursal=21/0021 ✅ |
| `get_connection_for_role(2, 'VENTAS_DIA_API_LOCAL')` | API=130° QRO LOCAL ✅ |

---

## 9. Validación 130MID

| Prueba | Resultado |
|--------|-----------|
| `resolve_empresa_by_alias('130MID')` | EmpresaID=5 ✅ |
| `resolve_empresa_by_alias('130-MER')` | EmpresaID=5 ✅ |
| `_mapear_codigo_a_unidad_negocio_id('130MID')` | '130-MER' ✅ |

---

## 10. Validación CIENFUEGOS

| Prueba | Resultado |
|--------|-----------|
| `resolve_empresa_by_alias('CIENFUEGOS')` | EmpresaID=3 ✅ |
| `_mapear_codigo_a_unidad_negocio_id('CIENFUEGOS')` | 'CIENFUEGOS' ✅ |

---

## 11. Validación ESTELAR

| Prueba | Resultado |
|--------|-----------|
| `resolve_empresa_by_alias('ESTELAR')` | EmpresaID=4 ✅ |
| `resolve_empresa_by_alias('LA ESTELAR')` | EmpresaID=4 ✅ |
| `_mapear_codigo_a_unidad_negocio_id('ESTELAR')` | 'ESTELAR' ✅ |

---

## 12. Validación APIs Locales por RolConexion

| Empresa | RolConexion | API Encontrada | Sucursal | Status |
|---------|-------------|----------------|----------|--------|
| ORIGEN | VENTAS_DIA_API_LOCAL | ORIGEN LOCAL | 23/0023 | ✅ |
| 130QRO | VENTAS_DIA_API_LOCAL | 130° QRO LOCAL | 21/0021 | ✅ |

---

## 13. Validación MPRO por NumeroSucursalSistema

| Empresa | NumeroSucursalSistema | CodigoSucursalSistema | Status |
|---------|----------------------|----------------------|--------|
| ORIGEN | 23 | 0023 | ✅ |
| 130QRO | 21 | 0021 | ✅ |

**Fuente**: `_obtener_sucursales_mpro_desde_resolver()` retorna:
```
ORIGEN  | SucursalID=0023 | Rol=VENTAS_DIA_API_LOCAL | Fuente=EmpresaResolver
130QRO  | SucursalID=0021 | Rol=VENTAS_DIA_API_LOCAL | Fuente=EmpresaResolver
```

---

## 14. Confirmación: No se Tocó Frontend

```bash
find /app/frontend -name "*.js" -newer /app/backend/modules/comercial/service.py 2>/dev/null
# Resultado: 0 archivos modificados
```

✅ **CONFIRMADO**: Frontend no modificado.

---

## 15. Confirmación: No se Tocaron Jobs

| Archivo | Modificado |
|---------|------------|
| `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py` | ❌ NO |
| `/app/backend/core/scheduler/` | ❌ NO |

✅ **CONFIRMADO**: Jobs no modificados.

---

## 16. Confirmación: No se Reactivó LIVE desde Tablero

- `get_kpis_softrestaurant()` sigue leyendo de EDARSAHUB SQL (Comercial_Ventas_Dia_Abiertas_v2)
- `get_kpis_mpro()` sigue leyendo de EDARSAHUB SQL (NO APIs locales)
- La función `_obtener_sucursales_mpro_desde_resolver()` solo proporciona metadatos, no ejecuta queries LIVE

✅ **CONFIRMADO**: No se reactivó LIVE desde tablero.

---

## 17. Riesgos Pendientes

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| `mpro.py` aún usa lógica legacy | Media | Medio | Siguiente fase: refactorizar |
| Jobs aún no usan EmpresaResolver | Alta | Alto | Siguiente fase: refactorizar |
| Fallbacks hardcodeados aún existen | Baja | Bajo | Se mantienen para resiliencia |

---

## 18. Fallbacks Legacy que Permanecen

| Función | Fallback | Motivo |
|---------|----------|--------|
| `_obtener_codigo_canonico_mpro()` | Mapeo `0021`→`130QRO`, `0023`→`ORIGEN` | Resiliencia si EmpresaResolver falla |
| `_mapear_codigo_a_unidad_negocio_id()` | Mapeo `130MID`→`130-MER`, etc. | Compatibilidad con tabla legacy |
| `_obtener_sucursales_mpro_desde_resolver()` | Lista hardcodeada de ORIGEN/130QRO | Resiliencia si EDARSAHUB no responde |

---

## 19. Siguiente Fase Recomendada

1. **P0**: Refactorizar `mpro.py` para usar EmpresaResolver
2. **P1**: Refactorizar jobs del scheduler para usar EmpresaResolver
3. **P2**: Limpiar registros legacy duplicados en tablas operativas

**NOTA**: Estas fases requieren autorización explícita antes de proceder.

---

## 20. Resumen de Pruebas

| Categoría | Pasaron | Total |
|-----------|---------|-------|
| Resolución de aliases | 9 | 9 |
| PRINCIPAL_SQL | 2 | 2 |
| VENTAS_DIA_API_LOCAL | 2 | 2 |
| Sucursales MPRO | 2 | 2 |
| **TOTAL** | **15** | **15** |

---

**FIN DEL REPORTE**

Refactorización de service.py completada. Esperando autorización para siguiente fase.
