# COSTOS-ALERTAS-001: DIAGNÓSTICO PREVIO A IMPLEMENTACIÓN

**Fecha de Diagnóstico:** 2025-05-25  
**Estado:** DIAGNÓSTICO COMPLETADO  
**Próximo Paso:** REVISIÓN Y AUTORIZACIÓN PARA IMPLEMENTAR

---

## 1. RESPUESTA A PREGUNTA CRÍTICA

### ¿Ya existen tablas que guardan "fotografías" históricas de recetas/costos?

**RESPUESTA: NO EXISTEN**

Tras auditoría exhaustiva del backend y búsqueda de tablas en SQL Server, **NO se encontraron**:
- Tablas de snapshots de recetas
- Históricos de costo de receta
- Histórico de insumos
- Variaciones acumuladas de costos
- Bitácora de recálculo de costos
- Versiones de recetas

### Evidencia del Diagnóstico

```bash
# Búsqueda de columnas relacionadas con snapshots/históricos
grep -Ri "Snapshot|Historico|Historial|Version|CostoAnterior|Variacion" /app/backend --include="*.py"

# Resultados relevantes:
# - comercial/service.py: snapshot_timestamp (pero es para ventas del día, NO recetas)
# - crm/comercial_service.py: RazonSocialSnapshot, RFCSnapshot (datos de clientes, NO costos)
# - fase2_operativo: umbral_aplicado (workflows operativos, NO recetas)
```

**Conclusión:** No existen estructuras de fotografía/snapshot para recetas y costos. Deberán crearse.

---

## 2. TABLAS EXISTENTES IDENTIFICADAS

### Tablas Comercial_*
| Tabla | Propósito |
|-------|-----------|
| `Comercial_KPIs_Diarios_v2` | KPIs de ventas diarias |
| `Comercial_Ventas_Dia_Abiertas_v2` | Ventas sin corte |
| `Comercial_ReglasPrecio` | Reglas de precios (ej: VINOS_RANGOS_MX) |
| `Comercial_ReglasPrecioRangos` | Rangos de multiplicadores por regla |
| `Comercial_Competidores` | Competidores para benchmark |
| `Comercial_CompetidoresMenuItems` | Items de menú de competidores |
| `Comercial_CompetidoresListas` | Listas de competidores |
| `Comercial_CompetidoresListasDetalle` | Detalle de listas |
| `Comercial_PricingAnalisisIA` | Historial de análisis IA de precios |
| `Comercial_PricingBenchmarkProducto` | Benchmarks de productos |
| `Comercial_ImpuestosOverrides` | Overrides de impuestos |
| `Comercial_ImpuestosMapeo` | Mapeo de impuestos |

### Tablas Sync_Producto*
| Tabla | Propósito |
|-------|-----------|
| `Sync_Productos` | Productos sincronizados (fuente de verdad) |
| `Sync_Productos_Recetas` | Recetas de productos (CostoTotal por insumo) |
| `Sync_Productos_Insumos` | Catálogo de insumos con costos |
| `Sync_Productos_Elaborados` | Sub-recetas (elaborados) |

### Tablas Sistema_*
| Tabla | Propósito |
|-------|-----------|
| `Sistema_Empresas` | Empresas |
| `Sistema_EmpresasServidores` | Servidores por empresa |
| `Sistema_UnidadesNegocioPerfilDigital` | Perfiles digitales |

### Tablas de Alertas Existentes
| Tabla | Propósito |
|-------|-----------|
| `Alertas_Sistema` | Alertas genéricas del sistema (Fase 2 Operativo) |

---

## 3. INTEGRACIÓN DE NOTIFICACIONES EXISTENTE

### Email (CONFIGURADO Y FUNCIONAL)
```env
EMAIL_HOST=mail.edarsa.com.mx
EMAIL_PORT=587
EMAIL_USER=notificaciones@edarsa.com.mx
EMAIL_PASSWORD=notificacionesedarsa
EMAIL_USE_TLS=true
EMAIL_FROM=notificaciones@edarsa.com.mx
EMAIL_FROM_NAME="EDARSA HUB"
EMAIL_ENABLED=true
ALERT_EMAIL_TO=admin@edarsa.com.mx
```

