# REVISIÓN DML: Catálogo Empresas / Servidores / Sucursales

**Fecha**: 2026-05-16  
**Estado**: PENDIENTE AUTORIZACIÓN  
**Rol**: Arquitecto Senior EDARSAHUB / DBA SQL Server  
**Tipo de Documento**: Revisión Pre-Ejecución DML

---

## 1. Resumen Ejecutivo

Este documento presenta los scripts DML propuestos para poblar las tablas canónicas creadas en la fase anterior (`Sistema_Tipos`, `Sistema_EmpresasAlias`, `Sistema_EmpresasServidores`). 

### Alcance:
- ✅ Solo operaciones INSERT
- ❌ NO se ejecutará UPDATE
- ❌ NO se ejecutará DELETE
- ❌ NO se modificará Sistema_Empresas
- ❌ NO se crearán empresas nuevas
- ❌ NO se usará MongoDB como fuente

### Validaciones Ejecutadas:
| Validación | Estado |
|------------|--------|
| Sistema_Tipos vacía | ✅ Confirmado (0 registros) |
| Sistema_EmpresasAlias vacía | ✅ Confirmado (0 registros) |
| Sistema_EmpresasServidores vacía | ✅ Confirmado (0 registros) |
| EmpresaIDs válidos desde Sistema_Empresas | ✅ Confirmado |
| ServidorIDs válidos desde Servidores_Conexiones | ✅ Confirmado |
| Códigos Sucursal MPRO (21, 23) confirmados | ✅ Confirmado |

---

## 2. Empresas Detectadas (Sistema_Empresas - NO MODIFICAR)

**Fuente**: EDARSAHUB.dbo.Sistema_Empresas  
**Fecha consulta**: 2026-05-16

| EmpresaID | CodigoEmpresa | NombreComercial | Activo |
|-----------|---------------|-----------------|--------|
| 1 | ORIGEN | Restaurante Origen S.A. de C.V. | ✅ |
| 2 | 130QRO | 130 Grados Querétaro S.A. de C.V. | ✅ |
| 3 | CIENFUEGOS | Restaurante Cienfuegos S.A. de C.V. | ✅ |
| 4 | ESTELAR | La Estelar S.A. de C.V. | ✅ |
| 5 | 130MID | 130 Grados Mérida S.A. de C.V. | ✅ |

**CONFIRMACIÓN**: No se crearán empresas nuevas. Los 5 EmpresaID (1-5) ya existen.

---

## 3. Servidores Detectados (Servidores_Conexiones - NO MODIFICAR)

**Fuente**: EDARSAHUB.dbo.Servidores_Conexiones  
**Fecha consulta**: 2026-05-16

### Servidores Activos Relevantes para el DML:

| ServidorID | NombreServidor | Tipo | Uso Propuesto |
|------------|----------------|------|---------------|
| A5547321-1139-4D2B-9D53-182CA737B6B6 | 130° MERIDA | SoftRestaurant | 130MID Principal |
| 72F6E9A7-8EA2-4EB2-802E-4EE31753435E | 130° QRO LOCAL | MPRO | 130QRO API Local |
| 6D053C22-523E-48C0-B72B-96081E2D781B | CIENFUEGOS | SoftRestaurant | CIENFUEGOS Principal |
| A5FF0E25-F029-43DB-B634-D4AC814C904F | LA ESTELAR | SoftRestaurant | ESTELAR Principal |
| 1B230A06-FFAF-4C70-BD27-B1BE3579DEA6 | ManagmentPro | MPRO | ORIGEN/130QRO Principal |
| 817A0AA8-6170-4738-A8F6-A72AC36BA0DF | ORIGEN LOCAL | MPRO | ORIGEN API Local |

**CONFIRMACIÓN**: No se crearán servidores nuevos. Todos los ServidorID propuestos existen y están activos.

---

## 4. Validación MPRO: Códigos de Sucursal

**Fuente**: CENTRAL2020.dbo.Sucursal  
**Fecha consulta**: 2026-05-16

