#!/usr/bin/env python3
"""Backfill selectivo del detalle canónico de Inteligencia Comercial.

Objetivo:
- Detectar días cuyo KPI Runtime ya existe pero cuyo detalle falta o no concilia.
- Reutilizar el extractor/validador canónico existente.
- Dry-run por defecto.
- Escribir únicamente con --commit.
- Nunca escribir días que no pasan OK_HEADER_CANONICO.

Este script no recalcula KPIs ni modifica headers. Solo repara
`dbo.Comercial_Inteligencia_VentasDetalleProducto` para unidad+fecha+sistema
cuando la extracción POS concilia contra Runtime V2.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from scripts.poblar_ventas_detalle_producto_canonico import (
    DESTINO,
    TOLERANCIA_VENTAS,
    _as_date,
    _d,
    _daterange,
    _load_runtime_rows,
    _query_edarsahub_dicts,
    _runtime_for,
    _runtime_metrics,
    _safe_print,
    get_pos_config_for_unidad,
    get_unidades_negocio_pos,
    sync_detalle_producto_canonico_dia,
)


def _detalle_existente(
    unidad_codigo: str,
    fecha_inicio: date,
    fecha_fin: date,
) -> Dict[date, Dict[str, Any]]:
    rows = _query_edarsahub_dicts(
        f"""
        WITH detalle_ticket AS (
            SELECT
                fecha_operacion,
                numero_ticket,
                SUM(CAST(ISNULL(importe_neto, 0) AS decimal(19,4))) AS ventas_ticket,
                MAX(CAST(ISNULL(pax, 0) AS bigint)) AS pax_ticket
            FROM {DESTINO}
            WHERE unidad_negocio_id = %s
              AND fecha_operacion >= %s
              AND fecha_operacion < %s
              AND ISNULL(activo, 1) = 1
              AND ISNULL(es_kpi_valido, 1) = 1
            GROUP BY fecha_operacion, numero_ticket
        )
        SELECT
            fecha_operacion,
            SUM(ventas_ticket) AS ventas_detalle,
            COUNT(*) AS tickets_detalle,
            SUM(pax_ticket) AS pax_detalle
        FROM detalle_ticket
        GROUP BY fecha_operacion
        """,
        (
            unidad_codigo,
            fecha_inicio.isoformat(),
            fecha_fin.isoformat(),
        ),
    )

    out: Dict[date, Dict[str, Any]] = {}
    for row in rows:
        dia = _as_date(row["fecha_operacion"])
        out[dia] = {
            "ventas": _d(row.get("ventas_detalle")),
            "tickets": int(_d(row.get("tickets_detalle"))),
            "pax": int(_d(row.get("pax_detalle"))),
        }
    return out


def _detalle_concilia(
    detalle: Optional[Dict[str, Any]],
    runtime: Dict[str, Any],
) -> bool:
    if not detalle:
        return False

    delta = abs(_d(detalle.get("ventas")) - _d(runtime.get("ventas")))
    return (
        delta <= TOLERANCIA_VENTAS
        and int(detalle.get("tickets") or 0) == int(runtime.get("tickets") or 0)
        and int(detalle.get("pax") or 0) == int(runtime.get("pax") or 0)
    )


def _safe_error_code(exc: Exception) -> str:
    text = str(exc or "").upper()
    rules = (
        ("TICKET SIN DETALLE MONETARIO DISTRIBUIBLE", "MPRO_NO_DISTRIBUTABLE_DETAIL"),
        ("VENTA NETA INCONSISTENTE", "MPRO_INCONSISTENT_HEADER_NET"),
        ("IMPORTE BRUTO NEGATIVO", "MPRO_NEGATIVE_GROSS"),
        ("RESIDUO DE PRORRATEO INVALIDO", "MPRO_INVALID_ALLOCATION_RESIDUAL"),
        ("VENTA NETA DISTRIBUIDA NO CONCILIA", "MPRO_ALLOCATION_TOTAL_MISMATCH"),
        ("INVALID COLUMN", "POS_SCHEMA_INVALID_COLUMN"),
        ("INVALID OBJECT", "POS_SCHEMA_INVALID_OBJECT"),
        ("DEADLOCK", "POS_DEADLOCK"),
        ("1205", "POS_DEADLOCK"),
        ("LOGIN FAILED", "POS_LOGIN_FAILED"),
        ("SIN CONEXIÓN POS", "POS_CONNECTION_UNAVAILABLE"),
        ("SIN CONEXION POS", "POS_CONNECTION_UNAVAILABLE"),
        ("REQUIERE SUCURSAL_ORIGEN_ID", "MPRO_BRANCH_MISSING"),
    )
    for needle, code in rules:
        if needle in text:
            return code
    return f"{type(exc).__name__.upper()}_UNCLASSIFIED"


def ejecutar_backfill(
    fecha_inicio: date,
    fecha_fin: date,
    unidades: Optional[List[str]] = None,
    commit: bool = False,
) -> Tuple[int, Dict[str, Any]]:
    if fecha_fin <= fecha_inicio:
        raise ValueError("fecha_fin debe ser mayor que fecha_inicio")

    run_id = f"backfill_detalle_{datetime.utcnow():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"
    unidades_raw = get_unidades_negocio_pos(unidades or None)
    runtime_rows = _load_runtime_rows(
        fecha_inicio,
        fecha_fin,
        None,
    )

    resumen: Dict[str, Any] = {
        "run_id": run_id,
        "modo": "COMMIT" if commit else "DRY_RUN",
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin_exclusivo": fecha_fin.isoformat(),
        "unidades": [],
        "dias_evaluados": 0,
        "dias_ya_ok": 0,
        "dias_candidatos": 0,
        "dias_reparables": 0,
        "dias_bloqueados": 0,
        "dias_sin_runtime": 0,
        "filas_insertadas": 0,
    }

    for unidad_row in unidades_raw:
        cfg = get_pos_config_for_unidad(unidad_row)
        unidad_codigo = str(cfg.get("unidad_codigo") or "").strip()
        if not unidad_codigo:
            raise RuntimeError("Unidad sin código canónico")

        detalle_actual = _detalle_existente(
            unidad_codigo,
            fecha_inicio,
            fecha_fin,
        )

        unidad_resumen = {
            "unidad": unidad_codigo,
            "ya_ok": 0,
            "candidatos": 0,
            "reparables": 0,
            "bloqueados": 0,
            "sin_runtime": 0,
            "filas_insertadas": 0,
            "dias": [],
        }

        for dia in _daterange(fecha_inicio, fecha_fin):
            resumen["dias_evaluados"] += 1
            rt_row = _runtime_for(runtime_rows, cfg, dia)
            if not rt_row:
                item = {
                    "fecha_operacion": dia.isoformat(),
                    "status": "SIN_RUNTIME",
                }
                unidad_resumen["dias"].append(item)
                unidad_resumen["sin_runtime"] += 1
                resumen["dias_sin_runtime"] += 1
                continue

            runtime = _runtime_metrics(rt_row)
            actual = detalle_actual.get(dia)

            if _detalle_concilia(actual, runtime):
                item = {
                    "fecha_operacion": dia.isoformat(),
                    "status": "YA_CONCILIADO",
                    "ventas": str(runtime["ventas"]),
                    "tickets": runtime["tickets"],
                    "pax": runtime["pax"],
                }
                unidad_resumen["dias"].append(item)
                unidad_resumen["ya_ok"] += 1
                resumen["dias_ya_ok"] += 1
                continue

            unidad_resumen["candidatos"] += 1
            resumen["dias_candidatos"] += 1

            try:
                result = sync_detalle_producto_canonico_dia(
                    cfg=cfg,
                    dia=dia,
                    runtime_row=rt_row,
                    run_id=run_id,
                    commit=commit,
                    excluir_abiertas=True,
                )
            except Exception as exc:
                result = {
                    "status": "ERROR",
                    "unidad": unidad_codigo,
                    "fecha_operacion": dia,
                    "error_type": type(exc).__name__,
                    "error_code": _safe_error_code(exc),
                    "filas_insertadas": 0,
                }

            status = str(result.get("status") or "ERROR")
            item = {
                "fecha_operacion": dia.isoformat(),
                "status": status,
                "ventas_runtime": str(result.get("ventas_runtime", runtime["ventas"])),
                "ventas_pos": str(result.get("ventas_por_ticket", "")),
                "delta_ventas": str(result.get("delta_ventas", "")),
                "tickets_runtime": result.get("tickets_runtime", runtime["tickets"]),
                "tickets_pos": result.get("tickets_por_ticket"),
                "delta_tickets": result.get("delta_tickets"),
                "pax_runtime": result.get("pax_runtime", runtime["pax"]),
                "pax_pos": result.get("pax_por_ticket"),
                "delta_pax": result.get("delta_pax"),
                "filas_insertadas": int(result.get("filas_insertadas") or 0),
            }
            if result.get("error_type"):
                item["error_type"] = str(result["error_type"])
            if result.get("error_code"):
                item["error_code"] = str(result["error_code"])

            unidad_resumen["dias"].append(item)

            if status == "OK_HEADER_CANONICO":
                unidad_resumen["reparables"] += 1
                resumen["dias_reparables"] += 1
                filas = int(result.get("filas_insertadas") or 0)
                unidad_resumen["filas_insertadas"] += filas
                resumen["filas_insertadas"] += filas
            else:
                unidad_resumen["bloqueados"] += 1
                resumen["dias_bloqueados"] += 1

        resumen["unidades"].append(unidad_resumen)

    return (1 if resumen["dias_bloqueados"] else 0), resumen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fecha-inicio", required=True)
    ap.add_argument("--fecha-fin", required=True, help="Fecha fin exclusiva YYYY-MM-DD")
    ap.add_argument(
        "--unidad",
        action="append",
        default=None,
        help="Código/UUID/nombre de unidad. Repetible. Si se omite procesa todas.",
    )
    ap.add_argument(
        "--commit",
        action="store_true",
        default=False,
        help="Escribe únicamente días que pasan OK_HEADER_CANONICO. Sin esta bandera es dry-run.",
    )
    args = ap.parse_args()

    fecha_inicio = _as_date(args.fecha_inicio)
    fecha_fin = _as_date(args.fecha_fin)

    code, resumen = ejecutar_backfill(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        unidades=args.unidad,
        commit=args.commit,
    )

    print("===== BACKFILL DETALLE COMERCIAL PENDIENTE =====")
    _safe_print(resumen)

    if not args.commit:
        print("DRY_RUN: no se modificó dbo.Comercial_Inteligencia_VentasDetalleProducto")
    elif resumen["dias_bloqueados"]:
        print("ADVERTENCIA: solo se escribieron días OK_HEADER_CANONICO; quedan días bloqueados por revisar.")
    elif resumen["dias_sin_runtime"]:
        print("INFO: días sin Runtime se omitieron; no existe encabezado canónico que reparar en detalle.")

    return code


if __name__ == "__main__":
    sys.exit(main())