**Servicio:** `/app/backend/modules/fase2_operativo/services/email_service.py`
- Usa SMTP vía `core/communications/providers/email_smtp_provider.py`
- Método: `enviar_email(destinatario, asunto, contenido_html)`

### WhatsApp (CONFIGURADO - Twilio Sandbox)
```env
TWILIO_ACCOUNT_SID=ACc41b705a355130d7d5e73920dd9d23b1
TWILIO_AUTH_TOKEN=dceae1314346bbc22bde34cadbf1bdee
TWILIO_WHATSAPP_FROM=+14155238886
WHATSAPP_ENABLED=true
ALERT_WHATSAPP_TO=  # VACÍO - pendiente configurar números destino
```

**Servicio:** `/app/backend/core/communications/providers/twilio_provider.py`
- Clase: `TwilioWhatsAppProvider`
- SDK oficial de Twilio instalado
- Dispatcher en: `/app/backend/core/communications/dispatcher/dispatcher.py`

**NOTA:** WhatsApp está habilitado pero `ALERT_WHATSAPP_TO` está vacío. El sistema debe manejar este caso sin fallar.

---

## 4. ARQUITECTURA DE SYNC_RECETAS

El job `sync_recetas.py` sincroniza:
1. Familias → EDARSAHUB
2. Productos → `Sync_Productos`
3. Insumos → `Sync_Productos_Insumos`
4. Recetas → `Sync_Productos_Recetas`
5. Elaborados → `Sync_Productos_Elaborados`

**IMPORTANTE:** No existe mecanismo de snapshot/fotografía histórica. Cada sync SOBRESCRIBE los datos anteriores.

---

## 5. DDL PROPUESTO PARA FASE COSTOS-ALERTAS-001

### 5.1 Tabla: Comercial_AlertasMargenReglas
```sql
CREATE TABLE Comercial_AlertasMargenReglas (
    ReglaMargenID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    NivelAplicacion VARCHAR(20) NOT NULL CHECK (NivelAplicacion IN ('GRUPO', 'FAMILIA', 'SUBFAMILIA', 'PRODUCTO')),
    
    -- Identificadores según nivel
    GrupoCodigo VARCHAR(100) NULL,
    FamiliaCodigo VARCHAR(100) NULL,
    SubfamiliaCodigo VARCHAR(100) NULL,
    ProductoClave VARCHAR(100) NULL,
    
    -- Alcance opcional
    EmpresaID INT NULL,
    SucursalID INT NULL,
    
    -- Regla de margen
    MargenPorcentajeEsperado DECIMAL(5,2) NULL,
    CostoMaximoPorcentaje DECIMAL(5,2) NULL,
    UtilidadMinimaPorcentaje DECIMAL(5,2) NULL,
    
    -- Configuración
    SeveridadBase VARCHAR(20) DEFAULT 'MEDIA' CHECK (SeveridadBase IN ('INFORMATIVA', 'MEDIA', 'ALTA', 'CRITICA')),
    Activo BIT DEFAULT 1,
    FechaInicioVigencia DATETIME DEFAULT GETDATE(),
    FechaFinVigencia DATETIME NULL,
    
    -- Auditoría
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FechaModificacion DATETIME NULL,
    CreadoPor VARCHAR(100),
    ModificadoPor VARCHAR(100),
    
    -- Índices
    INDEX IX_ReglaMargen_Nivel (NivelAplicacion, Activo),
    INDEX IX_ReglaMargen_Grupo (GrupoCodigo) WHERE NivelAplicacion = 'GRUPO',
    INDEX IX_ReglaMargen_Familia (FamiliaCodigo) WHERE NivelAplicacion = 'FAMILIA',
    INDEX IX_ReglaMargen_Subfamilia (SubfamiliaCodigo) WHERE NivelAplicacion = 'SUBFAMILIA',
    INDEX IX_ReglaMargen_Producto (ProductoClave) WHERE NivelAplicacion = 'PRODUCTO'
);
```