| Sc_Cve_Sucursal | Sc_Descripcion | EmpresaID Propuesto |
|-----------------|----------------|---------------------|
| 0023 | ORIGEN | 1 (ORIGEN) |
| 0021 | 130° QUERETARO | 2 (130QRO) |

**CONFIRMACIÓN**: Los códigos de sucursal 21 y 23 son reales y provienen directamente de MPRO CENTRAL2020.

---

## 5. Estado Actual Tablas Destino (SELECT previo)

### 5.1 Sistema_Tipos
```sql
SELECT * FROM Sistema_Tipos ORDER BY SistemaTipoID;
-- Resultado: TABLA VACÍA - 0 registros
```

### 5.2 Sistema_EmpresasAlias
```sql
SELECT COUNT(*) FROM Sistema_EmpresasAlias;
-- Resultado: 0 registros
SELECT * FROM Sistema_EmpresasAlias;
-- Resultado: TABLA VACÍA
```

### 5.3 Sistema_EmpresasServidores
```sql
SELECT COUNT(*) FROM Sistema_EmpresasServidores;
-- Resultado: 0 registros
SELECT * FROM Sistema_EmpresasServidores;
-- Resultado: TABLA VACÍA
```

---

## 6. DML Propuesto Completo

### 6.1 INSERT Sistema_Tipos

```sql
-- ============================================================================
-- DML 1: CARGA SISTEMA_TIPOS
-- ============================================================================
-- Descripción: Catálogo de tipos de sistema origen
-- Operación: INSERT ONLY (no UPDATE, no DELETE)
-- Registros esperados: 5
-- ============================================================================

INSERT INTO Sistema_Tipos (CodigoSistema, NombreSistema, Descripcion, Activo, CreatedBy)
VALUES 
    ('SOFTRESTAURANT', 'SoftRestaurant', 'Sistema POS SoftRestaurant para restaurantes', 1, 'DML_FASE_CATALOGO'),
    ('MPRO', 'ManagementPro', 'Sistema ManagementPro para gestión centralizada', 1, 'DML_FASE_CATALOGO'),
    ('API_LOCAL', 'API Local', 'API local para sincronización en tiempo real de ventas del día', 1, 'DML_FASE_CATALOGO'),
    ('EDARSAHUB_SQL', 'EDARSAHUB SQL Server', 'Base de datos centralizada EDARSAHUB', 1, 'DML_FASE_CATALOGO'),
    ('OTRO', 'Otro', 'Otros sistemas no clasificados', 1, 'DML_FASE_CATALOGO');

-- Verificación post-INSERT:
-- SELECT * FROM Sistema_Tipos ORDER BY SistemaTipoID;
```

---

### 6.2 INSERT Sistema_EmpresasAlias

