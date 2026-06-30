# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-30T04:59:35.443289
- Modo: `validate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/Users/ricardobalamgarcia/Documents/v1.0/EDARSA_HUB_work/backend/database/validation/phase3_comercial_kpi_cross_menu_source_audit.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 9
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: Comando
- Filas afectadas: -1

### Batch 2
- Tipo: SELECT
- Columnas: database_name, fecha_ejecucion, auditoria, modo, rango_base
- Filas: 1
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'fecha_ejecucion': datetime.datetime(2026, 6, 30, 4, 59, 33, 131236), 'auditoria': 'phase3_comercial_kpi_cross_menu_source_audit', 'modo': 'READ_ONLY', 'rango_base': 'Ultimos 30 dias cerrados segun vw_Comercial_KPIs_Diarios_v2_Runtime'}
```

### Batch 3
- Tipo: SELECT
- Columnas: objeto, type_desc, create_date, modify_date, estado
- Filas: 7
- Preview (primeras 20 filas):
```
  {'objeto': 'Comercial_Inteligencia_VentasDetalleProducto', 'type_desc': 'USER_TABLE', 'create_date': datetime.datetime(2026, 6, 2, 3, 51, 23, 130000), 'modify_date': datetime.datetime(2026, 6, 2, 3, 51, 23, 283000), 'estado': 'OK'}
  {'objeto': 'Comercial_KPIs_Diarios_v2', 'type_desc': 'USER_TABLE', 'create_date': datetime.datetime(2026, 5, 1, 10, 39, 18, 780000), 'modify_date': datetime.datetime(2026, 6, 5, 17, 41, 38, 413000), 'estado': 'OK'}
  {'objeto': 'Comercial_Ventas_Dia_Abiertas_v2', 'type_desc': 'USER_TABLE', 'create_date': datetime.datetime(2026, 5, 1, 10, 39, 18, 957000), 'modify_date': datetime.datetime(2026, 5, 1, 10, 39, 18, 960000), 'estado': 'OK'}
  {'objeto': 'Sync_PAX_Detalle', 'type_desc': 'USER_TABLE', 'create_date': datetime.datetime(2026, 5, 25, 20, 53, 38, 560000), 'modify_date': datetime.datetime(2026, 5, 25, 20, 53, 38, 560000), 'estado': 'OK'}
  {'objeto': 'Sync_Sales', 'type_desc': 'USER_TABLE', 'create_date': datetime.datetime(2026, 5, 31, 20, 51, 46, 260000), 'modify_date': datetime.datetime(2026, 6, 11, 0, 5, 56, 850000), 'estado': 'OK'}
  {'objeto': 'Unidades_Negocio', 'type_desc': 'USER_TABLE', 'create_date': datetime.datetime(2026, 4, 24, 19, 25, 42, 697000), 'modify_date': datetime.datetime(2026, 4, 24, 19, 25, 42, 720000), 'estado': 'OK'}
  {'objeto': 'vw_Comercial_KPIs_Diarios_v2_Runtime', 'type_desc': 'VIEW', 'create_date': datetime.datetime(2026, 6, 5, 10, 12, 1, 80000), 'modify_date': datetime.datetime(2026, 6, 5, 10, 12, 1, 80000), 'estado': 'OK'}
```

### Batch 4
- Tipo: SELECT
- Columnas: menu, endpoints_clave, fuente_principal, ventas_kpi, regla_promedios, riesgo
- Filas: 3
- Preview (primeras 20 filas):
```
  {'menu': 'Tablero Ejecutivo', 'endpoints_clave': '/api/v2/comercial/dashboard, /api/v2/comercial/kpis-diarios', 'fuente_principal': 'vw_Comercial_KPIs_Diarios_v2_Runtime', 'ventas_kpi': 'ventas_sin_propina para backend v2; algunas vistas frontend aun usan nombre ventas_total', 'regla_promedios': 'cheque_promedio = ventas / tickets; ticket_promedio canonico = ventas / pax', 'riesgo': 'Revisar nombres heredados ticket_promedio/pax_promedio'}
  {'menu': 'Comercial', 'endpoints_clave': '/api/comercial/dashboard/{server_id}', 'fuente_principal': 'Servicio comercial SQL-first; debe converger a vw_Comercial_KPIs_Diarios_v2_Runtime', 'ventas_kpi': 'ventas_sin_propina preferida; legacy puede exponer ventas_periodo', 'regla_promedios': 'legacy usa ticket_promedio como ventas / tickets', 'riesgo': 'Nomenclatura legacy puede diferir de Inteligencia'}
  {'menu': 'Inteligencia Comercial', 'endpoints_clave': '/api/inteligencia/dashboard, /api/reporteador-bi/*, /api/inteligencia/iscam/*', 'fuente_principal': 'KPI view + Comercial_Inteligencia_VentasDetalleProducto + Sync_Sales + Sync_PAX_Detalle', 'ventas_kpi': 'dashboard usa ventas_sin_propina; ISCAM usa MontoTotal', 'regla_promedios': 'dashboard canonico: ticket = ventas / pax, cheque = ventas / tickets', 'riesgo': 'Mezcla vista agregada, detalle por producto y Sync_Sales'}
```

### Batch 5
- Tipo: SELECT
- Columnas: fecha_inicio_audit, fecha_fin_audit, fuente, registros, unidades, dias, fecha_minima, fecha_maxima, dias_retraso_vs_kpi, ultima_sync, ventas_netas, ventas_brutas, tickets, pax
- Filas: 4
- Preview (primeras 20 filas):
```
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'fuente': 'INTEL_DETALLE', 'registros': 16400, 'unidades': 5, 'dias': 8, 'fecha_minima': datetime.date(2026, 5, 30), 'fecha_maxima': datetime.date(2026, 6, 6), 'dias_retraso_vs_kpi': 23, 'ultima_sync': datetime.datetime(2026, 6, 9, 5, 20, 35, 356469), 'ventas_netas': Decimal('4415283.33'), 'ventas_brutas': Decimal('4415283.33'), 'tickets': 1543, 'pax': None}
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'fuente': 'KPI_RUNTIME', 'registros': 155, 'unidades': 5, 'dias': 31, 'fecha_minima': datetime.date(2026, 5, 30), 'fecha_maxima': datetime.date(2026, 6, 29), 'dias_retraso_vs_kpi': 0, 'ultima_sync': datetime.datetime(2026, 6, 30, 10, 39, 53, 324285), 'ventas_netas': Decimal('16746021.78'), 'ventas_brutas': Decimal('17796325.74'), 'tickets': 6042, 'pax': Decimal('17368.00')}
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'fuente': 'SYNC_PAX_DETALLE', 'registros': 0, 'unidades': 0, 'dias': 0, 'fecha_minima': None, 'fecha_maxima': None, 'dias_retraso_vs_kpi': None, 'ultima_sync': None, 'ventas_netas': None, 'ventas_brutas': None, 'tickets': 0, 'pax': None}
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'fuente': 'SYNC_SALES', 'registros': 1572, 'unidades': 5, 'dias': 8, 'fecha_minima': datetime.date(2026, 5, 30), 'fecha_maxima': datetime.date(2026, 6, 6), 'dias_retraso_vs_kpi': 23, 'ultima_sync': datetime.datetime(2026, 6, 7, 21, 0, 30, 813333), 'ventas_netas': Decimal('4614153.57'), 'ventas_brutas': Decimal('4614153.57'), 'tickets': 1572, 'pax': Decimal('3644.00')}
```

