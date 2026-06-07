"""
EDARSAHUB - Bitácora RBAC SQL-First (reemplaza sec_bitacora_admin de Mongo).

Crea (idempotente) dbo.Usuario_RBAC_Bitacora con UsuarioID INT (consistente con
Usuario_Catalogo.UsuarioID y Usuario_RBAC_Asignacion). NO toca Mongo, NO borra datos.
"""
import os
import sys
import pymssql
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

DDL = """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Usuario_RBAC_Bitacora')
BEGIN
    CREATE TABLE dbo.Usuario_RBAC_Bitacora (
        BitacoraID            INT IDENTITY(1,1) PRIMARY KEY,
        EventoUUID            NVARCHAR(40)  NOT NULL,
        FechaEvento           DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        UsuarioAfectadoID     INT           NULL,
        UsuarioAfectadoEmail  NVARCHAR(320) NULL,
        Tipo                  NVARCHAR(40)  NOT NULL,   -- ASIGNAR | REVOCAR
        Accion                NVARCHAR(60)  NULL,        -- ASIGNAR_PERFIL, RETIRAR_ROL, ...
        Resultado             NVARCHAR(20)  NOT NULL DEFAULT 'exitoso',  -- exitoso | fallido | parcial
        Descripcion           NVARCHAR(500) NULL,
        Detalles              NVARCHAR(MAX) NULL,        -- JSON
        IP                    NVARCHAR(60)  NULL,
        AdministradorID       INT           NULL,
        AdministradorEmail    NVARCHAR(320) NULL
    );
    CREATE INDEX IX_Usuario_RBAC_Bitacora_Fecha ON dbo.Usuario_RBAC_Bitacora (FechaEvento DESC);
    CREATE INDEX IX_Usuario_RBAC_Bitacora_Email ON dbo.Usuario_RBAC_Bitacora (UsuarioAfectadoEmail);
END
"""


def main():
    conn = pymssql.connect(
        server=os.environ['EDARSAHUB_SQL_HOST'],
        port=int(os.environ['EDARSAHUB_SQL_PORT']),
        user=os.environ['EDARSAHUB_SQL_USER'],
        password=os.environ['EDARSAHUB_SQL_PASSWORD'],
        database=os.environ['EDARSAHUB_SQL_DATABASE'],
        login_timeout=15, timeout=30, autocommit=True,
    )
    cur = conn.cursor()
    print("[1/2] Creando dbo.Usuario_RBAC_Bitacora (idempotente)...")
    cur.execute(DDL)
    print("[2/2] Verificando...")
    cur.execute("""
        SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Usuario_RBAC_Bitacora' ORDER BY ORDINAL_POSITION
    """)
    for r in cur.fetchall():
        print("   ", r)
    cur.execute("SELECT COUNT(*) FROM dbo.Usuario_RBAC_Bitacora")
    print("   rows:", cur.fetchone()[0])
    conn.close()
    print("OK")


if __name__ == "__main__":
    sys.exit(main())
