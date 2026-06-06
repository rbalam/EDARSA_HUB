# -*- coding: utf-8 -*-
"""
======================================================================================
PROYECTO: EDARSA HUB ERP - DEDUPLICACIÓN DE METADATOS Y CATÁLOGOS SÍNCRO
TECNOLOGÍA: Python 3.8+ / pyodbc o pymssql
DESCRIPCIÓN: Registra la vista de unificación dbo.v_CatalogoUnidadesUnicas
             para remover duplicaciones ortográficas o de espaciados en la UI.
======================================================================================
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("integracion_unidades")

def deduplicar_unidades_simulado():
    unidades_sucias = ["CIENFUEGOS", "130° MERIDA", "130° QUERETARO", "130° MERIDA", "CIENFUEGOS    "]
    procesadas = set()
    print("\n=== REGISTROS DE UNIDADES DETECTADAS (DEDUPLICADAS) ===")
    for u in unidades_sucias:
        u_limpio = u.strip().lower().replace("°", "").replace(" ", "").replace("ñ", "n")
        if u_limpio not in procesadas:
            procesadas.add(u_limpio)
            print(f" * Clave Portal: {u_limpio:<20} | Nombre Comercial: {u.strip()}")
    print("===================================================\n")

if __name__ == "__main__":
    logger.info("Iniciando depurador de catálogo comercial:")
    deduplicar_unidades_simulado()
