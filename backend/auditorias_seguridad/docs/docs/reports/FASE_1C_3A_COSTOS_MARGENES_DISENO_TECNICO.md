# FASE 1C-3A: Diseño Técnico Costos y Márgenes / Recetas / Insumos / Precios

**Fecha**: 2026-05-24  
**Hora México**: 13:30 - 14:30  
**Ejecutado por**: Agente EDARSA HUB  
**Estado**: ✅ DISEÑO TÉCNICO COMPLETADO

---

## 1. Diagnóstico de Tablas Existentes en EDARSAHUB

### 1.1 Tablas de Productos (VACÍAS - Requieren sincronización)

| Tabla | Registros | Estado |
|-------|-----------|--------|
| `Producto_Catalogo` | 0 | ⚠ VACÍA |
| `Producto_Familias` | 0 | ⚠ VACÍA |
| `Producto_SubFamilias` | 0 | ⚠ VACÍA |
| `Producto_Lineas` | 0 | Verificar |
| `Producto_Marcas` | 0 | Verificar |
| `Producto_Presentaciones` | 0 | Verificar |

### 1.2 Tablas de Tablajería (EXISTENTES - Potencialmente reutilizables)

| Tabla | Registros | Uso Potencial |
|-------|-----------|---------------|
| `Operaciones_Tablaje_Plantillas` | 37 | Recetas de tablajería |
| `Operaciones_Tablaje_PlantillasDetalle` | 151 | Componentes de recetas |
| `Tablajeria_CosteoProduccion` | 2 | Costeo de producción |
| `Tablajeria_CosteoDetalle` | 5 | Detalle de costeo |
| `Operaciones_Tablaje_Rendimientos` | 6 | Rendimientos |
| `Operaciones_Tablaje_Costos` | ? | Costos de tablaje |

**NOTA**: Estas tablas son para TABLAJERÍA (producción industrial). NO son para productos de venta directa (menú de restaurante).

### 1.3 Tablas de Ventas/Precios

| Tabla | Registros | Estado |
|-------|-----------|--------|
| `Venta_ListasPrecios` | 1 | Parcial |
| `Venta_ListasPreciosDetalle` | 0 | ⚠ VACÍA |

### 1.4 Tablas Sync_* Existentes

| Tabla | Uso |
|-------|-----|
| `Sync_Ventas_Historicas` | Ventas históricas |
| `Sync_Ventas_PorHora` | Ventas por hora |
| `Sync_Ventas_PorDiaSemana` | Ventas por día |
| `Sync_Control_Ejecuciones` | Control de jobs |

**CONCLUSIÓN**: NO existen tablas de sincronización para productos, recetas ni insumos.

---

## 2. Tablas Reutilizables

### 2.1 REUTILIZAR PARCIALMENTE

| Tabla | Reutilizar Para | Condición |
|-------|-----------------|-----------|
| `Operaciones_Tablaje_Plantillas` | Recetas de tablajería únicamente | Solo para productos de tablaje, no menú |
| `Sync_Control_Ejecuciones` | Control de jobs | Agregar tipo SYNC_PRODUCTOS, SYNC_RECETAS |

### 2.2 NO REUTILIZAR (Propósito diferente)

| Tabla | Motivo |
|-------|--------|
| `Tablajeria_CosteoProduccion` | Es para costeo de órdenes de producción, no para catálogo de costos |
| `Tablajeria_CosteoDetalle` | Detalle de órdenes específicas |
| `Producto_Catalogo` | Estructura diferente a las fuentes, mejor crear tablas Sync_* específicas |

---

## 3. Tablas Faltantes (Propuestas)

### 3.1 Para Sincronización de Productos

```sql
-- Sync_Productos: Productos sincronizados desde fuentes remotas
-- Sync_Productos_Familias: Familias/grupos sincronizados
-- Sync_Productos_SubFamilias: Subfamilias/subgrupos sincronizados
-- Sync_Productos_Insumos: Insumos sincronizados
-- Sync_Productos_Recetas: Recetas (explosión producto→insumos)
-- Sync_Productos_Precios: Precios sincronizados
-- Sync_Productos_Costos: Costos sincronizados
```

---

## 4. Riesgo de Duplicidad

| Elemento | Tabla Existente | Tabla Propuesta | Riesgo | Mitigación |
|----------|-----------------|-----------------|--------|------------|
| Recetas tablaje | `Operaciones_Tablaje_Plantillas` | `Sync_Productos_Recetas` | BAJO | Tablas para propósitos diferentes: tablaje vs menú |
| Productos | `Producto_Catalogo` | `Sync_Productos` | MEDIO | Usar Sync_* como fuente viva, Producto_Catalogo como maestro consolidado |
| Familias | `Producto_Familias` | `Sync_Productos_Familias` | MEDIO | Mismo enfoque que productos |

**DECISIÓN ARQUITECTÓNICA**: 
- Las tablas `Sync_*` almacenan datos sincronizados por servidor/sistema.
- Las tablas `Producto_*` (si se usan) almacenarían un catálogo maestro consolidado.
- Para FASE 1C-3, usamos solo tablas `Sync_*` para evitar duplicidad.

---

## 5. Modelo Propuesto

### 5.1 Jerarquía de Datos

```
Nivel 1: FAMILIA (Grupo)
    └── Nivel 2: SUBFAMILIA (Subgrupo)
            └── Nivel 3: PRODUCTO
                    └── Nivel 4: RECETA (explosión)
                            └── Nivel 5: SUBRECETA (si aplica)
                                    └── Nivel 6: INSUMOS
```

### 5.2 Diagrama de Relaciones

