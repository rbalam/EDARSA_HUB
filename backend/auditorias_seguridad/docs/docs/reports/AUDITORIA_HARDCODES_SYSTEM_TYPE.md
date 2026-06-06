# Auditoría hardcodes system_type

Fecha: Thu Jun  4 18:49:29 UTC 2026

## 1. Hardcodes SoftRestaurant sin SOFTRESTAURANT_PRO
```text
/app/backend/modules/comercial/service.py:1212:    elif system_type.upper() in ['SOFTRESTAURANT', 'SR']:
/app/backend/modules/comercial/queries/__init__.py:47:    VentasPeriodoResult as VentasPeriodoResultSR,
/app/backend/modules/comercial/queries/__init__.py:57:VentasPeriodoResult = VentasPeriodoResultSR
/app/backend/modules/comercial/queries/softrestaurant.py:57:SR_KNOWN_TABLES = [
/app/backend/modules/comercial/queries/softrestaurant.py:72:MODULE_NAME = "COMERCIAL_QUERIES_SR"
/app/backend/modules/rh/service.py:133:    ('ISR', 'ISR', 'Descuento', -1, 'Formula'),
/app/backend/modules/consultas_sql/service.py:133:            codigo: CodigoConsulta (ej: 'SR_VENTAS_DIA')
/app/backend/modules/consultas_sql/repository.py:284:            codigo_consulta: Código único de la consulta (ej: 'SR_VENTAS_DIA')
/app/backend/modules/catalogos/schemas.py:278:        "campos": ["ConceptoNominaID", "CodigoConcepto", "NombreConcepto", "TipoConceptoNominaID", "ClaveSAT", "EsGravado", "EsExento", "IntegraSBC", "AfectaISR", "Activo"],
/app/backend/modules/catalogos/schemas.py:279:        "campos_editables": ["CodigoConcepto", "NombreConcepto", "TipoConceptoNominaID", "ClaveSAT", "EsGravado", "EsExento", "IntegraSBC", "AfectaISR", "Activo"],
/app/backend/modules/sync_historicos/service.py:169:            logger.error(f"[SYNC-SR] Error obteniendo ventas: {e}")
/app/backend/modules/sync_historicos/service.py:532:            logger.error(f"[SYNC-POR-HORA-SR] Error: {e}")
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:335:                logger.error(f"Error procesando fila SR: {e}")
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:190:QUERY_SR_MENSUAL = """
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:333:    query = QUERY_SR_MENSUAL.format(
/app/backend/modules/finanzas/carga_historica_propinas_tpv.py:110:    logger.info(f"[CARGA_HISTORICA] Iniciando carga histórica SR: {unidad_nombre}")
/app/backend/modules/finanzas/tesoreria.py:752:    - system_type in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']
/app/backend/modules/finanzas/tesoreria.py:798:                if system_type not in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']:
/app/backend/modules/finanzas/tesoreria.py:802:                if system_type in ['SOFTRESTAURANT', 'SR']:
/app/backend/modules/finanzas/tesoreria.py:844:            if system_type not in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']:
/app/backend/modules/finanzas/tesoreria.py:847:            if system_type in ['SOFTRESTAURANT', 'SR']:
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:49:UNIDADES_SR_AUTORIZADAS = ['130° MERIDA', 'CIENFUEGOS', 'LA ESTELAR']
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:119:              AND s.system_type IN ('SoftRestaurant', 'SOFTRESTAURANT', 'SR', 'SOFTRESTAURANT_PRO')
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:125:            logger.warning(f"[SYNC_SR] Unidad no encontrada: {unidad_nombre}")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:135:        logger.info(f"[SYNC_SR] Conexión parseada para {unidad_nombre}: "
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:196:        logger.info(f"[SYNC_SR] Conexión pytds exitosa a {host}:{port}/{database}")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:201:        logger.warning(f"[SYNC_SR] pytds falló: {pytds_error}, intentando pymssql...")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:297:    logger.info(f"[SYNC_SR] Extrayendo turnos de {conn_info['unidad_nombre']} "
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:328:        logger.info(f"[SYNC_SR] {len(turnos_origen)} turnos encontrados en {conn_info['unidad_nombre']}")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:365:                'TotalTarjetaDebito': float(t.get('tarjeta') or 0),  # SR no distingue deb/cred en turnos
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:392:        logger.error(f"[SYNC_SR] Error extrayendo de {conn_info['unidad_nombre']}: {e}")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:417:    logger.info(f"[SYNC_SR] Sincronizando {len(registros)} registros a EDARSAHUB")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:513:                logger.error(f"[SYNC_SR] Error procesando registro IdOrigen={reg.get('IdOrigen')}: {e}")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:517:        logger.info(f"[SYNC_SR] Sincronización completada: {stats}")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:521:        logger.error(f"[SYNC_SR] Error en sincronización: {e}")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:578:        logger.info(f"[SYNC_SR] SyncLog registrado: ID={log_id}, Estatus={estatus}")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:583:        logger.error(f"[SYNC_SR] Error registrando SyncLog: {e}")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:603:        unidad_nombre: Nombre de la unidad (debe estar en UNIDADES_SR_AUTORIZADAS)
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:612:    if unidad_nombre not in UNIDADES_SR_AUTORIZADAS:
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:614:                        f"Autorizadas: {UNIDADES_SR_AUTORIZADAS}")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:675:        logger.error(f"[SYNC_SR] Error sincronizando {unidad_nombre}: {e}")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:713:    for unidad in UNIDADES_SR_AUTORIZADAS:
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:714:        logger.info(f"[SYNC_SR] === Iniciando sincronización: {unidad} ===")
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:724:            logger.error(f"[SYNC_SR] Error fatal en {unidad}: {e}")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:71:UNIDADES_SR_AUTORIZADAS = ['130° MERIDA', 'CIENFUEGOS', 'LA ESTELAR']
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:132:              AND s.system_type IN ('SoftRestaurant', 'SOFTRESTAURANT', 'SR', 'SOFTRESTAURANT_PRO')
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:138:            logger.warning(f"[SYNC_PROPINAS_SR] Unidad no encontrada: {unidad_nombre}")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:146:        logger.info(f"[SYNC_PROPINAS_SR] Conexión parseada para {unidad_nombre}: "
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:199:        logger.info(f"[SYNC_PROPINAS_SR] Conexión pytds exitosa a {host}:{port}/{database}")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:203:        logger.warning(f"[SYNC_PROPINAS_SR] pytds falló: {pytds_error}, intentando pymssql...")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:293:    logger.info(f"[SYNC_PROPINAS_SR] Extrayendo propinas TPV de {conn_info['unidad_nombre']} "
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:299:        logger.error(f"[SYNC_PROPINAS_SR] Error conectando a {conn_info['unidad_nombre']}: {e}")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:341:        logger.info(f"[SYNC_PROPINAS_SR] {conn_info['unidad_nombre']}: {len(rows)} cheques con propina TPV")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:522:                logger.error(f"[SYNC_PROPINAS_SR] Error insertando registro: {e}")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:529:        logger.error(f"[SYNC_PROPINAS_SR] Error en carga: {e}")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:590:        logger.info(f"[SYNC_PROPINAS_SR] SyncLog registrado: ID={log_id}, Estatus={estatus}")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:620:    logger.info(f"[SYNC_PROPINAS_SR] === Iniciando sync de propinas TPV: {unidad_nombre} ===")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:625:    if unidad_nombre not in UNIDADES_SR_AUTORIZADAS:
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:629:            'error': f'Unidad no autorizada: {unidad_nombre}. Autorizadas: {UNIDADES_SR_AUTORIZADAS}'
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:708:        logger.error(f"[SYNC_PROPINAS_SR] Error en sync de {unidad_nombre}: {e}")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:723:    logger.info(f"[SYNC_PROPINAS_SR] {unidad_nombre}: {resultado['estatus']}, "
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:751:    for unidad in UNIDADES_SR_AUTORIZADAS:
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:782:    'UNIDADES_SR_AUTORIZADAS'
/app/backend/modules/finanzas/health.py:270:                and s.get('system_type_normalized', s.get('system_type', '')).upper() in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']
/app/backend/modules/finanzas/cuentas_por_pagar.py:333:        # Consultar MPRO si: no hay filtro, o hay filtro MPRO, o no es filtro exclusivo SR
/app/backend/modules/finanzas/cuentas_por_pagar.py:831:        # COMBINAR SR + MPRO (no fallback)
/app/backend/modules/finanzas/repository_cortes_z.py:182:        if system_type in ['SOFTRESTAURANT', 'SR']:
/app/backend/modules/finanzas/repository_cortes_z.py:618:                if tipo != 'CORE' and system_type in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']:
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:89:        if system_type in ['SOFTRESTAURANT', 'SR']:
/app/backend/modules/finanzas/propinas_tpv/routes.py:94:        if system_type in ['SOFTRESTAURANT', 'SR']:
/app/backend/modules/finanzas/repository_softrestaurant.py:168:        'CIENFUEGOS_SR': 'CIENFUEGOS',
/app/backend/modules/finanzas/repository_softrestaurant.py:239:            logging.warning(f"[SoftRestaurant] sucursal_id parece UUID, no es sucursal SR: {sucursal_id}")
/app/backend/modules/finanzas/carga_historica_ingresos.py:123:    logger.info(f"[HISTORICA_SR] === Iniciando carga histórica: {unidad_nombre} ===")
/app/backend/modules/finanzas/carga_historica_ingresos.py:124:    logger.info(f"[HISTORICA_SR] Bloques a procesar: {len(bloques)}")
/app/backend/modules/finanzas/carga_historica_ingresos.py:147:        logger.info(f"[HISTORICA_SR] Bloque {i}/{len(bloques)}: {bloque['bloque_nombre']}")
/app/backend/modules/finanzas/carga_historica_ingresos.py:193:            logger.error(f"[HISTORICA_SR] Error en bloque {bloque['bloque_nombre']}: {e}")
/app/backend/modules/finanzas/carga_historica_ingresos.py:214:        f"[HISTORICA_SR] {unidad_nombre} completado: "
/app/backend/modules/finanzas/sync_cortes_mpro.py:296:                # Montos - MPRO estructura diferente a SR
/app/backend/modules/compras/service.py:70:            log_compras_adapter_selected("inventarios-fisicos", server_id, system_type, "SR_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:137:            log_compras_adapter_selected("pedidos-vigentes", server_id, system_type, "SR_ADAPTER", sucursal_id)
```

