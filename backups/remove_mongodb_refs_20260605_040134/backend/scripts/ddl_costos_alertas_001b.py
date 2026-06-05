"""
COSTOS-ALERTAS-001-B: DDL para Sistema de Alertas de Margen y Snapshots de Recetas

FASE: Creación de tablas SQL
AUTORIZACIÓN: Usuario confirmó 2025-05-25
MÁXIMAS: EDARSAHUB SQL es el cerebro. CERO MongoDB.

TABLAS A CREAR:
1. Comercial_AlertasMargenReglas - Reglas de margen esperado por nivel
2. Comercial_AlertasMargenEventos - Eventos de alerta detectados
3. Comercial_AlertasMargenDestinatarios - Destinatarios de alertas
4. Comercial_AlertasMargenEnvios - Registro de envíos
5. Comercial_AlertasUmbralesSeveridad - Configuración de severidades
6. Comercial_RecetasSnapshot - Fotografías históricas de recetas
7. Comercial_RecetasSnapshotDetalle - Detalle de snapshots

JERARQUÍA DE REGLAS SOPORTADA:
Producto > Subfamilia > Familia > Grupo
"""

import sys
sys.path.insert(0, '/app/backend')

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG


def get_conn():
    """Conexión a EDARSAHUB SQL"""
    return (
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password']
    )


# =============================================================================
# DDL IDEMPOTENTE - TABLAS DE ALERTAS DE MARGEN
# =============================================================================

DDL_TABLA_1_REGLAS = """
-- TABLA 1: Comercial_AlertasMargenReglas
-- Reglas de margen esperado por nivel (Producto > Subfamilia > Familia > Grupo)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Comercial_AlertasMargenReglas')
BEGIN
    CREATE TABLE Comercial_AlertasMargenReglas (
        ReglaMargenID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        
        -- Nivel de aplicación con prioridad
        NivelAplicacion VARCHAR(20) NOT NULL,
        
        -- Identificadores según nivel (solo uno debe estar poblado según NivelAplicacion)
        GrupoCodigo VARCHAR(100) NULL,
        FamiliaCodigo VARCHAR(100) NULL,
        SubfamiliaCodigo VARCHAR(100) NULL,
        ProductoClave VARCHAR(100) NULL,
        
        -- Alcance opcional (null = aplica a todas)
        EmpresaID INT NULL,
        SucursalID INT NULL,
        ServerID UNIQUEIDENTIFIER NULL,
        
        -- Configuración de margen/costo/utilidad
        MargenPorcentajeEsperado DECIMAL(5,2) NULL,
        CostoMaximoPorcentaje DECIMAL(5,2) NULL,
        UtilidadMinimaPorcentaje DECIMAL(5,2) NULL,
        
        -- Configuración de alerta
        SeveridadBase VARCHAR(20) DEFAULT 'MEDIA',
        Descripcion NVARCHAR(500) NULL,
        
        -- Estado y vigencia
        Activo BIT DEFAULT 1,
        FechaInicioVigencia DATETIME DEFAULT GETDATE(),
        FechaFinVigencia DATETIME NULL,
        
        -- Auditoría
        FechaCreacion DATETIME DEFAULT GETDATE(),
        FechaModificacion DATETIME NULL,
        CreadoPor VARCHAR(100) NULL,
        ModificadoPor VARCHAR(100) NULL,
        
        -- Constraints
        CONSTRAINT CK_AlertasMargenReglas_Nivel CHECK (
            NivelAplicacion IN ('GRUPO', 'FAMILIA', 'SUBFAMILIA', 'PRODUCTO')
        ),
        CONSTRAINT CK_AlertasMargenReglas_Severidad CHECK (
            SeveridadBase IN ('INFORMATIVA', 'MEDIA', 'ALTA', 'CRITICA')
        ),
        CONSTRAINT CK_AlertasMargenReglas_MargenValido CHECK (
            MargenPorcentajeEsperado IS NULL OR (MargenPorcentajeEsperado >= 0 AND MargenPorcentajeEsperado <= 100)
        ),
        CONSTRAINT CK_AlertasMargenReglas_CostoValido CHECK (
            CostoMaximoPorcentaje IS NULL OR (CostoMaximoPorcentaje >= 0 AND CostoMaximoPorcentaje <= 100)
        ),
        CONSTRAINT CK_AlertasMargenReglas_UtilidadValida CHECK (
            UtilidadMinimaPorcentaje IS NULL OR (UtilidadMinimaPorcentaje >= -100 AND UtilidadMinimaPorcentaje <= 100)
        )
    );
    
    -- Índices
    CREATE INDEX IX_AlertasMargenReglas_Nivel ON Comercial_AlertasMargenReglas(NivelAplicacion, Activo);
    CREATE INDEX IX_AlertasMargenReglas_Grupo ON Comercial_AlertasMargenReglas(GrupoCodigo) WHERE NivelAplicacion = 'GRUPO';
    CREATE INDEX IX_AlertasMargenReglas_Familia ON Comercial_AlertasMargenReglas(FamiliaCodigo) WHERE NivelAplicacion = 'FAMILIA';
    CREATE INDEX IX_AlertasMargenReglas_Subfamilia ON Comercial_AlertasMargenReglas(SubfamiliaCodigo) WHERE NivelAplicacion = 'SUBFAMILIA';
    CREATE INDEX IX_AlertasMargenReglas_Producto ON Comercial_AlertasMargenReglas(ProductoClave) WHERE NivelAplicacion = 'PRODUCTO';
    CREATE INDEX IX_AlertasMargenReglas_Vigencia ON Comercial_AlertasMargenReglas(Activo, FechaInicioVigencia, FechaFinVigencia);
    
    PRINT 'Tabla Comercial_AlertasMargenReglas creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Comercial_AlertasMargenReglas ya existe';
END
"""

