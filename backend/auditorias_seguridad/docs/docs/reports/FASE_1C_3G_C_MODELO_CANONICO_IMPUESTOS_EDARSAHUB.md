# FASE 1C-3G-C: Modelo Canónico de Impuestos EDARSAHUB SQL

**Fecha de Creación:** 2026-05-25  
**Estado:** COMPLETADO

---

## 1. RESUMEN EJECUTIVO

Se creó el Modelo Canónico de Impuestos en EDARSAHUB SQL para homologar tasas fiscales desde SoftRestaurant y MPRO. El modelo permite resolver correctamente la tasa de impuesto por producto según una jerarquía de prioridades.

### Resultado:
- **5 tablas** canónicas creadas
- **8 impuestos** canónicos registrados (IVA, IEPS, Exento, Sin Configurar)
- **9,905 productos** mapeados a impuestos canónicos
- **62 productos MPRO** correctamente marcados como NO_CONFIGURADO
- **0 productos** con 0% inválido

---

## 2. TABLAS EXISTENTES REVISADAS

Antes de crear nuevas tablas, se verificó que NO existían tablas canónicas de impuestos:

| Tabla | Estado | Observación |
|-------|--------|-------------|
| Comercial_ImpuestosCatalogo | NO EXISTÍA | Creada |
| Comercial_ImpuestosTasas | NO EXISTÍA | Creada |
| Sync_Impuestos_Origen | NO EXISTÍA | Creada |
| Comercial_ImpuestosMapeo | NO EXISTÍA | Creada |
| Comercial_ImpuestosOverrides | NO EXISTÍA | Creada |

Tablas relacionadas existentes (NO modificadas):
- `Sync_Productos` - Ya contiene TasaImpuesto
- `Compras_DocumentosFiscales*` - Módulo de compras
- `RH_*Fiscal` - Módulo de RRHH

---

## 3. MODELO CANÓNICO CREADO

### 3.1 Comercial_ImpuestosCatalogo
Catálogo maestro de impuestos canónicos.

```sql
CREATE TABLE Comercial_ImpuestosCatalogo (
    ImpuestoID UNIQUEIDENTIFIER PRIMARY KEY,
    Codigo VARCHAR(20) UNIQUE,        -- IVA_16, IEPS_8, etc.
    Nombre NVARCHAR(200),
    TipoImpuesto VARCHAR(20),         -- IVA, IEPS, ISR_RETENIDO
    PaisISO VARCHAR(3) DEFAULT 'MEX',
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME2,
    FechaModificacion DATETIME2
);
```

### 3.2 Comercial_ImpuestosTasas
Tasas vigentes por período.

```sql
CREATE TABLE Comercial_ImpuestosTasas (
    TasaID UNIQUEIDENTIFIER PRIMARY KEY,
    ImpuestoID UNIQUEIDENTIFIER FK,
    Tasa DECIMAL(10,4),              -- 16.0000, 8.0000, 0.0000
    TipoFactor VARCHAR(20),          -- Tasa, Cuota, Exento
    VigenciaDesde DATE,
    VigenciaHasta DATE,              -- NULL = vigente
    Activo BIT
);
```

### 3.3 Sync_Impuestos_Origen
Mapeo de impuestos desde sistemas origen.

```sql
CREATE TABLE Sync_Impuestos_Origen (
    MapeoID UNIQUEIDENTIFIER PRIMARY KEY,
    ServerID UNIQUEIDENTIFIER FK,
    SystemType VARCHAR(50),
    CodigoImpuestoOrigen VARCHAR(50),
    NombreImpuestoOrigen NVARCHAR(200),
    TasaOrigen DECIMAL(10,4),
    ImpuestoCanonicoID UNIQUEIDENTIFIER FK,
    EstadoMapeo VARCHAR(30),         -- MAPEADO, PENDIENTE_HOMOLOGACION
    SyncRunID VARCHAR(100)
);
```

### 3.4 Comercial_ImpuestosMapeo
Mapeo de productos a impuestos canónicos.

```sql
CREATE TABLE Comercial_ImpuestosMapeo (
    MapeoProductoID UNIQUEIDENTIFIER PRIMARY KEY,
    ServerID UNIQUEIDENTIFIER FK,
    SystemType VARCHAR(50),
    CodigoProducto VARCHAR(100),
    NombreProducto NVARCHAR(500),
    ImpuestoCanonicoID UNIQUEIDENTIFIER FK,
    TasaEfectiva DECIMAL(10,4),
    EstadoFiscal VARCHAR(30),        -- CONFIGURADO, NO_CONFIGURADO, etc.
    FuenteOrigen VARCHAR(20),        -- SINCRONIZADO, MANUAL, OVERRIDE
    SyncRunID VARCHAR(100),
    UNIQUE (ServerID, CodigoProducto)
);
```

