"""
SYNC COMERCIAL EDARSAHUB - Comercial V2
=======================================

Sincronizador de datos comerciales hacia EDARSAHUB.
Extrae datos de SoftRestaurant y MPRO, los transforma y guarda en tablas v2.

IMPORTANTE:
- Este módulo NO está conectado al Tablero Ejecutivo actual
- NO modifica el módulo comercial existente
- Escribe SOLO en tablas con sufijo _v2 en EDARSAHUB
- NO tiene scheduler activo (ejecución manual)

Sistemas soportados:
- SoftRestaurant: cheques + turnos + tempcheques
- MPRO: Venta_Encabezado + Comanda
"""

import uuid
import time
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple


from .schemas import (
    KPIsDiariosV2,
    VentasDiaAbiertasV2,
    SyncLogV2,
    SyncRunType,
    SyncStatus,
    ConnectionStatus,
    UnidadNegocioConfig,
    SistemaOrigen,
    SyncResult
)
from .mappers import (
    map_softrestaurant_ventas_cerradas,
    map_softrestaurant_ventas_abiertas,
    map_mpro_ventas_cerradas,
    map_mpro_ventas_abiertas
)
from core.unidades_service import UnidadesService
from .repository_comercial_edarsahub import (
    EDARSAHUB_CONFIG,
    get_unidades_negocio_config,
    upsert_kpi_diario,
    upsert_ventas_dia_abiertas,
    insert_sync_log
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURACIÓN DE CONEXIONES A ORÍGENES
# =============================================================================


def get_server_connection_config(
    server_id: str,
    unidad_negocio_pk: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Resuelve una conexión POS mediante el catálogo canónico.

    Comercial V2 no consulta ni descifra directamente
    Servidores_Conexiones. La resolución autorizada es:

        Unidades_Negocio
            -> server_id
            -> PosRuntimeResolver
            -> secreto descifrado en memoria

    Cuando un servidor atiende más de una unidad, como MPRO,
    unidad_negocio_pk es obligatoria para evitar ambigüedad.
    """

    from core.connections.pos_runtime_resolver import (
        list_pos_runtime_contexts,
    )

    server_id_normalizado = str(
        server_id or ""
    ).strip().lower()

    unidad_pk_normalizada = str(
        unidad_negocio_pk or ""
    ).strip().lower()

    if not server_id_normalizado:
        logger.error(
            "server_id vacío al resolver conexión POS comercial"
        )
        return None

    try:
        contexts = list_pos_runtime_contexts(
            system_types=(
                "SOFTRESTAURANT",
                "MPRO",
            )
        )
    except Exception as exc:
        logger.error(
            "Error en resolvedor canónico POS: %s",
            exc,
        )
        return None

    matches = []

    for context in contexts:
        context_server_id = str(
            context.server_id or ""
        ).strip().lower()

        context_pk = str(
            context.unidad_negocio_pk or ""
        ).strip().lower()

        if context_server_id != server_id_normalizado:
            continue

        if (
            unidad_pk_normalizada
            and context_pk != unidad_pk_normalizada
        ):
            continue

        matches.append(context)

    if len(matches) != 1:
        logger.error(
            "Relación POS no única: server_id=%s, "
            "unidad_negocio_pk=%s, coincidencias=%s",
            server_id,
            unidad_negocio_pk,
            len(matches),
        )
        return None

    context = matches[0]

    try:
        external = context.external_connection_config(
            as_dict=True
        )
    except Exception as exc:
        logger.error(
            "No se pudo construir conexión POS para %s: %s",
            context.unidad_codigo,
            exc,
        )
        return None

    return {
        "id": context.server_id,
        "nombre": context.unidad_nombre,
        "host": context.host,
        "host_raw": external.get("host"),
        "port": context.port,
        "instance": context.instance,
        "database_name": context.database,
        "username": context.username,
        "password": context.password,
        "system_type": context.system_type,
        "activo": True,
        "unidad_negocio_pk": context.unidad_negocio_pk,
        "unidad_codigo": context.unidad_codigo,
        "empresa_id": context.empresa_id,
        "sucursal_id": context.sucursal_origen_id,
    }



def execute_query_on_server(
    server_config: Dict[str, Any],
    query: str,
    context: str = "web",
) -> Tuple[List[Dict], ConnectionStatus]:
    """Ejecuta SELECT comercial usando el adaptador SQL externo canónico."""

    del context

    from core.sql_first.connection_factory import (
        get_external_sql_connection,
    )

    connection = None
    cursor = None

    try:
        config = dict(server_config or {})
        config["as_dict"] = True
        config["login_timeout"] = int(
            config.get("login_timeout") or 20
        )
        config["timeout"] = int(
            config.get("timeout") or 60
        )

        connection = get_external_sql_connection(config)
        cursor = connection.cursor()
        cursor.execute(query)

        if not cursor.description:
            return [], ConnectionStatus.ONLINE

        columns = [
            description[0]
            for description in cursor.description
        ]

        rows = []
        for row in cursor.fetchall() or []:
            if isinstance(row, dict):
                rows.append(dict(row))
            elif hasattr(row, "_asdict"):
                rows.append(dict(row._asdict()))
            else:
                rows.append(
                    {
                        columns[index]: row[index]
                        for index in range(len(columns))
                    }
                )

        return rows, ConnectionStatus.ONLINE

    except Exception as exc:
        logger.error(
            "Error consultando POS mediante factory canónico: %s",
            type(exc).__name__,
        )
        return [], ConnectionStatus.OFFLINE

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass

        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass

# ============================================================
# AGREGACION CANONICA POR FECHA_OPERACION
# Ventas cerradas V2:
# - La query conserva fecha_hora real.
# - La fecha_operacion se calcula con Sistema_TurnosOperativosUnidad.
# - Los mappers actuales siguen recibiendo rows agregadas con campo fecha.
# ============================================================

def _normalizar_fecha_operacion_value(value):
    from datetime import date

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        raw = raw.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(raw).date()
        except ValueError:
            return datetime.strptime(raw[:10], "%Y-%m-%d").date()

    raise ValueError(f"No se pudo normalizar fecha_operacion: {value!r}")


def _normalizar_fecha_hora_value(value):
    from datetime import date, time

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(value, time.min)

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        raw = raw.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S")

    raise ValueError(f"No se pudo normalizar fecha_hora: {value!r}")


def _get_config_value(config, key):
    if config is None:
        return None

    if isinstance(config, dict):
        return config.get(key)

    return getattr(config, key, None)



def _resolver_unidad_negocio_pk_from_config(config):
    """Obtiene exclusivamente la PK canónica de la unidad.

    V1.0 comercial no permite promover unidad_negocio_id, código,
    nombre, sucursal o server_id a unidad_negocio_pk.
    """

    candidatos_pk = (
        "unidad_negocio_pk",
        "UnidadNegocioPK",
    )

    for key in candidatos_pk:
        value = _get_config_value(config, key)

        if value not in (None, ""):
            value = str(value).strip()

            if value:
                return value

    for nested_key in (
        "unidad_negocio",
        "unidad",
        "business_unit",
    ):
        nested = _get_config_value(config, nested_key)

        if not isinstance(nested, dict):
            continue

        for key in candidatos_pk:
            value = nested.get(key)

            if value not in (None, ""):
                value = str(value).strip()

                if value:
                    return value

    raise ValueError(
        "No se encontró unidad_negocio_pk canónica en config. "
        "No se aceptan códigos o IDs legacy como sustituto."
    )

def _row_to_dict(row):
    if row is None:
        return {}

    if isinstance(row, dict):
        return dict(row)

    if hasattr(row, "items"):
        return dict(row.items())

    if hasattr(row, "_asdict"):
        return dict(row._asdict())

    raise ValueError(f"Row no convertible a dict para ventas cerradas V2: {row!r}")


def _normalizar_distinct_key(value):
    if value is None:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    return raw


def _is_number_for_operational_group(value):

    if isinstance(value, bool):
        return False

    return isinstance(value, (int, float, Decimal))


def _is_metric_key_for_operational_group(key):
    k = str(key).lower()

    excluded_exact = {
        "fecha",
        "fecha_hora",
        "fecha_operacion",
        "fecha_hora_min",
        "fecha_hora_max",
        "server_id",
        "servidor_id",
        "sucursal_id",
        "unidad_negocio_id",
        "unidad_negocio_pk",
        "almacen_id",
        "cliente_id",
        "producto_id",
        "id",
    }

    excluded_fragments = (
        "codigo",
        "folio",
        "uuid",
        "guid",
        "nombre",
        "sucursal",
        "unidad",
        "servidor",
        "fecha",
        "hora",
        "promedio",
        "average",
        "avg",
        "porcentaje",
        "percent",
        "ratio",
        "margen",
    )

    excluded_suffixes = ("_id", "id", "_pk", "pk")

    if k in excluded_exact:
        return False

    if any(fragment in k for fragment in excluded_fragments):
        return False

    if any(k.endswith(suffix) for suffix in excluded_suffixes):
        return False

    return True


def _recalcular_derivados_ventas_cerradas(row):
    total_keys = (
        "ventas_total",
        "total_ventas",
        "venta_total",
        "ventas",
        "importe_total",
        "total",
        "Vn_Precio_Neto_Importe",
    )
    ticket_keys = (
        "num_cheques",
        "num_folios",
        "tickets",
        "total_tickets",
        "cantidad_tickets",
        "num_tickets",
        "numero_tickets",
        "transacciones",
        "total_transacciones",
    )
    promedio_keys = (
        "ticket_promedio",
        "promedio_ticket",
        "avg_ticket",
        "average_ticket",
    )

    total = None
    tickets = None

    for key in total_keys:
        if key in row and row.get(key) is not None:
            total = row.get(key)
            break

    for key in ticket_keys:
        if key in row and row.get(key) not in (None, 0):
            tickets = row.get(key)
            break

    if total is None or not tickets:
        return row

    for key in promedio_keys:
        if key in row:
            row[key] = total / tickets

    return row


def _agrupar_ventas_cerradas_por_fecha_operacion(rows, config, fecha_inicio=None, fecha_fin=None):
    from collections import OrderedDict

    fecha_inicio_op = _normalizar_fecha_operacion_value(fecha_inicio)
    fecha_fin_op = _normalizar_fecha_operacion_value(fecha_fin)

    agrupadas = OrderedDict()

    for row in rows or []:
        row_dict = _row_to_dict(row)

        fecha_hora = (
            row_dict.get("fecha_hora")
            or row_dict.get("fecha")
            or row_dict.get("Vn_Fecha")
            or row_dict.get("vn_fecha")
        )
        fecha_hora = _normalizar_fecha_hora_value(fecha_hora)

        if fecha_hora is None:
            raise ValueError(f"Row sin fecha_hora para ventas cerradas V2: {row_dict!r}")

        sistema_origen = getattr(config, "sistema_origen", None)
        fecha_operacion_query = row_dict.get("fecha_operacion")

        if fecha_operacion_query is not None:
            fecha_operacion = _normalizar_fecha_operacion_value(fecha_operacion_query)
        elif sistema_origen == SistemaOrigen.MPRO:
            fecha_operacion = _normalizar_fecha_operacion_value(fecha_hora)
        elif sistema_origen == SistemaOrigen.SOFTRESTAURANT:
            # Igual que Reporte Ejecutivo: fecha calendario de turnos.apertura.
            fecha_operacion = _normalizar_fecha_operacion_value(fecha_hora)
        else:
            raise ValueError(
                "Sistema origen no soportado para resolver "
                f"fecha_operacion: {sistema_origen!r}"
            )

        if fecha_inicio_op and fecha_operacion < fecha_inicio_op:
            continue

        if fecha_fin_op and fecha_operacion > fecha_fin_op:
            continue

        if fecha_operacion not in agrupadas:
            base = {}
            for col, value in row_dict.items():
                if _is_number_for_operational_group(value) and _is_metric_key_for_operational_group(col):
                    base[col] = 0
                elif col not in ("fecha", "fecha_hora"):
                    base[col] = value

            base["fecha"] = fecha_operacion
            base["fecha_operacion"] = fecha_operacion
            base["fecha_hora_min"] = fecha_hora
            base["fecha_hora_max"] = fecha_hora
            agrupadas[fecha_operacion] = base

        target = agrupadas[fecha_operacion]
        target["fecha_hora_min"] = min(target["fecha_hora_min"], fecha_hora)
        target["fecha_hora_max"] = max(target["fecha_hora_max"], fecha_hora)

        soft_folio = _normalizar_distinct_key(row_dict.get("folio"))
        if soft_folio is not None:
            target.setdefault("_distinct_num_cheques", set()).add(soft_folio)

        mpro_folio_value = row_dict.get("Vn_Folio")
        if mpro_folio_value is None:
            mpro_folio_value = row_dict.get("vn_folio")
        mpro_folio = _normalizar_distinct_key(mpro_folio_value)
        if mpro_folio is not None:
            target.setdefault("_distinct_num_folios", set()).add(mpro_folio)

        for col, value in row_dict.items():
            if (
                value is not None
                and _is_number_for_operational_group(value)
                and _is_metric_key_for_operational_group(col)
            ):
                target[col] = target.get(col, 0) + value

    rows_agrupadas = []
    for row in agrupadas.values():
        distinct_num_cheques = row.pop("_distinct_num_cheques", None)
        if distinct_num_cheques is not None and not row.get("num_cheques"):
            row["num_cheques"] = len(distinct_num_cheques)

        distinct_num_folios = row.pop("_distinct_num_folios", None)
        if distinct_num_folios is not None:
            row["num_folios"] = len(distinct_num_folios)

        rows_agrupadas.append(_recalcular_derivados_ventas_cerradas(row))

    return rows_agrupadas

# =============================================================================
# QUERIES POR SISTEMA
# =============================================================================

# -------------------- SOFTRESTAURANT --------------------

QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA = """
SELECT
    CONVERT(datetime, '{fecha_operacion} 12:00:00 AM') AS fecha_hora,
    CONVERT(date, '{fecha_operacion}') AS fecha_operacion,
    SUM(ch.totalalimentossindescuentos) AS alimentos,
    SUM(ch.totalbebidassindescuentos) AS bebidas,
    SUM(ch.totalotrossindescuentos) AS otros,
    SUM(ch.totalcortesias) AS cortesias,
    SUM(ch.totaldescuentos) AS descuentos,
    SUM(ch.subtotal) AS subtotal,
    SUM(ch.totalimpuesto1) AS iva,
    SUM(ch.total) AS ventas_total,
    SUM(ch.propina) AS propinas,
    SUM(ch.total + ch.propina) AS total_con_propina,
    SUM(ch.nopersonas) AS num_personas,
    COUNT(DISTINCT ch.folio) AS num_cheques
FROM cheques AS ch
INNER JOIN turnos AS tr
    ON tr.idturno = ch.idturno
WHERE CONVERT(varchar, DATEADD(hour, -{offset_hours}, tr.apertura), 112) = '{fecha_operacion_sql}'
  AND ch.cancelado = 0
"""


def build_softrestaurant_ventas_cerradas_query(
    server_config: Dict[str, Any],
    fecha_inicio: date,
    fecha_fin: date,
) -> str:
    """Construye ventas SoftRestaurant con el contrato del Reporte Ejecutivo.

    La pertenencia al dia se define SOLO por la fecha calendario de
    turnos.apertura. No usa turnos operativos, cierre ni idempresa.
    """
    offset_hours = 9 if str((server_config or {}).get('unidad_codigo') or '').strip().upper() == 'ESTELAR' else 0
    bloques = []
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        bloques.append(QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA.format(
            fecha_operacion=fecha_actual.strftime('%Y-%m-%d'),
            fecha_operacion_sql=fecha_actual.strftime('%Y%m%d'),
            offset_hours=offset_hours,
        ))
        fecha_actual += timedelta(days=1)
    return "\nUNION ALL\n".join(bloques)

QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS = """
SELECT 
    SUM(total) as ventas_abiertas,
    COUNT(DISTINCT folio) as tickets_abiertos,
    SUM(ISNULL(nopersonas, 1)) as pax_abiertos
FROM cheques
WHERE cancelado = 0
  AND cierre IS NULL  -- Cheques abiertos (sin cerrar)
  AND total > 0
"""


# -------------------- MPRO --------------------

QUERY_MPRO_VENTAS_CERRADAS = """
SELECT 
    ve.Vn_Fecha as fecha_hora,
    ve.Vn_Folio as Vn_Folio,
    ve.Vn_Precio_Neto_Importe as Vn_Precio_Neto_Importe,
    ISNULL(c.Co_Propina, 0) as propinas,
    ISNULL(c.Co_Personas, 1) as total_personas
FROM Venta_Encabezado ve
LEFT JOIN Comanda c ON ve.Vn_Documento = c.Co_Folio AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
WHERE ve.Vn_Fecha >= DATEADD(DAY, -1, CONVERT(DATETIME, REPLACE('{fecha_inicio}', '-', ''), 112))
  AND ve.Vn_Fecha < DATEADD(DAY, 2, CONVERT(DATETIME, REPLACE('{fecha_fin}', '-', ''), 112))
  AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
  AND ISNULL(ve.Es_Cve_Estado, '') IN ('AC', 'FA')
ORDER BY ve.Vn_Fecha
"""

QUERY_MPRO_VENTAS_ABIERTAS = """
SELECT 
    SUM(ve.Vn_Precio_Neto_Importe) as ventas_abiertas,
    COUNT(DISTINCT ve.Vn_Folio) as tickets_abiertos,
    SUM(ISNULL(c.Co_Personas, 1)) as pax_abiertos
FROM Venta_Encabezado ve
LEFT JOIN Comanda c ON ve.Vn_Documento = c.Co_Folio AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
WHERE CAST(ve.Vn_Fecha AS DATE) = CAST(GETDATE() AS DATE)
  AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
  AND ISNULL(ve.Es_Cve_Estado, '') IN ('AC', 'FA')
  AND ve.Vn_Tabla = 'Comanda'  -- Ventas aún en comanda (no cerradas)
"""


# =============================================================================
# FUNCIONES DE SYNC POR SISTEMA
# =============================================================================

def sync_softrestaurant_ventas_cerradas(
    config: UnidadNegocioConfig,
    fecha_inicio: date,
    fecha_fin: date,
    run_id: str
) -> SyncResult:
    """
    Sincroniza ventas cerradas de SoftRestaurant hacia EDARSAHUB v2.
    """
    start_time = time.time()
    result = SyncResult(
        success=False,
        run_id=run_id,
        unidad_negocio_pk=config.unidad_negocio_pk
    )
    
    try:
        # Obtener configuración del servidor
        server_config = get_server_connection_config(
            config.server_id,
            config.unidad_negocio_pk,
        )
        if not server_config:
            result.error_message = f"No se encontró configuración para server_id {config.server_id}"
            return result
        
        # Ejecutar exactamente el contrato del reporte oficial por turnos.
        query = build_softrestaurant_ventas_cerradas_query(
            server_config,
            fecha_inicio,
            fecha_fin,
        )
        
        rows, conn_status = execute_query_on_server(server_config, query)
        
        if conn_status != ConnectionStatus.ONLINE:
            result.error_message = f"Conexión fallida: {conn_status}"
            log = SyncLogV2(
                run_id=run_id,
                run_type=SyncRunType.INCREMENTAL,
                unidad_negocio_pk=config.unidad_negocio_pk,
                server_id=config.server_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                status=SyncStatus.FAILED,
                error_message=result.error_message,
                source_connection_status=conn_status,
                duration_seconds=int(time.time() - start_time)
            )
            insert_sync_log(log)
            return result
        
        # Agrupar detalle por fecha_operacion canonica y procesar cada dia operativo
        inserted = 0
        updated = 0
        skipped = 0
        errored = 0
        
        rows_agrupadas = _agrupar_ventas_cerradas_por_fecha_operacion(
            rows,
            config,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        for row in rows_agrupadas:
            try:
                kpi = map_softrestaurant_ventas_cerradas(row, config, run_id)
                upsert_result = upsert_kpi_diario(kpi)
                
                if upsert_result['action'] == 'INSERT':
                    inserted += 1
                elif upsert_result['action'] == 'UPDATE':
                    updated += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                logger.error(f"Error procesando fila SR: {e}")
                errored += 1
        
        # Registrar en log
        result.success = errored == 0
        result.records_processed = len(rows_agrupadas)
        result.records_inserted = inserted
        result.records_updated = updated
        result.records_skipped = skipped
        result.records_errored = errored
        result.duration_seconds = int(time.time() - start_time)
        
        log = SyncLogV2(
            run_id=run_id,
            run_type=SyncRunType.INCREMENTAL,
            unidad_negocio_pk=config.unidad_negocio_pk,
            server_id=config.server_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            status=SyncStatus.SUCCESS if result.success else SyncStatus.PARTIAL,
            records_processed=result.records_processed,
            records_inserted=inserted,
            records_updated=updated,
            records_skipped=skipped,
            records_errored=errored,
            source_connection_status=ConnectionStatus.ONLINE,
            duration_seconds=result.duration_seconds
        )
        insert_sync_log(log)
        
        return result
        
    except Exception as e:
        result.error_message = str(e)
        logger.error(f"Error en sync SoftRestaurant: {e}")
        return result


def sync_mpro_ventas_cerradas(
    config: UnidadNegocioConfig,
    sucursal_id: str,
    fecha_inicio: date,
    fecha_fin: date,
    run_id: str
) -> SyncResult:
    """
    Sincroniza ventas cerradas de MPRO hacia EDARSAHUB v2.
    MPRO tiene múltiples sucursales por servidor.
    """
    start_time = time.time()
    result = SyncResult(
        success=False,
        run_id=run_id,
        unidad_negocio_pk=config.unidad_negocio_pk
    )
    
    try:
        # Obtener configuración del servidor
        server_config = get_server_connection_config(
            config.server_id,
            config.unidad_negocio_pk,
        )
        if not server_config:
            result.error_message = f"No se encontró configuración para server_id {config.server_id}"
            return result
        
        # Ejecutar query con sucursal específica
        query = QUERY_MPRO_VENTAS_CERRADAS.format(
            fecha_inicio=fecha_inicio.isoformat(),
            fecha_fin=fecha_fin.isoformat(),
            sucursal_id=sucursal_id
        )
        
        rows, conn_status = execute_query_on_server(server_config, query)
        
        if conn_status != ConnectionStatus.ONLINE:
            result.error_message = f"Conexión fallida: {conn_status}"
            log = SyncLogV2(
                run_id=run_id,
                run_type=SyncRunType.INCREMENTAL,
                unidad_negocio_pk=config.unidad_negocio_pk,
                server_id=config.server_id,
                sucursal_id=sucursal_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                status=SyncStatus.FAILED,
                error_message=result.error_message,
                source_connection_status=conn_status,
                duration_seconds=int(time.time() - start_time)
            )
            insert_sync_log(log)
            return result
        
        # Actualizar config con sucursal específica para el mapeo
        config_with_sucursal = UnidadNegocioConfig(
            unidad_negocio_pk=config.unidad_negocio_pk,
            unidad_negocio_nombre=config.unidad_negocio_nombre,
            server_id=config.server_id,
            sucursal_id=sucursal_id,
            sucursal_nombre=config.sucursal_nombre,
            sistema_origen=SistemaOrigen.MPRO,
            activo=True
        )
        
        # Agrupar detalle por fecha_operacion canonica y procesar cada dia operativo
        inserted = 0
        updated = 0
        skipped = 0
        errored = 0
        
        rows_agrupadas = _agrupar_ventas_cerradas_por_fecha_operacion(
            rows,
            config_with_sucursal,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        for row in rows_agrupadas:
            try:
                kpi = map_mpro_ventas_cerradas(row, config_with_sucursal, run_id)
                upsert_result = upsert_kpi_diario(kpi)
                
                if upsert_result['action'] == 'INSERT':
                    inserted += 1
                elif upsert_result['action'] == 'UPDATE':
                    updated += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                logger.error(f"Error procesando fila MPRO: {e}")
                errored += 1
        
        # Registrar resultado
        result.success = errored == 0
        result.records_processed = len(rows_agrupadas)
        result.records_inserted = inserted
        result.records_updated = updated
        result.records_skipped = skipped
        result.records_errored = errored
        result.duration_seconds = int(time.time() - start_time)
        
        log = SyncLogV2(
            run_id=run_id,
            run_type=SyncRunType.INCREMENTAL,
            unidad_negocio_pk=config.unidad_negocio_pk,
            server_id=config.server_id,
            sucursal_id=sucursal_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            status=SyncStatus.SUCCESS if result.success else SyncStatus.PARTIAL,
            records_processed=result.records_processed,
            records_inserted=inserted,
            records_updated=updated,
            records_skipped=skipped,
            records_errored=errored,
            source_connection_status=ConnectionStatus.ONLINE,
            duration_seconds=result.duration_seconds
        )
        insert_sync_log(log)
        
        return result
        
    except Exception as e:
        result.error_message = str(e)
        logger.error(f"Error en sync MPRO: {e}")
        return result


# =============================================================================
# FUNCIONES DE SYNC DE ALTO NIVEL
# =============================================================================

def sync_unidad_ventas_cerradas(
    unidad_config: UnidadNegocioConfig,
    fecha_inicio: date,
    fecha_fin: date
) -> SyncResult:
    """
    Sincroniza ventas cerradas de una unidad específica.
    Detecta automáticamente si es SoftRestaurant o MPRO.
    """
    run_id = str(uuid.uuid4())[:8]
    
    if unidad_config.sistema_origen == SistemaOrigen.SOFTRESTAURANT:
        return sync_softrestaurant_ventas_cerradas(
            unidad_config, fecha_inicio, fecha_fin, run_id
        )
    elif unidad_config.sistema_origen == SistemaOrigen.MPRO:
        return sync_mpro_ventas_cerradas(
            unidad_config,
            unidad_config.sucursal_id,
            fecha_inicio,
            fecha_fin,
            run_id
        )
    else:
        return SyncResult(
            success=False,
            run_id=run_id,
            unidad_negocio_pk=unidad_config.unidad_negocio_pk,
            error_message=f"Sistema no soportado: {unidad_config.sistema_origen}"
        )


def sync_todas_unidades_ventas_cerradas(
    fecha_inicio: date,
    fecha_fin: date
) -> List[SyncResult]:
    """
    Sincroniza una vez cada unidad activa del catálogo canónico.

    Cada unidad MPRO ya contiene su server_id y sucursal_origen_id;
    no se expande nuevamente por servidor.
    """
    configs = get_unidades_negocio_config()
    if not configs:
        raise RuntimeError("No existen unidades activas para sincronizar")

    results: List[SyncResult] = []

    for config in configs:
        logger.info(
            "Sincronizando unidad canónica %s, sucursal=%s",
            config.unidad_negocio_nombre,
            config.sucursal_id,
        )
        results.append(
            sync_unidad_ventas_cerradas(
                config,
                fecha_inicio,
                fecha_fin,
            )
        )

    return results



def _get_config_canonica_por_codigo(
    codigo: str
) -> UnidadNegocioConfig:
    """Construye una configuración desde los helpers canónicos."""
    from core.server_registry import get_server_by_unidad_codigo

    row = get_server_by_unidad_codigo(codigo)
    if not row:
        raise RuntimeError(
            f"Unidad no encontrada en catálogo canónico: {codigo}"
        )

    system_type = str(
        row.get("system_type")
        or row.get("unidad_system_type")
        or row.get("servidor_system_type")
        or ""
    ).upper()

    if "SOFT" in system_type:
        sistema = SistemaOrigen.SOFTRESTAURANT
    elif "MPRO" in system_type or "MANAG" in system_type:
        sistema = SistemaOrigen.MPRO
    else:
        raise RuntimeError(
            f"Sistema no soportado para unidad {codigo}: {system_type}"
        )

    unidad_pk = str(row.get("unidad_negocio_pk") or "").strip()
    server_id = str(row.get("server_id") or "").strip()
    nombre = str(row.get("unidad_negocio_nombre") or "").strip()
    sucursal_id = (
        str(row.get("sucursal_origen_id") or "").strip()
        or "DEFAULT"
    )

    if not unidad_pk or not server_id or not nombre:
        raise RuntimeError(
            f"Configuración incompleta para unidad canónica {codigo}"
        )

    if sistema == SistemaOrigen.MPRO and sucursal_id == "DEFAULT":
        raise RuntimeError(
            f"Unidad MPRO sin sucursal_origen_id: {codigo}"
        )

    return UnidadNegocioConfig(
        unidad_negocio_pk=unidad_pk,
        unidad_negocio_nombre=nombre,
        server_id=server_id,
        sucursal_id=sucursal_id,
        sucursal_nombre=nombre,
        sistema_origen=sistema,
        activo=True,
    )


# =============================================================================
# FUNCIÓN DE PRUEBA CONTROLADA (Subfase 1)
# =============================================================================

def test_sync_una_unidad_softrestaurant(fecha: date = None) -> SyncResult:
    """
    Prueba controlada usando únicamente el catálogo canónico.
    No contiene servidor ni sucursal escritos manualmente.
    """
    if fecha is None:
        fecha = date.today() - timedelta(days=1)

    config = _get_config_canonica_por_codigo("ESTELAR")
    return sync_unidad_ventas_cerradas(config, fecha, fecha)



def test_sync_una_unidad_mpro(fecha: date = None) -> SyncResult:
    """
    Prueba controlada usando únicamente el catálogo canónico.
    No contiene servidor ni sucursal escritos manualmente.
    """
    if fecha is None:
        fecha = date.today() - timedelta(days=1)

    config = _get_config_canonica_por_codigo("130QRO")
    return sync_unidad_ventas_cerradas(config, fecha, fecha)



# =============================================================================
# EJECUCIÓN DIRECTA (Solo para pruebas manuales)
# =============================================================================

if __name__ == "__main__":
    """
    Ejecutar manualmente para probar:
    cd /app/backend && python -m modules.comercial_v2.sync_comercial_edarsahub
    """
    import sys
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("SYNC COMERCIAL V2 - Prueba Manual")
    print("=" * 60)
    print("\nEste script NO debe ejecutarse en producción.")
    print("Para pruebas controladas, usar las funciones test_sync_*")
    print("\nDisponibles:")
    print("  - test_sync_una_unidad_softrestaurant(fecha)")
    print("  - test_sync_una_unidad_mpro(fecha)")


# ============================================================
# P1 - Unidades dinámicas desde SQL
# No usar códigos hardcodeados como llave operativa.
# ============================================================

def _sync_codigos_unidades_activas():
    return UnidadesService.get_codigos()



# ============================================================
# P2-25 - unidad_negocio_pk obligatoria para KPI Comercial
# ============================================================

def _resolver_unidad_negocio_pk_obligatoria(unidad_codigo: str) -> str:
    """
    Regla estructural:
    Toda inserción KPI debe resolver unidad_negocio_pk desde Unidades_Negocio.
    unidad_negocio_id queda como código legacy/trazabilidad.
    
    Args:
        unidad_codigo: Código de unidad (130MID, CIENFUEGOS, etc.)
    
    Returns:
        UUID de la unidad
    
    Raises:
        ValueError si no puede resolver
    """
    pk = UnidadesService.resolver_pk(unidad_codigo)
    if not pk:
        raise ValueError(f"P2-25: No se pudo resolver unidad_negocio_pk para unidad={unidad_codigo}")
    return str(pk)


def _validar_payload_kpi_unidad_pk(payload: dict) -> dict:
    """
    Bloquea inserciones KPI sin unidad_negocio_pk.
    
    Args:
        payload: Diccionario con datos del KPI
    
    Returns:
        payload validado
    
    Raises:
        ValueError si falta unidad_negocio_pk
    """
    if not payload.get("unidad_negocio_pk"):
        raise ValueError("P2-25: Payload KPI inválido - unidad_negocio_pk es obligatorio")
    return payload

