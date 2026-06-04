# Corrección Conexión SoftRestaurant - Sync Propinas TPV

**Fecha:** 2026-06-05  
**Agente:** E1  
**Problema:** Las conexiones SQL a CIENFUEGOS y LA ESTELAR fallaban al sincronizar propinas TPV

## Resumen Ejecutivo

Se identificó y corrigió la causa raíz del fallo de sincronización de propinas TPV desde los servidores SoftRestaurant (CIENFUEGOS, LA ESTELAR, 130° MERIDA). El problema NO era de conectividad de red ni de credenciales, sino un **filtro incompleto de `system_type`** en la consulta SQL que busca la información de conexión en EDARSAHUB.

## Causa Raíz

### Diagnóstico Técnico

1. **Conectividad TCP:** Los puertos TCP de los servidores CIENFUEGOS (6669) y LA ESTELAR (6969) respondían correctamente.

2. **Conexión SQL directa:** Las conexiones usando `pytds` y `pymssql` funcionaban perfectamente cuando se proporcionaban las credenciales directamente.

3. **Fallo en lookup de conexión:** La función `get_unidad_connection_info()` en `sync_propinas_softrestaurant.py` (línea 112-120) usaba un filtro SQL:
   ```sql
   AND s.system_type IN ('SoftRestaurant', 'SOFTRESTAURANT', 'SR')
   ```
   
   Pero los servidores en EDARSAHUB tienen `system_type = 'SOFTRESTAURANT_PRO'`, que **NO estaba en la lista**.

4. **Resultado:** La query retornaba 0 filas, por lo que `conn_info = None`, y el sync reportaba "Unidad no encontrada" sin intentar conexión alguna.

### Datos de los Servidores en EDARSAHUB

| Servidor | Host | Port | system_type (correcto) |
|----------|------|------|------------------------|
| CIENFUEGOS | servercienfuegos.ddns.net,6669\nationalsoft | 6669 | SOFTRESTAURANT_PRO |
| LA ESTELAR | serverestelar.ddns.net,6969 | 6969 | SOFTRESTAURANT_PRO |
| 130° MERIDA | 130mid.ddns.net | 1433 | SOFTRESTAURANT_PRO |

## Corrección Aplicada

### Archivos Modificados

1. **`/app/backend/modules/finanzas/sync_propinas_softrestaurant.py`** (línea 112)
2. **`/app/backend/modules/finanzas/sync_cortes_softrestaurant.py`** (línea 119)

### Cambio

```sql
-- ANTES (incompleto)
AND s.system_type IN ('SoftRestaurant', 'SOFTRESTAURANT', 'SR')

-- DESPUÉS (correcto)
AND s.system_type IN ('SoftRestaurant', 'SOFTRESTAURANT', 'SR', 'SOFTRESTAURANT_PRO')
```

## Validación Post-Corrección

### Prueba de Conexión

```
=== CIENFUEGOS ===
  ✅ Info de conexión encontrada
  ✅ Conexión establecida con driver: pytds
  📊 Total cheques con propina TPV: 3,644
  📊 Suma propinas TPV: $2,219,183.60

=== LA ESTELAR ===
  ✅ Info de conexión encontrada
  ✅ Conexión establecida con driver: pytds
  📊 Total cheques con propina TPV: 5,609
  📊 Suma propinas TPV: $1,139,390.05

=== 130° MERIDA ===
  ✅ Info de conexión encontrada
  ✅ Conexión establecida con driver: pytds
  📊 Total cheques con propina TPV: 3,025
  📊 Suma propinas TPV: $2,038,627.10
```

### Backfill Ejecutado

Rango: 2026-05-17 a 2026-06-05

| Unidad | Registros Insertados | Propinas TPV |
|--------|---------------------|--------------|
| 130° MERIDA | 231 | $193,840.44 |
| CIENFUEGOS | 405 | $247,194.79 |
| LA ESTELAR | 550 | $103,831.74 |
| **TOTAL** | **1,186** | **$544,866.97** |

### Verificación en EDARSAHUB

Los datos están correctamente almacenados en `propinas_tpv_control`:
- Rango de fechas: 2026-05-17 a 2026-06-03
- Total registros desde 17-may: 1,245
- Suma propinas TPV: $544,866.97

## Nota Técnica: pymssql vs pytds

Durante el diagnóstico se observó que:

- **pymssql** falla con CIENFUEGOS porque no maneja bien el formato `hostname,port\instance` (error "Adaptive Server is unavailable")
- **pytds** funciona correctamente con todos los formatos de conexión

La función `get_softrestaurant_connection()` ya tiene implementado el fallback correcto: primero intenta `pytds`, y si falla, usa `pymssql`. Por esta razón, una vez corregido el lookup, las conexiones funcionan.

## Recomendaciones Futuras

1. **Estandarizar `system_type`:** Considerar unificar todos los valores a `SOFTRESTAURANT_PRO` o crear una tabla de mapeo.

2. **Query defensiva:** Cambiar el filtro a:
   ```sql
   AND UPPER(s.system_type) LIKE '%SOFT%'
   ```
   
3. **Monitoreo:** Agregar alerta cuando `get_unidad_connection_info()` retorne `None` para detectar problemas de lookup rápidamente.

## Archivos Relacionados

- `/app/backend/modules/finanzas/sync_propinas_softrestaurant.py`
- `/app/backend/modules/finanzas/sync_cortes_softrestaurant.py`
- `/app/backend/core/db.py` (parse_sql_server_host)
- `/app/backend/core/secret_manager.py` (decrypt_secret)
