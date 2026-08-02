from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CommercialMetric(str, Enum):
    VENTAS = "ventas"
    PAX = "pax"
    CHEQUES = "cheques"


class DrilldownLevel(str, Enum):
    BUSINESS_UNIT = "business_unit"
    YEAR = "year"
    MONTH = "month"
    OPERATIONAL_DAY = "operational_day"


class HistoricalPeriod(BaseModel):
    year: int = Field(..., ge=1900, le=9999)
    months: list[int] = Field(..., min_length=1)

    @field_validator("months")
    @classmethod
    def validate_months(cls, values: list[int]) -> list[int]:
        normalized = sorted({int(value) for value in values})

        if any(value < 1 or value > 12 for value in normalized):
            raise ValueError("Los meses deben estar entre 1 y 12")

        return normalized


class DrilldownScope(BaseModel):
    mode: str = "historical_periods"
    periods: list[HistoricalPeriod] = Field(..., min_length=1)


class CommercialDrilldownRequest(BaseModel):
    metric: CommercialMetric
    level: DrilldownLevel
    scope: DrilldownScope

    business_unit_pk: Optional[str] = None
    business_unit_code: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=9999)
    month: Optional[int] = Field(None, ge=1, le=12)
    operational_date: Optional[str] = None


class TemporalResolveRequest(BaseModel):
    selection: dict[str, Any]
    unidad_negocio_id: str | None = None
