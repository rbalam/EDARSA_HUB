# PLAN LOTE 3 — CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C.3-PLAN
## Definición de Lote 3 Quirúrgico

**Fecha:** 2025-12-19  
**Estado:** PROPUESTA PENDIENTE AUTORIZACIÓN  
**Autor:** Agente E1  
**Revisión requerida:** Usuario

---

## 1. RESUMEN

Este documento propone el **Lote 3** de migraciones de bypasses `db.servers.find_one()` hacia `server_registry.get_server_connection_info()`.

- **Bypasses restantes categoría A:** 35
- **Enfoque:** Reportes e Inventarios
- **Selección final Lote 3:** 5 cambios (máximo autorizado)

---

## 2. LISTA DE CANDIDATOS EVALUADOS (10 opciones)

### Candidato #1: get_almacenes_softrestaurant

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 2541 |
| **Endpoint/Función** | `GET /servers/{server_id}/almacenes-softrestaurant` → `get_almacenes_softrestaurant()` |
| **Módulo afectado** | Catálogos - SoftRestaurant |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **¿Conecta a SQL externo?** | Sí |
| **¿Afecta reportes?** | No |
| **¿Afecta inventarios?** | Sí - Catálogo de almacenes SoftRestaurant |
| **¿Afecta exportaciones?** | No |
| **Riesgo** | BAJO |
| **Impacto** | MEDIO - Catálogo específico SR |
| **Pruebas necesarias** | `GET /api/servers/{id}/almacenes-softrestaurant` responde |
| **Rollback** | Revertir función `get_almacenes_softrestaurant()` |

---

### Candidato #2: get_inventarios_list

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 2603 |
| **Endpoint/Función** | `GET /servers/{server_id}/inventarios` → `get_inventarios_list()` |
| **Módulo afectado** | Inventarios |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **¿Conecta a SQL externo?** | Sí |
| **¿Afecta reportes?** | Sí - Lista de inventarios disponibles |
| **¿Afecta inventarios?** | Sí - Lista principal de inventarios |
| **¿Afecta exportaciones?** | No |
| **Riesgo** | BAJO |
| **Impacto** | ALTO - Lista de inventarios físicos |
| **Pruebas necesarias** | Módulo Inventarios carga lista de folios |
| **Rollback** | Revertir función `get_inventarios_list()` |

---

### Candidato #3: get_pendientes_descargar

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 2708 |
| **Endpoint/Función** | `GET /servers/{server_id}/pendientes-descargar` → `get_pendientes_descargar()` |
| **Módulo afectado** | Inventarios / Operaciones |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, system_type, name |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **¿Conecta a SQL externo?** | Sí |
| **¿Afecta reportes?** | Sí - Reporte de pendientes |
| **¿Afecta inventarios?** | Sí - Pendientes de descargar |
| **¿Afecta exportaciones?** | No |
| **Riesgo** | BAJO |
| **Impacto** | ALTO - Operaciones diarias |
| **Pruebas necesarias** | Módulo Operaciones carga pendientes |
| **Rollback** | Revertir función `get_pendientes_descargar()` |

---

### Candidato #4: generate_inventory_report

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 2923 |
| **Endpoint/Función** | `POST /reports/inventory` → `generate_inventory_report()` |
| **Módulo afectado** | Reportes |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **¿Conecta a SQL externo?** | Sí |
| **¿Afecta reportes?** | Sí - Generador principal de reportes |
| **¿Afecta inventarios?** | Sí - Reportes de inventario |
| **¿Afecta exportaciones?** | Sí - Genera datos para exportación |
| **Riesgo** | MEDIO |
| **Impacto** | ALTO - Reportes principales |
| **Pruebas necesarias** | Generar reporte de inventario |
| **Rollback** | Revertir función `generate_inventory_report()` |

---

### Candidato #5: get_report_filters

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 2961 |
| **Endpoint/Función** | `GET /servers/{server_id}/report-filters` → `get_report_filters()` |
| **Módulo afectado** | Reportes - Filtros |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **¿Conecta a SQL externo?** | Sí |
| **¿Afecta reportes?** | Sí - Filtros para reportes de análisis |
| **¿Afecta inventarios?** | Sí - Filtros de categorías/familias |
| **¿Afecta exportaciones?** | Indirectamente |
| **Riesgo** | BAJO |
| **Impacto** | ALTO - Filtros usados en múltiples reportes |
| **Pruebas necesarias** | Filtros cargan en módulo Reportes |
| **Rollback** | Revertir función `get_report_filters()` |

