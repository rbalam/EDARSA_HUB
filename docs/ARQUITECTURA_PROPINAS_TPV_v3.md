# PROPUESTA DE ARQUITECTURA AJUSTADA
# Módulo de Control y Cuadre de Comisión de Propinas TPV

**Versión:** 3.0  
**Fecha:** 15 de Abril de 2026  
**Autor:** Arquitectura EDARSA HUB  
**Estado:** PROPUESTA PARA REVISIÓN  
**Clasificación:** REDISEÑO ARQUITECTÓNICO - MÓDULO FINANCIERO

---

## RESUMEN EJECUTIVO

### Problema Identificado
El módulo actual de Propinas TPV fue implementado usando **MongoDB como almacenamiento principal**. Esto viola los principios arquitectónicos de EDARSA HUB para módulos financieros:

| Aspecto | Implementación Actual | Implementación Correcta |
|---------|----------------------|------------------------|
| Persistencia principal | MongoDB | **SQL Server** |
| Auditoría | Limitada | **Completa en SQL** |
| Consistencia | Eventual | **ACID en SQL** |
| Fuente de verdad | MongoDB | **SQL Server (cerebro)** |
| MongoDB | Almacenamiento | **Solo cache** |

### Propuesta
Rediseñar la capa de persistencia para que:
1. **SQL Server EDARSA HUB** sea la fuente oficial de datos financieros
2. **MongoDB** funcione exclusivamente como cache de lectura para acelerar consultas
3. Mantener compatibilidad con endpoints existentes durante la transición

---

# 1. REDISEÑO DE PERSISTENCIA

## 1.1 Clasificación de Datos

### Datos que DEBEN vivir en SQL Server (Financieros/Auditables):

| Categoría | Datos | Justificación |
|-----------|-------|---------------|
| **Control** | Registro de propinas por corte | Dato financiero oficial |
| **Importes** | Propina detectada, comisión calculada | Auditoría financiera |
| **Tasas** | Porcentaje de comisión aplicado | Trazabilidad de cálculo |
| **Cuadre** | Importe esperado, depositado, contado | Control de caja |
| **Diferencias** | Faltante/Sobrante detectado | Auditoría operativa |
| **Estado** | Estatus del proceso (PENDIENTE, CUADRADO, etc.) | Control de flujo |
| **Usuarios** | Cajera que generó, Admin que cuadró | Responsabilidad |
| **Fechas** | Operación, sincronización, cuadre, pago | Trazabilidad temporal |
| **Historial** | Cambios de estado, ajustes | Auditoría completa |

### Datos que PUEDEN vivir en MongoDB (Cache/Temporales):

| Categoría | Datos | Justificación |
|-----------|-------|---------------|
| **Previews** | Resultados de consultas de prueba | No son oficiales |
| **Agregaciones** | Totales pre-calculados para dashboard | Aceleración de lectura |
| **Esquemas** | Cache de detección de estructura SQL | Evita queries repetidas |
| **Sesión** | Datos de trabajo en progreso | Temporal |

## 1.2 Principio de Prevalencia

```
SI existe_discrepancia(MongoDB, SQL_Server):
    ENTONCES:
        fuente_verdad = SQL_Server
        invalidar_cache(MongoDB)
        recargar_desde_SQL()
```

---

# 2. PROPUESTA DE TABLAS EN SQL SERVER

## 2.1 Modelo de Datos

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SQL SERVER - EDARSA HUB                          │
│                    Base de datos: edarsa_hub                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────┐    ┌─────────────────────────┐        │
│  │  propinas_tpv_config    │    │  propinas_tpv_control   │        │
│  │  (Configuración)        │    │  (Registro principal)   │        │
│  └─────────────────────────┘    └─────────────────────────┘        │
│              │                            │                         │
│              │                            │                         │
│              └──────────┬─────────────────┘                         │
│                         │                                           │
│                         ▼                                           │
│              ┌─────────────────────────┐                           │
│              │  propinas_tpv_historial │                           │
│              │  (Auditoría de cambios) │                           │
│              └─────────────────────────┘                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 2.2 Tabla: `propinas_tpv_control`

### Objetivo
Registro oficial de control y cuadre de propinas TPV por corte de caja.

### Estructura

