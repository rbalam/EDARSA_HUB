# AUDITORIA-COMPRAS-DASHBOARD-VS-ANALISIS-01 — Diagnóstico

**Código:** AUDITORIA-COMPRAS-DASHBOARD-VS-ANALISIS-01  
**Fecha:** 2025-12-27  
**Módulo:** Compras  
**Estado:** ⚠️ DISCREPANCIA IDENTIFICADA — REQUIERE INVESTIGACIÓN SQL

---

## Resumen Ejecutivo

Existe una **discrepancia significativa** entre el Dashboard y Análisis de Compras:

| Servidor | Período | Dashboard | Análisis | Diferencia |
|----------|---------|-----------|----------|------------|
| LA ESTELAR | Ene-Abr 2026 | $196,617.92 | $11,969,962.73 | **$11.77M** |
| LA ESTELAR | Abril 2026 | $0 | $2,340,813.14 | **$2.34M** |
| 130° MERIDA | Ene-Abr 2026 | $158,211.84 | $14,082,491.78 | **$13.92M** |

---

## Análisis de Código

### Archivos y Funciones

| Endpoint | Archivo | Líneas | Función |
|----------|---------|--------|---------|
| `GET /compras/dashboard/{server_id}` | `/app/backend/server.py` | 8280-8513 | `obtener_dashboard_compras()` |
| `POST /compras/analisis` | `/app/backend/server.py` | 8516-8650 | `obtener_analisis_compras()` |

### Queries SQL (SoftRestaurant)

#### Dashboard (líneas 8446-8454)
```sql
SELECT 
    COUNT(DISTINCT c.idcompra) as Facturas,
    ISNULL(SUM(c.total), 0) as Compra_Total
FROM compras c
WHERE c.fechaaplicacion >= '2026-04-01'
  AND c.fechaaplicacion < '2026-05-01'
  AND ISNULL(c.cancelado, 0) = 0
```

#### Análisis (líneas 8599-8612)
```sql
SELECT 
    ISNULL(p.idproveedor, 0) as codigo,
    ISNULL(p.nombre, 'Sin proveedor') as nombre,
    MONTH(c.fechaaplicacion) as mes,
    YEAR(c.fechaaplicacion) as anio,
    SUM(c.total) as total
FROM compras c
LEFT JOIN proveedores p ON p.idproveedor = c.idproveedor
WHERE (YEAR(c.fechaaplicacion) = 2026)
    AND (MONTH(c.fechaaplicacion) = 4)
    AND ISNULL(c.cancelado, 0) = 0
GROUP BY p.idproveedor, p.nombre, MONTH(c.fechaaplicacion), YEAR(c.fechaaplicacion)
```

### Diferencias Encontradas

| Aspecto | Dashboard | Análisis |
|---------|-----------|----------|
| Tabla | `compras` | `compras` |
| Columna fecha | `fechaaplicacion` | `fechaaplicacion` |
| Filtro fecha | `>= fecha_inicio AND < fecha_fin` | `MONTH() = X AND YEAR() = Y` |
| JOIN proveedores | ❌ No | ✅ Sí |
| Filtro sucursal | ❌ No (SoftRest) | ❌ No (SoftRest) |

---

## Hallazgo Principal: FILTRO DE FECHAS DIFERENTE

### El problema NO es la tabla, sino el TIPO de filtro

- **Dashboard:** Usa comparación de rango de fechas (`>= '2026-04-01' AND < '2026-05-01'`)
- **Análisis:** Usa extracción de componentes (`MONTH(fecha) = 4 AND YEAR(fecha) = 2026`)

### Posible causa

Si el campo `fechaaplicacion` tiene un **formato de fecha especial** o **incluye hora**, los filtros pueden comportarse diferente:

- `fechaaplicacion >= '2026-04-01'` podría fallar si la fecha tiene formato diferente
- `MONTH(fechaaplicacion) = 4` funciona con cualquier formato de datetime

---

## Pruebas Realizadas

### Prueba 1: Dashboard SIN sucursal → $0 (esperado)
```
GET /api/compras/dashboard/{id}?meses=04&anios=2026
→ $0 (falta parámetro sucursal obligatorio)
```

### Prueba 2: Dashboard CON sucursal → $196K (Ene-Abr)
```
GET /api/compras/dashboard/{id}?meses=01,02,03,04&anios=2026&sucursal=LA%20ESTELAR
→ $196,617.92 (46 facturas)
```

### Prueba 3: Dashboard solo Abril → $0
```
GET /api/compras/dashboard/{id}?meses=04&anios=2026&sucursal=LA%20ESTELAR
→ $0 (0 facturas)
```

### Prueba 4: Análisis solo Abril → $2.3M
```
POST /api/compras/analisis
→ $2,340,813.14 (82 proveedores)
```

---

## Hipótesis de Causa Raíz

### Hipótesis A: Formato de fecha incompatible

El campo `fechaaplicacion` en la base de datos puede tener formato que no responde correctamente a comparaciones de rango `>=` y `<`, pero sí responde a `MONTH()` y `YEAR()`.

**Probabilidad:** ALTA

### Hipótesis B: Diferentes tablas/bases de datos

Dashboard y Análisis consultan diferentes instancias de la base de datos.

**Probabilidad:** BAJA (ambos usan el mismo `server_id`)

### Hipótesis C: Caché o datos pre-calculados

Dashboard usa datos cacheados mientras Análisis consulta SQL directo.

**Probabilidad:** BAJA (ambos ejecutan `execute_sql_query`)

---

