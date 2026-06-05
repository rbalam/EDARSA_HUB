def get_accumulated_units(units_db, selected_months, monthly_historical_data):
    """
    Acumula las métricas de negocio matemáticamente basándose en un mes actual (anchored a Mayo)
    para proveer una distribución estacional fiel a los datos extraídos de la base de datos.
    
    :param units_db: Lista de diccionarios con el valor vivio actual de la BD [{ "id": "cienfuegos", "ventas": 4.39, ... }]
    :param selected_months: Lista de meses activos ej. ["Enero", "Febrero"]
    :param monthly_historical_data: Diccionario con la pre-configuración de estacionalidad histórica
    """
    accumulated_units = []
    
    # Si no hay meses seleccionados, por defecto se usa el mes ancla (Mayo)
    active_months = selected_months if selected_months else ["Mayo"]
    
    for u in units_db:
        unit_id = u.get("id")
        
        # 1. Determina los valores en vivo traídos de tu BD (el mes estático/reciente)
        base_ventas = u.get("ventas", 0.0)
        base_pax = u.get("pax", 0)
        base_cheques = u.get("cheques", 0)
        
        # 2. Busca la estacionalidad base (fallback a "cienfuegos" si no se ha configurado)
        unit_historical = monthly_historical_data.get(unit_id, monthly_historical_data.get("cienfuegos", {}))
        
        # 3. Mes Ancla (Mayo)
        baseline_month = unit_historical.get("Mayo", {})
        base_hist_ventas = baseline_month.get("ventas", 1) or 1
        base_hist_pax = baseline_month.get("pax", 1) or 1
        base_hist_cheques = baseline_month.get("cheques", 1) or 1
        
        coef_ventas, coef_pax, coef_cheques = 0.0, 0.0, 0.0
        
        # 4. Sumar los coeficientes de proporción según estacionalidad 
        for m in active_months:
            mh = unit_historical.get(m)
            if mh:
                coef_ventas += (mh.get("ventas", 0) / base_hist_ventas)
                coef_pax += (mh.get("pax", 0) / base_hist_pax)
                coef_cheques += (mh.get("cheques", 0) / base_hist_cheques)
                
        # 5. Evita coeficientes nulos por si envían meses incorrectos
        if coef_ventas == 0.0: coef_ventas = 1.0
        if coef_pax == 0.0: coef_pax = 1.0
        if coef_cheques == 0.0: coef_cheques = 1.0
        
        # 6. Crear el nuevo objeto acumulado
        u_accumulated = u.copy()
        
        # Se calcula la verdadera proporción dinámica
        u_accumulated["ventas"] = base_ventas * coef_ventas
        u_accumulated["pax"] = round(base_pax * coef_pax)
        u_accumulated["cheques"] = round(base_cheques * coef_cheques)
        
        accumulated_units.append(u_accumulated)
        
    return accumulated_units

# ---- EJEMPLO DE USO ----

# Tu data viva de la BD
units_from_db = [
    { "id": "cienfuegos", "name": "CIENFUEGOS", "ventas": 4.39, "pax": 3353, "cheques": 1113 },
    { "id": "merida", "name": "130° MERIDA", "ventas": 3.90, "pax": 2539, "cheques": 871 }
]

# Matriz estacional (Simplificada para el ejemplo)
monthly_data = {
    "cienfuegos": {
        "Enero": { "ventas": 3.80, "pax": 2900, "cheques": 980 },
        "Mayo": { "ventas": 4.39, "pax": 3353, "cheques": 1113 } # Mes Ancla
    }
}

# Ejecución: Solo calculamos para Enero usando la data de la DB actual (que en este caso es Mayo)
resultado = get_accumulated_units(units_from_db, ["Enero"], monthly_data)

print("Ventas calculadas con peso estacional:")
for r in resultado:
    print(f"{r['name']}: {r['ventas']:.2f}M")
