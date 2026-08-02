"""Contrato dinamico de periodos para los tableros comerciales.

Conecta las reglas puras de :mod:`periodos` con la vista canonica de KPIs. El
router es solo lectura, respeta RBAC y no consulta fuentes LIVE ni MongoDB.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta
from statistics import mean
from typing import Any, Iterable, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from core.security import get_current_user_dual_dependency
from core.unidades_service import UnidadesService
from core.comercial_temporal_availability import build_temporal_availability

from .periodos import (
    ModoPeriodo,
    NivelConfianza,
    calcular_variacion,
    contar_unidades_comparables,
    proyectar_mes_por_dia_semana,
    resolver_etiquetas,
    resolver_periodos_comparables,
)
from .repository_readonly import _execute_readonly_query
from .routes import (
    _require_unidades_permitidas,
    _unidades_runtime_where_sql,
    get_unidades_permitidas_v2,
    serialize_response,
)


router = APIRouter(prefix="/comercial", tags=["Comercial V2 - Periodos"])

logger = logging.getLogger(__name__)


def _fecha_sql(value: date) -> str:
    return value.isoformat()


def _normalizar_unidad_solicitada(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    return UnidadesService.resolver_codigo(raw) or raw


def _scope_unidades(
    unidades_permitidas: Iterable[str],
    unidad_solicitada: Optional[str],
) -> list[str]:
    permitidas = sorted({str(value).strip() for value in unidades_permitidas if value})
    solicitada = _normalizar_unidad_solicitada(unidad_solicitada)
    if not solicitada:
        return permitidas

    permitidas_resueltas = {
        UnidadesService.resolver_codigo(value) or value
        for value in permitidas
    }
    if solicitada not in permitidas_resueltas:
        raise HTTPException(
            status_code=403,
            detail=f"No tiene acceso a la unidad {solicitada}",
        )
    return [solicitada]


def _consultar_agregado(
    *,
    inicio: date,
    fin: date,
    unidades: list[str],
) -> dict[str, Any]:
    where_unidades = _unidades_runtime_where_sql(unidades)
    query = f"""
    SELECT
        SUM(ISNULL(ventas_total, 0)) AS ventas,
        SUM(ISNULL(pax_total, 0)) AS pax,
        SUM(ISNULL(tickets_total, 0)) AS cheques,
        COUNT(DISTINCT fecha_operacion) AS dias,
        COUNT(DISTINCT unidad_negocio_id) AS unidades_con_datos
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE {where_unidades}
      AND fecha_operacion >= '{_fecha_sql(inicio)}'
      AND fecha_operacion < '{_fecha_sql(fin + timedelta(days=1))}'
    """
    rows = _execute_readonly_query(query)
    row = rows[0] if rows else {}
    ventas = float(row.get("ventas") or 0)
    pax = int(row.get("pax") or 0)
    cheques = int(row.get("cheques") or 0)
    return {
        "ventas": ventas,
        "pax": pax,
        "cheques": cheques,
        "pax_promedio": round(ventas / pax, 2) if pax > 0 else 0.0,
        "cheque_promedio": round(ventas / cheques, 2) if cheques > 0 else 0.0,
        "dias": int(row.get("dias") or 0),
        "unidades_con_datos": int(row.get("unidades_con_datos") or 0),
    }


def _consultar_unidades_con_datos(
    *,
    inicio: date,
    fin: date,
    unidades: list[str],
) -> list[str]:
    where_unidades = _unidades_runtime_where_sql(unidades)
    query = f"""
    SELECT DISTINCT unidad_negocio_id
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE {where_unidades}
      AND fecha_operacion >= '{_fecha_sql(inicio)}'
      AND fecha_operacion < '{_fecha_sql(fin + timedelta(days=1))}'
      AND (
          ISNULL(ventas_total, 0) <> 0
          OR ISNULL(pax_total, 0) <> 0
          OR ISNULL(tickets_total, 0) <> 0
      )
    """
    rows = _execute_readonly_query(query)
    return [
        str(row.get("unidad_negocio_id"))
        for row in rows
        if row.get("unidad_negocio_id") not in (None, "")
    ]


def _consultar_ventas_diarias(
    *,
    inicio: date,
    fin: date,
    unidades: list[str],
) -> list[dict[str, Any]]:
    if inicio > fin:
        return []
    where_unidades = _unidades_runtime_where_sql(unidades)
    query = f"""
    SELECT
        fecha_operacion,
        SUM(ISNULL(ventas_total, 0)) AS ventas_total
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE {where_unidades}
      AND fecha_operacion >= '{_fecha_sql(inicio)}'
      AND fecha_operacion < '{_fecha_sql(fin + timedelta(days=1))}'
    GROUP BY fecha_operacion
    ORDER BY fecha_operacion ASC
    """
    return [
        {
            "fecha_operacion": row.get("fecha_operacion"),
            "ventas_total": float(row.get("ventas_total") or 0),
            "completo": True,
        }
        for row in _execute_readonly_query(query)
    ]


def _proyectar_dia(
    *,
    fecha_actual: date,
    ventas_actuales: float,
    unidades: list[str],
) -> dict[str, Any]:
    historico = _consultar_ventas_diarias(
        inicio=fecha_actual - timedelta(days=35),
        fin=fecha_actual - timedelta(days=1),
        unidades=unidades,
    )
    equivalentes = [
        row
        for row in reversed(historico)
        if date.fromisoformat(str(row["fecha_operacion"])[:10]).weekday()
        == fecha_actual.weekday()
    ][:3]
    muestras = [float(row["ventas_total"]) for row in equivalentes]
    promedio = round(mean(muestras), 2) if muestras else 0.0
    proyectado = round(max(float(ventas_actuales or 0), promedio), 2)
    if len(muestras) >= 3:
        confianza = NivelConfianza.ALTA
    elif len(muestras) >= 2:
        confianza = NivelConfianza.MEDIA
    elif muestras:
        confianza = NivelConfianza.BAJA
    else:
        confianza = NivelConfianza.SIN_BASE

    return {
        "ventas_reales": round(float(ventas_actuales or 0), 2),
        "proyeccion_total": proyectado,
        "metodo": (
            "PROMEDIO_ULTIMOS_3_DIAS_EQUIVALENTES"
            if muestras
            else "SIN_BASE_HISTORICA"
        ),
        "nivel_confianza": confianza.value,
        "muestras": len(muestras),
        "fechas_referencia": [
            str(row["fecha_operacion"])[:10] for row in equivalentes
        ],
        "promedio_dias_equivalentes": promedio,
    }


def _rango_to_dict(rango: Any) -> dict[str, str]:
    return {
        "fecha_inicio": rango.inicio.isoformat(),
        "fecha_fin": rango.fin.isoformat(),
    }


def _resumen_unidades_comparables(
    unidades_actuales: Iterable[str],
    unidades_inmediatas: Iterable[str],
    unidades_anuales: Iterable[str],
) -> dict[str, Any]:
    resumen = contar_unidades_comparables(unidades_actuales, unidades_anuales)
    actuales = {str(value) for value in unidades_actuales if value not in (None, "")}
    inmediatas = {str(value) for value in unidades_inmediatas if value not in (None, "")}
    resumen.update(
        {
            "periodo_anterior": len(inmediatas),
            "diferencia_periodo_anterior": len(actuales) - len(inmediatas),
            "unidades_periodo_anterior": sorted(inmediatas),
        }
    )
    return resumen


def _consultar_periodos_disponibles(
    *,
    unidades: list[str],
) -> dict[str, Any]:
    """Compatibilidad del router con el servicio temporal compartido."""
    return build_temporal_availability(
        units=unidades,
        readonly_query=_execute_readonly_query,
        units_where_builder=_unidades_runtime_where_sql,
    )


@router.get("/periodos/disponibles")
async def obtener_periodos_disponibles(
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_dual_dependency()),
):
    """Cobertura temporal canónica disponible para filtros de tableros."""

    try:
        permitidas = _require_unidades_permitidas(
            await get_unidades_permitidas_v2(current_user)
        )
        unidades = _scope_unidades(
            permitidas,
            unidad_negocio_pk,
        )

        disponibilidad = _consultar_periodos_disponibles(
            unidades=unidades,
        )

        response = {
            **disponibilidad,
            "trazabilidad": {
                "fuente": "vw_Comercial_KPIs_Diarios_v2_Runtime",
                "campo_temporal": "fecha_operacion",
                "sql_vivo": False,
                "mongodb": False,
                "hardcode": False,
                "unidades_rbac": unidades,
            },
        }

        return {
            "success": True,
            "data": serialize_response(response),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "[PERIODOS-DISPONIBLES] Error consultando cobertura temporal: %s",
            exc,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible consultar la disponibilidad "
                "temporal canónica"
            ),
        ) from exc


class PeriodoHistoricoSeleccionado(BaseModel):
    anio: int = Field(..., ge=1900, le=9999)
    meses: list[int] = Field(..., min_length=1)

    @field_validator("meses")
    @classmethod
    def validar_meses(cls, values: list[int]) -> list[int]:
        normalized = sorted({int(value) for value in values})
        if not normalized or any(value < 1 or value > 12 for value in normalized):
            raise ValueError("Los meses deben estar entre 1 y 12")
        return normalized


class PeriodosHistoricosRequest(BaseModel):
    periodos: list[PeriodoHistoricoSeleccionado] = Field(
        ...,
        min_length=1,
    )
    unidad_negocio_pk: Optional[str] = None


def _normalizar_periodos_historicos(
    periodos: list[PeriodoHistoricoSeleccionado],
) -> list[dict[str, Any]]:
    grouped: dict[int, set[int]] = {}

    for periodo in periodos:
        grouped.setdefault(periodo.anio, set()).update(periodo.meses)

    return [
        {
            "anio": anio,
            "meses": sorted(grouped[anio]),
        }
        for anio in sorted(grouped, reverse=True)
    ]


def _periodos_where_sql(
    periodos: list[dict[str, Any]],
    alias: str = "k",
) -> str:
    clauses = []

    for periodo in periodos:
        anio = int(periodo["anio"])
        meses = ",".join(str(int(value)) for value in periodo["meses"])
        clauses.append(
            f"(YEAR({alias}.fecha_operacion) = {anio} "
            f"AND MONTH({alias}.fecha_operacion) IN ({meses}))"
        )

    if not clauses:
        return "1 = 0"

    return "(" + " OR ".join(clauses) + ")"


def _consultar_periodos_agregados(
    *,
    periodos: list[dict[str, Any]],
    unidades: list[str],
) -> dict[str, Any]:
    """Agrega exclusivamente los meses/años solicitados.

    No usa rangos continuos para selecciones discontinuas.
    No incorpora el overlay del día operativo vigente.
    """
    where_unidades = _unidades_runtime_where_sql(unidades)
    where_periodos = _periodos_where_sql(periodos, "k")

    query_totales = f"""
    SELECT
        COUNT(DISTINCT k.fecha_operacion) AS dias,
        COUNT(DISTINCT k.unidad_negocio_id) AS unidades_con_datos,
        MIN(k.fecha_operacion) AS fecha_min,
        MAX(k.fecha_operacion) AS fecha_max,
        SUM(ISNULL(k.ventas_total, 0)) AS ventas_total,
        SUM(ISNULL(k.propinas_total, 0)) AS propinas_total,
        SUM(ISNULL(k.tickets_total, 0)) AS tickets_total,
        SUM(ISNULL(k.pax_total, 0)) AS pax_total
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime AS k
    WHERE {where_unidades}
      AND {where_periodos}
    """

    query_unidades = f"""
    SELECT
        CONVERT(varchar(36), k.unidad_negocio_pk) AS unidad_negocio_pk,
        MAX(k.unidad_negocio_id) AS unidad_negocio_codigo,
        MAX(k.unidad_negocio_nombre) AS unidad_negocio_nombre,
        MAX(k.sistema_origen) AS sistema_origen,
        COUNT(DISTINCT k.fecha_operacion) AS dias,
        MIN(k.fecha_operacion) AS fecha_min,
        MAX(k.fecha_operacion) AS fecha_max,
        SUM(ISNULL(k.ventas_total, 0)) AS ventas_total,
        SUM(ISNULL(k.propinas_total, 0)) AS propinas_total,
        SUM(ISNULL(k.tickets_total, 0)) AS tickets_total,
        SUM(ISNULL(k.pax_total, 0)) AS pax_total
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime AS k
    WHERE {where_unidades}
      AND {where_periodos}
    GROUP BY k.unidad_negocio_pk
    ORDER BY ventas_total DESC
    """

    total_rows = _execute_readonly_query(query_totales)
    unit_rows = _execute_readonly_query(query_unidades)

    totals = total_rows[0] if total_rows else {}

    def enrich(row: dict[str, Any]) -> dict[str, Any]:
        ventas = float(row.get("ventas_total") or 0)
        tickets = int(row.get("tickets_total") or 0)
        pax = int(row.get("pax_total") or 0)

        return {
            **row,
            "ventas_total": ventas,
            "propinas_total": float(row.get("propinas_total") or 0),
            "tickets_total": tickets,
            "pax_total": pax,
            "cheque_promedio": round(ventas / tickets, 2) if tickets else 0.0,
            "ticket_promedio": round(ventas / tickets, 2) if tickets else 0.0,
            "pax_promedio": round(ventas / pax, 2) if pax else 0.0,
        }

    return {
        "totales": enrich(totals),
        "unidades": [enrich(row) for row in unit_rows],
    }


@router.post("/periodos/agregado")
async def obtener_periodos_agregados(
    payload: PeriodosHistoricosRequest,
    current_user: dict = Depends(get_current_user_dual_dependency()),
):
    """KPIs de periodos históricos explícitos y potencialmente discontinuos."""

    try:
        permitidas = _require_unidades_permitidas(
            await get_unidades_permitidas_v2(current_user)
        )
        unidades = _scope_unidades(
            permitidas,
            payload.unidad_negocio_pk,
        )
        periodos = _normalizar_periodos_historicos(payload.periodos)

        agregado = _consultar_periodos_agregados(
            periodos=periodos,
            unidades=unidades,
        )

        response = {
            **agregado,
            "modo_periodo": "historical_periods",
            "periodos_seleccionados": periodos,
            "overlay_dia_actual_incluido": False,
            "trazabilidad": {
                "fuente": "vw_Comercial_KPIs_Diarios_v2_Runtime",
                "campo_temporal": "fecha_operacion",
                "sql_vivo": False,
                "mongodb": False,
                "agregacion_frontend": False,
                "unidades_rbac": unidades,
            },
        }

        return {
            "success": True,
            "data": serialize_response(response),
        }

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No fue posible agregar los periodos históricos",
        ) from exc


@router.get("/periodos/contrato")
async def obtener_contrato_periodo(
    modo: ModoPeriodo = Query(..., description="ventas_dia o mensual"),
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    fecha_corte_datos: Optional[date] = Query(None),
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_dual_dependency()),
):
    """Devuelve comparativos, etiquetas y proyeccion con una sola semantica."""

    try:
        permitidas = _require_unidades_permitidas(
            await get_unidades_permitidas_v2(current_user)
        )
        unidades = _scope_unidades(permitidas, unidad_negocio_pk)
        periodos = resolver_periodos_comparables(
            modo=modo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_corte_datos=fecha_corte_datos,
        )
        etiquetas = resolver_etiquetas(modo)

        actual = _consultar_agregado(
            inicio=periodos.actual.inicio,
            fin=periodos.actual.fin,
            unidades=unidades,
        )
        inmediato = _consultar_agregado(
            inicio=periodos.inmediato.inicio,
            fin=periodos.inmediato.fin,
            unidades=unidades,
        )
        anual = _consultar_agregado(
            inicio=periodos.anual.inicio,
            fin=periodos.anual.fin,
            unidades=unidades,
        )

        unidades_actuales = _consultar_unidades_con_datos(
            inicio=periodos.actual.inicio,
            fin=periodos.actual.fin,
            unidades=unidades,
        )
        unidades_inmediatas = _consultar_unidades_con_datos(
            inicio=periodos.inmediato.inicio,
            fin=periodos.inmediato.fin,
            unidades=unidades,
        )
        unidades_anuales = _consultar_unidades_con_datos(
            inicio=periodos.anual.inicio,
            fin=periodos.anual.fin,
            unidades=unidades,
        )

        if modo is ModoPeriodo.VENTAS_DIA:
            proyeccion = _proyectar_dia(
                fecha_actual=periodos.actual.fin,
                ventas_actuales=actual["ventas"],
                unidades=unidades,
            )
        else:
            fechas_pendientes = []
            cursor = periodos.actual.fin + timedelta(days=1)
            while cursor <= fecha_fin:
                fechas_pendientes.append(cursor)
                cursor += timedelta(days=1)

            historico_mes = _consultar_ventas_diarias(
                inicio=fecha_inicio,
                fin=periodos.actual.fin,
                unidades=unidades,
            )
            historico_respaldo = _consultar_ventas_diarias(
                inicio=fecha_inicio - timedelta(days=120),
                fin=fecha_inicio - timedelta(days=1),
                unidades=unidades,
            )
            proyeccion = proyectar_mes_por_dia_semana(
                ventas_reales_acumuladas=actual["ventas"],
                fechas_pendientes=fechas_pendientes,
                historico_mes=historico_mes,
                historico_respaldo=historico_respaldo,
            ).to_dict()

        proyeccion_total = float(proyeccion.get("proyeccion_total") or 0)
        tiene_inmediato = inmediato["dias"] > 0
        tiene_anual = anual["dias"] > 0
        response = {
            "modo_periodo": modo.value,
            "etiquetas": asdict(etiquetas),
            "periodos": {
                "actual": _rango_to_dict(periodos.actual),
                "inmediato": _rango_to_dict(periodos.inmediato),
                "anual": _rango_to_dict(periodos.anual),
                "periodo_cerrado": periodos.periodo_cerrado,
                "fecha_corte_datos": periodos.actual.fin.isoformat(),
            },
            "actual": actual,
            "comparativos": {
                "inmediato": {
                    **inmediato,
                    "var_ventas": calcular_variacion(
                        actual["ventas"], inmediato["ventas"] if tiene_inmediato else None
                    ),
                    "var_pax": calcular_variacion(
                        actual["pax"], inmediato["pax"] if tiene_inmediato else None
                    ),
                    "var_cheques": calcular_variacion(
                        actual["cheques"], inmediato["cheques"] if tiene_inmediato else None
                    ),
                    "var_proyeccion": calcular_variacion(
                        proyeccion_total,
                        inmediato["ventas"] if tiene_inmediato else None,
                    ),
                },
                "anual": {
                    **anual,
                    "var_ventas": calcular_variacion(
                        actual["ventas"], anual["ventas"] if tiene_anual else None
                    ),
                    "var_pax": calcular_variacion(
                        actual["pax"], anual["pax"] if tiene_anual else None
                    ),
                    "var_cheques": calcular_variacion(
                        actual["cheques"], anual["cheques"] if tiene_anual else None
                    ),
                    "var_proyeccion": calcular_variacion(
                        proyeccion_total,
                        anual["ventas"] if tiene_anual else None,
                    ),
                },
            },
            "proyeccion": proyeccion,
            "unidades_con_datos": _resumen_unidades_comparables(
                unidades_actuales,
                unidades_inmediatas,
                unidades_anuales,
            ),
            "trazabilidad": {
                "fuente": "vw_Comercial_KPIs_Diarios_v2_Runtime",
                "sql_vivo": False,
                "mongodb": False,
                "unidades_rbac": unidades,
            },
        }
        return {"success": True, "data": serialize_response(response)}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No fue posible construir el contrato canonico de periodo",
        ) from exc
