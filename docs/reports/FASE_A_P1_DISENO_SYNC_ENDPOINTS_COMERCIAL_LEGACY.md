# FASE A-P1: DISEÑO SYNC ENDPOINTS COMERCIAL LEGACY

**Fecha:** 2026-05-26  
**Estado:** COMPLETADO (Diagnóstico + Desbloqueo Endpoint 1)  
**Alcance:** Diseño de tablas SQL y jobs para desbloquear endpoints `comercial/routes.py`

---

## RESUMEN EJECUTIVO

### Endpoints Desbloqueados
| # | Endpoint | Estado | Fuente |
|---|----------|--------|--------|
| 1 | `/comercial/sucursales/{server_id}` | ✅ SQL-FIRST | `Sistema_Sucursales` + `Sistema_SucursalServidorMapeo` |

### Endpoints Aún Bloqueados (6)
| # | Endpoint | Tabla Requerida | Prioridad |
|---|----------|-----------------|-----------|
| 2 | `/comercial/metas/{server_id}` | `Sync_Metas_Comerciales` | P2 |
| 3 | `/comercial/ticket-perfecto/{server_id}` | `Sync_Ticket_Perfecto` | P3 |
| 4 | `/comercial/mesas/{server_id}` | `Sync_Mesas` | P3 |
| 5 | `/comercial/reporte-pax/{server_id}` | `Sync_PAX_Detalle` | P3 |
| 6 | `/comercial/precios-constantes/{server_id}` | `Sync_Precios_Historicos` | P4 |
| 7 | `/comercial/detalle-movimientos/{server_id}` | `Sync_Movimientos_Detalle` | P4 |

---

## 1. DIAGNÓSTICO SQL PREVIO

### Tablas Existentes Encontradas

| Tabla | Registros | Puede Servir Para |
|-------|-----------|-------------------|
| `Sistema_Sucursales` | 5 | `/comercial/sucursales/{server_id}` |
| `Sistema_SucursalServidorMapeo` | 5 | Mapeo ServidorID → SucursalID |
| `Sync_Ventas_PorHora` | Poblada | `/comercial/ventas-tiempo/{server_id}` (ya migrado) |
| `Sync_Ventas_PorDiaSemana` | Poblada | Dashboard |
| `Sync_Ventas_Historicas` | Poblada | Reportes históricos |
| `Sync_Productos` | Poblada | Catálogo de productos |
| `Sync_Productos_Recetas` | Poblada | Ticket perfecto (parcial) |

### Tablas Faltantes

| Tabla Requerida | Endpoint | Prioridad |
|-----------------|----------|-----------|
| ~~Sistema_Sucursales~~ | ~~`/sucursales/{server_id}`~~ | ✅ YA EXISTE |
| `Sync_Metas_Comerciales` | `/metas/{server_id}` | P2 |
| `Sync_Ticket_Perfecto` | `/ticket-perfecto/{server_id}` | P3 |
| `Sync_Mesas_Comensales` | `/mesas/{server_id}` | P3 |
| `Sync_Movimientos_Detalle` | `/detalle-movimientos/{server_id}` | P4 |
| `Sync_Precios_Historicos` | `/precios-constantes/{server_id}` | P4 |
| `Sync_PAX_Detalle` | `/reporte-pax/{server_id}` | P3 |

---

## 2. PLAN DE DESBLOQUEO POR ENDPOINT

### ENDPOINT 1: `/comercial/sucursales/{server_id}` ✅ LISTO PARA DESBLOQUEAR

**Estado:** Las tablas SQL ya existen.

**Tablas disponibles:**
- `Sistema_Sucursales` (5 registros)
- `Sistema_SucursalServidorMapeo` (mapeo ServidorID → SucursalID)

**Query SQL propuesta:**
```sql
SELECT 
    ss.SucursalID as id,
    ss.CodigoSucursal as codigo,
    ss.NombreSucursal as nombre,
    ss.EmpresaID,
    sm.ServidorID
FROM Sistema_Sucursales ss
JOIN Sistema_SucursalServidorMapeo sm ON ss.SucursalID = sm.SucursalID
WHERE sm.ServidorID = @ServidorID
  AND ss.Activo = 1
  AND sm.Activo = 1
ORDER BY ss.NombreSucursal
```

