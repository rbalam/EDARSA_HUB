"""
EDARSA HUB - Job: Sincronización Inteligencia Comercial
=======================================================
LEGACY DESHABILITADO COMO ESCRITOR: Inteligencia Comercial solo debe leer EDARSAHUB SQL canonico.

Sistemas origen:
- SoftRestaurant: 130MID, CIENFUEGOS, ESTELAR
- MPRO: 130QRO, ORIGEN

Tablas destino en EDARSAHUB:
- Sync_Sales (detalle de transacciones con items JSON)
- Comercial_KPIs_Diarios_v2 (PROHIBIDO escribir desde este job legacy)
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
from core.config.edarsahub_config import get_edarsahub_sql_config
from core.sql_first.connection_factory import (
    get_external_sql_connection,
)
from core.sql_first.db import (
    execute_sql,
    fetch_all_dict,
    get_sql_connection,
)
_edarsa_cfg = get_edarsahub_sql_config()


logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

EDARSAHUB_CONFIG = {
    "host": _edarsa_cfg.host,
    "port": _edarsa_cfg.port,
    "database": _edarsa_cfg.database,
    "user": _edarsa_cfg.user,
    "password": _edarsa_cfg.password,
}

# ============================================================================
# DEPRECATED (P1B 2026-06): UNIDADES_CONFIG hardcodeado eliminado del flujo.
# Fuente canónica única: dbo.Unidades_Negocio + dbo.Servidores_Conexiones,
# resuelto vía modules.comercial_v2.sync_comercial_edarsahub.get_server_connection_config
# (ver helpers get_unidades_negocio_pos / get_pos_config_for_unidad más abajo).
# Se conserva como dict vacío solo por compatibilidad de referencias legacy.
# ============================================================================
UNIDADES_CONFIG = {}


# ============================================================================
# FUNCIONES DE CONEXIÓN
# ============================================================================

def get_edarsahub_connection():
    """Conexión a EDARSAHUB (destino)."""
    return get_sql_connection()


def get_pos_connection(
    config: Dict,
) -> Optional[Any]:
    """
    Abre una conexión POS mediante el factory externo centralizado.

    La configuración debe haber sido resuelta desde la relación canónica
    Unidades_Negocio.server_id -> Servidores_Conexiones.id.
    """
    required = [
        "host",
        "database",
        "username",
        "password",
    ]
    missing = [
        key
        for key in required
        if not config.get(key)
    ]

    if missing:
        logger.error(
            "[SYNC] Config POS incompleta "
            "(host=%s); faltan/vacíos=%s. "
            "No se intenta conexión.",
            config.get("host"),
            missing,
        )
        return None

    connection_config = dict(config)
    connection_config.setdefault(
        "login_timeout",
        15,
    )
    connection_config.setdefault(
        "timeout",
        180,
    )
    connection_config.setdefault(
        "tds_version",
        "7.0",
    )
    connection_config.setdefault(
        "as_dict",
        True,
    )

    try:
        return get_external_sql_connection(
            connection_config
        )
    except Exception as exc:
        logger.error(
            "[SYNC] Error conectando a POS "
            "host=%s db=%s: %s",
            config.get("host"),
            config.get("database"),
            exc,
        )
        return None


# ============================================================================
# QUERIES DE EXTRACCIÓN POR SISTEMA
# ============================================================================

def get_softrestaurant_query(fecha_inicio: str, fecha_fin: str) -> str:
    """Query para extraer ventas de SoftRestaurant."""
    return f"""
    SELECT 
        CONVERT(VARCHAR(64), ch.folio) AS NumeroTicket,
        CONVERT(VARCHAR(64), NEWID()) AS IdTransaccion,
        ch.nopersonas AS Pax,
        ch.total AS MontoTotal,
        t.apertura AS FechaHora,
        'COMPLETED' AS status,
        (
            SELECT 
                p.idproducto AS id,
                p.descripcion AS name,
                dc.cantidad AS quantity,
                dc.precio AS price,
                (dc.cantidad * dc.precio) AS total
            FROM cheqdet dc
            INNER JOIN productos p ON dc.idproducto = p.idproducto
            WHERE dc.foliodet = ch.folio
            FOR JSON PATH
        ) AS items
    FROM cheques ch
    INNER JOIN turnos t ON t.idturno = ch.idturno
    WHERE t.apertura >= '{fecha_inicio}'
      AND t.apertura < '{fecha_fin}'
      AND ch.cancelado = 0
      AND ch.total > 0
    ORDER BY t.apertura DESC
    """


def get_mpro_query(fecha_inicio: str, fecha_fin: str) -> str:
    """Query para extraer ventas de MPRO (ManagmentPro)."""
    return f"""
    SELECT 
        CONVERT(VARCHAR(64), v.Vn_Folio) AS NumeroTicket,
        CONVERT(VARCHAR(64), NEWID()) AS IdTransaccion,
        ISNULL(c.Co_Personas, 1) AS Pax,
        v.Vn_Precio_Neto_Importe AS MontoTotal,
        v.Vn_Fecha AS FechaHora,
        CASE WHEN v.Es_Cve_Estado = 'CA' THEN 'CANCELLED' ELSE 'COMPLETED' END AS status,
        (
            SELECT 
                d.Ar_Cve_Articulo AS id,
                a.Ar_Descripcion AS name,
                d.Vd_Cantidad AS quantity,
                d.Vd_Precio_Unitario AS price,
                d.Vd_Importe AS total
            FROM Venta_Detalle d
            LEFT JOIN Articulo a ON d.Ar_Cve_Articulo = a.Ar_Cve_Articulo
            WHERE d.Vn_Folio = v.Vn_Folio 
              AND d.Sc_Cve_Sucursal = v.Sc_Cve_Sucursal
            FOR JSON PATH
        ) AS items
    FROM Venta_Encabezado v
    LEFT JOIN Comanda c ON c.Co_Folio = v.Vn_Folio AND c.Sc_Cve_Sucursal = v.Sc_Cve_Sucursal
    WHERE v.Vn_Fecha >= '{fecha_inicio}'
      AND v.Vn_Fecha < '{fecha_fin}'
      AND ISNULL(v.Es_Cve_Estado, '') <> 'CA'
      AND v.Vn_Precio_Neto_Importe > 0
    ORDER BY v.Vn_Fecha DESC
    """


# ============================================================================
# FUNCIONES DE SINCRONIZACIÓN
# ============================================================================

def extract_sales_from_pos(
    unidad: str, 
    config: Dict, 
    fecha_inicio: str, 
    fecha_fin: str
) -> List[Dict]:
    """Extrae ventas de un POS específico."""
    
    conn = get_pos_connection(config)
    if not conn:
        logger.warning(f"[SYNC] No se pudo conectar a {unidad}")
        return []
    
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Seleccionar query según sistema
        if config["system_type"] == "SoftRestaurant":
            query = get_softrestaurant_query(fecha_inicio, fecha_fin)
        else:  # MPRO
            query = get_mpro_query(fecha_inicio, fecha_fin)
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Agregar unidad de negocio a cada registro
        for row in rows:
            row["UnidadNegocio"] = unidad
        
        logger.info(f"[SYNC] {unidad}: {len(rows)} registros extraídos")
        
        cursor.close()
        conn.close()
        
        return rows
        
    except Exception as e:
        logger.error(f"[SYNC] Error extrayendo de {unidad}: {e}")
        return []


def insert_into_sync_sales(conn, sales: List[Dict]) -> int:
    """Inserta registros en Sync_Sales."""
    if not sales:
        return 0
    
    cursor = conn.cursor()
    inserted = 0
    
    for sale in sales:
        try:
            # Verificar si ya existe (por NumeroTicket + UnidadNegocio + FechaHora)
            cursor.execute("""
                SELECT COUNT(*) FROM Sync_Sales 
                WHERE NumeroTicket = %s AND UnidadNegocio = %s 
                  AND CAST(FechaHora AS DATE) = CAST(%s AS DATE)
            """, (sale["NumeroTicket"], sale["UnidadNegocio"], sale["FechaHora"]))
            
            if cursor.fetchone()[0] > 0:
                continue  # Ya existe, skip
            
            # Insertar nuevo registro
            cursor.execute("""
                INSERT INTO Sync_Sales (
                    id, branch, UnidadNegocio, NumeroTicket, 
                    MontoTotal, Pax, FechaHora, status, items,
                    created_at, total
                ) VALUES (
                    %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s,
                    GETDATE(), %s
                )
            """, (
                sale.get("IdTransaccion", str(datetime.now().timestamp())),
                sale["UnidadNegocio"],
                sale["UnidadNegocio"],
                sale["NumeroTicket"],
                sale["MontoTotal"],
                sale["Pax"],
                sale["FechaHora"],
                sale.get("status", "COMPLETED"),
                sale.get("items", "[]"),
                sale["MontoTotal"]
            ))
            
            inserted += 1
            
        except Exception as e:
            logger.warning(f"[SYNC] Error insertando ticket {sale.get('NumeroTicket')}: {e}")
    
    cursor.close()
    return inserted


def update_kpis_diarios(conn, unidad: str, fecha: str) -> bool:
    """Actualiza/inserta KPIs diarios para una unidad y fecha."""
    cursor = conn.cursor(as_dict=True)
    
    try:
        # Calcular KPIs desde Sync_Sales
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT NumeroTicket) AS tickets,
                SUM(MontoTotal) AS ventas,
                SUM(Pax) AS Pax
            FROM Sync_Sales
            WHERE UnidadNegocio = %s
              AND CAST(FechaHora AS DATE) = %s
              AND status = 'COMPLETED'
        """, (unidad, fecha))
        
        kpis = cursor.fetchone()
        
        if not kpis or not kpis["ventas"]:
            return False
        
        # Verificar si ya existe registro
        cursor.execute("""
            SELECT id FROM Comercial_KPIs_Diarios_v2
            WHERE unidad_negocio_nombre = %s AND fecha_operacion = %s
        """, (unidad, fecha))
        
        existing = cursor.fetchone()
        
        if existing:
            # Actualizar
            cursor.execute("""
                UPDATE Comercial_KPIs_Diarios_v2
                SET ventas_total = %s,
                    pax_total = %s,
                    tickets_total = %s,
                    ticket_promedio = CASE WHEN %s > 0 THEN %s / %s ELSE 0 END,
                    fecha_ultima_actualizacion = GETDATE()
                WHERE id = %s
            """, (
                kpis["ventas"], kpis["pax"], kpis["tickets"],
                kpis["tickets"], kpis["ventas"], kpis["tickets"],
                existing["id"]
            ))
        else:
            # Insertar nuevo
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
            cursor.execute("""
                INSERT INTO Comercial_KPIs_Diarios_v2 (
                    id, unidad_negocio_id, unidad_negocio_nombre,
                    server_id, sucursal_id, sistema_origen,
                    fecha_operacion, anio, mes, dia,
                    ventas_total, pax_total, tickets_total, ticket_promedio,
                    activo, fuente_original, fecha_alta
                ) VALUES (
                    NEWID(), %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    1, 'SYNC_JOB', GETDATE()
                )
            """, (
                unidad, unidad,
                unidad, unidad, "SYNC_JOB",
                fecha, fecha_dt.year, fecha_dt.month, fecha_dt.day,
                kpis["ventas"], kpis["pax"], kpis["tickets"],
                kpis["ventas"] / kpis["tickets"] if kpis["tickets"] > 0 else 0
            ))
        
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"[SYNC] Error actualizando KPIs para {unidad}/{fecha}: {e}")
        cursor.close()
        return False


