# FASE 3-B: DDL y Migración de Sucursales/Mapeos a EDARSAHUB SQL

**Fecha:** 2026-05-14  
**Fase:** FASE 3-B  
**Estado:** COMPLETADA  
**Autor:** Agente E1  
**Régimen:** Autorización Controlada

---

## 1. Decisión Tomada: Opción B

**Selección:** Crear nueva tabla canónica `Sistema_Sucursales` bajo patrón `Sistema_*`.

**NO usar** `RH_Cat_Sucursales` como tabla transversal.

---

## 2. Justificación de No Usar RH_Cat_Sucursales

| Criterio | Justificación |
|----------|---------------|
| **Prefijo** | `RH_Cat_*` pertenece al módulo Recursos Humanos |
| **Dependencia transversal** | No debe convertirse en dependencia para Comercial, Finanzas, Compras, Inventarios, Auth/RBAC |
| **Separación de concerns** | Nóminas usa RH_Cat_Sucursales; no debe afectar context_resolver |
| **Patrón institucional** | Tablas canónicas transversales usan `Sistema_*` |

**RH_Cat_Sucursales se conserva** como:
- Referencia comparativa
- Catálogo específico del módulo RH
- Sin modificaciones

---

## 3. DDL Ejecutado

### 3.1. Sistema_Sucursales
```sql
CREATE TABLE Sistema_Sucursales (
    SucursalID INT IDENTITY(1,1) PRIMARY KEY,
    CodigoSucursal VARCHAR(50) NOT NULL,
    NombreSucursal NVARCHAR(200) NOT NULL,
    EmpresaID INT NULL FOREIGN KEY REFERENCES Sistema_Empresas(EmpresaID),
    UnidadNegocioID INT NULL,
    MongoUUID VARCHAR(36) NULL,
    MongoEmpresaUUID VARCHAR(36) NULL,
    FuenteMigracion VARCHAR(50) NULL,
    Activo BIT NOT NULL DEFAULT 1,
    FechaAlta DATETIME2 NOT NULL DEFAULT GETDATE(),
    FechaModificacion DATETIME2 NULL,
    CreatedBy VARCHAR(100) NULL,
    UpdatedBy VARCHAR(100) NULL,
    Observaciones NVARCHAR(500) NULL
);
```

### 3.2. Sistema_SucursalServidorMapeo
```sql
CREATE TABLE Sistema_SucursalServidorMapeo (
    MapeoID INT IDENTITY(1,1) PRIMARY KEY,
    SucursalID INT NOT NULL FOREIGN KEY REFERENCES Sistema_Sucursales(SucursalID),
    ServidorID UNIQUEIDENTIFIER NOT NULL,
    SucursalOrigenID VARCHAR(100) NULL,
    MongoSucursalUUID VARCHAR(36) NULL,
    MongoServidorUUID VARCHAR(36) NULL,
    FuenteMigracion VARCHAR(50) NULL,
    Activo BIT NOT NULL DEFAULT 1,
    FechaCreacion DATETIME2 NOT NULL DEFAULT GETDATE(),
    FechaModificacion DATETIME2 NULL,
    CreatedBy VARCHAR(100) NULL,
    Observaciones NVARCHAR(500) NULL
);
```

### 3.3. Sistema_ServidorSucursalesConfig
```sql
CREATE TABLE Sistema_ServidorSucursalesConfig (
    ConfigID INT IDENTITY(1,1) PRIMARY KEY,
    ServidorID UNIQUEIDENTIFIER NOT NULL,
    SucursalNombre NVARCHAR(200) NOT NULL,
    SucursalCodigo VARCHAR(50) NULL,
    SucursalID INT NULL FOREIGN KEY REFERENCES Sistema_Sucursales(SucursalID),
    VisibleEnOperaciones BIT NOT NULL DEFAULT 0,
    VisibleEnComercial BIT NOT NULL DEFAULT 0,
    MongoConfigID VARCHAR(36) NULL,
    FuenteMigracion VARCHAR(50) NULL,
    Activo BIT NOT NULL DEFAULT 1,
    FechaCreacion DATETIME2 NOT NULL DEFAULT GETDATE(),
    FechaModificacion DATETIME2 NULL,
    CreatedBy VARCHAR(100) NULL,
    UpdatedBy VARCHAR(100) NULL,
    Observaciones NVARCHAR(500) NULL
);
```

---

## 4. Tablas Creadas

| Tabla | Registros | Estado |
|-------|-----------|--------|
| `Sistema_Sucursales` | 5 | ✅ Creada y poblada |
| `Sistema_SucursalServidorMapeo` | 5 | ✅ Creada y poblada |
| `Sistema_ServidorSucursalesConfig` | 7 | ✅ Creada y poblada |

---

## 5. Datos Migrados

### Sistema_Sucursales (5 registros)
| SucursalID | Nombre | EmpresaID | Empresa |
|------------|--------|-----------|---------|
| 1 | ORIGEN | 1 | ORIGEN |
| 2 | 130° QUERETARO | 2 | 130 QRO |
| 3 | CIENFUEGOS | 3 | CIENFUEGOS |
| 4 | LA ESTELAR | 4 | LA ESTELAR |
| 5 | 130° MERIDA | 5 | 130 MID |

