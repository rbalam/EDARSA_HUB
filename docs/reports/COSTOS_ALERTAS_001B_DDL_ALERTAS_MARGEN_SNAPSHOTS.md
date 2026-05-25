# COSTOS-ALERTAS-001-B: DDL de Alertas de Margen y Snapshots de Recetas

**Fecha de Ejecución:** 2025-05-25  
**Estado:** COMPLETADO  
**Fase:** COSTOS-ALERTAS-001-B (DDL)  
**Máximas:** EDARSAHUB SQL es el cerebro. CERO MongoDB.

---

## 1. Resumen Ejecutivo

Se crearon las 7 tablas autorizadas para el sistema de alertas de margen y snapshots de recetas en EDARSAHUB SQL Server.

| Tabla | Estado | Propósito |
|-------|--------|-----------|
| Comercial_AlertasMargenReglas | ✅ CREADA | Reglas de margen esperado por nivel |
| Comercial_AlertasMargenEventos | ✅ CREADA | Eventos de alerta detectados |
| Comercial_AlertasMargenDestinatarios | ✅ CREADA | Destinatarios de alertas |
| Comercial_AlertasMargenEnvios | ✅ CREADA | Registro de envíos |
| Comercial_AlertasUmbralesSeveridad | ✅ CREADA | Configuración de severidades |
| Comercial_RecetasSnapshot | ✅ CREADA | Fotografías históricas de recetas |
| Comercial_RecetasSnapshotDetalle | ✅ CREADA | Detalle de snapshots |

---

## 2. DDL Ejecutado

### 2.1 Comercial_AlertasMargenReglas

```sql
CREATE TABLE Comercial_AlertasMargenReglas (
    ReglaMargenID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    NivelAplicacion VARCHAR(20) NOT NULL,
    GrupoCodigo VARCHAR(100) NULL,
    FamiliaCodigo VARCHAR(100) NULL,
    SubfamiliaCodigo VARCHAR(100) NULL,
    ProductoClave VARCHAR(100) NULL,
    EmpresaID INT NULL,
    SucursalID INT NULL,
    ServerID UNIQUEIDENTIFIER NULL,
    MargenPorcentajeEsperado DECIMAL(5,2) NULL,
    CostoMaximoPorcentaje DECIMAL(5,2) NULL,
    UtilidadMinimaPorcentaje DECIMAL(5,2) NULL,
    SeveridadBase VARCHAR(20) DEFAULT 'MEDIA',
    Descripcion NVARCHAR(500) NULL,
    Activo BIT DEFAULT 1,
    FechaInicioVigencia DATETIME DEFAULT GETDATE(),
    FechaFinVigencia DATETIME NULL,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FechaModificacion DATETIME NULL,
    CreadoPor VARCHAR(100) NULL,
    ModificadoPor VARCHAR(100) NULL
);
```

**Constraints:**
- `CK_AlertasMargenReglas_Nivel`: NivelAplicacion IN ('GRUPO', 'FAMILIA', 'SUBFAMILIA', 'PRODUCTO')
- `CK_AlertasMargenReglas_Severidad`: SeveridadBase IN ('INFORMATIVA', 'MEDIA', 'ALTA', 'CRITICA')
- `CK_AlertasMargenReglas_MargenValido`: MargenPorcentajeEsperado BETWEEN 0 AND 100
- `CK_AlertasMargenReglas_CostoValido`: CostoMaximoPorcentaje BETWEEN 0 AND 100
- `CK_AlertasMargenReglas_UtilidadValida`: UtilidadMinimaPorcentaje BETWEEN -100 AND 100

**Índices:**
- `IX_AlertasMargenReglas_Nivel` (NivelAplicacion, Activo)
- `IX_AlertasMargenReglas_Grupo` (GrupoCodigo) WHERE NivelAplicacion = 'GRUPO'
- `IX_AlertasMargenReglas_Familia` (FamiliaCodigo) WHERE NivelAplicacion = 'FAMILIA'
- `IX_AlertasMargenReglas_Subfamilia` (SubfamiliaCodigo) WHERE NivelAplicacion = 'SUBFAMILIA'
- `IX_AlertasMargenReglas_Producto` (ProductoClave) WHERE NivelAplicacion = 'PRODUCTO'
- `IX_AlertasMargenReglas_Vigencia` (Activo, FechaInicioVigencia, FechaFinVigencia)

---

### 2.2 Comercial_AlertasMargenEventos

