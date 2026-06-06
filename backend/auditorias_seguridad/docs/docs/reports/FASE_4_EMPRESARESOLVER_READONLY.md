# FASE 4: EmpresaResolver Read-Only

**Fecha**: 2026-05-16  
**Estado**: ✅ IMPLEMENTADO Y VALIDADO  
**Rol**: Arquitecto Senior EDARSAHUB / DBA SQL Server  
**Tipo de Documento**: Reporte de Implementación

---

## 1. Resumen Ejecutivo

Se implementó exitosamente el componente `EmpresaResolver` en modo read-only, el cual proporciona una interfaz centralizada para resolver empresas, aliases, servidores, tipos de sistema, roles de conexión y sucursales desde EDARSAHUB SQL.

### Resultado:
- ✅ 8 funciones implementadas
- ✅ 15/15 pruebas de normalización pasaron
- ✅ 16/16 pruebas de resolución de aliases pasaron
- ✅ 7/7 pruebas de conexiones pasaron
- ✅ Health check: STATUS=OK
- ✅ No se modificaron módulos funcionales
- ✅ No se consulta MongoDB como fuente autoritativa

---

## 2. Archivo Creado

```
/app/backend/core/empresa_resolver.py
```

---

## 3. Funciones Implementadas

| # | Función | Descripción |
|---|---------|-------------|
| 1 | `normalize_alias(texto)` | Normaliza un alias: mayúsculas, sin acentos, sin °, guiones→espacio |
| 2 | `resolve_empresa_by_alias(alias)` | Busca alias en Sistema_EmpresasAlias, retorna EmpresaInfo |
| 3 | `resolve_empresa_by_id(empresa_id)` | Obtiene datos canónicos de Sistema_Empresas |
| 4 | `get_empresa_connections(empresa_id)` | Retorna todas las conexiones activas de una empresa |
| 5 | `get_connection_for_role(empresa_id, rol)` | Retorna conexión específica por rol |
| 6 | `get_system_branch_context(empresa_id, rol)` | Retorna contexto completo empresa-servidor-sucursal |
| 7 | `validate_no_ambiguous_alias(alias)` | Valida que un alias no apunte a múltiples empresas |
| 8 | `health_check_empresa_resolver()` | Valida estado del resolver y tablas canónicas |

### Funciones Auxiliares:
- `get_all_empresas()` - Lista todas las empresas activas
- `get_all_aliases_for_empresa(empresa_id)` - Lista aliases de una empresa
- `get_sistema_tipos()` - Lista tipos de sistema activos

---

## 4. Tablas Consultadas

| Tabla | Uso |
|-------|-----|
| Sistema_Empresas | Datos canónicos de empresas |
| Sistema_EmpresasAlias | Mapeo alias → EmpresaID |
| Sistema_EmpresasServidores | Relación empresa-servidor-rol-sucursal |
| Sistema_Tipos | Tipos de sistema (SoftRestaurant, MPRO, etc.) |
| Servidores_Conexiones | Datos de servidores |

---

## 5. Confirmaciones de Cumplimiento

| Confirmación | Estado |
|--------------|--------|
| No consulta MongoDB como fuente autoritativa | ✅ |
| No se modificó Tablero Ejecutivo | ✅ |
| No se modificó módulo Comercial | ✅ |
| No se modificó módulo Compras | ✅ |
| No se modificó módulo Finanzas | ✅ |
| No se modificó módulo Operaciones/Inventarios | ✅ |
| No se modificó RBAC/Auth | ✅ |
| No se modificó frontend | ✅ |
| No se modificaron jobs | ✅ |
| No se modificó adapters.py | ✅ |
| No se modificó mpro.py | ✅ |
| No se modificó service.py | ✅ |
| No se ejecutó DDL | ✅ |
| No se ejecutó DML | ✅ |
| No se reactivaron conexiones LIVE | ✅ |

---

## 6. Aliases Insertados vs Esperados

### 6.1 Aliases Insertados (12 registros)

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

### 6.2 Aliases Omitidos (14 registros)