```sql
CREATE TABLE propinas_tpv_control (
    -- ============================================
    -- IDENTIFICADORES (Llave primaria compuesta)
    -- ============================================
    id                      UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID(),
    server_id               VARCHAR(50)         NOT NULL,
    sucursal_id             VARCHAR(50)         NOT NULL,
    folio_corte             VARCHAR(50)         NOT NULL,
    fecha_corte             DATE                NOT NULL,
    
    -- ============================================
    -- CONTEXTO DEL ORIGEN
    -- ============================================
    server_name             VARCHAR(100)        NOT NULL,
    system_type             VARCHAR(20)         NOT NULL DEFAULT 'SoftRestaurant',
    sucursal_nombre         VARCHAR(100)        NULL,
    empresa_id              VARCHAR(50)         NULL,
    estacion_id             VARCHAR(50)         NULL,
    
    -- ============================================
    -- DATOS OPERATIVOS (Lectura de SoftRestaurant)
    -- ============================================
    propinas_totales_corte  DECIMAL(18,2)       NOT NULL DEFAULT 0,
    propinas_efectivo       DECIMAL(18,2)       NOT NULL DEFAULT 0,
    propinas_tpv            DECIMAL(18,2)       NOT NULL DEFAULT 0,
    ventas_tarjeta          DECIMAL(18,2)       NOT NULL DEFAULT 0,
    ventas_totales          DECIMAL(18,2)       NOT NULL DEFAULT 0,
    
    -- ============================================
    -- ORIGEN DEL DATO
    -- ============================================
    tipo_dato               VARCHAR(20)         NOT NULL DEFAULT 'EXACTO', -- EXACTO, ESTIMADO
    metodo_calculo          VARCHAR(100)        NULL,
    confianza               DECIMAL(3,2)        NOT NULL DEFAULT 1.00,
    query_origen            VARCHAR(500)        NULL,
    
    -- ============================================
    -- CÁLCULOS DE COMISIÓN
    -- ============================================
    config_aplicada_id      UNIQUEIDENTIFIER    NULL,
    porcentaje_comision     DECIMAL(5,4)        NOT NULL DEFAULT 0.0200, -- 2%
    comision_calculada      DECIMAL(18,2)       NOT NULL DEFAULT 0,
    monto_a_pagar_meseros   DECIMAL(18,2)       NOT NULL DEFAULT 0,
    
    -- ============================================
    -- REGISTRO DE PAGO
    -- ============================================
    pago_registrado         BIT                 NOT NULL DEFAULT 0,
    pago_monto              DECIMAL(18,2)       NULL,
    pago_fecha              DATETIME            NULL,
    pago_metodo             VARCHAR(20)         NULL, -- EFECTIVO, TRANSFERENCIA
    pago_usuario_id         VARCHAR(50)         NULL,
    pago_usuario_email      VARCHAR(100)        NULL,
    pago_observaciones      VARCHAR(500)        NULL,
    
    -- ============================================
    -- CUADRE
    -- ============================================
    cuadre_estado           VARCHAR(20)         NOT NULL DEFAULT 'PENDIENTE',
    cuadre_diferencia       DECIMAL(18,2)       NULL,
    cuadre_fecha            DATETIME            NULL,
    cuadre_usuario_id       VARCHAR(50)         NULL,
    cuadre_usuario_email    VARCHAR(100)        NULL,
    cuadre_observaciones    VARCHAR(500)        NULL,
    
    -- ============================================
    -- AUDITORÍA
    -- ============================================
    fecha_sincronizacion    DATETIME            NOT NULL DEFAULT GETDATE(),
    sincronizado_por        VARCHAR(100)        NULL,
    created_at              DATETIME            NOT NULL DEFAULT GETDATE(),
    updated_at              DATETIME            NOT NULL DEFAULT GETDATE(),
    version                 INT                 NOT NULL DEFAULT 1,
    
    -- ============================================
    -- CONSTRAINTS
    -- ============================================
    CONSTRAINT PK_propinas_tpv_control 
        PRIMARY KEY (id),
    
    CONSTRAINT UK_propinas_tpv_corte 
        UNIQUE (server_id, sucursal_id, folio_corte, fecha_corte),
    
    CONSTRAINT CK_propinas_tipo_dato 
        CHECK (tipo_dato IN ('EXACTO', 'ESTIMADO')),
    
    CONSTRAINT CK_propinas_cuadre_estado 
        CHECK (cuadre_estado IN ('PENDIENTE', 'CALCULADO', 'PAGADO', 'CUADRADO', 'DESCUADRE', 'CON_AJUSTE'))
);
```

### Índices

```sql
-- Índice para búsquedas por fecha y estado
CREATE INDEX IX_propinas_fecha_estado 
ON propinas_tpv_control (fecha_corte DESC, cuadre_estado);

-- Índice para búsquedas por servidor
CREATE INDEX IX_propinas_servidor 
ON propinas_tpv_control (server_id, fecha_corte DESC);

-- Índice para búsquedas por estado de cuadre
CREATE INDEX IX_propinas_cuadre 
ON propinas_tpv_control (cuadre_estado, fecha_corte DESC);

-- Índice para auditoría por usuario
CREATE INDEX IX_propinas_usuarios 
ON propinas_tpv_control (pago_usuario_id, cuadre_usuario_id);
```

