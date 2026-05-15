# FASE 2: Inventario de Consultas Hardcodeadas
## Análisis de catalogo_consultas.py

**Fecha:** 2026-05-15  
**Autor:** E1 Agent  
**Estado:** PREPARATORIO - SIN EJECUTAR DML

---

## 1. RESUMEN

Se detectaron **17 consultas** hardcodeadas en `/app/backend/catalogo/catalogo_consultas.py`.

| Sistema | Cantidad | Categorías |
|---------|----------|------------|
| SoftRestaurant | 12 | Ventas (7), Compras (3), Inventarios (1), Pagos (2) |
| MPRO | 5 | Ventas (4), Compras (2) |
| **TOTAL** | **17** | |

---

## 2. INVENTARIO COMPLETO

### 2.1 SoftRestaurant - Ventas (7 consultas)

| # | Código | Nombre | Parámetros | Riesgo | Clasificación |
|---|--------|--------|------------|--------|---------------|
| 1 | SR_VENTAS_DIA | Ventas del Día | fecha | 🟢 BAJO | SISTEMA |
| 2 | SR_VENTAS_PERIODO | Ventas por Período | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 3 | SR_VENTAS_POR_DIA | Ventas Desglosadas por Día | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 4 | SR_VENTAS_POR_HORA | Ventas por Hora | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 5 | SR_VENTAS_POR_MESERO | Ventas por Mesero | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 6 | SR_VENTAS_POR_PRODUCTO | Ventas por Producto | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 7 | SR_CORTESIAS | Cortesías y Descuentos | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 8 | SR_CANCELACIONES | Cancelaciones | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |

### 2.2 SoftRestaurant - Compras (3 consultas)

| # | Código | Nombre | Parámetros | Riesgo | Clasificación |
|---|--------|--------|------------|--------|---------------|
| 9 | SR_COMPRAS_PERIODO | Compras por Período | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 10 | SR_COMPRAS_POR_PROVEEDOR | Compras por Proveedor | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 11 | SR_COMPRAS_POR_PRODUCTO | Compras por Producto | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |

### 2.3 SoftRestaurant - Inventarios (1 consulta)

| # | Código | Nombre | Parámetros | Riesgo | Clasificación |
|---|--------|--------|------------|--------|---------------|
| 12 | SR_INVENTARIO_ACTUAL | Inventario Actual | almacen | 🟡 MEDIO | SISTEMA |

**Nota:** Usa `LIKE '%{almacen}%'` - Riesgo de SQL injection si almacén no se valida.

### 2.4 SoftRestaurant - Pagos (2 consultas)

| # | Código | Nombre | Parámetros | Riesgo | Clasificación |
|---|--------|--------|------------|--------|---------------|
| 13 | SR_FORMAS_PAGO | Formas de Pago | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 14 | SR_PROPINAS | Propinas | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |

### 2.5 MPRO - Ventas (4 consultas)

| # | Código | Nombre | Parámetros | Riesgo | Clasificación |
|---|--------|--------|------------|--------|---------------|
| 15 | MPRO_VENTAS_PERIODO | Ventas por Período | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 16 | MPRO_VENTAS_POR_DIA | Ventas por Día | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 17 | MPRO_VENTAS_POR_SUCURSAL | Ventas por Sucursal | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 18 | MPRO_VENTAS_POR_PRODUCTO | Ventas por Producto | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |

### 2.6 MPRO - Compras (2 consultas)

| # | Código | Nombre | Parámetros | Riesgo | Clasificación |
|---|--------|--------|------------|--------|---------------|
| 19 | MPRO_COMPRAS_PERIODO | Compras por Período | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |
| 20 | MPRO_COMPRAS_POR_PROVEEDOR | Compras por Proveedor | fecha_ini, fecha_fin | 🟢 BAJO | SISTEMA |

---

## 3. DETALLE POR CONSULTA

### SR_VENTAS_DIA
```
Código: SR_VENTAS_DIA
Nombre: Ventas del Día
Módulo: Ventas
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```
**SQL:**
```sql
SELECT 
    COUNT(DISTINCT cheques.folio) as Cheques,
    ISNULL(SUM(cheques.total), 0) as Venta_Total,
    ISNULL(SUM(cheques.nopersonas), 0) as PAX,
    ISNULL(AVG(cheques.total), 0) as Cheque_Promedio,
    ISNULL(AVG(CAST(cheques.nopersonas as float)), 0) as PAX_Promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(date, turnos.apertura) = '{fecha}'
  AND cheques.cancelado = 0
```

---

### SR_VENTAS_PERIODO
```
Código: SR_VENTAS_PERIODO
Nombre: Ventas por Período
Módulo: Ventas
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```
**SQL (resumido):**
```sql
SELECT COUNT(DISTINCT folio), SUM(total), SUM(nopersonas), AVG(total)
FROM cheques JOIN turnos ON...
WHERE apertura BETWEEN '{fecha_ini}' AND '{fecha_fin}'
```

---