### Batch 6
- Tipo: SELECT
- Columnas: fecha_inicio_audit, fecha_fin_audit, unidad_negocio_id, unidad_negocio_nombre, sistema_origen, dias_kpi, dias_detalle, dias_sync_sales, kpi_ventas_netas, detalle_ventas_netas, diff_kpi_neto_vs_detalle, pct_diff_detalle_neto, kpi_ventas_brutas, sync_sales_ventas, diff_sync_sales_vs_kpi_bruto, pct_diff_sync_sales_bruto, kpi_tickets, detalle_tickets, sync_sales_tickets, kpi_pax, detalle_pax, sync_sales_pax, hallazgo
- Filas: 5
- Preview (primeras 20 filas):
```
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'unidad_negocio_id': '130QRO', 'unidad_negocio_nombre': '130° QUERETARO', 'sistema_origen': 'MPRO', 'dias_kpi': 31, 'dias_detalle': 8, 'dias_sync_sales': 8, 'kpi_ventas_netas': Decimal('4197207.00'), 'detalle_ventas_netas': Decimal('908115.0000'), 'diff_kpi_neto_vs_detalle': Decimal('3289092.00'), 'pct_diff_detalle_neto': Decimal('-78.363800'), 'kpi_ventas_brutas': Decimal('4197207.00'), 'sync_sales_ventas': Decimal('1085215.00'), 'diff_sync_sales_vs_kpi_bruto': Decimal('-3111992.00'), 'pct_diff_sync_sales_bruto': Decimal('-74.144300'), 'kpi_tickets': 820, 'detalle_tickets': 193, 'sync_sales_tickets': 206, 'kpi_pax': 2418, 'detalle_pax': 207, 'sync_sales_pax': 220, 'hallazgo': 'KPI_NETO_VS_DETALLE_DIFIERE'}
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'unidad_negocio_id': 'CIENFUEGOS', 'unidad_negocio_nombre': 'CIENFUEGOS', 'sistema_origen': 'SOFTRESTAURANT', 'dias_kpi': 31, 'dias_detalle': 6, 'dias_sync_sales': 6, 'kpi_ventas_netas': Decimal('3923095.28'), 'detalle_ventas_netas': Decimal('1007202.6671'), 'diff_kpi_neto_vs_detalle': Decimal('2915892.61'), 'pct_diff_detalle_neto': Decimal('-74.326300'), 'kpi_ventas_brutas': Decimal('4329099.00'), 'sync_sales_ventas': Decimal('1004904.00'), 'diff_sync_sales_vs_kpi_bruto': Decimal('-3324195.00'), 'pct_diff_sync_sales_bruto': Decimal('-76.787200'), 'kpi_tickets': 1149, 'detalle_tickets': 248, 'sync_sales_tickets': 248, 'kpi_pax': 3431, 'detalle_pax': 834, 'sync_sales_pax': 834, 'hallazgo': 'KPI_NETO_VS_DETALLE_DIFIERE'}
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'unidad_negocio_id': '130MID', 'unidad_negocio_nombre': '130° MERIDA', 'sistema_origen': 'SOFTRESTAURANT', 'dias_kpi': 31, 'dias_detalle': 8, 'dias_sync_sales': 8, 'kpi_ventas_netas': Decimal('3447042.35'), 'detalle_ventas_netas': Decimal('981633.4356'), 'diff_kpi_neto_vs_detalle': Decimal('2465408.91'), 'pct_diff_detalle_neto': Decimal('-71.522400'), 'kpi_ventas_brutas': Decimal('3850341.00'), 'sync_sales_ventas': Decimal('978441.00'), 'diff_sync_sales_vs_kpi_bruto': Decimal('-2871900.00'), 'pct_diff_sync_sales_bruto': Decimal('-74.588100'), 'kpi_tickets': 861, 'detalle_tickets': 224, 'sync_sales_tickets': 224, 'kpi_pax': 2423, 'detalle_pax': 624, 'sync_sales_pax': 624, 'hallazgo': 'KPI_NETO_VS_DETALLE_DIFIERE'}
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'unidad_negocio_id': 'ORIGEN', 'unidad_negocio_nombre': 'ORIGEN', 'sistema_origen': 'MPRO', 'dias_kpi': 31, 'dias_detalle': 8, 'dias_sync_sales': 8, 'kpi_ventas_netas': Decimal('2393369.74'), 'detalle_ventas_netas': Decimal('560462.2245'), 'diff_kpi_neto_vs_detalle': Decimal('1832907.52'), 'pct_diff_detalle_neto': Decimal('-76.582700'), 'kpi_ventas_brutas': Decimal('2393369.74'), 'sync_sales_ventas': Decimal('599694.57'), 'diff_sync_sales_vs_kpi_bruto': Decimal('-1793675.17'), 'pct_diff_sync_sales_bruto': Decimal('-74.943500'), 'kpi_tickets': 1100, 'detalle_tickets': 265, 'sync_sales_tickets': 281, 'kpi_pax': 3325, 'detalle_pax': 303, 'sync_sales_pax': 319, 'hallazgo': 'KPI_NETO_VS_DETALLE_DIFIERE'}
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'unidad_negocio_id': 'ESTELAR', 'unidad_negocio_nombre': 'LA ESTELAR', 'sistema_origen': 'SOFTRESTAURANT', 'dias_kpi': 31, 'dias_detalle': 8, 'dias_sync_sales': 8, 'kpi_ventas_netas': Decimal('2785307.41'), 'detalle_ventas_netas': Decimal('957870.0000'), 'diff_kpi_neto_vs_detalle': Decimal('1827437.41'), 'pct_diff_detalle_neto': Decimal('-65.609900'), 'kpi_ventas_brutas': Decimal('3026309.00'), 'sync_sales_ventas': Decimal('945899.00'), 'diff_sync_sales_vs_kpi_bruto': Decimal('-2080410.00'), 'pct_diff_sync_sales_bruto': Decimal('-68.744100'), 'kpi_tickets': 2112, 'detalle_tickets': 613, 'sync_sales_tickets': 613, 'kpi_pax': 5771, 'detalle_pax': 1647, 'sync_sales_pax': 1647, 'hallazgo': 'KPI_NETO_VS_DETALLE_DIFIERE'}
```

