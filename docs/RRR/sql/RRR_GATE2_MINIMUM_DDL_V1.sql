/*
RRR GATE 2 - MINIMUM DDL V1 - DESIGN ONLY
NO EJECUTAR DESDE ESTE JOB. Production=false.
Los tipos de FK externas deben ser recertificados antes de ejecutar migracion.
*/

CREATE TABLE dbo.RRR_Reglas (
    ReglaID uniqueidentifier NOT NULL CONSTRAINT PK_RRR_Reglas PRIMARY KEY,
    Codigo varchar(100) NOT NULL,
    TipoRegla varchar(50) NOT NULL,
    Descripcion nvarchar(500) NULL,
    Activa bit NOT NULL,
    Prioridad int NOT NULL,
    FechaCreacion datetime2(3) NOT NULL,
    UsuarioCreacionID uniqueidentifier NULL,
    CONSTRAINT UQ_RRR_Reglas_Codigo UNIQUE (Codigo)
);

CREATE TABLE dbo.RRR_ReglasVersiones (
    ReglaVersionID uniqueidentifier NOT NULL CONSTRAINT PK_RRR_ReglasVersiones PRIMARY KEY,
    ReglaID uniqueidentifier NOT NULL,
    Version int NOT NULL,
    ConfigJson nvarchar(max) NOT NULL,
    ConfigHash varchar(64) NOT NULL,
    VigenteDesde datetime2(3) NOT NULL,
    VigenteHasta datetime2(3) NULL,
    Estado varchar(30) NOT NULL,
    FechaCreacion datetime2(3) NOT NULL,
    UsuarioCreacionID uniqueidentifier NULL,
    CONSTRAINT FK_RRR_ReglasVersiones_Regla FOREIGN KEY (ReglaID) REFERENCES dbo.RRR_Reglas(ReglaID),
    CONSTRAINT UQ_RRR_ReglasVersiones_ReglaVersion UNIQUE (ReglaID, Version)
);

CREATE TABLE dbo.RRR_Eventos (
    EventoID uniqueidentifier NOT NULL CONSTRAINT PK_RRR_Eventos PRIMARY KEY,
    ClienteID uniqueidentifier NOT NULL,
    EmpresaID uniqueidentifier NULL,
    UnidadID uniqueidentifier NULL,
    VentaID uniqueidentifier NULL,
    TipoEvento varchar(60) NOT NULL,
    SourceSystem varchar(60) NOT NULL,
    SourceKey varchar(200) NOT NULL,
    FechaOperacion date NOT NULL,
    OcurridoAtUtc datetime2(3) NOT NULL,
    PayloadHash varchar(64) NULL,
    EstadoValidacion varchar(30) NOT NULL,
    EstadoAntifraude varchar(30) NOT NULL,
    MotivoRechazo nvarchar(500) NULL,
    FechaCreacion datetime2(3) NOT NULL,
    CONSTRAINT UQ_RRR_Eventos_Source UNIQUE (SourceSystem, SourceKey),
    CONSTRAINT FK_RRR_Eventos_Cliente FOREIGN KEY (ClienteID) REFERENCES dbo.Cliente_Catalogo(ClienteID)
    /* FK VentaID/EmpresaID/UnidadID se agregan solo despues de recertificar tipos exactos */
);

CREATE TABLE dbo.RRR_Beneficios (
    BeneficioID uniqueidentifier NOT NULL CONSTRAINT PK_RRR_Beneficios PRIMARY KEY,
    Codigo varchar(100) NOT NULL,
    Nombre nvarchar(200) NOT NULL,
    TipoBeneficio varchar(50) NOT NULL,
    ConfigJson nvarchar(max) NOT NULL,
    VigenteDesde datetime2(3) NULL,
    VigenteHasta datetime2(3) NULL,
    Activo bit NOT NULL,
    ExternalDomain varchar(60) NULL,
    ExternalReference varchar(200) NULL,
    FechaCreacion datetime2(3) NOT NULL,
    UsuarioCreacionID uniqueidentifier NULL,
    CONSTRAINT UQ_RRR_Beneficios_Codigo UNIQUE (Codigo)
);

