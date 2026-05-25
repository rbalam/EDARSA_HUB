# FASE 1C-3G-D: Productos Clasificados como Vino y Extensión de Atributos

**Fecha:** 2026-05-25  
**Estado:** COMPLETADO (Diagnóstico)

---

## 1. RESUMEN EJECUTIVO

Se completó el diagnóstico de productos clasificados como vino en EDARSAHUB. Los vinos son **productos normales** dentro de `Sync_Productos`, identificables por familia/subfamilia.

### Resultado Principal:
- **1,439 productos** clasificados como vino
- **1,126 (78%)** tienen insumo asociado en `Sync_Productos_Insumos`
- **604 (42%)** tienen costo de botella disponible
- **835 (58%)** requieren configuración de costo

---

## 2. PRODUCTOS VINO IDENTIFICADOS

### 2.1 Familias/Subfamilias de Vinos Detectadas

| Familia | Sistema | Productos |
|---------|---------|-----------|
| B VINOS | SOFTRESTAURANT_PRO | 651 |
| VINOS TINTOS | MPRO | 527 |
| B CHAMPAGNES Y COGNACS | SOFTRESTAURANT_PRO | 71 |
| VINOS BLANCOS | MPRO | 92 |
| CHAMPAGNES Y COGNACS | MPRO | 55 |
| VINOS ROSADOS | MPRO | 46 |
| VINOS ESPUMOSOS/POSTRE | MPRO | 33 |
| C CAVAS | SOFTRESTAURANT_PRO | 18 |
| B VINOS DE POSTRE | SOFTRESTAURANT_PRO | 10 |
| CAVAS | MPRO | 9 |

**Total: 1,512 productos** (1,439 únicos con insumo asociado analizado)

### 2.2 Distribución por Servidor

| Servidor | Productos | Con Precio | Con Impuesto |
|----------|-----------|------------|--------------|
| CIENFUEGOS | 537 | 421 | 537 |
| ManagmentPro | 762 | 450 | 762 |
| 130° MERIDA | 139 | 139 | 139 |
| LA ESTELAR | 74 | 53 | 74 |

---

## 3. CONFIRMACIÓN: NO DUPLICAR PRODUCTOS

### 3.1 Estructura Actual
Los vinos ya existen en:
- `Sync_Productos` - Entidad principal con precio, impuesto, familia
- `Sync_Productos_Insumos` - Costos de compra/inventario
- `Comercial_ImpuestosMapeo` - Mapeo fiscal canónico

### 3.2 NO se creó catálogo separado
**Correcto**: Los vinos NO necesitan tabla `Comercial_VinosCatalogo` separada.

---

## 4. DIAGNÓSTICO DE CavaSocios_Botellas

### 4.1 Propósito de CavaSocios_Botellas
Esta tabla es para **gestión de botellas de SOCIOS**, NO catálogo comercial:

```
CavaSocios_Botellas
├── BotellaID
├── SocioID           ← Pertenece a un socio/cliente
├── ProductoCodigo    ← Referencia al producto
├── UbicacionCava     ← Ubicación física en cava
├── FechaIngreso
├── EstadoBotella
└── ...
```

### 4.2 Por qué NO reutilizar
- **CavaSocios_Botellas** = Inventario de terceros (socios)
- **Sync_Productos (vino)** = Inventario comercial de la empresa

**No se mezclan** porque son dominios diferentes:
- Una botella de socio puede tener `ProductoCodigo` para identificación
- Pero el inventario comercial NO usa esta tabla

---

## 5. FUENTE DE COSTO DE BOTELLA

### 5.1 Jerarquía de Resolución Propuesta

```
resolver_costo_botella(producto_codigo, server_id):
    1. Sync_Productos_Insumos.Costo          (Costo actual)
    2. Sync_Productos_Insumos.UltimoCosto    (Último costo compra)
    3. Sync_Productos_Insumos.CostoPromedio  (Promedio histórico)
    4. Override manual autorizado            (Comercial_CostosOverride)
    5. Si no hay costo → COSTO_BOTELLA_NO_CONFIGURADO
```

### 5.2 Estadísticas de Costo

| Estado | Productos | Porcentaje |
|--------|-----------|------------|
| Con costo disponible | 604 | 42% |
| Sin costo (requiere config) | 835 | 58% |
| **Total** | **1,439** | 100% |

### 5.3 Muestra de Vinos con Costo

| Código | Nombre | Precio | Costo |
|--------|--------|--------|-------|
| C050003 | CUCHILLO DE CAVA | $1,500 | $800 |
| 009237 | VT LAS NUBES SELECCION | - | $3,990 |
| 0000007550 | Vino Tinto 01 pz 04 lt | $272 | $272 |
| B160271 | VR D GUADIANA MERLOT | - | $345 |

---

## 6. INTEGRACIÓN CON IMPUESTOS CANÓNICOS

### 6.1 Estado Fiscal de Productos Vino

| Estado | Productos |
|--------|-----------|
| CONFIGURADO | 1,512 |
| NO_CONFIGURADO | 0 |
| TASA_CERO_VALIDADA | 0 |

**Todos los vinos tienen impuesto configurado (16% IVA)**

### 6.2 Uso de resolver_tasa_impuesto()

```python
resultado = resolver_tasa_impuesto('B160075', server_id)
# {
#     'tasa': 16.0,
#     'estado_fiscal': 'CONFIGURADO',
#     'permite_calculo_precio': True
# }
```

---

## 7. EVALUACIÓN DE TABLA EXTENSIÓN

