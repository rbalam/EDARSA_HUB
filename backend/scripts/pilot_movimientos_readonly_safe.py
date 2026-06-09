"""
PILOTO de SOLO LECTURA - validación de volumen de movimientos (SoftRestaurant).
SEGURO: NO imprime credenciales, host, usuario, base ni longitudes.
Reporta SOLO conteos agregados para validar volumen y fidelidad de clasificación.

Uso: python scripts/pilot_movimientos_readonly_safe.py <unidad_codigo>
"""
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))

from core.server_registry import get_server_by_unidad_codigo, get_server_connection_info_with_secrets
from core.db import execute_sql_query
from modules.compras.sync_service import TIPO_MOVIMIENTO_SR_TO_EDARSAHUB


def run(unidad_codigo: str):
    unidad = get_server_by_unidad_codigo(unidad_codigo)
    if not unidad:
        print(f"[ERR] Unidad '{unidad_codigo}' no encontrada")
        return
    server_id = unidad.get("server_id") or unidad.get("id")
    srv = get_server_connection_info_with_secrets(server_id)
    if not srv:
        print(f"[ERR] No se pudo resolver conexión para server_id de la unidad (sin exponer secretos)")
        return

    print(f"[OK] Conexion canonica resuelta para unidad={unidad_codigo} (secretos NO impresos)")

    # 1) Volumen total movtosalmacen ultimos 30 dias
    q_total = """
        SELECT COUNT(*) AS n
        FROM movtosalmacen m
        WHERE m.fecha >= DATEADD(DAY,-30,GETDATE()) AND m.cancelado = 0
    """
    r = execute_sql_query(srv['host'], srv['port'], srv['database'], srv['username'], srv['password'], q_total)
    total = r[0]['n'] if r else 0
    print(f"[VOL] movtosalmacen ult.30d (cancelado=0): {total} filas")

    # 2) Conceptos distintos y su volumen
    q_conc = """
        SELECT RTRIM(LTRIM(m.idconcepto)) AS concepto, COUNT(*) AS n
        FROM movtosalmacen m
        WHERE m.fecha >= DATEADD(DAY,-30,GETDATE()) AND m.cancelado = 0
        GROUP BY RTRIM(LTRIM(m.idconcepto))
        ORDER BY COUNT(*) DESC
    """
    rc = execute_sql_query(srv['host'], srv['port'], srv['database'], srv['username'], srv['password'], q_conc)
    mapeados = 0
    no_mapeados = 0
    filas_mapeadas = 0
    filas_no_mapeadas = 0
    print("[CONCEPTOS] (concepto -> filas | mapeado?)")
    for row in (rc or []):
        c = (row['concepto'] or '').upper()
        n = row['n']
        en_dict = c in TIPO_MOVIMIENTO_SR_TO_EDARSAHUB
        if en_dict:
            mapeados += 1
            filas_mapeadas += n
        else:
            no_mapeados += 1
            filas_no_mapeadas += n
        print(f"   {c or '(vacio)'} -> {n} | {'SI' if en_dict else 'NO-MAPEADO'}")
    print(f"[FIDELIDAD] conceptos mapeados={mapeados} no_mapeados={no_mapeados}")
    print(f"[FIDELIDAD] filas conservadas con mapeo actual={filas_mapeadas} | filas PERDIDAS={filas_no_mapeadas}")

    # 3) Existe tabla conceptos con tipo/descripcion (clasificacion DB-driven en origen)?
    q_conc_tbl = "SELECT COUNT(*) AS n FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='conceptos'"
    rt = execute_sql_query(srv['host'], srv['port'], srv['database'], srv['username'], srv['password'], q_conc_tbl)
    print(f"[ORIGEN] tabla 'conceptos' presente en POS: {(rt[0]['n']>0) if rt else False}")

    # 4) Almacenes distintos
    q_alm = """
        SELECT COUNT(DISTINCT m.idalmacen) AS n
        FROM movtosalmacen m
        WHERE m.fecha >= DATEADD(DAY,-30,GETDATE()) AND m.cancelado = 0
    """
    ra = execute_sql_query(srv['host'], srv['port'], srv['database'], srv['username'], srv['password'], q_alm)
    print(f"[ALMACENES] distintos ult.30d: {ra[0]['n'] if ra else 0}")


if __name__ == "__main__":
    cod = sys.argv[1] if len(sys.argv) > 1 else "CIENFUEGOS"
    run(cod)
