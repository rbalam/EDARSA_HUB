# DIAGNÓSTICO: Servidores, Conexiones API y Consultas SQL
## Migración a EDARSAHUB SQL como Fuente Autoritativa

**Fecha:** 2026-05-15  
**Autor:** E1 Agent  
**Clasificación:** Diagnóstico Pasivo - SIN IMPLEMENTACIÓN

---

## 1. RESUMEN EJECUTIVO

### Estado Actual
La infraestructura de EDARSAHUB ha avanzado significativamente hacia SQL Server como fuente autoritativa. Sin embargo, persisten componentes híbridos y código legacy que requieren consolidación.

### Hallazgos Clave

| Componente | Fuente Actual | Estado |
|------------|---------------|--------|
| **Servidores (CRUD)** | EDARSAHUB SQL (Servidores_Conexiones) | ✅ MIGRADO |
| **Conexiones API Local** | EDARSAHUB SQL (Servidores_Conexiones tipo=API_LOCAL) | ✅ MIGRADO |
| **Sistema_Tipos** | EDARSAHUB SQL | ✅ COMPLETO |
| **Consultas Predefinidas** | Python hardcodeado (`catalogo_consultas.py`) | ⚠️ PENDIENTE |
| **Consultas Personalizadas** | MongoDB `db.consultas_custom` | ⚠️ PENDIENTE |
| **Query Config por Servidor** | EDARSAHUB SQL (campos JSON en Servidores_Conexiones) | ✅ MIGRADO |
| **MongoDB db.servers** | **0 documentos** (desacoplado) | ✅ DESACTIVADO |
| **MongoDB db.consultas_custom** | **0 documentos** (sin uso actual) | ✅ SIN USO |

### Conclusión
**La migración de servidores y conexiones API ya está completada.** El único componente pendiente es el **Catálogo de Consultas SQL** que sigue hardcodeado en Python.

---

## 2. MAPA DE ARCHIVOS ANALIZADOS

### Frontend
| Archivo | Propósito | Endpoints Consumidos |
|---------|-----------|----------------------|
| `/app/frontend/src/pages/Servidores.js` | Administración de servidores y APIs | `/api/servers/*`, `/api/api-connections/*` |
| `/app/frontend/src/components/QueryConfigWizard.js` | Configuración de queries por servidor | `/api/servers/{id}/queries/*` |
| `/app/frontend/src/pages/CatalogoConsultas.js` | Catálogo de consultas SQL | `/api/catalogo/*` |

### Backend
| Archivo | Propósito | Fuente de Datos |
|---------|-----------|-----------------|
| `/app/backend/server.py` (líneas 1149-1825) | Endpoints `/api/servers/*` | EDARSAHUB SQL via server_registry |
| `/app/backend/core/server_registry.py` | Registry central de servidores | EDARSAHUB SQL |
| `/app/backend/modules/api_connections/routes.py` | Endpoints `/api/api-connections/*` | EDARSAHUB SQL |
| `/app/backend/modules/api_connections/repository.py` | Repositorio API connections | EDARSAHUB SQL |
| `/app/backend/catalogo/catalogo_consultas.py` | Catálogo consultas predefinidas | **HARDCODED PYTHON** |
| `/app/backend/server.py` (líneas 12308-12630) | Endpoints `/api/catalogo/*` | **HÍBRIDO** (Python + MongoDB) |

---

## 3. MAPA DE ENDPOINTS FRONTEND/BACKEND

### A) Servidores (`/api/servers/*`)

| Endpoint | Método | Fuente Actual | Estado |
|----------|--------|---------------|--------|
| `/api/servers` | GET | EDARSAHUB SQL | ✅ SQL-First |
| `/api/servers` | POST | EDARSAHUB SQL | ✅ SQL-First |
| `/api/servers/{id}` | GET | EDARSAHUB SQL | ✅ SQL-First |
| `/api/servers/{id}` | PUT | EDARSAHUB SQL | ✅ SQL-First |
| `/api/servers/{id}` | DELETE | EDARSAHUB SQL | ✅ SQL-First |
| `/api/servers/{id}/ping` | GET | Conexión directa | ✅ Operacional |
| `/api/servers/{id}/queries` | GET | EDARSAHUB SQL (JSON) | ✅ SQL-First |
| `/api/servers/{id}/queries/validate` | POST | Ejecución directa | ✅ Operacional |
| `/api/servers/{id}/queries/{type}` | PUT | EDARSAHUB SQL (JSON) | ✅ SQL-First |

### B) Conexiones API Local (`/api/api-connections/*`)