```sql
-- ============================================================================
-- DML 2: CARGA SISTEMA_EMPRESASALIAS
-- ============================================================================
-- Descripción: Mapeo de aliases legacy hacia EmpresaID canónico
-- Operación: INSERT ONLY (no UPDATE, no DELETE)
-- Registros esperados: 26
-- ============================================================================

-- -----------------------------------------------------------------------------
-- ORIGEN (EmpresaID = 1)
-- -----------------------------------------------------------------------------
-- Alias canónico
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (1, 'ORIGEN', 'ORIGEN', 'CANONICO', 1, 'DML_FASE_CATALOGO');

-- Variantes legacy
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (1, 'Origen', 'ORIGEN', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (1, 'origen', 'ORIGEN', 'LEGACY', 1, 'DML_FASE_CATALOGO');

-- -----------------------------------------------------------------------------
-- 130QRO (EmpresaID = 2)
-- -----------------------------------------------------------------------------
-- Alias canónico
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (2, '130QRO', '130QRO', 'CANONICO', 1, 'DML_FASE_CATALOGO');

-- Variantes legacy
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (2, '130 QRO', '130QRO', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (2, '130-QRO', '130QRO', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (2, '130° QRO', '130QRO', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (2, '130 QUERETARO', '130QUERETARO', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (2, '130° QUERETARO', '130QUERETARO', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (2, 'QUERETARO', 'QUERETARO', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (2, 'QRO', 'QRO', 'LEGACY', 1, 'DML_FASE_CATALOGO');

-- -----------------------------------------------------------------------------
-- CIENFUEGOS (EmpresaID = 3)
-- -----------------------------------------------------------------------------
-- Alias canónico
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (3, 'CIENFUEGOS', 'CIENFUEGOS', 'CANONICO', 1, 'DML_FASE_CATALOGO');

-- Variantes legacy
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (3, 'Cienfuegos', 'CIENFUEGOS', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (3, 'CF', 'CF', 'LEGACY', 1, 'DML_FASE_CATALOGO');

-- -----------------------------------------------------------------------------
-- ESTELAR (EmpresaID = 4)
-- -----------------------------------------------------------------------------
-- Alias canónico
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (4, 'ESTELAR', 'ESTELAR', 'CANONICO', 1, 'DML_FASE_CATALOGO');

-- Variantes legacy (REGLA: LA-ESTELAR es alias de ESTELAR, no empresa nueva)
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (4, 'LA ESTELAR', 'LAESTELAR', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (4, 'LA-ESTELAR', 'LAESTELAR', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (4, 'La Estelar', 'LAESTELAR', 'LEGACY', 1, 'DML_FASE_CATALOGO');

-- -----------------------------------------------------------------------------
-- 130MID (EmpresaID = 5)
-- -----------------------------------------------------------------------------
-- Alias canónico
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (5, '130MID', '130MID', 'CANONICO', 1, 'DML_FASE_CATALOGO');

-- Variantes legacy (REGLA: 130-MER es alias de 130MID, no duplicado)
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (5, '130 MID', '130MID', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (5, '130-MER', '130MER', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (5, '130 MER', '130MER', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (5, '130 MERIDA', '130MERIDA', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (5, '130° MERIDA', '130MERIDA', 'LEGACY', 1, 'DML_FASE_CATALOGO');

INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, Activo, CreatedBy)
VALUES (5, '130° MÉRIDA', '130MERIDA', 'LEGACY', 1, 'DML_FASE_CATALOGO');

-- Verificación post-INSERT:
-- SELECT EmpresaID, Alias, AliasNormalizado, OrigenAlias FROM Sistema_EmpresasAlias ORDER BY EmpresaID, OrigenAlias;
```

---

### 6.3 INSERT Sistema_EmpresasServidores

