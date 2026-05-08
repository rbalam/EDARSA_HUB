# PROPUESTA DDL AUTH/RBAC EDARSAHUB — VALIDACIÓN FINAL PRE-DDL

**Documento:** Propuesta de Modelo de Datos con Validación Funcional  
**Fecha:** 8 de Mayo 2026  
**Estado:** PROPUESTA DOCUMENTAL — NO EJECUTAR  
**Versión:** 3.0 (Validación Final Pre-DDL)

---

## VALIDACIÓN FINAL PRE-DDL (FASE A1.5)

### A. JERARQUÍA EMPRESA / UNIDAD DE NEGOCIO / SUCURSAL

#### A.1 Hallazgo Principal

**⚠️ EMPRESA ≠ UNIDAD DE NEGOCIO ≠ SUCURSAL**

Son **TRES ENTIDADES DISTINTAS** con **IDs DIFERENTES** en MongoDB:

| Entidad | Colección MongoDB | Registros | IDs Usados |
|---------|-------------------|-----------|------------|
| **Empresa** | `empresas` | 5 | `31784356-...`, `1118f83c-...`, etc. |
| **Unidad de Negocio** | `sec_unidades_negocio` | 7 | `c9d9696e-...`, `78db8a9e-...`, etc. |
| **Sucursal** | `sec_sucursales` | 7 | `1d28fa3a-...`, `a1e84e5a-...`, etc. |

**Relación jerárquica en MongoDB:**
```
Empresa
  └── Unidad de Negocio (empresa_id → Empresa.id)
        └── Sucursal (unidad_negocio_id → Unidad.id)
              └── Servidor (vía sucursal_servidor_map)
```

#### A.2 IDs que usa el Sistema ACTUALMENTE

| Campo | IDs que contiene | Tabla/Colección origen |
|-------|------------------|------------------------|
| `users.empresas_permitidas` | IDs de **Empresa** | `empresas` (MongoDB) |
| `Comercial_Ventas_Dia_Abiertas_v2.unidad_negocio_id` | Códigos cortos | NO son UUIDs |
| `Unidades_Negocio.id` (EDARSAHUB) | UUIDs de Unidad | Diferente a MongoDB |

**Problema detectado:**
- `users.empresas_permitidas` usa IDs de la colección `empresas` (MongoDB)
- EDARSAHUB tiene `Unidades_Negocio` pero **NO tiene tabla de Empresas**
- Los IDs de `empresas` MongoDB **NO coinciden** con `Unidades_Negocio` EDARSAHUB

#### A.3 Comparación de Datos

**MongoDB `empresas` (5 registros):**
| ID | Nombre |
|----|--------|
| `31784356-6d0b-47ce-8fe8-c8a442e45a07` | ORIGEN |
| `1118f83c-fd45-4681-8006-5e92dd6d01c1` | 130 QRO |
| `1d91f076-a28e-49a5-b445-84aa767737b6` | CIENFUEGOS |
| `e302e16f-2d97-4119-9ad9-bb5b00b71367` | LA ESTELAR |
| `a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff` | 130 MID |

**EDARSAHUB `Unidades_Negocio` (5 registros):**
| ID | Nombre |
|----|--------|
| `19e076fb-c6de-4ea5-84ab-1caa9e86082c` | 130° MERIDA |
| `23ca0b76-6580-4874-ba9b-672b122ca197` | ORIGEN |
| `dfb86008-1b81-472a-9e50-8a0821dec4b2` | LA ESTELAR |
| `9bc05ced-6b2b-4a0a-aa90-ce649b78e12c` | 130° QUERETARO |
| `b06ee652-0370-4267-b0a8-da6fc39b590a` | CIENFUEGOS |

**⚠️ CONCLUSIÓN:** Los IDs son COMPLETAMENTE DIFERENTES entre MongoDB y EDARSAHUB. Migración directa NO es posible.

