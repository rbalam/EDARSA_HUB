"""
FASE A — Backfill del comentario MPRO (Fi_Comentario de la tabla POS `Fisico`)
hacia EDARSAHUB `Compras_Inventarios_Fisicos_Sync.comentario` (NO-LIVE).

- Idempotente: crea la columna `comentario` si no existe.
- Backfill por FOLIO (UPDATE), sin re-sync ni REPLACE → no perturba filas/estatus.
- Solo MPRO (SoftRestaurant no tiene ese campo → queda vacío, data-driven).
- Se corre en proceso separado: cualquier cooldown queda aislado del backend vivo.

Uso: PYTHONPATH=/app/backend python scripts/backfill_comentario_mpro.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")

from modules.compras.sync_service import get_edarsahub_connection
from core.server_registry import get_server_connection_info_with_secrets
from core.db import execute_sql_query

MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"


def _decrypt(server):
    # decrypt_server_secrets vive en server.py; lo importamos perezosamente
    from server import decrypt_server_secrets
    return decrypt_server_secrets(server)


def ensure_column():
    conn = get_edarsahub_connection()
    cur = conn.cursor()
    cur.execute("""
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'Compras_Inventarios_Fisicos_Sync' AND COLUMN_NAME = 'comentario'
        )
        ALTER TABLE Compras_Inventarios_Fisicos_Sync ADD comentario NVARCHAR(255) NULL
    """)
    conn.commit()
    conn.close()
    print("[OK] Columna 'comentario' asegurada (idempotente).")


def fetch_pos_comentarios():
    s = _decrypt(get_server_connection_info_with_secrets(MPRO_SERVER_ID))
    print(f"[POS] host={s['host']} db={s['database']}")
    q = """
        SELECT F.Fi_Folio as folio, MAX(F.Fi_Comentario) as comentario
        FROM Fisico F
        WHERE F.Fi_Fecha >= DATEADD(MONTH, -6, GETDATE())
        GROUP BY F.Fi_Folio
    """
    rows = execute_sql_query(s['host'], s['port'], s['database'], s['username'], s['password'], q, timeout_seconds=60) or []
    mapping = {}
    for r in rows:
        folio = str(r.get('folio') or '').strip()
        com = (r.get('comentario') or '').strip()
        if folio:
            mapping[folio] = com
    print(f"[POS] folios leídos: {len(mapping)} | con comentario no vacío: {sum(1 for v in mapping.values() if v)}")
    return mapping


def backfill(mapping):
    conn = get_edarsahub_connection()
    cur = conn.cursor()
    updated = 0
    for folio, com in mapping.items():
        if not com:
            continue
        cur.execute("""
            UPDATE Compras_Inventarios_Fisicos_Sync
            SET comentario = %s
            WHERE LOWER(server_id) = LOWER(%s) AND folio = %s
              AND (comentario IS NULL OR comentario = '')
        """, (com[:255], MPRO_SERVER_ID, folio))
        updated += cur.rowcount or 0
    conn.commit()
    cur.execute("""
        SELECT COUNT(*) FROM Compras_Inventarios_Fisicos_Sync
        WHERE LOWER(server_id) = LOWER(%s) AND comentario IS NOT NULL AND comentario <> ''
    """, (MPRO_SERVER_ID,))
    total_con_com = cur.fetchone()[0]
    conn.close()
    print(f"[OK] Filas actualizadas: {updated} | total MPRO con comentario ahora: {total_con_com}")


if __name__ == "__main__":
    ensure_column()
    mapping = fetch_pos_comentarios()
    backfill(mapping)
    print("[DONE] Backfill comentario MPRO completado.")
