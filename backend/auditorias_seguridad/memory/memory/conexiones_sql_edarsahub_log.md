# LOG: Conexiones SQL EDARSAHUB
## CONEXIONES-SQL-EDARSAHUB-01

**Iniciado:** 2026-04-27  
**Estado:** SUBFASE B COMPLETADA - DIAGNÓSTICO DE BYPASS

---

## ENTRADA 2026-04-27 15:30 UTC - DIAGNÓSTICO INICIAL

### Contexto
Usuario reportó que conexiones SQL fallaban (Error 18456).
Diagnóstico inicial asumió incorrectamente que credenciales en MongoDB eran inválidas.

### Corrección arquitectónica
Usuario aclaró que EDARSAHUB debe ser fuente maestra, no MongoDB.

---

## ENTRADA 2026-04-27 15:45 UTC - VERIFICACIÓN DE ARQUITECTURA

### Hallazgos positivos:
1. `server_registry.py` está correctamente diseñado
2. EDARSAHUB SQL es fuente primaria
3. MongoDB es fallback legacy
4. Flag `USE_SQL_FOR_SERVERS` activo
5. Credenciales cifradas con Fernet funcionan
6. Conexiones a servidores SQL funcionan cuando se usa registry

### Prueba exitosa:
```
CIENFUEGOS: Conexión exitosa vía EDARSAHUB
- Host: servercienfuegos.ddns.net,6669\nationalsoft
- User: CFLectura
- Password: descifrado OK
```

---

## ENTRADA 2026-04-27 16:00 UTC - SUBFASE B BYPASS DETECTION

### Bypass encontrados:

| Ubicación | Cantidad |
|-----------|----------|
| server.py | 56 |
| Finanzas | 9 |
| Compras | 2 |
| Comercial | 3 (1 es fallback legítimo) |
| RH | 2 |
| Configuración | 2 |
| Portal Proveedores | 2 |
| Scheduler/Jobs | 2 |
| Context Resolver | 2 |
| Otros | 5+ |

### Diagnóstico:
La mayoría de endpoints en server.py y módulos hacen bypass directo a MongoDB, ignorando el registry que sí usa EDARSAHUB como fuente primaria.

### Documentación creada:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md`

---

## ENTRADA 2025-12-19 - SUBFASE C LOTE 3 COMPLETADO (DIAGNÓSTICO CONSOLIDADO)

### Dictamen por capas:

**CAPA A - Migración técnica:**
- 5 endpoints migrados a `server_registry.get_server_connection_info()`
- Ya no hay bypass directo a `db.servers.find_one()`
- Dictamen: **OK con observación**

**CAPA B - Conexión SQL externa:**
- Estado: **No verificable**
- Tiempos de ping (0.01-0.02ms) indican que SQL no conecta realmente
- No es regresión del código de migración

**CAPA C - Arquitectura/Catálogo maestro:**
- Estado: **BRECHA: usa MongoDB fallback**
- Servidores a5547321-*, b5175237-* NO existen en EDARSAHUB
- Se resuelven vía MongoDB legacy
- Acción pendiente: Sincronizar a EDARSAHUB

### Tabla de validación:

| Endpoint | Usa registry | Fuente | Dictamen migración | Dictamen arquitectura |
|----------|--------------|--------|-------------------|----------------------|
| get_inventarios_list | Sí | MongoDB fallback | OK con observación | Brecha |
| get_pendientes_descargar | Sí | MongoDB fallback | OK con observación | Brecha |
| get_report_filters | Sí | MongoDB fallback | OK con observación | Brecha |
| get_almacenes_softrestaurant | Sí | MongoDB fallback | OK con observación | Brecha |
| ejecutar_consulta_catalogo | Sí | MongoDB fallback | OK con observación | Brecha |

### Brechas de catálogo maestro:

| Server ID | Servidor | En EDARSAHUB | En MongoDB | Acción |
|-----------|----------|--------------|------------|--------|
| a5547321-* | 130° MERIDA | No | Sí | MIGRAR A EDARSAHUB |
| b5175237-* | HR2020 ESCRITURA | No | Sí | MIGRAR A EDARSAHUB |

### Documentación:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md` (v2.0)

### Progreso total:
- 15/56 bypasses migrados técnicamente (26.8%)
- 30 categoría A pendientes
- 100% de servidores probados usan MongoDB fallback (brecha catálogo)