### Batch 7
- Tipo: SELECT
- Columnas: unidad_negocio_id, unidad_negocio_nombre, fecha_operacion, ventas_sin_propina, ventas_total, propinas_total, tickets_total, pax_total, ticket_promedio_guardado, cheque_promedio_neto_calc, ticket_promedio_canonico_calc, pax_promedio_guardado, pax_por_cheque_calc, delta_ticket_vs_cheque_neto, delta_ticket_vs_ticket_canonico, delta_paxprom_vs_ticket_canonico, delta_paxprom_vs_pax_por_cheque, hallazgo_ticket_promedio, hallazgo_pax_promedio
- Filas: 100
- Preview (primeras 20 filas):
```
  {'unidad_negocio_id': '130MID', 'unidad_negocio_nombre': '130° MERIDA', 'fecha_operacion': datetime.date(2026, 6, 29), 'ventas_sin_propina': Decimal('48473.30'), 'ventas_total': Decimal('55393.00'), 'propinas_total': Decimal('6919.70'), 'tickets_total': 14, 'pax_total': 41, 'ticket_promedio_guardado': Decimal('3956.640000'), 'cheque_promedio_neto_calc': Decimal('3462.378571'), 'ticket_promedio_canonico_calc': Decimal('1182.275609'), 'pax_promedio_guardado': Decimal('2.930000'), 'pax_por_cheque_calc': Decimal('2.928571428571428'), 'delta_ticket_vs_cheque_neto': Decimal('494.261429'), 'delta_ticket_vs_ticket_canonico': Decimal('2774.364391'), 'delta_paxprom_vs_ticket_canonico': Decimal('1179.345609'), 'delta_paxprom_vs_pax_por_cheque': Decimal('0.001429'), 'hallazgo_ticket_promedio': 'CAMPO_TICKET_PROMEDIO_NO_CUADRA', 'hallazgo_pax_promedio': 'CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE'}
  {'unidad_negocio_id': '130QRO', 'unidad_negocio_nombre': '130° QUERETARO', 'fecha_operacion': datetime.date(2026, 6, 29), 'ventas_sin_propina': Decimal('101273.00'), 'ventas_total': Decimal('101273.00'), 'propinas_total': Decimal('0.00'), 'tickets_total': 17, 'pax_total': 56, 'ticket_promedio_guardado': Decimal('5957.240000'), 'cheque_promedio_neto_calc': Decimal('5957.235294'), 'ticket_promedio_canonico_calc': Decimal('1808.446428'), 'pax_promedio_guardado': Decimal('3.290000'), 'pax_por_cheque_calc': Decimal('3.294117647058823'), 'delta_ticket_vs_cheque_neto': Decimal('0.004706'), 'delta_ticket_vs_ticket_canonico': Decimal('4148.793572'), 'delta_paxprom_vs_ticket_canonico': Decimal('1805.156428'), 'delta_paxprom_vs_pax_por_cheque': Decimal('0.004118'), 'hallazgo_ticket_promedio': 'CAMPO_TICKET_PROMEDIO_ES_CHEQUE_PROMEDIO', 'hallazgo_pax_promedio': 'CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE'}
  {'unidad_negocio_id': 'CIENFUEGOS', 'unidad_negocio_nombre': 'CIENFUEGOS', 'fecha_operacion': datetime.date(2026, 6, 29), 'ventas_sin_propina': Decimal('57670.30'), 'ventas_total': Decimal('64205.00'), 'propinas_total': Decimal('6534.70'), 'tickets_total': 23, 'pax_total': 59, 'ticket_promedio_guardado': Decimal('2791.520000'), 'cheque_promedio_neto_calc': Decimal('2507.404347'), 'ticket_promedio_canonico_calc': Decimal('977.462711'), 'pax_promedio_guardado': Decimal('2.570000'), 'pax_por_cheque_calc': Decimal('2.565217391304347'), 'delta_ticket_vs_cheque_neto': Decimal('284.115653'), 'delta_ticket_vs_ticket_canonico': Decimal('1814.057289'), 'delta_paxprom_vs_ticket_canonico': Decimal('974.892711'), 'delta_paxprom_vs_pax_por_cheque': Decimal('0.004783'), 'hallazgo_ticket_promedio': 'CAMPO_TICKET_PROMEDIO_NO_CUADRA', 'hallazgo_pax_promedio': 'CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE'}
  {'unidad_negocio_id': 'ESTELAR', 'unidad_negocio_nombre': 'LA ESTELAR', 'fecha_operacion': datetime.date(2026, 6, 29), 'ventas_sin_propina': Decimal('24309.00'), 'ventas_total': Decimal('27250.00'), 'propinas_total': Decimal('2941.00'), 'tickets_total': 24, 'pax_total': 58, 'ticket_promedio_guardado': Decimal('1135.420000'), 'cheque_promedio_neto_calc': Decimal('1012.875000'), 'ticket_promedio_canonico_calc': Decimal('419.120689'), 'pax_promedio_guardado': Decimal('2.420000'), 'pax_por_cheque_calc': Decimal('2.416666666666666'), 'delta_ticket_vs_cheque_neto': Decimal('122.545000'), 'delta_ticket_vs_ticket_canonico': Decimal('716.299311'), 'delta_paxprom_vs_ticket_canonico': Decimal('416.700689'), 'delta_paxprom_vs_pax_por_cheque': Decimal('0.003333'), 'hallazgo_ticket_promedio': 'CAMPO_TICKET_PROMEDIO_NO_CUADRA', 'hallazgo_pax_promedio': 'CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE'}
  {'unidad_negocio_id': 'ORIGEN', 'unidad_negocio_nombre': 'ORIGEN', 'fecha_operacion': datetime.date(2026, 6, 29), 'ventas_sin_propina': Decimal('22446.86'), 'ventas_total': Decimal('22446.86'), 'propinas_total': Decimal('0.00'), 'tickets_total': 20, 'pax_total': 44, 'ticket_promedio_guardado': Decimal('1122.340000'), 'cheque_promedio_neto_calc': Decimal('1122.343000'), 'ticket_promedio_canonico_calc': Decimal('510.155909'), 'pax_promedio_guardado': Decimal('2.200000'), 'pax_por_cheque_calc': Decimal('2.200000000000000'), 'delta_ticket_vs_cheque_neto': Decimal('0.003000'), 'delta_ticket_vs_ticket_canonico': Decimal('612.184091'), 'delta_paxprom_vs_ticket_canonico': Decimal('507.955909'), 'delta_paxprom_vs_pax_por_cheque': Decimal('0.000000'), 'hallazgo_ticket_promedio': 'CAMPO_TICKET_PROMEDIO_ES_CHEQUE_PROMEDIO', 'hallazgo_pax_promedio': 'CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE'}
  {'unidad_negocio_id': '130MID', 'unidad_negocio_nombre': '130° MERIDA', 'fecha_operacion': datetime.date(2026, 6, 28), 'ventas_sin_propina': Decimal('115691.66'), 'ventas_total': Decimal('133004.00'), 'propinas_total': Decimal('17312.34'), 'tickets_total': 31, 'pax_total': 89, 'ticket_promedio_guardado': Decimal('4290.450000'), 'cheque_promedio_neto_calc': Decimal('3731.989032'), 'ticket_promedio_canonico_calc': Decimal('1299.906292'), 'pax_promedio_guardado': Decimal('2.870000'), 'pax_por_cheque_calc': Decimal('2.870967741935483'), 'delta_ticket_vs_cheque_neto': Decimal('558.460968'), 'delta_ticket_vs_ticket_canonico': Decimal('2990.543708'), 'delta_paxprom_vs_ticket_canonico': Decimal('1297.036292'), 'delta_paxprom_vs_pax_por_cheque': Decimal('0.000968'), 'hallazgo_ticket_promedio': 'CAMPO_TICKET_PROMEDIO_NO_CUADRA', 'hallazgo_pax_promedio': 'CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE'}
  {'unidad_negocio_id': '130QRO', 'unidad_negocio_nombre': '130° QUERETARO', 'fecha_operacion': datetime.date(2026, 6, 28), 'ventas_sin_propina': Decimal('57620.00'), 'ventas_total': Decimal('57620.00'), 'propinas_total': Decimal('0.00'), 'tickets_total': 14, 'pax_total': 43, 'ticket_promedio_guardado': Decimal('4115.710000'), 'cheque_promedio_neto_calc': Decimal('4115.714285'), 'ticket_promedio_canonico_calc': Decimal('1340.000000'), 'pax_promedio_guardado': Decimal('3.070000'), 'pax_por_cheque_calc': Decimal('3.071428571428571'), 'delta_ticket_vs_cheque_neto': Decimal('0.004285'), 'delta_ticket_vs_ticket_canonico': Decimal('2775.710000'), 'delta_paxprom_vs_ticket_canonico': Decimal('1336.930000'), 'delta_paxprom_vs_pax_por_cheque': Decimal('0.001429'), 'hallazgo_ticket_promedio': 'CAMPO_TICKET_PROMEDIO_ES_CHEQUE_PROMEDIO', 'hallazgo_pax_promedio': 'CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE'}
  {'unidad_negocio_id': 'CIENFUEGOS', 'unidad_negocio_nombre': 'CIENFUEGOS', 'fecha_operacion': datetime.date(2026, 6, 28), 'ventas_sin_propina': Decimal('69202.25'), 'ventas_total': Decimal('74004.00'), 'propinas_total': Decimal('4801.75'), 'tickets_total': 20, 'pax_total': 65, 'ticket_promedio_guardado': Decimal('3700.200000'), 'cheque_promedio_neto_calc': Decimal('3460.112500'), 'ticket_promedio_canonico_calc': Decimal('1064.650000'), 'pax_promedio_guardado': Decimal('3.250000'), 'pax_por_cheque_calc': Decimal('3.250000000000000'), 'delta_ticket_vs_cheque_neto': Decimal('240.087500'), 'delta_ticket_vs_ticket_canonico': Decimal('2635.550000'), 'delta_paxprom_vs_ticket_canonico': Decimal('1061.400000'), 'delta_paxprom_vs_pax_por_cheque': Decimal('0.000000'), 'hallazgo_ticket_promedio': 'CAMPO_TICKET_PROMEDIO_NO_CUADRA', 'hallazgo_pax_promedio': 'CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE'}
  {'unidad_negocio_id': 'ESTELAR', 'unidad_negocio_nombre': 'LA ESTELAR', 'fecha_operacion': datetime.date(2026, 6, 28), 'ventas_sin_propina': Decimal('57419.50'), 'ventas_total': Decimal('62930.00'), 'propinas_total': Decimal('5510.50'), 'tickets_total': 65, 'pax_total': 156, 'ticket_promedio_guardado': Decimal('968.150000'), 'cheque_promedio_neto_calc': Decimal('883.376923'), 'ticket_promedio_canonico_calc': Decimal('368.073717'), 'pax_promedio_guardado': Decimal('2.400000'), 'pax_por_cheque_calc': Decimal('2.400000000000000'), 'delta_ticket_vs_cheque_neto': Decimal('84.773077'), 'delta_ticket_vs_ticket_canonico': Decimal('600.076283'), 'delta_paxprom_vs_ticket_canonico': Decimal('365.673717'), 'delta_paxprom_vs_pax_por_cheque': Decimal('0.000000'), 'hallazgo_ticket_promedio': 'CAMPO_TICKET_PROMEDIO_NO_CUADRA', 'hallazgo_pax_promedio': 'CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE'}
  {'unidad_negocio_id': 'ORIGEN', 'unidad_negocio_nombre': 'ORIGEN', 'fecha_operacion': datetime.date(2026, 6, 28), 'ventas_sin_propina': Decimal('24206.19'), 'ventas_total': Decimal('24206.19'), 'propinas_total': Decimal('0.00'), 'tickets_total': 14, 'pax_total': 42, 'ticket_promedio_guardado': Decimal('1729.010000'), 'cheque_promedio_neto_calc': Decimal('1729.013571'), 'ticket_promedio_canonico_calc': Decimal('576.337857'), 'pax_promedio_guardado': Decimal('3.000000'), 'pax_por_cheque_calc': Decimal('3.000000000000000'), 'delta_ticket_vs_cheque_neto': Decimal('0.003571'), 'delta_ticket_vs_ticket_canonico': Decimal('1152.672143'), 'delta_paxprom_vs_ticket_canonico': Decimal('573.337857'), 'delta_paxprom_vs_pax_por_cheque': Decimal('0.000000'), 'hallazgo_ticket_promedio': 'CAMPO_TICKET_PROMEDIO_ES_CHEQUE_PROMEDIO', 'hallazgo_pax_promedio': 'CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE'}
```