### 7.1 ¿Se necesita Comercial_ProductosVinoDetalle?

**Evaluación:**
- Los atributos básicos (nombre, precio, familia) ya están en `Sync_Productos`
- Los costos están en `Sync_Productos_Insumos`
- Los impuestos están en `Comercial_ImpuestosMapeo`

**Atributos que NO existen actualmente:**
- Bodega/Casa productora
- País/Región de origen
- Denominación de origen
- Varietal/Uva
- Añada
- Graduación alcohólica
- Maridaje

### 7.2 Recomendación

**CREAR tabla extensión** solo si el negocio requiere administrar estos atributos.

Para esta fase, **NO se crea la tabla** porque:
1. No hay datos de origen para poblarla
2. Requiere entrada manual o integración con sistema de bodegas
3. El catálogo básico funciona sin estos atributos

**Dejar preparado DDL** para fase futura si se autoriza.

---

## 8. DDL PROPUESTO (NO EJECUTADO)

Si se autoriza en fase futura:

```sql
-- Solo crear si se requieren atributos especializados de vino
CREATE TABLE Comercial_ProductosVinoDetalle (
    ProductoVinoDetalleID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ProductoID UNIQUEIDENTIFIER NOT NULL,      -- FK a Sync_Productos.ProductoID
    ServerID UNIQUEIDENTIFIER NOT NULL,        -- FK a Servidores_Conexiones
    CodigoProducto VARCHAR(100) NOT NULL,      -- Referencia a CodigoFuente
    
    -- Atributos de Vino
    Bodega NVARCHAR(200),
    CasaProductora NVARCHAR(200),
    PaisOrigen VARCHAR(3),                     -- ISO 3166-1 alpha-3
    RegionOrigen NVARCHAR(100),
    DenominacionOrigen NVARCHAR(200),
    TipoVino VARCHAR(50),                      -- TINTO, BLANCO, ROSADO, ESPUMOSO
    Varietal NVARCHAR(100),                    -- Cabernet, Merlot, etc.
    UvaPrincipal NVARCHAR(100),
    Mezcla NVARCHAR(500),
    Anada INT,                                 -- Año de cosecha
    VolumenML INT,
    GraduacionAlcoholica DECIMAL(4,2),
    Presentacion VARCHAR(50),                  -- BOTELLA, COPA, MAGNUM
    Color VARCHAR(30),
    Maridaje NVARCHAR(500),
    TemperaturaServicio VARCHAR(50),
    
    -- Flags
    EsBotellaCompleta BIT DEFAULT 1,
    EsVinoCopa BIT DEFAULT 0,
    DisponibleMenu BIT DEFAULT 1,
    DisponibleCava BIT DEFAULT 0,
    
    -- Metadata
    Observaciones NVARCHAR(1000),
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME2 DEFAULT SYSDATETIME(),
    FechaModificacion DATETIME2 DEFAULT SYSDATETIME(),
    UsuarioCreacion NVARCHAR(100),
    UsuarioModificacion NVARCHAR(100),
    
    CONSTRAINT UQ_VinoDetalle_Producto UNIQUE (ServerID, CodigoProducto)
);
```

---

## 9. VALIDACIONES REALIZADAS

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Productos vino identificados | ✅ 1,439 |
| 2 | Familias/subfamilias detectadas | ✅ 10 familias |
| 3 | No se creó catálogo duplicado | ✅ |
| 4 | CavaSocios_Botellas NO reutilizado | ✅ |
| 5 | Fuente de CostoBotella propuesta | ✅ Sync_Productos_Insumos |
| 6 | Productos vino con costo | ✅ 604 (42%) |
| 7 | Productos vino sin costo | ✅ 835 (58%) - COSTO_NO_CONFIGURADO |
| 8 | Impuesto CONFIGURADO | ✅ 100% de vinos |
| 9 | No se usa CostoReceta | ✅ |
| 10 | No se hardcodeó 16% | ✅ |
| 11 | NO-LIVE confirmado | ✅ |
| 12 | Sin MongoDB | ✅ |
| 13 | Costos y Márgenes funciona | ✅ |

---

## 10. RIESGOS PENDIENTES

1. **835 vinos sin costo**: Requieren:
   - Sincronización de costos desde sistemas origen
   - O entrada manual de costo de botella
   - Sin costo → No se puede calcular precio sugerido

2. **Tabla extensión pendiente**: Si el negocio requiere atributos de vino (bodega, añada, varietal), se deberá crear `Comercial_ProductosVinoDetalle` en fase futura.

---

## 11. RECOMENDACIÓN PARA FASE 1C-3G-E

### Reglas de Precio por Rango para Productos Vino

Para implementar reglas de precio, se requiere:

1. **Crear tabla `Comercial_ReglasPrecios`** con:
   - Rango de costo (desde/hasta)
   - Margen objetivo
   - Factor de multiplicación
   - Redondeo
   - Aplicación (VINO, GENERAL, FAMILIA específica)

2. **Función `calcular_precio_sugerido()`** que:
   - Obtenga costo de botella
   - Aplique regla de margen por rango
   - Agregue impuesto
   - Aplique redondeo

3. **Comportamiento para productos sin costo**:
   - `precio_sugerido = NULL`
   - `estado = COSTO_BOTELLA_NO_CONFIGURADO`
   - No permitir solicitud de cambio de precio

---

**FIN DEL REPORTE**

**Siguiente Acción:** Esperar autorización para FASE 1C-3G-E (Reglas de Precio por Rango)