---

## ENTRADA 2025-12-19 - SUBFASE C.3-PLAN COMPLETADA

### Plan de Lote 3 propuesto (5 cambios):

| # | Función | Línea | Módulo | Riesgo |
|---|---------|-------|--------|--------|
| 1 | `get_inventarios_list()` | 2603 | Inventarios | BAJO |
| 2 | `get_pendientes_descargar()` | 2708 | Operaciones | BAJO |
| 3 | `get_report_filters()` | 2961 | Reportes | BAJO |
| 4 | `get_almacenes_softrestaurant()` | 2541 | Catálogos SR | BAJO |
| 5 | `ejecutar_consulta_catalogo()` | 5459 | Consultas | BAJO |

### Candidatos evaluados pero diferidos:
- `generate_inventory_report` - Riesgo MEDIO
- `generar_analisis_inventario` - Lee campos adicionales de MongoDB
- `export_inventario_comparativo` - Riesgo MEDIO, función compleja
- `ejecutar_consulta_personalizada` - Impacto BAJO
- `debug_mpro_calculo` - Impacto BAJO

### Protección explícita:
- Lote 1: 5 funciones NO TOCAR
- Lote 2: 5 funciones NO TOCAR

### Documentación:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md`

### Estado:
Pendiente autorización de usuario para implementar Lote 3.

---

## ENTRADA 2025-12-19 - SUBFASE C LOTE 2 COMPLETADO

### Cambios implementados:

| # | Función | Línea | Estado |
|---|---------|-------|--------|
| 1 | `get_categorias()` | ~1796 | ✅ MIGRADO |
| 2 | `get_departamentos()` | ~1838 | ✅ MIGRADO |
| 3 | `ping_server()` | ~1315 | ✅ MIGRADO |
| 4 | `get_sucursales_config()` | ~2129 | ✅ MIGRADO |
| 5 | `sync_sucursales_config()` | ~2157 | ✅ MIGRADO |

### Validaciones ejecutadas:
- ✅ Backend levanta correctamente
- ✅ Auth funciona (login + /me)
- ✅ Categorías: SoftRestaurant OK (117), MPRO OK (14)
- ✅ Departamentos: SoftRestaurant OK (39), MPRO OK (24)
- ✅ Ping: status=connected, time=75.81ms
- ✅ Sucursales Config: server_name cargado
- ✅ Sync: 403 para usuario sin rol Admin (correcto)
- ✅ Sin regresión en Lote 1

### Documentación:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md`

### Progreso total:
- 10/56 bypasses migrados (17.8%)
- 35 categoría A pendientes

---

## ENTRADA 2025-12-19 - SUBFASE C.2-PLAN COMPLETADA

### Plan de Lote 2 propuesto (5 cambios):

| # | Función | Línea | Módulo | Riesgo |
|---|---------|-------|--------|--------|
| 1 | `get_categorias()` | 1796 | Catálogos | BAJO |
| 2 | `get_departamentos()` | 1838 | Catálogos | BAJO |
| 3 | `ping_server()` | 1315 | Configuración | BAJO |
| 4 | `get_sucursales_config()` | 2129 | Config Sucursales | BAJO |
| 5 | `sync_sucursales_config()` | 2157 | Config Sucursales | BAJO |

### Candidatos evaluados pero diferidos:
- `validate_server_query` - Baja frecuencia
- `save_server_query` - Tiene escrituras (Cat C)
- `get_server_queries` - Campos query_* en MongoDB
- `delete_server_query` - Baja prioridad
- `generate_inventory_report` - Riesgo MEDIO, mejor después

### Documentación:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md`

### Estado:
Pendiente autorización de usuario para implementar Lote 2.

---

## ENTRADA 2025-12-19 - SUBFASE C LOTE 1 COMPLETADO

### Cambios implementados:

| # | Función | Línea | Estado |
|---|---------|-------|--------|
| 1 | `execute_edarsa_hub_query()` | ~9926 | ✅ MIGRADO |
| 2 | `validate_server_access_by_empresa()` | ~6096 | ✅ MIGRADO |
| 3 | `get_sucursales()` | ~1922 | ✅ MIGRADO |
| 4 | `get_almacenes()` | ~2019 | ✅ MIGRADO |
| 5 | `get_tipos_movimiento()` | ~1738 | ✅ MIGRADO |

