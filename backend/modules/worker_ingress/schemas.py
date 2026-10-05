"""API schemas for the remote canonical Universal Worker ingress."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkerSubmitRequest(BaseModel):
    """Only caller-controlled fields that belong to the Worker job body.

    Canonical transport fields and requester identity are intentionally absent.
    Extra fields are rejected, so callers cannot override repo, branch,
    production policy or requester identity.
    """

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=3, max_length=121, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")
    objective: str = Field(min_length=3, max_length=4000)
    mode: str = Field(min_length=1, max_length=80)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    checks: list[dict[str, Any]] = Field(default_factory=list)
    scheduling: dict[str, Any] | None = None


class WorkerIngressResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    job_id: str
    production_touched: bool = False
