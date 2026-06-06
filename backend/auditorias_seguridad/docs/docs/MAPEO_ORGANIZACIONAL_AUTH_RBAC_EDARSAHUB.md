# MAPEO ORGANIZACIONAL AUTH/RBAC EDARSAHUB

**Documento:** FASE A1.6 — Mapeo Organizacional para Migración Auth/RBAC  
**Fecha:** 8 de Mayo 2026  
**Estado:** ANÁLISIS DOCUMENTAL — NO SE HAN EJECUTADO CAMBIOS  
**Versión:** 1.0

---

## 1. RESUMEN EJECUTIVO

Este documento resuelve el bloqueo P0 de mapeo organizacional identificando las diferencias críticas entre las entidades Empresa, Unidad de Negocio, Sucursal y Servidor en MongoDB vs EDARSAHUB.

### Hallazgos Principales

| Entidad | MongoDB | EDARSAHUB | ¿Tabla existe? | ¿IDs coinciden? |
|---------|---------|-----------|----------------|-----------------|
| **Empresa** | `empresas` (5 docs) | **NO EXISTE** | ❌ NO | N/A |
| **Unidad de Negocio** | `sec_unidades_negocio` (7 docs) | `Unidades_Negocio` (5 regs) | ✅ SÍ | ❌ NO |
| **Sucursal** | `sec_sucursales` (7 docs) | `RH_Cat_Sucursales` (8 regs) | ✅ SÍ | ❌ NO (UUID vs INT) |
| **Servidor** | `servers` (9 activos) | `Servidores_Conexiones` (11 activos) | ✅ SÍ | ✅ SÍ |

### Bloqueo P0 Identificado

**`users.empresas_permitidas`** usa IDs de la colección `empresas` de MongoDB, pero **EDARSAHUB no tiene tabla de Empresas**. 

Esto significa que no se puede crear `Usuario_UnidadesAsignacion` apuntando a `Unidades_Negocio` porque los IDs no son equivalentes.

---

## 2. CONFIRMACIÓN DE ENTIDADES DISTINTAS

### ⚠️ Empresa ≠ Unidad de Negocio ≠ Sucursal ≠ Servidor

Estas son **CUATRO entidades organizacionales distintas** con propósitos diferentes:

| Entidad | Propósito | Ejemplo |
|---------|-----------|---------|
| **Empresa** | Entidad legal/fiscal, razón social, agrupador corporativo | EDARSA S.A. de C.V. |
| **Unidad de Negocio** | Operación comercial, concepto, marca | 130° Mérida, Cienfuegos, La Estelar |
| **Sucursal** | Ubicación física, punto de venta, establecimiento | Sucursal Centro, Sucursal Norte |
| **Servidor** | Fuente de datos, sistema origen (MPRO, SoftRestaurant) | ManagementPro, CIENFUEGOS DB |

### Jerarquía en MongoDB (Actual)

```
┌─────────────┐
│  empresas   │  ← users.empresas_permitidas apunta aquí
│  (5 docs)   │
│  ID: UUID   │
└──────┬──────┘
       │ empresa_id (FK)
       ▼
┌────────────────────────┐
│  sec_unidades_negocio  │  ← Todas apuntan a empresa_id: 62786c07-...
│       (7 docs)         │     (Esta empresa NO existe en `empresas`)
│       ID: UUID         │
└───────────┬────────────┘
            │ unidad_negocio_id (FK)
            ▼
┌─────────────────┐
│  sec_sucursales │
│    (7 docs)     │
│    ID: UUID     │
└────────┬────────┘
         │ vía sucursal_servidor_map
         ▼
┌─────────────────┐
│    servers      │
│   (9 activos)   │
│   ID: UUID      │
└─────────────────┘
```

### Jerarquía en EDARSAHUB (Objetivo)