### 5.2 Tabla: Comercial_AlertasMargenEventos
```sql
CREATE TABLE Comercial_AlertasMargenEventos (
    AlertaMargenEventoID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    FechaEvaluacion DATETIME DEFAULT GETDATE(),
    
    -- Producto afectado
    EmpresaID INT NULL,
    SucursalID INT NULL,
    UnidadNegocioID INT NULL,
    ProductoClave VARCHAR(100) NOT NULL,
    ProductoNombre NVARCHAR(500),
    GrupoCodigo VARCHAR(100),
    FamiliaCodigo VARCHAR(100),
    SubfamiliaCodigo VARCHAR(100),
    
    -- Datos de costo/precio
    PrecioVentaActual DECIMAL(18,4),
    CostoRecetaActual DECIMAL(18,4),
    MargenActualPorcentaje DECIMAL(5,2),
    MargenEsperadoPorcentaje DECIMAL(5,2),
    DiferenciaPuntos DECIMAL(5,2),
    UtilidadActual DECIMAL(18,4),
    UtilidadEsperada DECIMAL(18,4),
    PerdidaPorUnidad DECIMAL(18,4),
    
    -- Regla aplicada
    ReglaMargenID UNIQUEIDENTIFIER REFERENCES Comercial_AlertasMargenReglas(ReglaMargenID),
    FuenteRegla VARCHAR(20), -- PRODUCTO, SUBFAMILIA, FAMILIA, GRUPO
    Severidad VARCHAR(20) NOT NULL,
    
    -- Estado
    Estado VARCHAR(20) DEFAULT 'NUEVA' CHECK (Estado IN ('NUEVA', 'ENVIADA', 'ACK', 'RESUELTA', 'IGNORADA')),
    
    -- Datos adicionales
    SnapshotID UNIQUEIDENTIFIER NULL, -- Referencia a snapshot si existe
    Recomendacion NVARCHAR(500),
    ErrorDatos BIT DEFAULT 0,
    
    -- Auditoría
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FechaModificacion DATETIME NULL,
    
    -- Índices
    INDEX IX_AlertaMargen_Fecha (FechaEvaluacion),
    INDEX IX_AlertaMargen_Producto (ProductoClave),
    INDEX IX_AlertaMargen_Estado (Estado),
    INDEX IX_AlertaMargen_Severidad (Severidad)
);
```

### 5.3 Tabla: Comercial_AlertasMargenDestinatarios
```sql
CREATE TABLE Comercial_AlertasMargenDestinatarios (
    DestinatarioID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Nombre NVARCHAR(200) NOT NULL,
    Email VARCHAR(200) NULL,
    TelefonoWhatsApp VARCHAR(20) NULL,
    
    -- Canales habilitados
    CanalEmail BIT DEFAULT 1,
    CanalWhatsApp BIT DEFAULT 0,
    
    -- Alcance (null = global)
    EmpresaID INT NULL,
    SucursalID INT NULL,
    FamiliaCodigo VARCHAR(100) NULL,
    
    -- Filtro de severidad
    SeveridadMinima VARCHAR(20) DEFAULT 'ALTA' CHECK (SeveridadMinima IN ('INFORMATIVA', 'MEDIA', 'ALTA', 'CRITICA')),
    
    -- Estado
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FechaModificacion DATETIME NULL,
    
    INDEX IX_Destinatario_Activo (Activo),
    INDEX IX_Destinatario_Severidad (SeveridadMinima)
);
```

