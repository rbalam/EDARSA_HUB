#!/usr/bin/env python3
"""
H5 - Persistencia canónica de homologación para Integrations Center.

Crea (idempotente) en EDARSAHUB:
- dbo.Sistema_IntegracionHomologacionPerfil
- dbo.Sistema_IntegracionHomologacionDominio
- dbo.Sistema_IntegracionHomologacionBinding

Principios:
- Un perfil representa un contrato reutilizable, no una instancia física.
- Una conexión puede reutilizar un perfil certificado sólo por fingerprint exacto.
- La certificación es por dominio y versionada.
- Ningún secreto, host, empresa, unidad o sucursal participa en el fingerprint.
- Esta migración NO activa conexiones ni modifica Servidores_Conexiones.
- No toca Producción por sí sola; debe ejecutarse únicamente por el circuito de migraciones autorizado.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path("/app/backend")
sys.path.insert(0, str(BACKEND_DIR))

from core.sql_first.db import get_sql_connection


DDL = r"""
SET NOCOUNT ON;

IF OBJECT_ID('dbo.Sistema_IntegracionHomologacionPerfil', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_IntegracionHomologacionPerfil (
        HomologacionPerfilID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        CodigoPerfil NVARCHAR(160) NOT NULL,
        SystemType NVARCHAR(100) NOT NULL,
        TransportType NVARCHAR(50) NOT NULL,
        SourceContractVersion NVARCHAR(100) NULL,
        EdarsahubContractVersion NVARCHAR(100) NULL,
        SchemaFingerprint CHAR(64) NOT NULL,
        Estado NVARCHAR(40) NOT NULL DEFAULT 'NOT_ASSESSED',
        CertifiedAtUTC DATETIME2(0) NULL,
        CertifiedByUsuarioID UNIQUEIDENTIFIER NULL,
        LastValidatedAtUTC DATETIME2(0) NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaCreacionUTC DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaActualizacionUTC DATETIME2(0) NULL,

        CONSTRAINT UQ_IntegracionHomologacionPerfil_Codigo UNIQUE (CodigoPerfil),
        CONSTRAINT CK_IntegracionHomologacionPerfil_Estado CHECK (
            Estado IN (
                'NOT_ASSESSED',
                'PENDING',
                'IN_PROGRESS',
                'PARTIAL',
                'CERTIFIED',
                'REVALIDATION_REQUIRED',
                'BLOCKED',
                'NOT_APPLICABLE'
            )
        )
    );

    CREATE INDEX IX_IntegracionHomologacionPerfil_Contract
        ON dbo.Sistema_IntegracionHomologacionPerfil(
            SystemType,
            TransportType,
            SchemaFingerprint,
            Estado
        )
        INCLUDE (
            SourceContractVersion,
            EdarsahubContractVersion,
            LastValidatedAtUTC,
            Activo
        );
END;

IF OBJECT_ID('dbo.Sistema_IntegracionHomologacionDominio', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_IntegracionHomologacionDominio (
        HomologacionDominioID BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        HomologacionPerfilID UNIQUEIDENTIFIER NOT NULL,
        DominioCodigo NVARCHAR(100) NOT NULL,
        Estado NVARCHAR(40) NOT NULL DEFAULT 'NOT_ASSESSED',
        SourceContractVersion NVARCHAR(100) NULL,
        EdarsahubContractVersion NVARCHAR(100) NULL,
        MappingVersion NVARCHAR(100) NULL,
        CertifiedAtUTC DATETIME2(0) NULL,
        CertifiedByUsuarioID UNIQUEIDENTIFIER NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaCreacionUTC DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaActualizacionUTC DATETIME2(0) NULL,

        CONSTRAINT FK_IntegracionHomologacionDominio_Perfil
            FOREIGN KEY (HomologacionPerfilID)
            REFERENCES dbo.Sistema_IntegracionHomologacionPerfil(HomologacionPerfilID),

        CONSTRAINT UQ_IntegracionHomologacionDominio
            UNIQUE (HomologacionPerfilID, DominioCodigo),

        CONSTRAINT CK_IntegracionHomologacionDominio_Estado CHECK (
            Estado IN (
                'NOT_ASSESSED',
                'PENDING',
                'IN_PROGRESS',
                'PARTIAL',
                'CERTIFIED',
                'REVALIDATION_REQUIRED',
                'BLOCKED',
                'NOT_APPLICABLE'
            )
        )
    );

    CREATE INDEX IX_IntegracionHomologacionDominio_PerfilEstado
        ON dbo.Sistema_IntegracionHomologacionDominio(
            HomologacionPerfilID,
            Estado,
            DominioCodigo
        )
        INCLUDE (Activo);
END;

IF OBJECT_ID('dbo.Sistema_IntegracionHomologacionBinding', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_IntegracionHomologacionBinding (
        HomologacionBindingID BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        ConnectionID UNIQUEIDENTIFIER NOT NULL,
        HomologacionPerfilID UNIQUEIDENTIFIER NOT NULL,
        CertificationSource NVARCHAR(20) NOT NULL,
        ObservedSchemaFingerprint CHAR(64) NOT NULL,
        Estado NVARCHAR(40) NOT NULL,
        BoundAtUTC DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        BoundByUsuarioID UNIQUEIDENTIFIER NULL,
        LastValidatedAtUTC DATETIME2(0) NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaCreacionUTC DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaActualizacionUTC DATETIME2(0) NULL,

        CONSTRAINT FK_IntegracionHomologacionBinding_Conexion
            FOREIGN KEY (ConnectionID)
            REFERENCES dbo.Servidores_Conexiones(id),

        CONSTRAINT FK_IntegracionHomologacionBinding_Perfil
            FOREIGN KEY (HomologacionPerfilID)
            REFERENCES dbo.Sistema_IntegracionHomologacionPerfil(HomologacionPerfilID),

        CONSTRAINT CK_IntegracionHomologacionBinding_Source CHECK (
            CertificationSource IN ('DIRECT', 'REUSED')
        ),

        CONSTRAINT CK_IntegracionHomologacionBinding_Estado CHECK (
            Estado IN (
                'PENDING',
                'IN_PROGRESS',
                'PARTIAL',
                'CERTIFIED',
                'REVALIDATION_REQUIRED',
                'BLOCKED',
                'NOT_APPLICABLE'
            )
        )
    );

    CREATE UNIQUE INDEX UX_IntegracionHomologacionBinding_Connection_Activo
        ON dbo.Sistema_IntegracionHomologacionBinding(ConnectionID)
        WHERE Activo = 1;

    CREATE INDEX IX_IntegracionHomologacionBinding_Perfil
        ON dbo.Sistema_IntegracionHomologacionBinding(
            HomologacionPerfilID,
            Estado,
            Activo
        )
        INCLUDE (
            ConnectionID,
            CertificationSource,
            LastValidatedAtUTC
        );
END;
"""


VERIFY = r"""
SELECT
    OBJECT_ID('dbo.Sistema_IntegracionHomologacionPerfil','U') AS perfil,
    OBJECT_ID('dbo.Sistema_IntegracionHomologacionDominio','U') AS dominio,
    OBJECT_ID('dbo.Sistema_IntegracionHomologacionBinding','U') AS binding
"""


def main() -> None:
    conn = get_sql_connection()
    try:
        cur = conn.cursor()
        cur.execute(DDL)
        conn.commit()

        verify = conn.cursor()
        verify.execute(VERIFY)
        row = verify.fetchone()
        if not row or not all(row):
            raise SystemExit("ERROR: no se crearon todas las tablas de homologacion")

        print("OK: persistencia canónica de homologación lista (idempotente).")
        print("PRODUCTION_TOUCHED=NO")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
