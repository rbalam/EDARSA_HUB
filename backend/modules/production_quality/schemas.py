"""Schemas for Production Quality / Foto Finish."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QualityDecisionCode(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class QualityActionType(str, Enum):
    REWORK = "REWORK"
    OVERRIDE = "OVERRIDE"
    REJECT = "REJECT"
    RELEASE = "RELEASE"


class TenantScope(BaseModel):
    empresa_id: int = Field(gt=0)
    unidad_negocio_id: UUID


class MeasurementCreate(TenantScope):
    production_item_id: UUID
    production_station_id: Optional[UUID] = None
    quality_standard_version_id: Optional[UUID] = None
    device_id: Optional[UUID] = None
    measurement_type: str = Field(min_length=1, max_length=30)
    numeric_value: Decimal
    unit_code: str = Field(min_length=1, max_length=30)
    captured_at_utc: Optional[datetime] = None
    source: str = Field(default="EDARSAHUB", min_length=1, max_length=40)
    idempotency_key: str = Field(min_length=8, max_length=160)


class EvidenceCreate(TenantScope):
    production_item_id: UUID
    production_station_id: Optional[UUID] = None
    device_id: Optional[UUID] = None
    evidence_type: str = Field(min_length=1, max_length=30)
    storage_path: str = Field(min_length=1, max_length=500)
    content_type: str = Field(min_length=1, max_length=120)
    byte_size: Optional[int] = Field(default=None, ge=0)
    content_hash: str = Field(min_length=16, max_length=128)
    captured_at_utc: Optional[datetime] = None
    idempotency_key: str = Field(min_length=8, max_length=160)


class QualityDecisionCreate(TenantScope):
    production_item_id: UUID
    quality_standard_version_id: Optional[UUID] = None
    decision: QualityDecisionCode
    reason_code: Optional[str] = Field(default=None, max_length=60)
    reason_text: Optional[str] = Field(default=None, max_length=1000)
    previous_decision_id: Optional[UUID] = None
    idempotency_key: str = Field(min_length=8, max_length=160)


class QualityActionCreate(TenantScope):
    production_item_id: UUID
    quality_decision_id: UUID
    evidence_id: Optional[UUID] = None
    action_type: QualityActionType
    reason_code: Optional[str] = Field(default=None, max_length=60)
    reason_text: Optional[str] = Field(default=None, max_length=1000)
    idempotency_key: str = Field(min_length=8, max_length=160)


class DeviceCalibrationCreate(TenantScope):
    device_id: UUID
    evidence_id: Optional[UUID] = None
    calibration_type: str = Field(min_length=1, max_length=40)
    calibration_value: Optional[Decimal] = None
    unit_code: Optional[str] = Field(default=None, max_length=30)
    calibrated_at_utc: Optional[datetime] = None
    valid_until_utc: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=1000)
