"""Sincronización canónica de Cortes Z desde POS hacia EDARSAHUB SQL.

Las conexiones POS solo se abren dentro de este job. Los endpoints de usuario
siguen leyendo exclusivamente ``dbo.Finanzas_CortesCaja``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from core.connections.pos_runtime_resolver import PosRuntimeContext
from core.sql_first.connection_factory import get_external_sql_connection
from core.system_type_utils import is_mpro_system, is_softrestaurant_system
from modules.finanzas.sync_cortes_mpro import (
    calcular_hash_origen_mpro,
    registrar_sync_log_mpro,
    sincronizar_a_edarsahub_mpro,
)
from modules.finanzas.sync_cortes_softrestaurant import (
    calcular_hash_origen,
    registrar_sync_log,
    sincronizar_a_edarsahub,
)

logger = logging.getLogger(__name__)


def _resolve_dates(fecha_desde, fecha_hasta, dias_atras):
    end = fecha_hasta or datetime.now()
    start = fecha_desde or (end - timedelta(days=dias_atras))
    return start, end


def _sync_mapping(context: PosRuntimeContext) -> dict:
    return {
        "unidad_negocio_id": context.unidad_negocio_pk,
        "unidad_codigo": context.unidad_codigo,
        "unidad_nombre": context.unidad_nombre,
        "empresa_id": context.empresa_id,
        "server_id": context.server_id,
        "sucursal_origen_id": context.sucursal_origen_id,
        "sucursal_legacy_id": context.sucursal_legacy_id,
        "system_type": context.system_type,
        "host": context.host,
        "port": context.port,
        "instance": context.instance,
        "database": context.database,
        "user": context.username,
        "password": context.password,
    }


def _extract_softrestaurant(
    context: PosRuntimeContext,
    fecha_desde: datetime,
    fecha_hasta: datetime,
) -> list[dict]:
    connection = get_external_sql_connection(
        context.external_connection_config(as_dict=True)
    )
    try:
        cursor = connection.cursor(as_dict=True)
        cursor.execute(
            """
            SELECT
                idturnointerno, idturno, apertura, cierre, idestacion,
                cajero, efectivo, tarjeta, vales, credito, fondo, idempresa
            FROM turnos
            WHERE cierre IS NOT NULL
              AND cierre >= %s
              AND cierre < %s
            ORDER BY cierre ASC
            """,
            (fecha_desde, fecha_hasta),
        )
        rows = cursor.fetchall()
    finally:
        connection.close()

    records = []
    for row in rows:
        record = {
            "UnidadNegocioID": context.unidad_negocio_pk,
            "UnidadNegocioNombre": context.unidad_nombre,
            "ServerID": context.server_id,
            "EmpresaID": row.get("idempresa"),
            "SistemaOrigen": "SoftRestaurant",
            "BaseDatosOrigen": context.database,
            "TablaOrigen": "turnos",
            "IdOrigen": row["idturnointerno"],
            "FolioCorte": str(row["idturno"]),
            "FechaCorte": row["cierre"].date() if row.get("cierre") else None,
            "FechaApertura": row.get("apertura"),
            "FechaCierre": row.get("cierre"),
            "CajaID": row.get("idestacion"),
            "CajaNombre": row.get("idestacion"),
            "CajeroID": row.get("cajero"),
            "CajeroNombre": row.get("cajero"),
            "TurnoID": None,
            "TotalEfectivo": float(row.get("efectivo") or 0),
            "TotalTarjetaDebito": float(row.get("tarjeta") or 0),
            "TotalTarjetaCredito": float(row.get("credito") or 0),
            "TotalVales": float(row.get("vales") or 0),
            "FondoInicial": float(row.get("fondo") or 0),
            "TotalVenta": sum(
                float(row.get(key) or 0)
                for key in ("efectivo", "tarjeta", "credito", "vales")
            ),
            "Propinas": 0,
            "Retiros": 0,
            "TotalAmex": 0,
            "TotalInternacional": 0,
            "TotalOtros": 0,
            "EsDemo": 0,
            "Activo": 1,
        }
        record["HashOrigen"] = calcular_hash_origen(record)
        records.append(record)
    return records


def _extract_mpro(
    context: PosRuntimeContext,
    fecha_desde: datetime,
    fecha_hasta: datetime,
) -> list[dict]:
    if not context.sucursal_origen_id:
        raise ValueError(
            f"Unidad {context.unidad_codigo} sin sucursal_origen_id canónica"
        )

    connection = get_external_sql_connection(
        context.external_connection_config(as_dict=True)
    )
    try:
        cursor = connection.cursor(as_dict=True)
        cursor.execute(
            """
            SELECT
                Cc_Folio, Cc_Fecha, Sc_Cve_Sucursal, Cc_Turno, Cc_Caja,
                Cc_Cajero, Cc_Importe_Pago, Cc_Importe_Venta,
                Cc_Importe_Declarado, Cc_Importe_Retirado,
                Cc_Importe_Descuento, Cc_Venta_Contado,
                Cc_Venta_Credito, Es_Cve_Estado
            FROM Comanda_Corte
            WHERE Sc_Cve_Sucursal = %s
              AND Cc_Fecha >= %s
              AND Cc_Fecha < %s
              AND (Es_Cve_Estado IS NULL OR Es_Cve_Estado != 'BAJA')
            ORDER BY Cc_Fecha ASC, Cc_Turno ASC
            """,
            (context.sucursal_origen_id, fecha_desde, fecha_hasta),
        )
        rows = cursor.fetchall()
    finally:
        connection.close()

    records = []
    for row in rows:
        venta_credito = float(row.get("Cc_Venta_Credito") or 0)
        record = {
            "UnidadNegocioID": context.unidad_negocio_pk,
            "UnidadNegocioNombre": context.unidad_nombre,
            "ServerID": context.server_id,
            "EmpresaID": context.empresa_id,
            "SistemaOrigen": "MPRO",
            "BaseDatosOrigen": context.database,
            "TablaOrigen": "Comanda_Corte",
            "IdOrigen": row["Cc_Folio"],
            "FolioCorte": row["Cc_Folio"],
            "SucursalOrigenID": row.get("Sc_Cve_Sucursal"),
            "FechaCorte": row["Cc_Fecha"].date() if row.get("Cc_Fecha") else None,
            "FechaApertura": None,
            "FechaCierre": row.get("Cc_Fecha"),
            "CajaID": row.get("Cc_Caja"),
            "CajaNombre": row.get("Cc_Caja"),
            "CajeroID": row.get("Cc_Cajero"),
            "CajeroNombre": row.get("Cc_Cajero"),
            "TurnoID": row.get("Cc_Turno"),
            "TotalEfectivo": float(row.get("Cc_Venta_Contado") or 0),
            "TotalTarjetaDebito": venta_credito / 2 if venta_credito else 0,
            "TotalTarjetaCredito": venta_credito / 2 if venta_credito else 0,
            "TotalVales": 0,
            "FondoInicial": 0,
            "TotalVenta": float(row.get("Cc_Importe_Venta") or 0),
            "TotalPago": float(row.get("Cc_Importe_Pago") or 0),
            "TotalDeclarado": float(row.get("Cc_Importe_Declarado") or 0),
            "Propinas": 0,
            "Retiros": abs(float(row.get("Cc_Importe_Retirado") or 0)),
            "TotalAmex": 0,
            "TotalInternacional": 0,
            "TotalOtros": 0,
            "TotalDescuento": float(row.get("Cc_Importe_Descuento") or 0),
            "EsDemo": 0,
            "Activo": 1,
        }
        record["HashOrigen"] = calcular_hash_origen_mpro(record)
        records.append(record)
    return records


def sync_cortes_z_context(
    context: PosRuntimeContext,
    *,
    fecha_desde: datetime | None = None,
    fecha_hasta: datetime | None = None,
    dias_atras: int = 2,
    tipo_ejecucion: str = "SCHEDULER",
) -> Dict[str, Any]:
    start, end = _resolve_dates(fecha_desde, fecha_hasta, dias_atras)
    started = datetime.now()
    result: Dict[str, Any] = {
        "unidad": context.unidad_nombre,
        "unidad_codigo": context.unidad_codigo,
        "sistema": context.system_type,
        "server_id": context.server_id,
        "fecha_desde": start.isoformat(),
        "fecha_hasta": end.isoformat(),
        "stats": {},
        "estatus": "ERROR",
        "error": None,
    }

    try:
        mapping = _sync_mapping(context)
        if is_softrestaurant_system(context.system_type):
            records = _extract_softrestaurant(context, start, end)
            stats = sincronizar_a_edarsahub(records, mapping)
            result["estatus"] = "PARCIAL" if stats["errores"] else "COMPLETADO"
            registrar_sync_log(
                unidad_id=context.unidad_negocio_pk,
                server_id=context.server_id,
                sistema_origen="SoftRestaurant",
                fecha_desde=start,
                fecha_hasta=end,
                stats=stats,
                estatus=result["estatus"],
                duracion_segundos=int((datetime.now() - started).total_seconds()),
                tipo_ejecucion=tipo_ejecucion,
            )
        elif is_mpro_system(context.system_type):
            records = _extract_mpro(context, start, end)
            stats = sincronizar_a_edarsahub_mpro(records, mapping)
            result["estatus"] = "PARCIAL" if stats["errores"] else "COMPLETADO"
            registrar_sync_log_mpro(
                unidad_id=context.unidad_negocio_pk,
                server_id=context.server_id,
                fecha_desde=start,
                fecha_hasta=end,
                stats=stats,
                estatus=result["estatus"],
                duracion_segundos=int((datetime.now() - started).total_seconds()),
                tipo_ejecucion=tipo_ejecucion,
            )
        else:
            raise ValueError(
                f"system_type no soportado para Cortes Z: {context.system_type}"
            )
        result["stats"] = stats
    except Exception as exc:
        result["error"] = str(exc)
        logger.exception(
            "[CORTES_Z_SYNC] Error unidad=%s codigo=%s",
            context.unidad_nombre,
            context.unidad_codigo,
        )
    finally:
        result["duracion_segundos"] = int(
            (datetime.now() - started).total_seconds()
        )
    return result


__all__ = ["sync_cortes_z_context"]
