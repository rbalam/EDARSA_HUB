"""
DIAGNÓSTICO READ-ONLY (cero escritura) — Derivación desde ORIGEN de:
  (a) catálogo de almacenes por unidad, y
  (b) SucursalOrigenID para resolver la ambigüedad MPRO.

NO inventa ni carga datos. Solo LEE del POS (vía conexión canónica) y de EDARSAHUB,
y reporta evidencia para que el usuario autorice la canonización.

SEGURO: no imprime credenciales/host/usuario/password. Usa el resolver/registry
canónico para obtener la conexión.

Uso: python scripts/diag_origen_almacenes_sucursal_safe.py [UNIDAD_CODIGO]
     (sin args = todas las unidades activas)
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))
import logging
logging.disable(logging.CRITICAL)  # silencia logs del pool que exponen host/usuario

from core.server_registry import (
    list_unidades_negocio,
    get_server_by_unidad_codigo,
    get_server_connection_info_with_secrets,
)
from core.db import execute_sql_query
from core.sql_first.db import get_sql_connection


def _es_mpro(system_type: str) -> bool:
    st = (system_type or "").upper()
    return "MPRO" in st or "MANAGEMENT" in st or "MANAGMENT" in st


def diagnosticar_unidad(unidad: dict):
    codigo = unidad.get("codigo", "")
    system_type = unidad.get("system_type", "")
    server_id = unidad.get("server_id") or unidad.get("id")
    sucursal_origen_un = unidad.get("sucursal_origen_id")
    print(f"\n=== UNIDAD {codigo} ({system_type}) ===")
    print(f"   sucursal_origen_id (Unidades_Negocio) = {sucursal_origen_un!r}  [evidencia existente]")

    srv = get_server_connection_info_with_secrets(str(server_id))
    if not srv:
        print("   [SIN CONEXIÓN] No se resolvió conexión canónica (secretos no impresos).")
        return

    # Catálogo de almacenes en ORIGEN
    if _es_mpro(system_type):
        q_alm = "SELECT CAST(Al_Cve_Almacen AS VARCHAR(50)) cod, Al_Descripcion nom FROM Almacen"
        q_suc = "SELECT CAST(Sc_Cve_Sucursal AS VARCHAR(50)) sc, Sc_Nombre nom FROM Sucursal"
    else:
        q_alm = "SELECT CAST(idalmacen AS VARCHAR(50)) cod, nombre nom FROM almacen"
        q_suc = None  # SoftRestaurant = 1 sucursal por DB

    try:
        almacenes = execute_sql_query(srv["host"], srv["port"], srv["database"], srv["username"], srv["password"], q_alm)
        print(f"   ALMACENES en origen: {len(almacenes or [])}")
        for a in (almacenes or [])[:20]:
            print(f"      cod={a.get('cod')} nom={a.get('nom')}")
    except Exception as e:
        print(f"   [ERROR leyendo almacenes] {str(e)[:80]}")

    if q_suc:
        try:
            sucs = execute_sql_query(srv["host"], srv["port"], srv["database"], srv["username"], srv["password"], q_suc)
            print(f"   SUCURSALES en origen (MPRO): {len(sucs or [])}")
            for s in (sucs or []):
                marca = " <-- coincide con Unidades_Negocio" if str(s.get("sc")) == str(sucursal_origen_un) else ""
                print(f"      Sc_Cve_Sucursal={s.get('sc')} nom={s.get('nom')}{marca}")
        except Exception as e:
            print(f"   [ERROR leyendo sucursales] {str(e)[:80]}")


def main():
    cod = sys.argv[1] if len(sys.argv) > 1 else None
    if cod:
        u = get_server_by_unidad_codigo(cod)
        unidades = [u] if u else []
    else:
        unidades = list_unidades_negocio(active_only=True)

    print(f"Unidades a diagnosticar: {[u.get('codigo') for u in unidades]}")
    for u in unidades:
        diagnosticar_unidad(u)


if __name__ == "__main__":
    main()
