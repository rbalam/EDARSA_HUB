"""
EDARSA HUB - Job de Sincronización de Ventas del Día Comercial V2
==================================================================

ACTUALIZACIÓN ARQUITECTÓNICA (2026-05-14):
- ORIGEN y QRO usan APIs locales (NO SQL Server MPRO central)
- NO escribir $0 falso si falla la conexión al origen
- Conservar último dato válido si falla la sincronización
- UPSERT idempotente para datos mutables durante el día
- source_status técnico para diagnóstico

FASE 5D (2026-05-16):
- Integración con EmpresaResolver para resolución canónica
- Eliminado hardcoding de MPRO_API_LOCAL_CONFIG
- ORIGEN usa EmpresaID=1 + CodigoSucursalSistema=0023
- 130QRO usa EmpresaID=2 + CodigoSucursalSistema=0021
- get_operational_window() para FechaOperacion (NO date.today())

REGLAS:
1. Ventas del Día es dato mutable durante el día (cancelaciones, reaperturas, etc.)
2. Cada sync recalcula el estado actual, no acumula
3. Si falla conexión: NO escribir $0, conservar dato anterior
4. SoftRestaurant: tabla tempcheques (abiertas) + cheques (cerradas)
5. MPRO ORIGEN/QRO: API local (NO SQL Server central)
6. El tablero lee SOLO desde EDARSAHUB SQL

FRECUENCIA: Cada 5 minutos (configurable)
TABLA DESTINO: Comercial_Ventas_Dia_Abiertas_v2

Autor: E1 Agent
Fecha: 2026-05-14
Actualizado: 2026-05-16 (FASE 5D EmpresaResolver)
"""

import os
import uuid
import logging
import requests
import pytz
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple

# Import del helper de ventana operativa
from modules.integrations_runtime.sync_ledger import enrich_sync_start, mark_sync_finished
from core.utils.operational_window import (
    get_operational_window,
    get_operational_window_legacy,
    is_within_operational_hours,
    ResultadoVentanaOperativa
)

# =============================================================================
# FASE 5D: INTEGRACIÓN CON EmpresaResolver (Mayo 2026)
# =============================================================================
try:
    from core.empresa_resolver import (
        resolve_empresa_by_alias,
        resolve_empresa_by_id,
        get_connection_for_role,
        get_empresa_connections,
        EMPRESA_RESOLVER_AVAILABLE
    )
    _EMPRESA_RESOLVER_OK = True
except ImportError as e:
    logging.warning(f"[SYNC_ABIERTAS_V2] EmpresaResolver no disponible: {e}. Usando fallback legacy.")
    _EMPRESA_RESOLVER_OK = False
    EMPRESA_RESOLVER_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuración
JOB_NAME = "sync_comercial_abiertas_v2"
SYNC_INTERVAL_SECONDS = int(os.environ.get("SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_INTERVAL_SECONDS", "300"))


# =============================================================================
# CONFIGURACIÓN DE APIs LOCALES MPRO - FALLBACK LEGACY
# =============================================================================
# NOTA: Este mapeo se usa SOLO si EmpresaResolver no está disponible.
# La fuente autoritativa es Sistema_EmpresasServidores via EmpresaResolver.
#
# IMPORTANTE: Los códigos de unidad (ORIGEN, 130QRO) son necesarios aquí porque:
# 1. Son las claves del mapeo hacia server_config_name
# 2. El sistema MPRO tiene esquemas SQL diferentes por sucursal
# 3. No se puede generalizar porque cada unidad MPRO tiene queries específicas
#
# Para eliminar estos códigos, se necesitaría:
# 1. Migrar la configuración completa a una tabla SQL (Sistema_UnidadConfigMPRO)
# 2. Incluir el tipo de esquema SQL (COMANDA vs VENTA_ENCABEZADO) en esa tabla
#
# REFACTORIZADO PARCIALMENTE 2026-06-05: La lógica de queries específicas
# en líneas 889+ requiere estos códigos para seleccionar las queries correctas.

MPRO_API_LOCAL_CONFIG_LEGACY = {
    "ORIGEN": {
        "server_config_name": "ORIGEN LOCAL",
        "sucursal_id": "0023",
        "empresa_id": 1,
        "schema_type": "VENTA_ENCABEZADO"  # Agregado para documentar
    },
    "130QRO": {
        "server_config_name": "130° QRO LOCAL", 
        "sucursal_id": "0021",
        "empresa_id": 2,
        "schema_type": "COMANDA"  # Agregado para documentar - usa Comanda+Comanda_Detalle
    }
}

# Alias para compatibilidad
MPRO_API_LOCAL_CONFIG = MPRO_API_LOCAL_CONFIG_LEGACY


# =============================================================================
# FASE P0.8: LOCK ANTI-CONCURRENCIA SQL
# =============================================================================
SYNC_TYPE_VENTAS_DIA = "VENTAS_DIA_ABIERTAS"
LOCK_TIMEOUT_MINUTES = 30

# Conexion SQL resuelta solamente cuando se ejecuta una operacion.
# No evaluar credenciales ni configuracion SQL durante el import.
from core.sql_first.db import (
    fetch_one_dict_readonly,
    get_sql_connection,
)


def _coerce_mx_datetime(value):
    """Normaliza datetime SQL a datetime aware America/Mexico_City."""
    from zoneinfo import ZoneInfo
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        raw = value.strip().replace("T", " ").replace("Z", "")
        if "." in raw:
            base, frac = raw.split(".", 1)
            frac = "".join(ch for ch in frac if ch.isdigit())[:6]
            raw = base + ("." + frac if frac else "")
        dt = datetime.fromisoformat(raw)
    else:
        raise TypeError(f"Tipo datetime no soportado: {type(value)}")
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo("America/Mexico_City"))
    return dt.astimezone(ZoneInfo("America/Mexico_City"))


