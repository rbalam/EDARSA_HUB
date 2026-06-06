# DIAGNÓSTICO PASIVO — ALIASES Y ESTANDARIZACIÓN DE UNIDADES DE NEGOCIO

**Fecha:** 2026-05-15  
**Generado por:** Diagnóstico Automatizado EDARSAHUB  
**Estado:** SOLO LECTURA - No se modificó código ni base de datos

---

## 1. Resumen Ejecutivo

Se realizó un diagnóstico pasivo completo para detectar aliases, variantes y dependencias textuales utilizadas para identificar unidades de negocio en EDARSAHUB. Se encontraron **múltiples inconsistencias críticas** que requieren normalización urgente.

### Hallazgos Principales:
- **5 unidades de negocio canónicas** identificadas con **múltiples aliases cada una**
- **Matching textual riesgoso** encontrado en módulos de Comercial y Adapters
- **Inconsistencia entre MongoDB y SQL** en nombres y códigos
- **APIs locales** con dependencia de `sucursal_destino` basado en texto
- **No existe tabla centralizada de aliases** en EDARSAHUB SQL

### Riesgo General: **CRÍTICO**
La lógica funcional de ventas, KPIs e inventarios depende de matching textual flexible, lo cual puede causar pérdida o duplicación de datos.

---

## 2. Problema Detectado

### 2.1 Fragmentación de Identidad
Cada unidad de negocio tiene múltiples representaciones:
- Códigos canónicos (`130QRO`, `ORIGEN`)
- Códigos con variantes (`130-QRO`, `130_qro`, `130 QRO`)
- Nombres visibles (`130° QUERÉTARO`, `130 GRADOS QUERETARO`)
- Nombres en MongoDB (`130 QRO`, `130° QUERETARO`)
- Nombres en APIs locales (`QUERETARO`, `QRO`)

### 2.2 Matching Textual Riesgoso
Se encontró código que usa comparaciones flexibles:
```python
# En adapters.py línea 306:
if sucursal_destino in sucursal_actual or sucursal_actual in sucursal_destino:
```

Este tipo de matching puede causar:
- Falsos positivos (CIENFUEGOS match con CIENFUEGOS TABLAJERIA)
- Falsos negativos (QUERÉTARO vs QUERETARO)

### 2.3 Inconsistencia de Server IDs
ORIGEN y 130QRO comparten el mismo `server_id` (ManagmentPro central) pero tienen diferentes `sucursal_origen_id`:
- ORIGEN → `0023`
- 130QRO → `0021`

Sin embargo, también existen APIs locales separadas:
- ORIGEN LOCAL → `817a0aa8-6170-4738-a8f6-a72ac36ba0df`
- 130° QRO LOCAL → `72f6e9a7-8ea2-4eb2-802e-4ee31753435e`

---

## 3. Inventario de Unidades Canónicas Propuestas

| # | Código Canónico | Nombre Visible | Sistema | NumSucursal MPRO |
|---|-----------------|----------------|---------|------------------|
| 1 | ORIGEN | Origen | MPRO | 0023 |
| 2 | 130QRO | 130 Grados Querétaro | MPRO | 0021 |
| 3 | 130MID | 130 Grados Mérida | SoftRestaurant | NULL |
| 4 | CIENFUEGOS | Cienfuegos | SoftRestaurant | NULL |
| 5 | ESTELAR | La Estelar | SoftRestaurant | NULL |

---

## 4. Aliases Encontrados por Unidad

### 4.1 ORIGEN
| Alias | Fuente | Archivo/Colección |
|-------|--------|-------------------|
| `ORIGEN` | Código oficial | Unidades_Negocio SQL |
| `Origen` | Nombre visible | Frontend |
| `origen` | Lowercase | service.py:133 |
| `0023` | NumSucursal MPRO | server_sucursales_config |
| `ORIGEN LOCAL` | API Local | Servidores_Conexiones |