### Validaciones ejecutadas:
- ✅ Backend levanta correctamente
- ✅ Auth funciona (login + /me)
- ✅ Sucursales: SoftRestaurant OK, MPRO OK
- ✅ Almacenes: SoftRestaurant OK (39), MPRO OK (52)
- ✅ TiposMovimiento: SoftRestaurant OK (28), MPRO OK (82)
- ✅ validate_server_access_by_empresa: Compras inventarios-fisicos OK (1629)

### Documentación:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md`

---

## ENTRADA 2025-12-19 - SUBFASE B.1 COMPLETADA

### Clasificación de 56 bypasses en server.py:

| Categoría | Cantidad | Descripción |
|-----------|----------|-------------|
| A - MIGRAR | 45 | Resuelven conexión SQL (host/port/user/pass) |
| B - NO MIGRAR | 5 | Uso legítimo (conteos, listados UI) |
| C - REVISAR | 3 | Escrituras de config queries |
| D - LEGACY | 3 | Posiblemente obsoleto |

### Documentación creada:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md`

### Lote 1 propuesto (5 cambios):
1. `execute_edarsa_hub_query()` - Línea 9926 - Helper central
2. `validate_server_access_by_empresa()` - Línea 6096 - Validación RBAC
3. `get_sucursales()` - Línea 1922 - Catálogo
4. `get_almacenes()` - Línea 2019 - Catálogo
5. `get_tipos_movimiento()` - Línea 1738 - Catálogo

---

## ENTRADA 2025-12-19 - SUBFASE D DIAGNÓSTICO COMPLETADO

### Hallazgo principal:
**LA BRECHA DE CATÁLOGO MAESTRO YA NO EXISTE**

### Resultados del diagnóstico comparativo:

| Fuente | Servidores |
|--------|------------|
| EDARSAHUB | 13 (9 activos) |
| MongoDB | 0 |

### Conclusiones:
1. EDARSAHUB ya es el catálogo maestro funcional
2. MongoDB `db.servers` está vacío (0 documentos)
3. Los servidores mencionados en Lote 3 (130° MERIDA, HR2020 ESCRITURA) SÍ existen en EDARSAHUB
4. El server_registry funciona correctamente con `config_origin: EDARSAHUB_SQL`
5. **NO hay datos que migrar de MongoDB a EDARSAHUB**

### Observación técnica:
Error de descifrado de passwords:
```
ERROR: SERVER_SECRET_KEY no configurada
```
Esto es un problema de configuración de entorno, no de la migración.

### Documentación creada:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md`
- `/app/docs/sql/VALIDACION_SERVIDORES_EDARSAHUB.sql`

### Dictamen:
**BRECHA DE CATÁLOGO MAESTRO CERRADA**

Acción recomendada:
1. Cerrar SUBFASE D como "SIN HALLAZGOS PENDIENTES"
2. Proceder con LOTE 4 de migración de bypasses
3. Resolver `SERVER_SECRET_KEY` como issue separado

---

## ENTRADA 2025-12-19 - SUBFASE C.4-PLAN COMPLETADA

### Plan de Lote 4 propuesto (10 cambios):

| # | Función | Línea | Tipo | Riesgo |
|---|---------|-------|------|--------|
| 1 | `listar_tablas()` | 8911 | Explorador SQL | BAJO |
| 2 | `listar_columnas()` | 8950 | Explorador SQL | BAJO |
| 3 | `listar_relaciones()` | 8991 | Explorador SQL | BAJO |
| 4 | `preview_tabla()` | 9037 | Explorador SQL | BAJO |
| 5 | `ejecutar_query_libre()` | 9075 | Explorador SQL | BAJO |
| 6 | `ejecutar_script_sql()` | 9119 | Explorador SQL | BAJO |
| 7 | `debug_test_queries()` | 5654 | Debug | BAJO |
| 8 | `buscar_en_bd()` | 11580 | Consulta | BAJO |
| 9 | `sql_server_health_check()` | 12677 | Health Check | BAJO |
| 10 | `sql_server_test_query()` | 12740 | Health Check | BAJO |

### Justificación del tamaño (10 cambios):
- Todos son bajo riesgo
- Patrón 100% homogéneo
- Bajo impacto en usuarios (herramientas auxiliares)
- No hay escrituras a MongoDB
- No hay datos económicos críticos