### 5.4 Tabla: Comercial_AlertasMargenEnvios
```sql
CREATE TABLE Comercial_AlertasMargenEnvios (
    EnvioID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    AlertaMargenEventoID UNIQUEIDENTIFIER NOT NULL REFERENCES Comercial_AlertasMargenEventos(AlertaMargenEventoID),
    DestinatarioID UNIQUEIDENTIFIER NOT NULL REFERENCES Comercial_AlertasMargenDestinatarios(DestinatarioID),
    
    Canal VARCHAR(20) NOT NULL CHECK (Canal IN ('EMAIL', 'WHATSAPP')),
    EstadoEnvio VARCHAR(20) DEFAULT 'PENDIENTE' CHECK (EstadoEnvio IN ('PENDIENTE', 'ENVIADO', 'ERROR', 'PENDIENTE_CONFIGURACION')),
    
    FechaIntento DATETIME NULL,
    FechaEnvio DATETIME NULL,
    ErrorMensajeSeguro NVARCHAR(500) NULL, -- Sin datos sensibles
    ProviderMessageID VARCHAR(200) NULL,
    
    FechaCreacion DATETIME DEFAULT GETDATE(),
    
    INDEX IX_Envio_Estado (EstadoEnvio),
    INDEX IX_Envio_Alerta (AlertaMargenEventoID)
);
```

### 5.5 Tabla: Comercial_AlertasUmbralesSeveridad
```sql
CREATE TABLE Comercial_AlertasUmbralesSeveridad (
    UmbralID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Severidad VARCHAR(20) NOT NULL,
    PuntosDesde DECIMAL(5,2) NOT NULL,
    PuntosHasta DECIMAL(5,2) NOT NULL,
    IncluirUtilidadNegativa BIT DEFAULT 0,
    Descripcion NVARCHAR(200),
    Activo BIT DEFAULT 1,
    
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FechaModificacion DATETIME NULL,
    
    INDEX IX_Umbral_Severidad (Severidad, Activo)
);

-- Datos iniciales
INSERT INTO Comercial_AlertasUmbralesSeveridad (Severidad, PuntosDesde, PuntosHasta, IncluirUtilidadNegativa, Descripcion)
VALUES 
    ('INFORMATIVA', 0, 1.99, 0, 'Margen debajo del esperado por menos de 2 puntos'),
    ('MEDIA', 2, 4.99, 0, 'Margen debajo del esperado entre 2 y 5 puntos'),
    ('ALTA', 5, 9.99, 0, 'Margen debajo del esperado entre 5 y 10 puntos'),
    ('CRITICA', 10, 999, 1, 'Margen debajo por más de 10 puntos o utilidad negativa');
```

### 5.6 Tablas de Snapshot (PROPUESTAS - Sujetas a autorización)

```sql
-- Snapshot de recetas para comparación histórica
CREATE TABLE Comercial_RecetasSnapshot (
    RecetaSnapshotID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    FechaSnapshot DATETIME DEFAULT GETDATE(),
    
    EmpresaID INT NULL,
    SucursalID INT NULL,
    UnidadNegocioID INT NULL,
    ServerID UNIQUEIDENTIFIER NULL,
    
    ProductoClave VARCHAR(100) NOT NULL,
    ProductoNombre NVARCHAR(500),
    
    PrecioVenta DECIMAL(18,4),
    CostoRecetaTotal DECIMAL(18,4),
    MargenPorcentaje DECIMAL(5,2),
    MargenMonto DECIMAL(18,4),
    
    HashReceta VARCHAR(64), -- SHA256 de la receta para detectar cambios
    FuenteCalculo VARCHAR(50), -- SYNC_RECETAS, MANUAL, etc.
    
    FechaCreacion DATETIME DEFAULT GETDATE(),
    CreadoPor VARCHAR(100),
    
    INDEX IX_Snapshot_Fecha (FechaSnapshot),
    INDEX IX_Snapshot_Producto (ProductoClave)
);

-- Detalle de snapshot para auditoría
CREATE TABLE Comercial_RecetasSnapshotDetalle (
    RecetaSnapshotDetalleID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    RecetaSnapshotID UNIQUEIDENTIFIER NOT NULL REFERENCES Comercial_RecetasSnapshot(RecetaSnapshotID),
    
    InsumoClave VARCHAR(100),
    InsumoNombre NVARCHAR(500),
    Cantidad DECIMAL(18,6),
    Unidad VARCHAR(50),
    CostoUnitario DECIMAL(18,4),
    CostoTotal DECIMAL(18,4),
    PorcentajeDelCosto DECIMAL(5,2),
    
    FechaCreacion DATETIME DEFAULT GETDATE(),
    
    INDEX IX_SnapshotDetalle_Snapshot (RecetaSnapshotID)
);
```

