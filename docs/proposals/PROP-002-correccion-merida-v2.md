# PROPUESTA FORMAL PROP-002 (ACTUALIZADA)
## Corrección de Ausencia de 130° MÉRIDA en Dashboard Comercial V2

| Campo | Valor |
|-------|-------|
| **ID** | PROP-002 |
| **Fecha** | 2026-05-05 |
| **Versión** | 2.0 (Actualizada con análisis de dependencia MongoDB) |
| **Estado** | PENDIENTE AUTORIZACIÓN |
| **Prioridad** | P0 |
| **Tipo** | Corrección de Bug (Doble) |
| **Ambiente** | Preview + Producción |

---

## 1. HALLAZGO CONFIRMADO (Evidencia SQL Directa)

### 1.1 Consulta Ejecutada en EDARSAHUB - Mayo 2026

| UNIDAD | ID | activo | es_demo | DÍAS | VENTAS |
|--------|-----|--------|---------|------|--------|
| **130° MÉRIDA** | **130-MER** | **True** | **False** | **4** | **$409,213.00** |
| 130° QUERETARO | 130-QRO | True | False | 4 | $407,073.00 |
| CIENFUEGOS | CIENFUEGOS | True | False | 5 | $560,485.00 |
| LA ESTELAR | LA-ESTELAR | True | False | 4 | $462,031.00 |
| ORIGEN | ORIGEN | True | False | 4 | $223,447.70 |

**Verificación**: MÉRIDA tiene **729 registros históricos** con datos correctos.

---

## 2. DICTAMEN FINAL: OPCIÓN A + D COMBINADAS

> **A)** Los datos existen y están correctos en EDARSAHUB.  
> **D)** El filtro del backend usa condiciones incorrectas en DOS lugares.

---

## 3. ANÁLISIS DE DEPENDENCIA MONGODB EN `get_user_unidades_negocio()`

### 3.1 ¿Qué hace exactamente `get_user_unidades_negocio()`?

**Ubicación**: `/app/backend/core/context_resolver.py`, líneas 56-140

**Función**: Obtiene las unidades de negocio disponibles para un usuario según RBAC. Traduce la estructura empresas→sucursales→servidores de MongoDB a un formato usable.

**Flujo de ejecución**:
```
1. get_user_empresas_permitidas(user) → Lista de empresa_ids
2. db.empresas.find({id: $in empresa_ids}) → Empresas del catálogo
3. db.sucursales_catalogo.find({empresa_id: $in empresa_ids}) → Sucursales
4. db.sucursal_servidor_map.find({sucursal_id: $in sucursal_ids}) → Mapeos
5. db.servers.find({id: $in server_ids}) → Info de servidores
6. Construir resultado combinando los datos
```

### 3.2 ¿De qué colecciones de MongoDB lee?

| Colección | Propósito | Campos relevantes |
|-----------|-----------|-------------------|
| `empresas` | Catálogo de empresas | `id`, `codigo`, `nombre`, `activa` |
| `sucursales_catalogo` | Catálogo de sucursales | `id`, `empresa_id`, `codigo`, `nombre`, `activa` |
| `sucursal_servidor_map` | Mapeo sucursal→servidor | `sucursal_id`, `server_id`, `activo` |
| `servers` | Servidores de datos | `id`, `name`, `system_type` |

### 3.3 ¿Qué campos usa para mapear unidades?

El resultado de `get_user_unidades_negocio()` incluye:
```python
{
    "id": empresa_id,
    "codigo": empresa.codigo,      # <-- Usado en mapeo
    "nombre": empresa.nombre,      # <-- Usado en mapeo
    "server_id": server_id,
    "server_nombre": server.name,
    "system_type": server.system_type,
    "sucursal_origen_id": mapeo.sucursal_origen_id,
    "sucursales": [...]
}
```

**En `routes.py` líneas 76-89**, el mapeo usa `codigo` y `nombre`:
```python
codigo = u.get('codigo', '').upper()
nombre = u.get('nombre', '').upper()

if 'MERIDA' in nombre or 'MER' in codigo:
    unidades_v2.append('130-MER')
```

### 3.4 ¿Por qué MÉRIDA no está en ese mapeo?

**CAUSA RAÍZ #2**: El código busca patrones incorrectos.

| Empresa en MongoDB | Código | Nombre | Búsqueda en código |
|--------------------|--------|--------|---------------------|
| 130° MÉRIDA | `130MID` | `130 MID` | `'MERIDA' in '130 MID'` = **FALSE** |
| | | | `'MER' in '130MID'` = **FALSE** |

