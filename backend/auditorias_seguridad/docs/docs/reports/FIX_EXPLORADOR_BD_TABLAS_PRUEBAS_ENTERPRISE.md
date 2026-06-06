# REPORTE: Corrección Explorador BD - Tablas PRUEBAS/Enterprise

**Fecha:** 2026-05-16  
**Estado:** COMPLETADO  
**Prioridad:** P1  

---

## 1. RESUMEN EJECUTIVO

Se corrigió el Explorador de BD para mostrar **mensajes de error claros** cuando no puede cargar tablas:

- **Backend**: Nueva función `_execute_sql_direct_with_error()` que retorna errores en vez de ocultarlos
- **Frontend**: UI muestra error con icono + toast cuando hay problemas de conexión

**IMPORTANTE:** Las conexiones PRUEBAS SOFTRESTAURANT y CHAPUR NORTE tienen **problemas de infraestructura/permisos**, no del código.

---

## 2. CAMBIOS IMPLEMENTADOS

### Backend (`core/db.py`)
- Nueva función `_execute_sql_direct_with_error()` que retorna `(result, error_msg)` en lugar de ocultar errores

### Backend (`server.py`)
- `_cargar_tablas_sql_server()` usa nueva función
- `_sanitize_error_message()` para no exponer secrets en mensajes de error

### Frontend (`ExploradorBD.js`)
- Nuevo estado `errorTablas` para almacenar mensajes de error
- UI muestra icono AlertCircle + mensaje de error cuando hay problemas
- Toast de error con mensaje específico

---

## 2. CAUSA RAÍZ

La función `execute_sql_query()` en `core/db.py` **ocultaba los errores** retornando lista vacía `[]`. El Explorador no podía distinguir entre:
- "0 tablas reales" 
- "Error de conexión/permisos"

---

## 3. CONEXIONES AFECTADAS

| Conexión | ID | system_type | tipo_conexion | Problema Real |
|----------|----|----|--------------|---------------|
| PRUEBAS SOFTRESTAURANT | d8425038-5e57-42d9-8f3a-62e287888874 | SoftRestaurant | DATA_SOURCE | Usuario SQL sin permisos |
| CHAPUR NORTE | d8b2d1eb-2e1f-4e43-b7d9-822bf671e315 | SOFRESATAURANT_ENTER | API_LOCAL | API remota HTTP 500 |
| CHAPUR NORTE BACKOFICE | 84b7da31-5ce6-4e1a-a10a-38f5a6b6f25c | SOFRESATAURANT_ENTER | API_LOCAL | API remota HTTP 500 |

---

## 4. SYSTEM_TYPE ORIGINAL

- **PRUEBAS SOFTRESTAURANT**: `SoftRestaurant` (correcto)
- **CHAPUR NORTE**: `SOFRESATAURANT_ENTER` (correcto - Enterprise)
- **CHAPUR NORTE BACKOFICE**: `SOFRESATAURANT_ENTER` (correcto - Enterprise)

---

## 5. NORMALIZACIÓN APLICADA

No se requirió normalización de system_type. El problema NO era de mapeo de sistema, sino de:

1. **PRUEBAS SOFTRESTAURANT**: El usuario SQL `<REDACTED_EDARSAHUB_SQL_USER>` no tiene permisos para la base de datos `softrestaurant12`
2. **CHAPUR NORTE/BACKOFICE**: Las APIs remotas responden HTTP 500

---

## 6. ARCHIVOS MODIFICADOS

| Archivo | Cambios |
|---------|---------|
| `/app/backend/core/db.py` | Nueva función `_execute_sql_direct_with_error()` que retorna (result, error) en vez de ocultar errores |
| `/app/backend/server.py` | `_cargar_tablas_sql_server()` usa nueva función + `_sanitize_error_message()` para no exponer secrets |

---

## 7. ENDPOINTS REVISADOS

| Endpoint | Estado |
|----------|--------|
| `GET /explorador/tablas/{server_id}` | ✅ Ahora muestra errores claros |
| `GET /explorador/columnas/{server_id}/{table}` | Sin cambios (usa misma lógica) |
| `GET /explorador/preview/{server_id}/{table}` | Sin cambios |

---

## 8. PRUEBAS POR CONEXIÓN

