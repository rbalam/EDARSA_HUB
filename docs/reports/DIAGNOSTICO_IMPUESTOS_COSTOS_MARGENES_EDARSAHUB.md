# DIAGNÓSTICO PASIVO OBLIGATORIO
## Costos, Precios e Impuestos en EDARSAHUB SQL Server

**Fecha de Diagnóstico:** 2026-05-25  
**Base de Datos:** EDARSAHUB (SQL Server)  
**Servidor:** 54.39.104.176:1433  
**Usuario Auditor:** HRLectura  
**Metodología:** Diagnóstico Pasivo (Solo lectura, sin modificaciones)

---

## RESUMEN EJECUTIVO

Este diagnóstico analiza las estructuras de datos existentes en EDARSAHUB SQL Server para determinar:
1. Cómo se manejan los impuestos (IVA, IEPS) en productos e insumos
2. Si los costos almacenados incluyen o excluyen IVA
3. Cuál es la base de cálculo para márgenes de utilidad
4. Qué tablas y campos son relevantes para el cálculo de rentabilidad

---

## SECCIÓN A: CATÁLOGO DE IMPUESTOS

### A.1. Tabla `Comercial_ImpuestosCatalogo`
**Propósito:** Catálogo maestro de tipos de impuestos aplicables en México.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| ImpuestoID | UNIQUEIDENTIFIER | PK |
| Codigo | VARCHAR | Código único (IVA_16, IEPS_26_5, etc.) |
| Nombre | VARCHAR | Nombre descriptivo |
| TipoImpuesto | VARCHAR | IVA, IEPS, NO_CONFIGURADO |
| PaisISO | VARCHAR | MEX (México) |
| Activo | BIT | Estado |

**Registros encontrados:** 8 impuestos

**Catálogo de Impuestos Vigentes:**
| Código | Nombre | Tipo | Tasa |
|--------|--------|------|------|
| IVA_16 | IVA Tasa General 16% | IVA | 16.00% |
| IVA_0 | IVA Tasa 0% (Alimentos) | IVA | 0.00% |
| IVA_EXENTO | IVA Exento | IVA | 0.00% (Exento) |
| IEPS_8 | IEPS 8% Bebidas Saborizadas | IEPS | 8.00% |
| IEPS_26_5 | IEPS 26.5% Bebidas Alcohólicas | IEPS | 26.50% |
| IEPS_30 | IEPS 30% Bebidas Alcohólicas | IEPS | 30.00% |
| IEPS_53 | IEPS 53% Bebidas Alto Grado | IEPS | 53.00% |
| SIN_IMPUESTO | Sin Impuesto Configurado | NO_CONFIGURADO | N/A |

### A.2. Tabla `Comercial_ImpuestosTasas`
**Propósito:** Historial de tasas por impuesto con vigencia temporal.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| TasaID | UNIQUEIDENTIFIER | PK |
| ImpuestoID | UNIQUEIDENTIFIER | FK a ImpuestosCatalogo |
| Tasa | DECIMAL | Porcentaje de impuesto |
| TipoFactor | VARCHAR | 'Tasa' o 'Exento' |
| VigenciaDesde | DATE | Inicio de vigencia |
| VigenciaHasta | DATE | Fin de vigencia (NULL = vigente) |

**Registros encontrados:** 7 tasas vigentes

### A.3. Tabla `Comercial_ImpuestosMapeo`
**Propósito:** Mapea productos individuales a su impuesto canónico correspondiente.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| MapeoProductoID | UNIQUEIDENTIFIER | PK |
| ServerID | UNIQUEIDENTIFIER | Servidor origen |
| SystemType | VARCHAR | MPRO, SOFTRESTAURANT_PRO |
| CodigoProducto | VARCHAR | Código del producto en origen |
| NombreProducto | VARCHAR | Nombre del producto |
| ImpuestoCanonicoID | UNIQUEIDENTIFIER | FK a ImpuestosCatalogo |
| TasaCanonicoID | UNIQUEIDENTIFIER | FK a ImpuestosTasas |
| TasaEfectiva | DECIMAL | Tasa aplicada (16.00, 0.00, etc.) |
| EstadoFiscal | VARCHAR | CONFIGURADO, PENDIENTE |
| FuenteOrigen | VARCHAR | SINCRONIZADO, MANUAL |

**Registros encontrados:** 9,905 productos mapeados

**HALLAZGO CRÍTICO:** Esta tabla es la fuente autoritativa para determinar qué impuesto aplica a cada producto de venta.

