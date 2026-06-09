# AUDITORÍA + PROPUESTA — Clasificación Comercial Canónica de Producto
**Fecha:** 2026-06-09 · **Estado:** SOLO AUDITORÍA Y PROPUESTA — **NO se ejecutó DDL** · **NO MongoDB · NO-LIVE · SIN hardcode**

Objetivo: dejar la clasificación comercial (ALIMENTOS / BEBIDAS / OTROS / PENDIENTE_CLASIFICACION) como **dato canónico del producto** alimentado desde un **catálogo controlado**, eliminando el `CASE A/B` de los endpoints. La regla A/B aplica **solo a SOFTRESTAURANT_PRO** (no global).

---

## 1. AUDITORÍA (hechos verificados con SELECT, sin escrituras)

### 1.1 Tabla de productos por módulo
| Módulo | Tabla de producto real | Llave de join |
|---|---|---|
| **Portal Inteligencia Comercial** | `Comercial_Inteligencia_VentasDetalleProducto` (detalle ventas) **JOIN** `Sync_Productos` | `producto_id ↔ Sync_Productos.ProductoID` |
| **Costos y Márgenes / Precios Sugeridos** | `Sync_Productos` (+ `Sync_Productos_Recetas`, `Sync_Productos_Insumos`) | `Sync_Productos.ProductoID / ServerID+CodigoFuente` |
| **Pricing IA / Benchmark** | `Sync_Productos` (+ `Comercial_Competidores`) | `Sync_Productos sp` |
| **Enriquecimiento bebidas** (casa/marca/alcohol) | `Comercial_Productos_Enriquecidos` (satélite, 3.774 filas, solo bebidas) | `producto_id` |

➡️ **`Sync_Productos` es el catálogo de producto operativo ÚNICO que consumen los 3 módulos.**

### 1.2 Existencia y volumen de tablas candidatas
| Tabla | Existe | Filas | Veredicto |
|---|---|---|---|
| `Sync_Productos` | ✅ | **12.460** | **Catálogo operativo real** (sincronizado, en uso por todos los módulos) |
| `Producto_Catalogo` | ✅ | **0 (vacío)** | Esqueleto canónico NO poblado → **no usar como fuente** hoy |
| `Comercial_Productos_Enriquecidos` | ✅ | 3.774 | Satélite de enriquecimiento (solo bebidas) |
| `Sync_Catalogo_Filtros` | ✅ | 536 | Catálogo NO-LIVE de filtros Categoría→Familia→Subfamilia (SoftRestaurant) |
| `Comercial_Productos` | ❌ | — | No existe |
| `Comercial_Categorias` / `Comercial_Familias` / `Comercial_Subfamilias` | ❌ | — | No existen |
| `Comercial_ClasificacionesProducto` | ❌ | — | **No existe** (catálogo de clasificación a crear) |

### 1.3 Columnas de clasificación existentes en `Sync_Productos`
- ✅ `FamiliaNombre`, `FamiliaCodigoFuente`, `FamiliaID`
- ✅ `SubFamiliaNombre`, `SubFamiliaCodigoFuente`, `SubFamiliaID`
- ✅ `CategoriaNombre`, `CategoriaCodigoFuente` (**existe**)
- ✅ `SystemType` ('MPRO' | 'SOFTRESTAURANT_PRO'), `UnidadNegocioID`, `ServerID`
- ❌ **NO existe** ninguna columna de clasificación comercial canónica (Alimentos/Bebidas/Otros) ni `categoria_id` que apunte a un catálogo controlado.

### 1.4 ¿`Sync_Productos` es staging u operativo? ¿Cómo se recarga?
Se recarga por **`MERGE` (UPSERT)** en `modules/sync_recetas/sync_recetas.py` (línea ~1110), llave **`(ServerID, CodigoFuente)`**:
- `WHEN MATCHED → UPDATE SET` actualiza **solo**: Nombre, Familia\*, SubFamilia\*, Categoria\*, Precio\*, Activo, SystemType, SyncRunID, fechas.
- `WHEN NOT MATCHED → INSERT` con lista cerrada de columnas.
- **No** hay `WHEN NOT MATCHED BY SOURCE THEN DELETE` → **no borra** filas existentes.

