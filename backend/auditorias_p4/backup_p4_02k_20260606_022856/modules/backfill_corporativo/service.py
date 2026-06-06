"""
P3-03 Backfill Corporativo Service - SQL-First
Re-sincronización histórica controlada.
NO usa conexiones LIVE para dashboards.
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
from core.config.edarsahub_sql import get_edarsahub_connection
import logging

logger = logging.getLogger(__name__)

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
    """Verifica si una tabla existe."""
    cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = %s
    """, (table,))
    row = cur.fetchone()
    return (row.get('cnt', 0) if isinstance(row, dict) else row[0]) > 0


def _get_columns(cur, table: str) -> set:
    """Obtiene las columnas de una tabla."""
    cur.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = %s
    """, (table,))
    result = set()
    for r in cur.fetchall():
        if isinstance(r, dict):
            result.add(r.get('COLUMN_NAME', ''))
        else:
            result.add(r[0] if r else '')
    return result


def _count_table(cur, table: str) -> int:
    """Cuenta registros totales de una tabla."""
    cur.execute(f"SELECT COUNT(*) AS total FROM {table}")
    row = cur.fetchone()
    return int(row.get('total', 0) if isinstance(row, dict) else row[0] or 0)


def _get_table_columns(cur, table: str) -> set:
    """Alias de _get_columns para compatibilidad."""
    return _get_columns(cur, table)


def _pick_col(cols: set, candidates: list) -> Optional[str]:
    """Selecciona la primera columna que coincide de una lista de candidatos."""
    for c in candidates:
        if c in cols:
            return c
    return None


def _get_server(cur, server_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene información del servidor."""
    cur.execute("""
        SELECT 
            CAST(id AS VARCHAR(100)) AS id,
            nombre,
            system_type,
            tipo_conexion,
            EmpresaID
        FROM Servidores_Conexiones
        WHERE CAST(id AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))
    """, (server_id,))
    row = cur.fetchone()
    if not row:
        return None
    if isinstance(row, dict):
        return row
    cols = ['id', 'nombre', 'system_type', 'tipo_conexion', 'EmpresaID']
    return dict(zip(cols, row))


def _log_backfill(cur, server_id: str, modulo: str, fecha_inicio: str, fecha_fin: str, status: str, registros: int, mensaje: str):
    """Registra el backfill en Compras_Sync_Log (tabla existente de control)."""
    try:
        cur.execute("""
            INSERT INTO Compras_Sync_Log (
                server_id,
                sync_type,
                sync_start,
                sync_end,
                status,
                records_synced,
                error_message
            ) VALUES (
                %s, %s, GETDATE(), GETDATE(), %s, %s, %s
            )
        """, (server_id, f"BACKFILL_{modulo}", status, registros, mensaje))
    except Exception as e:
        logger.warning(f"[BACKFILL] Error registrando log: {e}")


