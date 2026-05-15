# FASE 3: DML Catálogo Empresas / Servidores / Sucursales - EJECUTADO

**Fecha**: 2026-05-16  
**Estado**: ✅ EJECUTADO EXITOSAMENTE  
**Rol**: Arquitecto Senior EDARSAHUB / DBA SQL Server  
**Tipo de Documento**: Reporte de Ejecución DML

---

## 1. Resumen Ejecutivo

Se ejecutó exitosamente el DML autorizado para poblar las tablas canónicas del catálogo de empresas, servidores y sucursales en EDARSAHUB SQL.

### Resultado Final:

| Tabla | Antes | Después | Esperados | Estado |
|-------|-------|---------|-----------|--------|
| Sistema_Tipos | 0 | 5 | 5 | ✅ |
| Sistema_EmpresasAlias | 0 | 12 | 26 (12 únicos) | ✅ |
| Sistema_EmpresasServidores | 0 | 7 | 7 | ✅ |

### Nota sobre Sistema_EmpresasAlias:
Se propusieron 26 aliases, pero el índice único filtrado por `AliasNormalizado` rechazó correctamente 14 duplicados. Por ejemplo:
- `Origen`, `origen` → mismo `AliasNormalizado` que `ORIGEN` → rechazados
- `130 QRO`, `130-QRO`, `130° QRO` → mismo `AliasNormalizado` que `130QRO` → rechazados

Esto es **comportamiento correcto** del diseño DDL.

---

## 2. Conteos Antes del DML

| Tabla | Registros |
|-------|-----------|
| Sistema_Tipos | 0 |
| Sistema_EmpresasAlias | 0 |
| Sistema_EmpresasServidores | 0 |
| Sistema_Empresas | 5 (sin cambios) |

---

## 3. DML Ejecutado

### 3.1 Sistema_Tipos

```sql
INSERT INTO Sistema_Tipos (CodigoSistema, NombreSistema, Descripcion, Activo, CreatedBy)
VALUES 
    ('SOFTRESTAURANT', 'SoftRestaurant', 'Sistema POS SoftRestaurant para restaurantes', 1, 'DML_FASE_CATALOGO'),
    ('MPRO', 'ManagementPro', 'Sistema ManagementPro para gestión centralizada', 1, 'DML_FASE_CATALOGO'),
    ('API_LOCAL', 'API Local', 'API local para sincronización en tiempo real de ventas del día', 1, 'DML_FASE_CATALOGO'),
    ('EDARSAHUB_SQL', 'EDARSAHUB SQL Server', 'Base de datos centralizada EDARSAHUB', 1, 'DML_FASE_CATALOGO'),
    ('OTRO', 'Otro', 'Otros sistemas no clasificados', 1, 'DML_FASE_CATALOGO');
```

### 3.2 Sistema_EmpresasAlias

```sql
-- 12 aliases únicos insertados exitosamente
-- 14 aliases rechazados por índice único (duplicados de AliasNormalizado)

-- ORIGEN (EmpresaID=1): 1 alias único
INSERT (1, 'ORIGEN', 'ORIGEN', 'CANONICO')

-- 130QRO (EmpresaID=2): 4 aliases únicos
INSERT (2, '130QRO', '130QRO', 'CANONICO')
INSERT (2, '130 QUERETARO', '130QUERETARO', 'LEGACY')
INSERT (2, 'QUERETARO', 'QUERETARO', 'LEGACY')
INSERT (2, 'QRO', 'QRO', 'LEGACY')

-- CIENFUEGOS (EmpresaID=3): 2 aliases únicos
INSERT (3, 'CIENFUEGOS', 'CIENFUEGOS', 'CANONICO')
INSERT (3, 'CF', 'CF', 'LEGACY')

-- ESTELAR (EmpresaID=4): 2 aliases únicos
INSERT (4, 'ESTELAR', 'ESTELAR', 'CANONICO')
INSERT (4, 'LA ESTELAR', 'LAESTELAR', 'LEGACY')

-- 130MID (EmpresaID=5): 3 aliases únicos
INSERT (5, '130MID', '130MID', 'CANONICO')
INSERT (5, '130-MER', '130MER', 'LEGACY')
INSERT (5, '130 MERIDA', '130MERIDA', 'LEGACY')
```