### Sistema_SucursalServidorMapeo (5 registros)
| Sucursal | Servidor |
|----------|----------|
| ORIGEN | ManagmentPro |
| 130° QUERETARO | ManagmentPro |
| CIENFUEGOS | CIENFUEGOS |
| LA ESTELAR | LA ESTELAR |
| 130° MERIDA | 130° MERIDA |

### Sistema_ServidorSucursalesConfig (7 registros)
| Sucursal | Servidor | VisibleEnOperaciones |
|----------|----------|---------------------|
| 130° QUERETARO | ManagmentPro | ✅ |
| ORIGEN | ManagmentPro | ✅ |
| CIEN FUEGOS | ManagmentPro | ❌ |
| AGRICREME | ManagmentPro | ❌ |
| EDARSA | ManagmentPro | ❌ |
| 130° MERIDA | ManagmentPro | ❌ |
| MECA | ManagmentPro | ❌ |

---

## 6. Fuente de Cada Dato

| Tabla SQL | Fuente MongoDB | Fuente SQL Auxiliar |
|-----------|----------------|---------------------|
| `Sistema_Sucursales` | `db.sucursales_catalogo` | `Sistema_EmpresasMongoMap` (para EmpresaID) |
| `Sistema_SucursalServidorMapeo` | `db.sucursal_servidor_map` | - |
| `Sistema_ServidorSucursalesConfig` | `db.server_sucursales_config` | - |

---

## 7. Trazabilidad Legacy

Todas las tablas incluyen campos de trazabilidad:

| Campo | Propósito |
|-------|-----------|
| `MongoUUID` | UUID original de MongoDB |
| `MongoEmpresaUUID` | UUID de empresa en MongoDB |
| `MongoSucursalUUID` | UUID de sucursal en MongoDB |
| `MongoServidorUUID` | UUID de servidor en MongoDB |
| `FuenteMigracion` | Indica colección MongoDB origen |
| `CreatedBy` | Marca como 'FASE3B' |

---

## 8. Validación de Duplicados

| Tabla | Duplicados |
|-------|------------|
| `Sistema_Sucursales` | 0 ✅ |
| `Sistema_SucursalServidorMapeo` | 0 ✅ |
| `Sistema_ServidorSucursalesConfig` | 0 ✅ |

---

## 9. Validación de Relaciones

### Empresa → Sucursal
```
ORIGEN (Empresa) → ORIGEN (Sucursal) ✅
130 QRO (Empresa) → 130° QUERETARO (Sucursal) ✅
CIENFUEGOS (Empresa) → CIENFUEGOS (Sucursal) ✅
LA ESTELAR (Empresa) → LA ESTELAR (Sucursal) ✅
130 MID (Empresa) → 130° MERIDA (Sucursal) ✅
```

### Sucursal → Servidor
```
ORIGEN → ManagmentPro ✅
130° QUERETARO → ManagmentPro ✅
CIENFUEGOS → CIENFUEGOS (SoftRestaurant) ✅
LA ESTELAR → LA ESTELAR (SoftRestaurant) ✅
130° MERIDA → 130° MERIDA (SoftRestaurant) ✅
```

---

## 10. Confirmación de No Regresión

| Validación | Resultado |
|------------|-----------|
| Sistema_Empresas conserva 5 empresas | ✅ |
| Sistema_EmpresasMongoMap conserva 5 mapeos | ✅ |
| Unidades_Negocio conserva 5 unidades | ✅ |
| Login funciona | ✅ |
| RH_Cat_Sucursales no modificada (8 registros) | ✅ |
| Nuevas tablas sin duplicados | ✅ |

---

## 11. Recomendación para FASE 3-C

**FASE 3-C debe migrar el código de `context_resolver.py`** para que lea de las nuevas tablas SQL en lugar de MongoDB.

### Orden sugerido:
1. **FASE 3-C:** Migrar `context_resolver.py` a SQL
2. **FASE 3-D:** Migrar `user_access_context.py` a SQL
3. **FASE 3-E:** Migrar `context_service.py` a SQL
4. **FASE 3-F:** Migrar endpoints de configuración en `server.py`
5. **FASE 3-G:** Validación y cierre

### Prerequisitos completados:
- ✅ `Sistema_Sucursales` creada y poblada
- ✅ `Sistema_SucursalServidorMapeo` creada y poblada
- ✅ `Sistema_ServidorSucursalesConfig` creada y poblada
- ✅ Relaciones Empresa→Sucursal→Servidor establecidas
- ✅ Trazabilidad MongoDB documentada

---

## Resumen Ejecutivo

| Aspecto | Estado |
|---------|--------|
| Tabla canónica `Sistema_Sucursales` creada | ✅ |
| `RH_Cat_Sucursales` NO usada como transversal | ✅ |
| Datos migrados con trazabilidad | ✅ |
| Sin duplicados ni ambigüedades | ✅ |
| Código productivo NO modificado | ✅ |
| Sin regresión | ✅ |

**FASE 3-B: COMPLETADA**
