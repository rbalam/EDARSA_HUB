"""Standalone always-on scheduler service for EDARSAHUB Production.

Required runtime:
    EDARSA_ENV=PRODUCTION
    EDARSA_RUNTIME_ROLE=PRODUCTION_SCHEDULER
    EDARSA_RUNTIME_ROLE_REQUIRED=1
    SCHEDULER_ENABLED=true
"""

import logging
from pathlib import Path

from dotenv import load_dotenv

# Cargar el mismo archivo de entorno que usa backend/server.py.
# load_dotenv no sobreescribe variables inyectadas por el runtime, por lo que
# EDARSA_RUNTIME_ROLE y EDARSA_ENV siguen siendo autoridad de despliegue.
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI

from core.mongo_stub import get_stub_database
from core.scheduler import get_scheduler_manager, start_scheduler, stop_scheduler
from modules.scheduler_runtime.policy import (
    require_standalone_production_scheduler,
    runtime_policy_snapshot,
)


logger = logging.getLogger(__name__)
app = FastAPI(title="EDARSAHUB Production Scheduler")


@app.on_event("startup")
async def startup_scheduler_service():
    policy = require_standalone_production_scheduler()
    manager = await start_scheduler(get_stub_database())
    status = manager.get_status()

    if not status.get("running"):
        raise RuntimeError("PRODUCTION_SCHEDULER_FAILED_TO_START")

    jobs = status.get("jobs") or []
    logger.warning(
        "Production scheduler service started environment=%s role=%s jobs=%s",
        policy.get("environment"),
        policy.get("role"),
        len(jobs),
    )


@app.on_event("shutdown")
async def shutdown_scheduler_service():
    await stop_scheduler()
    logger.info("Production scheduler service stopped cleanly")


@app.get("/api/health")
async def scheduler_health():
    policy = runtime_policy_snapshot()
    status = get_scheduler_manager(get_stub_database()).get_status()

    return {
        "status": "ok" if status.get("running") else "degraded",
        "service": "edarsahub-production-scheduler",
        "environment": policy.get("environment"),
        "runtime_role": policy.get("role"),
        "role_explicit": policy.get("role_explicit"),
        "scheduler_enabled": policy.get("scheduler_enabled"),
        "running": status.get("running", False),
        "jobs_count": len(status.get("jobs") or []),
        "jobs": status.get("jobs", []),
    }