```
┌─────────────────────────┐
│ Sync_Productos_Familias │
│  - FamiliaID (PK)       │
│  - ServerID (FK)        │
│  - CodigoFuente         │
│  - Nombre               │
└──────────┬──────────────┘
           │
           │ 1:N
           ▼
┌──────────────────────────┐
│ Sync_Productos_SubFamilias│
│  - SubFamiliaID (PK)     │
│  - FamiliaID (FK)        │
│  - ServerID (FK)         │
│  - CodigoFuente          │
│  - Nombre                │
└──────────┬───────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────┐
│     Sync_Productos      │
│  - ProductoID (PK)      │
│  - SubFamiliaID (FK)    │
│  - FamiliaID (FK)       │
│  - ServerID (FK)        │
│  - CodigoFuente         │
│  - Nombre               │
│  - PrecioVenta          │
│  - TipoProducto         │
│  - TieneReceta          │
└──────────┬──────────────┘
           │
           │ 1:1
           ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│  Sync_Productos_Precios │    │  Sync_Productos_Costos  │
│  - ProductoID (FK)      │    │  - ProductoID (FK)      │
│  - PrecioLista          │    │  - CostoReceta          │
│  - PrecioVenta          │    │  - CostoPromedio        │
│  - PrecioPromocion      │    │  - UltimoCosto          │
│  - MargenObjetivo       │    │  - CostoEstandar        │
└─────────────────────────┘    └─────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────┐
│  Sync_Productos_Recetas │
│  - RecetaID (PK)        │
│  - ProductoID (FK)      │
│  - InsumoID (FK)        │
│  - Cantidad             │
│  - UnidadMedida         │
│  - CostoUnitario        │
│  - CostoTotal           │
│  - EsSubReceta          │
│  - SubRecetaProductoID  │
└─────────────────────────┘
           │
           │ N:1
           ▼
┌─────────────────────────┐
│  Sync_Productos_Insumos │
│  - InsumoID (PK)        │
│  - ServerID (FK)        │
│  - CodigoFuente         │
│  - Nombre               │
│  - UnidadMedida         │
│  - Costo                │
│  - CostoPromedio        │
│  - UltimoCosto          │
│  - CostoEstandar        │
└─────────────────────────┘
```

---

## 6. DDL Propuesto (NO EJECUTAR - Solo diseño)

