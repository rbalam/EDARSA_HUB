# ADENDA ARQUITECTÓNICA
# Extensión: Módulo de Cuadre de Cortes Z bajo Principio SQL Server

**Versión:** 3.1  
**Fecha:** 15 de Abril de 2026  
**Autor:** Arquitectura EDARSA HUB  
**Estado:** PROPUESTA PARA REVISIÓN  
**Documento Padre:** `ARQUITECTURA_PROPINAS_TPV_v3.md`

---

## RESUMEN EJECUTIVO

### Objetivo de esta Adenda
Extender la arquitectura definida para Propinas TPV al módulo de **Cuadre de Cortes Z**, aplicando el mismo principio:

| Componente | Rol |
|------------|-----|
| **SQL Server EDARSA HUB** | Fuente oficial de datos financieros |
| **MongoDB** | Cache de lectura únicamente |

### Módulos Afectados

| Módulo | Colección Mongo Actual | Acción |
|--------|------------------------|--------|
| Cuadre de Corte Z | `tesoreria_cuadres_z` | **Migrar a SQL Server** |
| Diferencias de Corte | (dentro de cuadre) | **Migrar a SQL Server** |
| Incidencias de Caja | (no existe aún) | **Crear en SQL Server** |
| Auditoría de Cierres | (no existe aún) | **Crear en SQL Server** |
| Historial de Cortes | (no existe aún) | **Crear en SQL Server** |

---

# 1. ADAPTACIÓN DE ARQUITECTURA AL MÓDULO DE CORTE Z

## 1.1 Situación Actual

### Colección MongoDB: `tesoreria_cuadres_z`

```javascript
// Estructura actual del documento
{
  "_id": ObjectId,
  "corte_z": {
    "folio_corte": "2889",
    "fecha_corte": "2026-04-07T00:00:00",
    "sucursal_id": "CIENFUEGOS",
    "sucursal_nombre": "Cienfuegos",
    "fuente": "SOFTRESTAURANT",
    "efectivo_inicial": 15000.00,
    "efectivo_ventas": 13656.00,
    "tarjeta": 94179.20,
    "propinas_pagadas": 11725.20,
    "total_ventas": 100520.00,
    "monto_a_depositar": 1930.80
    // ... más campos
  },
  "conteo_efectivo": { ... },
  "ficha_deposito": { ... },
  "estado": "PENDIENTE",
  "monto_esperado": 1930.80,
  "monto_contado": 0,
  "monto_depositado": 0,
  "diferencia": 0,
  "created_at": "...",
  "created_by": "..."
}
```

### Problemas con el Modelo Actual

| Problema | Impacto |
|----------|---------|
| Datos financieros críticos en MongoDB | Sin garantías ACID |
| Sin auditoría de cambios | No hay trazabilidad |
| Sin historial de estados | No se sabe cuándo cambió de PENDIENTE a CUADRADO |
| Incidencias no registradas | Faltantes/sobrantes sin documentar |
| Sin relación explícita con Propinas | Datos desconectados |

## 1.2 Principio de Migración

```
╔════════════════════════════════════════════════════════════════════╗
║  REGLA MAESTRA EDARSA HUB                                          ║
║                                                                    ║
║  Todo dato que:                                                   ║
║  - Tenga implicación financiera/fiscal                            ║
║  - Requiera auditoría                                             ║
║  - Sea fuente para reportes oficiales                             ║
║  - Tenga responsabilidad legal                                    ║
║                                                                    ║
║  DEBE vivir en SQL Server, NUNCA en MongoDB.                      ║
╚════════════════════════════════════════════════════════════════════╝
```

---

# 2. TABLAS SQL PARA MÓDULO DE CORTE Z

## 2.1 Modelo de Datos Propuesto

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SQL SERVER - EDARSA HUB                          │
│              Módulo Financiero Unificado (Cortes + Propinas)        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────┐                                        │
│  │    cortes_z_control     │◄─────────────────────────────────┐    │
│  │    (Registro principal  │                                   │    │
│  │     de cada corte Z)    │                                   │    │
│  └───────────┬─────────────┘                                   │    │
│              │                                                  │    │
│      ┌───────┼───────┬───────────────┬──────────────┐          │    │
│      │       │       │               │              │          │    │
│      ▼       ▼       ▼               ▼              ▼          │    │
│  ┌───────┐ ┌───────┐ ┌─────────┐ ┌────────┐ ┌─────────────┐   │    │
│  │conteo │ │ficha  │ │inciden- │ │histo-  │ │propinas_tpv_│   │    │
│  │efect- │ │depo-  │ │cias_    │ │rial_   │ │control      │───┘    │
│  │ivo    │ │sito   │ │caja     │ │cortes  │ │(ya definido)│        │
│  └───────┘ └───────┘ └─────────┘ └────────┘ └─────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 2.2 Tabla Principal: `cortes_z_control`

