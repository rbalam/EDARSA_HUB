# PLAN TÉCNICO DEFINITIVO
# Finanzas Fase 2: Control de Ingresos / Cortes de Caja
# Migración y Sincronización hacia EDARSAHUB

**Versión:** 1.0  
**Fecha:** 30 de Abril de 2026  
**Autor:** E1 Agent - Arquitecto de Software  
**Status:** DISEÑO COMPLETO - PENDIENTE AUTORIZACIÓN PARA EJECUCIÓN

---

## 1. RESUMEN EJECUTIVO

Este documento presenta el plan técnico definitivo para migrar y sincronizar los datos reales de Control de Ingresos / Cortes de Caja desde los sistemas origen (SoftRestaurant y MPRO) hacia EDARSAHUB SQL, reemplazando los 70 registros demo actuales.

### Alcance
- **5 Unidades de Negocio:** 130° QRO, 130° MÉRIDA, ORIGEN, CIENFUEGOS, LA ESTELAR
- **2 Sistemas Origen:** SoftRestaurant (3 unidades), MPRO (2 unidades)
- **Histórico:** Últimos 12 meses
- **Sincronización:** Incremental cada 15 minutos

### Arquitectura Objetivo
```
SoftRestaurant ─────┐
(turnos, movtoscaja) │
                     │      ┌─────────────────┐      ┌─────────────────┐
                     ├─────►│  SINCRONIZADOR  │─────►│    EDARSAHUB    │
                     │      │   (Job/Script)  │      │ Finanzas_Cortes │
MPRO ───────────────┘      └─────────────────┘      └────────┬────────┘
(Comanda_Corte,                                              │
 Declaracion)                                                ▼
                                                    ┌─────────────────┐
                                                    │    DASHBOARD    │
                                                    │  Control Ingre. │
                                                    └─────────────────┘
```

---

## 2. ESTADO ACTUAL

### 2.1 Datos Demo en EDARSAHUB

| Campo | Valor Actual | Problema |
|-------|--------------|----------|
| Registros | 70 | Son DEMO |
| FechaAlta | 2026-04-13 (todos) | Creados en lote |
| SucursalID | Enteros 1-5 | No son UUIDs reales |
| UnidadNegocioID | NULL | Sin trazabilidad |
| Rango fechas | 13 días | Insuficiente |
| Cobertura real | **0%** | Sin datos de origen |

### 2.2 Datos Reales en Sistemas Origen

| Sistema | Tabla | Registros | Campos Clave | Cobertura |
|---------|-------|-----------|--------------|-----------|
| SoftRestaurant | `turnos` | 4,992 | efectivo, tarjeta, cajero | Completa |
| SoftRestaurant | `movtoscaja` | 23,387 | Desglose movimientos | Completa |
| MPRO | `Comanda_Corte` | 4,427 | Folio, importe, sucursal | Completa |
| MPRO | `Comanda_Corte_Declaracion` | ~8,000 | Desglose por forma pago | Completa |

---

## 3. CONFIRMACIÓN DE DATOS DEMO

### 3.1 Evidencia de Datos Demo

```sql
-- Los 70 registros tienen FechaAlta idéntica
SELECT DISTINCT FechaAlta FROM Finanzas_CortesCaja
-- Resultado: 2026-04-13T00:10:40 (todos)

-- SucursalID usa enteros simples, no UUIDs
SELECT DISTINCT SucursalID FROM Finanzas_CortesCaja
-- Resultado: 1, 2, 3, 4, 5

-- No hay UnidadNegocioID
SELECT COUNT(*) FROM Finanzas_CortesCaja WHERE UnidadNegocioID IS NOT NULL
-- Resultado: 0
```

### 3.2 Archivo con Datos Demo Hardcodeados

**Archivo:** `/app/backend/modules/finanzas/ingresos.py`  
**Líneas:** 171-179

```python
def generar_cortes_caja_demo():
    sucursales = [
        {"id": 1, "nombre": "130° QUERETARO"},
        {"id": 2, "nombre": "ORIGEN"},
        {"id": 3, "nombre": "130° TULUM"},     # ❌ No existe
        {"id": 4, "nombre": "CIEN FUEGOS"},
        {"id": 5, "nombre": "XCANATUN"},       # ❌ No existe
    ]
```

**Acción propuesta:** Reemplazar por lectura desde EDARSAHUB (ver sección 14).

---

## 4. ARQUITECTURA OBJETIVO

### 4.1 Principios

1. **EDARSAHUB es fuente de verdad** para el dashboard
2. **SoftRestaurant/MPRO son fuentes de extracción**, no dependencia en vivo
3. **MongoDB NO es fuente principal** - solo cache/logs
4. **Sincronización idempotente** - sin duplicados
5. **Tolerancia a fallos** - si origen cae, dashboard sigue con datos sincronizados

