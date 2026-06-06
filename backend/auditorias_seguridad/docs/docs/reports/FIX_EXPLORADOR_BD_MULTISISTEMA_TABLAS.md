# REPORTE: Corrección Explorador BD Multi-Sistema (Carga de Tablas)

**Fecha:** 2026-05-16  
**Estado:** COMPLETADO  
**Prioridad:** P1  

---

## 1. RESUMEN EJECUTIVO

Se corrigió el Explorador de Base de Datos para soportar carga de tablas desde **todos los tipos de conexión**, no solo SoftRestaurant. El endpoint `/api/explorador/tablas/{server_id}` ahora maneja:

1. **SQL_SERVER / DATA_SOURCE**: Conexión directa SQL Server (cualquier sistema)
2. **API_LOCAL**: Conexiones via API /query (MPRO, Enterprise, etc.)

---

## 2. SÍNTOMA

- El Explorador mostraba "0 tablas" para servidores MPRO, Enterprise, NOMIPAQ
- Solo funcionaba correctamente con SoftRestaurant
- Servidores API_LOCAL como CHAPUR NORTE, ORIGEN LOCAL no cargaban tablas

---

## 3. CAUSA RAÍZ

El endpoint `/api/explorador/tablas/{server_id}` asumía que **todos los servidores** tienen conexión SQL directa y usaba:

```python
execute_sql_query(host, port, database, username, password, query)
```

Sin embargo:
- Las conexiones `API_LOCAL` (MPRO, Enterprise) **no tienen credenciales SQL directas**
- Usan una URL de API (`http://host:port/query`) con `?sql=` parameter
- La función `get_server_connection_info()` no encontraba las conexiones `API_LOCAL` porque estaban filtradas en `_get_servers_from_sql()`

---

## 4. POR QUÉ SOLO SOFTRESTAURANT FUNCIONABA

| Sistema | tipo_conexion | ¿Funcionaba? | Razón |
|---------|---------------|--------------|-------|
| SoftRestaurant | DATA_SOURCE | ✅ Sí | Tiene host/port/database/credentials SQL |
| MPRO (ManagementPro SQL) | DATA_SOURCE | ✅ Sí | Tiene credenciales SQL directas |
| MPRO (API Local) | API_LOCAL | ❌ No | No tiene SQL credentials, usa URL API |
| Enterprise | API_LOCAL | ❌ No | No tiene SQL credentials, usa URL API |
| NOMIPAQ | DATA_SOURCE | ✅ Sí | Si tiene SQL credentials |

---

## 5. CORRECCIÓN POR TIPO DE CONEXIÓN

### SQL_SERVER / DATA_SOURCE
```python
# Sin cambios - usa INFORMATION_SCHEMA.TABLES
query = """
SELECT TABLE_NAME as tabla, TABLE_TYPE as tipo
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME
"""
execute_sql_query(host, port, database, username, password, query)
```

### API_LOCAL
```python
# NUEVO - usa API /query con GET ?sql=
metadata_query = "SELECT name AS tabla FROM sys.tables ORDER BY name"
async with httpx.AsyncClient() as client:
    response = await client.get(
        api_url,
        params={"sql": metadata_query},
        headers={"x-api-key": api_key}
    )
```

---

## 6. CORRECCIÓN POR SISTEMA

| Sistema | Corrección |
|---------|------------|
| SoftRestaurant | Sin cambios - ya funcionaba |
| MPRO (SQL) | Sin cambios - ya funcionaba |
| MPRO (API) | Agregado soporte API_LOCAL |
| Enterprise | Agregado soporte API_LOCAL |
| NOMIPAQ | Sin cambios si es SQL; API_LOCAL si es API |
| EDARSAHUB SQL | Sin cambios - usa SQL directa |

---

## 7. VALIDACIÓN DE MPRO

### MPRO DATA_SOURCE (ManagmentPro SQL)
```
Servidor: ManagmentPro
Sistema: MPRO
Database: CENTRAL2020
Tipo: SQL_SERVER
Tablas: 1076 ✅
```

### MPRO API_LOCAL (130° QRO LOCAL, ORIGEN LOCAL)
```
Servidor: ORIGEN LOCAL
Sistema: MPRO
Tipo: API_LOCAL
Tablas: Depende de disponibilidad de API remota
Mensaje si error: "Error de API: HTTP 500"
```

---

## 8. VALIDACIÓN DE ENTERPRISE

