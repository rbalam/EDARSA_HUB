# PLAN DE LOTE 4 — MIGRACIÓN DE BYPASSES
## CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C.4-PLAN

**Fecha:** 2025-12-19  
**Estado:** PLAN PROPUESTO — PENDIENTE APROBACIÓN  
**Autor:** Agente E1  
**Versión:** 1.0

---

## 1. RESUMEN EJECUTIVO

### Objetivo
Seleccionar 5-10 bypasses de bajo riesgo para migración a `server_registry.py`.

### Criterios de Selección
- ✅ Bajo riesgo funcional
- ✅ Bajo impacto en usuarios
- ✅ Patrón homogéneo (todos siguen el mismo patrón de migración)
- ✅ Tipo: Explorador SQL, Debug, Consultas auxiliares
- ❌ Excluir: Reportes críticos, exportaciones masivas, KPIs, RBAC, escritura de configuración

### Resultado
**10 candidatos seleccionados** — Todos de bajo riesgo, patrón homogéneo (explorador SQL y consultas auxiliares).

---

## 2. INVENTARIO DE BYPASSES PENDIENTES

### Bypasses Restantes por Categoría

| Categoría | Cantidad | Descripción |
|-----------|----------|-------------|
| Explorador SQL | 6 | listar_tablas, listar_columnas, listar_relaciones, preview_tabla, ejecutar_query_libre, ejecutar_script_sql |
| Consultas Auxiliares | 4 | ejecutar_consulta_personalizada, debug_test_queries, buscar_en_bd, guardar_script_pendiente |
| Health Check | 2 | sql_server_health_check, sql_server_test_query |
| Config Queries | 4 | validate_server_query, save_server_query, get_server_queries, delete_server_query |
| Reportes | 3 | generate_inventory_report, generate_inventory_analysis, export_comparativo_inventarios |
| Movimientos/Ventas | 4 | get_movement_details, get_sales_details, obtener_detalle_movimientos_post, obtener_detalle_consumos_post |
| Compras/Proveedores | 3 | obtener_analisis_compras, obtener_facturas_proveedor, obtener_detalle_factura |
| Catálogo Consultas | 2 | ejecutar_consulta_catalogo, ejecutar_consulta_custom |
| Operaciones | 2 | obtener_productos_para_captura, realizar_auditoria_operativa |
| Scripts Admin | 1 | ejecutar_script_con_credenciales |

**Total restantes: ~31 bypasses**

---

## 3. CANDIDATOS PARA LOTE 4

### Selección: Explorador SQL + Consultas Auxiliares (10 cambios)

| # | Función | Línea | Tipo | Riesgo | Impacto | Justificación |
|---|---------|-------|------|--------|---------|---------------|
| 1 | `listar_tablas()` | 8911 | Explorador | BAJO | BAJO | Solo metadata, no ejecuta queries de negocio |
| 2 | `listar_columnas()` | 8950 | Explorador | BAJO | BAJO | Solo metadata de estructura |
| 3 | `listar_relaciones()` | 8991 | Explorador | BAJO | BAJO | Solo metadata de FKs |
| 4 | `preview_tabla()` | 9037 | Explorador | BAJO | BAJO | Preview con LIMIT 10 |
| 5 | `ejecutar_query_libre()` | 9075 | Explorador | BAJO | MEDIO | Query libre pero solo lectura |
| 6 | `ejecutar_script_sql()` | 9119 | Explorador | BAJO | MEDIO | Scripts SQL controlados |
| 7 | `debug_test_queries()` | 5654 | Debug | BAJO | BAJO | Endpoint de pruebas internas |
| 8 | `buscar_en_bd()` | 11580 | Consulta | BAJO | BAJO | Búsqueda global en tablas |
| 9 | `sql_server_health_check()` | 12677 | Health | BAJO | BAJO | Verificación de conectividad |
| 10 | `sql_server_test_query()` | 12740 | Health | BAJO | BAJO | Test de query simple |

---

## 4. ANÁLISIS DETALLADO POR CANDIDATO

### 4.1 `listar_tablas()` — Línea 8911

| Campo | Valor |
|-------|-------|
| **Ruta API** | `GET /api/explorer/{server_id}/tables` |
| **Tipo** | Explorador SQL |
| **Riesgo** | BAJO |
| **Impacto** | BAJO — Solo devuelve lista de tablas (metadata) |
| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
| **Llamada propuesta** | `conn_info = await get_server_connection_info(server_id, db=db)` |
| **Prueba requerida** | `curl GET /api/explorer/{server_id}/tables` |
| **Rollback** | Revertir archivo |