```sql
-- =====================================================
-- FASE 1C-3A: DDL PROPUESTO COSTOS Y MÁRGENES
-- ESTADO: DISEÑO - NO EJECUTAR SIN AUTORIZACIÓN
-- =====================================================

-- 1. Sync_Productos_Familias
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Sync_Productos_Familias')
CREATE TABLE Sync_Productos_Familias (
    FamiliaID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ServerID UNIQUEIDENTIFIER NOT NULL,
    EmpresaID UNIQUEIDENTIFIER NULL,
    UnidadNegocioID UNIQUEIDENTIFIER NULL,
    SystemType NVARCHAR(50) NOT NULL,  -- SOFTRESTAURANT, MPRO, ENTERPRISE
    CodigoFuente NVARCHAR(100) NOT NULL,
    Nombre NVARCHAR(200) NOT NULL,
    Descripcion NVARCHAR(500) NULL,
    Orden INT DEFAULT 0,
    Activo BIT DEFAULT 1,
    SyncRunID NVARCHAR(100) NULL,
    SyncedAtMexico DATETIME2 DEFAULT SYSDATETIME(),
    SourceStatus NVARCHAR(50) DEFAULT 'SYNCED',
    HashOrigen NVARCHAR(64) NULL,
    CONSTRAINT UK_Sync_Familias_Server_Codigo UNIQUE (ServerID, CodigoFuente)
);

-- 2. Sync_Productos_SubFamilias
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Sync_Productos_SubFamilias')
CREATE TABLE Sync_Productos_SubFamilias (
    SubFamiliaID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    FamiliaID UNIQUEIDENTIFIER NOT NULL,
    ServerID UNIQUEIDENTIFIER NOT NULL,
    SystemType NVARCHAR(50) NOT NULL,
    CodigoFuente NVARCHAR(100) NOT NULL,
    Nombre NVARCHAR(200) NOT NULL,
    Descripcion NVARCHAR(500) NULL,
    Orden INT DEFAULT 0,
    Activo BIT DEFAULT 1,
    SyncRunID NVARCHAR(100) NULL,
    SyncedAtMexico DATETIME2 DEFAULT SYSDATETIME(),
    SourceStatus NVARCHAR(50) DEFAULT 'SYNCED',
    HashOrigen NVARCHAR(64) NULL,
    CONSTRAINT FK_SubFamilias_Familia FOREIGN KEY (FamiliaID) REFERENCES Sync_Productos_Familias(FamiliaID),
    CONSTRAINT UK_Sync_SubFamilias_Server_Codigo UNIQUE (ServerID, CodigoFuente)
);

-- 3. Sync_Productos
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Sync_Productos')
CREATE TABLE Sync_Productos (
    ProductoID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ServerID UNIQUEIDENTIFIER NOT NULL,
    EmpresaID UNIQUEIDENTIFIER NULL,
    UnidadNegocioID UNIQUEIDENTIFIER NULL,
    SystemType NVARCHAR(50) NOT NULL,
    CodigoFuente NVARCHAR(100) NOT NULL,
    CodigoBarras NVARCHAR(100) NULL,
    Nombre NVARCHAR(300) NOT NULL,
    NombreCorto NVARCHAR(100) NULL,
    Descripcion NVARCHAR(1000) NULL,
    FamiliaID UNIQUEIDENTIFIER NULL,
    SubFamiliaID UNIQUEIDENTIFIER NULL,
    FamiliaCodigoFuente NVARCHAR(100) NULL,
    SubFamiliaCodigoFuente NVARCHAR(100) NULL,
    TipoProducto NVARCHAR(50) NULL,  -- VENTA, INSUMO, PRODUCCION, COMPUESTO
    EsVendible BIT DEFAULT 1,
    EsInventariable BIT DEFAULT 0,
    EsCompuesto BIT DEFAULT 0,
    TieneReceta BIT DEFAULT 0,
    TieneSubRecetas BIT DEFAULT 0,
    UnidadVenta NVARCHAR(20) NULL,
    UnidadInventario NVARCHAR(20) NULL,
    -- Precios
    PrecioVenta DECIMAL(18,4) DEFAULT 0,
    PrecioSinImpuestos DECIMAL(18,4) DEFAULT 0,
    TasaImpuesto DECIMAL(5,2) DEFAULT 0,
    -- Costos (calculados desde receta o insumo directo)
    CostoReceta DECIMAL(18,4) DEFAULT 0,
    CostoPromedio DECIMAL(18,4) DEFAULT 0,
    UltimoCosto DECIMAL(18,4) DEFAULT 0,
    CostoEstandar DECIMAL(18,4) DEFAULT 0,
    -- Márgenes calculados
    MargenBrutoPesos DECIMAL(18,4) DEFAULT 0,
    MargenBrutoPorcentaje DECIMAL(5,2) DEFAULT 0,
    MargenObjetivo DECIMAL(5,2) NULL,
    DiferenciaMargenObjetivo DECIMAL(5,2) NULL,
    -- Ventas (para participación en mix)
    VentaTotalPeriodo DECIMAL(18,4) DEFAULT 0,
    UnidadesVendidasPeriodo INT DEFAULT 0,
    ParticipacionMix DECIMAL(5,2) DEFAULT 0,
    -- Metadatos
    ImagenURL NVARCHAR(500) NULL,
    Activo BIT DEFAULT 1,
    SyncRunID NVARCHAR(100) NULL,
    SyncedAtMexico DATETIME2 DEFAULT SYSDATETIME(),
    FechaUltimoCosteo DATETIME2 NULL,
    SourceStatus NVARCHAR(50) DEFAULT 'SYNCED',
    HashOrigen NVARCHAR(64) NULL,
    CONSTRAINT FK_Productos_Familia FOREIGN KEY (FamiliaID) REFERENCES Sync_Productos_Familias(FamiliaID),
    CONSTRAINT FK_Productos_SubFamilia FOREIGN KEY (SubFamiliaID) REFERENCES Sync_Productos_SubFamilias(SubFamiliaID),
    CONSTRAINT UK_Sync_Productos_Server_Codigo UNIQUE (ServerID, CodigoFuente)
);

-- 4. Sync_Productos_Insumos
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Sync_Productos_Insumos')
CREATE TABLE Sync_Productos_Insumos (
    InsumoID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ServerID UNIQUEIDENTIFIER NOT NULL,
    EmpresaID UNIQUEIDENTIFIER NULL,
    SystemType NVARCHAR(50) NOT NULL,
    CodigoFuente NVARCHAR(100) NOT NULL,
    Nombre NVARCHAR(300) NOT NULL,
    Descripcion NVARCHAR(500) NULL,
    GrupoInsumoCodigoFuente NVARCHAR(100) NULL,
    GrupoInsumoNombre NVARCHAR(200) NULL,
    UnidadMedida NVARCHAR(20) NOT NULL,
    -- Costos
    Costo DECIMAL(18,6) DEFAULT 0,
    CostoPromedio DECIMAL(18,6) DEFAULT 0,
    UltimoCosto DECIMAL(18,6) DEFAULT 0,
    CostoEstandar DECIMAL(18,6) DEFAULT 0,
    CostoConImpuestos DECIMAL(18,6) DEFAULT 0,
    -- Propiedades
    EsElaborado BIT DEFAULT 0,
    RendimientoElaborado DECIMAL(5,2) NULL,
    MermaPorcentaje DECIMAL(5,2) NULL,
    -- Metadatos
    Activo BIT DEFAULT 1,
    SyncRunID NVARCHAR(100) NULL,
    SyncedAtMexico DATETIME2 DEFAULT SYSDATETIME(),
    FechaUltimoCosto DATETIME2 NULL,
    SourceStatus NVARCHAR(50) DEFAULT 'SYNCED',
    HashOrigen NVARCHAR(64) NULL,
    CONSTRAINT UK_Sync_Insumos_Server_Codigo UNIQUE (ServerID, CodigoFuente)
);

-- 5. Sync_Productos_Recetas (explosión producto→insumos)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Sync_Productos_Recetas')
CREATE TABLE Sync_Productos_Recetas (
    RecetaDetalleID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ProductoID UNIQUEIDENTIFIER NOT NULL,
    ServerID UNIQUEIDENTIFIER NOT NULL,
    SystemType NVARCHAR(50) NOT NULL,
    -- Componente (puede ser insumo o subreceta)
    InsumoID UNIQUEIDENTIFIER NULL,
    SubRecetaProductoID UNIQUEIDENTIFIER NULL,  -- Si es subreceta
    ComponenteCodigoFuente NVARCHAR(100) NOT NULL,
    ComponenteNombre NVARCHAR(300) NOT NULL,
    TipoComponente NVARCHAR(50) NOT NULL,  -- INSUMO, SUBRECETA, ELABORADO
    -- Cantidades
    Cantidad DECIMAL(18,6) NOT NULL,
    UnidadMedida NVARCHAR(20) NOT NULL,
    RendimientoElaborado DECIMAL(5,2) NULL,
    -- Costos
    CostoUnitario DECIMAL(18,6) DEFAULT 0,
    CostoTotal DECIMAL(18,6) DEFAULT 0,
    PorcentajeCostoTotal DECIMAL(5,2) DEFAULT 0,
    -- Nivel en árbol de explosión
    NivelExplosion INT DEFAULT 1,
    OrdenVisual INT DEFAULT 0,
    -- Metadatos
    Activo BIT DEFAULT 1,
    SyncRunID NVARCHAR(100) NULL,
    SyncedAtMexico DATETIME2 DEFAULT SYSDATETIME(),
    SourceStatus NVARCHAR(50) DEFAULT 'SYNCED',
    CONSTRAINT FK_Recetas_Producto FOREIGN KEY (ProductoID) REFERENCES Sync_Productos(ProductoID),
    CONSTRAINT FK_Recetas_Insumo FOREIGN KEY (InsumoID) REFERENCES Sync_Productos_Insumos(InsumoID),
    CONSTRAINT FK_Recetas_SubReceta FOREIGN KEY (SubRecetaProductoID) REFERENCES Sync_Productos(ProductoID)
);

-- 6. Índices para rendimiento
CREATE INDEX IX_Sync_Productos_ServerID ON Sync_Productos(ServerID);
CREATE INDEX IX_Sync_Productos_FamiliaID ON Sync_Productos(FamiliaID);
CREATE INDEX IX_Sync_Productos_SubFamiliaID ON Sync_Productos(SubFamiliaID);
CREATE INDEX IX_Sync_Productos_TieneReceta ON Sync_Productos(TieneReceta);
CREATE INDEX IX_Sync_Productos_Recetas_ProductoID ON Sync_Productos_Recetas(ProductoID);
CREATE INDEX IX_Sync_Productos_Insumos_ServerID ON Sync_Productos_Insumos(ServerID);
```