| EmpresaID | Alias Propuesto | AliasNormalizado | Motivo Omisión |
|-----------|-----------------|------------------|----------------|
| 1 | Origen | ORIGEN | Duplicado (ya existe "ORIGEN") |
| 1 | origen | ORIGEN | Duplicado (ya existe "ORIGEN") |
| 2 | 130 QRO | 130QRO | Duplicado (ya existe "130QRO") |
| 2 | 130-QRO | 130QRO | Duplicado (ya existe "130QRO") |
| 2 | 130° QRO | 130QRO | Duplicado (ya existe "130QRO") |
| 2 | 130° QUERETARO | 130QUERETARO | Duplicado (ya existe "130 QUERETARO") |
| 3 | Cienfuegos | CIENFUEGOS | Duplicado (ya existe "CIENFUEGOS") |
| 4 | LA-ESTELAR | LAESTELAR | Duplicado (ya existe "LA ESTELAR") |
| 4 | La Estelar | LAESTELAR | Duplicado (ya existe "LA ESTELAR") |
| 5 | 130 MID | 130MID | Duplicado (ya existe "130MID") |
| 5 | 130 MER | 130MER | Duplicado (ya existe "130-MER") |
| 5 | 130° MERIDA | 130MERIDA | Duplicado (ya existe "130 MERIDA") |
| 5 | 130° MÉRIDA | 130MERIDA | Duplicado (ya existe "130 MERIDA") |

**Confirmación**: Todas las omisiones fueron por **duplicidad del AliasNormalizado** (índice único `IX_EmpresasAlias_Normalizado_Activo`). Esto es comportamiento correcto del diseño.

### 6.3 Impacto de Aliases Omitidos

**Ninguno**. La función `normalize_alias()` transforma cualquier variante al mismo valor normalizado:

| Entrada | Normalizado | Resuelve a |
|---------|-------------|------------|
| 130-QRO | 130QRO | ✅ EmpresaID=2 (130QRO) |
| 130 QRO | 130QRO | ✅ EmpresaID=2 (130QRO) |
| 130° QRO | 130QRO | ✅ EmpresaID=2 (130QRO) |
| Origen | ORIGEN | ✅ EmpresaID=1 (ORIGEN) |
| origen | ORIGEN | ✅ EmpresaID=1 (ORIGEN) |
| LA-ESTELAR | LAESTELAR | ✅ EmpresaID=4 (ESTELAR) |
| La Estelar | LAESTELAR | ✅ EmpresaID=4 (ESTELAR) |

---

## 7. Pruebas de Normalización

| # | Entrada | Esperado | Resultado | Status |
|---|---------|----------|-----------|--------|
| 1 | 130-MER | 130MER | 130MER | ✅ |
| 2 | 130 MER | 130MER | 130MER | ✅ |
| 3 | 130-QRO | 130QRO | 130QRO | ✅ |
| 4 | 130° QRO | 130QRO | 130QRO | ✅ |
| 5 | LA ESTELAR | LAESTELAR | LAESTELAR | ✅ |
| 6 | LA-ESTELAR | LAESTELAR | LAESTELAR | ✅ |
| 7 | La Estelar | LAESTELAR | LAESTELAR | ✅ |
| 8 | ORIGEN | ORIGEN | ORIGEN | ✅ |
| 9 | Origen | ORIGEN | ORIGEN | ✅ |
| 10 | origen | ORIGEN | ORIGEN | ✅ |
| 11 | CIENFUEGOS | CIENFUEGOS | CIENFUEGOS | ✅ |
| 12 | Cienfuegos | CIENFUEGOS | CIENFUEGOS | ✅ |
| 13 | 130° MÉRIDA | 130MERIDA | 130MERIDA | ✅ |
| 14 | 130° QUERETARO | 130QUERETARO | 130QUERETARO | ✅ |
| 15 | QRO | QRO | QRO | ✅ |

**Resultado**: 15/15 ✅

---

## 8. Pruebas de Resolución Alias → EmpresaID