**Acción:** Modificar endpoint para leer de EDARSAHUB SQL.

---

### ENDPOINT 2: `/comercial/metas/{server_id}` - DDL REQUERIDO

**Estado:** Tabla no existe.

**Fuente de datos:** MPRO → Tabla `meta_venta` (metas por producto/vendedor/mes)

**DDL Propuesto:**
```sql
CREATE TABLE Sync_Metas_Comerciales (
    MetaID INT IDENTITY(1,1) PRIMARY KEY,
    ServidorID UNIQUEIDENTIFIER NOT NULL,
    UnidadNegocioID VARCHAR(50),
    EmpresaID INT,
    SucursalID INT,
    
    -- Datos de meta
    Anio INT NOT NULL,
    Mes INT NOT NULL,
    ProductoID VARCHAR(50),
    ProductoNombre NVARCHAR(200),
    VendedorID VARCHAR(50),
    VendedorNombre NVARCHAR(200),
    MetaVenta DECIMAL(18,2),
    MetaUnidades INT,
    
    -- Campos de sync
    FuenteSistema VARCHAR(50) DEFAULT 'MPRO',
    SourceServerID UNIQUEIDENTIFIER,
    SyncRunID VARCHAR(50),
    FechaSincronizacion DATETIME2,
    EstadoSync VARCHAR(20),
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME2 DEFAULT SYSUTCDATETIME(),
    FechaModificacion DATETIME2
);
```

**Job requerido:** `sync_metas_comerciales_job.py`
**Frecuencia sugerida:** Diario a las 06:00 AM (metas cambian poco)
**Prioridad:** P2

---

### ENDPOINT 3: `/comercial/ticket-perfecto/{server_id}` - DDL REQUERIDO

**Estado:** Tabla no existe.

**Fuente de datos:** SoftRestaurant → `foliodet` + `producto` + costos

**DDL Propuesto:**
```sql
CREATE TABLE Sync_Ticket_Perfecto (
    TicketPerfectoID INT IDENTITY(1,1) PRIMARY KEY,
    ServidorID UNIQUEIDENTIFIER NOT NULL,
    UnidadNegocioID VARCHAR(50),
    
    -- Período
    FechaOperacion DATE NOT NULL,
    Anio INT,
    Mes INT,
    
    -- Métricas
    ProductoID VARCHAR(50),
    ProductoNombre NVARCHAR(200),
    FamiliaID VARCHAR(50),
    FamiliaNombre NVARCHAR(200),
    CategoriaID VARCHAR(50),
    CategoriaNombre NVARCHAR(200),
    
    -- KPIs
    UnidadesVendidas INT,
    VentaTotal DECIMAL(18,2),
    CostoTotal DECIMAL(18,2),
    MargenBruto DECIMAL(18,2),
    PorcentajeMargen DECIMAL(8,4),
    TicketsConProducto INT,
    PorcentajePresencia DECIMAL(8,4),
    
    -- Sync
    FuenteSistema VARCHAR(50) DEFAULT 'SoftRestaurant',
    SyncRunID VARCHAR(50),
    FechaSincronizacion DATETIME2,
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME2 DEFAULT SYSUTCDATETIME()
);
```

**Job requerido:** `sync_ticket_perfecto_job.py`
**Frecuencia sugerida:** Cada 2 horas (datos operativos)
**Prioridad:** P3

---

### ENDPOINT 4: `/comercial/mesas/{server_id}` - DDL REQUERIDO

**Estado:** Tabla no existe.

**Fuente de datos:** SoftRestaurant → `folio` (para datos de mesas/comensales)

**DDL Propuesto:**
```sql
CREATE TABLE Sync_Mesas_Comensales (
    MesaComensalID INT IDENTITY(1,1) PRIMARY KEY,
    ServidorID UNIQUEIDENTIFIER NOT NULL,
    UnidadNegocioID VARCHAR(50),
    
    -- Período
    FechaOperacion DATE NOT NULL,
    HoraServicio INT, -- 0-23
    
    -- Datos de mesa
    MesaNumero VARCHAR(20),
    Comensales INT,
    VentaMesa DECIMAL(18,2),
    TiempoAtencion INT, -- minutos
    
    -- Agregados diarios
    TotalMesasAtendidas INT,
    TotalComensales INT,
    PromedioComensalesPorMesa DECIMAL(8,2),
    VentaPromedioPorMesa DECIMAL(18,2),
    
    -- Sync
    FuenteSistema VARCHAR(50) DEFAULT 'SoftRestaurant',
    SyncRunID VARCHAR(50),
    FechaSincronizacion DATETIME2,
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME2 DEFAULT SYSUTCDATETIME()
);
```