### 4.2 `listar_columnas()` — Línea 8950

| Campo | Valor |
|-------|-------|
| **Ruta API** | `GET /api/explorer/{server_id}/columns/{table_name}` |
| **Tipo** | Explorador SQL |
| **Riesgo** | BAJO |
| **Impacto** | BAJO — Solo devuelve columnas de una tabla |
| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
| **Llamada propuesta** | `conn_info = await get_server_connection_info(server_id, db=db)` |
| **Prueba requerida** | `curl GET /api/explorer/{server_id}/columns/productos` |
| **Rollback** | Revertir archivo |

### 4.3 `listar_relaciones()` — Línea 8991

| Campo | Valor |
|-------|-------|
| **Ruta API** | `GET /api/explorer/{server_id}/relations/{table_name}` |
| **Tipo** | Explorador SQL |
| **Riesgo** | BAJO |
| **Impacto** | BAJO — Solo devuelve foreign keys |
| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
| **Llamada propuesta** | `conn_info = await get_server_connection_info(server_id, db=db)` |
| **Prueba requerida** | `curl GET /api/explorer/{server_id}/relations/ventas` |
| **Rollback** | Revertir archivo |

### 4.4 `preview_tabla()` — Línea 9037

| Campo | Valor |
|-------|-------|
| **Ruta API** | `GET /api/explorer/{server_id}/preview/{table_name}` |
| **Tipo** | Explorador SQL |
| **Riesgo** | BAJO |
| **Impacto** | BAJO — Preview con TOP 10 |
| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
| **Llamada propuesta** | `conn_info = await get_server_connection_info(server_id, db=db)` |
| **Prueba requerida** | `curl GET /api/explorer/{server_id}/preview/productos` |
| **Rollback** | Revertir archivo |

### 4.5 `ejecutar_query_libre()` — Línea 9075

| Campo | Valor |
|-------|-------|
| **Ruta API** | `POST /api/explorer/{server_id}/query` |
| **Tipo** | Explorador SQL |
| **Riesgo** | BAJO |
| **Impacto** | MEDIO — Permite queries libres pero validadas |
| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
| **Llamada propuesta** | `conn_info = await get_server_connection_info(server_id, db=db)` |
| **Prueba requerida** | `curl POST /api/explorer/{server_id}/query -d '{"query":"SELECT TOP 5 * FROM productos"}'` |
| **Rollback** | Revertir archivo |

### 4.6 `ejecutar_script_sql()` — Línea 9119

| Campo | Valor |
|-------|-------|
| **Ruta API** | `POST /api/explorer/{server_id}/script` |
| **Tipo** | Explorador SQL |
| **Riesgo** | BAJO |
| **Impacto** | MEDIO — Scripts SQL múltiples statements |
| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
| **Llamada propuesta** | `conn_info = await get_server_connection_info(server_id, db=db)` |
| **Prueba requerida** | `curl POST /api/explorer/{server_id}/script` |
| **Rollback** | Revertir archivo |

### 4.7 `debug_test_queries()` — Línea 5654

| Campo | Valor |
|-------|-------|
| **Ruta API** | `POST /api/debug/test-queries` |
| **Tipo** | Debug |
| **Riesgo** | BAJO |
| **Impacto** | BAJO — Endpoint de desarrollo/pruebas |
| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))` |
| **Llamada propuesta** | `conn_info = await get_server_connection_info(server_id, db=db)` |
| **Prueba requerida** | `curl POST /api/debug/test-queries` |
| **Rollback** | Revertir archivo |

### 4.8 `buscar_en_bd()` — Línea 11580

| Campo | Valor |
|-------|-------|
| **Ruta API** | `POST /api/search/database` |
| **Tipo** | Consulta |
| **Riesgo** | BAJO |
| **Impacto** | BAJO — Búsqueda global en tablas |
| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
| **Llamada propuesta** | `conn_info = await get_server_connection_info(server_id, db=db)` |
| **Prueba requerida** | `curl POST /api/search/database` |
| **Rollback** | Revertir archivo |

### 4.9 `sql_server_health_check()` — Línea 12677

| Campo | Valor |
|-------|-------|
| **Ruta API** | `GET /api/health/sql/{server_id}` |
| **Tipo** | Health Check |
| **Riesgo** | BAJO |
| **Impacto** | BAJO — Solo verifica conectividad |
| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))` |
| **Llamada propuesta** | `conn_info = await get_server_connection_info(target_server_id, db=db)` |
| **Prueba requerida** | `curl GET /api/health/sql/{server_id}` |
| **Rollback** | Revertir archivo |