### 4.2 130QRO (QUERÉTARO)
| Alias | Fuente | Archivo/Colección |
|-------|--------|-------------------|
| `130QRO` | Código oficial | Unidades_Negocio SQL |
| `130-QRO` | Legacy | carga_historica_abril_2026.py:109 |
| `130_qro` | Underscore | service.py:1236 |
| `130 QRO` | Con espacio | MongoDB empresas |
| `130° QRO` | Con símbolo | Frontend |
| `130° QUERETARO` | Nombre completo | server_sucursales_config |
| `130° QRO LOCAL` | API Local | Servidores_Conexiones |
| `QUERETARO` | sucursal_destino | api_connections_cache |
| `QUERÉTARO` | Con tilde | queries/softrestaurant.py:262 |
| `0021` | NumSucursal MPRO | server_sucursales_config |

### 4.3 130MID (MÉRIDA)
| Alias | Fuente | Archivo/Colección |
|-------|--------|-------------------|
| `130MID` | Código oficial | Unidades_Negocio SQL |
| `130-MER` | Legacy | service.py:979 |
| `130-MID` | Variante | repository_readonly.py:188 |
| `130 MID` | Con espacio | MongoDB empresas |
| `130° MERIDA` | Sin tilde | MongoDB servers |
| `130° MÉRIDA` | Con tilde | carga_historica_abril_2026.py:21 |
| `MERIDA` | Simplificado | queries/softrestaurant.py:262 |
| `MÉRIDA` | Con tilde | repository_readonly.py:206 |

### 4.4 CIENFUEGOS
| Alias | Fuente | Archivo/Colección |
|-------|--------|-------------------|
| `CIENFUEGOS` | Código oficial | Unidades_Negocio SQL |
| `Cienfuegos` | Title case | rh/importador/service.py:2 |
| `CIEN FUEGOS` | Con espacio | server_sucursales_config (0027) |
| `CIENFUEGOS TABLAJERIA` | Relacionado | MongoDB servers |
| `CF` | Abreviación | (no encontrado en código) |

### 4.5 ESTELAR
| Alias | Fuente | Archivo/Colección |
|-------|--------|-------------------|
| `ESTELAR` | Código oficial | Unidades_Negocio SQL |
| `LA-ESTELAR` | Legacy | service.py:981 |
| `LA ESTELAR` | Nombre completo | MongoDB servers |
| `La Estelar` | Title case | (documentación) |

---

## 5. Dependencias Encontradas en Código

### 5.1 Riesgo CRÍTICO - Matching Textual en Adapters

**Archivo:** `/app/backend/modules/comercial/adapters.py`

```python
# Línea 306 - CRÍTICO
if sucursal_destino in sucursal_actual or sucursal_actual in sucursal_destino:
    # Puede matchear incorrectamente

# Línea 363 - CRÍTICO  
if sucursal_destino in sucursal_actual or sucursal_actual in sucursal_destino:
    # Mismo problema
```

**Riesgo:** La lógica de APIs locales depende de comparación de substrings, lo cual puede causar:
- `CIENFUEGOS` matchea con `CIENFUEGOS TABLAJERIA`
- `QUERETARO` no matchea con `QUERÉTARO` (con tilde)

### 5.2 Riesgo ALTO - Mapeo Hardcodeado

**Archivo:** `/app/backend/modules/comercial/service.py`

```python
# Línea 979-981 - ALTO
UNIDAD_FORMATO_MAP = {
    '130MID': '130-MER',
    'CIENFUEGOS': 'CIENFUEGOS',
    'ESTELAR': 'LA-ESTELAR',
}

# Línea 1235-1236 - ALTO
sucursales_mpro = [
    {"api_key": "origen", "sucursal_origen_id": "0023"},
    {"api_key": "130_qro", "sucursal_origen_id": "0021"},
]
```

### 5.3 Riesgo ALTO - LIKE en Queries SQL

**Archivo:** `/app/backend/modules/comercial/queries/mpro.py`

```python
# Línea 322 - ALTO
sucursal_filter = f" AND S.Sc_Descripcion LIKE '%{sucursal}%'"

# Línea 466 - ALTO
f"OR {alias_sucursal}.Sc_Descripcion LIKE '%{sucursal}%')"
```

### 5.4 Riesgo MEDIO - Normalización Incompleta

**Archivo:** `/app/backend/modules/comercial_v2/repository_readonly.py`

```python
# Línea 206-219 - Intento de normalización pero incompleto
CASE 
    WHEN UPPER(unidad_negocio_nombre) LIKE '%MERIDA%' 
      OR UPPER(unidad_negocio_nombre) LIKE '%MÉRIDA%' THEN '130° MERIDA'
    WHEN UPPER(unidad_negocio_nombre) LIKE '%CIENFUEGOS%' THEN 'CIENFUEGOS'
    WHEN UPPER(unidad_negocio_nombre) LIKE '%ESTELAR%' THEN 'ESTELAR'
```