### Justificación
- **Necesaria:** Es el registro oficial de control de propinas
- **Única:** No existe tabla equivalente en EDARSA HUB
- **Campos:** Cubren todo el ciclo de vida del cuadre de propinas
- **Llaves:** Permiten integración con cualquier sistema origen

---

## 2.3 Tabla: `propinas_tpv_config`

### Objetivo
Configuración jerárquica de parámetros de propinas (tasas, tolerancias, mapeos).

### Estructura

```sql
CREATE TABLE propinas_tpv_config (
    -- ============================================
    -- IDENTIFICADORES
    -- ============================================
    id                      UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID(),
    
    -- ============================================
    -- ALCANCE (Jerarquía: GLOBAL → EMPRESA → SUCURSAL)
    -- ============================================
    alcance_tipo            VARCHAR(20)         NOT NULL DEFAULT 'GLOBAL',
    alcance_server_id       VARCHAR(50)         NULL,
    alcance_empresa_id      VARCHAR(50)         NULL,
    alcance_sucursal_id     VARCHAR(50)         NULL,
    
    -- ============================================
    -- VIGENCIA
    -- ============================================
    vigencia_inicio         DATETIME            NOT NULL DEFAULT GETDATE(),
    vigencia_fin            DATETIME            NULL,
    activa                  BIT                 NOT NULL DEFAULT 1,
    
    -- ============================================
    -- PARÁMETROS
    -- ============================================
    porcentaje_comision     DECIMAL(5,4)        NOT NULL DEFAULT 0.0200,
    tolerancia_descuadre    DECIMAL(18,2)       NOT NULL DEFAULT 5.00,
    dias_para_cuadrar       INT                 NOT NULL DEFAULT 1,
    
    -- ============================================
    -- MAPEO DE CONCEPTOS SOFTRESTAURANT
    -- ============================================
    soft_concepto_propinas  INT                 NOT NULL DEFAULT 9,
    soft_conceptos_tarjeta  VARCHAR(50)         NOT NULL DEFAULT '10,11,12',
    soft_concepto_efectivo  INT                 NOT NULL DEFAULT 2,
    
    -- ============================================
    -- AUDITORÍA
    -- ============================================
    created_at              DATETIME            NOT NULL DEFAULT GETDATE(),
    created_by              VARCHAR(100)        NULL,
    updated_at              DATETIME            NOT NULL DEFAULT GETDATE(),
    updated_by              VARCHAR(100)        NULL,
    motivo_cambio           VARCHAR(500)        NULL,
    
    -- ============================================
    -- CONSTRAINTS
    -- ============================================
    CONSTRAINT PK_propinas_tpv_config 
        PRIMARY KEY (id),
    
    CONSTRAINT CK_config_alcance 
        CHECK (alcance_tipo IN ('GLOBAL', 'EMPRESA', 'SUCURSAL'))
);
```

### Índices

```sql
-- Índice para resolución de configuración por jerarquía
CREATE INDEX IX_config_jerarquia 
ON propinas_tpv_config (alcance_tipo, alcance_server_id, activa);
```

### Justificación
- **Necesaria:** Permite parametrizar tasas por empresa/sucursal
- **Jerárquica:** GLOBAL como fallback, excepciones por sucursal
- **Auditable:** Registro de quién y cuándo cambió parámetros

---

## 2.4 Tabla: `propinas_tpv_historial`

### Objetivo
Registro de auditoría de todos los cambios realizados a los controles de propinas.

### Estructura

```sql
CREATE TABLE propinas_tpv_historial (
    -- ============================================
    -- IDENTIFICADORES
    -- ============================================
    id                      UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID(),
    control_id              UNIQUEIDENTIFIER    NOT NULL,
    
    -- ============================================
    -- DATOS DEL CAMBIO
    -- ============================================
    accion                  VARCHAR(50)         NOT NULL, -- CREACION, ACTUALIZACION, PAGO, CUADRE, AJUSTE
    campo_modificado        VARCHAR(100)        NULL,
    valor_anterior          VARCHAR(500)        NULL,
    valor_nuevo             VARCHAR(500)        NULL,
    
    -- ============================================
    -- CONTEXTO
    -- ============================================
    estado_anterior         VARCHAR(20)         NULL,
    estado_nuevo            VARCHAR(20)         NULL,
    
    -- ============================================
    -- AUDITORÍA
    -- ============================================
    usuario_id              VARCHAR(50)         NULL,
    usuario_email           VARCHAR(100)        NULL,
    ip_origen               VARCHAR(50)         NULL,
    fecha                   DATETIME            NOT NULL DEFAULT GETDATE(),
    observaciones           VARCHAR(500)        NULL,
    
    -- ============================================
    -- CONSTRAINTS
    -- ============================================
    CONSTRAINT PK_propinas_tpv_historial 
        PRIMARY KEY (id),
    
    CONSTRAINT FK_historial_control 
        FOREIGN KEY (control_id) 
        REFERENCES propinas_tpv_control(id)
);
```

