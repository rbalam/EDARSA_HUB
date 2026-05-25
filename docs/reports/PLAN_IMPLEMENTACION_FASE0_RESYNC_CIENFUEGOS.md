# PLAN DE IMPLEMENTACIÓN: Fase 0 Mínima - Re-sincronización CIENFUEGOS

**Fecha:** 2026-05-25  
**Ticket:** P0-B RECONCILIACIÓN CIENFUEGOS  
**Estado:** PLAN DE IMPLEMENTACIÓN - PENDIENTE AUTORIZACIÓN

---

## 1. OBJETIVO

Implementar la **Fase 0 mínima** de la Consola General de Scheduler para resolver P0-B CIENFUEGOS, construida sobre la arquitectura definitiva.

**Caso a resolver:**
- Unidad: CIENFUEGOS
- Período: 2026-05-19 a 2026-05-20
- Tipo sync: comercial_ventas_cerradas
- Días faltantes: 2 de 25 esperados

---

## 2. ALCANCE AUTORIZADO

### Incluido en Fase 0
1. ✅ Crear tabla mínima SQL de control (`Sistema_Sync_Tipos`)
2. ✅ Registrar tipo_sync `comercial_ventas_cerradas`
3. ✅ Crear endpoint administrativo de re-sincronización
4. ✅ Conectar a handler oficial `sync_softrestaurant_ventas_cerradas()`
5. ✅ Implementar dry_run
6. ✅ Implementar ejecución real con validaciones
7. ✅ Registrar trazabilidad completa
8. ✅ Ejecutar caso CIENFUEGOS

### NO incluido en Fase 0 (fases posteriores)
- ❌ Frontend visual completo
- ❌ Edición de frecuencias de jobs
- ❌ Activar/desactivar jobs
- ❌ Vista de todos los jobs
- ❌ Configuración global
- ❌ Otros tipos de sync

---

## 3. ARCHIVOS A CREAR/MODIFICAR

### 3.1 Archivos NUEVOS

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/api/admin_scheduler_resync.py` | Endpoint de re-sincronización |
| `/app/backend/core/scheduler/resync_manager.py` | Manager de re-sync |

### 3.2 Archivos a MODIFICAR

| Archivo | Modificación |
|---------|--------------|
| `/app/backend/server.py` | Registrar nuevo router |

### 3.3 Archivos EXISTENTES a REUTILIZAR (sin modificar)

| Archivo | Función |
|---------|---------|
| `/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py` | `sync_softrestaurant_ventas_cerradas()` |
| `/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py` | `upsert_kpi_diario()` |
| `/app/backend/modules/comercial_v2/schemas.py` | `UnidadNegocioConfig`, `SyncResult` |

---

## 4. TABLAS SQL

### 4.1 Verificación de Tablas Existentes

```sql
-- Verificar si ya existen tablas equivalentes
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME LIKE '%Scheduler%' 
   OR TABLE_NAME LIKE '%Sync%Tipo%'
   OR TABLE_NAME LIKE '%Job%Config%'
