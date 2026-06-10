"""
Seed idempotente del item de menú 'Catálogo Enriquecido' en Sistema_ModulosMenus.
Integración limpia (NO hardcode de datos de negocio; es configuración de navegación).
"""
import sys
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
from core.sql_first.db import get_sql_connection

CODIGO = "comercial.catalogo_enriquecido"


def main():
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)

    cur.execute("SELECT MenuID FROM Sistema_ModulosMenus WHERE Codigo = %s", (CODIGO,))
    existing = cur.fetchone()
    if existing:
        print(f"[SKIP] Ya existe MenuID={existing['MenuID']} para {CODIGO}")
        cur.close(); conn.close(); return

    # Tomar ModuloID del módulo comercial (referencia: comercial.dashboard)
    cur.execute("SELECT TOP 1 ModuloID FROM Sistema_ModulosMenus WHERE Codigo = 'comercial.dashboard'")
    row = cur.fetchone()
    modulo_id = row['ModuloID'] if row else 2

    cur.execute("""
        INSERT INTO Sistema_ModulosMenus
            (ModuloID, MenuPadreID, Codigo, Nombre, Descripcion, Icono, Ruta, Orden, RequierePermiso, Activo, FechaCreacion)
        VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, %s, 1, GETDATE())
    """, (
        modulo_id, CODIGO, "Catálogo Enriquecido",
        "Catálogo comercial de productos enriquecidos", "Package",
        "/comercial/catalogo-enriquecido", 7, "comercial.costos"
    ))
    conn.commit()
    print(f"[OK] Insertado menú '{CODIGO}' (ModuloID={modulo_id}, Ruta=/comercial/catalogo-enriquecido)")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