---

## 6. JERARQUÍA DE RESOLUCIÓN DE REGLAS

```
1. PRODUCTO      → Si existe regla activa para ProductoClave, usar esa
2. SUBFAMILIA    → Si no, buscar regla activa para SubfamiliaCodigo
3. FAMILIA       → Si no, buscar regla activa para FamiliaCodigo
4. GRUPO         → Si no, buscar regla activa para GrupoCodigo
5. SIN_REGLA     → Estado especial, no genera alerta crítica por defecto
```

**SQL de Resolución:**
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

## 7. FLUJO PROPUESTO DEL JOB

```
1. Leer productos activos de Sync_Productos (WHERE Activo = 1)
2. Para cada producto:
   a. Obtener costo de receta actual (Sync_Productos_Recetas)
   b. Calcular margen actual: (PrecioVenta - CostoReceta) / PrecioVenta * 100
   c. Resolver regla de margen esperado (jerarquía)
   d. Si sin regla → estado SIN_REGLA_MARGEN_ESPERADO
   e. Si margen < esperado:
      i. Calcular diferencia en puntos
      ii. Determinar severidad según umbrales
      iii. Verificar si ya existe alerta abierta (evitar duplicados)
      iv. Crear AlertaMargenEvento
      v. Obtener destinatarios según severidad y alcance
      vi. Crear registros de envío pendiente
3. Procesar envíos pendientes:
   a. Email: Usar EmailService existente
   b. WhatsApp: Usar TwilioWhatsAppProvider si configurado
   c. Si no configurado: Estado PENDIENTE_CONFIGURACION
4. Actualizar estados de alertas
5. Opcionalmente: Crear snapshot de receta
```

---

## 8. PRÓXIMOS PASOS (PENDIENTE AUTORIZACIÓN)

| # | Paso | Dependencia |
|---|------|-------------|
| 1 | Crear DDL de tablas | Autorización |
| 2 | Implementar repository `alertas_margen_repository.py` | DDL creado |
| 3 | Implementar servicio `alertas_margen_service.py` | Repository |
| 4 | Implementar job `alertas_margen_job.py` | Servicio |
| 5 | Crear endpoints CRUD de reglas | Servicio |
| 6 | Integrar en frontend (nueva pestaña en Costos y Márgenes) | Endpoints |
| 7 | Crear scheduler (APScheduler o cron) | Job |
| 8 | Implementar snapshots (opcional) | Autorización adicional |

---

## 9. RIESGOS IDENTIFICADOS

| Riesgo | Mitigación |
|--------|------------|
| WhatsApp sin número destino configurado | Estado PENDIENTE_CONFIGURACION sin fallar |
| SQL Server no accesible desde preview | Pruebas locales/staging |
| Alertas duplicadas masivas | Control de frecuencia y estado |
| Tokens IA desperdiciados | Ya resuelto con BUG-COSTOS-001 |

---

## 10. CUMPLIMIENTO DE MÁXIMAS

| Máxima | Estado |
|--------|--------|
| EDARSAHUB SQL es el cerebro | ✅ |
| CERO MongoDB | ✅ |
| No modificar precios oficiales | ✅ (solo alerta) |
| No modificar recetas oficiales | ✅ (solo lectura) |
| No usar IA para decidir alertas | ✅ (reglas determinísticas) |
| Alertas calculadas en backend/job | ✅ |

---

**Diagnóstico preparado por:** Agente E1  
**Pendiente:** Autorización para ejecutar DDL e implementación
