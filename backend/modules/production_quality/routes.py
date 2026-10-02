"""FastAPI routes for Production Quality / Foto Finish."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from core.rbac.middleware import require_explicit_permission_dual

from .schemas import (
    DeviceCalibrationCreate,
    EvidenceCreate,
    MeasurementCreate,
    QualityActionCreate,
    QualityDecisionCreate,
)
from .service import (
    ProductionQualityAccessDenied,
    ProductionQualityNotFound,
    ProductionQualityService,
)


router = APIRouter(
    prefix="/production-quality",
    tags=["Production Quality"],
)


CAN_VIEW_EXECUTION = require_explicit_permission_dual(
    "production_quality.execution_VER"
)
CAN_CAPTURE = require_explicit_permission_dual(
    "production_quality.execution_GESTIONAR"
)
CAN_CAPTURE_EVIDENCE = require_explicit_permission_dual(
    "production_quality.evidence_CREAR"
)
CAN_VIEW_STANDARDS = require_explicit_permission_dual(
    "production_quality.standards_VER"
)
CAN_DECIDE = require_explicit_permission_dual(
    "production_quality.decisions_AUTORIZAR"
)
CAN_REWORK = require_explicit_permission_dual(
    "production_quality.rework_GESTIONAR"
)
CAN_OVERRIDE = require_explicit_permission_dual(
    "production_quality.override_AUTORIZAR"
)
CAN_VIEW_DEVICES = require_explicit_permission_dual(
    "production_quality.devices_VER"
)
CAN_CONFIGURE_DEVICES = require_explicit_permission_dual(
    "production_quality.devices_CONFIGURAR"
)


def get_service() -> ProductionQualityService:
    return ProductionQualityService()


def _payload_dict(payload):
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    return payload.dict()


def _translate_error(exc: Exception):
    if isinstance(exc, ProductionQualityAccessDenied):
        raise HTTPException(
            status_code=403,
            detail={
                "code": str(exc),
                "message": "Acceso fuera del alcance RBAC canónico.",
            },
        ) from exc

    if isinstance(exc, ProductionQualityNotFound):
        raise HTTPException(
            status_code=404,
            detail={
                "code": str(exc),
                "message": "Entidad Production Quality no encontrada.",
            },
        ) from exc

    raise exc


@router.get("/items")
def list_items(
    empresa_id: int = Query(gt=0),
    unidad_negocio_id: UUID = Query(),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(CAN_VIEW_EXECUTION),
    service: ProductionQualityService = Depends(get_service),
):
    try:
        return {
            "items": service.list_items(
                current_user,
                empresa_id,
                unidad_negocio_id,
                limit,
                offset,
            ),
            "empresa_id": empresa_id,
            "unidad_negocio_id": str(unidad_negocio_id),
        }
    except Exception as exc:
        _translate_error(exc)


@router.get("/standards")
def list_standards(
    empresa_id: int = Query(gt=0),
    unidad_negocio_id: UUID = Query(),
    current_user: dict = Depends(CAN_VIEW_STANDARDS),
    service: ProductionQualityService = Depends(get_service),
):
    try:
        return {
            "items": service.list_standards(
                current_user,
                empresa_id,
                unidad_negocio_id,
            )
        }
    except Exception as exc:
        _translate_error(exc)


@router.get("/devices")
def list_devices(
    empresa_id: int = Query(gt=0),
    unidad_negocio_id: UUID = Query(),
    current_user: dict = Depends(CAN_VIEW_DEVICES),
    service: ProductionQualityService = Depends(get_service),
):
    try:
        return {
            "items": service.list_devices(
                current_user,
                empresa_id,
                unidad_negocio_id,
            )
        }
    except Exception as exc:
        _translate_error(exc)


@router.post("/measurements")
def create_measurement(
    payload: MeasurementCreate,
    current_user: dict = Depends(CAN_CAPTURE),
    service: ProductionQualityService = Depends(get_service),
):
    try:
        return service.create_measurement(
            current_user,
            _payload_dict(payload),
        )
    except Exception as exc:
        _translate_error(exc)


@router.post("/evidence")
def create_evidence(
    payload: EvidenceCreate,
    current_user: dict = Depends(CAN_CAPTURE_EVIDENCE),
    service: ProductionQualityService = Depends(get_service),
):
    try:
        return service.create_evidence(
            current_user,
            _payload_dict(payload),
        )
    except Exception as exc:
        _translate_error(exc)


@router.post("/decisions")
def create_decision(
    payload: QualityDecisionCreate,
    current_user: dict = Depends(CAN_DECIDE),
    service: ProductionQualityService = Depends(get_service),
):
    try:
        return service.create_decision(
            current_user,
            _payload_dict(payload),
        )
    except Exception as exc:
        _translate_error(exc)


@router.post("/actions/rework")
def create_rework(
    payload: QualityActionCreate,
    current_user: dict = Depends(CAN_REWORK),
    service: ProductionQualityService = Depends(get_service),
):
    if payload.action_type.value != "REWORK":
        raise HTTPException(
            status_code=422,
            detail="ACTION_TYPE_MUST_BE_REWORK",
        )

    try:
        return service.create_action(
            current_user,
            _payload_dict(payload),
        )
    except Exception as exc:
        _translate_error(exc)


@router.post("/actions/override")
def create_override(
    payload: QualityActionCreate,
    current_user: dict = Depends(CAN_OVERRIDE),
    service: ProductionQualityService = Depends(get_service),
):
    if payload.action_type.value != "OVERRIDE":
        raise HTTPException(
            status_code=422,
            detail="ACTION_TYPE_MUST_BE_OVERRIDE",
        )

    try:
        return service.create_action(
            current_user,
            _payload_dict(payload),
        )
    except Exception as exc:
        _translate_error(exc)


@router.post("/devices/calibrations")
def create_device_calibration(
    payload: DeviceCalibrationCreate,
    current_user: dict = Depends(CAN_CONFIGURE_DEVICES),
    service: ProductionQualityService = Depends(get_service),
):
    try:
        return service.create_calibration(
            current_user,
            _payload_dict(payload),
        )
    except Exception as exc:
        _translate_error(exc)