```
┌─────────────────────┐
│    (NO EXISTE)      │  ← ⚠️ EDARSAHUB no tiene tabla de Empresas
│  Sistema_Empresas?  │
└─────────────────────┘

┌─────────────────────┐
│  Unidades_Negocio   │  ← Existe pero IDs NO coinciden con MongoDB
│      (5 regs)       │
│  ID: UNIQUEIDENTIFIER│
│  Server_ID: UUID    │  ← Relacionada directamente con servidor
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  RH_Cat_Sucursales  │  ← Existe pero IDs son INT, no UUID
│      (8 regs)       │
│  SucursalID: INT    │  ← Tipo incompatible con MongoDB
└──────────┬──────────┘
           │
           ▼
┌──────────────────────┐
│ Servidores_Conexiones│  ← IDs SÍ coinciden con MongoDB
│     (11 activos)     │
│  ID: UNIQUEIDENTIFIER│
└──────────────────────┘
```

---

## 3. INVENTARIO MONGODB

### 3.1 Colección: `empresas` (5 documentos)

| ID (UUID) | Nombre | Código | Activo |
|-----------|--------|--------|--------|
| `31784356-6d0b-47ce-8fe8-c8a442e45a07` | ORIGEN | ORIGEN | ✅ |
| `1118f83c-fd45-4681-8006-5e92dd6d01c1` | 130 QRO | 130QRO | ✅ |
| `1d91f076-a28e-49a5-b445-84aa767737b6` | CIENFUEGOS | CIENFUEGOS | ✅ |
| `e302e16f-2d97-4119-9ad9-bb5b00b71367` | LA ESTELAR | ESTELAR | ✅ |
| `a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff` | 130 MID | 130MID | ✅ |

**Uso:** `users.empresas_permitidas` contiene estos IDs para filtro RBAC.

### 3.2 Colección: `sec_unidades_negocio` (7 documentos)

| ID (UUID) | Nombre | Empresa_ID |
|-----------|--------|------------|
| `c9d9696e-d1ee-438e-82fd-b3cd67fe523b` | ManagementPro | `62786c07-...` |
| `c2c7f590-dbf7-45cd-89a0-bd4e6b9f3126` | MPRO TABLAJERIA | `62786c07-...` |
| `65c80576-faa8-444e-99ad-2bc9f4ba5296` | HR2020 ESCRITURA | `62786c07-...` |
| `1a1768a7-7ba7-4024-9fa4-f70b94810f87` | CIENFUEGOS | `62786c07-...` |
| `78db8a9e-513a-42eb-90df-43dab5a4eb1f` | LA ESTELAR | `62786c07-...` |
| `a2c363e8-5f43-4fa4-a1b8-e27cdfad814e` | 130° MERIDA | `62786c07-...` |
| `8b1b95a4-ea83-4b70-9c31-5e1ad1e48a3c` | CIENFUEGOS TABLAJERIA | `62786c07-...` |

**⚠️ Problema:** Todas apuntan a `empresa_id: 62786c07-4475-4b06-860d-7af6e56bd867` que **NO EXISTE** en la colección `empresas`.

### 3.3 Colección: `sec_sucursales` (7 documentos)

| ID (UUID) | Nombre | Unidad_Negocio_ID |
|-----------|--------|-------------------|
| `1d28fa3a-2bad-4e26-b116-213ca621ea8b` | ManagementPro | `c9d9696e-...` |
| `a1e84e5a-8384-48b3-9de4-9b17628ff9de` | MPRO TABLAJERIA | `c2c7f590-...` |
| `340b4734-6a10-4000-b5ea-6fe7f28cd8d5` | HR2020 ESCRITURA | `65c80576-...` |
| `205f15b9-5840-4adf-9d52-9ff8091cb718` | CIENFUEGOS | `1a1768a7-...` |
| `b02156fc-b3ca-457b-9ee8-bd4af4c03008` | LA ESTELAR | `78db8a9e-...` |
| `d11bafc4-0051-40dd-b0da-07958ac20a6c` | 130° MERIDA | `a2c363e8-...` |
| `b879e14e-4817-4e99-b31c-5076070d69fc` | CIENFUEGOS TABLAJERIA | `8b1b95a4-...` |