### Batch 8
- Tipo: SELECT
- Columnas: fecha_operacion, unidad_negocio_id, unidad_negocio_nombre, kpi_ventas_netas, detalle_ventas_netas, diff_ventas_netas, pct_diff_ventas_netas, kpi_tickets, detalle_tickets, diff_tickets, kpi_pax, detalle_pax, diff_pax, hallazgo
- Filas: 100
- Preview (primeras 20 filas):
```
  {'fecha_operacion': datetime.date(2026, 6, 20), 'unidad_negocio_id': '130QRO', 'unidad_negocio_nombre': '130° QUERETARO', 'kpi_ventas_netas': Decimal('254607.00'), 'detalle_ventas_netas': None, 'diff_ventas_netas': None, 'pct_diff_ventas_netas': None, 'kpi_tickets': 51, 'detalle_tickets': None, 'diff_tickets': None, 'kpi_pax': 153, 'detalle_pax': None, 'diff_pax': None, 'hallazgo': 'DIA_SIN_DETALLE_INTELIGENCIA'}
  {'fecha_operacion': datetime.date(2026, 6, 20), 'unidad_negocio_id': 'ESTELAR', 'unidad_negocio_nombre': 'LA ESTELAR', 'kpi_ventas_netas': Decimal('248813.19'), 'detalle_ventas_netas': None, 'diff_ventas_netas': None, 'pct_diff_ventas_netas': None, 'kpi_tickets': 152, 'detalle_tickets': None, 'diff_tickets': None, 'kpi_pax': 449, 'detalle_pax': None, 'diff_pax': None, 'hallazgo': 'DIA_SIN_DETALLE_INTELIGENCIA'}
  {'fecha_operacion': datetime.date(2026, 6, 20), 'unidad_negocio_id': 'CIENFUEGOS', 'unidad_negocio_nombre': 'CIENFUEGOS', 'kpi_ventas_netas': Decimal('247367.60'), 'detalle_ventas_netas': None, 'diff_ventas_netas': None, 'pct_diff_ventas_netas': None, 'kpi_tickets': 73, 'detalle_tickets': None, 'diff_tickets': None, 'kpi_pax': 168, 'detalle_pax': None, 'diff_pax': None, 'hallazgo': 'DIA_SIN_DETALLE_INTELIGENCIA'}
  {'fecha_operacion': datetime.date(2026, 6, 13), 'unidad_negocio_id': 'ESTELAR', 'unidad_negocio_nombre': 'LA ESTELAR', 'kpi_ventas_netas': Decimal('232655.19'), 'detalle_ventas_netas': None, 'diff_ventas_netas': None, 'pct_diff_ventas_netas': None, 'kpi_tickets': 161, 'detalle_tickets': None, 'diff_tickets': None, 'kpi_pax': 475, 'detalle_pax': None, 'diff_pax': None, 'hallazgo': 'DIA_SIN_DETALLE_INTELIGENCIA'}
  {'fecha_operacion': datetime.date(2026, 6, 21), 'unidad_negocio_id': 'ORIGEN', 'unidad_negocio_nombre': 'ORIGEN', 'kpi_ventas_netas': Decimal('225079.57'), 'detalle_ventas_netas': None, 'diff_ventas_netas': None, 'pct_diff_ventas_netas': None, 'kpi_tickets': 90, 'detalle_tickets': None, 'diff_tickets': None, 'kpi_pax': 332, 'detalle_pax': None, 'diff_pax': None, 'hallazgo': 'DIA_SIN_DETALLE_INTELIGENCIA'}
  {'fecha_operacion': datetime.date(2026, 6, 21), 'unidad_negocio_id': '130MID', 'unidad_negocio_nombre': '130° MERIDA', 'kpi_ventas_netas': Decimal('217196.76'), 'detalle_ventas_netas': None, 'diff_ventas_netas': None, 'pct_diff_ventas_netas': None, 'kpi_tickets': 53, 'detalle_tickets': None, 'diff_tickets': None, 'kpi_pax': 155, 'detalle_pax': None, 'diff_pax': None, 'hallazgo': 'DIA_SIN_DETALLE_INTELIGENCIA'}
  {'fecha_operacion': datetime.date(2026, 6, 27), 'unidad_negocio_id': 'ESTELAR', 'unidad_negocio_nombre': 'LA ESTELAR', 'kpi_ventas_netas': Decimal('210511.56'), 'detalle_ventas_netas': None, 'diff_ventas_netas': None, 'pct_diff_ventas_netas': None, 'kpi_tickets': 149, 'detalle_tickets': None, 'diff_tickets': None, 'kpi_pax': 431, 'detalle_pax': None, 'diff_pax': None, 'hallazgo': 'DIA_SIN_DETALLE_INTELIGENCIA'}
  {'fecha_operacion': datetime.date(2026, 6, 21), 'unidad_negocio_id': 'CIENFUEGOS', 'unidad_negocio_nombre': 'CIENFUEGOS', 'kpi_ventas_netas': Decimal('210292.58'), 'detalle_ventas_netas': None, 'diff_ventas_netas': None, 'pct_diff_ventas_netas': None, 'kpi_tickets': 64, 'detalle_tickets': None, 'diff_tickets': None, 'kpi_pax': 221, 'detalle_pax': None, 'diff_pax': None, 'hallazgo': 'DIA_SIN_DETALLE_INTELIGENCIA'}
  {'fecha_operacion': datetime.date(2026, 6, 27), 'unidad_negocio_id': '130MID', 'unidad_negocio_nombre': '130° MERIDA', 'kpi_ventas_netas': Decimal('206105.25'), 'detalle_ventas_netas': None, 'diff_ventas_netas': None, 'pct_diff_ventas_netas': None, 'kpi_tickets': 55, 'detalle_tickets': None, 'diff_tickets': None, 'kpi_pax': 156, 'detalle_pax': None, 'diff_pax': None, 'hallazgo': 'DIA_SIN_DETALLE_INTELIGENCIA'}
  {'fecha_operacion': datetime.date(2026, 6, 12), 'unidad_negocio_id': '130MID', 'unidad_negocio_nombre': '130° MERIDA', 'kpi_ventas_netas': Decimal('205679.30'), 'detalle_ventas_netas': None, 'diff_ventas_netas': None, 'pct_diff_ventas_netas': None, 'kpi_tickets': 39, 'detalle_tickets': None, 'diff_tickets': None, 'kpi_pax': 113, 'detalle_pax': None, 'diff_pax': None, 'hallazgo': 'DIA_SIN_DETALLE_INTELIGENCIA'}
```