### 4.2 Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FLUJO DE SINCRONIZACIÓN                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PASO 1: Determinar Unidades a Sincronizar                          │
│  ┌────────────────────────────────────────────┐                     │
│  │ SELECT * FROM EDARSAHUB.Unidades_Negocio   │                     │
│  │ WHERE activo = 1                           │                     │
│  └────────────────────────────────────────────┘                     │
│                         │                                           │
│                         ▼                                           │
│  PASO 2: Para cada unidad, obtener servidor/conexión                │
│  ┌────────────────────────────────────────────┐                     │
│  │ Unidad → server_id → Servidores_Conexiones │                     │
│  │ Obtener: host, port, database, credentials │                     │
│  └────────────────────────────────────────────┘                     │
│                         │                                           │
│            ┌────────────┴────────────┐                              │
│            │                         │                              │
│            ▼                         ▼                              │
│  ┌──────────────────┐     ┌──────────────────┐                      │
│  │  SoftRestaurant  │     │      MPRO        │                      │
│  │  SELECT turnos   │     │ SELECT Comanda   │                      │
│  │  WHERE cierre >= │     │ _Corte WHERE     │                      │
│  │  @ultima_sync    │     │ Fecha >= @sync   │                      │
│  └────────┬─────────┘     └────────┬─────────┘                      │
│           │                        │                                │
│           └────────────┬───────────┘                                │
│                        ▼                                            │
│  PASO 3: Transformar y cargar                                       │
│  ┌────────────────────────────────────────────┐                     │
│  │ - Mapear campos origen → destino           │                     │
│  │ - Calcular HashOrigen                      │                     │
│  │ - MERGE INTO Finanzas_CortesCaja           │                     │
│  │   WHEN MATCHED AND hash diferente → UPDATE │                     │
│  │   WHEN NOT MATCHED → INSERT                │                     │
│  └────────────────────────────────────────────┘                     │
│                        │                                            │
│                        ▼                                            │
│  PASO 4: Registrar en bitácora                                      │
│  ┌────────────────────────────────────────────┐                     │
│  │ INSERT INTO Finanzas_CortesCaja_SyncLog    │                     │
│  └────────────────────────────────────────────┘                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. DISEÑO DE TABLA DESTINO

### 5.1 Modificaciones a `Finanzas_CortesCaja`

```sql
-- =====================================================
-- SCRIPT: Ampliación de Finanzas_CortesCaja
-- NO EJECUTAR SIN AUTORIZACIÓN
-- =====================================================

-- Agregar columnas para trazabilidad y datos reales
ALTER TABLE Finanzas_CortesCaja ADD
    -- Trazabilidad a EDARSAHUB
    UnidadNegocioID         NVARCHAR(50) NULL,
    UnidadNegocioNombre     NVARCHAR(100) NULL,
    EmpresaID               NVARCHAR(50) NULL,
    ServerID                NVARCHAR(50) NULL,
    
    -- Identificación de origen
    SistemaOrigen           NVARCHAR(20) NULL,          -- 'SoftRestaurant' | 'MPRO'
    BaseDatosOrigen         NVARCHAR(100) NULL,
    TablaOrigen             NVARCHAR(50) NULL,          -- 'turnos' | 'Comanda_Corte'
    
    -- Identificadores únicos del origen
    FolioCorte              NVARCHAR(50) NULL,          -- Cc_Folio o idturno
    IdOrigen                BIGINT NULL,                -- idturnointerno o PK origen
    SucursalOrigenID        NVARCHAR(20) NULL,          -- Sc_Cve_Sucursal
    
    -- Fechas operativas
    FechaApertura           DATETIME2 NULL,
    FechaCierre             DATETIME2 NULL,
    
    -- Identificación de caja/cajero
    CajeroID                NVARCHAR(20) NULL,
    CajeroNombre            NVARCHAR(100) NULL,
    CajaID                  NVARCHAR(50) NULL,
    CajaNombre              NVARCHAR(100) NULL,
    
    -- Montos adicionales
    Propinas                DECIMAL(18,2) DEFAULT 0,
    Retiros                 DECIMAL(18,2) DEFAULT 0,
    FondoInicial            DECIMAL(18,2) DEFAULT 0,
    TotalVenta              DECIMAL(18,2) DEFAULT 0,
    
    -- Integridad y sincronización
    HashOrigen              NVARCHAR(64) NULL,          -- SHA256
    FechaSincronizacion     DATETIME2 NULL,
    FechaUltimaActualizacion DATETIME2 NULL,
    
    -- Control de datos demo
    EsDemo                  BIT DEFAULT 0;              -- 1 = demo, 0 = real

-- Índices para rendimiento
CREATE INDEX IX_CortesCaja_UnidadNegocio 
    ON Finanzas_CortesCaja(UnidadNegocioID, FechaCorte);

CREATE INDEX IX_CortesCaja_Origen 
    ON Finanzas_CortesCaja(SistemaOrigen, IdOrigen);

CREATE INDEX IX_CortesCaja_Hash 
    ON Finanzas_CortesCaja(HashOrigen);

-- Constraint único para evitar duplicados
CREATE UNIQUE INDEX UQ_CortesCaja_Origen 
    ON Finanzas_CortesCaja(SistemaOrigen, ServerID, IdOrigen)
    WHERE IdOrigen IS NOT NULL;
```