### Objetivo
Registro oficial del cuadre de cada corte de caja Z.

### Estructura

```sql
CREATE TABLE cortes_z_control (
    -- ============================================
    -- IDENTIFICADORES
    -- ============================================
    id                          UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID(),
    server_id                   VARCHAR(50)         NOT NULL,
    sucursal_id                 VARCHAR(50)         NOT NULL,
    folio_corte                 VARCHAR(50)         NOT NULL,
    fecha_corte                 DATE                NOT NULL,
    
    -- ============================================
    -- CONTEXTO DEL ORIGEN
    -- ============================================
    server_name                 VARCHAR(100)        NOT NULL,
    system_type                 VARCHAR(20)         NOT NULL,  -- SOFTRESTAURANT, MPRO
    sucursal_nombre             VARCHAR(100)        NULL,
    empresa_id                  VARCHAR(50)         NULL,
    
    -- ============================================
    -- DATOS DEL CORTE Z (Lectura del origen)
    -- ============================================
    efectivo_inicial            DECIMAL(18,2)       NOT NULL DEFAULT 0,
    efectivo_ventas             DECIMAL(18,2)       NOT NULL DEFAULT 0,
    ventas_tarjeta              DECIMAL(18,2)       NOT NULL DEFAULT 0,
    ventas_vales                DECIMAL(18,2)       NOT NULL DEFAULT 0,
    ventas_otros                DECIMAL(18,2)       NOT NULL DEFAULT 0,
    depositos_efectivo          DECIMAL(18,2)       NOT NULL DEFAULT 0,
    retiros_efectivo            DECIMAL(18,2)       NOT NULL DEFAULT 0,
    propinas_pagadas            DECIMAL(18,2)       NOT NULL DEFAULT 0,
    saldo_final_sistema         DECIMAL(18,2)       NOT NULL DEFAULT 0,
    efectivo_final_sistema      DECIMAL(18,2)       NOT NULL DEFAULT 0,
    total_ventas                DECIMAL(18,2)       NOT NULL DEFAULT 0,
    
    -- ============================================
    -- CÁLCULOS EDARSA HUB
    -- ============================================
    monto_esperado_deposito     DECIMAL(18,2)       NOT NULL DEFAULT 0,
    monto_contado               DECIMAL(18,2)       NULL,
    monto_depositado            DECIMAL(18,2)       NULL,
    diferencia_conteo           DECIMAL(18,2)       NULL,
    diferencia_deposito         DECIMAL(18,2)       NULL,
    
    -- ============================================
    -- ESTADO DEL CUADRE
    -- ============================================
    estado                      VARCHAR(20)         NOT NULL DEFAULT 'PENDIENTE',
    fecha_cuadre_esperada       DATE                NULL,
    fecha_cuadre_real           DATETIME            NULL,
    
    -- ============================================
    -- REFERENCIAS A TABLAS RELACIONADAS
    -- ============================================
    conteo_efectivo_id          UNIQUEIDENTIFIER    NULL,
    ficha_deposito_id           UNIQUEIDENTIFIER    NULL,
    propina_tpv_id              UNIQUEIDENTIFIER    NULL,  -- FK a propinas_tpv_control
    
    -- ============================================
    -- VALIDACIONES
    -- ============================================
    fecha_deposito_valida       BIT                 NULL,
    importe_deposito_valido     BIT                 NULL,
    tolerancia_aplicada         DECIMAL(18,2)       NOT NULL DEFAULT 5.00,
    
    -- ============================================
    -- RESPONSABLES
    -- ============================================
    cajero_cierre_id            VARCHAR(50)         NULL,
    cajero_cierre_nombre        VARCHAR(100)        NULL,
    supervisor_cuadre_id        VARCHAR(50)         NULL,
    supervisor_cuadre_email     VARCHAR(100)        NULL,
    
    -- ============================================
    -- OBSERVACIONES
    -- ============================================
    observaciones               VARCHAR(1000)       NULL,
    
    -- ============================================
    -- AUDITORÍA
    -- ============================================
    fecha_sincronizacion        DATETIME            NOT NULL DEFAULT GETDATE(),
    sincronizado_por            VARCHAR(100)        NULL,
    created_at                  DATETIME            NOT NULL DEFAULT GETDATE(),
    updated_at                  DATETIME            NOT NULL DEFAULT GETDATE(),
    version                     INT                 NOT NULL DEFAULT 1,
    
    -- ============================================
    -- CONSTRAINTS
    -- ============================================
    CONSTRAINT PK_cortes_z_control 
        PRIMARY KEY (id),
    
    CONSTRAINT UK_cortes_z_corte 
        UNIQUE (server_id, sucursal_id, folio_corte, fecha_corte),
    
    CONSTRAINT CK_cortes_z_estado 
        CHECK (estado IN ('PENDIENTE', 'EN_PROCESO', 'CUADRADO', 'DESCUADRE', 'CON_INCIDENCIA', 'CERRADO')),
    
    CONSTRAINT CK_cortes_z_system 
        CHECK (system_type IN ('SOFTRESTAURANT', 'MPRO'))
);
```