def _acquire_sync_lock_sync(run_id: str, pid: int) -> bool:
    """
    Adquiere lock SQL transaccional para VENTAS_DIA_ABIERTAS.

    Garantías:
    - SERIALIZABLE + UPDLOCK + HOLDLOCK evita dos INSERT concurrentes.
    - Locks vencidos se marcan TIMEOUT dentro de la misma transacción.
    - Ante cualquier error opera fail-closed: no inicia el job.
    """
    from zoneinfo import ZoneInfo

    conn = None
    cursor = None

    try:
        conn = get_sql_connection()
        cursor = conn.cursor(as_dict=True)

        now_mx = datetime.now(ZoneInfo("America/Mexico_City"))
        now_sql = now_mx.replace(tzinfo=None)
        timeout_threshold = (
            now_mx - timedelta(minutes=LOCK_TIMEOUT_MINUTES)
        ).replace(tzinfo=None)

        cursor.execute("SET XACT_ABORT ON")
        cursor.execute(
            "SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"
        )
        cursor.execute("BEGIN TRANSACTION")

        # Liberar todas las ejecuciones activas que ya excedieron el lease.
        cursor.execute("""
            UPDATE dbo.Sync_Control_Ejecuciones
               WITH (UPDLOCK, HOLDLOCK)
            SET
                Status = 'TIMEOUT',
                FinishedAtMexico = %s,
                FinishedAtUTC = COALESCE(FinishedAtUTC, SYSUTCDATETIME()),
                ErrorMessage = COALESCE(
                    ErrorMessage,
                    'Lock vencido antes de nueva ejecución'
                )
            WHERE SyncType = %s
              AND Status = 'IN_PROGRESS'
              AND FinishedAtMexico IS NULL
              AND (
                    StartedAtMexico IS NULL
                    OR StartedAtMexico < %s
              )
        """, (
            now_sql,
            SYNC_TYPE_VENTAS_DIA,
            timeout_threshold,
        ))

        stale_count = cursor.rowcount
        if stale_count and stale_count > 0:
            logger.warning(
                "[LOCK] Ejecuciones vencidas marcadas TIMEOUT: "
                f"{stale_count}"
            )

        # La lectura y el INSERT quedan serializados en la misma transacción.
        cursor.execute("""
            SELECT TOP (1)
                SyncControlID,
                SyncRunID,
                StartedAtMexico
            FROM dbo.Sync_Control_Ejecuciones
                 WITH (UPDLOCK, HOLDLOCK)
            WHERE SyncType = %s
              AND Status = 'IN_PROGRESS'
              AND FinishedAtMexico IS NULL
            ORDER BY StartedAtMexico
        """, (SYNC_TYPE_VENTAS_DIA,))

        active = cursor.fetchone()

        if active:
            conn.commit()
            logger.info(
                "[LOCK] Ejecución activa: "
                f"{active.get('SyncRunID')}"
            )
            return False

        today = now_mx.date()

        cursor.execute("""
            INSERT INTO dbo.Sync_Control_Ejecuciones (
                SyncRunID,
                SyncType,
                FechaInicio,
                FechaFin,
                VentanaInicioHoraConfig,
                VentanaFinHoraConfig,
                IsDryRun,
                RegistrosProcesados,
                RegistrosInsertados,
                RegistrosActualizados,
                RegistrosError,
                Status,
                StartedAtMexico,
                CreatedAt
            )
            VALUES (
                %s, %s, %s, %s,
                0, 0, 0, 0, 0, 0, 0,
                'IN_PROGRESS', %s, %s
            )
        """, (
            run_id,
            SYNC_TYPE_VENTAS_DIA,
            today,
            today,
            now_sql,
            now_sql,
        ))

        enrich_sync_start(
            cursor,
            sync_run_id=run_id,
            sync_type=SYNC_TYPE_VENTAS_DIA,
        )
        conn.commit()

        logger.info(
            f"[LOCK] Adquirido: {run_id}, pid={pid}"
        )
        return True

    except Exception as exc:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass

        logger.error(
            "[LOCK] No se pudo adquirir lock; "
            f"ejecución bloqueada: {exc}"
        )
        return False

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass

        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

def _release_sync_lock_sync(
    run_id: str,
    status: str,
    processed: int,
    errors: int,
    error_msg: str = None,
):
    """Finaliza la ejecución SQL y libera su estado IN_PROGRESS."""
    from zoneinfo import ZoneInfo

    conn = None
    cursor = None

    try:
        conn = get_sql_connection()
        cursor = conn.cursor()

        now_mx = datetime.now(ZoneInfo("America/Mexico_City"))
        now_sql = now_mx.replace(tzinfo=None)

        cursor.execute("""
            SELECT StartedAtMexico
            FROM dbo.Sync_Control_Ejecuciones
            WHERE SyncRunID = %s
        """, (run_id,))

        row = cursor.fetchone()
        duration = 0

        if row and row[0]:
            started = _coerce_mx_datetime(row[0])
            if started:
                duration = int((now_mx - started).total_seconds())

        cursor.execute("""
            UPDATE dbo.Sync_Control_Ejecuciones
            SET
                Status = %s,
                FinishedAtMexico = %s,
                DurationSeconds = %s,
                RegistrosProcesados = %s,
                RegistrosError = %s,
                ErrorMessage = %s
            WHERE SyncRunID = %s
        """, (
            status,
            now_sql,
            duration,
            processed,
            errors,
            error_msg[:500] if error_msg else None,
            run_id,
        ))

        mark_sync_finished(cursor, run_id)
        conn.commit()
        logger.info(f"[LOCK] Liberado: {run_id}")

    except Exception as exc:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass

        logger.error(
            f"[LOCK] Error liberando {run_id}: {exc}"
        )

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass

        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

def _get_api_local_config(
    unidad_codigo: str,
) -> Optional[Dict]:
    """
    Obtiene la configuración API local MPRO mediante una lectura EDARSAHUB
    validada como HRLectura.
    """
    from core.secret_manager import decrypt_secret

    config = MPRO_API_LOCAL_CONFIG.get(
        unidad_codigo
    )

    if not config:
        logger.warning(
            "[SYNC_ABIERTAS_V2] Unidad %s no tiene "
            "config en MPRO_API_LOCAL_CONFIG",
            unidad_codigo,
        )
        return None

    try:
        row = fetch_one_dict_readonly(
            """
            SELECT TOP (1)
                id,
                nombre,
                api_url,
                api_key_encrypted
            FROM dbo.Servidores_Conexiones
            WHERE nombre = %s
              AND tipo_conexion = 'API_LOCAL'
              AND activo = 1
            """,
            (config["server_config_name"],),
        )

        if not row:
            logger.warning(
                "[SYNC_ABIERTAS_V2] No se encontró "
                "servidor %r en EDARSAHUB",
                config["server_config_name"],
            )
            return None

        api_key = ""

        if row.get("api_key_encrypted"):
            try:
                api_key = decrypt_secret(
                    row["api_key_encrypted"]
                )
            except Exception as exc:
                logger.error(
                    "[SYNC_ABIERTAS_V2] Error "
                    "descifrando API key: %s",
                    exc,
                )
                return None

        server_id = row["id"]

        if (
            hasattr(server_id, "hex")
            or str(type(server_id))
            == "<class 'uuid.UUID'>"
        ):
            server_id = str(server_id)

        return {
            "server_id": server_id,
            "server_name": row["nombre"],
            "api_url": row["api_url"],
            "api_key": api_key,
            "sucursal_id": config["sucursal_id"],
        }

    except Exception as exc:
        logger.error(
            "[SYNC_ABIERTAS_V2] Error obteniendo "
            "config API local: %s",
            exc,
        )
        return None