def update_job_status(conn, status: str = "ACTIVE"):
    """Actualiza el estado del job en Sys_Scheduler_Jobs."""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Sys_Scheduler_Jobs 
        SET LastRunDate = GETDATE(), Status = %s 
        WHERE JobName = 'inteligencia_comercial_sync'
    """, (status,))
    cursor.close()


# ============================================================================
# P1B - Sync POS canónico configurable (SQL-First, NO-LIVE seguro por defecto)
# Fuente canónica: dbo.Unidades_Negocio + dbo.Servidores_Conexiones
# Reúsa: modules.comercial_v2.sync_comercial_edarsahub.get_server_connection_config
# Control de ejecución: dbo.Sistema_SyncPOS_Config (Habilitado / PermitirPOSAutomatico)
# NO imprime secretos. NO conecta al POS salvo ejecución MANUAL autorizada.
# ============================================================================

def _syncpos_literal(value):
    """Literal NVARCHAR seguro para SQL (escapa comillas). NULL si es None."""
    if value is None:
        return "NULL"
    return "N'" + str(value).replace("'", "''") + "'"


def get_syncpos_config() -> Dict[str, Any]:
    """Lee la configuración de control del sync POS desde SQL.
    Si la tabla no existe o falla, devuelve defaults en MODO SEGURO (deshabilitado)."""
    try:
        rows = fetch_all_dict(
            "SELECT TOP 1 * FROM dbo.Sistema_SyncPOS_Config "
            "WHERE Codigo='INTELIGENCIA_COMERCIAL_POS' AND ISNULL(Activo,1)=1"
        )
    except Exception as e:
        logger.warning(f"[SYNCPOS] No se pudo leer config (modo seguro): {e}")
        rows = []
    if not rows:
        return {
            "Habilitado": False,
            "PermitirPOSAutomatico": False,
            "FrecuenciaMinutos": 60,
            "DiasAtrasAutomatico": 2,
            "DiasRevisionFaltantes": 14,
            "BackfillAutomaticoHabilitado": False,
            "MaxDiasBackfillPorCorrida": 1,
            "MaxUnidadesPorCorrida": 5,
        }
    return rows[0]


def should_run_syncpos_now(config: Optional[Dict] = None):
    """Decide si el job AUTO debe correr ahora según la config SQL."""
    cfg = config or get_syncpos_config()
    if not bool(cfg.get("Habilitado")):
        return False, "Sync POS deshabilitado por configuración SQL (Habilitado=0)"
    if not bool(cfg.get("PermitirPOSAutomatico")):
        return False, "Conexión POS automática deshabilitada por configuración SQL (PermitirPOSAutomatico=0)"
    last = cfg.get("FechaUltimaEjecucion")
    freq = int(cfg.get("FrecuenciaMinutos") or 60)
    if not last:
        return True, "Sin ejecución previa"
    try:
        delta = datetime.utcnow() - last
        if delta.total_seconds() >= freq * 60:
            return True, "Frecuencia cumplida"
        faltan = int((freq * 60 - delta.total_seconds()) / 60)
        return False, f"Frecuencia no cumplida: faltan aprox {faltan} min"
    except Exception:
        return True, "No se pudo evaluar frecuencia; se permite ejecución"


def get_unidades_negocio_pos(unidades: Optional[List[str]] = None) -> List[Dict]:
    """Unidades activas desde SQL canónico (NO usa UNIDADES_CONFIG)."""
    filters = ["ISNULL(u.activo,1)=1", "u.server_id IS NOT NULL"]
    if unidades:
        safe = ",".join(_syncpos_literal(u) for u in unidades)
        filters.append(
            f"(CONVERT(NVARCHAR(100), u.codigo) IN ({safe}) "
            f"OR CONVERT(NVARCHAR(100), u.id) IN ({safe}) "
            f"OR CONVERT(NVARCHAR(300), u.nombre) IN ({safe}))"
        )
    where_sql = " AND ".join(filters)
    return fetch_all_dict(f"""
        SELECT
            CONVERT(NVARCHAR(100), u.id) AS unidad_pk,
            CONVERT(NVARCHAR(100), u.codigo) AS unidad_codigo,
            CONVERT(NVARCHAR(300), u.nombre) AS unidad_nombre,
            CONVERT(NVARCHAR(100), u.server_id) AS server_id,
            CONVERT(NVARCHAR(100), u.sucursal_origen_id) AS sucursal_origen_id,
            CONVERT(NVARCHAR(100), u.system_type) AS system_type
        FROM dbo.Unidades_Negocio u
        WHERE {where_sql}
        ORDER BY u.codigo
    """)


def get_pos_config_for_unidad(unidad_row: Optional[Dict]) -> Optional[Dict]:
    """Resuelve la config POS reusando el helper canónico Comercial V2.
    NO duplica desencriptado. Import perezoso para evitar conexiones colaterales."""
    if not unidad_row:
        return None
    server_id = unidad_row.get("server_id")
    if not server_id:
        return None
    from modules.comercial_v2.sync_comercial_edarsahub import get_server_connection_config
    cfg = get_server_connection_config(
        server_id,
        unidad_negocio_pk=unidad_row.get("unidad_pk"),
    )
    if not cfg:
        return None
    return {
        "unidad": unidad_row.get("unidad_codigo") or unidad_row.get("unidad_pk"),
        "unidad_codigo": unidad_row.get("unidad_codigo"),
        "unidad_nombre": unidad_row.get("unidad_nombre"),
        "unidad_pk": unidad_row.get("unidad_pk"),
        "sucursal_origen_id": unidad_row.get("sucursal_origen_id"),
        "server_id": server_id,
        "system_type": unidad_row.get("system_type") or cfg.get("system_type"),
        "host": cfg.get("host"),
        "port": int(cfg.get("port") or 1433),
        "database": cfg.get("database_name") or cfg.get("database"),
        "username": cfg.get("username"),
        "password": cfg.get("password"),
        "source": "SQL_CANONICO_COMERCIAL_V2_HELPER",
    }


def audit_syncpos_canonical_configs(unidades: Optional[List[str]] = None) -> List[Dict]:
    """Auditoría segura: NUNCA expone password (solo has_password bool)."""
    result = []
    for unidad in get_unidades_negocio_pos(unidades):
        cfg = get_pos_config_for_unidad(unidad)
        result.append({
            "unidad": unidad.get("unidad_codigo"),
            "unidad_nombre": unidad.get("unidad_nombre"),
            "server_id": unidad.get("server_id"),
            "system_type": unidad.get("system_type"),
            "sucursal_origen_id": unidad.get("sucursal_origen_id"),
            "resolved": bool(cfg),
            "host": cfg.get("host") if cfg else None,
            "port": cfg.get("port") if cfg else None,
            "database": cfg.get("database") if cfg else None,
            "username": cfg.get("username") if cfg else None,
            "has_password": bool(cfg.get("password")) if cfg else False,
            "source": cfg.get("source") if cfg else None,
        })
    return result


def detectar_faltantes_syncpos(unidades: Optional[List[str]] = None) -> Dict[str, Any]:
    """P1B: detección de faltantes DIFERIDA por decisión del usuario.
    La tabla final de detalle de producto NO está definida (Venta_Detalle.PIC_* NO existe;
    Sync_Sales es solo staging/control). NO se asume cobertura ni se inventan faltantes."""
    try:
        unidades_consultadas = [u.get("unidad_codigo") for u in get_unidades_negocio_pos(unidades)]
    except Exception:
        unidades_consultadas = []
    return {
        "status": "SIN_DETALLE_HISTORICO_DISPONIBLE",
        "nota": ("Detección de faltantes pendiente de definir tabla final de detalle de producto "
                 "(Venta_Detalle vs Comercial_Inteligencia_VentasDetalleProducto). "
                 "Sync_Sales es solo staging/control, no fuente gerencial final."),
        "unidades_consultadas": unidades_consultadas,
    }


def registrar_syncpos_bitacora(tipo, estado, mensaje=None, unidad=None, fecha_inicio=None,
                               fecha_fin=None, tickets=None, lineas=None, venta=None):
    """Registra una entrada en la bitácora de sync (no-fatal)."""
    try:
        execute_sql(f"""
            INSERT INTO dbo.Sistema_SyncPOS_Bitacora (
                TipoEjecucion, UnidadNegocioID, FechaInicio, FechaFin,
                Estado, Mensaje, Tickets, Lineas, Venta, FechaFinEjecucion
            ) VALUES (
                {_syncpos_literal(tipo)}, {_syncpos_literal(unidad)},
                TRY_CONVERT(date,{_syncpos_literal(fecha_inicio)}),
                TRY_CONVERT(date,{_syncpos_literal(fecha_fin)}),
                {_syncpos_literal(estado)}, {_syncpos_literal(mensaje)},
                {tickets if tickets is not None else "NULL"},
                {lineas if lineas is not None else "NULL"},
                {venta if venta is not None else "NULL"},
                SYSUTCDATETIME()
            )
        """)
    except Exception as e:
        logger.warning(f"[SYNCPOS] No se pudo registrar bitácora: {e}")


def actualizar_syncpos_config_estado(estado, mensaje=None):
    """Actualiza el estado/última ejecución de la config (no-fatal)."""
    try:
        execute_sql(f"""
            UPDATE dbo.Sistema_SyncPOS_Config
            SET FechaUltimaEjecucion = SYSUTCDATETIME(),
                FechaSiguienteEjecucion = DATEADD(MINUTE, ISNULL(FrecuenciaMinutos,60), SYSUTCDATETIME()),
                EstadoUltimaEjecucion = {_syncpos_literal(estado)},
                MensajeUltimaEjecucion = {_syncpos_literal(mensaje)},
                FechaActualizacion = SYSUTCDATETIME()
            WHERE Codigo='INTELIGENCIA_COMERCIAL_POS'
        """)
    except Exception as e:
        logger.warning(f"[SYNCPOS] No se pudo actualizar estado config: {e}")


# ============================================================================
# FUNCIÓN PRINCIPAL DEL JOB
# ============================================================================

def job_inteligencia_comercial_sync(
    dias_atras: int = 1,
    unidades: List[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    dry_run: bool = False,
    tipo_ejecucion: str = "AUTO"
) -> Dict[str, Any]:
    """
    Job principal de sincronización de Inteligencia Comercial.
    
    Args:
        dias_atras: Cuántos días hacia atrás sincronizar (default: 1)
        unidades: Lista de unidades a sincronizar (default: todas)
    
    Returns:
        Dict con estadísticas de la ejecución
    """
    logger.info("[INTELIGENCIA_SYNC] ========== INICIO ==========")

    # GUARDRAIL CANONICO EDARSAHUB COMERCIAL:
    # Inteligencia Comercial NO es escritor de ventas/KPIs.
    # Este job legacy queda bloqueado para evitar doble verdad comercial.
    # El unico pipeline autorizado para KPIs historicos es sync_comercial_v2_job
    # -> sync_comercial_edarsahub -> mappers -> upsert_kpi_diario.
    blocked_reason = (
        "Job legacy inteligencia_comercial_sync deshabilitado como escritor. "
        "Inteligencia Comercial debe leer EDARSAHUB SQL canonico; no consultar POS, "
        "no insertar Sync_Sales y no recalcular Comercial_KPIs_Diarios_v2."
    )

    if not dry_run:
        logger.warning("[INTELIGENCIA_SYNC] BLOQUEADO: %s", blocked_reason)
        try:
            registrar_syncpos_bitacora(
                tipo_ejecucion,
                "SKIPPED",
                blocked_reason,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
            )
        except Exception:
            pass
        return {
            "success": True,
            "skipped": True,
            "legacy_writer_disabled": True,
            "reason": blocked_reason,
            "tipo_ejecucion": tipo_ejecucion,
            "dry_run": dry_run,
        }
    
    # Fechas a sincronizar.
    # Backfill explícito: fecha_inicio/fecha_fin en YYYY-MM-DD (fecha_fin EXCLUSIVA en la extracción).
    # Si no se pasan, se usa la ventana deslizante de 'dias_atras' (compatibilidad con el job horario).
    if fecha_inicio and fecha_fin:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
    else:
        fecha_fin_dt = datetime.now()
        fecha_inicio_dt = fecha_fin_dt - timedelta(days=dias_atras)
    fecha_inicio_str = fecha_inicio_dt.strftime("%Y-%m-%d")
    fecha_fin_str = fecha_fin_dt.strftime("%Y-%m-%d")
    
    logger.info(f"[INTELIGENCIA_SYNC] Período: {fecha_inicio_str} a {fecha_fin_str} (dry_run={dry_run}, tipo={tipo_ejecucion})")

    # P1B: Gate de control por configuración SQL (NO-LIVE seguro por defecto).
    cfg_syncpos = get_syncpos_config()
    if tipo_ejecucion == "AUTO":
        can_run, reason = should_run_syncpos_now(cfg_syncpos)
        if not can_run:
            logger.info(f"[INTELIGENCIA_SYNC] AUTO no ejecutado: {reason}")
            registrar_syncpos_bitacora("AUTO", "SKIPPED", reason,
                                       fecha_inicio=fecha_inicio_str, fecha_fin=fecha_fin_str)
            return {
                "success": True,
                "skipped": True,
                "reason": reason,
                "fecha_inicio": fecha_inicio_str,
                "fecha_fin": fecha_fin_str,
                "configs": audit_syncpos_canonical_configs(unidades),
            }

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "tipo_ejecucion": tipo_ejecucion,
            "fecha_inicio": fecha_inicio_str,
            "fecha_fin": fecha_fin_str,
            "configs": audit_syncpos_canonical_configs(unidades),
            "faltantes": detectar_faltantes_syncpos(unidades=unidades),
            "message": "Auditoría P1B (dry-run). NO se conectó al POS ni se cargaron datos."
        }

    # Unidades a procesar (fuente canónica SQL: Unidades_Negocio)
    if not unidades:
        unidades = [u.get('unidad_codigo') or u.get('unidad_pk') for u in get_unidades_negocio_pos(None)]
    
    stats = {
        "fecha_inicio": fecha_inicio_str,
        "fecha_fin": fecha_fin_str,
        "unidades_procesadas": 0,
        "registros_extraidos": 0,
        "registros_insertados": 0,
        "kpis_actualizados": 0,
        "errores": []
    }
    
    try:
        # Conexión a EDARSAHUB
        hub_conn = get_edarsahub_connection()
        
        for unidad in unidades:
            _unidad_row = next(
                (u for u in get_unidades_negocio_pos([unidad])
                 if (u.get('unidad_codigo') == unidad or u.get('unidad_pk') == unidad or u.get('unidad_nombre') == unidad)),
                None
            )
            config = get_pos_config_for_unidad(_unidad_row) if _unidad_row else None
            if not config:
                logger.warning(f"[INTELIGENCIA_SYNC] Configuración canónica no encontrada para {unidad}")
                continue
            
            logger.info(f"[INTELIGENCIA_SYNC] Procesando {unidad} ({config['system_type']})...")
            
            try:
                # 1. Extraer ventas del POS
                sales = extract_sales_from_pos(
                    unidad, config, fecha_inicio_str, fecha_fin_str
                )
                stats["registros_extraidos"] += len(sales)
                
                # 2. Insertar en Sync_Sales
                if sales:
                    inserted = insert_into_sync_sales(hub_conn, sales)
                    stats["registros_insertados"] += inserted
                    hub_conn.commit()
                
                # 3. Actualizar KPIs diarios
                current_date = fecha_inicio_dt
                while current_date <= fecha_fin_dt:
                    fecha_str = current_date.strftime("%Y-%m-%d")
                    if update_kpis_diarios(hub_conn, unidad, fecha_str):
                        stats["kpis_actualizados"] += 1
                    current_date += timedelta(days=1)
                
                hub_conn.commit()

                # 4. Enriquecer tipo de servicio + formas de pago por ticket
                #    (Sync_Sales.TipoServicio* + Finanzas_CortesCaja_DetallePagos).
                #    No-fatal: un fallo aquí no debe abortar el sync de ventas.
                try:
                    from core.scheduler.jobs.inteligencia_comercial_enrich import enrich_unidad
                    enr = enrich_unidad(unidad, fecha_inicio_str, fecha_fin_str, dry_run=False)
                    stats.setdefault("enriquecido", []).append(enr)
                    registrar_syncpos_bitacora(
                        tipo_ejecucion, "ENRICH_OK" if not enr.get("error") else "ENRICH_ERROR",
                        f"{unidad}: pagos={enr.get('pagos_insertados')} ts={enr.get('tickets_actualizados')} err={enr.get('error')}",
                        unidad=unidad, fecha_inicio=fecha_inicio_str, fecha_fin=fecha_fin_str,
                        tickets=enr.get("tickets_actualizados"), lineas=enr.get("pagos_insertados"),
                    )
                except Exception as e:
                    logger.error(f"[INTELIGENCIA_SYNC] Enriquecido falló para {unidad}: {e}")
                    stats["errores"].append(f"enrich {unidad}: {str(e)}")

                stats["unidades_procesadas"] += 1
                
            except Exception as e:
                error_msg = f"{unidad}: {str(e)}"
                logger.error(f"[INTELIGENCIA_SYNC] Error: {error_msg}")
                stats["errores"].append(error_msg)
                hub_conn.rollback()
        
        # Actualizar estado del job
        update_job_status(hub_conn, "ACTIVE")
        hub_conn.commit()
        hub_conn.close()
        
    except Exception as e:
        logger.error(f"[INTELIGENCIA_SYNC] Error general: {e}")
        stats["errores"].append(f"General: {str(e)}")
    
    logger.info("[INTELIGENCIA_SYNC] ========== FIN ==========")
    logger.info(f"[INTELIGENCIA_SYNC] Stats: {stats}")
    
    return stats


# ============================================================================
# EJECUCIÓN DIRECTA (para testing)
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _dry = os.environ.get("PIC_SYNC_DRY_RUN", "true").lower() == "true"
    result = job_inteligencia_comercial_sync(
        dias_atras=int(os.environ.get("PIC_SYNC_DIAS_ATRAS", "1")),
        unidades=[x.strip() for x in os.environ.get("PIC_SYNC_UNIDADES", "").split(",") if x.strip()] or None,
        fecha_inicio=os.environ.get("PIC_SYNC_FECHA_INICIO"),
        fecha_fin=os.environ.get("PIC_SYNC_FECHA_FIN"),
        dry_run=_dry,
        tipo_ejecucion=os.environ.get("PIC_SYNC_TIPO", "AUDITORIA" if _dry else "MANUAL"),
    )
    print(json.dumps(result, indent=2, default=str))