### Índices

```sql
CREATE INDEX IX_cortes_z_fecha_estado 
ON cortes_z_control (fecha_corte DESC, estado);

CREATE INDEX IX_cortes_z_servidor 
ON cortes_z_control (server_id, fecha_corte DESC);

CREATE INDEX IX_cortes_z_sucursal 
ON cortes_z_control (sucursal_id, fecha_corte DESC);

CREATE INDEX IX_cortes_z_propina 
ON cortes_z_control (propina_tpv_id);
```

---

## 2.3 Tabla: `cortes_z_conteo_efectivo`

### Objetivo
Registro detallado del conteo físico de efectivo realizado durante el cuadre.

### Estructura

```sql
CREATE TABLE cortes_z_conteo_efectivo (
    -- ============================================
    -- IDENTIFICADORES
    -- ============================================
    id                      UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID(),
    corte_z_id              UNIQUEIDENTIFIER    NOT NULL,
    
    -- ============================================
    -- CONTEO DE BILLETES
    -- ============================================
    billetes_1000           INT                 NOT NULL DEFAULT 0,
    billetes_500            INT                 NOT NULL DEFAULT 0,
    billetes_200            INT                 NOT NULL DEFAULT 0,
    billetes_100            INT                 NOT NULL DEFAULT 0,
    billetes_50             INT                 NOT NULL DEFAULT 0,
    billetes_20             INT                 NOT NULL DEFAULT 0,
    subtotal_billetes       DECIMAL(18,2)       NOT NULL DEFAULT 0,
    
    -- ============================================
    -- CONTEO DE MONEDAS
    -- ============================================
    monedas_20              INT                 NOT NULL DEFAULT 0,
    monedas_10              INT                 NOT NULL DEFAULT 0,
    monedas_5               INT                 NOT NULL DEFAULT 0,
    monedas_2               INT                 NOT NULL DEFAULT 0,
    monedas_1               INT                 NOT NULL DEFAULT 0,
    monedas_050             INT                 NOT NULL DEFAULT 0,
    subtotal_monedas        DECIMAL(18,2)       NOT NULL DEFAULT 0,
    
    -- ============================================
    -- TOTALES
    -- ============================================
    total_contado           DECIMAL(18,2)       NOT NULL DEFAULT 0,
    
    -- ============================================
    -- AUDITORÍA
    -- ============================================
    contado_por_id          VARCHAR(50)         NULL,
    contado_por_nombre      VARCHAR(100)        NULL,
    fecha_conteo            DATETIME            NOT NULL DEFAULT GETDATE(),
    observaciones           VARCHAR(500)        NULL,
    
    -- ============================================
    -- CONSTRAINTS
    -- ============================================
    CONSTRAINT PK_cortes_z_conteo 
        PRIMARY KEY (id),
    
    CONSTRAINT FK_conteo_corte 
        FOREIGN KEY (corte_z_id) 
        REFERENCES cortes_z_control(id)
);
```

---

## 2.4 Tabla: `cortes_z_ficha_deposito`

### Objetivo
Registro de las fichas de depósito bancario asociadas a cada corte.

### Estructura

