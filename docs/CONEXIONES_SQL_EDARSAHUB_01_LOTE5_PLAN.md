# PLAN DE LOTE 5 — CLASIFICACIÓN Y SELECCIÓN DE BYPASSES
## CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C.5-PLAN

**Fecha:** 2025-12-19  
**Estado:** PLAN PROPUESTO — PENDIENTE APROBACIÓN  
**Autor:** Agente E1  
**Versión:** 1.0

---

## 1. RESUMEN EJECUTIVO

### Estado Actual de Migración

| Métrica | Valor |
|---------|-------|
| Total bypasses originales | 56 |
| Migrados (Lotes 1-4) | 25 |
| Pendientes | 31 |
| Bypasses identificados en análisis | 26 (+ 5 Categoría B "no migrar") |

### Distribución por Categoría (Post-Análisis)

| Categoría | Cantidad | Descripción |
|-----------|----------|-------------|
| **A) Lectura simple / bajo riesgo** | 4 | Consultas auxiliares, dashboard |
| **B) Config Queries** | 4 | Validación/guardado de queries configuradas |
| **C) Reportes críticos** | 2 | Generación de informes de inventario |
| **D) Exportaciones** | 1 | Export comparativo de inventarios |
| **E) Compras / Datos económicos** | 4 | Análisis de compras, facturas, proveedores |
| **F) Operaciones / Inventarios** | 4 | Captura, auditoría, movimientos, consumos |
| **G) Legacy / Scripts** | 3 | Scripts pendientes, ejecución con credenciales |
| **H) Ventas / Transacciones** | 2 | Detalle de ventas y movimientos |
| **NO MIGRAR (Cat B original)** | 5 | Uso legítimo de MongoDB |

---

## 2. INVENTARIO COMPLETO DE BYPASSES RESTANTES

### CATEGORÍA A — LECTURA SIMPLE / BAJO RIESGO (4 bypasses)

#### A1. `get_all_sucursales()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 2404 |
| **Endpoint** | `GET /api/sucursales/all` |
| **Módulo** | Catálogos |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find({"id": {"$in": server_ids}}, ...)` |
| **Dato de MongoDB** | Nombres de servidores para enriquecer respuesta |
| **Llamada propuesta** | `list_servers(db, prefer_sql=True)` |
| **Conecta SQL externo** | No |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | No |
| **Afecta exportaciones** | No |
| **Afecta datos económicos** | No |
| **Riesgo** | BAJO |
| **Impacto** | BAJO |
| **Prueba** | `curl GET /api/sucursales/all` |
| **Rollback** | Revertir función |

#### A2. `get_unidades_negocio()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 2470 |
| **Endpoint** | `GET /api/unidades-negocio` |
| **Módulo** | Catálogos |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find({"active": True, ...})` |
| **Dato de MongoDB** | Lista de servidores activos |
| **Llamada propuesta** | `list_servers(db, prefer_sql=True)` |
| **Conecta SQL externo** | No |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | No |
| **Riesgo** | BAJO |
| **Impacto** | BAJO |
| **Prueba** | `curl GET /api/unidades-negocio` |
| **Rollback** | Revertir función |

#### A3. `get_dashboard_inventory_summary()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 5977 |
| **Endpoint** | `GET /api/dashboard/inventory-summary` |
| **Módulo** | Dashboard |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one(query)` |
| **Dato de MongoDB** | Configuración del servidor para consulta |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | Sí (dashboard) |
| **Riesgo** | BAJO |
| **Impacto** | MEDIO |
| **Prueba** | `curl GET /api/dashboard/inventory-summary` |
| **Rollback** | Revertir función |

#### A4. `get_dashboard_servers()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 6157 |
| **Endpoint** | `GET /api/dashboard/servers` |
| **Módulo** | Dashboard |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find({"active": True, ...})` |
| **Dato de MongoDB** | Lista de servidores para dashboard |
| **Llamada propuesta** | `list_servers(db, prefer_sql=True)` |
| **Conecta SQL externo** | No |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | Sí (dashboard) |
| **Riesgo** | BAJO |
| **Impacto** | BAJO |
| **Prueba** | `curl GET /api/dashboard/servers` |
| **Rollback** | Revertir función |

---

### CATEGORÍA B — CONFIG QUERIES (4 bypasses)

#### B1. `validate_server_query()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 1543 |
| **Endpoint** | `POST /api/servers/{server_id}/validate-query` |
| **Módulo** | Configuración de Queries |
| **Tipo operación** | Lectura + Validación |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para validar query |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | No |
| **Riesgo** | BAJO |
| **Impacto** | BAJO |
| **Prueba** | `curl POST /api/servers/{id}/validate-query` |
| **Rollback** | Revertir función |