### 3.3 Sistema_EmpresasServidores

```sql
-- ORIGEN (EmpresaID=1)
INSERT (1, '1B230A06-FFAF-4C70-BD27-B1BE3579DEA6', 'PRINCIPAL_SQL', 23, '0023', 'ORIGEN', 1, 1)
INSERT (1, '817A0AA8-6170-4738-A8F6-A72AC36BA0DF', 'VENTAS_DIA_API_LOCAL', 23, '0023', 'ORIGEN', 2, 0)

-- 130QRO (EmpresaID=2)
INSERT (2, '1B230A06-FFAF-4C70-BD27-B1BE3579DEA6', 'PRINCIPAL_SQL', 21, '0021', '130° QUERETARO', 1, 1)
INSERT (2, '72F6E9A7-8EA2-4EB2-802E-4EE31753435E', 'VENTAS_DIA_API_LOCAL', 21, '0021', '130° QUERETARO', 2, 0)

-- CIENFUEGOS (EmpresaID=3)
INSERT (3, '6D053C22-523E-48C0-B72B-96081E2D781B', 'PRINCIPAL_SQL', NULL, NULL, 'CIENFUEGOS', 1, 1)

-- ESTELAR (EmpresaID=4)
INSERT (4, 'A5FF0E25-F029-43DB-B634-D4AC814C904F', 'PRINCIPAL_SQL', NULL, NULL, 'LA ESTELAR', 1, 1)

-- 130MID (EmpresaID=5)
INSERT (5, 'A5547321-1139-4D2B-9D53-182CA737B6B6', 'PRINCIPAL_SQL', NULL, NULL, '130° MERIDA', 1, 1)
```

---

## 4. Conteos Después del DML

| Tabla | Registros |
|-------|-----------|
| Sistema_Tipos | 5 ✅ |
| Sistema_EmpresasAlias | 12 ✅ |
| Sistema_EmpresasServidores | 7 ✅ |
| Sistema_Empresas | 5 (sin cambios) ✅ |

---

## 5. Registros Insertados en Sistema_Tipos

| SistemaTipoID | CodigoSistema | NombreSistema |
|---------------|---------------|---------------|
| 1 | SOFTRESTAURANT | SoftRestaurant |
| 2 | MPRO | ManagementPro |
| 3 | API_LOCAL | API Local |
| 4 | EDARSAHUB_SQL | EDARSAHUB SQL Server |
| 5 | OTRO | Otro |

---

## 6. Registros Insertados en Sistema_EmpresasAlias

| EmpresaID | Empresa | Alias | AliasNormalizado | Origen |
|-----------|---------|-------|------------------|--------|
| 1 | ORIGEN | ORIGEN | ORIGEN | CANONICO |
| 2 | 130QRO | 130QRO | 130QRO | CANONICO |
| 2 | 130QRO | 130 QUERETARO | 130QUERETARO | LEGACY |
| 2 | 130QRO | QUERETARO | QUERETARO | LEGACY |
| 2 | 130QRO | QRO | QRO | LEGACY |
| 3 | CIENFUEGOS | CIENFUEGOS | CIENFUEGOS | CANONICO |
| 3 | CIENFUEGOS | CF | CF | LEGACY |
| 4 | ESTELAR | ESTELAR | ESTELAR | CANONICO |
| 4 | ESTELAR | LA ESTELAR | LAESTELAR | LEGACY |
| 5 | 130MID | 130MID | 130MID | CANONICO |
| 5 | 130MID | 130-MER | 130MER | LEGACY |
| 5 | 130MID | 130 MERIDA | 130MERIDA | LEGACY |

---

## 7. Registros Insertados en Sistema_EmpresasServidores