```sql
CREATE TABLE cortes_z_ficha_deposito (
    -- ============================================
    -- IDENTIFICADORES
    -- ============================================
    id                      UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID(),
    corte_z_id              UNIQUEIDENTIFIER    NOT NULL,
    
    -- ============================================
    -- DATOS DEL DEPÓSITO
    -- ============================================
    banco                   VARCHAR(50)         NULL,
    cuenta_destino          VARCHAR(30)         NULL,
    sucursal_banco          VARCHAR(100)        NULL,
    referencia              VARCHAR(50)         NULL,
    fecha_deposito          DATE                NOT NULL,
    importe                 DECIMAL(18,2)       NOT NULL,
    
    -- ============================================
    -- ARCHIVO ADJUNTO
    -- ============================================
    archivo_url             VARCHAR(500)        NULL,
    archivo_nombre          VARCHAR(200)        NULL,
    archivo_hash            VARCHAR(64)         NULL,  -- SHA256 para integridad
    
    -- ============================================
    -- OCR
    -- ============================================
    ocr_procesado           BIT                 NOT NULL DEFAULT 0,
    ocr_datos_json          NVARCHAR(MAX)       NULL,
    ocr_validado            BIT                 NOT NULL DEFAULT 0,
    
    -- ============================================
    -- VALIDACIÓN
    -- ============================================
    fecha_valida            BIT                 NULL,
    fecha_esperada          DATE                NULL,
    importe_valido          BIT                 NULL,
    diferencia_importe      DECIMAL(18,2)       NULL,
    
    -- ============================================
    -- AUDITORÍA
    -- ============================================
    registrado_por_id       VARCHAR(50)         NULL,
    registrado_por_email    VARCHAR(100)        NULL,
    fecha_registro          DATETIME            NOT NULL DEFAULT GETDATE(),
    validado_por_id         VARCHAR(50)         NULL,
    fecha_validacion        DATETIME            NULL,
    observaciones           VARCHAR(500)        NULL,
    
    -- ============================================
    -- CONSTRAINTS
    -- ============================================
    CONSTRAINT PK_cortes_z_ficha 
        PRIMARY KEY (id),
    
    CONSTRAINT FK_ficha_corte 
        FOREIGN KEY (corte_z_id) 
        REFERENCES cortes_z_control(id)
);
```

---

## 2.5 Tabla: `cortes_z_incidencias`

### Objetivo
Registro de incidencias de caja: faltantes, sobrantes, errores de conteo, etc.

### Estructura

```sql
CREATE TABLE cortes_z_incidencias (
    -- ============================================
    -- IDENTIFICADORES
    -- ============================================
    id                      UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID(),
    corte_z_id              UNIQUEIDENTIFIER    NOT NULL,
    
    -- ============================================
    -- TIPO DE INCIDENCIA
    -- ============================================
    tipo_incidencia         VARCHAR(30)         NOT NULL,
    -- FALTANTE_EFECTIVO, SOBRANTE_EFECTIVO, ERROR_TARJETA,
    -- DEPOSITO_FUERA_TIEMPO, FICHA_NO_COINCIDE, OTRO
    
    -- ============================================
    -- DATOS DE LA INCIDENCIA
    -- ============================================
    monto_involucrado       DECIMAL(18,2)       NOT NULL DEFAULT 0,
    descripcion             VARCHAR(1000)       NOT NULL,
    
    -- ============================================
    -- RESOLUCIÓN
    -- ============================================
    estado                  VARCHAR(20)         NOT NULL DEFAULT 'ABIERTA',
    -- ABIERTA, EN_REVISION, RESUELTA, CERRADA_SIN_RESOLVER
    
    resolucion              VARCHAR(1000)       NULL,
    fecha_resolucion        DATETIME            NULL,
    resuelto_por_id         VARCHAR(50)         NULL,
    resuelto_por_email      VARCHAR(100)        NULL,
    
    -- ============================================
    -- RESPONSABLE
    -- ============================================
    responsable_id          VARCHAR(50)         NULL,
    responsable_nombre      VARCHAR(100)        NULL,
    requiere_descuento      BIT                 NOT NULL DEFAULT 0,
    descuento_aplicado      DECIMAL(18,2)       NULL,
    
    -- ============================================
    -- AUDITORÍA
    -- ============================================
    reportado_por_id        VARCHAR(50)         NULL,
    reportado_por_email     VARCHAR(100)        NULL,
    fecha_reporte           DATETIME            NOT NULL DEFAULT GETDATE(),
    
    -- ============================================
    -- CONSTRAINTS
    -- ============================================
    CONSTRAINT PK_cortes_z_incidencias 
        PRIMARY KEY (id),
    
    CONSTRAINT FK_incidencia_corte 
        FOREIGN KEY (corte_z_id) 
        REFERENCES cortes_z_control(id),
    
    CONSTRAINT CK_incidencia_tipo 
        CHECK (tipo_incidencia IN (
            'FALTANTE_EFECTIVO', 'SOBRANTE_EFECTIVO', 'ERROR_TARJETA',
            'DEPOSITO_FUERA_TIEMPO', 'FICHA_NO_COINCIDE', 'OTRO'
        )),
    
    CONSTRAINT CK_incidencia_estado 
        CHECK (estado IN ('ABIERTA', 'EN_REVISION', 'RESUELTA', 'CERRADA_SIN_RESOLVER'))
);
```