#### B2. `save_server_query()` (2 bypasses en líneas 1634 y 1654)
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Líneas** | 1634, 1654 |
| **Endpoint** | `PUT /api/servers/{server_id}/queries` |
| **Módulo** | Configuración de Queries |
| **Tipo operación** | **ESCRITURA** |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Validación de servidor antes de guardar |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | Sí (para validar) |
| **Escribe configuración** | **SÍ** (guarda queries en servidor) |
| **Afecta permisos** | No |
| **Afecta KPIs** | No |
| **Riesgo** | **MEDIO** |
| **Impacto** | MEDIO |
| **Prueba** | `curl PUT /api/servers/{id}/queries` |
| **Rollback** | Revertir función + restaurar config |

#### B3. `get_server_queries()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 1679 |
| **Endpoint** | `GET /api/servers/{server_id}/queries` |
| **Módulo** | Configuración de Queries |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Queries configuradas del servidor |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | No |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Riesgo** | BAJO |
| **Impacto** | BAJO |
| **Prueba** | `curl GET /api/servers/{id}/queries` |
| **Rollback** | Revertir función |

#### B4. `delete_server_query()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 1733 |
| **Endpoint** | `DELETE /api/servers/{server_id}/queries/{query_type}` |
| **Módulo** | Configuración de Queries |
| **Tipo operación** | **ESCRITURA (eliminación)** |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Validación antes de eliminar query |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | No |
| **Escribe configuración** | **SÍ** (elimina queries) |
| **Afecta permisos** | No |
| **Riesgo** | **MEDIO** |
| **Impacto** | MEDIO |
| **Prueba** | `curl DELETE /api/servers/{id}/queries/{type}` |
| **Rollback** | Revertir función + restaurar config |

---

### CATEGORÍA C — REPORTES CRÍTICOS (2 bypasses)

#### C1. `generate_inventory_report()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 2959 |
| **Endpoint** | `POST /api/reports/inventory` |
| **Módulo** | Reportes |
| **Tipo operación** | Lectura + Generación |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para generar reporte |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | **SÍ** |
| **Afecta exportaciones** | **SÍ** |
| **Riesgo** | **MEDIO** |
| **Impacto** | **ALTO** |
| **Prueba** | `curl POST /api/reports/inventory` |
| **Rollback** | Revertir función |

#### C2. `generate_inventory_analysis()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 3176 |
| **Endpoint** | `POST /api/reports/inventory-analysis` |
| **Módulo** | Reportes |
| **Tipo operación** | Lectura + Análisis |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para análisis |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | **SÍ** |
| **Riesgo** | **MEDIO** |
| **Impacto** | **ALTO** |
| **Prueba** | `curl POST /api/reports/inventory-analysis` |
| **Rollback** | Revertir función |

---

### CATEGORÍA D — EXPORTACIONES (1 bypass)

#### D1. `export_comparativo_inventarios()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 5244 |
| **Endpoint** | `POST /api/operaciones/comparativo/export` |
| **Módulo** | Operaciones |
| **Tipo operación** | Lectura + Exportación |
| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para exportar |
| **Llamada propuesta** | `get_server_connection_info(request.server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | Sí |
| **Afecta exportaciones** | **SÍ** |
| **Riesgo** | **MEDIO** |
| **Impacto** | **ALTO** |
| **Prueba** | `curl POST /api/operaciones/comparativo/export` |
| **Rollback** | Revertir función |

---

### CATEGORÍA E — COMPRAS / DATOS ECONÓMICOS (4 bypasses)

#### E1. `obtener_analisis_compras()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 8492 |
| **Endpoint** | `POST /api/compras/analisis` |
| **Módulo** | Compras |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para análisis de compras |
| **Llamada propuesta** | `get_server_connection_info(request.server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | **SÍ** |
| **Afecta datos económicos** | **SÍ** |
| **Riesgo** | **ALTO** |
| **Impacto** | **ALTO** |
| **Prueba** | `curl POST /api/compras/analisis` |
| **Rollback** | Revertir función |

#### E2. `obtener_facturas_proveedor()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 8639 |
| **Endpoint** | `GET /api/compras/facturas/{server_id}/{proveedor}/{anio}` |
| **Módulo** | Compras |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para facturas |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | Sí |
| **Afecta datos económicos** | **SÍ** |
| **Riesgo** | **MEDIO** |
| **Impacto** | **ALTO** |
| **Prueba** | `curl GET /api/compras/facturas/{...}` |
| **Rollback** | Revertir función |