#### A.4 Diagrama de Jerarquía Real

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MONGODB (ACTUAL)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐                                                            │
│  │  empresas   │  ← users.empresas_permitidas apunta aquí                   │
│  │  (5 docs)   │                                                            │
│  │  ID: UUID   │                                                            │
│  └──────┬──────┘                                                            │
│         │ empresa_id                                                        │
│         ▼                                                                   │
│  ┌──────────────────────┐                                                   │
│  │ sec_unidades_negocio │  ← IDs diferentes a empresas                      │
│  │      (7 docs)        │                                                   │
│  │      ID: UUID        │                                                   │
│  └──────────┬───────────┘                                                   │
│             │ unidad_negocio_id                                             │
│             ▼                                                               │
│  ┌─────────────────┐                                                        │
│  │  sec_sucursales │  ← IDs diferentes a unidades                           │
│  │    (7 docs)     │                                                        │
│  │    ID: UUID     │                                                        │
│  └────────┬────────┘                                                        │
│           │ vía sucursal_servidor_map                                       │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │    servers      │                                                        │
│  │   (13 docs)     │                                                        │
│  └─────────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           EDARSAHUB (OBJETIVO)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐                                                    │
│  │   (NO EXISTE)       │  ← NO hay tabla de Empresas                        │
│  │   Sistema_Empresas? │                                                    │
│  └─────────────────────┘                                                    │
│                                                                              │
│  ┌─────────────────────┐                                                    │
│  │  Unidades_Negocio   │  ← Existe, 5 registros, IDs diferentes a MongoDB   │
│  │      (5 regs)       │                                                    │
│  │  ID: UNIQUEIDENTIFIER│                                                   │
│  └──────────┬──────────┘                                                    │
│             │                                                               │
│             ▼                                                               │
│  ┌─────────────────────┐                                                    │
│  │  RH_Cat_Sucursales  │  ← Existe, 8 registros, IDs tipo INT               │
│  │      (8 regs)       │                                                    │
│  │  ID: INT            │                                                    │
│  └──────────┬──────────┘                                                    │
│             │                                                               │
│             ▼                                                               │
│  ┌──────────────────────┐                                                   │
│  │ Servidores_Conexiones│  ← Existe, 17 registros, IDs coinciden con MongoDB│
│  │     (17 regs)        │                                                   │
│  └──────────────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### A.5 IDs Usados por Módulo

| Módulo | Campo de Filtro | Tipo de ID | Fuente |
|--------|-----------------|------------|--------|
| **user_access_context** | `empresas_ids` | UUID de `empresas` MongoDB | MongoDB |
| **Comercial** | `unidad_negocio_id` | Código corto (130-QRO, etc.) | Derivado |
| **Finanzas** | `UnidadNegocioID` | UUID | EDARSAHUB |
| **Tablero Ejecutivo** | `unidad_negocio_id` | Código corto | EDARSAHUB |
| **Servidores** | `server_id` | UUID | EDARSAHUB/MongoDB |

---

### B. ANÁLISIS DE PERMISOS DIRECTOS POR USUARIO

#### B.1 Hallazgo

| Aspecto | Resultado |
|---------|-----------|
| Usuarios con `sec_permisos` | **2 de 15** |
| Permisos únicos asignados directamente | **2** (`SISTEMA_ESTRUCTURA_VER`, `SCHEDULER_VER`) |
| ¿Hay permisos fuera del rol? | **SÍ, pero son casos especiales/legacy** |

**Usuarios con permisos directos:**
1. `admin@edarsa.com`: Tiene `SISTEMA_ESTRUCTURA_VER` pero su rol (`VISOR_ESTRUCTURA`) no existe
2. `ricardo@edarsa.com.mx`: Tiene `SCHEDULER_VER` pero NO tiene `sec_rol` asignado

#### B.2 Conclusión sobre Usuario_PermisosUsuario

**NO ES NECESARIA EN ESTA FASE.**

Razones:
1. Solo 2 usuarios de 15 tienen `sec_permisos` directos
2. Ambos casos son legacy/inconsistencias, no diseño intencional
3. El modelo `Usuario → Rol → Permisos` cubre el 87% de usuarios
4. Los casos especiales pueden resolverse asignando el rol correcto

**Recomendación:** Corregir los 2 usuarios anómalos asignándoles rol correcto, en lugar de crear tabla para excepciones.

---

### C. TABLAS REQUERIDAS VS DESCARTADAS

#### C.1 Tabla REQUERIDA: `Usuario_UnidadesAsignacion`

| Aspecto | Decisión |
|---------|----------|
| **Nombre** | `Usuario_UnidadesAsignacion` ✅ |
| **Propósito** | Relacionar usuario con unidades de negocio permitidas |
| **FK** | `UsuarioID → Usuario_Catalogo`, `UnidadNegocioID → Unidades_Negocio` |
| **Estado** | **REQUERIDA** - Sin esto no hay filtro RBAC |