---

## 2.6 Tabla: `cortes_z_historial`

### Objetivo
Auditoría completa de todos los cambios realizados en el cuadre de cortes Z.

### Estructura

```sql
CREATE TABLE cortes_z_historial (
    -- ============================================
    -- IDENTIFICADORES
    -- ============================================
    id                      UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID(),
    corte_z_id              UNIQUEIDENTIFIER    NOT NULL,
    
    -- ============================================
    -- DATOS DEL CAMBIO
    -- ============================================
    accion                  VARCHAR(50)         NOT NULL,
    -- CREACION, SINCRONIZACION, CONTEO_REGISTRADO, FICHA_CARGADA,
    -- FICHA_VALIDADA, CUADRADO, DESCUADRE_DETECTADO, INCIDENCIA_CREADA,
    -- INCIDENCIA_RESUELTA, CIERRE_MANUAL, AJUSTE
    
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
    CONSTRAINT PK_cortes_z_historial 
        PRIMARY KEY (id),
    
    CONSTRAINT FK_historial_corte_z 
        FOREIGN KEY (corte_z_id) 
        REFERENCES cortes_z_control(id)
);

CREATE INDEX IX_historial_corte_z 
ON cortes_z_historial (corte_z_id, fecha DESC);

CREATE INDEX IX_historial_usuario 
ON cortes_z_historial (usuario_id, fecha DESC);
```

---

## 2.7 Resumen de Tablas Cortes Z

| Tabla | Objetivo | Registros Esperados | Criticidad |
|-------|----------|---------------------|------------|
| `cortes_z_control` | Registro principal de cuadre | 1 por corte (~30-100/día) | **CRÍTICA** |
| `cortes_z_conteo_efectivo` | Detalle de conteo | 1 por corte | **ALTA** |
| `cortes_z_ficha_deposito` | Registro de depósito | 1 por corte | **ALTA** |
| `cortes_z_incidencias` | Faltantes/sobrantes | 0-5 por día | **ALTA** |
| `cortes_z_historial` | Auditoría de cambios | 3-10 por corte | **ALTA** |

---

# 3. INFORMACIÓN EN MONGODB (SOLO CACHE)

## 3.1 Qué SE QUEDA en MongoDB

| Colección | Propósito | TTL | Invalidación |
|-----------|-----------|-----|--------------|
| `cortes_z_cache_listado` | Lista de cortes para UI | 5 min | Al sincronizar |
| `cortes_z_cache_resumen` | Agregaciones (totales por estado) | 5 min | Al cambiar estado |
| `cortes_z_cache_dashboard` | Datos para widgets | 5 min | Automático |

## 3.2 Qué NO SE QUEDA en MongoDB

| Dato | Motivo |
|------|--------|
| Registro de cuadre | Dato financiero oficial |
| Conteo de efectivo | Auditoría operativa |
| Fichas de depósito | Documento fiscal |
| Incidencias | Responsabilidad legal |
| Historial de cambios | Trazabilidad obligatoria |

## 3.3 Estrategia de Cache (Igual que Propinas)

```
LECTURA:
1. Frontend solicita listado de cortes
2. Verificar cache MongoDB (TTL: 5 min)
   - SI válido → retornar
   - SI expirado → consultar SQL → actualizar cache → retornar

ESCRITURA:
1. Escribir SIEMPRE en SQL Server primero
2. Invalidar cache relacionado en MongoDB
3. Retornar respuesta
```

---

# 4. RELACIÓN ENTRE MÓDULOS

## 4.1 Modelo de Relaciones

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MODELO RELACIONAL FINANCIERO                      │
└─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │                      SOFTRESTAURANT / MPRO                   │
    │                      (Fuente Operativa)                      │
    │                                                              │
    │  movtoscaja ◄──── Corte Z ────► movtoscajadetalles          │
    │      │                               │                       │
    │      │                               └── idconcepto=9        │
    │      │                                   (Propinas)          │
    └──────┼───────────────────────────────────┼───────────────────┘
           │                                   │
           │ LECTURA                          │ LECTURA
           ▼                                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                      EDARSA HUB (SQL Server)                 │
    ├─────────────────────────────────────────────────────────────┤
    │                                                              │
    │  ┌──────────────────┐         ┌──────────────────┐         │
    │  │ cortes_z_control │◄───────►│ propinas_tpv_    │         │
    │  │                  │   FK    │ control          │         │
    │  │ - id (PK)        │         │                  │         │
    │  │ - propina_tpv_id │─────────│ - id (PK)        │         │
    │  │ - monto_esperado │         │ - propinas_tpv   │         │
    │  │ - estado         │         │ - comision_2%    │         │
    │  └────────┬─────────┘         └──────────────────┘         │
    │           │                                                  │
    │     ┌─────┼─────┬─────────────┬──────────────┐              │
    │     │     │     │             │              │              │
    │     ▼     ▼     ▼             ▼              ▼              │
    │  conteo  ficha  incidencias  historial   historial_        │
    │  efectivo deposito caja      cortes_z    propinas          │
    │                                                              │
    └─────────────────────────────────────────────────────────────┘