### Batch 9
- Tipo: SELECT
- Columnas: fecha_inicio_audit, fecha_fin_audit, unidad_negocio_id, unidad_negocio_nombre, SucursalNombre, dias_kpi, dias_pax, pax_kpi, pax_sync_pax, diff_pax, ventas_kpi_netas, venta_sync_pax, pax_fecha_minima, pax_fecha_maxima, hallazgo
- Filas: 5
- Preview (primeras 20 filas):
```
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'unidad_negocio_id': '130MID', 'unidad_negocio_nombre': '130° MERIDA', 'SucursalNombre': None, 'dias_kpi': 31, 'dias_pax': None, 'pax_kpi': 2423, 'pax_sync_pax': None, 'diff_pax': None, 'ventas_kpi_netas': Decimal('3447042.35'), 'venta_sync_pax': None, 'pax_fecha_minima': None, 'pax_fecha_maxima': None, 'hallazgo': 'SIN_SYNC_PAX_DETALLE'}
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'unidad_negocio_id': '130QRO', 'unidad_negocio_nombre': '130° QUERETARO', 'SucursalNombre': None, 'dias_kpi': 31, 'dias_pax': None, 'pax_kpi': 2418, 'pax_sync_pax': None, 'diff_pax': None, 'ventas_kpi_netas': Decimal('4197207.00'), 'venta_sync_pax': None, 'pax_fecha_minima': None, 'pax_fecha_maxima': None, 'hallazgo': 'SIN_SYNC_PAX_DETALLE'}
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'unidad_negocio_id': 'CIENFUEGOS', 'unidad_negocio_nombre': 'CIENFUEGOS', 'SucursalNombre': None, 'dias_kpi': 31, 'dias_pax': None, 'pax_kpi': 3431, 'pax_sync_pax': None, 'diff_pax': None, 'ventas_kpi_netas': Decimal('3923095.28'), 'venta_sync_pax': None, 'pax_fecha_minima': None, 'pax_fecha_maxima': None, 'hallazgo': 'SIN_SYNC_PAX_DETALLE'}
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'unidad_negocio_id': 'ESTELAR', 'unidad_negocio_nombre': 'LA ESTELAR', 'SucursalNombre': None, 'dias_kpi': 31, 'dias_pax': None, 'pax_kpi': 5771, 'pax_sync_pax': None, 'diff_pax': None, 'ventas_kpi_netas': Decimal('2785307.41'), 'venta_sync_pax': None, 'pax_fecha_minima': None, 'pax_fecha_maxima': None, 'hallazgo': 'SIN_SYNC_PAX_DETALLE'}
  {'fecha_inicio_audit': datetime.date(2026, 5, 30), 'fecha_fin_audit': datetime.date(2026, 6, 29), 'unidad_negocio_id': 'ORIGEN', 'unidad_negocio_nombre': 'ORIGEN', 'SucursalNombre': None, 'dias_kpi': 31, 'dias_pax': None, 'pax_kpi': 3325, 'pax_sync_pax': None, 'diff_pax': None, 'ventas_kpi_netas': Decimal('2393369.74'), 'venta_sync_pax': None, 'pax_fecha_minima': None, 'pax_fecha_maxima': None, 'hallazgo': 'SIN_SYNC_PAX_DETALLE'}
```


