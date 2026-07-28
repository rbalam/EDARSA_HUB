from datetime import date

import pytest

from modules.comercial_v2.periodos import (
    ModoPeriodo,
    calcular_variacion,
    contar_unidades_comparables,
    proyectar_mes_por_dia_semana,
    resolver_etiquetas,
    resolver_periodos_comparables,
)


def test_etiquetas_ventas_dia():
    etiquetas = resolver_etiquetas(ModoPeriodo.VENTAS_DIA)

    assert etiquetas.comparativo_inmediato == "vs Día Ant."
    assert etiquetas.comparativo_anual == "vs Día Año Ant."
    assert etiquetas.titulo_proyeccion == "Proyección del día"
    assert etiquetas.titulo_tendencia == "Ventas por hora"


def test_etiquetas_mes():
    etiquetas = resolver_etiquetas(ModoPeriodo.MENSUAL)

    assert etiquetas.comparativo_inmediato == "vs Mes Ant."
    assert etiquetas.comparativo_anual == "vs Mes Año Ant."
    assert etiquetas.titulo_proyeccion == "Proyección mes"
    assert etiquetas.titulo_tendencia == "Proyección por día de semana"


def test_etiqueta_multimes_conserva_periodo_anterior():
    etiquetas = resolver_etiquetas(ModoPeriodo.MENSUAL, es_multimes=True)

    assert etiquetas.comparativo_inmediato == "vs Periodo Ant."
    assert etiquetas.comparativo_anual == "vs Mes Año Ant."


def test_periodos_ventas_dia():
    periodos = resolver_periodos_comparables(
        modo=ModoPeriodo.VENTAS_DIA,
        fecha_inicio=date(2026, 7, 27),
        fecha_fin=date(2026, 7, 27),
        fecha_corte_datos=date(2026, 7, 27),
    )

    assert periodos.actual.inicio == date(2026, 7, 27)
    assert periodos.inmediato.inicio == date(2026, 7, 26)
    assert periodos.anual.inicio == date(2025, 7, 27)
    assert periodos.periodo_cerrado is False


def test_periodos_mes_abierto_comparan_mismo_dia_de_corte():
    periodos = resolver_periodos_comparables(
        modo=ModoPeriodo.MENSUAL,
        fecha_inicio=date(2026, 7, 1),
        fecha_fin=date(2026, 7, 31),
        fecha_corte_datos=date(2026, 7, 27),
    )

    assert periodos.actual.fin == date(2026, 7, 27)
    assert periodos.inmediato.inicio == date(2026, 6, 1)
    assert periodos.inmediato.fin == date(2026, 6, 27)
    assert periodos.anual.inicio == date(2025, 7, 1)
    assert periodos.anual.fin == date(2025, 7, 27)
    assert periodos.periodo_cerrado is False


def test_periodos_mes_cerrado_comparan_mes_completo():
    periodos = resolver_periodos_comparables(
        modo=ModoPeriodo.MENSUAL,
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 30),
        fecha_corte_datos=date(2026, 6, 30),
    )

    assert periodos.actual.fin == date(2026, 6, 30)
    assert periodos.anual.inicio == date(2025, 6, 1)
    assert periodos.anual.fin == date(2025, 6, 30)
    assert periodos.periodo_cerrado is True


def test_periodos_soportan_29_febrero():
    periodos = resolver_periodos_comparables(
        modo=ModoPeriodo.VENTAS_DIA,
        fecha_inicio=date(2024, 2, 29),
        fecha_fin=date(2024, 2, 29),
        fecha_corte_datos=date(2024, 2, 29),
    )

    assert periodos.anual.inicio == date(2023, 2, 28)


@pytest.mark.parametrize(
    ("actual", "base", "esperado"),
    [
        (120, 100, 20.0),
        (80, 100, -20.0),
        (0, 0, 0.0),
        (100, 0, None),
        (None, 100, None),
    ],
)
def test_calcular_variacion_sin_ceros_falsos(actual, base, esperado):
    assert calcular_variacion(actual, base) == esperado


def test_proyeccion_mes_por_dia_semana_conserva_reales_y_proyecta_pendientes():
    historico_mes = [
        {"fecha_operacion": "2026-07-06", "ventas_total": 100, "completo": True},
        {"fecha_operacion": "2026-07-13", "ventas_total": 120, "completo": True},
        {"fecha_operacion": "2026-07-07", "ventas_total": 200, "completo": True},
        {"fecha_operacion": "2026-07-14", "ventas_total": 220, "completo": True},
    ]

    resultado = proyectar_mes_por_dia_semana(
        ventas_reales_acumuladas=1000,
        fechas_pendientes=[date(2026, 7, 27), date(2026, 7, 28)],
        historico_mes=historico_mes,
    )

    assert resultado.ventas_reales == 1000
    assert resultado.ventas_pendientes_proyectadas == 320
    assert resultado.proyeccion_total == 1320
    assert resultado.periodo_cerrado is False
    assert {item.nombre for item in resultado.detalle} == {"lunes", "martes"}


def test_proyeccion_usa_respaldo_para_dia_con_muestras_insuficientes():
    historico_mes = [
        {"fecha_operacion": "2026-07-06", "ventas_total": 100, "completo": True},
    ]
    respaldo = [
        {"fecha_operacion": "2026-06-29", "ventas_total": 130, "completo": True},
        {"fecha_operacion": "2026-06-22", "ventas_total": 160, "completo": True},
    ]

    resultado = proyectar_mes_por_dia_semana(
        ventas_reales_acumuladas=500,
        fechas_pendientes=[date(2026, 7, 27)],
        historico_mes=historico_mes,
        historico_respaldo=respaldo,
    )

    assert resultado.proyeccion_total == 630
    assert resultado.detalle[0].muestras == 3
    assert resultado.detalle[0].metodo == "ULTIMOS_DIAS_EQUIVALENTES"


def test_mes_cerrado_no_inventa_proyeccion():
    resultado = proyectar_mes_por_dia_semana(
        ventas_reales_acumuladas=16007310.58,
        fechas_pendientes=[],
        historico_mes=[],
    )

    assert resultado.proyeccion_total == 16007310.58
    assert resultado.ventas_pendientes_proyectadas == 0
    assert resultado.periodo_cerrado is True
    assert resultado.metodo == "MES_CERRADO"


def test_conteo_unidades_actual_vs_anio_anterior():
    resultado = contar_unidades_comparables(
        ["130MID", "130QRO", "ORIGEN", "CIENFUEGOS", "ESTELAR"],
        ["130MID", "130QRO", "CIENFUEGOS", "ESTELAR"],
    )

    assert resultado["actual"] == 5
    assert resultado["anio_anterior"] == 4
    assert resultado["diferencia"] == 1