### Índices

```sql
-- Índice para consulta de historial por control
CREATE INDEX IX_historial_control 
ON propinas_tpv_historial (control_id, fecha DESC);

-- Índice para auditoría por usuario
CREATE INDEX IX_historial_usuario 
ON propinas_tpv_historial (usuario_id, fecha DESC);
```

### Justificación
- **Necesaria:** Auditoría completa para módulo financiero
- **Trazabilidad:** Quién, cuándo, qué cambió
- **Cumplimiento:** Requerimiento de control interno

---

## 2.5 Resumen de Tablas

| Tabla | Objetivo | Registros Esperados | Criticidad |
|-------|----------|---------------------|------------|
| `propinas_tpv_control` | Registro principal | 1 por corte (~30-100/día) | **CRÍTICA** |
| `propinas_tpv_config` | Configuración | 5-10 (estable) | **MEDIA** |
| `propinas_tpv_historial` | Auditoría | 2-5 por control | **ALTA** |

---

# 3. USO DE MONGODB COMO CACHE

## 3.1 Qué SE QUEDA en MongoDB

| Colección | Propósito | TTL | Invalidación |
|-----------|-----------|-----|--------------|
| `propinas_cache_preview` | Resultados de consultas preview | 1 hora | Al sincronizar |
| `propinas_cache_resumen` | Agregaciones pre-calculadas | 15 min | Al cambiar estado |
| `propinas_cache_esquemas` | Detección de estructura SQL | 24 horas | Manual |
| `propinas_cache_dashboard` | Datos para dashboard | 5 min | Automático |

## 3.2 Qué NO SE QUEDA en MongoDB

| Dato | Motivo |
|------|--------|
| Registro de propinas | Dato financiero oficial |
| Estado del proceso | Control de flujo crítico |
| Pagos registrados | Auditoría financiera |
| Cuadres realizados | Control operativo |
| Historial de cambios | Trazabilidad legal |
| Configuración oficial | Parámetros de negocio |

## 3.3 Estrategia de Cache

### Lectura (Read-Through)
```
1. Cliente solicita datos
2. Verificar cache en MongoDB
   - SI existe y no expiró → retornar cache
   - SI no existe o expiró → consultar SQL → guardar en cache → retornar
```

### Escritura (Write-Through)
```
1. Escribir SIEMPRE en SQL Server (fuente oficial)
2. Invalidar cache relacionado en MongoDB
3. Opcionalmente: actualizar cache con dato nuevo
```

### Diagrama de Flujo de Cache

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FLUJO DE CACHE                               │
└─────────────────────────────────────────────────────────────────────┘

LECTURA:
┌─────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Cliente │───►│ API Backend  │───►│   MongoDB    │───►│ SQL Server   │
│         │    │              │    │   (Cache)    │    │   (Fuente)   │
└─────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                     │                    │                    │
                     │   ¿Cache válido?   │                    │
                     │◄───────────────────│                    │
                     │        NO          │                    │
                     │────────────────────────────────────────►│
                     │                    │                    │
                     │◄────────────────────────────────────────│
                     │         Datos de SQL                    │
                     │────────────────────►│                   │
                     │   Guardar en cache  │                   │
                     │                     │                   │
                     │◄────────────────────│                   │
                     │    Retornar datos   │                   │

ESCRITURA:
┌─────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Cliente │───►│ API Backend  │───►│ SQL Server   │───►│   MongoDB    │
│         │    │              │    │   (Primero)  │    │  (Invalidar) │
└─────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                     │                    │                    │
                     │  1. Escribir SQL   │                    │
                     │───────────────────►│                    │
                     │                    │                    │
                     │◄───────────────────│                    │
                     │       OK           │                    │
                     │                    │  2. Invalidar     │
                     │────────────────────────────────────────►│
                     │                    │                    │