## 2. Comparaciones locales de MPRO / ManagementPro
```text
/app/backend/modules/comercial/service.py:1210:    if system_type.upper() in ['MPRO', 'MANAGEMENTPRO']:
/app/backend/modules/comercial/cache_service.py:94:    Ejemplo: comercial:dashboard:server123:suc001:MANAGEMENTPRO:2026-04-20:periodo=mes
/app/backend/modules/finanzas/tesoreria.py:752:    - system_type in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']
/app/backend/modules/finanzas/tesoreria.py:798:                if system_type not in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']:
/app/backend/modules/finanzas/tesoreria.py:804:                elif system_type in ['MANAGEMENTPRO', 'MPRO']:
/app/backend/modules/finanzas/tesoreria.py:844:            if system_type not in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']:
/app/backend/modules/finanzas/tesoreria.py:849:            elif system_type in ['MANAGEMENTPRO', 'MPRO']:
/app/backend/modules/finanzas/sync_propinas_mpro.py:125:              AND s.system_type IN ('MPRO', 'ManagementPro')
/app/backend/modules/finanzas/health.py:39:    "MANAGEMENTPRO": "SELECT TOP 1 id_venta FROM Venta_Encabezado"
/app/backend/modules/finanzas/health.py:270:                and s.get('system_type_normalized', s.get('system_type', '')).upper() in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']
/app/backend/modules/finanzas/cuentas_por_pagar.py:418:                        "fuente": "MANAGEMENTPRO"
/app/backend/modules/finanzas/cuentas_por_pagar.py:423:                    fuentes_activas.append("MANAGEMENTPRO")
/app/backend/modules/finanzas/cuentas_por_pagar.py:887:                        c['_fuente'] = 'MANAGEMENTPRO'
/app/backend/modules/finanzas/cuentas_por_pagar.py:889:                    fuentes_activas.append("MANAGEMENTPRO")
/app/backend/modules/finanzas/cuentas_por_pagar.py:893:                fuentes_fallidas.append(f"MANAGEMENTPRO: {str(e)[:50]}")
/app/backend/modules/finanzas/cuentas_por_pagar.py:1116:                        "Sistema": "MANAGEMENTPRO"
/app/backend/modules/finanzas/cuentas_por_pagar.py:1118:                fuentes_activas.append("MANAGEMENTPRO")
/app/backend/modules/finanzas/cuentas_por_pagar.py:1122:            fuentes_fallidas.append(f"MANAGEMENTPRO: {str(e)[:50]}")
/app/backend/modules/finanzas/repository_cortes_z.py:186:        elif system_type in ['MANAGEMENTPRO', 'MPRO']:
/app/backend/modules/finanzas/repository_cortes_z.py:618:                if tipo != 'CORE' and system_type in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']:
/app/backend/scripts/run_historical_load_finanzas.py:12:- MANAGEMENTPRO: Cortes Z
/app/backend/scripts/run_historical_load_finanzas.py:613:        # Solo SOFTRESTAURANT y MANAGEMENTPRO
/app/backend/scripts/run_historical_load_finanzas.py:614:        if normalized in ["SOFTRESTAURANT", "MANAGEMENTPRO"]:
/app/backend/scripts/validate_encrypted_server_connectivity.py:15:    --system-type <type>    Filtrar por SOFTRESTAURANT|MANAGEMENTPRO|API
/app/backend/scripts/validate_encrypted_server_connectivity.py:130:        if st_upper in ['MPRO', 'MANAGEMENTPRO', 'MANAGMENT', 'MANAGEMENT']:
/app/backend/scripts/validate_encrypted_server_connectivity.py:192:            system_type_normalized = 'MANAGEMENTPRO'
/app/backend/scripts/validate_encrypted_server_connectivity.py:609:    parser.add_argument('--system-type', type=str, help='Filtrar por SOFTRESTAURANT|MANAGEMENTPRO|API')
/app/backend/scripts/run_historical_load_compras.py:14:- MANAGEMENTPRO: Inventarios, Pedidos, Facturas Proveedor
/app/backend/scripts/run_historical_load_compras.py:717:        # Solo SOFTRESTAURANT y MANAGEMENTPRO
/app/backend/scripts/run_historical_load_compras.py:718:        if normalized in ["SOFTRESTAURANT", "MANAGEMENTPRO"]:
/app/backend/scripts/run_historical_load_24_months.py:212:    Solo servidores con system_type válido (SOFTRESTAURANT o MANAGEMENTPRO).
/app/backend/scripts/run_historical_load_24_months.py:225:        if normalized in ["SOFTRESTAURANT", "MANAGEMENTPRO"]:
/app/backend/server.py:11600:                WHEN UPPER(sc.system_type) IN ('MANAGEMENTPRO', 'MANAGMENTPRO') THEN 'ManagementPro'
/app/backend/api/catalogos_sistemas.py:222:                WHEN UPPER(sc.system_type) IN ('MANAGEMENTPRO', 'MANAGMENTPRO') THEN 'ManagementPro'
/app/backend/core/server_registry.py:63:        if st_upper in ['MPRO', 'MANAGMENTPRO', 'MANAGEMENTPRO', 'MANAGEMENT_PRO']:
/app/backend/core/server_registry.py:64:            return "MANAGEMENTPRO"
/app/backend/core/scheduler/jobs/sync_compras_job.py:218:              AND s.system_type IN ('SOFTRESTAURANT', 'MPRO', 'MANAGEMENTPRO', 'SOFTRESTAURANT_PRO')
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:178:              AND s.system_type IN ('SOFTRESTAURANT', 'MPRO', 'MANAGEMENTPRO', 'SOFTRESTAURANT_PRO')
/app/backend/core/cache_key_builder.py:200:            system_type_normalized="MANAGEMENTPRO",
/app/backend/core/cache_key_builder.py:203:        # Resultado: "comercial:dashboard:abc123:suc001:MANAGEMENTPRO:2026-04-25"
/app/backend/core/system_type_utils.py:12:- Normalizar system_type a valores estándar (MANAGEMENTPRO, SOFTRESTAURANT, API, UNKNOWN)
/app/backend/core/system_type_utils.py:27:    normalized = normalize_system_type("MPRO")  # → "MANAGEMENTPRO"
/app/backend/core/system_type_utils.py:49:    MANAGEMENTPRO = "MANAGEMENTPRO"
/app/backend/core/system_type_utils.py:57:    "MPRO": SystemType.MANAGEMENTPRO,
/app/backend/core/system_type_utils.py:58:    "MANAGEMENTPRO": SystemType.MANAGEMENTPRO,
/app/backend/core/system_type_utils.py:59:    "MANAGEMENT_PRO": SystemType.MANAGEMENTPRO,
/app/backend/core/system_type_utils.py:60:    "MANAGEMENT PRO": SystemType.MANAGEMENTPRO,
/app/backend/core/system_type_utils.py:61:    "MANAGMENTPRO": SystemType.MANAGEMENTPRO,   # Typo común
/app/backend/core/system_type_utils.py:62:    "MANAGMENT_PRO": SystemType.MANAGEMENTPRO,  # Typo común
/app/backend/core/system_type_utils.py:63:    "MANAGMENT PRO": SystemType.MANAGEMENTPRO,  # Typo común
/app/backend/core/system_type_utils.py:64:    "MANAG": SystemType.MANAGEMENTPRO,
/app/backend/core/system_type_utils.py:87:    SystemType.MANAGEMENTPRO: "ManagementPro",
/app/backend/core/system_type_utils.py:102:    - MPRO, MANAGEMENTPRO, MANAGEMENT_PRO, etc. → "MANAGEMENTPRO"
/app/backend/core/system_type_utils.py:111:        str: Uno de SOFTRESTAURANT, MANAGEMENTPRO, API, UNKNOWN
/app/backend/core/system_type_utils.py:140:    return normalize_system_type(system_type) == SystemType.MANAGEMENTPRO.value
/app/backend/core/system_type_utils.py:360:        → "compras:inventarios:server-123:MANAGEMENTPRO:sucursal_id=0021:fecha_inicio=2025-01-01"
```

