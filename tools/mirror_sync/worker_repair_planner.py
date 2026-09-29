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

    if publisher.count(old_imports) != 1:
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

    if publisher.count(old_forbidden) != 1:
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
                "old": old_imports,
                "new": new_imports,
                "expected_count": 1,
                "expected_sha256": publisher_sha,
            },
            {
                "type": "replace_text",
                "path": _CANONICAL_INGRESS_PUBLISHER,
                "old": old_forbidden,
                "new": new_forbidden,
                "expected_count": 1,
            },
            {
                "type": "replace_text",
                "path": _CANONICAL_INGRESS_PUBLISHER,
                "old": main_anchor,
                "new": (
                    submit_block
                    + "\n\n"
                    + main_anchor
                ),
                "expected_count": 1,
            },
            {
                "type": "write_file",
                "path": _CANONICAL_INGRESS_TEST,
                "content": ingress_test,
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