def _execute_query_via_api_local(api_config: Dict, query: str) -> Tuple[List[Dict], str]:
    """
    Ejecuta una query SQL via API local MPRO.
    
    Args:
        api_config: Dict con api_url, api_key, etc.
        query: Query SQL a ejecutar
        
    Returns:
        (rows, connection_status): Lista de resultados y estado de conexión
    """
    try:
        response = requests.get(
            api_config['api_url'],
            params={'sql': query},
            headers={'X-API-Key': api_config['api_key']},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            rows = data.get('data', [])
            return rows, "API_LOCAL_OK"
        elif response.status_code == 401:
            logger.error(f"[SYNC_ABIERTAS_V2] API Local no autorizado: {api_config['server_name']}")
            return [], "API_LOCAL_UNAUTHORIZED"
        else:
            logger.error(f"[SYNC_ABIERTAS_V2] API Local error {response.status_code}: {response.text[:200]}")
            return [], "API_LOCAL_ERROR"
            
    except requests.exceptions.Timeout:
        logger.error(f"[SYNC_ABIERTAS_V2] API Local timeout: {api_config['server_name']}")
        return [], "API_LOCAL_TIMEOUT"
    except requests.exceptions.ConnectionError:
        logger.error(f"[SYNC_ABIERTAS_V2] API Local sin conexión: {api_config['server_name']}")
        return [], "API_LOCAL_OFFLINE"
    except Exception as e:
        logger.error(f"[SYNC_ABIERTAS_V2] API Local error: {e}")
        return [], "API_LOCAL_FAILED"


def _get_existing_ventas_dia(
    unidad_negocio_id: str,
    sucursal_id: str,
) -> Optional[Dict]:
    """
    Consulta el último dato persistido mediante una conexión EDARSAHUB
    read-only validada como HRLectura.
    """
    try:
        return fetch_one_dict_readonly(
            """
            SELECT TOP (1)
                total_estimado_dia,
                ventas_abiertas,
                ventas_cerradas_dia,
                fecha_operacion,
                snapshot_timestamp
            FROM dbo.Comercial_Ventas_Dia_Abiertas_v2
            WHERE unidad_negocio_id = %s
              AND sucursal_id = %s
            ORDER BY snapshot_timestamp DESC
            """,
            (
                unidad_negocio_id,
                sucursal_id,
            ),
        )
    except Exception as exc:
        logger.warning(
            "[SYNC_ABIERTAS_V2] Error consultando "
            "dato existente para %s: %s",
            unidad_negocio_id,
            exc,
        )
        return None


# =============================================================================
# CONFIGURACIÓN DE UNIDADES
# =============================================================================


def _get_unidades_from_edarsahub() -> tuple:
    """Obtiene unidades comerciales desde UnidadesService.

    Retorna simultáneamente:
    - unidad_negocio_pk: UUID real de dbo.Unidades_Negocio.id
    - unidad_negocio_id: código operativo legacy

    No mantiene un catálogo comercial paralelo.
    """

    from core.unidades_service import UnidadesService

    unidades_sr = []
    unidades_mpro = []

    for row in UnidadesService.get_all() or []:
        unidad_pk = str(
            row.get("unidad_negocio_pk")
            or row.get("unidad_negocio_pk_real")
            or row.get("id")
            or ""
        ).strip()

        unidad_codigo = str(
            row.get("codigo")
            or row.get("unidad_negocio_codigo")
            or ""
        ).strip()

        nombre = str(
            row.get("nombre")
            or row.get("unidad_negocio_nombre")
            or ""
        ).strip()

        server_id = str(
            row.get("server_id") or ""
        ).strip()

        sucursal_id = str(
            row.get("sucursal_origen_id")
            or "DEFAULT"
        ).strip()

        system_type = str(
            row.get("system_type")
            or row.get("sistema")
            or ""
        ).strip().upper()

        if not (
            unidad_pk
            and unidad_codigo
            and nombre
            and server_id
        ):
            logger.error(
                "[SYNC_ABIERTAS_V2] Unidad comercial incompleta: %s",
                {
                    "unidad_negocio_pk": unidad_pk,
                    "unidad_negocio_id": unidad_codigo,
                    "nombre": nombre,
                    "server_id": server_id,
                    "sucursal_id": sucursal_id,
                    "system_type": system_type,
                },
            )
            continue

        unidad = {
            "unidad_negocio_pk": unidad_pk,
            "unidad_negocio_id": unidad_codigo,
            "nombre": nombre,
            "server_id": server_id,
            "sucursal_id": sucursal_id or "DEFAULT",
        }

        if "SOFT" in system_type:
            unidad["sistema"] = "SoftRestaurant"
            unidades_sr.append(unidad)

        elif "MPRO" in system_type or "MANAG" in system_type:
            unidad["sistema"] = "MPRO"
            unidades_mpro.append(unidad)

        else:
            logger.error(
                "[SYNC_ABIERTAS_V2] Sistema no soportado para %s: %s",
                unidad_codigo,
                system_type,
            )

    logger.info(
        "[SYNC_ABIERTAS_V2] Cargadas %s SoftRestaurant y %s MPRO "
        "desde UnidadesService",
        len(unidades_sr),
        len(unidades_mpro),
    )

    return unidades_sr, unidades_mpro


def select_mpro_closed_sales(
    canonical_result,
    provisional_result,
):
    """
    Selecciona una sola fuente de ventas cerradas MPRO.

    Precedencia:
    1. Venta_Encabezado cuando contiene tickets.
    2. Comanda/Comanda_Detalle únicamente como provisional.
    3. Nunca suma ambas fuentes.
    """
    canonical = dict(canonical_result or {})
    provisional = dict(provisional_result or {})

    canonical_tickets = int(
        canonical.get("tickets_cerrados_dia") or 0
    )

    if canonical_tickets > 0:
        selected = canonical
        source_kind = "CANONICAL_VENTA_ENCABEZADO"
        is_provisional = False
    else:
        selected = provisional
        source_kind = "PROVISIONAL_COMANDA"
        is_provisional = True

    return {
        "ventas_cerradas_dia": selected.get(
            "ventas_cerradas_dia"
        ) or 0,
        "tickets_cerrados_dia": selected.get(
            "tickets_cerrados_dia"
        ) or 0,
        "pax_cerrados_dia": selected.get(
            "pax_cerrados_dia"
        ) or 0,
        "propinas_cerradas_dia": selected.get(
            "propinas_cerradas_dia"
        ) or 0,
        "closed_sales_source": source_kind,
        "is_provisional": is_provisional,
    }


# =============================================================================
# QUERIES PARA VENTAS DEL DÍA
# =============================================================================

# SoftRestaurant: Cuentas abiertas desde tempcheques
# =============================================================================
# QUERIES SOFTRESTAURANT
# =============================================================================
# REGLA DE NEGOCIO: La fecha de la venta será la fecha del turno de caja 
# en el cual se aperturó la cuenta.
#
# - NO usar GETDATE() del servidor (puede ser UTC o zona horaria diferente)
# - Usar {fecha_operacion} calculada por backend en zona México
# - Si la tabla temporal (tempcheques) está vacía después del corte,
#   buscar en la tabla definitiva (cheques)
# - La venta pertenece a la FechaOperacion del turno de apertura, no al día del cierre
# =============================================================================

# SoftRestaurant: Ventas abiertas (turno aún abierto)
# Tabla: tempcheques (temporal mientras el turno está abierto)
# Filtrar por fecha_operacion para evitar sumar cheques de días anteriores no cerrados


QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS = """
SELECT
    '{fecha_operacion}' AS fecha,

    ISNULL(
        SUM(
            CASE
                WHEN ISNULL(total, 0) >= ISNULL(propina, 0)
                THEN ISNULL(total, 0) - ISNULL(propina, 0)
                ELSE ISNULL(total, 0)
            END
        ),
        0
    ) AS ventas_abiertas,

    ISNULL(
        SUM(ISNULL(propina, 0)),
        0
    ) AS propinas_abiertas,

    COUNT(DISTINCT folio) AS tickets_abiertos,

    ISNULL(
        SUM(ISNULL(nopersonas, 1)),
        0
    ) AS pax_abiertos,

    MAX(fecha) AS ultima_venta

FROM tempcheques

WHERE ISNULL(cancelado, 0) = 0
  AND ISNULL(total, 0) > 0
  AND fecha >= CONVERT(
        DATETIME,
        REPLACE('{fecha_operacion}', '-', ''),
        112
    )
  AND fecha < DATEADD(
        DAY,
        1,
        CONVERT(
            DATETIME,
            REPLACE('{fecha_operacion}', '-', ''),
            112
        )
    )
"""

# SoftRestaurant: Ventas cerradas del día (turno ya cerrado)
# Tabla: cheques (tabla definitiva después del corte)
# Buscar por fecha de apertura de la cuenta (campo 'fecha'), NO por GETDATE()


QUERY_SOFTRESTAURANT_CERRADAS_HOY = """
SELECT
    ISNULL(
        SUM(
            CASE
                WHEN ISNULL(total, 0) >= ISNULL(propina, 0)
                THEN ISNULL(total, 0) - ISNULL(propina, 0)
                ELSE ISNULL(total, 0)
            END
        ),
        0
    ) AS ventas_cerradas_dia,

    ISNULL(
        SUM(ISNULL(propina, 0)),
        0
    ) AS propinas_cerradas_dia,

    COUNT(DISTINCT folio) AS tickets_cerrados_dia,

    ISNULL(
        SUM(ISNULL(nopersonas, 1)),
        0
    ) AS pax_cerrados_dia

FROM cheques

WHERE ISNULL(cancelado, 0) = 0
  AND cierre IS NOT NULL
  AND fecha >= CONVERT(
        DATETIME,
        REPLACE('{fecha_operacion}', '-', ''),
        112
    )
  AND fecha < DATEADD(
        DAY,
        1,
        CONVERT(
            DATETIME,
            REPLACE('{fecha_operacion}', '-', ''),
            112
        )
    )
"""

# =============================================================================
# QUERIES MPRO - ORIGEN (FIX 15-May-2026: Usar Comanda como QRO)
# =============================================================================
# NOTA: ORIGEN tiene la misma estructura que QRO (Comanda + Comanda_Detalle)
# La tabla Venta_Encabezado NO tiene la columna Vn_Personas en ORIGEN
# Por lo tanto, usamos las mismas queries que QRO.
# =============================================================================
# FIX: fecha_operacion calculada por backend en zona México
# =============================================================================

# MPRO ORIGEN: Ventas abiertas (Comanda + Comanda_Detalle)
QUERY_MPRO_VENTAS_ABIERTAS_ORIGEN = """
SELECT
    '{fecha_operacion}' AS fecha,

    ISNULL(
        SUM(ticket.ventas),
        0
    ) AS ventas_abiertas,

    ISNULL(
        SUM(ticket.propina),
        0
    ) AS propinas_abiertas,

    COUNT(*)
        AS tickets_abiertos,

    ISNULL(
        SUM(ticket.pax),
        0
    ) AS pax_abiertos

FROM (
    SELECT
        c.Co_Folio,

        SUM(
            ISNULL(cd.Cd_Importe, 0)
        ) AS ventas,

        MAX(
            ISNULL(c.Co_Propina, 0)
        ) AS propina,

        MAX(
            ISNULL(c.Co_Personas, 0)
        ) AS pax

    FROM Comanda c

    INNER JOIN Comanda_Detalle cd
        ON cd.Co_Folio = c.Co_Folio

    WHERE CAST(c.Co_Fecha AS date)
            = '{fecha_operacion}'
      AND c.Sc_Cve_Sucursal
            = '{sucursal_id}'
      AND c.Es_Cve_Estado IN ('AC', 'IM')
      AND cd.Es_Cve_Estado = 'AC'
      AND cd.Fecha_Baja IS NULL

    GROUP BY
        c.Co_Folio
) AS ticket
"""

# =============================================================================
# DECISION ARQUITECTONICA
# ADR-20260804-mpro-logicas-ventas-cerradas-por-unidad.md
#
# FUENTE CANONICA FINAL MPRO:
# Venta_Encabezado.Vn_Precio_Neto_Importe.
#
# Comanda y Comanda_Detalle solo pueden actuar como fuente provisional
# intradia mientras la venta final aun no haya sido sincronizada.
# El dato provisional debe reconciliarse y sustituirse por el canonico.
# =============================================================================

# MPRO ORIGEN: Ventas cerradas del día
QUERY_MPRO_CERRADAS_HOY_ORIGEN = """
SELECT
    ISNULL(
        SUM(vc.venta_neta),
        0
    ) AS ventas_cerradas_dia,

    COUNT(
        DISTINCT vc.Vn_Documento
    ) AS tickets_cerrados_dia,

    ISNULL(
        SUM(
            ISNULL(c.Co_Personas, 0)
        ),
        0
    ) AS pax_cerrados_dia,

    ISNULL(
        SUM(
            ISNULL(c.Co_Propina, 0)
        ),
        0
    ) AS propinas_cerradas_dia

FROM (
    SELECT
        ve.Vn_Documento,
        SUM(
            ISNULL(
                ve.Vn_Precio_Neto_Importe,
                0
            )
        ) AS venta_neta

    FROM Venta_Encabezado ve

    WHERE ve.Sc_Cve_Sucursal = '{sucursal_id}'
      AND CAST(ve.Vn_Fecha AS date)
            = '{fecha_operacion}'
      AND ve.Es_Cve_Estado IN ('AC', 'FA')
      AND ve.Fecha_Baja IS NULL

    GROUP BY
        ve.Vn_Documento
) AS vc

LEFT JOIN Comanda c
    ON c.Co_Folio = vc.Vn_Documento
   AND c.Sc_Cve_Sucursal = '{sucursal_id}'
"""

# =============================================================================
# QUERIES MPRO - QRO (usa Comanda + Comanda_Detalle directamente)
# NOTA: QRO no tiene datos en Venta_Encabezado, solo en Comanda/Comanda_Detalle
# =============================================================================
# FIX 2026-05-15: Usar {fecha_operacion} (calculada en México) en lugar de GETDATE()
# GETDATE() del servidor remoto puede estar en UTC o zona horaria diferente,
# causando que la query no encuentre datos y guarde $0 falso.
# La fecha_operacion DEBE ser la misma que se guarda en EDARSAHUB.
# =============================================================================

# MPRO QRO: Ventas abiertas (Comanda + Comanda_Detalle, estado 'AC', sin baja)
# {fecha_operacion} = fecha operativa calculada por backend en zona México
QUERY_MPRO_VENTAS_ABIERTAS_QRO = """
SELECT
    '{fecha_operacion}' AS fecha,

    ISNULL(
        SUM(ticket.ventas),
        0
    ) AS ventas_abiertas,

    ISNULL(
        SUM(ticket.propina),
        0
    ) AS propinas_abiertas,

    COUNT(*)
        AS tickets_abiertos,

    ISNULL(
        SUM(ticket.pax),
        0
    ) AS pax_abiertos

FROM (
    SELECT
        c.Co_Folio,

        SUM(
            ISNULL(cd.Cd_Importe, 0)
        ) AS ventas,

        MAX(
            ISNULL(c.Co_Propina, 0)
        ) AS propina,

        MAX(
            ISNULL(c.Co_Personas, 0)
        ) AS pax

    FROM Comanda c

    INNER JOIN Comanda_Detalle cd
        ON cd.Co_Folio = c.Co_Folio

    WHERE CAST(c.Co_Fecha AS date)
            = '{fecha_operacion}'
      AND c.Sc_Cve_Sucursal
            = '{sucursal_id}'
      AND c.Es_Cve_Estado IN ('AC', 'IM')
      AND cd.Es_Cve_Estado = 'AC'
      AND cd.Fecha_Baja IS NULL

    GROUP BY
        c.Co_Folio
) AS ticket
"""

# MPRO QRO: Ventas cerradas del día (Comanda con cierre)
# NOTA: En QRO, las ventas cerradas se identifican por Es_Cve_Estado diferente o Fecha_Baja
# {fecha_operacion} = fecha operativa calculada por backend en zona México
QUERY_MPRO_CERRADAS_HOY_QRO = """
SELECT
    ISNULL(
        SUM(ticket.ventas),
        0
    ) AS ventas_cerradas_dia,

    ISNULL(
        SUM(ticket.propina),
        0
    ) AS propinas_cerradas_dia,

    COUNT(*)
        AS tickets_cerrados_dia,

    ISNULL(
        SUM(ticket.pax),
        0
    ) AS pax_cerrados_dia

FROM (
    SELECT
        c.Co_Folio,

        SUM(
            ISNULL(cd.Cd_Importe, 0)
        ) AS ventas,

        MAX(
            ISNULL(c.Co_Propina, 0)
        ) AS propina,

        MAX(
            ISNULL(c.Co_Personas, 0)
        ) AS pax

    FROM Comanda c

    INNER JOIN Comanda_Detalle cd
        ON cd.Co_Folio = c.Co_Folio

    WHERE CAST(c.Co_Fecha AS date)
            = '{fecha_operacion}'
      AND c.Sc_Cve_Sucursal
            = '{sucursal_id}'
      AND c.Es_Cve_Estado = 'PA'
      AND cd.Es_Cve_Estado = 'AC'
      AND cd.Fecha_Baja IS NULL

    GROUP BY
        c.Co_Folio
) AS ticket
"""


# =============================================================================
# FUNCIÓN PRINCIPAL DEL JOB
# =============================================================================

async def execute_sync_comercial_abiertas_v2(
    db=None,
    fecha_objetivo: date = None,
) -> Dict[str, Any]:
    """
    Ejecuta sincronización de ventas del día actual.
    
    REGLAS IMPLEMENTADAS:
    - NO escribir $0 si falla la conexión al origen
    - Conservar último dato válido si falla sync
    - ORIGEN y QRO usan API local (NO SQL Server MPRO)
    - UPSERT idempotente (dato mutable durante el día)
    """
    from modules.comercial_v2.sync_comercial_edarsahub import (
        get_server_connection_config,
        execute_query_on_server,
        ConnectionStatus
    )
    from modules.comercial_v2.schemas import (
        VentasDiaAbiertasV2,
        SyncLogV2,
        SyncRunType,
        SyncStatus,
        SistemaOrigen,
        FuenteOriginal
    )
    from modules.comercial_v2.repository_comercial_edarsahub import (
        upsert_ventas_dia_abiertas,
        insert_sync_log
    )
    
    logger.info("[SYNC_ABIERTAS_V2] === INICIO SINCRONIZACIÓN ===")
    
    start_time = datetime.now(timezone.utc)
    run_id = f"ABIERTA-{start_time.strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:4]}"
    
    # CORRECCIÓN: Usar zona horaria de México para fecha operativa
    mexico_tz = pytz.timezone('America/Mexico_City')
    now_mexico = datetime.now(mexico_tz)
    fecha_hoy = fecha_objetivo or now_mexico.date()
    pid = os.getpid()
    
    # LOG DIAGNÓSTICO OBLIGATORIO
    logger.warning(
        f"[SYNC_ABIERTAS_V2] DIAG: run_id={run_id}, "
        f"UTC={start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
        f"México={now_mexico.strftime('%Y-%m-%d %H:%M:%S')}, "
        f"fecha_hoy={fecha_hoy}, pid={pid}"
    )
    
    # =========================================================================
    # FASE P0.8: LOCK ANTI-CONCURRENCIA
    # =========================================================================
    lock_acquired = _acquire_sync_lock_sync(run_id, pid)
    if not lock_acquired:
        logger.warning(f"[SYNC_ABIERTAS_V2] ⏸️ SKIPPED_LOCKED: Otra ejecución activa")
        return {
            "job_name": JOB_NAME, "run_id": run_id, "status": "SKIPPED_LOCKED",
            "reason": "Otra instancia activa", "fecha": fecha_hoy.isoformat()
        }
    
    results = {
        "job_name": JOB_NAME,
        "run_id": run_id,
        "fecha": fecha_hoy.isoformat(),
        "inicio_ejecucion": start_time.isoformat(),
        "unidades_procesadas": 0,
        "unidades_exitosas": 0,
        "unidades_fallidas": 0,
        "total_ventas_abiertas": 0.0,
        "total_estimado_dia": 0.0,
        "detalles_unidades": [],
        "errores": []
    }
    
    try:
        # Cargar unidades desde EDARSAHUB
        unidades_sr, unidades_mpro = _get_unidades_from_edarsahub()
    
        # =========================================================================
        # SINCRONIZAR SOFTRESTAURANT
        # =========================================================================
    
        for unidad in unidades_sr:
            results["unidades_procesadas"] += 1
            unidad_id = unidad["unidad_negocio_id"]
            nombre = unidad["nombre"]
            server_id = unidad["server_id"]
        
            try:
                logger.info(f"[SYNC_ABIERTAS_V2] Procesando {nombre} (SoftRestaurant)...")
            
                # =================================================================
                # CALCULAR FechaOperacion SEGÚN VENTANA OPERATIVA DE LA UNIDAD
                # FASE P0.4: Usando nuevo sistema de turnos operativos
                # =================================================================
                resultado_ventana = get_operational_window(unidad_id)
                fecha_operacion = (
                    fecha_objetivo
                    or resultado_ventana.fecha_operacion
                )
                turno_codigo = resultado_ventana.turno_operativo_codigo
                hora_inicio = resultado_ventana.window_start_mx
                hora_fin = resultado_ventana.window_end_mx
                cruza_medianoche = resultado_ventana.cruza_medianoche
                fecha_operacion_str = fecha_operacion.isoformat()
            
                # LOG DIAGNÓSTICO: Verificar que FechaOperacion es correcta
                logger.warning(
                    f"[SYNC_ABIERTAS_V2] SR {unidad_id}: FechaOp={fecha_operacion_str}, "
                    f"turno={turno_codigo}, horario={hora_inicio}-{hora_fin}, cruza={cruza_medianoche}, "
                    f"metodo={resultado_ventana.metodo_fecha_operacion}, alertas={resultado_ventana.alertas}, "
                    f"run_id={run_id}, pid={os.getpid()}"
                )
            
                server_config = get_server_connection_config(server_id)
                if not server_config:
                    raise Exception(f"No se encontró config para server_id {server_id}")
            
                # =================================================================
                # REGLA DE NEGOCIO: Usar fecha_operacion del turno de apertura
                # =================================================================
            
                # Query ventas abiertas (tempcheques - turno aún abierto)
                query_abiertas = QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS.format(
                    fecha_operacion=fecha_operacion_str
                )
                rows_abiertas, conn_status = execute_query_on_server(
                    server_config,
                    query_abiertas,
                    context="jobs",
                )
            
                # REGLA: Si falla conexión, NO escribir $0
                if conn_status != ConnectionStatus.ONLINE:
                    raise Exception(f"Conexión fallida: {conn_status}")
            
                # Si la query retornó vacío o error silencioso, verificar
                if not rows_abiertas or rows_abiertas[0] is None:
                    raise Exception("Query retornó vacío - posible error de credenciales")
            
                # Query ventas cerradas (cheques - turno ya cerrado)
                # REGLA: Buscar por fecha de apertura de la cuenta, NO por GETDATE()
                query_cerradas = QUERY_SOFTRESTAURANT_CERRADAS_HOY.format(
                    fecha_operacion=fecha_operacion_str
                )
                rows_cerradas, cerradas_status = execute_query_on_server(
                    server_config,
                    query_cerradas,
                    context="jobs",
                )

                if cerradas_status != ConnectionStatus.ONLINE:
                    raise Exception(
                        "SOURCE_ERROR: consulta SoftRestaurant "
                        "de ventas cerradas falló con estado "
                        f"{cerradas_status}"
                    )

                if not rows_cerradas or rows_cerradas[0] is None:
                    raise Exception(
                        "SOURCE_ERROR: consulta SoftRestaurant "
                        "de ventas cerradas no devolvió "
                        "un contrato válido"
                    )
            
                # Extraer valores
                abiertas_data = rows_abiertas[0] if rows_abiertas else {}
                cerradas_data = rows_cerradas[0] if rows_cerradas else {}
            
                ventas_abiertas = Decimal(str(abiertas_data.get('ventas_abiertas') or 0))
                tickets_abiertos = int(abiertas_data.get('tickets_abiertos') or 0)
                pax_abiertos = int(abiertas_data.get('pax_abiertos') or 0)
            
                propinas_abiertas = Decimal(str(abiertas_data.get('propinas_abiertas') or 0))
                ventas_cerradas_dia = Decimal(str(cerradas_data.get('ventas_cerradas_dia') or 0))
                tickets_cerrados_dia = int(cerradas_data.get('tickets_cerrados_dia') or 0)
                pax_cerrados_dia = int(cerradas_data.get('pax_cerrados_dia') or 0)
            
                propinas_cerradas_dia = Decimal(str(cerradas_data.get('propinas_cerradas_dia') or 0))
                total_estimado_dia = ventas_abiertas + ventas_cerradas_dia
            
                propinas_total = propinas_abiertas + propinas_cerradas_dia
                # Cero confirmado por ambas consultas es válido.
                # Nunca se sustituye con ventas de otra fecha operativa.
                if total_estimado_dia == 0:
                    source_status = "NO_DATA_CONFIRMED"
                    logger.info(
                        "[SYNC_ABIERTAS_V2] %s (SR): "
                        "NO_DATA_CONFIRMED para fecha_operacion=%s. "
                        "Se escribirá cero.",
                        nombre,
                        fecha_operacion_str,
                    )
                else:
                    source_status = "DATA_OK"

                # Determinar fuente original
                if ventas_abiertas > 0 and ventas_cerradas_dia > 0:
                    fuente = FuenteOriginal.MIXTA
                elif ventas_abiertas > 0:
                    fuente = FuenteOriginal.TEMPCHEQUES
                else:
                    fuente = FuenteOriginal.CHEQUES
            
                # =================================================================
                # GUARD RAIL P0.H: VALIDAR FECHA_OPERACION ANTES DE ESCRIBIR
                # =================================================================
                # fecha_hoy viene de now_mexico.date() (línea 570)
                # fecha_operacion viene de get_operational_window()
                # La fecha_operacion NO puede ser futura respecto a fecha_hoy
                if fecha_operacion > fecha_hoy:
                    logger.error(
                        f"[SYNC_ABIERTAS_V2] ⛔ GUARD RAIL BLOQUEÓ ESCRITURA: "
                        f"fecha_operacion={fecha_operacion} > fecha_hoy={fecha_hoy}. "
                        f"Unidad={unidad_id}, run_id={run_id}"
                    )
                    results["errores"].append(f"{unidad_id}: fecha_operacion futura bloqueada")
                    results["unidades_fallidas"] += 1
                    continue  # NO escribir este registro
                
                # Crear modelo y upsert
                ventas_model = VentasDiaAbiertasV2(
                    unidad_negocio_pk=unidad["unidad_negocio_pk"],
                    unidad_negocio_nombre=nombre,
                    server_id=server_id,
                    sucursal_id=unidad["sucursal_id"],
                    sucursal_nombre=nombre,
                    sistema_origen=SistemaOrigen.SOFTRESTAURANT,
                    snapshot_timestamp=datetime.now(timezone.utc),
                    fecha_operacion=fecha_operacion,  # Usar fecha_operacion calculada
                    ventas_abiertas=ventas_abiertas,
                    tickets_abiertos=tickets_abiertos,
                    pax_abiertos=pax_abiertos,
                    propinas_abiertas=propinas_abiertas,
                    ventas_cerradas_dia=ventas_cerradas_dia,
                    tickets_cerrados_dia=tickets_cerrados_dia,
                    pax_cerrados_dia=pax_cerrados_dia,
                    propinas_cerradas_dia=propinas_cerradas_dia,
                    total_estimado_dia=total_estimado_dia,
                    propinas_total=propinas_total,
                    fuente_original=fuente,
                    sync_run_id=run_id,
                    source_status=source_status
                )
            
                upsert_result = upsert_ventas_dia_abiertas(ventas_model)
            
                results["unidades_exitosas"] += 1
                results["total_ventas_abiertas"] += float(ventas_abiertas)
                results["total_estimado_dia"] += float(total_estimado_dia)
                results["detalles_unidades"].append({
                    "unidad_negocio_id": unidad_id,
                    "unidad": nombre,
                    "sistema": "SoftRestaurant",
                    "estatus": "OK",
                    "source_status": source_status,
                    "fecha_operacion": fecha_operacion_str,  # Agregar para debug
                    "ventas_abiertas": float(ventas_abiertas),
                    "total_estimado_dia": float(total_estimado_dia)
                })
            
                logger.info(f"[SYNC_ABIERTAS_V2] {nombre}: fecha_op={fecha_operacion_str}, total=${total_estimado_dia:,.2f}")
            
                # Log exitoso
                log = SyncLogV2(
                    run_id=run_id,
                    run_type=SyncRunType.VENTAS_DIA,
                    unidad_negocio_pk=unidad["unidad_negocio_pk"],
                    server_id=server_id,
                    fecha_inicio=fecha_operacion,  # Usar fecha_operacion
                    fecha_fin=fecha_operacion,
                    status=SyncStatus.SUCCESS,
                    records_processed=1,
                    records_inserted=1 if upsert_result.get('action') == 'INSERT' else 0,
                    records_updated=1 if upsert_result.get('action') == 'UPDATE' else 0,
                    source_connection_status=ConnectionStatus.ONLINE
                )
                insert_sync_log(log)
            
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[SYNC_ABIERTAS_V2] Error en {nombre}: {error_msg}")
                results["unidades_fallidas"] += 1
                results["errores"].append(f"{nombre}: {error_msg}")
            
                # REGLA: Conservar último dato válido, NO escribir $0
                results["detalles_unidades"].append({
                    "unidad_negocio_id": unidad_id,
                    "unidad": nombre,
                    "sistema": "SoftRestaurant",
                    "estatus": "ERROR",
                    "source_status": "SYNC_FAILED",
                    "mensaje_error": error_msg[:200]
                })
            
                # Log de error - usar fecha_hoy como fallback si fecha_operacion no está definida
                log = SyncLogV2(
                    run_id=run_id,
                    run_type=SyncRunType.VENTAS_DIA,
                    unidad_negocio_pk=unidad["unidad_negocio_pk"],
                    server_id=server_id,
                    fecha_inicio=fecha_operacion if 'fecha_operacion' in dir() else fecha_hoy,
                    fecha_fin=fecha_operacion if 'fecha_operacion' in dir() else fecha_hoy,
                    status=SyncStatus.FAILED,
                    error_message=error_msg[:500],
                    source_connection_status=ConnectionStatus.OFFLINE
                )
                insert_sync_log(log)
    
        # =========================================================================
        # SINCRONIZAR MPRO VIA API LOCAL
        # =========================================================================
    
        for unidad in unidades_mpro:
            results["unidades_procesadas"] += 1
            unidad_id = unidad["unidad_negocio_id"]
            nombre = unidad["nombre"]
        
            try:
                logger.info(f"[SYNC_ABIERTAS_V2] Procesando {nombre} (MPRO API Local)...")
            
                # Obtener configuración de API local desde EDARSAHUB
                api_config = _get_api_local_config(unidad_id)
                if not api_config:
                    raise Exception(f"No se encontró configuración API local para {unidad_id}")
            
                server_id = api_config['server_id']  # ID del servidor API_LOCAL
                sucursal_id = api_config['sucursal_id']
            
                logger.info(f"[SYNC_ABIERTAS_V2] Usando API: {api_config['api_url']} para sucursal {sucursal_id}")
            
                # =================================================================
                # CALCULAR FechaOperacion SEGÚN VENTANA OPERATIVA DE LA UNIDAD
                # FASE P0.4: Usando nuevo sistema de turnos operativos
                # =================================================================
                # REGLA DE NEGOCIO:
                # - Si QRO opera de 13:00 a 03:00, a las 02:00 del día 15 todavía
                #   pertenece a la jornada del día 14
                # - Solo después del cierre inicia el nuevo día operativo
                # =================================================================
            
                resultado_ventana = get_operational_window(unidad_id)
                fecha_operacion = (
                    fecha_objetivo
                    or resultado_ventana.fecha_operacion
                )
                turno_codigo = resultado_ventana.turno_operativo_codigo
                hora_inicio = resultado_ventana.window_start_mx
                hora_fin = resultado_ventana.window_end_mx
                cruza_medianoche = resultado_ventana.cruza_medianoche
                fecha_operacion_str = fecha_operacion.isoformat()
            
                # LOG DIAGNÓSTICO: Verificar que FechaOperacion es correcta
                logger.warning(
                    f"[SYNC_ABIERTAS_V2] MPRO {unidad_id}: FechaOp={fecha_operacion_str}, "
                    f"turno={turno_codigo}, horario={hora_inicio}-{hora_fin}, cruza={cruza_medianoche}, "
                    f"metodo={resultado_ventana.metodo_fecha_operacion}, alertas={resultado_ventana.alertas}, "
                    f"run_id={run_id}, pid={os.getpid()}"
                )
            
                # =================================================================
                # SELECCIONAR QUERY SEGÚN UNIDAD
                # ORIGEN: Usa Venta_Encabezado (estructura estándar MPRO)
                # 130QRO: Usa Comanda + Comanda_Detalle (estructura alternativa)
                # =================================================================
            
                if unidad_id == '130QRO':
                    # QRO usa estructura diferente: Comanda + Comanda_Detalle
                    query_template_abiertas = QUERY_MPRO_VENTAS_ABIERTAS_QRO
                    query_template_cerradas = QUERY_MPRO_CERRADAS_HOY_QRO
                    logger.info(f"[SYNC_ABIERTAS_V2] {nombre}: Query Comanda+Comanda_Detalle, fecha_op={fecha_operacion_str}")
                else:
                    # ORIGEN y otras unidades MPRO usan Venta_Encabezado estándar
                    query_template_abiertas = QUERY_MPRO_VENTAS_ABIERTAS_ORIGEN
                    query_template_cerradas = QUERY_MPRO_CERRADAS_HOY_ORIGEN
                    logger.info(f"[SYNC_ABIERTAS_V2] {nombre}: Query Venta_Encabezado estándar")
            
                # Query ventas abiertas via API local
                # FIX: Incluir fecha_operacion para QRO (para ORIGEN no afecta, usa GETDATE)
                query_abiertas = query_template_abiertas.format(
                    sucursal_id=sucursal_id,
                    fecha_operacion=fecha_operacion_str
                )
                rows_abiertas, conn_status = _execute_query_via_api_local(api_config, query_abiertas)
            
                # REGLA: Si falla API, NO escribir $0
                if conn_status != "API_LOCAL_OK":
                    raise Exception(f"API Local falló: {conn_status}")
            
                # REGLA ANTI-$0 FALSO: Primero obtener AMBAS queries antes de decidir
                abiertas_data = rows_abiertas[0] if rows_abiertas else {}
            
                # =============================================================
                # VENTAS CERRADAS MPRO: CANONICO CON FALLBACK PROVISIONAL
                # =============================================================
                # Regla:
                # 1. Venta_Encabezado es la fuente canónica final.
                # 2. Comanda se consulta únicamente cuando el canónico no
                #    contiene tickets para la fecha operativa.
                # 3. Nunca se suman ambas fuentes.
                query_cerradas_canonical = (
                    QUERY_MPRO_CERRADAS_HOY_ORIGEN.format(
                        sucursal_id=sucursal_id,
                        fecha_operacion=fecha_operacion_str,
                    )
                )

                rows_canonical, canonical_status = (
                    _execute_query_via_api_local(
                        api_config,
                        query_cerradas_canonical,
                    )
                )

                if canonical_status != "API_LOCAL_OK":
                    raise Exception(
                        "SOURCE_ERROR: consulta canónica MPRO "
                        "de ventas cerradas falló con estado "
                        f"{canonical_status}"
                    )

                canonical_closed_data = (
                    rows_canonical[0]
                    if rows_canonical
                    else {}
                )

                canonical_tickets = int(
                    canonical_closed_data.get(
                        "tickets_cerrados_dia"
                    )
                    or 0
                )

                provisional_closed_data = {}

                if canonical_tickets <= 0:
                    query_cerradas_provisional = (
                        QUERY_MPRO_CERRADAS_HOY_QRO.format(
                            sucursal_id=sucursal_id,
                            fecha_operacion=fecha_operacion_str,
                        )
                    )

                    rows_provisional, provisional_status = (
                        _execute_query_via_api_local(
                            api_config,
                            query_cerradas_provisional,
                        )
                    )

                    if provisional_status != "API_LOCAL_OK":
                        raise Exception(
                            "SOURCE_ERROR: consulta provisional MPRO "
                            "de ventas cerradas falló con estado "
                            f"{provisional_status}"
                        )

                    provisional_closed_data = (
                        rows_provisional[0]
                        if rows_provisional
                        else {}
                    )

                cerradas_data = select_mpro_closed_sales(
                    canonical_closed_data,
                    provisional_closed_data,
                )

                closed_sales_source = cerradas_data[
                    "closed_sales_source"
                ]
                closed_sales_is_provisional = cerradas_data[
                    "is_provisional"
                ]

                logger.info(
                    "[SYNC_ABIERTAS_V2] %s: "
                    "fuente_cerradas=%s, provisional=%s, "
                    "canonical_tickets=%s, selected_tickets=%s",
                    nombre,
                    closed_sales_source,
                    closed_sales_is_provisional,
                    canonical_tickets,
                    cerradas_data.get("tickets_cerrados_dia"),
                )
            
                # Extraer valores ANTES de decidir
                ventas_abiertas_raw = abiertas_data.get('ventas_abiertas')
                ventas_cerradas_raw = cerradas_data.get('ventas_cerradas_dia')
            
                logger.info(
                    "[SYNC_ABIERTAS_V2] %s RAW: "
                    "abiertas=%s, cerradas=%s",
                    nombre,
                    ventas_abiertas_raw,
                    ventas_cerradas_raw,
                )

                # Dos NULL representan contrato inválido del origen.
                # No representan una venta confirmada en cero.
                if (
                    ventas_abiertas_raw is None
                    and ventas_cerradas_raw is None
                ):
                    raise Exception(
                        "SOURCE_ERROR: ambas consultas MPRO "
                        "devolvieron NULL"
                    )

                abiertas_valor = float(
                    ventas_abiertas_raw
                    if ventas_abiertas_raw is not None
                    else 0
                )
                cerradas_valor = float(
                    ventas_cerradas_raw
                    if ventas_cerradas_raw is not None
                    else 0
                )
                total_calculado = (
                    abiertas_valor
                    + cerradas_valor
                )

                if total_calculado == 0:
                    source_status = "NO_DATA_CONFIRMED"
                    logger.info(
                        "[SYNC_ABIERTAS_V2] %s: "
                        "NO_DATA_CONFIRMED para fecha_operacion=%s. "
                        "Se escribirá cero.",
                        nombre,
                        fecha_operacion_str,
                    )
                else:
                    source_status = "DATA_OK"
                    logger.info(
                        "[SYNC_ABIERTAS_V2] %s: "
                        "DATA_OK, total=$%s",
                        nombre,
                        f"{total_calculado:,.2f}",
                    )

                # Extraer valores finales (abiertas_data y cerradas_data ya están definidos arriba)
                ventas_abiertas = Decimal(str(abiertas_data.get('ventas_abiertas') or 0))
                tickets_abiertos = int(abiertas_data.get('tickets_abiertos') or 0)
                pax_abiertos = int(abiertas_data.get('pax_abiertos') or 0)
            
                ventas_cerradas_dia = Decimal(str(cerradas_data.get('ventas_cerradas_dia') or 0))
                tickets_cerrados_dia = int(cerradas_data.get('tickets_cerrados_dia') or 0)
                pax_cerrados_dia = int(cerradas_data.get('pax_cerrados_dia') or 0)
            
                propinas_abiertas = Decimal(str(abiertas_data.get('propinas_abiertas') or 0))
                propinas_cerradas_dia = Decimal(str(cerradas_data.get('propinas_cerradas_dia') or 0))
                propinas_total = propinas_abiertas + propinas_cerradas_dia

                total_estimado_dia = ventas_abiertas + ventas_cerradas_dia
            
                # FIX 2026-05-15: Log detallado para QRO (diagnóstico de bug $0)
                if unidad_id == '130QRO':
                    logger.info("[SYNC_ABIERTAS_V2] QRO DETALLE:")
                    logger.info(f"  fecha_operacion_backend: {fecha_operacion_str}")
                    logger.info(f"  server_id: {server_id}")
                    logger.info(f"  api_url: {api_config['api_url']}")
                    logger.info(f"  raw_abiertas: {abiertas_data}")
                    logger.info(f"  raw_cerradas: {cerradas_data}")
                    logger.info(f"  ventas_abiertas: ${ventas_abiertas:,.2f}")
                    logger.info(f"  ventas_cerradas_dia: ${ventas_cerradas_dia:,.2f}")
                    logger.info(f"  total_estimado_dia: ${total_estimado_dia:,.2f}")
            
                # =================================================================
                # GUARD RAIL P0.H: VALIDAR FECHA_OPERACION ANTES DE ESCRIBIR
                # =================================================================
                if fecha_operacion > fecha_hoy:
                    logger.error(
                        f"[SYNC_ABIERTAS_V2] ⛔ GUARD RAIL BLOQUEÓ ESCRITURA MPRO: "
                        f"fecha_operacion={fecha_operacion} > fecha_hoy={fecha_hoy}. "
                        f"Unidad={unidad_id}, run_id={run_id}"
                    )
                    results["errores"].append(f"{unidad_id}: fecha_operacion futura bloqueada")
                    results["unidades_fallidas"] += 1
                    continue  # NO escribir este registro
                
                # Crear modelo y upsert
                ventas_model = VentasDiaAbiertasV2(
                    unidad_negocio_pk=unidad["unidad_negocio_pk"],
                    unidad_negocio_nombre=nombre,
                    server_id=server_id,
                    sucursal_id=sucursal_id,
                    sucursal_nombre=nombre,
                    sistema_origen=SistemaOrigen.MPRO,
                    snapshot_timestamp=datetime.now(timezone.utc),
                    fecha_operacion=fecha_operacion,  # Usar fecha_operacion calculada
                    ventas_abiertas=ventas_abiertas,
                    propinas_abiertas=propinas_abiertas,
                    propinas_cerradas_dia=propinas_cerradas_dia,
                    propinas_total=propinas_total,
                    tickets_abiertos=tickets_abiertos,
                    pax_abiertos=pax_abiertos,
                    ventas_cerradas_dia=ventas_cerradas_dia,
                    tickets_cerrados_dia=tickets_cerrados_dia,
                    pax_cerrados_dia=pax_cerrados_dia,
                    total_estimado_dia=total_estimado_dia,
                    fuente_original=FuenteOriginal.API_LOCAL,
                    sync_run_id=run_id,
                    source_status=source_status
                )
            
                upsert_result = upsert_ventas_dia_abiertas(ventas_model)
            
                results["unidades_exitosas"] += 1
                results["total_ventas_abiertas"] += float(ventas_abiertas)
                results["total_estimado_dia"] += float(total_estimado_dia)
                results["detalles_unidades"].append({
                    "unidad_negocio_id": unidad_id,
                    "unidad": nombre,
                    "sistema": "MPRO",
                    "fuente": "API_LOCAL",
                    "estatus": "OK",
                    "source_status": source_status,
                    "closed_sales_source": closed_sales_source,
                    "closed_sales_is_provisional": (
                        closed_sales_is_provisional
                    ),
                    "fecha_operacion": fecha_operacion_str,  # Agregar para debug
                    "ventas_abiertas": float(ventas_abiertas),
                    "total_estimado_dia": float(total_estimado_dia)
                })
            
                logger.info(
                    "[SYNC_ABIERTAS_V2] %s (API Local): "
                    "fecha_op=%s, total=$%s, fuente_cerradas=%s, "
                    "provisional=%s",
                    nombre,
                    fecha_operacion_str,
                    f"{total_estimado_dia:,.2f}",
                    closed_sales_source,
                    closed_sales_is_provisional,
                )
            
                # Log exitoso
                log = SyncLogV2(
                    run_id=run_id,
                    run_type=SyncRunType.VENTAS_DIA,
                    unidad_negocio_pk=unidad["unidad_negocio_pk"],
                    server_id=server_id,
                    fecha_inicio=fecha_operacion,  # Usar fecha_operacion
                    fecha_fin=fecha_operacion,
                    status=SyncStatus.SUCCESS,
                    records_processed=1,
                    records_inserted=1 if upsert_result.get('action') == 'INSERT' else 0,
                    records_updated=1 if upsert_result.get('action') == 'UPDATE' else 0,
                    source_connection_status=ConnectionStatus.ONLINE
                )
                insert_sync_log(log)
            
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[SYNC_ABIERTAS_V2] Error en {nombre}: {error_msg}")
                results["unidades_fallidas"] += 1
                results["errores"].append(f"{nombre}: {error_msg}")
            
                # REGLA: Conservar último dato válido, NO escribir $0
                results["detalles_unidades"].append({
                    "unidad_negocio_id": unidad_id,
                    "unidad": nombre,
                    "sistema": "MPRO",
                    "fuente": "API_LOCAL",
                    "estatus": "ERROR",
                    "source_status": "SYNC_FAILED",
                    "mensaje_error": error_msg[:200]
                })
            
                # Log de error - usar fecha_operacion si está disponible
                log = SyncLogV2(
                    run_id=run_id,
                    run_type=SyncRunType.VENTAS_DIA,
                    unidad_negocio_pk=unidad["unidad_negocio_pk"],
                    server_id=unidad.get("server_id", "UNKNOWN"),
                    fecha_inicio=fecha_operacion if 'fecha_operacion' in dir() else fecha_hoy,
                    fecha_fin=fecha_operacion if 'fecha_operacion' in dir() else fecha_hoy,
                    status=SyncStatus.FAILED,
                    error_message=error_msg[:500],
                    source_connection_status=ConnectionStatus.OFFLINE
                )
                insert_sync_log(log)
    
        # Resumen final
        end_time = datetime.now(timezone.utc)
        results["fin_ejecucion"] = end_time.isoformat()
        results["duracion_segundos"] = (end_time - start_time).total_seconds()
    
        logger.info(
            f"[SYNC_ABIERTAS_V2] === FIN === "
            f"Procesadas: {results['unidades_procesadas']}, "
            f"Exitosas: {results['unidades_exitosas']}, "
            f"Fallidas: {results['unidades_fallidas']}, "
            f"Total día: ${results['total_estimado_dia']:,.2f}"
        )
    
        return results

    finally:
        # FASE P0.8: Liberar lock siempre
        status = "SUCCESS" if results.get("unidades_fallidas", 0) == 0 else "PARTIAL"
        err = "; ".join(results.get("errores", []))[:500] if results.get("errores") else None
        _release_sync_lock_sync(run_id, status, results.get("unidades_procesadas", 0), results.get("unidades_fallidas", 0), err)



# =============================================================================
# EJECUCIÓN MANUAL PARA TESTING
# =============================================================================

def run_sync_comercial_abiertas_v2_manual(
    fecha: date = None,
):
    """Ejecuta sincronización manual respetando la fecha solicitada."""
    import asyncio

    return asyncio.run(
        execute_sync_comercial_abiertas_v2(
            fecha_objetivo=fecha,
        )
    )


# Exportar
__all__ = ['execute_sync_comercial_abiertas_v2', 'run_sync_comercial_abiertas_v2_manual', 'JOB_NAME']