```

## 3.4 Política de Invalidación

| Evento | Acción en Cache |
|--------|-----------------|
| Sincronización completada | Invalidar `propinas_cache_preview` |
| Pago registrado | Invalidar `propinas_cache_resumen` |
| Cuadre realizado | Invalidar `propinas_cache_resumen`, `propinas_cache_dashboard` |
| Config modificada | Invalidar todo el cache |
| Cada 5 minutos | Refrescar `propinas_cache_dashboard` |

---

# 4. FLUJO DE DATOS

## 4.1 Flujo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FLUJO DE DATOS OFICIAL                          │
└─────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────┐
                    │    SOFTRESTAURANT       │
                    │    (Fuente operativa)   │
                    │    - movtoscaja         │
                    │    - movtoscajadetalles │
                    └───────────┬─────────────┘
                                │
                         SOLO LECTURA
                        (SELECT queries)
                                │
                                ▼
                    ┌─────────────────────────┐
                    │     EDARSA HUB API      │
                    │     (Backend Python)    │
                    │                         │
                    │  1. Lee de SoftRest     │
                    │  2. Calcula comisión    │
                    │  3. Persiste en SQL     │
                    │  4. Invalida cache      │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   SQL SERVER        │ │   SQL SERVER    │ │   MONGODB       │
│   EDARSA HUB        │ │   EDARSA HUB    │ │   (Cache)       │
│                     │ │                 │ │                 │
│ propinas_tpv_control│ │ propinas_tpv_   │ │ propinas_cache_ │
│ propinas_tpv_config │ │ historial       │ │ preview         │
│                     │ │                 │ │ propinas_cache_ │
│  FUENTE OFICIAL     │ │   AUDITORÍA     │ │ resumen         │
└─────────────────────┘ └─────────────────┘ └─────────────────┘
              │                                       │
              │                                       │
              └───────────────┬───────────────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │      FRONTEND           │
                    │   (React Dashboard)     │
                    │                         │
                    │  Lee de API             │
                    │  (que lee de cache      │
                    │   o de SQL)             │
                    └─────────────────────────┘
```

## 4.2 Flujo de Sincronización

```
1. Usuario solicita sincronización (POST /sincronizar)
         │
         ▼
2. Backend obtiene servidores SoftRestaurant de SQL Server
         │
         ▼
3. Para cada servidor:
   a. Detectar esquema (cache en Mongo por 24h)
   b. Ejecutar query defensiva en SoftRestaurant
   c. Calcular comisión (2% o según config SQL)
   d. UPSERT en SQL Server (propinas_tpv_control)
   e. Registrar en historial SQL (propinas_tpv_historial)
   f. Invalidar cache Mongo relacionado
         │
         ▼
4. Retornar resultado al frontend
```

## 4.3 Flujo de Consulta

```
1. Usuario solicita listado (GET /propinas)
         │
         ▼
2. Backend verifica cache MongoDB
   - ¿Existe cache válido para estos filtros?
         │
    ┌────┴────┐
    │         │
   SÍ        NO
    │         │
    │         ▼
    │    3. Consultar SQL Server
    │         │
    │         ▼
    │    4. Guardar en cache MongoDB
    │         │
    └────┬────┘
         │
         ▼
5. Retornar datos al frontend
```

---

# 5. COMPATIBILIDAD CON LO YA IMPLEMENTADO

## 5.1 Análisis de Endpoints Actuales

| Endpoint | Usa Mongo | Acción Requerida |
|----------|-----------|------------------|
| `GET /health` | Sí (verifica colecciones) | Mantener, agregar check SQL |
| `POST /sincronizar` | Sí (escribe) | **Migrar a SQL como primario** |
| `GET /propinas` | Sí (lee) | Migrar lectura a SQL + cache |
| `GET /propinas/{id}` | Sí (lee) | Migrar lectura a SQL |
| `PUT /propinas/{id}/pago` | Sí (escribe) | **Migrar a SQL como primario** |
| `GET /resumen` | Sí (lee agregados) | Migrar a SQL + cache |
| `GET /config` | Sí (lee) | Migrar a SQL |
| `POST /config` | Sí (escribe) | **Migrar a SQL como primario** |
| `GET /detectar-esquema-todos` | Sí (cache) | Mantener Mongo como cache |
| `GET /preview` | Sí (temporal) | Mantener Mongo como temporal |

## 5.2 Estrategia de Transición: Dual Write

### Fase 1: Dual Write (Paralelo)
```python
async def crear_propina(propina_data):
    # 1. Escribir en SQL Server (PRIMARIO)
    sql_result = await sql_repository.crear_propina(propina_data)
    
    # 2. Escribir en MongoDB (SECUNDARIO - temporal)
    try:
        await mongo_repository.crear_propina(propina_data)
    except Exception as e:
        logger.warning(f"Mongo secundario falló: {e}")
        # No es crítico, SQL ya tiene el dato
    
    return sql_result
```