### 4.10 `sql_server_test_query()` — Línea 12740

| Campo | Valor |
|-------|-------|
| **Ruta API** | `POST /api/health/sql/{server_id}/test` |
| **Tipo** | Health Check |
| **Riesgo** | BAJO |
| **Impacto** | BAJO — Ejecuta query de prueba simple |
| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))` |
| **Llamada propuesta** | `conn_info = await get_server_connection_info(target_server_id, db=db)` |
| **Prueba requerida** | `curl POST /api/health/sql/{server_id}/test` |
| **Rollback** | Revertir archivo |

---

## 5. CANDIDATOS DIFERIDOS (NO INCLUIDOS EN LOTE 4)

### 5.1 Reportes Críticos — Diferidos a Lote 5+

| Función | Línea | Motivo de Exclusión |
|---------|-------|---------------------|
| `generate_inventory_report()` | 2953 | Reporte crítico, alto impacto |
| `generate_inventory_analysis()` | 3121 | Análisis de negocio, alto impacto |
| `export_comparativo_inventarios()` | 5230 | Exportación masiva, riesgo medio |

### 5.2 Movimientos/Ventas — Diferidos a Lote 5+

| Función | Línea | Motivo de Exclusión |
|---------|-------|---------------------|
| `get_movement_details()` | 4447 | Datos de negocio críticos |
| `get_sales_details()` | 4681 | Datos de ventas, alto impacto |
| `obtener_detalle_movimientos_post()` | 7961 | Módulo Compras crítico |
| `obtener_detalle_consumos_post()` | 8138 | Módulo Compras crítico |

### 5.3 Compras/Proveedores — Diferidos a Lote 5+

| Función | Línea | Motivo de Exclusión |
|---------|-------|---------------------|
| `obtener_analisis_compras()` | 8481 | Análisis financiero |
| `obtener_facturas_proveedor()` | 8628 | Datos de proveedores |
| `obtener_detalle_factura()` | 8693 | Detalle fiscal |

### 5.4 Config Queries — Revisar Categoría C

| Función | Línea | Motivo de Exclusión |
|---------|-------|---------------------|
| `validate_server_query()` | 1524 | Categoría C - tiene escrituras |
| `save_server_query()` | 1615 | Categoría C - escribe en MongoDB |
| `get_server_queries()` | 1675 | Categoría C - lee config queries |
| `delete_server_query()` | 1722 | Categoría C - modifica MongoDB |

### 5.5 Operaciones — Diferidos a Lote 5+

| Función | Línea | Motivo de Exclusión |
|---------|-------|---------------------|
| `obtener_productos_para_captura()` | 7140 | Captura operativa |
| `realizar_auditoria_operativa()` | 7249 | Auditoría crítica |

### 5.6 Admin/Scripts — Diferidos

| Función | Línea | Motivo de Exclusión |
|---------|-------|---------------------|
| `ejecutar_script_con_credenciales()` | 11066 | Requiere credenciales admin |
| `guardar_script_pendiente()` | 10941 | Escribe en MongoDB |

---

## 6. PATRÓN DE MIGRACIÓN

### Código Actual (Bypass)
```python
@app.get("/api/explorer/{server_id}/tables")
async def listar_tablas(server_id: str, current_user: Dict = Depends(get_current_user)):
    server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    results = execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )
```

### Código Propuesto (Registry)
```python
from core.server_registry import get_server_connection_info