```

## 4.2 Relación Corte Z ↔ Propinas TPV

### Llave de Vinculación

```sql
-- En cortes_z_control
propina_tpv_id UNIQUEIDENTIFIER REFERENCES propinas_tpv_control(id)
```

### Reglas de Negocio

| Escenario | Acción |
|-----------|--------|
| Se sincroniza Corte Z | Buscar si existe propina_tpv para mismo (server_id, sucursal_id, folio_corte, fecha_corte) |
| Se sincroniza Propina TPV | Buscar si existe corte_z para vincular |
| Ambos existen | Vincular por `propina_tpv_id` |
| Solo existe uno | Crear el faltante al sincronizar el otro |

### Validación Cruzada

```sql
-- El monto de propinas pagadas del Corte Z debe coincidir 
-- con las propinas_totales del registro de propinas TPV
SELECT 
    cz.id AS corte_id,
    cz.propinas_pagadas,
    pt.propinas_totales_corte,
    ABS(cz.propinas_pagadas - pt.propinas_totales_corte) AS diferencia
FROM cortes_z_control cz
JOIN propinas_tpv_control pt ON cz.propina_tpv_id = pt.id
WHERE ABS(cz.propinas_pagadas - pt.propinas_totales_corte) > 1.00;
-- Si hay registros, hay inconsistencia que investigar
```

## 4.3 Relación con Sucursal y Servidor

```
┌─────────────────────────────────────────────────────────────────────┐
│                      JERARQUÍA DE DATOS                             │
└─────────────────────────────────────────────────────────────────────┘

SERVIDOR (ej: "Cienfuegos - SoftRestaurant")
    │
    ├── SUCURSAL (ej: "CIENFUEGOS")
    │       │
    │       ├── CORTE Z (fecha: 2026-04-14, folio: 2889)
    │       │       │
    │       │       ├── Conteo Efectivo
    │       │       ├── Ficha Depósito
    │       │       ├── Incidencias (0..n)
    │       │       ├── Historial (1..n)
    │       │       └── Propina TPV Vinculada (0..1)
    │       │
    │       └── CORTE Z (fecha: 2026-04-14, folio: 2890)
    │               └── ...
    │
    └── SUCURSAL (ej: "LA_ESTELAR")
            └── ...
```

---

# 5. CONSISTENCIA ENTRE CUADRE Y PROPINAS TPV

## 5.1 Puntos de Consistencia

| Punto | Validación | Acción si falla |
|-------|------------|-----------------|
| **Propinas Pagadas** | `corte_z.propinas_pagadas == propina_tpv.propinas_totales_corte` | Alerta, revisar sincronización |
| **Fecha** | `corte_z.fecha_corte == propina_tpv.fecha_corte` | Error, no deben diferir |
| **Folio** | `corte_z.folio_corte == propina_tpv.folio_corte` | Error, llaves deben coincidir |
| **Comisión** | Solo en propinas_tpv | Corte Z no calcula comisión |

## 5.2 Flujo de Sincronización Unificado

```
┌─────────────────────────────────────────────────────────────────────┐
│              SINCRONIZACIÓN UNIFICADA (Corte Z + Propinas)          │
└─────────────────────────────────────────────────────────────────────┘

1. Usuario solicita sincronización del día
         │
         ▼
2. Backend lee de SoftRestaurant:
   - movtoscaja (datos del corte)
   - movtoscajadetalles idconcepto=9 (propinas)
         │
         ▼
3. Transacción SQL Server:
   BEGIN TRANSACTION
         │
   ├── UPSERT cortes_z_control (datos del corte)
   │         │
   │         └── INSERT cortes_z_historial (SINCRONIZACION)
   │
   ├── UPSERT propinas_tpv_control (datos de propinas)
   │         │
   │         └── INSERT propinas_tpv_historial (SINCRONIZACION)
   │
   └── UPDATE cortes_z_control 
       SET propina_tpv_id = [id del registro de propinas]
         │
   COMMIT TRANSACTION
         │
         ▼