DDL_TABLA_2_EVENTOS = """
-- TABLA 2: Comercial_AlertasMargenEventos
-- Eventos de alerta detectados por el job de evaluación
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Comercial_AlertasMargenEventos')
BEGIN
    CREATE TABLE Comercial_AlertasMargenEventos (
        AlertaMargenEventoID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        FechaEvaluacion DATETIME DEFAULT GETDATE(),
        
        -- Identificación del producto
        ServerID UNIQUEIDENTIFIER NULL,
        EmpresaID INT NULL,
        SucursalID INT NULL,
        UnidadNegocioID INT NULL,
        ProductoClave VARCHAR(100) NOT NULL,
        ProductoNombre NVARCHAR(500) NULL,
        GrupoCodigo VARCHAR(100) NULL,
        FamiliaCodigo VARCHAR(100) NULL,
        SubfamiliaCodigo VARCHAR(100) NULL,
        
        -- Datos de costo/precio al momento de la evaluación
        PrecioVentaActual DECIMAL(18,4) NULL,
        CostoRecetaActual DECIMAL(18,4) NULL,
        MargenActualPorcentaje DECIMAL(5,2) NULL,
        MargenActualMonto DECIMAL(18,4) NULL,
        
        -- Comparación con margen esperado
        MargenEsperadoPorcentaje DECIMAL(5,2) NULL,
        DiferenciaPuntos DECIMAL(5,2) NULL,
        UtilidadActual DECIMAL(18,4) NULL,
        UtilidadEsperada DECIMAL(18,4) NULL,
        PerdidaPorUnidad DECIMAL(18,4) NULL,
        
        -- Regla aplicada
        ReglaMargenID UNIQUEIDENTIFIER NULL,
        FuenteRegla VARCHAR(20) NULL,
        Severidad VARCHAR(20) NOT NULL,
        
        -- Estado del evento
        Estado VARCHAR(30) DEFAULT 'NUEVA',
        
        -- Datos adicionales
        SnapshotID UNIQUEIDENTIFIER NULL,
        VariacionCostoAnterior DECIMAL(18,4) NULL,
        VariacionCostoAcumulada DECIMAL(18,4) NULL,
        Recomendacion NVARCHAR(500) NULL,
        ErrorDatos BIT DEFAULT 0,
        NotasInternas NVARCHAR(MAX) NULL,
        
        -- Auditoría
        FechaCreacion DATETIME DEFAULT GETDATE(),
        FechaModificacion DATETIME NULL,
        FechaResolucion DATETIME NULL,
        ResueltoPor VARCHAR(100) NULL,
        
        -- Constraints
        CONSTRAINT CK_AlertasMargenEventos_Severidad CHECK (
            Severidad IN ('INFORMATIVA', 'MEDIA', 'ALTA', 'CRITICA')
        ),
        CONSTRAINT CK_AlertasMargenEventos_Estado CHECK (
            Estado IN ('NUEVA', 'ENVIADA', 'ACK', 'EN_REVISION', 'RESUELTA', 'IGNORADA', 'DUPLICADA')
        ),
        CONSTRAINT CK_AlertasMargenEventos_FuenteRegla CHECK (
            FuenteRegla IS NULL OR FuenteRegla IN ('PRODUCTO', 'SUBFAMILIA', 'FAMILIA', 'GRUPO', 'SIN_REGLA')
        )
    );
    
    -- Índices
    CREATE INDEX IX_AlertasMargenEventos_Fecha ON Comercial_AlertasMargenEventos(FechaEvaluacion DESC);
    CREATE INDEX IX_AlertasMargenEventos_Producto ON Comercial_AlertasMargenEventos(ProductoClave);
    CREATE INDEX IX_AlertasMargenEventos_Estado ON Comercial_AlertasMargenEventos(Estado);
    CREATE INDEX IX_AlertasMargenEventos_Severidad ON Comercial_AlertasMargenEventos(Severidad);
    CREATE INDEX IX_AlertasMargenEventos_Server ON Comercial_AlertasMargenEventos(ServerID);
    CREATE INDEX IX_AlertasMargenEventos_Regla ON Comercial_AlertasMargenEventos(ReglaMargenID);
    CREATE INDEX IX_AlertasMargenEventos_Duplicados ON Comercial_AlertasMargenEventos(ProductoClave, ServerID, Estado, Severidad);
    
    PRINT 'Tabla Comercial_AlertasMargenEventos creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Comercial_AlertasMargenEventos ya existe';
END
"""

