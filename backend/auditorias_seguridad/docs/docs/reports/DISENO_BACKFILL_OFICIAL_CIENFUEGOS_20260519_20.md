# DISEÑO TÉCNICO: Backfill Oficial CIENFUEGOS desde EDARSAHUB

**Fecha:** 2026-05-25  
**Ticket:** P0-B RECONCILIACIÓN CIENFUEGOS  
**Estado:** PROPUESTA TÉCNICA - PENDIENTE AUTORIZACIÓN PARA IMPLEMENTAR

---

## 1. RESUMEN EJECUTIVO

Este documento describe el diseño técnico para crear un **endpoint administrativo de backfill** que se ejecutará desde el backend de EDARSAHUB, utilizando el mecanismo oficial de sincronización existente.

---

## 2. ARCHIVO A CREAR

**Ubicación:** `/app/backend/api/admin_backfill.py`

Este archivo implementará un endpoint REST que:
- Se ejecuta desde el ambiente de EDARSAHUB
- Usa la función oficial `sync_softrestaurant_ventas_cerradas`
- Obtiene credenciales de `Servidores_Conexiones`
- Registra trazabilidad completa

---

## 3. FUNCIÓN OFICIAL A REUTILIZAR

```python
# Ubicación: /app/backend/modules/comercial_v2/sync_comercial_edarsahub.py

def sync_softrestaurant_ventas_cerradas(
    config: UnidadNegocioConfig,
    fecha_inicio: date,
    fecha_fin: date,
    run_id: str
) -> SyncResult
```

### Parámetros Exactos para CIENFUEGOS

```python
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

fecha_inicio = date(2026, 5, 19)
fecha_fin = date(2026, 5, 20)
run_id = 'BACKFILL-CIENFUEGOS-20260519-20260520'
```

---

## 4. OBTENCIÓN DE CONFIGURACIÓN OFICIAL

La configuración se obtiene desde EDARSAHUB usando:

```python
# Ubicación: /app/backend/modules/comercial_v2/sync_comercial_edarsahub.py

def get_server_connection_config(server_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene configuración de Servidores_Conexiones.
    Descifra automáticamente password_encrypted usando SERVER_SECRET_KEY.
    """
```

### Query SQL que ejecuta:
```sql
SELECT 
    id, nombre, host, port, database_name, username, password_encrypted, system_type, activo
FROM Servidores_Conexiones
WHERE id = '6d053c22-523e-48c0-b72b-96081e2d781b'
```

### Resultado esperado:
```
Nombre: CIENFUEGOS
Host: servercienfuegos.ddns.net,6669\nationalsoft:1433
BD: softrestaurant95pro
Usuario: CFLectura
Password: [descifrada automáticamente con SERVER_SECRET_KEY]
```

---

## 5. VALIDACIÓN DE CONECTIVIDAD

El mecanismo oficial valida conectividad así:

```python
# En sync_softrestaurant_ventas_cerradas()
try:
    conn = pymssql.connect(
        server=config['host'],
        port=config['port'],
        database=config['database_name'],
        user=config['username'],
        password=config['password'],
        login_timeout=30
    )
    # Si llega aquí, connection_status = ONLINE
except:
    # connection_status = OFFLINE
    # Se registra en SyncLog con status = FAILED
```

---

## 6. VALIDACIÓN DE NO DUPLICADOS

El mecanismo oficial usa **UPSERT idempotente**:

```python
# Ubicación: /app/backend/modules/comercial_v2/repository_comercial_edarsahub.py

def upsert_kpi_diario(kpi: KPIsDiariosV2) -> bool:
    """
    UPSERT idempotente basado en (unidad_negocio_id, fecha_operacion).
    Si existe, actualiza. Si no existe, inserta.
    """
```

### Lógica interna:
```sql
-- Primero verifica si existe
SELECT id FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = @unidad_negocio_id
  AND fecha_operacion = @fecha_operacion
  AND activo = 1

-- Si existe: UPDATE (actualiza sync_run_id, fecha_sincronizacion, etc.)
-- Si no existe: INSERT
```

**Garantía:** Ejecutar el backfill múltiples veces NO crea duplicados.

