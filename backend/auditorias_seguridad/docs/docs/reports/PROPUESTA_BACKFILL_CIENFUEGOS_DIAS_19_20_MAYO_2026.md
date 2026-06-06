# PROPUESTA: Backfill CIENFUEGOS - Días 19 y 20 de Mayo 2026

**Fecha:** 2026-05-25  
**Autor:** E1 Agent  
**Estado:** PENDIENTE AUTORIZACIÓN PARA EJECUCIÓN

---

## 1. RESUMEN EJECUTIVO

### Problema
Los días 19 y 20 de mayo 2026 no están registrados en `Comercial_KPIs_Diarios_v2` para la unidad CIENFUEGOS.

### Causa Raíz REFINADA
**Falla de CONECTIVIDAD** (NO de credenciales) al servidor SoftRestaurant de CIENFUEGOS durante el período 2026-05-19 23:51 a 2026-05-21.

**Evidencia:**
- Último sync exitoso: 2026-05-19 23:47:06 (`source_connection_status = ONLINE`)
- Primer fallo: 2026-05-19 23:51:17 (`source_connection_status = OFFLINE`)
- El mensaje "Query retornó vacío - posible error de credenciales" es **GENÉRICO y ENGAÑOSO**
- Las credenciales SÍ funcionan (otros días se sincronizaron correctamente)

### Por qué no se recuperaron automáticamente
El job incremental usa `SYNC_INCREMENTAL_DAYS = 3` días. Cuando el sync se recuperó el 24 de mayo, solo trajo días 21-24. Los días 19 y 20 quedaron fuera del rango de backfill automático.

---

## 2. MECANISMO OFICIAL IDENTIFICADO

### Job de Sincronización
- **Archivo:** `/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py`
- **Función principal:** `execute_sync_comercial_v2()`
- **Función manual:** `run_sync_comercial_v2_manual(dias_atras, solo_unidades)`

### Módulo de Sync
- **Archivo:** `/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py`
- **Función:** `sync_softrestaurant_ventas_cerradas(config, fecha_inicio, fecha_fin, run_id)`
- **Destino:** `Comercial_KPIs_Diarios_v2` en EDARSAHUB

### Configuración de CIENFUEGOS
```python
UnidadNegocioConfig(
    unidad_negocio_id='CIENFUEGOS',
    unidad_negocio_nombre='CIENFUEGOS',
    server_id='6d053c22-523e-48c0-b72b-96081e2d781b',
    sucursal_id='DEFAULT',
    sucursal_nombre='CIENFUEGOS',
    sistema_origen=SistemaOrigen.SOFTRESTAURANT,
    activo=True
)
```

### Credenciales (desde `Servidores_Conexiones`)
- **Host:** servercienfuegos.ddns.net:6669
- **Base de datos:** softrestaurant95pro
- **Usuario:** CFLectura
- **Contraseña:** Encriptada con SERVER_SECRET_KEY

---

## 3. PROPUESTA DE BACKFILL OFICIAL

### Opción A: Usar función existente `sync_softrestaurant_ventas_cerradas`

Este es el mecanismo oficial y preferido porque:
1. Usa las mismas credenciales ya configuradas
2. Escribe en la misma tabla (`Comercial_KPIs_Diarios_v2`)
3. Genera el mismo formato de `sync_run_id`
4. Registra en `Comercial_SyncLog_v2`
5. Usa `upsert_kpi_diario` que previene duplicados automáticamente

### Script de Backfill Propuesto