4. Invalidar cache MongoDB:
   - cortes_z_cache_*
   - propinas_cache_*
         │
         ▼
5. Retornar resultado consolidado
```

## 5.3 Manejo de Inconsistencias

```sql
-- Procedimiento para detectar inconsistencias
CREATE PROCEDURE sp_validar_consistencia_corte_propinas
    @fecha_inicio DATE,
    @fecha_fin DATE
AS
BEGIN
    SELECT 
        cz.id AS corte_z_id,
        cz.folio_corte,
        cz.fecha_corte,
        cz.propinas_pagadas AS propinas_en_corte,
        pt.propinas_totales_corte AS propinas_en_registro,
        CASE 
            WHEN pt.id IS NULL THEN 'SIN_REGISTRO_PROPINA'
            WHEN ABS(cz.propinas_pagadas - pt.propinas_totales_corte) > 1 THEN 'MONTO_DIFERENTE'
            ELSE 'OK'
        END AS estado_consistencia
    FROM cortes_z_control cz
    LEFT JOIN propinas_tpv_control pt ON cz.propina_tpv_id = pt.id
    WHERE cz.fecha_corte BETWEEN @fecha_inicio AND @fecha_fin
      AND (pt.id IS NULL OR ABS(cz.propinas_pagadas - pt.propinas_totales_corte) > 1);
END;
```

---

# 6. IMPACTO TÉCNICO DE UNIFICACIÓN

## 6.1 Impacto en Backend

| Componente | Cambio | Esfuerzo |
|------------|--------|----------|
| `repository_cuadres_z.py` | Migrar de MongoDB a SQL | Alto |
| `tesoreria.py` | Adaptar endpoints a SQL | Medio |
| `tesoreria_models.py` | Agregar modelos SQLAlchemy | Medio |
| Nuevo: `sql_repository_cortes_z.py` | Crear desde cero | Alto |
| Nuevo: `sql_repository_propinas.py` | Ya definido en v3 | - |
| Nuevo: `sync_service.py` | Sincronización unificada | Alto |
| `cache_manager.py` | Extender para Cortes Z | Bajo |

## 6.2 Impacto en Frontend

| Componente | Cambio | Esfuerzo |
|------------|--------|----------|
| Listado de Cortes Z | Sin cambio (misma API) | Ninguno |
| Detalle de Cuadre | Sin cambio visual | Ninguno |
| Dashboard Financiero | Agregar indicador de consistencia | Bajo |

## 6.3 Impacto en Rendimiento

| Operación | Antes (Mongo) | Después (SQL + Cache) | Delta |
|-----------|---------------|----------------------|-------|
| Listado cortes | 10-20ms | 15-30ms (sin cache) / 5ms (con cache) | ≈0 |
| Detalle cuadre | 5-10ms | 10-20ms | +10ms |
| Crear cuadre | 20-30ms | 40-60ms (transacción SQL) | +30ms |
| Sincronización unificada | N/A | 100-200ms | Nuevo |

**Conclusión:** Impacto aceptable, compensado por cache y garantías ACID.

## 6.4 Impacto en Almacenamiento

| Sistema | Antes | Después |
|---------|-------|---------|
| MongoDB `tesoreria_cuadres_z` | ~200KB/día | ~20KB/día (solo cache) |
| SQL Server (nuevas tablas) | 0 | ~300KB/día |
| **Total** | ~200KB/día | ~320KB/día |

---

# 7. RECOMENDACIÓN DE IMPLEMENTACIÓN

## 7.1 Opciones Evaluadas

| Opción | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| **A: Secuencial** | Primero Propinas, luego Cortes Z | Menor riesgo | Duplicación temporal de código |
| **B: Paralela** | Ambos módulos simultáneamente | Código unificado desde inicio | Mayor complejidad |
| **C: Unificada** | Un solo repositorio SQL compartido | Máxima consistencia | Depende de ambos módulos |

## 7.2 Recomendación: OPCIÓN C - IMPLEMENTACIÓN UNIFICADA

### Justificación

1. **Consistencia:** Un solo servicio de sincronización que escribe ambos registros en transacción
2. **Código:** Repositorio SQL compartido (`FinanzasRepository`) para ambos módulos
3. **Cache:** Mismo `CacheManager` para invalidación coordinada
4. **Auditoría:** Historial unificado que muestra correlación entre eventos

### Fases de Implementación

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PLAN DE IMPLEMENTACIÓN UNIFICADA                  │
└─────────────────────────────────────────────────────────────────────┘

FASE U1: Preparación (Sin cambios en producción)
├── Crear todas las tablas SQL (propinas + cortes_z)
├── Implementar FinanzasSQLRepository (unificado)
├── Implementar CacheManager
├── Crear tests unitarios
└── Duración: 2-3 días

FASE U2: Migración de Lectura
├── Implementar endpoints de lectura desde SQL
├── Mantener escritura dual (SQL + Mongo)
├── Validar consistencia
└── Duración: 1-2 días

FASE U3: Migración de Escritura
├── Sincronización unificada escribiendo solo a SQL
├── Invalidación de cache MongoDB
├── Validar transacciones ACID
└── Duración: 1-2 días

FASE U4: Deprecación MongoDB
├── Remover código de escritura a Mongo
├── Mantener colecciones de cache
├── Eliminar colecciones de datos
└── Duración: 1 día

TOTAL ESTIMADO: 5-8 días
```

