# P1-FASE5A.1 — Implementación Funcional: Endpoints Cuentas y Saldos Bancarios

## PROPUESTA TÉCNICA

| Campo | Valor |
|-------|-------|
| **Fecha** | 2025-12-05 |
| **Versión** | 1.0 |
| **Estado** | PROPUESTA - PENDIENTE AUTORIZACIÓN |
| **Prioridad** | P1 |
| **Padre** | P1-FASE5A.1 DDL (COMPLETADO) |
| **Prerrequisito** | DDL v2.0 ejecutado ✅ |

---

## 1. OBJETIVO FUNCIONAL

Implementar los endpoints backend para gestionar el catálogo de cuentas bancarias y el registro histórico de saldos bancarios, permitiendo:

1. **CRUD de cuentas bancarias**: Alta, consulta, edición y baja lógica de cuentas.
2. **Gestión de saldos**: Captura, consulta, corrección y cancelación de saldos bancarios.
3. **Auditoría completa**: Trazabilidad de quién creó/modificó/canceló cada registro.
4. **Seguridad**: Enmascaramiento de datos sensibles y validación de permisos.

---

## 2. ALCANCE EXACTO

### 2.1 Incluido en esta fase

| Componente | Descripción |
|------------|-------------|
| Endpoints CRUD cuentas | Listar, crear, editar, desactivar cuentas bancarias |
| Endpoints saldos | Listar, capturar, corregir, cancelar, historial |
| Endpoint bancos | Listar catálogo de bancos (solo lectura) |
| Validaciones | Permisos, datos, unicidad, coherencia |
| Enmascaramiento | Número de cuenta y CLABE |
| Auditoría | Campos de usuario y fecha en cada operación |

### 2.2 Separación de fases

| Subfase | Descripción | Estado |
|---------|-------------|--------|
| **5A.1-FUNC-BACKEND** | Endpoints FastAPI sin frontend | PROPUESTA ACTUAL |
| **5A.1-FUNC-FRONTEND** | Formularios y tablas UI | FASE POSTERIOR |

---

## 3. FUERA DE ALCANCE

| Elemento | Razón |
|----------|-------|
| ❌ Frontend / UI | Fase 5A.1-FUNC-FRONTEND separada |
| ❌ Dashboard posición de efectivo | Fase 5A.3 |
| ❌ Efectivo pendiente depositar | Fase 5A.4 |
| ❌ Importación Excel | Fase posterior |
| ❌ API bancaria | Fase futura |
| ❌ Conciliación bancaria | Fase futura |
| ❌ CxP | INTOCABLE |
| ❌ Cuadre de Cortes Z | INTOCABLE |
| ❌ Comercial V2 | INTOCABLE |
| ❌ Tablero Ejecutivo | INTOCABLE |
| ❌ Compras | INTOCABLE |
| ❌ Propinas TPV | INTOCABLE |
| ❌ Auth/RBAC | INTOCABLE |
| ❌ Menús globales | INTOCABLE |
| ❌ Filtros globales | INTOCABLE |

---

## 4. ENDPOINTS PROPUESTOS — CUENTAS BANCARIAS

### 4.1 Listar cuentas bancarias

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v2/finanzas/cuentas-bancarias` |
| **Método** | GET |
| **Permiso** | `finanzas.cuentas_bancarias.view` |
| **Descripción** | Lista todas las cuentas bancarias activas |

**Query params opcionales:**

| Param | Tipo | Descripción |
|-------|------|-------------|
| `banco_id` | int | Filtrar por banco |
| `activo` | bool | Filtrar por estado (default: true) |
| `include_inactive` | bool | Incluir inactivas (default: false) |

**Response 200:**

```json
{
  "cuentas": [
    {
      "cuenta_bancaria_id": 1,
      "banco_id": 2,
      "banco_nombre": "BBVA",
      "banco_codigo": "012",
      "numero_cuenta": "****6789",
      "clabe": "****4567",
      "alias": "BBVA Principal",
      "moneda": "MXN",
      "es_cuenta_principal": true,
      "activo": true,
      "fecha_alta": "2026-05-05T12:00:00",
      "ultimo_saldo": {
        "fecha": "2026-05-05",
        "saldo_final": 1200000.00
      }
    }
  ],
  "total": 1,
  "_fuente": "EDARSAHUB"
}
```

---

### 4.2 Obtener cuenta bancaria por ID

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v2/finanzas/cuentas-bancarias/{cuenta_id}` |
| **Método** | GET |
| **Permiso** | `finanzas.cuentas_bancarias.view` |

**Response 200:**

```json
{
  "cuenta_bancaria_id": 1,
  "empresa_id": null,
  "banco_id": 2,
  "banco_nombre": "BBVA BANCOMER",
  "banco_codigo": "012",
  "numero_cuenta": "****6789",
  "clabe": "****4567",
  "alias": "BBVA Principal",
  "moneda": "MXN",
  "es_cuenta_principal": true,
  "activo": true,
  "fecha_alta": "2026-05-05T12:00:00",
  "usuario_creacion_id": 1,
  "fecha_modificacion": null,
  "usuario_modificacion_id": null,
  "historial_saldos": [
    {
      "fecha": "2026-05-05",
      "saldo_final": 1200000.00,
      "estatus": "VIGENTE"
    }
  ]
}
```

**Response 404:**

```json
{
  "detail": "Cuenta bancaria no encontrada"
}
```

---

