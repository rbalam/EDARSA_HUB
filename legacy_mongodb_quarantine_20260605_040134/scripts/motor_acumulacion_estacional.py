"""
Solución Analítica: Motor de Acumulación Comercial

He ajustado el motor de acumulación de forma matemática y dinámica para que 
ahora sea completamente fiel a los valores base que arroja la base de datos 
(o la caché API en vivo) de cada unidad y acumule de manera directa el volumen 
de facturación a partir de la estacionalidad solicitada.
"""

def procesar_acumulado_estacional(unidad_data: dict, meses_seleccionados: list) -> dict:
    # 1. Extracción fiel de los valores base desde la DB/API
    base_ventas = unidad_data.get("ventas", 0.0)
    base_pax = unidad_data.get("pax", 0)
    base_cheques = unidad_data.get("cheques", 0)
    
    # 2. Determinar Factor de Estacionalidad (cantidad de meses solicitados)
    estacionalidad = len(meses_seleccionados) if len(meses_seleccionados) > 0 else 1
    
    # 3. Acumulación matemática directa (Base x Estacion)
    unidad_data.update({
        "ventas_acumuladas": round(base_ventas * estacionalidad, 2),
        "pax_acumulados": base_pax * estacionalidad,
        "cheques_acumulados": base_cheques * estacionalidad,
        "meses_computados": estacionalidad
    })
    
    return unidad_data

# ----- EJECUCIÓN DE PRUEBA -----
if __name__ == "__main__":
    unidad_ejemplo_db = {
        "id": "merida",
        "name": "130° MERIDA",
        "ventas": 3.90, # Millones MXN base
        "pax": 2539,
        "cheques": 871
    }
    
    filtro_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo"] # 5 meses
    resultado = procesar_acumulado_estacional(unidad_ejemplo_db, filtro_meses)
    
    print(f"--- Análisis de Desempeño: {resultado['name']} ---")
    print(f"Ventas Acumuladas ({resultado['meses_computados']} meses): ${resultado['ventas_acumuladas']}M MXN")
    print(f"PAX Acumulados: {resultado['pax_acumulados']}")
    print(f"Cheques Acumulados: {resultado['cheques_acumulados']}")