### 3.4 Colección: `servers` (9 activos)

| ID (UUID) | Nombre | System_Type |
|-----------|--------|-------------|
| `1b230a06-ffaf-4c70-bd27-b1be3579dea6` | ManagmentPro | MPRO |
| `6d053c22-523e-48c0-b72b-96081e2d781b` | CIENFUEGOS | SoftRestaurant |
| `a5ff0e25-f029-43db-b634-d4ac814c904f` | LA ESTELAR | SoftRestaurant |
| `a5547321-1139-4d2b-9d53-182ca737b6b6` | 130° MERIDA | SoftRestaurant |
| `d1d8c70f-c3d0-4407-ae50-f09e8e5992ee` | MPRO TABLAJERIA | MPRO |
| `6d859026-710a-4920-9a44-6da98fabc690` | CIENFUEGOS TABLAJERIA | SoftRestaurant |
| `b5175237-5e57-41f3-ab6d-b5ae2f5e780b` | HR2020 ESCRITURA | MPRO |
| `f8a9049a-96e8-4210-84ae-595ffa2822fa` | EDARSA HUB | EDARSA_HUB |
| `d8425038-5e57-42d9-8f3a-62e287888874` | PRUEBAS SOFTRESTAURANT | SoftRestaurant |

### 3.5 Campo: `users.empresas_permitidas`

IDs únicos usados por usuarios:
- `31784356-6d0b-47ce-8fe8-c8a442e45a07` → ORIGEN
- `1118f83c-fd45-4681-8006-5e92dd6d01c1` → 130 QRO
- `1d91f076-a28e-49a5-b445-84aa767737b6` → CIENFUEGOS
- `e302e16f-2d97-4119-9ad9-bb5b00b71367` → LA ESTELAR
- `a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff` → 130 MID

Estos IDs corresponden a la colección `empresas`, **NO a `sec_unidades_negocio`**.

---

## 4. INVENTARIO EDARSAHUB

### 4.1 Tabla: `Unidades_Negocio` (5 registros)

| ID (UNIQUEIDENTIFIER) | Nombre | Código | Server_ID |
|-----------------------|--------|--------|-----------|
| `19e076fb-c6de-4ea5-84ab-1caa9e86082c` | 130° MERIDA | 130MID | `a5547321-...` |
| `b06ee652-0370-4267-b0a8-da6fc39b590a` | CIENFUEGOS | CIENFUEGOS | `6d053c22-...` |
| `dfb86008-1b81-472a-9e50-8a0821dec4b2` | LA ESTELAR | ESTELAR | `a5ff0e25-...` |
| `9bc05ced-6b2b-4a0a-aa90-ce649b78e12c` | 130° QUERETARO | 130QRO | `1b230a06-...` |
| `23ca0b76-6580-4874-ba9b-672b122ca197` | ORIGEN | ORIGEN | `1b230a06-...` |

### 4.2 Tabla: `RH_Cat_Sucursales` (8 registros)

| SucursalID (INT) | Nombre | Ciudad |
|------------------|--------|--------|
| 1 | 130° QUERETARO | México |
| 2 | 130° TULUM | México |
| 3 | CIEN FUEGOS | México |
| 4 | EDARSA | México |
| 5 | GARCIA LAVIN | México |
| 6 | MECA | México |
| 7 | ORIGEN | México |
| 8 | XCANATUN | México |

**⚠️ Problema:** `SucursalID` es INT, pero MongoDB usa UUID para sucursales.

### 4.3 Tabla: `Servidores_Conexiones` (11 activos)

