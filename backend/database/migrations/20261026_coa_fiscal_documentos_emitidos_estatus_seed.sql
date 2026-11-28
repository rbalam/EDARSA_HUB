/*
COA Gate 6D - DESIGN ONLY
Seed canonico de estados de CFDI emitidos.
NO ejecutar fuera del canal controlado.
*/
SET NOCOUNT ON;
SET XACT_ABORT ON;

IF OBJECT_ID('dbo.Fiscal_DocumentosEmitidosEstatus','U') IS NULL
    THROW 51000, 'COA_GATE6D_TARGET_TABLE_MISSING', 1;

DECLARE @Seed TABLE (
    EstatusDocumentoFiscalEmitidoID tinyint NOT NULL PRIMARY KEY,
    Codigo varchar(30) NOT NULL UNIQUE,
    Nombre nvarchar(200) NOT NULL,
    Descripcion nvarchar(1000) NULL,
    EsFinal bit NOT NULL,
    Activo bit NOT NULL
);

INSERT INTO @Seed
(EstatusDocumentoFiscalEmitidoID,Codigo,Nombre,Descripcion,EsFinal,Activo)
VALUES
(1,'BORRADOR',N'Borrador',N'Documento capturado o preparado, aun no enviado a timbrar.',0,1),
(2,'PENDIENTE_TIMBRADO',N'Pendiente de timbrado',N'Listo para enviarse al proveedor de timbrado o esperando respuesta.',0,1),
(3,'TIMBRADO',N'Timbrado',N'CFDI timbrado exitosamente; conserva su UUID y evidencia fiscal.',0,1),
(4,'ERROR_TIMBRADO',N'Error de timbrado',N'Intento de timbrado rechazado o fallido; permite correccion y reintento.',0,1),
(5,'CANCELACION_SOLICITADA',N'Cancelacion solicitada',N'Proceso de cancelacion iniciado y aun no confirmado como final.',0,1),
(6,'CANCELADO',N'Cancelado',N'CFDI con cancelacion confirmada.',1,1);

IF EXISTS (
    SELECT 1
    FROM @Seed s
    JOIN dbo.Fiscal_DocumentosEmitidosEstatus t
      ON t.EstatusDocumentoFiscalEmitidoID=s.EstatusDocumentoFiscalEmitidoID
    WHERE t.Codigo<>s.Codigo
       OR t.Nombre<>s.Nombre
       OR ISNULL(t.Descripcion,N'')<>ISNULL(s.Descripcion,N'')
       OR t.EsFinal<>s.EsFinal
       OR t.Activo<>s.Activo
)
    THROW 51001, 'COA_GATE6D_ID_COLLISION', 1;

IF EXISTS (
    SELECT 1
    FROM @Seed s
    JOIN dbo.Fiscal_DocumentosEmitidosEstatus t
      ON t.Codigo=s.Codigo
    WHERE t.EstatusDocumentoFiscalEmitidoID<>s.EstatusDocumentoFiscalEmitidoID
)
    THROW 51002, 'COA_GATE6D_CODE_COLLISION', 1;

INSERT INTO dbo.Fiscal_DocumentosEmitidosEstatus
(EstatusDocumentoFiscalEmitidoID,Codigo,Nombre,Descripcion,EsFinal,Activo)
SELECT s.EstatusDocumentoFiscalEmitidoID,s.Codigo,s.Nombre,s.Descripcion,s.EsFinal,s.Activo
FROM @Seed s
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.Fiscal_DocumentosEmitidosEstatus t
    WHERE t.EstatusDocumentoFiscalEmitidoID=s.EstatusDocumentoFiscalEmitidoID
);

IF (SELECT COUNT(*) FROM dbo.Fiscal_DocumentosEmitidosEstatus WHERE EstatusDocumentoFiscalEmitidoID BETWEEN 1 AND 6) < 6
    THROW 51003, 'COA_GATE6D_POSTCONDITION_FAILED', 1;
