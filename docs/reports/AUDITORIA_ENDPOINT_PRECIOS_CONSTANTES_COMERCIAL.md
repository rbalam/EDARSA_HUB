# Auditoría endpoint /comercial/precios-constantes/{server_id}

Fecha: Thu Jun  4 20:38:38 UTC 2026

## Objetivo

Auditar el endpoint visual:

```text
GET /comercial/precios-constantes/{server_id}
```

Este endpoint está clasificado como PROHIBIDO_LIVE_VISUAL.

Este script no modifica código.

## Reglas

- No modificar backend.
- No modificar frontend.
- No crear tabla todavía.
- No activar políticas.
- No tocar sync.
- Solo documentar endpoint, queries, response, consumidores frontend y tabla SQL-first candidata.
## Bloque backend del endpoint
```python
# Línea inicial: 3500
@router.get("/comercial/precios-constantes/{server_id}")
async def ventas_precios_constantes(
    server_id: str,
    periodo_actual: str = Query(..., description="Período actual: YYYY-MM o YYYY-MM,YYYY-MM"),
    periodo_base: str = Query(..., description="Período base para precios: YYYY-MM o YYYY-MM,YYYY-MM"),
    granularidad: str = Query(default="categoria", description="categoria, familia, producto"),
    sucursal: str = Query(default="all", description="ID de sucursal o 'all' para todas"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Análisis de ventas valuando a precios constantes de un período base.
    
    FASE A-P0 (2026-05-26): GUARD RAIL LIVE
    Este endpoint requiere conexión LIVE. Bloqueado hasta migrar a Sync_Precios_Historicos.
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # FASE 6-8: Validación centralizada de acceso
    await validate_server_access_rbac(current_user, server_id)
    
    # FASE A-P0: GUARD RAIL LIVE
    guard_result = check_live_guard_rail('/comercial/precios-constantes', server_id)
    if guard_result:
        return {
            "source_status": guard_result['source_status'],
            "source_message": guard_result['source_message'],
            "periodo_actual": periodo_actual,
            "periodo_base": periodo_base,
            "granularidad": granularidad,
            "data": [],
            "resumen": {
                "ventas_reales": 0,
                "ventas_constantes": 0,
                "variacion_real": 0,
                "variacion_volumen": 0,
                "inflacion_implicita": 0
            }
        }
    
    # CÓDIGO LEGACY (solo se ejecuta si ENABLE_LIVE_GUARD_RAIL = False)
    try:
        # Parsear períodos (pueden ser múltiples meses separados por coma)
        def parse_periodos(periodo_str):
            meses = [m.strip() for m in periodo_str.split(',')]
            fechas = []
            for mes in meses:
                year, month = mes.split('-')
                year, month = int(year), int(month)
                ultimo_dia = calendar.monthrange(year, month)[1]
                fechas.append({
                    'mes': mes,
                    'year': year,
                    'month': month,
                    'fecha_ini': f"{year}-{month:02d}-01",
                    'fecha_fin': f"{year}-{month:02d}-{ultimo_dia:02d}"
                })
            return fechas
        
        periodos_actual = parse_periodos(periodo_actual)
        periodos_base = parse_periodos(periodo_base)
        
        # Fechas consolidadas
        fecha_ini_actual = min(p['fecha_ini'] for p in periodos_actual)
        fecha_fin_actual = max(p['fecha_fin'] for p in periodos_actual)
        fecha_ini_base = min(p['fecha_ini'] for p in periodos_base)
        fecha_fin_base = max(p['fecha_fin'] for p in periodos_base)
        
        logging.info(f"Precios Constantes - Actual: {fecha_ini_actual} a {fecha_fin_actual}, Base: {fecha_ini_base} a {fecha_fin_base}")
        
        # FASE 3A.2: Migrado a helper centralizado
        if is_softrestaurant_system(server.get('system_type')):
            # Formato YYYYMMDD para SoftRestaurant - usando CONVERT para evitar errores de conversión
            f_ini_actual = fecha_ini_actual.replace('-', '')
            f_fin_actual = fecha_fin_actual.replace('-', '')
            f_ini_base = fecha_ini_base.replace('-', '')
            f_fin_base = fecha_fin_base.replace('-', '')
            
            # Verificar si la tabla cheques tiene columna 'propina'
            has_propina = check_column_exists(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], 'cheques', 'propina'
            )
            propina_expr = get_propina_safe_column(has_propina)
            
            # PASO 1: Obtener VENTAS REALES del período (misma lógica que Dashboard)
            # Esto asegura que los totales coincidan con el Tablero Ejecutivo
            # BLINDAJE: Usamos CONVERT(varchar, turnos.apertura, 112) para consistencia
            # NOTA: Se excluyen propinas de las ventas SI existe la columna
            query_ventas_reales = f"""
SELECT SUM(cheques.total{propina_expr}) as ventas_reales
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini_actual}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin_actual}'
  AND cheques.cancelado = 0
"""
            result_ventas_reales = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_reales
            )
            ventas_reales_periodo = float(result_ventas_reales[0]['ventas_reales'] or 0) if result_ventas_reales else 0
            
            # Query para ventas del período ACTUAL con precios actuales
            # Agrupa por producto y calcula precio promedio
            # NOTA: En SoftRestaurant la tabla de detalle es 'cheqdet' (no 'chequedetalle')
            # BLINDAJE: Usamos CONVERT para fechas
            query_ventas_actual = f"""
SELECT 
    p.idproducto as producto_id,
    p.descripcion as producto,
    'SoftRestaurant' as categoria,
    'Productos' as familia,
    SUM(cd.cantidad) as cantidad,
    SUM(cd.precio * cd.cantidad) as importe_actual,
    AVG(cd.precio) as precio_promedio_actual
FROM cheqdet cd
INNER JOIN cheques c ON c.folio = cd.foliodet
INNER JOIN turnos t ON t.idturno = c.idturno
INNER JOIN productos p ON p.idproducto = cd.idproducto
WHERE CONVERT(varchar, t.apertura, 112) >= '{f_ini_actual}'
  AND CONVERT(varchar, t.apertura, 112) <= '{f_fin_actual}'
  AND c.cancelado = 0
  AND cd.cantidad > 0
GROUP BY p.idproducto, p.descripcion
"""
            
            # Query para precios del período BASE - BLINDAJE: Usamos CONVERT
            query_precios_base = f"""
SELECT 
    p.idproducto as producto_id,
    p.descripcion as producto,
    AVG(cd.precio) as precio_promedio_base
FROM cheqdet cd
INNER JOIN cheques c ON c.folio = cd.foliodet
INNER JOIN turnos t ON t.idturno = c.idturno
INNER JOIN productos p ON p.idproducto = cd.idproducto
WHERE CONVERT(varchar, t.apertura, 112) >= '{f_ini_base}'
  AND CONVERT(varchar, t.apertura, 112) <= '{f_fin_base}'
  AND c.cancelado = 0
  AND cd.cantidad > 0
GROUP BY p.idproducto, p.descripcion
"""
            
            # Ejecutar queries
            ventas_actual = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_actual
            ) or []
            
            precios_base = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_precios_base
            ) or []
            
            # VALIDACIÓN (Abril 2026): Si no hay datos en el período base, no se puede hacer análisis
            # porque no hay precios de referencia con los cuales comparar
            if not precios_base or len(precios_base) == 0:
                logging.warning(f"Precios Constantes SoftRestaurant {server['name']}: Sin datos en período base {periodo_base}")
                return {
                    "servidor": server['name'],
                    "system_type": server['system_type'],
                    "periodo_actual": periodo_actual,
                    "periodo_base": periodo_base,
                    "granularidad": granularidad,
                    "error": f"Sin datos de ventas en el período base ({periodo_base}). No es posible calcular precios constantes sin un período de referencia con ventas.",
                    "kpis": {
                        "ventas_actuales": ventas_reales_periodo,
                        "ventas_constantes": 0,
                        "efecto_precio": 0,
                        "efecto_inflacion_pct": 0,
                        "variacion_real_pct": 0,
                        "productos_analizados": 0,
                        "productos_nuevos": 0,
                        "productos_descontinuados": 0
                    },
                    "datos": [],
                    "detalle_productos": None
                }
            
            # Crear diccionario de precios base
            precios_base_dict = {str(p['producto_id']): float(p['precio_promedio_base'] or 0) for p in precios_base}
            
            # PASO 2: Calcular suma de productos para obtener factor de ajuste
            suma_productos_actual = sum(float(v['importe_actual'] or 0) for v in ventas_actual)
            
            # Factor de ajuste: ventas reales / suma de productos
            # Esto distribuye propinas, impuestos, descuentos proporcionalmente
            factor_ajuste = ventas_reales_periodo / suma_productos_actual if suma_productos_actual > 0 else 1
            logging.info(f"SoftRestaurant - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
            
            # Procesar resultados aplicando factor de ajuste
            productos_detalle = []
            total_actual = 0
            total_constante = 0
            
            for venta in ventas_actual:
                producto_id = str(venta['producto_id'])
                cantidad = float(venta['cantidad'] or 0)
                precio_actual = float(venta['precio_promedio_actual'] or 0)
                # Aplicar factor de ajuste al importe para que coincida con ventas reales
                importe_actual = float(venta['importe_actual'] or 0) * factor_ajuste
                
                # Determinar precio a usar para valuación constante
                if producto_id in precios_base_dict:
                    precio_base = precios_base_dict[producto_id]
                    es_nuevo = False
                else:
                    # Producto nuevo - usar precio actual
                    precio_base = precio_actual
                    es_nuevo = True
                
                # El importe constante también debe ajustarse con el factor
                importe_constante = (cantidad * precio_base) * factor_ajuste
                efecto_precio = importe_actual - importe_constante
                variacion_precio_pct = ((precio_actual - precio_base) / precio_base * 100) if precio_base > 0 else 0
                
                productos_detalle.append({
                    'producto_id': producto_id,
                    'producto': venta['producto'],
                    'categoria': venta['categoria'],
                    'familia': venta['familia'],
                    'cantidad': cantidad,
                    'precio_actual': precio_actual,
                    'precio_base': precio_base,
                    'importe_actual': importe_actual,
                    'importe_constante': importe_constante,
                    'efecto_precio': efecto_precio,
                    'variacion_precio_pct': round(variacion_precio_pct, 2),
                    'es_nuevo': es_nuevo,
                    'es_descontinuado': False
                })
                
                total_actual += importe_actual
                total_constante += importe_constante
            
            # Buscar productos descontinuados (estaban en base pero no en actual)
            productos_actuales_ids = {str(v['producto_id']) for v in ventas_actual}
            for producto_id, precio_base in precios_base_dict.items():
                if producto_id not in productos_actuales_ids:
                    # Obtener info del producto descontinuado
                    # CORRECCIÓN SQL-SAFE (Abril 2026): Query parametrizada para prevenir SQL injection
                    # y manejar correctamente IDs alfanuméricos como 'A090035'
                    query_info = "SELECT TOP 1 descripcion FROM productos WHERE idproducto = %s"
                    info_result = execute_sql_query_params(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], 
                        query_info,
                        params=(str(producto_id),)  # Parámetro nativo - el driver maneja el tipo
                    )
                    nombre_producto = info_result[0]['descripcion'] if info_result else f'Producto {producto_id}'
                    
                    productos_detalle.append({
                        'producto_id': producto_id,
                        'producto': nombre_producto,
                        'categoria': 'Descontinuado',
                        'familia': '-',
                        'cantidad': 0,
                        'precio_actual': 0,
                        'precio_base': precio_base,
                        'importe_actual': 0,
                        'importe_constante': 0,
                        'efecto_precio': 0,
                        'variacion_precio_pct': 0,
                        'es_nuevo': False,
                        'es_descontinuado': True
                    })
            
            # Agrupar según granularidad
            if granularidad == 'categoria':
                agrupado = {}
                for p in productos_detalle:
                    key = p['categoria']
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                    if p['es_descontinuado']:
                        agrupado[key]['productos_descontinuados'] += 1
                
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            
            elif granularidad == 'familia':
                agrupado = {}
                for p in productos_detalle:
                    key = f"{p['categoria']} > {p['familia']}"
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'categoria': p['categoria'],
                            'familia': p['familia'],
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                    if p['es_descontinuado']:
                        agrupado[key]['productos_descontinuados'] += 1
                
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            
            else:  # producto
                datos_agrupados = sorted(productos_detalle, key=lambda x: x['importe_actual'], reverse=True)
            
            # Calcular métricas resumen
            efecto_precio_total = total_actual - total_constante
            variacion_real = round(((total_constante - total_actual) / total_actual * 100), 2) if total_actual > 0 else 0
            efecto_inflacion_pct = round((efecto_precio_total / total_constante * 100), 2) if total_constante > 0 else 0
            
            return {
                'servidor': server['name'],
                'system_type': server['system_type'],
                'periodo_actual': periodo_actual,
                'periodo_base': periodo_base,
                'granularidad': granularidad,
                'kpis': {
                    'ventas_actuales': round(total_actual, 2),
                    'ventas_constantes': round(total_constante, 2),
                    'efecto_precio': round(efecto_precio_total, 2),
                    'efecto_inflacion_pct': efecto_inflacion_pct,
                    'variacion_real_pct': variacion_real,
                    'productos_analizados': len([p for p in productos_detalle if not p['es_descontinuado']]),
                    'productos_nuevos': len([p for p in productos_detalle if p.get('es_nuevo')]),
                    'productos_descontinuados': len([p for p in productos_detalle if p.get('es_descontinuado')])
                },
                'datos': datos_agrupados,
                'detalle_productos': productos_detalle if granularidad == 'producto' else None
            }
        
        # FASE 3A.2: Migrado a helper centralizado
        elif is_mpro_system(server.get('system_type')):
            # Para MPRO - Las ventas están en la tabla 'venta' directamente
            # La sucursal está en la tabla 'sucursal' relacionada por Sc_Cve_Sucursal
            
            # BLINDAJE (Abril 2026): Mapeo de nombres de sucursal a códigos
            # El frontend envía nombres (ORIGEN, QUERETARO) pero MPRO usa códigos (0023, 0021)
            NOMBRE_A_CODIGO_SUCURSAL = {
                'ORIGEN': '0023',
                'QUERETARO': '0021',
                '130 QRO': '0021',
                'QRO': '0021',
            }
            
            # Convertir nombre de sucursal a código si es necesario
            sucursal_codigo = sucursal
            if sucursal and sucursal.upper() in NOMBRE_A_CODIGO_SUCURSAL:
                sucursal_codigo = NOMBRE_A_CODIGO_SUCURSAL[sucursal.upper()]
                logging.info(f"Precios Constantes MPRO: Traduciendo sucursal '{sucursal}' -> '{sucursal_codigo}'")
            
            # Filtro de sucursal - en MPRO se relaciona venta con sucursal
            filtro_sucursal = f"AND V.Sc_Cve_Sucursal = '{sucursal_codigo}'" if sucursal != 'all' and sucursal_codigo else ""
            filtro_sucursal_ve = f"AND VE.Sc_Cve_Sucursal = '{sucursal_codigo}'" if sucursal != 'all' and sucursal_codigo else ""
            
            # PASO 1: Obtener VENTAS REALES del período (misma lógica que Dashboard)
            # Esto asegura que los totales coincidan con el Tablero Ejecutivo
            query_ventas_reales_mpro = f"""
SELECT ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas_reales
FROM Venta_Encabezado VE
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{fecha_ini_actual} 00:00:00', 120)
  AND VE.Vn_Fecha <= CONVERT(datetime, '{fecha_fin_actual} 23:59:59', 120)
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {filtro_sucursal_ve}
"""
            result_ventas_reales = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_reales_mpro
            )
            ventas_reales_periodo = float(result_ventas_reales[0]['ventas_reales'] or 0) if result_ventas_reales else 0
            
            query_ventas_actual = f"""
SELECT 
    V.Pr_Cve_Producto as producto_id,
    P.Pr_Descripcion as producto,
    ISNULL(S.Sc_Descripcion, 'Sin Sucursal') as categoria,
    'Productos' as familia,
    SUM(V.Vn_Cantidad_Control_1) as cantidad,
    SUM(V.Vn_Precio_Lista * V.Vn_Cantidad_Control_1) as importe_actual,
    AVG(V.Vn_Precio_Lista) as precio_promedio_actual
FROM venta V
INNER JOIN Producto P ON P.Pr_Cve_Producto = V.Pr_Cve_Producto
LEFT JOIN sucursal S ON S.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
WHERE V.Vn_Fecha >= CONVERT(datetime, '{fecha_ini_actual} 00:00:00', 120)
  AND V.Vn_Fecha <= CONVERT(datetime, '{fecha_fin_actual} 23:59:59', 120)
  AND ISNULL(V.Es_Cve_Estado, '') <> 'CA'
  AND V.Vn_Cantidad_Control_1 > 0
  {filtro_sucursal}
GROUP BY V.Pr_Cve_Producto, P.Pr_Descripcion, S.Sc_Descripcion
"""
            
            query_precios_base = f"""
SELECT 
    V.Pr_Cve_Producto as producto_id,
    AVG(V.Vn_Precio_Lista) as precio_promedio_base
FROM venta V
WHERE V.Vn_Fecha >= CONVERT(datetime, '{fecha_ini_base} 00:00:00', 120)
  AND V.Vn_Fecha <= CONVERT(datetime, '{fecha_fin_base} 23:59:59', 120)
  AND ISNULL(V.Es_Cve_Estado, '') <> 'CA'
  AND V.Vn_Cantidad_Control_1 > 0
  {filtro_sucursal}
GROUP BY V.Pr_Cve_Producto
"""
            
            # Ejecutar queries
            ventas_actual = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_actual
            ) or []
            
            precios_base = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_precios_base
            ) or []
            
            # VALIDACIÓN (Abril 2026): Si no hay datos en el período base, no se puede hacer análisis
            # porque no hay precios de referencia con los cuales comparar
            if not precios_base or len(precios_base) == 0:
                logging.warning(f"Precios Constantes MPRO {server['name']}: Sin datos en período base {periodo_base}")
                return {
                    "servidor": server['name'],
                    "system_type": server['system_type'],
                    "periodo_actual": periodo_actual,
                    "periodo_base": periodo_base,
                    "granularidad": granularidad,
                    "error": f"Sin datos de ventas en el período base ({periodo_base}). No es posible calcular precios constantes sin un período de referencia con ventas.",
                    "kpis": {
                        "ventas_actuales": ventas_reales_periodo,
                        "ventas_constantes": 0,
                        "efecto_precio": 0,
                        "efecto_inflacion_pct": 0,
                        "variacion_real_pct": 0,
                        "productos_analizados": 0,
                        "productos_nuevos": 0,
                        "productos_descontinuados": 0
                    },
                    "datos": [],
                    "detalle_productos": None
                }
            
            # Crear diccionario de precios base
            precios_base_dict = {str(p['producto_id']): float(p['precio_promedio_base'] or 0) for p in precios_base}
            
            # PASO 2: Calcular suma de productos para obtener factor de ajuste
            suma_productos_actual = sum(float(v['importe_actual'] or 0) for v in ventas_actual)
            
            # Factor de ajuste: ventas reales / suma de productos
            factor_ajuste = ventas_reales_periodo / suma_productos_actual if suma_productos_actual > 0 else 1
            logging.info(f"MPRO - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
            
            productos_detalle = []
            total_actual = 0
            total_constante = 0
            
            for venta in ventas_actual:
                producto_id = str(venta['producto_id'])
                cantidad = float(venta['cantidad'] or 0)
                precio_actual = float(venta['precio_promedio_actual'] or 0)
                # Aplicar factor de ajuste al importe para que coincida con ventas reales
                importe_actual = float(venta['importe_actual'] or 0) * factor_ajuste
                
                if producto_id in precios_base_dict:
                    precio_base = precios_base_dict[producto_id]
                    es_nuevo = False
                else:
                    precio_base = precio_actual
                    es_nuevo = True
                
                # El importe constante también debe ajustarse con el factor
                importe_constante = (cantidad * precio_base) * factor_ajuste
                efecto_precio = importe_actual - importe_constante
                variacion_precio_pct = ((precio_actual - precio_base) / precio_base * 100) if precio_base > 0 else 0
                
                productos_detalle.append({
                    'producto_id': producto_id,
                    'producto': venta['producto'],
                    'categoria': venta['categoria'],
                    'familia': venta['familia'],
                    'cantidad': cantidad,
                    'precio_actual': precio_actual,
                    'precio_base': precio_base,
                    'importe_actual': importe_actual,
                    'importe_constante': importe_constante,
                    'efecto_precio': efecto_precio,
                    'variacion_precio_pct': round(variacion_precio_pct, 2),
                    'es_nuevo': es_nuevo,
                    'es_descontinuado': False
                })
                
                total_actual += importe_actual
                total_constante += importe_constante
            
            # Agrupar según granularidad (mismo código)
            if granularidad == 'categoria':
                agrupado = {}
                for p in productos_detalle:
                    key = p['categoria']
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            elif granularidad == 'familia':
                agrupado = {}
                for p in productos_detalle:
                    key = f"{p['categoria']} > {p['familia']}"
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'categoria': p['categoria'],
                            'familia': p['familia'],
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            else:
                datos_agrupados = sorted(productos_detalle, key=lambda x: x['importe_actual'], reverse=True)
            
            efecto_precio_total = total_actual - total_constante
            variacion_real = round(((total_constante - total_actual) / total_actual * 100), 2) if total_actual > 0 else 0
            efecto_inflacion_pct = round((efecto_precio_total / total_constante * 100), 2) if total_constante > 0 else 0
            
            return {
                'servidor': server['name'],
                'system_type': server['system_type'],
                'periodo_actual': periodo_actual,
                'periodo_base': periodo_base,
                'granularidad': granularidad,
                'kpis': {
                    'ventas_actuales': round(total_actual, 2),
                    'ventas_constantes': round(total_constante, 2),
                    'efecto_precio': round(efecto_precio_total, 2),
                    'efecto_inflacion_pct': efecto_inflacion_pct,
                    'variacion_real_pct': variacion_real,
                    'productos_analizados': len([p for p in productos_detalle if not p['es_descontinuado']]),
                    'productos_nuevos': len([p for p in productos_detalle if p.get('es_nuevo')]),
                    'productos_descontinuados': len([p for p in productos_detalle if p.get('es_descontinuado')])
                },
                'datos': datos_agrupados,
                'detalle_productos': productos_detalle if granularidad == 'producto' else None
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Sistema no soportado: {server['system_type']}")
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error en precios constantes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-4H (Abril 2026)
# ============================================================================
```
## Detección técnica backend
```text
Función: ventas_precios_constantes
execute_sql_query: True
pymssql.connect: False
pyodbc.connect: False
pytds.connect: False
SoftRestaurant: True
MPRO: True
server_id: True
EDARSAHUB_SQL: True
GUARD_RAIL: True

Conteo execute_sql_query: 6

Tablas detectadas FROM/JOIN:
- Producto
- Venta_Encabezado
- cheqdet
- cheques
- productos
- sucursal
- turnos
- venta
```
## Consumidores frontend
```text
```
/app/frontend/src/pages/Comercial.js:2103:      const response = await api.get(`/comercial/precios-constantes/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:2126:        const responseAnterior = await api.get(`/comercial/precios-constantes/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:2167:          const res = await api.get(`/comercial/precios-constantes/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:2207:    <div className="space-y-4" data-testid="precios-constantes">
```
## Contexto Comercial.js
```jsx
2098-        // Manual: selección libre
2099-        pActual = mesesActual.map(m => `${anioActual}-${String(m).padStart(2, '0')}`).join(',');
2100-        pBase = mesesBase.map(m => `${anioBase}-${String(m).padStart(2, '0')}`).join(',');
2101-      }
2102-      
2103:      const response = await api.get(`/comercial/precios-constantes/${selectedServer}`, {
2104-        params: {
2105-          periodo_actual: pActual,
2106-          periodo_base: pBase,
2107-          granularidad: granularidad,
2108-          sucursal: localSucursal
2109-        }
2110-      });
2111-      
2112-      // Verificar si hay error en la respuesta (ej: sin datos en período base)
2113-      if (response.data.error) {
2114-        setError(response.data.error);
2115-        setData(response.data); // Mantener los KPIs vacíos para mostrar la UI correctamente
2116-      } else {
2117-        setError(null);
2118-        setData(response.data);
--
2121-      // Cargar datos del año anterior para comparar crecimiento real
2122-      const pAnioAnterior = mesesActual.map(m => `${anioActual - 1}-${String(m).padStart(2, '0')}`).join(',');
2123-      const pBaseAnterior = mesesActual.map(m => `${anioActual - 2}-${String(m).padStart(2, '0')}`).join(',');
2124-      
2125-      try {
2126:        const responseAnterior = await api.get(`/comercial/precios-constantes/${selectedServer}`, {
2127-          params: {
2128-            periodo_actual: pAnioAnterior,
2129-            periodo_base: pBaseAnterior,
2130-            granularidad: 'categoria',
2131-            sucursal: localSucursal
2132-          }
2133-        });
2134-        setDataAnioAnterior(responseAnterior.data);
2135-      } catch (e) {
2136-        logger.log('No hay datos del año anterior');
2137-        setDataAnioAnterior(null);
2138-      }
2139-      
2140-      // Cargar serie histórica de 5 años
2141-      cargarSerieHistorica();
--
2162-        const anio = anioActual - 4 + i; // Del -4 al actual
2163-        const pPeriodo = mesesActual.map(m => `${anio}-${String(m).padStart(2, '0')}`).join(',');
2164-        const pRef = mesesActual.map(m => `${anioBase}-${String(m).padStart(2, '0')}`).join(',');
2165-        
2166-        try {
2167:          const res = await api.get(`/comercial/precios-constantes/${selectedServer}`, {
2168-            params: {
2169-              periodo_actual: pPeriodo,
2170-              periodo_base: pRef,
2171-              granularidad: 'categoria',
2172-              sucursal: localSucursal
2173-            }
2174-          });
2175-          
2176-          serie.push({
2177-            anio: anio,
2178-            ventas_actuales: res.data.kpis?.ventas_actuales || 0,
2179-            ventas_constantes: res.data.kpis?.ventas_constantes || 0,
2180-            efecto_precio: res.data.kpis?.efecto_precio || 0
2181-          });
2182-        } catch (e) {
--
2202-    if (valor < 0) return 'text-green-600';
2203-    return 'text-zinc-600';
2204-  };
2205-
2206-  return (
2207:    <div className="space-y-4" data-testid="precios-constantes">
2208-      {/* Filtros */}
2209-      <Card>
2210-        <CardHeader className="pb-3">
2211-          <CardTitle className="text-lg flex items-center gap-2">
2212-            <Scale className="h-5 w-5 text-blue-600" />
2213-            Análisis de Ventas a Precios Constantes
2214-          </CardTitle>
2215-          <p className="text-sm text-zinc-500">
```
## GUARD_RAIL existente
```text
=== GUARD RAIL ENCONTRADO ===
# FASE A-P0: GUARD RAIL LIVE
    guard_result = check_live_guard_rail('/comercial/precios-constantes', server_id)
    if guard_result:
        return {
            "source_status": guard_result['source_status'],
            "source_message": guard_result['source_message'],
            "periodo_actual": periodo_actual,
            "periodo_base": periodo_base,
            "granularidad": granularidad,
            "data": [],
            "resumen": {
                "ventas_reales": 0,
                "ventas_constantes": 0,
                "variacion_real": 0,
                "variacion_volumen": 0,
                "inflacion_implicita": 0
            }
        }
    
    # CÓDIGO LEGACY

Retorna source_status: SÍ
```
```

## Hallazgo Crítico

El endpoint **ya tiene implementado un GUARD RAIL** mediante `check_live_guard_rail()`.

Sin embargo, el guard rail **NO está activo por defecto**. Requiere:
```python
ENABLE_LIVE_GUARD_RAIL = True
```

Cuando el guard rail está activo, el endpoint retorna:
```json
{
    "source_status": "SIN_DATOS_LIVE_BLOQUEADO",
    "source_message": "...",
    "data": [],
    "resumen": {...KPIs en cero...}
}
```

## Dictamen

### Opción A: Activar GUARD RAIL inmediatamente
- Ventaja: Bloquea conexión live de inmediato
- Desventaja: Comercial.js mostraría "Sin datos" hasta crear sync

### Opción B: Crear tabla SQL-first primero, luego activar GUARD RAIL
- Ventaja: No rompe funcionalidad visual
- Desventaja: Requiere más trabajo antes de bloquear live

### Recomendación: Opción B

1. Crear `Sync_Ventas_Precios_Historicos` en EDARSAHUB SQL
2. Crear job `sync_ventas_precios_historicos.py` 
3. Poblar tabla con backfill
4. Modificar endpoint para leer de EDARSAHUB
5. Activar GUARD RAIL como fallback

## Archivos generados

```text
/app/docs/reports/AUDITORIA_ENDPOINT_PRECIOS_CONSTANTES_COMERCIAL.md
/app/docs/audits/auditoria_endpoint_precios_constantes_comercial.json
```