## SQL ejecutado / revisado
```sql
/*
Fase 3 Comercial KPI cross-menu/source audit.

Solo lectura. Ejecutar con:
/app/.venv/bin/python backend/tools/edarsahub_sql_runner.py --mode validate --script backend/database/validation/phase3_comercial_kpi_cross_menu_source_audit.sql

Objetivo:
- Comparar KPIs visibles en Tablero Ejecutivo, Comercial e Inteligencia Comercial.
- Contrastar la vista KPI diaria v2 contra las tablas sincronizadas de detalle.
- Detectar diferencias de ventas netas/brutas, tickets, pax y semantica de promedios.
*/

SET NOCOUNT ON;
GO

SELECT
    DB_NAME() AS database_name,
    SYSDATETIME() AS fecha_ejecucion,
    'phase3_comercial_kpi_cross_menu_source_audit' AS auditoria,
    'READ_ONLY' AS modo,
    'Ultimos 30 dias cerrados segun vw_Comercial_KPIs_Diarios_v2_Runtime' AS rango_base;
GO

SELECT
    esperado.name AS objeto,
    obj.type_desc,
    obj.create_date,
    obj.modify_date,
    CASE WHEN obj.object_id IS NULL THEN 'FALTA' ELSE 'OK' END AS estado
FROM (
    VALUES
        ('vw_Comercial_KPIs_Diarios_v2_Runtime'),
        ('Comercial_KPIs_Diarios_v2'),
        ('Comercial_Ventas_Dia_Abiertas_v2'),
        ('Comercial_Inteligencia_VentasDetalleProducto'),
        ('Sync_Sales'),
        ('Sync_PAX_Detalle'),
        ('Unidades_Negocio')
) AS esperado(name)
LEFT JOIN sys.objects obj
    ON obj.object_id = OBJECT_ID('dbo.' + esperado.name)
ORDER BY esperado.name;
GO

SELECT
    'Tablero Ejecutivo' AS menu,
    '/api/v2/comercial/dashboard, /api/v2/comercial/kpis-diarios' AS endpoints_clave,
    'vw_Comercial_KPIs_Diarios_v2_Runtime' AS fuente_principal,
    'ventas_sin_propina para backend v2; algunas vistas frontend aun usan nombre ventas_total' AS ventas_kpi,
    'cheque_promedio = ventas / tickets; ticket_promedio canonico = ventas / pax' AS regla_promedios,
    'Revisar nombres heredados ticket_promedio/pax_promedio' AS riesgo
UNION ALL
SELECT
    'Comercial',
    '/api/comercial/dashboard/{server_id}',
    'Servicio comercial SQL-first; debe converger a vw_Comercial_KPIs_Diarios_v2_Runtime',
    'ventas_sin_propina preferida; legacy puede exponer ventas_periodo',
    'legacy usa ticket_promedio como ventas / tickets',
    'Nomenclatura legacy puede diferir de Inteligencia'
UNION ALL
SELECT
    'Inteligencia Comercial',
    '/api/inteligencia/dashboard, /api/reporteador-bi/*, /api/inteligencia/iscam/*',
    'KPI view + Comercial_Inteligencia_VentasDetalleProducto + Sync_Sales + Sync_PAX_Detalle',
    'dashboard usa ventas_sin_propina; ISCAM usa MontoTotal',
    'dashboard canonico: ticket = ventas / pax, cheque = ventas / tickets',
    'Mezcla vista agregada, detalle por producto y Sync_Sales';
GO

DECLARE @fecha_fin DATE = (
    SELECT MAX(fecha_operacion)
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE ISNULL(ventas_sin_propina, 0) > 0
);
DECLARE @fecha_inicio DATE = DATEADD(DAY, -30, ISNULL(@fecha_fin, CAST(GETDATE() AS DATE)));

WITH SourceFreshness AS (
    SELECT
        'KPI_RUNTIME' AS fuente,
        COUNT_BIG(*) AS registros,
        COUNT(DISTINCT unidad_negocio_id) AS unidades,
        COUNT(DISTINCT fecha_operacion) AS dias,
        MIN(fecha_operacion) AS fecha_minima,
        MAX(fecha_operacion) AS fecha_maxima,
        MAX(fecha_sincronizacion) AS ultima_sync,
        SUM(ISNULL(ventas_sin_propina, 0)) AS ventas_netas,
        SUM(ISNULL(ventas_total, 0)) AS ventas_brutas,
        SUM(ISNULL(tickets_total, 0)) AS tickets,
        SUM(ISNULL(pax_total, 0)) AS pax
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin

    UNION ALL

    SELECT
        'INTEL_DETALLE',
        COUNT_BIG(*),
        COUNT(DISTINCT unidad_negocio_id),
        COUNT(DISTINCT fecha_operacion),
        MIN(fecha_operacion),
        MAX(fecha_operacion),
        MAX(fecha_sincronizacion),
        SUM(ISNULL(importe_neto, 0)),
        SUM(ISNULL(importe_bruto, 0)),
        COUNT(DISTINCT CONCAT(
            ISNULL(NULLIF(id_transaccion, ''), 'SIN_TX'),
            '|',
            ISNULL(NULLIF(numero_ticket, ''), 'SIN_TICKET'),
            '|',
            CONVERT(VARCHAR(10), fecha_operacion, 120)
        )),
        CAST(NULL AS DECIMAL(18, 2))
    FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
    WHERE ISNULL(activo, 1) = 1
      AND fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin

    UNION ALL

    SELECT
        'SYNC_SALES',
        COUNT_BIG(*),
        COUNT(DISTINCT UnidadNegocio),
        COUNT(DISTINCT CAST(FechaHora AS DATE)),
        MIN(CAST(FechaHora AS DATE)),
        MAX(CAST(FechaHora AS DATE)),
        MAX(last_modified),
        SUM(ISNULL(MontoTotal, total)),
        SUM(ISNULL(MontoTotal, total)),
        COUNT_BIG(*),
        SUM(ISNULL(Pax, 0))
    FROM dbo.Sync_Sales
    WHERE ISNULL(status, 'COMPLETED') = 'COMPLETED'
      AND CAST(FechaHora AS DATE) BETWEEN @fecha_inicio AND @fecha_fin

    UNION ALL

    SELECT
        'SYNC_PAX_DETALLE',
        COUNT_BIG(*),
        COUNT(DISTINCT SucursalNombre),
        COUNT(DISTINCT FechaOperacion),
        MIN(FechaOperacion),
        MAX(FechaOperacion),
        MAX(FechaSync),
        SUM(ISNULL(VentaCuenta, 0)),
        SUM(ISNULL(VentaCuenta, 0)),
        COUNT(DISTINCT ISNULL(CuentaID, CuentaFolio)),
        SUM(ISNULL(NumeroComensales, 0))
    FROM dbo.Sync_PAX_Detalle
    WHERE FechaOperacion BETWEEN @fecha_inicio AND @fecha_fin
)
SELECT
    @fecha_inicio AS fecha_inicio_audit,
    @fecha_fin AS fecha_fin_audit,
    fuente,
    registros,
    unidades,
    dias,
    fecha_minima,
    fecha_maxima,
    DATEDIFF(DAY, fecha_maxima, @fecha_fin) AS dias_retraso_vs_kpi,
    ultima_sync,
    ventas_netas,
    ventas_brutas,
    tickets,
    pax
FROM SourceFreshness
ORDER BY fuente;
GO

DECLARE @fecha_fin DATE = (
    SELECT MAX(fecha_operacion)
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE ISNULL(ventas_sin_propina, 0) > 0
);
DECLARE @fecha_inicio DATE = DATEADD(DAY, -30, ISNULL(@fecha_fin, CAST(GETDATE() AS DATE)));

WITH Unidades AS (
    SELECT
        codigo,
        nombre,
        system_type,
        server_id,
        activo
    FROM dbo.Unidades_Negocio
    WHERE ISNULL(activo, 1) = 1
),
KpiUnidad AS (
    SELECT
        k.unidad_negocio_id,
        MAX(k.unidad_negocio_nombre) AS unidad_negocio_nombre,
        MAX(k.sistema_origen) AS sistema_origen,
        COUNT(DISTINCT k.fecha_operacion) AS dias_kpi,
        SUM(ISNULL(k.ventas_sin_propina, 0)) AS kpi_ventas_netas,
        SUM(ISNULL(k.ventas_total, 0)) AS kpi_ventas_brutas,
        SUM(ISNULL(k.propinas_total, 0)) AS kpi_propinas,
        SUM(ISNULL(k.tickets_total, 0)) AS kpi_tickets,
        SUM(ISNULL(k.pax_total, 0)) AS kpi_pax
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime k
    WHERE k.fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY k.unidad_negocio_id
),
DetalleTicket AS (
    SELECT
        COALESCE(NULLIF(d.unidad_negocio_id, ''), u.codigo, d.unidad_negocio_nombre) AS unidad_negocio_id,
        MAX(COALESCE(d.unidad_negocio_nombre, u.nombre)) AS unidad_negocio_nombre,
        d.fecha_operacion,
        CONCAT(
            ISNULL(NULLIF(d.id_transaccion, ''), 'SIN_TX'),
            '|',
            ISNULL(NULLIF(d.numero_ticket, ''), 'SIN_TICKET'),
            '|',
            CONVERT(VARCHAR(10), d.fecha_operacion, 120)
        ) AS ticket_key,
        SUM(ISNULL(d.importe_neto, 0)) AS venta_ticket_neta,
        SUM(ISNULL(d.importe_bruto, 0)) AS venta_ticket_bruta,
        MAX(ISNULL(d.pax, 0)) AS pax_ticket,
        COUNT_BIG(*) AS lineas_producto
    FROM dbo.Comercial_Inteligencia_VentasDetalleProducto d
    LEFT JOIN Unidades u
        ON UPPER(LTRIM(RTRIM(d.unidad_negocio_id))) = UPPER(LTRIM(RTRIM(u.codigo)))
        OR UPPER(LTRIM(RTRIM(d.unidad_negocio_nombre))) = UPPER(LTRIM(RTRIM(u.nombre)))
    WHERE ISNULL(d.activo, 1) = 1
      AND d.fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY
        COALESCE(NULLIF(d.unidad_negocio_id, ''), u.codigo, d.unidad_negocio_nombre),
        d.fecha_operacion,
        CONCAT(
            ISNULL(NULLIF(d.id_transaccion, ''), 'SIN_TX'),
            '|',
            ISNULL(NULLIF(d.numero_ticket, ''), 'SIN_TICKET'),
            '|',
            CONVERT(VARCHAR(10), d.fecha_operacion, 120)
        )
),
DetalleUnidad AS (
    SELECT
        unidad_negocio_id,
        MAX(unidad_negocio_nombre) AS unidad_negocio_nombre,
        COUNT(DISTINCT fecha_operacion) AS dias_detalle,
        COUNT_BIG(*) AS detalle_tickets,
        SUM(venta_ticket_neta) AS detalle_ventas_netas,
        SUM(venta_ticket_bruta) AS detalle_ventas_brutas,
        SUM(pax_ticket) AS detalle_pax,
        SUM(lineas_producto) AS detalle_lineas
    FROM DetalleTicket
    GROUP BY unidad_negocio_id
),
SyncSalesUnidad AS (
    SELECT
        COALESCE(u.codigo, s.UnidadNegocio) AS unidad_negocio_id,
        MAX(COALESCE(u.nombre, s.UnidadNegocio)) AS unidad_negocio_nombre,
        COUNT(DISTINCT CAST(s.FechaHora AS DATE)) AS dias_sync_sales,
        COUNT_BIG(*) AS sync_sales_tickets,
        SUM(ISNULL(s.MontoTotal, s.total)) AS sync_sales_ventas,
        SUM(ISNULL(s.Pax, 0)) AS sync_sales_pax
    FROM dbo.Sync_Sales s
    LEFT JOIN Unidades u
        ON UPPER(LTRIM(RTRIM(s.UnidadNegocio))) = UPPER(LTRIM(RTRIM(u.codigo)))
        OR UPPER(LTRIM(RTRIM(s.UnidadNegocio))) = UPPER(LTRIM(RTRIM(u.nombre)))
    WHERE ISNULL(s.status, 'COMPLETED') = 'COMPLETED'
      AND CAST(s.FechaHora AS DATE) BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY COALESCE(u.codigo, s.UnidadNegocio)
),
KeySet AS (
    SELECT unidad_negocio_id FROM KpiUnidad
    UNION
    SELECT unidad_negocio_id FROM DetalleUnidad
    UNION
    SELECT unidad_negocio_id FROM SyncSalesUnidad
)
SELECT
    @fecha_inicio AS fecha_inicio_audit,
    @fecha_fin AS fecha_fin_audit,
    keyset.unidad_negocio_id,
    COALESCE(k.unidad_negocio_nombre, d.unidad_negocio_nombre, s.unidad_negocio_nombre) AS unidad_negocio_nombre,
    COALESCE(k.sistema_origen, u.system_type) AS sistema_origen,
    k.dias_kpi,
    d.dias_detalle,
    s.dias_sync_sales,
    k.kpi_ventas_netas,
    d.detalle_ventas_netas,
    k.kpi_ventas_netas - d.detalle_ventas_netas AS diff_kpi_neto_vs_detalle,
    CASE WHEN ABS(k.kpi_ventas_netas) > 0
        THEN ((d.detalle_ventas_netas - k.kpi_ventas_netas) / NULLIF(k.kpi_ventas_netas, 0)) * 100
        ELSE NULL END AS pct_diff_detalle_neto,
    k.kpi_ventas_brutas,
    s.sync_sales_ventas,
    s.sync_sales_ventas - k.kpi_ventas_brutas AS diff_sync_sales_vs_kpi_bruto,
    CASE WHEN ABS(k.kpi_ventas_brutas) > 0
        THEN ((s.sync_sales_ventas - k.kpi_ventas_brutas) / NULLIF(k.kpi_ventas_brutas, 0)) * 100
        ELSE NULL END AS pct_diff_sync_sales_bruto,
    k.kpi_tickets,
    d.detalle_tickets,
    s.sync_sales_tickets,
    k.kpi_pax,
    d.detalle_pax,
    s.sync_sales_pax,
    CASE
        WHEN k.unidad_negocio_id IS NULL THEN 'SIN_KPI_RUNTIME'
        WHEN d.unidad_negocio_id IS NULL AND s.unidad_negocio_id IS NULL THEN 'SIN_DETALLE_Y_SYNC_SALES'
        WHEN d.unidad_negocio_id IS NULL THEN 'SIN_DETALLE_INTELIGENCIA'
        WHEN s.unidad_negocio_id IS NULL THEN 'SIN_SYNC_SALES'
        WHEN ABS(ISNULL(d.detalle_ventas_netas, 0) - ISNULL(k.kpi_ventas_netas, 0)) > 1000
             AND ABS(ISNULL(d.detalle_ventas_netas, 0) - ISNULL(k.kpi_ventas_netas, 0)) > ABS(ISNULL(k.kpi_ventas_netas, 0)) * 0.01
             THEN 'KPI_NETO_VS_DETALLE_DIFIERE'
        WHEN ABS(ISNULL(s.sync_sales_ventas, 0) - ISNULL(k.kpi_ventas_brutas, 0)) > 1000
             AND ABS(ISNULL(s.sync_sales_ventas, 0) - ISNULL(k.kpi_ventas_brutas, 0)) > ABS(ISNULL(k.kpi_ventas_brutas, 0)) * 0.01
             THEN 'KPI_BRUTO_VS_SYNC_SALES_DIFIERE'
        WHEN ABS(ISNULL(k.kpi_tickets, 0) - ISNULL(d.detalle_tickets, 0)) > 2 THEN 'TICKETS_KPI_VS_DETALLE_DIFIEREN'
        WHEN ABS(ISNULL(k.kpi_pax, 0) - ISNULL(d.detalle_pax, 0)) > 5 THEN 'PAX_KPI_VS_DETALLE_DIFIERE'
        ELSE 'OK'
    END AS hallazgo
FROM KeySet keyset
LEFT JOIN KpiUnidad k
    ON k.unidad_negocio_id = keyset.unidad_negocio_id
LEFT JOIN DetalleUnidad d
    ON d.unidad_negocio_id = keyset.unidad_negocio_id
LEFT JOIN SyncSalesUnidad s
    ON s.unidad_negocio_id = keyset.unidad_negocio_id
LEFT JOIN Unidades u
    ON u.codigo = keyset.unidad_negocio_id
ORDER BY
    CASE
        WHEN k.unidad_negocio_id IS NULL THEN 0
        WHEN d.unidad_negocio_id IS NULL OR s.unidad_negocio_id IS NULL THEN 1
        ELSE 2
    END,
    ABS(ISNULL(d.detalle_ventas_netas, 0) - ISNULL(k.kpi_ventas_netas, 0)) DESC,
    keyset.unidad_negocio_id;
GO

DECLARE @fecha_fin DATE = (
    SELECT MAX(fecha_operacion)
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE ISNULL(ventas_sin_propina, 0) > 0
);
DECLARE @fecha_inicio DATE = DATEADD(DAY, -30, ISNULL(@fecha_fin, CAST(GETDATE() AS DATE)));

WITH KpiDia AS (
    SELECT
        unidad_negocio_id,
        MAX(unidad_negocio_nombre) AS unidad_negocio_nombre,
        fecha_operacion,
        SUM(ISNULL(ventas_sin_propina, 0)) AS ventas_sin_propina,
        SUM(ISNULL(ventas_total, 0)) AS ventas_total,
        SUM(ISNULL(propinas_total, 0)) AS propinas_total,
        SUM(ISNULL(tickets_total, 0)) AS tickets_total,
        SUM(ISNULL(pax_total, 0)) AS pax_total,
        AVG(ISNULL(ticket_promedio, 0)) AS ticket_promedio_guardado,
        AVG(ISNULL(pax_promedio, 0)) AS pax_promedio_guardado
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY unidad_negocio_id, fecha_operacion
),
Semantica AS (
    SELECT
        unidad_negocio_id,
        unidad_negocio_nombre,
        fecha_operacion,
        ventas_sin_propina,
        ventas_total,
        propinas_total,
        tickets_total,
        pax_total,
        ticket_promedio_guardado,
        pax_promedio_guardado,
        CASE WHEN tickets_total > 0 THEN ventas_sin_propina / tickets_total ELSE 0 END AS cheque_promedio_neto_calc,
        CASE WHEN pax_total > 0 THEN ventas_sin_propina / pax_total ELSE 0 END AS ticket_promedio_canonico_calc,
        CASE WHEN tickets_total > 0 THEN CAST(pax_total AS DECIMAL(18, 4)) / tickets_total ELSE 0 END AS pax_por_cheque_calc
    FROM KpiDia
)
SELECT TOP 100
    unidad_negocio_id,
    unidad_negocio_nombre,
    fecha_operacion,
    ventas_sin_propina,
    ventas_total,
    propinas_total,
    tickets_total,
    pax_total,
    ticket_promedio_guardado,
    cheque_promedio_neto_calc,
    ticket_promedio_canonico_calc,
    pax_promedio_guardado,
    pax_por_cheque_calc,
    ABS(ticket_promedio_guardado - cheque_promedio_neto_calc) AS delta_ticket_vs_cheque_neto,
    ABS(ticket_promedio_guardado - ticket_promedio_canonico_calc) AS delta_ticket_vs_ticket_canonico,
    ABS(pax_promedio_guardado - ticket_promedio_canonico_calc) AS delta_paxprom_vs_ticket_canonico,
    ABS(pax_promedio_guardado - pax_por_cheque_calc) AS delta_paxprom_vs_pax_por_cheque,
    CASE
        WHEN ABS(ticket_promedio_guardado - cheque_promedio_neto_calc) <= 0.05
             AND ABS(ticket_promedio_guardado - ticket_promedio_canonico_calc) > 0.05
             THEN 'CAMPO_TICKET_PROMEDIO_ES_CHEQUE_PROMEDIO'
        WHEN ABS(ticket_promedio_guardado - ticket_promedio_canonico_calc) <= 0.05
             THEN 'CAMPO_TICKET_PROMEDIO_CANONICO'
        ELSE 'CAMPO_TICKET_PROMEDIO_NO_CUADRA'
    END AS hallazgo_ticket_promedio,
    CASE
        WHEN ABS(pax_promedio_guardado - ticket_promedio_canonico_calc) <= 0.05
             THEN 'CAMPO_PAX_PROMEDIO_ES_VENTA_POR_PAX'
        WHEN ABS(pax_promedio_guardado - pax_por_cheque_calc) <= 0.05
             THEN 'CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE'
        ELSE 'CAMPO_PAX_PROMEDIO_NO_CUADRA'
    END AS hallazgo_pax_promedio
FROM Semantica
WHERE ABS(ticket_promedio_guardado - cheque_promedio_neto_calc) > 0.05
   OR ABS(ticket_promedio_guardado - ticket_promedio_canonico_calc) > 0.05
   OR ABS(pax_promedio_guardado - ticket_promedio_canonico_calc) > 0.05
   OR ABS(pax_promedio_guardado - pax_por_cheque_calc) > 0.05
ORDER BY fecha_operacion DESC, unidad_negocio_id;
GO

DECLARE @fecha_fin DATE = (
    SELECT MAX(fecha_operacion)
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE ISNULL(ventas_sin_propina, 0) > 0
);
DECLARE @fecha_inicio DATE = DATEADD(DAY, -30, ISNULL(@fecha_fin, CAST(GETDATE() AS DATE)));

WITH KpiDia AS (
    SELECT
        unidad_negocio_id,
        MAX(unidad_negocio_nombre) AS unidad_negocio_nombre,
        fecha_operacion,
        SUM(ISNULL(ventas_sin_propina, 0)) AS kpi_ventas_netas,
        SUM(ISNULL(ventas_total, 0)) AS kpi_ventas_brutas,
        SUM(ISNULL(tickets_total, 0)) AS kpi_tickets,
        SUM(ISNULL(pax_total, 0)) AS kpi_pax
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY unidad_negocio_id, fecha_operacion
),
DetalleTicket AS (
    SELECT
        COALESCE(NULLIF(unidad_negocio_id, ''), unidad_negocio_nombre) AS unidad_negocio_id,
        MAX(unidad_negocio_nombre) AS unidad_negocio_nombre,
        fecha_operacion,
        CONCAT(
            ISNULL(NULLIF(id_transaccion, ''), 'SIN_TX'),
            '|',
            ISNULL(NULLIF(numero_ticket, ''), 'SIN_TICKET'),
            '|',
            CONVERT(VARCHAR(10), fecha_operacion, 120)
        ) AS ticket_key,
        SUM(ISNULL(importe_neto, 0)) AS venta_ticket_neta,
        MAX(ISNULL(pax, 0)) AS pax_ticket
    FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
    WHERE ISNULL(activo, 1) = 1
      AND fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY
        COALESCE(NULLIF(unidad_negocio_id, ''), unidad_negocio_nombre),
        fecha_operacion,
        CONCAT(
            ISNULL(NULLIF(id_transaccion, ''), 'SIN_TX'),
            '|',
            ISNULL(NULLIF(numero_ticket, ''), 'SIN_TICKET'),
            '|',
            CONVERT(VARCHAR(10), fecha_operacion, 120)
        )
),
DetalleDia AS (
    SELECT
        unidad_negocio_id,
        MAX(unidad_negocio_nombre) AS unidad_negocio_nombre,
        fecha_operacion,
        SUM(venta_ticket_neta) AS detalle_ventas_netas,
        COUNT_BIG(*) AS detalle_tickets,
        SUM(pax_ticket) AS detalle_pax
    FROM DetalleTicket
    GROUP BY unidad_negocio_id, fecha_operacion
),
KeySet AS (
    SELECT unidad_negocio_id, fecha_operacion FROM KpiDia
    UNION
    SELECT unidad_negocio_id, fecha_operacion FROM DetalleDia
)
SELECT TOP 100
    keyset.fecha_operacion,
    keyset.unidad_negocio_id,
    COALESCE(k.unidad_negocio_nombre, d.unidad_negocio_nombre) AS unidad_negocio_nombre,
    k.kpi_ventas_netas,
    d.detalle_ventas_netas,
    d.detalle_ventas_netas - k.kpi_ventas_netas AS diff_ventas_netas,
    CASE WHEN ABS(k.kpi_ventas_netas) > 0
        THEN ((d.detalle_ventas_netas - k.kpi_ventas_netas) / NULLIF(k.kpi_ventas_netas, 0)) * 100
        ELSE NULL END AS pct_diff_ventas_netas,
    k.kpi_tickets,
    d.detalle_tickets,
    d.detalle_tickets - k.kpi_tickets AS diff_tickets,
    k.kpi_pax,
    d.detalle_pax,
    d.detalle_pax - k.kpi_pax AS diff_pax,
    CASE
        WHEN k.unidad_negocio_id IS NULL THEN 'DIA_SIN_KPI_RUNTIME'
        WHEN d.unidad_negocio_id IS NULL THEN 'DIA_SIN_DETALLE_INTELIGENCIA'
        WHEN ABS(ISNULL(d.detalle_ventas_netas, 0) - ISNULL(k.kpi_ventas_netas, 0)) > 1000
             AND ABS(ISNULL(d.detalle_ventas_netas, 0) - ISNULL(k.kpi_ventas_netas, 0)) > ABS(ISNULL(k.kpi_ventas_netas, 0)) * 0.01
             THEN 'VENTA_NETA_DIARIA_DIFIERE'
        WHEN ABS(ISNULL(d.detalle_tickets, 0) - ISNULL(k.kpi_tickets, 0)) > 2 THEN 'TICKETS_DIARIOS_DIFIEREN'
        WHEN ABS(ISNULL(d.detalle_pax, 0) - ISNULL(k.kpi_pax, 0)) > 5 THEN 'PAX_DIARIO_DIFIERE'
        ELSE 'OK'
    END AS hallazgo
FROM KeySet keyset
LEFT JOIN KpiDia k
    ON k.unidad_negocio_id = keyset.unidad_negocio_id
   AND k.fecha_operacion = keyset.fecha_operacion
LEFT JOIN DetalleDia d
    ON d.unidad_negocio_id = keyset.unidad_negocio_id
   AND d.fecha_operacion = keyset.fecha_operacion
WHERE k.unidad_negocio_id IS NULL
   OR d.unidad_ne
```