DDL_TABLA_3_DESTINATARIOS = """
-- TABLA 3: Comercial_AlertasMargenDestinatarios
-- Destinatarios de alertas (email y/o WhatsApp)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Comercial_AlertasMargenDestinatarios')
BEGIN
    CREATE TABLE Comercial_AlertasMargenDestinatarios (
        DestinatarioID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        Nombre NVARCHAR(200) NOT NULL,
        
        -- Canales de notificación
        Email VARCHAR(200) NULL,
        TelefonoWhatsApp VARCHAR(20) NULL,
        CanalEmail BIT DEFAULT 1,
        CanalWhatsApp BIT DEFAULT 0,
        
        -- Alcance de alertas que recibe (null = global)
        EmpresaID INT NULL,
        SucursalID INT NULL,
        ServerID UNIQUEIDENTIFIER NULL,
        FamiliaCodigo VARCHAR(100) NULL,
        
        -- Filtro de severidad mínima
        SeveridadMinima VARCHAR(20) DEFAULT 'ALTA',
        
        -- Configuración
        RecibeResumen BIT DEFAULT 1,
        RecibeDetalle BIT DEFAULT 1,
        FrecuenciaMaximaDiaria INT DEFAULT 10,
        HoraPreferida VARCHAR(5) DEFAULT '08:00',
        
        -- Estado
        Activo BIT DEFAULT 1,
        
        -- Auditoría
        FechaCreacion DATETIME DEFAULT GETDATE(),
        FechaModificacion DATETIME NULL,
        CreadoPor VARCHAR(100) NULL,
        ModificadoPor VARCHAR(100) NULL,
        
        -- Constraints
        CONSTRAINT CK_AlertasMargenDestinatarios_Severidad CHECK (
            SeveridadMinima IN ('INFORMATIVA', 'MEDIA', 'ALTA', 'CRITICA')
        ),
        CONSTRAINT CK_AlertasMargenDestinatarios_CanalRequerido CHECK (
            Email IS NOT NULL OR TelefonoWhatsApp IS NOT NULL
        )
    );
    
    -- Índices
    CREATE INDEX IX_AlertasMargenDestinatarios_Activo ON Comercial_AlertasMargenDestinatarios(Activo);
    CREATE INDEX IX_AlertasMargenDestinatarios_Severidad ON Comercial_AlertasMargenDestinatarios(SeveridadMinima);
    CREATE INDEX IX_AlertasMargenDestinatarios_Empresa ON Comercial_AlertasMargenDestinatarios(EmpresaID);
    CREATE INDEX IX_AlertasMargenDestinatarios_Server ON Comercial_AlertasMargenDestinatarios(ServerID);
    
    PRINT 'Tabla Comercial_AlertasMargenDestinatarios creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Comercial_AlertasMargenDestinatarios ya existe';
END
"""