#### E3. `obtener_detalle_factura()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 8704 |
| **Endpoint** | `GET /api/compras/facturas/{server_id}/detalle/{folio}` |
| **Módulo** | Compras |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para detalle |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | Sí |
| **Afecta datos económicos** | **SÍ** |
| **Riesgo** | **MEDIO** |
| **Impacto** | **MEDIO** |
| **Prueba** | `curl GET /api/compras/facturas/{...}/detalle/{folio}` |
| **Rollback** | Revertir función |

#### E4. `get_sales_details()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 4692 |
| **Endpoint** | `POST /api/comercial/sales-details` |
| **Módulo** | Comercial |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para detalle de ventas |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | **SÍ** |
| **Afecta datos económicos** | **SÍ** |
| **Riesgo** | **ALTO** |
| **Impacto** | **ALTO** |
| **Prueba** | `curl POST /api/comercial/sales-details` |
| **Rollback** | Revertir función |

---

### CATEGORÍA F — OPERACIONES / INVENTARIOS (4 bypasses)

#### F1. `obtener_productos_para_captura()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 7154 |
| **Endpoint** | `POST /api/operaciones/productos-captura` |
| **Módulo** | Operaciones |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para productos |
| **Llamada propuesta** | `get_server_connection_info(request.server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | No |
| **Riesgo** | BAJO |
| **Impacto** | MEDIO |
| **Prueba** | `curl POST /api/operaciones/productos-captura` |
| **Rollback** | Revertir función |

#### F2. `realizar_auditoria_operativa()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 7269 |
| **Endpoint** | `POST /api/operaciones/auditoria` |
| **Módulo** | Operaciones |
| **Tipo operación** | Lectura + Cálculo |
| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para auditoría |
| **Llamada propuesta** | `get_server_connection_info(request.server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | **SÍ** |
| **Riesgo** | **MEDIO** |
| **Impacto** | **ALTO** |
| **Prueba** | `curl POST /api/operaciones/auditoria` |
| **Rollback** | Revertir función |

#### F3. `obtener_detalle_movimientos_post()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 7973 |
| **Endpoint** | `POST /api/compras/detalle-movimientos` |
| **Módulo** | Compras |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para movimientos |
| **Llamada propuesta** | `get_server_connection_info(request.server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | No |
| **Riesgo** | BAJO |
| **Impacto** | MEDIO |
| **Prueba** | `curl POST /api/compras/detalle-movimientos` |
| **Rollback** | Revertir función |

#### F4. `obtener_detalle_consumos_post()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 8150 |
| **Endpoint** | `POST /api/compras/detalle-consumos` |
| **Módulo** | Compras |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para consumos |
| **Llamada propuesta** | `get_server_connection_info(request.server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | No |
| **Riesgo** | BAJO |
| **Impacto** | MEDIO |
| **Prueba** | `curl POST /api/compras/detalle-consumos` |
| **Rollback** | Revertir función |

---

### CATEGORÍA G — LEGACY / SCRIPTS (3 bypasses)

#### G1. `guardar_script_pendiente()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 10994 |
| **Endpoint** | `POST /api/scripts/pendientes` |
| **Módulo** | Admin/Scripts |
| **Tipo operación** | **ESCRITURA** |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Validación de servidor |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | No |
| **Escribe configuración** | **SÍ** (guarda script pendiente) |
| **Afecta permisos** | No |
| **Riesgo** | **MEDIO** |
| **Impacto** | BAJO |
| **Prueba** | `curl POST /api/scripts/pendientes` |
| **Rollback** | Revertir función |

