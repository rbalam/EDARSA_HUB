"""
Migracion idempotente: tabla de staging para Ingesta de Competencia.
dbo.Comercial_Ingesta_Competencia

Guarda el archivo archivado (object storage), su metadata, las filas extraidas
(JSON) pendientes de validacion humana, la(s) unidad(es) relacionadas y la
auditoria de confirmacion/rechazo.

Uso: python migrations/comercial_ingesta_competencia_20260611.py
"""
import os
import pymssql

DDL = """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Comercial_Ingesta_Competencia')
BEGIN
    CREATE TABLE dbo.Comercial_Ingesta_Competencia (
        IngestaID UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_CIC_Id DEFAULT NEWID(),
        EmpresaID INT NOT NULL,
        UnidadesNegocioIDs NVARCHAR(200) NULL,
        Origen VARCHAR(20) NOT NULL,
        MetodoExtraccion VARCHAR(20) NOT NULL,
        ModeloIA VARCHAR(50) NULL,
        ArchivoPath NVARCHAR(400) NULL,
        ArchivoNombre NVARCHAR(255) NULL,
        ArchivoContentType NVARCHAR(120) NULL,
        ArchivoTamano INT NULL,
        FuenteUrl NVARCHAR(1000) NULL,
        FilasExtraidas NVARCHAR(MAX) NULL,
        TotalFilas INT NOT NULL CONSTRAINT DF_CIC_Total DEFAULT 0,
        Estado VARCHAR(20) NOT NULL CONSTRAINT DF_CIC_Estado DEFAULT 'PENDIENTE',
        Mensaje NVARCHAR(1000) NULL,
        CompetidoresCreados INT NULL,
        ItemsCreados INT NULL,
        UsuarioCreacion NVARCHAR(150) NULL,
        FechaCreacion DATETIME2 NOT NULL CONSTRAINT DF_CIC_Fecha DEFAULT SYSDATETIME(),
        UsuarioResolucion NVARCHAR(150) NULL,
        FechaResolucion DATETIME2 NULL,
        CONSTRAINT PK_Comercial_Ingesta_Competencia PRIMARY KEY (IngestaID)
    );
    CREATE INDEX IX_CIC_Empresa_Estado ON dbo.Comercial_Ingesta_Competencia (EmpresaID, Estado);
END
"""


def main():
    conn = pymssql.connect(
        server=os.getenv('EDARSAHUB_SQL_HOST'), port=int(os.getenv('EDARSAHUB_SQL_PORT', '1433')),
        database=os.getenv('EDARSAHUB_SQL_DATABASE', 'EDARSAHUB'),
        user=os.getenv('EDARSAHUB_SQL_USER'), password=os.getenv('EDARSAHUB_SQL_PASSWORD'),
        autocommit=True,
    )
    try:
        cur = conn.cursor()
        cur.execute(DDL)
        cur.execute("SELECT COUNT(*) FROM dbo.Comercial_Ingesta_Competencia")
        print("OK. Comercial_Ingesta_Competencia lista. Filas:", cur.fetchone()[0])
    finally:
        conn.close()


if __name__ == "__main__":
    main()
