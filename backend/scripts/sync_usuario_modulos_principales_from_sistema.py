from contextlib import closing
from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

TARGETS = [
    "ACTIVOS_FIJOS",
    "CALIDAD",
    "CATALOGOS",
    "COMISIONES",
    "COMPRAS",
    "CONTABILIDAD",
    "DIRECCION",
    "FINANZAS",
    "HOST_TO_HOST",
    "IA",
    "INTEGRACIONES",
    "INVENTARIOS",
    "MARKETING",
    "PROYECTOS",
    "REPORTES_BI",
    "RH",
    "SISTEMA",
]

def norm(value):
    return str(value or "").strip().lower()

def fetch_existing_codes(cur):
    cur.execute("""
        SELECT LOWER(LTRIM(RTRIM(CodigoModulo))) AS CodigoModulo
        FROM dbo.Usuario_Modulos
    """)
    return {norm(r["CodigoModulo"]) for r in cur.fetchall()}

def get_modulo_id(cur, codigo):
    cur.execute("""
        SELECT TOP 1 ModuloID
        FROM dbo.Usuario_Modulos
        WHERE LOWER(LTRIM(RTRIM(CodigoModulo))) = %s
    """, (norm(codigo),))
    row = cur.fetchone()
    return row["ModuloID"] if row else None

def insert_modulo(
    cur,
    codigo,
    nombre,
    descripcion,
    tipo,
    ruta,
    icono,
    orden,
    visible,
    requiere_autorizacion,
    activo,
    padre_id=None,
):
    cur.execute("""
        IF NOT EXISTS (
            SELECT 1
            FROM dbo.Usuario_Modulos
            WHERE LOWER(LTRIM(RTRIM(CodigoModulo))) = LOWER(LTRIM(RTRIM(%s)))
        )
        BEGIN
            INSERT INTO dbo.Usuario_Modulos (
                ModuloPadreID,
                CodigoModulo,
                NombreModulo,
                Descripcion,
                TipoModulo,
                Ruta,
                Icono,
                OrdenMenu,
                EsVisibleMenu,
                RequiereAutorizacion,
                Activo,
                FechaAlta
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, SYSDATETIME()
            )
        END
    """, (
        codigo,
        padre_id,
        codigo,
        nombre,
        descripcion,
        tipo,
        ruta,
        icono,
        int(orden or 0),
        int(bool(visible)),
        int(bool(requiere_autorizacion)),
        int(bool(activo)),
    ))

def main(apply=False):
    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10, autocommit=False)

    inserted_parents = []
    inserted_children = []
    skipped = []

    try:
        with closing(conn):
            cur = conn.cursor(as_dict=True)

            cur.execute("SELECT DB_NAME() AS database_name, @@SERVERNAME AS server_name")
            base = cur.fetchone()
            print("===== BASE =====")
            print(f"database={base['database_name']} server={base['server_name']}")

            placeholders = ",".join(["%s"] * len(TARGETS))

            cur.execute(f"""
                SELECT
                    sm.Codigo,
                    sm.Nombre,
                    sm.Descripcion,
                    sm.Icono,
                    ISNULL(sm.Orden, 0) AS Orden
                FROM dbo.Sistema_Modulos sm
                LEFT JOIN dbo.Usuario_Modulos um
                    ON UPPER(LTRIM(RTRIM(um.CodigoModulo))) = UPPER(LTRIM(RTRIM(sm.Codigo)))
                WHERE sm.Codigo IN ({placeholders})
                  AND ISNULL(sm.Activo, 1) = 1
                  AND ISNULL(sm.EsPrincipal, 0) = 1
                  AND um.ModuloID IS NULL
                ORDER BY sm.Orden, sm.Codigo
            """, tuple(TARGETS))
            parent_rows = cur.fetchall()

            print()
            print("===== INSERT PADRES =====")
            for r in parent_rows:
                codigo = norm(r["Codigo"])
                insert_modulo(
                    cur=cur,
                    codigo=codigo,
                    nombre=r["Nombre"],
                    descripcion=r["Descripcion"],
                    tipo="MODULO",
                    ruta=None,
                    icono=r["Icono"],
                    orden=r["Orden"],
                    visible=True,
                    requiere_autorizacion=False,
                    activo=True,
                    padre_id=None,
                )
                inserted_parents.append(codigo)
                print(f"PADRE {codigo}")

            existing_codes = fetch_existing_codes(cur)

            cur.execute(f"""
                SELECT
                    sm.Codigo AS SistemaCodigo,
                    smm.Codigo AS MenuCodigo,
                    smm.Nombre AS MenuNombre,
                    smm.Descripcion AS MenuDescripcion,
                    smm.Ruta,
                    smm.Icono AS MenuIcono,
                    sm.Icono AS SistemaIcono,
                    ISNULL(smm.Orden, 0) AS MenuOrden,
                    smm.RequierePermiso
                FROM dbo.Sistema_Modulos sm
                JOIN dbo.Sistema_ModulosMenus smm
                    ON smm.ModuloID = sm.ModuloID
                WHERE sm.Codigo IN ({placeholders})
                  AND ISNULL(sm.Activo, 1) = 1
                  AND ISNULL(sm.EsPrincipal, 0) = 1
                  AND ISNULL(smm.Activo, 1) = 1
                  AND NULLIF(LTRIM(RTRIM(smm.RequierePermiso)), '') IS NOT NULL
                ORDER BY sm.Orden, sm.Codigo, smm.Orden, smm.MenuID
            """, tuple(TARGETS))
            menu_rows = cur.fetchall()

            seen_child = set()

            print()
            print("===== INSERT HIJOS =====")
            for r in menu_rows:
                parent_code = norm(r["SistemaCodigo"])
                child_code = norm(r["RequierePermiso"])

                if not child_code:
                    continue

                if child_code == parent_code:
                    skipped.append((child_code, "mismo codigo que padre"))
                    continue

                if child_code in existing_codes:
                    skipped.append((child_code, "ya existe en Usuario_Modulos"))
                    continue

                if child_code in seen_child:
                    skipped.append((child_code, "duplicado dentro del plan"))
                    continue

                parent_id = get_modulo_id(cur, parent_code)
                if not parent_id:
                    raise RuntimeError(f"No existe padre para hijo {child_code}: {parent_code}")

                insert_modulo(
                    cur=cur,
                    codigo=child_code,
                    nombre=r["MenuNombre"],
                    descripcion=r["MenuDescripcion"],
                    tipo="SUBMODULO",
                    ruta=r["Ruta"],
                    icono=r["MenuIcono"] or r["SistemaIcono"],
                    orden=r["MenuOrden"],
                    visible=True,
                    requiere_autorizacion=False,
                    activo=True,
                    padre_id=parent_id,
                )

                seen_child.add(child_code)
                inserted_children.append(child_code)
                print(f"HIJO {parent_code} -> {child_code}")

            print()
            print("===== OMITIDOS =====")
            for code, reason in skipped:
                print(f"{code}: {reason}")

            print()
            print("===== RESUMEN =====")
            print(f"padres_insertados_o_confirmados={len(inserted_parents)}")
            print(f"hijos_insertados_o_confirmados={len(inserted_children)}")
            print(f"omitidos={len(skipped)}")

            if apply:
                conn.commit()
                print("COMMIT_OK")
            else:
                conn.rollback()
                print("DRY_RUN_ROLLBACK_OK")

    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise

if __name__ == "__main__":
    import sys
    main(apply="--apply" in sys.argv)