```sql
CREATE TABLE Comercial_AlertasMargenEventos (
    AlertaMargenEventoID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    FechaEvaluacion DATETIME DEFAULT GETDATE(),
    ServerID UNIQUEIDENTIFIER NULL,
    EmpresaID INT NULL,
    SucursalID INT NULL,
    UnidadNegocioID INT NULL,
    ProductoClave VARCHAR(100) NOT NULL,
    ProductoNombre NVARCHAR(500) NULL,
    GrupoCodigo VARCHAR(100) NULL,
    FamiliaCodigo VARCHAR(100) NULL,
    SubfamiliaCodigo VARCHAR(100) NULL,
    PrecioVentaActual DECIMAL(18,4) NULL,
    CostoRecetaActual DECIMAL(18,4) NULL,
    MargenActualPorcentaje DECIMAL(5,2) NULL,
    MargenActualMonto DECIMAL(18,4) NULL,
    MargenEsperadoPorcentaje DECIMAL(5,2) NULL,
    DiferenciaPuntos DECIMAL(5,2) NULL,
    UtilidadActual DECIMAL(18,4) NULL,
    UtilidadEsperada DECIMAL(18,4) NULL,
    PerdidaPorUnidad DECIMAL(18,4) NULL,
    ReglaMargenID UNIQUEIDENTIFIER NULL,
    FuenteRegla VARCHAR(20) NULL,
    Severidad VARCHAR(20) NOT NULL,
    Estado VARCHAR(30) DEFAULT 'NUEVA',
    SnapshotID UNIQUEIDENTIFIER NULL,
    VariacionCostoAnterior DECIMAL(18,4) NULL,
    VariacionCostoAcumulada DECIMAL(18,4) NULL,
    Recomendacion NVARCHAR(500) NULL,
    ErrorDatos BIT DEFAULT 0,
    NotasInternas NVARCHAR(MAX) NULL,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FechaModificacion DATETIME NULL,
    FechaResolucion DATETIME NULL,
    ResueltoPor VARCHAR(100) NULL
);
```

**Constraints:**
- `CK_AlertasMargenEventos_Severidad`: IN ('INFORMATIVA', 'MEDIA', 'ALTA', 'CRITICA')
- `CK_AlertasMargenEventos_Estado`: IN ('NUEVA', 'ENVIADA', 'ACK', 'EN_REVISION', 'RESUELTA', 'IGNORADA', 'DUPLICADA')
- `CK_AlertasMargenEventos_FuenteRegla`: IN ('PRODUCTO', 'SUBFAMILIA', 'FAMILIA', 'GRUPO', 'SIN_REGLA')

**Índices:**
- `IX_AlertasMargenEventos_Fecha` (FechaEvaluacion DESC)
- `IX_AlertasMargenEventos_Producto` (ProductoClave)
- `IX_AlertasMargenEventos_Estado` (Estado)
- `IX_AlertasMargenEventos_Severidad` (Severidad)
- `IX_AlertasMargenEventos_Server` (ServerID)
- `IX_AlertasMargenEventos_Regla` (ReglaMargenID)
- `IX_AlertasMargenEventos_Duplicados` (ProductoClave, ServerID, Estado, Severidad)

---

### 2.3 Comercial_AlertasMargenDestinatarios

```sql
CREATE TABLE Comercial_AlertasMargenDestinatarios (
    DestinatarioID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Nombre NVARCHAR(200) NOT NULL,
    Email VARCHAR(200) NULL,
    TelefonoWhatsApp VARCHAR(20) NULL,
    CanalEmail BIT DEFAULT 1,
    CanalWhatsApp BIT DEFAULT 0,
    EmpresaID INT NULL,
    SucursalID INT NULL,
    ServerID UNIQUEIDENTIFIER NULL,
    FamiliaCodigo VARCHAR(100) NULL,
    SeveridadMinima VARCHAR(20) DEFAULT 'ALTA',
    RecibeResumen BIT DEFAULT 1,
    RecibeDetalle BIT DEFAULT 1,
    FrecuenciaMaximaDiaria INT DEFAULT 10,
    HoraPreferida VARCHAR(5) DEFAULT '08:00',
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FechaModificacion DATETIME NULL,
    CreadoPor VARCHAR(100) NULL,
    ModificadoPor VARCHAR(100) NULL
);
```

---

### 2.4 Comercial_AlertasMargenEnvios