# =============================================================================
# BACKFILL VENTAS
# =============================================================================
def _backfill_ventas(cur, server_id: str, fecha_inicio: str, fecha_fin: str, dry_run: bool) -> Dict[str, Any]:
    """
    Backfill VENTAS (Comercial_KPIs_Diarios_v2).
    En modo DRY_RUN solo valida; en COMMIT registra control.
    """
    tabla = "Comercial_KPIs_Diarios_v2"
    
    if not _table_exists(cur, tabla):
        return {
            "success": False,
            "tabla": tabla,
            "error": "Tabla no existe",
            "insertados": 0,
            "actualizados": 0,
            "omitidos": 0,
        }
    
    server = _get_server(cur, server_id)
    if not server:
        return {
            "success": False,
            "tabla": tabla,
            "error": "Servidor no encontrado",
            "server_id": server_id,
            "insertados": 0,
            "actualizados": 0,
            "omitidos": 0,
        }
    
    cols = _get_columns(cur, tabla)
    fecha_col = next((c for c in ["fecha_operacion", "FechaOperacion", "fecha", "Fecha"] if c in cols), "fecha_operacion")
    server_col = next((c for c in ["server_id", "ServerID", "ServidorID", "servidor_id"] if c in cols), "server_id")
    
    # Contar registros en el rango
    cur.execute(f"""
        SELECT COUNT(*) AS total
        FROM {tabla}
        WHERE CAST({server_col} AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))
          AND CAST({fecha_col} AS DATE) >= %s
          AND CAST({fecha_col} AS DATE) <= %s
    """, (server_id, fecha_inicio, fecha_fin))
    row = cur.fetchone()
    total_rango = int(row.get('total', 0) if isinstance(row, dict) else row[0] or 0)
    
    # Obtener días con datos
    cur.execute(f"""
        SELECT
            CAST({fecha_col} AS DATE) AS fecha,
            COUNT(*) AS registros,
            SUM(ISNULL(ventas_total, 0)) AS venta_total
        FROM {tabla}
        WHERE CAST({server_col} AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))
          AND CAST({fecha_col} AS DATE) >= %s
          AND CAST({fecha_col} AS DATE) <= %s
        GROUP BY CAST({fecha_col} AS DATE)
        ORDER BY CAST({fecha_col} AS DATE)
    """, (server_id, fecha_inicio, fecha_fin))
    
    dias_con_data = []
    for r in cur.fetchall():
        if isinstance(r, dict):
            dias_con_data.append({
                "fecha": str(r.get('fecha', '')),
                "registros": int(r.get('registros', 0)),
                "venta_total": float(r.get('venta_total', 0) or 0)
            })
        else:
            dias_con_data.append({
                "fecha": str(r[0]),
                "registros": int(r[1] or 0),
                "venta_total": float(r[2] or 0)
            })
    
    if dry_run:
        return {
            "success": True,
            "tabla": tabla,
            "server": server,
            "modo": "DRY_RUN",
            "registros_actuales_rango": total_rango,
            "dias_con_data": dias_con_data,
            "insertados": 0,
            "actualizados": 0,
            "omitidos": total_rango,
            "message": "Dry-run VENTAS completado. No se insertó información."
        }
    
    # Modo COMMIT: registrar control
    status = "SUCCESS" if total_rango > 0 else "PENDING_SOURCE"
    msg = f"Backfill VENTAS validado: {total_rango} registros existentes." if total_rango > 0 else "No hay datos VENTAS en el rango."
    
    _log_backfill(cur, server_id, "VENTAS", fecha_inicio, fecha_fin, status, total_rango, msg)
    
    return {
        "success": True,
        "tabla": tabla,
        "server": server,
        "modo": "COMMIT_CONTROL",
        "registros_actuales_rango": total_rango,
        "dias_con_data": dias_con_data,
        "insertados": 0,
        "actualizados": 0,
        "omitidos": total_rango,
        "status": status,
        "message": msg
    }


# =============================================================================
# BACKFILL VENTAS_HORA
# =============================================================================
def _backfill_ventas_hora(cur, server_id: str, fecha_inicio: str, fecha_fin: str, dry_run: bool) -> Dict[str, Any]:
    """
    Backfill VENTAS_HORA (Sync_Ventas_PorHora).
    No consulta LIVE. Valida huecos por fecha/servidor.
    """
    tabla = "Sync_Ventas_PorHora"
    
    if not _table_exists(cur, tabla):
        return {
            "success": False,
            "tabla": tabla,
            "error": "Tabla Sync_Ventas_PorHora no existe",
            "insertados": 0,
            "actualizados": 0,
            "omitidos": 0,
        }
    
    server = _get_server(cur, server_id)
    if not server:
        return {
            "success": False,
            "tabla": tabla,
            "error": "Servidor no encontrado",
            "server_id": server_id,
            "insertados": 0,
            "actualizados": 0,
            "omitidos": 0,
        }
    
    cols = _get_columns(cur, tabla)
    fecha_col = next((c for c in ["fecha_operacion", "FechaOperacion", "fecha", "Fecha"] if c in cols), "fecha_operacion")
    server_col = next((c for c in ["server_id", "ServerID", "ServidorID", "servidor_id"] if c in cols), "server_id")
    
    # Contar registros en el rango
    cur.execute(f"""
        SELECT COUNT(*) AS total
        FROM {tabla}
        WHERE CAST({server_col} AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))
          AND CAST({fecha_col} AS DATE) >= %s
          AND CAST({fecha_col} AS DATE) <= %s
    """, (server_id, fecha_inicio, fecha_fin))
    row = cur.fetchone()
    total_rango = int(row.get('total', 0) if isinstance(row, dict) else row[0] or 0)
    
    # Obtener días con datos
    cur.execute(f"""
        SELECT
            CAST({fecha_col} AS DATE) AS fecha,
            COUNT(*) AS registros
        FROM {tabla}
        WHERE CAST({server_col} AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))
          AND CAST({fecha_col} AS DATE) >= %s
          AND CAST({fecha_col} AS DATE) <= %s
        GROUP BY CAST({fecha_col} AS DATE)
        ORDER BY CAST({fecha_col} AS DATE)
    """, (server_id, fecha_inicio, fecha_fin))
    
    dias_con_data = []
    for r in cur.fetchall():
        if isinstance(r, dict):
            dias_con_data.append({
                "fecha": str(r.get('fecha', '')),
                "registros": int(r.get('registros', 0))
            })
        else:
            dias_con_data.append({
                "fecha": str(r[0]),
                "registros": int(r[1] or 0)
            })
    
    if dry_run:
        return {
            "success": True,
            "tabla": tabla,
            "server": server,
            "modo": "DRY_RUN",
            "registros_actuales_rango": total_rango,
            "dias_con_data": dias_con_data,
            "insertados": 0,
            "actualizados": 0,
            "omitidos": total_rango,
            "message": "Dry-run VENTAS_HORA completado. No se insertó información."
        }
    
    # Modo COMMIT: registrar control
    status = "SUCCESS" if total_rango > 0 else "PENDING_SOURCE"
    msg = f"Backfill VENTAS_HORA validado: {total_rango} registros." if total_rango > 0 else "No hay datos VENTAS_HORA en el rango; pendiente fuente batch/sync."
    
    _log_backfill(cur, server_id, "VENTAS_HORA", fecha_inicio, fecha_fin, status, total_rango, msg)
    
    return {
        "success": True,
        "tabla": tabla,
        "server": server,
        "modo": "COMMIT_CONTROL",
        "registros_actuales_rango": total_rango,
        "dias_con_data": dias_con_data,
        "insertados": 0,
        "actualizados": 0,
        "omitidos": total_rango,
        "status": status,
        "message": msg
    }


