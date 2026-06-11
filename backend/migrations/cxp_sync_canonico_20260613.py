"""
Migración: Tabla canónica de Cuentas por Pagar (NO-LIVE)
========================================================
`dbo.Finanzas_CxP_Sync` es el TARGET canónico (denormalizado) que alimenta el job
`core/scheduler/jobs/cxp_sync_job.py` desde las fuentes operativas (SoftRestaurant + MPRO).
La pantalla de Cuentas por Pagar leerá EXCLUSIVAMENTE de esta tabla (NO-LIVE, sin demo).

Idempotente. NO MongoDB. 100% SQL Server (EDARSAHUB).
"""
import os
import sys
import pymssql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
except Exception:
    pass


def _conn():
    return pymssql.connect(
        server=os.getenv('EDARSAHUB_SQL_HOST'), port=int(os.getenv('EDARSAHUB_SQL_PORT', '1433')),
        database=os.getenv('EDARSAHUB_SQL_DATABASE'), user=os.getenv('EDARSAHUB_SQL_USER'),
        password=os.getenv('EDARSAHUB_SQL_PASSWORD'), timeout=120, login_timeout=30,
    )


DDL = """
IF OBJECT_ID('dbo.Finanzas_CxP_Sync','U') IS NULL
CREATE TABLE dbo.Finanzas_CxP_Sync (
    CxpSyncID            BIGINT IDENTITY(1,1) PRIMARY KEY,
    Fuente               NVARCHAR(20)  NOT NULL,   -- SOFTRESTAURANT | MANAGEMENTPRO
    UnidadNegocio        NVARCHAR(100) NULL,        -- código canónico (CIENFUEGOS, ESTELAR, 130MID, ORIGEN, 130QRO)
    UnidadNegocioNombre  NVARCHAR(150) NULL,
    SucursalCodigoOrigen NVARCHAR(40)  NULL,        -- server_key SR o Sc_Cve_Sucursal MPRO
    ProveedorID          NVARCHAR(60)  NULL,
    ProveedorNombre      NVARCHAR(250) NULL,
    ProveedorRFC         NVARCHAR(30)  NULL,
    TipoProveedor        NVARCHAR(2)   NULL,        -- A | B | X
    TipoProveedorNombre  NVARCHAR(40)  NULL,
    FolioEntrada         NVARCHAR(60)  NULL,
    FolioFactura         NVARCHAR(60)  NULL,
    Referencia           NVARCHAR(300) NULL,
    FechaEntrada         DATE          NULL,
    FechaVencimiento     DATE          NULL,
    DiasVencido          INT           NULL,
    MontoOriginal        DECIMAL(18,2) NULL,
    MontoPagado          DECIMAL(18,2) NULL,
    Saldo                DECIMAL(18,2) NULL,
    HashOrigen           NVARCHAR(64)  NULL,
    EsDemo               BIT           NOT NULL DEFAULT 0,
    Activo               BIT           NOT NULL DEFAULT 1,
    FechaSync            DATETIME      NOT NULL DEFAULT GETDATE()
);
"""

INDEXES = [
    "IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_CxPSync_Unidad' AND object_id=OBJECT_ID('dbo.Finanzas_CxP_Sync')) "
    "CREATE INDEX IX_CxPSync_Unidad ON dbo.Finanzas_CxP_Sync(UnidadNegocio, TipoProveedor) INCLUDE (Saldo);",
    "IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_CxPSync_Fuente' AND object_id=OBJECT_ID('dbo.Finanzas_CxP_Sync')) "
    "CREATE INDEX IX_CxPSync_Fuente ON dbo.Finanzas_CxP_Sync(Fuente);",
]


def run():
    conn = _conn(); cur = conn.cursor()
    try:
        cur.execute(DDL); conn.commit()
        for sql in INDEXES:
            cur.execute(sql); conn.commit()
        print("[OK] Finanzas_CxP_Sync creada/verificada + índices.")
    finally:
        cur.close(); conn.close()


if __name__ == "__main__":
    run()
