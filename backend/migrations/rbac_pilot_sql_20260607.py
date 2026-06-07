"""
Migración SQL-First del RBAC Piloto (perfiles/roles/permisos de sistema).

Contexto: el panel "Seguridad RBAC" de la pantalla Usuarios corría sobre colecciones
Mongo (`sec_perfiles`, `sec_roles`, `sec_permisos_catalogo`, `users.sec_*`), hoy
deshabilitadas (`db = get_stub_database()`). Esta migración lleva ese modelo a SQL
(EDARSAHUB) de forma fiel, reusando datos del respaldo mongodump.

Crea (idempotente):
  - dbo.Sistema_RBAC_PerfilCatalogo  : catálogo de perfiles -> roles (CSV)
  - dbo.Usuario_RBAC_Asignacion      : asignación por usuario (PERFIL | ROL | PERMISO)

Y siembra el catálogo de perfiles FASE 13 (idéntico al respaldo sec_perfiles).
NO destruye datos. Ejecutable múltiples veces sin efecto duplicado.
"""
import os
import sys
import pymssql
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

# Perfiles FASE 13 (fuente: mongodump edarsa_hub/sec_perfiles.bson)
PERFILES_SEED = [
    ("PERFIL_VISOR_BASICO",   "Visor Básico",    "VISOR_ESTRUCTURA"),
    ("PERFIL_VISOR_SISTEMA",  "Visor Sistema",   "VISOR_ESTRUCTURA,VISOR_SISTEMA"),
    ("PERFIL_VISOR_COMPLETO", "Visor Completo",  "VISOR_ADMIN"),
    ("PERFIL_ADMIN_USUARIOS", "Admin Usuarios",  "VISOR_ADMIN,ADMIN_USUARIOS"),
    ("PERFIL_GESTOR_SISTEMA", "Gestor Sistema",  "GESTOR_SISTEMA"),
]

DDL_PERFIL_CATALOGO = """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Sistema_RBAC_PerfilCatalogo')
BEGIN
    CREATE TABLE dbo.Sistema_RBAC_PerfilCatalogo (
        PerfilID   INT IDENTITY(1,1) PRIMARY KEY,
        Codigo     NVARCHAR(60)  NOT NULL UNIQUE,
        Nombre     NVARCHAR(120) NOT NULL,
        RolesCsv   NVARCHAR(500) NOT NULL DEFAULT '',
        Activo     BIT           NOT NULL DEFAULT 1,
        FechaAlta  DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
"""

DDL_ASIGNACION = """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Usuario_RBAC_Asignacion')
BEGIN
    CREATE TABLE dbo.Usuario_RBAC_Asignacion (
        AsignacionID    INT IDENTITY(1,1) PRIMARY KEY,
        UsuarioID       INT           NOT NULL,
        Tipo            NVARCHAR(12)   NOT NULL,   -- 'PERFIL' | 'ROL' | 'PERMISO'
        Codigo          NVARCHAR(60)   NOT NULL,
        AsignadoPor     NVARCHAR(150)  NULL,
        FechaAsignacion DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_UsuarioRBACAsignacion_Usuario
        ON dbo.Usuario_RBAC_Asignacion (UsuarioID, Tipo);
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
    print("[1/3] Creando tablas (idempotente)...")
    cur.execute(DDL_PERFIL_CATALOGO)
    cur.execute(DDL_ASIGNACION)

    print("[2/3] Sembrando catálogo de perfiles FASE 13...")
    for codigo, nombre, roles_csv in PERFILES_SEED:
        cur.execute(
            "SELECT PerfilID FROM dbo.Sistema_RBAC_PerfilCatalogo WHERE Codigo = %s",
            (codigo,),
        )
        if cur.fetchone():
            cur.execute(
                "UPDATE dbo.Sistema_RBAC_PerfilCatalogo SET Nombre=%s, RolesCsv=%s, Activo=1 WHERE Codigo=%s",
                (nombre, roles_csv, codigo),
            )
        else:
            cur.execute(
                "INSERT INTO dbo.Sistema_RBAC_PerfilCatalogo (Codigo, Nombre, RolesCsv, Activo) VALUES (%s,%s,%s,1)",
                (codigo, nombre, roles_csv),
            )

    print("[3/3] Verificando...")
    cur.execute("SELECT Codigo, Nombre, RolesCsv, Activo FROM dbo.Sistema_RBAC_PerfilCatalogo ORDER BY PerfilID")
    for r in cur.fetchall():
        print("   ", r)
    cur.execute("SELECT COUNT(*) FROM dbo.Usuario_RBAC_Asignacion")
    print("   Usuario_RBAC_Asignacion rows:", cur.fetchone()[0])
    conn.close()
    print("OK")


if __name__ == "__main__":
    sys.exit(main())