**Impacto sobre una columna nueva (p.ej. `ClasificacionProductoID`):**
- Filas existentes (MATCHED): la columna **NO se toca → se preserva** entre re-syncs. ✅
- Filas nuevas (NOT MATCHED): la columna queda **NULL** (no está en el INSERT) → se mostrará **PENDIENTE_CLASIFICACION** hasta correr el backfill. ✅ (comportamiento correcto, no inventa)

> ⚠️ Supuesto a validar con el dueño del **Sync Agent externo**: que NO exista otro proceso que haga `TRUNCATE`/recarga total de `Sync_Productos`. El `sync_recetas.py` del repo usa MERGE no-destructivo. La propuesta incluye un **job de re-backfill idempotente post-sync** que mitiga este riesgo en cualquier caso.

### 1.5 Simulación de backfill (SELECT, sin escribir) — 12.460 productos
| SystemType | Regla | ALIMENTOS | BEBIDAS | OTROS | PENDIENTE |
|---|---|--:|--:|--:|--:|
| **MPRO** | `CategoriaNombre` controlado | 2.781 | 3.684 | 1.492 | 0 |
| **SOFTRESTAURANT_PRO** | prefijo familia `A `/`B ` | 543 | 2.874 | — | **1.086** |
| **TOTAL** | | **3.324** | **6.558** | **1.492** | **1.086** |

➡️ Cobertura clasificable inmediata ≈ **91,3%**. Pendientes = **1.086 (8,7%)** = productos SoftRestaurant cuya familia no empieza con `A `/`B ` → quedan **PENDIENTE_CLASIFICACION** (clasificación manual posterior, **no se inventa**).

### 1.6 Separación por unidad canónica (130 QRO / ORIGEN)
- La clasificación es **atributo del producto** (`ProductoID`), **independiente de la unidad** → no hay mezcla por unidad.
- Los reportes ya filtran por **unidad canónica** (`unidad_negocio_nombre` en el detalle vía `normalizar_unidad`), **no por `server_id`**. 130 QRO y ORIGEN quedan separados por unidad canónica. La clasificación no introduce dependencia de `server_id`.

---

## 2. PROPUESTA SQL (para autorización — **aún no ejecutada**)

### Decisión de diseño
- **A. Catálogo controlado nuevo:** `Comercial_ClasificacionesProducto` (no existe equivalente).
- **B. Referencia desde el producto:** el patrón de `Sync_Productos` usa **IDs** (`FamiliaID`, `SubFamiliaID`) → usar **FK por ID**: `ClasificacionProductoID`.
- Se añade a `Sync_Productos` (catálogo operativo real) + columnas de **trazabilidad** (`ClasificacionOrigen`, `ClasificacionFecha`). El MERGE las preserva (§1.4).
- **Alternativa de menor riesgo (Opción 2):** tabla satélite `Comercial_Producto_Clasificacion` (PK `ProductoID`) al estilo `Comercial_Productos_Enriquecidos`, sin tocar `Sync_Productos`. Se documenta abajo; recomiendo **Opción 1** por simplicidad de lectura para todos los módulos, dado que el MERGE es no-destructivo.

### 2.A · DDL — Catálogo de clasificaciones
```sql
-- === FORWARD A ===
CREATE TABLE dbo.Comercial_ClasificacionesProducto (
    ClasificacionProductoID INT IDENTITY(1,1) PRIMARY KEY,
    Codigo                  VARCHAR(40)  NOT NULL UNIQUE,   -- ALIMENTOS / BEBIDAS / OTROS / PENDIENTE_CLASIFICACION
    Nombre                  NVARCHAR(120) NOT NULL,
    Descripcion             NVARCHAR(400) NULL,
    Activo                  BIT          NOT NULL CONSTRAINT DF_CCP_Activo DEFAULT(1),
    Orden                   INT          NOT NULL CONSTRAINT DF_CCP_Orden  DEFAULT(0),
    FechaCreacion           DATETIME2    NOT NULL CONSTRAINT DF_CCP_FCrea  DEFAULT(SYSDATETIME()),
    FechaActualizacion      DATETIME2    NULL,
    CreadoPor               NVARCHAR(120) NULL,
    ActualizadoPor          NVARCHAR(120) NULL
);

INSERT INTO dbo.Comercial_ClasificacionesProducto (Codigo, Nombre, Descripcion, Orden, CreadoPor) VALUES
 ('ALIMENTOS',               N'Alimentos',                N'Productos de cocina/alimentos',                1, N'migracion_clasificacion'),
 ('BEBIDAS',                 N'Bebidas',                  N'Bebidas (con o sin alcohol)',                  2, N'migracion_clasificacion'),
 ('OTROS',                   N'Otros',                    N'No-alimentos/no-bebidas (gastos, cavas, etc.)',3, N'migracion_clasificacion'),
 ('PENDIENTE_CLASIFICACION', N'Pendiente de clasificación', N'Sin clasificación confiable; requiere revisión', 99, N'migracion_clasificacion');
```