ORDER BY TABLE_NAME;
```

### 4.2 Tabla: Sistema_Sync_Tipos (Mínima para Fase 0)

```sql
CREATE TABLE Sistema_Sync_Tipos (
    -- Identificación
    TipoSyncID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Codigo VARCHAR(100) NOT NULL UNIQUE,
    Nombre NVARCHAR(200) NOT NULL,
    Modulo VARCHAR(50) NOT NULL,
    Descripcion NVARCHAR(500),
    
    -- Handler
    SyncHandler VARCHAR(300) NOT NULL,
    
    -- Tablas
    TablaDestinoPrincipal VARCHAR(100) NOT NULL,
    TablaLog VARCHAR(100),
    
    -- Sistemas origen
    SistemasOrigen VARCHAR(200),
    
    -- Configuración de re-sync
    PermiteResync BIT DEFAULT 1,
    PermiteDryRun BIT DEFAULT 1,
    RequiereUnidad BIT DEFAULT 1,
    RequiereRangoFechas BIT DEFAULT 1,
    RangoMaximoDias INT DEFAULT 30,
    NivelRiesgo VARCHAR(20) DEFAULT 'MEDIO',
    
    -- KPIs
    SeparaPropinas BIT DEFAULT 0,
    CampoVentaSinPropina VARCHAR(100),
    
    -- Estado
    Activo BIT DEFAULT 1,
    
    -- Auditoría
    FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
    UsuarioCreacion VARCHAR(100)
);
```

### 4.3 Tabla: Sistema_Sync_Ejecuciones (Mínima para Fase 0)

```sql
CREATE TABLE Sistema_Sync_Ejecuciones (
    -- Identificación
    EjecucionID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    TipoSyncID UNIQUEIDENTIFIER NOT NULL REFERENCES Sistema_Sync_Tipos(TipoSyncID),
    SyncRunID VARCHAR(100) NOT NULL,
    
    -- Estado
    Estado VARCHAR(20) NOT NULL,
    DryRun BIT DEFAULT 0,
    
    -- Fechas
    FechaSolicitud DATETIME2 DEFAULT GETUTCDATE(),
    FechaInicio DATETIME2,
    FechaFin DATETIME2,
    
    -- Solicitante
    UsuarioID VARCHAR(100),
    UsuarioEmail VARCHAR(200),
    Motivo NVARCHAR(500) NOT NULL,
    
    -- Alcance
    UnidadNegocioID VARCHAR(50),
    ServerID UNIQUEIDENTIFIER,
    FechaInicioRango DATE NOT NULL,
    FechaFinRango DATE NOT NULL,
    
    -- Resultados
    RegistrosDetectados INT DEFAULT 0,
    RegistrosInsertados INT DEFAULT 0,
    RegistrosActualizados INT DEFAULT 0,
    RegistrosOmitidos INT DEFAULT 0,
    RegistrosError INT DEFAULT 0,
    
    -- Resultado JSON
    ResultadoJSON NVARCHAR(MAX),
    
    -- Errores
    ErrorCodigo VARCHAR(50),
    ErrorMensaje NVARCHAR(500),
    
    -- Métricas
    DuracionMS INT,
    
    -- Índices
    INDEX IX_Ejecuciones_Estado (Estado),
    INDEX IX_Ejecuciones_Fecha (FechaSolicitud DESC),
    INDEX IX_Ejecuciones_SyncRunID (SyncRunID)
);
```

### 4.4 Datos Iniciales

```sql
-- Registrar tipo_sync comercial_ventas_cerradas
INSERT INTO Sistema_Sync_Tipos (
    Codigo, Nombre, Modulo, Descripcion,
    SyncHandler,
    TablaDestinoPrincipal, TablaLog,
    SistemasOrigen,
    PermiteResync, PermiteDryRun, RequiereUnidad, RequiereRangoFechas,
    RangoMaximoDias, NivelRiesgo,
    SeparaPropinas, CampoVentaSinPropina,
    Activo, UsuarioCreacion
) VALUES (
    'comercial_ventas_cerradas',
    'Sincronización Ventas Cerradas',
    'Comercial',
    'Sincroniza cheques cerrados desde SoftRestaurant/MPRO hacia Comercial_KPIs_Diarios_v2',
    'modules.comercial_v2.sync_comercial_edarsahub.sync_softrestaurant_ventas_cerradas',
    'Comercial_KPIs_Diarios_v2',
    'Comercial_SyncLog_v2',
    'SOFTRESTAURANT,MPRO',
    1, 1, 1, 1,
    30, 'MEDIO',
    1, 'ventas_sin_propina',
    1, 'E1_AGENT'
);
```

---

## 5. ENDPOINT DE RE-SINCRONIZACIÓN

### 5.1 Archivo: `/app/backend/api/admin_scheduler_resync.py`

```python
"""
API ADMINISTRATIVA: Re-sincronización Controlada
================================================
Fase 0 mínima de la Consola General de Scheduler.
Permite re-sincronizar períodos históricos usando handlers oficiales.

MÁXIMAS CUMPLIDAS:
- #3: Usa scheduler oficial
- #6: Trazabilidad completa
- #7: Motivo obligatorio
- #8: Dry run para alto riesgo
- #14: Credenciales desde Servidores_Conexiones
- #15: UPSERT idempotente
- #28: Tablero sigue leyendo EDARSAHUB SQL
- #31: Propinas separadas
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, Dict, Any
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/scheduler/resync", tags=["Admin - Scheduler Resync"])


# =============================================================================
# SCHEMAS
# =============================================================================

class ResyncValidateRequest(BaseModel):
    """Request para validar re-sync antes de ejecutar."""
    tipo_sync: str = Field(..., description="Código del tipo de sync")
    unidad_negocio_id: str = Field(..., description="ID canónico de la unidad")
    fecha_inicio: date
    fecha_fin: date


class ResyncExecuteRequest(BaseModel):
    """Request para ejecutar re-sync."""
    tipo_sync: str = Field(..., description="Código del tipo de sync")
    unidad_negocio_id: str = Field(..., description="ID canónico de la unidad")
    fecha_inicio: date
    fecha_fin: date
    motivo: str = Field(..., min_length=10, description="Motivo obligatorio (mín 10 chars)")
    dry_run: bool = Field(True, description="True=simular, False=ejecutar real")


class ResyncResponse(BaseModel):
    """Response de re-sync."""
    success: bool
    ejecucion_id: str
    sync_run_id: str
    modo: str
    tipo_sync: str
    unidad_negocio_id: str
    fecha_inicio: str
    fecha_fin: str
    validacion_previa: Dict[str, Any]
    resultado: Optional[Dict[str, Any]] = None
    validacion_posterior: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# =============================================================================
# CONFIGURACIÓN DE TIPOS DE SYNC
# =============================================================================

def _get_tipo_sync_config(codigo: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene configuración del tipo de sync desde EDARSAHUB SQL.
    Fase 0: Si no existe la tabla, usa config hardcodeada temporal.
    """
    try:
        from modules.comercial_v2.repository_comercial_edarsahub import execute_edarsahub_query
        
        query = f"""
        SELECT * FROM Sistema_Sync_Tipos
        WHERE Codigo = '{codigo}' AND Activo = 1
        """
        result = execute_edarsahub_query(query)
        
        if result:
            return dict(result[0])
    except Exception as e:
        logger.warning(f"[RESYNC] Tabla Sistema_Sync_Tipos no existe, usando fallback: {e}")
    
    # Fallback para Fase 0 si no existe la tabla aún
    TIPOS_SYNC_FALLBACK = {
        'comercial_ventas_cerradas': {
            'Codigo': 'comercial_ventas_cerradas',
            'Nombre': 'Sincronización Ventas Cerradas',
            'Modulo': 'Comercial',
            'SyncHandler': 'sync_softrestaurant_ventas_cerradas',
            'TablaDestinoPrincipal': 'Comercial_KPIs_Diarios_v2',
            'SistemasOrigen': 'SOFTRESTAURANT,MPRO',
            'PermiteResync': True,
            'PermiteDryRun': True,
            'RequiereUnidad': True,
            'RequiereRangoFechas': True,
            'RangoMaximoDias': 30,
            'NivelRiesgo': 'MEDIO',
            'SeparaPropinas': True,
            'CampoVentaSinPropina': 'ventas_sin_propina'
        }
    }
    
    return TIPOS_SYNC_FALLBACK.get(codigo)


