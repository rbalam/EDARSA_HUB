"""BOS Agent Harness.

Control-plane modular fuera de backend.core. Ningun registry concede autoridad;
la autorizacion efectiva permanece en RBAC y los policy/execution gates canonicos.
"""

from .registry import (
    AgentRegistry,
    AgentSpec,
    RegistryError,
    SkillRegistry,
    SkillSpec,
)

__all__ = [
    "AgentRegistry",
    "AgentSpec",
    "RegistryError",
    "SkillRegistry",
    "SkillSpec",
]