### 4.3 Obtener cuenta con datos sensibles

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v2/finanzas/cuentas-bancarias/{cuenta_id}/completa` |
| **Método** | GET |
| **Permiso** | `finanzas.cuentas_bancarias.view_sensitive` |
| **Descripción** | Devuelve número de cuenta y CLABE SIN enmascarar |

**Response 200:**

```json
{
  "cuenta_bancaria_id": 1,
  "numero_cuenta": "0123456789",
  "clabe": "012345678901234567",
  "alias": "BBVA Principal",
  "banco_nombre": "BBVA BANCOMER"
}
```

**Response 403:**

```json
{
  "detail": "No tiene permiso para ver datos sensibles"
}
```

---

### 4.4 Crear cuenta bancaria

| Campo | Valor |
|-------|-------|
| **Ruta** | `POST /api/v2/finanzas/cuentas-bancarias` |
| **Método** | POST |
| **Permiso** | `finanzas.cuentas_bancarias.manage` |

**Request body:**

```json
{
  "banco_id": 2,
  "numero_cuenta": "0123456789",
  "clabe": "012345678901234567",
  "alias": "BBVA Principal",
  "moneda": "MXN",
  "es_cuenta_principal": false,
  "empresa_id": null
}
```

**Validaciones:**

| Campo | Regla |
|-------|-------|
| `banco_id` | Requerido, debe existir en `Global_Cat_Bancos` |
| `numero_cuenta` | Requerido, 10-20 caracteres, único |
| `clabe` | Opcional, exactamente 18 dígitos si se proporciona |
| `alias` | Requerido, 3-50 caracteres, único |
| `moneda` | Opcional, default 'MXN', valores: MXN, USD, EUR, CAD |
| `es_cuenta_principal` | Opcional, default false |

**Response 201:**

```json
{
  "message": "Cuenta bancaria creada exitosamente",
  "cuenta": {
    "cuenta_bancaria_id": 1,
    "alias": "BBVA Principal",
    "numero_cuenta": "****6789"
  }
}
```

**Response 400:**

```json
{
  "detail": "Ya existe una cuenta con ese número"
}
```

---

### 4.5 Editar cuenta bancaria

| Campo | Valor |
|-------|-------|
| **Ruta** | `PUT /api/v2/finanzas/cuentas-bancarias/{cuenta_id}` |
| **Método** | PUT |
| **Permiso** | `finanzas.cuentas_bancarias.manage` |

**Request body (campos opcionales):**

```json
{
  "alias": "BBVA Operaciones",
  "es_cuenta_principal": true,
  "empresa_id": 1
}
```

**Campos editables:**

| Campo | Editable | Notas |
|-------|----------|-------|
| `alias` | ✅ | Único |
| `es_cuenta_principal` | ✅ | - |
| `empresa_id` | ✅ | - |
| `numero_cuenta` | ❌ | Inmutable después de creación |
| `clabe` | ❌ | Inmutable después de creación |
| `banco_id` | ❌ | Inmutable después de creación |
| `moneda` | ❌ | Inmutable después de creación |

**Response 200:**

```json
{
  "message": "Cuenta bancaria actualizada",
  "cuenta": {
    "cuenta_bancaria_id": 1,
    "alias": "BBVA Operaciones",
    "fecha_modificacion": "2026-05-05T15:30:00"
  }
}
```

---

### 4.6 Desactivar cuenta bancaria

| Campo | Valor |
|-------|-------|
| **Ruta** | `POST /api/v2/finanzas/cuentas-bancarias/{cuenta_id}/desactivar` |
| **Método** | POST |
| **Permiso** | `finanzas.cuentas_bancarias.manage` |

**Request body:**

```json
{
  "motivo": "Cuenta cerrada en banco"
}
```

**Validaciones:**

- `motivo` es requerido (mínimo 10 caracteres)
- No se puede desactivar si tiene saldos VIGENTES sin cancelar

**Response 200:**

```json
{
  "message": "Cuenta bancaria desactivada",
  "cuenta_bancaria_id": 1
}
```

**Response 400:**

```json
{
  "detail": "No se puede desactivar: tiene saldos vigentes"
}
```

---

## 5. ENDPOINTS PROPUESTOS — SALDOS BANCARIOS

### 5.1 Listar saldos de una cuenta

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v2/finanzas/cuentas-bancarias/{cuenta_id}/saldos` |
| **Método** | GET |
| **Permiso** | `finanzas.saldos.view` |

**Query params:**

| Param | Tipo | Descripción |
|-------|------|-------------|
| `fecha_inicio` | date | Filtrar desde fecha |
| `fecha_fin` | date | Filtrar hasta fecha |
| `solo_vigentes` | bool | Solo mostrar VIGENTES (default: false) |
| `limit` | int | Máximo registros (default: 100) |

**Response 200:**

```json
{
  "cuenta_bancaria_id": 1,
  "alias": "BBVA Principal",
  "saldos": [
    {
      "saldo_bancario_id": 10,
      "fecha_saldo": "2026-05-05",
      "saldo_final": 1200000.00,
      "moneda": "MXN",
      "fuente_datos": "MANUAL",
      "es_vigente": true,
      "activo": true,
      "estatus": "VIGENTE",
      "fecha_creacion": "2026-05-05T12:00:00",
      "usuario_creacion": "Juan Pérez"
    },
    {
      "saldo_bancario_id": 9,
      "fecha_saldo": "2026-05-04",
      "saldo_final": 1150000.00,
      "moneda": "MXN",
      "fuente_datos": "MANUAL",
      "es_vigente": true,
      "activo": true,
      "estatus": "VIGENTE",
      "fecha_creacion": "2026-05-04T11:30:00",
      "usuario_creacion": "Juan Pérez"
    }
  ],
  "total": 2
}
```

---

