"""
Migración: Usuarios del Portal de Inteligencia Comercial (EXTERNOS)
==================================================================
Crea dbo.Portal_Inteligencia_Usuarios: usuarios EXTERNOS con login propio para
el Portal de Inteligencia Comercial, cada uno acotado a un conjunto de unidades
de negocio asignadas.

MÁXIMA NO-MONGO: almacenamiento 100% SQL Server (EDARSAHUB). Idempotente.
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
        server=os.getenv('EDARSAHUB_SQL_HOST'),
        port=int(os.getenv('EDARSAHUB_SQL_PORT', '1433')),
        database=os.getenv('EDARSAHUB_SQL_DATABASE'),
        user=os.getenv('EDARSAHUB_SQL_USER'),
        password=os.getenv('EDARSAHUB_SQL_PASSWORD'),
        timeout=60, login_timeout=30,
    )


DDL = """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Portal_Inteligencia_Usuarios')
BEGIN
    CREATE TABLE dbo.Portal_Inteligencia_Usuarios (
        Id                  NVARCHAR(36)  NOT NULL PRIMARY KEY,
        Email               NVARCHAR(200) NOT NULL,
        PasswordHash        NVARCHAR(255) NOT NULL,
        Nombre              NVARCHAR(200) NULL,
        UnidadesAsignadas   NVARCHAR(MAX) NULL,   -- JSON array de CÓDIGOS de unidad
        Activo              BIT           NOT NULL DEFAULT 1,
        FechaCreacion       DATETIME      NOT NULL DEFAULT GETDATE(),
        FechaActualizacion  DATETIME      NULL,
        UltimoAcceso        DATETIME      NULL,
        CreadoPor           NVARCHAR(200) NULL
    );
    CREATE UNIQUE INDEX UX_PortalIntel_Email ON dbo.Portal_Inteligencia_Usuarios(Email);
END
"""


def run():
    conn = _conn()
    cur = conn.cursor()
    print('[MIG] Creando tabla Portal_Inteligencia_Usuarios (si no existe)...')
    cur.execute(DDL)
    conn.commit()
    cur.execute("SELECT COUNT(1) FROM dbo.Portal_Inteligencia_Usuarios")
    print(f'[MIG] OK. Usuarios actuales: {cur.fetchone()[0]}')
    cur.close()
    conn.close()


if __name__ == '__main__':
    run()