### 5.2 Tabla Auxiliar: Detalle de Pagos (Opcional)

```sql
-- =====================================================
-- TABLA: Finanzas_CortesCaja_DetallePagos
-- Para desglose por forma de pago
-- NO EJECUTAR SIN AUTORIZACIÓN
-- =====================================================

CREATE TABLE Finanzas_CortesCaja_DetallePagos (
    DetalleID               BIGINT IDENTITY(1,1) PRIMARY KEY,
    CorteCajaID             BIGINT NOT NULL,            -- FK a Finanzas_CortesCaja
    FormaPago               NVARCHAR(50) NOT NULL,      -- EFECTIVO, TARJETA, etc.
    FormaPagoCodigo         NVARCHAR(10) NULL,          -- Código origen
    Importe                 DECIMAL(18,2) NOT NULL,
    Referencia              NVARCHAR(100) NULL,
    
    -- Trazabilidad
    SistemaOrigen           NVARCHAR(20) NULL,
    IdOrigen                BIGINT NULL,
    HashOrigen              NVARCHAR(64) NULL,
    
    -- Control
    FechaAlta               DATETIME2 DEFAULT GETDATE(),
    Activo                  BIT DEFAULT 1,
    
    CONSTRAINT FK_DetallePagos_Corte 
        FOREIGN KEY (CorteCajaID) 
        REFERENCES Finanzas_CortesCaja(CorteCajaID)
);

CREATE INDEX IX_DetallePagos_Corte 
    ON Finanzas_CortesCaja_DetallePagos(CorteCajaID);
```

### 5.3 Tabla de Bitácora de Sincronización

```sql
-- =====================================================
-- TABLA: Finanzas_CortesCaja_SyncLog
-- Bitácora de sincronizaciones
-- NO EJECUTAR SIN AUTORIZACIÓN
-- =====================================================

CREATE TABLE Finanzas_CortesCaja_SyncLog (
    LogID                   BIGINT IDENTITY(1,1) PRIMARY KEY,
    FechaInicio             DATETIME2 NOT NULL,
    FechaFin                DATETIME2 NULL,
    
    -- Alcance
    UnidadNegocioID         NVARCHAR(50) NULL,          -- NULL = todas
    ServerID                NVARCHAR(50) NULL,
    SistemaOrigen           NVARCHAR(20) NULL,
    FechaDesde              DATE NULL,
    FechaHasta              DATE NULL,
    
    -- Resultados
    RegistrosLeidos         INT DEFAULT 0,
    RegistrosInsertados     INT DEFAULT 0,
    RegistrosActualizados   INT DEFAULT 0,
    RegistrosOmitidos       INT DEFAULT 0,
    RegistrosError          INT DEFAULT 0,
    
    -- Estado
    Estatus                 NVARCHAR(20) DEFAULT 'EN_PROCESO',  -- EN_PROCESO, COMPLETADO, ERROR, PARCIAL
    ErrorMensaje            NVARCHAR(MAX) NULL,
    DuracionSegundos        INT NULL,
    
    -- Usuario/Proceso
    UsuarioEjecucion        NVARCHAR(50) NULL,
    TipoEjecucion           NVARCHAR(20) NULL           -- MANUAL, SCHEDULER, HISTORICO
);
```

---

## 6. MAPEO DE CAMPOS

### 6.1 SoftRestaurant (`turnos`) → `Finanzas_CortesCaja`

| Campo Origen | Tipo | Campo Destino | Transformación |
|--------------|------|---------------|----------------|
| `idturnointerno` | bigint | `IdOrigen` | Directo |
| `idturno` | bigint | `FolioCorte` | CAST a VARCHAR |
| `apertura` | datetime | `FechaApertura` | Directo |
| `cierre` | datetime | `FechaCierre` | Directo |
| CAST(cierre AS DATE) | date | `FechaCorte` | Extraer fecha |
| `idestacion` | varchar | `CajaID`, `CajaNombre` | Directo |
| `cajero` | varchar | `CajeroID`, `CajeroNombre` | Directo |
| `efectivo` | money | `TotalEfectivo` | CAST a DECIMAL |
| `tarjeta` | money | `TotalTarjetaDebito` | CAST (ver nota) |
| `vales` | money | `TotalVales` | CAST a DECIMAL |
| `credito` | money | `TotalTarjetaCredito` | CAST (ver nota) |
| `fondo` | money | `FondoInicial` | CAST a DECIMAL |
| `idempresa` | varchar | (lookup) | Para filtros |
| - | - | `UnidadNegocioID` | Lookup por server_id |
| - | - | `SistemaOrigen` | 'SoftRestaurant' |
| - | - | `TablaOrigen` | 'turnos' |

