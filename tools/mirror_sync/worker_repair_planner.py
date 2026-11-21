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

import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from tools.mirror_sync import worker_maintenance_runtime as maintenance
from tools.mirror_sync import worker_repair_capability_registry as learned_registry
from tools.mirror_sync.git_divergence_guard import ensure_submit_convergence
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
    requester: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(requester, dict):
        email = str(
            requester.get("email") or ""
        ).strip().lower()

        if not email:
            raise ValueError(
                "REPAIR_PLANNER_REQUESTER_REQUIRED"
            )

        return {
            "email": email,
            "source": str(
                requester.get("source") or "worker_repair"
            ).strip(),
            "project": str(
                requester.get("project") or "EDARSAHUB-BOS"
            ).strip(),
            "chat": str(
                requester.get("chat") or "Worker Repair Planner"
            ).strip(),
        }

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


def _learned_as_runtime_capability(
    learned: learned_registry.LearnedCapability,
) -> RepairCapability:
    def builder(
        _incident: Any,
        _context: dict[str, Any],
    ) -> dict[str, Any]:
        return learned_registry.recipe_from_learned(
            learned
        )

    return RepairCapability(
        code=learned.code,
        incident_ids=learned.incident_ids,
        required_paths=learned.required_paths,
        builder=builder,
    )