| EmpresaID | Empresa | ServidorID | Servidor | RolConexion | NumSucursal | CodSucursal | Principal |
|-----------|---------|------------|----------|-------------|-------------|-------------|-----------|
| 1 | ORIGEN | 1B230A06-... | ManagmentPro | PRINCIPAL_SQL | 23 | 0023 | ✅ |
| 1 | ORIGEN | 817A0AA8-... | ORIGEN LOCAL | VENTAS_DIA_API_LOCAL | 23 | 0023 | ❌ |
| 2 | 130QRO | 1B230A06-... | ManagmentPro | PRINCIPAL_SQL | 21 | 0021 | ✅ |
| 2 | 130QRO | 72F6E9A7-... | 130° QRO LOCAL | VENTAS_DIA_API_LOCAL | 21 | 0021 | ❌ |
| 3 | CIENFUEGOS | 6D053C22-... | CIENFUEGOS | PRINCIPAL_SQL | NULL | NULL | ✅ |
| 4 | ESTELAR | A5FF0E25-... | LA ESTELAR | PRINCIPAL_SQL | NULL | NULL | ✅ |
| 5 | 130MID | A5547321-... | 130° MERIDA | PRINCIPAL_SQL | NULL | NULL | ✅ |

---

## 8. Validación: ORIGEN → Sucursal 23/0023

| Validación | Resultado |
|------------|-----------|
| ORIGEN PRINCIPAL_SQL usa NumeroSucursalSistema=23 | ✅ |
| ORIGEN PRINCIPAL_SQL usa CodigoSucursalSistema=0023 | ✅ |
| ORIGEN VENTAS_DIA_API_LOCAL usa NumeroSucursalSistema=23 | ✅ |
| ORIGEN VENTAS_DIA_API_LOCAL usa CodigoSucursalSistema=0023 | ✅ |

---

## 9. Validación: 130QRO → Sucursal 21/0021

| Validación | Resultado |
|------------|-----------|
| 130QRO PRINCIPAL_SQL usa NumeroSucursalSistema=21 | ✅ |
| 130QRO PRINCIPAL_SQL usa CodigoSucursalSistema=0021 | ✅ |
| 130QRO VENTAS_DIA_API_LOCAL usa NumeroSucursalSistema=21 | ✅ |
| 130QRO VENTAS_DIA_API_LOCAL usa CodigoSucursalSistema=0021 | ✅ |

---

## 10. Validación: APIs Locales con RolConexion = VENTAS_DIA_API_LOCAL

| EmpresaID | Empresa | RolConexion | Servidor |
|-----------|---------|-------------|----------|
| 1 | ORIGEN | VENTAS_DIA_API_LOCAL | ORIGEN LOCAL |
| 2 | 130QRO | VENTAS_DIA_API_LOCAL | 130° QRO LOCAL |

**CONFIRMACIÓN**: Las APIs locales NO usan PRINCIPAL_SQL. Usan correctamente VENTAS_DIA_API_LOCAL.

---

## 11. Validación: SoftRestaurant con NumeroSucursalSistema NULL

| EmpresaID | Empresa | NumeroSucursalSistema | Resultado |
|-----------|---------|----------------------|-----------|
| 3 | CIENFUEGOS | NULL | ✅ |
| 4 | ESTELAR | NULL | ✅ |
| 5 | 130MID | NULL | ✅ |

**CONFIRMACIÓN**: SoftRestaurant no requiere NumeroSucursalSistema.

---

## 12. Validación: Aliases Legacy Críticos

| Alias Legacy | EmpresaID Asignado | Empresa | Resultado |
|--------------|-------------------|---------|-----------|
| 130-MER | 5 | 130MID | ✅ |
| LA ESTELAR | 4 | ESTELAR | ✅ |
| 130 QUERETARO | 2 | 130QRO | ✅ |

