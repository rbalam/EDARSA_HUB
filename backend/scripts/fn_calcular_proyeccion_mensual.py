# -*- coding: utf-8 -*-
"""
======================================================================================
PROYECTO: EDARSA HUB ERP - PROYECCIÓN MENSUAL ESCALAR CON COMPENSACIÓN TEMPORAL
TECNOLOGÍA: Python 3.8+ / pyodbc o pymssql
DESCRIPCIÓN: Define la función escalar dbo.fn_CalcularProyeccionMensual en BD.
             Resuelve bisiestos y mapea meses en español para la capa React.
======================================================================================
"""

import sys
import logging
import calendar

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("proyeccion_mensual")

def py_calcular_proyeccion_mensual(ventas, dias_vta, mes, anio):
    mes_map = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    num_mes = mes_map.get(mes.lower().strip())
    if num_mes is None:
        return None
    _, total_dias = calendar.monthrange(anio, num_mes)
    if dias_vta == 0:
        return 0.0
    return (ventas / dias_vta) * total_dias

if __name__ == "__main__":
    logger.info("Validando aritmética de proyección mensual local:")
    bisiesto = py_calcular_proyeccion_mensual(15000.00, 10, "febrero", 2024)
    regular = py_calcular_proyeccion_mensual(15000.00, 10, "febrero", 2026)
    
    print(f" -> Febrero Bisiesto 2024 (29 días): ${bisiesto:,.2f} MXN")
    print(f" -> Febrero Regular  2026 (28 días): ${regular:,.2f}  MXN")