**⚠️ PROBLEMA:** Los IDs de `empresas` MongoDB no coinciden con `Unidades_Negocio` EDARSAHUB. Se requiere mapeo previo.

#### C.2 Tabla POSIBLEMENTE REQUERIDA: `Sistema_Empresas`

| Aspecto | Decisión |
|---------|----------|
| **Nombre propuesto** | `Sistema_Empresas` |
| **Propósito** | Catálogo de empresas (entidad legal/corporativa) |
| **Estado** | **PENDIENTE DE DECISIÓN** |

**Pregunta para el usuario:** ¿"Empresas" en el contexto de EDARSA son:
- a) Equivalentes a "Unidades de Negocio" (solo diferente nombre)
- b) Un nivel superior (holding/corporativo) que agrupa unidades
- c) Otra cosa

Si (a): Usar `Unidades_Negocio` existente
Si (b): Crear `Sistema_Empresas`

#### C.3 Tabla DESCARTADA: `Usuario_SucursalesAsignacion`

| Aspecto | Decisión |
|---------|----------|
| **Nombre** | `Usuario_SucursalesAsignacion` |
| **Estado** | **DESCARTADA POR AHORA** |
| **Razón** | El filtro actual es por Empresa/Unidad, no por Sucursal directamente |

El código actual (`user_access_context.py`) resuelve sucursales a partir de empresas:
```python
await _resolver_servers_desde_empresas(context, empresas_rbac)
```

#### C.4 Tabla DESCARTADA: `Usuario_PermisosUsuario`

| Aspecto | Decisión |
|---------|----------|
| **Nombre** | `Usuario_PermisosUsuario` |
| **Estado** | **DESCARTADA POR AHORA** |
| **Razón** | Solo 2 usuarios tienen permisos directos, ambos son legacy |

El modelo `Usuario → Rol → Permisos` (vía `Usuario_RolesAsignacion` + `Usuario_PermisosRolModulo`) es suficiente.

---

### D. DDL FINAL RECOMENDADO

#### D.1 DDL APROBADO PARA REVISIÓN (1 tabla + 1 columna)

```sql
-- ⚠️ NO EJECUTAR - SOLO PROPUESTA PARA REVISIÓN

-- ============================================================
-- TABLA: Usuario_UnidadesAsignacion
-- Relación N:M entre usuarios y unidades de negocio
-- ============================================================
CREATE TABLE Usuario_UnidadesAsignacion (
    UsuarioUnidadAsignacionID   BIGINT IDENTITY(1,1) NOT NULL,
    UsuarioID                   INT NOT NULL,
    UnidadNegocioID             UNIQUEIDENTIFIER NOT NULL,
    EsPrincipal                 BIT NOT NULL DEFAULT 0,
    FechaInicio                 DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaFin                    DATETIME2 NULL,
    Activo                      BIT NOT NULL DEFAULT 1,
    CreatedAt                   DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CreatedBy                   VARCHAR(100) NULL,
    
    CONSTRAINT PK_Usuario_UnidadesAsignacion 
        PRIMARY KEY (UsuarioUnidadAsignacionID),
    CONSTRAINT FK_UsuarioUnidades_Usuario 
        FOREIGN KEY (UsuarioID) REFERENCES Usuario_Catalogo(UsuarioID),
    CONSTRAINT FK_UsuarioUnidades_Unidad 
        FOREIGN KEY (UnidadNegocioID) REFERENCES Unidades_Negocio(id),
    CONSTRAINT UQ_UsuarioUnidades_Unico 
        UNIQUE (UsuarioID, UnidadNegocioID)
);

CREATE INDEX IX_UsuarioUnidadesAsignacion_Usuario 
    ON Usuario_UnidadesAsignacion(UsuarioID);
CREATE INDEX IX_UsuarioUnidadesAsignacion_Unidad 
    ON Usuario_UnidadesAsignacion(UnidadNegocioID);

-- ============================================================
-- MODIFICACIÓN: Usuario_Roles - Agregar NivelJerarquia
-- ============================================================
ALTER TABLE Usuario_Roles ADD
    NivelJerarquia INT NOT NULL 
        CONSTRAINT DF_Usuario_Roles_NivelJerarquia DEFAULT 0;
```

#### D.2 DDL DESCARTADO

```sql
-- ❌ NO CREAR - Usuario_SucursalesAsignacion
-- Razón: El filtro actual es por Unidad, no por Sucursal directamente

-- ❌ NO CREAR - Usuario_PermisosUsuario  
-- Razón: Solo 2 usuarios tienen permisos directos, ambos son legacy
```

