import pytest

from modules.cava_socios.domain import (
    BottleOrigin,
    BottleOriginEvidence,
    IntelligenceConsumptionSource,
    ProductReferenceKind,
    contributes_commercial_sale,
    intelligence_source_for_origin,
    validate_origin_evidence,
)


def test_bottle_origin_contract_is_explicit():
    assert {item.value for item in BottleOrigin} == {
        "BOTELLA_EXTERNA_CAVA",
        "COMPRA_UNIDAD_PARA_CAVA",
        "TRANSFERENCIA_OTRA_CAVA",
        "REGULARIZACION_HISTORICA",
    }


def test_product_reference_supports_canonical_and_extended_catalog():
    assert ProductReferenceKind.PRODUCTO_CANONICO.value == "PRODUCTO_CANONICO"
    assert ProductReferenceKind.CATALOGO_EXTENDIDO.value == "CATALOGO_EXTENDIDO"


def test_unit_purchase_requires_commercial_evidence():
    with pytest.raises(ValueError):
        validate_origin_evidence(BottleOriginEvidence(origin=BottleOrigin.COMPRA_UNIDAD_PARA_CAVA))

    validate_origin_evidence(
        BottleOriginEvidence(
            origin=BottleOrigin.COMPRA_UNIDAD_PARA_CAVA,
            source_unit_id="UNIT-1",
            source_transaction_id="TX-1",
        )
    )


def test_external_bottle_does_not_require_sale_evidence():
    validate_origin_evidence(BottleOriginEvidence(origin=BottleOrigin.BOTELLA_EXTERNA_CAVA))


def test_transfer_requires_source_assignment():
    with pytest.raises(ValueError):
        validate_origin_evidence(BottleOriginEvidence(origin=BottleOrigin.TRANSFERENCIA_OTRA_CAVA))


def test_historical_regularization_requires_reference():
    with pytest.raises(ValueError):
        validate_origin_evidence(BottleOriginEvidence(origin=BottleOrigin.REGULARIZACION_HISTORICA))


def test_observed_consumption_never_becomes_sale_implicitly():
    for origin in BottleOrigin:
        source = intelligence_source_for_origin(origin)
        assert contributes_commercial_sale(source) is False

    assert contributes_commercial_sale(IntelligenceConsumptionSource.VENTA_UNIDAD) is True
