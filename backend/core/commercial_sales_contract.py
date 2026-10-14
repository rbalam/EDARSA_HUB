"""Contrato monetario transversal de Comercial.

La capa de sincronizacion legacy de Ventas del Dia de SoftRestaurant persiste
temporalmente total - propina en los campos de venta del snapshot. El POS,
sin embargo, define cheques.total / tempcheques.total como la venta visible
con IVA. propina es una metrica separada y nunca debe convertirse en descuento.

Este modulo concentra la compatibilidad de lectura para que Ejecutivo,
Comercial y Ticket compartan la misma semantica sin modificar el scheduler
protegido sync_comercial_abiertas_v2_job.py.
"""

from __future__ import annotations

from typing import Any


SNAPSHOT_SOURCE = "Comercial_Ventas_Dia_Abiertas_v2"


def _money(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def is_softrestaurant(system_type: Any) -> bool:
    return "SOFT" in str(system_type or "").strip().upper()


def snapshot_visible_sales(
    persisted_sales: Any,
    tips: Any,
    system_type: Any,
) -> float:
    """Restaura la columna total de SoftRestaurant en snapshots legacy.

    Solo debe invocarse para datos nacidos de
    Comercial_Ventas_Dia_Abiertas_v2. MPRO permanece sin cambios.
    """
    sales = _money(persisted_sales)
    if is_softrestaurant(system_type):
        return sales + _money(tips)
    return sales


def ticket_visible_total(total_ticket: Any, system_type: Any = None) -> float:
    """Total visible del ticket; la propina nunca se resta aqui."""
    del system_type
    return _money(total_ticket)


def runtime_visible_sales_sql(alias: str = "k") -> str:
    """Expresion SQL del mismo contrato para la vista runtime consumida."""
    if not alias.replace("_", "").isalnum():
        raise ValueError("Alias SQL invalido")

    return f"""CASE
        WHEN UPPER(ISNULL({alias}.sistema_origen, '')) LIKE 'SOFT%'
         AND ISNULL({alias}.fuente_original, '') = '{SNAPSHOT_SOURCE}'
        THEN ISNULL({alias}.ventas_total, 0) + ISNULL({alias}.propinas_total, 0)
        ELSE ISNULL({alias}.ventas_total, 0)
    END"""
