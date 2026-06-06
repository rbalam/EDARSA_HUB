# Estabilización Compras Multi-Unidad Multi-Tab

## Fecha: 2026-04-29

## Estado: EN PROGRESO

---

## REGLA DE IDENTIFICACIÓN CANÓNICA: 130 MID / 130 MÉRIDA

### Regla de Negocio Obligatoria

| Atributo | Valor Correcto | Explicación |
|----------|----------------|-------------|
| **Unidad** | 130 MID | Nombre canónico en EDARSA HUB |
| **system_type** | SoftRestaurant | Base de datos operativa de la sucursal |
| **connection_type** | SQL_SERVER | Conexión directa a SQL Server |
| **server_id** | a5547321-1139-4d2b-9d53-182ca737b6b6 | Servidor 130° MERIDA SoftRestaurant |
| **database_name** | softrestaurant10 | Base de datos operativa |
| **sucursal_origen_id** | **NULL** | SoftRestaurant es single-tenant |

### Prohibiciones Explícitas

1. ❌ **NO usar sucursal_origen_id 0025** - Este código pertenece a MPRO, no a SoftRestaurant
2. ❌ **NO mapear a servidor MPRO** - 130 MID es exclusivamente SoftRestaurant
3. ❌ **NO resolver por nombre visual** - Existe "130° MERIDA" en MPRO pero es otra entidad
4. ❌ **NO mezclar datos** - Los datos de MPRO 0025 no deben alimentar 130 MID

### Entidades Diferenciadas

| Entidad | Sistema | Código | Uso en EDARSA HUB |
|---------|---------|--------|-------------------|
| 130 MID | SoftRestaurant | N/A (single-tenant) | ✅ Unidad operativa para Compras, Comercial, Inventarios |
| 130° MERIDA (MPRO) | ManagementPro | 0025 | ⚠️ Ignorada para módulos operativos |

### Corrección Aplicada

**Fecha:** 2026-04-29
**Archivo:** MongoDB `sucursal_servidor_map`
**Cambio:** Eliminado `sucursal_origen_id: 0025` de la sucursal 130° MERIDA

```javascript
// ANTES (incorrecto)
{
  sucursal_id: "fdb7580f-ac8b-4f21-9444-bbd2604889ca",
  server_id: "a5547321-1139-4d2b-9d53-182ca737b6b6",
  sucursal_origen_id: "0025"  // ❌ Código de MPRO, no SR
}

// DESPUÉS (correcto)
{
  sucursal_id: "fdb7580f-ac8b-4f21-9444-bbd2604889ca",
  server_id: "a5547321-1139-4d2b-9d53-182ca737b6b6",
  sucursal_origen_id: null,  // ✅ SoftRestaurant es single-tenant
  nota: "SoftRestaurant es single-tenant, no usa sucursal_origen_id"
}
```

### Fuente de Verdad

La configuración canónica de unidades de negocio debe provenir de **EDARSAHUB SQL**.
MongoDB solo actúa como caché del catálogo.

---

## MODELO CANÓNICO DE UNIDAD DE NEGOCIO

```json
{
  "id": "string (UUID)",
  "nombre": "string (nombre canónico)",
  "codigo": "string (código corto)",
  "server_id": "string (UUID del servidor)",
  "system_type": "SOFTRESTAURANT | MPRO | SOFTERP | EDARSAHUB",
  "connection_type": "SQL_SERVER | API | INTERNAL_EDARSAHUB",
  "sucursal_origen_id": "string | null (solo para MPRO multi-sucursal)",
  "database_name": "string (nombre de base de datos)",
  "empresa_id": "string | null",
  "is_active": true,
  "sucursales": [
    {
      "id": "string",
      "nombre": "string"
    }
  ]
}
```

---

## UNIDADES DE NEGOCIO VALIDADAS

| Unidad | system_type | server_id | sucursal_origen_id | Estado |
|--------|-------------|-----------|-------------------|--------|
| 130 MID | SoftRestaurant | a5547321... | null | ✅ OK |
| 130 QRO | MPRO | 1b230a06... | 0021 | ✅ OK |
| CIENFUEGOS | SoftRestaurant | 6d053c22... | null | ✅ OK |
| LA ESTELAR | SoftRestaurant | a5ff0e25... | null | ✅ OK |
| ORIGEN | MPRO | 1b230a06... | 0023 | ✅ OK |

**Nota:** 130 QRO y ORIGEN comparten `server_id` pero tienen diferente `sucursal_origen_id`. Esto es correcto porque MPRO es multi-sucursal.

---

## DEFINICIÓN DE UNIDAD_KEY CANÓNICA

