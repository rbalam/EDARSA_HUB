# CLASIFICACIÓN QUIRÚRGICA DE BYPASS
## CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE B.1

**Fecha:** 2025-12-19  
**Estado:** COMPLETADO - CLASIFICACIÓN DE 56 BYPASSES  
**Última actualización:** 2025-12-19 - LOTE 4 COMPLETADO  
**Autor:** Agente E1  

---

## PROGRESO DE MIGRACIÓN

| Lote | Estado | Bypasses Corregidos | Pendientes |
|------|--------|---------------------|------------|
| **Lote 1** | ✅ COMPLETADO | 5 | - |
| **Lote 2** | ✅ COMPLETADO | 5 | - |
| **Lote 3** | ✅ COMPLETADO | 5 | - |
| **Lote 4** | ✅ COMPLETADO | 10 | - |
| **Lote 5** | ✅ COMPLETADO | 5 | - |
| **Lote 6** | ✅ COMPLETADO | 1 | - |
| Lote 7+ | ⏳ PENDIENTE | - | ~20 (Config Escrituras + Reportes + Económicos + Operaciones) |

### Bypasses Corregidos en Lote 1:
- [x] A40 - `execute_edarsa_hub_query()` - Línea 9926
- [x] A26 - `validate_server_access_by_empresa()` - Línea 6096
- [x] A09 - `get_sucursales()` - Línea 1922
- [x] A10 - `get_almacenes()` - Línea 2019
- [x] A06 - `get_tipos_movimiento()` - Línea 1738

### Bypasses Corregidos en Lote 2:
- [x] C6 - `get_categorias()` - Línea 1796
- [x] C7 - `get_departamentos()` - Línea 1838
- [x] C1 - `ping_server()` - Línea 1315
- [x] C8 - `get_sucursales_config()` - Línea 2129
- [x] C9 - `sync_sucursales_config()` - Línea 2157

### Bypasses Corregidos en Lote 3:
- [x] C2 - `get_inventarios_list()` - Línea 2603 - **OK con observación (MongoDB fallback)**
- [x] C3 - `get_pendientes_descargar()` - Línea 2708 - **OK con observación (MongoDB fallback)**
- [x] C5 - `get_report_filters()` - Línea 2961 - **OK con observación (MongoDB fallback)**
- [x] C1 - `get_almacenes_softrestaurant()` - Línea 2541 - **OK con observación (MongoDB fallback)**
- [x] C8 - `ejecutar_consulta_catalogo()` - Línea 5459 - **OK con observación (MongoDB fallback)**

### Bypasses Corregidos en Lote 4:
- [x] `listar_tablas()` - Línea 8911 - Explorador SQL
- [x] `listar_columnas()` - Línea 8955 - Explorador SQL
- [x] `listar_relaciones()` - Línea 9000 - Explorador SQL
- [x] `preview_tabla()` - Línea 9045 - Explorador SQL
- [x] `ejecutar_query_libre()` - Línea 9090 - Explorador SQL (solo Admin)
- [x] `ejecutar_script_sql()` - Línea 9135 - Explorador SQL (solo Admin)
- [x] `debug_test_queries()` - Línea 5654 - Debug
- [x] `buscar_en_bd()` - Línea 11620 - Consulta
- [x] `sql_server_health_check()` - Línea 12722 - Health Check
- [x] `sql_server_test_query()` - Línea 12785 - Health Check

### Bypasses Corregidos en Lote 6:
- [x] `guardar_script_pendiente()` - Línea 11010 - Solo lectura servidor, escritura en MongoDB (documento operativo)

**Reportes:**
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md`
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md`
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md` (v2.0 - Diagnóstico consolidado)
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md`
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE5_REPORT.md`
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE6_REPORT.md`

---

## SUBFASE D - REGULARIZACIÓN CATÁLOGO MAESTRO (2025-12-19)

**Estado:** CERRADA - BRECHA DESCARTADA

Diagnóstico reveló:
- EDARSAHUB contiene 13 servidores (9 activos)
- MongoDB `db.servers` está vacío (0 documentos)
- **NO hay brecha de catálogo maestro**
- `config_origin: EDARSAHUB_SQL` confirmado

Ver: `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md`

---

## 1. RESUMEN EJECUTIVO