El código espera:
- `MERIDA` en el nombre → MongoDB tiene `130 MID`
- `MER` en el código → MongoDB tiene `130MID` (contiene `MID`, no `MER`)

**Resultado**: El mapeo falla silenciosamente y MÉRIDA no se incluye en `unidades_v2`.

### 3.5 ¿Ese mapeo desde MongoDB aplica solo a Comercial V2 o también a otros módulos?

**Análisis de uso de `get_user_unidades_negocio()`**:

| Módulo | Archivo | ¿Usa el mapeo de V2? |
|--------|---------|----------------------|
| Comercial V2 | `/app/backend/modules/comercial_v2/routes.py` | **SÍ** (línea 70) |
| Configuración | `/app/backend/modules/configuracion/routes/config_asignaciones_routes.py` | NO (usa estructura directa) |
| Context Resolver | `/app/backend/core/context_resolver.py` | Función base |

**Conclusión**: El mapeo problemático (`'MERIDA' in nombre`) es **exclusivo de Comercial V2**. Otros módulos usan la estructura directa de MongoDB sin traducción.

### 3.6 ¿Cuál debe ser la fuente oficial de unidades permitidas: MongoDB, EDARSAHUB o JWT?

**Arquitectura actual (temporal)**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FLUJO DE AUTORIZACIÓN                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  JWT Token ──────► user.role, user.empresas_permitidas              │
│       │                      │                                      │
│       │                      ▼                                      │
│       │            MongoDB (catálogos)                              │
│       │            ├─ empresas                                      │
│       │            ├─ sucursales_catalogo                           │
│       │            ├─ sucursal_servidor_map                         │
│       │            └─ servers                                       │
│       │                      │                                      │
│       │                      ▼                                      │
│       │            get_user_unidades_negocio()                      │
│       │                      │                                      │
│       │                      ▼                                      │
│       │            MAPEO MANUAL (routes.py:76-89)                   │
│       │            "MERIDA" → "130-MER"  ◄── BUG #2                 │
│       │                      │                                      │
│       ▼                      ▼                                      │
│  SuperAdmin check    unidades_v2 list                               │
│  (línea 92)                  │                                      │
│  'rol' vs 'role'             │                                      │
│       │                      │                                      │
│       ▼                      ▼                                      │
│    BUG #1 ──────────► Consulta a EDARSAHUB                          │
│                       WHERE unidad_negocio_id IN (...)              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Fuentes actuales**:
- **JWT**: Identidad del usuario (role, empresas_permitidas)
- **MongoDB**: Catálogos de configuración (empresas, sucursales, servidores)
- **EDARSAHUB**: Datos operativos de ventas

**Fuente oficial de unidades V2**: Debería ser MongoDB → traducido a IDs de EDARSAHUB mediante mapeo correcto.

### 3.7 ¿Qué pasa con un usuario no-SuperAdministrador que sí debe ver MÉRIDA?

**Escenario**: Usuario con `role != SuperAdministrador` pero con `empresa_id: a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff` (MÉRIDA) en `empresas_permitidas`.

**Resultado actual**:
1. `get_user_unidades_negocio()` retorna correctamente la empresa MÉRIDA con `codigo='130MID'`, `nombre='130 MID'`
2. El mapeo en líneas 76-89 procesa el registro
3. Condición: `'MERIDA' in '130 MID'` = **FALSE**
4. Condición: `'MER' in '130MID'` = **FALSE**
5. **MÉRIDA no se agrega a `unidades_v2`**
6. El usuario NO ve MÉRIDA aunque tenga permisos

**IMPACTO**: El Bug #2 afecta a **TODOS los usuarios**, no solo a SuperAdministradores.

### 3.8 ¿El cambio de una línea solo corrige SuperAdministrador/Director o también el acceso real por RBAC?

**Análisis**:

| Bug | Línea | Corrección | ¿A quién afecta? |
|-----|-------|------------|------------------|
| #1 | 92 | `'rol'` → `'role'` | Solo SuperAdministrador/Director |
| #2 | 84 | Agregar `'MID' in codigo` | **TODOS los usuarios** |

**Sin el Bug #2 corregido**: Los usuarios no-SuperAdmin con permisos a MÉRIDA seguirían sin verla.

### 3.9 ¿Existe riesgo de que otros módulos tengan el mismo bug role/rol?