---

## 7. CÁLCULO DE VENTA KPI SIN PROPINAS

### Query que extrae de SoftRestaurant:
```sql
-- En map_softrestaurant_ventas_cerradas()
SELECT 
    CAST(fecha AS DATE) AS fecha_operacion,
    SUM(total) AS ventas_total,
    SUM(total - ISNULL(propina, 0)) AS ventas_sin_propina,
    SUM(ISNULL(propina, 0)) AS propinas_total,
    COUNT(DISTINCT folio) AS tickets_total,
    SUM(ISNULL(nopersonas, 1)) AS pax_total
FROM cheques
WHERE CAST(fecha AS DATE) BETWEEN @fecha_inicio AND @fecha_fin
  AND cancelado = 0
  AND cierre IS NOT NULL  -- Solo cheques cerrados
GROUP BY CAST(fecha AS DATE)
```

### Campos en destino:
- `ventas_total`: Incluye propinas (para compatibilidad)
- `ventas_sin_propina`: **KPI DE VENTAS OFICIAL** (sin propinas)
- `propinas_total`: Propinas separadas

**Regla de negocio:** El Tablero Ejecutivo puede usar `ventas_sin_propina` para el KPI de ventas.

---

## 8. TABLAS AFECTADAS

| Tabla | Acción | Registros |
|-------|--------|-----------|
| `Comercial_KPIs_Diarios_v2` | UPSERT | 2 (días 19 y 20) |
| `Comercial_SyncLog_v2` | INSERT | 1 (log del backfill) |

### Nota: Tablas NO afectadas
- `Sync_Ventas_Historicas`: El job INCREMENTAL NO escribe aquí
- `Comercial_Ventas_Dia_Abiertas_v2`: Solo para días en curso (no aplica)

---

## 9. CAMPOS INSERTADOS/ACTUALIZADOS

```sql
INSERT INTO Comercial_KPIs_Diarios_v2 (
    -- Identificación
    id,                          -- UUID nuevo
    unidad_negocio_id,           -- 'CIENFUEGOS'
    unidad_negocio_nombre,       -- 'CIENFUEGOS'
    server_id,                   -- '6d053c22-523e-48c0-b72b-96081e2d781b'
    sucursal_id,                 -- 'DEFAULT'
    sucursal_nombre,             -- 'CIENFUEGOS'
    sistema_origen,              -- 'SOFTRESTAURANT'
    
    -- Fecha
    fecha_operacion,             -- '2026-05-19' o '2026-05-20'
    anio,                        -- 2026
    mes,                         -- 5
    dia,                         -- 19 o 20
    
    -- KPIs (PROPINAS SEPARADAS)
    ventas_total,                -- SUM(total) incluyendo propinas
    ventas_sin_propina,          -- SUM(total - propina) ← KPI OFICIAL
    propinas_total,              -- SUM(propina) ← SEPARADO
    tickets_total,               -- COUNT(cheques)
    pax_total,                   -- SUM(nopersonas)
    ticket_promedio,             -- ventas_total / tickets
    pax_promedio,                -- pax / tickets
    
    -- Control
    ventas_cerradas,             -- = ventas_total
    ventas_abiertas,             -- 0
    total_estimado_dia,          -- = ventas_total
    es_venta_abierta,            -- 0 (cerrado)
    es_corte_cerrado,            -- 1 (cerrado)
    es_demo,                     -- 0 (datos reales)
    activo,                      -- 1
    
    -- Trazabilidad
    fuente_original,             -- 'SYNC_EDARSAHUB'
    sync_run_id,                 -- 'BACKFILL-CIENFUEGOS-20260519-20260520'
    fecha_sincronizacion,        -- GETUTCDATE()
    fecha_alta,                  -- GETUTCDATE()
    fecha_ultima_actualizacion,  -- GETUTCDATE()
    version                      -- 1
)
```

---

## 10. SYNC_RUN_ID

**Formato:** `BACKFILL-CIENFUEGOS-20260519-20260520`

Este ID permite:
1. Identificar registros creados por backfill (vs INCR- para incrementales)
2. Auditar qué días se reconciliaron
3. Filtrar en `Comercial_SyncLog_v2`