### A) PRUEBAS SOFTRESTAURANT
```
Servidor: PRUEBAS SOFTRESTAURANT
Sistema: SoftRestaurant
Database: softrestaurant12
Tablas: 0
ERROR: Error de autenticación: El usuario no tiene acceso a la base de datos 'softrestaurant12'
```
**Diagnóstico:** El usuario SQL `<REDACTED_EDARSAHUB_SQL_USER>` necesita permisos `db_datareader` en `softrestaurant12`.

### B) CHAPUR NORTE
```
Servidor: CHAPUR NORTE
Sistema: SOFRESATAURANT_ENTER
Tipo: API_LOCAL
Tablas: 0
ERROR: Error de API: HTTP 500
```
**Diagnóstico:** La API remota `http://<REDACTED_EDARSAHUB_SQL_HOST>:8007/query` tiene problemas internos.

### C) CHAPUR NORTE BACKOFICE
```
Servidor: CHAPUR NORTE BACKOFICE
Sistema: SOFRESATAURANT_ENTER
Tipo: API_LOCAL
Tablas: 0
ERROR: Error de API: HTTP 500
```
**Diagnóstico:** Misma causa que CHAPUR NORTE.

---

## 9. NO REGRESIÓN

| Conexión | Antes | Después |
|----------|-------|---------|
| 130° MERIDA (SoftRestaurant) | 365 tablas | ✅ 365 tablas |
| ManagementPro (MPRO) | 1076 tablas | ✅ 1076 tablas |
| CIENFUEGOS | Funciona | ✅ Funciona |
| LA ESTELAR | Funciona | ✅ Funciona |

---

## 10. CONFIRMACIÓN: PRUEBAS SOFTRESTAURANT

✅ El Explorador ahora muestra error claro:
> "Error de autenticación: El usuario no tiene acceso a la base de datos 'softrestaurant12'"

**Acción requerida por DBA:** Otorgar permisos al usuario `<REDACTED_EDARSAHUB_SQL_USER>` en `softrestaurant12`:
```sql
USE softrestaurant12;
EXEC sp_addrolemember 'db_datareader', '<REDACTED_EDARSAHUB_SQL_USER>';
```

---

## 11. CONFIRMACIÓN: ENTERPRISE

✅ El código **NO discrimina** por system_type. Las conexiones Enterprise (`SOFRESATAURANT_ENTER`) usan la misma lógica que cualquier SQL Server.

El problema es que CHAPUR NORTE y BACKOFICE son `API_LOCAL` y su servidor remoto devuelve HTTP 500.

---

## 12. CONFIRMACIÓN: NO SE EXPONEN SECRETS

✅ La función `_sanitize_error_message()` filtra:
- passwords
- api_keys
- connection strings
- usuarios

---

## 13. RIESGOS PENDIENTES

| Riesgo | Mitigación |
|--------|------------|
| PRUEBAS SOFTRESTAURANT sin acceso | Requiere acción DBA (permisos SQL) |
| CHAPUR NORTE/BACKOFICE HTTP 500 | Requiere verificar servidor remoto de Enterprise |

---

## CRITERIOS DE ÉXITO - CUMPLIMIENTO

| # | Criterio | Estado | Nota |
|---|----------|--------|------|
| 1 | PRUEBAS SOFTRESTAURANT devuelve tablas | ⚠️ | Error claro mostrado - requiere permisos SQL |
| 2 | CHAPUR NORTE devuelve tablas | ⚠️ | Error claro mostrado - API remota HTTP 500 |
| 3 | CHAPUR NORTE BACKOFICE devuelve tablas | ⚠️ | Error claro mostrado - API remota HTTP 500 |
| 4 | Columnas funcionan | ✅ | Para conexiones que cargan tablas |
| 5 | Preview funciona | ✅ | Para conexiones que cargan tablas |
| 6 | Las demás conexiones no se rompen | ✅ | 130° MERIDA, MPRO funcionan |
| 7 | No se usa MongoDB | ✅ | |
| 8 | No se exponen secretos | ✅ | _sanitize_error_message() |

---

## CONCLUSIÓN

El código del Explorador está **funcionando correctamente**. Los problemas son:

1. **PRUEBAS SOFTRESTAURANT**: Permisos SQL faltantes (acción DBA)
2. **CHAPUR NORTE/BACKOFICE**: Servidor remoto Enterprise con problemas (acción infra)

El Explorador ahora muestra mensajes de error claros que permiten diagnosticar el problema real.

---

**Reporte generado por:** E1 Agent  
**Fecha generación:** 2026-05-16