**Búsqueda exhaustiva**:
```bash
grep -rn "\.get('rol')" /app/backend/ --include="*.py"
```

**Resultado**:
```
/app/backend/modules/comercial_v2/routes.py:92
```

**Conclusión**: El bug `'rol'` vs `'role'` es **único** en Comercial V2. Otros módulos usan `'role'` correctamente.

### 3.10 ¿Cuál es el plan para que Comercial V2 deje de depender de MongoDB como fuente final de mapeo?

**Estado actual**: Comercial V2 depende de MongoDB para resolver RBAC y luego traduce a IDs de EDARSAHUB mediante mapeo hardcodeado.

**Propuesta futura (fuera de alcance de PROP-002)**:

| Fase | Acción | Beneficio |
|------|--------|-----------|
| 1 | Corregir bugs actuales (PROP-002) | Funcionalidad inmediata |
| 2 | Crear tabla `Unidades_Negocio_v2` en EDARSAHUB | Fuente maestra única |
| 3 | Migrar RBAC de MongoDB a EDARSAHUB | Eliminar dependencia |
| 4 | Deprecar mapeo hardcodeado | Código limpio |

**Nota**: PROP-002 aborda el problema inmediato sin modificar la arquitectura.

---

## 4. CAUSA RAÍZ COMPLETA

### Bug #1: Nomenclatura de campo (Afecta SuperAdmin/Director)

**Archivo**: `/app/backend/modules/comercial_v2/routes.py`  
**Línea**: 92

```python
# INCORRECTO:
if current_user.get('rol') in ['SuperAdministrador', 'Director']:

# CORRECTO:
if current_user.get('role') in ['SuperAdministrador', 'Director']:
```

### Bug #2: Mapeo de MÉRIDA (Afecta TODOS los usuarios)

**Archivo**: `/app/backend/modules/comercial_v2/routes.py`  
**Línea**: 84

```python
# INCORRECTO (no detecta 130MID):
elif 'MERIDA' in nombre or 'MER' in codigo:

# CORRECTO (detecta 130MID):
elif 'MERIDA' in nombre or 'MER' in codigo or 'MID' in codigo:
```

---

## 5. TABLA AFECTADA

| Campo | Valor |
|-------|-------|
| Base de datos | No aplica (bug en código, no en datos) |
| Tabla origen | N/A |
| Estado de datos | **CORRECTO** (no requiere modificación) |

---

## 6. ENDPOINT AFECTADO

| Campo | Valor |
|-------|-------|
| Método | GET |
| Ruta | `/api/v2/comercial/dashboard` |
| Otros endpoints V2 | `/api/v2/comercial/kpis-diarios`, `/api/v2/comercial/ventas-dia`, etc. |

---

## 7. ARCHIVO AFECTADO

| Campo | Valor |
|-------|-------|
| Ruta | `/app/backend/modules/comercial_v2/routes.py` |
| Función | `get_unidades_permitidas_v2()` |
| Líneas del bug | **84** y **92** |
| Tipo de cambio | Corrección de 2 líneas |

---

## 8. RIESGO

### 8.1 Si se corrige mal

| Riesgo | Impacto | Probabilidad |
|--------|---------|--------------|
| Romper autenticación de otros módulos | ALTO | NULA (módulos separados) |
| Exponer unidades no autorizadas | MEDIO | BAJA (RBAC sigue activo) |
| Afectar V1 | ALTO | NULA (archivos separados) |
| Mapear incorrectamente otra unidad | MEDIO | BAJA (patrón específico) |

### 8.2 Si NO se corrige

| Riesgo | Impacto |
|--------|---------|
| 130° MÉRIDA seguirá invisible en Dashboard V2 | ALTO |
| Datos de $409K+ mensuales sin reportar | ALTO |
| Usuarios no-SuperAdmin tampoco verán MÉRIDA | ALTO |

---

## 9. ALCANCE QUIRÚRGICO

### 9.1 QUÉ SÍ SE TOCARÁ

| Archivo | Línea | Cambio |
|---------|-------|--------|
| `/app/backend/modules/comercial_v2/routes.py` | 84 | Agregar `or 'MID' in codigo` |
| `/app/backend/modules/comercial_v2/routes.py` | 92 | Cambiar `'rol'` por `'role'` |

### 9.2 QUÉ NO SE TOCARÁ