```python
#!/usr/bin/env python3
"""
BACKFILL OFICIAL: CIENFUEGOS Días 19 y 20 de Mayo 2026
======================================================
Este script usa el mecanismo oficial de sincronización.
NO requiere credenciales manuales - usa las de EDARSAHUB.
"""

import uuid
import logging
from datetime import date

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ejecutar_backfill_cienfuegos():
    """
    Ejecuta backfill para CIENFUEGOS días 19 y 20 de mayo 2026
    usando el mecanismo oficial de sync.
    """
    from modules.comercial_v2.sync_comercial_edarsahub import (
        sync_softrestaurant_ventas_cerradas
    )
    from modules.comercial_v2.schemas import (
        UnidadNegocioConfig,
        SistemaOrigen
    )
    
    # Configuración de CIENFUEGOS (igual que el job oficial)
    config = UnidadNegocioConfig(
        unidad_negocio_id='CIENFUEGOS',
        unidad_negocio_nombre='CIENFUEGOS',
        server_id='6d053c22-523e-48c0-b72b-96081e2d781b',
        sucursal_id='DEFAULT',
        sucursal_nombre='CIENFUEGOS',
        sistema_origen=SistemaOrigen.SOFTRESTAURANT,
        activo=True
    )
    
    # Fechas a reconciliar
    fecha_inicio = date(2026, 5, 19)
    fecha_fin = date(2026, 5, 20)
    
    # Run ID con prefijo BACKFILL para trazabilidad
    run_id = f"BACKFILL-20260525-CIENFUEGOS-{str(uuid.uuid4())[:4]}"
    
    logger.info(f"=" * 60)
    logger.info(f"BACKFILL CIENFUEGOS: {fecha_inicio} a {fecha_fin}")
    logger.info(f"Run ID: {run_id}")
    logger.info(f"=" * 60)
    
    # Ejecutar sync usando función oficial
    resultado = sync_softrestaurant_ventas_cerradas(
        config=config,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        run_id=run_id
    )
    
    # Reportar resultado
    logger.info(f"\n{'='*60}")
    logger.info(f"RESULTADO DEL BACKFILL")
    logger.info(f"{'='*60}")
    logger.info(f"Éxito: {resultado.success}")
    logger.info(f"Procesados: {resultado.records_processed}")
    logger.info(f"Insertados: {resultado.records_inserted}")
    logger.info(f"Actualizados: {resultado.records_updated}")
    logger.info(f"Omitidos: {resultado.records_skipped}")
    logger.info(f"Errores: {resultado.records_errored}")
    logger.info(f"Duración: {resultado.duration_seconds} seg")
    
    if resultado.error_message:
        logger.error(f"Error: {resultado.error_message}")
    
    return resultado


if __name__ == '__main__':
    resultado = ejecutar_backfill_cienfuegos()
    
    if resultado.success and resultado.records_inserted > 0:
        print(f"\n✅ BACKFILL EXITOSO: {resultado.records_inserted} días insertados")
    elif resultado.success and resultado.records_inserted == 0:
        print(f"\n⚠️ BACKFILL COMPLETADO: 0 registros insertados (posiblemente ya existen o no hay datos en origen)")
    else:
        print(f"\n❌ BACKFILL FALLIDO: {resultado.error_message}")
```

---

## 4. IMPACTO ESPERADO

### Tablas Afectadas
| Tabla | Acción | Registros |
|-------|--------|-----------|
| `Comercial_KPIs_Diarios_v2` | INSERT | 2 (días 19 y 20) |
| `Comercial_SyncLog_v2` | INSERT | 1 (log del backfill) |

### Campos que se insertarán
```sql
-- Para cada día (19 y 20):
INSERT INTO Comercial_KPIs_Diarios_v2 (
    id,                      -- UUID nuevo
    unidad_negocio_id,       -- 'CIENFUEGOS'
    unidad_negocio_nombre,   -- 'CIENFUEGOS'
    server_id,               -- '6d053c22-523e-48c0-b72b-96081e2d781b'
    sucursal_id,             -- 'DEFAULT'
    sistema_origen,          -- 'SOFTRESTAURANT'
    fecha_operacion,         -- '2026-05-19' o '2026-05-20'
    anio, mes, dia,          -- Derivados de fecha_operacion
    ventas_total,            -- SUM(total) de cheques cerrados
    ventas_sin_propina,      -- SUM(total - propina)
    propinas_total,          -- SUM(propina)
    tickets_total,           -- COUNT(DISTINCT folio)
    pax_total,               -- SUM(nopersonas)
    ticket_promedio,         -- Calculado
    pax_promedio,            -- Calculado
    es_corte_cerrado,        -- 1 (TRUE)
    es_demo,                 -- 0 (FALSE)
    activo,                  -- 1 (TRUE)
    fuente_original,         -- 'SYNC_EDARSAHUB'
    sync_run_id,             -- 'BACKFILL-20260525-CIENFUEGOS-xxxx'
    fecha_sincronizacion,    -- GETUTCDATE()
    ...
)
```

---

## 5. PROTECCIÓN CONTRA DUPLICADOS

El mecanismo `upsert_kpi_diario` en `repository_comercial_edarsahub.py` usa:

```sql
-- Verifica si ya existe antes de insertar
SELECT id FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = @unidad
  AND fecha_operacion = @fecha
  AND activo = 1

-- Si existe: UPDATE (actualiza sync_run_id y fecha_sincronizacion)
-- Si no existe: INSERT
```

**Garantía:** No se crearán duplicados aunque el script se ejecute múltiples veces.

---

## 6. KPI DE VENTAS SIN PROPINAS

La query de SoftRestaurant extrae propinas por separado:

```sql
SELECT 
    ...
    SUM(total) as ventas_total,
    SUM(total - ISNULL(propina, 0)) as ventas_sin_propina,
    SUM(ISNULL(propina, 0)) as propinas,
    ...
FROM cheques
WHERE ...
```

El campo `ventas_sin_propina` está disponible para el dashboard si se requiere excluir propinas del KPI.

---

## 7. TRAZABILIDAD