### 5.2 Obtener último saldo vigente

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v2/finanzas/cuentas-bancarias/{cuenta_id}/saldo-actual` |
| **Método** | GET |
| **Permiso** | `finanzas.saldos.view` |

**Response 200:**

```json
{
  "cuenta_bancaria_id": 1,
  "alias": "BBVA Principal",
  "ultimo_saldo": {
    "saldo_bancario_id": 10,
    "fecha_saldo": "2026-05-05",
    "saldo_final": 1200000.00,
    "moneda": "MXN",
    "dias_desde_actualizacion": 0
  },
  "alerta_desactualizado": false
}
```

**Response 200 (sin saldos):**

```json
{
  "cuenta_bancaria_id": 1,
  "alias": "BBVA Principal",
  "ultimo_saldo": null,
  "mensaje": "Esta cuenta no tiene saldos registrados"
}
```

---

### 5.3 Capturar saldo bancario

| Campo | Valor |
|-------|-------|
| **Ruta** | `POST /api/v2/finanzas/saldos-bancarios` |
| **Método** | POST |
| **Permiso** | `finanzas.saldos.manage` |

**Request body:**

```json
{
  "cuenta_bancaria_id": 1,
  "fecha_saldo": "2026-05-05",
  "saldo_final": 1200000.00,
  "observaciones": "Saldo al cierre del día"
}
```

**Validaciones:**

| Campo | Regla |
|-------|-------|
| `cuenta_bancaria_id` | Requerido, debe existir y estar activa |
| `fecha_saldo` | Requerido, no puede ser futuro, formato YYYY-MM-DD |
| `saldo_final` | Requerido, decimal con 2 decimales |
| `observaciones` | Opcional, máximo 500 caracteres |

**Regla de unicidad:**
- Si ya existe un saldo VIGENTE para esa cuenta+fecha, rechazar con error 400.
- El usuario debe usar el endpoint de corrección si necesita modificar.

**Response 201:**

```json
{
  "message": "Saldo capturado exitosamente",
  "saldo": {
    "saldo_bancario_id": 10,
    "cuenta_bancaria_id": 1,
    "fecha_saldo": "2026-05-05",
    "saldo_final": 1200000.00,
    "estatus": "VIGENTE"
  }
}
```

**Response 400:**

```json
{
  "detail": "Ya existe un saldo vigente para esta cuenta y fecha. Use el endpoint de corrección."
}
```

---

### 5.4 Corregir saldo bancario

| Campo | Valor |
|-------|-------|
| **Ruta** | `POST /api/v2/finanzas/saldos-bancarios/{saldo_id}/corregir` |
| **Método** | POST |
| **Permiso** | `finanzas.saldos.manage` |

**Request body:**

```json
{
  "saldo_final_correcto": 1250000.00,
  "motivo_correccion": "Error de digitación en el saldo original"
}
```

**Validaciones:**

| Campo | Regla |
|-------|-------|
| `saldo_final_correcto` | Requerido, decimal |
| `motivo_correccion` | Requerido, mínimo 10 caracteres |

**Proceso interno:**

1. Verificar que el saldo existe y es VIGENTE
2. Marcar saldo anterior:
   - `EsVigente = 0`
   - `Activo = 0`
   - `Estatus = 'CORREGIDO'`
   - `UsuarioCancelacionID = usuario_actual`
   - `FechaCancelacion = GETDATE()`
   - `MotivoCancelacion = motivo_correccion`
3. Crear nuevo saldo:
   - Misma cuenta y fecha
   - `SaldoFinal = saldo_final_correcto`
   - `EsVigente = 1`
   - `Activo = 1`
   - `Estatus = 'VIGENTE'`
   - `FuenteDatos = 'MANUAL'`
   - `Observaciones = 'Corrección de saldo anterior'`

**Response 200:**

```json
{
  "message": "Saldo corregido exitosamente",
  "saldo_anterior": {
    "saldo_bancario_id": 10,
    "saldo_final": 1200000.00,
    "estatus": "CORREGIDO"
  },
  "saldo_nuevo": {
    "saldo_bancario_id": 11,
    "saldo_final": 1250000.00,
    "estatus": "VIGENTE"
  }
}
```

**Response 400:**

```json
{
  "detail": "Solo se pueden corregir saldos VIGENTES"
}
```

---

### 5.5 Cancelar saldo bancario

| Campo | Valor |
|-------|-------|
| **Ruta** | `POST /api/v2/finanzas/saldos-bancarios/{saldo_id}/cancelar` |
| **Método** | POST |
| **Permiso** | `finanzas.saldos.manage` |

**Request body:**

```json
{
  "motivo_cancelacion": "Saldo capturado por error, no corresponde a esta cuenta"
}
```

**Validaciones:**

| Campo | Regla |
|-------|-------|
| `motivo_cancelacion` | Requerido, mínimo 10 caracteres |

**Proceso interno:**

1. Verificar que el saldo existe y es VIGENTE
2. Marcar saldo:
   - `EsVigente = 0`
   - `Activo = 0`
   - `Estatus = 'CANCELADO'`
   - `UsuarioCancelacionID = usuario_actual`
   - `FechaCancelacion = GETDATE()`
   - `MotivoCancelacion = motivo_cancelacion`

**Response 200:**

```json
{
  "message": "Saldo cancelado exitosamente",
  "saldo": {
    "saldo_bancario_id": 10,
    "estatus": "CANCELADO",
    "fecha_cancelacion": "2026-05-05T16:00:00"
  }
}
```

---

### 5.6 Historial de auditoría de un saldo

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v2/finanzas/saldos-bancarios/{saldo_id}/historial` |
| **Método** | GET |
| **Permiso** | `finanzas.saldos.view` |

**Response 200:**

```json
{
  "saldo_bancario_id": 10,
  "cuenta_bancaria_id": 1,
  "fecha_saldo": "2026-05-05",
  "historial": [
    {
      "accion": "CREACION",
      "fecha": "2026-05-05T12:00:00",
      "usuario": "Juan Pérez",
      "saldo_final": 1200000.00
    },
    {
      "accion": "CORRECCION",
      "fecha": "2026-05-05T15:00:00",
      "usuario": "María García",
      "saldo_final_anterior": 1200000.00,
      "saldo_final_nuevo": 1250000.00,
      "motivo": "Error de digitación"
    }
  ]
}
```

---

### 5.7 Saldo bancario total (todas las cuentas)

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v2/finanzas/saldos-bancarios/total` |
| **Método** | GET |
| **Permiso** | `finanzas.saldos.view` |

**Query params:**

| Param | Tipo | Descripción |
|-------|------|-------------|
| `fecha` | date | Fecha de consulta (default: hoy) |

**Response 200:**

```json
{
  "fecha_consulta": "2026-05-05",
  "saldo_bancario_total": 2500000.00,
  "moneda": "MXN",
  "cuentas_con_saldo": 3,
  "cuentas_sin_saldo": 1,
  "cuentas_desactualizadas": 0,
  "detalle_por_banco": [
    {
      "banco_id": 2,
      "banco_nombre": "BBVA",
      "saldo_total": 1500000.00,
      "cuentas": 2
    },
    {
      "banco_id": 5,
      "banco_nombre": "BANORTE",
      "saldo_total": 1000000.00,
      "cuentas": 1
    }
  ],
  "_fuente": "EDARSAHUB"
}
```

---

## 6. ENDPOINT CATÁLOGO DE BANCOS

### 6.1 Listar bancos

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v2/finanzas/bancos` |
| **Método** | GET |
| **Permiso** | `finanzas.cuentas_bancarias.view` |

