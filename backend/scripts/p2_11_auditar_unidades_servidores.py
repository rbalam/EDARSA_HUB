import os
import pymssql

cn = pymssql.connect(
    server=os.getenv("EDARSAHUB_SQL_HOST"),
    port=int(os.getenv("EDARSAHUB_SQL_PORT","1433")),
    user=os.getenv("EDARSAHUB_SQL_USER"),
    password=os.getenv("EDARSAHUB_SQL_PASSWORD"),
    database=os.getenv("EDARSAHUB_SQL_DATABASE")
)

cur = cn.cursor(as_dict=True)

print("\n=== UNIDADES DE NEGOCIO ===")
for q in [
    "SELECT * FROM Unidades_Negocio",
    "SELECT * FROM Unidad_Negocio",
    "SELECT * FROM Empresa_Unidades"
]:
    try:
        cur.execute(q)
        rows = cur.fetchall()
        print(q, "->", len(rows))
        if rows:
            for r in rows[:20]:
                print(r)
    except:
        pass

print("\n=== SERVIDORES_CONEXIONES ===")
cur.execute("""
SELECT
    ID,
    Nombre,
    EmpresaID,
    UnidadNegocioID,
    CodigoUnidad,
    TipoConexion
FROM Servidores_Conexiones
ORDER BY Nombre
""")

for r in cur.fetchall():
    print(r)

print("\n=== USUARIOS ===")
try:
    cur.execute("""
    SELECT TOP 50 *
    FROM Usuario_Catalogo
    """)
    for r in cur.fetchall():
        print(r)
except Exception as e:
    print(e)

print("\n=== ROLES ===")
try:
    cur.execute("""
    SELECT TOP 100 *
    FROM Usuario_Roles
    """)
    for r in cur.fetchall():
        print(r)
except Exception as e:
    print(e)

cn.close()
