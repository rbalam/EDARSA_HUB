from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, Optional

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
    unidad_negocio_ids: list[str] | None = None

    @field_validator("unidad_negocio_id")
    @classmethod
    def normalize_single_unit(
        cls,
        value: str | None,
    ) -> str | None:
        normalized = str(value or "").strip()
        return normalized or None

    @field_validator("unidad_negocio_ids")
    @classmethod
    def normalize_multiple_units(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None

        normalized = sorted({
            str(value or "").strip()
            for value in values
            if str(value or "").strip()
        })

        if not normalized:
            raise ValueError(
                "unidad_negocio_ids debe contener "
                "al menos una unidad"
            )

        return normalized

    def requested_unit_codes(self) -> list[str] | None:
        single = self.unidad_negocio_id
        multiple = self.unidad_negocio_ids

        if single and multiple:
            if multiple != [single]:
                raise ValueError(
                    "unidad_negocio_id y unidad_negocio_ids "
                    "definen alcances diferentes"
                )

            return [single]

        if multiple is not None:
            return multiple

        if single:
            return [single]

        return None

    def resolve_unit_scope(
        self,
        allowed_codes: Iterable[str],
    ) -> list[str]:
        allowed = sorted({
            str(value or "").strip()
            for value in allowed_codes
            if str(value or "").strip()
        })

        if not allowed:
            raise PermissionError(
                "El usuario no tiene unidades permitidas"
            )

        requested = self.requested_unit_codes()

        if requested is None:
            return allowed

        unauthorized = sorted(
            set(requested) - set(allowed)
        )

        if unauthorized:
            raise PermissionError(
                "No tiene acceso a las unidades: "
                + ", ".join(unauthorized)
            )

        return sorted(set(requested))