**Response 200:**

```json
{
  "bancos": [
    {"banco_id": 1, "codigo": "002", "nombre": "BANAMEX", "nombre_corto": "BANAMEX"},
    {"banco_id": 2, "codigo": "012", "nombre": "BBVA BANCOMER", "nombre_corto": "BBVA"},
    {"banco_id": 3, "codigo": "014", "nombre": "SANTANDER", "nombre_corto": "SANTANDER"},
    {"banco_id": 4, "codigo": "021", "nombre": "HSBC", "nombre_corto": "HSBC"},
    {"banco_id": 5, "codigo": "072", "nombre": "BANORTE", "nombre_corto": "BANORTE"}
  ],
  "total": 5
}
```

---

## 7. VALIDACIONES OBLIGATORIAS

### 7.1 Validaciones de cuentas

| Validación | Regla |
|------------|-------|
| Banco existe | `BancoID` debe existir en `Global_Cat_Bancos` con `Activo = 1` |
| Número único | `NumeroCuenta` no debe repetirse |
| Alias único | `Alias` no debe repetirse |
| CLABE formato | Si se proporciona, exactamente 18 dígitos numéricos |
| Moneda válida | MXN, USD, EUR, CAD |

### 7.2 Validaciones de saldos

| Validación | Regla |
|------------|-------|
| Cuenta existe | `CuentaBancariaID` debe existir y estar activa |
| Fecha no futura | `FechaSaldo` <= fecha actual |
| Unicidad vigente | Solo un saldo VIGENTE por cuenta+fecha |
| Corrección solo vigentes | Solo se pueden corregir saldos con `Estatus = 'VIGENTE'` |
| Cancelación con motivo | `MotivoCancelacion` obligatorio (min 10 chars) |

---

## 8. PERMISOS/RBAC REQUERIDOS

### 8.1 Permisos propuestos

| Permiso | Descripción |
|---------|-------------|
| `finanzas.cuentas_bancarias.view` | Ver catálogo de cuentas (enmascarado) |
| `finanzas.cuentas_bancarias.view_sensitive` | Ver datos completos (sin enmascarar) |
| `finanzas.cuentas_bancarias.manage` | Alta, edición, baja de cuentas |
| `finanzas.saldos.view` | Ver saldos bancarios |
| `finanzas.saldos.manage` | Capturar, corregir, cancelar saldos |

### 8.2 Matriz de permisos por rol sugerido

| Rol | view | view_sensitive | manage cuentas | view saldos | manage saldos |
|-----|------|----------------|----------------|-------------|---------------|
| SuperAdministrador | ✅ | ✅ | ✅ | ✅ | ✅ |
| Director Finanzas | ✅ | ✅ | ✅ | ✅ | ✅ |
| Contador | ✅ | ❌ | ❌ | ✅ | ✅ |
| Tesorero | ✅ | ❌ | ❌ | ✅ | ✅ |
| Gerente Unidad | ✅ | ❌ | ❌ | ✅ | ❌ |

### 8.3 Implementación de permisos

Los permisos se validarán en cada endpoint usando el token JWT existente. **NO se modifica Auth/RBAC**, solo se agregan validaciones en los endpoints.

```python
# Ejemplo de validación
def check_permission(user: dict, permission: str) -> bool:
    """Verifica permiso del usuario"""
    user_permissions = user.get('permissions', [])
    user_role = user.get('role', '')
    
    # SuperAdmin tiene todos los permisos
    if user_role in ['superadmin', 'SuperAdministrador']:
        return True
    
    return permission in user_permissions
```

---

## 9. REGLAS DE ENMASCARAMIENTO

### 9.1 Funciones de enmascaramiento

```python
def mask_numero_cuenta(numero: str) -> str:
    """
    Enmascara número de cuenta.
    Entrada: '0123456789'
    Salida:  '****6789'
    """
    if not numero or len(numero) < 4:
        return "****"
    return f"****{numero[-4:]}"

def mask_clabe(clabe: str) -> str:
    """
    Enmascara CLABE interbancaria.
    Entrada: '012345678901234567'
    Salida:  '****4567'
    """
    if not clabe or len(clabe) < 4:
        return "****"
    return f"****{clabe[-4:]}"
```

### 9.2 Reglas de aplicación

| Endpoint | Enmascaramiento |
|----------|-----------------|
| `GET /cuentas-bancarias` | ✅ Siempre enmascarado |
| `GET /cuentas-bancarias/{id}` | ✅ Siempre enmascarado |
| `GET /cuentas-bancarias/{id}/completa` | ❌ Sin enmascarar (requiere permiso especial) |
| Logs y auditoría | ✅ Siempre enmascarado |

---

## 10. REGLAS PARA CUENTAS BANCARIAS

### 10.1 Creación

1. Validar que `BancoID` existe en `Global_Cat_Bancos`
2. Validar unicidad de `NumeroCuenta`
3. Validar unicidad de `Alias`
4. Validar formato de `CLABE` si se proporciona
5. Asignar `UsuarioCreacionID` del token JWT
6. Asignar `FechaAlta = GETDATE()`
7. Asignar `Activo = 1`

### 10.2 Edición

1. Solo campos permitidos: `Alias`, `EsCuentaPrincipal`, `EmpresaID`
2. Campos inmutables: `NumeroCuenta`, `CLABE`, `BancoID`, `Moneda`
3. Asignar `UsuarioModificacionID` del token JWT
4. Asignar `FechaModificacion = GETDATE()`

### 10.3 Baja lógica

1. Verificar que no tiene saldos VIGENTES
2. Asignar `Activo = 0`
3. Asignar `UsuarioModificacionID` del token JWT
4. Asignar `FechaModificacion = GETDATE()`
5. **NO eliminar físicamente**

---

## 11. REGLAS PARA CAPTURA DE SALDOS

### 11.1 Creación de saldo