| ID (UNIQUEIDENTIFIER) | Nombre | System_Type |
|-----------------------|--------|-------------|
| `a5547321-1139-4d2b-9d53-182ca737b6b6` | 130° MERIDA | SoftRestaurant |
| `1b230a06-ffaf-4c70-bd27-b1be3579dea6` | ManagmentPro | MPRO |
| `6d053c22-523e-48c0-b72b-96081e2d781b` | CIENFUEGOS | SoftRestaurant |
| `a5ff0e25-f029-43db-b634-d4ac814c904f` | LA ESTELAR | SoftRestaurant |
| `6d859026-710a-4920-9a44-6da98fabc690` | CIENFUEGOS TABLAJERIA | SoftRestaurant |
| `b5175237-5e57-41f3-ab6d-b5ae2f5e780b` | HR2020 ESCRITURA | MPRO |
| `d1d8c70f-c3d0-4407-ae50-f09e8e5992ee` | MPRO TABLAJERIA | MPRO |
| `f8a9049a-96e8-4210-84ae-595ffa2822fa` | EDARSA HUB | EDARSA_HUB |
| `d8425038-5e57-42d9-8f3a-62e287888874` | PRUEBAS SOFTRESTAURANT | SoftRestaurant |
| `72f6e9a7-8ea2-4eb2-802e-4ee31753435e` | 130° QRO LOCAL | MPRO |
| `817a0aa8-6170-4738-a8f6-a72ac36ba0df` | ORIGEN LOCAL | MPRO |

### 4.4 Tabla: Empresas

**⚠️ NO EXISTE tabla de Empresas en EDARSAHUB.**

Tablas buscadas sin resultado:
- `Empresa`, `Empresas`, `Sistema_Empresas`
- `Global_Empresas`, `Corporativo`, `Holding`
- `RazonSocial`, `Grupo`

---

## 5. MATRIZ DE EQUIVALENCIAS MONGODB vs EDARSAHUB

### 5.1 Empresas

| MongoDB ID | MongoDB Nombre | EDARSAHUB Tabla | EDARSAHUB ID | Coincidencia | Riesgo |
|------------|----------------|-----------------|--------------|--------------|--------|
| `31784356-...` | ORIGEN | **NO EXISTE** | N/A | ❌ | **P0** |
| `1118f83c-...` | 130 QRO | **NO EXISTE** | N/A | ❌ | **P0** |
| `1d91f076-...` | CIENFUEGOS | **NO EXISTE** | N/A | ❌ | **P0** |
| `e302e16f-...` | LA ESTELAR | **NO EXISTE** | N/A | ❌ | **P0** |
| `a4d8b5e7-...` | 130 MID | **NO EXISTE** | N/A | ❌ | **P0** |

### 5.2 Unidades de Negocio (mapeo por nombre)

| MongoDB Nombre | MongoDB ID | EDARSAHUB Nombre | EDARSAHUB ID | ¿Coincide ID? | ¿Coincide Nombre? |
|----------------|------------|------------------|--------------|---------------|-------------------|
| CIENFUEGOS | `1a1768a7-...` | CIENFUEGOS | `b06ee652-...` | ❌ | ✅ |
| LA ESTELAR | `78db8a9e-...` | LA ESTELAR | `dfb86008-...` | ❌ | ✅ |
| 130° MERIDA | `a2c363e8-...` | 130° MERIDA | `19e076fb-...` | ❌ | ✅ |
| ManagementPro | `c9d9696e-...` | (no existe) | N/A | N/A | ❌ |
| MPRO TABLAJERIA | `c2c7f590-...` | (no existe) | N/A | N/A | ❌ |
| HR2020 ESCRITURA | `65c80576-...` | (no existe) | N/A | N/A | ❌ |
| CIENFUEGOS TABLAJERIA | `8b1b95a4-...` | (no existe) | N/A | N/A | ❌ |
| (no existe) | N/A | 130° QUERETARO | `9bc05ced-...` | N/A | ❌ |
| (no existe) | N/A | ORIGEN | `23ca0b76-...` | N/A | ❌ |

### 5.3 Servidores (mapeo por ID)

