"""
EJECUCIÓN AUTORIZADA (puntual) - UPDATE aditivo SucursalOrigenID MPRO.
ORIGEN(SucursalID=1)->'0023' ; 130QRO(SucursalID=2)->'0021'.
Cumple condiciones del usuario: backup lógico, transacción, validación pre/post,
solo 2 filas, additive (solo donde SucursalOrigenID IS NULL), reporte completo.
NO toca ServerID/unidad/permisos/usuarios/roles/otras unidades.
"""
import sys, json
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))
import logging; logging.disable(logging.CRITICAL)
from core.sql_first.db import get_sql_connection

SERVER_MPRO = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
OBJETIVO = {1: "0023", 2: "0021"}  # SucursalID(Sistema_Sucursales) -> SucursalOrigenID


def snapshot(cur):
    cur.execute("SELECT * FROM Sistema_SucursalServidorMapeo WHERE ServidorID=%s ORDER BY SucursalID", (SERVER_MPRO,))
    return cur.fetchall()


def main():
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)

    # Conteos globales (para probar que no se inserta/borra nada en ningún lado)
    cur.execute("SELECT COUNT(*) n FROM Sistema_SucursalServidorMapeo")
    total_global_antes = cur.fetchone()["n"]

    # BACKUP LÓGICO de filas afectadas
    antes = snapshot(cur)
    print("=== BACKUP LÓGICO (filas server MPRO, ANTES) ===")
    print(json.dumps([{k: str(v) for k, v in r.items()} for r in antes], indent=2, ensure_ascii=False))

    # UPDATE aditivo (solo SucursalOrigenID NULL, exactamente las 2 filas objetivo)
    w = conn.cursor()
    afectadas = 0
    for suc_id, origen in OBJETIVO.items():
        w.execute(
            """UPDATE Sistema_SucursalServidorMapeo SET SucursalOrigenID=%s
               WHERE ServidorID=%s AND SucursalID=%s AND SucursalOrigenID IS NULL""",
            (origen, SERVER_MPRO, suc_id),
        )
        afectadas += w.rowcount

    # VALIDACIÓN PRE-COMMIT
    despues = snapshot(cur)
    cur.execute("SELECT COUNT(*) n FROM Sistema_SucursalServidorMapeo")
    total_global_despues = cur.fetchone()["n"]
    by_suc = {r["SucursalID"]: r["SucursalOrigenID"] for r in despues}
    ok = (
        afectadas == 2
        and by_suc.get(1) == "0023"
        and by_suc.get(2) == "0021"
        and len(despues) == len(antes)            # no se agregaron/quitaron filas del server
        and total_global_despues == total_global_antes  # nada global insertado/borrado
        and {r["ServidorID"] for r in despues} == {r["ServidorID"] for r in antes}  # ServerID intacto
    )
    print(f"\n[PRE-COMMIT] filas_afectadas={afectadas} (esperado 2)")
    print(f"[PRE-COMMIT] SucursalOrigenID -> {by_suc}")
    print(f"[PRE-COMMIT] total filas server: antes={len(antes)} despues={len(despues)} | global: antes={total_global_antes} despues={total_global_despues}")
    if not ok:
        conn.rollback()
        print("[ABORT] Validación falló -> ROLLBACK. Cero persistido.")
        conn.close(); return

    conn.commit()
    print("[COMMIT] Cambios persistidos (2 filas, additive).")

    # VALIDACIÓN POST-COMMIT
    cur2 = conn.cursor(as_dict=True)
    final = snapshot(cur2)
    print("\n=== DESPUÉS (POST-COMMIT) ===")
    for r in final:
        print(f"   SucursalID={r['SucursalID']} SucursalOrigenID={r['SucursalOrigenID']} ServidorID={r['ServidorID']}")

    # Resolver MPRO ya no AMBIGUO
    from core.inventarios.resolver_canonico import resolver_sucursal_id
    r_origen = resolver_sucursal_id(SERVER_MPRO, "0023")
    r_qro = resolver_sucursal_id(SERVER_MPRO, "0021")
    print(f"\n[RESOLVER] ORIGEN(0023) -> {r_origen}")
    print(f"[RESOLVER] 130QRO(0021) -> {r_qro}")

    # Control de acceso: la seguridad filtra por EmpresaID (no SucursalOrigenID) -> sin cambio.
    print("\n[ACCESO] La query de seguridad (core/security.py) NO filtra por SucursalOrigenID;")
    print("         solo se rellenó ese campo (NULL->valor). EmpresaID/SucursalID/Activo intactos -> SIN cambio de acceso.")
    print("[OK] ORIGEN y 130QRO permanecen separados; ninguna otra unidad fue tocada.")
    conn.close()


if __name__ == "__main__":
    main()