---

### Candidato #6: generar_analisis_inventario

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 3128 |
| **Endpoint/Función** | `POST /reports/analisis-inventario` → `generar_analisis_inventario()` |
| **Módulo afectado** | Reportes - Análisis |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, system_type, tipos_movimiento, categorias |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **¿Conecta a SQL externo?** | Sí |
| **¿Afecta reportes?** | Sí - Análisis de inventario principal |
| **¿Afecta inventarios?** | Sí |
| **¿Afecta exportaciones?** | Sí |
| **Riesgo** | MEDIO |
| **Impacto** | ALTO - Reporte crítico de análisis |
| **Pruebas necesarias** | Generar análisis de inventario |
| **Rollback** | Revertir función `generar_analisis_inventario()` |
| **ALERTA** | ⚠️ Lee campos adicionales `tipos_movimiento`, `categorias` de MongoDB |

---

### Candidato #7: export_inventario_comparativo

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 5196 |
| **Endpoint/Función** | `POST /inventory/export-comparativo` → `export_inventario_comparativo()` |
| **Módulo afectado** | Exportaciones |
| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
| **Dato tomado de MongoDB** | Todo el documento del servidor |
| **Llamada propuesta** | `get_server_connection_info(request.server_id, db=db)` |
| **¿Conecta a SQL externo?** | Sí |
| **¿Afecta reportes?** | Sí |
| **¿Afecta inventarios?** | Sí |
| **¿Afecta exportaciones?** | Sí - Exportación principal de comparativos |
| **Riesgo** | MEDIO |
| **Impacto** | ALTO - Exportación de inventarios |
| **Pruebas necesarias** | Exportar inventario comparativo a Excel |
| **Rollback** | Revertir función `export_inventario_comparativo()` |

---

### Candidato #8: ejecutar_consulta_catalogo

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 5459 |
| **Endpoint/Función** | `POST /catalogo/consulta` → `ejecutar_consulta_catalogo()` |
| **Módulo afectado** | Catálogos - Consultas |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **¿Conecta a SQL externo?** | Sí |
| **¿Afecta reportes?** | Indirectamente |
| **¿Afecta inventarios?** | Indirectamente |
| **¿Afecta exportaciones?** | No |
| **Riesgo** | BAJO |
| **Impacto** | MEDIO - Consultas de catálogo |
| **Pruebas necesarias** | Ejecutar consulta de catálogo |
| **Rollback** | Revertir función `ejecutar_consulta_catalogo()` |

---

### Candidato #9: ejecutar_consulta_personalizada

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 5525 |
| **Endpoint/Función** | `POST /catalogo/consulta-personalizada` → `ejecutar_consulta_personalizada()` |
| **Módulo afectado** | Consultas Admin |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **¿Conecta a SQL externo?** | Sí |
| **¿Afecta reportes?** | No |
| **¿Afecta inventarios?** | No |
| **¿Afecta exportaciones?** | No |
| **Riesgo** | BAJO |
| **Impacto** | BAJO - Solo para administradores |
| **Pruebas necesarias** | Ejecutar consulta personalizada (admin) |
| **Rollback** | Revertir función `ejecutar_consulta_personalizada()` |

---

### Candidato #10: debug_mpro_calculo

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 5604 |
| **Endpoint/Función** | `POST /debug/mpro-calculo` → `debug_mpro_calculo()` |
| **Módulo afectado** | Debug |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **¿Conecta a SQL externo?** | Sí |
| **¿Afecta reportes?** | No |
| **¿Afecta inventarios?** | No |
| **¿Afecta exportaciones?** | No |
| **Riesgo** | BAJO |
| **Impacto** | BAJO - Solo debug |
| **Pruebas necesarias** | Endpoint de debug responde |
| **Rollback** | Revertir función `debug_mpro_calculo()` |

---

## 3. SELECCIÓN FINAL: LOTE 3 (5 CAMBIOS)