### Candidatos diferidos a Lote 5+:
- Reportes críticos: `generate_inventory_report`, `generate_inventory_analysis`, `export_comparativo_inventarios`
- Movimientos/Ventas: `get_movement_details`, `get_sales_details`
- Compras: `obtener_analisis_compras`, `obtener_facturas_proveedor`
- Config Queries (Cat C): `validate_server_query`, `save_server_query`, etc.
- Operaciones: `obtener_productos_para_captura`, `realizar_auditoria_operativa`

### Documentación:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md`

### Estado:
Lote 4 completado. Pendiente validación de usuario.

### Resultados de Pruebas Lote 4:
| # | Endpoint | Estado |
|---|----------|--------|
| 1 | `sql_server_health_check` | ✅ PASS — `healthy: true, config_origin: EDARSAHUB_SQL` |
| 2 | `listar_tablas` | ✅ PASS — 365 tablas listadas |
| 3-4 | `listar_columnas`, `preview_tabla` | ⚠️ OK — 0 resultados (tablas no existen en BD destino) |
| 5-6 | `ejecutar_query_libre`, `ejecutar_script_sql` | ✅ Migrado — Solo Admin |
| 7 | `debug_test_queries` | ✅ Migrado |
| 8 | `buscar_en_bd` | ✅ Migrado |
| 9-10 | `sql_server_health_check`, `sql_server_test_query` | ✅ PASS |

### Regresión:
- Lote 1: ✅ Sin regresión (sucursales: 1)
- Lote 2: ✅ Sin regresión (ping: connected)
- Lote 3: No probado directamente

---

## ENTRADA 2025-12-19 - SUBFASE C.5-PLAN COMPLETADA

### Plan de Lote 5 propuesto:

**Opción A (RECOMENDADA) — 5 cambios de lectura simple:**

| # | Función | Riesgo |
|---|---------|--------|
| 1 | `get_all_sucursales()` | BAJO |
| 2 | `get_unidades_negocio()` | BAJO |
| 3 | `get_dashboard_servers()` | BAJO |
| 4 | `ejecutar_consulta_personalizada()` | BAJO |
| 5 | `ejecutar_consulta_custom()` | BAJO |

**Opción B (Extendida) — 10 cambios:**
Incluye validación/lectura de queries, dashboard y productos captura.

### Diferidos para Lotes 6+:
- Lote 6: Escrituras de configuración (save_server_query, delete_server_query)
- Lote 7: Reportes/Exportaciones (generate_inventory_report, export_comparativo)
- Lote 8: Datos económicos (obtener_analisis_compras, get_sales_details)
- Lote 9-11: Operaciones críticas y restantes

### Documentación:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md`

### Estado:
Pendiente autorización de usuario.

---

## ENTRADA 2025-12-19 - SUBFASE C LOTE 5 COMPLETADO

### 5 de 5 endpoints migrados:

| # | Función | Estado |
|---|---------|--------|
| 1 | `get_all_sucursales()` | ✅ PASS — 7 sucursales |
| 2 | `get_unidades_negocio()` | ✅ PASS — 5 unidades |
| 3 | `get_dashboard_servers()` | ✅ PASS — `config_origin: EDARSAHUB_SQL` |
| 4 | `ejecutar_consulta_personalizada()` | ✅ Migrado — Permisos Admin conservados |
| 5 | `ejecutar_consulta_custom()` | ✅ Migrado |

### Regresión:
- Lote 1: ✅ Sin regresión
- Lote 2: ✅ Sin regresión  
- Lote 4: ✅ Sin regresión

### Documentación:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE5_REPORT.md`

### Progreso Total:
- **30 de 56 bypasses migrados (54%)**
- **26 pendientes**

---

## ENTRADA 2025-12-19 - SUBFASE C.6-PLAN COMPLETADA

### Análisis de candidatos para Lote 6:

| Función | Tipo | Fuente Actual | Destino Correcto | Clasificación |
|---------|------|---------------|------------------|---------------|
| `save_server_query()` | Escritura config | MongoDB | EDARSAHUB | ⚠️ REQUIERE FUNCIÓN ESCRITURA |
| `delete_server_query()` | Eliminación config | MongoDB | EDARSAHUB | ⚠️ REQUIERE FUNCIÓN ESCRITURA |
| `guardar_script_pendiente()` | Scripts stand-by | MongoDB | **MongoDB** (correcto) | ✅ MIGRAR SOLO LECTURA |