---

## 11. ROLLBACK / RESGUARDO

### Opción A: DELETE antes de reinsertar
No recomendado. El UPSERT es idempotente.

### Opción B: Marcar como inactivo
```sql
-- Si se necesita revertir:
UPDATE Comercial_KPIs_Diarios_v2
SET activo = 0, fecha_ultima_actualizacion = GETUTCDATE()
WHERE sync_run_id = 'BACKFILL-CIENFUEGOS-20260519-20260520'
```

### Opción C: Backup previo
```sql
-- Crear tabla de backup antes del backfill
SELECT * INTO Comercial_KPIs_Diarios_v2_backup_pre_backfill_20260525
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = 'CIENFUEGOS'
  AND fecha_operacion IN ('2026-05-19', '2026-05-20')
```

**Recomendación:** Opción B + C combinadas.

---

## 12. LOGS GENERADOS

### Comercial_SyncLog_v2
```sql
INSERT INTO Comercial_SyncLog_v2 (
    run_id,                      -- 'BACKFILL-CIENFUEGOS-20260519-20260520'
    run_timestamp,               -- GETUTCDATE()
    run_type,                    -- 'INCREMENTAL' (mismo tipo que job normal)
    unidad_negocio_id,           -- 'CIENFUEGOS'
    server_id,                   -- '6d053c22-523e-48c0-b72b-96081e2d781b'
    fecha_inicio,                -- '2026-05-19'
    fecha_fin,                   -- '2026-05-20'
    status,                      -- 'SUCCESS' o 'FAILED'
    records_processed,           -- Número de días procesados
    records_inserted,            -- Número de días insertados
    records_updated,             -- Número de días actualizados
    records_skipped,             -- Número de días omitidos
    records_errored,             -- Número de errores
    source_connection_status,    -- 'ONLINE' o 'OFFLINE'
    error_code,                  -- NULL o código de error
    error_message,               -- NULL o mensaje de error
    duration_seconds             -- Duración en segundos
)
```

---

## 13. VALIDACIÓN POST-BACKFILL

### Query 1: Verificar días insertados
```sql
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
  AND activo = 1
ORDER BY fecha_operacion;

-- Resultado esperado: 2 filas con datos reales de SoftRestaurant
```

### Query 2: Verificar total de días mayo
```sql
SELECT COUNT(*) as total_dias_mayo
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = 'CIENFUEGOS'
  AND fecha_operacion BETWEEN '2026-05-01' AND '2026-05-25'
  AND activo = 1;

-- Resultado esperado: 24 días (22 existentes + 2 backfill)
-- Nota: día 25 puede estar en curso
```

### Query 3: Verificar log del backfill
```sql
SELECT *
FROM Comercial_SyncLog_v2
WHERE run_id = 'BACKFILL-CIENFUEGOS-20260519-20260520';

-- Resultado esperado: 1 fila con status='SUCCESS', records_inserted>=2
```

---

## 14. VALIDACIÓN DEL TABLERO EJECUTIVO

### Endpoint a validar:
```
GET /api/v2/comercial/dashboard
```

### Verificación:
1. El endpoint debe mostrar CIENFUEGOS con 24 días (en lugar de 22)
2. La venta total debe aumentar por los días 19 y 20
3. El campo `ventas_sin_propina` debe estar disponible

### Query que ejecuta el endpoint:
```sql
-- El endpoint lee de Comercial_KPIs_Diarios_v2
-- NO consulta SoftRestaurant directamente
SELECT 
    unidad_negocio_id,
    SUM(ventas_total) as ventas_total,
    SUM(ventas_sin_propina) as ventas_sin_propina,
    SUM(tickets_total) as tickets_total,
    COUNT(DISTINCT fecha_operacion) as dias
FROM Comercial_KPIs_Diarios_v2
WHERE fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin
  AND activo = 1 AND es_demo = 0
  AND unidad_negocio_id IN (@unidades_permitidas)
GROUP BY unidad_negocio_id
```

---

## 15. DISEÑO DEL ENDPOINT ADMINISTRATIVO