```sql
-- ============================================================================
-- DML 3: CARGA SISTEMA_EMPRESASSERVIDORES
-- ============================================================================
-- Descripción: Relación empresa-servidor con rol de conexión
-- Operación: INSERT ONLY (no UPDATE, no DELETE)
-- Registros esperados: 7
-- ============================================================================

-- -----------------------------------------------------------------------------
-- ORIGEN (EmpresaID = 1)
-- -----------------------------------------------------------------------------
-- MPRO Principal (NumeroSucursalSistema = 23)
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, CodigoSucursalSistema, 
     NombreSucursalSistema, Prioridad, EsPrincipal, Activo, CreatedBy)
VALUES 
    (1, '1B230A06-FFAF-4C70-BD27-B1BE3579DEA6', 'PRINCIPAL_SQL', 23, '0023', 
     'ORIGEN', 1, 1, 1, 'DML_FASE_CATALOGO');

-- API Local ORIGEN para ventas del día (RolConexion = VENTAS_DIA_API_LOCAL, no PRINCIPAL_SQL)
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, CodigoSucursalSistema, 
     NombreSucursalSistema, Prioridad, EsPrincipal, Activo, CreatedBy)
VALUES 
    (1, '817A0AA8-6170-4738-A8F6-A72AC36BA0DF', 'VENTAS_DIA_API_LOCAL', 23, '0023', 
     'ORIGEN', 2, 0, 1, 'DML_FASE_CATALOGO');

-- -----------------------------------------------------------------------------
-- 130QRO (EmpresaID = 2)
-- -----------------------------------------------------------------------------
-- MPRO Principal (NumeroSucursalSistema = 21)
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, CodigoSucursalSistema, 
     NombreSucursalSistema, Prioridad, EsPrincipal, Activo, CreatedBy)
VALUES 
    (2, '1B230A06-FFAF-4C70-BD27-B1BE3579DEA6', 'PRINCIPAL_SQL', 21, '0021', 
     '130° QUERETARO', 1, 1, 1, 'DML_FASE_CATALOGO');

-- API Local 130QRO para ventas del día (RolConexion = VENTAS_DIA_API_LOCAL, no PRINCIPAL_SQL)
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, CodigoSucursalSistema, 
     NombreSucursalSistema, Prioridad, EsPrincipal, Activo, CreatedBy)
VALUES 
    (2, '72F6E9A7-8EA2-4EB2-802E-4EE31753435E', 'VENTAS_DIA_API_LOCAL', 21, '0021', 
     '130° QUERETARO', 2, 0, 1, 'DML_FASE_CATALOGO');

-- -----------------------------------------------------------------------------
-- CIENFUEGOS (EmpresaID = 3)
-- -----------------------------------------------------------------------------
-- SoftRestaurant Principal (NumeroSucursalSistema = NULL para SR)
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, CodigoSucursalSistema, 
     NombreSucursalSistema, Prioridad, EsPrincipal, Activo, CreatedBy)
VALUES 
    (3, '6D053C22-523E-48C0-B72B-96081E2D781B', 'PRINCIPAL_SQL', NULL, NULL, 
     'CIENFUEGOS', 1, 1, 1, 'DML_FASE_CATALOGO');

-- -----------------------------------------------------------------------------
-- ESTELAR (EmpresaID = 4)
-- -----------------------------------------------------------------------------
-- SoftRestaurant Principal (NumeroSucursalSistema = NULL para SR)
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, CodigoSucursalSistema, 
     NombreSucursalSistema, Prioridad, EsPrincipal, Activo, CreatedBy)
VALUES 
    (4, 'A5FF0E25-F029-43DB-B634-D4AC814C904F', 'PRINCIPAL_SQL', NULL, NULL, 
     'LA ESTELAR', 1, 1, 1, 'DML_FASE_CATALOGO');

-- -----------------------------------------------------------------------------
-- 130MID (EmpresaID = 5)
-- -----------------------------------------------------------------------------
-- SoftRestaurant Principal (NumeroSucursalSistema = NULL para SR)
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, CodigoSucursalSistema, 
     NombreSucursalSistema, Prioridad, EsPrincipal, Activo, CreatedBy)
VALUES 
    (5, 'A5547321-1139-4D2B-9D53-182CA737B6B6', 'PRINCIPAL_SQL', NULL, NULL, 
     '130° MERIDA', 1, 1, 1, 'DML_FASE_CATALOGO');

-- Verificación post-INSERT:
-- SELECT EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, NombreSucursalSistema 
-- FROM Sistema_EmpresasServidores ORDER BY EmpresaID, Prioridad;
```

---

## 7. Aliases Propuestos por Empresa

### 7.1 ORIGEN (EmpresaID = 1)
| Alias | AliasNormalizado | Origen |
|-------|------------------|--------|
| ORIGEN | ORIGEN | CANONICO |
| Origen | ORIGEN | LEGACY |
| origen | ORIGEN | LEGACY |

### 7.2 130QRO (EmpresaID = 2)
| Alias | AliasNormalizado | Origen |
|-------|------------------|--------|
| 130QRO | 130QRO | CANONICO |
| 130 QRO | 130QRO | LEGACY |
| 130-QRO | 130QRO | LEGACY |
| 130° QRO | 130QRO | LEGACY |
| 130 QUERETARO | 130QUERETARO | LEGACY |
| 130° QUERETARO | 130QUERETARO | LEGACY |
| QUERETARO | QUERETARO | LEGACY |
| QRO | QRO | LEGACY |

**NOTA IMPORTANTE**: `130-QRO` es alias de `130QRO` (EmpresaID=2), NO una empresa separada.

### 7.3 CIENFUEGOS (EmpresaID = 3)
| Alias | AliasNormalizado | Origen |
|-------|------------------|--------|
| CIENFUEGOS | CIENFUEGOS | CANONICO |
| Cienfuegos | CIENFUEGOS | LEGACY |
| CF | CF | LEGACY |