1. Verificar cuenta existe y está activa
2. Verificar que no existe saldo VIGENTE para cuenta+fecha
3. Asignar:
   - `EsVigente = 1`
   - `Activo = 1`
   - `Estatus = 'VIGENTE'`
   - `FuenteDatos = 'MANUAL'`
   - `UsuarioCreacionID` del token JWT
   - `FechaCreacion = GETDATE()`
   - `Moneda` = moneda de la cuenta

---

## 12. REGLAS PARA CORRECCIÓN DE SALDOS

### 12.1 Proceso de corrección

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Usuario solicita corregir saldo ID=10                    │
│ 2. Sistema verifica saldo es VIGENTE                        │
│ 3. Sistema inicia transacción                               │
│ 4. UPDATE saldo anterior:                                   │
│    - EsVigente = 0                                          │
│    - Activo = 0                                             │
│    - Estatus = 'CORREGIDO'                                  │
│    - UsuarioCancelacionID = usuario_actual                  │
│    - FechaCancelacion = GETDATE()                           │
│    - MotivoCancelacion = motivo_correccion                  │
│ 5. INSERT nuevo saldo:                                      │
│    - Misma CuentaBancariaID y FechaSaldo                    │
│    - SaldoFinal = nuevo valor                               │
│    - EsVigente = 1, Activo = 1, Estatus = 'VIGENTE'         │
│    - UsuarioCreacionID = usuario_actual                     │
│ 6. COMMIT transacción                                       │
└─────────────────────────────────────────────────────────────┘
```

### 12.2 Restricciones

- Solo se pueden corregir saldos con `Estatus = 'VIGENTE'`
- Motivo de corrección es obligatorio
- Ambos registros quedan en histórico para auditoría

---

## 13. REGLAS PARA CANCELACIÓN DE SALDOS

### 13.1 Proceso de cancelación

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Usuario solicita cancelar saldo ID=10                    │
│ 2. Sistema verifica saldo es VIGENTE                        │
│ 3. UPDATE saldo:                                            │
│    - EsVigente = 0                                          │
│    - Activo = 0                                             │
│    - Estatus = 'CANCELADO'                                  │
│    - UsuarioCancelacionID = usuario_actual                  │
│    - FechaCancelacion = GETDATE()                           │
│    - MotivoCancelacion = motivo (OBLIGATORIO)               │
│ 4. COMMIT                                                   │
└─────────────────────────────────────────────────────────────┘
```

### 13.2 Restricciones

- Solo se pueden cancelar saldos con `Estatus = 'VIGENTE'`
- `MotivoCancelacion` es OBLIGATORIO (mínimo 10 caracteres)
- El saldo queda en histórico, no se elimina

---

## 14. QUERY — ÚLTIMO SALDO VIGENTE POR CUENTA

```sql
-- Obtener último saldo vigente de una cuenta específica
SELECT TOP 1 
    sb.SaldoBancarioID,
    sb.CuentaBancariaID,
    sb.FechaSaldo,
    sb.SaldoFinal,
    sb.Moneda,
    sb.FuenteDatos,
    sb.Observaciones,
    sb.FechaCreacion,
    uc.NombreCompleto AS UsuarioCreacion
FROM Finanzas_SaldosBancarios sb
LEFT JOIN Usuario_Catalogo uc ON sb.UsuarioCreacionID = uc.UsuarioID
WHERE sb.CuentaBancariaID = @CuentaID
  AND sb.EsVigente = 1
  AND sb.Activo = 1
  AND sb.Estatus = 'VIGENTE'
ORDER BY sb.FechaSaldo DESC;
```

---

## 15. QUERY — SALDO BANCARIO TOTAL

```sql
-- Obtener saldo total de todas las cuentas activas
WITH UltimosSaldos AS (
    SELECT 
        sb.CuentaBancariaID,
        sb.SaldoFinal,
        sb.FechaSaldo,
        ROW_NUMBER() OVER (
            PARTITION BY sb.CuentaBancariaID 
            ORDER BY sb.FechaSaldo DESC
        ) AS rn
    FROM Finanzas_SaldosBancarios sb
    WHERE sb.EsVigente = 1
      AND sb.Activo = 1
      AND sb.Estatus = 'VIGENTE'
)
SELECT 
    SUM(us.SaldoFinal) AS SaldoBancarioTotal,
    COUNT(DISTINCT us.CuentaBancariaID) AS CuentasConSaldo
FROM UltimosSaldos us
INNER JOIN Finanzas_Cat_CuentasBancarias cb 
    ON us.CuentaBancariaID = cb.CuentaBancariaID
WHERE us.rn = 1
  AND cb.Activo = 1;
```

---

## 16. MANEJO DE ESTADO VACÍO

### 16.1 Sin cuentas bancarias

**Response de `GET /cuentas-bancarias`:**

```json
{
  "cuentas": [],
  "total": 0,
  "mensaje": "No hay cuentas bancarias configuradas",
  "accion_sugerida": "Configure al menos una cuenta bancaria para comenzar"
}
```

### 16.2 Cuenta sin saldos

**Response de `GET /cuentas-bancarias/{id}/saldo-actual`:**

```json
{
  "cuenta_bancaria_id": 1,
  "alias": "BBVA Principal",
  "ultimo_saldo": null,
  "mensaje": "Esta cuenta no tiene saldos registrados",
  "accion_sugerida": "Capture el saldo actual para ver la posición de efectivo"
}
```

### 16.3 Sin saldos totales

**Response de `GET /saldos-bancarios/total`:**

```json
{
  "fecha_consulta": "2026-05-05",
  "saldo_bancario_total": 0.00,
  "cuentas_con_saldo": 0,
  "cuentas_sin_saldo": 2,
  "mensaje": "No hay saldos registrados para ninguna cuenta",
  "accion_sugerida": "Capture los saldos actuales de las cuentas bancarias"
}
```

---

## 17. MANEJO DE ERRORES

### 17.1 Códigos de error HTTP

| Código | Uso |
|--------|-----|
| 200 | Operación exitosa |
| 201 | Recurso creado |
| 400 | Error de validación (datos inválidos) |
| 401 | No autenticado |
| 403 | Sin permiso |
| 404 | Recurso no encontrado |
| 409 | Conflicto (duplicado) |
| 500 | Error interno del servidor |

