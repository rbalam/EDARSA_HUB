# Corrección de Servidores Duplicados en MongoDB

**Fecha:** 2026-04-19  
**Autor:** EDARSA HUB / Arquitecto Software Senior  
**Ticket:** P0 - Corrección integridad referencial servidores

## Resumen Ejecutivo

Se corrigió el problema de servidores duplicados en MongoDB que impedía el correcto funcionamiento del módulo Compras > Auditoría Operativa.

## Diagnóstico

### Causa Raíz Identificada

| Servidor | ID Canónico (activo) | ID Duplicado (huérfano) |
|----------|---------------------|------------------------|
| LA ESTELAR | `a5ff0e25-f029-43db-b634-d4ac814c904f` | `57c1a273-27e8-4d01-8c14-087916607933` |
| 130° MERIDA | `a5547321-1139-4d2b-9d53-182ca737b6b6` | `572502c7-a993-4a05-9ade-e13651d687db` |

### Hallazgos Adicionales

1. **Los duplicados ya estaban con `active: false`** antes de esta intervención
2. **`sucursal_servidor_map`** ya apuntaba a los IDs canónicos correctos
3. **No existían referencias activas** a los IDs huérfanos en ninguna colección
4. **Bug secundario encontrado**: El endpoint `/api/compras/pedidos-vigentes` tenía una query SQL incorrecta para MPRO que usaba una tabla inexistente (`Requisicion_Compra_Detalle`)

## Acciones Realizadas

### 1. Snapshot de respaldo
```
/tmp/snapshot_final_20260419_082514/estado_actual.json
```

### 2. Marcado de servidores duplicados con metadata de deprecación

```javascript
// Campos agregados a los servidores huérfanos:
{
  "active": false,
  "deprecated": true,
  "deprecated_reason": "duplicado_huerfano_server_id",
  "deprecated_at": "2026-04-19T08:25:14...",
  "canonical_server_id": "<id_del_canonico>",
  "deprecation_notes": "Servidor duplicado de X. El ID canónico correcto es Y..."
}
```

### 3. Corrección de query SQL en endpoint MPRO

**Antes (query incorrecta):**
```sql
-- Usaba tabla inexistente Requisicion_Compra_Detalle
LEFT JOIN Requisicion_Compra_Detalle RCD ON RCD.Rc_Folio = RC.Rc_Folio
```

**Después (query corregida):**
```sql
-- Los productos están directamente en Requisicion_Compra
COUNT(RC.Pr_Cve_Producto) as total_productos
```

## Validaciones Realizadas

### Backend

| Endpoint | Resultado |
|----------|-----------|
| `/api/compras/pedidos-vigentes/{server_id}?sucursal=ORIGEN` | 77 requisiciones ✅ |
| `/api/comercial/tablero-ejecutivo` | Funcional con IDs canónicos ✅ |

### Frontend (Console Log)

```
[Auditoría] Requisiciones cargadas para sucursal "ORIGEN": 77 ✅
[Auditoría] Inventarios cargados para sucursal "ORIGEN": 1021 ✅
```

### No Regresiones

- Tablero Ejecutivo Comercial: ✅ Funcionando
- Módulo Compras > Dashboard: ✅ Funcionando
- Módulo Operaciones: ✅ Sin cambios

## Limitación Conocida

**Servidores SQL locales (LA ESTELAR, CIENFUEGOS)** no son accesibles desde el pod de Emergent por restricciones de red. El endpoint devuelve array vacío cuando se intenta conectar a estos servidores. Este es un problema de infraestructura de red, **no de integridad de datos**.

```
Error: Unable to connect: Adaptive Server is unavailable or does not exist (servercienfuegos.ddns.net)
```

## Confirmación de No Modificaciones

- [x] No se modificó `.env`
- [x] No se modificó `DB_NAME`
- [x] No se modificó `URI` ni conexión principal
- [x] Los duplicados NO fueron eliminados, solo marcados como deprecated

## Siguiente Paso Estructural (Post-P0)

Implementar resolución automática de `server_id` en EDARSA HUB basada en `empresa_id` + `sucursal_id`, eliminando la exposición directa del `server_id` en la UI de Compras > Auditoría.

**Este cambio NO se implementa en este P0.**

## Archivos Modificados

1. `/app/backend/server.py` - Líneas 5616-5635 (query corregida para MPRO)

## Archivos de Referencia

1. `/tmp/snapshot_final_20260419_082514/estado_actual.json`
2. `/tmp/snapshot_servers_duplicados.json` (snapshot previo)