| Módulo/Archivo | Razón |
|----------------|-------|
| `/app/backend/modules/comercial/` (V1) | **INTOCABLE** |
| `/app/backend/modules/compras/` | No relacionado |
| `/app/backend/modules/auth/` | No relacionado |
| `/app/backend/core/context_resolver.py` | Funciona correctamente |
| `/app/backend/core/security.py` | Ya usa `'role'` correctamente |
| Tablero Ejecutivo | No relacionado |
| MongoDB | No se modifica |
| EDARSAHUB (SQL) | No se modifica |

---

## 10. PLAN DE CORRECCIÓN

### Paso 1: Corregir Bug #2 (Mapeo de MÉRIDA)

**Línea 84**:
```python
# ANTES:
elif 'MERIDA' in nombre or 'MER' in codigo:

# DESPUÉS:
elif 'MERIDA' in nombre or 'MER' in codigo or 'MID' in codigo:
```

### Paso 2: Corregir Bug #1 (Nomenclatura role/rol)

**Línea 92**:
```python
# ANTES:
if current_user.get('rol') in ['SuperAdministrador', 'Director']:

# DESPUÉS:
if current_user.get('role') in ['SuperAdministrador', 'Director']:
```

### Paso 3: Reiniciar backend

```bash
sudo supervisorctl restart backend
```

---

## 11. PRUEBAS OBLIGATORIAS

### 11.1 Post-corrección

| Prueba | Criterio de éxito |
|--------|-------------------|
| Endpoint retorna 5 unidades | `filtros_aplicados.unidades` incluye `130-MER` |
| MÉRIDA aparece en datos | `unidades[]` contiene `unidad_negocio_id: "130-MER"` |
| Ventas de MÉRIDA visibles | `ventas_total` ≈ $409,213 para Mayo 2026 |
| V1 no afectada | Endpoint V1 sigue funcionando igual |
| Usuario no-SuperAdmin | Con permisos a MÉRIDA, la puede ver |

---

## 12. NO REGRESIÓN

| Verificación | Estado |
|--------------|--------|
| Comercial V1 intacto | NO SE TOCA |
| Tablero Ejecutivo intacto | NO SE TOCA |
| Compras intacto | NO SE TOCA |
| Auth intacto | NO SE TOCA |
| MongoDB intacto | NO SE TOCA |
| EDARSAHUB intacto | NO SE TOCA |
| Otros módulos V2 | Usan la misma función, se benefician |

---

## 13. ROLLBACK

### Procedimiento de reversión

```bash
# 1. Revertir línea 84
# 'MID' in codigo → eliminar

# 2. Revertir línea 92
# 'role' → 'rol'

# 3. Reiniciar backend
sudo supervisorctl restart backend
```

**Tiempo estimado**: < 2 minutos

---

## 14. AUTORIZACIÓN REQUERIDA

### Se solicita autorización explícita para:

1. Modificar **LÍNEA 84** en `/app/backend/modules/comercial_v2/routes.py`
   - Agregar `or 'MID' in codigo` al mapeo de MÉRIDA
2. Modificar **LÍNEA 92** en `/app/backend/modules/comercial_v2/routes.py`
   - Cambiar `current_user.get('rol')` por `current_user.get('role')`
3. Reiniciar el servicio backend
4. Ejecutar pruebas de verificación post-corrección

### NO se solicita autorización para:

- Modificar Comercial V1
- Modificar Tablero Ejecutivo
- Modificar Compras
- Modificar Auth
- Modificar context_resolver.py
- Modificar security.py
- Modificar datos en EDARSAHUB
- Modificar datos en MongoDB
- Activar feature flag V2
- Refactorizar arquitectura

---

## 15. RESUMEN EJECUTIVO

| Campo | Valor |
|-------|-------|
| **Problema** | 130° MÉRIDA no aparece en Dashboard V2 |
| **Bug #1** | Nomenclatura: código busca `'rol'`, token tiene `'role'` |
| **Bug #2** | Mapeo: código busca `'MER'`, MongoDB tiene `'MID'` |
| **Impacto Bug #1** | Solo SuperAdmin/Director |
| **Impacto Bug #2** | **TODOS los usuarios** |
| **Solución** | Cambiar 2 líneas de código |
| **Riesgo** | BAJO (cambio aislado, no afecta otros módulos) |
| **Rollback** | < 2 minutos |

---

**ESTADO**: PENDIENTE AUTORIZACIÓN

---

*Documento generado: 2026-05-05*  
*Versión: 2.0 (Actualizada con análisis de dependencia MongoDB)*
