from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

AGENT_SCHEMA = "edarsahub.bos-agent.v1"
SKILL_SCHEMA = "edarsahub.bos-skill.v1"

VALID_STATUS = frozenset({"DRAFT", "APPROVED", "BLOCKED", "DEPRECATED"})
VALID_ADOPTION = frozenset({"NATIVE", "ADOPTED", "ADAPTED", "ON_DEMAND", "BLOCKED"})
VALID_RISK = frozenset({"R0", "R1", "R2", "R3", "R4"})
VALID_DATA_CLASSIFICATIONS = frozenset({
    "PUBLIC", "INTERNAL", "CONFIDENTIAL", "PII",
    "FINANCIAL_PRIVATE", "SECRET",
})
VALID_EXECUTORS = frozenset({"worker", "ai_gateway", "agent_reach", "communications"})


class RegistryError(ValueError):
    pass


def _clean_token(value: str, field_name: str) -> str:
    token = str(value or "").strip()
    if not token:
        raise RegistryError(f"{field_name}_REQUIRED")
    return token


def _unique_tokens(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    cleaned = tuple(_clean_token(value, field_name) for value in values)
    if len(cleaned) != len(set(cleaned)):
        raise RegistryError(f"{field_name}_DUPLICATED")
    return cleaned


@dataclass(frozen=True)
class AgentSpec:
    id: str
    version: str
    role: str
    domains: tuple[str, ...]
    status: str = "DRAFT"
    allowed_skills: tuple[str, ...] = ()
    capability_ceiling: tuple[str, ...] = ()
    scope_ceiling: tuple[str, ...] = ()
    max_risk: str = "R0"
    allowed_data_classifications: tuple[str, ...] = ("PUBLIC",)
    model_requirements: Mapping[str, object] = field(default_factory=dict)
    budgets: Mapping[str, float] = field(default_factory=dict)
    max_concurrency: int = 1
    red_team_required: bool = False
    human_approval_thresholds: tuple[str, ...] = ()
    provenance: str = "BOS_NATIVE"
    schema: str = AGENT_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _clean_token(self.id, "AGENT_ID"))
        object.__setattr__(self, "version", _clean_token(self.version, "AGENT_VERSION"))
        object.__setattr__(self, "role", _clean_token(self.role, "AGENT_ROLE"))
        object.__setattr__(self, "domains", _unique_tokens(self.domains, "AGENT_DOMAIN"))
        object.__setattr__(self, "allowed_skills", _unique_tokens(self.allowed_skills, "AGENT_SKILL"))
        object.__setattr__(self, "capability_ceiling", _unique_tokens(self.capability_ceiling, "AGENT_CAPABILITY"))
        object.__setattr__(self, "scope_ceiling", _unique_tokens(self.scope_ceiling, "AGENT_SCOPE"))
        object.__setattr__(self, "allowed_data_classifications", _unique_tokens(self.allowed_data_classifications, "AGENT_DATA_CLASSIFICATION"))
        if self.schema != AGENT_SCHEMA:
            raise RegistryError("AGENT_SCHEMA_INVALID")
        if not self.domains:
            raise RegistryError("AGENT_DOMAIN_REQUIRED")
        if self.status not in VALID_STATUS:
            raise RegistryError("AGENT_STATUS_INVALID")
        if self.max_risk not in VALID_RISK:
            raise RegistryError("AGENT_RISK_INVALID")
        if not set(self.allowed_data_classifications).issubset(VALID_DATA_CLASSIFICATIONS):
            raise RegistryError("AGENT_DATA_CLASSIFICATION_INVALID")
        if self.max_concurrency < 1:
            raise RegistryError("AGENT_MAX_CONCURRENCY_INVALID")
        if any(float(value) < 0 for value in self.budgets.values()):
            raise RegistryError("AGENT_BUDGET_INVALID")


@dataclass(frozen=True)
class SkillSpec:
    id: str
    version: str
    source: str
    origin: str
    domain: str
    description: str
    entrypoint: str
    provenance: str
    checksum: str = ""
    license: str = ""
    required_capabilities: tuple[str, ...] = ()
    allowed_scopes: tuple[str, ...] = ()
    max_risk: str = "R0"
    allowed_data_classifications: tuple[str, ...] = ("PUBLIC",)
    external_egress: bool = False
    allowed_executors: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    validations: tuple[str, ...] = ()
    lifecycle: str = "DRAFT"
    adoption: str = "NATIVE"
    schema: str = SKILL_SCHEMA

    def __post_init__(self) -> None:
        for name in ("id", "version", "source", "origin", "domain", "description", "entrypoint", "provenance"):
            object.__setattr__(self, name, _clean_token(getattr(self, name), f"SKILL_{name.upper()}"))
        for name in ("required_capabilities", "allowed_scopes", "allowed_data_classifications", "allowed_executors", "allowed_tools", "dependencies", "conflicts", "validations"):
            object.__setattr__(self, name, _unique_tokens(getattr(self, name), f"SKILL_{name.upper()}"))
        if self.schema != SKILL_SCHEMA:
            raise RegistryError("SKILL_SCHEMA_INVALID")
        if self.lifecycle not in VALID_STATUS:
            raise RegistryError("SKILL_LIFECYCLE_INVALID")
        if self.adoption not in VALID_ADOPTION:
            raise RegistryError("SKILL_ADOPTION_INVALID")
        if self.max_risk not in VALID_RISK:
            raise RegistryError("SKILL_RISK_INVALID")
        if not set(self.allowed_data_classifications).issubset(VALID_DATA_CLASSIFICATIONS):
            raise RegistryError("SKILL_DATA_CLASSIFICATION_INVALID")
        if not set(self.allowed_executors).issubset(VALID_EXECUTORS):
            raise RegistryError("SKILL_EXECUTOR_INVALID")
        if set(self.dependencies).intersection(self.conflicts):
            raise RegistryError("SKILL_DEPENDENCY_CONFLICT")
        if self.source != "BOS_NATIVE" and self.lifecycle == "APPROVED" and (not self.checksum or not self.license):
            raise RegistryError("EXTERNAL_SKILL_PROVENANCE_INCOMPLETE")


class _Registry:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], object] = {}

    def _register(self, item: object, item_id: str, version: str) -> None:
        key = (item_id, version)
        if key in self._items:
            raise RegistryError("REGISTRY_DUPLICATE_VERSION")
        self._items[key] = item

    def get(self, item_id: str, version: str):
        key = (_clean_token(item_id, "REGISTRY_ID"), _clean_token(version, "REGISTRY_VERSION"))
        try:
            return self._items[key]
        except KeyError as exc:
            raise RegistryError("REGISTRY_ITEM_NOT_FOUND") from exc

    def versions(self, item_id: str) -> tuple[str, ...]:
        item_id = _clean_token(item_id, "REGISTRY_ID")
        return tuple(sorted(version for (registered_id, version) in self._items if registered_id == item_id))


class AgentRegistry(_Registry):
    def register(self, spec: AgentSpec) -> None:
        if not isinstance(spec, AgentSpec):
            raise RegistryError("AGENT_SPEC_REQUIRED")
        self._register(spec, spec.id, spec.version)


class SkillRegistry(_Registry):
    def register(self, spec: SkillSpec) -> None:
        if not isinstance(spec, SkillSpec):
            raise RegistryError("SKILL_SPEC_REQUIRED")
        self._register(spec, spec.id, spec.version)