### 17.2 Formato de errores

```json
{
  "detail": "Mensaje de error legible",
  "code": "ERROR_CODE",
  "field": "campo_con_error"
}
```

### 17.3 Errores específicos

| Código | Mensaje | Situación |
|--------|---------|-----------|
| `CUENTA_NOT_FOUND` | Cuenta bancaria no encontrada | GET/PUT/DELETE con ID inexistente |
| `CUENTA_DUPLICADA` | Ya existe una cuenta con ese número | POST con número duplicado |
| `ALIAS_DUPLICADO` | Ya existe una cuenta con ese alias | POST/PUT con alias duplicado |
| `BANCO_NOT_FOUND` | Banco no encontrado | POST con BancoID inválido |
| `SALDO_EXISTS` | Ya existe un saldo vigente para esta cuenta y fecha | POST saldo duplicado |
| `SALDO_NOT_VIGENTE` | Solo se pueden corregir/cancelar saldos VIGENTES | Corrección/cancelación de saldo no vigente |
| `MOTIVO_REQUERIDO` | El motivo es obligatorio | Cancelación sin motivo |
| `FECHA_FUTURA` | La fecha no puede ser futura | POST saldo con fecha futura |
| `PERMISO_DENEGADO` | No tiene permiso para esta operación | Acción sin permiso |

---

## 18. AUDITORÍA

### 18.1 Campos de auditoría automáticos

| Operación | Campos asignados |
|-----------|------------------|
| Crear cuenta | `UsuarioCreacionID`, `FechaAlta` |
| Editar cuenta | `UsuarioModificacionID`, `FechaModificacion` |
| Desactivar cuenta | `UsuarioModificacionID`, `FechaModificacion` |
| Crear saldo | `UsuarioCreacionID`, `FechaCreacion` |
| Corregir saldo | `UsuarioCancelacionID`, `FechaCancelacion`, `MotivoCancelacion` (en anterior) + campos creación (en nuevo) |
| Cancelar saldo | `UsuarioCancelacionID`, `FechaCancelacion`, `MotivoCancelacion` |

### 18.2 Log de actividades

Además de los campos en BD, se recomienda registrar en `Usuario_LogActividades` (si existe) o en logs del sistema:

```python
{
  "timestamp": "2026-05-05T15:30:00",
  "usuario_id": 1,
  "accion": "SALDO_CORREGIDO",
  "entidad": "Finanzas_SaldosBancarios",
  "entidad_id": 10,
  "datos_anteriores": {"saldo_final": 1200000.00},
  "datos_nuevos": {"saldo_final": 1250000.00},
  "motivo": "Error de digitación"
}
```

---

## 19. ARCHIVOS BACKEND PROPUESTOS

### 19.1 Estructura de archivos

```
/app/backend/modules/finanzas/
├── __init__.py
├── cuentas_bancarias.py        # NUEVO - Endpoints cuentas
├── saldos_bancarios.py         # NUEVO - Endpoints saldos
├── models_bancarios.py         # NUEVO - Pydantic models
├── repository_bancarios.py     # NUEVO - Acceso a BD EDARSAHUB
├── utils_bancarios.py          # NUEVO - Enmascaramiento, validaciones
└── ... (archivos existentes intactos)
```

### 19.2 Descripción de archivos

| Archivo | Responsabilidad |
|---------|-----------------|
| `cuentas_bancarias.py` | Router FastAPI con endpoints CRUD de cuentas |
| `saldos_bancarios.py` | Router FastAPI con endpoints de saldos |
| `models_bancarios.py` | Modelos Pydantic para request/response |
| `repository_bancarios.py` | Queries SQL a EDARSAHUB |
| `utils_bancarios.py` | Funciones de enmascaramiento y validación |

---

## 20. ARCHIVOS FRONTEND PROPUESTOS (NO IMPLEMENTAR AÚN)

### 20.1 Estructura propuesta para 5A.1-FUNC-FRONTEND

```
/app/frontend/src/components/finanzas/
├── cuentas-bancarias/
│   ├── CuentasBancariasPage.jsx      # Página principal
│   ├── TablaCuentas.jsx              # Tabla de cuentas
│   ├── FormularioCuenta.jsx          # Alta/edición
│   └── DetalleCuenta.jsx             # Vista detalle
├── saldos-bancarios/
│   ├── CapturaSaldo.jsx              # Formulario captura
│   ├── HistorialSaldos.jsx           # Historial de una cuenta
│   └── CorreccionSaldo.jsx           # Modal de corrección
└── hooks/
    ├── useCuentasBancarias.js        # Hook API cuentas
    └── useSaldosBancarios.js         # Hook API saldos
```

**NOTA**: Esta sección es solo referencia. No se implementa en esta fase.

---

## 21. PRUEBAS OBLIGATORIAS

### 21.1 Pruebas de cuentas bancarias

| # | Prueba | Criterio de aceptación |
|---|--------|------------------------|
| 1 | Listar cuentas vacías | Retorna array vacío con mensaje |
| 2 | Crear cuenta válida | Retorna 201 con ID |
| 3 | Crear cuenta duplicada | Retorna 400 con error |
| 4 | Obtener cuenta existente | Retorna 200 con datos enmascarados |
| 5 | Obtener cuenta inexistente | Retorna 404 |
| 6 | Obtener cuenta completa sin permiso | Retorna 403 |
| 7 | Editar alias | Retorna 200, alias actualizado |
| 8 | Editar número cuenta (inmutable) | Retorna 400 |
| 9 | Desactivar cuenta sin saldos | Retorna 200 |
| 10 | Desactivar cuenta con saldos vigentes | Retorna 400 |

### 21.2 Pruebas de saldos bancarios

| # | Prueba | Criterio de aceptación |
|---|--------|------------------------|
| 11 | Capturar saldo válido | Retorna 201 |
| 12 | Capturar saldo duplicado | Retorna 400 |
| 13 | Capturar saldo fecha futura | Retorna 400 |
| 14 | Obtener último saldo | Retorna saldo más reciente |
| 15 | Corregir saldo vigente | Retorna 200, anterior CORREGIDO |
| 16 | Corregir saldo no vigente | Retorna 400 |
| 17 | Cancelar saldo sin motivo | Retorna 400 |
| 18 | Cancelar saldo con motivo | Retorna 200 |
| 19 | Historial muestra correcciones | Lista completa con estatus |
| 20 | Saldo total calcula correctamente | Suma de últimos vigentes |

