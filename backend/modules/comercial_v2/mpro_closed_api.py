"""MPRO closed-sales source via the canonical local API relationship.

This module is intentionally isolated from sync_comercial_abiertas_v2_job.
It resolves the source from EDARSAHUB metadata and never falls back to the
shared MPRO SQL server for incremental closed sales.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import requests

from .schemas import ConnectionStatus


logger = logging.getLogger(__name__)

MPRO_CLOSED_SALES_API_ROLE = "VENTAS_DIA_API_LOCAL"


def resolve_mpro_closed_api(
    unidad_negocio_pk: str,
) -> Optional[Dict[str, Any]]:
    """Resolve the MPRO local API assigned to a canonical business unit.

    Resolution path:
        Unidades_Negocio PK -> canonical code -> Sistema_Empresas
        -> Sistema_EmpresasServidores(RolConexion=VENTAS_DIA_API_LOCAL)
        -> Servidores_Conexiones(API_LOCAL)

    The function is fail-closed. It does not fall back to CENTRAL2020 or any
    other shared SQL source when the local API relationship is unavailable.
    """

    from core.empresa_resolver import (
        get_connection_for_role,
        resolve_empresa_by_alias,
    )
    from core.secret_manager import decrypt_secret
    from core.sql_first.db import fetch_one_dict_readonly
    from core.unidades_service import UnidadesService

    unidad_codigo = UnidadesService.resolver_codigo(unidad_negocio_pk)
    if not unidad_codigo:
        logger.error(
            "[MPRO_CLOSED_API] Unidad canónica no resuelta: pk=%s",
            unidad_negocio_pk,
        )
        return None

    empresa = resolve_empresa_by_alias(unidad_codigo)
    if not empresa:
        logger.error(
            "[MPRO_CLOSED_API] Empresa no resuelta para unidad=%s",
            unidad_codigo,
        )
        return None

    relation = get_connection_for_role(
        empresa.empresa_id,
        MPRO_CLOSED_SALES_API_ROLE,
    )
    if not relation:
        logger.error(
            "[MPRO_CLOSED_API] Sin relación %s para unidad=%s empresa_id=%s",
            MPRO_CLOSED_SALES_API_ROLE,
            unidad_codigo,
            empresa.empresa_id,
        )
        return None

    row = fetch_one_dict_readonly(
        """
        SELECT TOP (1)
            id,
            nombre,
            api_url,
            api_key_encrypted,
            system_type,
            tipo_conexion,
            activo
        FROM dbo.Servidores_Conexiones
        WHERE id = %s
          AND tipo_conexion = 'API_LOCAL'
          AND activo = 1
        """,
        (str(relation.servidor_id),),
    )

    if not row or not str(row.get("api_url") or "").strip():
        logger.error(
            "[MPRO_CLOSED_API] API_LOCAL no disponible para unidad=%s servidor=%s",
            unidad_codigo,
            relation.servidor_id,
        )
        return None

    api_key_raw = row.get("api_key_encrypted")
    try:
        api_key = decrypt_secret(api_key_raw) if api_key_raw else ""
    except Exception as exc:
        logger.error(
            "[MPRO_CLOSED_API] No se pudo descifrar API key para unidad=%s: %s",
            unidad_codigo,
            type(exc).__name__,
        )
        return None

    sucursal_id = (
        relation.codigo_sucursal_sistema
        or relation.numero_sucursal_sistema
        or ""
    )

    return {
        "unidad_codigo": str(unidad_codigo).strip().upper(),
        "empresa_id": empresa.empresa_id,
        "server_id": str(relation.servidor_id),
        "server_name": row.get("nombre"),
        "api_url": str(row.get("api_url")).strip(),
        "api_key": api_key,
        "sucursal_id": str(sucursal_id).strip(),
        "role": MPRO_CLOSED_SALES_API_ROLE,
    }


def build_mpro_closed_sales_query(
    unidad_codigo: str,
    sucursal_id: str,
    fecha_inicio,
    fecha_fin,
) -> str:
    """Build the canonical final closed-sales SELECT for MPRO local APIs.

    ORIGEN and 130QRO share the same final accounting authority:
    Venta_Encabezado.Vn_Precio_Neto_Importe.  Comanda/Comanda_Detalle may be
    used only by the isolated intraday provisional path while the final header
    is not yet available; it is never authoritative for persisted closed KPIs.
    """

    codigo = str(unidad_codigo or "").strip().upper()
    sucursal = str(sucursal_id or "").strip()
    inicio = fecha_inicio.strftime("%Y%m%d")
    fin = fecha_fin.strftime("%Y%m%d")

    if codigo not in {"ORIGEN", "130QRO"}:
        raise ValueError(
            f"Unsupported MPRO closed-sales unit: {codigo or 'EMPTY'}"
        )

    return f"""