### sync_run_id
Formato: `BACKFILL-20260525-CIENFUEGOS-xxxx`

Este ID permite:
1. Identificar registros insertados por backfill
2. Auditar qué días se reconciliaron
3. Distinguir de syncs automáticos (prefijo INCR-)

### Comercial_SyncLog_v2
Se insertará un registro con:
- `run_type`: 'INCREMENTAL' (mismo tipo que sync normal)
- `status`: 'SUCCESS' o 'FAILED'
- `records_inserted`: Número de días insertados
- `source_connection_status`: Estado de conexión al servidor origen

---

## 8. VALIDACIÓN PRE-EJECUCIÓN (SELECT)

Antes de ejecutar el backfill, se debe verificar:

```sql
-- 1. Confirmar que los días NO existen en destino
SELECT fecha_operacion, ventas_total
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = 'CIENFUEGOS'
  AND fecha_operacion IN ('2026-05-19', '2026-05-20')
  AND activo = 1;
-- Resultado esperado: 0 filas

-- 2. Confirmar conectividad al servidor origen
-- (El script lo verifica automáticamente)
```

---

## 9. COMANDO DE EJECUCIÓN

### Opción 1: Ejecutar script directamente
```bash
cd /app/backend
python3 -c "
from datetime import date
import uuid
import logging

logging.basicConfig(level=logging.INFO)

from modules.comercial_v2.sync_comercial_edarsahub import sync_softrestaurant_ventas_cerradas
from modules.comercial_v2.schemas import UnidadNegocioConfig, SistemaOrigen

config = UnidadNegocioConfig(
    unidad_negocio_id='CIENFUEGOS',
    unidad_negocio_nombre='CIENFUEGOS',
    server_id='6d053c22-523e-48c0-b72b-96081e2d781b',
    sucursal_id='DEFAULT',
    sucursal_nombre='CIENFUEGOS',
    sistema_origen=SistemaOrigen.SOFTRESTAURANT,
    activo=True
)

run_id = f'BACKFILL-20260525-CIENFUEGOS-{str(uuid.uuid4())[:4]}'
result = sync_softrestaurant_ventas_cerradas(config, date(2026, 5, 19), date(2026, 5, 20), run_id)

print(f'Éxito: {result.success}')
print(f'Insertados: {result.records_inserted}')
print(f'Error: {result.error_message}')
"
```

### Opción 2: Guardar como archivo y ejecutar
```bash
# Guardar script
cat > /app/backend/scripts/backfill_cienfuegos_mayo_2026.py << 'EOF'
# [contenido del script de la sección 3]
EOF

# Ejecutar
cd /app/backend && python3 -m scripts.backfill_cienfuegos_mayo_2026
```

---

## 10. VALIDACIÓN POST-EJECUCIÓN

```sql
-- 1. Verificar días insertados
SELECT 
    fecha_operacion,
    ventas_total,
    ventas_sin_propina,
    propinas_total,
    tickets_total,
    sync_run_id,
    fecha_sincronizacion
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = 'CIENFUEGOS'
  AND fecha_operacion IN ('2026-05-19', '2026-05-20')
  AND activo = 1;
-- Resultado esperado: 2 filas con datos reales

-- 2. Verificar total de días de mayo
SELECT COUNT(*) as dias_mayo
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = 'CIENFUEGOS'
  AND fecha_operacion BETWEEN '2026-05-01' AND '2026-05-25'
  AND activo = 1;
-- Resultado esperado: 24 días (22 + 2 backfill)

-- 3. Verificar log del backfill
SELECT *
FROM Comercial_SyncLog_v2
WHERE run_id LIKE 'BACKFILL-20260525-CIENFUEGOS%'
  AND unidad_negocio_id = 'CIENFUEGOS';
```

---

## 11. RIESGOS Y MITIGACIÓN

| Riesgo | Mitigación |
|--------|------------|
| Servidor CIENFUEGOS offline | El script fallará con error claro; reintentar cuando esté disponible |
| Datos no existen en origen | El script completará con 0 insertados; investigar SoftRestaurant |
| Duplicados | Imposible: upsert verifica antes de insertar |
| Propinas incluidas | Campo `ventas_sin_propina` disponible para dashboard |

---

## 12. AUTORIZACIÓN REQUERIDA

**Para ejecutar este backfill se requiere:**

1. ✅ Confirmación de que el servidor CIENFUEGOS está online
2. ⏳ Autorización para ejecutar INSERT en `Comercial_KPIs_Diarios_v2`
3. ⏳ Confirmación de que el entorno tiene `SERVER_SECRET_KEY` para descifrar credenciales

---

**Firmado:** E1 Agent  
**Estado:** PROPUESTA LISTA - PENDIENTE AUTORIZACIÓN PARA EJECUCIÓN