---

## 7. Diseño de Job sync_recetas.py

### 7.1 Estructura del Job

```python
# /app/backend/modules/sync_historicos/sync_recetas.py

class SyncRecetasConfig:
    """Configuración para sincronización de recetas"""
    server_ids: List[str]
    sync_familias: bool = True
    sync_productos: bool = True
    sync_insumos: bool = True
    sync_recetas: bool = True
    dry_run: bool = True
    
class SyncRecetasResult:
    """Resultado de sincronización"""
    sync_run_id: str
    success: bool
    is_dry_run: bool
    total_familias: int
    total_productos: int
    total_insumos: int
    total_recetas: int
    registros_insertados: int
    registros_actualizados: int
    registros_error: int
    duration_seconds: float
    resultados_por_servidor: Dict

# Funciones principales
def ejecutar_sync_recetas_dry_run(server_ids, ...) -> SyncRecetasResult
def ejecutar_sync_recetas_real(server_ids, ...) -> SyncRecetasResult
```

### 7.2 Flujo de Sincronización

```
1. Validar configuración
2. Para cada servidor:
   a. Detectar tipo de sistema (SoftRestaurant/MPRO/Enterprise)
   b. Obtener conexión descifrada
   c. Sincronizar en orden:
      i.   Familias/Grupos
      ii.  SubFamilias/SubGrupos
      iii. Insumos
      iv.  Productos
      v.   Recetas (explosión producto→insumos)
   d. Calcular costos de recetas
   e. Calcular márgenes
3. Registrar en Sync_Control_Ejecuciones
4. Retornar resultado
```

### 7.3 Queries por Sistema

#### SoftRestaurant

```sql
-- Familias (grupos)
SELECT idgrupo, descripcion, clasificacion, prioridad
FROM grupos
WHERE descripcion IS NOT NULL

-- SubFamilias (subgrupos)
SELECT s.idsubgrupo, s.descripcion, gs.idgrupo
FROM subgrupos s
LEFT JOIN grupossubgrupos gs ON s.idsubgrupo = gs.idsubgrupo

-- Productos
SELECT p.idproducto, p.descripcion, p.idgrupo, p.nombrecorto,
       pd.precio, pd.preciosinimpuestos, pd.impuesto1
FROM productos p
JOIN productosdetalle pd ON p.idproducto = pd.idproducto
WHERE p.descripcion IS NOT NULL

-- Insumos
SELECT i.idinsumo, i.descripcion, i.unidad, i.elaborado, i.rendimientoelaborado,
       id.costo, id.costopromedio, id.costoestandar, id.costoconimpuestos
FROM insumos i
JOIN insumosdetalle id ON i.idinsumo = id.idinsumo

-- RECETAS DE PRODUCTOS (tabla costos)
SELECT c.idproducto, c.idinsumo, c.cantidad,
       i.unidad, id.costo, id.costopromedio
FROM costos c
JOIN insumos i ON c.idinsumo = i.idinsumo
LEFT JOIN insumosdetalle id ON c.idinsumo = id.idinsumo

-- RECETAS DE INSUMOS ELABORADOS (tabla elaborados)
SELECT e.idelaborado, e.idinsumo, e.cantidad
FROM elaborados e
```

#### MPRO

```sql
-- Familias
SELECT Fm_Cve_Familia, Fm_Descripcion
FROM Familia
WHERE Es_Cve_Estado = 'A'

-- SubFamilias
SELECT Sf_Cve_SubFamilia, Sf_Descripcion, Fm_Cve_Familia
FROM SubFamilia
WHERE Es_Cve_Estado = 'A'

-- Productos
SELECT p.Pr_Cve_Producto, p.Pr_Descripcion, p.Pr_Descripcion_Corta,
       p.Fm_Cve_Familia, p.Sf_Cve_SubFamilia, p.Pr_Tipo_Producto,
       pp.Pp_Precio_Lista
FROM Producto p
LEFT JOIN Producto_Precio pp ON p.Pr_Cve_Producto = pp.Pr_Cve_Producto
WHERE p.Es_Cve_Estado = 'A'

-- Insumos/Existencias (costos)
SELECT e.Pr_Cve_Producto, e.Ex_Ultimo_Costo, e.Ex_Costo_Promedio, 
       e.Ex_Costo_Estandar, e.Ex_Unidad_Costo
FROM Existencia e
WHERE e.Es_Cve_Estado = 'A'

-- Recetas (Fórmulas de producción)
SELECT fp.Pr_Cve_Producto, fp.Fp_ID, fp.Fp_Descripcion, fp.Fp_Rendimiento,
       fpd.Fpd_Producto, fpd.Fpd_Cantidad, fpd.Fpd_Unidad, fpd.Fpd_Costo
FROM Formula_Produccion fp
JOIN Formula_Produccion_Detalle fpd 
    ON fp.Pr_Cve_Producto = fpd.Pr_Cve_Producto AND fp.Fp_ID = fpd.Fp_ID
WHERE fp.Es_Cve_Estado = 'A'
```

---

## 8. Fuentes por Sistema

### 8.1 SoftRestaurant

| Dato | Tabla Fuente | Columnas Clave |
|------|-------------|----------------|
| Familias | `grupos` | idgrupo, descripcion |
| SubFamilias | `subgrupos` + `grupossubgrupos` | idsubgrupo, descripcion, idgrupo |
| Productos | `productos` + `productosdetalle` | idproducto, descripcion, precio |
| Insumos | `insumos` + `insumosdetalle` | idinsumo, descripcion, costo, costopromedio |
| **Recetas de PRODUCTOS** | `costos` | idproducto, idinsumo, cantidad |
| **Recetas de INSUMOS ELABORADOS** | `elaborados` | idelaborado, idinsumo, cantidad |