Se han analizado y clasificado los **56 accesos directos** a `db.servers.find_one(...)` o `db.servers.find(...)` en el archivo `/app/backend/server.py`. Estos bypasses ignoran el módulo centralizado `core/server_registry.py` que implementa correctamente la arquitectura EDARSAHUB-first.

### Estadísticas de Clasificación (Actualizado post-Lote 6):

| Categoría | Original | Migrados | Pendientes | Descripción |
|-----------|----------|----------|------------|-------------|
| **A - MIGRAR** | 45 | 31 | 14 | Resuelven conexión SQL externa |
| **B - NO MIGRAR** | 5 | 0 | 5 | Uso legítimo (no tocar) |
| **C - REVISAR** | 3 | 0 | 3 | Casos mixtos |
| **D - LEGACY** | 3 | 0 | 3 | Código posiblemente obsoleto |
| **TOTAL** | 56 | 31 | 25 | |

### Módulos Afectados:

| Módulo | Líneas Afectadas | Prioridad |
|--------|------------------|-----------|
| Configuración de Servidores | 1315-1731 | P0 |
| Reportes/Catálogos | 1738-1922 | P1 |
| Almacenes/Sucursales | 2019-2606 | P1 |
| Inventarios | 2821-3026 | P1 |
| Compras | 4309-8525 | P1 |
| Explorador SQL | 8746-8961 | P2 |
| EDARSA HUB Query Helper | 9926 | P0 |
| Explorador Avanzado | 10767-10892 | P2 |
| Búsqueda Global | 11406 | P2 |
| Catálogo de Consultas | 11641-11877 | P2 |
| Health Check | 12522-12574 | P2 |

---

## 2. INVENTARIO COMPLETO DE HALLAZGOS

### 2.1 Categoría A - MIGRAR A server_registry.py (45 instancias)

Estos casos **DEBEN** usar `server_registry.py` porque resuelven credenciales SQL para conexión externa.