#### G2. `ejecutar_script_con_credenciales()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 11119 |
| **Endpoint** | `POST /api/scripts/execute` |
| **Módulo** | Admin/Scripts |
| **Tipo operación** | **EJECUCIÓN SQL** |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para ejecutar script |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | **SÍ** |
| **Escribe configuración** | No |
| **Afecta permisos** | **POTENCIAL** |
| **Riesgo** | **ALTO** |
| **Impacto** | **ALTO** |
| **Prueba** | Solo Admin - requiere validación manual |
| **Rollback** | Revertir función |

#### G3. `ejecutar_consulta_catalogo()` (línea 11873)
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 11873 |
| **Endpoint** | `POST /api/catalogo/consultas/{id}/ejecutar` |
| **Módulo** | Catálogos |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para consulta |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Riesgo** | BAJO |
| **Impacto** | BAJO |
| **Prueba** | `curl POST /api/catalogo/consultas/{id}/ejecutar` |
| **Rollback** | Revertir función |

---

### CATEGORÍA H — CONSULTAS AUXILIARES (2 bypasses)

#### H1. `ejecutar_consulta_personalizada()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 5584 |
| **Endpoint** | `POST /api/consultas/personalizada` |
| **Módulo** | Consultas |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para consulta |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Riesgo** | BAJO |
| **Impacto** | BAJO |
| **Prueba** | `curl POST /api/consultas/personalizada` |
| **Rollback** | Revertir función |

#### H2. `ejecutar_consulta_custom()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 12109 |
| **Endpoint** | `POST /api/catalogo/consultas/custom` |
| **Módulo** | Catálogos |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para consulta |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Riesgo** | BAJO |
| **Impacto** | BAJO |
| **Prueba** | `curl POST /api/catalogo/consultas/custom` |
| **Rollback** | Revertir función |

---

### CATEGORÍA TRANSACCIONAL — MOVIMIENTOS (1 bypass adicional)

#### T1. `get_movement_details()`
| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 4459 |
| **Endpoint** | `POST /api/comercial/movement-details` |
| **Módulo** | Comercial |
| **Tipo operación** | Lectura |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato de MongoDB** | Conexión SQL para movimientos |
| **Llamada propuesta** | `get_server_connection_info(server_id, db)` |
| **Conecta SQL externo** | Sí |
| **Escribe configuración** | No |
| **Afecta permisos** | No |
| **Afecta KPIs** | **SÍ** |
| **Riesgo** | MEDIO |
| **Impacto** | **ALTO** |
| **Prueba** | `curl POST /api/comercial/movement-details` |
| **Rollback** | Revertir función |

---

## 3. SELECCIÓN PROPUESTA PARA LOTE 5

### Opción A: Lote 5 Conservador (5 cambios — RECOMENDADO)

**Criterio:** Solo lectura simple, sin KPIs críticos, sin datos económicos, sin escrituras.

| # | Función | Categoría | Riesgo | Justificación |
|---|---------|-----------|--------|---------------|
| 1 | `get_all_sucursales()` | A1 | BAJO | Solo enriquece nombres |
| 2 | `get_unidades_negocio()` | A2 | BAJO | Lista de servidores |
| 3 | `get_dashboard_servers()` | A4 | BAJO | Lista para dashboard |
| 4 | `ejecutar_consulta_personalizada()` | H1 | BAJO | Consulta auxiliar |
| 5 | `ejecutar_consulta_custom()` | H2 | BAJO | Consulta auxiliar |

**Tamaño:** 5 cambios  
**Justificación:** Todos son lectura simple, no afectan KPIs ni datos económicos, no escriben configuración.

---

### Opción B: Lote 5 Extendido (10 cambios)

**Criterio:** Lectura + Config Queries sin escritura + Dashboard

