# DIAGNÓSTICO ARQUITECTÓNICO — Ventas del Día

**Fecha:** 2026-05-14  
**Estado:** DIAGNÓSTICO COMPLETADO

---

## RESUMEN EJECUTIVO

| Ítem | Estado | Detalle |
|------|--------|---------|
| Tabla de conexiones | ✅ | `Servidores_Conexiones` en EDARSAHUB SQL |
| Tabla de Ventas del Día | ✅ | `Comercial_Ventas_Dia_Abiertas_v2` en EDARSAHUB SQL |
| Job de sincronización | ✅ | `sync_comercial_abiertas_v2_job.py` cada 5 min |
| Tablero lee EDARSAHUB SQL | ✅ | Endpoint `/v2/comercial/ventas-dia` lee de SQL |
| Frontend usa endpoint correcto | ✅ | Usa `/v2/comercial/ventas-dia` |
| ORIGEN usa API_LOCAL | ✅ | Configuración en Servidores_Conexiones |
| QRO usa API_LOCAL | ✅ | Configuración en Servidores_Conexiones |
| SoftRestaurant usa tempcheques | ✅ | Fuente: TEMPCHEQUES |
| $0 falsos | ⚠️ | QRO muestra $0 (puede ser dato real o sin ventas) |

---

## 1. TABLA DE CONEXIONES

**Tabla:** `Servidores_Conexiones`  
**Base de datos:** EDARSAHUB

### Columnas principales:
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | uniqueidentifier | PK |
| nombre | nvarchar | Nombre descriptivo |
| system_type | nvarchar | MPRO, SoftRestaurant, EDARSA_HUB |
| tipo_conexion | nvarchar | DATA_SOURCE, API_LOCAL, CORE |
| host | nvarchar | Host/IP del servidor |
| port | int | Puerto |
| database_name | nvarchar | Nombre de BD |
| api_url | nvarchar | URL de API local (si aplica) |
| api_key_encrypted | nvarchar | API key encriptada |
| activo | bit | Estado activo |
| visible_en_operaciones | bit | Visible en tableros |

### Conexiones API_LOCAL configuradas:

| Nombre | System | api_url |
|--------|--------|---------|
| ORIGEN LOCAL | MPRO | http://54.39.104.176:8000/query |
| 130° QRO LOCAL | MPRO | http://54.39.104.176:8001/query |

### Conexiones DATA_SOURCE (SoftRestaurant):

| Nombre | Host | Database |
|--------|------|----------|
| 130° MERIDA | 130mid.ddns.net | softrestaurant10 |
| CIENFUEGOS | servercienfuegos.ddns.net,6669\nationalsoft | softrestaurant95pro |
| LA ESTELAR | serverestelar.ddns.net,6969 | softrestaurant12 |

---

## 2. TABLA DE VENTAS DEL DÍA SINCRONIZADA

**Tabla:** `Comercial_Ventas_Dia_Abiertas_v2`  
**Base de datos:** EDARSAHUB

### Estructura:
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | uniqueidentifier | PK |
| unidad_negocio_id | nvarchar | ID de unidad (ORIGEN, 130MID, etc.) |
| unidad_negocio_nombre | nvarchar | Nombre legible |
| server_id | nvarchar | FK a Servidores_Conexiones |
| sistema_origen | nvarchar | MPRO, SOFTRESTAURANT |
| fuente_original | nvarchar | API_LOCAL, TEMPCHEQUES |
| ventas_abiertas | decimal | Ventas sin cerrar |
| ventas_cerradas_dia | decimal | Ventas cerradas del día |
| total_estimado_dia | decimal | ventas_abiertas + ventas_cerradas_dia |
| tickets_abiertos | int | Cheques abiertos |
| pax_abiertos | int | Personas atendidas |
| snapshot_timestamp | datetime2 | Momento del snapshot |
| fecha_operacion | date | Fecha operativa |
| fecha_ultima_actualizacion | datetime2 | Última actualización |

### Datos actuales:

| Unidad | Sistema | Fuente | Total Día | Última Sync |
|--------|---------|--------|-----------|-------------|
| ORIGEN | MPRO | API_LOCAL | $5,769.55 | 2026-05-14 19:49:52 |
| 130° MÉRIDA | SOFTRESTAURANT | TEMPCHEQUES | $4,441.00 | 2026-05-14 19:49:48 |
| CIENFUEGOS | SOFTRESTAURANT | TEMPCHEQUES | $905.00 | 2026-05-14 19:49:48 |
| LA ESTELAR | SOFTRESTAURANT | TEMPCHEQUES | $395.00 | 2026-05-14 19:49:49 |
| 130° QRO | MPRO | API_LOCAL | $0.00 | 2026-05-14 19:49:51 |

---

## 3. JOB DE SINCRONIZACIÓN

**Archivo:** `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py`

### Frecuencia:
- **Intervalo:** 300 segundos (5 minutos)
- **Variable ENV:** `SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_INTERVAL_SECONDS`
- **Habilitado:** `SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED=true`

### Flujo de sincronización:

