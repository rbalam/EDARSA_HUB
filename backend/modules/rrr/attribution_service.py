import hashlib
import json
from typing import Any, Dict, Optional

from core.corporate_filters.service import CorporateFilterService
from core.server_registry import get_server_connection_info
from core.sql_first.db import get_sql_connection

from .schemas import AttributionTransactionRequest


class AttributionConflict(Exception):
    pass


class AttributionInvalidCustomer(Exception):
    pass


class AttributionInvalidCommercial(Exception):
    pass


class AttributionOrgScopeError(Exception):
    pass


def _cursor(conn):
    try:
        return conn.cursor(as_dict=True)
    except TypeError:
        return conn.cursor()


def _one(cur) -> Optional[Dict[str, Any]]:
    row = cur.fetchone()
    if not row:
        return None
    if isinstance(row, dict):
        return row
    cols = [c[0] for c in cur.description] if cur.description else []
    return dict(zip(cols, row))


def _stable_payload_hash(payload: AttributionTransactionRequest) -> str:
    if payload.payload_hash:
        return payload.payload_hash
    data = payload.model_dump(mode="json")
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _resolve_org(payload: AttributionTransactionRequest) -> Dict[str, Any]:
    server = get_server_connection_info(payload.server_id)
    if not server:
        raise AttributionOrgScopeError("server_id no registrado")

    unit = CorporateFilterService.resolver_unidad(payload.unit_source_id)
    unidad_pk = unit.get("pk")
    if not unidad_pk:
        raise AttributionOrgScopeError("unidad no resoluble canonicamente")

    empresa_id = server.get("empresa_id") or server.get("EmpresaID")
    if empresa_id is None:
        raise AttributionOrgScopeError("empresa no resoluble desde server_id")

    return {
        "empresa_id": int(empresa_id),
        "unidad_negocio_id": str(unidad_pk),
    }


def _validate_customer(cur, cliente_id: int) -> None:
    cur.execute(
        "SELECT TOP 1 ClienteID FROM dbo.Cliente_Catalogo WHERE ClienteID = %s",
        (cliente_id,),
    )
    if not cur.fetchone():
        raise AttributionInvalidCustomer("ClienteID no existe en Cliente_Catalogo")


def _find_commercial_fact(cur, payload: AttributionTransactionRequest) -> Optional[Dict[str, Any]]:
    if not payload.commercial_system:
        return None

    keys = [
        payload.native_transaction_id,
        payload.native_ticket_number,
        payload.native_folio,
    ]
    if not any(keys):
        return None

    cur.execute(
        """
        SELECT
            sistema_origen,
            fecha_operacion,
            unidad_negocio_id,
            sucursal_id,
            id_transaccion,
            numero_ticket,
            folio_origen,
            MAX(CASE WHEN ISNULL(cancelado_origen, 0) = 1 THEN 1 ELSE 0 END) AS any_cancelled,
            MIN(CASE WHEN ISNULL(es_kpi_valido, 0) = 1 THEN 1 ELSE 0 END) AS all_valid,
            COUNT_BIG(*) AS detail_rows
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
        WHERE UPPER(sistema_origen) = UPPER(%s)
          AND (
                (%s IS NOT NULL AND id_transaccion = %s)
             OR (%s IS NOT NULL AND numero_ticket = %s)
             OR (%s IS NOT NULL AND folio_origen = %s)
          )
        GROUP BY
            sistema_origen,
            fecha_operacion,
            unidad_negocio_id,
            sucursal_id,
            id_transaccion,
            numero_ticket,
            folio_origen
        """,
        (
            payload.commercial_system,
            payload.native_transaction_id,
            payload.native_transaction_id,
            payload.native_ticket_number,
            payload.native_ticket_number,
            payload.native_folio,
            payload.native_folio,
        ),
    )
    rows = cur.fetchall()
    if not rows:
        return None
    if len(rows) != 1:
        raise AttributionConflict("la llave comercial exacta produjo multiples transacciones logicas")

    row = rows[0] if isinstance(rows[0], dict) else dict(zip([c[0] for c in cur.description], rows[0]))
    if int(row.get("any_cancelled") or 0) != 0 or int(row.get("all_valid") or 0) != 1:
        raise AttributionInvalidCommercial("la transaccion comercial esta cancelada o no es KPI valida")
    return row