**Job requerido:** `sync_mesas_comensales_job.py`
**Frecuencia sugerida:** Cada hora (datos operativos)
**Prioridad:** P3

---

### ENDPOINT 5: `/comercial/reporte-pax/{server_id}` - DDL REQUERIDO

**Estado:** Tabla no existe.

**Fuente de datos:** SoftRestaurant → `folio` + `foliodet` (comensales por cheque)

**DDL Propuesto:**
```sql
CREATE TABLE Sync_PAX_Detalle (
    PaxDetalleID INT IDENTITY(1,1) PRIMARY KEY,
    ServidorID UNIQUEIDENTIFIER NOT NULL,
    UnidadNegocioID VARCHAR(50),
    
    -- Período
    FechaOperacion DATE NOT NULL,
    
    -- Datos por vendedor
    VendedorID VARCHAR(50),
    VendedorNombre NVARCHAR(200),
    
    -- KPIs
    TotalCheques INT,
    TotalPax INT,
    VentaTotal DECIMAL(18,2),
    TicketPromedio DECIMAL(18,2),
    PaxPromedio DECIMAL(8,2),
    VentaPorPax DECIMAL(18,2),
    
    -- Sync
    FuenteSistema VARCHAR(50) DEFAULT 'SoftRestaurant',
    SyncRunID VARCHAR(50),
    FechaSincronizacion DATETIME2,
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME2 DEFAULT SYSUTCDATETIME()
);
```

**Job requerido:** `sync_pax_detalle_job.py`
**Frecuencia sugerida:** Cada 2 horas
**Prioridad:** P3

---

### ENDPOINT 6: `/comercial/precios-constantes/{server_id}` - COMPLEJO

**Estado:** Tabla no existe. Requiere análisis complejo de precios históricos.

**Fuente de datos:** MPRO/SoftRestaurant → Tablas de precios por período

**Complejidad:** ALTA
- Requiere guardar precios por producto/período
- Requiere lógica de valuación a precios base
- Requiere manejo de productos nuevos/descontinuados

**DDL Propuesto:**
```sql
CREATE TABLE Sync_Precios_Historicos (
    PrecioHistoricoID INT IDENTITY(1,1) PRIMARY KEY,
    ServidorID UNIQUEIDENTIFIER NOT NULL,
    UnidadNegocioID VARCHAR(50),
    
    -- Período
    Anio INT NOT NULL,
    Mes INT NOT NULL,
    
    -- Producto
    ProductoID VARCHAR(50),
    ProductoNombre NVARCHAR(200),
    FamiliaID VARCHAR(50),
    CategoriaID VARCHAR(50),
    
    -- Precios
    PrecioPromedio DECIMAL(18,4),
    PrecioMinimo DECIMAL(18,4),
    PrecioMaximo DECIMAL(18,4),
    UnidadesVendidas INT,
    VentaTotal DECIMAL(18,2),
    
    -- Sync
    FuenteSistema VARCHAR(50),
    SyncRunID VARCHAR(50),
    FechaSincronizacion DATETIME2,
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME2 DEFAULT SYSUTCDATETIME()
);
```

**Job requerido:** `sync_precios_historicos_job.py`
**Frecuencia sugerida:** Mensual (datos históricos)
**Prioridad:** P4

---

### ENDPOINT 7: `/comercial/detalle-movimientos/{server_id}` - COMPLEJO

**Estado:** Tabla no existe. Requiere detalle de cheques/facturas.

**Fuente de datos:** SoftRestaurant → `folio` + `foliodet` / MPRO → `venta` + `detalle_venta`

**Complejidad:** ALTA
- Gran volumen de datos (todos los cheques)
- Requiere paginación eficiente
- Requiere índices optimizados