**Nota:** SoftRestaurant no distingue débito/crédito en `turnos`. Se puede obtener de `movtoscaja` si se requiere desglose.

### 6.2 MPRO (`Comanda_Corte`) → `Finanzas_CortesCaja`

| Campo Origen | Tipo | Campo Destino | Transformación |
|--------------|------|---------------|----------------|
| `Cc_Folio` | nvarchar | `FolioCorte` | Directo |
| `Cc_Fecha` | datetime | `FechaCorte` | CAST a DATE |
| `Cc_Turno` | char | `TurnoID` | CAST a INT |
| `Cc_Caja` | nvarchar | `CajaID` | Directo |
| `Cc_Cajero` | nvarchar | `CajeroID` | Directo (lookup nombre) |
| `Cc_Importe_Pago` | decimal | `TotalEfectivo` | Consolidado |
| `Cc_Importe_Venta` | decimal | `TotalVenta` | Directo |
| `Cc_Venta_Contado` | decimal | - | Para análisis |
| `Cc_Venta_Credito` | decimal | `TotalTarjetaCredito` | Mapeo |
| `Cc_Importe_Retirado` | decimal | `Retiros` | Directo |
| `Sc_Cve_Sucursal` | nvarchar | `SucursalOrigenID` | Directo |
| `Fecha_Alta` | datetime | `FechaAlta` | Directo |
| `Es_Cve_Estado` | nvarchar | (filtro) | Solo 'A' o 'AB' |
| - | - | `UnidadNegocioID` | Lookup por sucursal |
| - | - | `SistemaOrigen` | 'MPRO' |
| - | - | `TablaOrigen` | 'Comanda_Corte' |

### 6.3 Mapeo Sucursal MPRO → Unidad de Negocio

| Sc_Cve_Sucursal | Unidad de Negocio | UnidadNegocioID |
|-----------------|-------------------|-----------------|
| `0021` | 130° QUERÉTARO | `9bc05ced-6b2b-4a0a-aa90-ce649b78e12c` |
| `0023` | ORIGEN | `23ca0b76-6580-4874-ba9b-672b122ca197` |

---

## 7. LLAVES ÚNICAS Y ANTI-DUPLICADOS

### 7.1 Llave Única - SoftRestaurant

```
UNIQUE (SistemaOrigen, ServerID, idturnointerno)
```

**Justificación:**
- `idturnointerno` es PK en tabla `turnos`
- `ServerID` diferencia entre 130° MÉRIDA, CIENFUEGOS, LA ESTELAR
- `SistemaOrigen` = 'SoftRestaurant'

### 7.2 Llave Única - MPRO

```
UNIQUE (SistemaOrigen, ServerID, Cc_Folio)
```

**Justificación:**
- `Cc_Folio` es único por sucursal (ej: "21-0001678", "SB-0001989")
- `ServerID` identifica el servidor MPRO
- `SistemaOrigen` = 'MPRO'

### 7.3 Cálculo de HashOrigen

```python
def calcular_hash_origen(registro):
    """Genera SHA256 para validar integridad"""
    componentes = [
        str(registro['SistemaOrigen']),
        str(registro['ServerID']),
        str(registro['FolioCorte']),
        str(registro['FechaCorte']),
        str(registro['CajaID'] or ''),
        str(registro['CajeroID'] or ''),
        str(registro['TotalEfectivo'] or 0),
        str(registro['TotalTarjetaDebito'] or 0),
        str(registro['TotalTarjetaCredito'] or 0)
    ]
    cadena = '|'.join(componentes)
    return hashlib.sha256(cadena.encode()).hexdigest()
```

---

## 8. ESTRATEGIA DE MIGRACIÓN HISTÓRICA

### 8.1 Parámetros

| Parámetro | Valor Propuesto |
|-----------|-----------------|
| Rango histórico | Últimos 12 meses |
| Fecha inicio | 2025-05-01 |
| Fecha fin | 2026-04-30 (hoy) |
| Batch size | 500 registros |
| Timeout por unidad | 5 minutos |

### 8.2 Orden de Ejecución