| # | Alias | EmpresaID Esperado | Código Esperado | Resultado | Status |
|---|-------|-------------------|-----------------|-----------|--------|
| 1 | 130-MER | 5 | 130MID | EmpresaID=5 | ✅ |
| 2 | 130 MER | 5 | 130MID | EmpresaID=5 | ✅ |
| 3 | 130-QRO | 2 | 130QRO | EmpresaID=2 | ✅ |
| 4 | QRO | 2 | 130QRO | EmpresaID=2 | ✅ |
| 5 | LA ESTELAR | 4 | ESTELAR | EmpresaID=4 | ✅ |
| 6 | LA-ESTELAR | 4 | ESTELAR | EmpresaID=4 | ✅ |
| 7 | ESTELAR | 4 | ESTELAR | EmpresaID=4 | ✅ |
| 8 | ORIGEN | 1 | ORIGEN | EmpresaID=1 | ✅ |
| 9 | Origen | 1 | ORIGEN | EmpresaID=1 | ✅ |
| 10 | CIENFUEGOS | 3 | CIENFUEGOS | EmpresaID=3 | ✅ |
| 11 | CF | 3 | CIENFUEGOS | EmpresaID=3 | ✅ |
| 12 | 130MID | 5 | 130MID | EmpresaID=5 | ✅ |
| 13 | 130QRO | 2 | 130QRO | EmpresaID=2 | ✅ |
| 14 | 130 MERIDA | 5 | 130MID | EmpresaID=5 | ✅ |
| 15 | 130 QUERETARO | 2 | 130QRO | EmpresaID=2 | ✅ |
| 16 | QUERETARO | 2 | 130QRO | EmpresaID=2 | ✅ |

**Resultado**: 16/16 ✅

---

## 9. Pruebas de Resolución EmpresaID → Servidor/Rol/Sucursal

| # | Empresa | Rol | Servidor Esperado | Sucursal Esperada | Resultado | Status |
|---|---------|-----|-------------------|-------------------|-----------|--------|
| 1 | ORIGEN | PRINCIPAL_SQL | ManagmentPro | 23/0023 | ManagmentPro, 23/0023 | ✅ |
| 2 | ORIGEN | VENTAS_DIA_API_LOCAL | ORIGEN LOCAL | 23/0023 | ORIGEN LOCAL, 23/0023 | ✅ |
| 3 | 130QRO | PRINCIPAL_SQL | ManagmentPro | 21/0021 | ManagmentPro, 21/0021 | ✅ |
| 4 | 130QRO | VENTAS_DIA_API_LOCAL | 130° QRO LOCAL | 21/0021 | 130° QRO LOCAL, 21/0021 | ✅ |
| 5 | 130MID | PRINCIPAL_SQL | 130° MERIDA | NULL | 130° MERIDA, NULL | ✅ |
| 6 | CIENFUEGOS | PRINCIPAL_SQL | CIENFUEGOS | NULL | CIENFUEGOS, NULL | ✅ |
| 7 | ESTELAR | PRINCIPAL_SQL | LA ESTELAR | NULL | LA ESTELAR, NULL | ✅ |

**Resultado**: 7/7 ✅

---

## 10. Validación ORIGEN Sucursal 23

| Campo | Valor |
|-------|-------|
| EmpresaID | 1 |
| CodigoEmpresa | ORIGEN |
| ServidorID | 1B230A06-FFAF-4C70-BD27-B1BE3579DEA6 |
| NombreServidor | ManagmentPro |
| RolConexion | PRINCIPAL_SQL |
| NumeroSucursalSistema | **23** ✅ |
| CodigoSucursalSistema | **0023** ✅ |

---

## 11. Validación 130QRO Sucursal 21

| Campo | Valor |
|-------|-------|
| EmpresaID | 2 |
| CodigoEmpresa | 130QRO |
| ServidorID | 1B230A06-FFAF-4C70-BD27-B1BE3579DEA6 |
| NombreServidor | ManagmentPro |
| RolConexion | PRINCIPAL_SQL |
| NumeroSucursalSistema | **21** ✅ |
| CodigoSucursalSistema | **0021** ✅ |