| Endpoint | Método | Fuente Actual | Estado |
|----------|--------|---------------|--------|
| `/api/api-connections` | GET | EDARSAHUB SQL | ✅ SQL-First |
| `/api/api-connections` | POST | EDARSAHUB SQL | ✅ SQL-First |
| `/api/api-connections/{id}` | PUT | EDARSAHUB SQL | ✅ SQL-First |
| `/api/api-connections/{id}` | DELETE | EDARSAHUB SQL | ✅ SQL-First |
| `/api/api-connections/{id}/test-connectivity` | POST | Conexión directa | ✅ Operacional |

### C) Catálogo Consultas (`/api/catalogo/*`)

| Endpoint | Método | Fuente Actual | Estado |
|----------|--------|---------------|--------|
| `/api/catalogo/consultas-rich` | GET | Python + MongoDB | ⚠️ HÍBRIDO |
| `/api/catalogo/ejecutar-rich/{id}` | POST | Python + MongoDB | ⚠️ HÍBRIDO |
| `/api/catalogo/consultas/{id}` | PUT | MongoDB | ⚠️ MONGODB |
| `/api/catalogo/consultas-custom` | POST | MongoDB | ⚠️ MONGODB |
| `/api/catalogo/consultas-custom/{id}` | DELETE | MongoDB | ⚠️ MONGODB |

---

## 4. PERSISTENCIA ACTUAL REAL

### A) MongoDB `db.servers`
```
ESTADO: 0 DOCUMENTOS - DESACOPLADO FUNCIONALMENTE
```
- El sistema ya NO depende de `db.servers` para operación normal
- El fallback a MongoDB sigue en código pero retorna vacío
- Comentarios en código confirman migración (`FASE P1.2`, `FASE 3B`)

### B) MongoDB `db.consultas_custom`
```
ESTADO: 0 DOCUMENTOS - SIN USO ACTUAL
```
- El endpoint de creación existe pero no hay consultas guardadas
- El catálogo actual usa solo consultas hardcodeadas en Python

### C) Python Hardcodeado (`catalogo_consultas.py`)
```
ESTADO: 20+ CONSULTAS PREDEFINIDAS
Categorías: Ventas, Compras, Pagos
Sistemas: SoftRestaurant, MPRO
Ubicación: /app/backend/catalogo/catalogo_consultas.py (484 líneas)
```

**Consultas Detectadas:**
| ID | Nombre | Sistema | Categoría |
|----|--------|---------|-----------|
| SR_VENTAS_DIA | Ventas del Día | SoftRestaurant | Ventas |
| SR_VENTAS_PERIODO | Ventas por Período | SoftRestaurant | Ventas |
| SR_VENTAS_POR_DIA | Ventas Desglosadas por Día | SoftRestaurant | Ventas |
| SR_VENTAS_POR_HORA | Ventas por Hora | SoftRestaurant | Ventas |
| SR_VENTAS_POR_MESERO | Ventas por Mesero | SoftRestaurant | Ventas |
| SR_VENTAS_POR_PRODUCTO | Ventas por Producto | SoftRestaurant | Ventas |
| SR_CORTESIAS | Cortesías y Descuentos | SoftRestaurant | Ventas |
| SR_CANCELACIONES | Cancelaciones | SoftRestaurant | Ventas |
| SR_COMPRAS_PERIODO | Compras por Período | SoftRestaurant | Compras |
| SR_COMPRAS_POR_PROVEEDOR | Compras por Proveedor | SoftRestaurant | Compras |
| SR_COMPRAS_POR_PRODUCTO | Compras por Producto | SoftRestaurant | Compras |
| SR_INVENTARIO_ACTUAL | Inventario Actual | SoftRestaurant | Inventario |
| MPRO_VENTAS_PERIODO | Ventas por Período | MPRO | Ventas |
| MPRO_VENTAS_POR_DIA | Ventas por Día | MPRO | Ventas |
| MPRO_VENTAS_POR_SUCURSAL | Ventas por Sucursal | MPRO | Ventas |
| MPRO_VENTAS_POR_PRODUCTO | Ventas por Producto | MPRO | Ventas |
| MPRO_COMPRAS_PERIODO | Compras por Período | MPRO | Compras |
| MPRO_COMPRAS_POR_PROVEEDOR | Compras por Proveedor | MPRO | Compras |
| SR_FORMAS_PAGO | Formas de Pago | SoftRestaurant | Pagos |
| SR_PROPINAS | Propinas | SoftRestaurant | Pagos |

### D) EDARSAHUB SQL - Tablas Existentes