| ID | Línea | Endpoint/Función | Uso MongoDB | ¿Resuelve SQL? | Riesgo | Acción |
|----|-------|------------------|-------------|----------------|--------|--------|
| A01 | 1315 | `test_server_connection` | `db.servers.find_one({"id": server_id})` | Sí - host/port/user/pass para execute_sql_query | ALTO | Migrar a `get_server_connection_info()` |
| A02 | 1531 | `validate_server_query` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - conexión SQL para validar query | ALTO | Migrar |
| A03 | 1622 | `save_server_query` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - lectura de config servidor | MEDIO | Migrar |
| A04 | 1667 | `get_server_queries` | `db.servers.find_one({"id": server_id, "active": True})` | Parcial - lee config queries | MEDIO | Migrar |
| A05 | 1721 | `delete_server_query` | `db.servers.find_one({"id": server_id, "active": True})` | Parcial | BAJO | Migrar |
| A06 | 1738 | `get_tipos_movimiento` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A07 | 1782 | `get_categorias` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A08 | 1824 | `get_departamentos` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A09 | 1922 | `get_sucursales` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A10 | 2019 | `get_almacenes` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A11 | 2091 | `get_sucursales_config` | `db.servers.find_one({"id": server_id, "active": True})` | Parcial - valida existencia | MEDIO | Migrar |
| A12 | 2119 | `sync_sucursales_config` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A13 | 2439 | `get_almacenes_softrestaurant` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A14 | 2501 | `get_inventarios_list` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A15 | 2606 | `get_pendientes_descargar` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A16 | 2821 | `generate_inventory_report` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A17 | 2859 | `get_report_filters` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A18 | 3026 | `generar_analisis_inventario` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A19 | 4309 | `get_detalle_movimientos_producto` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A20 | 4542 | `get_detalle_ventas_producto` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A21 | 5094 | `export_inventario_comparativo` | `db.servers.find_one({"id": request.server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A22 | 5357 | `ejecutar_consulta_catalogo` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A23 | 5423 | `ejecutar_consulta_personalizada` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A24 | 5502 | `debug_mpro_calculo` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | MEDIO | Migrar |
| A25 | 5809 | `get_dashboard_inventory` | `db.servers.find_one(query)` | Sí - execute_sql_query | ALTO | Migrar |
| A26 | 6096 | `validate_server_access_by_empresa` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - credenciales | ALTO | Migrar |
| A27 | 6975 | `obtener_productos_para_captura` | `db.servers.find_one({"id": request.server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A28 | 7090 | `realizar_auditoria_operativa` | `db.servers.find_one({"id": request.server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A29 | 7794 | `obtener_detalle_movimientos_post` | `db.servers.find_one({"id": request.server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A30 | 7971 | `obtener_detalle_consumos_post` | `db.servers.find_one({"id": request.server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A31 | 8313 | `obtener_analisis_compras` | `db.servers.find_one({"id": request.server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A32 | 8460 | `obtener_facturas_proveedor` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A33 | 8525 | `obtener_detalle_factura` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A34 | 8746 | `listar_tablas` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | MEDIO | Migrar |
| A35 | 8786 | `listar_columnas` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | MEDIO | Migrar |
| A36 | 8827 | `listar_relaciones` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | MEDIO | Migrar |
| A37 | 8874 | `preview_tabla` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | MEDIO | Migrar |
| A38 | 8915 | `ejecutar_query_libre` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A39 | 8961 | `ejecutar_script_sql` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A40 | 9926 | `execute_edarsa_hub_query` | `db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})` | Sí - CRÍTICO: helper para EDARSA HUB | **CRÍTICO** | Migrar primero |
| A41 | 10767 | `guardar_script_standby` | `db.servers.find_one({"id": server_id, "active": True})` | Parcial | BAJO | Migrar |
| A42 | 10892 | `ejecutar_script_con_credenciales` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query con creds admin | ALTO | Migrar |
| A43 | 11406 | `buscar_global_bd` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | MEDIO | Migrar |
| A44 | 11641 | `ejecutar_consulta_catalogo_v2` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
| A45 | 11877 | `ejecutar_consulta_custom` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |

---

### 2.2 Categoría B - NO MIGRAR (5 instancias)

Estos casos usan MongoDB **legítimamente** para cache, conteos, métricas o listados sin resolver credenciales SQL.

| ID | Línea | Endpoint/Función | Uso MongoDB | ¿Resuelve SQL? | ¿Cache/Log? | Clasificación | Justificación |
|----|-------|------------------|-------------|----------------|-------------|---------------|---------------|
| B01 | 5989 | `get_dashboard_servers` | `db.servers.find({"active": True, "queries_configured": True})` | No | Listado | NO MIGRAR | Solo lista servidores para selector UI, no conecta |
| B02 | 6000 | `get_dashboard_metrics` | `db.servers.count_documents({"active": True})` | No | Conteo | NO MIGRAR | Solo cuenta servidores activos |
| B03 | 6003 | `get_dashboard_metrics` | `db.servers.count_documents({"active": True, "queries_configured": True})` | No | Conteo | NO MIGRAR | Solo cuenta servidores configurados |
| B04 | 2302 | `get_sucursales_globales` | `db.servers.find({"id": {"$in": server_ids}})` | No | Enriquecimiento | NO MIGRAR | Solo enriquece nombres de servidor en resultado |
| B05 | 2368 | `get_unidades_negocio` | `db.servers.find({"id": {"$in": server_ids}})` | No | Metadata | NO MIGRAR | Solo obtiene system_type para respuesta |

---

### 2.3 Categoría C - REVISAR MANUALMENTE (3 instancias)

Requieren análisis adicional para determinar si son migración o uso legítimo.

| ID | Línea | Endpoint/Función | Uso MongoDB | Duda | Acción Recomendada |
|----|-------|------------------|-------------|------|-------------------|
| C01 | 1636 | `save_server_query` | `db.servers.update_one({"id": server_id}, ...)` | Escribe configuración de query en MongoDB | Revisar si la config de queries debe ir a EDARSAHUB |
| C02 | 1642 | `save_server_query` | `db.servers.find_one({"id": server_id})` | Lee servidor post-update | Depende de C01 |
| C03 | 1649 | `save_server_query` | `db.servers.update_one({"id": server_id}, ...)` | Escribe flag queries_configured | Revisar si el flag debe ir a EDARSAHUB |
| C04 | 1726 | `delete_server_query` | `db.servers.update_one({"id": server_id}, ...)` | Elimina configuración de query | Revisar si la config de queries debe ir a EDARSAHUB |

**Nota sobre C01-C04:** Estas operaciones de escritura actualizan configuración de queries SQL en MongoDB. El diseño actual asume que `queries_configured`, `query_ventas`, `query_inventario`, etc. se almacenan en MongoDB. Si EDARSAHUB es el maestro, deberían escribirse allá primero y sincronizar a MongoDB.

---

### 2.4 Categoría D - LEGACY / DEPRECAR (3 instancias)

Código potencialmente obsoleto o redundante.

| ID | Línea | Endpoint/Función | Motivo | Acción Recomendada |
|----|-------|------------------|--------|-------------------|
| D01 | 12522 | `sql_server_health` | Helper de health check usa bypass directo | Evaluar si el endpoint sigue en uso |
| D02 | 12574 | `sql_server_test_query` | Similar a D01 | Evaluar consolidación con D01 |
| D03 | - | (potencial) | Revisar si hay endpoints deshabilitados en comentarios | Limpiar código muerto |

---

## 3. USOS LEGÍTIMOS DE MONGODB (NO TOCAR)

Los siguientes usos de MongoDB son correctos y **NO deben migrarse**:

| Colección | Propósito | Ejemplo de Uso |
|-----------|-----------|----------------|
| `server_status` | Cache de estado de conexión | Línea 1337: `db.server_status.update_one(...)` |
| `server_sucursales_config` | Configuración de visibilidad de sucursales | Línea 2096: `db.server_sucursales_config.find(...)` |
| `comercial_dashboard_cache` | Cache de datos comerciales | Módulo comercial |
| `kpis_cache` | Cache de KPIs calculados | Varios módulos |
| `audit_log` | Logs de auditoría | Varios módulos |
| `jobs_*` | Estado de jobs del scheduler | Core scheduler |
| `scripts_pendientes` | Scripts SQL en stand-by | Línea 10785 |
| `consultas_custom` | Catálogo de consultas personalizadas | Línea 11872 |

---

## 4. PRIMER LOTE RECOMENDADO (MÁXIMO 5 CAMBIOS)

### Criterios de Selección del Lote 1:
1. **Mayor impacto** - Afecta módulos críticos (Tablero Ejecutivo, Comercial)
2. **Menor riesgo** - Funciones aisladas con scope claro
3. **Fácil validación** - Endpoints que pueden probarse individualmente
4. **Patrón replicable** - Sirven como modelo para los demás

### Lote 1 Propuesto:

| Prioridad | ID | Línea | Función | Justificación |
|-----------|-----|-------|---------|---------------|
| 1 | **A40** | 9926 | `execute_edarsa_hub_query()` | HELPER CENTRAL que ya debería usar registry. Afecta todos los endpoints de RH y catálogos EDARSA HUB |
| 2 | **A26** | 6096 | `validate_server_access_by_empresa()` | Función de validación RBAC usada por múltiples endpoints de Compras |
| 3 | **A09** | 1922 | `get_sucursales()` | Catálogo fundamental usado por Tablero Comercial y filtros |
| 4 | **A10** | 2019 | `get_almacenes()` | Catálogo fundamental usado por todos los módulos de inventario |
| 5 | **A06** | 1738 | `get_tipos_movimiento()` | Catálogo usado en análisis de inventario |

### Justificación del Lote 1:
- **A40 primero:** Es un helper que otros endpoints usan indirectamente. Corregirlo establece el patrón correcto para todo EDARSA HUB.
- **A26 segundo:** La función de validación RBAC es crítica para seguridad y es compartida por endpoints de Compras.
- **A09, A10, A06:** Son catálogos fundamentales llamados frecuentemente. Su corrección demuestra el patrón para los ~30 endpoints de catálogos restantes.

---

## 5. RIESGOS DEL LOTE 1

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Falla de conexión a EDARSAHUB | Baja | Alto | `server_registry.py` ya tiene fallback a MongoDB |
| Incompatibilidad de schema | Media | Medio | Verificar que campos devueltos por SQL incluyen `host`, `port`, `database`, `username`, `password` |
| Regresión en módulos dependientes | Media | Alto | Testing exhaustivo post-migración |
| Performance degradada | Baja | Bajo | SQL es más rápido que MongoDB para lookups por ID |

---

## 6. PRUEBAS NECESARIAS POR LOTE

### Para Lote 1:
1. **Test unitario:** Verificar que `get_server_connection_info()` devuelve credenciales válidas
2. **Test de integración:**
   - `GET /api/servers/{id}/sucursales` - debe retornar lista
   - `GET /api/servers/{id}/almacenes` - debe retornar lista
   - `GET /api/servers/{id}/tipos-movimiento` - debe retornar lista
3. **Test funcional:**
   - Cargar Tablero Comercial con filtro de servidor
   - Cargar módulo Compras y verificar dropdown de sucursales
4. **Test de regresión:**
   - Ejecutar auditoría operativa de Compras
   - Verificar que catálogos RH siguen funcionando

### Herramientas de Test:
```bash
# Test de conexión básica
curl -X GET "$API_URL/api/servers/test-connection/{SERVER_ID}" -H "Authorization: Bearer $TOKEN"

# Test de catálogo sucursales
curl -X GET "$API_URL/api/servers/{SERVER_ID}/sucursales" -H "Authorization: Bearer $TOKEN"

# Test de catálogo almacenes
curl -X GET "$API_URL/api/servers/{SERVER_ID}/almacenes" -H "Authorization: Bearer $TOKEN"
```

---

## 7. PROCEDIMIENTO DE ROLLBACK

### Rollback Inmediato (si falla en producción):
1. En `.env` del backend: `USE_SQL_FOR_SERVERS=false`
2. Reiniciar backend: `sudo supervisorctl restart backend`
3. El registry automáticamente usará MongoDB como fallback

### Rollback por Endpoint:
Si solo un endpoint falla, se puede revertir ese archivo específico usando:
```bash
git checkout HEAD~1 -- /app/backend/server.py
sudo supervisorctl restart backend
```

### Rollback de Lote Completo:
Si el lote completo falla:
1. Revertir los cambios del lote
2. Documentar la causa del fallo
3. Ajustar la estrategia antes de reintentar

---

## 8. CRONOGRAMA PROPUESTO

| Fase | Descripción | Dependencia |
|------|-------------|-------------|
| B.1 | Clasificación (ESTE DOCUMENTO) | Ninguna |
| C.1 | Implementación Lote 1 (5 cambios) | Aprobación usuario |
| C.2 | Testing Lote 1 | C.1 completado |
| C.3 | Validación usuario Lote 1 | C.2 exitoso |
| C.4 | Implementación Lote 2 (10 cambios) | C.3 aprobado |
| ... | Lotes adicionales | Iterativo |

---

## 9. PATRÓN DE MIGRACIÓN RECOMENDADO

### Antes (Bypass):
```python
server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
if not server:
    raise HTTPException(status_code=404, detail="Servidor no encontrado")

results = execute_sql_query(
    server['host'], server['port'], server['database'],
    server['username'], server['password'], query
)
```

### Después (Registry):
```python
from core.server_registry import get_server_connection_info

conn_info = await get_server_connection_info(server_id, db=db, user=current_user)
if not conn_info:
    raise HTTPException(status_code=404, detail="Servidor no encontrado")

results = execute_sql_query(
    conn_info['host'], conn_info['port'], conn_info['database'],
    conn_info['username'], conn_info['password'], query
)
```

### Beneficios:
- EDARSAHUB consultado primero (fuente maestra)
- Fallback automático a MongoDB si SQL falla
- Descifrado de secretos centralizado
- Validación RBAC integrada
- Logging de origen de config (`config_origin`)

---

## 10. DICTAMEN FINAL

### Estado: CLASIFICACIÓN COMPLETADA

**Hallazgos clave:**
- 80% de los bypasses (45/56) **DEBEN** migrarse a `server_registry.py`
- 9% (5/56) son usos legítimos de MongoDB que **NO** deben tocarse
- 5% (3/56) requieren revisión adicional (escrituras de config)
- 5% (3/56) son potencialmente legacy

**Recomendación:**
Proceder con SUBFASE C iniciando con el Lote 1 de 5 cambios, priorizando:
1. Helper central `execute_edarsa_hub_query()`
2. Función RBAC `validate_server_access_by_empresa()`
3. Catálogos fundamentales (sucursales, almacenes, tipos_movimiento)

**Acción requerida:**
Usuario debe autorizar SUBFASE C - Lote 1 para proceder con la corrección quirúrgica.

---

**Documento generado por Agente E1 - EDARSA HUB**  
**Fecha:** 2025-12-19  
**Versión:** 1.0