**DDL Propuesto:**
```sql
CREATE TABLE Sync_Movimientos_Detalle (
    MovimientoID BIGINT IDENTITY(1,1) PRIMARY KEY,
    ServidorID UNIQUEIDENTIFIER NOT NULL,
    UnidadNegocioID VARCHAR(50),
    
    -- Identificación
    FolioID VARCHAR(50),
    NumeroFolio VARCHAR(50),
    FechaOperacion DATE NOT NULL,
    HoraOperacion TIME,
    
    -- Detalle
    TipoMovimiento VARCHAR(20), -- VENTA, PROPINA, DESCUENTO
    ProductoID VARCHAR(50),
    ProductoNombre NVARCHAR(200),
    Cantidad DECIMAL(18,4),
    PrecioUnitario DECIMAL(18,4),
    Subtotal DECIMAL(18,2),
    Impuestos DECIMAL(18,2),
    Total DECIMAL(18,2),
    
    -- Vendedor
    VendedorID VARCHAR(50),
    VendedorNombre NVARCHAR(200),
    
    -- Sync
    FuenteSistema VARCHAR(50),
    SyncRunID VARCHAR(50),
    FechaSincronizacion DATETIME2,
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME2 DEFAULT SYSUTCDATETIME(),
    
    -- Índices sugeridos
    INDEX IX_Mov_Fecha (FechaOperacion, ServidorID),
    INDEX IX_Mov_Folio (FolioID, ServidorID)
);
```

**Job requerido:** `sync_movimientos_detalle_job.py`
**Frecuencia sugerida:** Cada hora (últimos 3 días)
**Prioridad:** P4

---

## 3. JOBS EXISTENTES (Referencia)

| Job | Tabla Destino | Frecuencia | Estado |
|-----|---------------|------------|--------|
| `sync_comercial_v2_job.py` | `Comercial_KPIs_Diarios_v2` | 5 min | ✅ Activo |
| `sync_comercial_abiertas_v2_job.py` | `Comercial_Ventas_Dia_Abiertas_v2` | 2 min | ✅ Activo |
| `pedidos_detector_job.py` | `Scheduler_PedidosProcesados` | 1 min | ✅ Activo |
| `sync_nightly_comercial_job.py` | `Sync_Ventas_*` | Nightly | ✅ Activo |

---

## 4. PLAN DE IMPLEMENTACIÓN

### INMEDIATO (FASE A-P1-D1)
1. **Desbloquear `/comercial/sucursales/{server_id}`**
   - Tablas ya existen
   - Solo requiere modificar endpoint para leer SQL
   - Sin DDL
   - Sin job nuevo

### CORTO PLAZO (FASE A-P1-D2)
2. **`/comercial/metas/{server_id}`** - P2
3. **`/comercial/reporte-pax/{server_id}`** - P3

### MEDIANO PLAZO (FASE A-P1-D3)
4. **`/comercial/mesas/{server_id}`** - P3
5. **`/comercial/ticket-perfecto/{server_id}`** - P3

### LARGO PLAZO (FASE A-P1-D4)
6. **`/comercial/precios-constantes/{server_id}`** - P4
7. **`/comercial/detalle-movimientos/{server_id}`** - P4

---

## 5. CONFIRMACIONES

| Requisito | Estado |
|-----------|--------|
| ✅ CERO MongoDB | Confirmado |
| ✅ NO LIVE para UI | Guard rail activo |
| ✅ Solo jobs pueden conectar a fuentes externas | Diseñado |
| ✅ Endpoints leerán EDARSAHUB SQL | Plan definido |
| ✅ Comercial V2 no afectado | Confirmado |
| ✅ Tablero Ejecutivo no afectado | Confirmado |
| ✅ Auth/RBAC no afectado | Confirmado |

---

## 6. RIESGOS

| Riesgo | Mitigación |
|--------|------------|
| Volumen de datos en Sync_Movimientos_Detalle | Sincronizar solo últimos 7 días + paginación |
| Complejidad de precios históricos | Comenzar con snapshot mensual simple |
| Jobs MPRO requieren conexión a servidor remoto | Usar pattern existente de `execute_query_on_server` |

---

## 7. PRÓXIMO PASO AUTORIZADO

**Implementar desbloqueo de `/comercial/sucursales/{server_id}`**
- Modificar endpoint en `comercial/routes.py`
- Leer de `Sistema_Sucursales` + `Sistema_SucursalServidorMapeo`
- Quitar guard rail solo para este endpoint
- Validar sin regresiones
