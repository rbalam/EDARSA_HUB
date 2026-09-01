/* EDARSAHUB - Catalogo Ampliado V1 - nucleo canonico/atomico. Idempotente, aditivo, SQL-first. */
SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRY
 BEGIN TRANSACTION;
 IF OBJECT_ID('dbo.Sistema_Empresas','U') IS NULL THROW 51000,'Falta dbo.Sistema_Empresas canonica.',1;

 IF OBJECT_ID('dbo.Gobierno_EmpresaConfiguracion','U') IS NULL
 CREATE TABLE dbo.Gobierno_EmpresaConfiguracion(
  EmpresaID INT NOT NULL PRIMARY KEY,
  CatalogoLegalAmpliadoActivo BIT NOT NULL CONSTRAINT DF_GobEmpCfg_Activo DEFAULT(0),
  DiasAlertaDefault INT NULL,
  Activo BIT NOT NULL CONSTRAINT DF_GobEmpCfg_RegActivo DEFAULT(1),
  FechaAlta DATETIME2(0) NOT NULL CONSTRAINT DF_GobEmpCfg_Alta DEFAULT(SYSUTCDATETIME()),
  FechaActualizacion DATETIME2(0) NULL,
  UsuarioActualizacion NVARCHAR(320) NULL,
  CONSTRAINT FK_GobEmpCfg_Empresa FOREIGN KEY(EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
  CONSTRAINT CK_GobEmpCfg_Dias CHECK(DiasAlertaDefault IS NULL OR DiasAlertaDefault BETWEEN 0 AND 3650)
 );

 IF OBJECT_ID('dbo.Gobierno_Persona','U') IS NULL
 CREATE TABLE dbo.Gobierno_Persona(
  PersonaID BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  PublicUUID UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_GobPersona_UUID DEFAULT(NEWSEQUENTIALID()),
  Nombre NVARCHAR(150) NOT NULL, ApellidoPaterno NVARCHAR(100) NULL, ApellidoMaterno NVARCHAR(100) NULL,
  RFC VARCHAR(13) NULL, CURP VARCHAR(18) NULL, FechaNacimiento DATE NULL, Nacionalidad NVARCHAR(80) NULL,
  Activo BIT NOT NULL CONSTRAINT DF_GobPersona_Activo DEFAULT(1),
  FechaAlta DATETIME2(0) NOT NULL CONSTRAINT DF_GobPersona_Alta DEFAULT(SYSUTCDATETIME()),
  FechaActualizacion DATETIME2(0) NULL, UsuarioActualizacion NVARCHAR(320) NULL,
  CONSTRAINT UQ_GobPersona_UUID UNIQUE(PublicUUID)
 );
 CREATE UNIQUE INDEX UX_GobPersona_RFC ON dbo.Gobierno_Persona(RFC) WHERE RFC IS NOT NULL;
 CREATE UNIQUE INDEX UX_GobPersona_CURP ON dbo.Gobierno_Persona(CURP) WHERE CURP IS NOT NULL;

 IF OBJECT_ID('dbo.Gobierno_PersonaVinculo','U') IS NULL
 CREATE TABLE dbo.Gobierno_PersonaVinculo(
  VinculoID BIGINT IDENTITY(1,1) PRIMARY KEY, PersonaID BIGINT NOT NULL,
  TipoEntidad VARCHAR(40) NOT NULL, EntidadClave NVARCHAR(200) NOT NULL,
  EsPrincipal BIT NOT NULL CONSTRAINT DF_GobPV_Principal DEFAULT(0), Activo BIT NOT NULL CONSTRAINT DF_GobPV_Activo DEFAULT(1),
  FechaAlta DATETIME2(0) NOT NULL CONSTRAINT DF_GobPV_Alta DEFAULT(SYSUTCDATETIME()), UsuarioAlta NVARCHAR(320) NULL,
  CONSTRAINT FK_GobPV_Persona FOREIGN KEY(PersonaID) REFERENCES dbo.Gobierno_Persona(PersonaID),
  CONSTRAINT UQ_GobPV_Entidad UNIQUE(TipoEntidad,EntidadClave),
  CONSTRAINT CK_GobPV_Tipo CHECK(TipoEntidad IN('USUARIO','CLIENTE','PROVEEDOR','CONTACTO_PROVEEDOR','OTRO_CANONICO'))
 );

 IF OBJECT_ID('dbo.Gobierno_RolCorporativoCatalogo','U') IS NULL
 CREATE TABLE dbo.Gobierno_RolCorporativoCatalogo(
  RolCorporativoID INT IDENTITY(1,1) PRIMARY KEY, Codigo VARCHAR(60) NOT NULL UNIQUE, Nombre NVARCHAR(120) NOT NULL,
  RequiereParticipacion BIT NOT NULL DEFAULT(0), RequiereFacultades BIT NOT NULL DEFAULT(0), Activo BIT NOT NULL DEFAULT(1),
  FechaAlta DATETIME2(0) NOT NULL DEFAULT(SYSUTCDATETIME())
 );

 IF OBJECT_ID('dbo.Gobierno_PersonaEmpresaRol','U') IS NULL
 CREATE TABLE dbo.Gobierno_PersonaEmpresaRol(
  PersonaEmpresaRolID BIGINT IDENTITY(1,1) PRIMARY KEY, PersonaID BIGINT NOT NULL, EmpresaID INT NOT NULL, RolCorporativoID INT NOT NULL,
  CargoDetalle NVARCHAR(200) NULL, ParticipacionPct DECIMAL(9,6) NULL, Facultades NVARCHAR(MAX) NULL,
  VigenteDesde DATE NULL, VigenteHasta DATE NULL, Activo BIT NOT NULL DEFAULT(1),
  FechaAlta DATETIME2(0) NOT NULL DEFAULT(SYSUTCDATETIME()), UsuarioAlta NVARCHAR(320) NULL,
  CONSTRAINT FK_GobPER_Persona FOREIGN KEY(PersonaID) REFERENCES dbo.Gobierno_Persona(PersonaID),
  CONSTRAINT FK_GobPER_Empresa FOREIGN KEY(EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
  CONSTRAINT FK_GobPER_Rol FOREIGN KEY(RolCorporativoID) REFERENCES dbo.Gobierno_RolCorporativoCatalogo(RolCorporativoID),
  CONSTRAINT CK_GobPER_Pct CHECK(ParticipacionPct IS NULL OR ParticipacionPct BETWEEN 0 AND 100),
  CONSTRAINT CK_GobPER_Vigencia CHECK(VigenteHasta IS NULL OR VigenteDesde IS NULL OR VigenteHasta>=VigenteDesde)
 );

 IF OBJECT_ID('dbo.Gobierno_TipoDocumento','U') IS NULL
 CREATE TABLE dbo.Gobierno_TipoDocumento(
  TipoDocumentoID INT IDENTITY(1,1) PRIMARY KEY, Codigo VARCHAR(80) NOT NULL UNIQUE, Nombre NVARCHAR(160) NOT NULL,
  PropietarioPermitido VARCHAR(20) NOT NULL, RequiereVigencia BIT NOT NULL DEFAULT(0), Sensibilidad VARCHAR(20) NOT NULL DEFAULT('CONFIDENCIAL'),
  Activo BIT NOT NULL DEFAULT(1), FechaAlta DATETIME2(0) NOT NULL DEFAULT(SYSUTCDATETIME()),
  CONSTRAINT CK_GobTipoDoc_Prop CHECK(PropietarioPermitido IN('PERSONA','EMPRESA','RELACION','CUALQUIERA')),
  CONSTRAINT CK_GobTipoDoc_Sens CHECK(Sensibilidad IN('INTERNO','CONFIDENCIAL','RESTRINGIDO'))
 );

 IF OBJECT_ID('dbo.Gobierno_Documento','U') IS NULL
 CREATE TABLE dbo.Gobierno_Documento(
  DocumentoID BIGINT IDENTITY(1,1) PRIMARY KEY, PublicUUID UNIQUEIDENTIFIER NOT NULL DEFAULT(NEWSEQUENTIALID()), TipoDocumentoID INT NOT NULL,
  PropietarioTipo VARCHAR(20) NOT NULL, PersonaID BIGINT NULL, EmpresaID INT NULL, PersonaEmpresaRolID BIGINT NULL,
  Titulo NVARCHAR(250) NOT NULL, Estado VARCHAR(20) NOT NULL DEFAULT('VIGENTE'), Activo BIT NOT NULL DEFAULT(1),
  FechaAlta DATETIME2(0) NOT NULL DEFAULT(SYSUTCDATETIME()), UsuarioAlta NVARCHAR(320) NULL,
  CONSTRAINT UQ_GobDoc_UUID UNIQUE(PublicUUID), CONSTRAINT FK_GobDoc_Tipo FOREIGN KEY(TipoDocumentoID) REFERENCES dbo.Gobierno_TipoDocumento(TipoDocumentoID),
  CONSTRAINT FK_GobDoc_Persona FOREIGN KEY(PersonaID) REFERENCES dbo.Gobierno_Persona(PersonaID),
  CONSTRAINT FK_GobDoc_Empresa FOREIGN KEY(EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
  CONSTRAINT FK_GobDoc_Rel FOREIGN KEY(PersonaEmpresaRolID) REFERENCES dbo.Gobierno_PersonaEmpresaRol(PersonaEmpresaRolID),
  CONSTRAINT CK_GobDoc_Prop CHECK((PropietarioTipo='PERSONA' AND PersonaID IS NOT NULL AND EmpresaID IS NULL AND PersonaEmpresaRolID IS NULL) OR (PropietarioTipo='EMPRESA' AND EmpresaID IS NOT NULL AND PersonaID IS NULL AND PersonaEmpresaRolID IS NULL) OR (PropietarioTipo='RELACION' AND PersonaEmpresaRolID IS NOT NULL AND PersonaID IS NULL AND EmpresaID IS NULL)),
  CONSTRAINT CK_GobDoc_Estado CHECK(Estado IN('VIGENTE','POR_REVISAR','SUSTITUIDO','VENCIDO','INACTIVO'))
 );

 IF OBJECT_ID('dbo.Gobierno_DocumentoVersion','U') IS NULL
 CREATE TABLE dbo.Gobierno_DocumentoVersion(
  DocumentoVersionID BIGINT IDENTITY(1,1) PRIMARY KEY, DocumentoID BIGINT NOT NULL, NumeroVersion INT NOT NULL,
  NombreArchivo NVARCHAR(260) NOT NULL, StorageKey NVARCHAR(900) NOT NULL, MimeType NVARCHAR(120) NULL, TamanioBytes BIGINT NULL,
  SHA256 CHAR(64) NOT NULL, FechaEmision DATE NULL, FechaVencimiento DATE NULL, FechaVencimientoFuente VARCHAR(20) NULL,
  OCRTexto NVARCHAR(MAX) NULL, OCRMetadataJSON NVARCHAR(MAX) NULL, OCRConfianza DECIMAL(6,5) NULL,
  EstadoRevision VARCHAR(20) NOT NULL DEFAULT('PENDIENTE'), RevisadoPor NVARCHAR(320) NULL, FechaRevision DATETIME2(0) NULL,
  FechaAlta DATETIME2(0) NOT NULL DEFAULT(SYSUTCDATETIME()), UsuarioAlta NVARCHAR(320) NULL,
  CONSTRAINT FK_GobDocVer_Doc FOREIGN KEY(DocumentoID) REFERENCES dbo.Gobierno_Documento(DocumentoID),
  CONSTRAINT UQ_GobDocVer_Num UNIQUE(DocumentoID,NumeroVersion), CONSTRAINT UQ_GobDocVer_Hash UNIQUE(DocumentoID,SHA256),
  CONSTRAINT CK_GobDocVer_Revision CHECK(EstadoRevision IN('PENDIENTE','VALIDADO','RECHAZADO')),
  CONSTRAINT CK_GobDocVer_Fuente CHECK(FechaVencimientoFuente IS NULL OR FechaVencimientoFuente IN('CAPTURA','OCR','SISTEMA')),
  CONSTRAINT CK_GobDocVer_Fechas CHECK(FechaVencimiento IS NULL OR FechaEmision IS NULL OR FechaVencimiento>=FechaEmision)
 );

 IF OBJECT_ID('dbo.Gobierno_DocumentoMovimiento','U') IS NULL
 CREATE TABLE dbo.Gobierno_DocumentoMovimiento(
  MovimientoID BIGINT IDENTITY(1,1) PRIMARY KEY, DocumentoID BIGINT NOT NULL, DocumentoVersionID BIGINT NULL,
  TipoMovimiento VARCHAR(40) NOT NULL, DetalleJSON NVARCHAR(MAX) NULL, FechaUTC DATETIME2(0) NOT NULL DEFAULT(SYSUTCDATETIME()), Usuario NVARCHAR(320) NULL,
  CONSTRAINT FK_GobMov_Doc FOREIGN KEY(DocumentoID) REFERENCES dbo.Gobierno_Documento(DocumentoID),
  CONSTRAINT FK_GobMov_Ver FOREIGN KEY(DocumentoVersionID) REFERENCES dbo.Gobierno_DocumentoVersion(DocumentoVersionID)
 );

 IF OBJECT_ID('dbo.Gobierno_AlertaRegla','U') IS NULL
 CREATE TABLE dbo.Gobierno_AlertaRegla(
  AlertaReglaID BIGINT IDENTITY(1,1) PRIMARY KEY, EmpresaID INT NULL, TipoDocumentoID INT NULL, UsuarioObjetivo NVARCHAR(320) NULL,
  DiasAntes INT NOT NULL, Canal VARCHAR(20) NOT NULL, Activo BIT NOT NULL DEFAULT(1), FechaAlta DATETIME2(0) NOT NULL DEFAULT(SYSUTCDATETIME()), UsuarioAlta NVARCHAR(320) NULL,
  CONSTRAINT FK_GobAR_Emp FOREIGN KEY(EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID), CONSTRAINT FK_GobAR_Tipo FOREIGN KEY(TipoDocumentoID) REFERENCES dbo.Gobierno_TipoDocumento(TipoDocumentoID),
  CONSTRAINT CK_GobAR_Dias CHECK(DiasAntes BETWEEN 0 AND 3650), CONSTRAINT CK_GobAR_Canal CHECK(Canal IN('TAREA','EMAIL','WHATSAPP','APP'))
 );

 IF OBJECT_ID('dbo.Gobierno_AlertaEvento','U') IS NULL
 CREATE TABLE dbo.Gobierno_AlertaEvento(
  AlertaEventoID BIGINT IDENTITY(1,1) PRIMARY KEY, DocumentoVersionID BIGINT NOT NULL, AlertaReglaID BIGINT NOT NULL,
  FechaObjetivo DATE NOT NULL, FechaProgramada DATE NOT NULL, Estado VARCHAR(20) NOT NULL DEFAULT('PENDIENTE'),
  TareaReferencia NVARCHAR(100) NULL, NotificacionReferencia NVARCHAR(100) NULL, FechaEjecucion DATETIME2(0) NULL, ErrorMensaje NVARCHAR(1000) NULL,
  CONSTRAINT FK_GobAE_Ver FOREIGN KEY(DocumentoVersionID) REFERENCES dbo.Gobierno_DocumentoVersion(DocumentoVersionID), CONSTRAINT FK_GobAE_Regla FOREIGN KEY(AlertaReglaID) REFERENCES dbo.Gobierno_AlertaRegla(AlertaReglaID),
  CONSTRAINT UQ_GobAE_Idem UNIQUE(DocumentoVersionID,AlertaReglaID,FechaObjetivo), CONSTRAINT CK_GobAE_Est CHECK(Estado IN('PENDIENTE','GENERADA','ENVIADA','ERROR','CANCELADA'))
 );

 MERGE dbo.Gobierno_RolCorporativoCatalogo AS t USING (VALUES
 ('SOCIO',N'Socio',1,0),('ACCIONISTA',N'Accionista',1,0),('REPRESENTANTE_LEGAL',N'Representante legal',0,1),('APODERADO',N'Apoderado',0,1),('CONSEJERO',N'Consejero',0,0),('PRESIDENTE',N'Presidente',0,0),('SECRETARIO',N'Secretario',0,0),('TESORERO',N'Tesorero',0,0),('VOCAL',N'Vocal',0,0),('COMISARIO',N'Comisario',0,0),('FIRMANTE',N'Firmante',0,1)
 ) s(Codigo,Nombre,RequiereParticipacion,RequiereFacultades) ON t.Codigo=s.Codigo
 WHEN NOT MATCHED THEN INSERT(Codigo,Nombre,RequiereParticipacion,RequiereFacultades) VALUES(s.Codigo,s.Nombre,s.RequiereParticipacion,s.RequiereFacultades);

 COMMIT;
END TRY
BEGIN CATCH
 IF @@TRANCOUNT>0 ROLLBACK;
 DECLARE @m NVARCHAR(4000)=ERROR_MESSAGE(); THROW 51000,@m,1;
END CATCH;
