"""Contratos puros del dominio Cavas Personales.

No accede a SQL ni a sistemas externos. Define vocabulario y validaciones
canónicas que después son persistidas/adaptadas por la capa de servicio.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BottleOrigin(str, Enum):
    BOTELLA_EXTERNA_CAVA = "BOTELLA_EXTERNA_CAVA"
    COMPRA_UNIDAD_PARA_CAVA = "COMPRA_UNIDAD_PARA_CAVA"
    TRANSFERENCIA_OTRA_CAVA = "TRANSFERENCIA_OTRA_CAVA"
    REGULARIZACION_HISTORICA = "REGULARIZACION_HISTORICA"


class ProductReferenceKind(str, Enum):
    PRODUCTO_CANONICO = "PRODUCTO_CANONICO"
    CATALOGO_EXTENDIDO = "CATALOGO_EXTENDIDO"


class IntelligenceConsumptionSource(str, Enum):
    VENTA_UNIDAD = "VENTA_UNIDAD"
    COMPRA_UNIDAD_PARA_CAVA = "COMPRA_UNIDAD_PARA_CAVA"
    BOTELLA_EXTERNA_CAVA = "BOTELLA_EXTERNA_CAVA"
    TRANSFERENCIA_OTRA_CAVA = "TRANSFERENCIA_OTRA_CAVA"
    REGULARIZACION_HISTORICA = "REGULARIZACION_HISTORICA"


@dataclass(frozen=True)
class BottleOriginEvidence:
    origin: BottleOrigin
    source_unit_id: Optional[str] = None
    source_transaction_id: Optional[str] = None
    source_line_id: Optional[str] = None
    source_system: Optional[str] = None
    source_cava_assignment_id: Optional[str] = None
    historical_reference: Optional[str] = None


def validate_origin_evidence(evidence: BottleOriginEvidence) -> None:
    """Valida evidencia mínima sin asumir proveedor POS/ERP específico."""
    if evidence.origin == BottleOrigin.COMPRA_UNIDAD_PARA_CAVA:
        missing = []
        if not evidence.source_unit_id:
            missing.append("source_unit_id")
        if not evidence.source_transaction_id:
            missing.append("source_transaction_id")
        if missing:
            raise ValueError("COMPRA_UNIDAD_PARA_CAVA requiere evidencia comercial: " + ", ".join(missing))
        return

    if evidence.origin == BottleOrigin.TRANSFERENCIA_OTRA_CAVA:
        if not evidence.source_cava_assignment_id:
            raise ValueError("TRANSFERENCIA_OTRA_CAVA requiere source_cava_assignment_id")
        return

    if evidence.origin == BottleOrigin.REGULARIZACION_HISTORICA:
        if not evidence.historical_reference:
            raise ValueError("REGULARIZACION_HISTORICA requiere historical_reference")
        return

    # BOTELLA_EXTERNA_CAVA no requiere una venta ni transacción comercial.


def intelligence_source_for_origin(origin: BottleOrigin) -> IntelligenceConsumptionSource:
    if origin == BottleOrigin.COMPRA_UNIDAD_PARA_CAVA:
        return IntelligenceConsumptionSource.COMPRA_UNIDAD_PARA_CAVA
    if origin == BottleOrigin.BOTELLA_EXTERNA_CAVA:
        return IntelligenceConsumptionSource.BOTELLA_EXTERNA_CAVA
    if origin == BottleOrigin.TRANSFERENCIA_OTRA_CAVA:
        return IntelligenceConsumptionSource.TRANSFERENCIA_OTRA_CAVA
    return IntelligenceConsumptionSource.REGULARIZACION_HISTORICA


def contributes_commercial_sale(source: IntelligenceConsumptionSource) -> bool:
    """Solo una venta comercial real incrementa venta/ingreso/ticket.

    COMPRA_UNIDAD_PARA_CAVA conserva vínculo comercial, pero el evento de consumo
    posterior de la botella en Cavas no genera una segunda venta.
    """
    return source == IntelligenceConsumptionSource.VENTA_UNIDAD
