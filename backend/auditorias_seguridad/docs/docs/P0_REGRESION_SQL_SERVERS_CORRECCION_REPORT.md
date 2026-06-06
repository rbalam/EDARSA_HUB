# P0 REGRESIÓN CRÍTICA - Corrección: Servidores SQL Restaurados

## Fecha: 2026-04-29

## Problema Reportado
Los servidores SQL desaparecieron de la UI después de implementar Conexiones API flexibles.

## Causa Raíz
El endpoint `/api/servers` estaba retornando TODOS los registros de `Servidores_Conexiones`, incluyendo los de tipo `API_LOCAL`.

Los registros `API_LOCAL` tienen campos NULL que el modelo Pydantic `Server` no acepta:
- `username: str` (recibía None)
- `date_calculation_method: str` (recibía None)
- `sucursales: List[str]` (recibía {})
- `categorias: List[str]` (recibía None)
- `departamentos: List[str]` (recibía None)

Esto causaba un `ResponseValidationError` que impedía que el endpoint respondiera.

## Solución Implementada

### Archivo modificado: `/app/backend/core/server_registry.py`

**Cambio 1 (línea ~201):** Agregar filtro para excluir `API_LOCAL` en consulta SQL
```python
# ANTES
conditions.append("(tipo_conexion != 'CORE' OR tipo_conexion IS NULL)")

# DESPUÉS
conditions.append("(tipo_conexion != 'CORE' OR tipo_conexion IS NULL)")
# Excluir conexiones API_LOCAL (tienen su propio endpoint /api/api-connections)
conditions.append("(tipo_conexion != 'API_LOCAL' OR tipo_conexion IS NULL)")
```

**Cambio 2 (línea ~318):** Agregar filtro en MongoDB fallback
```python
# ANTES
if exclude_core:
    servers = [s for s in servers if s.get('tipo_conexion') != 'CORE']

# DESPUÉS
if exclude_core:
    servers = [s for s in servers if s.get('tipo_conexion') != 'CORE']
# Excluir conexiones API_LOCAL (tienen su propio endpoint)
servers = [s for s in servers if s.get('tipo_conexion') != 'API_LOCAL']
```

## Verificaciones Realizadas

### 1. Endpoint /api/servers (SQL Servers)
```
Total servidores SQL: 8
  - 130° MERIDA: SoftRestaurant
  - CIENFUEGOS: SoftRestaurant
  - CIENFUEGOS TABLAJERIA: SoftRestaurant
  - HR2020 ESCRITURA: MPRO
  - LA ESTELAR: SoftRestaurant
  - ManagmentPro: MPRO
  - MPRO TABLAJERIA: MPRO
  - PRUEBAS SOFTRESTAURANT: SoftRestaurant
```
✅ **RESTAURADO**

### 2. Endpoint /api/api-connections (Conexiones API)
```
Total conexiones API: 2 (source: EDARSAHUB_SQL)
  - 130° QRO LOCAL
  - ORIGEN LOCAL
```
✅ **FUNCIONA POR SEPARADO**

### 3. Tablero Ejecutivo (Comercial)
```
Unidades: 5 (todas online)
```
✅ **SIN REGRESIÓN**

### 4. Base de datos EDARSAHUB SQL
```sql
SELECT tipo_conexion, COUNT(*) FROM Servidores_Conexiones WHERE activo=1 GROUP BY tipo_conexion
-- API_LOCAL: 2
-- CORE: 1
-- DATA_SOURCE: 8
```
✅ **DATOS INTACTOS**

## Arquitectura Confirmada

| Endpoint | Tipo | Fuente | Filtro |
|----------|------|--------|--------|
| `/api/servers` | SQL Servers | EDARSAHUB SQL | `tipo_conexion != 'API_LOCAL' AND tipo_conexion != 'CORE'` |
| `/api/api-connections` | APIs Locales | EDARSAHUB SQL | `tipo_conexion = 'API_LOCAL'` |

## No Regresión Confirmada

- ✅ Servidores SQL visibles en UI
- ✅ Conexiones API separadas en su pestaña
- ✅ Ping Todos funciona para SQL Servers
- ✅ Tablero Ejecutivo carga datos
- ✅ No hay duplicados
- ✅ No se perdieron conexiones
- ✅ EDARSAHUB SQL sigue siendo fuente primaria
- ✅ MongoDB NO es fuente primaria