DDL_TABLA_4_ENVIOS = """
-- TABLA 4: Comercial_AlertasMargenEnvios
-- Registro de envíos de alertas (email/WhatsApp)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Comercial_AlertasMargenEnvios')
BEGIN
    CREATE TABLE Comercial_AlertasMargenEnvios (
        EnvioID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        AlertaMargenEventoID UNIQUEIDENTIFIER NOT NULL,
        DestinatarioID UNIQUEIDENTIFIER NOT NULL,
        
        -- Canal y estado
        Canal VARCHAR(20) NOT NULL,
        EstadoEnvio VARCHAR(30) DEFAULT 'PENDIENTE',
        
        -- Tracking de intentos
        FechaIntento DATETIME NULL,
        FechaEnvio DATETIME NULL,
        NumeroIntentos INT DEFAULT 0,
        
        -- Respuesta del proveedor (sin datos sensibles)
        ProviderMessageID VARCHAR(200) NULL,
        ErrorMensajeSeguro NVARCHAR(500) NULL,
        
        -- Auditoría
        FechaCreacion DATETIME DEFAULT GETDATE(),
        
        -- Constraints
        CONSTRAINT CK_AlertasMargenEnvios_Canal CHECK (
            Canal IN ('EMAIL', 'WHATSAPP')
        ),
        CONSTRAINT CK_AlertasMargenEnvios_Estado CHECK (
            EstadoEnvio IN ('PENDIENTE', 'EN_PROCESO', 'ENVIADO', 'ERROR', 'PENDIENTE_CONFIGURACION', 'OMITIDO')
        )
    );
    
    -- Índices
    CREATE INDEX IX_AlertasMargenEnvios_Alerta ON Comercial_AlertasMargenEnvios(AlertaMargenEventoID);
    CREATE INDEX IX_AlertasMargenEnvios_Destinatario ON Comercial_AlertasMargenEnvios(DestinatarioID);
    CREATE INDEX IX_AlertasMargenEnvios_Estado ON Comercial_AlertasMargenEnvios(EstadoEnvio);
    CREATE INDEX IX_AlertasMargenEnvios_Canal ON Comercial_AlertasMargenEnvios(Canal, EstadoEnvio);
    CREATE INDEX IX_AlertasMargenEnvios_Fecha ON Comercial_AlertasMargenEnvios(FechaCreacion DESC);
    
    PRINT 'Tabla Comercial_AlertasMargenEnvios creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Comercial_AlertasMargenEnvios ya existe';
END
"""

DDL_TABLA_5_UMBRALES = """
-- TABLA 5: Comercial_AlertasUmbralesSeveridad
-- Configuración de umbrales para determinar severidad de alertas
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Comercial_AlertasUmbralesSeveridad')
BEGIN
    CREATE TABLE Comercial_AlertasUmbralesSeveridad (
        UmbralID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        Severidad VARCHAR(20) NOT NULL,
        
        -- Rango de diferencia en puntos porcentuales
        PuntosDesde DECIMAL(5,2) NOT NULL,
        PuntosHasta DECIMAL(5,2) NOT NULL,
        
        -- Condiciones adicionales
        IncluirUtilidadNegativa BIT DEFAULT 0,
        IncluirCostoMayorPrecio BIT DEFAULT 0,
        
        -- Descripción
        Descripcion NVARCHAR(200) NULL,
        ColorHex VARCHAR(7) DEFAULT '#FFA500',
        
        -- Estado
        Activo BIT DEFAULT 1,
        Orden INT DEFAULT 0,
        
        -- Auditoría
        FechaCreacion DATETIME DEFAULT GETDATE(),
        FechaModificacion DATETIME NULL,
        
        -- Constraints
        CONSTRAINT CK_AlertasUmbralesSeveridad_Severidad CHECK (
            Severidad IN ('INFORMATIVA', 'MEDIA', 'ALTA', 'CRITICA')
        ),
        CONSTRAINT CK_AlertasUmbralesSeveridad_Rango CHECK (
            PuntosDesde <= PuntosHasta
        )
    );
    
    -- Índices
    CREATE INDEX IX_AlertasUmbralesSeveridad_Activo ON Comercial_AlertasUmbralesSeveridad(Activo, Orden);
    CREATE INDEX IX_AlertasUmbralesSeveridad_Severidad ON Comercial_AlertasUmbralesSeveridad(Severidad);
    
    PRINT 'Tabla Comercial_AlertasUmbralesSeveridad creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Comercial_AlertasUmbralesSeveridad ya existe';
END
"""