| MongoDB ID | MongoDB Nombre | EDARSAHUB ID | EDARSAHUB Nombre | ¿Coincide? |
|------------|----------------|--------------|------------------|------------|
| `1b230a06-...` | ManagmentPro | `1b230a06-...` | ManagmentPro | ✅ |
| `6d053c22-...` | CIENFUEGOS | `6d053c22-...` | CIENFUEGOS | ✅ |
| `a5ff0e25-...` | LA ESTELAR | `a5ff0e25-...` | LA ESTELAR | ✅ |
| `a5547321-...` | 130° MERIDA | `a5547321-...` | 130° MERIDA | ✅ |
| `d1d8c70f-...` | MPRO TABLAJERIA | `d1d8c70f-...` | MPRO TABLAJERIA | ✅ |
| `6d859026-...` | CIENFUEGOS TABLAJERIA | `6d859026-...` | CIENFUEGOS TABLAJERIA | ✅ |
| `b5175237-...` | HR2020 ESCRITURA | `b5175237-...` | HR2020 ESCRITURA | ✅ |
| `f8a9049a-...` | EDARSA HUB | `f8a9049a-...` | EDARSA HUB | ✅ |
| `d8425038-...` | PRUEBAS SOFTRESTAURANT | `d8425038-...` | PRUEBAS SOFTRESTAURANT | ✅ |

**✅ Los IDs de Servidores SÍ coinciden entre MongoDB y EDARSAHUB.**

---

## 6. IDs QUE COINCIDEN

| Entidad | MongoDB | EDARSAHUB | Coincidencia |
|---------|---------|-----------|--------------|
| **Servidores** | 9 activos | 11 activos | ✅ 9/9 coinciden por ID |

---

## 7. IDs QUE NO COINCIDEN

| Entidad | Problema | Impacto |
|---------|----------|---------|
| **Empresas** | No existe tabla en EDARSAHUB | `users.empresas_permitidas` no tiene destino |
| **Unidades de Negocio** | IDs completamente diferentes | No se puede mapear por ID, solo por nombre |
| **Sucursales** | EDARSAHUB usa INT, MongoDB usa UUID | Tipos incompatibles |

---

## 8. RIESGOS P0/P1/P2/P3

### P0_CRÍTICO

| Riesgo | Descripción | Impacto |
|--------|-------------|---------|
| R-P0-001 | `users.empresas_permitidas` usa IDs de `empresas` MongoDB que no existen en EDARSAHUB | **Login y filtros RBAC fallarían** |
| R-P0-002 | No existe tabla `Sistema_Empresas` en EDARSAHUB | **No se puede migrar filtro por empresa** |
| R-P0-003 | `sec_unidades_negocio.empresa_id` apunta a empresa inexistente (`62786c07-...`) | **Inconsistencia de datos en MongoDB** |

### P1_ALTO

| Riesgo | Descripción | Impacto |
|--------|-------------|---------|
| R-P1-001 | IDs de `Unidades_Negocio` MongoDB ≠ EDARSAHUB | Requiere mapeo por nombre |
| R-P1-002 | `RH_Cat_Sucursales` usa INT, no UUID | Tipos incompatibles con MongoDB |
| R-P1-003 | EDARSAHUB tiene 2 unidades (ORIGEN, 130° QRO) que MongoDB no tiene | Datos incompletos |

### P2_MEDIO

| Riesgo | Descripción | Impacto |
|--------|-------------|---------|
| R-P2-001 | MongoDB tiene 7 unidades, EDARSAHUB solo 5 | Mapeo parcial |
| R-P2-002 | Sucursales en EDARSAHUB no coinciden con MongoDB | Filtros por sucursal incorrectos |

### P3_BAJO

| Riesgo | Descripción | Impacto |
|--------|-------------|---------|
| R-P3-001 | 2 usuarios con permisos directos legacy | Corregible asignando rol |

---

## 9. RECOMENDACIÓN SOBRE TABLA EMPRESAS

### Análisis de Opciones

| Opción | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| **A** | No crear `Empresas`. Mapear `empresas_permitidas` → `Unidades_Negocio` | Simple, usa tabla existente | Semánticamente incorrecto (empresa ≠ unidad) |
| **B** | Crear tabla `Sistema_Empresas` en EDARSAHUB | Modelo correcto, preserva jerarquía | Requiere CREATE TABLE |
| **C** | Crear tabla de equivalencias temporal | Permite migración gradual | Complejidad adicional |
| **D** | Mantener `empresas_permitidas` en MongoDB temporalmente | Sin cambios inmediatos | Deuda técnica persiste |