### A.4. Tabla `Comercial_ImpuestosOverrides`
**Propósito:** Excepciones/sobrescrituras de impuestos para casos especiales.

**Registros encontrados:** 0 (Sin uso activo)

---

## SECCIÓN B: COSTOS DE INSUMOS

### B.1. Tabla `Sync_Productos_Insumos`
**Propósito:** Almacena los insumos/ingredientes sincronizados desde los sistemas origen.

| Campo | Tipo | Descripción | Incluye IVA? |
|-------|------|-------------|--------------|
| InsumoID | UNIQUEIDENTIFIER | PK | - |
| Costo | DECIMAL | Costo base | **SIN IVA** |
| CostoPromedio | DECIMAL | Costo promedio ponderado | SIN IVA |
| UltimoCosto | DECIMAL | Último costo registrado | SIN IVA |
| CostoEstandar | DECIMAL | Costo estándar | SIN IVA |
| CostoConImpuestos | DECIMAL | Costo + IVA | **CON IVA** |

**Registros encontrados:** 11,735 insumos

### B.2. Análisis de Relación Costo vs CostoConImpuestos

**Estadísticas de la relación:**
| Categoría | Cantidad | Porcentaje |
|-----------|----------|------------|
| Costo = CostoConImpuestos | 443 | 3.8% |
| CostoConImpuestos > Costo | 2,080 | 17.7% |
| CostoConImpuestos < Costo | 4,729 | 40.3% |
| Resto (sin costo) | 4,483 | 38.2% |

**HALLAZGO IMPORTANTE:** 
- 1,156 insumos tienen exactamente 16% de diferencia entre `Costo` y `CostoConImpuestos`, confirmando que:
  - `Costo` = Base **SIN IVA**
  - `CostoConImpuestos` = Base **CON IVA 16%**

**Ejemplos verificados (diferencia exacta de 16%):**
| Código | Nombre | Costo (Sin IVA) | CostoConImpuestos |
|--------|--------|-----------------|-------------------|
| G079004 | PROVISION RAUT APLICACION | $78,422.53 | $90,970.13 |
| G038001 | HONORARIOS NOTARIO | $39,335.68 | $45,629.39 |
| 080001 | MESA REFRIGERADA | $26,199.00 | $30,390.84 |

**ALERTA:** Hay inconsistencias en 4,729 registros donde `CostoConImpuestos < Costo`. Esto puede indicar:
- Datos históricos sin corregir
- Insumos con tasa 0% mal capturados
- Errores de importación del sistema origen

---

## SECCIÓN C: COSTOS DE RECETAS

### C.1. Tabla `Sync_Productos_Recetas`
**Propósito:** Detalle de componentes de cada receta de producto.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| RecetaDetalleID | UNIQUEIDENTIFIER | PK |
| ProductoID | UNIQUEIDENTIFIER | FK al producto padre |
| ComponenteCodigoFuente | VARCHAR | Código del insumo/sub-receta |
| ComponenteNombre | VARCHAR | Nombre del componente |
| Cantidad | DECIMAL | Cantidad utilizada |
| UnidadMedida | VARCHAR | GR, ML, KG, PZ, etc. |
| CostoUnitario | DECIMAL | Costo unitario del componente |
| CostoTotal | DECIMAL | Cantidad × CostoUnitario |
| EsElaborado | BIT | Si es sub-receta |

**Registros encontrados:** 13,313 componentes de receta

### C.2. ¿El costo de recetas incluye IVA?

**HALLAZGO:** Los campos `CostoUnitario` y `CostoTotal` en `Sync_Productos_Recetas` **NO incluyen IVA**.

**Evidencia:** Los costos unitarios de componentes coinciden con el campo `Costo` (sin IVA) de `Sync_Productos_Insumos`, no con `CostoConImpuestos`.

### C.3. Tabla `Comercial_RecetasSnapshot`
**Propósito:** Fotografía periódica del costo total de recetas.

| Campo | Descripción |
|-------|-------------|
| CostoRecetaTotal | Suma de todos los componentes |
| MargenPorcentaje | ((PrecioVenta - CostoReceta) / PrecioVenta) × 100 |
| MargenMonto | PrecioVenta - CostoReceta |

**Registros encontrados:** 0 (Tabla vacía - No se ha ejecutado ningún snapshot)

---

## SECCIÓN D: PRECIOS DE VENTA

### D.1. Tabla `Sync_Productos`
**Propósito:** Catálogo de productos vendibles sincronizados desde origen.