### Fase 2: Lectura Preferente SQL
```python
async def obtener_propinas(filtros):
    try:
        # Intentar leer de SQL (PRIMARIO)
        return await sql_repository.obtener_propinas(filtros)
    except Exception as e:
        logger.error(f"SQL falló, intentando Mongo: {e}")
        # Fallback a Mongo solo en emergencia
        return await mongo_repository.obtener_propinas(filtros)
```

### Fase 3: Deprecar Mongo como Storage
```python
async def obtener_propinas(filtros):
    # Cache check
    cache_key = f"propinas:{hash(filtros)}"
    cached = await mongo_cache.get(cache_key)
    if cached:
        return cached
    
    # SQL es la única fuente
    result = await sql_repository.obtener_propinas(filtros)
    
    # Guardar en cache
    await mongo_cache.set(cache_key, result, ttl=300)
    
    return result
```

## 5.3 Mapeo de Colecciones Mongo → Tablas SQL

| Colección Mongo (Actual) | Tabla SQL (Nueva) | Acción |
|--------------------------|-------------------|--------|
| `propinas_control` | `propinas_tpv_control` | Migrar datos, deprecar colección |
| `propinas_config` | `propinas_tpv_config` | Migrar datos, deprecar colección |
| (no existe) | `propinas_tpv_historial` | Crear nueva |

---

# 6. IMPACTO TÉCNICO

## 6.1 Impacto en Backend

| Componente | Cambio | Esfuerzo |
|------------|--------|----------|
| `repository.py` | Agregar SQL repository | Alto |
| `service.py` | Cambiar a dual write → SQL only | Medio |
| `routes.py` | Sin cambios (misma interfaz) | Bajo |
| `models.py` | Agregar modelos SQLAlchemy | Medio |
| Nuevo: `sql_repository.py` | Crear desde cero | Alto |
| Nuevo: `cache_manager.py` | Gestión de cache | Medio |

## 6.2 Impacto en Rendimiento

| Operación | Antes (Mongo) | Después (SQL + Cache) | Delta |
|-----------|---------------|----------------------|-------|
| Lectura simple | 5-10ms | 10-20ms (sin cache) / 5ms (con cache) | ≈0 |
| Escritura | 10-20ms | 20-30ms | +10ms |
| Agregación | 20-50ms | 30-50ms (sin cache) / 10ms (con cache) | ≈0 |
| Sincronización | 100-200ms | 150-250ms | +50ms |

**Conclusión:** Impacto mínimo en rendimiento, compensado por cache.

## 6.3 Impacto en Almacenamiento

| Sistema | Antes | Después |
|---------|-------|---------|
| MongoDB | ~100KB por día | ~10KB (solo cache) |
| SQL Server | 0 | ~100KB por día |
| **Total** | ~100KB/día | ~110KB/día |

## 6.4 Riesgos de Migración

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Pérdida de datos durante migración | Baja | Alto | Backup completo, validación cruzada |
| Inconsistencia SQL-Mongo | Media | Medio | Dual write, verificación periódica |
| Timeout en SQL Server | Media | Bajo | Pool de conexiones, retry |
| Cambio de esquema post-migración | Baja | Alto | Versionado de esquema |

---

# 7. ESTRATEGIA DE MIGRACIÓN

## 7.1 Plan de Migración en Fases

### FASE M1: Preparación (Sin cambios en producción)
```
Duración: 1-2 días
Actividades:
1. Crear tablas SQL en ambiente de desarrollo
2. Implementar sql_repository.py
3. Implementar cache_manager.py
4. Crear tests unitarios para SQL
5. NO tocar producción
```

### FASE M2: Dual Write (Paralelo seguro)
```
Duración: 2-3 días
Actividades:
1. Activar dual write (SQL + Mongo)
2. Todas las escrituras van a ambos
3. Lectura sigue siendo de Mongo
4. Monitorear consistencia
5. Validar que SQL recibe todos los datos
```

### FASE M3: Lectura de SQL (Cambio de fuente)
```
Duración: 1-2 días
Actividades:
1. Cambiar lectura a SQL como primario
2. Mongo como fallback de emergencia
3. Validar que lecturas funcionan
4. Monitorear errores
```

### FASE M4: Mongo como Cache Only
```
Duración: 1 día
Actividades:
1. Remover escrituras a colecciones Mongo de datos
2. Mantener Mongo solo para cache
3. Implementar invalidación de cache
4. Validar rendimiento
```