### 3.5 Comercial_ImpuestosOverrides
Sobreescrituras autorizadas.

```sql
CREATE TABLE Comercial_ImpuestosOverrides (
    OverrideID UNIQUEIDENTIFIER PRIMARY KEY,
    TipoOverride VARCHAR(30),        -- PRODUCTO, FAMILIA, UNIDAD, SUCURSAL
    ServerID UNIQUEIDENTIFIER,
    CodigoProducto VARCHAR(100),
    FamiliaCodigoFuente VARCHAR(50),
    UnidadNegocioID UNIQUEIDENTIFIER,
    ImpuestoCanonicoID UNIQUEIDENTIFIER FK,
    TasaOverride DECIMAL(10,4),
    Motivo NVARCHAR(500),
    AutorizadoPor NVARCHAR(200),
    VigenciaDesde DATE,
    VigenciaHasta DATE,
    Activo BIT
);
```

---

## 4. IMPUESTOS CANÓNICOS REGISTRADOS

| Código | Nombre | Tipo | Tasa | Factor |
|--------|--------|------|------|--------|
| IVA_16 | IVA Tasa General 16% | IVA | 16.0% | Tasa |
| IVA_0 | IVA Tasa 0% (Alimentos) | IVA | 0.0% | Tasa |
| IVA_EXENTO | IVA Exento | IVA | 0.0% | Exento |
| IEPS_8 | IEPS 8% Bebidas Saborizadas | IEPS | 8.0% | Tasa |
| IEPS_26_5 | IEPS 26.5% Bebidas Alcohólicas | IEPS | 26.5% | Tasa |
| IEPS_30 | IEPS 30% Bebidas Alcohólicas | IEPS | 30.0% | Tasa |
| IEPS_53 | IEPS 53% Bebidas Alto Grado | IEPS | 53.0% | Tasa |
| SIN_IMPUESTO | Sin Impuesto Configurado | NO_CONFIGURADO | N/A | N/A |

---

## 5. MAPEO DE PRODUCTOS

### 5.1 Distribución por Sistema y Estado

| Sistema | Estado | Cantidad |
|---------|--------|----------|
| MPRO | CONFIGURADO | 3,651 |
| MPRO | TASA_CERO_VALIDADA | 1,701 |
| MPRO | NO_CONFIGURADO | 62 |
| SOFTRESTAURANT_PRO | CONFIGURADO | 4,489 |
| SOFTRESTAURANT_PRO | TASA_CERO_VALIDADA | 2 |
| **TOTAL** | | **9,905** |

### 5.2 Por Servidor

| Servidor | Total | Configurado | Tasa 0 | No Config |
|----------|-------|-------------|--------|-----------|
| 130° MERIDA | 1,858 | 1,858 | 0 | 0 |
| CIENFUEGOS | 2,022 | 2,021 | 1 | 0 |
| LA ESTELAR | 611 | 610 | 1 | 0 |
| ManagmentPro | 5,414 | 3,651 | 1,701 | 62 |

---

## 6. ESTADOS FISCALES DEFINIDOS

| Estado | Descripción | Permite Cálculo |
|--------|-------------|-----------------|
| CONFIGURADO | Tasa válida > 0 (IVA, IEPS) | ✅ SÍ |
| TASA_CERO_VALIDADA | Tasa 0% fiscal válida (alimentos) | ✅ SÍ |
| EXENTO_VALIDADO | Producto fiscalmente exento | ✅ SÍ |
| NO_CONFIGURADO | Sin homologación fiscal | ❌ NO |
| PENDIENTE_HOMOLOGACION | En proceso de mapeo | ❌ NO |
| ERROR_MAPEO | Error en proceso de mapeo | ❌ NO |

---

## 7. MANEJO DE LOS 62 PRODUCTOS MPRO

Los 62 productos MPRO sin impuesto configurado quedaron correctamente marcados:

- **EstadoFiscal:** NO_CONFIGURADO
- **TasaEfectiva:** NULL
- **ImpuestoCanonicoID:** Apunta a "SIN_IMPUESTO"
- **NO permiten:** Cálculo de precio sugerido
- **NO permiten:** Solicitud de cambio de precio

**Muestra de productos:**
- BRANDIG
- EXTRA DE CHIMICHURRI
- ISR Retenido
- Intereses Bancarios
- Licencia Paqueteria Office 365