1. **Marcar datos demo:** `UPDATE SET EsDemo = 1 WHERE FechaAlta = '2026-04-13'`
2. **SoftRestaurant - 130° MÉRIDA** (más datos recientes)
3. **SoftRestaurant - CIENFUEGOS**
4. **SoftRestaurant - LA ESTELAR**
5. **MPRO - 130° QRO** (Sucursal 0021)
6. **MPRO - ORIGEN** (Sucursal 0023)
7. **Validar totales**
8. **Archivar datos demo** (opcional)

### 8.3 Query de Migración - SoftRestaurant

```sql
-- Extraer turnos cerrados de los últimos 12 meses
SELECT 
    idturnointerno AS IdOrigen,
    CAST(idturno AS NVARCHAR(50)) AS FolioCorte,
    CAST(cierre AS DATE) AS FechaCorte,
    apertura AS FechaApertura,
    cierre AS FechaCierre,
    idestacion AS CajaID,
    idestacion AS CajaNombre,
    cajero AS CajeroID,
    cajero AS CajeroNombre,
    CAST(efectivo AS DECIMAL(18,2)) AS TotalEfectivo,
    CAST(tarjeta AS DECIMAL(18,2)) AS TotalTarjetaDebito,
    CAST(vales AS DECIMAL(18,2)) AS TotalVales,
    CAST(credito AS DECIMAL(18,2)) AS TotalTarjetaCredito,
    CAST(fondo AS DECIMAL(18,2)) AS FondoInicial,
    idempresa
FROM turnos
WHERE cierre IS NOT NULL
  AND cierre >= DATEADD(MONTH, -12, GETDATE())
  AND cierre < GETDATE()
ORDER BY cierre ASC
```

### 8.4 Query de Migración - MPRO

```sql
-- Extraer cortes activos de los últimos 12 meses
SELECT 
    Cc_Folio AS FolioCorte,
    Cc_Fecha AS FechaCorte,
    Cc_Turno AS TurnoID,
    Cc_Caja AS CajaID,
    Cc_Cajero AS CajeroID,
    CAST(Cc_Importe_Pago AS DECIMAL(18,2)) AS TotalEfectivo,
    CAST(Cc_Importe_Venta AS DECIMAL(18,2)) AS TotalVenta,
    CAST(Cc_Venta_Credito AS DECIMAL(18,2)) AS TotalTarjetaCredito,
    CAST(Cc_Importe_Retirado AS DECIMAL(18,2)) AS Retiros,
    Sc_Cve_Sucursal AS SucursalOrigenID,
    Fecha_Alta,
    Es_Cve_Estado
FROM Comanda_Corte
WHERE Es_Cve_Estado IN ('A', 'AB')
  AND Cc_Fecha >= DATEADD(MONTH, -12, GETDATE())
  AND Cc_Fecha < GETDATE()
ORDER BY Cc_Fecha ASC
```

---

## 9. ESTRATEGIA DE SINCRONIZACIÓN INCREMENTAL

### 9.1 Parámetros

| Parámetro | Valor |
|-----------|-------|
| Frecuencia | Cada 15 minutos |
| Modo | Incremental por fecha |
| Ventana | Últimas 24 horas (para capturas tardías) |
| Reintentos | 3 intentos con backoff |

### 9.2 Lógica de Sincronización

```python
async def sincronizar_unidad(unidad_id, ultima_sync):
    """
    Sincroniza cortes de una unidad desde última sync
    """
    # 1. Obtener configuración de EDARSAHUB
    unidad = await get_unidad_negocio(unidad_id)
    servidor = await get_servidor(unidad['server_id'])
    
    # 2. Determinar fecha desde
    fecha_desde = ultima_sync - timedelta(hours=24)  # Ventana segura
    
    # 3. Extraer de origen según system_type
    if unidad['system_type'] == 'SoftRestaurant':
        registros = await extraer_turnos_softrestaurant(servidor, fecha_desde)
    elif unidad['system_type'] == 'MPRO':
        registros = await extraer_cortes_mpro(servidor, fecha_desde, unidad)
    
    # 4. Transformar y calcular hash
    for reg in registros:
        reg['UnidadNegocioID'] = unidad_id
        reg['HashOrigen'] = calcular_hash_origen(reg)
    
    # 5. MERGE a EDARSAHUB
    resultado = await merge_cortes_edarsahub(registros)
    
    # 6. Registrar en bitácora
    await registrar_sync_log(unidad_id, resultado)
    
    return resultado
```

### 9.3 Sentencia MERGE