#### `Servidores_Conexiones` (35 columnas)
```sql
-- COLUMNAS PRINCIPALES:
id, nombre, system_type, tipo_conexion, host, port, database_name,
username, password_encrypted, api_url, api_key_encrypted,
activo, visible_en_operaciones, visible_en_listado,
empresa_id, sucursales, categorias, departamentos,
queries_configured, query_ventas, query_inventario, query_movimientos,
tipos_movimiento, created_at, updated_at, created_by, updated_by
```

**Datos Actuales (19 registros):**
| Nombre | Tipo | TipoConexion | Host | Activo |
|--------|------|--------------|------|--------|
| 130° MERIDA | SoftRestaurant | DATA_SOURCE | 130mid.ddns.net | ✅ |
| 130° QRO LOCAL | MPRO | API_LOCAL | 54.39.104.176 | ✅ |
| CIENFUEGOS | SoftRestaurant | DATA_SOURCE | servercienfuegos.ddns.net | ✅ |
| LA ESTELAR | SoftRestaurant | DATA_SOURCE | serverestelar.ddns.net | ✅ |
| ManagmentPro | MPRO | DATA_SOURCE | 54.39.104.176 | ✅ |
| ORIGEN LOCAL | MPRO | API_LOCAL | 54.39.104.176 | ✅ |

#### `Sistema_Tipos` (5 registros)
| ID | Código | Nombre | Activo |
|----|--------|--------|--------|
| 1 | SOFTRESTAURANT | SoftRestaurant | ✅ |
| 2 | MPRO | ManagementPro | ✅ |
| 3 | API_LOCAL | API Local | ✅ |
| 4 | EDARSAHUB_SQL | EDARSAHUB SQL Server | ✅ |
| 5 | OTRO | Otro | ✅ |

---

## 5. CAMPOS DETECTADOS - COMPARATIVA

### MongoDB `db.servers` (Esquema Histórico)
```javascript
{
  id: String,           // UUID o identificador único
  name: String,         // Nombre del servidor
  system_type: String,  // SoftRestaurant, MPRO, etc.
  host: String,
  port: Number,
  database: String,
  username: String,
  password: String,     // ⚠️ Sin cifrar en versiones antiguas
  api_url: String,
  api_key: String,      // ⚠️ Sin cifrar en versiones antiguas
  active: Boolean,
  visible_en_operaciones: Boolean,
  empresa_id: String,
  sucursales: Array,
  queries_configured: Boolean,
  query_ventas: Object,
  query_inventario: Object,
  query_movimientos: Object
}
```

### SQL `Servidores_Conexiones` (Esquema Actual)
```sql
-- Todos los campos de MongoDB más:
tipo_conexion       NVARCHAR(20)  -- DATA_SOURCE, API_LOCAL, CORE
password_encrypted  NVARCHAR(500) -- Cifrado AES
api_key_encrypted   NVARCHAR(500) -- Cifrado AES
visible_en_listado  BIT           -- Control de visibilidad UI
es_editable_ui      BIT           -- Control de edición UI
es_eliminable_ui    BIT           -- Control de eliminación UI
categorias          NVARCHAR(MAX) -- JSON
departamentos       NVARCHAR(MAX) -- JSON
tipos_movimiento    NVARCHAR(MAX) -- JSON
created_by          NVARCHAR(100)
updated_by          NVARCHAR(100)
EmpresaID           INT           -- FK a Sistema_Empresas
```

---

## 6. BRECHAS ENTRE ARQUITECTURA DESEADA Y ESTADO ACTUAL

| Brecha | Severidad | Componente | Descripción |
|--------|-----------|------------|-------------|
| B1 | 🔴 ALTA | Catálogo Consultas | 20+ consultas hardcodeadas en Python sin versionado ni auditoría |
| B2 | 🟡 MEDIA | Fallback MongoDB | Código de fallback sigue presente aunque retorna vacío |
| B3 | 🟡 MEDIA | Conexiones API Frontend | Fallback hardcodeado en `Servidores.js` líneas 249-274 |
| B4 | 🟢 BAJA | Auditoría Consultas | No existe log de ejecución de consultas del catálogo |
| B5 | 🟢 BAJA | Permisos Consultas | No hay control granular de quién puede ejecutar qué consulta |

---

## 7. RIESGOS TÉCNICOS

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R1 | Modificar Python requiere deploy | ALTA | MEDIO | Migrar a SQL versionado |
| R2 | Sin auditoría de ejecuciones | ALTA | MEDIO | Implementar tabla de log |
| R3 | Consultas sin validación whitelist | MEDIA | ALTO | Validar parámetros estrictamente |
| R4 | Fallback frontend puede activarse | BAJA | BAJO | Eliminar fallback hardcodeado |