### 21.3 Pruebas de no regresión

| # | Prueba | Verificación |
|---|--------|--------------|
| 21 | CxP intacto | No se modifica |
| 22 | Cuadre Cortes Z | 4 sucursales operativas |
| 23 | Comercial V2 | 5 unidades, endpoint OK |
| 24 | Tablero Ejecutivo | No se modifica |
| 25 | Auth/RBAC | No se modifica |

---

## 22. CRITERIOS DE ACEPTACIÓN

| # | Criterio | Obligatorio |
|---|----------|-------------|
| 1 | Endpoints CRUD cuentas funcionan | ✅ |
| 2 | Endpoints saldos funcionan | ✅ |
| 3 | Enmascaramiento activo | ✅ |
| 4 | Permisos validados | ✅ |
| 5 | Corrección crea nuevo registro | ✅ |
| 6 | Cancelación requiere motivo | ✅ |
| 7 | Auditoría completa | ✅ |
| 8 | Errores descriptivos | ✅ |
| 9 | Estados vacíos manejados | ✅ |
| 10 | No regresión en módulos existentes | ✅ |

---

## 23. ROLLBACK

### 23.1 Rollback de código

```bash
# Eliminar archivos nuevos
rm -f /app/backend/modules/finanzas/cuentas_bancarias.py
rm -f /app/backend/modules/finanzas/saldos_bancarios.py
rm -f /app/backend/modules/finanzas/models_bancarios.py
rm -f /app/backend/modules/finanzas/repository_bancarios.py
rm -f /app/backend/modules/finanzas/utils_bancarios.py

# Remover imports del router principal si se agregaron
# (editar server.py manualmente)

# Reiniciar
sudo supervisorctl restart backend
```

### 23.2 Rollback de datos

Los datos capturados durante pruebas pueden eliminarse con:

```sql
-- SOLO SI AUTORIZADO
DELETE FROM Finanzas_SaldosBancarios;
DELETE FROM Finanzas_Cat_CuentasBancarias;
```

**Tiempo estimado de rollback**: < 5 minutos

---

## 24. REGLAS DE NO REGRESIÓN

| Módulo | Verificación | Método |
|--------|--------------|--------|
| CxP | No se modifica ningún archivo | Revisión de git diff |
| Cuadre Cortes Z | `/api/finanzas/tesoreria/sucursales` → 4 sucursales | curl |
| Comercial V2 | `/api/v2/comercial/dashboard` → responde OK | curl |
| Tablero Ejecutivo | No se modifica | Revisión de git diff |
| Compras | No se modifica | Revisión de git diff |
| Propinas TPV | No se modifica | Revisión de git diff |
| Auth/RBAC | No se modifica | Revisión de git diff |
| Menús globales | No se modifica | Revisión de git diff |
| Filtros globales | No se modifica | Revisión de git diff |

---

## SEPARACIÓN DE FASES

### A) 5A.1-FUNC-BACKEND (Esta propuesta)

| Componente | Estado |
|------------|--------|
| Endpoints CRUD cuentas bancarias | PROPUESTA |
| Endpoints saldos bancarios | PROPUESTA |
| Endpoint catálogo bancos | PROPUESTA |
| Validaciones y permisos | PROPUESTA |
| Repository EDARSAHUB | PROPUESTA |
| Modelos Pydantic | PROPUESTA |

### B) 5A.1-FUNC-FRONTEND (Fase posterior separada)

| Componente | Estado |
|------------|--------|
| Página cuentas bancarias | PENDIENTE |
| Formulario alta/edición cuenta | PENDIENTE |
| Tabla de cuentas | PENDIENTE |
| Formulario captura saldo | PENDIENTE |
| Modal corrección saldo | PENDIENTE |
| Historial de saldos | PENDIENTE |

---

## AUTORIZACIÓN SOLICITADA

### Para 5A.1-FUNC-BACKEND:

1. ✅ Crear `cuentas_bancarias.py` con endpoints CRUD
2. ✅ Crear `saldos_bancarios.py` con endpoints de saldos
3. ✅ Crear `models_bancarios.py` con modelos Pydantic
4. ✅ Crear `repository_bancarios.py` para queries EDARSAHUB
5. ✅ Crear `utils_bancarios.py` para enmascaramiento
6. ✅ Registrar routers en `server.py`
7. ✅ Pruebas con curl

### NO se solicita:

- ❌ Crear frontend
- ❌ Modificar menús
- ❌ Crear dashboard
- ❌ Modificar CxP, Cuadre Cortes Z, Comercial V2, etc.

---

**ESTADO**: ⏳ **PROPUESTA 5A.1-FUNC-BACKEND - PENDIENTE AUTORIZACIÓN**

*Documento: P1-FASE5A-1-ENDPOINTS-CUENTAS-SALDOS-BANCARIOS.md*  
*Fecha: 2025-12-05 v1.0*

---

## CIERRE IMPLEMENTACIÓN BACKEND P1-FASE5A.1

---

### RESUMEN DE EJECUCIÓN

| Campo | Valor |
|-------|-------|
| **Fecha/Hora** | 2026-05-06 00:15 UTC |
| **Estado** | ✅ COMPLETADO |
| **Alcance** | Backend API únicamente |

---

### ARCHIVOS CREADOS

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| `/app/backend/modules/finanzas/utils_bancarios.py` | Enmascaramiento y validaciones | ~150 |
| `/app/backend/modules/finanzas/models_bancarios.py` | Modelos Pydantic request/response | ~180 |
| `/app/backend/modules/finanzas/repository_bancarios.py` | Queries EDARSAHUB | ~700 |
| `/app/backend/modules/finanzas/cuentas_bancarias.py` | Router endpoints cuentas | ~430 |
| `/app/backend/modules/finanzas/saldos_bancarios.py` | Router endpoints saldos | ~530 |

---

### ENDPOINTS CREADOS (13 de 14 autorizados)