```sql
MERGE INTO Finanzas_CortesCaja AS target
USING @RegistrosOrigen AS source
ON target.SistemaOrigen = source.SistemaOrigen
   AND target.ServerID = source.ServerID
   AND target.IdOrigen = source.IdOrigen

WHEN MATCHED AND target.HashOrigen <> source.HashOrigen THEN
    UPDATE SET
        FechaCorte = source.FechaCorte,
        TotalEfectivo = source.TotalEfectivo,
        TotalTarjetaDebito = source.TotalTarjetaDebito,
        TotalTarjetaCredito = source.TotalTarjetaCredito,
        HashOrigen = source.HashOrigen,
        FechaUltimaActualizacion = GETDATE(),
        FechaSincronizacion = GETDATE()

WHEN NOT MATCHED THEN
    INSERT (UnidadNegocioID, SistemaOrigen, ServerID, IdOrigen, FolioCorte,
            FechaCorte, TotalEfectivo, TotalTarjetaDebito, TotalTarjetaCredito,
            HashOrigen, FechaAlta, FechaSincronizacion, EsDemo)
    VALUES (source.UnidadNegocioID, source.SistemaOrigen, source.ServerID,
            source.IdOrigen, source.FolioCorte, source.FechaCorte,
            source.TotalEfectivo, source.TotalTarjetaDebito, source.TotalTarjetaCredito,
            source.HashOrigen, GETDATE(), GETDATE(), 0);
```

---

## 10. MANEJO DE ERRORES

### 10.1 Estrategia de Tolerancia a Fallos

```python
async def sincronizar_todas_unidades():
    """Si una unidad falla, las demás continúan"""
    unidades = await get_unidades_activas()
    resultados = []
    
    for unidad in unidades:
        try:
            resultado = await sincronizar_unidad(unidad['id'])
            resultados.append({'unidad': unidad['nombre'], 'status': 'OK', 'resultado': resultado})
        except ConnectionError as e:
            # Servidor no disponible - registrar y continuar
            await registrar_error(unidad['id'], f"Conexión fallida: {e}")
            resultados.append({'unidad': unidad['nombre'], 'status': 'ERROR_CONEXION'})
        except TimeoutError as e:
            # Timeout - registrar y continuar
            await registrar_error(unidad['id'], f"Timeout: {e}")
            resultados.append({'unidad': unidad['nombre'], 'status': 'ERROR_TIMEOUT'})
        except Exception as e:
            # Error inesperado - registrar y continuar
            await registrar_error(unidad['id'], f"Error: {e}")
            resultados.append({'unidad': unidad['nombre'], 'status': 'ERROR'})
    
    return resultados
```

### 10.2 Reintentos con Backoff

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((ConnectionError, TimeoutError))
)
async def conectar_origen(servidor):
    """Conexión con reintentos automáticos"""
    return await create_connection(servidor)
```

---

## 11. ESTRATEGIA PARA DATOS DEMO

### 11.1 Opción Recomendada: Marcar como Demo

```sql
-- Paso 1: Marcar registros existentes como demo
UPDATE Finanzas_CortesCaja
SET EsDemo = 1
WHERE FechaAlta = '2026-04-13T00:10:40'
  AND UnidadNegocioID IS NULL;

-- Paso 2: El dashboard excluye demos
SELECT * FROM Finanzas_CortesCaja
WHERE EsDemo = 0 OR EsDemo IS NULL;
```

### 11.2 Opción Alternativa: Respaldo y Limpieza

```sql
-- Solo después de migración exitosa y autorización explícita

-- Paso 1: Respaldar
SELECT * INTO Finanzas_CortesCaja_Demo_Backup
FROM Finanzas_CortesCaja
WHERE EsDemo = 1;

-- Paso 2: Eliminar demos (SOLO CON AUTORIZACIÓN)
DELETE FROM Finanzas_CortesCaja
WHERE EsDemo = 1;
```

---

## 12. VALIDACIÓN POST-SINCRONIZACIÓN

### 12.1 Queries de Validación

```sql
-- A. Totales por unidad
SELECT 
    UnidadNegocioNombre,
    COUNT(*) AS Registros,
    MIN(FechaCorte) AS FechaMin,
    MAX(FechaCorte) AS FechaMax,
    SUM(TotalEfectivo + TotalTarjetaDebito + TotalTarjetaCredito) AS TotalIngresos
FROM Finanzas_CortesCaja
WHERE EsDemo = 0
GROUP BY UnidadNegocioNombre;

-- B. Comparar con origen (SoftRestaurant)
-- Ejecutar en origen y comparar con EDARSAHUB

-- C. Detectar duplicados
SELECT SistemaOrigen, ServerID, IdOrigen, COUNT(*) as duplicados
FROM Finanzas_CortesCaja
WHERE EsDemo = 0
GROUP BY SistemaOrigen, ServerID, IdOrigen
HAVING COUNT(*) > 1;