SELECT
    ve.Vn_Fecha AS fecha_hora,
    ve.Vn_Folio AS Vn_Folio,
    ve.Vn_Precio_Neto_Importe AS Vn_Precio_Neto_Importe,
    ISNULL(c.Co_Propina, 0) AS propinas,
    ISNULL(c.Co_Personas, 0) AS total_personas
FROM Venta_Encabezado AS ve
LEFT JOIN Comanda AS c
    ON c.Co_Folio = ve.Vn_Documento
   AND c.Sc_Cve_Sucursal = ve.Sc_Cve_Sucursal
WHERE ve.Vn_Fecha >= CONVERT(datetime, '{inicio}', 112)
  AND ve.Vn_Fecha < DATEADD(day, 1, CONVERT(datetime, '{fin}', 112))
  AND ve.Sc_Cve_Sucursal = '{sucursal}'
  AND ISNULL(ve.Vn_Tabla, '') = 'Comanda'
  AND ISNULL(ve.Es_Cve_Estado, '') IN ('AC', 'FA')
  AND ve.Fecha_Baja IS NULL
ORDER BY ve.Vn_Fecha
"""


def execute_mpro_select_via_api(
    api_config: Dict[str, Any],
    query: str,
    timeout: int = 30,
) -> Tuple[List[Dict[str, Any]], ConnectionStatus]:
    """Execute one read-only SELECT against an MPRO local API.

    Queries that do not begin with SELECT are rejected locally so the caller
    can never bypass the API's read-only contract.
    """

    normalized_query = str(query or "").lstrip()
    if not normalized_query.upper().startswith("SELECT"):
        raise ValueError(
            "MPRO local API closed-sales query must begin with SELECT"
        )

    api_url = str((api_config or {}).get("api_url") or "").strip()
    if not api_url:
        return [], ConnectionStatus.OFFLINE

    headers = {}
    api_key = (api_config or {}).get("api_key")
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        response = requests.get(
            api_url,
            params={"sql": query},
            headers=headers,
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        return [], ConnectionStatus.TIMEOUT
    except requests.exceptions.RequestException as exc:
        logger.error(
            "[MPRO_CLOSED_API] Error de conexión unidad=%s: %s",
            (api_config or {}).get("unidad_codigo"),
            type(exc).__name__,
        )
        return [], ConnectionStatus.OFFLINE

    if response.status_code != 200:
        response_detail = ""
        try:
            payload_error = response.json()
            response_detail = str(
                payload_error.get("detail")
                or payload_error.get("error")
                or payload_error
            )
        except Exception:
            response_detail = str(response.text or "")

        logger.error(
            "[MPRO_CLOSED_API] HTTP %s unidad=%s servidor=%s detail=%s",
            response.status_code,
            (api_config or {}).get("unidad_codigo"),
            (api_config or {}).get("server_name"),
            response_detail[:800],
        )
        return [], ConnectionStatus.OFFLINE

    try:
        payload = response.json()
    except ValueError:
        logger.error(
            "[MPRO_CLOSED_API] Respuesta JSON inválida unidad=%s",
            (api_config or {}).get("unidad_codigo"),
        )
        return [], ConnectionStatus.OFFLINE

    if isinstance(payload, dict):
        rows = payload.get("data", [])
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = []

    if rows is None:
        rows = []

    if not isinstance(rows, list):
        logger.error(
            "[MPRO_CLOSED_API] Contrato data inválido unidad=%s",
            (api_config or {}).get("unidad_codigo"),
        )
        return [], ConnectionStatus.OFFLINE

    return rows, ConnectionStatus.ONLINE
