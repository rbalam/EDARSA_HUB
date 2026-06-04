# Diagnóstico PropinasTPV MPRO vs SoftRestaurant

Fecha: Thu Jun  4 17:56:07 UTC 2026

## 1. Endpoints backend de propinas
```text
/app/backend/server.py.backup_env_connection_20260604_075317:549:# MÓDULO PROPINAS TPV: Control y cuadre de comisión sobre propinas TPV (2%)
/app/backend/server.py.backup_env_connection_20260604_075317:557:from modules.finanzas.propinas_tpv import get_router_sql as get_propinas_tpv_router
/app/backend/server.py.backup_env_connection_20260604_075317:641:# MÓDULO PROPINAS TPV: Registrar router de propinas TPV (FASE 1 MVP - Solo SoftRestaurant)
/app/backend/server.py.backup_env_connection_20260604_075317:642:# Endpoints bajo /api/finanzas/propinas/*
/app/backend/server.py.backup_env_connection_20260604_075317:645:api_router.include_router(get_propinas_tpv_router())
/app/backend/server.py.backup_env_connection_20260604_075317:648:# Endpoints bajo /api/finanzas/propinas/v2/*
/app/backend/server.py.backup_env_connection_20260604_075317:649:# Fuente de verdad: EDARSAHUB.propinas_tpv_control
/app/backend/server.py.backup_env_connection_20260604_075317:650:from modules.finanzas.propinas_tpv import get_router_edarsahub as get_propinas_tpv_edarsahub_router
/app/backend/server.py.backup_env_connection_20260604_075317:651:api_router.include_router(get_propinas_tpv_edarsahub_router())
/app/backend/db/migrations/create_finanzas_kpis_historico.sql:30:        propinas DECIMAL(18,2) DEFAULT 0,
/app/backend/db/migrations/create_comercial_kpis_historico.sql:50:        propinas_total DECIMAL(18, 2) NULL DEFAULT 0,
/app/backend/modules/comercial/queries/softrestaurant.py:110:    - total_venta: SUM(cheques.total - cheques.propina) - Venta total en pesos (SIN propinas)
/app/backend/modules/comercial/queries/softrestaurant.py:166:    # NOTA: Se excluyen propinas de las ventas SI la columna existe
/app/backend/modules/comercial/inteligencia_comercial_routes.py:183:        SUM(propinas_total) AS propinas_total,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:243:        SUM(propinas_total) AS propinas_total,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:405:        SUM(propinas_total) AS propinas_total,
/app/backend/modules/comercial/inteligencia_repository.py:66:                SUM(propinas_total) AS propinas_total,
/app/backend/modules/comercial/inteligencia_repository.py:114:                SUM(propinas_total) AS propinas_total,
/app/backend/modules/comercial/routes.py.bak:2178:            # Ventas por mesero/vendedor (excluyendo propinas SI existe la columna)
/app/backend/modules/comercial/routes.py.bak:3008:            # NOTA: Se excluyen propinas de las ventas SI existe la columna
/app/backend/modules/comercial/routes.py.bak:3307:            # NOTA: importe excluye propinas SI existe la columna
/app/backend/modules/comercial/routes.py.bak:3589:            # NOTA: Se excluyen propinas de las ventas SI existe la columna
/app/backend/modules/comercial/routes.py.bak:3688:            # Esto distribuye propinas, impuestos, descuentos proporcionalmente
/app/backend/modules/comercial/historical_kpis_repository.py:117:        'propinas': kpi_data.get('propinas_total', 0)
/app/backend/modules/comercial/historical_kpis_repository.py:197:    propinas_total = float(record.get('propinas_total', record.get('propinas', 0)) or 0)
/app/backend/modules/comercial/historical_kpis_repository.py:212:        'propinas_total': propinas_total
/app/backend/modules/comercial/historical_kpis_repository.py:263:                propinas_total = {propinas_total},
/app/backend/modules/comercial/historical_kpis_repository.py:294:                ticket_promedio, propinas_total, source_hash,
/app/backend/modules/comercial/historical_kpis_repository.py:311:                {propinas_total},
/app/backend/modules/comercial/historical_kpis_repository.py:537:                'propinas_total': kpis.get('propinas', 0),
/app/backend/modules/comercial/routes.py:2178:            # Ventas por mesero/vendedor (excluyendo propinas SI existe la columna)
/app/backend/modules/comercial/routes.py:3008:            # NOTA: Se excluyen propinas de las ventas SI existe la columna
/app/backend/modules/comercial/routes.py:3307:            # NOTA: importe excluye propinas SI existe la columna
/app/backend/modules/comercial/routes.py:3589:            # NOTA: Se excluyen propinas de las ventas SI existe la columna
/app/backend/modules/comercial/routes.py:3688:            # Esto distribuye propinas, impuestos, descuentos proporcionalmente
/app/backend/modules/hub/bus_abstraccion_universal.py:61:        Extrae las métricas de rendimiento y propinas acumuladas del vendedor para
/app/backend/modules/inteligencia_comercial/routes.py:143:                COALESCE(SUM(propinas_total), 0) AS propinas_total,
/app/backend/modules/inteligencia_comercial/routes.py:162:                    SUM(propinas_total) AS propinas
/app/backend/modules/inteligencia_comercial/routes.py:226:                "propinas_total": round(float(kpi_data.get("propinas_total", 0)), 2),
/app/backend/modules/inteligencia_comercial/routes.py:235:                    "propinas": round(float(u["propinas"] or 0), 2),
/app/backend/modules/inteligencia_comercial/routes.py:255:            "kpis": {"ventas_totales": 0, "pax_total": 0, "cheques_total": 0, "propinas_total": 0, "cheque_promedio": 0}
/app/backend/modules/inteligencia_comercial/routes.py:292:                SUM(propinas_total) AS propinas,
/app/backend/modules/inteligencia_comercial/routes.py:315:                    "propinas": round(float(d["propinas"] or 0), 2),
/app/backend/modules/edge/super_caja_arquero.py:81:            # Rastreo paralelo de propinas e integraciones
/app/backend/modules/edge/super_caja_arquero.py:105:            "propinas_acumuladas_staff": round(acumulado_kpis["propina_total_staff"], 2)
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:212:    SUM(ISNULL(propina, 0)) as propinas,
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:253:    SUM(ISNULL(propina, 0)) as propinas,
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:344:            propinas = safe_decimal(row.get('propinas', 0))
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:386:                propinas_total=propinas,
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:512:            ventas_sin_propina = ventas_total  # MPRO no separa propinas aquí
```

