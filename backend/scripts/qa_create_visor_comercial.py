"""QA: crea (idempotente) un usuario con rol VISOR_COMERCIAL para validar RBAC
comercial.* en endpoints reales. Solo para pruebas."""
import os, pymssql
from core.security import hash_password

EMAIL = 'qa.visorcomercial@edarsa.com'
PWD = 'VisorCom2026!'
ROL_ID = 20  # VISOR_COMERCIAL

conn = pymssql.connect(
    server=os.getenv('EDARSAHUB_SQL_HOST'), port=int(os.getenv('EDARSAHUB_SQL_PORT', '1433')),
    database=os.getenv('EDARSAHUB_SQL_DATABASE', 'EDARSAHUB'),
    user=os.getenv('EDARSAHUB_SQL_USER'), password=os.getenv('EDARSAHUB_SQL_PASSWORD'))
cur = conn.cursor()

cur.execute("SELECT UsuarioID FROM Usuario_Catalogo WHERE Email=%s", (EMAIL,))
row = cur.fetchone()
ph = hash_password(PWD)
if row:
    uid = row[0]
    cur.execute("UPDATE Usuario_Catalogo SET PasswordHashTexto=%s, Activo=1, Bloqueado=0, PasswordTemporal=0, DebeCambiarPassword=0 WHERE UsuarioID=%s", (ph, uid))
    print(f"[UPDATE] usuario existente UsuarioID={uid}")
else:
    cur.execute("""INSERT INTO Usuario_Catalogo
        (CodigoUsuario, Username, Email, PasswordHashTexto, Nombre, Apellidos, Activo,
         Bloqueado, PasswordTemporal, DebeCambiarPassword, FechaAlta)
        VALUES (%s,%s,%s,%s,%s,%s,1,0,0,0,SYSDATETIME())""",
        ('qa.visorcom', 'qa.visorcom', EMAIL, ph, 'QA Visor', 'Comercial'))
    cur.execute("SELECT @@IDENTITY")
    uid = int(cur.fetchone()[0])
    print(f"[CREATE] usuario nuevo UsuarioID={uid}")

# Asignar rol VISOR_COMERCIAL (limpiar otras asignaciones para que sea no-admin puro)
cur.execute("UPDATE Usuario_RolesAsignacion SET Activo=0 WHERE UsuarioID=%s", (uid,))
cur.execute("SELECT UsuarioRolAsignacionID FROM Usuario_RolesAsignacion WHERE UsuarioID=%s AND RolID=%s", (uid, ROL_ID))
if cur.fetchone():
    cur.execute("UPDATE Usuario_RolesAsignacion SET Activo=1, EsPrincipal=1 WHERE UsuarioID=%s AND RolID=%s", (uid, ROL_ID))
else:
    cur.execute("""INSERT INTO Usuario_RolesAsignacion (UsuarioID, RolID, EsPrincipal, FechaInicio, Activo, CreatedAt, CreatedBy)
        VALUES (%s,%s,1,GETDATE(),1,GETDATE(),'QA_SCRIPT')""", (uid, ROL_ID))
print(f"[ROL] VISOR_COMERCIAL (RolID={ROL_ID}) asignado a UsuarioID={uid}")

conn.commit()
conn.close()
print(f"OK -> {EMAIL} / {PWD}")
