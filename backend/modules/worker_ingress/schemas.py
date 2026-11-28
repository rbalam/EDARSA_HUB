"""API schemas for the remote canonical Universal Worker ingress."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkerSubmitRequest(BaseModel):
    """Low-level internal endpoint retained for trusted EDARSAHUB callers."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(
        min_length=3,
        max_length=121,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$",
    )
    objective: str = Field(min_length=3, max_length=4000)
    mode: str = Field(min_length=1, max_length=80)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    checks: list[dict[str, Any]] = Field(default_factory=list)
    scheduling: dict[str, Any] | None = None


class WorkerObjectiveRequest(BaseModel):
    """Semantic public boundary intended for ChatGPT Plugin/Connector use.

    Raw Worker actions/checks, requester, repo, branch and production policy are
    not part of this schema.
    """

    model_config = ConfigDict(extra="forbid")

    objective: str = Field(min_length=3, max_length=4000)
    bounded_context: str = Field(
        min_length=2,
        max_length=120,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{1,119}$",
    )
    mode: str = Field(min_length=1, max_length=80)
    capability: str = Field(
        min_length=2,
        max_length=120,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{1,119}$",
    )
    request_key: str | None = Field(default=None, min_length=3, max_length=160)
    constraints: dict[str, Any] = Field(default_factory=dict)


class WorkerIngressResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    job_id: str
    production_touched: bool = False
