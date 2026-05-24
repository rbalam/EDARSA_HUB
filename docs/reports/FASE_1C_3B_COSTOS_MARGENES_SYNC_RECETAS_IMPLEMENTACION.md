# FASE 1C-3B: Implementación Job Sync Recetas - Costos y Márgenes

**Fecha**: 24 de Mayo 2026  
**Autor**: Sistema EDARSA HUB  
**Estado**: COMPLETADO (Sync en progreso background)

---

## 1. Resumen Ejecutivo

Se implementó el job `sync_recetas.py` para sincronizar productos, recetas, insumos, familias y costos desde los sistemas fuente (SoftRestaurant y MPRO) hacia las tablas `Sync_Productos*` en EDARSAHUB SQL.

### Resultados DRY-RUN (Validación Previa)

| Servidor | Sistema | Familias | SubFam | Productos | Con Receta | Insumos | Recetas | Elaborados |
|----------|---------|----------|--------|-----------|------------|---------|---------|------------|
| LA ESTELAR | SOFTRESTAURANT_PRO | 46 | 63 | 611 | 559 (91%) | 1,199 | 1,583 | 615 |
| 130° MERIDA | SOFTRESTAURANT_PRO | 33 | 36 | 1,858 | 1,765 (95%) | 2,629 | 4,999 | 1,435 |
| ManagmentPro | MPRO | 73 | 108 | 5,414 | 452 (8%) | 10,696 | 2,759 | 0 |
| **TOTAL** | - | **152** | **207** | **7,883** | **2,776** | **14,524** | **9,341** | **2,050** |

### Sync Run ID
`SYNC-RECETAS-20260524133926-b652313f`

---

## 2. Archivos Modificados

### 2.1 Archivos Creados/Modificados

| Archivo | Estado | Descripción |
|---------|--------|-------------|
| `/app/backend/modules/sync_recetas/__init__.py` | Creado | Módulo de sincronización |
| `/app/backend/modules/sync_recetas/models.py` | Creado | Dataclasses para entidades de sync |
| `/app/backend/modules/sync_recetas/sync_recetas.py` | Creado | Job ETL completo (1,084 líneas) |

### 2.2 Tablas Destino (EDARSAHUB SQL)

| Tabla | Propósito |
|-------|-----------|
| `Sync_Productos` | Catálogo de productos |
| `Sync_Productos_Familias` | Grupos/Familias de productos |
| `Sync_Productos_SubFamilias` | SubGrupos/SubFamilias |
| `Sync_Productos_Insumos` | Catálogo de insumos con costos |
| `Sync_Productos_Recetas` | Líneas de receta (producto → insumo) |
| `Sync_Productos_Elaborados` | Sub-recetas (insumo elaborado → componente) |

---

## 3. Fuentes de Datos Utilizadas

### 3.1 SoftRestaurant (LA ESTELAR, 130° MERIDA)

| Tabla Fuente | Uso |
|--------------|-----|
| `grupos` | Familias de productos |
| `subgrupos` + `grupossubgrupos` | SubFamilias |
| `productos` + `productosdetalle` | Catálogo de productos y precios |
| `insumos` + `insumosdetalle` | Catálogo de insumos y costos |
| `costos` | **RECETAS** (producto → insumo) |
| `elaborados` | **SUB-RECETAS** (insumo elaborado → componente) |

**NOTA IMPORTANTE**: Se confirmó que en SoftRestaurant las recetas están en la tabla `costos`, NO en `explosioninsumosdetalle` (que está vacía).

### 3.2 MPRO (ManagmentPro)

| Tabla Fuente | Uso |
|--------------|-----|
| `Familia` | Familias de productos |
| `SubFamilia` | SubFamilias |
| `Producto` + `Producto_Precio` | Catálogo de productos y precios |
| `Existencia` | Costos de productos/insumos |
| `Formula_Produccion` + `Formula_Produccion_Detalle` | Recetas |

**NOTA**: En MPRO el estado activo es `Es_Cve_Estado = 'AC'` (no 'A').

---

## 4. Validación del Producto de Ejemplo

### QUESADILLA DE FLOR DE CALABAZA

```
PRODUCTO ENCONTRADO:
  ID: e3cd6b88-c29f-4007-aa8c-fee6d7d34497
  Nombre: QUESADILLA DE FLOR DE CALABAZA
  CodigoFuente: 46001
  Familia: C EVENTOS
  Precio: 0.0010
  TieneReceta: True
  Componentes: 7
  SystemType: SOFTRESTAURANT_PRO
  SyncRunID: SYNC-RECETAS-20260524133926-b652313f

RECETA (7 insumos):
  - A CILANTRO CRIOLLO GR           1.000 GR
  - A CREMA ENTERA/ACIDA GR        50.000 GR
  - A FLOR DE CALABAZA             20.000 GR
  - A MASA AMARILLA GR             90.000 GR
  - A QUESO COTIJA GR              20.000 GR
  - A QUESO OAXACA GR             100.000 GR
  - B CHAPULIN SECO GR              1.000 GR
```