| # | Función | Categoría | Riesgo | Justificación |
|---|---------|-----------|--------|---------------|
| 1-5 | (Igual que Opción A) | A1, A2, A4, H1, H2 | BAJO | — |
| 6 | `validate_server_query()` | B1 | BAJO | Solo validación, no escribe |
| 7 | `get_server_queries()` | B3 | BAJO | Solo lectura de queries |
| 8 | `get_dashboard_inventory_summary()` | A3 | BAJO | Dashboard |
| 9 | `ejecutar_consulta_catalogo()` (11873) | G3 | BAJO | Consulta de catálogo |
| 10 | `obtener_productos_para_captura()` | F1 | BAJO | Productos para captura |

**Tamaño:** 10 cambios  
**Justificación:** Todos son lectura, ninguno escribe configuración, ninguno afecta datos económicos directamente.

---

### DIFERIDOS PARA LOTES POSTERIORES

#### Lote 6 — Escrituras de Configuración (máximo 3)
- `save_server_query()` (2 bypasses)
- `delete_server_query()`
- `guardar_script_pendiente()`

#### Lote 7 — Reportes y Exportaciones (máximo 3)
- `generate_inventory_report()`
- `generate_inventory_analysis()`
- `export_comparativo_inventarios()`

#### Lote 8 — Datos Económicos (máximo 3)
- `obtener_analisis_compras()`
- `obtener_facturas_proveedor()`
- `obtener_detalle_factura()`

#### Lote 9 — Ventas y KPIs (máximo 3)
- `get_sales_details()`
- `get_movement_details()`

#### Lote 10 — Operaciones Críticas (máximo 3)
- `realizar_auditoria_operativa()`
- `ejecutar_script_con_credenciales()`

#### Lote 11 — Operaciones Restantes
- `obtener_detalle_movimientos_post()`
- `obtener_detalle_consumos_post()`

---

## 4. VALIDACIONES PROPUESTAS PARA LOTE 5

### Validaciones Generales
- [ ] Backend levanta
- [ ] Auth funciona
- [ ] Login funciona
- [ ] `/api/auth/me` retorna usuario

### Validaciones de Módulos
- [ ] Dashboard carga
- [ ] Lista de servidores funciona
- [ ] Catálogos cargan

### Validaciones de Regresión
- [ ] Lote 1 sin regresión
- [ ] Lote 2 sin regresión
- [ ] Lote 3 sin regresión
- [ ] Lote 4 sin regresión

### Validaciones de Seguridad
- [ ] No se imprimen credenciales
- [ ] No se imprimen connection strings
- [ ] RBAC sigue funcionando

### Validaciones por Endpoint (Opción A)
- [ ] `GET /api/sucursales/all` responde
- [ ] `GET /api/unidades-negocio` responde
- [ ] `GET /api/dashboard/servers` responde
- [ ] `POST /api/consultas/personalizada` responde
- [ ] `POST /api/catalogo/consultas/custom` responde

---

## 5. ROLLBACK

### Rollback General
```bash
git checkout HEAD~1 -- /app/backend/server.py
sudo supervisorctl restart backend
```

### Rollback por Función Individual
Revertir solo la función específica manualmente.

### Rollback por Flag
```bash
# En /app/backend/.env
USE_SQL_FOR_SERVERS=false
sudo supervisorctl restart backend
```

---

## 6. RECOMENDACIÓN FINAL

### Propuesta: OPCIÓN A (5 cambios)

**Motivo:**
1. Todos son lectura simple
2. No afectan KPIs críticos
3. No afectan datos económicos
4. No escriben configuración
5. Fácil validación
6. Fácil rollback
7. No mezcla categorías sensibles

**Alternativa:** Si se desea avanzar más rápido, la Opción B (10 cambios) también es viable porque ninguno escribe configuración ni afecta datos económicos directamente.

---

## 7. PROTECCIÓN EXPLÍCITA

### Lotes Anteriores — NO TOCAR
- Lote 1: 5 funciones
- Lote 2: 5 funciones
- Lote 3: 5 funciones
- Lote 4: 10 funciones

### Issues Separados — NO TOCAR
- CONFIG-SECURITY-01 (SERVER_SECRET_KEY)
- Refresh Tokens (bloqueado)

### Categorías Diferidas — NO MEZCLAR
- Escrituras de configuración
- Reportes críticos
- Datos económicos
- Scripts con credenciales

---

**Documento generado por Agente E1 — EDARSA HUB**  
**Fecha:** 2025-12-19  
**Estado:** PENDIENTE APROBACIÓN USUARIO
