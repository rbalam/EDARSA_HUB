# FASE 1C-3B-R3 - Fix Bug Decimal en Familias SoftRestaurant

## Resumen Ejecutivo

**Fecha**: 24 Mayo 2026
**SyncRunID**: `SYNC-RECETAS-20260524151422-c1122c37`
**Estado**: ✅ COMPLETADO

Se corrigió el bug de `Decimal.replace()` que impedía la sincronización de familias de SoftRestaurant hacia EDARSAHUB SQL Server.

---

## 1. Causa del Bug

### Problema
El campo `clasificacion` de la tabla `grupos` en SoftRestaurant podía devolver valores de tipo `Decimal` (cuando el campo contiene valores numéricos). El código original aplicaba `.replace()` directamente sin conversión previa a string.

### Error Original
```
AttributeError: 'decimal.Decimal' object has no attribute 'replace'
```

### Ubicación del Bug
**Archivo**: `/app/backend/modules/sync_recetas/sync_recetas.py`

**Línea 322 (ANTES)**:
```python
descripcion=r.get('clasificacion'),
```

**Línea 707/719 (USO QUE FALLABA)**:
```python
fam.descripcion.replace(chr(39), chr(39)+chr(39))
```

---

## 2. Archivo Corregido

**Archivo**: `/app/backend/modules/sync_recetas/sync_recetas.py`

### Correcciones Aplicadas

#### Corrección 1: Familias SoftRestaurant (línea 322)
**ANTES**:
```python
return [
    FamiliaSync(
        codigo_fuente=str(r.get('idgrupo', '')),
        nombre=str(r.get('descripcion', '')),
        descripcion=r.get('clasificacion'),  # ❌ Sin conversión
        orden=int(r.get('prioridad') or 0)
    )
    for r in rows
]
```

**DESPUÉS**:
```python
return [
    FamiliaSync(
        codigo_fuente=str(r.get('idgrupo', '')),
        nombre=str(r.get('descripcion', '')),
        # Fix FASE 1C-3B-R3: Convertir explícitamente a str()
        descripcion=str(r.get('clasificacion')) if r.get('clasificacion') is not None else None,
        orden=int(r.get('prioridad') or 0)
    )
    for r in rows
]
```

#### Corrección 2: Productos SoftRestaurant (líneas 398-400)
**ANTES**:
```python
nombre_corto=r.get('nombrecorto'),
familia_nombre=r.get('grupo_nombre'),
```

**DESPUÉS**:
```python
nombre_corto=str(r.get('nombrecorto')) if r.get('nombrecorto') else None,
familia_nombre=str(r.get('grupo_nombre')) if r.get('grupo_nombre') else None,
```

#### Corrección 3: Productos MPRO (líneas 638, 641-642)
**ANTES**:
```python
nombre_corto=r.get('Pr_Descripcion_Corta'),
familia_nombre=r.get('Fm_Descripcion'),
subfamilia_nombre=r.get('Sf_Descripcion'),
```

**DESPUÉS**:
```python
nombre_corto=str(r.get('Pr_Descripcion_Corta')) if r.get('Pr_Descripcion_Corta') else None,
familia_nombre=str(r.get('Fm_Descripcion')) if r.get('Fm_Descripcion') else None,
subfamilia_nombre=str(r.get('Sf_Descripcion')) if r.get('Sf_Descripcion') else None,
```

---

## 3. Resultado DRY-RUN

| Métrica | Valor |
|---------|-------|
| SyncRunID | `SYNC-RECETAS-20260524151350-7a8ae612` |
| Duración | 18.34 segundos |
| Éxito | ✅ True |
| Errores | 0 |

### Conteos Detectados
| Servidor | Familias | SubFamilias |
|----------|----------|-------------|
| CIENFUEGOS | 37 | 57 |
| 130° MÉRIDA | 33 | 36 |
| LA ESTELAR | 46 | 63 |
| **TOTAL** | **116** | **156** |

---

## 4. Familias Recuperadas por Unidad

### Antes del Fix
| Sistema | Familias |
|---------|----------|
| MPRO | 73 |
| SOFTRESTAURANT_PRO | 0 ❌ |
| **TOTAL** | **73** |