DDL_TABLA_6_SNAPSHOT = """
-- TABLA 6: Comercial_RecetasSnapshot
-- Fotografías históricas de recetas para comparación de costos
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Comercial_RecetasSnapshot')
BEGIN
    CREATE TABLE Comercial_RecetasSnapshot (
        RecetaSnapshotID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        FechaSnapshot DATETIME DEFAULT GETDATE(),
        
        -- Identificación del producto
        ServerID UNIQUEIDENTIFIER NULL,
        EmpresaID INT NULL,
        SucursalID INT NULL,
        UnidadNegocioID INT NULL,
        ProductoClave VARCHAR(100) NOT NULL,
        ProductoNombre NVARCHAR(500) NULL,
        
        -- Datos de precio y costo al momento del snapshot
        PrecioVenta DECIMAL(18,4) NULL,
        CostoRecetaTotal DECIMAL(18,4) NULL,
        MargenPorcentaje DECIMAL(5,2) NULL,
        MargenMonto DECIMAL(18,4) NULL,
        
        -- Metadata de la receta
        NumeroInsumos INT DEFAULT 0,
        HashReceta VARCHAR(64) NULL,
        FuenteCalculo VARCHAR(50) DEFAULT 'SYNC_RECETAS',
        
        -- Comparación con snapshot anterior
        SnapshotAnteriorID UNIQUEIDENTIFIER NULL,
        VariacionCosto DECIMAL(18,4) NULL,
        VariacionCostoPorcentaje DECIMAL(5,2) NULL,
        VariacionMargen DECIMAL(5,2) NULL,
        
        -- Estado
        EsActual BIT DEFAULT 1,
        
        -- Auditoría
        FechaCreacion DATETIME DEFAULT GETDATE(),
        CreadoPor VARCHAR(100) DEFAULT 'SISTEMA',
        SyncRunID VARCHAR(100) NULL,
        
        -- Constraint
        CONSTRAINT CK_RecetasSnapshot_Fuente CHECK (
            FuenteCalculo IN ('SYNC_RECETAS', 'MANUAL', 'JOB_ALERTAS', 'IMPORTACION')
        )
    );
    
    -- Índices
    CREATE INDEX IX_RecetasSnapshot_Fecha ON Comercial_RecetasSnapshot(FechaSnapshot DESC);
    CREATE INDEX IX_RecetasSnapshot_Producto ON Comercial_RecetasSnapshot(ProductoClave);
    CREATE INDEX IX_RecetasSnapshot_Server ON Comercial_RecetasSnapshot(ServerID);
    CREATE INDEX IX_RecetasSnapshot_Actual ON Comercial_RecetasSnapshot(ProductoClave, ServerID, EsActual) WHERE EsActual = 1;
    CREATE INDEX IX_RecetasSnapshot_Hash ON Comercial_RecetasSnapshot(HashReceta);
    
    PRINT 'Tabla Comercial_RecetasSnapshot creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Comercial_RecetasSnapshot ya existe';
END
"""

