import pytest

from core.agent_capability_policy import PolicyContext
from modules.agent_harness.inventory_adapter import InventoryAgentRequest, authorize_inventory_agent
from modules.agent_harness.purchases_adapter import PurchaseAgentRequest, authorize_purchase_agent
from modules.agent_harness.transversal_capability_registry import list_domain_capabilities


def context(capability, scopes):
    caps = frozenset({capability})
    scope_set = frozenset(scopes)
    limits = {
        'runtime_seconds': 60,
        'files_changed': 0,
        'lines_changed': 0,
        'external_calls': 0,
        'sql_rows': 1000,
        'inference_cost_usd': 1.0,
    }
    return PolicyContext(caps, caps, caps, caps, scope_set, scope_set, scope_set, scope_set, limits)


def test_gate2_registry_extends_same_transversal_registry_without_side_effects():
    compras = list_domain_capabilities('COMPRAS')
    inventarios = list_domain_capabilities('INVENTARIOS')
    assert {x.code for x in compras} == {'PURCHASE_ANALYZE', 'PURCHASE_PROPOSE'}
    assert {x.code for x in inventarios} == {'INVENTORY_ANALYZE', 'INVENTORY_REPLENISHMENT_PROPOSE'}
    assert all(not item.side_effect for item in compras + inventarios)
    assert all(not item.approval_required for item in compras + inventarios)


def test_purchase_analyze_uses_canonical_permission_and_scope():
    req = PurchaseAgentRequest('buy-1', 1, 2, 'PURCHASE_ANALYZE')
    scopes = {'empresa:1', 'unidad:2', 'domain:compras', 'resource:purchases'}
    gate, policy = authorize_purchase_agent(
        req,
        {'allowed': True, 'permission': 'COMPRAS_FACT_VER', 'empresa_id': 1, 'unidad_id': 2},
        context(req.capability, scopes),
    )
    assert gate.allowed is True
    assert policy.external_egress is False
    assert policy.production_allowed is False


def test_purchase_fails_closed_on_permission_mismatch():
    req = PurchaseAgentRequest('buy-2', 1, 2)
    scopes = {'empresa:1', 'unidad:2', 'domain:compras', 'resource:purchases'}
    gate, _ = authorize_purchase_agent(
        req,
        {'allowed': True, 'permission': 'COMPRAS_FACT_EJECUTAR', 'empresa_id': 1, 'unidad_id': 2},
        context(req.capability, scopes),
    )
    assert gate.allowed is False
    assert gate.reasons == ('REQUESTER_PERMISSION_MISMATCH',)


def test_inventory_analyze_uses_existing_inventory_menu_permission():
    req = InventoryAgentRequest('inv-1', 1, 2, 'INVENTORY_ANALYZE')
    scopes = {'empresa:1', 'unidad:2', 'domain:inventarios', 'resource:inventory'}
    gate, policy = authorize_inventory_agent(
        req,
        {'allowed': True, 'permission': 'COMPRAS_INVENTARIOS_VER', 'empresa_id': 1, 'unidad_id': 2},
        context(req.capability, scopes),
    )
    assert gate.allowed is True
    assert policy.external_egress is False
    assert policy.production_allowed is False


def test_inventory_fails_closed_on_business_scope():
    req = InventoryAgentRequest('inv-2', 1, 2)
    scopes = {'empresa:1', 'unidad:2', 'domain:inventarios', 'resource:inventory'}
    gate, _ = authorize_inventory_agent(
        req,
        {'allowed': True, 'permission': 'COMPRAS_INVENTARIOS_VER', 'empresa_id': 1, 'unidad_id': 99},
        context(req.capability, scopes),
    )
    assert gate.allowed is False
    assert gate.reasons == ('REQUESTER_BUSINESS_SCOPE_MISMATCH',)


def test_cross_domain_capability_is_rejected():
    with pytest.raises(Exception, match='PURCHASE_CAPABILITY_REQUIRED'):
        PurchaseAgentRequest('buy-3', 1, 2, 'INVENTORY_ANALYZE')
    with pytest.raises(Exception, match='INVENTORY_CAPABILITY_REQUIRED'):
        InventoryAgentRequest('inv-3', 1, 2, 'PURCHASE_ANALYZE')