-- D. Verificar integridad de hash
SELECT COUNT(*) AS sin_hash
FROM Finanzas_CortesCaja
WHERE HashOrigen IS NULL AND EsDemo = 0;
```

---

## 13. PLAN DE PRUEBAS

### 13.1 Pruebas por Unidad

| # | Unidad | Sistema | Prueba | Criterio Aceptación |
|---|--------|---------|--------|---------------------|
| 1 | 130° QRO | MPRO | Migración histórica | Registros = origen ±1% |
| 2 | 130° MÉRIDA | SoftRest | Migración histórica | Registros = origen ±1% |
| 3 | ORIGEN | MPRO | Migración histórica | Registros = origen ±1% |
| 4 | CIENFUEGOS | SoftRest | Migración histórica | Registros = origen ±1% |
| 5 | LA ESTELAR | SoftRest | Migración histórica | Registros = origen ±1% |
| 6 | TODAS | - | Sync incremental | Sin duplicados |
| 7 | - | - | Tolerancia fallos | Dashboard no en ceros |
| 8 | - | - | RBAC | Solo unidades autorizadas |

### 13.2 Métricas Esperadas (Estimadas)

| Unidad | Registros Origen (12m) | Total Importe Estimado |
|--------|------------------------|------------------------|
| 130° MÉRIDA | ~360 turnos | ~$60M |
| CIENFUEGOS | ~350 turnos | ~$55M |
| LA ESTELAR | ~300 turnos | ~$45M |
| 130° QRO | ~400 cortes | ~$70M |
| ORIGEN | ~350 cortes | ~$50M |
| **TOTAL** | **~1,760** | **~$280M** |

---

## 14. CAMBIOS REQUERIDOS EN BACKEND

### 14.1 Archivos a Modificar

| Archivo | Cambio | Riesgo |
|---------|--------|--------|
| `/app/backend/modules/finanzas/ingresos.py` | Reemplazar demo por EDARSAHUB | Bajo |
| Nuevo: `repository_ingresos_edarsahub.py` | Repositorio para leer de EDARSAHUB | Ninguno |
| Nuevo: `sync_cortes_caja.py` | Proceso de sincronización | Ninguno |

### 14.2 Código Propuesto - Endpoint

```python
# /app/backend/modules/finanzas/ingresos.py (modificación)