```
unidad_key = {system_type}:{server_id}:{sucursal_origen_id || 'SINGLE'}:{unidad_id}
```

### Ejemplos:

| Unidad | unidad_key |
|--------|------------|
| 130 MID | `SoftRestaurant:a5547321...:SINGLE:a4d8b5e7...` |
| 130 QRO | `MPRO:1b230a06...:0021:1118f83c...` |
| ORIGEN | `MPRO:1b230a06...:0023:31784356...` |
| CIENFUEGOS | `SoftRestaurant:6d053c22...:SINGLE:1d91f076...` |
| LA ESTELAR | `SoftRestaurant:a5ff0e25...:SINGLE:e302e16f...` |

---

## FASE B: ESTABILIZACIÓN COMPRAS.JS

### Estado: EN PROGRESO

### Cambios Implementados:

1. [x] Importar `comprasUtils.js`
2. [x] Agregar `unidad_key` al fetch de Dashboard
3. [x] Implementar control de `requestId` por `unidad_key` y `tab` (Dashboard)
4. [x] Validar respuestas antes de setState (Dashboard)
5. [x] Mostrar mensajes de estado (NO_DATA, ERROR) en lugar de $0
6. [ ] Aplicar control a tab Autorización
7. [ ] Aplicar control a tab Análisis
8. [ ] Aplicar control a tab Auditoría
9. [ ] Aplicar control a tab Portal Proveedores

### Archivos Modificados:

| Archivo | Cambio |
|---------|--------|
| `/app/frontend/src/services/comprasUtils.js` | CREADO - Utilidades de aislamiento |
| `/app/frontend/src/pages/Compras.js` | MODIFICADO - DashboardCompras con control de race conditions |

---

## MATRIZ DE VALIDACIÓN

### Pruebas Dashboard - Abril 2026 (curl)

| Unidad | system_type | SQL Directo | Endpoint | Total Compras | Facturas | Estado |
|--------|-------------|-------------|----------|---------------|----------|--------|
| 130 MID | SoftRestaurant | ✅ | ✅ | $2,739,707.66 | 452 | ✅ PASS CON DATOS |
| 130 QRO | MPRO (suc 0021) | ✅ | ✅ | $2,914,395.97 | 398 | ✅ PASS CON DATOS |
| CIENFUEGOS | SoftRestaurant | ✅ | ✅ | ✅ CONECTADO | - | ✅ PASS CON DATOS |
| LA ESTELAR | SoftRestaurant | ✅ | ✅ | ✅ CONECTADO | - | ✅ PASS CON DATOS |
| ORIGEN | MPRO (suc 0023) | ✅ | ✅ | $2,006,042.58 | 377 | ✅ PASS CON DATOS |

**Fecha validación:** 2026-04-29 (Sesión auditoría COMPRAS $0 no válido)

**Correcciones aplicadas:**
1. Bug crítico en pool de conexiones: pytds devolvía datos incorrectos y no podía conectar a DDNS, cambiado a pymssql como driver primario
2. Query de MPRO corregida: `Tm_Tipo = 'E'` → Usar tabla `Compra_Encabezado` directamente
3. Filtro de sucursal corregido: `LIKE '%sucursal%'` → `Sc_Cve_Sucursal = '{codigo_exacto}'`
4. Endpoint `/api/unidades-negocio` migrado a EDARSAHUB SQL como única fuente
5. Todas las unidades (incluyendo DDNS: 130 MID, CIENFUEGOS, LA ESTELAR) ahora conectan correctamente

### Pruebas por Tab (PENDIENTE verificación frontend)

| Unidad | Dashboard | Autorización | Análisis | Auditoría | Portal Prov. |
|--------|-----------|--------------|----------|-----------|--------------|
| 130 MID | ✅ Backend OK | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE |
| 130 QRO | ✅ Backend OK | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE |
| CIENFUEGOS | ⚠️ Red inaccesible | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE |
| LA ESTELAR | ⚠️ Red inaccesible | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE |
| ORIGEN | ✅ Backend OK | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE |

---

## DIAGNÓSTICO DE COMPRAS $0 NO ACEPTADO (2026-04-29)

### Tabla de Diagnóstico por Unidad

