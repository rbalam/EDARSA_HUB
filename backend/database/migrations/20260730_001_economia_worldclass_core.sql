/*
EDARSAHUB V1.0
Economia WorldClass - nucleo canonico de series economicas.

REGLAS:
- SQL-First.
- NO MongoDB.
- NO conexiones LIVE para dashboards.
- NO hardcodes de paises, indicadores, proveedores o frecuencias.
- Indicadores futuros deben ser datos, no columnas nuevas.
- Reutiliza Sistema_Empresas, Unidades_Negocio, Proveedor_Monedas,
  Servidores_Conexiones, scheduler y RBAC existentes.
- Las tablas transaccionales con TipoCambio NO son fuente macroeconomica FX.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    /* ================================================================
       1. Paises / geografias economicas
       ================================================================ */

    IF OBJECT_ID('dbo.Economia_Paises', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Economia_Paises
        (
            PaisID                  int IDENTITY(1,1) NOT NULL,
            CodigoISO2              char(2) NOT NULL,
            CodigoISO3              char(3) NOT NULL,
            CodigoNumericoISO       char(3) NULL,
            Nombre                  nvarchar(150) NOT NULL,
            NombreOficial           nvarchar(250) NULL,
            MonedaID                smallint NULL,
            RegionCodigo            nvarchar(50) NULL,
            SubregionCodigo         nvarchar(50) NULL,
            Activo                  bit NOT NULL
                CONSTRAINT DF_Economia_Paises_Activo DEFAULT (1),
            FechaCreacionUTC        datetime2(3) NOT NULL
                CONSTRAINT DF_Economia_Paises_FechaCreacionUTC DEFAULT (SYSUTCDATETIME()),
            FechaModificacionUTC    datetime2(3) NULL,

            CONSTRAINT PK_Economia_Paises
                PRIMARY KEY CLUSTERED (PaisID),

            CONSTRAINT UQ_Economia_Paises_CodigoISO2
                UNIQUE (CodigoISO2),

            CONSTRAINT UQ_Economia_Paises_CodigoISO3
                UNIQUE (CodigoISO3),

            CONSTRAINT FK_Economia_Paises_Moneda
                FOREIGN KEY (MonedaID)
                REFERENCES dbo.Proveedor_Monedas(MonedaID)
        );
    END;

    /* ================================================================
       2. Proveedores / fuentes economicas
       No almacena secretos.
       Si requiere API, referencia arquitectura de conexiones existente.
       ================================================================ */

    IF OBJECT_ID('dbo.Economia_Proveedores', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Economia_Proveedores
        (
            ProveedorEconomicoID    int IDENTITY(1,1) NOT NULL,
            Codigo                  nvarchar(80) NOT NULL,
            Nombre                  nvarchar(200) NOT NULL,
            TipoProveedor           nvarchar(50) NOT NULL,
            PaisID                  int NULL,
            ServerConexionID        uniqueidentifier NULL,
            UrlPublica              nvarchar(500) NULL,
            DocumentacionURL        nvarchar(500) NULL,
            RequiereAutenticacion   bit NOT NULL
                CONSTRAINT DF_Economia_Proveedores_RequiereAuth DEFAULT (0),
            PermiteBackfill         bit NOT NULL
                CONSTRAINT DF_Economia_Proveedores_Backfill DEFAULT (1),
            Activo                  bit NOT NULL
                CONSTRAINT DF_Economia_Proveedores_Activo DEFAULT (1),
            FechaCreacionUTC        datetime2(3) NOT NULL
                CONSTRAINT DF_Economia_Proveedores_FechaCreacionUTC DEFAULT (SYSUTCDATETIME()),
            FechaModificacionUTC    datetime2(3) NULL,

            CONSTRAINT PK_Economia_Proveedores
                PRIMARY KEY CLUSTERED (ProveedorEconomicoID),

            CONSTRAINT UQ_Economia_Proveedores_Codigo
                UNIQUE (Codigo),

            CONSTRAINT FK_Economia_Proveedores_Pais
                FOREIGN KEY (PaisID)
                REFERENCES dbo.Economia_Paises(PaisID),

            CONSTRAINT FK_Economia_Proveedores_ServerConexion
                FOREIGN KEY (ServerConexionID)
                REFERENCES dbo.Servidores_Conexiones(id)
        );
    END;

    /* ================================================================
       3. Categorias de indicadores
       ================================================================ */

    IF OBJECT_ID('dbo.Economia_CategoriasIndicador', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Economia_CategoriasIndicador
        (
            CategoriaIndicadorID    int IDENTITY(1,1) NOT NULL,
            Codigo                  nvarchar(80) NOT NULL,
            Nombre                  nvarchar(150) NOT NULL,
            Descripcion             nvarchar(500) NULL,
            CategoriaPadreID        int NULL,
            OrdenVisual             int NULL,
            Activo                  bit NOT NULL
                CONSTRAINT DF_Economia_Categorias_Activo DEFAULT (1),
            FechaCreacionUTC        datetime2(3) NOT NULL
                CONSTRAINT DF_Economia_Categorias_FechaCreacionUTC DEFAULT (SYSUTCDATETIME()),
            FechaModificacionUTC    datetime2(3) NULL,

            CONSTRAINT PK_Economia_CategoriasIndicador
                PRIMARY KEY CLUSTERED (CategoriaIndicadorID),

            CONSTRAINT UQ_Economia_CategoriasIndicador_Codigo
                UNIQUE (Codigo),

            CONSTRAINT FK_Economia_CategoriasIndicador_Padre
                FOREIGN KEY (CategoriaPadreID)
                REFERENCES dbo.Economia_CategoriasIndicador(CategoriaIndicadorID)
        );
    END;

    /* ================================================================
       4. Series economicas
       Un registro describe una serie.
       INPC, CPI, PIB, desempleo, FX, energia, etc. son DATOS.
       ================================================================ */

    IF OBJECT_ID('dbo.Economia_Series', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Economia_Series
        (
            SerieEconomicaID        bigint IDENTITY(1,1) NOT NULL,
            CodigoCanonico          nvarchar(150) NOT NULL,
            CodigoProveedor         nvarchar(200) NULL,
            Nombre                  nvarchar(250) NOT NULL,
            Descripcion             nvarchar(1000) NULL,
            CategoriaIndicadorID    int NOT NULL,
            ProveedorEconomicoID    int NOT NULL,
            PaisID                  int NULL,
            MonedaID                smallint NULL,

            FrecuenciaCodigo        nvarchar(30) NOT NULL,
            UnidadMedidaCodigo      nvarchar(80) NULL,
            TipoValorCodigo         nvarchar(50) NOT NULL,
            Escala                  decimal(18,6) NULL,

            EsPorcentaje            bit NOT NULL
                CONSTRAINT DF_Economia_Series_EsPorcentaje DEFAULT (0),

            EsIndice                bit NOT NULL
                CONSTRAINT DF_Economia_Series_EsIndice DEFAULT (0),

            EsTipoCambio            bit NOT NULL
                CONSTRAINT DF_Economia_Series_EsTipoCambio DEFAULT (0),

            MonedaBaseID            smallint NULL,
            MonedaCotizadaID        smallint NULL,

            SeriePadreID            bigint NULL,
            FechaInicioDisponible   date NULL,
            FechaFinDisponible      date NULL,

            PermiteRevision         bit NOT NULL
                CONSTRAINT DF_Economia_Series_PermiteRevision DEFAULT (1),

            MetadataJSON            nvarchar(max) NULL,

            Activo                  bit NOT NULL
                CONSTRAINT DF_Economia_Series_Activo DEFAULT (1),

            FechaCreacionUTC        datetime2(3) NOT NULL
                CONSTRAINT DF_Economia_Series_FechaCreacionUTC DEFAULT (SYSUTCDATETIME()),

            FechaModificacionUTC    datetime2(3) NULL,

            CONSTRAINT PK_Economia_Series
                PRIMARY KEY CLUSTERED (SerieEconomicaID),

            CONSTRAINT UQ_Economia_Series_CodigoCanonico
                UNIQUE (CodigoCanonico),

            CONSTRAINT FK_Economia_Series_Categoria
                FOREIGN KEY (CategoriaIndicadorID)
                REFERENCES dbo.Economia_CategoriasIndicador(CategoriaIndicadorID),

            CONSTRAINT FK_Economia_Series_Proveedor
                FOREIGN KEY (ProveedorEconomicoID)
                REFERENCES dbo.Economia_Proveedores(ProveedorEconomicoID),

            CONSTRAINT FK_Economia_Series_Pais
                FOREIGN KEY (PaisID)
                REFERENCES dbo.Economia_Paises(PaisID),

            CONSTRAINT FK_Economia_Series_Moneda
                FOREIGN KEY (MonedaID)
                REFERENCES dbo.Proveedor_Monedas(MonedaID),

            CONSTRAINT FK_Economia_Series_MonedaBase
                FOREIGN KEY (MonedaBaseID)
                REFERENCES dbo.Proveedor_Monedas(MonedaID),

            CONSTRAINT FK_Economia_Series_MonedaCotizada
                FOREIGN KEY (MonedaCotizadaID)
                REFERENCES dbo.Proveedor_Monedas(MonedaID),

            CONSTRAINT FK_Economia_Series_Padre
                FOREIGN KEY (SeriePadreID)
                REFERENCES dbo.Economia_Series(SerieEconomicaID),

            CONSTRAINT CK_Economia_Series_MetadataJSON
                CHECK (MetadataJSON IS NULL OR ISJSON(MetadataJSON) = 1)
        );
    END;

    /* ================================================================
       5. Valores / observaciones versionadas
       No sobrescribir revisiones historicas.
       ================================================================ */

    IF OBJECT_ID('dbo.Economia_Valores', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Economia_Valores
        (
            ValorEconomicoID        bigint IDENTITY(1,1) NOT NULL,
            SerieEconomicaID        bigint NOT NULL,

            FechaPeriodo            date NOT NULL,
            PeriodoCodigo           nvarchar(30) NULL,

            Valor                   decimal(28,10) NOT NULL,

            VersionDato             int NOT NULL
                CONSTRAINT DF_Economia_Valores_VersionDato DEFAULT (1),

            EsRevision              bit NOT NULL
                CONSTRAINT DF_Economia_Valores_EsRevision DEFAULT (0),

            EsDatoPreliminar        bit NOT NULL
                CONSTRAINT DF_Economia_Valores_Preliminar DEFAULT (0),

            EsDatoEstimado          bit NOT NULL
                CONSTRAINT DF_Economia_Valores_Estimado DEFAULT (0),

            FechaPublicacion        datetime2(3) NULL,
            FechaVigenciaDesde      datetime2(3) NULL,
            FechaVigenciaHasta      datetime2(3) NULL,

            ValorAnterior           decimal(28,10) NULL,

            FuenteDatoID            nvarchar(250) NULL,
            HashFuente              nvarchar(128) NULL,
            MetadataJSON            nvarchar(max) NULL,

            FechaIngestaUTC         datetime2(3) NOT NULL
                CONSTRAINT DF_Economia_Valores_FechaIngestaUTC DEFAULT (SYSUTCDATETIME()),

            SyncRunID               uniqueidentifier NULL,

            Activo                  bit NOT NULL
                CONSTRAINT DF_Economia_Valores_Activo DEFAULT (1),

            CONSTRAINT PK_Economia_Valores
                PRIMARY KEY CLUSTERED (ValorEconomicoID),

            CONSTRAINT FK_Economia_Valores_Serie
                FOREIGN KEY (SerieEconomicaID)
                REFERENCES dbo.Economia_Series(SerieEconomicaID),

            CONSTRAINT UQ_Economia_Valores_SeriePeriodoVersion
                UNIQUE
                (
                    SerieEconomicaID,
                    FechaPeriodo,
                    VersionDato
                ),

            CONSTRAINT CK_Economia_Valores_Version
                CHECK (VersionDato >= 1),

            CONSTRAINT CK_Economia_Valores_MetadataJSON
                CHECK (MetadataJSON IS NULL OR ISJSON(MetadataJSON) = 1)
        );
    END;

    /* ================================================================
       6. Contexto economico por empresa/unidad.
       No duplicar Empresa ni Unidad.
       ================================================================ */

    IF OBJECT_ID('dbo.Economia_ContextoOperativo', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Economia_ContextoOperativo
        (
            ContextoEconomicoID     bigint IDENTITY(1,1) NOT NULL,

            EmpresaID               int NULL,
            UnidadNegocioID         uniqueidentifier NULL,

            PaisID                  int NOT NULL,
            MonedaID                smallint NULL,

            VigenciaDesde           date NOT NULL,
            VigenciaHasta           date NULL,

            EsPrincipal             bit NOT NULL
                CONSTRAINT DF_Economia_ContextoOperativo_Principal DEFAULT (1),

            Activo                  bit NOT NULL
                CONSTRAINT DF_Economia_ContextoOperativo_Activo DEFAULT (1),

            FechaCreacionUTC        datetime2(3) NOT NULL
                CONSTRAINT DF_Economia_ContextoOperativo_FechaCreacionUTC DEFAULT (SYSUTCDATETIME()),

            FechaModificacionUTC    datetime2(3) NULL,

            CONSTRAINT PK_Economia_ContextoOperativo
                PRIMARY KEY CLUSTERED (ContextoEconomicoID),

            CONSTRAINT FK_Economia_ContextoOperativo_Pais
                FOREIGN KEY (PaisID)
                REFERENCES dbo.Economia_Paises(PaisID),

            CONSTRAINT FK_Economia_ContextoOperativo_Empresa
                FOREIGN KEY (EmpresaID)
                REFERENCES dbo.Sistema_Empresas(EmpresaID),

            CONSTRAINT FK_Economia_ContextoOperativo_Unidad
                FOREIGN KEY (UnidadNegocioID)
                REFERENCES dbo.Unidades_Negocio(id),

            CONSTRAINT FK_Economia_ContextoOperativo_Moneda
                FOREIGN KEY (MonedaID)
                REFERENCES dbo.Proveedor_Monedas(MonedaID),

            CONSTRAINT CK_Economia_ContextoOperativo_Entidad
                CHECK
                (
                    EmpresaID IS NOT NULL
                    OR UnidadNegocioID IS NOT NULL
                ),

            CONSTRAINT CK_Economia_ContextoOperativo_Vigencia
                CHECK
                (
                    VigenciaHasta IS NULL
                    OR VigenciaHasta >= VigenciaDesde
                )
        );
    END;

    /* ================================================================
       Indices
       ================================================================ */

    IF NOT EXISTS
    (
        SELECT 1
        FROM sys.indexes
        WHERE object_id = OBJECT_ID('dbo.Economia_Valores')
          AND name = 'IX_Economia_Valores_Serie_Fecha'
    )
    BEGIN
        CREATE INDEX IX_Economia_Valores_Serie_Fecha
            ON dbo.Economia_Valores
            (
                SerieEconomicaID,
                FechaPeriodo DESC
            )
            INCLUDE
            (
                Valor,
                VersionDato,
                EsRevision,
                EsDatoPreliminar,
                FechaPublicacion,
                FechaIngestaUTC
            );
    END;

    IF NOT EXISTS
    (
        SELECT 1
        FROM sys.indexes
        WHERE object_id = OBJECT_ID('dbo.Economia_Series')
          AND name = 'IX_Economia_Series_Pais_Categoria'
    )
    BEGIN
        CREATE INDEX IX_Economia_Series_Pais_Categoria
            ON dbo.Economia_Series
            (
                PaisID,
                CategoriaIndicadorID,
                Activo
            );
    END;

    IF NOT EXISTS
    (
        SELECT 1
        FROM sys.indexes
        WHERE object_id = OBJECT_ID('dbo.Economia_ContextoOperativo')
          AND name = 'IX_Economia_ContextoOperativo_Entidad'
    )
    BEGIN
        CREATE INDEX IX_Economia_ContextoOperativo_Entidad
            ON dbo.Economia_ContextoOperativo
            (
                EmpresaID,
                UnidadNegocioID,
                VigenciaDesde,
                Activo
            );
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