---

## 8. RIESGOS DE SEGURIDAD

| ID | Riesgo | Estado | Mitigación Actual |
|----|--------|--------|-------------------|
| S1 | Passwords expuestos | ✅ MITIGADO | Cifrado AES en SQL |
| S2 | API Keys expuestas | ✅ MITIGADO | Cifrado + Enmascarado en respuestas |
| S3 | SQL Injection en catálogo | ⚠️ PARCIAL | Parámetros reemplazados con string.replace |
| S4 | Ejecución sin permisos | ⚠️ PARCIAL | Solo valida autenticación, no autorización |

---

## 9. RIESGOS DE REGRESIÓN

| Módulo | Dependencia de Servidores | Riesgo si se Modifica |
|--------|--------------------------|----------------------|
| Tablero Ejecutivo | Lee via EmpresaResolver | 🟢 BAJO |
| Comercial | Usa server_registry | 🟢 BAJO |
| Compras | Usa server_registry | 🟢 BAJO |
| Finanzas | Usa server_registry | 🟢 BAJO |
| Operaciones/Inventarios | Usa server_registry | 🟢 BAJO |
| Auth/RBAC | No depende de servidores | 🟢 NINGUNO |

---

## 10. RECOMENDACIÓN DE MIGRACIÓN POR FASES

### FASE 0 - Diagnóstico Pasivo ✅
- Análisis completo del estado actual
- Documentación de brechas

### FASE 1 - DDL Propuesto (Próxima)
- Crear tablas `ConsultasSQL_Catalogo`, `ConsultasSQL_Parametros`, etc.
- NO ejecutar hasta autorización

### FASE 2 - Cargar Consultas Hardcodeadas
- Migrar `CATALOGO_CONSULTAS` a tabla SQL con versionado
- Marcar como `EsSistema = 1`

### FASE 3 - Crear Repository SQL-First para Consultas
- Nuevo módulo `/app/backend/modules/consultas_sql/`
- Endpoints nuevos `/api/consultas-sql/*`

### FASE 4 - Dual-Read Temporal
- `GET /api/catalogo/consultas-rich` lee de SQL primero
- Fallback a Python solo para consultas no migradas

### FASE 5 - Auditoría y Permisos
- Implementar `ConsultasSQL_EjecucionesLog`
- Implementar `ConsultasSQL_Permisos`

### FASE 6 - Deprecar Código Legacy
- Eliminar fallback MongoDB
- Eliminar fallback frontend hardcodeado

---

## 11. TABLA DE IMPACTO POR MÓDULO

| Módulo | Impacto Estimado | Archivos a Modificar | Riesgo |
|--------|------------------|---------------------|--------|
| Servidores | NINGUNO | Ya migrado | 🟢 |
| API Connections | NINGUNO | Ya migrado | 🟢 |
| Catálogo Consultas | ALTO | 3-5 archivos nuevos | 🟡 |
| Tablero Ejecutivo | NINGUNO | Sin cambios | 🟢 |
| Comercial | NINGUNO | Sin cambios | 🟢 |
| Compras | NINGUNO | Sin cambios | 🟢 |
| Finanzas | NINGUNO | Sin cambios | 🟢 |
| Operaciones | NINGUNO | Sin cambios | 🟢 |

---

## 12. CONCLUSIÓN DURA

### Lo que YA está migrado:
1. ✅ **Servidores** - Completamente en EDARSAHUB SQL via `server_registry.py`
2. ✅ **Conexiones API Local** - Completamente en EDARSAHUB SQL
3. ✅ **Sistema_Tipos** - Tabla poblada y funcional
4. ✅ **Query Config por Servidor** - Guardado como JSON en SQL
5. ✅ **MongoDB db.servers** - Desacoplado (0 documentos)

### Lo que FALTA migrar:
1. ⚠️ **Catálogo de Consultas SQL** - 20+ consultas hardcodeadas en Python
2. ⚠️ **Auditoría de Ejecuciones** - No existe tabla de log
3. ⚠️ **Permisos por Consulta** - No hay control granular
4. ⚠️ **Versionado de Consultas** - No existe historial de cambios

### Recomendación:
**Priorizar FASE 1-3** (Catálogo SQL) ya que es el único componente operativo que sigue dependiendo de código hardcodeado. Los servidores y APIs ya están completamente migrados.

---

*Documento de diagnóstico pasivo. NO se ejecutó ninguna modificación.*  
*Siguiente paso: Esperar autorización para FASE 1 (DDL Propuesto)*
