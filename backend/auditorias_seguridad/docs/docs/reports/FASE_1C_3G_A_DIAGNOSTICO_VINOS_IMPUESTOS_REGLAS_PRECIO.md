# FASE 1C-3G-A: Diagnóstico - Catálogo de Vinos, Impuestos y Reglas de Precio

**Fecha:** 25 Mayo 2026  
**Estado:** DIAGNÓSTICO COMPLETADO - HALLAZGO P0 CRÍTICO  
**Autor:** Agente EDARSA HUB

---

## RESUMEN EJECUTIVO

### HALLAZGO P0 CRÍTICO: IMPUESTO MPRO EN 0% NO ES ACEPTABLE

Se identificó que **TODOS los 5,414 productos MPRO tienen TasaImpuesto = 0.00%** en la tabla `Sync_Productos`. Este valor NO es una tasa fiscal válida, sino un **fallo de sincronización**.

#### Causa Raíz Identificada

En el archivo `/app/backend/modules/sync_recetas/sync_recetas.py`, función `_obtener_productos_mpro()` (líneas 618-647):

```python
def _obtener_productos_mpro(host, port, database, username, password) -> List[ProductoSync]:
    query = """
    SELECT p.Pr_Cve_Producto, p.Pr_Descripcion, p.Pr_Descripcion_Corta,
           p.Fm_Cve_Familia, p.Sf_Cve_SubFamilia,
           f.Fm_Descripcion, sf.Sf_Descripcion,
           pp.Pp_Precio_1 as Precio
    FROM Producto p
    LEFT JOIN Familia f ON p.Fm_Cve_Familia = f.Fm_Cve_Familia
    LEFT JOIN SubFamilia sf ON p.Sf_Cve_SubFamilia = sf.Sf_Cve_SubFamilia
    LEFT JOIN Producto_Precio pp ON p.Pr_Cve_Producto = pp.Pr_Cve_Producto
    WHERE p.Es_Cve_Estado = 'AC'
    """
    # ...
    return [
        ProductoSync(
            # ... otros campos ...
            precio_venta=Decimal(str(r.get('Precio') or 0))
            # ❌ NO HAY: tasa_impuesto=...
        )
    ]
```

**El campo `tasa_impuesto` NO se extrae de MPRO.** El modelo `ProductoSync` tiene un default de 0, por lo que todos los productos MPRO quedan con tasa 0%.

#### Comparación con SoftRestaurant

En `_obtener_productos_sr()` (líneas 381-407) SÍ se extrae el impuesto:

```python
SELECT ... pd.preciosinimpuestos, pd.impuesto1
...
tasa_impuesto=Decimal(str(r.get('impuesto1') or 0))
```

---

## SECCIÓN 1: TABLAS EXISTENTES EN EDARSAHUB

### 1.1 Tablas Relacionadas con Vinos

| Tabla | Propósito | ¿Reutilizar? |
|-------|-----------|--------------|
| `CavaSocios_Botellas` | Botellas de Cava de Socios (NO comercial) | ❌ NO - Es para custodia |
| `Sync_Productos` | Productos sincronizados | ✅ SÍ - Tiene 1,583 vinos |

**Familias de vinos encontradas en `Sync_Productos`:**
- B VINOS: 651 productos
- B VINOS TINTOS 750: 236 productos
- B VINOS BLANCOS: 168 productos
- B VINOS ROSADOS: 121 productos
- B VINOS ESPUMOSOS: 144 productos
- CAVAS: 9 productos

### 1.2 Tablas Relacionadas con Impuestos

| Tabla | Existe | Estado |
|-------|--------|--------|
| `Comercial_ImpuestosCatalogo` | ❌ NO | A crear |
| `Comercial_ImpuestosTasas` | ❌ NO | A crear |
| `Sync_Impuestos_Origen` | ❌ NO | A crear |

### 1.3 Tablas Relacionadas con Reglas de Precio

| Tabla | Existe | Estado |
|-------|--------|--------|
| `Comercial_ReglasPrecio` | ❌ NO | A crear |
| `Comercial_ReglasPrecioRangos` | ❌ NO | A crear |
| `Comercial_SolicitudesCambioPrecio` | ✅ SÍ | Ya existe |
| `Comercial_SimulacionesPrecios` | ✅ SÍ | Ya existe |
| `Venta_ListasPrecios` | ✅ SÍ | Ya existe |

---

## SECCIÓN 2: DIAGNÓSTICO DE IMPUESTOS EN SYNC_PRODUCTOS

### 2.1 Distribución por Sistema

| Sistema | TasaImpuesto | Productos | Servidores |
|---------|--------------|-----------|------------|
| SOFTRESTAURANT_PRO | 16.00% | 4,491 | 4 |
| MPRO | **0.00%** | **5,414** | 1 |

