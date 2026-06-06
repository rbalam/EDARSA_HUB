# FASE 1C-3G-B: Diagnóstico y Corrección de Impuestos MPRO

**Fecha:** 2025-12-XX  
**Estado:** COMPLETADO  
**Autor:** Agente E1 (Arquitecto Senior ERP)

---

## 1. RESUMEN EJECUTIVO

Se completó el diagnóstico y corrección del sincronizador de productos MPRO para homologar correctamente las tasas de impuesto desde ManagementPro hacia EDARSAHUB SQL.

### Resultado Final:
- **ANTES:** Todos los productos MPRO se sincronizaban con `TasaImpuesto = 0%` por defecto (ERROR)
- **DESPUÉS:** Productos sincronizados con tasa real desde tabla `Impuesto` de MPRO

---

## 2. CAUSA RAÍZ DEL PROBLEMA

### 2.1 Diagnóstico Inicial
La función `_obtener_productos_mpro()` en `/app/backend/modules/sync_recetas/sync_recetas.py` NO consultaba ninguna tabla de impuestos de MPRO.

```python
# CÓDIGO ANTERIOR (INCORRECTO)
query = """
SELECT p.Pr_Cve_Producto, p.Pr_Descripcion, ...
       pp.Pp_Precio_1 as Precio
FROM Producto p
LEFT JOIN Producto_Precio pp ON p.Pr_Cve_Producto = pp.Pr_Cve_Producto
...
"""
# El modelo ProductoSync.tasa_impuesto quedaba con default Decimal('0')
```

### 2.2 Estructura Fiscal Real de MPRO
Se descubrió que MPRO almacena impuestos en una relación N:M:

```
Producto ──┬── Impuesto_Grupo_Impuesto ──┬── Impuesto
           │   (Pr_Cve_Producto)         │   (Im_Cve_Impuesto)
           │   (Im_Cve_Impuesto)         │   (Im_Tasa)
           └───────────────────────────────┘
```

### 2.3 Complejidad del Mapeo
- Un producto puede tener **MÚLTIPLES impuestos** (IVA + IEPS, IVA + Retención, etc.)
- Para VENTAS, se debe usar el impuesto **IVA COBRADO** (código '0013')
- Las **retenciones** (tasas negativas) NO aplican para cálculo de precio de venta

---

## 3. TABLAS MPRO REVISADAS

| Tabla | Propósito | Campos Relevantes |
|-------|-----------|-------------------|
| `Producto` | Catálogo de productos | `Pr_Cve_Producto`, `Pr_Descripcion` |
| `Producto_Precio` | Precios de productos | `Pp_Precio_1` |
| `Impuesto` | Catálogo de impuestos | `Im_Cve_Impuesto`, `Im_Tasa`, `Im_Tipo_Impuesto`, `Im_Tipo_Factor` |
| `Impuesto_Grupo_Impuesto` | Relación Producto-Impuesto | `Pr_Cve_Producto`, `Im_Cve_Impuesto` |
| `Grupo_Impuesto` | Grupos de impuestos | `Gi_Cve_Grupo_Impuesto` |

---

## 4. IMPUESTOS CONFIGURADOS EN MPRO

| Código | Descripción | Tasa | Tipo | Uso |
|--------|-------------|------|------|-----|
| 0013 | IVA COBRADO 16% | 16.0% | IVA | Ventas nacionales |
| 0011 | IVA PAGADO 16% | 16.0% | IVA | Compras nacionales |
| 0021 | IVA PAGADO 0% | 0.0% | IVA (Tasa) | Alimentos tasa cero |
| 0022 | IVA PAGADO EXENTO | 0.0% | IVA (Exento) | Productos exentos |
| 0017 | IEPS 26.5% | 26.5% | IEPS | Bebidas alcohólicas |
| 0018 | IEPS 30% | 30.0% | IEPS | Bebidas alcohólicas |
| 0019 | IEPS 53% | 53.0% | IEPS | Bebidas alcohólicas alto grado |
| 0025 | IEPS 8% | 8.0% | IEPS | Bebidas saborizadas |

---

## 5. ESTRATEGIA DE HOMOLOGACIÓN

### 5.1 Priorización de Impuestos
Cuando un producto tiene múltiples impuestos, se usa la siguiente prioridad:

1. **IVA COBRADO 16%** (código '0013') - Prioridad máxima para ventas
2. **Otro IVA positivo** (>0%)
3. **IEPS positivo** (>0%)
4. **IVA Exento** (0%, Im_Tipo_Factor='Exento')
5. **IVA Tasa 0%** (0%, Im_Tipo_Factor='Tasa')

### 5.2 Manejo de Casos Especiales

| Caso | Tasa en BD | Comportamiento |
|------|------------|----------------|
| Producto con IVA 16% | 16.0 | Cálculo normal |
| Producto tasa 0% válida | 0.0 | Cálculo normal (alimentos) |
| Producto exento | 0.0 | Cálculo normal, marcado como exento |
| Producto SIN impuesto | -1 | **IMPUESTO_NO_CONFIGURADO** - Bloquea cálculo de precio |

---

## 6. CAMBIOS REALIZADOS

