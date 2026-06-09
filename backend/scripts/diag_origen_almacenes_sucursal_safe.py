"""
==============================================================================
DIAGNÓSTICO DE ORIGEN (READ-ONLY) — Candidatos de canonización
==============================================================================
Deriva DESDE EL ORIGEN (POS) evidencia para canonizar, SIN escribir nada:
  - catálogo de almacenes por unidad,
  - sucursales de origen (MPRO) para resolver la ambigüedad ORIGEN / 130QRO,
  - cobertura por unidad,
  - propuesta de mapeo (NO se aplica automáticamente).

------------------------------------------------------------------------------
CONDICIONES (cumplidas estrictamente):
  1. 100% READ-ONLY.        2. Cero escritura.     3. Cero DDL.    4. Cero DML.
  5. NO imprime host, base, usuario, password, tokens ni longitudes de password.
  6. Reporta SOLO: unidad_codigo, sistema_origen, conectividad sí/no, tabla
     consultada, conteo de filas, MIN/MAX de fechas, almacenes origen, sucursales
     origen, estado (OK | SIN_CONEXION | SIN_DATOS | ERROR_CONTROLADO).
  7. NO usa POS live desde dashboards (es un script de diagnóstico aislado).
  8. NO cambia drivers ni instala ODBC.
  9. NO usa fallback improvisado.
 10. Usa el helper canónico core/server_registry.py.

------------------------------------------------------------------------------
CÓMO EJECUTAR (en el ENTORNO PRODUCTIVO con acceso real al POS):

    cd /app/backend
    python scripts/diag_origen_almacenes_sucursal_safe.py            # todas las unidades
    python scripts/diag_origen_almacenes_sucursal_safe.py CIENFUEGOS # una unidad

  Salida: reporte por unidad + sección final de CANDIDATOS. No escribe nada.
  Si el POS no responde -> estado SIN_CONEXION (sin exponer secretos).
==============================================================================
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))

import logging
logging.disable(logging.CRITICAL)  # silencia logs del pool que podrían exponer host/usuario

from core.server_registry import (
    list_unidades_negocio,
    get_server_by_unidad_codigo,
    get_server_connection_info_with_secrets,
)
from core.db import execute_sql_query


def _es_mpro(system_type: str) -> bool:
    st = (system_type or "").upper()
    return "MPRO" in st or "MANAGEMENT" in st or "MANAGMENT" in st


def _probar_conexion(srv) -> bool:
    """Sonda REAL de conectividad: SELECT 1. Una conexión viva siempre devuelve fila.
    (execute_sql_query devuelve [] tanto en error como en tabla vacía, por eso no basta
    con el conteo: hay que probar SELECT 1 explícitamente.)"""
    r = execute_sql_query(srv["host"], srv["port"], srv["database"],
                          srv["username"], srv["password"], "SELECT 1 AS ok")
    return bool(r) and r[0].get("ok") == 1


def _safe_query(srv, query):
    """Ejecuta SELECT read-only. Devuelve (filas|[]). Nunca expone secretos."""
    return execute_sql_query(srv["host"], srv["port"], srv["database"],
                             srv["username"], srv["password"], query)


def diagnosticar_unidad(unidad: dict) -> dict:
    codigo = unidad.get("codigo", "")
    system_type = unidad.get("system_type", "")
    server_id = unidad.get("server_id") or unidad.get("id")
    sucursal_origen_un = unidad.get("sucursal_origen_id")
    es_mpro = _es_mpro(system_type)

    rep = {
        "unidad_codigo": codigo,
        "sistema_origen": system_type,
        "conectividad": False,
        "tabla_consultada": "movtosalmacen" if not es_mpro else "Movimiento",
        "conteo_filas_movimientos": 0,
        "fecha_min": None,
        "fecha_max": None,
        "almacenes_origen": [],
        "sucursales_origen": [],
        "sucursal_origen_unidad_negocio": sucursal_origen_un,
        "estado": "SIN_CONEXION",
    }

    srv = get_server_connection_info_with_secrets(str(server_id))
    if not srv:
        rep["estado"] = "SIN_CONEXION"
        return rep

    # Sonda REAL de conectividad antes de cualquier conteo (evita falsos positivos
    # porque execute_sql_query devuelve [] tanto en error como en tabla vacía).
    if not _probar_conexion(srv):
        rep["conectividad"] = False
        rep["estado"] = "SIN_CONEXION"
        return rep
    rep["conectividad"] = True

    try:
        # 1) Movimientos: conteo + MIN/MAX fecha (read-only)
        if es_mpro:
            q_mov = "SELECT COUNT(*) n, MIN(Mo_Fecha) fmin, MAX(Mo_Fecha) fmax FROM Movimiento"
            q_alm = "SELECT CAST(Al_Cve_Almacen AS VARCHAR(50)) cod, Al_Descripcion nom FROM Almacen"
            q_suc = "SELECT CAST(Sc_Cve_Sucursal AS VARCHAR(50)) sc, Sc_Nombre nom FROM Sucursal"
        else:
            q_mov = "SELECT COUNT(*) n, MIN(fecha) fmin, MAX(fecha) fmax FROM movtosalmacen WHERE cancelado = 0"
            q_alm = "SELECT CAST(idalmacen AS VARCHAR(50)) cod, nombre nom FROM almacen"
            q_suc = None  # SoftRestaurant = 1 sucursal por base

        mov = _safe_query(srv, q_mov)
        if mov and mov[0].get("n") is not None:
            rep["conteo_filas_movimientos"] = int(mov[0]["n"] or 0)
            fmin, fmax = mov[0].get("fmin"), mov[0].get("fmax")
            rep["fecha_min"] = str(fmin) if fmin else None
            rep["fecha_max"] = str(fmax) if fmax else None

        # 2) Almacenes de origen (candidatos)
        almacenes = _safe_query(srv, q_alm) or []
        rep["almacenes_origen"] = [{"codigo": a.get("cod"), "nombre": a.get("nom")} for a in almacenes]

        # 3) Sucursales de origen (solo MPRO)
        if q_suc:
            sucs = _safe_query(srv, q_suc) or []
            for s in sucs:
                rep["sucursales_origen"].append({
                    "sc_cve_sucursal": s.get("sc"),
                    "nombre": s.get("nom"),
                    "coincide_unidad_negocio": str(s.get("sc")) == str(sucursal_origen_un),
                })

        if rep["conteo_filas_movimientos"] == 0 and not rep["almacenes_origen"]:
            rep["estado"] = "SIN_DATOS"
        else:
            rep["estado"] = "OK"

    except Exception as e:
        rep["conectividad"] = True if rep["conectividad"] else False
        rep["estado"] = "ERROR_CONTROLADO"
        rep["error"] = str(e)[:120]  # mensaje recortado, sin secretos

    return rep


def imprimir_reporte(rep: dict):
    print(f"\n=== UNIDAD {rep['unidad_codigo']} ({rep['sistema_origen']}) ===")
    print(f"   conectividad      : {'SI' if rep['conectividad'] else 'NO'}")
    print(f"   tabla_consultada  : {rep['tabla_consultada']}")
    print(f"   conteo_filas_mov  : {rep['conteo_filas_movimientos']}")
    print(f"   fecha_min/max     : {rep['fecha_min']} .. {rep['fecha_max']}")
    print(f"   almacenes_origen  : {len(rep['almacenes_origen'])}")
    for a in rep["almacenes_origen"][:30]:
        print(f"        - {a['codigo']}: {a['nombre']}")
    print(f"   sucursales_origen : {len(rep['sucursales_origen'])}")
    for s in rep["sucursales_origen"]:
        marca = " <-- coincide con Unidades_Negocio.sucursal_origen_id" if s["coincide_unidad_negocio"] else ""
        print(f"        - Sc={s['sc_cve_sucursal']}: {s['nombre']}{marca}")
    print(f"   estado            : {rep['estado']}")


def imprimir_candidatos(reportes):
    print("\n\n========== CANDIDATOS DE CANONIZACIÓN (propuesta, SIN escritura) ==========")
    print("\n[1] ALMACENES ORIGEN -> Inventario_Almacenes (por unidad):")
    for r in reportes:
        if r["almacenes_origen"]:
            print(f"   {r['unidad_codigo']}: {len(r['almacenes_origen'])} almacenes candidatos")

    print("\n[2] SUCURSAL ORIGEN MPRO -> Sistema_SucursalServidorMapeo.SucursalOrigenID:")
    for r in reportes:
        if _es_mpro(r["sistema_origen"]):
            confirma = [s for s in r["sucursales_origen"] if s["coincide_unidad_negocio"]]
            if confirma:
                print(f"   {r['unidad_codigo']}: ORIGEN confirma SucursalOrigenID={confirma[0]['sc_cve_sucursal']} "
                      f"(coincide con Unidades_Negocio) -> AMBIGÜEDAD RESOLUBLE")
            else:
                print(f"   {r['unidad_codigo']}: sin confirmación cruzada -> PERMANECE AMBIGUO")

    print("\n[3] COBERTURA POR UNIDAD (estado de conectividad/datos):")
    for r in reportes:
        print(f"   {r['unidad_codigo']:<12} {r['sistema_origen']:<18} estado={r['estado']:<16} "
              f"mov={r['conteo_filas_movimientos']} almacenes={len(r['almacenes_origen'])}")

    print("\n[4] NOTA: Esta es una PROPUESTA. NO se aplica ningún INSERT/UPDATE automático.")
    print("    La carga real requiere autorización explícita paso a paso.")


def main():
    cod = sys.argv[1] if len(sys.argv) > 1 else None
    if cod:
        u = get_server_by_unidad_codigo(cod)
        unidades = [u] if u else []
    else:
        unidades = list_unidades_negocio(active_only=True)

    print(f"Unidades a diagnosticar: {[u.get('codigo') for u in unidades]}")
    reportes = []
    for u in unidades:
        rep = diagnosticar_unidad(u)
        imprimir_reporte(rep)
        reportes.append(rep)
    imprimir_candidatos(reportes)


if __name__ == "__main__":
    main()
