"""
Migración idempotente — Retiro del turno LEGACY 'COMIDA_CENA'
=============================================================
Fecha: 2026-06-10

CONTEXTO:
    La tabla `Sistema_TurnosOperativosUnidad` contiene por unidad los turnos
    canónicos DESAYUNO / COMIDA / CENA (aplica_ventas_dia=1) MÁS un turno
    duplicado y obsoleto 'COMIDA_CENA' (aplica_ventas_dia=0) etiquetado como
    "Comida/Cena (LEGACY)". Ese turno legacy:
      - NO lo usa el motor canónico (`operational_window` filtra aplica_ventas_dia=1).
      - Solo causa ruido visual (4ª tarjeta duplicada) en la pantalla de
        Configuración Operativa.

ACCIÓN (autorizada por el usuario):
    Eliminar las filas con turno_codigo = 'COMIDA_CENA'. Antes de borrar se
    imprime un respaldo JSON de las filas (reversible re-insertando).

IDEMPOTENTE: si no hay filas legacy, no hace nada.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from core.sql_first.db import get_sql_connection

LEGACY_CODE = 'COMIDA_CENA'


def main():
    conn = get_sql_connection()
    cur = conn.cursor()

    # 1) Respaldo de las filas que se eliminarán
    cur.execute("""
        SELECT CAST(id AS VARCHAR(50)) AS id, unidad_negocio_id, turno_codigo, turno_nombre,
               CAST(hora_inicio AS VARCHAR(8)) AS hora_inicio, CAST(hora_fin AS VARCHAR(8)) AS hora_fin,
               cruza_medianoche, aplica_ventas_dia, es_turno_principal, orden, activo
        FROM Sistema_TurnosOperativosUnidad
        WHERE turno_codigo = %s
        ORDER BY unidad_negocio_id
    """, (LEGACY_CODE,))
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    print(f"[MIGRACION] Filas LEGACY '{LEGACY_CODE}' encontradas: {len(rows)}")
    if rows:
        print("[MIGRACION] RESPALDO (JSON):")
        print(json.dumps(rows, default=str, ensure_ascii=False, indent=2))

    if not rows:
        print("[MIGRACION] Nada que eliminar. Idempotente OK.")
        conn.close()
        return

    # 2) DELETE
    cur.execute(
        "DELETE FROM Sistema_TurnosOperativosUnidad WHERE turno_codigo = %s",
        (LEGACY_CODE,)
    )
    conn.commit()
    print(f"[MIGRACION] Eliminadas {cur.rowcount} filas legacy.")

    # 3) Verificación post-delete: turnos por unidad
    cur.execute("""
        SELECT unidad_negocio_id, COUNT(*) AS total
        FROM Sistema_TurnosOperativosUnidad
        GROUP BY unidad_negocio_id
        ORDER BY unidad_negocio_id
    """)
    for r in cur.fetchall():
        print(f"  {r[0]:>10}: {r[1]} turnos restantes")

    conn.close()
    print("[MIGRACION] Completado.")


if __name__ == '__main__':
    main()