def process_attribution(payload: AttributionTransactionRequest) -> Dict[str, Any]:
    if payload.cliente_id is None:
        return {
            "status": "ACCEPTED_PENDING_CUSTOMER",
            "source_key": payload.source_transaction_uuid,
            "attributed": False,
            "message": "transaccion recibida sin ClienteID explicito",
        }

    org = _resolve_org(payload)
    payload_hash = _stable_payload_hash(payload)

    with get_sql_connection() as conn:
        cur = _cursor(conn)
        _validate_customer(cur, payload.cliente_id)

        cur.execute(
            """
            SELECT TOP 1
                EventoID, ClienteID, EmpresaID, UnidadNegocioID,
                SourceSystem, SourceKey, PayloadHash, FechaOperacion
            FROM dbo.RRR_Eventos
            WHERE SourceSystem = %s AND SourceKey = %s
            """,
            (payload.source_system, payload.source_transaction_uuid),
        )
        existing = _one(cur)
        if existing:
            same_customer = int(existing["ClienteID"]) == int(payload.cliente_id)
            same_hash = not existing.get("PayloadHash") or existing.get("PayloadHash") == payload_hash
            if same_customer and same_hash:
                return {
                    "status": "IDEMPOTENT_REPLAY",
                    "source_key": payload.source_transaction_uuid,
                    "attributed": True,
                    "event_id": existing.get("EventoID"),
                    "fecha_operacion": str(existing.get("FechaOperacion")) if existing.get("FechaOperacion") else None,
                    "message": "evento ya atribuido con la misma identidad",
                }
            raise AttributionConflict("SourceKey ya existe con identidad o payload materialmente distinto")

        fact = _find_commercial_fact(cur, payload)
        if fact is None:
            return {
                "status": "ACCEPTED_PENDING_COMMERCIAL",
                "source_key": payload.source_transaction_uuid,
                "attributed": False,
                "message": "falta acknowledgement/llave comercial exacta",
            }

        fact_unit = CorporateFilterService.resolver_unidad(fact.get("unidad_negocio_id"))
        if fact_unit.get("pk") and str(fact_unit.get("pk")) != str(org["unidad_negocio_id"]):
            raise AttributionOrgScopeError("unidad del hecho comercial no coincide con la unidad canonica solicitada")

        cur.execute(
            """
            INSERT INTO dbo.RRR_Eventos (
                ClienteID, EmpresaID, UnidadNegocioID, VentaID,
                TipoEvento, SourceSystem, SourceKey, FechaOperacion,
                OcurridoAtUtc, PayloadHash, EstadoValidacion,
                EstadoAntifraude, MotivoRechazo, FechaCreacion
            )
            OUTPUT INSERTED.EventoID
            VALUES (
                %s, %s, %s, NULL,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, NULL, SYSUTCDATETIME()
            )
            """,
            (
                payload.cliente_id,
                org["empresa_id"],
                org["unidad_negocio_id"],
                "ACTIVIDAD_COMERCIAL",
                payload.source_system,
                payload.source_transaction_uuid,
                fact["fecha_operacion"],
                payload.occurred_at_utc,
                payload_hash,
                "VALIDADO",
                "PENDIENTE",
            ),
        )
        inserted = _one(cur)
        conn.commit()

        return {
            "status": "ATTRIBUTED",
            "source_key": payload.source_transaction_uuid,
            "attributed": True,
            "event_id": inserted.get("EventoID") if inserted else None,
            "fecha_operacion": str(fact["fecha_operacion"]),
            "message": "atribucion determinista persistida",
        }