DDL_TABLA_7_SNAPSHOT_DETALLE = """
-- TABLA 7: Comercial_RecetasSnapshotDetalle
-- Detalle de insumos en cada snapshot de receta
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Comercial_RecetasSnapshotDetalle')
BEGIN
    CREATE TABLE Comercial_RecetasSnapshotDetalle (
        RecetaSnapshotDetalleID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        RecetaSnapshotID UNIQUEIDENTIFIER NOT NULL,
        
        -- Identificación del insumo
        InsumoClave VARCHAR(100) NOT NULL,
        InsumoNombre NVARCHAR(500) NULL,
        
        -- Datos de cantidad y costo
        Cantidad DECIMAL(18,6) NULL,
        UnidadMedida VARCHAR(50) NULL,
        CostoUnitario DECIMAL(18,4) NULL,
        CostoTotal DECIMAL(18,4) NULL,
        
        -- Análisis
        PorcentajeDelCosto DECIMAL(5,2) NULL,
        EsElaborado BIT DEFAULT 0,
        
        -- Comparación con snapshot anterior (si existe)
        CostoAnterior DECIMAL(18,4) NULL,
        VariacionCosto DECIMAL(18,4) NULL,
        VariacionCostoPorcentaje DECIMAL(5,2) NULL,
        
        -- Auditoría
        FechaCreacion DATETIME DEFAULT GETDATE(),
        Orden INT DEFAULT 0
    );
    
    -- Índices
    CREATE INDEX IX_RecetasSnapshotDetalle_Snapshot ON Comercial_RecetasSnapshotDetalle(RecetaSnapshotID);
    CREATE INDEX IX_RecetasSnapshotDetalle_Insumo ON Comercial_RecetasSnapshotDetalle(InsumoClave);
    CREATE INDEX IX_RecetasSnapshotDetalle_Costo ON Comercial_RecetasSnapshotDetalle(RecetaSnapshotID, CostoTotal DESC);
    
    PRINT 'Tabla Comercial_RecetasSnapshotDetalle creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Comercial_RecetasSnapshotDetalle ya existe';
END
"""

# =============================================================================
# DATOS SEMILLA - UMBRALES DE SEVERIDAD
# =============================================================================

DDL_UMBRALES_SEMILLA = """
-- Insertar umbrales de severidad si no existen
IF NOT EXISTS (SELECT 1 FROM Comercial_AlertasUmbralesSeveridad WHERE Activo = 1)
BEGIN
    INSERT INTO Comercial_AlertasUmbralesSeveridad 
        (Severidad, PuntosDesde, PuntosHasta, IncluirUtilidadNegativa, IncluirCostoMayorPrecio, Descripcion, ColorHex, Orden)
    VALUES 
        ('INFORMATIVA', 0, 1.99, 0, 0, 'Margen debajo del esperado por menos de 2 puntos porcentuales', '#3B82F6', 1),
        ('MEDIA', 2, 4.99, 0, 0, 'Margen debajo del esperado entre 2 y 5 puntos porcentuales', '#F59E0B', 2),
        ('ALTA', 5, 9.99, 0, 0, 'Margen debajo del esperado entre 5 y 10 puntos porcentuales', '#F97316', 3),
        ('CRITICA', 10, 999, 1, 1, 'Margen debajo por mas de 10 puntos, utilidad negativa o costo mayor a precio', '#EF4444', 4);
    
    PRINT 'Umbrales de severidad insertados exitosamente';
END
ELSE
BEGIN
    PRINT 'Umbrales de severidad ya existen';
END
"""


