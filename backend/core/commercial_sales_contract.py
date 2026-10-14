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


def fiscal_breakdown(
    total: Any,
    *,
    subtotal_source: Any = None,
    tax_source: Any = None,
    fallback_tax_rate: float = 0.16,
) -> tuple[float, float]:
    """Subtotal e impuestos para impresion, sin alterar la venta comercial.

    Se prefieren siempre los importes fiscales del POS. El fallback solo se usa
    en tickets historicos que todavia no persisten esos campos.
    """
    total_value = round(max(0.0, _money(total)), 2)
    subtotal_value = _money(subtotal_source)
    tax_value = _money(tax_source)

    if subtotal_value > 0 or tax_value > 0:
        if subtotal_value <= 0:
            subtotal_value = max(0.0, total_value - tax_value)
        if tax_value <= 0:
            tax_value = max(0.0, total_value - subtotal_value)
        return round(subtotal_value, 2), round(tax_value, 2)

    rate = float(fallback_tax_rate or 0)
    if total_value <= 0 or rate <= 0:
        return total_value, 0.0

    subtotal_value = round(total_value / (1.0 + rate), 2)
    tax_value = round(total_value - subtotal_value, 2)
    return subtotal_value, tax_value


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