### 7.4 ESTELAR (EmpresaID = 4)
| Alias | AliasNormalizado | Origen |
|-------|------------------|--------|
| ESTELAR | ESTELAR | CANONICO |
| LA ESTELAR | LAESTELAR | LEGACY |
| LA-ESTELAR | LAESTELAR | LEGACY |
| La Estelar | LAESTELAR | LEGACY |

**NOTA IMPORTANTE**: `LA-ESTELAR` es alias de `ESTELAR` (EmpresaID=4), NO una empresa separada.

### 7.5 130MID (EmpresaID = 5)
| Alias | AliasNormalizado | Origen |
|-------|------------------|--------|
| 130MID | 130MID | CANONICO |
| 130 MID | 130MID | LEGACY |
| 130-MER | 130MER | LEGACY |
| 130 MER | 130MER | LEGACY |
| 130 MERIDA | 130MERIDA | LEGACY |
| 130° MERIDA | 130MERIDA | LEGACY |
| 130° MÉRIDA | 130MERIDA | LEGACY |

**NOTA IMPORTANTE**: `130-MER` es alias de `130MID` (EmpresaID=5), NO duplicado de otra empresa.

---

## 8. Relaciones Empresa-Servidor Propuestas

| EmpresaID | Empresa | ServidorID | Servidor | RolConexion | NumSucursal | EsPrincipal |
|-----------|---------|------------|----------|-------------|-------------|-------------|
| 1 | ORIGEN | 1B230A06-... | ManagmentPro | PRINCIPAL_SQL | 23 | ✅ |
| 1 | ORIGEN | 817A0AA8-... | ORIGEN LOCAL | VENTAS_DIA_API_LOCAL | 23 | ❌ |
| 2 | 130QRO | 1B230A06-... | ManagmentPro | PRINCIPAL_SQL | 21 | ✅ |
| 2 | 130QRO | 72F6E9A7-... | 130° QRO LOCAL | VENTAS_DIA_API_LOCAL | 21 | ❌ |
| 3 | CIENFUEGOS | 6D053C22-... | CIENFUEGOS | PRINCIPAL_SQL | NULL | ✅ |
| 4 | ESTELAR | A5FF0E25-... | LA ESTELAR | PRINCIPAL_SQL | NULL | ✅ |
| 5 | 130MID | A5547321-... | 130° MERIDA | PRINCIPAL_SQL | NULL | ✅ |

---

## 9. Mapeo MPRO Propuesto

### 9.1 Servidor MPRO Compartido

**ServidorID**: `1B230A06-FFAF-4C70-BD27-B1BE3579DEA6`  
**Nombre**: ManagmentPro  
**Database**: CENTRAL2020  
**Host**: 54.39.104.176

### 9.2 Diferenciación por NumeroSucursalSistema

| Empresa | EmpresaID | NumeroSucursalSistema | CodigoSucursalSistema | Confirmado en MPRO |
|---------|-----------|----------------------|----------------------|-------------------|
| ORIGEN | 1 | 23 | 0023 | ✅ |
| 130QRO | 2 | 21 | 0021 | ✅ |

### 9.3 APIs Locales

| Empresa | ServidorID | RolConexion |
|---------|------------|-------------|
| ORIGEN | 817A0AA8-6170-4738-A8F6-A72AC36BA0DF | VENTAS_DIA_API_LOCAL |
| 130QRO | 72F6E9A7-8EA2-4EB2-802E-4EE31753435E | VENTAS_DIA_API_LOCAL |

**NOTA**: Las APIs locales usan RolConexion = `VENTAS_DIA_API_LOCAL`, NO `PRINCIPAL_SQL`.

---

## 10. Mapeo SoftRestaurant Propuesto

| Empresa | EmpresaID | ServidorID | Servidor | NumeroSucursalSistema |
|---------|-----------|------------|----------|----------------------|
| CIENFUEGOS | 3 | 6D053C22-523E-48C0-B72B-96081E2D781B | CIENFUEGOS | NULL |
| ESTELAR | 4 | A5FF0E25-F029-43DB-B634-D4AC814C904F | LA ESTELAR | NULL |
| 130MID | 5 | A5547321-1139-4D2B-9D53-182CA737B6B6 | 130° MERIDA | NULL |