def _resolve_capability(
    incident_id: str,
    capability_code: str | None,
    *,
    problem_signature: str | None = None,
) -> RepairCapability:
    code = str(capability_code or "").strip()

    if code:
        capability = _CAPABILITIES.get(code)

        if capability is not None:
            if incident_id not in capability.incident_ids:
                raise ValueError(
                    "REPAIR_CAPABILITY_INCIDENT_MISMATCH"
                )
            return capability

        learned = learned_registry.resolve_learned_capability(
            incident_id=incident_id,
            problem_signature=problem_signature,
            capability_code=code,
        )
        if learned is None:
            raise ValueError(
                "REPAIR_CAPABILITY_UNKNOWN"
            )
        return _learned_as_runtime_capability(
            learned
        )

    matches = [
        item
        for item in _CAPABILITIES.values()
        if incident_id in item.incident_ids
    ]

    learned = learned_registry.resolve_learned_capability(
        incident_id=incident_id,
        problem_signature=problem_signature,
    )

    if learned is not None and learned.code not in {
        item.code for item in matches
    }:
        matches.append(
            _learned_as_runtime_capability(
                learned
            )
        )

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
    problem_signature: str | None = None,
    requester: dict[str, Any] | None = None,
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

    if incident.state not in {
        "REPAIR_REQUIRED",
        "REJECTED",
    }:
        raise ValueError(
            "INCIDENT_NOT_REPAIRABLE"
        )

    capability = (
        _resolve_capability(
            incident_id,
            capability_code,
            problem_signature=problem_signature,
        )
    )

    allowed, reason = (
        maintenance.repair_attempt_allowed(
            incident_id
        )
    )

    if (
        not allowed
        and not incident.repair_job_id
    ):
        raise ValueError(reason)

    provisional_job_id = (
        incident.repair_job_id
        or deterministic_repair_job_id(
            incident.incident_id,
            incident.attempts + 1,
        )
    )

    convergence = ensure_submit_convergence(
        ROOT,
        job_id=provisional_job_id,
        owner="worker-repair-planner",
        owner_pid=os.getpid(),
    )

    if (
        convergence.get("converged")
        is not True
    ):
        raise ValueError(
            "DEV_MIRROR_NOT_CONVERGED:"
            + str(convergence.get("status"))
        )

    try:
        resolved_requester = (
            _canonical_requester(requester)
        )
    except TypeError:
        resolved_requester = (
            _canonical_requester()
        )

    context = {
        "base_sha": convergence[
            "development"
        ],
        "requester": resolved_requester,
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


def declare_registered_incident(
    incident_id: str,
    *,
    capability_code: str,
    requester: dict[str, Any] | None = None,
) -> dict[str, Any]:
    capability = _resolve_capability(
        incident_id,
        capability_code,
    )
    state = maintenance.declare_runtime_incident(
        incident_id,
        list(capability.required_paths),
        problem_signature=capability.code,
        capability_code=capability.code,
        requester=requester,
    )
    return {
        "incident_id": state.incident_id,
        "state": state.state,
        "target_paths": list(state.target_paths),
        "capability": state.capability_code,
        "production_touched": False,
    }


def publish_planned_repair(
    incident_id: str,
    *,
    capability_code: str | None = None,
    problem_signature: str | None = None,
    requester: dict[str, Any] | None = None,
) -> dict[str, Any]:
    planned = (
        build_deterministic_repair_job(
            incident_id,
            capability_code=(
                capability_code
            ),
            problem_signature=(
                problem_signature
            ),
            requester=requester,
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


# WORKER_REPAIR_CANONICAL_JOB_INGRESS_CAPABILITY_V1

_CANONICAL_INGRESS_INCIDENT = (
    "EDARSAHUB-BOS-WORKER-V1.2-"
    "CANONICAL-JOB-INGRESS-R1"
)

_CANONICAL_INGRESS_PUBLISHER = (
    "tools/mirror_sync/"
    "gate_chain_publisher.py"
)

_CANONICAL_INGRESS_TEST = (
    "backend/tests/"
    "test_worker_canonical_job_ingress_contract.py"
)


def _canonical_job_ingress_recipe(
    incident: Any,
    context: dict[str, Any],
) -> dict[str, Any]:

    publisher_path = (
        ROOT
        / _CANONICAL_INGRESS_PUBLISHER
    )

    if not publisher_path.is_file():
        raise ValueError(
            "CANONICAL_INGRESS_PUBLISHER_MISSING"
        )

    publisher = publisher_path.read_text(
        encoding="utf-8"
    )

    test_path = (
        ROOT
        / _CANONICAL_INGRESS_TEST
    )

    if not test_path.is_file():
        raise ValueError(
            "CANONICAL_INGRESS_TEST_MISSING"
        )

    test_source = test_path.read_text(
        encoding="utf-8"
    )

    test_sha = hashlib.sha256(
        test_source.encode("utf-8")
    ).hexdigest()

    old_imports = """import argparse
import json
import re
import subprocess
import sys
"""

    new_imports = """import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
"""

    if publisher.count(old_imports) == 1:
        import_anchor = old_imports
    elif publisher.count(new_imports) == 1:
        import_anchor = new_imports
    else:
        raise ValueError(
            "CANONICAL_INGRESS_IMPORT_ANCHOR_DRIFT"
        )

    old_forbidden = """    for key, _ in _walk(template):
        if key in FORBIDDEN_KEYS:
            raise ValueError(f"FORBIDDEN_TEMPLATE_KEY:{key}")
"""

    new_forbidden = """    def walk_with_path(
        value: Any,
        path: tuple[Any, ...] = (),
    ):
        if isinstance(value, dict):
            for raw_key, item in value.items():
                key = str(raw_key).lower()
                child = path + (str(raw_key),)
                yield child, key, item
                yield from walk_with_path(
                    item,
                    child,
                )
        elif isinstance(value, list):
            for index, item in enumerate(value):
                yield from walk_with_path(
                    item,
                    path + (index,),
                )

    for path, key, _ in walk_with_path(
        template
    ):
        readonly_sql_query = (
            key == "sql"
            and str(
                template.get("mode") or ""
            ).strip().upper()
            == "READ_ONLY_SQL"
            and len(path) == 5
            and path[0] == "checks"
            and isinstance(path[1], int)
            and path[2] == "queries"
            and isinstance(path[3], int)
            and path[4] == "sql"
        )

        if (
            key in FORBIDDEN_KEYS
            and not readonly_sql_query
        ):
            raise ValueError(
                f"FORBIDDEN_TEMPLATE_KEY:{key}"
            )
"""

    if publisher.count(old_forbidden) == 1:
        forbidden_anchor = old_forbidden
    elif publisher.count(new_forbidden) == 1:
        forbidden_anchor = new_forbidden
    else:
        raise ValueError(
            "CANONICAL_INGRESS_SQL_ANCHOR_DRIFT"
        )

    main_anchor = "def main() -> int:\n"

    if publisher.count(main_anchor) != 1:
        raise ValueError(
            "CANONICAL_INGRESS_MAIN_ANCHOR_DRIFT"
        )

    submit_block = r"""
STATE = (
    ROOT
    / ".git"
    / "universal-worker-queue"
)

DRAFTS = STATE / "drafts"
PENDING = STATE / "pending"
PROCESSING = STATE / "processing"
RESULTS = STATE / "results"
DONE = STATE / "done"
REJECTED = STATE / "rejected"


def _atomic_submit_draft(
    job: dict[str, Any],
) -> Path:

    DRAFTS.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        DRAFTS
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
        current = path.read_text(
            encoding="utf-8"
        )

        if current != serialized:
            raise ValueError(
                "JOB_DRAFT_IDEMPOTENCY_CONFLICT"
            )

        return path

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=DRAFTS,
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


def _submit_local_lifecycle(
    job_id: str,
) -> str | None:

    name = f"{job_id}.json"

    if (
        (RESULTS / name).is_file()
        or (DONE / name).is_file()
    ):
        return "ALREADY_COMPLETED"

    if (PROCESSING / name).is_file():
        return "ALREADY_PROCESSING"

    if (PENDING / name).is_file():
        return "ALREADY_SUBMITTED"

    if (REJECTED / name).is_file():
        return "INVALID_JOB"

    return None


def _submit_remote_exists(
    job_id: str,
    *,
    remote: str,
    queue_branch: str,
) -> bool:

    rel = (
        "worker_queue/inbox/"
        f"{job_id}.json"
    )

    fetched = git(
        "fetch",
        remote,
        queue_branch,
        check=False,
    )

    if fetched.returncode != 0:
        return False

    return (
        git(
            "cat-file",
            "-e",
            f"{remote}/{queue_branch}:{rel}",
            check=False,
        ).returncode
        == 0
    )


def _submit_convergence(
    *,
    remote: str,
) -> dict[str, Any]:

    for branch in (
        "Edarsahub_Desarrollo",
        "mirror/emergent-live",
    ):
        fetched = git(
            "fetch",
            remote,
            branch,
            check=False,
        )

        if fetched.returncode != 0:
            return {
                "converged": False,
                "reason": "FETCH_FAILED",
            }

    local = git(
        "rev-parse",
        "HEAD",
        check=False,
    ).stdout.strip()

    development = git(
        "rev-parse",
        f"{remote}/Edarsahub_Desarrollo",
        check=False,
    ).stdout.strip()

    mirror = git(
        "rev-parse",
        f"{remote}/mirror/emergent-live",
        check=False,
    ).stdout.strip()

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


def _submit_failure_status(
    error: Exception,
) -> str:

    message = (
        f"{type(error).__name__}:{error}"
    ).upper()

    if (
        "REMOTE_MOVED_RETRY_REQUIRED"
        in message
    ):
        return "REMOTE_MOVED_RETRYABLE"

    if "GIT_LOCK_BUSY" in message:
        return "WRITER_BUSY"

    if (
        "CLAIM" in message
        and "BUSY" in message
    ):
        return "CLAIM_BUSY"

    if (
        "WRITER" in message
        and "BUSY" in message
    ):
        return "WRITER_BUSY"

    return "RECOVERY_REQUIRED"


def submit(
    job_spec: dict[str, Any],
    *,
    remote: str = "origin",
    queue_branch: str = "worker/requests",
) -> dict[str, Any]:

    try:
        template = validate_template(
            job_spec
        )

        from tools.mirror_sync.universal_job_bridge import (
            validate as validate_worker_job,
        )

        errors = validate_worker_job(
            template
        )

        if errors:
            return {
                "status": "INVALID_JOB",
                "errors": errors,
                "production_touched": False,
            }

    except Exception as exc:
        return {
            "status": "INVALID_JOB",
            "reason": (
                f"{type(exc).__name__}:{exc}"
            ),
            "production_touched": False,
        }

    job_id = str(
        template["job_id"]
    )

    try:
        draft = _atomic_submit_draft(
            template
        )
    except Exception as exc:
        return {
            "status": "RECOVERY_REQUIRED",
            "job_id": job_id,
            "reason": (
                f"{type(exc).__name__}:{exc}"
            ),
            "production_touched": False,
        }

    lifecycle = _submit_local_lifecycle(
        job_id
    )

    if lifecycle:
        return {
            "status": lifecycle,
            "job_id": job_id,
            "draft_path": str(draft),
            "production_touched": False,
        }

    if _submit_remote_exists(
        job_id,
        remote=remote,
        queue_branch=queue_branch,
    ):
        return {
            "status": "ALREADY_SUBMITTED",
            "job_id": job_id,
            "draft_path": str(draft),
            "production_touched": False,
        }

    try:
        from tools.mirror_sync.worker_requester_rbac import (
            authorize_requester,
        )

        authorization = authorize_requester(
            template["requester"]
        )

    except Exception as exc:
        return {
            "status": "REQUESTER_DENIED",
            "job_id": job_id,
            "reason": (
                f"{type(exc).__name__}:{exc}"
            ),
            "production_touched": False,
        }

    if (
        authorization.get("allowed")
        is not True
    ):
        return {
            "status": "REQUESTER_DENIED",
            "job_id": job_id,
            "reason": authorization.get(
                "reason"
            ),
            "production_touched": False,
        }

    convergence = _submit_convergence(
        remote=remote
    )

    if (
        convergence.get("converged")
        is not True
    ):
        return {
            "status": "WAITING_FOR_CONVERGENCE",
            "job_id": job_id,
            "draft_path": str(draft),
            "convergence": convergence,
            "production_touched": False,
        }

    plan = {
        "status": "READY_TO_PUBLISH",
        "job_id": job_id,
        "template": template,
    }

    try:
        publication = publish(
            plan,
            remote=remote,
            queue_branch=queue_branch,
        )

    except Exception as exc:
        return {
            "status": _submit_failure_status(
                exc
            ),
            "job_id": job_id,
            "draft_path": str(draft),
            "reason": (
                f"{type(exc).__name__}:{exc}"
            ),
            "production_touched": False,
        }

    publication_status = str(
        publication.get("status")
        or ""
    ).strip()

    if publication_status == "PUBLISHED":
        final = "SUBMITTED"
    elif publication_status == "EXISTS":
        final = "ALREADY_SUBMITTED"
    else:
        final = "RECOVERY_REQUIRED"

    return {
        "status": final,
        "job_id": job_id,
        "draft_path": str(draft),
        "publication": publication,
        "production_touched": False,
    }
"""

    ingress_test = r"""from __future__ import annotations

from pathlib import Path

import pytest

from tools.mirror_sync import gate_chain_publisher as ingress


def requester():
    return {
        "email": "test@example.invalid",
        "source": "pytest",
        "project": "EDARSAHUB",
        "chat": "canonical-ingress",
    }


def readonly_job(job_id):
    return {
        "job_id": job_id,
        "objective": "Test canonical ingress.",
        "requester": requester(),
        "mode": "READ_ONLY",
        "actions": [],
        "checks": [
            {
                "type": "git_diff_check",
            }
        ],
    }


def readonly_sql_job(job_id):
    return {
        "job_id": job_id,
        "objective": "Test READ_ONLY_SQL ingress.",
        "requester": requester(),
        "mode": "READ_ONLY_SQL",
        "actions": [],
        "checks": [
            {
                "type": "sql_readonly_audit",
                "source": "EDARSAHUB",
                "queries": [
                    {
                        "name": "identity",
                        "sql": (
                            "SELECT DB_NAME() "
                            "AS database_name"
                        ),
                    }
                ],
            }
        ],
    }


def redirect_state(
    tmp_path,
    monkeypatch,
):
    for name in (
        "DRAFTS",
        "PENDING",
        "PROCESSING",
        "RESULTS",
        "DONE",
        "REJECTED",
    ):
        path = (
            tmp_path
            / name.lower()
        )

        path.mkdir()

        monkeypatch.setattr(
            ingress,
            name,
            path,
        )


def test_submit_exists():
    assert callable(
        ingress.submit
    )


def test_readonly_sql_allowed_only_in_query():
    result = ingress.validate_template(
        readonly_sql_job(
            "INGRESS-SQL-1"
        )
    )

    assert (
        result["mode"]
        == "READ_ONLY_SQL"
    )

    bad = readonly_sql_job(
        "INGRESS-SQL-2"
    )

    bad["requester"]["sql"] = (
        "SELECT 1"
    )

    with pytest.raises(
        ValueError,
        match="FORBIDDEN_TEMPLATE_KEY:sql",
    ):
        ingress.validate_template(
            bad
        )


def test_completed_idempotency(
    tmp_path,
    monkeypatch,
):
    redirect_state(
        tmp_path,
        monkeypatch,
    )

    (
        ingress.RESULTS
        / "INGRESS-DONE.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = ingress.submit(
        readonly_job(
            "INGRESS-DONE"
        )
    )

    assert (
        result["status"]
        == "ALREADY_COMPLETED"
    )


def test_processing_idempotency(
    tmp_path,
    monkeypatch,
):
    redirect_state(
        tmp_path,
        monkeypatch,
    )

    (
        ingress.PROCESSING
        / "INGRESS-PROCESSING.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = ingress.submit(
        readonly_job(
            "INGRESS-PROCESSING"
        )
    )

    assert (
        result["status"]
        == "ALREADY_PROCESSING"
    )


def test_pending_idempotency(
    tmp_path,
    monkeypatch,
):
    redirect_state(
        tmp_path,
        monkeypatch,
    )

    (
        ingress.PENDING
        / "INGRESS-PENDING.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = ingress.submit(
        readonly_job(
            "INGRESS-PENDING"
        )
    )

    assert (
        result["status"]
        == "ALREADY_SUBMITTED"
    )


def test_no_tmp_dependency():
    assert "/tmp" not in str(
        ingress.DRAFTS
    )


def test_submit_reuses_canonical_publisher():
    source = Path(
        ingress.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "def submit(" in source
    assert "publication = publish(" in source
"""

    publisher_sha = hashlib.sha256(
        publisher.encode("utf-8")
    ).hexdigest()

    return {
        "objective": (
            "Materializar canonical job ingress "
            "submit(job_spec), persistente, "
            "idempotente y fail-closed."
        ),
        "actions": [
            {
                "type": "replace_text",
                "path": _CANONICAL_INGRESS_PUBLISHER,
                "old": import_anchor,
                "new": new_imports,
                "expected_count": 1,
                "expected_sha256": publisher_sha,
            },
            {
                "type": "replace_text",
                "path": _CANONICAL_INGRESS_PUBLISHER,
                "old": forbidden_anchor,
                "new": new_forbidden,
                "expected_count": 1,
            },
            {
                "type": "replace_text",
                "path": _CANONICAL_INGRESS_PUBLISHER,
                "old": main_anchor,
                "new": (
                    main_anchor
                    if "def submit(" in publisher
                    else (
                        submit_block
                        + "\n\n"
                        + main_anchor
                    )
                ),
                "expected_count": 1,
            },
            {
                "type": "write_file",
                "path": _CANONICAL_INGRESS_TEST,
                "content": ingress_test,
                "expected_sha256": test_sha,
            },
        ],
        "checks": [
            {
                "type": "py_compile",
                "paths": [
                    _CANONICAL_INGRESS_PUBLISHER,
                    _CANONICAL_INGRESS_TEST,
                ],
            },
            {
                "type": "pytest",
                "paths": [
                    _CANONICAL_INGRESS_TEST,
                ],
            },
            {
                "type": "git_diff_check",
            },
        ],
    }


register_capability(
    RepairCapability(
        code="CANONICAL_JOB_INGRESS",
        incident_ids=(
            _CANONICAL_INGRESS_INCIDENT,
        ),
        required_paths=(
            _CANONICAL_INGRESS_PUBLISHER,
            _CANONICAL_INGRESS_TEST,
        ),
        builder=_canonical_job_ingress_recipe,
    )
)


# D2.2 - exact runtime artifact convergence repair.
_D2_2_INCIDENT = "EDARSAHUB-D2-2-RUNTIME-ARTIFACT-CONVERGENCE-R1"
_D2_2_CAPABILITY = "D2_2_RUNTIME_ARTIFACT_CONVERGENCE"
_D2_2_GITIGNORE = ".gitignore"
_D2_2_GUARD = "tools/mirror_sync/shared_app_safety_guard.sh"
_D2_2_IGNORE_TEST = "backend/tests/test_preview_local_artifacts_ignore_contract.py"
_D2_2_SAFETY_TEST = "backend/tests/test_shared_app_sync_safety_contract.py"


def _d2_2_runtime_artifact_recipe(
    incident: Any,
    context: dict[str, Any],
) -> dict[str, Any]:
    gitignore_path = ROOT / _D2_2_GITIGNORE
    guard_path = ROOT / _D2_2_GUARD
    ignore_test_path = ROOT / _D2_2_IGNORE_TEST
    safety_test_path = ROOT / _D2_2_SAFETY_TEST

    for path in (
        gitignore_path,
        guard_path,
        ignore_test_path,
        safety_test_path,
    ):
        if not path.is_file():
            raise ValueError("D2_2_REQUIRED_FILE_MISSING")

    gitignore = gitignore_path.read_text(encoding="utf-8")
    guard = guard_path.read_text(encoding="utf-8")
    ignore_test = ignore_test_path.read_text(encoding="utf-8")
    safety_test = safety_test_path.read_text(encoding="utf-8")

    ignored_line = "/.emergent/stripped_env_names\n"
    if gitignore.count(ignored_line) != 1:
        raise ValueError("D2_2_GITIGNORE_ANCHOR_DRIFT")

    guard_const = 'EDARSAHUB_PLATFORM_MANAGED_SYSTEM_DEPS_REL=".emergent/system_deps.txt"\n'
    guard_const_new = (
        guard_const
        + 'EDARSAHUB_PLATFORM_MANAGED_STRIPPED_ENV_REL=".emergent/stripped_env_names"\n'
    )
    if guard.count(guard_const) != 1:
        raise ValueError("D2_2_GUARD_CONST_ANCHOR_DRIFT")

    status_anchor = """edarsahub_effective_status() {
    local raw
    raw="$(git -C "$EDARSAHUB_APP" status --porcelain=v1 --untracked-files=all)"
    if edarsahub_expected_platform_system_deps_drift; then
        printf '%s\\n' "$raw" | grep -v '^ M \\.emergent/system_deps\\.txt$' || true
    else
        printf '%s\\n' "$raw"
    fi
}
"""
    status_new = """edarsahub_validated_platform_stripped_env_artifact() {
    local current_path raw size
    current_path="$EDARSAHUB_APP/$EDARSAHUB_PLATFORM_MANAGED_STRIPPED_ENV_REL"

    [ -f "$current_path" ] || return 1
    [ ! -L "$current_path" ] || return 1

    raw="$(git -C "$EDARSAHUB_APP" status --porcelain=v1 --untracked-files=all -- "$EDARSAHUB_PLATFORM_MANAGED_STRIPPED_ENV_REL")"
    [ "$raw" = "?? $EDARSAHUB_PLATFORM_MANAGED_STRIPPED_ENV_REL" ] || return 1

    size="$(wc -c < "$current_path" 2>/dev/null || echo 65537)"
    case "$size" in ''|*[!0-9]*) return 1 ;; esac
    [ "$size" -le 65536 ] || return 1

    return 0
}

edarsahub_effective_status() {
    local raw effective
    raw="$(git -C "$EDARSAHUB_APP" status --porcelain=v1 --untracked-files=all)"
    effective="$raw"

    if edarsahub_expected_platform_system_deps_drift; then
        effective="$(printf '%s\\n' "$effective" | grep -v '^ M \\.emergent/system_deps\\.txt$' || true)"
    fi
    if edarsahub_validated_platform_stripped_env_artifact; then
        effective="$(printf '%s\\n' "$effective" | grep -v '^?? \\.emergent/stripped_env_names$' || true)"
    fi

    printf '%s\\n' "$effective"
}
"""
    if guard.count(status_anchor) != 1:
        raise ValueError("D2_2_GUARD_STATUS_ANCHOR_DRIFT")

    untracked_old = 'untracked="$(git -C "$EDARSAHUB_APP" status --porcelain=v1 --untracked-files=all | grep \'^?? \' | wc -l)"'
    untracked_new = 'untracked="$(edarsahub_effective_status | grep \'^?? \' | wc -l)"'
    if guard.count(untracked_old) != 1:
        raise ValueError("D2_2_GUARD_UNTRACKED_ANCHOR_DRIFT")

    echo_anchor = """    if edarsahub_expected_platform_system_deps_drift; then
        echo "PLATFORM_MANAGED_SYSTEM_DEPS_DRIFT=IGNORED_EXPECTED_EMPTY_RUNTIME"
    fi
"""
    echo_new = echo_anchor + """    if edarsahub_validated_platform_stripped_env_artifact; then
        echo "PLATFORM_MANAGED_STRIPPED_ENV_ARTIFACT=VALIDATED_RUNTIME_ARTIFACT"
    fi
"""
    if guard.count(echo_anchor) != 1:
        raise ValueError("D2_2_GUARD_ECHO_ANCHOR_DRIFT")

    ignore_old = '        "/.emergent/stripped_env_names",\n'
    if ignore_test.count(ignore_old) != 1:
        raise ValueError("D2_2_IGNORE_TEST_ANCHOR_DRIFT")
    ignore_tail = """    for pattern in required:
        assert pattern in text


"""
    ignore_tail_new = """    for pattern in required:
        assert pattern in text

    assert "/.emergent/stripped_env_names" not in text


"""
    if ignore_test.count(ignore_tail) != 1:
        raise ValueError("D2_2_IGNORE_TEST_TAIL_DRIFT")

    safety_anchor = """def test_dirty_app_is_hard_blocked_without_discarding_local_work():
"""
    safety_new = """def test_stripped_env_runtime_artifact_is_exact_and_bounded():
    guard = ROOT / "tools/mirror_sync/shared_app_safety_guard.sh"
    text = guard.read_text(encoding="utf-8")
    assert 'EDARSAHUB_PLATFORM_MANAGED_STRIPPED_ENV_REL=".emergent/stripped_env_names"' in text
    assert '[ ! -L "$current_path" ] || return 1' in text
    assert '[ "$raw" = "?? $EDARSAHUB_PLATFORM_MANAGED_STRIPPED_ENV_REL" ] || return 1' in text
    assert '[ "$size" -le 65536 ] || return 1' in text
    assert "PLATFORM_MANAGED_STRIPPED_ENV_ARTIFACT=VALIDATED_RUNTIME_ARTIFACT" in text


""" + safety_anchor
    if safety_test.count(safety_anchor) != 1:
        raise ValueError("D2_2_SAFETY_TEST_ANCHOR_DRIFT")

    return {
        "objective": (
            "D2.2 Runtime Artifact Convergence: retirar stripped_env_names "
            "de .gitignore y clasificar exclusivamente ese artefacto runtime "
            "como VALIDATED_RUNTIME_ARTIFACT con validacion estricta."
        ),
        "actions": [
            {
                "type": "replace_text",
                "path": _D2_2_GITIGNORE,
                "old": ignored_line,
                "new": "",
                "expected_count": 1,
                "expected_sha256": hashlib.sha256(
                    gitignore.encode("utf-8")
                ).hexdigest(),
            },
            {
                "type": "replace_text",
                "path": _D2_2_GUARD,
                "old": guard_const,
                "new": guard_const_new,
                "expected_count": 1,
                "expected_sha256": hashlib.sha256(
                    guard.encode("utf-8")
                ).hexdigest(),
            },
            {
                "type": "replace_text",
                "path": _D2_2_GUARD,
                "old": status_anchor,
                "new": status_new,
                "expected_count": 1,
            },
            {
                "type": "replace_text",
                "path": _D2_2_GUARD,
                "old": untracked_old,
                "new": untracked_new,
                "expected_count": 1,
            },
            {
                "type": "replace_text",
                "path": _D2_2_GUARD,
                "old": echo_anchor,
                "new": echo_new,
                "expected_count": 1,
            },
            {
                "type": "replace_text",
                "path": _D2_2_IGNORE_TEST,
                "old": ignore_old,
                "new": "",
                "expected_count": 1,
                "expected_sha256": hashlib.sha256(
                    ignore_test.encode("utf-8")
                ).hexdigest(),
            },
            {
                "type": "replace_text",
                "path": _D2_2_IGNORE_TEST,
                "old": ignore_tail,
                "new": ignore_tail_new,
                "expected_count": 1,
            },
            {
                "type": "replace_text",
                "path": _D2_2_SAFETY_TEST,
                "old": safety_anchor,
                "new": safety_new,
                "expected_count": 1,
                "expected_sha256": hashlib.sha256(
                    safety_test.encode("utf-8")
                ).hexdigest(),
            },
        ],
        "checks": [
            {
                "type": "pytest",
                "paths": [
                    _D2_2_IGNORE_TEST,
                    _D2_2_SAFETY_TEST,
                ],
            },
            {
                "type": "git_diff_check",
            },
        ],
    }


register_capability(
    RepairCapability(
        code=_D2_2_CAPABILITY,
        incident_ids=(_D2_2_INCIDENT,),
        required_paths=(
            _D2_2_GITIGNORE,
            _D2_2_GUARD,
            _D2_2_IGNORE_TEST,
            _D2_2_SAFETY_TEST,
        ),
        builder=_d2_2_runtime_artifact_recipe,
    )
)


# Preview Watchdog Transient Recovery - bounded out-of-band backend recovery.
_PREVIEW_WATCHDOG_INCIDENT = (
    "EDARSAHUB-BOS-PREVIEW-WATCHDOG-TRANSIENT-RECOVERY-R1"
)
_PREVIEW_WATCHDOG_CAPABILITY = "PREVIEW_WATCHDOG_TRANSIENT_RECOVERY"
_PREVIEW_WATCHDOG_SCRIPT = "tools/bootstrap/edarsahub_bootstrap_watchdog.py"
_PREVIEW_WATCHDOG_TEST = (
    "backend/tests/test_bootstrap_watchdog_safety_contract.py"
)


def _preview_watchdog_transient_recovery_recipe(
    incident: Any,
    context: dict[str, Any],
) -> dict[str, Any]:
    watchdog_path = ROOT / _PREVIEW_WATCHDOG_SCRIPT
    test_path = ROOT / _PREVIEW_WATCHDOG_TEST

    for path in (watchdog_path, test_path):
        if not path.is_file():
            raise ValueError("PREVIEW_WATCHDOG_REQUIRED_FILE_MISSING")

    watchdog = watchdog_path.read_text(encoding="utf-8")
    safety_test = test_path.read_text(encoding="utf-8")

    const_old = """BACKEND_RECOVERY_COOLDOWN = int(os.environ.get("EDARSAHUB_BACKEND_RECOVERY_COOLDOWN", "120"))
RUNTIME = APP / ".git" / "universal-worker-queue" / "runtime"
MIRROR_STATE = APP / ".git" / "mirror-sync"
MIRROR_ENABLE = MIRROR_STATE / "ENABLED"
MIRROR_STOP = MIRROR_STATE / "STOP"
SYNC_PAUSE = APP / ".git" / "EDARSAHUB_SYNC_PAUSED"
STATUS = STATE / "status.json"
AUDIT = STATE / "audit.jsonl"
BACKEND_RECOVERY_STAMP = STATE / "backend_recovery_epoch"
"""

    const_new = """BACKEND_RECOVERY_COOLDOWN = int(os.environ.get("EDARSAHUB_BACKEND_RECOVERY_COOLDOWN", "120"))
BACKEND_UNHEALTHY_THRESHOLD = max(
    1,
    int(os.environ.get("EDARSAHUB_BACKEND_UNHEALTHY_THRESHOLD", "3")),
)
BACKEND_STOPWAITSECS = 30
SUPERVISOR_RESTART_TIMEOUT = max(
    BACKEND_STOPWAITSECS + 5,
    int(os.environ.get("EDARSAHUB_SUPERVISOR_RESTART_TIMEOUT", "65")),
)
STOPPED_SUPERVISOR_STATES = frozenset({"STOPPED", "FATAL", "EXITED"})
RUNTIME = APP / ".git" / "universal-worker-queue" / "runtime"
MIRROR_STATE = APP / ".git" / "mirror-sync"
MIRROR_ENABLE = MIRROR_STATE / "ENABLED"
MIRROR_STOP = MIRROR_STATE / "STOP"
SYNC_PAUSE = APP / ".git" / "EDARSAHUB_SYNC_PAUSED"
STATUS = STATE / "status.json"
AUDIT = STATE / "audit.jsonl"
BACKEND_RECOVERY_STAMP = STATE / "backend_recovery_epoch"
BACKEND_RECOVERY_STATE = STATE / "backend_recovery_state.json"
"""

    health_old = """def backend_wake_route_health() -> dict:
    \"\"\"Probe the local route without a queue proof.

    A healthy mounted route must reject the request with 401. 404 means the
    running backend is stale and does not have the router mounted.
    \"\"\"
    try:
        result = run(
            [
                "curl",
                "--silent",
                "--show-error",
                "--connect-timeout",
                "2",
                "--max-time",
                "5",
                "--output",
                "/tmp/edarsahub-bootstrap-wake-probe.json",
                "--write-out",
                "%{http_code}",
                "--request",
                "POST",
                BACKEND_WAKE_URL,
                "--header",
                "Content-Type: application/json",
                "--data",
                "{}",
            ],
            timeout=8,
        )
        code = (result.stdout or "").strip()[-3:]
        healthy = result.returncode == 0 and code == "401"
        return {"healthy": healthy, "http_code": code or "000", "returncode": result.returncode}
    except Exception as exc:
        return {"healthy": False, "http_code": "000", "error": str(exc)}


def maybe_recover_backend() -> dict:
    if is_production_environment():
        audit("BACKEND_RECOVERY_BLOCKED_PRODUCTION_ENV", service=BACKEND_SERVICE)
        return {"state": "BLOCKED_PRODUCTION_ENV", "restarted": False}

    probe = backend_wake_route_health()
    if probe.get("healthy"):
        return {"state": "HEALTHY", "probe": probe, "restarted": False}

    now_epoch = int(time.time())
    try:
        last_epoch = int(BACKEND_RECOVERY_STAMP.read_text(encoding="utf-8").strip())
    except Exception:
        last_epoch = 0
    if now_epoch - last_epoch < BACKEND_RECOVERY_COOLDOWN:
        audit("BACKEND_RECOVERY_COOLDOWN", probe=probe, service=BACKEND_SERVICE)
        return {"state": "COOLDOWN", "probe": probe, "restarted": False}

    STATE.mkdir(parents=True, exist_ok=True)
    BACKEND_RECOVERY_STAMP.write_text(str(now_epoch) + "\\n", encoding="utf-8")
    restarted = supervisor_restart("WAKE_ROUTE_UNHEALTHY", BACKEND_SERVICE)
    audit(
        "PREVIEW_BACKEND_STALE_RECOVERY",
        probe=probe,
        action="SUPERVISOR_RESTART",
        service=BACKEND_SERVICE,
        restarted=restarted,
    )
    return {
        "state": "RESTART_REQUESTED" if restarted else "RESTART_FAILED",
        "probe": probe,
        "restarted": restarted,
    }
"""

    health_new = """def backend_wake_route_health() -> dict:
    \"\"\"Probe the local route without a queue proof.

    A healthy mounted route must reject the request with 401. 404 means the
    running backend is stale and does not have the router mounted.
    \"\"\"
    try:
        result = run(
            [
                "curl",
                "--silent",
                "--show-error",
                "--connect-timeout",
                "2",
                "--max-time",
                "5",
                "--output",
                "/dev/null",
                "--write-out",
                "%{http_code}",
                "--request",
                "POST",
                BACKEND_WAKE_URL,
                "--header",
                "Content-Type: application/json",
                "--data",
                "{}",
            ],
            timeout=8,
        )
        code = (result.stdout or "").strip()[-3:]
        http_code = code if len(code) == 3 and code.isdigit() else "000"
        healthy = result.returncode == 0 and code == "401"
        if healthy:
            failure_kind = None
        elif result.returncode == 28:
            failure_kind = "PROBE_TIMEOUT"
        elif http_code == "404":
            failure_kind = "ROUTE_NOT_MOUNTED"
        elif result.returncode != 0:
            failure_kind = "TRANSPORT_ERROR"
        else:
            failure_kind = "HTTP_UNHEALTHY"
        return {
            "healthy": healthy,
            "http_code": http_code,
            "returncode": result.returncode,
            "failure_kind": failure_kind,
        }
    except subprocess.TimeoutExpired:
        return {
            "healthy": False,
            "http_code": "000",
            "returncode": 124,
            "failure_kind": "PROBE_TIMEOUT",
        }
    except Exception as exc:
        return {
            "healthy": False,
            "http_code": "000",
            "failure_kind": "PROBE_ERROR",
            "error": str(exc),
        }


def backend_supervisor_status(service: str = BACKEND_SERVICE) -> dict:
    try:
        result = run(["supervisorctl", "status", service], cwd=APP, timeout=15)
    except subprocess.TimeoutExpired:
        return {
            "state": "STATUS_TIMEOUT",
            "confirmed_stopped": False,
            "running": False,
            "returncode": 124,
        }
    except Exception as exc:
        return {
            "state": "STATUS_ERROR",
            "confirmed_stopped": False,
            "running": False,
            "error": str(exc),
        }

    raw = (result.stdout or "").strip()
    tokens = raw.split()
    parsed_state = "UNKNOWN"
    if len(tokens) >= 2 and tokens[0] == service:
        parsed_state = tokens[1].upper()
    else:
        for token in tokens:
            candidate = token.strip(",:").upper()
            if candidate in {
                "RUNNING",
                "STARTING",
                "STOPPING",
                "BACKOFF",
                *STOPPED_SUPERVISOR_STATES,
            }:
                parsed_state = candidate
                break

    confirmed_stopped = parsed_state in STOPPED_SUPERVISOR_STATES
    return {
        "state": parsed_state,
        "confirmed_stopped": confirmed_stopped,
        "running": parsed_state == "RUNNING",
        "returncode": result.returncode,
    }


def _write_atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f"{path.name}.tmp-{os.getpid()}-{time.monotonic_ns()}")
    temp.write_text(content, encoding="utf-8")
    os.replace(temp, path)


def _read_backend_recovery_state() -> dict:
    payload = read_json(BACKEND_RECOVERY_STATE)
    if not isinstance(payload, dict):
        return {"consecutive_failures": 0}
    try:
        failures = max(0, int(payload.get("consecutive_failures") or 0))
    except (TypeError, ValueError):
        failures = 0
    return {**payload, "consecutive_failures": failures}


def _write_backend_recovery_state(payload: dict) -> None:
    record = {
        "schema": "edarsahub.backend-recovery-state.v1",
        **payload,
        "updated_at_utc": now(),
        "production_touched": False,
    }
    _write_atomic_text(
        BACKEND_RECOVERY_STATE,
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\\n",
    )


def maybe_recover_backend() -> dict:
    if is_production_environment():
        audit("BACKEND_RECOVERY_BLOCKED_PRODUCTION_ENV", service=BACKEND_SERVICE)
        return {"state": "BLOCKED_PRODUCTION_ENV", "restarted": False}

    prev_state = _read_backend_recovery_state()
    prev_failures = int(prev_state.get("consecutive_failures") or 0)

    probe = backend_wake_route_health()
    if probe.get("healthy"):
        if prev_failures > 0 or BACKEND_RECOVERY_STATE.exists():
            _write_backend_recovery_state(
                {
                    "consecutive_failures": 0,
                    "last_healthy_at_utc": now(),
                    "previous_failures": prev_failures,
                }
            )
        if prev_failures > 0:
            audit(
                "BACKEND_PROBE_RECOVERED",
                previous_failures=prev_failures,
                service=BACKEND_SERVICE,
            )
        return {
            "state": "HEALTHY",
            "probe": probe,
            "consecutive_failures": 0,
            "restarted": False,
        }

    supervisor_info = backend_supervisor_status(BACKEND_SERVICE)
    sup_state = str(supervisor_info.get("state") or "UNKNOWN")
    confirmed_stopped = bool(supervisor_info.get("confirmed_stopped"))
    consecutive_failures = prev_failures + 1

    if not confirmed_stopped and consecutive_failures < BACKEND_UNHEALTHY_THRESHOLD:
        _write_backend_recovery_state(
            {
                "consecutive_failures": consecutive_failures,
                "last_unhealthy_at_utc": now(),
                "last_failure_kind": probe.get("failure_kind"),
                "supervisor_state": sup_state,
            }
        )
        audit(
            "BACKEND_PROBE_TRANSIENT_FAILURE",
            probe=probe,
            supervisor_state=sup_state,
            consecutive_failures=consecutive_failures,
            threshold=BACKEND_UNHEALTHY_THRESHOLD,
            service=BACKEND_SERVICE,
        )
        return {
            "state": "TRANSIENT_UNHEALTHY",
            "probe": probe,
            "supervisor_state": sup_state,
            "consecutive_failures": consecutive_failures,
            "threshold": BACKEND_UNHEALTHY_THRESHOLD,
            "restarted": False,
        }

    now_epoch = int(time.time())
    try:
        last_epoch = int(BACKEND_RECOVERY_STAMP.read_text(encoding="utf-8").strip())
    except Exception:
        last_epoch = 0

    in_cooldown = (now_epoch - last_epoch) < BACKEND_RECOVERY_COOLDOWN
    if in_cooldown and not confirmed_stopped:
        _write_backend_recovery_state(
            {
                "consecutive_failures": consecutive_failures,
                "last_unhealthy_at_utc": now(),
                "last_failure_kind": probe.get("failure_kind"),
                "supervisor_state": sup_state,
            }
        )
        audit(
            "BACKEND_RECOVERY_COOLDOWN",
            probe=probe,
            supervisor_state=sup_state,
            consecutive_failures=consecutive_failures,
            service=BACKEND_SERVICE,
        )
        return {
            "state": "COOLDOWN",
            "probe": probe,
            "supervisor_state": sup_state,
            "consecutive_failures": consecutive_failures,
            "restarted": False,
        }

    cooldown_bypassed = bool(in_cooldown and confirmed_stopped)
    if confirmed_stopped:
        restarted = supervisor_restart("BACKEND_PROCESS_STOPPED", BACKEND_SERVICE)
        recovery_reason = "BACKEND_PROCESS_STOPPED"
    else:
        restarted = supervisor_restart("WAKE_ROUTE_UNHEALTHY", BACKEND_SERVICE)
        recovery_reason = "WAKE_ROUTE_UNHEALTHY"

    post_supervisor = (
        backend_supervisor_status(BACKEND_SERVICE)
        if restarted
        else supervisor_info
    )
    post_probe = backend_wake_route_health() if restarted else probe
    restart_confirmed = bool(
        restarted
        and not post_supervisor.get("confirmed_stopped")
        and (post_supervisor.get("running") or post_probe.get("healthy"))
    )

    if restart_confirmed:
        confirmed_epoch = int(time.time())
        _write_atomic_text(BACKEND_RECOVERY_STAMP, f"{confirmed_epoch}\\n")
        _write_backend_recovery_state(
            {
                "consecutive_failures": 0,
                "last_confirmed_restart_at_utc": now(),
                "last_recovery_reason": recovery_reason,
                "supervisor_state": post_supervisor.get("state"),
            }
        )
    else:
        _write_backend_recovery_state(
            {
                "consecutive_failures": consecutive_failures,
                "last_unhealthy_at_utc": now(),
                "last_failed_restart_at_utc": now(),
                "last_recovery_reason": recovery_reason,
                "supervisor_state": post_supervisor.get("state"),
            }
        )

    audit(
        "PREVIEW_BACKEND_STALE_RECOVERY",
        probe=probe,
        supervisor_state=sup_state,
        post_supervisor_state=post_supervisor.get("state"),
        consecutive_failures=consecutive_failures,
        cooldown_bypassed=cooldown_bypassed,
        reason=recovery_reason,
        action="SUPERVISOR_RESTART",
        service=BACKEND_SERVICE,
        restarted=restart_confirmed,
    )
    return {
        "state": "RESTART_REQUESTED" if restart_confirmed else "RESTART_FAILED",
        "probe": probe,
        "supervisor_state": sup_state,
        "post_supervisor_state": post_supervisor.get("state"),
        "consecutive_failures": 0 if restart_confirmed else consecutive_failures,
        "cooldown_bypassed": cooldown_bypassed,
        "restarted": restart_confirmed,
        "restart_confirmed": restart_confirmed,
    }
"""

    restart_old = """def supervisor_restart(reason: str, service: str = SERVICE) -> bool:
    if is_production_environment():
        audit("SUPERVISOR_RESTART_BLOCKED_PRODUCTION_ENV", reason=reason, service=service)
        return False
    result = run(["supervisorctl", "restart", service], cwd=APP, timeout=30)
    ok = result.returncode == 0
    audit("SUPERVISOR_RESTART", reason=reason, service=service, ok=ok, output=result.stdout[-1000:])
    return ok
"""

    restart_new = """def supervisor_restart(
    reason: str,
    service: str = SERVICE,
    timeout: int | None = None,
) -> bool:
    if is_production_environment():
        audit("SUPERVISOR_RESTART_BLOCKED_PRODUCTION_ENV", reason=reason, service=service)
        return False
    effective_timeout = max(
        BACKEND_STOPWAITSECS + 5,
        SUPERVISOR_RESTART_TIMEOUT if timeout is None else int(timeout),
    )
    try:
        result = run(
            ["supervisorctl", "restart", service],
            cwd=APP,
            timeout=effective_timeout,
        )
    except subprocess.TimeoutExpired:
        audit(
            "SUPERVISOR_RESTART_TIMEOUT",
            reason=reason,
            service=service,
            timeout=effective_timeout,
        )
        return False
    ok = result.returncode == 0
    audit(
        "SUPERVISOR_RESTART",
        reason=reason,
        service=service,
        timeout=effective_timeout,
        ok=ok,
        output=(result.stdout or "")[-1000:],
    )
    return ok
"""

    test_tail_old = """def test_control_plane_convergence_remains_fail_closed():
    text = body()

    assert '"production_touched": False' in text
    assert "Edarsahub_Produccion" not in text
    assert "MIRROR_ENABLE.unlink" not in text
    assert "MIRROR_STOP.unlink" not in text
"""

    test_tail_new = test_tail_old + """

def _load_watchdog_for_test(tmp_path: Path, monkeypatch):
    import importlib.util

    state_dir = tmp_path / "bootstrap_state"
    monkeypatch.setenv("EDARSAHUB_BOOTSTRAP_STATE", str(state_dir))
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.delenv("EDARSAHUB_BACKEND_UNHEALTHY_THRESHOLD", raising=False)
    monkeypatch.delenv("EDARSAHUB_SUPERVISOR_RESTART_TIMEOUT", raising=False)
    monkeypatch.delenv("EDARSAHUB_BACKEND_RECOVERY_COOLDOWN", raising=False)

    spec = importlib.util.spec_from_file_location(
        f"edarsahub_bootstrap_watchdog_test_{id(tmp_path)}",
        BOOTSTRAP,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_transient_probe_timeout_does_not_restart_running_backend(tmp_path, monkeypatch):
    import subprocess

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    calls: list[list[str]] = []

    def fake_run(args, cwd=None, timeout=60):
        calls.append(list(args))
        if args[0] == "curl":
            return subprocess.CompletedProcess(args, 28, stdout="000")
        if args[:2] == ["supervisorctl", "status"]:
            return subprocess.CompletedProcess(
                args, 0, stdout="backend RUNNING pid 1001, uptime 0:05:00\\n"
            )
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", fake_run)
    outcome = watchdog.maybe_recover_backend()

    assert outcome["state"] == "TRANSIENT_UNHEALTHY"
    assert outcome["restarted"] is False
    assert outcome["consecutive_failures"] == 1
    assert outcome["probe"]["failure_kind"] == "PROBE_TIMEOUT"
    assert not watchdog.BACKEND_RECOVERY_STAMP.exists()
    assert not any(cmd[:2] == ["supervisorctl", "restart"] for cmd in calls)


def test_consecutive_failures_require_threshold_before_restart(tmp_path, monkeypatch):
    import subprocess

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    restart_calls = 0
    restarted_ok = False

    def fake_run(args, cwd=None, timeout=60):
        nonlocal restart_calls, restarted_ok
        if args[0] == "curl":
            if restarted_ok:
                return subprocess.CompletedProcess(args, 0, stdout="401")
            return subprocess.CompletedProcess(args, 28, stdout="000")
        if args[:2] == ["supervisorctl", "status"]:
            return subprocess.CompletedProcess(
                args, 0, stdout="backend RUNNING pid 1002, uptime 0:05:00\\n"
            )
        if args[:2] == ["supervisorctl", "restart"]:
            restart_calls += 1
            restarted_ok = True
            return subprocess.CompletedProcess(args, 0, stdout="backend: started\\n")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", fake_run)

    first = watchdog.maybe_recover_backend()
    second = watchdog.maybe_recover_backend()
    assert first["state"] == "TRANSIENT_UNHEALTHY"
    assert first["consecutive_failures"] == 1
    assert second["state"] == "TRANSIENT_UNHEALTHY"
    assert second["consecutive_failures"] == 2
    assert restart_calls == 0
    assert not watchdog.BACKEND_RECOVERY_STAMP.exists()

    third = watchdog.maybe_recover_backend()
    assert third["state"] == "RESTART_REQUESTED"
    assert third["restarted"] is True
    assert third["restart_confirmed"] is True
    assert third["consecutive_failures"] == 0
    assert restart_calls == 1
    assert watchdog.BACKEND_RECOVERY_STAMP.exists()


def test_healthy_probe_resets_consecutive_failure_counter(tmp_path, monkeypatch):
    import subprocess

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    probe_healthy = False
    restart_calls = 0

    def fake_run(args, cwd=None, timeout=60):
        nonlocal restart_calls
        if args[0] == "curl":
            if probe_healthy:
                return subprocess.CompletedProcess(args, 0, stdout="401")
            return subprocess.CompletedProcess(args, 28, stdout="000")
        if args[:2] == ["supervisorctl", "status"]:
            return subprocess.CompletedProcess(
                args, 0, stdout="backend RUNNING pid 1003, uptime 0:05:00\\n"
            )
        if args[:2] == ["supervisorctl", "restart"]:
            restart_calls += 1
            return subprocess.CompletedProcess(args, 0, stdout="ok\\n")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", fake_run)

    assert watchdog.maybe_recover_backend()["consecutive_failures"] == 1
    assert watchdog.maybe_recover_backend()["consecutive_failures"] == 2

    probe_healthy = True
    healthy = watchdog.maybe_recover_backend()
    assert healthy["state"] == "HEALTHY"
    assert healthy["consecutive_failures"] == 0

    probe_healthy = False
    after_healthy = watchdog.maybe_recover_backend()
    assert after_healthy["state"] == "TRANSIENT_UNHEALTHY"
    assert after_healthy["consecutive_failures"] == 1
    assert restart_calls == 0


def test_persistent_unhealthy_route_recovers_after_threshold(tmp_path, monkeypatch):
    import subprocess

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    restarted = False

    def fake_run(args, cwd=None, timeout=60):
        nonlocal restarted
        if args[0] == "curl":
            code = "401" if restarted else "404"
            return subprocess.CompletedProcess(args, 0, stdout=code)
        if args[:2] == ["supervisorctl", "status"]:
            return subprocess.CompletedProcess(
                args, 0, stdout="backend RUNNING pid 1004, uptime 0:02:00\\n"
            )
        if args[:2] == ["supervisorctl", "restart"]:
            restarted = True
            return subprocess.CompletedProcess(args, 0, stdout="backend: started\\n")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", fake_run)

    assert watchdog.maybe_recover_backend()["restarted"] is False
    assert watchdog.maybe_recover_backend()["restarted"] is False
    third = watchdog.maybe_recover_backend()
    assert third["state"] == "RESTART_REQUESTED"
    assert third["restarted"] is True
    assert third["probe"]["failure_kind"] == "ROUTE_NOT_MOUNTED"


def test_confirmed_stopped_fatal_or_exited_backend_recovers_immediately(tmp_path, monkeypatch):
    import subprocess

    for dead_state in ("STOPPED", "FATAL", "EXITED"):
        sub = tmp_path / dead_state.lower()
        sub.mkdir()
        watchdog = _load_watchdog_for_test(sub, monkeypatch)
        process_up = False
        restart_calls = 0

        def fake_run(args, cwd=None, timeout=60):
            nonlocal process_up, restart_calls
            if args[0] == "curl":
                if process_up:
                    return subprocess.CompletedProcess(args, 0, stdout="401")
                return subprocess.CompletedProcess(args, 7, stdout="000")
            if args[:2] == ["supervisorctl", "status"]:
                if process_up:
                    return subprocess.CompletedProcess(
                        args, 0, stdout="backend RUNNING pid 2001, uptime 0:00:02\\n"
                    )
                return subprocess.CompletedProcess(
                    args, 3, stdout=f"backend {dead_state} Nov 17 04:49 AM\\n"
                )
            if args[:2] == ["supervisorctl", "restart"]:
                restart_calls += 1
                process_up = True
                return subprocess.CompletedProcess(args, 0, stdout="backend: started\\n")
            raise AssertionError(f"unexpected command: {args}")

        monkeypatch.setattr(watchdog, "run", fake_run)
        result = watchdog.maybe_recover_backend()
        assert result["restarted"] is True
        assert result["restart_confirmed"] is True
        assert result["supervisor_state"] == dead_state
        assert restart_calls == 1


def test_cooldown_blocks_running_unhealthy_but_not_confirmed_stopped(tmp_path, monkeypatch):
    import subprocess
    import time

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    watchdog.STATE.mkdir(parents=True, exist_ok=True)
    watchdog.BACKEND_RECOVERY_STAMP.write_text(
        f"{int(time.time()) - 10}\\n", encoding="utf-8"
    )

    sup_state = "RUNNING"
    restarted = False
    restart_calls = 0

    def fake_run(args, cwd=None, timeout=60):
        nonlocal sup_state, restarted, restart_calls
        if args[0] == "curl":
            if restarted:
                return subprocess.CompletedProcess(args, 0, stdout="401")
            return subprocess.CompletedProcess(args, 28, stdout="000")
        if args[:2] == ["supervisorctl", "status"]:
            rc = 0 if sup_state == "RUNNING" else 3
            return subprocess.CompletedProcess(
                args, rc, stdout=f"backend {sup_state} detail\\n"
            )
        if args[:2] == ["supervisorctl", "restart"]:
            restart_calls += 1
            restarted = True
            sup_state = "RUNNING"
            return subprocess.CompletedProcess(args, 0, stdout="backend: started\\n")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", fake_run)

    assert watchdog.maybe_recover_backend()["state"] == "TRANSIENT_UNHEALTHY"
    assert watchdog.maybe_recover_backend()["state"] == "TRANSIENT_UNHEALTHY"
    blocked = watchdog.maybe_recover_backend()
    assert blocked["state"] == "COOLDOWN"
    assert blocked["restarted"] is False
    assert restart_calls == 0

    sup_state = "STOPPED"
    recovered = watchdog.maybe_recover_backend()
    assert recovered["state"] == "RESTART_REQUESTED"
    assert recovered["cooldown_bypassed"] is True
    assert recovered["restarted"] is True
    assert restart_calls == 1


def test_supervisor_restart_timeout_exceeds_stopwaitsecs_and_handles_timeout_expired(
    tmp_path, monkeypatch
):
    import subprocess

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    assert watchdog.BACKEND_STOPWAITSECS == 30
    assert watchdog.SUPERVISOR_RESTART_TIMEOUT == 65
    assert watchdog.SUPERVISOR_RESTART_TIMEOUT > watchdog.BACKEND_STOPWAITSECS

    sup_conf = Path("/etc/supervisor/conf.d/supervisord.conf")
    if sup_conf.is_file():
        backend_block = sup_conf.read_text(encoding="utf-8").split(
            "[program:backend]", 1
        )[1].split("[program:", 1)[0]
        assert "stopwaitsecs=30" in backend_block
        assert watchdog.SUPERVISOR_RESTART_TIMEOUT > 30

    observed_timeouts: list[int] = []

    def timeout_run(args, cwd=None, timeout=60):
        if args[:2] == ["supervisorctl", "restart"]:
            observed_timeouts.append(timeout)
            raise subprocess.TimeoutExpired(cmd=args, timeout=timeout)
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", timeout_run)
    assert watchdog.supervisor_restart("WAKE_ROUTE_UNHEALTHY", "backend") is False
    assert observed_timeouts == [65]


def test_regression_unconfirmed_restart_never_poisons_cooldown_stamp(
    tmp_path, monkeypatch
):
    import subprocess

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    attempt = 0
    sup_state = "RUNNING"
    healthy_after = False

    def fake_run(args, cwd=None, timeout=60):
        nonlocal attempt, sup_state, healthy_after
        if args[0] == "curl":
            if healthy_after:
                return subprocess.CompletedProcess(args, 0, stdout="401")
            return subprocess.CompletedProcess(args, 28, stdout="000")
        if args[:2] == ["supervisorctl", "status"]:
            rc = 0 if sup_state == "RUNNING" else 3
            return subprocess.CompletedProcess(
                args, rc, stdout=f"backend {sup_state} info\\n"
            )
        if args[:2] == ["supervisorctl", "restart"]:
            attempt += 1
            if attempt == 1:
                sup_state = "STOPPED"
                raise subprocess.TimeoutExpired(cmd=args, timeout=timeout)
            sup_state = "RUNNING"
            healthy_after = True
            return subprocess.CompletedProcess(args, 0, stdout="backend: started\\n")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", fake_run)

    assert watchdog.maybe_recover_backend()["restarted"] is False
    assert watchdog.maybe_recover_backend()["restarted"] is False
    failed = watchdog.maybe_recover_backend()
    assert failed["state"] == "RESTART_FAILED"
    assert failed["restarted"] is False
    assert failed["restart_confirmed"] is False
    assert not watchdog.BACKEND_RECOVERY_STAMP.exists()

    recovered = watchdog.maybe_recover_backend()
    assert recovered["state"] == "RESTART_REQUESTED"
    assert recovered["restarted"] is True
    assert recovered["restart_confirmed"] is True
    assert watchdog.BACKEND_RECOVERY_STAMP.exists()
"""

    already_applied_watchdog = (
        const_new in watchdog
        and health_new in watchdog
        and restart_new in watchdog
    )
    if not already_applied_watchdog:
        if watchdog.count(const_old) != 1:
            raise ValueError("PREVIEW_WATCHDOG_CONST_ANCHOR_DRIFT")
        if watchdog.count(health_old) != 1:
            raise ValueError("PREVIEW_WATCHDOG_HEALTH_ANCHOR_DRIFT")
        if watchdog.count(restart_old) != 1:
            raise ValueError("PREVIEW_WATCHDOG_RESTART_ANCHOR_DRIFT")

    already_applied_test = test_tail_new in safety_test
    if not already_applied_test and safety_test.count(test_tail_old) != 1:
        raise ValueError("PREVIEW_WATCHDOG_TEST_ANCHOR_DRIFT")

    return {
        "objective": (
            "Preview Watchdog Transient Recovery: exigir umbral de fallas "
            "consecutivas antes de reiniciar backend por probes transitorios, "
            "distinguir procesos STOPPED/FATAL/EXITED sin bloqueo por cooldown, "
            "elevar timeout de supervisorctl restart a 65s (> stopwaitsecs=30) "
            "y registrar BACKEND_RECOVERY_STAMP solo tras confirmar el reinicio."
        ),
        "actions": [
            {
                "type": "replace_text",
                "path": _PREVIEW_WATCHDOG_SCRIPT,
                "old": const_new if already_applied_watchdog else const_old,
                "new": const_new,
                "expected_count": 1,
                "expected_sha256": hashlib.sha256(
                    watchdog.encode("utf-8")
                ).hexdigest(),
            },
            {
                "type": "replace_text",
                "path": _PREVIEW_WATCHDOG_SCRIPT,
                "old": health_new if already_applied_watchdog else health_old,
                "new": health_new,
                "expected_count": 1,
            },
            {
                "type": "replace_text",
                "path": _PREVIEW_WATCHDOG_SCRIPT,
                "old": restart_new if already_applied_watchdog else restart_old,
                "new": restart_new,
                "expected_count": 1,
            },
            {
                "type": "replace_text",
                "path": _PREVIEW_WATCHDOG_TEST,
                "old": test_tail_new if already_applied_test else test_tail_old,
                "new": test_tail_new,
                "expected_count": 1,
                "expected_sha256": hashlib.sha256(
                    safety_test.encode("utf-8")
                ).hexdigest(),
            },
        ],
        "checks": [
            {
                "type": "py_compile",
                "paths": [
                    _PREVIEW_WATCHDOG_SCRIPT,
                    _PREVIEW_WATCHDOG_TEST,
                ],
            },
            {
                "type": "pytest",
                "paths": [
                    _PREVIEW_WATCHDOG_TEST,
                ],
            },
            {
                "type": "git_diff_check",
            },
        ],
    }


register_capability(
    RepairCapability(
        code=_PREVIEW_WATCHDOG_CAPABILITY,
        incident_ids=(_PREVIEW_WATCHDOG_INCIDENT,),
        required_paths=(
            _PREVIEW_WATCHDOG_SCRIPT,
            _PREVIEW_WATCHDOG_TEST,
        ),
        builder=_preview_watchdog_transient_recovery_recipe,
    )
)
