"""Reglas puras para el tablero comercial dinamico por periodo.

Este modulo no consulta SQL, no conoce unidades y no modifica fuentes. Centraliza
las reglas de etiquetas, rangos comparables y proyeccion por dia de semana para
que Ejecutivo, Comercial e Inteligencia consuman el mismo contrato.
"""

from __future__ import annotations

import calendar
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from statistics import mean
from typing import Any, Iterable, Mapping, Optional, Sequence


class ModoPeriodo(str, Enum):
    VENTAS_DIA = "ventas_dia"
    MENSUAL = "mensual"


class NivelConfianza(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"
    SIN_BASE = "SIN_BASE"


DIAS_SEMANA_ES = {
    0: "lunes",
    1: "martes",
    2: "mi\u00e9rcoles",
    3: "jueves",
    4: "viernes",
    5: "s\u00e1bado",
    6: "domingo",
}


@dataclass(frozen=True)
class EtiquetasPeriodo:
    comparativo_inmediato: str
    comparativo_anual: str
    titulo_proyeccion: str
    titulo_tendencia: str
    tooltip_inmediato: str
    tooltip_anual: str


@dataclass(frozen=True)
class RangoComparable:
    inicio: date
    fin: date


@dataclass(frozen=True)
class PeriodosComparables:
    modo: ModoPeriodo
    actual: RangoComparable
    inmediato: RangoComparable
    anual: RangoComparable
    periodo_cerrado: bool


@dataclass(frozen=True)
class ProyeccionDiaSemana:
    dia_semana: int
    nombre: str
    dias_pendientes: int
    promedio_ventas: float
    muestras: int
    metodo: str
    nivel_confianza: NivelConfianza
    importe_proyectado: float


@dataclass(frozen=True)
class ProyeccionMes:
    ventas_reales: float
    ventas_pendientes_proyectadas: float
    proyeccion_total: float
    periodo_cerrado: bool
    metodo: str
    nivel_confianza: NivelConfianza
    detalle: tuple[ProyeccionDiaSemana, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["nivel_confianza"] = self.nivel_confianza.value
        for item in data["detalle"]:
            item["nivel_confianza"] = item["nivel_confianza"].value
        return data


def resolver_etiquetas(
    modo: ModoPeriodo | str,
    *,
    es_multimes: bool = False,
) -> EtiquetasPeriodo:
    modo_resuelto = ModoPeriodo(modo)
    if modo_resuelto is ModoPeriodo.VENTAS_DIA:
        return EtiquetasPeriodo(
            comparativo_inmediato="vs D\u00eda Ant.",
            comparativo_anual="vs D\u00eda A\u00f1o Ant.",
            titulo_proyeccion="Proyecci\u00f3n del d\u00eda",
            titulo_tendencia="Ventas por hora",
            tooltip_inmediato=(
                "Comparaci\u00f3n contra el d\u00eda operativo anterior al mismo corte."
            ),
            tooltip_anual=(
                "Comparaci\u00f3n contra el mismo d\u00eda operativo del a\u00f1o anterior "
                "al mismo corte."
            ),
        )

    return EtiquetasPeriodo(
        comparativo_inmediato=("vs Periodo Ant." if es_multimes else "vs Mes Ant."),
        comparativo_anual="vs Mes A\u00f1o Ant.",
        titulo_proyeccion="Proyecci\u00f3n mes",
        titulo_tendencia="Proyecci\u00f3n por d\u00eda de semana",
        tooltip_inmediato=(
            "Comparaci\u00f3n contra el periodo mensual inmediato anterior con el "
            "mismo alcance de dias cuando el mes sigue abierto."
        ),
        tooltip_anual=(
            "Comparaci\u00f3n contra el mismo mes del a\u00f1o anterior; si el mes est\u00e1 "
            "abierto usa el mismo d\u00eda de corte y si est\u00e1 cerrado usa el mes completo."
        ),
    )


def calcular_variacion(actual: Optional[float], base: Optional[float]) -> Optional[float]:
    """Devuelve porcentaje o ``None`` cuando no existe una base valida.

    Cero contra cero es una variacion real de 0 %. Un valor actual positivo
    contra base cero no se inventa como 0 %, porque la division no es comparable.
    """

    if actual is None or base is None:
        return None
    actual_num = float(actual)
    base_num = float(base)
    if base_num == 0:
        return 0.0 if actual_num == 0 else None
    return round(((actual_num - base_num) / base_num) * 100, 1)


def _coerce_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise TypeError(f"Fecha no soportada: {type(value)!r}")


def _replace_year_safe(value: date, year: int) -> date:
    try:
        return value.replace(year=year)
    except ValueError:
        return value.replace(year=year, day=28)


def _shift_month(value: date, months: int) -> date:
    absolute = value.year * 12 + (value.month - 1) + months
    year, month_zero = divmod(absolute, 12)
    month = month_zero + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def resolver_periodos_comparables(
    *,
    modo: ModoPeriodo | str,
    fecha_inicio: date,
    fecha_fin: date,
    fecha_corte_datos: Optional[date] = None,
) -> PeriodosComparables:
    """Resuelve rangos actuales, inmediatos y anuales sin usar fecha civil oculta."""

    modo_resuelto = ModoPeriodo(modo)
    inicio = _coerce_date(fecha_inicio)
    fin = _coerce_date(fecha_fin)
    if inicio > fin:
        raise ValueError("fecha_inicio no puede ser posterior a fecha_fin")

    corte = _coerce_date(fecha_corte_datos) if fecha_corte_datos else fin
    fin_efectivo = min(fin, max(inicio, corte))

    if modo_resuelto is ModoPeriodo.VENTAS_DIA:
        actual = RangoComparable(fin_efectivo, fin_efectivo)
        inmediato_fecha = fin_efectivo - timedelta(days=1)
        anual_fecha = _replace_year_safe(fin_efectivo, fin_efectivo.year - 1)
        return PeriodosComparables(
            modo=modo_resuelto,
            actual=actual,
            inmediato=RangoComparable(inmediato_fecha, inmediato_fecha),
            anual=RangoComparable(anual_fecha, anual_fecha),
            periodo_cerrado=False,
        )

    periodo_cerrado = corte >= fin
    actual = RangoComparable(inicio, fin if periodo_cerrado else fin_efectivo)
    inmediato_inicio = _shift_month(inicio, -1)
    inmediato_fin = _shift_month(actual.fin, -1)
    anual_inicio = _replace_year_safe(inicio, inicio.year - 1)
    anual_fin = _replace_year_safe(actual.fin, actual.fin.year - 1)

    return PeriodosComparables(
        modo=modo_resuelto,
        actual=actual,
        inmediato=RangoComparable(inmediato_inicio, inmediato_fin),
        anual=RangoComparable(anual_inicio, anual_fin),
        periodo_cerrado=periodo_cerrado,
    )


def _normalizar_historico(
    rows: Optional[Iterable[Mapping[str, Any]]],
) -> list[tuple[date, float]]:
    normalizado: list[tuple[date, float]] = []
    for row in rows or []:
        if row.get("completo", True) is False:
            continue
        fecha_raw = row.get("fecha_operacion", row.get("fecha"))
        ventas_raw = row.get("ventas_total", row.get("ventas"))
        if fecha_raw in (None, "") or ventas_raw is None:
            continue
        fecha = _coerce_date(fecha_raw)
        ventas = float(ventas_raw)
        normalizado.append((fecha, ventas))
    normalizado.sort(key=lambda item: item[0], reverse=True)
    return normalizado


def _nivel_confianza(muestras: int, *, uso_respaldo: bool) -> NivelConfianza:
    if muestras <= 0:
        return NivelConfianza.SIN_BASE
    if not uso_respaldo and muestras >= 3:
        return NivelConfianza.ALTA
    if muestras >= 2:
        return NivelConfianza.MEDIA
    return NivelConfianza.BAJA


def proyectar_mes_por_dia_semana(
    *,
    ventas_reales_acumuladas: float,
    fechas_pendientes: Sequence[date],
    historico_mes: Iterable[Mapping[str, Any]],
    historico_respaldo: Optional[Iterable[Mapping[str, Any]]] = None,
    minimo_muestras_mes: int = 2,
    muestras_respaldo: int = 3,
) -> ProyeccionMes:
    """Proyecta dias pendientes con promedios de lunes, martes, etc.

    Conserva las ventas reales, usa primero dias completos del mes y completa
    muestras insuficientes con dias equivalentes recientes del respaldo.
    """

    if minimo_muestras_mes < 1:
        raise ValueError("minimo_muestras_mes debe ser mayor o igual a 1")
    if muestras_respaldo < 1:
        raise ValueError("muestras_respaldo debe ser mayor o igual a 1")

    pendientes = [_coerce_date(value) for value in fechas_pendientes]
    ventas_reales = float(ventas_reales_acumuladas or 0)
    if not pendientes:
        return ProyeccionMes(
            ventas_reales=round(ventas_reales, 2),
            ventas_pendientes_proyectadas=0.0,
            proyeccion_total=round(ventas_reales, 2),
            periodo_cerrado=True,
            metodo="MES_CERRADO",
            nivel_confianza=NivelConfianza.ALTA,
            detalle=tuple(),
        )

    mes_rows = _normalizar_historico(historico_mes)
    respaldo_rows = _normalizar_historico(historico_respaldo)
    mes_por_dia: dict[int, list[tuple[date, float]]] = defaultdict(list)
    respaldo_por_dia: dict[int, list[tuple[date, float]]] = defaultdict(list)
    pendientes_por_dia: dict[int, int] = defaultdict(int)

    for fecha, ventas in mes_rows:
        mes_por_dia[fecha.weekday()].append((fecha, ventas))
    for fecha, ventas in respaldo_rows:
        respaldo_por_dia[fecha.weekday()].append((fecha, ventas))
    for fecha in pendientes:
        pendientes_por_dia[fecha.weekday()] += 1

    detalle: list[ProyeccionDiaSemana] = []
    proyeccion_pendiente = 0.0
    niveles: list[NivelConfianza] = []

    for dia_semana in sorted(pendientes_por_dia):
        dias_pendientes = pendientes_por_dia[dia_semana]
        muestras_mes = mes_por_dia.get(dia_semana, [])
        uso_respaldo = len(muestras_mes) < minimo_muestras_mes

        if uso_respaldo:
            fechas_mes = {fecha for fecha, _ in muestras_mes}
            respaldo_filtrado = [
                item
                for item in respaldo_por_dia.get(dia_semana, [])
                if item[0] not in fechas_mes
            ]
            objetivo = max(muestras_respaldo, minimo_muestras_mes)
            muestras = (muestras_mes + respaldo_filtrado)[:objetivo]
            metodo = "ULTIMOS_DIAS_EQUIVALENTES"
        else:
            muestras = muestras_mes
            metodo = "PROMEDIO_MES_DIA_SEMANA"

        promedio = round(mean(ventas for _, ventas in muestras), 2) if muestras else 0.0
        importe = round(promedio * dias_pendientes, 2)
        confianza = _nivel_confianza(len(muestras), uso_respaldo=uso_respaldo)
        niveles.append(confianza)
        proyeccion_pendiente += importe
        detalle.append(
            ProyeccionDiaSemana(
                dia_semana=dia_semana,
                nombre=DIAS_SEMANA_ES[dia_semana],
                dias_pendientes=dias_pendientes,
                promedio_ventas=promedio,
                muestras=len(muestras),
                metodo=metodo if muestras else "SIN_BASE_HISTORICA",
                nivel_confianza=confianza,
                importe_proyectado=importe,
            )
        )

    orden_confianza = {
        NivelConfianza.ALTA: 3,
        NivelConfianza.MEDIA: 2,
        NivelConfianza.BAJA: 1,
        NivelConfianza.SIN_BASE: 0,
    }
    confianza_global = min(niveles, key=orden_confianza.get) if niveles else NivelConfianza.SIN_BASE
    metodos = {item.metodo for item in detalle}
    metodo_global = next(iter(metodos)) if len(metodos) == 1 else "MIXTO_DIA_SEMANA"

    return ProyeccionMes(
        ventas_reales=round(ventas_reales, 2),
        ventas_pendientes_proyectadas=round(proyeccion_pendiente, 2),
        proyeccion_total=round(ventas_reales + proyeccion_pendiente, 2),
        periodo_cerrado=False,
        metodo=metodo_global,
        nivel_confianza=confianza_global,
        detalle=tuple(detalle),
    )


def contar_unidades_comparables(
    unidades_actuales: Iterable[str],
    unidades_anio_anterior: Iterable[str],
) -> dict[str, Any]:
    actuales = {str(value) for value in unidades_actuales if value not in (None, "")}
    anteriores = {
        str(value) for value in unidades_anio_anterior if value not in (None, "")
    }
    return {
        "actual": len(actuales),
        "anio_anterior": len(anteriores),
        "diferencia": len(actuales) - len(anteriores),
        "unidades_actuales": sorted(actuales),
        "unidades_anio_anterior": sorted(anteriores),
    }