**CONFIRMACIÓN**: 
- `130-MER` NO es una empresa nueva. Es alias de `130MID` (EmpresaID=5).
- `LA-ESTELAR` NO es una empresa nueva. Es alias de `ESTELAR` (EmpresaID=4).
- `130-QRO` NO es una empresa nueva. Es alias de `130QRO` (EmpresaID=2).

---

## 13. Confirmaciones de Integridad

| Confirmación | Estado |
|--------------|--------|
| No se modificó Sistema_Empresas | ✅ CONFIRMADO (sigue con 5 empresas) |
| No se crearon empresas nuevas | ✅ CONFIRMADO |
| No se ejecutó UPDATE | ✅ CONFIRMADO |
| No se ejecutó DELETE | ✅ CONFIRMADO |
| No hay aliases duplicados activos | ✅ CONFIRMADO |
| No hay relaciones duplicadas activas | ✅ CONFIRMADO |
| Todas las FK apuntan correctamente | ✅ CONFIRMADO |
| ServidorID son reales (no inventados) | ✅ CONFIRMADO |

---

## 14. Confirmaciones de Alcance

| Confirmación | Estado |
|--------------|--------|
| No se modificó código backend | ✅ CONFIRMADO |
| No se modificó frontend | ✅ CONFIRMADO |
| No se modificaron jobs | ✅ CONFIRMADO |
| No se tocó Tablero Ejecutivo | ✅ CONFIRMADO |
| No se tocó módulo Comercial | ✅ CONFIRMADO |
| No se tocó módulo Compras | ✅ CONFIRMADO |
| No se tocó módulo Finanzas | ✅ CONFIRMADO |
| No se tocó módulo Operaciones/Inventarios | ✅ CONFIRMADO |
| No se tocó RBAC/Auth | ✅ CONFIRMADO |
| No se reactivaron conexiones LIVE | ✅ CONFIRMADO |
| No se usó MongoDB como fuente | ✅ CONFIRMADO |
| No se usaron datos mock | ✅ CONFIRMADO |
| No se implementó EmpresaResolver | ✅ CONFIRMADO |
| No se refactorizó adapters.py | ✅ CONFIRMADO |
| No se refactorizó mpro.py | ✅ CONFIRMADO |
| No se refactorizó service.py | ✅ CONFIRMADO |

---

## 15. Riesgos Pendientes

| Riesgo | Probabilidad | Impacto | Estado |
|--------|--------------|---------|--------|
| Aliases legacy no mapeados en datos operativos | Media | Bajo | Pendiente EmpresaResolver |
| Registros duplicados en Comercial_Ventas_Dia_Abiertas_v2 | Baja | Medio | Pendiente limpieza post-migración |
| Jobs aún usan comparación textual | Alta | Alto | Pendiente refactorización |

---

## 16. Siguiente Fase Recomendada

1. **P0**: Implementar `EmpresaResolver` en backend
   - Función `normalize_alias(texto: str) -> str`
   - Función `resolve_empresa_by_alias(alias: str) -> int`
   - Función `get_empresa_connections(empresa_id: int) -> list`

2. **P0**: Refactorizar `adapters.py` para usar `EmpresaResolver`
   - Eliminar comparaciones LIKE
   - Eliminar hardcoding de nombres

3. **P1**: Refactorizar jobs del scheduler para usar `EmpresaResolver`

4. **P2**: Limpieza de registros legacy duplicados en tablas operativas

**NOTA**: Estas fases requieren autorización explícita antes de proceder.

---

## 17. Resumen de Ejecución

| Métrica | Valor |
|---------|-------|
| Registros insertados en Sistema_Tipos | 5 |
| Registros insertados en Sistema_EmpresasAlias | 12 |
| Registros insertados en Sistema_EmpresasServidores | 7 |
| Registros rechazados por duplicado | 14 (comportamiento esperado) |
| Errores de FK | 0 |
| Errores de integridad | 0 |
| Sistema_Empresas modificada | NO |
| Código modificado | NO |

---

**FIN DEL REPORTE DE EJECUCIÓN**

DML ejecutado exitosamente. Esperando autorización para siguiente fase.