---

## 8. FUNCIÓN resolver_tasa_impuesto

Se creó el servicio `/app/backend/modules/comercial/services/impuestos_service.py` con:

### 8.1 Jerarquía de Resolución

```
1. Override autorizado (PRODUCTO > SUCURSAL > UNIDAD > FAMILIA > REGION > PAIS)
2. Tasa específica por producto (Comercial_ImpuestosMapeo)
3. Fallback a Sync_Productos
```

### 8.2 Funciones Disponibles

```python
# Resolver tasa de impuesto
resultado = resolver_tasa_impuesto(
    codigo_producto='0000008496',
    server_id='1b230a06-ffaf-4c70-bd27-b1be3579dea6',
    unidad_negocio_id=None,
    familia_codigo=None
)

# Resultado
{
    'tasa': 16.0,
    'estado_fiscal': 'CONFIGURADO',
    'fuente': 'PRODUCTO',
    'permite_calculo_precio': True
}

# Para producto NO_CONFIGURADO
{
    'tasa': None,
    'estado_fiscal': 'NO_CONFIGURADO',
    'fuente': 'PRODUCTO',
    'permite_calculo_precio': False,
    'mensaje': 'Producto sin tasa de impuesto homologada. Requiere configuración fiscal.'
}
```

### 8.3 Tests Realizados

| Test | Producto | Resultado |
|------|----------|-----------|
| IVA 16% | Cordero Osobuco | ✅ tasa=16.0, CONFIGURADO |
| Tasa 0% | Arrachera | ✅ tasa=0.0, TASA_CERO_VALIDADA |
| NO_CONFIG | BRANDIG | ✅ tasa=None, NO_CONFIGURADO |

---

## 9. VALIDACIONES REALIZADAS

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | DDL idempotente | ✅ |
| 2 | Tablas existentes revisadas | ✅ |
| 3 | No duplicación | ✅ |
| 4 | Impuestos SoftRestaurant homologados | ✅ 4,491 productos |
| 5 | Impuestos MPRO homologados | ✅ 5,414 productos |
| 6 | Productos tasa > 0 mapeados | ✅ 8,140 |
| 7 | Productos tasa 0 validados | ✅ 1,703 |
| 8 | Los 62 MPRO como NO_CONFIGURADO | ✅ |
| 9 | No hay 0% inválido | ✅ 0 productos |
| 10 | No se hardcodeó 16% | ✅ |
| 11 | resolver_tasa_impuesto funciona | ✅ |
| 12 | NO_CONFIGURADO bloquea cálculo | ✅ |
| 13 | Costos y Márgenes funciona | ✅ |
| 14 | NO-LIVE confirmado | ✅ |
| 15 | Sin MongoDB | ✅ |
| 16 | Login funciona | ✅ |

---

## 10. ARCHIVOS CREADOS/MODIFICADOS

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `/app/backend/modules/comercial/services/impuestos_service.py` | NUEVO | Servicio de resolución de impuestos |
| `/app/docs/reports/FASE_1C_3G_C_MODELO_CANONICO_IMPUESTOS_EDARSAHUB.md` | NUEVO | Este reporte |

---

## 11. RIESGOS PENDIENTES

1. **Sincronización periódica:** Se requiere job nocturno para mantener actualizado el mapeo cuando se agreguen productos nuevos.

2. **UI de administración:** Los 62 productos NO_CONFIGURADO requieren interfaz para asignar configuración fiscal manual.

3. **Overrides:** La tabla de overrides está creada pero vacía. Se poblará cuando haya solicitudes de excepción fiscal autorizadas.

---

## 12. RECOMENDACIÓN PARA SIGUIENTE FASE

### FASE 1C-3G-D: Catálogo Comercial de Vinos

Ahora que el modelo canónico de impuestos está completo, se puede proceder con:

1. Crear tabla `Comercial_VinosCatalogo` para productos de vino
2. Integrar con el modelo de impuestos para aplicar IEPS correctamente
3. Crear reglas de precio por rango (FASE 1C-3G-E)

### FASE 1C-3G-F: UI Administración Fiscal

Para los 62 productos sin impuesto configurado:

1. Crear endpoint para listar productos NO_CONFIGURADO
2. Crear UI en frontend para asignar impuesto canónico
3. Validar que solo usuarios autorizados puedan modificar

---

**FIN DEL REPORTE**

**Siguiente Acción:** Esperar autorización para FASE 1C-3G-D (Catálogo de Vinos) o FASE 1C-3G-F (UI Administración Fiscal)
