# FASE 1C-3G-E: Reglas de Precio por Rango para Productos Clasificados como Vino

**Fecha:** 2026-05-25  
**Actualizado:** 2026-05-25 (Corrección conceptual CostoBaseVino)  
**Estado:** COMPLETADO CON CORRECCIÓN CONCEPTUAL

---

## 1. RESUMEN EJECUTIVO

Se crearon las reglas de precio por rango para productos clasificados como vino. **La tabla de rangos determina el PRECIO DE VENTA SUGERIDO a partir del CostoBaseVino**, no calcula el costo del vino.

### Resultados Principales:
- **3 tablas** creadas con DDL idempotente
- **13 rangos** de margen configurados
- **1 gap** documentado ($4,000.01 - $4,999.99)
- **626 vinos** con precio calculado (procesando 1,512 total)
- **886 vinos** marcados como COSTO_BASE_NO_CONFIGURADO
- **0 vinos** con IMPUESTO_NO_CONFIGURADO

---

## 1.1 CORRECCIÓN CONCEPTUAL: CostoBaseVino vs CostoReceta

### Definición de CostoBaseVino
El `CostoBaseVino` es el costo consolidado confiable del producto que se usa como entrada para calcular el precio de venta sugerido. **NO es el precio de venta**, es el insumo para determinarlo.

### Cuándo se puede usar CostoReceta
- **SI** `CostoReceta > 0` y representa un costo consolidado confiable del producto.
- Para productos elaborados (platillos, cocteles), el `CostoReceta` puede ser la fuente principal.

### Cuándo NO se debe usar CostoReceta
- **Cuando `CostoReceta = 0`**: Esto NO significa costo cero.
- Para vinos (botellas compradas), `CostoReceta = 0` generalmente porque no son recetas elaboradas, son productos adquiridos.
- En estos casos, se recurre a la jerarquía de costos de insumos.

### Jerarquía Final de Fuentes de Costo

| Prioridad | Fuente | Descripción |
|-----------|--------|-------------|
| 1 | `CostoReceta` | Si > 0 y confiable como costo consolidado |
| 2 | `Sync_Productos_Insumos.Costo` | Costo de botella/insumo actual |
| 3 | `Sync_Productos_Insumos.UltimoCosto` | Último costo registrado |
| 4 | `Sync_Productos_Insumos.CostoPromedio` | Costo promedio |
| 5-9 | (Futuro) | Compras, proveedor, inventario, override |

### Diagnóstico de Vinos con CostoReceta > 0

| Métrica | Valor |
|---------|-------|
| Total vinos | 1,512 |
| Con CostoReceta > 0 | **0** |
| Con CostoReceta = 0 o NULL | 1,512 |

**Conclusión:** Para la categoría VINO, todos los productos tienen `CostoReceta = 0` porque son botellas compradas, no recetas elaboradas. El costo proviene de `Sync_Productos_Insumos`.

### Resultado del Recálculo

| Estado | Antes de corrección | Después de corrección |
|--------|---------------------|----------------------|
| Total procesados | 500 | 1,512 |
| CALCULADO | 195 | 626 |
| COSTO_BASE_NO_CONFIGURADO | 305 | 886 |
| IMPUESTO_NO_CONFIGURADO | 0 | 0 |
| RANGO_NO_CONFIGURADO | 0 | 0 |

**Fuentes de costo utilizadas:**
- INSUMO_COSTO: 618 (costo de botella actual)
- INSUMO_PROMEDIO: 8 (costo promedio como fallback)
- COSTO_RECETA: 0 (ningún vino tiene CostoReceta > 0)

---

## 2. TABLAS REVISADAS Y CREADAS

### 2.1 Tablas Existentes Revisadas
- `ActivoFijo_ReglasClaseLibro` - No relacionada (activos fijos)
- `CRM_Automation_Reglas` - No relacionada (CRM)

**No existían tablas de reglas de precio comercial.**

### 2.2 Tablas Creadas

| Tabla | Propósito |
|-------|-----------|
| `Comercial_ReglasPrecio` | Reglas maestras con configuración de redondeo |
| `Comercial_ReglasPrecioRangos` | Rangos de costo con margen multiplicador |
| `Comercial_PreciosSugeridos` | Resultados de cálculo con trazabilidad |

---

## 3. DDL EJECUTADO

### 3.1 Comercial_ReglasPrecio
```sql
CREATE TABLE Comercial_ReglasPrecio (
    ReglaPrecioID UNIQUEIDENTIFIER PRIMARY KEY,
    Codigo VARCHAR(50) UNIQUE,
    NombreRegla NVARCHAR(200),
    TipoRegla VARCHAR(30),  -- VINO, GENERAL
    MetodoRedondeo VARCHAR(20),  -- MAS_CERCANO, HACIA_ARRIBA, HACIA_ABAJO
    MultiploRedondeo INT DEFAULT 5,
    UsaCostoReceta BIT DEFAULT 0,  -- Siempre false para vinos
    UsaCostoBotella BIT DEFAULT 1, -- Siempre true para vinos
    VigenciaDesde DATE,
    VigenciaHasta DATE,
    Activo BIT
);
```

