"""Configuration for the EDARSAHUB Universal Worker MCP adapter."""
from __future__ import annotations

import os
from dataclasses import dataclass


class WorkerMcpConfigError(RuntimeError):
    pass


def _required(name: str) -> str:
    value = str(os.environ.get(name) or "").strip()
    if not value:
        raise WorkerMcpConfigError(f"REQUIRED_ENV_MISSING:{name}")
    return value


def _csv(name: str, *, required: bool = False) -> tuple[str, ...]:
    raw = str(os.environ.get(name) or "").strip()
    values = tuple(
        item.strip()
        for item in raw.split(",")
        if item.strip()
    )
    if required and not values:
        raise WorkerMcpConfigError(f"REQUIRED_ENV_MISSING:{name}")
    return values


@dataclass(frozen=True)
class WorkerMcpConfig:
    issuer_url: str
    resource_url: str
    backend_url: str
    allowed_hosts: tuple[str, ...]
    allowed_origins: tuple[str, ...] = ()
    bind_host: str = "127.0.0.1"

    @classmethod
    def from_env(cls) -> "WorkerMcpConfig":
        return cls(
            issuer_url=_required("EDARSAHUB_MCP_ISSUER_URL"),
            resource_url=_required("EDARSAHUB_MCP_RESOURCE_URL"),
            backend_url=_required("EDARSAHUB_MCP_BACKEND_URL").rstrip("/"),
            allowed_hosts=_csv(
                "EDARSAHUB_MCP_ALLOWED_HOSTS",
                required=True,
            ),
            allowed_origins=_csv(
                "EDARSAHUB_MCP_ALLOWED_ORIGINS",
            ),
            bind_host=str(
                os.environ.get(
                    "EDARSAHUB_MCP_BIND_HOST",
                    "127.0.0.1",
                )
            ).strip() or "127.0.0.1",
        )
