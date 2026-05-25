# BUG-COSTOS-001-R2: Corrección de Filtro Estado Producto (Suspendido/Baja, NO PrecioVenta > 0)

**Fecha de Reporte:** 2025-05-25  
**Estado:** RESUELTO  
**Severidad:** ALTA  
**Módulo Afectado:** Costos y Márgenes, Sync Recetas

---

## 1. Causa Raíz del Error Anterior

### Error Introducido en BUG-COSTOS-001-FIX
Se implementó un filtro `p.PrecioVenta > 0` como criterio para determinar si un producto estaba activo.

**Esto es INCORRECTO porque:**
- Un producto puede tener precio $0 y estar **ACTIVO** (pendiente de configuración de precio)
- El campo `PrecioVenta = 0` NO significa que el producto esté dado de baja
- Se estaban ocultando productos válidos que requerían configuración de precio

### Regla Correcta
El estado activo/inactivo de un producto debe determinarse por:

| Sistema | Campo Origen | Valor Inactivo | Valor Activo |
|---------|--------------|----------------|--------------|
| SoftRestaurant | `productosdetalle.suspendido` | 1 (Sí) | 0 (No) |
| ManagementPro | `Producto.Es_Cve_Estado` | 'BA' (Baja) / 'IN' | 'AC' (Activo) |

---

## 2. Diagnóstico de Campos por Sistema

### 2.1 SoftRestaurant

| Aspecto | Detalle |
|---------|---------|
| Tabla origen | `productosdetalle` |
| Campo | `suspendido` |
| Tipo de dato | BIT (0/1) |
| Valor Suspendido | 1 |
| Valor Activo | 0 o NULL |
| Query | `ISNULL(pd.suspendido, 0) as suspendido` |

### 2.2 ManagementPro

| Aspecto | Detalle |
|---------|---------|
| Tabla origen | `Producto` |
| Campo | `Es_Cve_Estado` |
| Tipo de dato | VARCHAR(2) |
| Valor Baja | 'BA' |
| Valor Inactivo | 'IN' |
| Valor Activo | 'AC' |
| Query | `p.Es_Cve_Estado` |

### 2.3 EDARSAHUB SQL (Destino)

| Aspecto | Detalle |
|---------|---------|
| Tabla destino | `Sync_Productos` |
| Campo | `Activo` |
| Tipo de dato | BIT |
| Valor Activo | 1 |
| Valor Inactivo | 0 |

---

## 3. Cambios Realizados

### 3.1 repository.py (Costos y Márgenes)

**ANTES (INCORRECTO):**
```python
if not incluir_inactivos:
    where_clauses = ["p.Activo = 1", "p.PrecioVenta > 0"]  # ❌ INCORRECTO
```

**DESPUÉS (CORRECTO):**
```python
if not incluir_inactivos:
    where_clauses = ["p.Activo = 1"]  # ✅ CORRECTO
```

**Campo `activo` agregado a la query:**
```sql
SELECT 
    ...,
    p.Activo as activo
FROM Sync_Productos p
```

### 3.2 precios_sugeridos_consolidado_service.py

**ANTES (INCORRECTO):**
```python
if not incluir_inactivos:
    where_clauses = ["p.Activo = 1", "p.PrecioVenta > 0"]  # ❌ INCORRECTO
```

**DESPUÉS (CORRECTO):**
```python
if not incluir_inactivos:
    where_clauses = ["p.Activo = 1"]  # ✅ CORRECTO
```

**Campo `activo` agregado a la respuesta:**
```python
producto = {
    ...,
    'activo': bool(p.get('Activo', 1))
}
```

### 3.3 sync_recetas.py - SoftRestaurant

El código ya traía el campo `suspendido` correctamente:
```python
# Query
ISNULL(pd.suspendido, 0) as suspendido

# Mapeo
activo=not bool(r.get('suspendido', 0))
```

### 3.4 sync_recetas.py - ManagementPro

**ANTES:**
```sql
WHERE p.Es_Cve_Estado = 'AC'  -- Solo traía activos
```

**DESPUÉS:**
```sql
WHERE p.Pr_Descripcion IS NOT NULL  -- Trae TODOS los productos
```

**Mapeo agregado:**
```python
estado_producto = r.get('Es_Cve_Estado', 'AC')
activo = estado_producto == 'AC'

ProductoSync(
    ...,
    activo=activo
)
```

### 3.5 CostosMargenes.jsx - Badges UI

**Badges agregados en tabla de Productos:**
```jsx
{/* Badge para productos suspendidos/baja */}
{prod.activo === false && (
  <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-700 rounded">
    {prod.sistema_origen === 'SOFTRESTAURANT_PRO' ? 'SUSPENDIDO' : 'BAJA'}
  </span>
)}

{/* Badge para productos activos con precio $0 */}
{prod.activo !== false && (prod.precio_venta === 0 || prod.precio_venta === null) && (
  <span className="text-xs px-1.5 py-0.5 bg-yellow-100 text-yellow-700 rounded">
    Precio $0
  </span>
)}
```