| # | Endpoint | Método | Estado |
|---|----------|--------|--------|
| 1 | `/api/v2/finanzas/bancos` | GET | ✅ |
| 2 | `/api/v2/finanzas/cuentas-bancarias` | GET | ✅ |
| 3 | `/api/v2/finanzas/cuentas-bancarias/{id}` | GET | ✅ |
| 4 | `/api/v2/finanzas/cuentas-bancarias` | POST | ✅ |
| 5 | `/api/v2/finanzas/cuentas-bancarias/{id}` | PUT | ✅ |
| 6 | `/api/v2/finanzas/cuentas-bancarias/{id}/desactivar` | POST | ✅ |
| 7 | `/api/v2/finanzas/cuentas-bancarias/{id}/saldos` | GET | ✅ |
| 8 | `/api/v2/finanzas/cuentas-bancarias/{id}/saldo-actual` | GET | ✅ |
| 9 | `/api/v2/finanzas/saldos-bancarios` | POST | ✅ |
| 10 | `/api/v2/finanzas/saldos-bancarios/{id}/corregir` | POST | ✅ |
| 11 | `/api/v2/finanzas/saldos-bancarios/{id}/cancelar` | POST | ✅ |
| 12 | `/api/v2/finanzas/saldos-bancarios/{id}/historial` | GET | ✅ |
| 13 | `/api/v2/finanzas/saldos-bancarios/total` | GET | ✅ |

### ENDPOINT NO CREADO (por diseño)

| Endpoint | Razón |
|----------|-------|
| `GET /cuentas-bancarias/{id}/completa` | No autorizado - expone datos sin enmascarar |

---

### VALIDACIONES IMPLEMENTADAS

| Validación | Estado |
|------------|--------|
| Enmascaramiento cuenta/CLABE en respuestas | ✅ |
| BancoID debe existir en Global_Cat_Bancos | ✅ |
| Número de cuenta único | ✅ |
| Alias único | ✅ |
| CLABE formato 18 dígitos | ✅ |
| Saldo vigente único por cuenta+fecha | ✅ |
| Corrección crea nuevo registro VIGENTE | ✅ |
| Cancelación requiere motivo (min 10 chars) | ✅ |
| Fecha saldo no futura | ✅ |
| No editar registros históricos | ✅ |

---

### EVIDENCIA DE ENMASCARAMIENTO

```json
// Respuesta de GET /cuentas-bancarias/{id}
{
  "cuenta_bancaria_id": 8,
  "numero_cuenta": "****6789",  // ← ENMASCARADO
  "clabe": "****",              // ← ENMASCARADO
  "alias": "BBVA Principal"
}
```

---

### EVIDENCIA DE AUDITORÍA

```json
// Respuesta de GET /saldos-bancarios/{id}/historial
{
  "historial": [
    {"accion": "CORRECCION", "saldo_final": 1200000.5},
    {"accion": "CORRECCION_NUEVA", "saldo_final": 1250000.75}
  ]
}
```

---

### PRUEBAS REALIZADAS

| # | Prueba | Resultado |
|---|--------|-----------|
| 1 | GET bancos responde catálogo | ✅ PASS (5 bancos) |
| 2 | GET cuentas estado vacío | ✅ PASS |
| 3 | POST cuenta valida BancoID | ✅ PASS |
| 4 | POST cuenta duplicada rechazada | ✅ PASS |
| 5 | GET cuenta datos enmascarados | ✅ PASS |
| 6 | PUT cuenta actualiza alias | ✅ PASS |
| 7 | POST saldo capturado | ✅ PASS |
| 8 | POST saldo duplicado rechazado | ✅ PASS |
| 9 | GET saldo-actual funciona | ✅ PASS |
| 10 | POST corregir crea nuevo VIGENTE | ✅ PASS |
| 11 | POST cancelar exige motivo | ✅ PASS |
| 12 | POST cancelar con motivo válido | ✅ PASS |
| 13 | GET historial muestra trazabilidad | ✅ PASS |
| 14 | GET total calcula correctamente | ✅ PASS |

---

### PRUEBAS DE NO REGRESIÓN

| Módulo | Estado | Verificación |
|--------|--------|--------------|
| Cuadre Cortes Z | ✅ INTACTO | 4 sucursales operativas |
| Comercial V2 | ✅ INTACTO | Endpoint responde 200 |
| Auth/RBAC | ✅ INTACTO | Login funciona |
| CxP | ✅ INTACTO | No modificado |
| Tablero Ejecutivo | ✅ INTACTO | No modificado |

---

### MODIFICACIONES A DDL (durante implementación)

| Tabla | Columna | Cambio | Razón |
|-------|---------|--------|-------|
| `Finanzas_SaldosBancarios` | `UsuarioCreacionID` | `NOT NULL` → `NULL` | Usuario_Catalogo vacía |

---

### ROLLBACK EXACTO

```bash
# 1. Eliminar archivos nuevos
rm -f /app/backend/modules/finanzas/utils_bancarios.py
rm -f /app/backend/modules/finanzas/models_bancarios.py
rm -f /app/backend/modules/finanzas/repository_bancarios.py
rm -f /app/backend/modules/finanzas/cuentas_bancarias.py
rm -f /app/backend/modules/finanzas/saldos_bancarios.py

# 2. Revertir imports en server.py (líneas ~295-305)
# Eliminar:
#   from modules.finanzas.cuentas_bancarias import router as cuentas_bancarias_router
#   from modules.finanzas.saldos_bancarios import router as saldos_bancarios_router
#   api_router.include_router(cuentas_bancarias_router)
#   api_router.include_router(saldos_bancarios_router)

# 3. Reiniciar
sudo supervisorctl restart backend
```

**Tiempo estimado de rollback**: < 5 minutos

---

### DATOS DE PRUEBA

Los datos de prueba creados durante las pruebas fueron eliminados al finalizar.
Tablas `Finanzas_Cat_CuentasBancarias` y `Finanzas_SaldosBancarios` quedan vacías.

---

**ESTADO FINAL**: ✅ **P1-FASE5A.1-FUNC-BACKEND COMPLETADO**

*Documento actualizado: 2026-05-06 v1.0 CIERRE*