**Estado de datos (LA ESTELAR)**:
- 46 grupos
- 63 subgrupos
- 611 productos
- 1199 insumos
- **1,583 líneas de receta** en tabla `costos`
- **559 productos con receta** (91% del catálogo)
- **615 líneas de elaborados** (recetas de insumos compuestos)

**CORRECCIÓN IMPORTANTE**: Las recetas NO están en `explosioninsumosdetalle` (vacía).
Las recetas están en la tabla `costos` que relaciona producto → insumos con cantidad.

### 8.2 MPRO (ManagmentPro)

| Dato | Tabla Fuente | Columnas Clave |
|------|-------------|----------------|
| Familias | `Familia` | Fm_Cve_Familia, Fm_Descripcion |
| SubFamilias | `SubFamilia` | Sf_Cve_SubFamilia, Sf_Descripcion, Fm_Cve_Familia |
| Productos | `Producto` + `Producto_Precio` | Pr_Cve_Producto, Pr_Descripcion, Pp_Precio_Lista |
| Costos | `Existencia` | Pr_Cve_Producto, Ex_Ultimo_Costo, Ex_Costo_Promedio |
| Recetas | `Formula_Produccion` + `Formula_Produccion_Detalle` | Pr_Cve_Producto, Fp_ID, Fpd_Producto, Fpd_Cantidad |

**Estado de datos (ManagmentPro)**:
- 81 familias
- 108 subfamilias
- 7,957 productos
- 7,957 precios
- 554 fórmulas de producción
- 3,103 detalles de fórmula

### 8.3 Enterprise

| Consideración | Detalle |
|---------------|---------|
| Tipo de sistema | Variante de SoftRestaurant (backoffice) |
| Estructura esperada | Similar a SoftRestaurant |
| Estado | Requiere investigación adicional |
| Recomendación | Tratar como SoftRestaurant inicialmente |

---

## 9. Mapeo Producto/Familia/SubFamilia/Receta/Insumo

### 9.1 Mapeo SoftRestaurant

```
grupos.idgrupo ────────────────► Sync_Productos_Familias.CodigoFuente
    │
    └──► grupossubgrupos.idgrupo
              │
              └──► subgrupos.idsubgrupo ──► Sync_Productos_SubFamilias.CodigoFuente
                        │
                        └──► productos.idgrupo ──► Sync_Productos.CodigoFuente
                                    │
                                    └──► explosioninsumosdetalle.idproducto
                                              │
                                              └──► insumos.idinsumo ──► Sync_Productos_Insumos.CodigoFuente
```

### 9.2 Mapeo MPRO

```
Familia.Fm_Cve_Familia ────────► Sync_Productos_Familias.CodigoFuente
    │
    └──► SubFamilia.Fm_Cve_Familia
              │
              └──► Producto.Fm_Cve_Familia + Sf_Cve_SubFamilia ──► Sync_Productos
                        │
                        └──► Formula_Produccion.Pr_Cve_Producto
                                    │
                                    └──► Formula_Produccion_Detalle.Fpd_Producto ──► Insumo o SubReceta
```

### 9.3 Compatibilidad entre Sistemas

| Aspecto | SoftRestaurant | MPRO | Compatible |
|---------|----------------|------|------------|
| ID de producto | VARCHAR (ej: A085003) | NVARCHAR (ej: 0000000695) | ✓ Homologable |
| Familias | 1 nivel (grupos) | 1 nivel (Familia) | ✓ Equivalente |
| SubFamilias | 1 nivel (subgrupos) | 1 nivel (SubFamilia) | ✓ Equivalente |
| Estructura de receta | explosioninsumosdetalle | Formula_Produccion_Detalle | ✓ Equivalente |
| Costos | insumosdetalle | Existencia | ✓ Equivalente |
| Precios | productosdetalle | Producto_Precio | ✓ Equivalente |

---

## 10. Diseño de Costos

### 10.1 Tipos de Costo

| Tipo | Descripción | Fuente | Uso |
|------|-------------|--------|-----|
| `CostoReceta` | Suma de costos de insumos según receta | Calculado | Principal para márgenes |
| `CostoPromedio` | Promedio ponderado de compras | insumosdetalle / Existencia | Referencia |
| `UltimoCosto` | Último precio de compra | insumosdetalle / Existencia | Referencia |
| `CostoEstandar` | Costo objetivo definido | insumosdetalle / Existencia | Comparación |

### 10.2 Cálculo de Costo de Receta

```python
def calcular_costo_receta(producto_id: str) -> Decimal:
    """
    Calcula el costo total de la receta de un producto.
    
    Si el producto tiene subrecetas:
    1. Primero calcular costo de cada subreceta recursivamente
    2. Luego sumar todos los componentes
    
    Fórmula:
    CostoReceta = Σ (Cantidad_insumo × CostoUnitario_insumo)
    
    Para insumos elaborados:
    CostoReal = CostoBase × (1 / RendimientoElaborado)
    """
    total = Decimal('0')
    for componente in obtener_componentes_receta(producto_id):
        if componente.es_subreceta:
            costo_unit = calcular_costo_receta(componente.subreceta_id)
        else:
            costo_unit = componente.costo_unitario
            if componente.es_elaborado and componente.rendimiento:
                costo_unit = costo_unit / componente.rendimiento
        total += componente.cantidad * costo_unit
    return total
```

### 10.3 Prioridad de Costo

```
1. CostoReceta (si tiene receta)
2. CostoPromedio (si > 0)
3. UltimoCosto (si > 0)
4. CostoEstandar (fallback)
5. 0 (sin costo disponible → ALERTA)
```

---

## 11. Diseño de Márgenes

### 11.1 Fórmulas de Cálculo

```
MargenBrutoPesos = PrecioVenta - CostoTotal
MargenBrutoPorcentaje = (MargenBrutoPesos / PrecioVenta) × 100
DiferenciaMargenObjetivo = MargenBrutoPorcentaje - MargenObjetivo
```

### 11.2 Indicadores de Alerta