# =============================================================================
# BACKFILL PRODUCTOS
# =============================================================================
def _backfill_productos(cur, server_id: str, fecha_inicio: str, fecha_fin: str, dry_run: bool) -> Dict[str, Any]:
    """Backfill PRODUCTOS (Sync_Productos)."""
    tabla = "Sync_Productos"
    server = _get_server(cur, server_id)

    if not server:
        return {"success": False, "tabla": tabla, "error": "Servidor no encontrado", "server_id": server_id}

    if not _table_exists(cur, tabla):
        return {"success": True, "tabla": tabla, "server": server, "existe": False, "registros": 0, "message": f"Tabla {tabla} no existe."}

    cols = _get_columns(cur, tabla)
    server_col = next((c for c in ["server_id", "ServerID", "ServidorID"] if c in cols), None)
    
    total = 0
    if server_col:
        cur.execute(f"SELECT COUNT(*) AS total FROM {tabla} WHERE CAST({server_col} AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))", (server_id,))
        row = cur.fetchone()
        total = int(row.get('total', 0) if isinstance(row, dict) else row[0] or 0)
    else:
        cur.execute(f"SELECT COUNT(*) AS total FROM {tabla}")
        row = cur.fetchone()
        total = int(row.get('total', 0) if isinstance(row, dict) else row[0] or 0)

    if dry_run:
        return {"success": True, "tabla": tabla, "server": server, "modo": "DRY_RUN", "existe": True, "registros": total, "message": "Dry-run PRODUCTOS completado."}

    status = "SUCCESS" if total > 0 else "PENDING_SOURCE"
    _log_backfill(cur, server_id, "PRODUCTOS", fecha_inicio, fecha_fin, status, total, f"Backfill PRODUCTOS: {total} registros.")
    return {"success": True, "tabla": tabla, "server": server, "modo": "COMMIT_CONTROL", "existe": True, "registros": total, "status": status}


# =============================================================================
# BACKFILL PRECIOS
# =============================================================================
def _backfill_precios(cur, server_id: str, fecha_inicio: str, fecha_fin: str, dry_run: bool) -> Dict[str, Any]:
    """Backfill PRECIOS (Sync_Precios_Historicos)."""
    tabla = "Sync_Precios_Historicos"
    server = _get_server(cur, server_id)

    if not server:
        return {"success": False, "tabla": tabla, "error": "Servidor no encontrado", "server_id": server_id}

    if not _table_exists(cur, tabla):
        return {"success": True, "tabla": tabla, "server": server, "existe": False, "registros": 0, "message": f"Tabla {tabla} no existe."}

    cols = _get_columns(cur, tabla)
    server_col = next((c for c in ["ServerID", "server_id", "ServidorID"] if c in cols), None)
    
    total = 0
    if server_col:
        cur.execute(f"SELECT COUNT(*) AS total FROM {tabla} WHERE CAST({server_col} AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))", (server_id,))
        row = cur.fetchone()
        total = int(row.get('total', 0) if isinstance(row, dict) else row[0] or 0)
    else:
        cur.execute(f"SELECT COUNT(*) AS total FROM {tabla}")
        row = cur.fetchone()
        total = int(row.get('total', 0) if isinstance(row, dict) else row[0] or 0)

    if dry_run:
        return {"success": True, "tabla": tabla, "server": server, "modo": "DRY_RUN", "existe": True, "registros": total, "message": "Dry-run PRECIOS completado."}

    status = "SUCCESS" if total > 0 else "PENDING_SOURCE"
    _log_backfill(cur, server_id, "PRECIOS", fecha_inicio, fecha_fin, status, total, f"Backfill PRECIOS: {total} registros.")
    return {"success": True, "tabla": tabla, "server": server, "modo": "COMMIT_CONTROL", "existe": True, "registros": total, "status": status}


