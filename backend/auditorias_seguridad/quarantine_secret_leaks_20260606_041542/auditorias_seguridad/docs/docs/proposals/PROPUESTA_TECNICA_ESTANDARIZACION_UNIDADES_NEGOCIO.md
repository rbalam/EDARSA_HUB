# PROPUESTA TÉCNICA — ESTANDARIZACIÓN DE UNIDADES DE NEGOCIO EDARSAHUB

**Versión:** 1.0  
**Fecha:** 2026-05-15  
**Autor:** Arquitectura EDARSAHUB  
**Estado:** PROPUESTA PASIVA - NO EJECUTAR SIN AUTORIZACIÓN  
**Basado en:** `/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md`

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Estado Actual de la Arquitectura](#2-estado-actual-de-la-arquitectura)
3. [DDL: Sistema_Tipos](#3-ddl-sistema_tipos)
4. [DDL: Sistema_EmpresasAlias](#4-ddl-sistema_empresasalias)
5. [DDL: Sistema_EmpresasServidores](#5-ddl-sistema_empresasservidores)
6. [Compatibilidad con Tablas Existentes](#6-compatibilidad-con-tablas-existentes)
7. [Script de Carga Inicial de Aliases](#7-script-de-carga-inicial-de-aliases)
8. [Diseño del Resolver Central](#8-diseño-del-resolver-central)
9. [Reglas de Negocio por Sistema](#9-reglas-de-negocio-por-sistema)
10. [Plan de Migración Gradual](#10-plan-de-migración-gradual)
11. [Riesgos de Regresión](#11-riesgos-de-regresión)
12. [Plan de Rollback](#12-plan-de-rollback)
13. [Pruebas de No Regresión](#13-pruebas-de-no-regresión)
14. [Apéndices](#14-apéndices)

---

## 1. Resumen Ejecutivo

### 1.1 Objetivo
Implementar un sistema centralizado de resolución de identidad para unidades de negocio en EDARSAHUB, eliminando la dependencia de matching textual y normalizando aliases dispersos.

### 1.2 Alcance
- 5 unidades de negocio canónicas
- ~37 aliases conocidos a normalizar
- 4 módulos críticos a migrar
- 2 tablas nuevas a crear
- 1 helper central (EmpresaResolver)

### 1.3 Impacto
| Área | Impacto | Prioridad |
|------|---------|-----------|
| Comercial/Adapters | CRÍTICO - Matching textual | P0 |
| Sync Jobs | ALTO - Hardcodes | P1 |
| Repository Readonly | MEDIO - LIKE queries | P2 |
| Frontend | BAJO - Display only | P3 |

### 1.4 Prerequisitos
- ✅ `Sistema_Empresas` existe con 5 empresas
- ✅ `Servidores_Conexiones` existe con FK a `Sistema_Empresas`
- ✅ `Unidades_Negocio` existe como catálogo operativo
- ✅ `Sistema_EmpresasMongoMap` existe para transición
- ❌ `Sistema_Tipos` NO existe (crear)

---

## 2. Estado Actual de la Arquitectura

### 2.1 Tablas Existentes Relevantes

```
Sistema_Empresas (5 registros)
├── EmpresaID: 1=ORIGEN, 2=130QRO, 3=CIENFUEGOS, 4=ESTELAR, 5=130MID
├── CodigoEmpresa: ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID
└── NombreComercial: Nombres largos con S.A. de C.V.

Servidores_Conexiones (19 registros, 13 activos)
├── EmpresaID: FK a Sistema_Empresas (parcialmente poblado)
├── tipo_conexion: DATA_SOURCE, API_LOCAL, CORE
└── system_type: MPRO, SoftRestaurant, EDARSA_HUB

Unidades_Negocio (5 registros)
├── codigo: ORIGEN, 130QRO, 130MID, CIENFUEGOS, ESTELAR
├── server_id: UUID del servidor principal
├── sucursal_origen_id: 0023(ORIGEN), 0021(130QRO), NULL(otros)
└── system_type: MPRO, SoftRestaurant
```

### 2.2 Relaciones Existentes

```
[Sistema_Empresas]
       ↑
       │ FK (EmpresaID)
       │
[Servidores_Conexiones] ←── FK ──→ [Sistema_EmpresasMongoMap]
       │
       │ (server_id referenciado por texto)
       ↓
[Unidades_Negocio]
```

### 2.3 Brechas Identificadas

| Brecha | Descripción | Solución Propuesta |
|--------|-------------|-------------------|
| Sin tabla de aliases | Aliases dispersos en código | `Sistema_EmpresasAlias` |
| Sin mapeo empresa-servidor formalizado | `EmpresaID` en `Servidores_Conexiones` parcial | `Sistema_EmpresasServidores` |
| Sin catálogo de tipos de sistema | `system_type` como texto libre | `Sistema_Tipos` |
| Matching textual | `sucursal_destino in sucursal_actual` | `EmpresaResolver` |

---

## 3. DDL: Sistema_Tipos

### 3.1 Justificación
Actualmente `system_type` es un campo de texto libre con variantes:
- `MPRO`, `ManagementPro`, `MANAGEMENTPRO`
- `SoftRestaurant`, `SR`, `SOFTRESTAURANT`
- `EDARSA_HUB`, `Otro`

### 3.2 Definición

```sql
-- ============================================================================
-- TABLA: Sistema_Tipos
-- Catálogo de tipos de sistema (MPRO, SoftRestaurant, etc.)
-- 
-- NO EJECUTAR SIN AUTORIZACIÓN
-- ============================================================================

CREATE TABLE Sistema_Tipos (
    TipoID INT IDENTITY(1,1) PRIMARY KEY,
    
    -- Identificación
    Codigo VARCHAR(20) NOT NULL,          -- MPRO, SOFTRESTAURANT, EDARSA_HUB
    Nombre NVARCHAR(100) NOT NULL,        -- Management Pro, SoftRestaurant
    Descripcion NVARCHAR(500) NULL,
    
    -- Aliases conocidos (para migración)
    AliasesJSON NVARCHAR(MAX) NULL,       -- ["MPRO","ManagementPro","MANAGEMENTPRO"]
    
    -- Características
    SoportaSucursales BIT NOT NULL DEFAULT 1,  -- MPRO=1, SR=0
    SoportaAPILocal BIT NOT NULL DEFAULT 0,
    QueryTemplateVentas NVARCHAR(MAX) NULL,
    QueryTemplateInventario NVARCHAR(MAX) NULL,
    
    -- Auditoría
    Activo BIT NOT NULL DEFAULT 1,
    FechaCreacion DATETIME2 DEFAULT SYSUTCDATETIME(),
    FechaModificacion DATETIME2 NULL,
    CreatedBy VARCHAR(100) NULL,
    UpdatedBy VARCHAR(100) NULL,
    
    -- Restricciones
    CONSTRAINT UQ_Sistema_Tipos_Codigo UNIQUE (Codigo)
);

-- Índice para búsqueda por código
CREATE INDEX IX_Sistema_Tipos_Codigo ON Sistema_Tipos(Codigo) WHERE Activo = 1;
```

### 3.3 Datos Iniciales

```sql
-- NO EJECUTAR SIN AUTORIZACIÓN

INSERT INTO Sistema_Tipos (Codigo, Nombre, Descripcion, AliasesJSON, SoportaSucursales, SoportaAPILocal)
VALUES 
    ('MPRO', 'Management Pro', 'Sistema de punto de venta Management Pro', 
     '["MPRO","ManagementPro","MANAGEMENTPRO","ManagmentPro"]', 1, 1),
    
    ('SOFTRESTAURANT', 'SoftRestaurant', 'Sistema de punto de venta SoftRestaurant/NationalSoft',
     '["SoftRestaurant","SOFTRESTAURANT","SR","NationalSoft"]', 0, 1),
    
    ('EDARSA_HUB', 'EDARSA HUB', 'Sistema central EDARSA HUB',
     '["EDARSA_HUB","EDARSAHUB","Otro"]', 0, 0);
```

---

## 4. DDL: Sistema_EmpresasAlias

### 4.1 Justificación
Centralizar todos los aliases conocidos para cada empresa, permitiendo:
- Resolución única: cualquier alias → EmpresaID
- Normalización automática mediante columna computada
- Auditoría del origen de cada alias

### 4.2 Definición

```sql
-- ============================================================================
-- TABLA: Sistema_EmpresasAlias
-- Catálogo centralizado de aliases por empresa
--
-- REGLA: Usar AliasNormalizado solo para resolución, NUNCA como llave de negocio
-- La llave de negocio es EmpresaID
--
-- NO EJECUTAR SIN AUTORIZACIÓN
-- ============================================================================

CREATE TABLE Sistema_EmpresasAlias (
    AliasID INT IDENTITY(1,1) PRIMARY KEY,
    
    -- Relación con empresa
    EmpresaID INT NOT NULL,
    
    -- El alias original tal como se encontró
    Alias NVARCHAR(100) NOT NULL,
    
    -- Alias normalizado (computado, persistido para índice)
    -- Reglas: UPPER + sin acentos + sin símbolos + sin espacios
    AliasNormalizado AS (
        UPPER(
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                Alias,
                'Á','A'), 'É','E'), 'Í','I'), 'Ó','O'), 'Ú','U'),
                'á','A'), 'é','E'), 'í','I'), 'ó','O'), 'ú','U'),
                '°',''), '-',''), ' ','')
            )
        )
    ) PERSISTED,
    
    -- Clasificación del alias
    TipoAlias VARCHAR(30) NOT NULL,
    -- Valores permitidos:
    -- CODIGO_CANONICO: El código oficial (ORIGEN, 130QRO)
    -- NOMBRE_VISIBLE: Nombre para UI (Origen, 130 Grados Querétaro)
    -- NOMBRE_SISTEMA: Nombre en sistemas externos (130° QUERETARO)
    -- CODIGO_LEGACY: Códigos de versiones anteriores (130-QRO, 130_qro)
    -- API_KEY: Identificador en APIs locales (QUERETARO, origen)
    -- SUCURSAL_NOMBRE: Nombre en tablas de sucursales (CIEN FUEGOS)
    -- MONGO_ID: ID o nombre en MongoDB
    
    -- Origen del alias
    OrigenAlias VARCHAR(100) NULL,
    -- Ejemplos: MongoDB.empresas, Frontend, adapters.py, sync_job.py
    
    -- Contexto
    Observaciones NVARCHAR(500) NULL,
    
    -- Estado
    Activo BIT NOT NULL DEFAULT 1,
    EsPrincipal BIT NOT NULL DEFAULT 0,  -- Solo 1 por empresa puede ser principal
    
    -- Auditoría
    FechaCreacion DATETIME2 DEFAULT SYSUTCDATETIME(),
    FechaModificacion DATETIME2 NULL,
    CreatedBy VARCHAR(100) NULL,
    UpdatedBy VARCHAR(100) NULL,
    
    -- Restricciones
    CONSTRAINT FK_EmpresasAlias_Empresa 
        FOREIGN KEY (EmpresaID) REFERENCES Sistema_Empresas(EmpresaID),
    
    -- Unicidad: Un alias normalizado solo puede pertenecer a una empresa
    CONSTRAINT UQ_EmpresasAlias_Normalizado UNIQUE (AliasNormalizado)
);

-- Índices para búsqueda eficiente
CREATE INDEX IX_EmpresasAlias_EmpresaID ON Sistema_EmpresasAlias(EmpresaID) WHERE Activo = 1;
CREATE INDEX IX_EmpresasAlias_TipoAlias ON Sistema_EmpresasAlias(TipoAlias) WHERE Activo = 1;
CREATE INDEX IX_EmpresasAlias_Normalizado ON Sistema_EmpresasAlias(AliasNormalizado) WHERE Activo = 1;

-- Índice único para empresa principal
CREATE UNIQUE INDEX UQ_EmpresasAlias_Principal 
    ON Sistema_EmpresasAlias(EmpresaID) 
    WHERE EsPrincipal = 1 AND Activo = 1;
```

### 4.3 Ejemplo de Normalización

| Alias Original | AliasNormalizado | Resultado |
|----------------|------------------|-----------|
| `130° QUERÉTARO` | `130QUERETARO` | ✓ |
| `130-QRO` | `130QRO` | ✓ |
| `130 QRO` | `130QRO` | ✓ |
| `LA ESTELAR` | `LAESTELAR` | ✓ |
| `CIENFUEGOS` | `CIENFUEGOS` | ✓ |

---

## 5. DDL: Sistema_EmpresasServidores

### 5.1 Justificación
Formalizar la relación empresa-servidor con roles específicos:
- DATA_SOURCE: Servidor principal de datos
- API_LOCAL_VENTAS: API para ventas del día
- API_LOCAL_INVENTARIO: API para inventarios
- REPLICA: Servidor de réplica

### 5.2 Definición

```sql
-- ============================================================================
-- TABLA: Sistema_EmpresasServidores
-- Mapeo formal entre empresas y servidores con roles
--
-- REGLA MPRO: ORIGEN=suc23, 130QRO=suc21, NO resolver por nombre de servidor
-- REGLA SR: sucursal NULL salvo evidencia contraria
-- REGLA API_LOCAL: asociar por EmpresaID + RolConexion
--
-- NO EJECUTAR SIN AUTORIZACIÓN
-- ============================================================================

CREATE TABLE Sistema_EmpresasServidores (
    MapeoID INT IDENTITY(1,1) PRIMARY KEY,
    
    -- Relaciones
    EmpresaID INT NOT NULL,
    ServidorID UNIQUEIDENTIFIER NOT NULL,
    
    -- Rol del servidor para esta empresa
    RolConexion VARCHAR(30) NOT NULL,
    -- Valores permitidos:
    -- DATA_SOURCE: Servidor principal para consultas
    -- API_LOCAL_VENTAS: API local para ventas del día
    -- API_LOCAL_INVENTARIO: API local para inventarios
    -- API_LOCAL_BACKOFFICE: API local para backoffice
    -- REPLICA: Servidor de réplica
    -- TABLAJERIA: Servidor de tablajería relacionada
    
    -- Configuración específica MPRO
    NumSucursalSistema VARCHAR(10) NULL,  -- 0021, 0023, NULL para SR
    SucursalNombre NVARCHAR(100) NULL,    -- Nombre descriptivo
    
    -- Prioridad (para ordenamiento cuando hay múltiples)
    Prioridad INT NOT NULL DEFAULT 100,
    EsPrincipal BIT NOT NULL DEFAULT 0,
    
    -- Estado
    Activo BIT NOT NULL DEFAULT 1,
    
    -- Auditoría
    FechaCreacion DATETIME2 DEFAULT SYSUTCDATETIME(),
    FechaModificacion DATETIME2 NULL,
    CreatedBy VARCHAR(100) NULL,
    UpdatedBy VARCHAR(100) NULL,
    Observaciones NVARCHAR(500) NULL,
    
    -- Restricciones
    CONSTRAINT FK_EmpresasServidores_Empresa 
        FOREIGN KEY (EmpresaID) REFERENCES Sistema_Empresas(EmpresaID),
    CONSTRAINT FK_EmpresasServidores_Servidor 
        FOREIGN KEY (ServidorID) REFERENCES Servidores_Conexiones(id),
    
    -- Unicidad: Una empresa no puede tener el mismo servidor con el mismo rol dos veces
    CONSTRAINT UQ_EmpresasServidores_EmpresaServidorRol 
        UNIQUE (EmpresaID, ServidorID, RolConexion)
);

-- Índices
CREATE INDEX IX_EmpresasServidores_EmpresaID 
    ON Sistema_EmpresasServidores(EmpresaID) WHERE Activo = 1;
CREATE INDEX IX_EmpresasServidores_ServidorID 
    ON Sistema_EmpresasServidores(ServidorID) WHERE Activo = 1;
CREATE INDEX IX_EmpresasServidores_Rol 
    ON Sistema_EmpresasServidores(RolConexion) WHERE Activo = 1;

-- Índice único para servidor principal por empresa
CREATE UNIQUE INDEX UQ_EmpresasServidores_Principal 
    ON Sistema_EmpresasServidores(EmpresaID, RolConexion) 
    WHERE EsPrincipal = 1 AND Activo = 1;
```

---

## 6. Compatibilidad con Tablas Existentes

### 6.1 Sistema_Empresas
| Aspecto | Estado | Acción |
|---------|--------|--------|
| Estructura | ✅ Compatible | Ninguna |
| Datos | ✅ 5 empresas | Usar como referencia |
| FK | ✅ Usada por otras tablas | Agregar nueva FK |

### 6.2 Servidores_Conexiones
| Aspecto | Estado | Acción |
|---------|--------|--------|
| Columna EmpresaID | ✅ Existe | Mantener para compatibilidad |
| FK a Sistema_Empresas | ✅ Existe | Mantener |
| Datos | ⚠️ Parcialmente poblado | Completar vía Sistema_EmpresasServidores |

### 6.3 Unidades_Negocio
| Aspecto | Estado | Acción |
|---------|--------|--------|
| Estructura | ✅ Completa | Ninguna |
| Datos | ✅ 5 unidades | Usar como referencia |
| Sin FK a Sistema_Empresas | ⚠️ Brecha | Agregar columna EmpresaID (futuro) |

### 6.4 Plan de Coexistencia

```
FASE 1 (Actual):
[Sistema_Empresas] ← FK ← [Servidores_Conexiones.EmpresaID]
                  ← FK ← [Sistema_EmpresasMongoMap]

FASE 2 (Propuesta):
[Sistema_Empresas] ← FK ← [Servidores_Conexiones.EmpresaID] (mantener)
                  ← FK ← [Sistema_EmpresasMongoMap] (mantener)
                  ← FK ← [Sistema_EmpresasAlias] (NUEVO)
                  ← FK ← [Sistema_EmpresasServidores] (NUEVO)
                  
[Servidores_Conexiones] ← FK ← [Sistema_EmpresasServidores.ServidorID] (NUEVO)
```

---

## 7. Script de Carga Inicial de Aliases

### 7.1 Aliases para ORIGEN (EmpresaID=1)

```sql
-- NO EJECUTAR SIN AUTORIZACIÓN

-- ORIGEN: EmpresaID = 1
INSERT INTO Sistema_EmpresasAlias 
    (EmpresaID, Alias, TipoAlias, OrigenAlias, EsPrincipal, Observaciones)
VALUES
    -- Código canónico
    (1, 'ORIGEN', 'CODIGO_CANONICO', 'Sistema_Empresas', 1, 'Código oficial'),
    
    -- Variantes de caso
    (1, 'Origen', 'NOMBRE_VISIBLE', 'Frontend', 0, 'Display en UI'),
    (1, 'origen', 'API_KEY', 'sync_comercial_abiertas_v2_job.py', 0, 'Clave en MPRO_API_LOCAL_CONFIG'),
    
    -- Nombre de servidor
    (1, 'ORIGEN LOCAL', 'NOMBRE_SISTEMA', 'Servidores_Conexiones', 0, 'Nombre del servidor API_LOCAL');
```

### 7.2 Aliases para 130QRO (EmpresaID=2)

```sql
-- NO EJECUTAR SIN AUTORIZACIÓN

-- 130QRO: EmpresaID = 2
INSERT INTO Sistema_EmpresasAlias 
    (EmpresaID, Alias, TipoAlias, OrigenAlias, EsPrincipal, Observaciones)
VALUES
    -- Código canónico
    (2, '130QRO', 'CODIGO_CANONICO', 'Sistema_Empresas', 1, 'Código oficial'),
    
    -- Variantes legacy
    (2, '130-QRO', 'CODIGO_LEGACY', 'carga_historica_abril_2026.py', 0, 'Formato con guión'),
    (2, '130_qro', 'API_KEY', 'sync_comercial_abiertas_v2_job.py', 0, 'Clave en MPRO_API_LOCAL_CONFIG'),
    (2, '130 QRO', 'NOMBRE_SISTEMA', 'MongoDB.empresas', 0, 'Nombre en MongoDB'),
    
    -- Nombres con símbolo
    (2, '130° QRO', 'NOMBRE_VISIBLE', 'Frontend', 0, 'Display corto'),
    (2, '130° QUERETARO', 'SUCURSAL_NOMBRE', 'server_sucursales_config', 0, 'Nombre de sucursal MPRO'),
    (2, '130° QRO LOCAL', 'NOMBRE_SISTEMA', 'Servidores_Conexiones', 0, 'Nombre del servidor API_LOCAL'),
    
    -- Variantes de ciudad
    (2, 'QUERETARO', 'API_KEY', 'api_connections_cache.sucursal_destino', 0, 'Clave de destino API'),
    (2, 'QUERÉTARO', 'NOMBRE_SISTEMA', 'queries/softrestaurant.py', 0, 'Con acento'),
    
    -- Nombre comercial
    (2, '130 Grados Querétaro', 'NOMBRE_VISIBLE', 'Sistema_Empresas.NombreComercial', 0, 'Nombre comercial');
```

### 7.3 Aliases para 130MID (EmpresaID=5)

```sql
-- NO EJECUTAR SIN AUTORIZACIÓN

-- 130MID: EmpresaID = 5
INSERT INTO Sistema_EmpresasAlias 
    (EmpresaID, Alias, TipoAlias, OrigenAlias, EsPrincipal, Observaciones)
VALUES
    -- Código canónico
    (5, '130MID', 'CODIGO_CANONICO', 'Sistema_Empresas', 1, 'Código oficial'),
    
    -- Variantes legacy
    (5, '130-MER', 'CODIGO_LEGACY', 'service.py', 0, 'Formato legacy'),
    (5, '130-MID', 'CODIGO_LEGACY', 'repository_readonly.py', 0, 'Variante'),
    (5, '130 MID', 'NOMBRE_SISTEMA', 'MongoDB.empresas', 0, 'Nombre en MongoDB'),
    
    -- Nombres con símbolo
    (5, '130° MERIDA', 'SUCURSAL_NOMBRE', 'MongoDB.servers', 0, 'Sin acento'),
    (5, '130° MÉRIDA', 'NOMBRE_VISIBLE', 'carga_historica_abril_2026.py', 0, 'Con acento'),
    
    -- Variantes de ciudad
    (5, 'MERIDA', 'API_KEY', 'queries/softrestaurant.py', 0, 'Sin acento'),
    (5, 'MÉRIDA', 'NOMBRE_SISTEMA', 'repository_readonly.py', 0, 'Con acento'),
    
    -- Nombre comercial
    (5, '130 Grados Mérida', 'NOMBRE_VISIBLE', 'Sistema_Empresas.NombreComercial', 0, 'Nombre comercial');
```

### 7.4 Aliases para CIENFUEGOS (EmpresaID=3)

```sql
-- NO EJECUTAR SIN AUTORIZACIÓN

-- CIENFUEGOS: EmpresaID = 3
INSERT INTO Sistema_EmpresasAlias 
    (EmpresaID, Alias, TipoAlias, OrigenAlias, EsPrincipal, Observaciones)
VALUES
    -- Código canónico
    (3, 'CIENFUEGOS', 'CODIGO_CANONICO', 'Sistema_Empresas', 1, 'Código oficial'),
    
    -- Variantes de caso
    (3, 'Cienfuegos', 'NOMBRE_VISIBLE', 'rh/importador/service.py', 0, 'Title case'),
    
    -- Variante con espacio
    (3, 'CIEN FUEGOS', 'SUCURSAL_NOMBRE', 'server_sucursales_config', 0, 'Con espacio - sucursal 0027');
```

### 7.5 Aliases para ESTELAR (EmpresaID=4)

```sql
-- NO EJECUTAR SIN AUTORIZACIÓN

-- ESTELAR: EmpresaID = 4
INSERT INTO Sistema_EmpresasAlias 
    (EmpresaID, Alias, TipoAlias, OrigenAlias, EsPrincipal, Observaciones)
VALUES
    -- Código canónico
    (4, 'ESTELAR', 'CODIGO_CANONICO', 'Sistema_Empresas', 1, 'Código oficial'),
    
    -- Variantes con prefijo
    (4, 'LA-ESTELAR', 'CODIGO_LEGACY', 'service.py', 0, 'Formato legacy'),
    (4, 'LA ESTELAR', 'NOMBRE_SISTEMA', 'MongoDB.servers', 0, 'Nombre completo'),
    (4, 'La Estelar', 'NOMBRE_VISIBLE', 'Documentación', 0, 'Title case');
```

### 7.6 Mapeo Empresa-Servidor Inicial

```sql
-- NO EJECUTAR SIN AUTORIZACIÓN

-- ORIGEN: Servidor principal MPRO + API Local
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumSucursalSistema, SucursalNombre, EsPrincipal)
VALUES
    (1, '1b230a06-ffaf-4c70-bd27-b1be3579dea6', 'DATA_SOURCE', '0023', 'ORIGEN', 1),
    (1, '817a0aa8-6170-4738-a8f6-a72ac36ba0df', 'API_LOCAL_VENTAS', '0023', 'ORIGEN LOCAL', 0);

-- 130QRO: Servidor principal MPRO + API Local
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumSucursalSistema, SucursalNombre, EsPrincipal)
VALUES
    (2, '1b230a06-ffaf-4c70-bd27-b1be3579dea6', 'DATA_SOURCE', '0021', '130° QUERETARO', 1),
    (2, '72f6e9a7-8ea2-4eb2-802e-4ee31753435e', 'API_LOCAL_VENTAS', '0021', '130° QRO LOCAL', 0);

-- CIENFUEGOS: Servidor SoftRestaurant + Tablajería
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumSucursalSistema, SucursalNombre, EsPrincipal)
VALUES
    (3, '6d053c22-523e-48c0-b72b-96081e2d781b', 'DATA_SOURCE', NULL, 'CIENFUEGOS', 1),
    (3, '6d859026-710a-4920-9a44-6da98fabc690', 'TABLAJERIA', NULL, 'CIENFUEGOS TABLAJERIA', 0);

-- ESTELAR: Servidor SoftRestaurant
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumSucursalSistema, SucursalNombre, EsPrincipal)
VALUES
    (4, 'a5ff0e25-f029-43db-b634-d4ac814c904f', 'DATA_SOURCE', NULL, 'LA ESTELAR', 1);

-- 130MID: Servidor SoftRestaurant
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumSucursalSistema, SucursalNombre, EsPrincipal)
VALUES
    (5, 'a5547321-1139-4d2b-9d53-182ca737b6b6', 'DATA_SOURCE', NULL, '130° MERIDA', 1);
```

---

## 8. Diseño del Resolver Central

### 8.1 Arquitectura

```
                    ┌─────────────────────────────────────┐
                    │         EmpresaResolver             │
                    │                                     │
  Input: alias ────▶│  1. normalizar_alias(alias)        │
                    │  2. buscar en cache                 │
                    │  3. consultar Sistema_EmpresasAlias │
                    │  4. retornar EmpresaID              │
                    │                                     │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │    Sistema_EmpresasAlias (SQL)      │
                    │                                     │
                    │  AliasNormalizado → EmpresaID       │
                    └─────────────────────────────────────┘
```

### 8.2 Código Propuesto

```python
# /app/backend/core/utils/empresa_resolver.py
# NO IMPLEMENTAR SIN AUTORIZACIÓN

"""
Módulo de Resolución de Empresas para EDARSAHUB.

Este módulo proporciona una función central para resolver cualquier alias,
código o nombre a su EmpresaID canónico.

REGLAS:
- NUNCA usar el alias resuelto como llave de negocio
- SIEMPRE usar EmpresaID para joins y referencias
- El alias solo sirve para la resolución inicial
"""

import unicodedata
import re
import logging
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache
from datetime import datetime, timedelta

from core.db import execute_sql_query

logger = logging.getLogger(__name__)

# Configuración EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'HRLectura',
    'password': 'National09$'
}

# Cache en memoria
_cache: Dict[str, int] = {}
_cache_timestamp: Optional[datetime] = None
_CACHE_TTL_MINUTES = 60


def normalizar_alias(alias: str) -> str:
    """
    Normaliza un alias para búsqueda.
    
    Reglas:
    1. Convertir a mayúsculas
    2. Quitar acentos (NFD + filtrar)
    3. Quitar símbolos (°, -, _, .)
    4. Quitar espacios
    
    Args:
        alias: El alias original
    
    Returns:
        Alias normalizado para búsqueda
    
    Examples:
        >>> normalizar_alias("130° QUERÉTARO")
        '130QUERETARO'
        >>> normalizar_alias("LA ESTELAR")
        'LAESTELAR'
        >>> normalizar_alias("130-QRO")
        '130QRO'
    """
    if not alias:
        return ""
    
    # 1. Mayúsculas
    resultado = alias.upper()
    
    # 2. Normalizar Unicode y quitar acentos
    resultado = unicodedata.normalize('NFD', resultado)
    resultado = ''.join(c for c in resultado if unicodedata.category(c) != 'Mn')
    
    # 3. Quitar símbolos específicos
    resultado = resultado.replace('°', '')
    resultado = resultado.replace('-', '')
    resultado = resultado.replace('_', '')
    resultado = resultado.replace('.', '')
    
    # 4. Quitar espacios
    resultado = ''.join(resultado.split())
    
    return resultado


def _cargar_cache():
    """Carga el cache desde Sistema_EmpresasAlias."""
    global _cache, _cache_timestamp
    
    query = """
    SELECT AliasNormalizado, EmpresaID
    FROM Sistema_EmpresasAlias
    WHERE Activo = 1
    """
    
    try:
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        _cache = {r['AliasNormalizado']: r['EmpresaID'] for r in results}
        _cache_timestamp = datetime.now()
        
        logger.info(f"[EMPRESA_RESOLVER] Cache cargado: {len(_cache)} aliases")
        
    except Exception as e:
        logger.error(f"[EMPRESA_RESOLVER] Error cargando cache: {e}")


def _cache_valido() -> bool:
    """Verifica si el cache sigue válido."""
    if _cache_timestamp is None:
        return False
    return (datetime.now() - _cache_timestamp).total_seconds() < _CACHE_TTL_MINUTES * 60


def resolver_empresa_id(alias: str) -> Optional[int]:
    """
    Resuelve un alias a su EmpresaID.
    
    Esta es la función principal que DEBE usarse para resolver
    cualquier identificador de empresa a su ID canónico.
    
    Args:
        alias: Cualquier forma de identificar la empresa
               (código, nombre, variante, etc.)
    
    Returns:
        EmpresaID (int) si se encuentra, None si no
    
    Examples:
        >>> resolver_empresa_id("130° QUERÉTARO")
        2
        >>> resolver_empresa_id("QUERETARO")
        2
        >>> resolver_empresa_id("130-QRO")
        2
        >>> resolver_empresa_id("CIENFUEGOS")
        3
    """
    if not alias:
        logger.warning("[EMPRESA_RESOLVER] Alias vacío recibido")
        return None
    
    # Normalizar
    alias_norm = normalizar_alias(alias)
    
    if not alias_norm:
        logger.warning(f"[EMPRESA_RESOLVER] Alias normalizado vacío para: {alias}")
        return None
    
    # Verificar/cargar cache
    if not _cache_valido():
        _cargar_cache()
    
    # Buscar en cache
    if alias_norm in _cache:
        empresa_id = _cache[alias_norm]
        logger.debug(f"[EMPRESA_RESOLVER] {alias} -> {alias_norm} -> EmpresaID={empresa_id}")
        return empresa_id
    
    # No encontrado
    logger.warning(
        f"[EMPRESA_RESOLVER] Alias no encontrado: {alias} (normalizado: {alias_norm}). "
        f"Considere agregar a Sistema_EmpresasAlias."
    )
    return None


def resolver_empresa_completa(alias: str) -> Optional[Dict[str, Any]]:
    """
    Resuelve un alias y retorna información completa de la empresa.
    
    Args:
        alias: Cualquier forma de identificar la empresa
    
    Returns:
        Dict con EmpresaID, CodigoEmpresa, NombreEmpresa, etc.
        o None si no se encuentra
    """
    empresa_id = resolver_empresa_id(alias)
    
    if empresa_id is None:
        return None
    
    query = f"""
    SELECT 
        EmpresaID,
        CodigoEmpresa,
        NombreEmpresa,
        NombreComercial,
        Activo
    FROM Sistema_Empresas
    WHERE EmpresaID = {empresa_id}
    """
    
    try:
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        if results:
            return results[0]
        
    except Exception as e:
        logger.error(f"[EMPRESA_RESOLVER] Error consultando empresa {empresa_id}: {e}")
    
    return None


def obtener_servidor_empresa(
    empresa_id: int, 
    rol: str = 'DATA_SOURCE'
) -> Optional[Dict[str, Any]]:
    """
    Obtiene el servidor asociado a una empresa para un rol específico.
    
    Args:
        empresa_id: ID de la empresa
        rol: Rol del servidor (DATA_SOURCE, API_LOCAL_VENTAS, etc.)
    
    Returns:
        Dict con información del servidor o None
    """
    query = f"""
    SELECT 
        es.ServidorID,
        es.RolConexion,
        es.NumSucursalSistema,
        es.SucursalNombre,
        es.EsPrincipal,
        sc.nombre AS ServidorNombre,
        sc.system_type,
        sc.tipo_conexion,
        sc.api_url,
        sc.host
    FROM Sistema_EmpresasServidores es
    INNER JOIN Servidores_Conexiones sc ON es.ServidorID = sc.id
    WHERE es.EmpresaID = {empresa_id}
      AND es.RolConexion = '{rol}'
      AND es.Activo = 1
      AND sc.activo = 1
    ORDER BY es.EsPrincipal DESC, es.Prioridad ASC
    """
    
    try:
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        if results:
            return results[0]
        
    except Exception as e:
        logger.error(f"[EMPRESA_RESOLVER] Error obteniendo servidor para empresa {empresa_id}: {e}")
    
    return None


def invalidar_cache():
    """Fuerza recarga del cache."""
    global _cache_timestamp
    _cache_timestamp = None
    logger.info("[EMPRESA_RESOLVER] Cache invalidado")


# Mapeo directo para compatibilidad (deprecar gradualmente)
MAPEO_LEGACY = {
    'ORIGEN': 1,
    '130QRO': 2,
    'CIENFUEGOS': 3,
    'ESTELAR': 4,
    '130MID': 5,
}
```

### 8.3 Uso del Resolver

```python
# EJEMPLO DE USO (NO EJECUTAR SIN IMPLEMENTAR TABLAS)

from core.utils.empresa_resolver import resolver_empresa_id, obtener_servidor_empresa

# Resolver cualquier alias a EmpresaID
empresa_id = resolver_empresa_id("130° QUERÉTARO")  # → 2
empresa_id = resolver_empresa_id("QUERETARO")       # → 2
empresa_id = resolver_empresa_id("130-QRO")         # → 2

# Obtener servidor para ventas del día
servidor = obtener_servidor_empresa(empresa_id, rol='API_LOCAL_VENTAS')
# → {'ServidorID': '72f6e9a7-...', 'api_url': 'http://...', 'NumSucursalSistema': '0021'}
```

---

## 9. Reglas de Negocio por Sistema

### 9.1 Reglas MPRO

```
┌─────────────────────────────────────────────────────────────────────────┐
│ REGLA MPRO-001: Identificación por Sucursal Sistema                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ORIGEN   = NumSucursalSistema '0023'                                  │
│  130QRO   = NumSucursalSistema '0021'                                  │
│                                                                         │
│  ⚠️ NO resolver por nombre de servidor                                  │
│  ⚠️ NO asumir que servidor "ManagmentPro" = una empresa específica      │
│  ⚠️ El servidor MPRO central es compartido por múltiples empresas       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Implementación:**

```python
# CORRECTO
def obtener_empresa_mpro(servidor_id: str, num_sucursal: str) -> int:
    # Buscar en Sistema_EmpresasServidores por NumSucursalSistema
    servidor = obtener_servidor_empresa_por_sucursal(servidor_id, num_sucursal)
    return servidor['EmpresaID']

# INCORRECTO (NO HACER)
def obtener_empresa_mpro_incorrecto(servidor_id: str) -> int:
    # ❌ Asumir empresa por nombre de servidor
    if "ManagmentPro" in servidor_nombre:
        return ???  # ¿ORIGEN o 130QRO?
```

### 9.2 Reglas SoftRestaurant

```
┌─────────────────────────────────────────────────────────────────────────┐
│ REGLA SR-001: Sucursal Sistema NULL                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CIENFUEGOS = NumSucursalSistema NULL                                  │
│  ESTELAR    = NumSucursalSistema NULL                                  │
│  130MID     = NumSucursalSistema NULL                                  │
│                                                                         │
│  ✓ SoftRestaurant es single-tenant                                      │
│  ✓ Un servidor = Una empresa                                            │
│  ✓ Resolver por ServidorID directo                                      │
│                                                                         │
│  ⚠️ Si aparece NumSucursalSistema != NULL, documentar evidencia         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.3 Reglas API Local

```
┌─────────────────────────────────────────────────────────────────────────┐
│ REGLA API-001: Asociación por EmpresaID + RolConexion                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Para encontrar la API local de ventas de una empresa:                  │
│                                                                         │
│  SELECT ServidorID, api_url                                            │
│  FROM Sistema_EmpresasServidores es                                    │
│  JOIN Servidores_Conexiones sc ON es.ServidorID = sc.id                │
│  WHERE es.EmpresaID = @EmpresaID                                       │
│    AND es.RolConexion = 'API_LOCAL_VENTAS'                             │
│    AND es.Activo = 1                                                   │
│                                                                         │
│  ❌ NO resolver por sucursal_destino in sucursal_actual                 │
│  ❌ NO usar matching textual                                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Mapeo API Local:**

| EmpresaID | Empresa | API Local | URL |
|-----------|---------|-----------|-----|
| 1 | ORIGEN | ORIGEN LOCAL | http://54.39.104.176:8000/query |
| 2 | 130QRO | 130° QRO LOCAL | http://54.39.104.176:8001/query |

---

## 10. Plan de Migración Gradual

### Fase 0: Preparación (Sin cambios funcionales)
**Duración estimada:** 1 día

| Tarea | Archivo | Riesgo |
|-------|---------|--------|
| Crear `Sistema_Tipos` | DDL | Ninguno |
| Crear `Sistema_EmpresasAlias` | DDL | Ninguno |
| Crear `Sistema_EmpresasServidores` | DDL | Ninguno |
| Cargar datos iniciales | INSERT | Ninguno |
| Crear `empresa_resolver.py` (sin usar) | Python | Ninguno |

### Fase 1: Sync Jobs (Crítico)
**Duración estimada:** 1 día

| Tarea | Archivo | Riesgo |
|-------|---------|--------|
| Reemplazar `MPRO_API_LOCAL_CONFIG` | `sync_comercial_abiertas_v2_job.py` | MEDIO |
| Usar `obtener_servidor_empresa()` | `sync_comercial_abiertas_v2_job.py` | MEDIO |
| Validar que jobs funcionan igual | Tests | - |

**Código a modificar:**
```python
# ANTES (hardcoded)
MPRO_API_LOCAL_CONFIG = {
    "ORIGEN": {"server_config_name": "ORIGEN LOCAL", "sucursal_id": "0001"},
    "130QRO": {"server_config_name": "130° QRO LOCAL", "sucursal_id": "0021"},
}

# DESPUÉS (desde BD)
def obtener_config_api_local(empresa_id: int) -> dict:
    servidor = obtener_servidor_empresa(empresa_id, rol='API_LOCAL_VENTAS')
    return {
        'server_id': servidor['ServidorID'],
        'api_url': servidor['api_url'],
        'sucursal_id': servidor['NumSucursalSistema']
    }
```

### Fase 2: Adapters (CRÍTICO)
**Duración estimada:** 2 días

| Tarea | Archivo | Riesgo |
|-------|---------|--------|
| Reemplazar matching textual | `adapters.py:306` | CRÍTICO |
| Reemplazar matching textual | `adapters.py:363` | CRÍTICO |
| Usar `resolver_empresa_id()` | `adapters.py` | CRÍTICO |
| Validar APIs locales | Tests | - |

**Código a modificar:**
```python
# ANTES (matching textual PELIGROSO)
if sucursal_destino in sucursal_actual or sucursal_actual in sucursal_destino:
    # Match

# DESPUÉS (resolver por ID)
empresa_destino = resolver_empresa_id(sucursal_destino)
empresa_actual = resolver_empresa_id(sucursal_actual)
if empresa_destino and empresa_destino == empresa_actual:
    # Match exacto por ID
```

### Fase 3: Repository Readonly (MEDIO)
**Duración estimada:** 1 día

| Tarea | Archivo | Riesgo |
|-------|---------|--------|
| Reemplazar `LIKE '%texto%'` | `repository_readonly.py` | MEDIO |
| Normalizar antes de comparar | `repository_readonly.py` | MEDIO |

### Fase 4: Queries MPRO (ALTO)
**Duración estimada:** 1 día

| Tarea | Archivo | Riesgo |
|-------|---------|--------|
| Reemplazar `LIKE '%sucursal%'` | `mpro.py:322` | ALTO |
| Reemplazar `LIKE '%sucursal%'` | `mpro.py:466` | ALTO |
| Usar filtro por ID | `mpro.py` | ALTO |

### Fase 5: Limpieza (BAJO)
**Duración estimada:** Continuo

| Tarea | Riesgo |
|-------|--------|
| Eliminar hardcodes obsoletos | BAJO |
| Documentar nuevos aliases encontrados | Ninguno |
| Agregar aliases faltantes a BD | Ninguno |

---

## 11. Riesgos de Regresión

### 11.1 Matriz de Riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R1 | Alias no encontrado en BD | Media | ALTO | Fallback a MAPEO_LEGACY |
| R2 | Cache desactualizado | Baja | Medio | TTL + invalidación manual |
| R3 | Normalización incorrecta | Baja | ALTO | Tests exhaustivos |
| R4 | FK viola integridad | Baja | ALTO | Validar antes de INSERT |
| R5 | Colisión de aliases | Muy baja | CRÍTICO | UNIQUE constraint |
| R6 | Performance cache | Baja | Medio | Índices optimizados |

### 11.2 Riesgos por Módulo

| Módulo | Riesgo Principal | Plan |
|--------|-----------------|------|
| Tablero Ejecutivo | R1: Alias nuevo | Agregar a BD antes de producción |
| Comercial | R3: Normalización | Tests con datos reales |
| Sync Jobs | R1: Config faltante | Validar todas las empresas |
| Adapters | R5: Falso positivo | Tests de matching |

---

## 12. Plan de Rollback

### 12.1 Rollback DDL

```sql
-- SOLO SI ES NECESARIO REVERTIR

-- 1. Eliminar datos
DELETE FROM Sistema_EmpresasServidores;
DELETE FROM Sistema_EmpresasAlias;
DELETE FROM Sistema_Tipos;

-- 2. Eliminar tablas (orden inverso por FK)
DROP TABLE IF EXISTS Sistema_EmpresasServidores;
DROP TABLE IF EXISTS Sistema_EmpresasAlias;
DROP TABLE IF EXISTS Sistema_Tipos;
```

### 12.2 Rollback Código

| Archivo | Acción |
|---------|--------|
| `empresa_resolver.py` | Eliminar archivo |
| `sync_comercial_abiertas_v2_job.py` | Restaurar `MPRO_API_LOCAL_CONFIG` |
| `adapters.py` | Restaurar matching textual |
| `repository_readonly.py` | Restaurar `LIKE` queries |

### 12.3 Checkpoints de Git

```bash
# Antes de cada fase, crear tag
git tag -a "pre-fase-X-empresas-alias" -m "Checkpoint antes de Fase X"

# Si falla, revertir
git checkout pre-fase-X-empresas-alias
```

---

## 13. Pruebas de No Regresión

### 13.1 Pruebas de Normalización

```python
# /app/backend/tests/test_empresa_resolver.py

import pytest
from core.utils.empresa_resolver import normalizar_alias, resolver_empresa_id

class TestNormalizacion:
    
    @pytest.mark.parametrize("alias,esperado", [
        ("130° QUERÉTARO", "130QUERETARO"),
        ("130-QRO", "130QRO"),
        ("130_qro", "130QRO"),
        ("130 QRO", "130QRO"),
        ("LA ESTELAR", "LAESTELAR"),
        ("CIENFUEGOS", "CIENFUEGOS"),
        ("CIEN FUEGOS", "CIENFUEGOS"),
        ("MÉRIDA", "MERIDA"),
        ("origen", "ORIGEN"),
    ])
    def test_normalizar_alias(self, alias, esperado):
        assert normalizar_alias(alias) == esperado
    
    def test_normalizar_alias_vacio(self):
        assert normalizar_alias("") == ""
        assert normalizar_alias(None) == ""
```

### 13.2 Pruebas de Resolución

```python
class TestResolucion:
    
    @pytest.mark.parametrize("alias,empresa_id_esperado", [
        # ORIGEN
        ("ORIGEN", 1),
        ("origen", 1),
        ("Origen", 1),
        ("ORIGEN LOCAL", 1),
        
        # 130QRO
        ("130QRO", 2),
        ("130-QRO", 2),
        ("130° QUERÉTARO", 2),
        ("QUERETARO", 2),
        ("130° QRO LOCAL", 2),
        
        # CIENFUEGOS
        ("CIENFUEGOS", 3),
        ("Cienfuegos", 3),
        ("CIEN FUEGOS", 3),
        
        # ESTELAR
        ("ESTELAR", 4),
        ("LA ESTELAR", 4),
        ("LA-ESTELAR", 4),
        
        # 130MID
        ("130MID", 5),
        ("130° MÉRIDA", 5),
        ("MERIDA", 5),
    ])
    def test_resolver_empresa_id(self, alias, empresa_id_esperado):
        assert resolver_empresa_id(alias) == empresa_id_esperado
    
    def test_alias_no_encontrado(self):
        assert resolver_empresa_id("EMPRESA_INEXISTENTE") is None
```

### 13.3 Pruebas de Integración

```python
class TestIntegracion:
    
    def test_sync_job_origen(self):
        """Verificar que sync job resuelve ORIGEN correctamente."""
        # 1. Resolver empresa
        empresa_id = resolver_empresa_id("ORIGEN")
        assert empresa_id == 1
        
        # 2. Obtener servidor API Local
        servidor = obtener_servidor_empresa(empresa_id, 'API_LOCAL_VENTAS')
        assert servidor is not None
        assert servidor['NumSucursalSistema'] == '0023'
        assert 'http://' in servidor['api_url']
    
    def test_sync_job_qro(self):
        """Verificar que sync job resuelve 130QRO correctamente."""
        empresa_id = resolver_empresa_id("130QRO")
        assert empresa_id == 2
        
        servidor = obtener_servidor_empresa(empresa_id, 'API_LOCAL_VENTAS')
        assert servidor is not None
        assert servidor['NumSucursalSistema'] == '0021'
    
    def test_adapters_no_falso_positivo(self):
        """Verificar que CIENFUEGOS != CIENFUEGOS TABLAJERIA."""
        emp1 = resolver_empresa_id("CIENFUEGOS")
        emp2 = resolver_empresa_id("CIENFUEGOS TABLAJERIA")
        
        # Ambos deben resolver a la misma empresa (3)
        # porque TABLAJERIA es un servidor relacionado, no otra empresa
        assert emp1 == emp2 == 3
```

### 13.4 Pruebas de Ventas del Día

```bash
# Verificar que después de migración, ventas del día siguen funcionando

# 1. Ejecutar sync job manualmente
python -c "
import asyncio
from core.scheduler.jobs.sync_comercial_abiertas_v2_job import execute_sync_comercial_abiertas_v2
asyncio.run(execute_sync_comercial_abiertas_v2())
"

# 2. Verificar datos en SQL
SELECT unidad_negocio_id, total_estimado_dia, snapshot_timestamp
FROM Comercial_Ventas_Dia_Abiertas_v2
ORDER BY snapshot_timestamp DESC;

# 3. Verificar endpoint
curl -X GET "https://HOST/api/v2/comercial/ventas-dia" -H "Authorization: Bearer TOKEN"

# Criterios de éxito:
# - 5 unidades con datos
# - total_estimado_dia > 0 para unidades activas
# - No errores en logs
```

---

## 14. Apéndices

### A. Inventario Completo de Aliases

| EmpresaID | Alias | Normalizado | Tipo | Origen |
|-----------|-------|-------------|------|--------|
| 1 | ORIGEN | ORIGEN | CODIGO_CANONICO | Sistema_Empresas |
| 1 | Origen | ORIGEN | NOMBRE_VISIBLE | Frontend |
| 1 | origen | ORIGEN | API_KEY | sync_job |
| 1 | ORIGEN LOCAL | ORIGENLOCAL | NOMBRE_SISTEMA | Servidores |
| 2 | 130QRO | 130QRO | CODIGO_CANONICO | Sistema_Empresas |
| 2 | 130-QRO | 130QRO | CODIGO_LEGACY | carga_historica |
| 2 | 130_qro | 130QRO | API_KEY | sync_job |
| 2 | 130 QRO | 130QRO | NOMBRE_SISTEMA | MongoDB |
| 2 | 130° QRO | 130QRO | NOMBRE_VISIBLE | Frontend |
| 2 | 130° QUERETARO | 130QUERETARO | SUCURSAL_NOMBRE | server_config |
| 2 | 130° QRO LOCAL | 130QROLOCAL | NOMBRE_SISTEMA | Servidores |
| 2 | QUERETARO | QUERETARO | API_KEY | api_cache |
| 2 | QUERÉTARO | QUERETARO | NOMBRE_SISTEMA | queries |
| 2 | 130 Grados Querétaro | 130GRADOSQUERETARO | NOMBRE_VISIBLE | NombreComercial |
| 3 | CIENFUEGOS | CIENFUEGOS | CODIGO_CANONICO | Sistema_Empresas |
| 3 | Cienfuegos | CIENFUEGOS | NOMBRE_VISIBLE | rh/importador |
| 3 | CIEN FUEGOS | CIENFUEGOS | SUCURSAL_NOMBRE | server_config |
| 4 | ESTELAR | ESTELAR | CODIGO_CANONICO | Sistema_Empresas |
| 4 | LA-ESTELAR | LAESTELAR | CODIGO_LEGACY | service.py |
| 4 | LA ESTELAR | LAESTELAR | NOMBRE_SISTEMA | MongoDB |
| 4 | La Estelar | LAESTELAR | NOMBRE_VISIBLE | Documentación |
| 5 | 130MID | 130MID | CODIGO_CANONICO | Sistema_Empresas |
| 5 | 130-MER | 130MER | CODIGO_LEGACY | service.py |
| 5 | 130-MID | 130MID | CODIGO_LEGACY | repository |
| 5 | 130 MID | 130MID | NOMBRE_SISTEMA | MongoDB |
| 5 | 130° MERIDA | 130MERIDA | SUCURSAL_NOMBRE | MongoDB |
| 5 | 130° MÉRIDA | 130MERIDA | NOMBRE_VISIBLE | carga_historica |
| 5 | MERIDA | MERIDA | API_KEY | queries |
| 5 | MÉRIDA | MERIDA | NOMBRE_SISTEMA | repository |
| 5 | 130 Grados Mérida | 130GRADOSMERIDA | NOMBRE_VISIBLE | NombreComercial |

### B. Servidores por Empresa

| EmpresaID | Empresa | ServidorID | Nombre | Rol | NumSuc |
|-----------|---------|------------|--------|-----|--------|
| 1 | ORIGEN | 1b230a06-... | ManagmentPro | DATA_SOURCE | 0023 |
| 1 | ORIGEN | 817a0aa8-... | ORIGEN LOCAL | API_LOCAL_VENTAS | 0023 |
| 2 | 130QRO | 1b230a06-... | ManagmentPro | DATA_SOURCE | 0021 |
| 2 | 130QRO | 72f6e9a7-... | 130° QRO LOCAL | API_LOCAL_VENTAS | 0021 |
| 3 | CIENFUEGOS | 6d053c22-... | CIENFUEGOS | DATA_SOURCE | NULL |
| 3 | CIENFUEGOS | 6d859026-... | CIENFUEGOS TABLAJERIA | TABLAJERIA | NULL |
| 4 | ESTELAR | a5ff0e25-... | LA ESTELAR | DATA_SOURCE | NULL |
| 5 | 130MID | a5547321-... | 130° MERIDA | DATA_SOURCE | NULL |

---

## Conclusión

Esta propuesta técnica establece las bases para normalizar la identificación de unidades de negocio en EDARSAHUB, eliminando dependencias de matching textual y centralizando la resolución de aliases.

**Estado:** PROPUESTA PASIVA - Esperando autorización para implementación.

**Próximo paso:** Aprobación de Fase 0 (DDL y carga inicial).

---

*Documento generado automáticamente. No ejecutar sin autorización explícita.*