```sql
CREATE TABLE Comercial_AlertasMargenEnvios (
    EnvioID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    AlertaMargenEventoID UNIQUEIDENTIFIER NOT NULL,
    DestinatarioID UNIQUEIDENTIFIER NOT NULL,
    Canal VARCHAR(20) NOT NULL,
    EstadoEnvio VARCHAR(30) DEFAULT 'PENDIENTE',
    FechaIntento DATETIME NULL,
    FechaEnvio DATETIME NULL,
    NumeroIntentos INT DEFAULT 0,
    ProviderMessageID VARCHAR(200) NULL,
    ErrorMensajeSeguro NVARCHAR(500) NULL,
    FechaCreacion DATETIME DEFAULT GETDATE()
);
```

**Estados de Envío:**
- `PENDIENTE`: Pendiente de procesar
- `EN_PROCESO`: En proceso de envío
- `ENVIADO`: Enviado exitosamente
- `ERROR`: Error en el envío
- `PENDIENTE_CONFIGURACION`: WhatsApp no configurado
- `OMITIDO`: Omitido por regla de frecuencia

---

### 2.5 Comercial_AlertasUmbralesSeveridad

```sql
CREATE TABLE Comercial_AlertasUmbralesSeveridad (
    UmbralID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Severidad VARCHAR(20) NOT NULL,
    PuntosDesde DECIMAL(5,2) NOT NULL,
    PuntosHasta DECIMAL(5,2) NOT NULL,
    IncluirUtilidadNegativa BIT DEFAULT 0,
    IncluirCostoMayorPrecio BIT DEFAULT 0,
    Descripcion NVARCHAR(200) NULL,
    ColorHex VARCHAR(7) DEFAULT '#FFA500',
    Activo BIT DEFAULT 1,
    Orden INT DEFAULT 0,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FechaModificacion DATETIME NULL
);
```

---

### 2.6 Comercial_RecetasSnapshot

```sql
CREATE TABLE Comercial_RecetasSnapshot (
    RecetaSnapshotID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    FechaSnapshot DATETIME DEFAULT GETDATE(),
    ServerID UNIQUEIDENTIFIER NULL,
    EmpresaID INT NULL,
    SucursalID INT NULL,
    UnidadNegocioID INT NULL,
    ProductoClave VARCHAR(100) NOT NULL,
    ProductoNombre NVARCHAR(500) NULL,
    PrecioVenta DECIMAL(18,4) NULL,
    CostoRecetaTotal DECIMAL(18,4) NULL,
    MargenPorcentaje DECIMAL(5,2) NULL,
    MargenMonto DECIMAL(18,4) NULL,
    NumeroInsumos INT DEFAULT 0,
    HashReceta VARCHAR(64) NULL,
    FuenteCalculo VARCHAR(50) DEFAULT 'SYNC_RECETAS',
    SnapshotAnteriorID UNIQUEIDENTIFIER NULL,
    VariacionCosto DECIMAL(18,4) NULL,
    VariacionCostoPorcentaje DECIMAL(5,2) NULL,
    VariacionMargen DECIMAL(5,2) NULL,
    EsActual BIT DEFAULT 1,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    CreadoPor VARCHAR(100) DEFAULT 'SISTEMA',
    SyncRunID VARCHAR(100) NULL
);
```

---

### 2.7 Comercial_RecetasSnapshotDetalle

```sql
CREATE TABLE Comercial_RecetasSnapshotDetalle (
    RecetaSnapshotDetalleID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    RecetaSnapshotID UNIQUEIDENTIFIER NOT NULL,
    InsumoClave VARCHAR(100) NOT NULL,
    InsumoNombre NVARCHAR(500) NULL,
    Cantidad DECIMAL(18,6) NULL,
    UnidadMedida VARCHAR(50) NULL,
    CostoUnitario DECIMAL(18,4) NULL,
    CostoTotal DECIMAL(18,4) NULL,
    PorcentajeDelCosto DECIMAL(5,2) NULL,
    EsElaborado BIT DEFAULT 0,
    CostoAnterior DECIMAL(18,4) NULL,
    VariacionCosto DECIMAL(18,4) NULL,
    VariacionCostoPorcentaje DECIMAL(5,2) NULL,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    Orden INT DEFAULT 0
);
```

---

## 3. Umbrales de Severidad Iniciales