### 3.2 Comercial_ReglasPrecioRangos
```sql
CREATE TABLE Comercial_ReglasPrecioRangos (
    ReglaPrecioRangoID UNIQUEIDENTIFIER PRIMARY KEY,
    ReglaPrecioID UNIQUEIDENTIFIER FK,
    LimiteInferior DECIMAL(18,2),
    LimiteSuperior DECIMAL(18,2),
    MargenMultiplicador DECIMAL(6,4),
    Orden INT,
    CONSTRAINT CK_Rango_Limites CHECK (LimiteSuperior > LimiteInferior)
);
```

### 3.3 Comercial_PreciosSugeridos
```sql
CREATE TABLE Comercial_PreciosSugeridos (
    PrecioSugeridoID UNIQUEIDENTIFIER PRIMARY KEY,
    ProductoID UNIQUEIDENTIFIER,
    ServerID UNIQUEIDENTIFIER,
    CodigoProducto VARCHAR(100),
    ReglaPrecioID UNIQUEIDENTIFIER FK,
    ReglaPrecioRangoID UNIQUEIDENTIFIER,
    CostoBotella DECIMAL(18,4),
    FuenteCostoBotella VARCHAR(50),
    MargenMultiplicador DECIMAL(6,4),
    TasaImpuestoAplicada DECIMAL(6,4),
    PrecioBase DECIMAL(18,4),
    ImporteImpuesto DECIMAL(18,4),
    PrecioConImpuesto DECIMAL(18,4),
    MetodoRedondeo VARCHAR(20),
    MultiploRedondeo INT,
    PrecioSugerido DECIMAL(18,2),
    EstadoCalculo VARCHAR(40)
);
```

---

## 4. REGLA DE PRECIO CREADA

### 4.1 Configuración

| Campo | Valor |
|-------|-------|
| Código | VINOS_RANGOS_MX |
| Nombre | Regla de Precio por Rango para Vinos México |
| Tipo | VINO |
| Método Redondeo | MAS_CERCANO |
| Múltiplo Redondeo | 5 |
| Usa CostoReceta | **SÍ, si > 0 y confiable** (corregido) |
| Usa CostoBotella | SÍ (fallback si CostoReceta = 0) |
| Vigencia | Desde 2024-01-01, sin fecha fin |

> **NOTA CONCEPTUAL**: La regla PRIMERO verifica `CostoReceta`. Si es mayor a 0, lo usa como `CostoBaseVino`. Si es 0 (caso de vinos/botellas compradas), recurre a `Sync_Productos_Insumos`.

---

## 5. RANGOS CONFIGURADOS

| Orden | Límite Inferior | Límite Superior | Margen |
|-------|-----------------|-----------------|--------|
| 1 | $0.00 | $500.00 | 2.50x |
| 2 | $500.01 | $750.00 | 2.40x |
| 3 | $750.01 | $1,000.00 | 2.30x |
| 4 | $1,000.01 | $1,250.00 | 2.20x |
| 5 | $1,250.01 | $1,500.00 | 2.10x |
| 6 | $1,500.01 | $1,750.00 | 2.00x |
| 7 | $1,750.01 | $2,000.00 | 1.90x |
| 8 | $2,000.01 | $2,500.00 | 1.80x |
| 9 | $2,500.01 | $2,750.00 | 1.70x |
| 10 | $2,750.01 | $3,000.00 | 1.60x |
| 11 | $3,000.01 | $4,000.00 | 1.50x |
| 12 | $5,000.00 | $6,000.00 | 1.40x |
| 13 | $6,000.01 | $20,000.00 | 1.30x |

---

## 6. GAP DETECTADO

### 6.1 Rango No Configurado
```
$4,000.01 - $4,999.99 → SIN MARGEN CONFIGURADO
```

### 6.2 Comportamiento
- Productos con costo en este rango quedan con estado: `RANGO_NO_CONFIGURADO`
- NO se calcula precio sugerido
- NO se permite solicitud de cambio de precio

### 6.3 Opciones para el Usuario
1. **Ampliar rango 11** a $3,000.01 - $5,000.00 con margen 1.50
2. **Crear nuevo rango** $4,000.01 - $4,999.99 con margen específico
3. **Mantener gap** sin cálculo (estado actual)

---

## 7. SERVICIO DE CÁLCULO

### 7.1 Archivo Creado
`/app/backend/modules/comercial/services/precios_vinos_service.py`

### 7.2 Funciones Disponibles