## 3. Verificar existencia del normalizador central
```text
FALTA: /app/backend/core/system_type_normalizer.py
```

## 4. Correcciones Aplicadas (2026-06-05)

| Archivo | Antes | Después | Estado |
|---------|-------|---------|--------|
| `sync_propinas_softrestaurant.py` | `IN ('SoftRestaurant', 'SOFTRESTAURANT', 'SR')` | `IN ('SoftRestaurant', 'SOFTRESTAURANT', 'SR', 'SOFTRESTAURANT_PRO')` | ✅ Corregido |
| `sync_cortes_softrestaurant.py` | `IN ('SoftRestaurant', 'SOFTRESTAURANT', 'SR')` | `IN ('SoftRestaurant', 'SOFTRESTAURANT', 'SR', 'SOFTRESTAURANT_PRO')` | ✅ Corregido |
| `sync_propinas_mpro.py` | `IN ('MPRO', 'ManagementPro')` | `IN ('MPRO', 'ManagementPro', 'MANAGEMENTPRO')` | ✅ Corregido |

## 5. Archivos con Filtros Correctos

Los siguientes archivos ya tienen filtros completos:

| Archivo | Filtro |
|---------|--------|
| `sync_compras_job.py` | `IN ('SOFTRESTAURANT', 'MPRO', 'MANAGEMENTPRO', 'SOFTRESTAURANT_PRO')` |
| `detect_nuevos_compras_job.py` | `IN ('SOFTRESTAURANT', 'MPRO', 'MANAGEMENTPRO', 'SOFTRESTAURANT_PRO')` |

## 6. Recomendación Futura

Existe el módulo `/app/backend/core/system_type_utils.py` con funciones de normalización (`normalize_system_type()`).
Se recomienda refactorizar los filtros SQL para usar una función centralizada que construya el filtro IN() dinámicamente.

Ejemplo propuesto:
```python
from core.system_type_utils import get_softrestaurant_variants, get_mpro_variants

# En vez de hardcodear:
# AND s.system_type IN ('SoftRestaurant', 'SOFTRESTAURANT', 'SR', 'SOFTRESTAURANT_PRO')

# Usar función centralizada:
sr_filter = build_system_type_sql_filter('SOFTRESTAURANT')
# → "s.system_type IN ('SoftRestaurant', 'SOFTRESTAURANT', 'SR', 'SOFTRESTAURANT_PRO')"
```
