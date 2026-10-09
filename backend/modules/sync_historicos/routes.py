"""API nativa de Sincronizacion Historica de Tablas."""
from __future__ import annotations

import os
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.rbac.middleware import require_permission, require_explicit_permission
from modules.sync_historicos.catalog_service import (
    get_catalog_payload,
    planner_inputs,
)
from modules.sync_historicos.controls import (
    get_parent_status,
    prepare_resume,
    request_cancel,
    request_pause,
)
from modules.sync_historicos.job_repository import (
    HistoricalJobConflict,
    persist_plan,
)
from modules.sync_historicos.planner import (
    HistoricalPlanError,
    build_historical_plan,
)
from modules.sync_historicos.worker_submit import (
    HistoricalWorkerSubmitError,
    submit_parent_to_worker,
)


router = APIRouter(
    prefix="/api/sync-historical",
    tags=["Sincronizacion Historica"],
)


class HistoricalSelection(BaseModel):
    systems: List[str] = Field(..., min_length=1)
    units: List[str] = Field(..., min_length=1)
    capabilities: List[str] = Field(..., min_length=1)
    date_start: date
    date_end: date


class HistoricalCreateRequest(HistoricalSelection):
    reason: str = Field(..., min_length=10, max_length=1000)
    dry_run: bool = False


class ResumeRequest(BaseModel):
    retry_failed: bool = False


def _plan(body: HistoricalSelection):
    registry, unit_contexts = planner_inputs()
    return build_historical_plan(
        start=body.date_start,
        end=body.date_end,
        selected_systems=body.systems,
        selected_units=body.units,
        selected_capabilities=body.capabilities,
        registry=registry,
        unit_contexts=unit_contexts,
    )


def _max_atomic_units() -> int:
    try:
        return max(
            1,
            int(os.environ.get(
                "SYNC_HISTORICAL_MAX_ATOMIC_UNITS",
                "5000",
            )),
        )
    except ValueError:
        return 5000


@router.get("/catalog")
def catalog(
    current_user: dict = Depends(
        require_permission("SCHEDULER_VER")
    ),
):
    return {"success": True, **get_catalog_payload()}


@router.post("/preflight")
def preflight(
    body: HistoricalSelection,
    current_user: dict = Depends(
        require_permission("SCHEDULER_VER")
    ),
):
    try:
        plan = _plan(body)
    except HistoricalPlanError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    total = len(plan.atomic_units)
    maximum = _max_atomic_units()
    return {
        "success": True,
        "ready": total <= maximum,
        "total_atomic_units": total,
        "max_atomic_units": maximum,
        "correlation_id": plan.correlation_id,
        "date_start": plan.start,
        "date_end": plan.end,
        "systems": list(plan.selected_systems),
        "units": list(plan.selected_units),
        "capabilities": list(plan.selected_capabilities),
        "preview": [
            unit.to_dict()
            for unit in plan.atomic_units[:200]
        ],
        "preview_truncated": total > 200,
        "warnings": (
            []
            if total <= maximum
            else ["ATOMIC_UNIT_LIMIT_EXCEEDED"]
        ),
    }


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
def create_job(
    body: HistoricalCreateRequest,
    current_user: dict = Depends(
        require_explicit_permission("SCHEDULER_ADMIN")
    ),
):
    try:
        plan = _plan(body)
        if len(plan.atomic_units) > _max_atomic_units():
            raise HistoricalPlanError(
                "ATOMIC_UNIT_LIMIT_EXCEEDED"
            )
        persisted = persist_plan(
            plan,
            requested_by=current_user.get("email", "unknown"),
            reason=body.reason,
            dry_run=body.dry_run,
        )
        worker = submit_parent_to_worker(
            persisted["parent_sync_control_id"],
            requester_email=current_user.get("email", ""),
        )
    except HistoricalJobConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except HistoricalPlanError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HistoricalWorkerSubmitError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return {
        "success": True,
        **persisted,
        "worker": worker,
    }


@router.get("/jobs/{parent_id}")
def job_status(
    parent_id: int,
    current_user: dict = Depends(
        require_permission("SCHEDULER_VER")
    ),
):
    result = get_parent_status(parent_id)
    if not result:
        raise HTTPException(status_code=404, detail="PARENT_NOT_FOUND")
    return {"success": True, **result}


@router.post("/jobs/{parent_id}/pause", status_code=202)
def pause_job(
    parent_id: int,
    current_user: dict = Depends(
        require_explicit_permission("SCHEDULER_ADMIN")
    ),
):
    try:
        result = request_pause(parent_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"success": True, **result}


@router.post("/jobs/{parent_id}/cancel", status_code=202)
def cancel_job(
    parent_id: int,
    current_user: dict = Depends(
        require_explicit_permission("SCHEDULER_ADMIN")
    ),
):
    try:
        result = request_cancel(parent_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"success": True, **result}


@router.post("/jobs/{parent_id}/resume", status_code=202)
def resume_job(
    parent_id: int,
    body: ResumeRequest,
    current_user: dict = Depends(
        require_explicit_permission("SCHEDULER_ADMIN")
    ),
):
    try:
        control = prepare_resume(
            parent_id,
            retry_failed=body.retry_failed,
        )
        worker = submit_parent_to_worker(
            parent_id,
            requester_email=current_user.get("email", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except HistoricalWorkerSubmitError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {
        "success": True,
        **control,
        "worker": worker,
    }