### Archivo: `/app/backend/api/admin_backfill.py`

```python
"""
API ADMINISTRATIVA: Backfill de KPIs Comerciales
================================================
Endpoint para ejecutar backfill de días faltantes desde EDARSAHUB.
Usa el mecanismo oficial de sincronización.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import date
from typing import Optional, List
import uuid
import logging

from core.auth import get_current_user, require_admin
from modules.comercial_v2.sync_comercial_edarsahub import (
    sync_softrestaurant_ventas_cerradas,
    sync_mpro_ventas_cerradas,
    get_server_connection_config
)
from modules.comercial_v2.schemas import (
    UnidadNegocioConfig,
    SistemaOrigen
)
from modules.comercial_v2.repository_comercial_edarsahub import (
    execute_edarsahub_query
)

router = APIRouter(prefix="/api/admin/backfill", tags=["Admin - Backfill"])
logger = logging.getLogger(__name__)


class BackfillRequest(BaseModel):
    """Request para ejecutar backfill."""
    unidad_negocio_id: str
    fecha_inicio: date
    fecha_fin: date
    dry_run: bool = True  # Por defecto solo simula


class BackfillResponse(BaseModel):
    """Response del backfill."""
    success: bool
    run_id: str
    unidad_negocio_id: str
    fecha_inicio: str
    fecha_fin: str
    dry_run: bool
    records_processed: int
    records_inserted: int
    records_updated: int
    records_skipped: int
    records_errored: int
    error_message: Optional[str] = None
    validacion_previa: dict
    validacion_posterior: Optional[dict] = None


# Configuración de unidades válidas para backfill
UNIDADES_CONFIG = {
    'CIENFUEGOS': {
        'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b',
        'sistema': SistemaOrigen.SOFTRESTAURANT,
        'sucursal_id': 'DEFAULT'
    },
    '130MID': {
        'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6',
        'sistema': SistemaOrigen.SOFTRESTAURANT,
        'sucursal_id': 'DEFAULT'
    },
    'ESTELAR': {
        'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f',
        'sistema': SistemaOrigen.SOFTRESTAURANT,
        'sucursal_id': 'DEFAULT'
    },
    '130QRO': {
        'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
        'sistema': SistemaOrigen.MPRO,
        'sucursal_id': '0021'
    },
    'ORIGEN': {
        'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
        'sistema': SistemaOrigen.MPRO,
        'sucursal_id': '0023'
    }
}


def _validar_dias_existentes(unidad_negocio_id: str, fecha_inicio: date, fecha_fin: date) -> dict:
    """Valida qué días ya existen en EDARSAHUB."""
    query = f"""
    SELECT 
        fecha_operacion,
        ventas_total,
        sync_run_id
    FROM Comercial_KPIs_Diarios_v2
    WHERE unidad_negocio_id = '{unidad_negocio_id}'
      AND fecha_operacion BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
      AND activo = 1
    ORDER BY fecha_operacion
    """
    
    try:
        resultado = execute_edarsahub_query(query)
        dias_existentes = [str(r['fecha_operacion']) for r in resultado]
        return {
            'dias_existentes': dias_existentes,
            'cantidad': len(dias_existentes)
        }
    except Exception as e:
        return {'error': str(e)}


def _validar_conectividad_servidor(server_id: str) -> dict:
    """Valida conectividad al servidor origen."""
    config = get_server_connection_config(server_id)
    
    if not config:
        return {'conectado': False, 'error': 'No se encontró configuración del servidor'}
    
    try:
        import pymssql
        conn = pymssql.connect(
            server=config['host'],
            port=config['port'],
            database=config['database_name'],
            user=config['username'],
            password=config['password'],
            login_timeout=30
        )
        conn.close()
        return {
            'conectado': True,
            'host': config['host'],
            'database': config['database_name']
        }
    except Exception as e:
        return {'conectado': False, 'error': str(e)}


@router.post("/ejecutar", response_model=BackfillResponse)
async def ejecutar_backfill(
    request: BackfillRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Ejecuta backfill de KPIs para una unidad y rango de fechas.
    
    CONDICIONES:
    - Solo usuarios admin pueden ejecutar
    - dry_run=True: solo simula, no modifica datos
    - dry_run=False: ejecuta el backfill real
    
    TRAZABILIDAD:
    - Genera sync_run_id único
    - Registra en Comercial_SyncLog_v2
    - Usa UPSERT idempotente
    """
    
    # Validar unidad
    if request.unidad_negocio_id not in UNIDADES_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unidad '{request.unidad_negocio_id}' no válida. Opciones: {list(UNIDADES_CONFIG.keys())}"
        )
    
    unidad_config = UNIDADES_CONFIG[request.unidad_negocio_id]
    
    # Generar run_id
    run_id = f"BACKFILL-{request.unidad_negocio_id}-{request.fecha_inicio.strftime('%Y%m%d')}-{request.fecha_fin.strftime('%Y%m%d')}"
    
    logger.info(f"[BACKFILL] Iniciando - Run ID: {run_id}")
    logger.info(f"[BACKFILL] Usuario: {current_user.get('email', 'N/A')}")
    logger.info(f"[BACKFILL] Unidad: {request.unidad_negocio_id}, Rango: {request.fecha_inicio} a {request.fecha_fin}")
    logger.info(f"[BACKFILL] Dry Run: {request.dry_run}")
    
    # Validación previa
    validacion_previa = {
        'dias_existentes': _validar_dias_existentes(
            request.unidad_negocio_id, 
            request.fecha_inicio, 
            request.fecha_fin
        ),
        'conectividad': _validar_conectividad_servidor(unidad_config['server_id'])
    }
    
    # Si no hay conectividad, abortar
    if not validacion_previa['conectividad'].get('conectado'):
        return BackfillResponse(
            success=False,
            run_id=run_id,
            unidad_negocio_id=request.unidad_negocio_id,
            fecha_inicio=request.fecha_inicio.isoformat(),
            fecha_fin=request.fecha_fin.isoformat(),
            dry_run=request.dry_run,
            records_processed=0,
            records_inserted=0,
            records_updated=0,
            records_skipped=0,
            records_errored=0,
            error_message=f"Sin conectividad al servidor: {validacion_previa['conectividad'].get('error')}",
            validacion_previa=validacion_previa
        )
    
    # Si es dry_run, solo retornar validación
    if request.dry_run:
        return BackfillResponse(
            success=True,
            run_id=run_id,
            unidad_negocio_id=request.unidad_negocio_id,
            fecha_inicio=request.fecha_inicio.isoformat(),
            fecha_fin=request.fecha_fin.isoformat(),
            dry_run=True,
            records_processed=0,
            records_inserted=0,
            records_updated=0,
            records_skipped=0,
            records_errored=0,
            error_message=None,
            validacion_previa=validacion_previa
        )
    
    # Ejecutar backfill real
    config = UnidadNegocioConfig(
        unidad_negocio_id=request.unidad_negocio_id,
        unidad_negocio_nombre=request.unidad_negocio_id,
        server_id=unidad_config['server_id'],
        sucursal_id=unidad_config['sucursal_id'],
        sucursal_nombre=request.unidad_negocio_id,
        sistema_origen=unidad_config['sistema'],
        activo=True
    )
    
    # Seleccionar función según sistema
    if unidad_config['sistema'] == SistemaOrigen.SOFTRESTAURANT:
        resultado = sync_softrestaurant_ventas_cerradas(
            config=config,
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
            run_id=run_id
        )
    else:  # MPRO
        resultado = sync_mpro_ventas_cerradas(
            config=config,
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
            run_id=run_id
        )
    
    # Validación posterior
    validacion_posterior = {
        'dias_existentes': _validar_dias_existentes(
            request.unidad_negocio_id,
            request.fecha_inicio,
            request.fecha_fin
        )
    }
    
    logger.info(f"[BACKFILL] Completado - Success: {resultado.success}, Insertados: {resultado.records_inserted}")
    
    return BackfillResponse(
        success=resultado.success,
        run_id=run_id,
        unidad_negocio_id=request.unidad_negocio_id,
        fecha_inicio=request.fecha_inicio.isoformat(),
        fecha_fin=request.fecha_fin.isoformat(),
        dry_run=False,
        records_processed=resultado.records_processed,
        records_inserted=resultado.records_inserted,
        records_updated=resultado.records_updated,
        records_skipped=resultado.records_skipped,
        records_errored=resultado.records_errored,
        error_message=resultado.error_message,
        validacion_previa=validacion_previa,
        validacion_posterior=validacion_posterior
    )


@router.get("/validar/{unidad_negocio_id}")
async def validar_unidad(
    unidad_negocio_id: str,
    fecha_inicio: date,
    fecha_fin: date,
    current_user: dict = Depends(require_admin)
):
    """
    Valida el estado de una unidad para backfill.
    Solo lectura, no modifica datos.
    """
    
    if unidad_negocio_id not in UNIDADES_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unidad '{unidad_negocio_id}' no válida"
        )
    
    unidad_config = UNIDADES_CONFIG[unidad_negocio_id]
    
    return {
        'unidad_negocio_id': unidad_negocio_id,
        'fecha_inicio': fecha_inicio.isoformat(),
        'fecha_fin': fecha_fin.isoformat(),
        'dias_existentes': _validar_dias_existentes(unidad_negocio_id, fecha_inicio, fecha_fin),
        'conectividad': _validar_conectividad_servidor(unidad_config['server_id'])
    }
```