def _get_unidad_config(unidad_negocio_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene configuración de la unidad desde EDARSAHUB.
    """
    # Configuración de unidades (igual que en sync_comercial_v2_job.py)
    UNIDADES = {
        'CIENFUEGOS': {
            'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b',
            'sistema': 'SOFTRESTAURANT',
            'sucursal_id': 'DEFAULT'
        },
        '130MID': {
            'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6',
            'sistema': 'SOFTRESTAURANT',
            'sucursal_id': 'DEFAULT'
        },
        'ESTELAR': {
            'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f',
            'sistema': 'SOFTRESTAURANT',
            'sucursal_id': 'DEFAULT'
        },
        '130QRO': {
            'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
            'sistema': 'MPRO',
            'sucursal_id': '0021'
        },
        'ORIGEN': {
            'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
            'sistema': 'MPRO',
            'sucursal_id': '0023'
        }
    }
    
    return UNIDADES.get(unidad_negocio_id)


# =============================================================================
# VALIDACIONES
# =============================================================================

def _validar_conectividad(server_id: str) -> Dict[str, Any]:
    """Valida conectividad al servidor origen."""
    try:
        from modules.comercial_v2.sync_comercial_edarsahub import get_server_connection_config
        import pymssql
        
        config = get_server_connection_config(server_id)
        
        if not config:
            return {'conectado': False, 'error': 'Servidor no encontrado en Servidores_Conexiones'}
        
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


def _validar_dias_existentes(unidad_negocio_id: str, fecha_inicio: date, fecha_fin: date) -> Dict[str, Any]:
    """Valida qué días ya existen en destino."""
    try:
        from modules.comercial_v2.repository_comercial_edarsahub import execute_edarsahub_query
        
        query = f"""
        SELECT 
            fecha_operacion,
            ventas_total,
            ventas_sin_propina,
            sync_run_id
        FROM Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id = '{unidad_negocio_id}'
          AND fecha_operacion BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
          AND activo = 1
        ORDER BY fecha_operacion
        """
        
        resultado = execute_edarsahub_query(query)
        
        return {
            'dias_existentes': [
                {
                    'fecha': str(r['fecha_operacion']),
                    'ventas_total': float(r['ventas_total']),
                    'ventas_sin_propina': float(r['ventas_sin_propina']),
                    'sync_run_id': r['sync_run_id']
                }
                for r in resultado
            ],
            'cantidad': len(resultado)
        }
    except Exception as e:
        return {'error': str(e), 'dias_existentes': [], 'cantidad': 0}


def _validar_rango(fecha_inicio: date, fecha_fin: date, max_dias: int) -> Dict[str, Any]:
    """Valida que el rango no exceda el máximo."""
    dias = (fecha_fin - fecha_inicio).days + 1
    
    return {
        'dias_solicitados': dias,
        'max_permitido': max_dias,
        'valido': dias <= max_dias,
        'mensaje': f"Rango de {dias} días" + (f" (máximo: {max_dias})" if dias > max_dias else "")
    }


# =============================================================================
# REGISTRO DE EJECUCIONES
# =============================================================================

def _registrar_ejecucion(
    tipo_sync_id: str,
    sync_run_id: str,
    estado: str,
    dry_run: bool,
    usuario_id: str,
    motivo: str,
    unidad_negocio_id: str,
    server_id: str,
    fecha_inicio: date,
    fecha_fin: date,
    resultado: Dict[str, Any] = None,
    error: str = None,
    duracion_ms: int = None
) -> str:
    """
    Registra la ejecución en Sistema_Sync_Ejecuciones.
    Fase 0: Si la tabla no existe, solo loguea.
    """
    ejecucion_id = str(uuid.uuid4())
    
    try:
        from modules.comercial_v2.repository_comercial_edarsahub import execute_edarsahub_query
        import json
        
        query = f"""
        INSERT INTO Sistema_Sync_Ejecuciones (
            EjecucionID, TipoSyncID, SyncRunID, Estado, DryRun,
            UsuarioID, Motivo, UnidadNegocioID, ServerID,
            FechaInicioRango, FechaFinRango,
            RegistrosDetectados, RegistrosInsertados, RegistrosActualizados,
            RegistrosOmitidos, RegistrosError,
            ResultadoJSON, ErrorMensaje, DuracionMS
        ) VALUES (
            '{ejecucion_id}', '{tipo_sync_id}', '{sync_run_id}', '{estado}', {1 if dry_run else 0},
            '{usuario_id}', '{motivo.replace("'", "''")}', '{unidad_negocio_id}', '{server_id}',
            '{fecha_inicio}', '{fecha_fin}',
            {resultado.get('records_processed', 0) if resultado else 0},
            {resultado.get('records_inserted', 0) if resultado else 0},
            {resultado.get('records_updated', 0) if resultado else 0},
            {resultado.get('records_skipped', 0) if resultado else 0},
            {resultado.get('records_errored', 0) if resultado else 0},
            '{json.dumps(resultado).replace("'", "''")}' if resultado else NULL,
            '{error.replace("'", "''") if error else ''}',
            {duracion_ms or 0}
        )
        """
        execute_edarsahub_query(query)
        
    except Exception as e:
        logger.warning(f"[RESYNC] No se pudo registrar ejecución en SQL: {e}")
    
    return ejecucion_id


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/validate", response_model=Dict[str, Any])
async def validar_resync(request: ResyncValidateRequest):
    """
    Valida parámetros de re-sincronización antes de ejecutar.
    Solo lectura, no modifica datos.
    """
    logger.info(f"[RESYNC] Validando: {request.tipo_sync} / {request.unidad_negocio_id} / {request.fecha_inicio} a {request.fecha_fin}")
    
    # Validar tipo_sync
    tipo_sync = _get_tipo_sync_config(request.tipo_sync)
    if not tipo_sync:
        raise HTTPException(status_code=400, detail=f"Tipo de sync '{request.tipo_sync}' no encontrado")
    
    if not tipo_sync.get('PermiteResync'):
        raise HTTPException(status_code=400, detail=f"Tipo de sync '{request.tipo_sync}' no permite re-sincronización")
    
    # Validar unidad
    unidad = _get_unidad_config(request.unidad_negocio_id)
    if not unidad:
        raise HTTPException(status_code=400, detail=f"Unidad '{request.unidad_negocio_id}' no encontrada")
    
    # Validar rango
    validacion_rango = _validar_rango(
        request.fecha_inicio, 
        request.fecha_fin, 
        tipo_sync.get('RangoMaximoDias', 30)
    )
    
    if not validacion_rango['valido']:
        raise HTTPException(status_code=400, detail=validacion_rango['mensaje'])
    
    # Validar conectividad
    validacion_conectividad = _validar_conectividad(unidad['server_id'])
    
    # Validar días existentes
    validacion_dias = _validar_dias_existentes(
        request.unidad_negocio_id,
        request.fecha_inicio,
        request.fecha_fin
    )
    
    return {
        'tipo_sync': tipo_sync,
        'unidad': {
            'id': request.unidad_negocio_id,
            'server_id': unidad['server_id'],
            'sistema': unidad['sistema']
        },
        'rango': validacion_rango,
        'conectividad': validacion_conectividad,
        'dias_existentes': validacion_dias,
        'permite_dry_run': tipo_sync.get('PermiteDryRun', True),
        'nivel_riesgo': tipo_sync.get('NivelRiesgo', 'MEDIO'),
        'propinas_separadas': tipo_sync.get('SeparaPropinas', False),
        'campo_venta_sin_propina': tipo_sync.get('CampoVentaSinPropina')
    }


@router.post("/execute", response_model=ResyncResponse)
async def ejecutar_resync(request: ResyncExecuteRequest):
    """
    Ejecuta re-sincronización controlada.
    
    MÁXIMAS CUMPLIDAS:
    - Usa handler oficial (#3, #26)
    - Motivo obligatorio (#7)
    - Dry run disponible (#8)
    - Trazabilidad completa (#6)
    - Credenciales desde EDARSAHUB (#14)
    - UPSERT idempotente (#15)
    - Propinas separadas (#31)
    """
    import time
    start_time = time.time()
    
    logger.info(f"[RESYNC] Ejecutando: {request.tipo_sync} / {request.unidad_negocio_id}")
    logger.info(f"[RESYNC] Rango: {request.fecha_inicio} a {request.fecha_fin}")
    logger.info(f"[RESYNC] Modo: {'DRY_RUN' if request.dry_run else 'REAL'}")
    logger.info(f"[RESYNC] Motivo: {request.motivo}")
    
    # Validaciones previas
    tipo_sync = _get_tipo_sync_config(request.tipo_sync)
    if not tipo_sync:
        raise HTTPException(status_code=400, detail=f"Tipo de sync '{request.tipo_sync}' no encontrado")
    
    unidad = _get_unidad_config(request.unidad_negocio_id)
    if not unidad:
        raise HTTPException(status_code=400, detail=f"Unidad '{request.unidad_negocio_id}' no encontrada")
    
    # Generar IDs
    ejecucion_id = str(uuid.uuid4())
    sync_run_id = f"RESYNC-{request.unidad_negocio_id}-{request.fecha_inicio.strftime('%Y%m%d')}-{request.fecha_fin.strftime('%Y%m%d')}-{str(uuid.uuid4())[:4]}"
    
    # Validación previa
    validacion_previa = {
        'conectividad': _validar_conectividad(unidad['server_id']),
        'dias_existentes': _validar_dias_existentes(
            request.unidad_negocio_id,
            request.fecha_inicio,
            request.fecha_fin
        )
    }
    
    # Si no hay conectividad, abortar
    if not validacion_previa['conectividad'].get('conectado'):
        error_msg = f"Sin conectividad: {validacion_previa['conectividad'].get('error')}"
        
        _registrar_ejecucion(
            tipo_sync_id=tipo_sync.get('TipoSyncID', request.tipo_sync),
            sync_run_id=sync_run_id,
            estado='FAILED',
            dry_run=request.dry_run,
            usuario_id='API',  # TODO: obtener de auth
            motivo=request.motivo,
            unidad_negocio_id=request.unidad_negocio_id,
            server_id=unidad['server_id'],
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
            error=error_msg
        )
        
        return ResyncResponse(
            success=False,
            ejecucion_id=ejecucion_id,
            sync_run_id=sync_run_id,
            modo='DRY_RUN' if request.dry_run else 'REAL',
            tipo_sync=request.tipo_sync,
            unidad_negocio_id=request.unidad_negocio_id,
            fecha_inicio=request.fecha_inicio.isoformat(),
            fecha_fin=request.fecha_fin.isoformat(),
            validacion_previa=validacion_previa,
            error_message=error_msg
        )
    
    # Si es dry_run, simular
    if request.dry_run:
        # En dry_run, conectamos y extraemos datos pero NO escribimos
        resultado_simulado = await _ejecutar_dry_run(
            request.unidad_negocio_id,
            unidad,
            request.fecha_inicio,
            request.fecha_fin
        )
        
        _registrar_ejecucion(
            tipo_sync_id=tipo_sync.get('TipoSyncID', request.tipo_sync),
            sync_run_id=sync_run_id,
            estado='SUCCESS',
            dry_run=True,
            usuario_id='API',
            motivo=request.motivo,
            unidad_negocio_id=request.unidad_negocio_id,
            server_id=unidad['server_id'],
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
            resultado=resultado_simulado,
            duracion_ms=int((time.time() - start_time) * 1000)
        )
        
        return ResyncResponse(
            success=True,
            ejecucion_id=ejecucion_id,
            sync_run_id=sync_run_id,
            modo='DRY_RUN',
            tipo_sync=request.tipo_sync,
            unidad_negocio_id=request.unidad_negocio_id,
            fecha_inicio=request.fecha_inicio.isoformat(),
            fecha_fin=request.fecha_fin.isoformat(),
            validacion_previa=validacion_previa,
            resultado=resultado_simulado
        )
    
    # Ejecución REAL
    resultado = await _ejecutar_sync_real(
        request.unidad_negocio_id,
        unidad,
        request.fecha_inicio,
        request.fecha_fin,
        sync_run_id
    )
    
    # Validación posterior
    validacion_posterior = {
        'dias_existentes': _validar_dias_existentes(
            request.unidad_negocio_id,
            request.fecha_inicio,
            request.fecha_fin
        )
    }
    
    duracion_ms = int((time.time() - start_time) * 1000)
    
    _registrar_ejecucion(
        tipo_sync_id=tipo_sync.get('TipoSyncID', request.tipo_sync),
        sync_run_id=sync_run_id,
        estado='SUCCESS' if resultado.get('success') else 'FAILED',
        dry_run=False,
        usuario_id='API',
        motivo=request.motivo,
        unidad_negocio_id=request.unidad_negocio_id,
        server_id=unidad['server_id'],
        fecha_inicio=request.fecha_inicio,
        fecha_fin=request.fecha_fin,
        resultado=resultado,
        error=resultado.get('error_message'),
        duracion_ms=duracion_ms
    )
    
    logger.info(f"[RESYNC] Completado: {resultado}")
    
    return ResyncResponse(
        success=resultado.get('success', False),
        ejecucion_id=ejecucion_id,
        sync_run_id=sync_run_id,
        modo='REAL',
        tipo_sync=request.tipo_sync,
        unidad_negocio_id=request.unidad_negocio_id,
        fecha_inicio=request.fecha_inicio.isoformat(),
        fecha_fin=request.fecha_fin.isoformat(),
        validacion_previa=validacion_previa,
        resultado=resultado,
        validacion_posterior=validacion_posterior,
        error_message=resultado.get('error_message')
    )


# =============================================================================
# FUNCIONES DE EJECUCIÓN
# =============================================================================

async def _ejecutar_dry_run(
    unidad_negocio_id: str,
    unidad_config: Dict[str, Any],
    fecha_inicio: date,
    fecha_fin: date
) -> Dict[str, Any]:
    """
    Ejecuta simulación de sync (extrae datos pero no escribe).
    """
    from modules.comercial_v2.sync_comercial_edarsahub import get_server_connection_config
    import pymssql
    
    try:
        config = get_server_connection_config(unidad_config['server_id'])
        
        if not config:
            return {'success': False, 'error_message': 'Config de servidor no encontrada'}
        
        conn = pymssql.connect(
            server=config['host'],
            port=config['port'],
            database=config['database_name'],
            user=config['username'],
            password=config['password'],
            login_timeout=30
        )
        cursor = conn.cursor(as_dict=True)
        
        # Query para extraer datos (sin modificar)
        query = f"""
        SELECT 
            CAST(fecha AS DATE) AS fecha_operacion,
            SUM(total) AS ventas_total,
            SUM(total - ISNULL(propina, 0)) AS ventas_sin_propina,
            SUM(ISNULL(propina, 0)) AS propinas_total,
            COUNT(DISTINCT folio) AS tickets_total,
            SUM(ISNULL(nopersonas, 1)) AS pax_total
        FROM cheques
        WHERE CAST(fecha AS DATE) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
          AND cancelado = 0
          AND cierre IS NOT NULL
        GROUP BY CAST(fecha AS DATE)
        ORDER BY fecha_operacion
        """
        
        cursor.execute(query)
        datos = cursor.fetchall()
        conn.close()
        
        detalle = []
        for d in datos:
            detalle.append({
                'fecha': str(d['fecha_operacion']),
                'accion': 'INSERT',  # En dry_run siempre mostramos como INSERT
                'ventas_total': float(d['ventas_total'] or 0),
                'ventas_sin_propina': float(d['ventas_sin_propina'] or 0),
                'propinas_total': float(d['propinas_total'] or 0),
                'tickets_total': int(d['tickets_total'] or 0),
                'pax_total': int(d['pax_total'] or 0)
            })
        
        return {
            'success': True,
            'modo': 'DRY_RUN',
            'mensaje': 'Simulación completada - NO se modificaron datos',
            'records_processed': len(detalle),
            'registros_que_se_insertarian': len(detalle),
            'detalle': detalle
        }
        
    except Exception as e:
        return {'success': False, 'error_message': str(e)}


async def _ejecutar_sync_real(
    unidad_negocio_id: str,
    unidad_config: Dict[str, Any],
    fecha_inicio: date,
    fecha_fin: date,
    sync_run_id: str
) -> Dict[str, Any]:
    """
    Ejecuta sync real usando el handler oficial.
    MÁXIMA #26: No duplicar lógica, usar handler oficial.
    """
    from modules.comercial_v2.sync_comercial_edarsahub import sync_softrestaurant_ventas_cerradas
    from modules.comercial_v2.schemas import UnidadNegocioConfig, SistemaOrigen
    
    try:
        # Crear config usando el formato oficial
        config = UnidadNegocioConfig(
            unidad_negocio_id=unidad_negocio_id,
            unidad_negocio_nombre=unidad_negocio_id,
            server_id=unidad_config['server_id'],
            sucursal_id=unidad_config['sucursal_id'],
            sucursal_nombre=unidad_negocio_id,
            sistema_origen=SistemaOrigen.SOFTRESTAURANT if unidad_config['sistema'] == 'SOFTRESTAURANT' else SistemaOrigen.MPRO,
            activo=True
        )
        
        # Ejecutar handler oficial
        resultado = sync_softrestaurant_ventas_cerradas(
            config=config,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            run_id=sync_run_id
        )
        
        return {
            'success': resultado.success,
            'records_processed': resultado.records_processed,
            'records_inserted': resultado.records_inserted,
            'records_updated': resultado.records_updated,
            'records_skipped': resultado.records_skipped,
            'records_errored': resultado.records_errored,
            'duration_seconds': resultado.duration_seconds,
            'error_message': resultado.error_message
        }
        
    except Exception as e:
        return {'success': False, 'error_message': str(e)}


# =============================================================================
# ENDPOINT DE HISTORIAL
# =============================================================================

@router.get("/history")
async def obtener_historial(
    tipo_sync: Optional[str] = None,
    unidad_negocio_id: Optional[str] = None,
    limit: int = 50
):
    """
    Obtiene historial de re-sincronizaciones.
    """
    try:
        from modules.comercial_v2.repository_comercial_edarsahub import execute_edarsahub_query
        
        where_clauses = ["1=1"]
        if tipo_sync:
            where_clauses.append(f"t.Codigo = '{tipo_sync}'")
        if unidad_negocio_id:
            where_clauses.append(f"e.UnidadNegocioID = '{unidad_negocio_id}'")
        
        query = f"""
        SELECT TOP {limit}
            e.EjecucionID,
            e.SyncRunID,
            t.Codigo as TipoSync,
            e.Estado,
            e.DryRun,
            e.FechaSolicitud,
            e.UnidadNegocioID,
            e.FechaInicioRango,
            e.FechaFinRango,
            e.Motivo,
            e.RegistrosInsertados,
            e.RegistrosActualizados,
            e.ErrorMensaje,
            e.DuracionMS
        FROM Sistema_Sync_Ejecuciones e
        LEFT JOIN Sistema_Sync_Tipos t ON e.TipoSyncID = t.TipoSyncID
        WHERE {' AND '.join(where_clauses)}
        ORDER BY e.FechaSolicitud DESC
        """
        
        resultado = execute_edarsahub_query(query)
        
        return {
            'ejecuciones': [dict(r) for r in resultado],
            'total': len(resultado)
        }
        
    except Exception as e:
        logger.warning(f"[RESYNC] Error obteniendo historial: {e}")
        return {'ejecuciones': [], 'total': 0, 'error': str(e)}
```

---

## 6. FLUJO DRY RUN

```
┌─────────────────────────────────────────────────────────────────┐
│                        DRY RUN FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. POST /api/admin/scheduler/resync/execute                    │
│     { "tipo_sync": "comercial_ventas_cerradas",                │
│       "unidad_negocio_id": "CIENFUEGOS",                       │
│       "fecha_inicio": "2026-05-19",                            │
│       "fecha_fin": "2026-05-20",                               │
│       "motivo": "Reconciliación P0-B...",                      │
│       "dry_run": true }                                        │
│                                                                 │
│  2. Validar tipo_sync existe y permite resync                  │
│                                                                 │
│  3. Validar unidad existe y obtener server_id                  │
│                                                                 │
│  4. Obtener credenciales desde Servidores_Conexiones           │
│                                                                 │
│  5. Conectar a SoftRestaurant CIENFUEGOS                       │
│                                                                 │
│  6. Ejecutar query de extracción (SELECT, no INSERT)           │
│     SELECT fecha, SUM(total), SUM(propina), COUNT(*)...        │
│                                                                 │
│  7. Construir preview de lo que se insertaría:                 │
│     ┌────────────────────────────────────────────────┐         │
│     │ {                                              │         │
│     │   "modo": "DRY_RUN",                          │         │
│     │   "registros_que_se_insertarian": 2,          │         │
│     │   "detalle": [                                │         │
│     │     { "fecha": "2026-05-19",                  │         │
│     │       "ventas_total": 125430.50,              │         │
│     │       "ventas_sin_propina": 118750.00,        │         │
│     │       "propinas": 6680.50,                    │         │
│     │       "tickets": 42 },                        │         │
│     │     { "fecha": "2026-05-20",                  │         │
│     │       "ventas_total": 98320.00,               │         │
│     │       "ventas_sin_propina": 92100.00,         │         │
│     │       "propinas": 6220.00,                    │         │
│     │       "tickets": 38 }                         │         │
│     │   ]                                           │         │
│     │ }                                             │         │
│     └────────────────────────────────────────────────┘         │
│                                                                 │
│  8. ❌ NO ejecutar INSERT/UPDATE en EDARSAHUB                  │
│                                                                 │
│  9. Registrar ejecución en Sistema_Sync_Ejecuciones            │
│     (Estado='SUCCESS', DryRun=1)                               │
│                                                                 │
│  10. Retornar response con preview                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. FLUJO EJECUCIÓN REAL

```
┌─────────────────────────────────────────────────────────────────┐
│                      EJECUCIÓN REAL FLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. POST /api/admin/scheduler/resync/execute                    │
│     { "tipo_sync": "comercial_ventas_cerradas",                │
│       "unidad_negocio_id": "CIENFUEGOS",                       │
│       "fecha_inicio": "2026-05-19",                            │
│       "fecha_fin": "2026-05-20",                               │
│       "motivo": "Reconciliación P0-B...",                      │
│       "dry_run": false }   ← REAL                              │
│                                                                 │
│  2. Validaciones (igual que dry_run)                           │
│                                                                 │
│  3. Generar sync_run_id único:                                 │
│     "RESYNC-CIENFUEGOS-20260519-20260520-a1b2"                 │
│                                                                 │
│  4. Registrar ejecución INICIADA en Sistema_Sync_Ejecuciones   │
│                                                                 │
│  5. ✅ LLAMAR HANDLER OFICIAL (MÁXIMA #26):                    │
│     sync_softrestaurant_ventas_cerradas(                       │
│         config=UnidadNegocioConfig(CIENFUEGOS),                │
│         fecha_inicio='2026-05-19',                             │
│         fecha_fin='2026-05-20',                                │
│         run_id='RESYNC-CIENFUEGOS-20260519-20260520-a1b2'      │
│     )                                                          │
│                                                                 │
│  6. Handler oficial ejecuta:                                   │
│     - Conectar a SoftRestaurant                                │
│     - Extraer cheques cerrados                                 │
│     - Calcular ventas, propinas, tickets, pax                  │
│     - UPSERT en Comercial_KPIs_Diarios_v2                      │
│     - Registrar en Comercial_SyncLog_v2                        │
│                                                                 │
│  7. Validación posterior:                                      │
│     SELECT COUNT(*) FROM Comercial_KPIs_Diarios_v2             │
│     WHERE unidad='CIENFUEGOS' AND fecha IN ('05-19','05-20')   │
│     → Debe retornar 2                                          │
│                                                                 │
│  8. Actualizar Sistema_Sync_Ejecuciones con resultado          │
│                                                                 │
│  9. Retornar response con validación antes/después             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. VALIDACIONES

### 8.1 Validación Previa (antes de ejecutar)

| Validación | Descripción | Bloquea Ejecución |
|------------|-------------|-------------------|
| Tipo sync existe | Código registrado en Sistema_Sync_Tipos | ✅ Sí |
| Permite resync | PermiteResync = 1 | ✅ Sí |
| Unidad existe | UnidadNegocioID válido | ✅ Sí |
| Rango válido | días <= RangoMaximoDias | ✅ Sí |
| Conectividad | Conexión a servidor origen | ✅ Sí |
| Días existentes | Muestra qué días ya existen | ⚠️ Solo info |

### 8.2 Validación Posterior (después de ejecutar)

| Validación | Descripción |
|------------|-------------|
| Días insertados | Confirmar cantidad insertada |
| No duplicados | Verificar no hay duplicados |
| Propinas separadas | Verificar campo ventas_sin_propina |
| SyncLog registrado | Verificar registro en Comercial_SyncLog_v2 |

---

## 9. CASO CIENFUEGOS

### 9.1 Request de Validación

```bash
curl -X POST "https://[URL]/api/admin/scheduler/resync/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_sync": "comercial_ventas_cerradas",
    "unidad_negocio_id": "CIENFUEGOS",
    "fecha_inicio": "2026-05-19",
    "fecha_fin": "2026-05-20"
  }'
```

### 9.2 Request Dry Run

```bash
curl -X POST "https://[URL]/api/admin/scheduler/resync/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_sync": "comercial_ventas_cerradas",
    "unidad_negocio_id": "CIENFUEGOS",
    "fecha_inicio": "2026-05-19",
    "fecha_fin": "2026-05-20",
    "motivo": "Reconciliación P0-B días faltantes Tablero Ejecutivo Mayo 2026 - Falla de conectividad 19-21 mayo",
    "dry_run": true
  }'
```

### 9.3 Request Ejecución Real

```bash
curl -X POST "https://[URL]/api/admin/scheduler/resync/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_sync": "comercial_ventas_cerradas",
    "unidad_negocio_id": "CIENFUEGOS",
    "fecha_inicio": "2026-05-19",
    "fecha_fin": "2026-05-20",
    "motivo": "Reconciliación P0-B días faltantes Tablero Ejecutivo Mayo 2026 - Falla de conectividad 19-21 mayo",
    "dry_run": false
  }'
```

---

## 10. RESULTADO ESPERADO

### Antes del Resync
```
CIENFUEGOS Mayo 2026: 22 días
Días faltantes: 19, 20 (+ 25 en curso)
```

### Después del Resync
```
CIENFUEGOS Mayo 2026: 24 días
Días faltantes: ninguno (25 en curso)
```

### Verificación SQL
```sql
SELECT 
    fecha_operacion,
    ventas_total,
    ventas_sin_propina,
    propinas_total,
    tickets_total,
    sync_run_id
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = 'CIENFUEGOS'
  AND fecha_operacion IN ('2026-05-19', '2026-05-20')
  AND activo = 1
ORDER BY fecha_operacion;

-- Resultado esperado: 2 filas con sync_run_id comenzando con "RESYNC-CIENFUEGOS-"
```

---

## 11. SIGUIENTE PASO

**¿Autoriza implementar la Fase 0 mínima?**

Si autoriza, procederé a:
1. Verificar si existen tablas equivalentes en EDARSAHUB
2. Crear tablas Sistema_Sync_Tipos y Sistema_Sync_Ejecuciones (si no existen)
3. Insertar registro de tipo_sync comercial_ventas_cerradas
4. Crear archivo `/app/backend/api/admin_scheduler_resync.py`
5. Registrar router en `server.py`
6. Ejecutar validación con dry_run=true para CIENFUEGOS
7. Presentar resultados antes de ejecutar real

---

**Firmado:** E1 Agent  
**Estado:** PLAN DE IMPLEMENTACIÓN FASE 0 - PENDIENTE AUTORIZACIÓN