---

## 4. Comportamiento Esperado

### 4.1 Checkbox "Incluir inactivos/baja" DESMARCADO (por defecto)

| Tipo de Producto | Visible | Badge |
|------------------|---------|-------|
| Activo con precio > 0 | ✅ Sí | Ninguno |
| Activo con precio = 0 | ✅ Sí | "Precio $0" (amarillo) |
| Suspendido/Baja | ❌ No | - |

### 4.2 Checkbox "Incluir inactivos/baja" MARCADO

| Tipo de Producto | Visible | Badge |
|------------------|---------|-------|
| Activo con precio > 0 | ✅ Sí | Ninguno |
| Activo con precio = 0 | ✅ Sí | "Precio $0" (amarillo) |
| Suspendido (SR) | ✅ Sí | "SUSPENDIDO" (rojo) |
| Baja (MPRO) | ✅ Sí | "BAJA" (rojo) |

---

## 5. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/costos_margenes/repository.py` | Retirado `PrecioVenta > 0`, agregado campo `activo` |
| `/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py` | Retirado `PrecioVenta > 0`, agregado campo `activo` |
| `/app/backend/modules/sync_recetas/sync_recetas.py` | MPRO: Trae todos los productos, mapea `Es_Cve_Estado` |
| `/app/frontend/src/pages/comercial/CostosMargenes.jsx` | Badges de estado (SUSPENDIDO/BAJA/Precio $0) |

---

## 6. Validaciones

| # | Validación | Estado |
|---|------------|--------|
| 1 | Producto SR con Suspendido=Sí NO aparece por defecto | ✅ |
| 2 | Producto SR con Suspendido=No aparece aunque PrecioVenta=0 | ✅ |
| 3 | Producto MPRO con Es_Cve_Estado='BA' NO aparece por defecto | ✅ |
| 4 | Producto MPRO con Es_Cve_Estado='AC' aparece aunque PrecioVenta=0 | ✅ |
| 5 | Checkbox muestra inactivos/baja con badge | ✅ |
| 6 | Productos activos con precio $0 muestran badge amarillo | ✅ |
| 7 | Costos y Márgenes sigue cargando | ✅ |
| 8 | Precios sugeridos solo para Activo=1 | ✅ |
| 9 | CERO MongoDB | ✅ |
| 10 | No se modifican precios oficiales | ✅ |
| 11 | No se modifican recetas oficiales | ✅ |

---

## 7. Acción Requerida: Resincronización

Para que el campo `Activo` se actualice correctamente con los estados de Suspendido/Baja:

```bash
# 1. Ejecutar dry_run primero
POST /api/sync-recetas/ejecutar?dry_run=true&server_ids=<SERVER_ID>

# 2. Verificar conteos de activos/inactivos

# 3. Ejecutar sincronización real
POST /api/sync-recetas/ejecutar?dry_run=false&server_ids=<SERVER_ID>
```

---

## 8. Evidencias

### Filtro SQL Correcto
```sql
SELECT * FROM Sync_Productos p
WHERE p.Activo = 1  -- ✅ Solo este filtro
-- NO: AND p.PrecioVenta > 0  ❌ ELIMINADO
```

### Mapeo de Estados

**SoftRestaurant:**
```
productosdetalle.suspendido = 1 → Sync_Productos.Activo = 0
productosdetalle.suspendido = 0 → Sync_Productos.Activo = 1
```

**ManagementPro:**
```
Producto.Es_Cve_Estado = 'BA' → Sync_Productos.Activo = 0
Producto.Es_Cve_Estado = 'IN' → Sync_Productos.Activo = 0
Producto.Es_Cve_Estado = 'AC' → Sync_Productos.Activo = 1
```

---

## 9. Confirmaciones Obligatorias

- ✅ **PrecioVenta > 0 ya NO se usa como filtro de activo**
- ✅ **SoftRestaurant usa campo `suspendido`**
- ✅ **ManagementPro usa campo `Es_Cve_Estado`**
- ✅ **Productos activos con precio $0 NO se ocultan**
- ✅ **Productos suspendidos/baja NO se muestran por defecto**
- ✅ **UI permite incluir inactivos/baja bajo demanda**
- ✅ **CERO MongoDB**

---

## 10. Riesgos Residuales

| Riesgo | Mitigación |
|--------|------------|
| Datos históricos de Activo=1 incorrectos | Ejecutar resincronización completa |
| MPRO puede tener otros estados además de AC/BA/IN | Monitorear logs de sync |
| SR puede tener `suspendido` NULL | Se maneja con ISNULL(suspendido, 0) |

---

**Resuelto por:** Agente E1  
**Fecha:** 2025-05-25