**NOTA**: SoftRestaurant tiene servidor dedicado por unidad. NumeroSucursalSistema es NULL.

---

## 11. Validación de Duplicados

### 11.1 Validación Pre-INSERT Sistema_EmpresasAlias

```sql
-- Verificar que no existen aliases duplicados antes de insertar
SELECT AliasNormalizado, COUNT(*) as Cantidad
FROM Sistema_EmpresasAlias
WHERE Activo = 1
GROUP BY AliasNormalizado
HAVING COUNT(*) > 1;

-- Resultado esperado: 0 filas (tabla vacía)
```

### 11.2 Validación Pre-INSERT Sistema_EmpresasServidores

```sql
-- Verificar que no existen relaciones duplicadas
SELECT EmpresaID, ServidorID, RolConexion, COUNT(*) as Cantidad
FROM Sistema_EmpresasServidores
WHERE Activo = 1
GROUP BY EmpresaID, ServidorID, RolConexion
HAVING COUNT(*) > 1;

-- Resultado esperado: 0 filas (tabla vacía)
```

---

## 12. Riesgos Identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Alias ambiguos (ej. QRO solo) | Baja | Medio | Índice único filtrado + validación en EmpresaResolver |
| FK violation si EmpresaID no existe | Nula | Alto | Validado: Los 5 EmpresaID existen |
| FK violation si ServidorID no existe | Nula | Alto | Validado: Todos los ServidorID propuestos existen |
| Datos legacy con aliases no mapeados | Media | Bajo | Se pueden agregar aliases adicionales posteriormente |

---

## 13. Decisiones Pendientes

| Decisión | Estado | Observación |
|----------|--------|-------------|
| ¿Incluir alias "MÉRIDA" con acento? | PENDIENTE | Podría agregarse si hay datos legacy con acento |
| ¿Incluir alias "ESTELAR" sin "LA"? | INCLUIDO | Ya está como alias canónico |
| ¿Incluir alias "130-QRO" (con guión)? | INCLUIDO | Mapeado a EmpresaID=2 |

---

## 14. Confirmaciones de Seguridad

| Confirmación | Estado |
|--------------|--------|
| No se ejecutó DML | ✅ CONFIRMADO |
| No se modificó código backend | ✅ CONFIRMADO |
| No se modificó frontend | ✅ CONFIRMADO |
| No se modificaron jobs | ✅ CONFIRMADO |
| No se tocó Tablero Ejecutivo | ✅ CONFIRMADO |
| No se tocó módulo Comercial | ✅ CONFIRMADO |
| No se modificó Sistema_Empresas | ✅ CONFIRMADO |
| No se crearán empresas nuevas | ✅ CONFIRMADO |
| No se usó MongoDB como fuente | ✅ CONFIRMADO |
| ServidorID son reales (no inventados) | ✅ CONFIRMADO |
| Códigos sucursal MPRO verificados en origen | ✅ CONFIRMADO |
| No se ejecutará UPDATE | ✅ CONFIRMADO |
| No se ejecutará DELETE | ✅ CONFIRMADO |

---

## 15. Resumen de INSERTs Propuestos

| Tabla | Registros a Insertar |
|-------|---------------------|
| Sistema_Tipos | 5 |
| Sistema_EmpresasAlias | 26 |
| Sistema_EmpresasServidores | 7 |
| **TOTAL** | **38** |

---

## 16. Siguiente Paso

**ACCIÓN REQUERIDA**: Autorización explícita del usuario para ejecutar el DML propuesto.

Una vez autorizado:
1. Ejecutar DML 1 (Sistema_Tipos)
2. Validar con SELECT
3. Ejecutar DML 2 (Sistema_EmpresasAlias)
4. Validar con SELECT
5. Ejecutar DML 3 (Sistema_EmpresasServidores)
6. Validar con SELECT
7. Generar reporte de ejecución

---

**FIN DEL REPORTE DE REVISIÓN**

Esperando autorización explícita del usuario para ejecutar el DML.