| Indicador | Condición | Color |
|-----------|-----------|-------|
| CRÍTICO | Margen < 30% | 🔴 Rojo |
| BAJO | Margen 30-45% | 🟡 Amarillo |
| NORMAL | Margen 45-60% | 🟢 Verde |
| ALTO | Margen > 60% | 🔵 Azul |
| SIN_COSTO | Costo = 0 | ⚫ Gris (revisar) |

### 11.3 Recomendaciones de Acción

| Situación | Recomendación |
|-----------|---------------|
| Margen < MargenObjetivo | "Revisar precio o costo" |
| Costo sin actualizar > 30 días | "Actualizar costo" |
| Sin receta | "Crear receta para costeo preciso" |
| Margen muy alto (> 80%) | "Verificar competitividad" |

---

## 12. Diseño de Endpoints

### 12.1 Endpoints Propuestos

```python
# Router: /api/comercial/costos-margenes

@router.get("/resumen")
async def costos_margenes_resumen(
    server_id: str,
    empresa_id: str = None,
    unidad_id: str = None,
    current_user: Dict = Depends(get_current_user)
) -> CostosMaRgenesResumenResponse:
    """
    KPIs generales:
    - Total productos con receta
    - Margen promedio
    - Productos con margen bajo
    - Última sincronización
    """

@router.get("/familias")
async def costos_margenes_familias(
    server_id: str,
    ...
) -> List[FamiliaConMargenResponse]:
    """
    Lista de familias con métricas agregadas:
    - Nombre familia
    - Total productos
    - Margen promedio
    - Venta total
    """

@router.get("/productos")
async def costos_margenes_productos(
    server_id: str,
    familia_id: str = None,
    subfamilia_id: str = None,
    busqueda: str = None,
    orden: str = "nombre",  # nombre, precio, margen
    direccion: str = "asc",
    pagina: int = 1,
    limite: int = 50,
    ...
) -> ProductosCostosMargenesResponse:
    """
    Lista paginada de productos con:
    - Familia, SubFamilia
    - Precio venta
    - Costo receta
    - Utilidad
    - Margen %
    - Indicador de alerta
    - Tiene receta (expandible)
    """

@router.get("/productos/{producto_id}")
async def costos_margenes_producto_detalle(
    producto_id: str,
    server_id: str,
    ...
) -> ProductoDetalleResponse:
    """
    Detalle completo del producto:
    - Info general
    - Todos los costos
    - Margen histórico
    - Participación en mix
    """

@router.get("/productos/{producto_id}/receta")
async def costos_margenes_receta(
    producto_id: str,
    server_id: str,
    expandir_subrecetas: bool = False,
    ...
) -> RecetaDetalleResponse:
    """
    Receta completa:
    - Lista de insumos
    - Cantidad, unidad
    - Costo unitario
    - Costo total
    - % del costo total
    - SubRecetas expandibles
    """

@router.get("/simulacion")
async def costos_margenes_simulacion(
    producto_id: str,
    server_id: str,
    nuevo_precio: Decimal = None,
    nuevo_costo: Decimal = None,
    ...
) -> SimulacionResponse:
    """
    Simulador de precios (solo lectura):
    - Margen actual
    - Margen con nuevo precio
    - Precio sugerido para margen objetivo
    """

@router.get("/sync-status")
async def costos_margenes_sync_status(
    server_id: str,
    ...
) -> SyncStatusResponse:
    """
    Estado de sincronización:
    - Última ejecución
    - Registros sincronizados
    - Errores
    - Próxima ejecución sugerida
    """
```

### 12.2 Modelos de Respuesta

```python
class CostosMargenesResumenResponse(BaseModel):
    server_id: str
    server_name: str
    source_type: str  # EDARSAHUB_SQL
    source_status: str  # SUCCESS, STALE, SIN_DATOS
    source_message: str
    ultima_sincronizacion: datetime
    
    total_familias: int
    total_productos: int
    productos_con_receta: int
    productos_sin_receta: int
    
    margen_promedio: Decimal
    margen_minimo: Decimal
    margen_maximo: Decimal
    
    productos_margen_critico: int  # < 30%
    productos_margen_bajo: int     # 30-45%
    productos_sin_costo: int
    
class ProductoCostosMargenesResponse(BaseModel):
    producto_id: str
    codigo: str
    nombre: str
    familia: str
    subfamilia: str
    
    precio_venta: Decimal
    costo_receta: Decimal
    costo_promedio: Decimal
    ultimo_costo: Decimal
    
    utilidad: Decimal
    margen_porcentaje: Decimal
    margen_objetivo: Decimal
    diferencia_objetivo: Decimal
    
    indicador_alerta: str  # CRITICO, BAJO, NORMAL, ALTO
    tiene_receta: bool
    tiene_subrecetas: bool
    
    venta_periodo: Decimal
    unidades_vendidas: int
    participacion_mix: Decimal
```

---

## 13. Diseño de Frontend

### 13.1 Estructura de Pantalla

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Costos y Márgenes                                            [Exportar] │
├─────────────────────────────────────────────────────────────────────────┤
│ [Empresa ▼] [Unidad ▼] [Familia ▼] [SubFamilia ▼] [Tipo Costo ▼]       │
│ [Buscar producto...                              ] [Actualizar]         │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│ │ 📦 548      │ │ 📈 52.3%    │ │ ⚠️ 23       │ │ 🕐 Hace 2h  │        │
│ │ Productos   │ │ Margen Prom │ │ Margen Bajo │ │ Última Sync │        │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │
├─────────────────────────────────────────────────────────────────────────┤
│ Ordenar: [Nombre ▼] [Precio ▼] [Margen ▼]         Fuente: EDARSAHUB SQL│
├─────────────────────────────────────────────────────────────────────────┤
│ ┌───┬──────────┬──────────┬────────┬────────────────────────────┬──────┤
│ │   │ FAMILIA  │ SUBFAM.  │ PRECIO │ NOMBRE                     │MARGEN│
│ ├───┼──────────┼──────────┼────────┼────────────────────────────┼──────┤
│ │ ▶ │ALIMENTOS │ENTRADAS  │ $350   │ GUACAMOLE AGUACATE         │65.9% │
│ │   │          │          │        │ ├─ Aguacate Hass 300gr $12 │      │
│ │   │          │          │        │ └─ Antioxidante 5ml $0.50  │      │
│ ├───┼──────────┼──────────┼────────┼────────────────────────────┼──────┤
│ │ ▶ │ALIMENTOS │PLATO FTE │ $280   │ CAMARONES A LA DIABLA      │58.2% │
│ ├───┼──────────┼──────────┼────────┼────────────────────────────┼──────┤
│ │   │BEBIDAS   │CERVEZAS  │ $45    │ CORONA                     │🔴42%│
│ ├───┼──────────┼──────────┼────────┼────────────────────────────┼──────┤
│ │   │BEBIDAS   │WHISKIS   │ $180   │ CHIVAS REGAL 12 AÑOS       │72.1% │
│ └───┴──────────┴──────────┴────────┴────────────────────────────┴──────┘
├─────────────────────────────────────────────────────────────────────────┤
│ Mostrando 1-50 de 548                              [◀] [1] [2] ... [▶]  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Interacciones

