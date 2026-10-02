import pytest

from modules.agent_harness.registry import AgentRegistry, AgentSpec, RegistryError, SkillRegistry, SkillSpec


def test_agent_registry_is_versioned_and_fail_closed():
    registry = AgentRegistry()
    spec = AgentSpec(id='bos-backend', version='1.0.0', role='backend', domains=('bos',), max_risk='R2')
    registry.register(spec)
    assert registry.get('bos-backend', '1.0.0') == spec
    assert registry.versions('bos-backend') == ('1.0.0',)
    with pytest.raises(RegistryError, match='REGISTRY_DUPLICATE_VERSION'):
        registry.register(spec)
    with pytest.raises(RegistryError, match='REGISTRY_ITEM_NOT_FOUND'):
        registry.get('bos-backend', '9.9.9')


def test_agent_spec_rejects_invalid_policy_metadata():
    with pytest.raises(RegistryError, match='AGENT_RISK_INVALID'):
        AgentSpec(id='x', version='1', role='x', domains=('bos',), max_risk='R9')
    with pytest.raises(RegistryError, match='AGENT_DATA_CLASSIFICATION_INVALID'):
        AgentSpec(id='x', version='1', role='x', domains=('bos',), allowed_data_classifications=('UNKNOWN',))


def test_skill_registry_validates_executor_and_dependency_conflict():
    with pytest.raises(RegistryError, match='SKILL_EXECUTOR_INVALID'):
        SkillSpec(id='x', version='1', source='BOS_NATIVE', origin='bos', domain='bos', description='x', entrypoint='x', provenance='native', allowed_executors=('shell',))
    with pytest.raises(RegistryError, match='SKILL_DEPENDENCY_CONFLICT'):
        SkillSpec(id='x', version='1', source='BOS_NATIVE', origin='bos', domain='bos', description='x', entrypoint='x', provenance='native', dependencies=('a',), conflicts=('a',))


def test_external_approved_skill_requires_checksum_and_license():
    with pytest.raises(RegistryError, match='EXTERNAL_SKILL_PROVENANCE_INCOMPLETE'):
        SkillSpec(id='external-x', version='1', source='COMMUNITY', origin='https://example.invalid', domain='bos', description='x', entrypoint='x', provenance='third-party', lifecycle='APPROVED', adoption='ADAPTED')


def test_native_skill_can_be_registered_without_granting_authority():
    registry = SkillRegistry()
    spec = SkillSpec(id='bos-read', version='1.0.0', source='BOS_NATIVE', origin='edarsahub', domain='bos', description='Read governed BOS context', entrypoint='bos.read', provenance='native', required_capabilities=('READ',), allowed_executors=('worker',), lifecycle='APPROVED')
    registry.register(spec)
    assert registry.get('bos-read', '1.0.0') == spec
    assert spec.required_capabilities == ('READ',)