### FASE M5: Deprecación Final
```
Duración: 1 día
Actividades:
1. Eliminar código de escritura a Mongo
2. Eliminar colecciones de datos en Mongo
3. Mantener solo colecciones de cache
4. Documentar arquitectura final
```

## 7.2 Diagrama de Fases

```
         FASE M1      FASE M2       FASE M3       FASE M4       FASE M5
         Preparar   Dual Write   SQL Lectura   Cache Only    Deprecar
            │           │            │             │            │
MONGO   ████████████████████████████████████████─ ─ ─ ─ ─ ─ ─ ─┤ (cache)
        (storage)   (storage)    (fallback)    (cache only)    │
            │           │            │             │            │
SQL         │       ████████████████████████████████████████████│
        (vacío)     (writes)     (r+w)         (principal)  (principal)
            │           │            │             │            │
```

## 7.3 Script de Migración de Datos

```sql
-- Script de migración de MongoDB a SQL Server
-- Ejecutar SOLO después de FASE M2

-- 1. Verificar que tabla destino está vacía
SELECT COUNT(*) FROM propinas_tpv_control;

-- 2. Migrar datos desde archivo JSON exportado de MongoDB
-- (el backend generará el script INSERT)

-- 3. Validar conteo
SELECT COUNT(*) as sql_count FROM propinas_tpv_control;
-- Comparar con: db.propinas_control.countDocuments()

-- 4. Validar integridad
SELECT 
    SUM(propinas_tpv) as total_propinas_sql
FROM propinas_tpv_control;
-- Comparar con agregación de MongoDB
```

---

# 8. ESTRATEGIA DE NO REGRESIÓN

## 8.1 Garantías de No Ruptura

| Garantía | Mecanismo |
|----------|-----------|
| Endpoints mantienen misma interfaz | Tests de contrato (API) |
| Datos no se pierden | Backup antes de cada fase |
| Cálculos son correctos | Tests de validación cruzada SQL vs Mongo |
| Rendimiento aceptable | Monitoreo de latencias |
| Rollback posible | Feature flags por fase |

## 8.2 Checklist Pre-Migración

```
[ ] Backup completo de MongoDB
[ ] Backup de configuración actual
[ ] Tests de API funcionando en verde
[ ] Ambiente de staging disponible
[ ] Scripts de rollback preparados
[ ] Monitoreo configurado
[ ] Plan de comunicación listo
```

## 8.3 Checklist Post-Migración (Por Fase)

```
[ ] Todos los endpoints responden
[ ] Datos son consistentes SQL vs Mongo
[ ] Tiempos de respuesta dentro de SLA
[ ] Sin errores en logs
[ ] Usuarios pueden operar normalmente
[ ] Auditoría funcionando
```

## 8.4 Plan de Rollback

### Rollback FASE M2 → M1
```
1. Desactivar dual write
2. Volver a Mongo-only
3. Truncar tablas SQL (datos son copia)
```

### Rollback FASE M3 → M2
```
1. Cambiar lectura a Mongo
2. Mantener dual write
3. Sincronizar datos perdidos si los hay
```

### Rollback FASE M4 → M3
```
1. Reactivar escrituras a Mongo
2. Sincronizar datos desde SQL
```

---

# 9. MVP AJUSTADO

## 9.1 Alcance MVP con Arquitectura Correcta

| Componente | Incluido en MVP |
|------------|-----------------|
| Tabla `propinas_tpv_control` | ✅ Sí |
| Tabla `propinas_tpv_config` | ✅ Sí |
| Tabla `propinas_tpv_historial` | ✅ Sí (simplificada) |
| Cache MongoDB | ✅ Sí (solo para preview/dashboard) |
| Dual write temporal | ✅ Sí (durante migración) |
| UI Frontend | ❌ No (fase posterior) |

## 9.2 Endpoints MVP

| Endpoint | Storage | Cache |
|----------|---------|-------|
| `POST /sincronizar` | SQL | Invalida cache |
| `GET /propinas` | SQL | Usa cache |
| `GET /propinas/{id}` | SQL | No cache |
| `PUT /propinas/{id}/pago` | SQL | Invalida cache |
| `GET /resumen` | SQL | Usa cache |
| `GET /config` | SQL | Cache largo (1h) |
| `GET /preview` | Temporal | Mongo (no persiste) |

## 9.3 Flujo MVP Simplificado

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUJO MVP SIMPLIFICADO                           │
└─────────────────────────────────────────────────────────────────────┘