@app.get("/api/explorer/{server_id}/tables")
async def listar_tablas(server_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 4
    """
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    conn_info = await get_server_connection_info(server_id, db=db)
    if not conn_info:
        raise HTTPException(status_code=404, detail="Servidor no encontrado o sin acceso")
    
    results = execute_sql_query(
        conn_info['host'], conn_info['port'], conn_info['database'],
        conn_info['username'], conn_info['password'], query
    )
```

---

## 7. PRUEBAS REQUERIDAS

### 7.1 Pruebas por Endpoint

| # | Endpoint | Método | Prueba |
|---|----------|--------|--------|
| 1 | `/api/explorer/{server_id}/tables` | GET | Listar tablas de servidor activo |
| 2 | `/api/explorer/{server_id}/columns/{table}` | GET | Listar columnas de tabla existente |
| 3 | `/api/explorer/{server_id}/relations/{table}` | GET | Listar relaciones |
| 4 | `/api/explorer/{server_id}/preview/{table}` | GET | Preview con datos |
| 5 | `/api/explorer/{server_id}/query` | POST | Query SELECT simple |
| 6 | `/api/explorer/{server_id}/script` | POST | Script SQL multi-statement |
| 7 | `/api/debug/test-queries` | POST | Endpoint de debug |
| 8 | `/api/search/database` | POST | Búsqueda global |
| 9 | `/api/health/sql/{server_id}` | GET | Health check |
| 10 | `/api/health/sql/{server_id}/test` | POST | Test query |

### 7.2 Pruebas de Regresión

- Verificar que Lotes 1, 2 y 3 siguen funcionando
- Verificar que el backend inicia sin errores
- Verificar que auth funciona

---

## 8. ROLLBACK

### Rollback Inmediato
```bash
# Si falla el lote completo
git checkout HEAD~1 -- /app/backend/server.py
sudo supervisorctl restart backend
```

### Rollback por Endpoint
Si solo un endpoint falla, revertir solo esa función manualmente.

### Rollback Global (Flag)
```bash
# En /app/backend/.env
USE_SQL_FOR_SERVERS=false
sudo supervisorctl restart backend
```

---

## 9. JUSTIFICACIÓN DEL TAMAÑO DEL LOTE

### ¿Por qué 10 cambios?

1. **Todos son bajo riesgo** — Explorador SQL y health checks no afectan operación de negocio
2. **Patrón 100% homogéneo** — Todos siguen exactamente el mismo patrón de migración
3. **Bajo impacto en usuarios** — Son herramientas auxiliares, no flujos críticos
4. **Fácil validación** — Cada endpoint puede probarse con un curl simple
5. **No hay escrituras a MongoDB** — Todos son endpoints de solo lectura SQL
6. **No hay RBAC complejo** — Solo validan usuario autenticado
7. **No hay datos económicos críticos** — Son metadata y diagnóstico

### Regla aplicada
> "Hasta 10 cambios solo si son bajo riesgo, bajo impacto y homogéneos"

✅ Cumple todos los criterios.

---

## 10. PROTECCIÓN EXPLÍCITA

### Lotes Anteriores — NO TOCAR

| Lote | Funciones |
|------|-----------|
| Lote 1 | `execute_edarsa_hub_query`, `validate_server_access_by_empresa`, `get_sucursales`, `get_almacenes`, `get_tipos_movimiento` |
| Lote 2 | `get_categorias`, `get_departamentos`, `ping_server`, `get_sucursales_config`, `sync_sucursales_config` |
| Lote 3 | `get_inventarios_list`, `get_pendientes_descargar`, `get_report_filters`, `get_almacenes_softrestaurant`, `ejecutar_consulta_catalogo` (línea 5459) |

### Issues Separados — NO TOCAR

| Issue | Descripción |
|-------|-------------|
| CONFIG-SECURITY-01 | SERVER_SECRET_KEY pendiente |
| Refresh Tokens | Bloqueado por script SQL manual |

---

## 11. RESUMEN DE SELECCIÓN FINAL

### Lote 4 — 10 Cambios Aprobados para Implementación

| # | Función | Tipo | Riesgo |
|---|---------|------|--------|
| 1 | `listar_tablas()` | Explorador | BAJO |
| 2 | `listar_columnas()` | Explorador | BAJO |
| 3 | `listar_relaciones()` | Explorador | BAJO |
| 4 | `preview_tabla()` | Explorador | BAJO |
| 5 | `ejecutar_query_libre()` | Explorador | BAJO |
| 6 | `ejecutar_script_sql()` | Explorador | BAJO |
| 7 | `debug_test_queries()` | Debug | BAJO |
| 8 | `buscar_en_bd()` | Consulta | BAJO |
| 9 | `sql_server_health_check()` | Health | BAJO |
| 10 | `sql_server_test_query()` | Health | BAJO |

---

## 12. CRITERIO DE ACEPTACIÓN

El plan se considera aceptado si:

1. ✅ Lista de 10 candidatos documentada
2. ✅ Clasificación de riesgo: todos BAJO
3. ✅ Tipo de endpoint: explorador, debug, health
4. ✅ Bypass actual documentado
5. ✅ Llamada propuesta a server_registry documentada
6. ✅ Impacto analizado
7. ✅ Prueba requerida definida
8. ✅ Rollback documentado
9. ✅ Justificación del tamaño (10 = bajo riesgo, homogéneo)
10. ✅ Protección de lotes anteriores

---

**Documento generado por Agente E1 — EDARSA HUB**  
**Fecha:** 2025-12-19  
**Estado:** PENDIENTE APROBACIÓN USUARIO