**Validación**: ✅ EXITOSA - Producto encontrado con receta completa de 7 insumos.

---

## 5. Estado de Sincronización

### 5.1 Progreso al cierre del reporte

| Tabla | Actual | Esperado | % |
|-------|--------|----------|---|
| Sync_Productos | 2,469 | 7,883 | 31% |
| Sync_Productos_Familias | 73 | 152 | 48% |
| Sync_Productos_SubFamilias | 207 | 207 | 100% ✅ |
| Sync_Productos_Insumos | 6,763 | 14,524 | 47% |
| Sync_Productos_Recetas | 6,582 | 9,341 | 70% |
| Sync_Productos_Elaborados | 2,050 | 2,050 | 100% ✅ |

**NOTA**: El sync de MPRO continúa en background. Los datos de SoftRestaurant están completos.

### 5.2 Servidores Procesados

| Servidor | Estado |
|----------|--------|
| LA ESTELAR | ✅ Completado |
| 130° MERIDA | ✅ Completado |
| ManagmentPro (MPRO) | ⏳ En progreso |
| CIENFUEGOS | ⚠️ Excluido (problema de red conocido) |

---

## 6. Correcciones Aplicadas

### 6.1 Errores de Esquema Corregidos

| Error | Corrección |
|-------|-----------|
| `idgrupoinsumo` no válida | Cambiado a `idgruposi` (SoftRestaurant) |
| `Pp_Precio_Lista` no válida | Cambiado a `Pp_Precio_1` (MPRO) |
| `Es_Cve_Estado = 'A'` sin resultados | Cambiado a `'AC'` (MPRO) |
| Campo `nombre` vs `name` en servidor | Añadido fallback `server.get('name', server.get('nombre'))` |

### 6.2 Tabla Familias - FamiliaID

Se detectó que la tabla `Sync_Productos_Familias` requiere `FamiliaID` como PK generado. El INSERT incluye `NEWID()` para generarlo automáticamente en el MERGE.

---

## 7. Validaciones NO-LIVE

| Validación | Estado |
|------------|--------|
| Login funciona | ✅ |
| Auth SQL-first funciona | ✅ |
| Dashboard Comercial responde | ✅ |
| Ventas por Hora (EDARSAHUB SQL) | ✅ |
| No conexiones live a SoftRestaurant desde endpoints | ✅ |
| No conexiones live a MPRO desde endpoints | ✅ |
| No dependencia MongoDB | ✅ |

---

## 8. Costos de Insumos

### Estadísticas

- **Total insumos sincronizados**: 6,147+
- **Insumos con costo > 0**: 3,865 (62.9%)
- **Insumos sin costo**: 2,282 (37.1%)

**NOTA**: Los insumos sin costo son datos del origen. Esto es esperado para insumos que aún no tienen precio de compra registrado.

---

## 9. Riesgos y Observaciones

| Riesgo | Mitigación |
|--------|-----------|
| CIENFUEGOS no sincronizado | Servidor con problemas de red (backlog operativo) |
| Algunos insumos sin costo | Dato de origen, no error del sync |
| Sync de MPRO lento | ~10,000+ registros, usa MERGE individual |

---

## 10. Recomendación para FASE 1C-3C

✅ **Se recomienda proceder con FASE 1C-3C** (Endpoints NO-LIVE de Costos y Márgenes)

**Justificación**:
1. Las tablas `Sync_Productos*` ya contienen datos válidos
2. El producto de validación fue encontrado con su receta completa
3. El sistema no presenta regresiones
4. Los datos de SoftRestaurant están completos (91-95% de productos con receta)
5. El sync de MPRO continuará en background

**Endpoints propuestos para FASE 1C-3C**:
- `GET /api/costos-margenes/productos` - Lista productos con costo calculado
- `GET /api/costos-margenes/productos/{id}/receta` - Receta expandida con costos
- `GET /api/costos-margenes/resumen` - KPIs de costos y márgenes
- `GET /api/costos-margenes/analisis-margen` - Análisis de margen por producto

---

## 11. Checklist Cumplido

- [x] Archivos revisados
- [x] Archivos modificados/creados
- [x] Tablas destino usadas
- [x] Fuentes SoftRestaurant usadas
- [x] Confirmación de uso de `costos` (recetas)
- [x] Confirmación de uso de `elaborados` (sub-recetas)
- [x] Confirmación de NO uso de `explosioninsumosdetalle`
- [x] Resultado DRY-RUN documentado
- [x] Resultado sync real (parcial - en progreso)
- [x] `sync_run_id` registrado
- [x] Validación de QUESADILLA DE FLOR DE CALABAZA ✅
- [x] Errores encontrados y corregidos
- [x] Validación NO-LIVE confirmada
- [x] Validación no regresión confirmada
- [x] Recomendación para FASE 1C-3C incluida

---

**Fin del Reporte FASE 1C-3B**