| Severidad | Desde | Hasta | Utilidad Negativa | Costo > Precio | Color |
|-----------|-------|-------|-------------------|----------------|-------|
| INFORMATIVA | 0.00 | 1.99 | No | No | #3B82F6 (Azul) |
| MEDIA | 2.00 | 4.99 | No | No | #F59E0B (Amarillo) |
| ALTA | 5.00 | 9.99 | No | No | #F97316 (Naranja) |
| CRITICA | 10.00 | 999.00 | Sí | Sí | #EF4444 (Rojo) |

---

## 4. Jerarquía de Resolución de Reglas

La estructura de `Comercial_AlertasMargenReglas` soporta la siguiente jerarquía:

```
1. PRODUCTO      → ProductoClave poblado, resto NULL
2. SUBFAMILIA    → SubfamiliaCodigo poblado, resto NULL
3. FAMILIA       → FamiliaCodigo poblado, resto NULL
4. GRUPO         → GrupoCodigo poblado, resto NULL
```

**SQL de Resolución (para implementar en FASE C):**
```sql
SELECT TOP 1 *
FROM Comercial_AlertasMargenReglas
WHERE Activo = 1
  AND (FechaFinVigencia IS NULL OR FechaFinVigencia > GETDATE())
  AND (
      (NivelAplicacion = 'PRODUCTO' AND ProductoClave = @ProductoClave) OR
      (NivelAplicacion = 'SUBFAMILIA' AND SubfamiliaCodigo = @SubfamiliaCodigo) OR
      (NivelAplicacion = 'FAMILIA' AND FamiliaCodigo = @FamiliaCodigo) OR
      (NivelAplicacion = 'GRUPO' AND GrupoCodigo = @GrupoCodigo)
  )
ORDER BY 
  CASE NivelAplicacion 
    WHEN 'PRODUCTO' THEN 1
    WHEN 'SUBFAMILIA' THEN 2
    WHEN 'FAMILIA' THEN 3
    WHEN 'GRUPO' THEN 4
  END
```

---

## 5. Validaciones Realizadas

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Las 7 tablas existen | ✅ |
| 2 | DDL es idempotente | ✅ (ejecutado 2 veces sin error) |
| 3 | No hay tablas duplicadas | ✅ |
| 4 | Constraints creados | ✅ |
| 5 | Índices creados | ✅ |
| 6 | Umbrales de severidad configurados | ✅ (4 registros) |
| 7 | Login funciona | ✅ |
| 8 | CERO MongoDB | ✅ |
| 9 | No se modificaron precios | ✅ |
| 10 | No se modificaron recetas | ✅ |

---

## 6. Archivos Creados

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/scripts/ddl_costos_alertas_001b.py` | Script DDL idempotente |
| `/app/docs/reports/COSTOS_ALERTAS_001B_DDL_ALERTAS_MARGEN_SNAPSHOTS.md` | Este reporte |

---

## 7. Confirmaciones Obligatorias

- ✅ **CERO MongoDB:** Todo el DDL es SQL Server puro
- ✅ **No se modificaron precios oficiales:** Las tablas solo almacenan datos de alertas
- ✅ **No se modificaron recetas oficiales:** Las tablas de snapshot son independientes
- ✅ **No se enviaron alertas:** Solo se creó la estructura, no se ejecutó el job
- ✅ **No se modificó el frontend:** Solo DDL backend
- ✅ **Patrón Comercial_*:** Todas las tablas siguen el patrón existente

---

## 8. Próximos Pasos (COSTOS-ALERTAS-001-C)

### Recomendación para siguiente fase:

**COSTOS-ALERTAS-001-C: Servicios Backend para Reglas de Margen**

1. Crear `alertas_margen_repository.py`:
   - CRUD de reglas de margen
   - Resolución de regla aplicable (jerarquía)
   - Validación de duplicados

2. Crear `alertas_margen_service.py`:
   - Lógica de negocio para reglas
   - Validación de vigencia
   - Cálculo de margen esperado

3. Crear `routes_alertas_margen.py`:
   - `GET /api/alertas-margen/reglas` - Listar reglas
   - `POST /api/alertas-margen/reglas` - Crear regla
   - `PUT /api/alertas-margen/reglas/{id}` - Actualizar regla
   - `DELETE /api/alertas-margen/reglas/{id}` - Desactivar regla
   - `GET /api/alertas-margen/umbrales` - Obtener umbrales

4. **NO INCLUIR EN FASE C:**
   - Job de evaluación (FASE E)
   - Envío de alertas (FASE F)
   - UI (FASE D)

---

**Reporte generado por:** Agente E1  
**Fecha:** 2025-05-25  
**Fase completada:** COSTOS-ALERTAS-001-B