# =============================================================================
# BACKFILL RECETAS
# =============================================================================
def _backfill_recetas(cur, server_id: str, fecha_inicio: str, fecha_fin: str, dry_run: bool) -> Dict[str, Any]:
    """Backfill RECETAS (Sync_Recetas)."""
    tabla = "Sync_Recetas"
    server = _get_server(cur, server_id)

    if not server:
        return {"success": False, "tabla": tabla, "error": "Servidor no encontrado", "server_id": server_id}

    if not _table_exists(cur, tabla):
        return {"success": True, "tabla": tabla, "server": server, "existe": False, "registros": 0, "message": f"Tabla {tabla} no existe."}

    cols = _get_columns(cur, tabla)
    server_col = next((c for c in ["server_id", "ServerID", "ServidorID"] if c in cols), None)
    
    total = 0
    if server_col:
        cur.execute(f"SELECT COUNT(*) AS total FROM {tabla} WHERE CAST({server_col} AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))", (server_id,))
        row = cur.fetchone()
        total = int(row.get('total', 0) if isinstance(row, dict) else row[0] or 0)
    else:
        cur.execute(f"SELECT COUNT(*) AS total FROM {tabla}")
        row = cur.fetchone()
        total = int(row.get('total', 0) if isinstance(row, dict) else row[0] or 0)

    if dry_run:
        return {"success": True, "tabla": tabla, "server": server, "modo": "DRY_RUN", "existe": True, "registros": total, "message": "Dry-run RECETAS completado."}

    status = "SUCCESS" if total > 0 else "PENDING_SOURCE"
    _log_backfill(cur, server_id, "RECETAS", fecha_inicio, fecha_fin, status, total, f"Backfill RECETAS: {total} registros.")
    return {"success": True, "tabla": tabla, "server": server, "modo": "COMMIT_CONTROL", "existe": True, "registros": total, "status": status}


# =============================================================================
# BACKFILL GENÉRICO (para módulos sin implementación específica)
# =============================================================================
def _backfill_generico(cur, modulo: str, server_id: str, fecha_inicio: str, fecha_fin: str, dry_run: bool) -> List[Dict[str, Any]]:
    """Backfill genérico: solo valida existencia y conteos."""
    tablas = TABLAS_MODULO.get(modulo, [])
    resultados = []
    
    server = _get_server(cur, server_id)
    
    for tabla in tablas:
        existe = _table_exists(cur, tabla)
        total = _count_table(cur, tabla) if existe else 0
        
        resultados.append({
            "tabla": tabla,
            "existe": existe,
            "total_actual": total,
            "accion": "VALIDAR_EXISTENCIA_Y_CONTEO",
            "dry_run": dry_run,
            "insertados": 0,
            "actualizados": 0,
            "omitidos": total,
            "server": server,
            "message": f"Módulo {modulo} sin implementación específica. Solo validación."
        })
    
    return resultados


# =============================================================================
# EJECUTAR BACKFILL (ENTRY POINT)
# =============================================================================

def _count_existing_table_records(cur, table: str, server_id: str, fecha_inicio: str, fecha_fin: str):
    if not _table_exists(cur, table):
        return {"tabla": table, "existe": False, "total": 0, "rango": 0, "server_col": None, "date_col": None}

    cols = _get_table_columns(cur, table)
    server_col = _pick_col(cols, ["server_id", "ServerID", "ServidorID", "servidor_id"])
    date_col = _pick_col(cols, ["FechaPedido", "FechaOrden", "FechaRecepcion", "Fecha", "fecha", "FechaCreacion", "FechaSync"])

    cur.execute(f"SELECT COUNT(*) AS cnt FROM {table}")
    row = cur.fetchone()
    total = int(row.get('cnt', 0) if isinstance(row, dict) else row[0] or 0)

    rango = total
    if date_col:
        if server_col:
            cur.execute(f"""
            SELECT COUNT(*) AS cnt
            FROM {table}
            WHERE CAST({server_col} AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))
              AND CAST({date_col} AS DATE) >= %s
              AND CAST({date_col} AS DATE) <= %s
            """, (server_id, fecha_inicio, fecha_fin))
        else:
            cur.execute(f"""
            SELECT COUNT(*) AS cnt
            FROM {table}
            WHERE CAST({date_col} AS DATE) >= %s
              AND CAST({date_col} AS DATE) <= %s
            """, (fecha_inicio, fecha_fin))
        row = cur.fetchone()
        rango = int(row.get('cnt', 0) if isinstance(row, dict) else row[0] or 0)

    return {
        "tabla": table,
        "existe": True,
        "total": total,
        "rango": rango,
        "server_col": server_col,
        "date_col": date_col,
    }