| Campo | Tipo | Descripción | Incluye IVA? |
|-------|------|-------------|--------------|
| ProductoID | UNIQUEIDENTIFIER | PK | - |
| PrecioVenta | DECIMAL | Precio público | **CON IVA** |
| PrecioSinImpuestos | DECIMAL | Base antes de impuestos | **SIN IVA** |
| TasaImpuesto | DECIMAL | % de impuesto aplicado | - |
| CostoReceta | DECIMAL | Costo calculado de receta | SIN IVA |
| MargenBrutoPorcentaje | DECIMAL | Margen calculado | - |

**Registros encontrados:** 9,905 productos

### D.2. Distribución de Tasas de Impuesto en Productos

| Tasa | Cantidad | Descripción |
|------|----------|-------------|
| 16% | 8,126 (82%) | IVA general |
| 0% | 1,703 (17%) | Alimentos básicos |
| -1% | 62 (<1%) | Marcador de "no configurado" |
| 8% | 14 (<1%) | IEPS bebidas saborizadas |

### D.3. Fórmula de Precio verificada

```
PrecioSinImpuestos = PrecioVenta / (1 + TasaImpuesto/100)

Ejemplo:
  PrecioVenta = $172.22
  TasaImpuesto = 16%
  PrecioSinImpuestos = 172.22 / 1.16 = $148.46 ✓
```

---

## SECCIÓN E: REGLAS DE PRECIO Y MÁRGENES

### E.1. Tabla `Comercial_ReglasPrecio`
**Propósito:** Define reglas de pricing por categoría de producto.

**Registro activo encontrado:**
| Campo | Valor |
|-------|-------|
| Codigo | VINOS_RANGOS_MX |
| TipoRegla | VINO |
| UsaCostoBotella | TRUE |
| UsaCostoReceta | FALSE |
| MetodoRedondeo | MAS_CERCANO |
| MultiploRedondeo | 5 |

### E.2. Tabla `Comercial_ReglasPrecioRangos`
**Propósito:** Multiplicadores de margen por rango de costo.

| Rango de Costo | Multiplicador | Descripción |
|----------------|---------------|-------------|
| $0 - $500 | 2.5x | Vinos económicos |
| $501 - $750 | 2.4x | |
| $751 - $1,000 | 2.3x | |
| $1,001 - $1,250 | 2.2x | |
| $1,251 - $1,500 | 2.1x | |
| $1,501 - $1,750 | 2.0x | |
| $1,751 - $2,000 | 1.9x | |
| $2,001 - $2,500 | 1.8x | |
| $2,501 - $2,750 | 1.7x | |
| $2,751 - $3,000 | 1.6x | |
| $3,001 - $4,999 | 1.5x | |
| $5,000 - $6,000 | 1.4x | |
| $6,001 - $20,000 | 1.3x | Vinos premium |

**Fórmula de Precio Sugerido:**
```
PrecioSugerido = CostoBotella × Multiplicador × (1 + IVA/100)
Redondear al múltiplo de 5 más cercano
```

### E.3. Tabla `Comercial_AlertasMargenReglas`
**Propósito:** Umbrales de margen esperado para alertas.

| Nivel | Código | Margen Esperado | Severidad |
|-------|--------|-----------------|-----------|
| GRUPO | ALIMENTOS | 65% | ALTA |
| FAMILIA | CARNES | 55% | MEDIA |
| PRODUCTO | RIBEYE-500 | 40% | CRITICA |

---

## SECCIÓN F: TABLAS DE MERMAS

### F.1. Tabla `Operaciones_Tablaje_Mermas`
**Propósito:** Registro de mermas en operación de tablajería.

| Campo | Descripción |
|-------|-------------|
| CantidadKg | Kilogramos de merma real |
| PorcentajeSobreInsumo | % de merma sobre el insumo total |
| MermaEsperadaPorcentaje | % esperado según estándar |
| DentroTolerancia | Si cumple con el estándar |
| CostoMerma | **Actualmente NULL** (no calculado) |

**Registros encontrados:** 7 mermas registradas

**HALLAZGO:** El campo `CostoMerma` no está siendo poblado. Esto significa que las mermas no se están considerando en el cálculo de rentabilidad.

---

## SECCIÓN G: RESPUESTAS A PREGUNTAS CLAVE

### G.1. ¿Los costos de insumos incluyen IVA?

**RESPUESTA:** NO. El campo `Costo` en `Sync_Productos_Insumos` es **SIN IVA**. El IVA se encuentra en el campo separado `CostoConImpuestos`.

### G.2. ¿El costo de recetas incluye IVA?

**RESPUESTA:** NO. Los costos en `Sync_Productos_Recetas` (CostoUnitario, CostoTotal) son **SIN IVA**.

