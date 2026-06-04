# PENDIENTE: VALIDAR_COLUMNAS_DESTINO_SYNC_COMPRAS

**Fecha de registro:** 2026-06-04  
**Prioridad:** P0 (Bloqueante para sincronización real)  
**Estado:** ⏳ PENDIENTE - Requiere acceso SSMS/Producción

---

## Objetivo

Confirmar que existen las columnas usadas por los comandos `MERGE` en `sync_service.py` **ANTES** de ejecutar la sincronización real (`dry_run=false`).

---

## Tablas a Validar

| # | Tabla | Tipo |
|---|-------|------|
| 1 | `Inventario_Movimientos` | Encabezado |
| 2 | `Inventario_MovimientosDetalle` | Detalle |
| 3 | `Compras_Pedidos` | Encabezado |
| 4 | `Compras_PedidosDetalle` | Detalle |
| 5 | `Compras_Ordenes` | Encabezado |
| 6 | `Compras_OrdenesDetalle` | Detalle |
| 7 | `Compras_Recepciones` | Encabezado |
| 8 | `Compras_RecepcionesDetalle` | Detalle |

---

## Query de Validación

Ejecutar en SSMS conectado a **EDARSAHUB**:

```sql
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo'
AND TABLE_NAME IN (
    'Inventario_Movimientos',
    'Inventario_MovimientosDetalle',
    'Compras_Pedidos',
    'Compras_PedidosDetalle',
    'Compras_Ordenes',
    'Compras_OrdenesDetalle',
    'Compras_Recepciones',
    'Compras_RecepcionesDetalle'
)
ORDER BY TABLE_NAME, ORDINAL_POSITION;
```

---

## Documento de Referencia

Los campos esperados por cada tabla están documentados en:
- `/app/docs/reports/CAMPOS_ESPERADOS_SYNC_*.md`

---

## Restricciones Activas (NO EJECUTAR)

| Acción | Estado |
|--------|--------|
| `POST /api/admin/sync/compras?dry_run=false` | ❌ BLOQUEADO |
| `COMPRAS_SQL_FIRST_ENABLED=true` | ❌ BLOQUEADO |
| Refactor Frontend SQL-First | ❌ BLOQUEADO |

---

## Criterio de Desbloqueo

1. Usuario ejecuta query de validación en SSMS
2. Usuario comparte resultados
3. Agente valida compatibilidad con MERGE
4. Si hay discrepancias → Generar DDL correctivo
5. Si compatible → Autorizar `dry_run=false`

---

## Archivos Relacionados

- `/app/backend/modules/compras/sync_service.py` (funciones MERGE)
- `/app/backend/core/scheduler/jobs/sync_compras_job.py` (job integrado)
- `/app/docs/reports/CAMPOS_ESPERADOS_SYNC_*.md` (campos esperados)