1. SINCRONIZAR
   SoftRestaurant ──SELECT──► Backend ──INSERT/UPDATE──► SQL Server
                                 │
                                 └──INVALIDATE──► MongoDB Cache

2. CONSULTAR
   Frontend ──GET──► Backend ──CHECK──► MongoDB Cache
                        │                    │
                        │               ┌────┴────┐
                        │              HIT      MISS
                        │               │         │
                        │               │    SQL Server
                        │               │         │
                        │◄──────────────┴─────────┘

3. REGISTRAR PAGO
   Frontend ──PUT──► Backend ──UPDATE──► SQL Server
                                 │
                                 ├──INSERT──► Historial SQL
                                 │
                                 └──INVALIDATE──► MongoDB Cache
```

---

# 10. RESULTADO Y RECOMENDACIÓN FINAL

## 10.1 Propuesta Completa de Arquitectura

| Capa | Tecnología | Rol |
|------|------------|-----|
| **Fuente Operativa** | SoftRestaurant SQL | Solo lectura de propinas |
| **Persistencia Oficial** | SQL Server EDARSA HUB | Fuente de verdad financiera |
| **Auditoría** | SQL Server EDARSA HUB | Historial de cambios |
| **Cache** | MongoDB | Acelerador de lectura |
| **API** | FastAPI | Orquestación |
| **Frontend** | React | Presentación |

## 10.2 Modelo de Tablas SQL (Resumen)

| Tabla | Campos Clave | Registros/Día |
|-------|--------------|---------------|
| `propinas_tpv_control` | 30+ campos (completo) | 30-100 |
| `propinas_tpv_config` | 15 campos | Estable (5-10 total) |
| `propinas_tpv_historial` | 12 campos | 60-300 |

## 10.3 Rol Exacto de MongoDB

```
MongoDB en este módulo:
├── propinas_cache_preview     → Preview de datos (TTL: 1h)
├── propinas_cache_resumen     → Agregaciones (TTL: 15min)
├── propinas_cache_esquemas    → Estructura SQL (TTL: 24h)
└── propinas_cache_dashboard   → Dashboard (TTL: 5min)

MongoDB NO almacena:
├── Datos financieros oficiales
├── Estados de proceso
├── Registros de pago
├── Historial de auditoría
└── Configuración oficial
```

## 10.4 Flujo de Datos Final

```
SoftRestaurant (SQL) ──LECTURA──► Backend ──ESCRITURA──► SQL Server EDARSA HUB
                                    │                           │
                                    │                    (Fuente oficial)
                                    │                           │
                                    └──CACHE──► MongoDB ◄───────┘
                                                   │
                                            (Solo lectura acelerada)
```

## 10.5 Estrategia de Migración (Resumen)

| Fase | Duración | Acción Principal |
|------|----------|------------------|
| M1 | 1-2 días | Preparar SQL sin tocar producción |
| M2 | 2-3 días | Dual write SQL + Mongo |
| M3 | 1-2 días | Lectura de SQL |
| M4 | 1 día | Mongo solo cache |
| M5 | 1 día | Deprecar colecciones Mongo |

## 10.6 Riesgos Identificados

| Riesgo | Mitigación |
|--------|------------|
| Pérdida de datos | Backup + validación cruzada |
| Inconsistencia temporal | Dual write + monitoreo |
| Degradación de rendimiento | Cache + pool de conexiones |
| Complejidad de migración | Fases incrementales con rollback |

## 10.7 Recomendación Final

```
╔════════════════════════════════════════════════════════════════════╗
║                     RECOMENDACIÓN FINAL                            ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  APROBAR esta arquitectura ajustada donde:                        ║
║                                                                    ║
║  ✅ SQL Server EDARSA HUB = Fuente oficial de datos financieros   ║
║  ✅ MongoDB = Solo cache de lectura                               ║
║  ✅ Migración en 5 fases con rollback posible                     ║
║  ✅ Compatibilidad con endpoints existentes                       ║
║  ✅ Auditoría completa en SQL                                     ║
║                                                                    ║
║  IMPLEMENTAR solo después de:                                     ║
║  1. Validación VPN de esquemas SoftRestaurant                     ║
║  2. Aprobación de este documento                                  ║
║  3. Creación de ambiente de staging                               ║
║                                                                    ║
║  PRIORIDAD: Alta                                                  ║
║  RIESGO: Medio (mitigado con fases)                              ║
║  IMPACTO: Bajo en operación actual                               ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

---

**FIN DEL DOCUMENTO DE ARQUITECTURA AJUSTADA**

*Este documento requiere aprobación antes de proceder con implementación.*
*No se realizarán cambios en producción sin autorización explícita.*
