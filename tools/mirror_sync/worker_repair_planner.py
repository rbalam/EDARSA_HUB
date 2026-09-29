"""Deterministic Worker Repair Planner.

Maintenance-plane planner for Universal Worker infrastructure repairs.

It converts an already-declared MaintenanceIncident into a deterministic
edarsahub.worker-job.v2 payload through explicitly registered repair
capabilities.

It does not:
- execute repository mutation;
- create another Worker, queue, scheduler, or control plane;
- execute SQL or touch Production;
- expand an incident's authorized scope;
- invent repair actions for unknown capabilities;
- certify its own repair.

Repository mutation remains exclusively the responsibility of Universal Worker.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from tools.mirror_sync import worker_maintenance_runtime as maintenance
from tools.mirror_sync.universal_job_bridge import validate as validate_worker_job
from tools.mirror_sync.worker_job_factory import canonicalize_job
from tools.mirror_sync.worker_repair_execution import (
    deterministic_repair_job_id,
    publish_repair_job,
    validate_repair_worker_job,
)


ROOT = Path(__file__).resolve().parents[2]

REPAIR_SPECS = (
    maintenance.STATE_DIR
    / "repair_specs"
)

DEV_BRANCH = "Edarsahub_Desarrollo"
MIRROR_BRANCH = "mirror/emergent-live"


@dataclass(frozen=True)
class RepairCapability:
    code: str
    incident_ids: tuple[str, ...]
    required_paths: tuple[str, ...]
    builder: Callable[
        [Any, dict[str, Any]],
        dict[str, Any],
    ]


_CAPABILITIES: dict[
    str,
    RepairCapability,
] = {}


def register_capability(
    capability: RepairCapability,
) -> None:
    code = str(
        capability.code or ""
    ).strip()

    if not code:
        raise ValueError(
            "REPAIR_CAPABILITY_CODE_REQUIRED"
        )

    if code in _CAPABILITIES:
        raise ValueError(
            "REPAIR_CAPABILITY_DUPLICATE"
        )

    if not capability.incident_ids:
        raise ValueError(
            "REPAIR_CAPABILITY_INCIDENT_REQUIRED"
        )

    if not capability.required_paths:
        raise ValueError(
            "REPAIR_CAPABILITY_PATHS_REQUIRED"
        )

    _CAPABILITIES[code] = capability


def registered_capabilities(
) -> tuple[str, ...]:
    return tuple(
        sorted(_CAPABILITIES)
    )


def _git(
    *args: str,
) -> str:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env={
            **os.environ,
            "GIT_TERMINAL_PROMPT": "0",
        },
    )

    if proc.returncode != 0:
        raise RuntimeError(
            "REPAIR_PLANNER_GIT_FAILED:"
            + (proc.stdout or "")[-1200:]
        )

    return proc.stdout.strip()


def convergence_state(
) -> dict[str, Any]:
    _git(
        "fetch",
        "--quiet",
        "origin",
        DEV_BRANCH,
        MIRROR_BRANCH,
    )

    local = _git(
        "rev-parse",
        "HEAD",
    )

    development = _git(
        "rev-parse",
        f"origin/{DEV_BRANCH}",
    )

    mirror = _git(
        "rev-parse",
        f"origin/{MIRROR_BRANCH}",
    )

    return {
        "local": local,
        "development": development,
        "mirror": mirror,
        "converged": bool(
            local
            and local
            == development
            == mirror
        ),
    }


def _canonical_requester(
) -> dict[str, Any]:
    email = str(
        os.environ.get(
            "EDARSAHUB_WORKER_REPAIR_REQUESTER_EMAIL",
            os.environ.get(
                "EDARSAHUB_WORKER_REQUESTER_EMAIL",
                "",
            ),
        )
    ).strip().lower()

    if not email:
        raise ValueError(
            "REPAIR_PLANNER_REQUESTER_REQUIRED"
        )

    return {
        "email": email,
        "source": "worker_repair",
        "project": "EDARSAHUB-BOS",
        "chat": "Worker Repair Planner",
    }


def _resolve_capability(
    incident_id: str,
    capability_code: str | None,
) -> RepairCapability:
    if capability_code:
        capability = _CAPABILITIES.get(
            str(capability_code).strip()
        )

        if capability is None:
            raise ValueError(
                "REPAIR_CAPABILITY_UNKNOWN"
            )

        if (
            incident_id
            not in capability.incident_ids
        ):
            raise ValueError(
                "REPAIR_CAPABILITY_INCIDENT_MISMATCH"
            )

        return capability

    matches = [
        item
        for item in _CAPABILITIES.values()
        if incident_id
        in item.incident_ids
    ]

    if not matches:
        raise ValueError(
            "REPAIR_CAPABILITY_UNKNOWN"
        )

    if len(matches) != 1:
        raise ValueError(
            "REPAIR_CAPABILITY_AMBIGUOUS"
        )

    return matches[0]


def _validate_scope(
    incident: Any,
    capability: RepairCapability,
    actions: list[dict[str, Any]],
) -> None:
    authorized = set(
        incident.target_paths
    )

    required = set(
        capability.required_paths
    )

    if not required.issubset(
        authorized
    ):
        raise ValueError(
            "REPAIR_CAPABILITY_SCOPE_NOT_AUTHORIZED"
        )

    action_paths = set()

    for action in actions:
        if not isinstance(
            action,
            dict,
        ):
            raise ValueError(
                "REPAIR_ACTION_INVALID"
            )

        path = str(
            action.get("path") or ""
        ).strip()

        if not path:
            raise ValueError(
                "REPAIR_ACTION_PATH_REQUIRED"
            )

        action_paths.add(path)

    if not action_paths:
        raise ValueError(
            "REPAIR_ACTION_SCOPE_EMPTY"
        )

    if not action_paths.issubset(
        authorized
    ):
        raise ValueError(
            "REPAIR_ACTION_SCOPE_MISMATCH"
        )


def _persist_spec(
    job: dict[str, Any],
) -> Path:
    REPAIR_SPECS.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        REPAIR_SPECS
        / f"{job['job_id']}.json"
    )

    serialized = (
        json.dumps(
            job,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    if path.is_file():
        existing = path.read_text(
            encoding="utf-8"
        )

        if existing != serialized:
            raise ValueError(
                "REPAIR_SPEC_IDEMPOTENCY_CONFLICT"
            )

        return path

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=REPAIR_SPECS,
        delete=False,
    ) as handle:
        handle.write(serialized)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(
            handle.name
        )

    os.replace(
        temporary,
        path,
    )

    return path


def build_deterministic_repair_job(
    incident_id: str,
    *,
    capability_code: str | None = None,
) -> dict[str, Any]:
    incident = (
        maintenance.read_runtime_incident(
            incident_id
        )
    )

    if incident is None:
        raise ValueError(
            "INCIDENT_NOT_DECLARED"
        )

    if incident.state != "REPAIR_REQUIRED":
        raise ValueError(
            "INCIDENT_NOT_REPAIR_REQUIRED"
        )

    convergence = (
        convergence_state()
    )

    if (
        convergence.get("converged")
        is not True
    ):
        raise ValueError(
            "DEV_MIRROR_NOT_CONVERGED"
        )

    capability = (
        _resolve_capability(
            incident_id,
            capability_code,
        )
    )

    context = {
        "base_sha": convergence[
            "development"
        ],
        "requester": (
            _canonical_requester()
        ),
    }

    recipe = capability.builder(
        incident,
        context,
    )

    if not isinstance(
        recipe,
        dict,
    ):
        raise ValueError(
            "REPAIR_RECIPE_INVALID"
        )

    actions = recipe.get(
        "actions"
    )

    checks = recipe.get(
        "checks"
    )

    if not isinstance(
        actions,
        list,
    ):
        raise ValueError(
            "REPAIR_RECIPE_ACTIONS_INVALID"
        )

    if not isinstance(
        checks,
        list,
    ) or not checks:
        raise ValueError(
            "REPAIR_RECIPE_CHECKS_INVALID"
        )

    _validate_scope(
        incident,
        capability,
        actions,
    )

    attempt_number = (
        incident.attempts + 1
    )

    job_id = (
        incident.repair_job_id
        or deterministic_repair_job_id(
            incident.incident_id,
            attempt_number,
        )
    )

    job = canonicalize_job(
        {
            "job_id": job_id,
            "objective": str(
                recipe.get(
                    "objective"
                )
                or (
                    "Reparacion "
                    f"{capability.code}"
                )
            ),
            "mode": "MUTATION",
            "base_sha": context[
                "base_sha"
            ],
            "requester": context[
                "requester"
            ],
            "actions": actions,
            "checks": checks,
        }
    )

    errors = validate_worker_job(
        job
    )

    if errors:
        raise ValueError(
            "REPAIR_JOB_INVALID:"
            + ",".join(errors)
        )

    job = validate_repair_worker_job(
        incident_id,
        job,
    )

    spec = _persist_spec(
        job
    )

    return {
        "incident_id": incident_id,
        "capability": capability.code,
        "job": job,
        "spec_path": str(spec),
        "production_touched": False,
    }


def publish_planned_repair(
    incident_id: str,
    *,
    capability_code: str | None = None,
) -> dict[str, Any]:
    planned = (
        build_deterministic_repair_job(
            incident_id,
            capability_code=(
                capability_code
            ),
        )
    )

    publication = (
        publish_repair_job(
            incident_id,
            planned["job"],
        )
    )

    return {
        **planned,
        "publication": publication,
        "production_touched": False,
    }