```python
# Calcular precio para un vino
resultado = calcular_precio_sugerido_vino(
    codigo_producto='0000008496',
    server_id='1b230a06-ffaf-4c70-bd27-b1be3579dea6'
)

# Calcular masivamente
resultados = calcular_precios_vinos_masivo(server_id=None, limit=1000)

# Obtener estadísticas
stats = get_estadisticas_calculo()
```

### 7.3 Fórmula de Cálculo

```
precio_base = costo_botella × margen_multiplicador
importe_impuesto = precio_base × tasa_impuesto_resuelta
precio_con_impuesto = precio_base + importe_impuesto
precio_sugerido = redondear(precio_con_impuesto, 5, MAS_CERCANO)
```

---

## 8. PRUEBA COSTO $450

### 8.1 Datos de Entrada
- CostoBotella = $450.00
- Margen = 2.50 (rango $0-$500)
- TasaImpuesto = 16% (configurada en EDARSAHUB SQL)

### 8.2 Cálculo
```
precio_base = 450.00 × 2.50 = $1,125.00
importe_impuesto = 1,125.00 × 0.16 = $180.00
precio_con_impuesto = 1,125.00 + 180.00 = $1,305.00
precio_sugerido = $1,305.00 (ya es múltiplo de 5)
```

### 8.3 Resultado
```
✓ ESPERADO: $1,305.00
✓ CALCULADO: $1,305.00
```

---

## 9. PRUEBAS DE FRONTERA

| Costo | Descripción | Resultado |
|-------|-------------|-----------|
| $500.00 | Límite superior rango 1 | ✓ Margen 2.50 |
| $500.01 | Inicio rango 2 | ✓ Margen 2.40 |
| $750.00 | Límite superior rango 2 | ✓ Margen 2.40 |
| $750.01 | Inicio rango 3 | ✓ Margen 2.30 |
| $3,000.00 | Límite superior rango 10 | ✓ Margen 1.60 |
| $3,000.01 | Inicio rango 11 | ✓ Margen 1.50 |
| $4,000.00 | Límite superior rango 11 | ✓ Margen 1.50 |
| **$4,500.00** | **GAP** | **✓ GAP detectado** |
| $5,000.00 | Inicio rango 12 | ✓ Margen 1.40 |
| $6,000.00 | Límite superior rango 12 | ✓ Margen 1.40 |
| $6,000.01 | Inicio rango 13 | ✓ Margen 1.30 |

---

## 10. RESULTADOS DE CÁLCULO MASIVO

### 10.1 Estadísticas (1,512 productos procesados - actualizado con corrección conceptual)

| Estado | Cantidad | Porcentaje |
|--------|----------|------------|
| CALCULADO | 626 | 41.4% |
| COSTO_BASE_NO_CONFIGURADO | 886 | 58.6% |
| IMPUESTO_NO_CONFIGURADO | 0 | 0% |
| RANGO_NO_CONFIGURADO | 0 | 0% |
| ERROR_CALCULO | 0 | 0% |

### 10.2 Observaciones
- **626 vinos** tienen costo disponible y precio calculado
- **886 vinos** requieren configuración de costo base (sincronización o entrada manual)
- **0 vinos** tienen impuesto no configurado (todos tienen IVA resuelto desde modelo canónico)
- **0 vinos** cayeron en el gap $4,000.01-$4,999.99
- **0 vinos** usan `CostoReceta` porque todos tienen CostoReceta = 0 (botellas compradas)

---

## 11. CONFIRMACIONES

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | DDL idempotente | ✅ |
| 2 | Regla de vino creada | ✅ |
| 3 | 13 rangos insertados | ✅ |
| 4 | Gap documentado | ✅ |
| 5 | Método redondeo configurado | ✅ MAS_CERCANO |
| 6 | Múltiplo redondeo = 5 | ✅ |
| 7 | Cálculo costo 450 = $1,305 | ✅ |
| 8 | Fronteras validadas | ✅ 11/11 |
| 9 | Costo 4,500 = RANGO_NO_CONFIGURADO | ✅ |
| 10 | CostoReceta: prioridad 1 si > 0 | ✅ (corregido) |
| 11 | No se hardcodeó 16% | ✅ Usa resolver_tasa_impuesto |
| 12 | No se modificó precio oficial | ✅ |
| 13 | NO-LIVE confirmado | ✅ |
| 14 | Sin MongoDB | ✅ |
| 15 | Tabla determina PRECIO SUGERIDO, no costo | ✅ |
| 16 | No regresión Costos y Márgenes | ✅ |
| 17 | No regresión Dashboard Comercial | ✅ |

---

## 12. INTEGRACIÓN CON SOLICITUD DE CAMBIO DE PRECIO

