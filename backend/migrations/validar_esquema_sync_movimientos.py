"""
Validación de ESQUEMA (rollback) para el sync canónico de movimientos (4a).
Inserta 1 encabezado + 1 detalle con IDs reales resueltos y hace ROLLBACK.
NO persiste nada. Prueba que las columnas/FK coinciden (corrige 'Invalid column').
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))
import logging; logging.disable(logging.CRITICAL)
from core.sql_first.db import get_sql_connection


def main():
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    # IDs reales para respetar FKs
    cur.execute("SELECT TOP 1 AlmacenID, EmpresaID, SucursalID FROM Inventario_Almacenes WHERE Activo=1")
    alm = cur.fetchone()
    cur.execute("SELECT TOP 1 ProductoID FROM Producto_Catalogo ORDER BY ProductoID")
    prod = cur.fetchone()
    cur.execute("SELECT TOP 1 TipoMovimientoID FROM Inventario_TipoMovimiento WHERE Activo=1")
    tipo = cur.fetchone()
    cur.execute("SELECT TOP 1 SucursalID FROM RH_Cat_Sucursales")
    rhsuc = cur.fetchone()

    if not (alm and prod and tipo and rhsuc):
        print("[SKIP] Faltan catálogos para validar FKs:", alm, prod, tipo, rhsuc)
        conn.close(); return

    # SucursalID debe existir en RH_Cat_Sucursales (FK de Inventario_Movimientos)
    sucursal_id = alm["SucursalID"]
    cur.execute("SELECT COUNT(*) n FROM RH_Cat_Sucursales WHERE SucursalID=%s", (sucursal_id,))
    if cur.fetchone()["n"] == 0:
        sucursal_id = rhsuc["SucursalID"]

    empresa_id, almacen_id = alm["EmpresaID"], alm["AlmacenID"]
    producto_id, tipo_id = prod["ProductoID"], tipo["TipoMovimientoID"]
    print(f"[IDs reales] empresa={empresa_id} sucursal={sucursal_id} almacen={almacen_id} producto={producto_id} tipo={tipo_id}")

    w = conn.cursor()
    try:
        # Encabezado (mismas columnas que el módulo sync canónico)
        w.execute(
            """INSERT INTO Inventario_Movimientos
                 (TipoMovimientoID, EmpresaID, SucursalID, AlmacenID, FechaMovimiento,
                  ReferenciaTipo, FolioReferencia, Activo, CreatedAt)
               VALUES (%s,%s,%s,%s,GETDATE(),'MOVIMIENTO_POS','VALIDACION-RB',1,GETDATE())""",
            (tipo_id, empresa_id, sucursal_id, almacen_id),
        )
        w.execute("SELECT CAST(SCOPE_IDENTITY() AS BIGINT)")
        mid = w.fetchone()[0]
        # Detalle
        w.execute(
            """INSERT INTO Inventario_MovimientosDetalle
                 (MovimientoID, ProductoID, Cantidad, CostoUnitario, CreatedAt)
               VALUES (%s,%s,%s,%s,GETDATE())""",
            (mid, producto_id, 1.0, 10.0),
        )
        print(f"[OK] INSERT encabezado (MovimientoID={mid}) + detalle SIN errores de esquema/FK.")
    except Exception as e:
        print(f"[FALLO ESQUEMA/FK] {str(e)[:200]}")
        conn.rollback(); conn.close(); return

    conn.rollback()  # NO persistir
    print("[ROLLBACK] cambios revertidos. Cero filas persistidas.")
    # Confirmar que no quedó nada
    c2 = conn.cursor()
    c2.execute("SELECT COUNT(*) FROM Inventario_Movimientos WHERE FolioReferencia='VALIDACION-RB'")
    print(f"[VERIF] filas 'VALIDACION-RB' tras rollback: {c2.fetchone()[0]} (debe ser 0)")
    conn.close()


if __name__ == "__main__":
    main()