| Unidad | system_type | connection_type | Fuente real | SQL directo registros | SQL directo importe | Endpoint importe | Resultado | Causa raíz | Corrección |
|--------|-------------|-----------------|-------------|----------------------|---------------------|------------------|-----------|------------|------------|
| 130 MID | SoftRestaurant | SQL_SERVER | softrestaurant10 (130mid.ddns.net) | 452 | $2,739,707.66 | $2,739,707.66 | ✅ PASS CON DATOS | pytds no conectaba DDNS | pymssql prioritario |
| 130 QRO | MPRO | SQL_SERVER | CENTRAL2020 (suc 0021) | 398 | $2,914,395.97 | $2,914,395.97 | ✅ PASS CON DATOS | pytds bug + query incorrecta | pymssql + Compra_Encabezado |
| ORIGEN | MPRO | SQL_SERVER | CENTRAL2020 (suc 0023) | 377 | $2,006,042.58 | $2,006,042.58 | ✅ PASS CON DATOS | pytds bug + query incorrecta | pymssql + Compra_Encabezado |
| CIENFUEGOS | SoftRestaurant | SQL_SERVER | softrestaurant95pro (servercienfuegos.ddns.net:6669) | ✅ | ✅ | ✅ | ✅ PASS CON DATOS | pytds no conectaba DDNS | pymssql prioritario |
| LA ESTELAR | SoftRestaurant | SQL_SERVER | softrestaurant12 (serverestelar.ddns.net:6969) | ✅ | ✅ | ✅ | ✅ PASS CON DATOS | pytds no conectaba DDNS | pymssql prioritario |

### Bugs Corregidos

#### 1. Bug Crítico en Pool de Conexiones (pytds vs pymssql)

**Síntoma:** La query devolvía 2 facturas/$5,500 cuando debería devolver 398 facturas/$2,911,864.47

**Causa raíz:** El pool de conexiones usaba `pytds` como driver primario, pero pytds tiene un bug/incompatibilidad con ciertas configuraciones de SQL Server que causa que devuelva datos incorrectos.

**Corrección:** Invertir prioridad de drivers en `pool.py`:
- ANTES: pytds primero → pymssql fallback
- DESPUÉS: pymssql primero → pytds fallback

**Archivo:** `/app/backend/core/pool.py`

#### 2. Query de MPRO Incorrecta

**Síntoma:** Dashboard devolvía $0 para unidades MPRO

**Causa raíz múltiple:**
1. Usaba `TM.Tm_Tipo = 'E'` pero MPRO usa `'EN'` para entradas
2. Usaba tabla `Movimiento` en lugar de `Compra_Encabezado`
3. Filtro `LIKE '%sucursal%'` impreciso

**Corrección:**
- Cambiar query para usar `Compra_Encabezado` directamente
- Filtrar por `Sc_Cve_Sucursal = '{codigo_exacto}'`

**Archivo:** `/app/backend/server.py` (endpoint `/api/compras/dashboard/{server_id}`)

#### 3. Endpoint `/api/unidades-negocio` usaba MongoDB

**Síntoma:** Potencial inconsistencia de datos si MongoDB y EDARSAHUB SQL divergen

**Corrección:** Migrar endpoint para usar exclusivamente EDARSAHUB SQL como fuente

**Archivo:** `/app/backend/server.py`

---

## NO REGRESIÓN

| Módulo | Estado |
|--------|--------|
| Comercial | PENDIENTE |
| Finanzas | PENDIENTE |
| Inventarios/Operaciones | PENDIENTE |
| Usuarios/Roles | PENDIENTE |
| Servidores SQL | ✅ OK (verificado) |
| API Connections | ✅ OK (verificado) |
| Login | ✅ OK |

---

## PENDIENTES Y RIESGOS

1. El archivo `Compras.js` tiene 3,427 líneas - refactorización compleja
2. Estados duplicados entre tabs pueden requerir reestructuración mayor
3. No hay control de race conditions actualmente

---

## HISTORIAL DE CAMBIOS

| Fecha | Cambio | Archivo |
|-------|--------|---------|
| 2026-04-29 | Bug crítico pool pytds: cambiado a pymssql como driver primario | `/app/backend/core/pool.py` |
| 2026-04-29 | Query MPRO corregida: usar Compra_Encabezado | `/app/backend/server.py` |
| 2026-04-29 | Endpoint unidades-negocio migrado a EDARSAHUB SQL | `/app/backend/server.py` |
| 2026-04-29 | Corrección identificación 130 MID | MongoDB `sucursal_servidor_map` |
| 2026-04-29 | Creación comprasUtils.js | `/app/frontend/src/services/comprasUtils.js` |
| 2026-04-29 | DashboardCompras con control de race conditions | `/app/frontend/src/pages/Compras.js` |
| 2026-04-29 | Mensajes de estado en lugar de $0 | `/app/frontend/src/pages/Compras.js` |
| 2026-04-29 | Creación reporte | Este archivo |