### Criterios de selección aplicados:
1. **Prioridad por impacto:** Funciones usadas por reportes/inventarios principales
2. **Riesgo:** Preferir BAJO sobre MEDIO
3. **Patrón:** Funciones con patrón similar a Lote 1 y 2
4. **Dependencias:** Evitar funciones que lean campos adicionales de MongoDB (como `tipos_movimiento`)
5. **Proteger:** No romper Lote 1 ni Lote 2

### LOTE 3 SELECCIONADO:

| # | ID | Función | Línea | Módulo | Riesgo | Impacto |
|---|-----|---------|-------|--------|--------|---------|
| 1 | C2 | `get_inventarios_list()` | 2603 | Inventarios | BAJO | ALTO |
| 2 | C3 | `get_pendientes_descargar()` | 2708 | Operaciones | BAJO | ALTO |
| 3 | C5 | `get_report_filters()` | 2961 | Reportes | BAJO | ALTO |
| 4 | C1 | `get_almacenes_softrestaurant()` | 2541 | Catálogos SR | BAJO | MEDIO |
| 5 | C8 | `ejecutar_consulta_catalogo()` | 5459 | Consultas | BAJO | MEDIO |

---

## 4. JUSTIFICACIÓN DE SELECCIÓN

### ¿Por qué estos 5 van primero?

1. **get_inventarios_list():**
   - Lista principal de inventarios físicos usada por módulo Inventarios
   - Riesgo BAJO, impacto ALTO
   - Patrón idéntico a Lote 1/2

2. **get_pendientes_descargar():**
   - Endpoint crítico para Operaciones diarias
   - Afecta flujo de trabajo de descarga de inventario
   - Riesgo BAJO, impacto ALTO

3. **get_report_filters():**
   - Filtros usados por reportes de análisis
   - Afecta múltiples pantallas de reportes
   - Riesgo BAJO, impacto ALTO

4. **get_almacenes_softrestaurant():**
   - Catálogo específico para SoftRestaurant
   - Complementa catálogos de Lote 1/2
   - Riesgo BAJO

5. **ejecutar_consulta_catalogo():**
   - Consultas de catálogo desde diccionario
   - Patrón simple y aislado
   - Riesgo BAJO

### ¿Por qué NO se incluyen estos en Lote 3?

1. **generate_inventory_report (C4):** Riesgo MEDIO - Mejor después de validar filtros
2. **generar_analisis_inventario (C6):** ⚠️ Lee campos adicionales `tipos_movimiento`, `categorias` de MongoDB - Requiere análisis
3. **export_inventario_comparativo (C7):** Riesgo MEDIO - Función compleja de exportación
4. **ejecutar_consulta_personalizada (C9):** Impacto BAJO - Solo admin, no prioritario
5. **debug_mpro_calculo (C10):** Impacto BAJO - Solo debug

---

## 5. MÓDULOS TOCADOS POR LOTE 3

| Módulo | Funciones | Impacto |
|--------|-----------|---------|
| Inventarios | `get_inventarios_list()` | Lista de folios |
| Operaciones | `get_pendientes_descargar()` | Pendientes diarios |
| Reportes | `get_report_filters()` | Filtros de análisis |
| Catálogos SR | `get_almacenes_softrestaurant()` | Almacenes SR |
| Consultas | `ejecutar_consulta_catalogo()` | Consultas de catálogo |

**No se tocan:** Comercial, Finanzas, RH, Centro de Control (directamente).

---

## 6. RIESGO POR CAMBIO

| # | Función | Riesgo | Descripción |
|---|---------|--------|-------------|
| 1 | `get_inventarios_list()` | BAJO | Lectura de lista, patrón probado |
| 2 | `get_pendientes_descargar()` | BAJO | Lectura de pendientes, patrón probado |
| 3 | `get_report_filters()` | BAJO | Lectura de filtros, patrón probado |
| 4 | `get_almacenes_softrestaurant()` | BAJO | Catálogo específico |
| 5 | `ejecutar_consulta_catalogo()` | BAJO | Consulta de diccionario |

**Riesgo total del lote:** BAJO

---

## 7. VALIDACIONES OBLIGATORIAS PROPUESTAS

### Después de cada cambio:

| Cambio | Validación |
|--------|------------|
| `get_inventarios_list()` | `GET /api/servers/{id}/inventarios` retorna lista |
| `get_pendientes_descargar()` | `GET /api/servers/{id}/pendientes-descargar` retorna datos |
| `get_report_filters()` | `GET /api/servers/{id}/report-filters` retorna filtros |
| `get_almacenes_softrestaurant()` | `GET /api/servers/{id}/almacenes-softrestaurant` retorna lista |
| `ejecutar_consulta_catalogo()` | `POST /api/catalogo/consulta` ejecuta correctamente |

### Validación final del Lote 3:

| Check | Criterio |
|-------|----------|
| Backend levanta | ✅ Sin errores de import |
| Auth funciona | Login + /me retornan datos |
| Inventarios carga | Lista de folios disponibles |
| Operaciones carga | Pendientes de descargar |
| Reportes carga | Filtros de análisis disponibles |
| Filtros funcionan | Categorías/Familias cargan |
| Permisos funcionan | RBAC respetado |
| No se imprimen credenciales | Logs limpios |
| No se toca frontend | Ningún cambio |
| No se toca refresh tokens | Módulo intacto |
| No regresión Lote 1 | Sucursales, almacenes, tipos mov OK |
| No regresión Lote 2 | Categorías, departamentos, ping OK |

---

## 8. ROLLBACK POR CAMBIO

### Rollback individual:

| # | Función | Comando |
|---|---------|---------|
| 1 | `get_inventarios_list()` | Copiar código "ANTES" del reporte Lote 3 |
| 2 | `get_pendientes_descargar()` | Copiar código "ANTES" del reporte Lote 3 |
| 3 | `get_report_filters()` | Copiar código "ANTES" del reporte Lote 3 |
| 4 | `get_almacenes_softrestaurant()` | Copiar código "ANTES" del reporte Lote 3 |
| 5 | `ejecutar_consulta_catalogo()` | Copiar código "ANTES" del reporte Lote 3 |

### Rollback completo del lote:

```bash
git checkout HEAD~1 -- /app/backend/server.py
sudo supervisorctl restart backend
```

### Pruebas después del rollback:

1. Backend levanta
2. Login funciona
3. Endpoints revertidos responden igual que antes
4. Lote 1 y Lote 2 funcionan sin regresión
5. Módulos Inventarios/Operaciones/Reportes cargan normalmente

---

## 9. PROTECCIÓN EXPLÍCITA DE LOTES ANTERIORES

### Lote 1 (5 funciones) - NO TOCAR:
- [x] `execute_edarsa_hub_query()`
- [x] `validate_server_access_by_empresa()`
- [x] `get_sucursales()`
- [x] `get_almacenes()`
- [x] `get_tipos_movimiento()`

### Lote 2 (5 funciones) - NO TOCAR:
- [x] `get_categorias()`
- [x] `get_departamentos()`
- [x] `ping_server()`
- [x] `get_sucursales_config()`
- [x] `sync_sucursales_config()`

### Validación de no regresión:
Después de Lote 3, se validarán explícitamente:
- `GET /api/servers/{id}/sucursales` (Lote 1)
- `GET /api/servers/{id}/almacenes` (Lote 1)
- `GET /api/servers/{id}/categorias` (Lote 2)
- `GET /api/servers/{id}/ping` (Lote 2)

---

## 10. DICTAMEN

### Estado: PROPUESTA LISTA PARA AUTORIZACIÓN

**Lote 3 propuesto (5 cambios):**
1. `get_inventarios_list()` - Inventarios
2. `get_pendientes_descargar()` - Operaciones
3. `get_report_filters()` - Reportes
4. `get_almacenes_softrestaurant()` - Catálogos SR
5. `ejecutar_consulta_catalogo()` - Consultas

**Riesgo total:** BAJO  
**Módulos tocados:** Inventarios, Operaciones, Reportes, Catálogos SR  
**Frontend:** No se toca  
**Lotes anteriores:** Protegidos explícitamente  
**Rollback:** Documentado  

**Acción requerida:**  
Usuario debe autorizar Lote 3 para proceder con la implementación.

---

**Documento generado por Agente E1 - EDARSA HUB**  
**Fecha:** 2025-12-19  
**Versión:** 1.0