### 6.1 Archivo Modificado
`/app/backend/modules/sync_recetas/sync_recetas.py`

### 6.2 Función Corregida
`_obtener_productos_mpro()`

### 6.3 Query Implementada
```sql
WITH ImpuestosPriorizados AS (
    SELECT 
        p.Pr_Cve_Producto,
        i.Im_Cve_Impuesto,
        i.Im_Tasa,
        i.Im_Tipo_Factor,
        ROW_NUMBER() OVER (PARTITION BY p.Pr_Cve_Producto ORDER BY 
            CASE 
                WHEN i.Im_Cve_Impuesto = '0013' THEN 1  -- IVA COBRADO
                WHEN i.Im_Tipo_Impuesto = 'IVA' AND i.Im_Tasa > 0 THEN 2
                WHEN i.Im_Tipo_Impuesto = 'IEPS' AND i.Im_Tasa > 0 THEN 3
                WHEN i.Im_Tipo_Factor = 'Exento' THEN 4
                WHEN i.Im_Tasa = 0 THEN 5
                ELSE 99
            END
        ) as rn
    FROM Producto p
    LEFT JOIN Impuesto_Grupo_Impuesto igi ON p.Pr_Cve_Producto = igi.Pr_Cve_Producto
    LEFT JOIN Impuesto i ON igi.Im_Cve_Impuesto = i.Im_Cve_Impuesto
    WHERE p.Es_Cve_Estado = 'AC'
      AND (i.Im_Tasa >= 0 OR i.Im_Tasa IS NULL)  -- Excluir retenciones
)
SELECT p.*, ip.Im_Tasa, ip.Im_Tipo_Factor, ...
FROM Producto p
LEFT JOIN ImpuestosPriorizados ip ON p.Pr_Cve_Producto = ip.Pr_Cve_Producto AND ip.rn = 1
```

---

## 7. RESULTADO DRY-RUN

### 7.1 Estadísticas

| Categoría | Cantidad | Porcentaje |
|-----------|----------|------------|
| Total productos activos | 5,414 | 100% |
| Con tasa > 0 (IVA/IEPS) | 3,651 | 67.4% |
| Con tasa = 0 (tasa cero válida) | 1,701 | 31.4% |
| Sin impuesto configurado | 62 | 1.1% |

### 7.2 Validación
- ✅ NO se hardcodea 16%
- ✅ Tasas reales provienen de MPRO
- ✅ Tasa 0% solo cuando es fiscalmente válida
- ✅ Productos sin impuesto marcados como `IMPUESTO_NO_CONFIGURADO`
- ✅ Retenciones excluidas del cálculo de precio venta

---

## 8. REGLAS PARA CÁLCULO DE PRECIOS

### 8.1 Producto con Tasa Válida (≥ 0)
```
precio_sugerido = costo_receta * (1 + margen) * (1 + tasa_impuesto/100)
```

### 8.2 Producto con Tasa = -1 (NO_CONFIGURADO)
```
precio_sugerido = NULL
status = 'IMPUESTO_NO_CONFIGURADO'
mensaje = "Producto MPRO sin tasa de impuesto homologada"
// NO permitir solicitud de cambio de precio
```

---

## 9. VALIDACIONES CONFIRMADAS

| # | Validación | Estado |
|---|------------|--------|
| 1 | Tabla fiscal real identificada | ✅ |
| 2 | Relación producto-impuesto descubierta | ✅ |
| 3 | Causa del 0% confirmada | ✅ |
| 4 | No se hardcodea 16% | ✅ |
| 5 | 0% inválido marcado como -1 | ✅ |
| 6 | Arquitectura NO-LIVE respetada | ✅ |
| 7 | Sin uso de MongoDB | ✅ |
| 8 | Sin exposición de secretos | ✅ |

---

## 10. RIESGOS PENDIENTES

1. **62 productos sin impuesto**: Requieren configuración en MPRO o mapeo manual
2. **Precios negativos (-1)**: Algunos productos tienen precio -1, posible marcador especial de MPRO

---

## 11. RECOMENDACIONES PARA FASE 1C-3G-C

1. **Crear Modelo Canónico de Impuestos** en EDARSAHUB SQL:
   - `Comercial_ImpuestosCatalogo`: Catálogo maestro
   - `Comercial_ImpuestosTasas`: Tasas vigentes por período
   - `Sync_Impuestos_Origen`: Trazabilidad MPRO/SR

2. **Ejecutar SYNC REAL** cuando usuario autorice

3. **Crear UI de administración** para productos sin impuesto configurado

4. **Documentar los 62 productos** sin impuesto para revisión manual

---

## 12. CONEXIONES UTILIZADAS

| Sistema | Host | Base de Datos | Usuario |
|---------|------|---------------|---------|
| MPRO | <REDACTED_EDARSAHUB_SQL_HOST>:1433 | CENTRAL2020 | <REDACTED_EDARSAHUB_SQL_USER> |
| EDARSAHUB | <REDACTED_EDARSAHUB_SQL_HOST>:1433 | EDARSAHUB | <REDACTED_EDARSAHUB_SQL_USER> |

---

**FIN DEL REPORTE**