### 2.B · DDL — Referencia + trazabilidad en `Sync_Productos`
```sql
-- === FORWARD B ===  (columnas NULLABLES → 100% seguras, sin reescribir filas)
ALTER TABLE dbo.Sync_Productos ADD
    ClasificacionProductoID INT NULL,
    ClasificacionOrigen     VARCHAR(40) NULL,   -- 'PREFIJO_FAMILIA_AB' | 'MPRO_CATEGORIA' | 'MANUAL'
    ClasificacionFecha      DATETIME2 NULL;

ALTER TABLE dbo.Sync_Productos
    ADD CONSTRAINT FK_SyncProductos_Clasificacion
    FOREIGN KEY (ClasificacionProductoID)
    REFERENCES dbo.Comercial_ClasificacionesProducto (ClasificacionProductoID);

CREATE INDEX IX_SyncProductos_Clasificacion ON dbo.Sync_Productos (ClasificacionProductoID);
```

### 2.C · Backfill inicial (idempotente, con trazabilidad — re-ejecutable post-sync)
```sql
-- === BACKFILL (idempotente) ===
DECLARE @ALI INT = (SELECT ClasificacionProductoID FROM dbo.Comercial_ClasificacionesProducto WHERE Codigo='ALIMENTOS');
DECLARE @BEB INT = (SELECT ClasificacionProductoID FROM dbo.Comercial_ClasificacionesProducto WHERE Codigo='BEBIDAS');
DECLARE @OTR INT = (SELECT ClasificacionProductoID FROM dbo.Comercial_ClasificacionesProducto WHERE Codigo='OTROS');
DECLARE @PEN INT = (SELECT ClasificacionProductoID FROM dbo.Comercial_ClasificacionesProducto WHERE Codigo='PENDIENTE_CLASIFICACION');

-- (1) SOFTRESTAURANT_PRO → SOLO por prefijo de familia (regla NO global)
UPDATE sp SET ClasificacionProductoID=@ALI, ClasificacionOrigen='PREFIJO_FAMILIA_AB', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='SOFTRESTAURANT_PRO' AND LEFT(LTRIM(sp.FamiliaNombre),2)='A '
  AND sp.ClasificacionProductoID IS NULL;   -- idempotente: no recalcula manuales ya puestos

UPDATE sp SET ClasificacionProductoID=@BEB, ClasificacionOrigen='PREFIJO_FAMILIA_AB', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='SOFTRESTAURANT_PRO' AND LEFT(LTRIM(sp.FamiliaNombre),2)='B '
  AND sp.ClasificacionProductoID IS NULL;

UPDATE sp SET ClasificacionProductoID=@PEN, ClasificacionOrigen='PREFIJO_FAMILIA_AB', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='SOFTRESTAURANT_PRO'
  AND LEFT(LTRIM(sp.FamiliaNombre),2) NOT IN ('A ','B ')
  AND sp.ClasificacionProductoID IS NULL;

-- (2) MPRO → SOLO por CategoriaNombre (catálogo controlado), resto OTROS/PENDIENTE
UPDATE sp SET ClasificacionProductoID=@ALI, ClasificacionOrigen='MPRO_CATEGORIA', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='MPRO' AND UPPER(LTRIM(RTRIM(ISNULL(sp.CategoriaNombre,''))))='ALIMENTOS'
  AND sp.ClasificacionProductoID IS NULL;

UPDATE sp SET ClasificacionProductoID=@BEB, ClasificacionOrigen='MPRO_CATEGORIA', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='MPRO' AND UPPER(LTRIM(RTRIM(ISNULL(sp.CategoriaNombre,''))))='BEBIDAS'
  AND sp.ClasificacionProductoID IS NULL;

UPDATE sp SET ClasificacionProductoID=@OTR, ClasificacionOrigen='MPRO_CATEGORIA', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='MPRO' AND LTRIM(RTRIM(ISNULL(sp.CategoriaNombre,'')))<>''
  AND UPPER(LTRIM(RTRIM(sp.CategoriaNombre))) NOT IN ('ALIMENTOS','BEBIDAS')
  AND sp.ClasificacionProductoID IS NULL;

UPDATE sp SET ClasificacionProductoID=@PEN, ClasificacionOrigen='MPRO_CATEGORIA', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='MPRO' AND LTRIM(RTRIM(ISNULL(sp.CategoriaNombre,'')))=''
  AND sp.ClasificacionProductoID IS NULL;

-- (3) Cualquier otro sistema / no contemplado → PENDIENTE (no se aplica A/B global)
UPDATE sp SET ClasificacionProductoID=@PEN, ClasificacionOrigen='NO_REGLA', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.ClasificacionProductoID IS NULL;
```