---

## 16. REGISTRO DEL ROUTER

### Archivo a modificar: `/app/backend/server.py`

```python
# Agregar import
from api.admin_backfill import router as admin_backfill_router

# Agregar router (junto a los demás routers)
app.include_router(admin_backfill_router)
```

---

## 17. EJECUCIÓN DEL BACKFILL

### Paso 1: Validar (dry_run=true)
```bash
curl -X POST "https://[EDARSAHUB_URL]/api/admin/backfill/ejecutar" \
  -H "Authorization: Bearer [TOKEN_ADMIN]" \
  -H "Content-Type: application/json" \
  -d '{
    "unidad_negocio_id": "CIENFUEGOS",
    "fecha_inicio": "2026-05-19",
    "fecha_fin": "2026-05-20",
    "dry_run": true
  }'
```

### Paso 2: Ejecutar (dry_run=false)
```bash
curl -X POST "https://[EDARSAHUB_URL]/api/admin/backfill/ejecutar" \
  -H "Authorization: Bearer [TOKEN_ADMIN]" \
  -H "Content-Type: application/json" \
  -d '{
    "unidad_negocio_id": "CIENFUEGOS",
    "fecha_inicio": "2026-05-19",
    "fecha_fin": "2026-05-20",
    "dry_run": false
  }'
```

