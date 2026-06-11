"""
Regresión: Enriquecimiento Inteligencia Comercial (tipo de servicio + formas de pago por ticket).
SOLO LECTURA de EDARSAHUB (no conecta al POS). Valida el resultado del piloto cargado.

Ejecutar: cd /app/backend && python3 -m pytest tests/test_enrich_tiposervicio_pagos.py -q
"""
import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
for raw in (BACKEND_DIR / ".env").read_text(encoding="utf-8", errors="ignore").splitlines():
    line = raw.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
sys.path.insert(0, str(BACKEND_DIR))

from core.sql_first.db import fetch_all_dict  # noqa: E402


def _cols(table):
    return {r["COLUMN_NAME"] for r in fetch_all_dict(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=%s", (table,))}


def test_migracion_columnas_sync_sales():
    cols = _cols("Sync_Sales")
    assert {"TipoServicioID", "TipoServicio"}.issubset(cols)


def test_migracion_columnas_detallepagos():
    cols = _cols("Finanzas_CortesCaja_DetallePagos")
    assert {"UnidadNegocio", "NumeroTicket", "FechaHora", "Propina"}.issubset(cols)


def test_detallepagos_corecajaid_nullable():
    rows = fetch_all_dict(
        "SELECT IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_NAME='Finanzas_CortesCaja_DetallePagos' AND COLUMN_NAME='CorteCajaID'")
    assert rows and rows[0]["IS_NULLABLE"] == "YES"


@pytest.mark.parametrize("unidad", ["ESTELAR", "ORIGEN"])
def test_piloto_poblado(unidad):
    """El piloto cargó pagos por ticket y tipo de servicio para las unidades validadas."""
    pagos = fetch_all_dict(
        "SELECT COUNT(*) n, COUNT(DISTINCT NumeroTicket) tk, SUM(Importe) imp "
        "FROM Finanzas_CortesCaja_DetallePagos WHERE UnidadNegocio=%s "
        "AND FechaHora>='2026-05-01' AND FechaHora<'2026-06-01'", (unidad,))[0]
    assert int(pagos["n"]) > 0, f"{unidad} sin pagos por ticket"
    assert float(pagos["imp"] or 0) > 0
    ts = fetch_all_dict(
        "SELECT COUNT(*) n FROM Sync_Sales WHERE UnidadNegocio=%s AND TipoServicioID IS NOT NULL "
        "AND FechaHora>='2026-05-01' AND FechaHora<'2026-06-01'", (unidad,))[0]
    assert int(ts["n"]) > 0, f"{unidad} sin tipo de servicio en Sync_Sales"


def test_no_corte_huerfano_obligatorio():
    """Verifica que ningún pago por ticket quedó sin UnidadNegocio (clave del drill ISCAM)."""
    rows = fetch_all_dict(
        "SELECT COUNT(*) n FROM Finanzas_CortesCaja_DetallePagos "
        "WHERE NumeroTicket IS NOT NULL AND UnidadNegocio IS NULL")
    assert int(rows[0]["n"]) == 0