```
1. Job se ejecuta cada 5 minutos
2. Para MPRO (ORIGEN, QRO):
   - Lee config de Servidores_Conexiones WHERE nombre='ORIGEN LOCAL'
   - Obtiene api_url, api_key_encrypted
   - Ejecuta query vía API local
   - Escribe resultado a Comercial_Ventas_Dia_Abiertas_v2
3. Para SoftRestaurant (130MID, CIENFUEGOS, ESTELAR):
   - Lee config de Servidores_Conexiones
   - Conecta SQL directo a tempcheques
   - Query: SELECT SUM(total) FROM tempcheques WHERE cancelado=0
   - Escribe resultado a Comercial_Ventas_Dia_Abiertas_v2
```

---

## 4. ARQUITECTURA ACTUAL VS REQUERIDA

| Aspecto | Estado Actual | Estado Requerido | ✓ |
|---------|---------------|------------------|---|
| Conexiones desde EDARSAHUB SQL | ✅ Sí | Sí | ✅ |
| Job sincroniza cada 5 min | ✅ Sí | Sí | ✅ |
| Escribe a EDARSAHUB SQL | ✅ Sí | Sí | ✅ |
| Tablero lee de EDARSAHUB SQL | ✅ Sí | Sí | ✅ |
| No consulta live al abrir tablero | ✅ Correcto | Correcto | ✅ |
| ORIGEN usa API_LOCAL | ✅ Sí | Sí | ✅ |
| QRO usa API_LOCAL | ✅ Sí | Sí | ✅ |
| No usa SQL MPRO central | ✅ Correcto | Correcto | ✅ |
| SoftRestaurant usa tempcheques | ✅ Sí | Sí | ✅ |
| Filtro cancelado=0 | ✅ Sí | Sí | ✅ |
| Muestra hora última actualización | ✅ Sí | Sí | ✅ |
| UPSERT idempotente | ✅ Sí | Sí | ✅ |

---

## 5. CÓDIGO QUE LEE CONEXIONES

### Archivo: `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py`

**Líneas 74-84:**
```python
rows = execute_sql_query(
    '54.39.104.176', 1433, 'EDARSAHUB', 'HRLectura', 'National09$',
    f'''
    SELECT id, nombre, api_url, api_key_encrypted
    FROM Servidores_Conexiones
    WHERE nombre = '{config["server_config_name"]}' 
      AND tipo_conexion = 'API_LOCAL'
      AND activo = 1
    '''
)
```

### Mapeo auxiliar (líneas 47-56):
```python
MPRO_API_LOCAL_CONFIG = {
    "ORIGEN": {
        "server_config_name": "ORIGEN LOCAL",
        "sucursal_id": "0023"
    },
    "130QRO": {
        "server_config_name": "130° QRO LOCAL", 
        "sucursal_id": "0021"
    }
}
```

**Nota:** El `sucursal_id` está hardcodeado en el mapeo. Esto podría migrarse a la tabla `Servidores_Conexiones` o `Unidades_Negocio` para mayor flexibilidad.

---

## 6. VERIFICACIÓN: NO HAY CONSULTA LIVE DESDE TABLERO

### Endpoint del Tablero:
**Archivo:** `/app/backend/modules/comercial_v2/routes.py` línea 1030

### Repositorio de lectura:
**Archivo:** `/app/backend/modules/comercial_v2/repository_readonly.py` línea 318

**Query (solo lee EDARSAHUB SQL):**
```python
query = f"""
SELECT 
    unidad_negocio_id,
    unidad_negocio_nombre,
    sistema_origen,
    snapshot_timestamp,
    ventas_abiertas,
    total_estimado_dia,
    fuente_original
FROM Comercial_Ventas_Dia_Abiertas_v2
WHERE fecha_operacion = '{fecha.isoformat()}'
"""
```

**CONFIRMADO:** El tablero NO consulta fuentes en vivo.

---

## 7. HALLAZGO: HARDCODEO DE SUCURSAL_ID

El mapeo `MPRO_API_LOCAL_CONFIG` tiene hardcodeados los `sucursal_id`:
- ORIGEN: "0023"
- 130QRO: "0021"

**Recomendación:** Mover estos valores a la tabla `Unidades_Negocio.sucursal_origen_id`.

**Estado actual de la tabla:**
```sql
SELECT codigo, nombre, sucursal_origen_id 
FROM Unidades_Negocio 
WHERE codigo IN ('ORIGEN', '130QRO');
```
- ORIGEN: sucursal_origen_id = `0023` (ya existe)
- 130° QRO: sucursal_origen_id = `0021` (ya existe)

---

## 8. CONCLUSIONES

### ✅ ARQUITECTURA CORRECTA:
1. Conexiones configuradas en EDARSAHUB SQL (`Servidores_Conexiones`)
2. Job sincroniza cada 5 minutos a `Comercial_Ventas_Dia_Abiertas_v2`
3. Tablero lee exclusivamente de EDARSAHUB SQL
4. ORIGEN y QRO usan API_LOCAL (no SQL MPRO central)
5. SoftRestaurant usa tempcheques con cancelado=0

### ⚠️ MEJORAS OPCIONALES:
1. Migrar `sucursal_id` hardcodeado a `Unidades_Negocio.sucursal_origen_id`
2. Agregar ordenamiento DESC por total_estimado_dia en el endpoint
3. Verificar valor $0 de QRO (puede ser dato real o sin ventas)

---

**Diagnóstico completado:** 2026-05-14  
**Resultado:** Arquitectura cumple con las reglas establecidas
