"""Schemas del dominio Economía."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class SerieEconomicaResponse(BaseModel):
    id: int
    codigo_canonico: str
    nombre: str
    unidad_medida: Optional[str] = None
    frecuencia: Optional[str] = None
    activo: bool


class ValorEconomicoResponse(BaseModel):
    serie_id: int
    periodo: date
    valor: float
    version_dato: int
    es_revision: bool
    preliminar: bool
    estimado: bool


class ContextoEconomicoResponse(BaseModel):
    id: int
    pais_id: Optional[str] = None
    empresa_id: Optional[int] = None
    unidad_negocio_id: Optional[str] = None
    moneda_id: Optional[int] = None
    principal: bool
    activo: bool


class SerieEconomicaQuery(BaseModel):
    desde: Optional[date] = None
    hasta: Optional[date] = None
    limite: int = Field(default=500, ge=1, le=5000)