### SR_VENTAS_POR_DIA
```
Código: SR_VENTAS_POR_DIA
Nombre: Ventas Desglosadas por Día
Módulo: Ventas
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### SR_VENTAS_POR_HORA
```
Código: SR_VENTAS_POR_HORA
Nombre: Ventas por Hora
Módulo: Ventas
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### SR_VENTAS_POR_MESERO
```
Código: SR_VENTAS_POR_MESERO
Nombre: Ventas por Mesero
Módulo: Ventas
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### SR_VENTAS_POR_PRODUCTO
```
Código: SR_VENTAS_POR_PRODUCTO
Nombre: Ventas por Producto
Módulo: Ventas
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
Nota: Usa TOP 50
```

---

### SR_CORTESIAS
```
Código: SR_CORTESIAS
Nombre: Cortesías y Descuentos
Módulo: Ventas
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### SR_CANCELACIONES
```
Código: SR_CANCELACIONES
Nombre: Cancelaciones
Módulo: Ventas
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### SR_COMPRAS_PERIODO
```
Código: SR_COMPRAS_PERIODO
Nombre: Compras por Período
Módulo: Compras
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### SR_COMPRAS_POR_PROVEEDOR
```
Código: SR_COMPRAS_POR_PROVEEDOR
Nombre: Compras por Proveedor
Módulo: Compras
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### SR_COMPRAS_POR_PRODUCTO
```
Código: SR_COMPRAS_POR_PRODUCTO
Nombre: Compras por Producto
Módulo: Compras
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
Nota: Usa TOP 50
```

---

### SR_INVENTARIO_ACTUAL
```
Código: SR_INVENTARIO_ACTUAL
Nombre: Inventario Actual
Módulo: Inventarios
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: almacen (STRING)
SoloLectura: Sí
EsSistema: Sí
Riesgo: MEDIO - Usa LIKE sin escape
```
**Mitigación recomendada:** Validar parámetro `almacen` con whitelist o escapar caracteres especiales.

---

### SR_FORMAS_PAGO
```
Código: SR_FORMAS_PAGO
Nombre: Formas de Pago
Módulo: Pagos
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### SR_PROPINAS
```
Código: SR_PROPINAS
Nombre: Propinas
Módulo: Pagos
Sistema: SoftRestaurant (SistemaTipoID = 1)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### MPRO_VENTAS_PERIODO
```
Código: MPRO_VENTAS_PERIODO
Nombre: Ventas por Período
Módulo: Ventas
Sistema: MPRO (SistemaTipoID = 2)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### MPRO_VENTAS_POR_DIA
```
Código: MPRO_VENTAS_POR_DIA
Nombre: Ventas por Día
Módulo: Ventas
Sistema: MPRO (SistemaTipoID = 2)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### MPRO_VENTAS_POR_SUCURSAL
```
Código: MPRO_VENTAS_POR_SUCURSAL
Nombre: Ventas por Sucursal
Módulo: Ventas
Sistema: MPRO (SistemaTipoID = 2)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### MPRO_VENTAS_POR_PRODUCTO
```
Código: MPRO_VENTAS_POR_PRODUCTO
Nombre: Ventas por Producto
Módulo: Ventas
Sistema: MPRO (SistemaTipoID = 2)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
Nota: Usa TOP 50
```

---

### MPRO_COMPRAS_PERIODO
```
Código: MPRO_COMPRAS_PERIODO
Nombre: Compras por Período
Módulo: Compras
Sistema: MPRO (SistemaTipoID = 2)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

### MPRO_COMPRAS_POR_PROVEEDOR
```
Código: MPRO_COMPRAS_POR_PROVEEDOR
Nombre: Compras por Proveedor
Módulo: Compras
Sistema: MPRO (SistemaTipoID = 2)
Parámetros: fecha_ini (DATE), fecha_fin (DATE)
SoloLectura: Sí
EsSistema: Sí
Riesgo: BAJO
```

---

## 4. MAPEO A SistemaTipoID

| Sistema | SistemaTipoID | Consultas |
|---------|---------------|-----------|
| SoftRestaurant | 1 | 12 |
| MPRO | 2 | 5 |

---

## 5. TIPOS DE PARÁMETROS

| Parámetro | Tipo | Consultas que lo usan |
|-----------|------|----------------------|
| fecha | DATE | SR_VENTAS_DIA |
| fecha_ini | DATE | 16 consultas |
| fecha_fin | DATE | 16 consultas |
| almacen | STRING | SR_INVENTARIO_ACTUAL |

---

## 6. RECOMENDACIONES DE MIGRACIÓN

| Prioridad | Acción | Consultas |
|-----------|--------|-----------|
| 🔴 ALTA | Migrar sin cambios | 16 |
| 🟡 MEDIA | Migrar + sanitizar parámetro | SR_INVENTARIO_ACTUAL |

---

## 7. CLASIFICACIÓN ConfigOrigen

Todas las consultas se migrarán con:
- `ConfigOrigen = 'LEGACY_PYTHON'`
- `EsSistema = 1`
- `EsPersonalizada = 0`
- `SoloLectura = 1`
- `PermiteEjecucionManual = 1`
- `Activo = 1`
- `Version = 1`

---

## 8. PRÓXIMO PASO

Ejecutar script DML en `/app/backend/sql/migrations/prepare_consultas_sql_catalogo_seed.sql` tras autorización.

---

*Documento generado automáticamente por E1 Agent*  
*Fecha: 2026-05-15*