### Recomendación

**OPCIÓN B: Crear `Sistema_Empresas` en EDARSAHUB**

Justificación:
1. `Empresa` es una entidad distinta de `Unidad de Negocio`
2. El sistema actual YA usa `empresas` como nivel de filtro RBAC
3. Mantener la jerarquía Empresa → Unidad → Sucursal es arquitectónicamente correcto
4. Permite migración limpia sin cambiar semántica

**Nombre propuesto siguiendo patrón EDARSAHUB:** `Sistema_Empresas`
- Patrón detectado: `Global_*` para catálogos transversales, `Sistema_*` para configuración
- `Global_Cat_Bancos` existe como catálogo global
- `Sistema_Empresas` sería catálogo de empresas del sistema

---

## 10. RECOMENDACIÓN SOBRE Usuario_UnidadesAsignacion

### Estado Actual

La tabla `Usuario_UnidadesAsignacion` **NO puede crearse todavía** porque:

1. `users.empresas_permitidas` usa IDs de **Empresas**, no de Unidades
2. Si se crea FK a `Unidades_Negocio`, los IDs actuales no servirían
3. Se requiere primero resolver el mapeo Empresa → Unidad

### Opciones

| Opción | Descripción |
|--------|-------------|
| A | Crear `Usuario_EmpresasAsignacion` apuntando a nueva tabla `Sistema_Empresas` |
| B | Crear `Usuario_UnidadesAsignacion` + tabla de mapeo Empresa→Unidad |
| C | Redefinir `empresas_permitidas` en MongoDB para usar IDs de `Unidades_Negocio` |

### Recomendación

**OPCIÓN A: Crear primero `Sistema_Empresas`, luego `Usuario_EmpresasAsignacion`**

Esto preserva la semántica actual del sistema.

---

## 11. RECOMENDACIÓN SOBRE NivelJerarquia

**SÍ se puede agregar columna `NivelJerarquia INT` a `Usuario_Roles`.**

Esta modificación es independiente del mapeo organizacional.

Valores sugeridos (de `rbac_roles` MongoDB):
| Rol | Nivel |
|-----|-------|
| ADMIN | 100 |
| DIRECCION | 80 |
| GERENTE_OPS | 60 |
| SUPERVISOR | 40 |
| AUDITOR | 30 |
| OPERADOR | 20 |

---

## 12. RECOMENDACIÓN SOBRE PERMISOS DIRECTOS LEGACY

### Usuarios Afectados

| Usuario | sec_rol | sec_permisos | Problema | Corrección |
|---------|---------|--------------|----------|------------|
| `admin@edarsa.com` | `VISOR_ESTRUCTURA` (no existe) | `['SISTEMA_ESTRUCTURA_VER']` | Rol inválido | Asignar rol ADMIN |
| `ricardo@edarsa.com.mx` | NO ASIGNADO | `['SCHEDULER_VER']` | Sin rol | Asignar rol ADMIN |

### Recomendación

1. **NO crear tabla `Usuario_PermisosUsuario`**
2. Corregir usuarios asignando rol válido (ADMIN incluye SCHEDULER_VER)
3. Si se necesita `SISTEMA_ESTRUCTURA_VER`, agregarlo al rol ADMIN o crear rol `VISOR`

---

## 13. DDL QUE PODRÍA EJECUTARSE (SIN EJECUTAR TODAVÍA)

### 13.1 Tabla: `Sistema_Empresas` (NUEVA)