**Problema:** No maneja todos los casos y no está centralizado.

---

## 6. Dependencias Encontradas en MongoDB

### 6.1 Colección `empresas`
| Código | Nombre |
|--------|--------|
| `ORIGEN` | `ORIGEN` |
| `130QRO` | `130 QRO` ← Inconsistente (espacio) |
| `CIENFUEGOS` | `CIENFUEGOS` |
| `ESTELAR` | `LA ESTELAR` ← Incluye "LA" |
| `130MID` | `130 MID` ← Inconsistente (espacio) |

### 6.2 Colección `servers`
| Nombre | System Type |
|--------|-------------|
| `ManagmentPro` | `MPRO` ← Sin "e" (typo persistente) |
| `CIENFUEGOS` | `SoftRestaurant` |
| `LA ESTELAR` | `SoftRestaurant` |
| `130° MERIDA` | `SoftRestaurant` ← Sin tilde |

### 6.3 Colección `server_sucursales_config`
| sucursal_nombre | sucursal_origen_id | server_id |
|-----------------|-------------------|-----------|
| `130° QUERETARO` | `0021` | ManagmentPro |
| `ORIGEN` | `0023` | ManagmentPro |
| `CIEN FUEGOS` | `0027` | ManagmentPro ← Con espacio, ID diferente |

### 6.4 Colección `api_connections_cache`
| name | sucursal_destino | tipo_conexion |
|------|------------------|---------------|
| `130° QRO LOCAL` | `QUERETARO` | `API_LOCAL` |
| `ORIGEN LOCAL` | `ORIGEN` | `API_LOCAL` |
| `CHAPUR NORTE` | `CHAPUR` | `API_LOCAL` |

---

## 7. Dependencias Encontradas en EDARSAHUB SQL

### 7.1 Tabla `Unidades_Negocio`
| codigo | nombre | server_id | sucursal_origen_id |
|--------|--------|-----------|-------------------|
| `ORIGEN` | `ORIGEN` | ManagmentPro | `0023` |
| `130QRO` | `130° QUERETARO` | ManagmentPro | `0021` |
| `CIENFUEGOS` | `CIENFUEGOS` | (su propio server) | NULL |
| `ESTELAR` | `LA ESTELAR` | (su propio server) | NULL |
| `130MID` | `130° MERIDA` | (su propio server) | NULL |

### 7.2 Tabla `Servidores_Conexiones` (APIs Locales)
| nombre | tipo_conexion | api_url |
|--------|---------------|---------|
| `130° QRO LOCAL` | `API_LOCAL` | http://<REDACTED_EDARSAHUB_SQL_HOST>:8001/query |
| `ORIGEN LOCAL` | `API_LOCAL` | http://<REDACTED_EDARSAHUB_SQL_HOST>:8000/query |

### 7.3 Tabla `Sistema_EmpresasMongoMap`
| CodigoEmpresa | NombreEmpresa | EmpresaMongoUUID |
|---------------|---------------|------------------|
| `ORIGEN` | `ORIGEN` | 31784356-... |
| `130QRO` | `130 QRO` | 1118f83c-... |
| `CIENFUEGOS` | `CIENFUEGOS` | 1d91f076-... |
| `ESTELAR` | `LA ESTELAR` | e302e16f-... |
| `130MID` | `130 MID` | a4d8b5e7-... |

---

## 8. APIs Locales MPRO Detectadas

### 8.1 Configuración en EDARSAHUB SQL
| ID | Nombre | URL | Destino |
|----|--------|-----|---------|
| `72f6e9a7-...` | 130° QRO LOCAL | http://<REDACTED_EDARSAHUB_SQL_HOST>:8001/query | QUERETARO |
| `817a0aa8-...` | ORIGEN LOCAL | http://<REDACTED_EDARSAHUB_SQL_HOST>:8000/query | ORIGEN |