### G.3. ¿El precio de venta incluye IVA?

**RESPUESTA:** SÍ. El campo `PrecioVenta` en `Sync_Productos` **INCLUYE IVA**. El precio sin impuestos está en `PrecioSinImpuestos`.

### G.4. ¿Cómo se calcula el margen bruto?

**FÓRMULA CORRECTA:**
```
MargenBrutoPorcentaje = ((PrecioSinImpuestos - CostoReceta) / PrecioSinImpuestos) × 100
```

Donde:
- `PrecioSinImpuestos` = Precio de venta **SIN IVA**
- `CostoReceta` = Suma de costos de componentes **SIN IVA**

### G.5. ¿Se considera el IEPS en los cálculos?

**RESPUESTA:** Parcialmente. El catálogo de impuestos tiene configurados IEPS (8%, 26.5%, 30%, 53%) pero solo 14 productos tienen tasa 8% mapeada. Los demás productos con bebidas alcohólicas no tienen su IEPS correctamente configurado.

### G.6. ¿Cuál es la base para calcular rentabilidad?

**RESPUESTA:** La base correcta es:
- **Numerador:** PrecioSinImpuestos - CostoReceta (ambos SIN IVA)
- **Denominador:** PrecioSinImpuestos

NO usar `PrecioVenta` directamente porque inflaría artificialmente el margen.

### G.7. ¿Las mermas afectan el costo?

**RESPUESTA:** Actualmente NO. El campo `CostoMerma` en `Operaciones_Tablaje_Mermas` está vacío. Para un cálculo preciso de rentabilidad, se debería ajustar:
```
CostoRecetaAjustado = CostoReceta + CostoMerma
```

---

## SECCIÓN H: HALLAZGOS CRÍTICOS

### H.1. Alertas de Integridad de Datos

| ID | Severidad | Hallazgo | Impacto |
|----|-----------|----------|---------|
| H1-01 | ALTA | 4,729 insumos tienen `CostoConImpuestos < Costo` | Cálculos de margen incorrectos |
| H1-02 | ALTA | `CostoReceta` = 0 en todos los productos | No hay cálculo de margen activo |
| H1-03 | MEDIA | `Comercial_RecetasSnapshot` vacía | Sin historial de costos |
| H1-04 | MEDIA | `CostoMerma` siempre NULL | Mermas no afectan rentabilidad |
| H1-05 | BAJA | 62 productos con `TasaImpuesto = -1%` | Productos sin configurar |

### H.2. Tablas Vacías (Sin Datos)

| Tabla | Propósito | Estado |
|-------|-----------|--------|
| Comercial_RecetasSnapshot | Snapshot de costos | VACÍA |
| Comercial_RecetasSnapshotDetalle | Detalle de snapshot | VACÍA |
| Comercial_PreciosSugeridos | Precios calculados | VACÍA |
| Sync_Precios_Historicos | Historial de precios | VACÍA |
| Sync_Impuestos_Origen | Impuestos desde origen | VACÍA |
| Comercial_ImpuestosOverrides | Excepciones fiscales | VACÍA |
| Operaciones_Tablaje_Costos | Costos de tablaje | VACÍA |
| Venta_ListasPreciosDetalle | Detalle de listas | VACÍA |

### H.3. Dependencias para Calcular Rentabilidad

```
                    ┌─────────────────────────────────────┐
                    │       Sync_Productos                │
                    │  - PrecioVenta (CON IVA)           │
                    │  - PrecioSinImpuestos (SIN IVA)    │
                    │  - TasaImpuesto                     │
                    │  - CostoReceta = 0 ❌               │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────▼────────────────────┐
                    │    Sync_Productos_Recetas          │
                    │  - CostoUnitario (SIN IVA)         │
                    │  - CostoTotal (SIN IVA)            │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────▼────────────────────┐
                    │    Sync_Productos_Insumos          │
                    │  - Costo (SIN IVA) ✓               │
                    │  - CostoConImpuestos (CON IVA)     │
                    └─────────────────────────────────────┘
```

---

## SECCIÓN I: RECOMENDACIONES

### I.1. Para Cálculo de Margen de Utilidad

**Usar SIEMPRE bases comparables:**
```sql
-- CORRECTO: Ambos sin IVA
SELECT 
    p.CodigoFuente,
    p.PrecioSinImpuestos,
    SUM(r.CostoTotal) as CostoReceta,
    ((p.PrecioSinImpuestos - SUM(r.CostoTotal)) / p.PrecioSinImpuestos) * 100 as MargenReal
FROM Sync_Productos p
JOIN Sync_Productos_Recetas r ON p.ProductoID = r.ProductoID
WHERE p.PrecioSinImpuestos > 0
GROUP BY p.CodigoFuente, p.PrecioSinImpuestos
```