| Acción | Comportamiento |
|--------|----------------|
| Click en ▶ | Expandir/Colapsar receta del producto |
| Doble click en producto | Abrir modal con detalle completo |
| Click en header columna | Ordenar por esa columna |
| Click en "Exportar" | Descargar CSV/Excel |
| Click en "Actualizar" | Refrescar datos desde EDARSAHUB |
| Hover en margen rojo | Tooltip con recomendación |

### 13.3 Estados de Pantalla

| Estado | Condición | Mensaje |
|--------|-----------|---------|
| SUCCESS | Datos frescos | (sin mensaje, mostrar datos) |
| STALE | Última sync > 24h | "Datos desactualizados. Última sync: [fecha]" |
| SIN_DATOS | 0 productos | "No hay datos sincronizados para esta unidad" |
| LOADING | Cargando | Skeleton loading |
| ERROR | Error de API | "Error al cargar datos. Intente de nuevo" |

---

## 14. Diseño RBAC

### 14.1 Permisos Propuestos

| Permiso | Descripción | Nivel |
|---------|-------------|-------|
| `comercial.costos_margenes.ver` | Ver pantalla de costos/márgenes | Básico |
| `comercial.costos_margenes.ver_receta` | Ver detalle de recetas | Medio |
| `comercial.costos_margenes.ver_insumos` | Ver insumos y sus costos | Medio |
| `comercial.costos_margenes.ver_costos` | Ver costos reales (no solo márgenes) | Alto |
| `comercial.costos_margenes.exportar` | Exportar a CSV/Excel | Medio |
| `comercial.costos_margenes.simular_precio` | Usar simulador de precios | Alto |
| `comercial.costos_margenes.configurar_margen_objetivo` | Configurar márgenes objetivo | Admin |
| `comercial.costos_margenes.ejecutar_sync` | Ejecutar sincronización manual | Admin |

### 14.2 Niveles de Usuario

| Rol | Permisos |
|-----|----------|
| Vendedor | ver (solo márgenes, sin costos) |
| Supervisor | ver, ver_receta, exportar |
| Gerente | ver, ver_receta, ver_insumos, ver_costos, exportar, simular_precio |
| Director | Todos |
| Admin | Todos + configurar + ejecutar_sync |

---

## 15. Reglas NO-LIVE