def _backfill_compras(cur, server_id: str, fecha_inicio: str, fecha_fin: str, dry_run: bool) -> Dict[str, Any]:
    server = _get_server(cur, server_id)
    if not server:
        return {"success": False, "modulo": "COMPRAS", "error": "Servidor no encontrado", "server_id": server_id}

    tablas = ["Compras_Pedidos", "Compras_PedidosDetalle", "Compras_Ordenes", "Compras_Recepciones"]
    stats = [_count_existing_table_records(cur, t, server_id, fecha_inicio, fecha_fin) for t in tablas]

    total_rango = sum(x.get("rango", 0) for x in stats if x.get("existe"))

    # Hallazgo específico: encabezados sin detalle y total cero.
    cur.execute("""
    SELECT COUNT(*) AS cnt
    FROM Compras_Pedidos p
    WHERE ISNULL(p.Total,0)=0
      AND NOT EXISTS (
          SELECT 1 FROM Compras_PedidosDetalle d
          WHERE d.PedidoCompraID = p.PedidoCompraID
      )
    """)
    row = cur.fetchone()
    encabezados_vacios = int(row.get('cnt', 0) if isinstance(row, dict) else row[0] or 0)

    if dry_run:
        return {
            "success": True,
            "modulo": "COMPRAS",
            "server": server,
            "modo": "DRY_RUN",
            "tablas": stats,
            "registros_rango": total_rango,
            "encabezados_sin_detalle_total_cero": encabezados_vacios,
            "insertados": 0,
            "actualizados": 0,
            "omitidos": total_rango,
            "message": "Dry-run COMPRAS completado. No se insertó información."
        }

    status = "SUCCESS" if total_rango > 0 and encabezados_vacios == 0 else "WARNING"
    msg = (
        "Backfill COMPRAS validado."
        if status == "SUCCESS"
        else f"COMPRAS requiere ejecución de job sync fuente. Encabezados vacíos: {encabezados_vacios}"
    )

    _log_backfill(cur, server_id, "COMPRAS", fecha_inicio, fecha_fin, status, total_rango, msg)

    return {
        "success": True,
        "modulo": "COMPRAS",
        "server": server,
        "modo": "COMMIT_CONTROL",
        "tablas": stats,
        "registros_rango": total_rango,
        "encabezados_sin_detalle_total_cero": encabezados_vacios,
        "insertados": 0,
        "actualizados": 0,
        "omitidos": total_rango,
        "status": status,
        "message": msg
    }

def _backfill_inventarios(cur, server_id: str, fecha_inicio: str, fecha_fin: str, dry_run: bool) -> Dict[str, Any]:
    server = _get_server(cur, server_id)
    if not server:
        return {"success": False, "modulo": "INVENTARIOS", "error": "Servidor no encontrado", "server_id": server_id}

    # Detectar tablas de inventarios existentes, sin inventar nombres.
    cur.execute("""
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE='BASE TABLE'
      AND TABLE_NAME LIKE '%Inventario%'
    ORDER BY TABLE_NAME
    """)
    raw_rows = cur.fetchall()
    tablas = []
    for r in raw_rows:
        if isinstance(r, dict):
            tablas.append(r.get('TABLE_NAME', ''))
        else:
            tablas.append(r[0] if r else '')

    stats = [_count_existing_table_records(cur, t, server_id, fecha_inicio, fecha_fin) for t in tablas if t]
    total_rango = sum(x.get("rango", 0) for x in stats if x.get("existe"))

    if dry_run:
        return {
            "success": True,
            "modulo": "INVENTARIOS",
            "server": server,
            "modo": "DRY_RUN",
            "tablas_detectadas": tablas,
            "tablas": stats,
            "registros_rango": total_rango,
            "insertados": 0,
            "actualizados": 0,
            "omitidos": total_rango,
            "message": "Dry-run INVENTARIOS completado. No se insertó información."
        }

    status = "SUCCESS" if total_rango > 0 else "PENDING_SOURCE"
    msg = "Backfill INVENTARIOS validado con datos existentes." if total_rango > 0 else "No hay inventarios en rango; pendiente fuente batch/sync."

    _log_backfill(cur, server_id, "INVENTARIOS", fecha_inicio, fecha_fin, status, total_rango, msg)

    return {
        "success": True,
        "modulo": "INVENTARIOS",
        "server": server,
        "modo": "COMMIT_CONTROL",
        "tablas_detectadas": tablas,
        "tablas": stats,
        "registros_rango": total_rango,
        "insertados": 0,
        "actualizados": 0,
        "omitidos": total_rango,
        "status": status,
        "message": msg
    }