```sql
-- ⚠️ NO EJECUTAR - SOLO PROPUESTA

CREATE TABLE Sistema_Empresas (
    EmpresaID               BIGINT IDENTITY(1,1) NOT NULL,
    EmpresaUUID             UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    Codigo                  VARCHAR(20) NOT NULL,
    Nombre                  NVARCHAR(100) NOT NULL,
    RazonSocial             NVARCHAR(200) NULL,
    RFC                     VARCHAR(13) NULL,
    Activo                  BIT NOT NULL DEFAULT 1,
    FechaAlta               DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaModificacion       DATETIME2 NULL,
    
    CONSTRAINT PK_Sistema_Empresas PRIMARY KEY (EmpresaID),
    CONSTRAINT UQ_Sistema_Empresas_UUID UNIQUE (EmpresaUUID),
    CONSTRAINT UQ_Sistema_Empresas_Codigo UNIQUE (Codigo)
);

CREATE INDEX IX_Sistema_Empresas_Codigo ON Sistema_Empresas(Codigo);
```

### 13.2 Tabla: `Usuario_EmpresasAsignacion` (NUEVA)

```sql
-- ⚠️ NO EJECUTAR - SOLO PROPUESTA

CREATE TABLE Usuario_EmpresasAsignacion (
    UsuarioEmpresaAsignacionID  BIGINT IDENTITY(1,1) NOT NULL,
    UsuarioID                   INT NOT NULL,
    EmpresaID                   BIGINT NOT NULL,
    EsPrincipal                 BIT NOT NULL DEFAULT 0,
    FechaInicio                 DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaFin                    DATETIME2 NULL,
    Activo                      BIT NOT NULL DEFAULT 1,
    CreatedAt                   DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CreatedBy                   VARCHAR(100) NULL,
    
    CONSTRAINT PK_Usuario_EmpresasAsignacion PRIMARY KEY (UsuarioEmpresaAsignacionID),
    CONSTRAINT FK_UsuarioEmpresas_Usuario FOREIGN KEY (UsuarioID) REFERENCES Usuario_Catalogo(UsuarioID),
    CONSTRAINT FK_UsuarioEmpresas_Empresa FOREIGN KEY (EmpresaID) REFERENCES Sistema_Empresas(EmpresaID),
    CONSTRAINT UQ_UsuarioEmpresas_Unico UNIQUE (UsuarioID, EmpresaID)
);
```

### 13.3 Tabla Opcional: `Sistema_EmpresasEquivalencias` (Temporal para migración)

```sql
-- ⚠️ NO EJECUTAR - SOLO PROPUESTA

CREATE TABLE Sistema_EmpresasEquivalencias (
    EquivalenciaID          BIGINT IDENTITY(1,1) NOT NULL,
    EmpresaID_EDARSAHUB     BIGINT NOT NULL,
    EmpresaUUID_MongoDB     UNIQUEIDENTIFIER NOT NULL,
    EmpresaNombre_MongoDB   NVARCHAR(100) NOT NULL,
    Validado                BIT NOT NULL DEFAULT 0,
    FechaValidacion         DATETIME2 NULL,
    ValidadoPor             VARCHAR(100) NULL,
    
    CONSTRAINT PK_Sistema_EmpresasEquivalencias PRIMARY KEY (EquivalenciaID),
    CONSTRAINT FK_Equivalencias_Empresa FOREIGN KEY (EmpresaID_EDARSAHUB) REFERENCES Sistema_Empresas(EmpresaID),
    CONSTRAINT UQ_Equivalencias_MongoDB UNIQUE (EmpresaUUID_MongoDB)
);
```

### 13.4 Columna: `NivelJerarquia` en `Usuario_Roles`

```sql
-- ⚠️ NO EJECUTAR - SOLO PROPUESTA

ALTER TABLE Usuario_Roles ADD
    NivelJerarquia INT NOT NULL 
        CONSTRAINT DF_Usuario_Roles_NivelJerarquia DEFAULT 0;
```

---

## 14. PLAN DE MIGRACIÓN SEGURO

### Fase 1: Preparación (Sin cambios en producción)
1. ✅ Backup MongoDB (COMPLETADO)
2. ✅ Documentar equivalencias (ESTE DOCUMENTO)
3. ⬜ Aprobar DDL de `Sistema_Empresas`

