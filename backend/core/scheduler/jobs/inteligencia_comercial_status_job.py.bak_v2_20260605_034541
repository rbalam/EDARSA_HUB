"""
EDARSA HUB - Inteligencia Comercial Status Job
==============================================
Fase 1: job validador de frescura de datos.
No sincroniza ventas. No consulta dashboards live. No ejecuta SPs vacíos.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List
import logging
import os

import pytds

from .base_job import BaseJob

logger = logging.getLogger(__name__)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _rows_to_dicts(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{k: _json_safe(v) for k, v in row.items()} for row in rows]


def _get_edarsahub_sql_connection():
    host = os.environ.get("EDARSA_HUB_SQL_HOST") or os.environ.get("EDARSAHUB_SQL_HOST")
    if not host:
        raise RuntimeError("Falta EDARSA_HUB_SQL_HOST / EDARSAHUB_SQL_HOST")

    return pytds.connect(
        server=host,
        port=int(os.environ.get("EDARSA_HUB_SQL_PORT") or os.environ.get("EDARSAHUB_SQL_PORT") or "1433"),
        database=os.environ.get("EDARSA_HUB_SQL_DB") or os.environ.get("EDARSAHUB_SQL_DATABASE") or os.environ.get("EDARSAHUB_SQL_DB") or "EDARSA_HUB",
        user=os.environ.get("EDARSA_HUB_SQL_USER") or os.environ.get("EDARSAHUB_SQL_USER") or "sa",
        password=os.environ.get("EDARSA_HUB_SQL_PASS") or os.environ.get("EDARSAHUB_SQL_PASSWORD") or os.environ.get("EDARSAHUB_SQL_PASS") or "",
        timeout=30,
        login_timeout=30,
        as_dict=True,
    )


class InteligenciaComercialStatusJob(BaseJob):
    """Valida frescura de fuentes SQL para Inteligencia Comercial."""

    async def execute(self) -> Dict[str, Any]:
        sql = """
        SELECT
            Fuente,
            UltimaFechaOperacion,
            UltimaFechaSincronizacion,
            Registros,
            CASE
                WHEN Registros IS NULL OR Registros = 0 THEN 'SIN_DATOS'
                WHEN UltimaFechaOperacion IS NULL THEN 'SIN_DATOS'
                WHEN DATEDIFF(DAY, UltimaFechaOperacion, CAST(GETDATE() AS DATE)) > 2 THEN 'STALE'
                ELSE 'OK'
            END AS Estado
        FROM (
            SELECT
                'Comercial_KPIs_Diarios_v2' AS Fuente,
                MAX(fecha_operacion) AS UltimaFechaOperacion,
                MAX(fecha_sincronizacion) AS UltimaFechaSincronizacion,
                COUNT(*) AS Registros
            FROM dbo.Comercial_KPIs_Diarios_v2
            WHERE ISNULL(activo, 1) = 1

            UNION ALL

            SELECT
                'Comercial_Ventas_Dia_Abiertas_v2' AS Fuente,
                MAX(fecha_operacion) AS UltimaFechaOperacion,
                MAX(fecha_ultima_actualizacion) AS UltimaFechaSincronizacion,
                COUNT(*) AS Registros
            FROM dbo.Comercial_Ventas_Dia_Abiertas_v2

            UNION ALL

            SELECT
                'Sync_PAX_Detalle' AS Fuente,
                MAX(FechaOperacion) AS UltimaFechaOperacion,
                MAX(FechaSync) AS UltimaFechaSincronizacion,
                COUNT(*) AS Registros
            FROM dbo.Sync_PAX_Detalle

            UNION ALL

            SELECT
                'Sync_Sales' AS Fuente,
                CAST(MAX(FechaHora) AS DATE) AS UltimaFechaOperacion,
                MAX(last_modified) AS UltimaFechaSincronizacion,
                COUNT(*) AS Registros
            FROM dbo.Sync_Sales
        ) s;
        """

        with _get_edarsahub_sql_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = _rows_to_dicts(cur.fetchall() or [])

        failed = len([r for r in rows if r.get("Estado") in {"SIN_DATOS", "ERROR"}])
        stale = len([r for r in rows if r.get("Estado") == "STALE"])
        ok = len([r for r in rows if r.get("Estado") == "OK"])

        return {
            "processed_count": len(rows),
            "success_count": ok,
            "failed_count": failed,
            "skipped_count": stale,
            "message": f"Inteligencia Comercial status: OK={ok}, STALE={stale}, SIN_DATOS/ERROR={failed}",
            "details": {"sources": rows},
        }


def create_inteligencia_comercial_status_job(db, config):
    return InteligenciaComercialStatusJob(db, config)
