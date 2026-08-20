from pathlib import Path


TARGET = Path(
    "/app/backend/modules/finanzas/cuentas_por_pagar.py"
)


def source():
    return TARGET.read_text(encoding="utf-8")


def test_cxp_uses_aut_tes_pagos():
    src = source()
    assert (
        'CXP_AUTHORIZATION_TYPE_CODE = "AUT_TES_PAGOS"'
        in src
    )


def test_cxp_uses_existing_polymorphic_link():
    src = source()

    assert (
        'CXP_AUTHORIZATION_ENTITY_NAME = '
        '"FINANZAS_CXP_DECISION_PAGO"'
        in src
    )

    assert "A.EntidadNombre = %s" in src
    assert "A.EntidadID = %s" in src


def test_create_uses_canonical_engine():
    src = source()

    assert "dbo.sp_Usuario_CrearAutorizacion" in src
    assert "@AutorizacionID = @AutorizacionID OUTPUT" in src
    assert "@UnidadNegocioID" in src


def test_resolve_uses_canonical_engine():
    src = source()

    assert "dbo.sp_Usuario_ResolverAutorizacion" in src
    assert "@UsuarioAutorizadorID" in src


def test_endpoint_no_longer_calls_legacy_direct_authorization():
    src = source()

    start = src.index(
        '@router.post("/{factura_id}/decision-pago/autorizacion")'
    )
    end = src.index(
        '@router.put("/decision-pago-masivo")',
        start,
    )

    block = src[start:end]

    assert "_cxp_update_autorizacion(" not in block
    assert "_cxp_resolve_canonical_authorization(" in block


def test_queue_only_after_final_authorized():
    src = source()

    start = src.index(
        '@router.post("/{factura_id}/decision-pago/autorizacion")'
    )
    end = src.index(
        '@router.put("/decision-pago-masivo")',
        start,
    )

    block = src[start:end]

    assert 'projected_state == "AUTORIZADO"' in block
    assert "_cxp_enqueue_pago_origen(" in block


def test_mark_for_payment_creates_authorization():
    src = source()

    start = src.index(
        "async def actualizar_decision_pago("
    )
    end = src.index(
        '@router.post("/{factura_id}/decision-pago/autorizacion")',
        start,
    )

    block = src[start:end]

    assert "_cxp_create_canonical_authorization(" in block


def test_legacy_helper_explicitly_deprecated():
    src = source()
    assert "LEGACY_DEPRECATED_CXP_AUTHORIZATION" in src


def test_no_schema_parallel_link_added():
    src = source()

    assert (
        "ALTER TABLE dbo.Finanzas_CxP_DecisionesPago"
        not in src
    )
    assert "ADD AutorizacionID" not in src