## 7.3 Estructura de Código Propuesta

```
/app/backend/modules/finanzas/
├── __init__.py
├── # NUEVO: Repositorio SQL unificado
├── sql_repository.py           # Clase FinanzasSQLRepository
│   ├── # Métodos para propinas_tpv_*
│   ├── # Métodos para cortes_z_*
│   └── # Métodos de sincronización unificada
│
├── # NUEVO: Gestor de cache
├── cache_manager.py            # Clase FinanzasCacheManager
│   ├── # Cache de propinas
│   └── # Cache de cortes Z
│
├── # EXISTENTES (se mantienen, se adaptan)
├── propinas_tpv/
│   ├── routes.py               # Sin cambios de interfaz
│   ├── service.py              # Usa sql_repository
│   └── models.py               # Agrega modelos SQLAlchemy
│
├── # EXISTENTES (se adaptan)
├── tesoreria.py                # Usa sql_repository
├── tesoreria_models.py         # Agrega modelos SQLAlchemy
├── repository_cuadres_z.py     # SE DEPRECA → usa sql_repository
│
└── # NUEVO: Servicio de sincronización
    sync_service.py             # Clase SyncService
    ├── sincronizar_corte_completo()
    ├── validar_consistencia()
    └── reparar_inconsistencias()
```

---

# 8. CONCLUSIÓN Y APROBACIÓN

## 8.1 Resumen de Cambios

| Aspecto | Situación Actual | Situación Propuesta |
|---------|------------------|---------------------|
| **Propinas TPV** | MongoDB | SQL Server + Cache Mongo |
| **Cortes Z** | MongoDB | SQL Server + Cache Mongo |
| **Conteo Efectivo** | Embebido en Mongo | Tabla SQL separada |
| **Fichas Depósito** | Embebido en Mongo | Tabla SQL separada |
| **Incidencias** | No existe | Tabla SQL nueva |
| **Historial** | No existe | Tablas SQL nuevas |
| **Relación Corte-Propina** | Implícita | FK explícita |

## 8.2 Beneficios

| Beneficio | Descripción |
|-----------|-------------|
| **Consistencia ACID** | Transacciones garantizadas para operaciones financieras |
| **Auditoría completa** | Historial de todos los cambios con usuario y timestamp |
| **Integridad referencial** | FK entre cortes y propinas |
| **Modelo unificado** | Un solo principio arquitectónico para módulos financieros |
| **Escalabilidad** | SQL Server optimizado para queries complejas |
| **Cumplimiento** | Datos financieros en sistema auditable |

## 8.3 Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Pérdida de datos en migración | Backup completo + validación cruzada |
| Degradación de rendimiento | Cache MongoDB + índices SQL optimizados |
| Complejidad de transacciones | Servicio de sincronización bien probado |
| Tiempo de implementación | Fases incrementales con rollback |

## 8.4 Aprobación Requerida

```
╔════════════════════════════════════════════════════════════════════╗
║                     SOLICITUD DE APROBACIÓN                        ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  Aprobar esta ADENDA para proceder con implementación unificada:  ║
║                                                                    ║
║  ✅ 5 tablas nuevas para Cortes Z en SQL Server                   ║
║  ✅ Relación FK entre Cortes Z y Propinas TPV                     ║
║  ✅ Cache MongoDB unificado para ambos módulos                    ║
║  ✅ Servicio de sincronización transaccional                      ║
║  ✅ Implementación en 4 fases (5-8 días)                          ║
║                                                                    ║
║  Espera: Confirmación del usuario para iniciar FASE U1            ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

---

**FIN DE ADENDA ARQUITECTÓNICA**

*Este documento complementa `ARQUITECTURA_PROPINAS_TPV_v3.md` y debe aprobarse antes de proceder con implementación.*
