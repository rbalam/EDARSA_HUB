/* EDARSAHUB - Catalogo Ampliado / Gobierno Corporativo - Gate 2 DDL. NO EJECUTAR DESDE ESTE GATE. */
SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRY
 BEGIN TRANSACTION;
 IF OBJECT_ID('dbo.Sistema_Empresas','U') IS NULL THROW 51000,'Falta dbo.Sistema_Empresas canonica.',1;
 IF OBJECT_ID('dbo.Usuario_Catalogo','U') IS NULL THROW 51000,'Falta dbo.Usuario_Catalogo canonica.',1;
 IF OBJECT_ID('dbo.Cliente_Catalogo','U') IS NULL THROW 51000,'Falta dbo.Cliente_Catalogo canonica.',1;
 IF OBJECT_ID('dbo.Proveedor_Catalogo','U') IS NULL THROW 51000,'Falta dbo.Proveedor_Catalogo canonica.',1;
 IF OBJECT_ID('dbo.Cliente_Contactos','U') IS NULL THROW 51000,'Falta dbo.Cliente_Contactos canonica.',1;
 IF OBJECT_ID('dbo.Proveedor_Contactos','U') IS NULL THROW 51000,'Falta dbo.Proveedor_Contactos canonica.',1;

 IF OBJECT_ID('dbo.Gobierno_EmpresaConfiguracion','U') IS NULL BEGIN
  CREATE TABLE dbo.Gobierno_EmpresaConfiguracion(EmpresaID INT NOT NULL CONSTRAINT PK_Gobierno_EmpresaConfiguracion PRIMARY KEY,CatalogoLegalAmpliadoActivo BIT NOT NULL CONSTRAINT DF_GobEmpCfg_Activo DEFAULT(0),DiasAlertaDefault INT NULL,Activo BIT NOT NULL CONSTRAINT DF_GobEmpCfg_RegActivo DEFAULT(1),FechaAlta DATETIME2(0) NOT NULL CONSTRAINT DF_GobEmpCfg_Alta DEFAULT(SYSUTCDATETIME()),FechaActualizacion DATETIME2(0) NULL,UsuarioActualizacionID INT NULL,CONSTRAINT FK_GobEmpCfg_Empresa FOREIGN KEY(EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),CONSTRAINT FK_GobEmpCfg_Usuario FOREIGN KEY(UsuarioActualizacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),CONSTRAINT CK_GobEmpCfg_Dias CHECK(DiasAlertaDefault IS NULL OR DiasAlertaDefault BETWEEN 0 AND 3650));
 END;

 IF OBJECT_ID('dbo.Gobierno_Persona','U') IS NULL BEGIN
  CREATE TABLE dbo.Gobierno_Persona(PersonaID BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Gobierno_Persona PRIMARY KEY,PublicUUID UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_GobPersona_UUID DEFAULT(NEWSEQUENTIALID()),Nombre NVARCHAR(150) NOT NULL,ApellidoPaterno NVARCHAR(100) NULL,ApellidoMaterno NVARCHAR(100) NULL,RFC VARCHAR(13) NULL,CURP VARCHAR(18) NULL,FechaNacimiento DATE NULL,Nacionalidad NVARCHAR(80) NULL,Activo BIT NOT NULL CONSTRAINT DF_GobPersona_Activo DEFAULT(1),FechaAlta DATETIME2(0) NOT NULL CONSTRAINT DF_GobPersona_Alta DEFAULT(SYSUTCDATETIME()),FechaActualizacion DATETIME2(0) NULL,UsuarioActualizacionID INT NULL,CONSTRAINT UQ_GobPersona_UUID UNIQUE(PublicUUID),CONSTRAINT FK_GobPersona_UsuarioActualizacion FOREIGN KEY(UsuarioActualizacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID));
  CREATE UNIQUE INDEX UX_GobPersona_RFC ON dbo.Gobierno_Persona(RFC) WHERE RFC IS NOT NULL;
  CREATE UNIQUE INDEX UX_GobPersona_CURP ON dbo.Gobierno_Persona(CURP) WHERE CURP IS NOT NULL;
 END;

 IF OBJECT_ID('dbo.Gobierno_PersonaVinculo','U') IS NULL BEGIN
  CREATE TABLE dbo.Gobierno_PersonaVinculo(VinculoID BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Gobierno_PersonaVinculo PRIMARY KEY,PersonaID BIGINT NOT NULL,UsuarioID INT NULL,ClienteID INT NULL,ProveedorID INT NULL,ContactoClienteID INT NULL,ContactoProveedorID INT NULL,EsPrincipal BIT NOT NULL CONSTRAINT DF_GobPV_Principal DEFAULT(0),Activo BIT NOT NULL CONSTRAINT DF_GobPV_Activo DEFAULT(1),FechaAlta DATETIME2(0) NOT NULL CONSTRAINT DF_GobPV_Alta DEFAULT(SYSUTCDATETIME()),UsuarioAltaID INT NULL,CONSTRAINT FK_GobPV_Persona FOREIGN KEY(PersonaID) REFERENCES dbo.Gobierno_Persona(PersonaID),CONSTRAINT FK_GobPV_Usuario FOREIGN KEY(UsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),CONSTRAINT FK_GobPV_Cliente FOREIGN KEY(ClienteID) REFERENCES dbo.Cliente_Catalogo(ClienteID),CONSTRAINT FK_GobPV_Proveedor FOREIGN KEY(ProveedorID) REFERENCES dbo.Proveedor_Catalogo(ProveedorID),CONSTRAINT FK_GobPV_ContactoCliente FOREIGN KEY(ContactoClienteID) REFERENCES dbo.Cliente_Contactos(ContactoClienteID),CONSTRAINT FK_GobPV_ContactoProveedor FOREIGN KEY(ContactoProveedorID) REFERENCES dbo.Proveedor_Contactos(ContactoID),CONSTRAINT FK_GobPV_UsuarioAlta FOREIGN KEY(UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),CONSTRAINT CK_GobPV_UnDestino CHECK((CASE WHEN UsuarioID IS NULL THEN 0 ELSE 1 END)+(CASE WHEN ClienteID IS NULL THEN 0 ELSE 1 END)+(CASE WHEN ProveedorID IS NULL THEN 0 ELSE 1 END)+(CASE WHEN ContactoClienteID IS NULL THEN 0 ELSE 1 END)+(CASE WHEN ContactoProveedorID IS NULL THEN 0 ELSE 1 END)=1));
  CREATE UNIQUE INDEX UX_GobPV_Usuario ON dbo.Gobierno_PersonaVinculo(UsuarioID) WHERE UsuarioID IS NOT NULL;
  CREATE UNIQUE INDEX UX_GobPV_Cliente ON dbo.Gobierno_PersonaVinculo(ClienteID) WHERE ClienteID IS NOT NULL;
  CREATE UNIQUE INDEX UX_GobPV_Proveedor ON dbo.Gobierno_PersonaVinculo(ProveedorID) WHERE ProveedorID IS NOT NULL;
  CREATE UNIQUE INDEX UX_GobPV_ContactoCliente ON dbo.Gobierno_PersonaVinculo(ContactoClienteID) WHERE ContactoClienteID IS NOT NULL;
  CREATE UNIQUE INDEX UX_GobPV_ContactoProveedor ON dbo.Gobierno_PersonaVinculo(ContactoProveedorID) WHERE ContactoProveedorID IS NOT NULL;
 END;

 IF OBJECT_ID('dbo.Gobierno_RolCorporativoCatalogo','U') IS NULL BEGIN
  CREATE TABLE dbo.Gobierno_RolCorporativoCatalogo(RolCorporativoID INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Gobierno_RolCorporativoCatalogo PRIMARY KEY,Codigo VARCHAR(60) NOT NULL,Nombre NVARCHAR(120) NOT NULL,RequiereParticipacion BIT NOT NULL CONSTRAINT DF_GobRol_Part DEFAULT(0),RequiereFacultades BIT NOT NULL CONSTRAINT DF_GobRol_Fac DEFAULT(0),Activo BIT NOT NULL CONSTRAINT DF_GobRol_Activo DEFAULT(1),FechaAlta DATETIME2(0) NOT NULL CONSTRAINT DF_GobRol_Alta DEFAULT(SYSUTCDATETIME()),CONSTRAINT UQ_GobRol_Codigo UNIQUE(Codigo));
 END;

 IF OBJECT_ID('dbo.Gobierno_PersonaEmpresaRol','U') IS NULL BEGIN
  CREATE TABLE dbo.Gobierno_PersonaEmpresaRol(PersonaEmpresaRolID BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Gobierno_PersonaEmpresaRol PRIMARY KEY,PersonaID BIGINT NOT NULL,EmpresaID INT NOT NULL,RolCorporativoID INT NOT NULL,CargoDetalle NVARCHAR(200) NULL,ParticipacionPct DECIMAL(9,6) NULL,Facultades NVARCHAR(MAX) NULL,VigenteDesde DATE NULL,VigenteHasta DATE NULL,Activo BIT NOT NULL CONSTRAINT DF_GobPER_Activo DEFAULT(1),FechaAlta DATETIME2(0) NOT NULL CONSTRAINT DF_GobPER_Alta DEFAULT(SYSUTCDATETIME()),UsuarioAltaID INT NULL,CONSTRAINT FK_GobPER_Persona FOREIGN KEY(PersonaID) REFERENCES dbo.Gobierno_Persona(PersonaID),CONSTRAINT FK_GobPER_Empresa FOREIGN KEY(EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),CONSTRAINT FK_GobPER_Rol FOREIGN KEY(RolCorporativoID) REFERENCES dbo.Gobierno_RolCorporativoCatalogo(RolCorporativoID),CONSTRAINT FK_GobPER_UsuarioAlta FOREIGN KEY(UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),CONSTRAINT CK_GobPER_Pct CHECK(ParticipacionPct IS NULL OR ParticipacionPct BETWEEN 0 AND 100),CONSTRAINT CK_GobPER_Vigencia CHECK(VigenteHasta IS NULL OR VigenteDesde IS NULL OR VigenteHasta>=VigenteDesde));
  CREATE INDEX IX_GobPER_EmpresaRol ON dbo.Gobierno_PersonaEmpresaRol(EmpresaID,RolCorporativoID,Activo);
  CREATE INDEX IX_GobPER_Persona ON dbo.Gobierno_PersonaEmpresaRol(PersonaID,Activo);
 END;

 IF OBJECT_ID('dbo.Gobierno_TipoDocumento','U') IS NULL BEGIN
  CREATE TABLE dbo.Gobierno_TipoDocumento(TipoDocumentoID INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Gobierno_TipoDocumento PRIMARY KEY,Codigo VARCHAR(80) NOT NULL,Nombre NVARCHAR(160) NOT NULL,PropietarioPermitido VARCHAR(20) NOT NULL,RequiereVigencia BIT NOT NULL CONSTRAINT DF_GobTipoDoc_Vig DEFAULT(0),Sensibilidad VARCHAR(20) NOT NULL CONSTRAINT DF_GobTipoDoc_Sens DEFAULT('CONFIDENCIAL'),Activo BIT NOT NULL CONSTRAINT DF_GobTipoDoc_Activo DEFAULT(1),FechaAlta DATETIME2(0) NOT NULL CONSTRAINT DF_GobTipoDoc_Alta DEFAULT(SYSUTCDATETIME()),CONSTRAINT UQ_GobTipoDoc_Codigo UNIQUE(Codigo),CONSTRAINT CK_GobTipoDoc_Prop CHECK(PropietarioPermitido IN('PERSONA','EMPRESA','RELACION','CUALQUIERA')),CONSTRAINT CK_GobTipoDoc_Sens CHECK(Sensibilidad IN('INTERNO','CONFIDENCIAL','RESTRINGIDO')));
 END;

 IF OBJECT_ID('dbo.Gobierno_Documento','U') IS NULL BEGIN
  CREATE TABLE dbo.Gobierno_Documento(DocumentoID BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Gobierno_Documento PRIMARY KEY,PublicUUID UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_GobDoc_UUID DEFAULT(NEWSEQUENTIALID()),TipoDocumentoID INT NOT NULL,PropietarioTipo VARCHAR(20) NOT NULL,PersonaID BIGINT NULL,EmpresaID INT NULL,PersonaEmpresaRolID BIGINT NULL,Titulo NVARCHAR(250) NOT NULL,Estado VARCHAR(20) NOT NULL CONSTRAINT DF_GobDoc_Estado DEFAULT('VIGENTE'),Activo BIT NOT NULL CONSTRAINT DF_GobDoc_Activo DEFAULT(1),FechaAlta DATETIME2(0) NOT NULL CONSTRAINT DF_GobDoc_Alta DEFAULT(SYSUTCDATETIME()),UsuarioAltaID INT NULL,CONSTRAINT UQ_GobDoc_UUID UNIQUE(PublicUUID),CONSTRAINT FK_GobDoc_Tipo FOREIGN KEY(TipoDocumentoID) REFERENCES dbo.Gobierno_TipoDocumento(TipoDocumentoID),CONSTRAINT FK_GobDoc_Persona FOREIGN KEY(PersonaID) REFERENCES dbo.Gobierno_Persona(PersonaID),CONSTRAINT FK_GobDoc_Empresa FOREIGN KEY(EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),CONSTRAINT FK_GobDoc_Rel FOREIGN KEY(PersonaEmpresaRolID) REFERENCES dbo.Gobierno_PersonaEmpresaRol(PersonaEmpresaRolID),CONSTRAINT FK_GobDoc_UsuarioAlta FOREIGN KEY(UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),CONSTRAINT CK_GobDoc_Prop CHECK((PropietarioTipo='PERSONA' AND PersonaID IS NOT NULL AND EmpresaID IS NULL AND PersonaEmpresaRolID IS NULL) OR (PropietarioTipo='EMPRESA' AND EmpresaID IS NOT NULL AND PersonaID IS NULL AND PersonaEmpresaRolID IS NULL) OR (PropietarioTipo='RELACION' AND PersonaEmpresaRolID IS NOT NULL AND PersonaID IS NULL AND EmpresaID IS NULL)),CONSTRAINT CK_GobDoc_Estado CHECK(Estado IN('VIGENTE','POR_REVISAR','SUSTITUIDO','VENCIDO','INACTIVO')));
  CREATE INDEX IX_GobDoc_Empresa ON dbo.Gobierno_Documento(EmpresaID,Activo);
  CREATE INDEX IX_GobDoc_Persona ON dbo.Gobierno_Documento(PersonaID,Activo);
 END;

 IF OBJECT_ID('dbo.Gobierno_DocumentoVersion','U') IS NULL BEGIN
  CREATE TABLE dbo.Gobierno_DocumentoVersion(DocumentoVersionID BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Gobierno_DocumentoVersion PRIMARY KEY,DocumentoID BIGINT NOT NULL,NumeroVersion INT NOT NULL,NombreArchivo NVARCHAR(260) NOT NULL,StorageKey NVARCHAR(900) NOT NULL,MimeType NVARCHAR(120) NULL,TamanioBytes BIGINT NULL,SHA256 CHAR(64) NOT NULL,FechaEmision DATE NULL,FechaVencimiento DATE NULL,FechaVencimientoFuente VARCHAR(20) NULL,OCRTexto NVARCHAR(MAX) NULL,OCRMetadataJSON NVARCHAR(MAX) NULL,OCRConfianza DECIMAL(6,5) NULL,EstadoRevision VARCHAR(20) NOT NULL CONSTRAINT DF_GobDocVer_Rev DEFAULT('PENDIENTE'),RevisadoPorUsuarioID INT NULL,FechaRevision DATETIME2(0) NULL,FechaAlta DATETIME2(0) NOT NULL CONSTRAINT DF_GobDocVer_Alta DEFAULT(SYSUTCDATETIME()),UsuarioAltaID INT NULL,CONSTRAINT FK_GobDocVer_Doc FOREIGN KEY(DocumentoID) REFERENCES dbo.Gobierno_Documento(DocumentoID),CONSTRAINT FK_GobDocVer_Revisor FOREIGN KEY(RevisadoPorUsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),CONSTRAINT FK_GobDocVer_UsuarioAlta FOREIGN KEY(UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),CONSTRAINT UQ_GobDocVer_Num UNIQUE(DocumentoID,NumeroVersion),CONSTRAINT UQ_GobDocVer_Hash UNIQUE(DocumentoID,SHA256),CONSTRAINT CK_GobDocVer_Num CHECK(NumeroVersion>=1),CONSTRAINT CK_GobDocVer_Revision CHECK(EstadoRevision IN('PENDIENTE','VALIDADO','RECHAZADO')),CONSTRAINT CK_GobDocVer_Fuente CHECK(FechaVencimientoFuente IS NULL OR FechaVencimientoFuente IN('CAPTURA','OCR','SISTEMA')),CONSTRAINT CK_GobDocVer_Fechas CHECK(FechaVencimiento IS NULL OR FechaEmision IS NULL OR FechaVencimiento>=FechaEmision),CONSTRAINT CK_GobDocVer_OCR CHECK(OCRConfianza IS NULL OR OCRConfianza BETWEEN 0 AND 1));
  CREATE INDEX IX_GobDocVer_Vencimiento ON dbo.Gobierno_DocumentoVersion(FechaVencimiento,DocumentoID);
 END;

 IF OBJECT_ID('dbo.Gobierno_DocumentoMovimiento','U') IS NULL BEGIN
  CREATE TABLE dbo.Gobierno_DocumentoMovimiento(MovimientoID BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Gobierno_DocumentoMovimiento PRIMARY KEY,DocumentoID BIGINT NOT NULL,DocumentoVersionID BIGINT NULL,TipoMovimiento VARCHAR(40) NOT NULL,DetalleJSON NVARCHAR(MAX) NULL,FechaUTC DATETIME2(0) NOT NULL CONSTRAINT DF_GobMov_Fecha DEFAULT(SYSUTCDATETIME()),UsuarioID INT NULL,CONSTRAINT FK_GobMov_Doc FOREIGN KEY(DocumentoID) REFERENCES dbo.Gobierno_Documento(DocumentoID),CONSTRAINT FK_GobMov_Ver FOREIGN KEY(DocumentoVersionID) REFERENCES dbo.Gobierno_DocumentoVersion(DocumentoVersionID),CONSTRAINT FK_GobMov_Usuario FOREIGN KEY(UsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID));
  CREATE INDEX IX_GobMov_DocFecha ON dbo.Gobierno_DocumentoMovimiento(DocumentoID,FechaUTC);
 END;

 IF OBJECT_ID('dbo.Gobierno_AlertaRegla','U') IS NULL BEGIN
  CREATE TABLE dbo.Gobierno_AlertaRegla(AlertaReglaID BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Gobierno_AlertaRegla PRIMARY KEY,EmpresaID INT NULL,TipoDocumentoID INT NULL,UsuarioObjetivoID INT NULL,DiasAntes INT NOT NULL,Canal VARCHAR(20) NOT NULL,Activo BIT NOT NULL CONSTRAINT DF_GobAR_Activo DEFAULT(1),FechaAlta DATETIME2(0) NOT NULL CONSTRAINT DF_GobAR_Alta DEFAULT(SYSUTCDATETIME()),UsuarioAltaID INT NULL,CONSTRAINT FK_GobAR_Emp FOREIGN KEY(EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),CONSTRAINT FK_GobAR_Tipo FOREIGN KEY(TipoDocumentoID) REFERENCES dbo.Gobierno_TipoDocumento(TipoDocumentoID),CONSTRAINT FK_GobAR_UsuarioObjetivo FOREIGN KEY(UsuarioObjetivoID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),CONSTRAINT FK_GobAR_UsuarioAlta FOREIGN KEY(UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),CONSTRAINT CK_GobAR_Dias CHECK(DiasAntes BETWEEN 0 AND 3650),CONSTRAINT CK_GobAR_Canal CHECK(Canal IN('TAREA','EMAIL','WHATSAPP','APP')));
  CREATE INDEX IX_GobAR_EmpTipo ON dbo.Gobierno_AlertaRegla(EmpresaID,TipoDocumentoID,Activo);
 END;

 IF OBJECT_ID('dbo.Gobierno_AlertaEvento','U') IS NULL BEGIN
  CREATE TABLE dbo.Gobierno_AlertaEvento(AlertaEventoID BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Gobierno_AlertaEvento PRIMARY KEY,DocumentoVersionID BIGINT NOT NULL,AlertaReglaID BIGINT NOT NULL,FechaObjetivo DATE NOT NULL,FechaProgramada DATE NOT NULL,Estado VARCHAR(20) NOT NULL CONSTRAINT DF_GobAE_Estado DEFAULT('PENDIENTE'),TareaReferencia VARCHAR(50) NULL,NotificacionReferencia VARCHAR(50) NULL,FechaEjecucion DATETIME2(0) NULL,ErrorMensaje NVARCHAR(1000) NULL,CONSTRAINT FK_GobAE_Ver FOREIGN KEY(DocumentoVersionID) REFERENCES dbo.Gobierno_DocumentoVersion(DocumentoVersionID),CONSTRAINT FK_GobAE_Regla FOREIGN KEY(AlertaReglaID) REFERENCES dbo.Gobierno_AlertaRegla(AlertaReglaID),CONSTRAINT UQ_GobAE_Idem UNIQUE(DocumentoVersionID,AlertaReglaID,FechaObjetivo),CONSTRAINT CK_GobAE_Est CHECK(Estado IN('PENDIENTE','GENERADA','ENVIADA','ERROR','CANCELADA')));
  CREATE INDEX IX_GobAE_Programada ON dbo.Gobierno_AlertaEvento(FechaProgramada,Estado);
 END;

 COMMIT;
END TRY
BEGIN CATCH
 IF @@TRANCOUNT>0 ROLLBACK;
 DECLARE @m NVARCHAR(4000)=ERROR_MESSAGE(); THROW 51000,@m,1;
END CATCH;