### 8.2 Configuración Hardcodeada en sync_comercial_abiertas_v2_job.py
```python
MPRO_API_LOCAL_CONFIG = {
    "ORIGEN": {
        "server_config_name": "ORIGEN LOCAL",
        "sucursal_id": "0001",  # ⚠️ INCONSISTENTE con 0023
    },
    "130QRO": {
        "server_config_name": "130° QRO LOCAL",
        "sucursal_id": "0021",
    }
}
```

**⚠️ ALERTA:** El hardcode de `sucursal_id: "0001"` para ORIGEN es inconsistente con `sucursal_origen_id: "0023"` en la base de datos.

---

## 9. Riesgos por Módulo

| Módulo | Nivel | Descripción |
|--------|-------|-------------|
| **Comercial** | CRÍTICO | Matching textual en adapters.py |
| **Comercial_v2** | ALTO | repository_readonly.py con LIKE |
| **Scheduler Jobs** | ALTO | MPRO_API_LOCAL_CONFIG hardcodeado |
| **Frontend** | MEDIO | Dependencia de nombres visibles |
| **RH/Importador** | BAJO | Referencias a "Excel Cienfuegos" |
| **Fase2 Operativo** | BAJO | Referencias documentales |

---

## 10. Matriz de Normalización Recomendada

### 10.1 Mapeo Canónico Propuesto

| Código Canónico | Nombre Oficial | Aliases a Normalizar |
|-----------------|----------------|---------------------|
| `ORIGEN` | Origen | origen, ORIGEN, Origen |
| `130QRO` | 130 Grados Querétaro | 130-QRO, 130_qro, 130 QRO, 130° QRO, 130° QUERETARO, QUERETARO, QUERÉTARO |
| `130MID` | 130 Grados Mérida | 130-MER, 130-MID, 130 MID, 130° MERIDA, 130° MÉRIDA, MERIDA, MÉRIDA |
| `CIENFUEGOS` | Cienfuegos | CIENFUEGOS, Cienfuegos, CIEN FUEGOS |
| `ESTELAR` | La Estelar | ESTELAR, LA-ESTELAR, LA ESTELAR, La Estelar |

### 10.2 Reglas de Normalización

1. **Convertir a mayúsculas**
2. **Quitar acentos:** É→E, Á→A, Í→I, Ó→O, Ú→U
3. **Quitar símbolos:** °, -, _, .
4. **Quitar prefijos:** "LA ", "EL "
5. **Quitar espacios múltiples**
6. **Trim**

**Ejemplo:**
```
"130° QUERÉTARO" 
→ "130 QUERETARO" (sin símbolo, sin tilde)
→ "130QUERETARO" (sin espacios)
→ código canónico: "130QRO"
```

---

## 11. Propuesta de Tablas SQL Futuras (Sin Ejecutar)

### 11.1 Sistema_EmpresasAlias
```sql
-- NO EJECUTAR - Solo propuesta
CREATE TABLE Sistema_EmpresasAlias (
    AliasID INT IDENTITY(1,1) PRIMARY KEY,
    EmpresaID INT NOT NULL REFERENCES Sistema_Empresas(EmpresaID),
    Alias NVARCHAR(100) NOT NULL,
    AliasNormalizado AS (
        UPPER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
            Alias, 'Á','A'), 'É','E'), 'Í','I'), 'Ó','O'), 'Ú','U'
        ))
    ) PERSISTED,
    TipoAlias NVARCHAR(50) NOT NULL, -- CODIGO, NOMBRE, LEGACY, API_KEY
    OrigenAlias NVARCHAR(100), -- MongoDB, Frontend, API_LOCAL
    Activo BIT NOT NULL DEFAULT 1,
    FechaCreacion DATETIME2 DEFAULT SYSUTCDATETIME(),
    CONSTRAINT UQ_EmpresaAlias UNIQUE (AliasNormalizado)
);
```

### 11.2 Sistema_EmpresasServidores
```sql
-- NO EJECUTAR - Solo propuesta
CREATE TABLE Sistema_EmpresasServidores (
    MapeoID INT IDENTITY(1,1) PRIMARY KEY,
    EmpresaID INT NOT NULL REFERENCES Sistema_Empresas(EmpresaID),
    ServidorID UNIQUEIDENTIFIER NOT NULL REFERENCES Servidores_Conexiones(id),
    RolConexion NVARCHAR(50) NOT NULL, -- DATA_SOURCE, API_LOCAL_VENTAS, REPLICA
    NumSucursalSistema NVARCHAR(10), -- 0021, 0023, NULL para SoftRestaurant
    EsPrincipal BIT NOT NULL DEFAULT 0,
    Activo BIT NOT NULL DEFAULT 1,
    FechaCreacion DATETIME2 DEFAULT SYSUTCDATETIME(),
    CONSTRAINT UQ_EmpresaServidor UNIQUE (EmpresaID, ServidorID, RolConexion)
);
```