### 2.D · ROLLBACK completo
```sql
-- === ROLLBACK B ===
DROP INDEX IX_SyncProductos_Clasificacion ON dbo.Sync_Productos;
ALTER TABLE dbo.Sync_Productos DROP CONSTRAINT FK_SyncProductos_Clasificacion;
ALTER TABLE dbo.Sync_Productos DROP COLUMN ClasificacionProductoID, ClasificacionOrigen, ClasificacionFecha;
-- === ROLLBACK A ===
DROP TABLE dbo.Comercial_ClasificacionesProducto;
```

---

## 3. CÓMO CAMBIAN LOS REPORTES (eliminación del CASE)
- Hoy (temporal): `_real_clasificacion_nested` y `_real_ticket_lineas` usan un `CASE A/B` inline en `modules/inteligencia_comercial/routes.py`.
- Después del backfill: los reportes harán **JOIN** `Sync_Productos sp → Comercial_ClasificacionesProducto cc ON cc.ClasificacionProductoID = sp.ClasificacionProductoID` y leerán **`cc.Codigo`/`cc.Nombre`**. Se **elimina el CASE**. Si la FK es NULL → mostrar **PENDIENTE_CLASIFICACION** (no inventar).
- Beneficio transversal: Inteligencia, Costos/Márgenes, Pricing/Benchmark y el futuro **reporteador multidimensional (MECA MPRO)** comparten la MISMA clasificación canónica.

## 4. VALIDACIÓN POST-EJECUCIÓN (cuando se autorice)
```sql
-- Totales por clasificación
SELECT cc.Codigo, COUNT(*) n FROM dbo.Sync_Productos sp
JOIN dbo.Comercial_ClasificacionesProducto cc ON cc.ClasificacionProductoID=sp.ClasificacionProductoID
GROUP BY cc.Codigo ORDER BY n DESC;
-- Soft por prefijo / MPRO por categoría / pendientes
SELECT SystemType, ClasificacionOrigen, COUNT(*) n FROM dbo.Sync_Productos GROUP BY SystemType, ClasificacionOrigen;
-- Cero NULL (todo clasificado o PENDIENTE)
SELECT COUNT(*) sin_clasificar FROM dbo.Sync_Productos WHERE ClasificacionProductoID IS NULL;  -- esperado: 0
```
Esperado tras backfill: ALIMENTOS≈3.324, BEBIDAS≈6.558, OTROS≈1.492, PENDIENTE≈1.086, NULL=0.

## 5. REGLAS RESPETADAS
✅ No DDL ejecutado (solo SELECT). ✅ Regla A/B SOLO para SOFTRESTAURANT_PRO. ✅ Catálogo controlado (no nombre libre). ✅ Trazabilidad (`ClasificacionOrigen`/`Fecha`). ✅ Pendientes visibles, no inventados. ✅ Sin recálculo de históricos (clasificación viaja en producto, no en ventas). ✅ Sin POS live. ✅ Sin Mongo. ✅ Sin `server_id` (unidad canónica). ✅ Backfill idempotente (no pisa clasificación MANUAL).

---
### PENDIENTE DE AUTORIZACIÓN DEL USUARIO
1. ¿Opción **1** (columnas en `Sync_Productos`) u **Opción 2** (tabla satélite `Comercial_Producto_Clasificacion`)?
2. ¿Confirmar con el dueño del Sync Agent externo que no hay TRUNCATE de `Sync_Productos`?
3. ¿Autorizo ejecutar DDL 2.A + 2.B + backfill 2.C?
