-- Migración: Bitácora de seguridad (bloqueos/desbloqueos de cuentas)
-- Fecha: 2026-08-19
IF OBJECT_ID('dbo.Sistema_Seguridad_Bitacora','U') IS NULL
BEGIN
  CREATE TABLE dbo.Sistema_Seguridad_Bitacora (
    BitacoraID BIGINT IDENTITY(1,1) PRIMARY KEY,
    UsuarioID INT NULL,
    Email NVARCHAR(200) NULL,
    Evento VARCHAR(20) NOT NULL,           -- BLOQUEO | DESBLOQUEO
    Motivo NVARCHAR(300) NULL,
    IntentosFallidos INT NULL,
    RealizadoPor NVARCHAR(200) NULL,        -- 'sistema' (auto) o email del admin
    FechaEvento DATETIME2 NOT NULL CONSTRAINT DF_SegBitacora_Fecha DEFAULT SYSUTCDATETIME()
  );
  CREATE INDEX IX_SegBitacora_Fecha ON dbo.Sistema_Seguridad_Bitacora (FechaEvento DESC);
  CREATE INDEX IX_SegBitacora_Usuario ON dbo.Sistema_Seguridad_Bitacora (UsuarioID);
END