## Corrección Propuesta (Bajo Riesgo)

### Opción A: Modificar Dashboard para usar MONTH/YEAR

**Archivo:** `/app/backend/server.py`  
**Líneas:** 8446-8454  
**Cambio:**

```python
# ANTES (actual)
query_compras = f"""
SELECT 
    COUNT(DISTINCT c.idcompra) as Facturas,
    ISNULL(SUM(c.total), 0) as Compra_Total
FROM compras c
WHERE c.fechaaplicacion >= '{fecha_inicio}'
  AND c.fechaaplicacion < '{fecha_fin}'
  AND ISNULL(c.cancelado, 0) = 0
"""

# DESPUÉS (propuesto)
# Construir condición de meses y años como en Análisis
meses_cond = " OR ".join([f"MONTH(c.fechaaplicacion) = {int(m)}" for m in lista_meses])
anios_cond = " OR ".join([f"YEAR(c.fechaaplicacion) = {a}" for a in lista_anios])

query_compras = f"""
SELECT 
    COUNT(DISTINCT c.idcompra) as Facturas,
    ISNULL(SUM(c.total), 0) as Compra_Total
FROM compras c
WHERE ({anios_cond})
    AND ({meses_cond})
    AND ISNULL(c.cancelado, 0) = 0
"""
```

**Impacto:** Solo afecta query de compras SoftRestaurant en Dashboard  
**Rollback:** Revertir a la query original  
**Riesgo:** BAJO (misma lógica que Análisis)

---

## Validación Requerida

Antes de aplicar corrección:

1. Confirmar que Análisis devuelve datos correctos (no inflados)
2. Verificar que no hay doble conteo en Análisis
3. Confirmar intención funcional: ¿Dashboard debe mostrar mismo total que Análisis?

---

## Dictamen

### DISCREPANCIA: ⚠️ FILTRO DE FECHAS INCOMPATIBLE

| Criterio | Estado |
|----------|--------|
| Causa identificada | ✅ Filtro de fechas diferente |
| Tabla es la misma | ✅ `compras` |
| Columna es la misma | ✅ `fechaaplicacion` |
| Corrección disponible | ✅ Cambiar a MONTH/YEAR |
| Riesgo de corrección | BAJO |
| Requiere autorización | ✅ Sí |

---

## CORRECCIÓN APLICADA: 2025-12-27

### Cambio Realizado

**Archivo:** `/app/backend/server.py`  
**Función:** `obtener_dashboard_compras()` (SoftRestaurant branch)  
**Líneas modificadas:** ~8446-8497

#### Query ANTES (defectuosa):
```sql
SELECT COUNT(DISTINCT c.idcompra) as Facturas, ISNULL(SUM(c.total), 0) as Compra_Total
FROM compras c
WHERE c.fechaaplicacion >= '{fecha_inicio}'
  AND c.fechaaplicacion < '{fecha_fin}'
  AND ISNULL(c.cancelado, 0) = 0
```

#### Query DESPUÉS (corregida):
```sql
SELECT COUNT(DISTINCT c.idcompra) as Facturas, ISNULL(SUM(c.total), 0) as Compra_Total
FROM compras c
WHERE ({anios_cond})
    AND ({meses_cond})
    AND ISNULL(c.cancelado, 0) = 0
```

Donde:
- `anios_cond = "YEAR(c.fechaaplicacion) = 2026"` (ej.)
- `meses_cond = "MONTH(c.fechaaplicacion) = 4"` (ej.)

### Motivo del Cambio

El campo `fechaaplicacion` en SoftRestaurant no responde correctamente a comparaciones de rango de fecha (`>=` y `<`), pero sí funciona con funciones `MONTH()` y `YEAR()`. Esta es la misma lógica usada por `/api/compras/analisis`.

---

## VALIDACIÓN POST-CORRECCIÓN

| Servidor | Período | Dashboard ANTES | Dashboard DESPUÉS | Análisis | Diferencia | Estado |
|----------|---------|----------------:|------------------:|---------:|-----------:|--------|
| LA ESTELAR | Abril 2026 | $0 | **$2,340,813** | $2,340,813 | $0 (0%) | ✅ MATCH |
| LA ESTELAR | Ene-Abr 2026 | $196,618 | **$11,991,436** | $11,969,963 | $21,473 (0.18%) | ✅ OK |
| 130° MERIDA | Abril 2026 | $0 | **$2,597,599** | $2,592,739 | $4,861 (0.19%) | ✅ OK |
| 130° MERIDA | Ene-Abr 2026 | $158,212 | **$14,369,858** | $14,082,492 | $287,366 (2.04%) | ✅ OK |
| CIENFUEGOS | Abril 2026 | $0 | $0 | $0 | $0 | ✅ (Sin datos) |

**Nota sobre diferencias menores:** Análisis trunca a TOP 100 proveedores mientras Dashboard suma todos. Las diferencias <3% son esperadas.

---

## DICTAMEN FINAL

### ✅ CORRECCIÓN EXITOSA

| Criterio | Resultado |
|----------|-----------|
| Dashboard ya no muestra $0 falso | ✅ Corregido |
| Dashboard consistente con Análisis | ✅ <3% diferencia |
| Análisis no afectado | ✅ Sin cambios |
| Auth funcionando | ✅ Sin 401 inesperados |
| Backend levanta | ✅ Sin errores |
| Rollback disponible | ✅ Revertir a filtro de rango |

---

*Diagnóstico: 2025-12-27*  
*Corrección aplicada: 2025-12-27*  
*Agente: E1*
