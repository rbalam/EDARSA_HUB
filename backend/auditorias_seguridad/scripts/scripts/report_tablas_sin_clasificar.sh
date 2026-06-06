#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/app}"
OUT="$ROOT/docs/reports/MATRIZ_TABLAS_SIN_CLASIFICAR_EDARSAHUB.md"

mkdir -p "$ROOT/docs/reports"

cat > "$OUT" <<'MD'
# MATRIZ TABLAS SIN CLASIFICAR EDARSAHUB

Este reporte se genera desde SQL Server con la siguiente consulta:

```sql
SELECT
    esquema,
    nombre_tabla,
    modulo,
    categoria,
    estado,
    fuente_verdad,
    tabla_reemplazo,
    observaciones
FROM dbo.Sistema_Gobierno_Tablas
WHERE categoria = 'SIN_CLASIFICAR'
   OR modulo = 'Pendiente'
   OR estado IN ('REVISION', 'NO_USAR_NUEVO')
ORDER BY estado, modulo, categoria, nombre_tabla;
```

## Instrucciones

Para obtener el listado actualizado:

1. Ejecutar la consulta SQL anterior contra EDARSAHUB
2. Exportar resultados a CSV o copiar en este documento
3. Clasificar cada tabla pendiente con UPDATE en Sistema_Gobierno_Tablas

## Campos requeridos para clasificacion

| Campo | Descripcion |
|-------|-------------|
| modulo | Modulo propietario (AUTH, COMERCIAL, FINANZAS, INVENTARIOS, RH, SISTEMA, etc.) |
| categoria | CORE, SATELITE, SYNC, VISTA, PROCEDIMIENTO, TRANSICIONAL, LEGADO |
| estado | ACTIVA, DEPRECADA, NO_USAR_NUEVO, REVISION |
| fuente_verdad | S/N - Si esta tabla es la fuente autoritativa |
| tabla_reemplazo | Nombre de tabla canonica si esta es legado |

## Acciones por Estado

| Estado | Accion |
|--------|--------|
| SIN_CLASIFICAR | Revisar manualmente por modulo |
| REVISION | Validar canonicidad antes de uso nuevo |
| NO_USAR_NUEVO | No usar en desarrollo nuevo |
| LEGADO_REVISION | Mantener compatibilidad, no crecer |

## Pendientes (actualizar manualmente)

> Ejecutar consulta SQL y pegar resultados aqui

MD

echo "Plantilla generada: $OUT"