---

## 12. Validación APIs Locales con VENTAS_DIA_API_LOCAL

| Empresa | ServidorID | Servidor | RolConexion |
|---------|------------|----------|-------------|
| ORIGEN | 817A0AA8-6170-4738-A8F6-A72AC36BA0DF | ORIGEN LOCAL | **VENTAS_DIA_API_LOCAL** ✅ |
| 130QRO | 72F6E9A7-8EA2-4EB2-802E-4EE31753435E | 130° QRO LOCAL | **VENTAS_DIA_API_LOCAL** ✅ |

**Confirmación**: Las APIs locales NO usan PRINCIPAL_SQL.

---

## 13. Validación SoftRestaurant con NumeroSucursalSistema NULL

| Empresa | Servidor | NumeroSucursalSistema |
|---------|----------|----------------------|
| 130MID | 130° MERIDA | **NULL** ✅ |
| CIENFUEGOS | CIENFUEGOS | **NULL** ✅ |
| ESTELAR | LA ESTELAR | **NULL** ✅ |

---

## 14. Health Check Result

```
Status: OK
Empresas: 5
Aliases: 12
Servidores: 13
Relaciones: 7
ORIGEN OK: True
130QRO OK: True
130MID OK: True
CIENFUEGOS OK: True
ESTELAR OK: True
Errores: []
```

---

## 15. Riesgos Pendientes

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Aliases no cubiertos en datos legacy | Media | Bajo | Se pueden agregar más aliases si se detectan |
| SistemaTipoID no poblado en Sistema_EmpresasServidores | Baja | Bajo | Agregar DML para poblar FK cuando se autorice |
| Módulos funcionales aún usan comparación textual | Alta | Alto | Siguiente fase: refactorizar adapters.py |

---

## 16. Siguiente Fase Recomendada

1. **P0**: Refactorizar `adapters.py` para usar `EmpresaResolver`
   - Eliminar comparaciones LIKE, contains, split
   - Usar `resolve_empresa_by_alias()` para traducir nombres

2. **P0**: Refactorizar `service.py` para usar `EmpresaResolver`
   - Resolver unidades de negocio por ID, no por texto

3. **P0**: Refactorizar jobs del scheduler para usar `EmpresaResolver`

4. **P1**: Agregar endpoint REST para exponer el resolver (opcional)

5. **P2**: Poblar `SistemaTipoID` en `Sistema_EmpresasServidores`

**NOTA**: Estas fases requieren autorización explícita antes de proceder.

---

## 17. Dataclasses Disponibles

```python
@dataclass
class EmpresaInfo:
    empresa_id: int
    codigo_empresa: str
    nombre_comercial: str
    nombre_empresa: str
    activo: bool

@dataclass
class ConnectionInfo:
    empresa_servidor_id: int
    empresa_id: int
    servidor_id: str
    nombre_servidor: str
    sistema_tipo: Optional[str]
    rol_conexion: str
    numero_sucursal_sistema: Optional[int]
    codigo_sucursal_sistema: Optional[str]
    nombre_sucursal_sistema: Optional[str]
    prioridad: int
    es_principal: bool
    activo: bool

@dataclass
class SystemBranchContext:
    empresa_id: int
    codigo_empresa: str
    nombre_comercial: str
    servidor_id: str
    nombre_servidor: str
    sistema_tipo: Optional[str]
    rol_conexion: str
    numero_sucursal_sistema: Optional[int]
    codigo_sucursal_sistema: Optional[str]
    nombre_sucursal_sistema: Optional[str]

@dataclass
class HealthCheckResult:
    status: str  # OK, WARNING, ERROR
    empresas_count: int
    aliases_count: int
    servidores_count: int
    relaciones_count: int
    origen_ok: bool
    qro_ok: bool
    mid_ok: bool
    cienfuegos_ok: bool
    estelar_ok: bool
    errors: List[str]
```

---

**FIN DEL REPORTE**

EmpresaResolver implementado y validado en modo read-only. Esperando autorización para siguiente fase.
