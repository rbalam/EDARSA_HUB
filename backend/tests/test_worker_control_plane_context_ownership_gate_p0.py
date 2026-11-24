from __future__ import annotations

import pytest

from modules.worker_ingress import semantic_capabilities as caps


def test_cfdi_context_owns_exact_legacy_portal_paths():
    for path in (
        "backend/routes/portal_proveedores.py",
        "backend/routes/portal_proveedores_repository_sql.py",
    ):
        assert caps._dev_validate_path(path, context="COMUNICACIONES_CFDI") == path


def test_other_context_cannot_mutate_cfdi_portal_paths():
    with pytest.raises(caps.SemanticCapabilityError, match="SEMANTIC_DEV_PATH_FORBIDDEN"):
        caps._dev_validate_path(
            "backend/routes/portal_proveedores.py",
            context="FINANZAS",
        )


def test_arbitrary_backend_routes_remain_forbidden_even_for_cfdi():
    with pytest.raises(caps.SemanticCapabilityError, match="SEMANTIC_DEV_PATH_FORBIDDEN"):
        caps._dev_validate_path(
            "backend/routes/otro_modulo.py",
            context="COMUNICACIONES_CFDI",
        )


def test_context_ownership_does_not_expand_verification_test_roots():
    with pytest.raises(caps.SemanticCapabilityError, match="SEMANTIC_DEV_PATH_FORBIDDEN"):
        caps._dev_validate_path(
            "backend/routes/portal_proveedores.py",
            allowed_roots=caps._DEV_TEST_ROOTS,
            context="COMUNICACIONES_CFDI",
        )


def test_capability_catalog_exposes_reviewed_context_ownership():
    catalog = {item["code"]: item for item in caps.capability_catalog()}
    ownership = catalog["DEVELOPMENT_MUTATION_BOUNDED"]["bounded_context_path_ownership"]
    assert ownership["COMUNICACIONES_CFDI"] == [
        "backend/routes/portal_proveedores.py",
        "backend/routes/portal_proveedores_repository_sql.py",
    ]