### 15.1 Arquitectura de Datos

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FUENTES REMOTAS                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ SoftRestaurant│  │    MPRO      │  │  Enterprise  │                  │
│  │  (productos,  │  │  (Producto,  │  │  (similar a  │                  │
│  │   insumos,    │  │   Formula,   │  │     SR)      │                  │
│  │   recetas)    │  │  Existencia) │                  │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                  │                  │                          │
│         └──────────────────┼──────────────────┘                          │
│                            │                                             │
│                    ┌───────▼───────┐                                     │
│                    │  sync_recetas │ ← Job de sincronización             │
│                    │     .py       │   (ÚNICA conexión permitida)        │
│                    └───────┬───────┘                                     │
│                            │                                             │
└────────────────────────────┼─────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        EDARSAHUB SQL                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Sync_Productos_Familias    Sync_Productos    Sync_Productos_    │   │
│  │  Sync_Productos_SubFamilias Sync_Productos_   Recetas            │   │
│  │                             Insumos                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Endpoints              │ ← Solo lectura EDARSAHUB
                    │  /api/comercial/        │
                    │  costos-margenes/*      │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Frontend               │ ← Solo consume endpoints
                    │  /comercial/            │
                    │  costos-margenes        │
                    └─────────────────────────┘
```

### 15.2 Reglas Estrictas

| Regla | Descripción | Verificación |
|-------|-------------|--------------|
| NO conexión remota en endpoint | Endpoints NO pueden conectarse a SoftRestaurant/MPRO/Enterprise | Code review |
| NO conexión remota en frontend | Frontend NO puede conectarse a APIs externas | Code review |
| NO MongoDB | Cero dependencias de MongoDB | Grep en código |
| NO fallback remoto | Si EDARSAHUB no tiene datos → SIN_DATOS, NO conectar remoto | Test unitario |
| NO cache como fuente | Cache solo para performance, no como fuente de verdad | Code review |
| Job es única excepción | Solo sync_recetas.py puede conectar a fuentes remotas | Arquitectura |

---

## 16. Riesgos Identificados

| # | Riesgo | Severidad | Mitigación |
|---|--------|-----------|------------|
| 1 | ~~explosioninsumosdetalle vacía en SoftRestaurant~~ | ~~ALTA~~ | ✅ RESUELTO: Usar tabla `costos` que tiene 1,583 líneas de receta |
| 2 | Falta de recetas para productos de venta | BAJA | 559 de 611 productos (91%) tienen receta. Los 52 restantes mostrarán "SIN_RECETA" |
| 3 | Costos desactualizados | MEDIA | Incluir fecha de último costeo y alertar si > 30 días |
| 4 | Diferencias de estructura entre sistemas | MEDIA | Mapeo flexible con CodigoFuente + SystemType |
| 5 | Volumen de datos alto (8K+ productos MPRO) | MEDIA | Paginación, índices, carga incremental |
| 6 | Enterprise sin analizar | BAJA | Tratar como SoftRestaurant, ajustar si necesario |
| 7 | SubRecetas recursivas infinitas | BAJA | Limitar niveles de explosión (max 5) |
| 8 | Insumos elaborados requieren sub-explosión | MEDIA | Usar tabla `elaborados` para expandir insumos compuestos |

---

## 17. Pruebas Propuestas

### 17.1 Pruebas de Sincronización

| Test | Descripción | Criterio de Éxito |
|------|-------------|-------------------|
| DRY-RUN SoftRestaurant | Ejecutar sync sin escribir | Retorna registros identificados sin error |
| DRY-RUN MPRO | Ejecutar sync sin escribir | Retorna registros identificados sin error |
| REAL SoftRestaurant | Ejecutar sync con escritura | Datos en Sync_Productos_* |
| REAL MPRO | Ejecutar sync con escritura | Datos en Sync_Productos_* |
| Cálculo de costos | Calcular costo de receta | Costo = Σ(insumos × cantidad) |
| Cálculo de márgenes | Calcular margen | Margen = (Precio - Costo) / Precio × 100 |

### 17.2 Pruebas de Endpoint

| Test | Endpoint | Criterio |
|------|----------|----------|
| GET resumen | /costos-margenes/resumen | Retorna KPIs correctos |
| GET familias | /costos-margenes/familias | Retorna lista de familias |
| GET productos | /costos-margenes/productos | Retorna lista paginada |
| GET receta | /costos-margenes/productos/{id}/receta | Retorna componentes de receta |
| Sin permiso | Cualquiera sin auth | 401/403 |
| Server inválido | Cualquiera con server_id malo | Error controlado |

### 17.3 Pruebas NO-LIVE

| Test | Descripción | Criterio |
|------|-------------|----------|
| Endpoint sin conexión remota | Desconectar fuentes remotas | Endpoint retorna datos de EDARSAHUB |
| Sin datos EDARSAHUB | Vaciar tablas Sync_* | Retorna source_status=SIN_DATOS |
| Datos stale | Última sync > 24h | Retorna source_status=STALE |

---

## 18. Recomendación para FASE 1C-3B

### PRÓXIMOS PASOS AUTORIZADOS (tras aprobación)

#### FASE 1C-3B: Creación de Tablas y Job de Sincronización
1. Ejecutar DDL idempotente para crear tablas Sync_Productos_*
2. Crear archivo sync_recetas.py con estructura de job
3. Ejecutar DRY-RUN en servidor de prueba
4. Ejecutar sincronización real controlada
5. Validar datos en EDARSAHUB SQL

#### FASE 1C-3C: Endpoints
1. Crear endpoints en /api/comercial/costos-margenes/
2. Implementar lógica de cálculo de costos y márgenes
3. Implementar filtros y paginación
4. Validar permisos RBAC

#### FASE 1C-3D: Frontend
1. Crear página /comercial/costos-margenes
2. Implementar tabla jerárquica expandible
3. Implementar filtros y ordenamiento
4. Implementar modal de detalle y simulador

#### FASE 1C-3E: Validación Final
1. Pruebas de no regresión
2. Documentación de usuario
3. Capacitación

### CRITERIOS DE APROBACIÓN PARA 1C-3B

Antes de autorizar FASE 1C-3B, confirmar:

1. ✅ DDL propuesto es correcto y completo
2. ✅ No hay riesgo de duplicidad con tablas existentes
3. ✅ Estructura de job sync_recetas.py es adecuada
4. ✅ Mapeo de fuentes es correcto
5. ✅ Diseño de endpoints cubre casos de uso
6. ✅ Diseño de frontend cumple requerimientos del usuario
7. ✅ Permisos RBAC son apropiados
8. ✅ Reglas NO-LIVE están claras

---

## 19. Estructura Correcta de Recetas en SoftRestaurant

### Hallazgo Corregido

El usuario indicó que las recetas en SoftRestaurant están en `productosdetalle` con referencia a `insumospresentaciones`. Tras investigación:

**Estructura REAL de recetas:**

| Tabla | Contenido | Registros | Uso |
|-------|-----------|-----------|-----|
| `costos` | Recetas de PRODUCTOS (producto → insumos) | 1,583 | ⭐ PRINCIPAL |
| `elaborados` | Recetas de INSUMOS ELABORADOS (sub-recetas) | 615 | Insumos compuestos |
| `insumospresentaciones` | Tipos/formatos de insumo | 1,927 | NO es receta |
| `explosioninsumosdetalle` | Vacía en LA ESTELAR | 0 | No usar |

### Ejemplo de Receta Real (tabla `costos`)

```
[46001] QUESADILLA DE FLOR DE CALABAZA - COSTO TOTAL: $30.15
   ├─ A CREMA ENTERA/ACIDA GR     | 50gr  × $0.0682 = $3.41
   ├─ A MASA AMARILLA GR          | 90gr  × $0.0220 = $1.98
   ├─ A CILANTRO CRIOLLO GR       | 1gr   × $0.0900 = $0.09
   ├─ A FLOR DE CALABAZA          | 20gr  × $0.1600 = $3.20
   ├─ A QUESO COTIJA GR           | 20gr  × $0.2760 = $5.52
   ├─ A QUESO OAXACA GR           | 100gr × $0.1520 = $15.20
   └─ B CHAPULIN SECO GR          | 1gr   × $0.7500 = $0.75
```

### Estadísticas Actualizadas

- **559 de 611 productos tienen receta** (91%)
- **1,583 líneas de receta** en tabla `costos`
- **615 líneas de elaborados** para insumos compuestos

---

**Documento generado por**: Agente EDARSA HUB  
**Fecha de generación**: 2026-05-24 14:30 (hora México)  
**Actualizado**: 2026-05-24 15:00 - Corrección estructura recetas SoftRestaurant
**Estado**: Pendiente de autorización para FASE 1C-3B