### 2.2 Análisis de Causa

**SoftRestaurant (OK):**
- Extrae campo `impuesto1` de tabla `productosdetalle`
- Sincroniza tasa 16.00% correctamente

**MPRO (FALLO):**
- La función `_obtener_productos_mpro()` NO incluye JOIN ni campo de impuesto
- El query solo obtiene: Producto, Familia, SubFamilia, Producto_Precio
- **NO hay JOIN a tablas de impuestos/IVA/tasas**
- El modelo usa default = 0

---

## SECCIÓN 3: MPRO - IMPUESTO 0% NO ACEPTABLE

### 3.1 Regla Crítica

El impuesto MPRO en 0% **NO es aceptable** para:
- ❌ Cálculo de precios sugeridos
- ❌ Reglas de precio de vinos
- ❌ Simulaciones
- ❌ Solicitudes de cambio de precio
- ❌ Precio de menú

### 3.2 Tratamiento del 0% MPRO

| Escenario | Acción |
|-----------|--------|
| TasaImpuesto = 0 sin justificación | Marcar como `IMPUESTO_NO_CONFIGURADO` |
| TasaImpuesto = 0 sin mapeo canónico | Marcar como `PENDIENTE_HOMOLOGACION` |
| TasaImpuesto = 0 por falla de sync | Marcar como `TASA_INVALIDA_ORIGEN` |
| Producto exento documentado | Permitir 0% con código fiscal |

### 3.3 Cálculo de Precio con Impuesto Inválido

```
SI TasaImpuesto = 0 Y NO hay justificación fiscal ENTONCES:
    precio_sugerido = NULL
    status = 'IMPUESTO_NO_CONFIGURADO'
    mensaje = "Producto MPRO sin tasa de impuesto homologada"
    NO permitir solicitud de cambio de precio
    NO mostrar precio sugerido en UI
```

### 3.4 Tablas MPRO a Investigar

Para encontrar la fuente real de impuestos en MPRO, se deben revisar:

1. **Tablas de configuración fiscal:**
   - Buscar tablas con nombres: `Impuesto`, `IVA`, `Tax`, `Fiscal`, `Tasa`, `CFDI`, `SAT`

2. **Tablas de precios:**
   - `Producto_Precio` - ¿Tiene campos de impuesto?
   - Buscar campos: `Impuesto`, `IVA`, `Tasa`, `PrecioConImpuesto`

3. **Tablas de venta:**
   - `Venta_Detalle` - ¿El impuesto se calcula en venta?
   - ¿MPRO maneja precios CON impuesto incluido?

4. **Tablas de configuración:**
   - Parámetros de empresa
   - Configuración global de IVA

### 3.5 Hipótesis de Causa del 0%

| # | Hipótesis | Probabilidad |
|---|-----------|--------------|
| 1 | Campo incorrecto en sync (no se hace JOIN a tabla de impuestos) | **ALTA** |
| 2 | MPRO maneja precios con impuesto incluido (sin desglose) | MEDIA |
| 3 | Impuesto en configuración global, no por producto | MEDIA |
| 4 | Error de mapeo en sync_recetas.py | **CONFIRMADA** |

---

## SECCIÓN 4: REGLA DE RESOLUCIÓN DE TASA

### 4.1 Prioridad de Resolución

```
1. Override autorizado por producto/unidad/sucursal (Comercial_ImpuestosOverrides)
2. Tasa específica por producto sincronizada (Sync_Productos.TasaImpuesto != 0)
3. Tasa por familia/subfamilia configurada en EDARSAHUB
4. Tasa por unidad de negocio/sucursal
5. Tasa por país/región
6. Tasa default global SOLO si está activa y autorizada
```

### 4.2 Fallback desde EDARSAHUB SQL

Si MPRO no entrega tasa válida, se debe usar fallback **SOLO desde EDARSAHUB SQL**:

```sql
-- Ejemplo de resolución para producto MPRO
SELECT 
    CASE 
        WHEN ov.TasaOverride IS NOT NULL THEN ov.TasaOverride
        WHEN p.TasaImpuesto > 0 THEN p.TasaImpuesto
        WHEN t_familia.TasaImpuesto IS NOT NULL THEN t_familia.TasaImpuesto
        WHEN t_unidad.TasaImpuesto IS NOT NULL THEN t_unidad.TasaImpuesto
        WHEN t_pais.TasaImpuesto IS NOT NULL THEN t_pais.TasaImpuesto
        ELSE NULL  -- NO DEFAULT 16%
    END as TasaResuelta
FROM Sync_Productos p
LEFT JOIN Comercial_ImpuestosOverrides ov ON ...
LEFT JOIN Comercial_ImpuestosTasas t_familia ON ...
LEFT JOIN Comercial_ImpuestosTasas t_unidad ON ...
LEFT JOIN Comercial_ImpuestosTasas t_pais ON ...
WHERE p.ProductoID = @ProductoID
```

