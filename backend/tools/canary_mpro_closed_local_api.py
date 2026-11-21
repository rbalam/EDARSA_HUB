#!/usr/bin/env python3
"""Read-only canary for MPRO closed sales through canonical local APIs.

No writes to EDARSAHUB. No CENTRAL2020 fallback. No replication trigger.
"""

import json
from datetime import date, timedelta
from decimal import Decimal

from core.unidades_service import UnidadesService
from modules.comercial_v2.mpro_closed_api import (
    build_mpro_closed_sales_query,
    execute_mpro_select_via_api,
    resolve_mpro_closed_api,
)
from modules.comercial_v2.ticket_snapshot import (
    QUERY_MPRO_DETALLE_CERRADAS_CANONICAS,
    QUERY_MPRO_DETALLE_CERRADAS_CANONICAS_COMANDA,
    QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES,
)
from modules.comercial_v2.schemas import ConnectionStatus


UNITS = ("ORIGEN", "130QRO")


def _num(value):
    return Decimal(str(value or 0))


def _summary(rows):
    rows = rows or []
    folios = {
        str(row.get("Vn_Folio") or "").strip()
        for row in rows
        if str(row.get("Vn_Folio") or "").strip()
    }
    return {
        "rows": len(rows),
        "tickets": len(folios) if folios else len(rows),
        "ventas": str(
            sum((_num(row.get("Vn_Precio_Neto_Importe")) for row in rows), Decimal("0"))
        ),
        "propinas": str(
            sum((_num(row.get("propinas")) for row in rows), Decimal("0"))
        ),
        "pax": int(
            sum((_num(row.get("total_personas")) for row in rows), Decimal("0"))
        ),
    }


def _safe_source(api_config):
    return {
        "unidad_codigo": api_config.get("unidad_codigo"),
        "server_name": api_config.get("server_name"),
        "sucursal_id": api_config.get("sucursal_id"),
        "role": api_config.get("role"),
    }


def _run_query(api_config, query, label):
    if not str(query or "").lstrip().upper().startswith("SELECT"):
        raise RuntimeError(f"{label}: query no comienza con SELECT")

    rows, status = execute_mpro_select_via_api(api_config, query)
    print(json.dumps({
        "label": label,
        "status": str(status.value if hasattr(status, "value") else status),
        "rows": len(rows or []),
    }, ensure_ascii=False))

    if status != ConnectionStatus.ONLINE:
        raise RuntimeError(f"{label}: API local no respondió ONLINE")

    return rows


def main():
    today = date.today()
    dates = (today - timedelta(days=1), today)
    failures = []

    for code in UNITS:
        unit = UnidadesService.get_by_codigo(code)
        if not unit:
            failures.append(f"{code}: unidad no resuelta")
            continue

        unidad_pk = unit.get("unidad_negocio_pk")
        api = resolve_mpro_closed_api(unidad_pk)
        if not api:
            failures.append(f"{code}: API local canónica no resuelta")
            continue

        print("CANARY_SOURCE=" + json.dumps(_safe_source(api), ensure_ascii=False))

        for target_date in dates:
            try:
                closed_query = build_mpro_closed_sales_query(
                    code,
                    api.get("sucursal_id"),
                    target_date,
                    target_date,
                )
                closed_rows = _run_query(
                    api,
                    closed_query,
                    f"{code}:{target_date.isoformat()}:closed_sales",
                )
                print("CANARY_TOTAL=" + json.dumps({
                    "unidad": code,
                    "fecha": target_date.isoformat(),
                    **_summary(closed_rows),
                }, ensure_ascii=False))

                canonical_detail = QUERY_MPRO_DETALLE_CERRADAS_CANONICAS.format(
                    sucursal_id=api.get("sucursal_id"),
                    fecha_operacion=target_date.isoformat(),
                )
                _run_query(
                    api,
                    canonical_detail,
                    f"{code}:{target_date.isoformat()}:canonical_detail",
                )

                comanda_detail = QUERY_MPRO_DETALLE_CERRADAS_CANONICAS_COMANDA.format(
                    sucursal_id=api.get("sucursal_id"),
                    fecha_operacion=target_date.isoformat(),
                )
                _run_query(
                    api,
                    comanda_detail,
                    f"{code}:{target_date.isoformat()}:canonical_comanda_detail",
                )

                provisional_detail = QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES.format(
                    sucursal_id=api.get("sucursal_id"),
                    fecha_operacion=target_date.isoformat(),
                )
                _run_query(
                    api,
                    provisional_detail,
                    f"{code}:{target_date.isoformat()}:provisional_detail",
                )

            except Exception as exc:
                failures.append(f"{code}:{target_date.isoformat()}: {exc}")

    if failures:
        print("CANARY_FAILURES=" + json.dumps(failures, ensure_ascii=False))
        raise SystemExit(2)

    print("CANARY_RESULT=PASS_READ_ONLY_LOCAL_APIS")


if __name__ == "__main__":
    main()