@router.get("/cortes-caja")
async def get_cortes_caja(
    unidad_id: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene cortes de caja desde EDARSAHUB.
    NO consulta en vivo a SoftRestaurant/MPRO.
    """
    # Validar RBAC
    unidades_permitidas = await get_user_unidades_permitidas(current_user)
    
    if unidad_id and unidad_id not in unidades_permitidas:
        raise HTTPException(403, "Sin acceso a esta unidad")
    
    # Consultar EDARSAHUB
    cortes = await repository_ingresos.get_cortes_caja(
        unidad_id=unidad_id,
        unidades_permitidas=unidades_permitidas,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        excluir_demo=True
    )
    
    if not cortes:
        return {
            "mensaje": "Sin cortes sincronizados para el rango seleccionado",
            "data": [],
            "total": 0
        }
    
    return cortes
```

---

## 15. CAMBIOS REQUERIDOS EN FRONTEND

### 15.1 Componentes Afectados

| Componente | Cambio | Impacto |
|------------|--------|---------|
| `FinanzasControlIngresos.jsx` | Usar endpoint real | Bajo |
| Filtro Unidad de Negocio | Sin cambio | Ninguno |
| Tabs Finanzas | Sin cambio | Ninguno |

### 15.2 Manejo de "Sin Datos"

```jsx
// En lugar de mostrar ceros o demo
{cortes.length === 0 ? (
  <Alert variant="info">
    Sin cortes sincronizados para el rango seleccionado.
    Los datos se actualizan cada 15 minutos.
  </Alert>
) : (
  <CortesTable data={cortes} />
)}
```

---

## 16. POSIBLES AFECTACIONES Y AUTORIZACIÓN REQUERIDA

### 16.1 Análisis de Impacto

| Componente | ¿Se modifica? | Riesgo | Mitigación |
|------------|---------------|--------|------------|
| Tablero Ejecutivo | ❌ NO | Ninguno | No tocar |
| Servidores | ❌ NO | Ninguno | No tocar |
| Operaciones | ❌ NO | Ninguno | No tocar |
| Compras | ❌ NO | Ninguno | No tocar |
| Comercial | ❌ NO | Ninguno | No tocar |
| CxP | ❌ NO | Ninguno | No tocar |
| Menús globales | ❌ NO | Ninguno | No tocar |
| RBAC global | ❌ NO | Ninguno | Reutilizar existente |
| Finanzas_CortesCaja | ✅ SÍ (ALTER) | Bajo | Solo agregar columnas |
| ingresos.py | ✅ SÍ | Bajo | Preservar estructura |

### 16.2 Cambios que Requieren Autorización Adicional

1. **ALTER TABLE en EDARSAHUB** - Requiere autorización de DBA
2. **Creación de tablas nuevas** - Requiere autorización
3. **Job de sincronización** - Requiere autorización para scheduler
4. **Eliminación de datos demo** - Requiere autorización explícita

---

## 17. PLAN DE ROLLBACK

### 17.1 Puntos de Rollback

| Fase | Punto de Rollback |
|------|-------------------|
| Pre-migración | Backup de Finanzas_CortesCaja |
| Alteración tabla | Script para DROP columnas nuevas |
| Migración datos | DELETE WHERE EsDemo = 0 |
| Sync activa | Deshabilitar job, restaurar endpoint demo |

### 17.2 Script de Rollback

```sql
-- ROLLBACK COMPLETO (SOLO EN EMERGENCIA)

-- 1. Eliminar datos migrados
DELETE FROM Finanzas_CortesCaja WHERE EsDemo = 0;

-- 2. Restaurar demos
UPDATE Finanzas_CortesCaja SET EsDemo = 0 WHERE EsDemo = 1;

-- 3. Eliminar columnas nuevas (si se requiere)
ALTER TABLE Finanzas_CortesCaja DROP COLUMN UnidadNegocioID;
-- ... etc
```

---

## 18. ARCHIVOS QUE NO DEBEN TOCARSE

### 18.1 Lista de Archivos Blindados

```
/app/backend/modules/comercial/*           # Comercial
/app/backend/modules/compras/*             # Compras
/app/backend/modules/operaciones/*         # Operaciones
/app/backend/modules/sistema/*             # Sistema
/app/backend/modules/finanzas/cuentas_por_pagar.py  # CxP ya corregido
/app/backend/modules/finanzas/repository_softrestaurant.py  # CxP
/app/backend/modules/finanzas/repository_mpro.py  # CxP
/app/backend/core/*                        # Core (RBAC, auth, etc.)
/app/frontend/src/components/comercial/*
/app/frontend/src/components/compras/*
/app/frontend/src/components/operaciones/*
/app/frontend/src/pages/Comercial*.js
/app/frontend/src/pages/Compras*.js
/app/frontend/src/pages/Operaciones*.js
/app/frontend/src/components/ui/*          # Componentes compartidos
/app/frontend/src/components/layout/*      # Layout global
```

---

## 19. CRITERIOS DE ACEPTACIÓN

| # | Criterio | Verificación |
|---|----------|--------------|
| 1 | Cubre 5 unidades | ✅ Diseñado |
| 2 | Incluye SoftRestaurant y MPRO | ✅ Diseñado |
| 3 | Sin dependencia en vivo | ✅ Sync a EDARSAHUB |
| 4 | EDARSAHUB es fuente de verdad | ✅ Diseñado |
| 5 | MongoDB no es fuente principal | ✅ No se usa |
| 6 | Maneja datos demo sin mezclar | ✅ Campo EsDemo |
| 7 | Llaves únicas y hash | ✅ Diseñado |
| 8 | Sincronización idempotente | ✅ MERGE |
| 9 | Bitácora de sync | ✅ Tabla SyncLog |
| 10 | Plan de rollback | ✅ Documentado |
| 11 | No toca módulos blindados | ✅ Verificado |
| 12 | Mantiene filtros/tabs | ✅ Sin cambios |
| 13 | Pide autorización | ✅ Este documento |

---

## 20. SOLICITUD FINAL DE AUTORIZACIÓN

### Para proceder con la ejecución, se requiere autorización explícita para:

1. **[ ] ALTER TABLE** - Agregar columnas a `Finanzas_CortesCaja`
2. **[ ] CREATE TABLE** - Crear `Finanzas_CortesCaja_DetallePagos` (opcional)
3. **[ ] CREATE TABLE** - Crear `Finanzas_CortesCaja_SyncLog`
4. **[ ] MIGRACIÓN HISTÓRICA** - Cargar últimos 12 meses de datos reales
5. **[ ] MARCAR DEMOS** - Establecer `EsDemo = 1` en registros actuales
6. **[ ] CREAR SINCRONIZADOR** - Script/job de sincronización incremental
7. **[ ] MODIFICAR ingresos.py** - Reemplazar demo por EDARSAHUB
8. **[ ] ACTUALIZAR FRONTEND** - Ajustar manejo de "sin datos"

### Confirmación Solicitada

```
¿Autoriza la ejecución del plan técnico?

[ ] SÍ, autorizo todos los puntos
[ ] SÍ, autorizo parcialmente (especificar)
[ ] NO, requiero ajustes (especificar)
```

---

**FIN DEL PLAN TÉCNICO DEFINITIVO**

**Versión:** 1.0  
**Estado:** PENDIENTE AUTORIZACIÓN  
**Próximo paso:** Esperar confirmación para iniciar ejecución