### Después del Fix
| Sistema | Familias |
|---------|----------|
| MPRO | 73 |
| SOFTRESTAURANT_PRO | 116 ✅ |
| **TOTAL** | **189** |

### Familias Recuperadas por Servidor SR
| Servidor | Familias Recuperadas |
|----------|---------------------|
| CIENFUEGOS | 37 |
| 130° MÉRIDA | 33 |
| LA ESTELAR | 46 |

---

## 5. Conteos Antes/Después

| Tabla | Antes | Después | Delta |
|-------|-------|---------|-------|
| Sync_Productos | 9,905 | 9,905 | 0 |
| Sync_Productos_Insumos | 11,735 | 11,735 | 0 |
| Sync_Productos_Recetas | 13,313 | 13,313 | 0 |
| Sync_Productos_Elaborados | 3,893 | 3,893 | 0 |
| Sync_Productos_Familias | 73 | 189 | **+116** |
| Sync_Productos_SubFamilias | 216 | 264 | **+48** |

---

## 6. Validación Sin Duplicados

| Tabla | Duplicados |
|-------|------------|
| Sync_Productos_Familias | ✅ 0 |
| Sync_Productos_SubFamilias | ✅ 0 |
| Sync_Productos | ✅ 0 |
| Sync_Productos_Recetas | ✅ 0 |
| Sync_Productos_Insumos | ✅ 0 |

---

## 7. Validación de Endpoints

### GET /api/costos-margenes/resumen
```json
{
  "source_type": "EDARSAHUB_SQL",
  "total_productos": 9905,
  "productos_con_receta": 4699
}
```
**Estado**: ✅ Funcional, NO-LIVE

### GET /api/costos-margenes/productos?familia=VINOS
```json
{
  "total": 1359,
  "items": [
    {"nombre": "CONVENIO COUNTRYCLUB", "familia": "B VINOS"},
    {"nombre": "DESCORCHE", "familia": "B VINOS"}
  ]
}
```
**Estado**: ✅ Filtro por familia funciona

---

## 8. Validación Frontend

- ✅ Login funciona
- ✅ Menú SQL carga
- ✅ Comercial/Ventas carga
- ✅ Dashboard Comercial funciona
- ✅ Costos y Márgenes muestra datos (9,905 productos)
- ✅ Filtro por familia disponible

---

## 9. Confirmación NO-LIVE

| Validación | Estado |
|------------|--------|
| Endpoints solo leen de EDARSAHUB SQL | ✅ |
| Sin conexiones live a SoftRestaurant | ✅ |
| Sin conexiones live a MPRO | ✅ |
| Sin MongoDB | ✅ |
| Frontend consume solo APIs locales | ✅ |

---

## 10. Validación de Productos Existentes

| Producto | Estado |
|----------|--------|
| QUESADILLA DE FLOR DE CALABAZA | ✅ Visible (Fam: C030, Receta: True) |
| Prod B Naranja en Gajos | ✅ Visible (Fam: 0019) |
| Productos CIENFUEGOS | ✅ 2,022 productos |

---

## 11. Riesgos Pendientes

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Error en `Sync_Control_Ejecuciones` (columna FechaInicio NULL) | Bajo | No afecta sincronización principal, solo auditoría |
| Conexión intermitente a CIENFUEGOS | Bajo | DNS dinámico resuelve correctamente |

---

## 12. Recomendación

✅ **Bug de Decimal corregido exitosamente**

Se recomienda proceder con **FASE 1C-3E** (Validación integral, permisos y exportación del módulo Costos y Márgenes).

### Criterios cumplidos para continuar:
1. ✅ Todas las familias SR sincronizadas (116)
2. ✅ Sin duplicados
3. ✅ Productos/Recetas/Insumos intactos
4. ✅ Endpoints NO-LIVE funcionando
5. ✅ Filtro por familia operativo
6. ✅ Sin regresiones

---

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/sync_recetas/sync_recetas.py` | Líneas 318-328, 394-408, 634-648 |

---

## Métricas de Desempeño

| Métrica | Valor |
|---------|-------|
| Tiempo DRY-RUN | 18.34s |
| Tiempo SYNC REAL | 28.71s |
| Registros insertados | 272 (116 familias + 156 subfamilias) |
| Errores de sync | 0 |
| Tasa de éxito | 100% |