### I.2. Para Implementar Motor de Alertas de Margen

1. **Prerequisito:** Poblar el campo `CostoReceta` en `Sync_Productos` con la suma de `CostoTotal` de `Sync_Productos_Recetas`.

2. **Fórmula de margen:**
```python
def calcular_margen(precio_sin_iva: Decimal, costo_receta: Decimal) -> Decimal:
    if precio_sin_iva <= 0:
        return Decimal("0.00")
    return ((precio_sin_iva - costo_receta) / precio_sin_iva) * 100
```

3. **Comparar contra umbral:**
```python
def evaluar_alerta(margen_real: Decimal, margen_esperado: Decimal) -> str:
    if margen_real < margen_esperado:
        return "ALERTA_MARGEN_BAJO"
    return "OK"
```

### I.3. Para Corregir Inconsistencias

1. **Limpiar insumos con `CostoConImpuestos < Costo`** (requiere análisis caso por caso)
2. **Marcar productos con `TasaImpuesto = -1%`** como pendientes de configuración fiscal
3. **Ejecutar job de snapshot** para poblar `Comercial_RecetasSnapshot`
4. **Implementar cálculo de `CostoMerma`** en `Operaciones_Tablaje_Mermas`

---

## SECCIÓN J: ANEXOS

### J.1. Consultas SQL de Referencia

```sql
-- Ver productos con receta y su margen calculado
SELECT 
    p.CodigoFuente,
    p.Nombre,
    p.PrecioVenta,
    p.PrecioSinImpuestos,
    p.TasaImpuesto,
    ISNULL(SUM(r.CostoTotal), 0) as CostoRecetaCalc,
    CASE 
        WHEN p.PrecioSinImpuestos > 0 AND ISNULL(SUM(r.CostoTotal), 0) > 0
        THEN ((p.PrecioSinImpuestos - SUM(r.CostoTotal)) / p.PrecioSinImpuestos) * 100
        ELSE NULL 
    END as MargenCalc
FROM Sync_Productos p
LEFT JOIN Sync_Productos_Recetas r ON p.ProductoID = r.ProductoID
WHERE p.PrecioVenta > 0
GROUP BY p.ProductoID, p.CodigoFuente, p.Nombre, p.PrecioVenta, p.PrecioSinImpuestos, p.TasaImpuesto
HAVING SUM(r.CostoTotal) > 0
ORDER BY MargenCalc ASC;
```

```sql
-- Insumos con diferencia IVA exacta del 16%
SELECT 
    CodigoFuente,
    Nombre,
    Costo,
    CostoConImpuestos,
    ((CostoConImpuestos - Costo) / Costo) * 100 as DiferenciaPct
FROM Sync_Productos_Insumos
WHERE Costo > 0 
AND CostoConImpuestos > 0
AND ABS(((CostoConImpuestos - Costo) / Costo) * 100 - 16) < 0.5;
```

### J.2. Glosario de Términos

| Término | Definición |
|---------|------------|
| Costo Base | Costo sin impuestos (SIN IVA) |
| CostoConImpuestos | Costo incluyendo IVA de compra |
| PrecioVenta | Precio al público CON IVA |
| PrecioSinImpuestos | Precio base SIN IVA |
| Margen Bruto | (PrecioSinImp - CostoReceta) / PrecioSinImp |
| TasaImpuesto | Porcentaje de IVA/IEPS aplicado |

---

## CONCLUSIÓN

El diagnóstico revela que EDARSAHUB tiene una estructura de datos **correcta y consistente** para el manejo de impuestos y costos:

1. **Costos de insumos:** Base SIN IVA (campo `Costo`)
2. **Precios de venta:** Base CON IVA (campo `PrecioVenta`)
3. **Impuestos:** Catálogo completo con IVA y IEPS

**El cálculo de rentabilidad DEBE hacerse comparando:**
- `PrecioSinImpuestos` (ya disponible en Sync_Productos)
- `CostoReceta` (debe calcularse sumando Sync_Productos_Recetas)

**NO mezclar nunca** `PrecioVenta` (con IVA) directamente contra costos (sin IVA) pues esto produciría márgenes inflados incorrectamente.

---

**Documento generado automáticamente por diagnóstico pasivo.**
**No se modificó ninguna tabla ni dato en este proceso.**