---

## 18. CRITERIO DE ACEPTACIÓN

| # | Criterio | Estado |
|---|----------|--------|
| 1 | Se ejecuta desde EDARSAHUB | ✅ Endpoint en backend |
| 2 | Usa mecanismo oficial | ✅ `sync_softrestaurant_ventas_cerradas` |
| 3 | Usa credenciales oficiales | ✅ `get_server_connection_config` |
| 4 | No depende de ejecución local | ✅ Es un endpoint REST |
| 5 | No cambia dashboard a live | ✅ Solo escribe en SQL |
| 6 | No incluye propinas en ventas | ✅ Campo `ventas_sin_propina` |
| 7 | Trazabilidad completa | ✅ `sync_run_id`, `SyncLog` |
| 8 | Reconcilia CIENFUEGOS 19-20 | ✅ Parámetros configurables |

---

## 19. SIGUIENTE PASO

**¿Autoriza implementar el endpoint administrativo de backfill?**

Una vez autorizado:
1. Crearé `/app/backend/api/admin_backfill.py`
2. Registraré el router en `server.py`
3. Ejecutaré validación con `dry_run=true`
4. Presentaré resultados antes de ejecutar `dry_run=false`

---

**Firmado:** E1 Agent  
**Rol:** Ingeniero Senior Fullstack + SQL Server Especialista EDARSAHUB  
**Estado:** DISEÑO TÉCNICO COMPLETO - PENDIENTE AUTORIZACIÓN PARA IMPLEMENTAR
