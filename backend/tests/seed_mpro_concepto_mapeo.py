"""
Poblar Inventario_ConceptoMapeoOrigen para SystemType='MPRO'.
Lee el catálogo activo Tipo_Movimiento del POS ManagementPro y clasifica cada
Tm_Cve_Tipo_Movimiento al tipo canónico, según la regla validada por el usuario:
  - TRASPASO/TRANSFERENCIA/TRANSITO  -> EN:5 (TRASPASO_ENTRADA) / SA:6 (TRASPASO_SALIDA)
  - COMPRA (EN, sin ANULACION)       -> 1 (ENTRADA_COMPRA)
  - COMPRA o PROVEEDOR (SA)          -> 2 (SALIDA_DEV_PROV)   [incl. anulación entrada compra, dev. proveedor]
  - resto por naturaleza             -> EN:3 (AJUSTE_ENTRADA) / SA:4 (AJUSTE_SALIDA)
Idempotente (upsert por SystemType+ConceptoOrigen). NO hardcodea conceptos: deriva del catálogo POS.
"""
import sys
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
from core.sql_first.db import get_sql_connection
from core.db import execute_sql_query
from core.secret_manager import decrypt_secret

SYSTEM_TYPE = "MPRO"
CANON = {1: "ENTRADA_COMPRA", 2: "SALIDA_DEV_PROV", 3: "AJUSTE_ENTRADA",
         4: "AJUSTE_SALIDA", 5: "TRASPASO_ENTRADA", 6: "TRASPASO_SALIDA"}


def clasificar(descr: str, nat: str) -> int:
    d = (descr or "").upper()
    n = (nat or "").upper().strip()  # 'EN' / 'SA'
    if any(k in d for k in ("TRASPASO", "TRANSFERENCIA", "TRANSITO")):
        return 5 if n == "EN" else 6
    if n == "EN" and "COMPRA" in d and "ANULACION" not in d:
        return 1
    if n == "SA" and ("PROVEEDOR" in d or "COMPRA" in d):
        return 2
    return 3 if n == "EN" else 4


def main():
    conn = get_sql_connection(); cur = conn.cursor()
    cur.execute("SELECT host,port,database_name,username,password_encrypted FROM Servidores_Conexiones WHERE nombre='ManagmentPro'")
    h, p, db, u, pe = cur.fetchone(); pwd = decrypt_secret(pe)
    catalogo = execute_sql_query(h, int(p or 1433), db, u, pwd,
        "SELECT Tm_Cve_Tipo_Movimiento AS cve, Tm_Descripcion AS descr, Tm_Tipo AS nat FROM Tipo_Movimiento WHERE Es_Cve_Estado='AC'",
        timeout_seconds=40, context="jobs")
    print(f"Catálogo MPRO activo: {len(catalogo)} tipos")

    insertados = actualizados = 0
    w = conn.cursor()
    for row in catalogo:
        cve = str(row["cve"]).strip()
        descr = (row["descr"] or "").strip()
        nat = (row["nat"] or "").strip()
        tipo_id = clasificar(descr, nat)
        desc_canon = f"MPRO {cve} {descr} -> {CANON[tipo_id]}"[:200]
        w.execute("SELECT TipoMovimientoID FROM Inventario_ConceptoMapeoOrigen WHERE SystemType=%s AND ConceptoOrigen=%s",
                  (SYSTEM_TYPE, cve))
        ex = w.fetchone()
        if ex:
            w.execute("""UPDATE Inventario_ConceptoMapeoOrigen
                         SET TipoMovimientoID=%s, Descripcion=%s, Activo=1
                         WHERE SystemType=%s AND ConceptoOrigen=%s""",
                      (tipo_id, desc_canon, SYSTEM_TYPE, cve))
            actualizados += 1
        else:
            w.execute("""INSERT INTO Inventario_ConceptoMapeoOrigen
                         (SystemType, ConceptoOrigen, TipoMovimientoID, Descripcion, Activo, FechaCreacion)
                         VALUES (%s,%s,%s,%s,1,SYSDATETIME())""",
                      (SYSTEM_TYPE, cve, tipo_id, desc_canon))
            insertados += 1
    conn.commit()
    print(f"MPRO conceptos -> insertados={insertados} actualizados={actualizados}")

    # Resumen por tipo canónico
    w.execute("""SELECT TipoMovimientoID, COUNT(*) n FROM Inventario_ConceptoMapeoOrigen
                 WHERE SystemType='MPRO' GROUP BY TipoMovimientoID ORDER BY TipoMovimientoID""")
    print("Distribución MPRO:", [(CANON[r[0]], r[1]) for r in w.fetchall()])
    # Verificación de los códigos usados clave
    for cve, esperado in [("050","ENTRADA_COMPRA"),("106","TRASPASO_ENTRADA"),("506","TRASPASO_SALIDA"),
                          ("400","SALIDA_DEV_PROV"),("051","SALIDA_DEV_PROV"),("700","AJUSTE_SALIDA"),
                          ("902","AJUSTE_ENTRADA"),("904","AJUSTE_SALIDA"),("940","AJUSTE_ENTRADA"),
                          ("508","AJUSTE_SALIDA"),("512","AJUSTE_SALIDA"),("108","AJUSTE_ENTRADA"),("112","AJUSTE_ENTRADA")]:
        w.execute("SELECT TipoMovimientoID FROM Inventario_ConceptoMapeoOrigen WHERE SystemType='MPRO' AND ConceptoOrigen=%s",(cve,))
        r = w.fetchone()
        got = CANON.get(r[0]) if r else None
        print(f"  {cve}: {got} {'OK' if got==esperado else 'MISMATCH(esp '+esperado+')'}")
    conn.close()


if __name__ == "__main__":
    main()