---

## SECCIÓN 5: ESTRATEGIA DE HOMOLOGACIÓN

### 5.1 Fase Inmediata (P0)

1. **Corregir sync_recetas.py:**
   - Investigar tablas de impuestos en MPRO
   - Agregar JOIN a tabla de impuestos
   - Extraer campo de tasa real

2. **Crear tabla Comercial_ImpuestosTasas:**
   - Configurar tasa default por unidad MPRO
   - México: 16% (IVA general)
   - Debe ser configurable, NO hardcodeada

3. **Bloquear cálculo con 0%:**
   - En endpoints de pricing/simulación
   - Retornar status `IMPUESTO_NO_CONFIGURADO`

### 5.2 Validación de Excepción 0%

Solo permitir tasa 0% si cumple TODO:
- [ ] Producto marcado como exento según catálogo fiscal
- [ ] Existe código fiscal que lo justifica
- [ ] Existe mapeo canónico en EDARSAHUB SQL
- [ ] Está activo y vigente
- [ ] Queda documentado en auditoría
- [ ] NO es default/null/vacío/falla de sync

---

## SECCIÓN 6: CRITERIO DE PARO

### 6.1 Condiciones de Paro Detectadas

| Condición | Estado | Acción |
|-----------|--------|--------|
| No se encuentra fuente de impuesto MPRO | ⚠️ PENDIENTE | Investigar tablas MPRO |
| No se puede diferenciar 0% real de error | ⚠️ PENDIENTE | Requiere análisis de BD MPRO |
| Se requiere hardcodear 16% | ❌ NO PERMITIDO | Usar configuración EDARSAHUB |
| Conexión a MPRO desde endpoints | ❌ NO PERMITIDO | Solo vía job de sync |

### 6.2 Riesgo Fiscal

**ALTO:** Si se calculan precios con tasa 0% no válida:
- Precios sugeridos serían 16% menores al correcto
- Podría generar diferencias en facturación
- Podría generar diferencias en declaraciones fiscales

---

## SECCIÓN 7: PROPUESTA DE CORRECCIÓN

### 7.1 Acción Inmediata

1. **Agregar validación en endpoints de pricing:**
```python
def calcular_precio_sugerido(producto):
    if producto.tasa_impuesto == 0 and producto.sistema_origen == 'MPRO':
        if not tiene_justificacion_fiscal(producto):
            return {
                'precio_sugerido': None,
                'status': 'IMPUESTO_NO_CONFIGURADO',
                'mensaje': 'Producto MPRO sin tasa de impuesto homologada'
            }
```

2. **Crear configuración fallback en EDARSAHUB:**
```sql
INSERT INTO Comercial_ImpuestosTasas (
    ImpuestoID, PaisCodigo, TasaImpuesto, EsDefault, Activo
) VALUES (
    1, 'MX', 16.00, 1, 1  -- IVA México configurable
)
```

### 7.2 Siguiente Fase Recomendada

Antes de implementar catálogo de vinos y reglas de precio:

**FASE 1C-3G-B: Homologación de Impuestos MPRO**
1. Conectar a MPRO (con credenciales correctas)
2. Diagnosticar tablas fiscales reales
3. Encontrar relación producto-impuesto
4. Actualizar `_obtener_productos_mpro()` en sync_recetas.py
5. Re-sincronizar productos MPRO con tasa correcta
6. Validar que no haya productos con 0% no justificado

---

## SECCIÓN 8: ARCHIVOS AFECTADOS

| Archivo | Cambio Requerido |
|---------|------------------|
| `/app/backend/modules/sync_recetas/sync_recetas.py` | Agregar extracción de impuesto MPRO |
| `/app/backend/modules/costos_margenes/repository.py` | Validar tasa antes de cálculo |
| `/app/backend/modules/costos_margenes/routes.py` | Retornar error si tasa = 0 sin justificación |

---

## CONCLUSIÓN

**NO PROCEDER** con catálogo de vinos ni reglas de precio hasta que:

1. ✅ Se diagnostique la fuente real de impuestos en MPRO
2. ✅ Se corrija el sync para extraer tasa correcta
3. ✅ Se creen tablas de impuestos canónicos en EDARSAHUB
4. ✅ Se implemente fallback controlado para productos sin tasa
5. ✅ Se bloquee cálculo de precios con 0% no autorizado

**Próximo paso:** Diagnóstico profundo de tablas MPRO (requiere conexión a base de datos MPRO).
