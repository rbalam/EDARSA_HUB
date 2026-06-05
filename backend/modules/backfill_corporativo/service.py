from datetime import datetime
from typing import Dict, Any, List
from core.config.edarsahub_sql import get_edarsahub_connection

MODULOS_VALIDOS = {
    "VENTAS",
    "VENTAS_HORA",
    "PRODUCTOS",
    "PRECIOS",
    "RECETAS",
    "COMPRAS",
    "INVENTARIOS",
}

TABLAS_MODULO = {
    "VENTAS": ["Comercial_KPIs_Diarios_v2"],
    "VENTAS_HORA": ["Sync_Ventas_PorHora"],
    "PRODUCTOS": ["Sync_Productos"],
    "PRECIOS": ["Sync_Precios_Historicos"],
    "RECETAS": ["Sync_Recetas"],
    "COMPRAS": ["Compras_Pedidos", "Compras_PedidosDetalle", "Compras_Ordenes", "Compras_Recepciones"],
    "INVENTARIOS": ["Inventarios", "Inventarios_Detalle", "Inventarios_Fisicos"],
}

def _table_exists(cur, table: str) -> bool:
    cur.execute("""
    SELECT COUNT(*) AS cnt
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME = %s
    """, (table,))
    row = cur.fetchone()
    return row['cnt'] > 0 if isinstance(row, dict) else row[0] > 0

def _count_table(cur, table: str, server_id: str = "", fecha_inicio: str = "", fecha_fin: str = "") -> int:
    cur.execute(f"SELECT COUNT(*) AS total FROM {table}")
    row = cur.fetchone()
    return int(row['total'] if isinstance(row, dict) else row[0] or 0)

def ejecutar_backfill(
    server_id: str,
    fecha_inicio: str,
    fecha_fin: str,
    modulo: str,
    dry_run: bool = True
) -> Dict[str, Any]:
    modulo = (modulo or "").upper().strip()

    if modulo not in MODULOS_VALIDOS:
        return {
            "success": False,
            "error": f"Modulo inválido: {modulo}",
            "modulos_validos": sorted(MODULOS_VALIDOS)
        }

    cn = get_edarsahub_connection(timeout=30)
    cur = cn.cursor()

    inicio = datetime.now()
    tablas = TABLAS_MODULO.get(modulo, [])

    resultados: List[Dict[str, Any]] = []

    for tabla in tablas:
        existe = _table_exists(cur, tabla)
        total_actual = _count_table(cur, tabla) if existe else 0

        resultados.append({
            "tabla": tabla,
            "existe": existe,
            "total_actual": total_actual,
            "accion": "VALIDAR_EXISTENCIA_Y_CONTEO",
            "dry_run": dry_run,
            "insertados": 0,
            "actualizados": 0,
            "omitidos": 0
        })

    fin = datetime.now()

    cn.close()

    return {
        "success": True,
        "source": "EDARSAHUB_SQL",
        "mode": "DRY_RUN" if dry_run else "COMMIT",
        "server_id": server_id,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "modulo": modulo,
        "inicio": inicio.isoformat(),
        "fin": fin.isoformat(),
        "duracion_segundos": (fin - inicio).total_seconds(),
        "resultados": resultados,
        "message": "Backfill base creado. En esta fase solo valida tablas/conteos; no ejecuta conexiones live."
    }