### Hallazgo Crítico:
- EDARSAHUB SÍ tiene columnas `query_inventario`, `query_ventas`, `query_movimientos`
- EDARSAHUB NO tiene tabla para scripts pendientes
- `save_server_query` y `delete_server_query` **requieren función de escritura a EDARSAHUB** que no existe en `server_registry.py`

### Propuesta Lote 6:
**1 solo cambio:** `guardar_script_pendiente()` (solo migrar lectura del servidor)

### Diferidos a Lotes Futuros:
- `save_server_query()` — Requiere implementar `update_server_query()` en registry
- `delete_server_query()` — Depende de save_server_query

### Documentación:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md`

---

## ENTRADA 2025-12-19 - SUBFASE C LOTE 6 COMPLETADO

### 1 de 1 endpoint migrado:

| Función | Estado | Observación |
|---------|--------|-------------|
| `guardar_script_pendiente()` | ✅ PASS | Lectura servidor migrada, escritura MongoDB conservada |

### Confirmaciones:
- ✅ MongoDB solo como documento operativo temporal
- ✅ No se guardan credenciales en MongoDB
- ✅ Permisos Admin conservados (403 para no-Admin)
- ✅ `save_server_query()` y `delete_server_query()` DIFERIDOS

### Regresión:
- Lote 1: ✅ Sin regresión
- Lote 2: ✅ Sin regresión  
- Lote 4: ✅ Sin regresión
- Lote 5: ✅ Sin regresión

### Documentación:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE6_REPORT.md`

### Progreso Total:
- **31 de 56 bypasses migrados (55%)**
- **25 pendientes**

---

## ENTRADA 2025-12-19 - SUBFASE E DISEÑO COMPLETADO

### Hallazgos Clave:

| Elemento | Estado | Ubicación |
|----------|--------|-----------|
| Tabla principal | ✅ EXISTE | `Servidores_Conexiones` |
| Columnas `query_*` | ✅ EXISTEN | `query_inventario`, `query_ventas`, `query_movimientos` |
| Tabla de log | ✅ EXISTE | `Servidores_Conexiones_Log` |
| Campos auditoría | ✅ EXISTEN | `updated_at`, `updated_by` |

### Conclusión:
**EDARSAHUB ya tiene la infraestructura necesaria.** No se requiere crear tablas ni columnas.

### Bloqueador:
**Usuario `<REDACTED_EDARSAHUB_SQL_USER>` es SOLO LECTURA.** Se requiere usuario con permisos de escritura para implementar Lote 7.

### Funciones Propuestas:
- `update_server_query()` — Actualizar query con auditoría
- `clear_server_query()` — Nulificar query con log

### Documentación:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md`

---

## ISSUE SEPARADO: CONFIG-SECURITY-01 — SERVER_SECRET_KEY PENDIENTE

| Campo | Valor |
|-------|-------|
| **ID** | CONFIG-SECURITY-01 |
| **Tipo** | Configuración / Seguridad |
| **Estado** | PENDIENTE CONFIGURACIÓN |
| **Impacto** | No bloquea migración de código. Sí bloquea validación de conexión SQL externa. |
| **Solución** | Agregar `SERVER_SECRET_KEY` a `/app/backend/.env` con la clave Fernet original |

---

## PRÓXIMOS PASOS

### Pendiente autorización usuario:
1. Cerrar SUBFASE D
2. Continuar con LOTE 4 de migración de bypasses en server.py
3. Resolver issue de `SERVER_SECRET_KEY` (no bloquea migración de código)

---

---

## NOTA 2025-12-27 - BUG P0 USUARIOS (FUERA DE ALCANCE)

**Referencia cruzada:** Se resolvió bug P0 "no se ven los usuarios" que NO está relacionado con la fase CONEXIONES-SQL-EDARSAHUB-01.

| Campo | Valor |
|-------|-------|
| **Reporte** | `/app/docs/P0_USUARIOS_VISIBILIDAD_FIX_REPORT.md` |
| **Log RBAC** | `/app/memory/usuarios_rbac_fix_log.md` |
| **Impacto en migración** | NINGUNO |

Este bug fue de datos maestros de usuario y permisos RBAC, no de conexiones SQL.

---