---

## 12. Reglas de Normalización - Función Conceptual

```python
# NO EJECUTAR - Solo propuesta conceptual
import unicodedata
import re

def normalizar_alias(alias: str) -> str:
    """
    Normaliza un alias para búsqueda.
    NO usar como llave principal, solo para resolución hacia EmpresaID.
    """
    if not alias:
        return ""
    
    # 1. Mayúsculas
    resultado = alias.upper()
    
    # 2. Quitar acentos
    resultado = unicodedata.normalize('NFD', resultado)
    resultado = ''.join(c for c in resultado if unicodedata.category(c) != 'Mn')
    
    # 3. Quitar símbolos
    resultado = resultado.replace('°', '')
    resultado = resultado.replace('-', '')
    resultado = resultado.replace('_', '')
    resultado = resultado.replace('.', '')
    
    # 4. Quitar prefijos comunes
    resultado = re.sub(r'^(LA |EL |LOS |LAS )', '', resultado)
    
    # 5. Quitar espacios
    resultado = ''.join(resultado.split())
    
    return resultado

def resolver_empresa(alias: str) -> int:
    """
    Resuelve un alias a EmpresaID.
    Busca primero en Sistema_EmpresasAlias por AliasNormalizado.
    """
    alias_norm = normalizar_alias(alias)
    # Buscar en Sistema_EmpresasAlias WHERE AliasNormalizado = alias_norm
    # Retornar EmpresaID o None
    pass
```

---

## 13. Plan de Implementación Recomendado por Fases

### Fase A: Diagnóstico y Catálogo (✓ COMPLETADA)
- [x] Escaneo de código
- [x] Escaneo de MongoDB
- [x] Escaneo de EDARSAHUB SQL
- [x] Generación de este reporte

### Fase B: DDL Pasivo
- [ ] Crear tabla `Sistema_EmpresasAlias`
- [ ] Crear tabla `Sistema_EmpresasServidores`
- [ ] Crear índices de búsqueda
- [ ] NO migrar datos aún

### Fase C: Carga Inicial de Aliases
- [ ] Insertar aliases conocidos desde este diagnóstico
- [ ] Validar unicidad
- [ ] Documentar conflictos

### Fase D: Resolver Central EmpresaResolver
- [ ] Crear función `resolve_empresa_id(alias)`
- [ ] Implementar cache en memoria
- [ ] Agregar logs de resolución fallida

### Fase E: Migración Gradual de Módulos
- [ ] Actualizar `adapters.py` (CRÍTICO)
- [ ] Actualizar `repository_readonly.py`
- [ ] Actualizar `sync_comercial_abiertas_v2_job.py`
- [ ] Eliminar hardcodes

### Fase F: Eliminación de Matching Textual
- [ ] Reemplazar `sucursal_destino in sucursal_actual`
- [ ] Reemplazar `LIKE '%texto%'`
- [ ] Validar con tests

---

## 14. Validaciones Obligatorias

### Confirmaciones de Diagnóstico Pasivo:
- [x] **No se modificó código**
- [x] **No se modificó base de datos**
- [x] **No se tocaron módulos protegidos** (Tablero Ejecutivo, Comercial, Compras, Finanzas, Operaciones, RBAC)
- [x] **No se alteraron endpoints**
- [x] **No se eliminó MongoDB**
- [x] **Solo se generó reporte de lectura**

---

## 15. Próximos Pasos Recomendados

1. **Revisar y aprobar** este diagnóstico con el equipo
2. **Priorizar** la corrección de `adapters.py` (riesgo CRÍTICO)
3. **Crear las tablas** propuestas en Fase B
4. **Implementar** EmpresaResolver centralizado
5. **Migrar** módulos gradualmente

---

**FIN DEL DIAGNÓSTICO**

*Este documento es de solo lectura y no implica ningún cambio en el sistema.*