def ejecutar_ddl():
    """Ejecuta todo el DDL de forma idempotente."""
    conn = get_conn()
    resultados = {
        'tablas_creadas': [],
        'tablas_existentes': [],
        'errores': [],
        'umbrales_insertados': False
    }
    
    ddls = [
        ('Comercial_AlertasMargenReglas', DDL_TABLA_1_REGLAS),
        ('Comercial_AlertasMargenEventos', DDL_TABLA_2_EVENTOS),
        ('Comercial_AlertasMargenDestinatarios', DDL_TABLA_3_DESTINATARIOS),
        ('Comercial_AlertasMargenEnvios', DDL_TABLA_4_ENVIOS),
        ('Comercial_AlertasUmbralesSeveridad', DDL_TABLA_5_UMBRALES),
        ('Comercial_RecetasSnapshot', DDL_TABLA_6_SNAPSHOT),
        ('Comercial_RecetasSnapshotDetalle', DDL_TABLA_7_SNAPSHOT_DETALLE),
    ]
    
    print("=" * 60)
    print("COSTOS-ALERTAS-001-B: Ejecutando DDL")
    print("=" * 60)
    
    for tabla_nombre, ddl in ddls:
        try:
            print(f"\n[DDL] Procesando {tabla_nombre}...")
            execute_sql_query(*conn, ddl)
            
            # Verificar si la tabla existe
            check_query = f"SELECT 1 FROM sys.tables WHERE name = '{tabla_nombre}'"
            result = execute_sql_query(*conn, check_query)
            
            if result:
                print(f"[OK] {tabla_nombre} - Tabla verificada")
                resultados['tablas_creadas'].append(tabla_nombre)
            else:
                print(f"[WARN] {tabla_nombre} - No se pudo verificar")
                resultados['errores'].append(f"{tabla_nombre}: No verificada")
                
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower() or "ya existe" in error_msg.lower():
                print(f"[INFO] {tabla_nombre} - Ya existe (idempotente)")
                resultados['tablas_existentes'].append(tabla_nombre)
            else:
                print(f"[ERROR] {tabla_nombre} - {error_msg[:100]}")
                resultados['errores'].append(f"{tabla_nombre}: {error_msg[:100]}")
    
    # Insertar umbrales semilla
    print("\n[DDL] Insertando umbrales de severidad...")
    try:
        execute_sql_query(*conn, DDL_UMBRALES_SEMILLA)
        
        # Verificar umbrales
        check_umbrales = "SELECT COUNT(*) as cnt FROM Comercial_AlertasUmbralesSeveridad WHERE Activo = 1"
        result = execute_sql_query(*conn, check_umbrales)
        cnt = result[0].get('cnt', 0) if result else 0
        
        if cnt >= 4:
            print(f"[OK] Umbrales de severidad: {cnt} registros activos")
            resultados['umbrales_insertados'] = True
        else:
            print(f"[WARN] Umbrales insuficientes: {cnt}")
            
    except Exception as e:
        print(f"[ERROR] Umbrales: {str(e)[:100]}")
        resultados['errores'].append(f"Umbrales: {str(e)[:100]}")
    
    return resultados


def validar_tablas():
    """Valida que todas las tablas existan."""
    conn = get_conn()
    tablas_requeridas = [
        'Comercial_AlertasMargenReglas',
        'Comercial_AlertasMargenEventos',
        'Comercial_AlertasMargenDestinatarios',
        'Comercial_AlertasMargenEnvios',
        'Comercial_AlertasUmbralesSeveridad',
        'Comercial_RecetasSnapshot',
        'Comercial_RecetasSnapshotDetalle'
    ]
    
    print("\n" + "=" * 60)
    print("VALIDACIÓN DE TABLAS")
    print("=" * 60)
    
    todas_ok = True
    for tabla in tablas_requeridas:
        query = f"SELECT 1 FROM sys.tables WHERE name = '{tabla}'"
        result = execute_sql_query(*conn, query)
        
        if result:
            print(f"[OK] {tabla}")
        else:
            print(f"[FALTA] {tabla}")
            todas_ok = False
    
    # Validar umbrales
    query_umbrales = "SELECT Severidad, PuntosDesde, PuntosHasta FROM Comercial_AlertasUmbralesSeveridad WHERE Activo = 1 ORDER BY Orden"
    umbrales = execute_sql_query(*conn, query_umbrales)
    
    print("\n[UMBRALES DE SEVERIDAD]")
    if umbrales:
        for u in umbrales:
            print(f"  - {u['Severidad']}: {u['PuntosDesde']} - {u['PuntosHasta']} puntos")
    else:
        print("  [WARN] No hay umbrales configurados")
        todas_ok = False
    
    return todas_ok


def main():
    """Función principal."""
    print("\n" + "=" * 60)
    print("COSTOS-ALERTAS-001-B: CREACIÓN DE DDL")
    print("MÁXIMAS: EDARSAHUB SQL es el cerebro. CERO MongoDB.")
    print("=" * 60)
    
    # Ejecutar DDL
    resultados = ejecutar_ddl()
    
    # Validar
    tablas_ok = validar_tablas()
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE EJECUCIÓN")
    print("=" * 60)
    print(f"Tablas creadas/verificadas: {len(resultados['tablas_creadas'])}")
    print(f"Tablas ya existentes: {len(resultados['tablas_existentes'])}")
    print(f"Errores: {len(resultados['errores'])}")
    print(f"Umbrales insertados: {'Sí' if resultados['umbrales_insertados'] else 'No'}")
    print(f"Validación final: {'EXITOSA' if tablas_ok else 'CON PROBLEMAS'}")
    
    if resultados['errores']:
        print("\nErrores encontrados:")
        for e in resultados['errores']:
            print(f"  - {e}")
    
    return tablas_ok


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