### Fase 2: Crear Estructura (DDL)
1. ⬜ Crear `Sistema_Empresas`
2. ⬜ Crear `Usuario_EmpresasAsignacion`
3. ⬜ Agregar `NivelJerarquia` a `Usuario_Roles`

### Fase 3: Poblar Datos
1. ⬜ INSERT `Sistema_Empresas` con datos de MongoDB `empresas`
2. ⬜ INSERT `Usuario_EmpresasAsignacion` con mapeo de `users.empresas_permitidas`
3. ⬜ UPDATE `Usuario_Roles.NivelJerarquia` con niveles de `rbac_roles`

### Fase 4: Validar
1. ⬜ Verificar que todos los usuarios tienen empresas asignadas
2. ⬜ Verificar que filtros RBAC funcionan
3. ⬜ Probar login con usuario piloto

### Fase 5: Activar
1. ⬜ Modificar código para leer de EDARSAHUB
2. ⬜ Mantener MongoDB como fallback
3. ⬜ Monitorear errores

---

## 15. ROLLBACK

### DDL Rollback

```sql
-- En caso de problemas:
DROP TABLE IF EXISTS Sistema_EmpresasEquivalencias;
DROP TABLE IF EXISTS Usuario_EmpresasAsignacion;
DROP TABLE IF EXISTS Sistema_Empresas;

ALTER TABLE Usuario_Roles DROP CONSTRAINT IF EXISTS DF_Usuario_Roles_NivelJerarquia;
ALTER TABLE Usuario_Roles DROP COLUMN IF EXISTS NivelJerarquia;
```

### Código Rollback

```python
# Variable de entorno para rollback instantáneo
USE_EDARSAHUB_AUTH = os.environ.get('USE_EDARSAHUB_AUTH', 'false')

# Si 'false', el sistema sigue leyendo de MongoDB
```

---

## 16. AUTORIZACIÓN REQUERIDA

### Checklist

| Paso | Descripción | Estado |
|------|-------------|--------|
| 1 | ✅ Backup MongoDB | COMPLETADO |
| 2 | ✅ Análisis de equivalencias | COMPLETADO |
| 3 | ✅ Documentar mapeo organizacional | COMPLETADO |
| 4 | ⬜ Aprobar creación de `Sistema_Empresas` | **PENDIENTE** |
| 5 | ⬜ Aprobar creación de `Usuario_EmpresasAsignacion` | **PENDIENTE** |
| 6 | ⬜ Aprobar ALTER TABLE `Usuario_Roles` | **PENDIENTE** |
| 7 | ⬜ Ejecutar DDL | **NO AUTORIZADO** |
| 8 | ⬜ Poblar datos | **NO AUTORIZADO** |
| 9 | ⬜ Modificar código | **NO AUTORIZADO** |

---

## RESUMEN EJECUTIVO FINAL

### Bloqueo P0 Resuelto

El problema de mapeo organizacional ha sido documentado completamente:

1. **Empresa ≠ Unidad de Negocio** - Son entidades distintas
2. **EDARSAHUB no tiene tabla de Empresas** - Se debe crear `Sistema_Empresas`
3. **IDs no coinciden** - Se requiere tabla de equivalencias o INSERT directo
4. **Servidores SÍ coinciden** - Único punto de paridad

### Recomendación Final

| Tabla | Recomendación | Prioridad |
|-------|---------------|-----------|
| `Sistema_Empresas` | **CREAR** | P0 |
| `Usuario_EmpresasAsignacion` | **CREAR** | P0 |
| `Usuario_Roles.NivelJerarquia` | **AGREGAR** | P1 |
| `Usuario_UnidadesAsignacion` | **POSPONER** (usar Empresas primero) | P2 |
| `Usuario_PermisosUsuario` | **NO CREAR** | N/A |

---

**FIN DEL DOCUMENTO DE MAPEO ORGANIZACIONAL**

*Ningún DDL ha sido ejecutado. Toda implementación requiere autorización expresa.*