---

### E. RIESGOS IDENTIFICADOS

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| IDs de `empresas` MongoDB ≠ `Unidades_Negocio` EDARSAHUB | **P0_CRÍTICO** | Crear tabla de mapeo o normalizar IDs antes de migrar |
| No existe tabla `Sistema_Empresas` en EDARSAHUB | **P1_ALTO** | Decidir si crear o usar `Unidades_Negocio` como equivalente |
| `RH_Cat_Sucursales` usa INT, MongoDB usa UUID | **P2_MEDIO** | Usar mapeo por nombre o crear columna UUID |

---

### F. ESTRATEGIA DE ROLLBACK

```sql
-- En caso de problemas post-implementación:
DROP TABLE IF EXISTS Usuario_UnidadesAsignacion;
ALTER TABLE Usuario_Roles DROP CONSTRAINT IF EXISTS DF_Usuario_Roles_NivelJerarquia;
ALTER TABLE Usuario_Roles DROP COLUMN IF EXISTS NivelJerarquia;
```

---

### G. PRUEBAS REQUERIDAS ANTES DE DDL

| # | Prueba | Criterio |
|---|--------|----------|
| 1 | Mapear IDs `empresas` MongoDB → `Unidades_Negocio` EDARSAHUB | 5/5 mapeados por nombre |
| 2 | Verificar FK a Usuario_Catalogo funciona | UsuarioID existe |
| 3 | Verificar FK a Unidades_Negocio funciona | UnidadNegocioID existe |
| 4 | Probar INSERT de asignación | Sin errores |
| 5 | Probar query de permisos con JOIN | Datos correctos |

---

### H. AUTORIZACIONES REQUERIDAS

| Paso | Autorización |
|------|--------------|
| 1. Crear `Usuario_UnidadesAsignacion` | ⬜ PENDIENTE |
| 2. Agregar columna `NivelJerarquia` a `Usuario_Roles` | ⬜ PENDIENTE |
| 3. Poblar tablas con datos mapeados | ⬜ PENDIENTE |
| 4. Modificar código para leer EDARSAHUB | ⬜ PENDIENTE |

---

### I. PREGUNTAS PENDIENTES PARA EL USUARIO

1. **¿"Empresas" = "Unidades de Negocio" en el contexto de EDARSA?**
   - Si SÍ: Usar `Unidades_Negocio` existente y mapear IDs por nombre
   - Si NO: Crear tabla `Sistema_Empresas`

2. **¿Cómo mapear IDs de `empresas` MongoDB a `Unidades_Negocio` EDARSAHUB?**
   - Opción A: Por coincidencia de nombre (ORIGEN↔ORIGEN, etc.)
   - Opción B: Crear tabla de equivalencias
   - Opción C: Actualizar MongoDB para usar IDs de EDARSAHUB

3. **¿Los 2 usuarios con permisos directos deben corregirse asignándoles rol?**
   - Si SÍ: Corregir antes de migración
   - Si NO: Explicar caso de uso para diseñar solución

---

## RESUMEN EJECUTIVO

### Lo que se confirmó:

1. ✅ **Empresa ≠ Unidad de Negocio ≠ Sucursal** (entidades distintas)
2. ✅ **IDs de MongoDB ≠ IDs de EDARSAHUB** (requiere mapeo)
3. ✅ **Usuario_PermisosUsuario NO es necesaria** (permisos por rol son suficientes)
4. ✅ **Nomenclatura `Usuario_UnidadesAsignacion` es correcta**

### Lo que falta decidir:

1. ⬜ ¿Crear `Sistema_Empresas` o usar `Unidades_Negocio` como equivalente?
2. ⬜ ¿Cómo mapear IDs entre sistemas?
3. ⬜ ¿Autorizar DDL?

### DDL Final Propuesto:

- **CREAR:** `Usuario_UnidadesAsignacion` (1 tabla)
- **MODIFICAR:** `Usuario_Roles` (agregar columna `NivelJerarquia`)
- **DESCARTAR:** `Usuario_SucursalesAsignacion`, `Usuario_PermisosUsuario`

---

**FIN DEL DOCUMENTO DE VALIDACIÓN FINAL PRE-DDL**

*Ningún DDL ha sido ejecutado. Toda implementación requiere autorización expresa.*