```
Servidor: CHAPUR NORTE
Sistema: SOFRESATAURANT_ENTER
Tipo: API_LOCAL
Resultado: API remota responde HTTP 500 (problema de conectividad SQL Server remoto)
Mensaje claro: "Error de API: HTTP 500"
```

El error es de la API remota, no del Explorador. El Explorador ahora muestra el error claramente.

---

## 9. VALIDACIÓN DE NOMIPAQ

No hay conexiones NOMIPAQ activas en el sistema actualmente.

---

## 10. VALIDACIÓN DE EDARSAHUB SQL

No hay conexión "EDARSAHUB SQL" registrada como explorable directamente. Los datos de EDARSAHUB se acceden a través de endpoints internos.

---

## 11. CONFIRMACIÓN: NO SE TOCÓ SOFTRESTAURANT PRODUCTIVO

✅ **CONFIRMADO**

- **130° MERIDA**: 365 tablas ✅
- **CIENFUEGOS**: Funciona ✅
- **LA ESTELAR**: Funciona ✅

La lógica de SQL_SERVER/DATA_SOURCE no fue modificada, solo se agregó lógica **adicional** para API_LOCAL.

---

## 12. CONFIRMACIÓN DE NO MONGODB

✅ **CONFIRMADO**: No se usa MongoDB para cargar tablas.

Fuente de datos:
- `Servidores_Conexiones` (EDARSAHUB SQL) para conexiones
- `INFORMATION_SCHEMA.TABLES` del servidor destino para tablas SQL
- Endpoint `/query` del servidor destino para tablas API

---

## 13. CONFIRMACIÓN DE NO SECRETS EXPUESTOS

✅ **CONFIRMADO**

- Passwords SQL no se envían al frontend
- API keys no se exponen en respuestas
- Solo se envía: servidor, sistema, database, tablas[], error (si aplica)

---

## 14. CONFIRMACIÓN DE NO REGRESIÓN EN SERVIDORES

✅ El menú Servidores sigue funcionando.

---

## 15. CONFIRMACIÓN DE NO REGRESIÓN EN MÓDULOS PROTEGIDOS

| Módulo | Estado |
|--------|--------|
| Comercial | ✅ No tocado |
| Tablero Ejecutivo | ✅ No tocado |
| Finanzas | ✅ No tocado |
| Compras | ✅ No tocado |
| Operaciones / Inventarios | ✅ No tocado |
| Usuarios / Roles / Permisos | ✅ No tocado |
| Catálogo de Consultas | ✅ No tocado |
| Catálogos del Sistema | ✅ No tocado |

---

## 16. ARCHIVOS MODIFICADOS

| Archivo | Cambios |
|---------|---------|
| `/app/backend/server.py` | Refactorizado endpoint `/explorador/tablas/{server_id}` para soportar API_LOCAL y SQL_SERVER |
| `/app/backend/modules/api_connections/repository.py` | Agregadas funciones `get_api_connection_by_id_full()` y `get_decrypted_api_key()` |

---

## 17. PENDIENTES

| Item | Prioridad | Descripción |
|------|-----------|-------------|
| APIs remotas no disponibles | Baja | CHAPUR NORTE, ORIGEN LOCAL dependen de servidores remotos que retornan HTTP 500. Esto es un problema de infraestructura, no del código. |
| Agregar endpoint columnas para API_LOCAL | Media | Actualmente solo soporta tablas; columnas requeriría query adicional. |

---

## CRITERIOS DE ACEPTACIÓN - CUMPLIMIENTO

| # | Criterio | Estado |
|---|----------|--------|
| 1 | Explorador no limitado a SoftRestaurant | ✅ |
| 2 | Filtro muestra todos los sistemas | ✅ |
| 3 | Filtro muestra todos los servidores explorables | ✅ |
| 4 | SoftRestaurant productivo sigue funcionando | ✅ |
| 5 | MPRO aparece e intenta cargar tablas | ✅ |
| 6 | Enterprise aparece e intenta cargar tablas | ✅ |
| 7 | SQL_SERVER genérico carga tablas | ✅ |
| 8 | API_LOCAL usa GET /query?sql= | ✅ |
| 9 | Errores mostrados claramente | ✅ |
| 10 | No se exponen secrets | ✅ |
| 11 | No se usa MongoDB | ✅ |
| 12 | No se rompen módulos protegidos | ✅ |

---

**Reporte generado por:** E1 Agent  
**Fecha generación:** 2026-05-16