def ejecutar_backfill(
    server_id: str,
    fecha_inicio: str,
    fecha_fin: str,
    modulo: str,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Ejecuta backfill para un módulo específico.
    
    Args:
        server_id: UUID del servidor
        fecha_inicio: Fecha inicio (YYYY-MM-DD)
        fecha_fin: Fecha fin (YYYY-MM-DD)
        modulo: VENTAS, VENTAS_HORA, PRODUCTOS, PRECIOS, RECETAS, COMPRAS, INVENTARIOS
        dry_run: Si True, solo valida sin modificar
    
    Returns:
        Dict con resultado del backfill
    """
    modulo = (modulo or "").upper().strip()
    
    if modulo not in MODULOS_VALIDOS:
        return {
            "success": False,
            "error": f"Módulo inválido: {modulo}",
            "modulos_validos": sorted(MODULOS_VALIDOS)
        }
    
    try:
        cn = get_edarsahub_connection(timeout=30)
        cur = cn.cursor()
        
        inicio = datetime.now()
        resultados: List[Dict[str, Any]] = []
        
        # Dispatch por módulo
        if modulo == "VENTAS":
            # Si dry_run=True solo valida; si dry_run=False ejecuta backfill real para faltantes/cero.
            if dry_run:
                resultados.append(_backfill_ventas(cur, server_id, fecha_inicio, fecha_fin, dry_run))
            else:
                resultados.append(_backfill_ventas_real(cur, server_id, fecha_inicio, fecha_fin, dry_run))
        elif modulo == "VENTAS_HORA":
            resultados.append(_backfill_ventas_hora(cur, server_id, fecha_inicio, fecha_fin, dry_run))
        elif modulo == "PRODUCTOS":
            resultados.append(_backfill_productos(cur, server_id, fecha_inicio, fecha_fin, dry_run))
        elif modulo == "PRECIOS":
            resultados.append(_backfill_precios(cur, server_id, fecha_inicio, fecha_fin, dry_run))
        elif modulo == "RECETAS":
            resultados.append(_backfill_recetas(cur, server_id, fecha_inicio, fecha_fin, dry_run))
        elif modulo == "COMPRAS":
            resultados.append(_backfill_compras(cur, server_id, fecha_inicio, fecha_fin, dry_run))
        elif modulo == "INVENTARIOS":
            resultados.append(_backfill_inventarios(cur, server_id, fecha_inicio, fecha_fin, dry_run))
        else:
            # Módulos sin implementación específica
            resultados = _backfill_generico(cur, modulo, server_id, fecha_inicio, fecha_fin, dry_run)
        
        if not dry_run:
            cn.commit()
        
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
            "duracion_segundos": round((fin - inicio).total_seconds(), 3),
            "resultados": resultados,
        }
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"[BACKFILL] Error en {modulo}: {e}\n{tb}")
        return {
            "success": False,
            "error": str(e) or repr(e),
            "traceback": tb,
            "modulo": modulo,
            "server_id": server_id,
        }

# P3-04 BACKFILL_VENTAS_REAL
# Regla:
# Si hay días faltantes o en cero, consultar fuente autorizada y sincronizar solo si hay datos reales.
# Este proceso pertenece a sincronización/backfill, NO a dashboard visual.

def _get_missing_or_zero_sales_days(cur, server_id: str, fecha_inicio: str, fecha_fin: str):
    cur.execute("""
    ;WITH fechas AS (
        SELECT CAST(%s AS DATE) AS fecha
        UNION ALL
        SELECT DATEADD(DAY, 1, fecha)
        FROM fechas
        WHERE fecha < CAST(%s AS DATE)
    )
    SELECT
        f.fecha,
        ISNULL(k.ventas_total, 0) AS ventas_total,
        ISNULL(k.tickets_total, 0) AS tickets_total,
        ISNULL(k.pax_total, 0) AS pax_total,
        CASE
            WHEN k.fecha_operacion IS NULL THEN 'FALTANTE'
            WHEN ISNULL(k.ventas_total,0)=0 AND ISNULL(k.tickets_total,0)=0 THEN 'CERO'
            ELSE 'OK'
        END AS estado
    FROM fechas f
    LEFT JOIN Comercial_KPIs_Diarios_v2 k
      ON k.fecha_operacion = f.fecha
     AND CAST(k.server_id AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))
    WHERE k.fecha_operacion IS NULL
       OR (ISNULL(k.ventas_total,0)=0 AND ISNULL(k.tickets_total,0)=0)
    OPTION (MAXRECURSION 0)
    """, (fecha_inicio, fecha_fin, server_id))

    rows = cur.fetchall()
    result = []
    for r in rows:
        if isinstance(r, dict):
            result.append(r)
        else:
            result.append({
                "fecha": r[0],
                "ventas_total": r[1],
                "tickets_total": r[2],
                "pax_total": r[3],
                "estado": r[4]
            })
    return result


def _get_source_connection_config(cur, server_id: str):
    cur.execute("""
    SELECT TOP 1 *
    FROM Servidores_Conexiones
    WHERE CAST(id AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))
      AND ISNULL(activo,1)=1
    """, (server_id,))
    row = cur.fetchone()
    return row if row else None


def _backfill_ventas_real(cur, server_id: str, fecha_inicio: str, fecha_fin: str, dry_run: bool):
    """
    Backfill real de ventas.
    Detecta faltantes/cero en EDARSAHUB.
    Si existe fuente autorizada y trae datos, actualiza Comercial_KPIs_Diarios_v2.
    """
    import pymssql
    from datetime import datetime

    faltantes = _get_missing_or_zero_sales_days(cur, server_id, fecha_inicio, fecha_fin)
    server = _get_source_connection_config(cur, server_id)

    if not server:
        return {
            "success": False,
            "modulo": "VENTAS",
            "error": "Servidor fuente no encontrado en Servidores_Conexiones",
            "server_id": server_id,
            "faltantes": len(faltantes) if faltantes else 0,
            "insertados": 0,
            "actualizados": 0
        }

    if not faltantes:
        _log_backfill(cur, server_id, "VENTAS_REAL", fecha_inicio, fecha_fin, "SUCCESS", 0, "Sin faltantes ni días en cero.")
        return {
            "success": True,
            "modulo": "VENTAS",
            "message": "No hay días faltantes ni en cero.",
            "faltantes": [],
            "insertados": 0,
            "actualizados": 0
        }

    system_type = str(server.get("system_type") or "").upper() if isinstance(server, dict) else ""
    source_results = []

    if dry_run:
        return {
            "success": True,
            "modulo": "VENTAS",
            "mode": "DRY_RUN",
            "server_id": server_id,
            "system_type": system_type,
            "dias_a_validar": [
                {
                    "fecha": str(x.get("fecha") if isinstance(x, dict) else x[0]),
                    "estado": x.get("estado") if isinstance(x, dict) else x[4]
                }
                for x in faltantes
            ],
            "message": "Dry-run: detectados días faltantes/cero. No se conectó a fuente ni se insertó."
        }

    # COMMIT: fuente autorizada
    # Nota: Las credenciales pueden estar encriptadas.
    # En esta versión simplificada, intentamos conexión directa.
    host = server.get("host") if isinstance(server, dict) else None
    port = server.get("port") if isinstance(server, dict) else 1433
    username = server.get("username") if isinstance(server, dict) else None
    password = server.get("password") if isinstance(server, dict) else None
    database_name = server.get("database_name") if isinstance(server, dict) else None

    if not host or not username or not database_name:
        _log_backfill(cur, server_id, "VENTAS_REAL", fecha_inicio, fecha_fin, "ERROR", 0, "Credenciales incompletas en servidor")
        return {
            "success": False,
            "modulo": "VENTAS",
            "error": "Credenciales incompletas en servidor fuente",
            "insertados": 0,
            "actualizados": 0
        }

    try:
        src = pymssql.connect(
            server=host,
            port=int(port or 1433),
            user=username,
            password=password,
            database=database_name,
            login_timeout=10,
            timeout=30
        )
        scur = src.cursor(as_dict=True)
    except Exception as e:
        _log_backfill(cur, server_id, "VENTAS_REAL", fecha_inicio, fecha_fin, "ERROR", 0, f"No conecta fuente: {e}")
        return {
            "success": False,
            "modulo": "VENTAS",
            "error": f"No conecta fuente: {e}",
            "insertados": 0,
            "actualizados": 0
        }

    insertados = 0
    actualizados = 0
    sin_datos = 0

    for d in faltantes:
        fecha = d.get("fecha") if isinstance(d, dict) else d[0]
        fecha_str = str(fecha)[:10]
        data = None

        try:
            if "SOFT" in system_type:
                scur.execute("""
                SELECT
                    CAST(t.apertura AS DATE) AS fecha,
                    SUM(ISNULL(c.total,0) - ISNULL(c.propina,0)) AS ventas_netas,
                    COUNT(*) AS num_cheques,
                    SUM(ISNULL(c.nopersonas,0)) AS pax
                FROM cheques c
                INNER JOIN turnos t ON t.idturno = c.idturno
                WHERE CAST(t.apertura AS DATE) = %s
                  AND ISNULL(c.cancelado,0)=0
                  AND ISNULL(c.total,0)>0
                GROUP BY CAST(t.apertura AS DATE)
                """, (fecha_str,))
                data = scur.fetchone()

            elif "MPRO" in system_type or "MANAGMENT" in system_type:
                scur.execute("""
                SELECT
                    CAST(VE.Vn_Fecha AS DATE) AS fecha,
                    SUM(ISNULL(VE.Vn_Precio_Neto_Importe,0)) AS ventas_netas,
                    COUNT(*) AS num_cheques,
                    SUM(ISNULL(C.Co_Personas,0)) AS pax
                FROM Venta_Encabezado VE
                LEFT JOIN Comanda C
                    ON C.Co_Folio = VE.Vn_Folio
                   AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
                WHERE CAST(VE.Vn_Fecha AS DATE) = %s
                  AND ISNULL(VE.Es_Cve_Estado,'') <> 'CA'
                  AND ISNULL(VE.Vn_Precio_Neto_Importe,0)>0
                GROUP BY CAST(VE.Vn_Fecha AS DATE)
                """, (fecha_str,))
                data = scur.fetchone()

            else:
                source_results.append({
                    "fecha": fecha_str,
                    "status": "UNSUPPORTED_SYSTEM",
                    "system_type": system_type
                })
                continue

        except Exception as e:
            source_results.append({
                "fecha": fecha_str,
                "status": "SOURCE_QUERY_ERROR",
                "error": str(e)[:200]
            })
            continue

        # data viene como tupla (fecha, ventas_netas, num_cheques, pax) por índice
        ventas_raw = data[1] if data else 0
        if not data or float(ventas_raw or 0) <= 0:
            sin_datos += 1
            source_results.append({
                "fecha": fecha_str,
                "status": "SIN_DATOS"
            })
            continue

        ventas = float(data[1] or 0)
        cheques = int(data[2] or 0)
        pax = int(data[3] or 0)
        ticket_promedio = ventas / cheques if cheques else 0

        cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM Comercial_KPIs_Diarios_v2
        WHERE CAST(server_id AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))
          AND fecha_operacion = %s
        """, (server_id, fecha_str))
        row = cur.fetchone()
        exists = (row.get('cnt', 0) if isinstance(row, dict) else row[0]) > 0

        if exists:
            cur.execute("""
            UPDATE Comercial_KPIs_Diarios_v2
            SET
                ventas_total = %s,
                tickets_total = %s,
                pax_total = %s,
                ticket_promedio = %s,
                source_status = 'BACKFILL_REAL',
                fecha_sync = GETDATE()
            WHERE CAST(server_id AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))
              AND fecha_operacion = %s
            """, (ventas, cheques, pax, ticket_promedio, server_id, fecha_str))
            actualizados += 1
        else:
            cur.execute("""
            INSERT INTO Comercial_KPIs_Diarios_v2 (
                server_id,
                fecha_operacion,
                ventas_total,
                tickets_total,
                pax_total,
                ticket_promedio,
                source_status,
                fecha_sync
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'BACKFILL_REAL', GETDATE())
            """, (server_id, fecha_str, ventas, cheques, pax, ticket_promedio))
            insertados += 1

        source_results.append({
            "fecha": fecha_str,
            "status": "SYNCED",
            "ventas_total": ventas,
            "tickets_total": cheques,
            "pax_total": pax
        })

    src.close()

    records = insertados + actualizados
    status = "SUCCESS" if records > 0 else "SIN_DATOS"
    msg = f"Backfill ventas real: insertados={insertados}, actualizados={actualizados}, sin_datos={sin_datos}"

    _log_backfill(cur, server_id, "VENTAS_REAL", fecha_inicio, fecha_fin, status, records, msg)

    return {
        "success": True,
        "modulo": "VENTAS",
        "mode": "COMMIT",
        "server_id": server_id,
        "system_type": system_type,
        "insertados": insertados,
        "actualizados": actualizados,
        "sin_datos": sin_datos,
        "resultados": source_results,
        "message": msg
    }