### 12.1 Tabla Existente
`Comercial_SolicitudesCambioPrecio` ya existe con campos:
- PrecioActual
- PrecioSolicitado
- VariacionPesos
- VariacionPorcentaje

### 12.2 Integración Propuesta
El precio sugerido calculado puede usarse como base para:
1. Comparar `PrecioActual` vs `PrecioSugerido`
2. Pre-poblar `PrecioSolicitado` en nuevas solicitudes
3. Validar que solicitudes no usen productos sin costo/impuesto configurado

**NO se modifica precio oficial** - Solo se calcula precio sugerido.

---

## 13. ARCHIVOS CREADOS

| Archivo | Descripción |
|---------|-------------|
| `/app/backend/modules/comercial/services/precios_vinos_service.py` | Servicio de cálculo |
| `/app/docs/reports/FASE_1C_3G_E_REGLAS_PRECIO_RANGO_VINOS.md` | Este reporte |

---

## 14. RIESGOS PENDIENTES

1. **886 vinos sin costo configurado**: Requieren sincronización de costos desde sistemas origen o entrada manual.

2. **Gap $4,000.01-$4,999.99**: Pendiente definición del usuario si desea cerrar el gap.

3. **Costos muy bajos detectados**: Algunos costos parecen muy bajos (<$10). Puede ser por:
   - Unidad de medida diferente (copa vs botella)
   - Datos de prueba
   - Requiere validación de negocio

4. **CostoReceta no disponible para vinos**: Todos los vinos tienen CostoReceta = 0. Esto es esperado porque son botellas compradas, no recetas elaboradas. Si en el futuro se desea consolidar costos en CostoReceta, la jerarquía ya está preparada para priorizarlo.

---

## 15. FÓRMULA DE CÁLCULO CLARIFICADA

```
ACLARACIÓN CONCEPTUAL:
La tabla de rangos NO calcula el costo del vino.
La tabla de rangos determina el PRECIO DE VENTA SUGERIDO.

FÓRMULA:
CostoBaseVino
  → Buscar en jerarquía (CostoReceta > Costo Insumo > Último > Promedio)
  → rango de costo (determina margen multiplicador)
  → margen multiplicador
  → impuesto resuelto desde EDARSAHUB SQL (NO hardcodear 16%)
  → redondeo a múltiplo de 5
  → precio sugerido de venta

EJEMPLO:
CostoBaseVino = 450.00 (fuente: INSUMO_COSTO)
MargenMultiplicador = 2.50 (rango $0-$500)
TasaImpuestoResuelta = 0.16 (resuelto desde modelo canónico)

precio_base = 450.00 × 2.50 = $1,125.00
importe_impuesto = 1,125.00 × 0.16 = $180.00
precio_con_impuesto = 1,125.00 + 180.00 = $1,305.00
precio_menu_sugerido = $1,305.00 (ya es múltiplo de 5)
```

---

## 15. RECOMENDACIÓN PARA SIGUIENTE FASE

### FASE 1C-3G-F: Frontend de Precios Sugeridos

Para implementar UI de precios de vinos, se requiere:

1. **Endpoint API** para listar vinos con precio sugerido:
   - `/api/comercial/precios-vinos`
   - Filtros por servidor, familia, estado de cálculo

2. **Componente React** para mostrar:
   - Tabla de vinos con costo, margen, precio sugerido
   - Indicadores de estado (calculado, sin costo, sin rango)
   - Botón para crear solicitud de cambio de precio

3. **Validaciones**:
   - No permitir solicitud si estado ≠ CALCULADO
   - Mostrar mensaje de error apropiado para cada estado

---

**FIN DEL REPORTE**

**Corrección Conceptual Completada:** 2026-05-25  
**Siguiente Acción:** Esperar autorización para FASE 1C-3G-F (UI de administración fiscal para productos NO_CONFIGURADO)

---

## APÉNDICE: Resumen de Corrección Conceptual

### Antes de la Corrección
- Se descartaba `CostoReceta` para vinos de inmediato
- Estado de error se llamaba `COSTO_BOTELLA_NO_CONFIGURADO`
- No se documentaba la distinción entre cálculo de costo vs precio de venta

### Después de la Corrección
- `CostoReceta` tiene prioridad 1 (si > 0 y confiable)
- Estado renombrado a `COSTO_BASE_NO_CONFIGURADO` (más preciso)
- Documentación clara: la tabla de rangos calcula **PRECIO DE VENTA SUGERIDO**
- Jerarquía completa de 9 fuentes de costo (5 futuras)
- Validaciones adicionales (17 confirmaciones vs 14 anteriores)

### Cambios en Código
- `precios_vinos_service.py`: Nueva función `obtener_costo_base_vino()` con jerarquía corregida
- Campo `costo_botella` renombrado a `costo_base_vino` en `ResultadoPrecioSugerido`
- Docstrings actualizados con aclaración conceptual