CREATE TABLE dbo.RRR_LedgerMovimientos (
    MovimientoID uniqueidentifier NOT NULL CONSTRAINT PK_RRR_LedgerMovimientos PRIMARY KEY,
    ClienteID uniqueidentifier NOT NULL,
    EventoID uniqueidentifier NULL,
    ReglaVersionID uniqueidentifier NULL,
    BeneficioID uniqueidentifier NULL,
    TipoMovimiento varchar(20) NOT NULL,
    Unidades decimal(19,4) NOT NULL,
    IdempotencyKey varchar(200) NOT NULL,
    ReversalMovimientoID uniqueidentifier NULL,
    VigenteDesde datetime2(3) NOT NULL,
    ExpiraAt datetime2(3) NULL,
    Estado varchar(30) NOT NULL,
    MetadatosJson nvarchar(max) NULL,
    FechaCreacion datetime2(3) NOT NULL,
    UsuarioCreacionID uniqueidentifier NULL,
    CONSTRAINT FK_RRR_Ledger_Cliente FOREIGN KEY (ClienteID) REFERENCES dbo.Cliente_Catalogo(ClienteID),
    CONSTRAINT FK_RRR_Ledger_Evento FOREIGN KEY (EventoID) REFERENCES dbo.RRR_Eventos(EventoID),
    CONSTRAINT FK_RRR_Ledger_ReglaVersion FOREIGN KEY (ReglaVersionID) REFERENCES dbo.RRR_ReglasVersiones(ReglaVersionID),
    CONSTRAINT FK_RRR_Ledger_Beneficio FOREIGN KEY (BeneficioID) REFERENCES dbo.RRR_Beneficios(BeneficioID),
    CONSTRAINT FK_RRR_Ledger_Reversal FOREIGN KEY (ReversalMovimientoID) REFERENCES dbo.RRR_LedgerMovimientos(MovimientoID),
    CONSTRAINT UQ_RRR_Ledger_Idempotency UNIQUE (IdempotencyKey),
    CONSTRAINT CK_RRR_Ledger_Tipo CHECK (TipoMovimiento IN ('EARN','REDEEM','REVERSAL','EXPIRE','ADJUST'))
);

CREATE TABLE dbo.RRR_ScoreHistorial (
    ScoreID uniqueidentifier NOT NULL CONSTRAINT PK_RRR_ScoreHistorial PRIMARY KEY,
    ClienteID uniqueidentifier NOT NULL,
    ModeloVersion varchar(50) NOT NULL,
    Score decimal(19,6) NOT NULL,
    ComponentesJson nvarchar(max) NOT NULL,
    CalculadoAtUtc datetime2(3) NOT NULL,
    FechaOperacionCorte date NULL,
    FechaCreacion datetime2(3) NOT NULL,
    CONSTRAINT FK_RRR_Score_Cliente FOREIGN KEY (ClienteID) REFERENCES dbo.Cliente_Catalogo(ClienteID)
);

CREATE TABLE dbo.RRR_RankingHistorial (
    RankingID uniqueidentifier NOT NULL CONSTRAINT PK_RRR_RankingHistorial PRIMARY KEY,
    ClienteID uniqueidentifier NOT NULL,
    ScoreID uniqueidentifier NULL,
    ModeloVersion varchar(50) NOT NULL,
    RankCode varchar(100) NOT NULL,
    CalculadoAtUtc datetime2(3) NOT NULL,
    VigenteDesde datetime2(3) NOT NULL,
    VigenteHasta datetime2(3) NULL,
    MotivoJson nvarchar(max) NULL,
    FechaCreacion datetime2(3) NOT NULL,
    CONSTRAINT FK_RRR_Ranking_Cliente FOREIGN KEY (ClienteID) REFERENCES dbo.Cliente_Catalogo(ClienteID),
    CONSTRAINT FK_RRR_Ranking_Score FOREIGN KEY (ScoreID) REFERENCES dbo.RRR_ScoreHistorial(ScoreID)
);

/* Vistas propuestas para ejecucion posterior:
CREATE VIEW dbo.vw_RRR_ClienteBalance AS ... SUM ledger ...;
CREATE VIEW dbo.vw_RRR_ClienteEstadoActual AS ... ultimo score + rank + balance ...;
*/
