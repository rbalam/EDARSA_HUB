# P1-FASE5A.1 — Frontend: Cuentas y Saldos Bancarios

## PROPUESTA TÉCNICA

| Campo | Valor |
|-------|-------|
| **Fecha** | 2025-12-06 |
| **Versión** | 1.0 |
| **Estado** | PROPUESTA - PENDIENTE AUTORIZACIÓN |
| **Prioridad** | P1 |
| **Padre** | P1-FASE5A.1-FUNC-BACKEND (COMPLETADO) |
| **Prerrequisito** | 13 endpoints backend operativos ✅ |

---

## 1. OBJETIVO FUNCIONAL

Implementar la interfaz de usuario para gestionar el catálogo de cuentas bancarias y la captura/consulta de saldos bancarios, consumiendo exclusivamente los endpoints backend ya creados en P1-FASE5A.1-FUNC-BACKEND.

**Objetivos específicos:**

1. Permitir al usuario crear, editar y desactivar cuentas bancarias
2. Permitir capturar saldos bancarios por cuenta y fecha
3. Permitir corregir y cancelar saldos con trazabilidad
4. Mostrar el saldo bancario total consolidado
5. Mantener datos sensibles enmascarados en todo momento

---

## 2. ALCANCE EXACTO

### BLOQUE A — Catálogo de Cuentas Bancarias

| Funcionalidad | Incluido |
|---------------|----------|
| Listar cuentas bancarias | ✅ |
| Crear cuenta bancaria | ✅ |
| Editar cuenta bancaria (alias, cuenta principal) | ✅ |
| Desactivar cuenta bancaria (baja lógica) | ✅ |
| Ver último saldo de cada cuenta | ✅ |
| Mostrar datos enmascarados | ✅ |

### BLOQUE B — Captura y Consulta de Saldos

| Funcionalidad | Incluido |
|---------------|----------|
| Capturar saldo por cuenta y fecha | ✅ |
| Ver último saldo vigente | ✅ |
| Ver historial de saldos | ✅ |
| Corregir saldo existente | ✅ |
| Cancelar saldo con motivo | ✅ |
| Ver saldo bancario total | ✅ |
| Trazabilidad de cambios | ✅ |

---

## 3. FUERA DE ALCANCE

| Elemento | Razón |
|----------|-------|
| ❌ Efectivo pendiente de depositar | Fase 5A.4 |
| ❌ Dashboard posición de efectivo consolidado | Fase 5A.5 |
| ❌ Widget de posición en dashboard principal | Fase 5A.3 |
| ❌ Importación Excel de cuentas/saldos | Fase posterior |
| ❌ API bancaria | Fase futura |
| ❌ Conciliación bancaria | Fase futura |
| ❌ Endpoint de datos completos (sin enmascarar) | No autorizado |
| ❌ Flujo proyectado | Fase futura |
| ❌ Integración con cortes de caja | Fase 5A.4 |
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

## 4. PANTALLAS/COMPONENTES PROPUESTOS

### 4.1 Estructura de componentes

```
/app/frontend/src/components/finanzas/cuentas-bancarias/
├── CuentasBancariasPage.jsx          # Página principal del módulo
├── TablaCuentasBancarias.jsx         # Tabla listado de cuentas
├── FormularioCuentaBancaria.jsx      # Modal crear/editar cuenta
├── ModalDesactivarCuenta.jsx         # Confirmación de baja
├── DetalleCuentaBancaria.jsx         # Vista detalle con saldos
│
├── saldos/
│   ├── FormularioCapturaSaldo.jsx    # Modal captura de saldo
│   ├── FormularioCorreccionSaldo.jsx # Modal corrección
│   ├── ModalCancelarSaldo.jsx        # Confirmación cancelación
│   ├── HistorialSaldos.jsx           # Lista de saldos con auditoría
│   └── TarjetaSaldoTotal.jsx         # Widget saldo total bancario
│
└── hooks/
    ├── useCuentasBancarias.js        # Hook para CRUD cuentas
    ├── useSaldosBancarios.js         # Hook para saldos
    └── useBancos.js                  # Hook para catálogo bancos
```

### 4.2 Descripción de componentes

| Componente | Propósito | Tipo |
|------------|-----------|------|
| `CuentasBancariasPage` | Contenedor principal, gestiona estado global | Página |
| `TablaCuentasBancarias` | Lista cuentas con acciones | Tabla |
| `FormularioCuentaBancaria` | Alta y edición de cuentas | Modal |
| `ModalDesactivarCuenta` | Confirmación de desactivación | Modal |
| `DetalleCuentaBancaria` | Vista detalle con historial | Panel |
| `FormularioCapturaSaldo` | Captura de saldo diario | Modal |
| `FormularioCorreccionSaldo` | Corregir saldo existente | Modal |
| `ModalCancelarSaldo` | Confirmación cancelación | Modal |
| `HistorialSaldos` | Lista de saldos con estatus | Tabla |
| `TarjetaSaldoTotal` | KPI saldo total | Card |

---

## 5. UBICACIÓN EN MÓDULO FINANZAS

### 5.1 Integración propuesta

**Opción recomendada**: Nuevo tab dentro del módulo Finanzas existente.

```
Finanzas (módulo existente)
├── [Tab existente] Cuentas por Pagar (CxP)
├── [Tab existente] Tesorería / Cuadre Cortes Z
├── [NUEVO TAB] Cuentas Bancarias    ← P1-FASE5A.1
│   ├── Catálogo de cuentas
│   ├── Captura de saldos
│   └── Saldo total bancario
└── [Futuro] Dashboard Posición Efectivo  ← P1-FASE5A.5
```

### 5.2 Ruta propuesta

```
/finanzas/cuentas-bancarias
```

### 5.3 Navegación

- Se agrega entrada en el menú lateral de Finanzas
- NO se modifica el menú global
- NO se modifica el header
- NO se agregan filtros globales

---

## 6. INTEGRACIÓN CON TAB EXISTENTE O NUEVO TAB

**Decisión**: **NUEVO TAB**

| Aspecto | Decisión |
|---------|----------|
| ¿Nuevo tab? | SÍ |
| ¿Dentro de tab existente? | NO |
| ¿Afecta CxP? | NO |
| ¿Afecta Tesorería? | NO |
| Nombre del tab | "Cuentas Bancarias" |
| Icono sugerido | `Building2` o `Landmark` (lucide-react) |

---

## 7. FLUJO DE USUARIO — ALTA DE CUENTA

```
┌─────────────────────────────────────────────────────────────────┐
│ FLUJO: Crear cuenta bancaria                                    │
├─────────────────────────────────────────────────────────────────┤
│ 1. Usuario accede a Finanzas > Cuentas Bancarias                │
│ 2. Click en botón "+ Nueva cuenta"                              │
│ 3. Se abre modal FormularioCuentaBancaria                       │
│ 4. Usuario selecciona banco del dropdown (GET /bancos)          │
│ 5. Usuario ingresa:                                             │
│    - Número de cuenta (10-20 dígitos)                           │
│    - CLABE (opcional, 18 dígitos)                               │
│    - Alias (3-50 caracteres)                                    │
│    - Moneda (dropdown: MXN, USD, EUR, CAD)                      │
│    - ¿Es cuenta principal? (checkbox)                           │
│ 6. Click en "Guardar"                                           │
│ 7. Frontend valida formato antes de enviar                      │
│ 8. POST /api/v2/finanzas/cuentas-bancarias                      │
│ 9. Si éxito: cerrar modal, refrescar lista, mostrar toast OK   │
│ 10. Si error: mostrar mensaje de error en modal                 │
└─────────────────────────────────────────────────────────────────┘
```

**Validaciones frontend antes de enviar:**

| Campo | Validación |
|-------|------------|
| Banco | Requerido |
| Número cuenta | 10-20 dígitos numéricos |
| CLABE | Exactamente 18 dígitos si se proporciona |
| Alias | 3-50 caracteres |
| Moneda | Selección de lista |

---

## 8. FLUJO DE USUARIO — EDICIÓN DE CUENTA

```
┌─────────────────────────────────────────────────────────────────┐
│ FLUJO: Editar cuenta bancaria                                   │
├─────────────────────────────────────────────────────────────────┤
│ 1. Usuario ve la tabla de cuentas                               │
│ 2. Click en icono "Editar" de una cuenta                        │
│ 3. Se abre modal FormularioCuentaBancaria (modo edición)        │
│ 4. Campos editables:                                            │
│    - Alias                                                      │
│    - ¿Es cuenta principal?                                      │
│ 5. Campos NO editables (solo lectura, deshabilitados):          │
│    - Banco                                                      │
│    - Número de cuenta (enmascarado)                             │
│    - CLABE (enmascarado)                                        │
│    - Moneda                                                     │
│ 6. Click en "Guardar cambios"                                   │
│ 7. PUT /api/v2/finanzas/cuentas-bancarias/{id}                  │
│ 8. Si éxito: cerrar modal, refrescar lista, mostrar toast OK   │
│ 9. Si error: mostrar mensaje de error                           │
└─────────────────────────────────────────────────────────────────┘
```

**Nota**: Los campos inmutables (banco, número, CLABE, moneda) se muestran pero están deshabilitados visualmente.

---

## 9. FLUJO DE USUARIO — BAJA LÓGICA DE CUENTA

```
┌─────────────────────────────────────────────────────────────────┐
│ FLUJO: Desactivar cuenta bancaria                               │
├─────────────────────────────────────────────────────────────────┤
│ 1. Usuario ve la tabla de cuentas                               │
│ 2. Click en icono "Desactivar" de una cuenta                    │
│ 3. Se abre modal ModalDesactivarCuenta                          │
│ 4. Modal muestra:                                               │
│    - Alias de la cuenta                                         │
│    - Banco                                                      │
│    - Último saldo (si existe)                                   │
│    - ADVERTENCIA si tiene saldos vigentes                       │
│ 5. Usuario ingresa motivo (mínimo 10 caracteres)                │
│ 6. Click en "Confirmar desactivación"                           │
│ 7. POST /api/v2/finanzas/cuentas-bancarias/{id}/desactivar      │
│ 8. Si éxito: cerrar modal, refrescar lista, mostrar toast OK   │
│ 9. Si error (tiene saldos vigentes): mostrar error específico   │
└─────────────────────────────────────────────────────────────────┘
```

**Validación especial**: Si la cuenta tiene saldos vigentes, el backend rechaza la desactivación. El frontend debe mostrar mensaje claro indicando que primero deben cancelarse los saldos.

---

## 10. FLUJO DE USUARIO — CAPTURA DE SALDO

```
┌─────────────────────────────────────────────────────────────────┐
│ FLUJO: Capturar saldo bancario                                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. Usuario accede al detalle de una cuenta (click en fila)      │
│ 2. Ve el historial de saldos y el último saldo vigente          │
│ 3. Click en botón "+ Capturar saldo"                            │
│ 4. Se abre modal FormularioCapturaSaldo                         │
│ 5. Usuario ingresa:                                             │
│    - Fecha del saldo (date picker, no futuro)                   │
│    - Saldo final (input numérico con decimales)                 │
│    - Observaciones (opcional)                                   │
│ 6. Click en "Guardar saldo"                                     │
│ 7. POST /api/v2/finanzas/saldos-bancarios                       │
│ 8. Si éxito: cerrar modal, refrescar historial, toast OK        │
│ 9. Si error (ya existe saldo para fecha): mostrar mensaje       │
│    indicando usar "Corregir saldo"                              │
└─────────────────────────────────────────────────────────────────┘
```

**Validaciones frontend:**

| Campo | Validación |
|-------|------------|
| Fecha | Requerido, no puede ser futura |
| Saldo | Requerido, número válido |
| Observaciones | Opcional, máximo 500 caracteres |

---

## 11. FLUJO DE USUARIO — CORRECCIÓN DE SALDO

```
┌─────────────────────────────────────────────────────────────────┐
│ FLUJO: Corregir saldo bancario                                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. Usuario ve el historial de saldos de una cuenta              │
│ 2. Identifica un saldo VIGENTE que necesita corrección          │
│ 3. Click en icono "Corregir" del saldo                          │
│ 4. Se abre modal FormularioCorreccionSaldo                      │
│ 5. Modal muestra:                                               │
│    - Fecha del saldo                                            │
│    - Saldo actual (solo lectura)                                │
│    - Campo: Saldo correcto                                      │
│    - Campo: Motivo de corrección (mínimo 10 caracteres)         │
│ 6. Click en "Confirmar corrección"                              │
│ 7. POST /api/v2/finanzas/saldos-bancarios/{id}/corregir         │
│ 8. Si éxito:                                                    │
│    - Cerrar modal                                               │
│    - Refrescar historial (mostrará CORREGIDO + nuevo VIGENTE)   │
│    - Toast OK                                                   │
│ 9. Si error: mostrar mensaje                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Comportamiento visual post-corrección:**

El historial mostrará:
- Saldo anterior con badge "CORREGIDO" (gris/tachado)
- Saldo nuevo con badge "VIGENTE" (verde)

---

## 12. FLUJO DE USUARIO — CANCELACIÓN DE SALDO

```
┌─────────────────────────────────────────────────────────────────┐
│ FLUJO: Cancelar saldo bancario                                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. Usuario ve el historial de saldos de una cuenta              │
│ 2. Identifica un saldo VIGENTE que necesita cancelarse          │
│ 3. Click en icono "Cancelar" del saldo                          │
│ 4. Se abre modal ModalCancelarSaldo                             │
│ 5. Modal muestra:                                               │
│    - Fecha del saldo                                            │
│    - Monto del saldo                                            │
│    - ADVERTENCIA: "Esta acción no se puede deshacer"            │
│    - Campo: Motivo de cancelación (OBLIGATORIO, min 10 chars)   │
│ 6. Click en "Confirmar cancelación"                             │
│ 7. POST /api/v2/finanzas/saldos-bancarios/{id}/cancelar         │
│ 8. Si éxito:                                                    │
│    - Cerrar modal                                               │
│    - Refrescar historial (saldo aparece como CANCELADO)         │
│    - Toast OK                                                   │
│ 9. Si error: mostrar mensaje                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Comportamiento visual post-cancelación:**

El saldo aparece en historial con:
- Badge "CANCELADO" (rojo)
- Texto tachado o atenuado
- Fecha y usuario de cancelación visible

---

## 13. ESTADOS VACÍOS

### 13.1 Sin cuentas bancarias

```jsx
// TablaCuentasBancarias.jsx - Estado vacío
<div className="text-center py-12">
  <Landmark className="mx-auto h-12 w-12 text-gray-400" />
  <h3 className="mt-2 text-sm font-medium text-gray-900">
    No hay cuentas bancarias
  </h3>
  <p className="mt-1 text-sm text-gray-500">
    Configure al menos una cuenta bancaria para comenzar.
  </p>
  <div className="mt-6">
    <Button onClick={onNuevaCuenta}>
      + Nueva cuenta
    </Button>
  </div>
</div>
```

### 13.2 Cuenta sin saldos

```jsx
// DetalleCuentaBancaria.jsx - Sin saldos
<div className="text-center py-8">
  <Wallet className="mx-auto h-10 w-10 text-gray-400" />
  <p className="mt-2 text-sm text-gray-500">
    Esta cuenta no tiene saldos registrados.
  </p>
  <Button variant="outline" onClick={onCapturarSaldo}>
    Capturar saldo
  </Button>
</div>
```

### 13.3 Saldo total en cero

```jsx
// TarjetaSaldoTotal.jsx - Sin saldos
<Card>
  <CardHeader>
    <CardTitle>Saldo Bancario Total</CardTitle>
  </CardHeader>
  <CardContent>
    <p className="text-2xl font-bold text-gray-400">$0.00</p>
    <p className="text-sm text-gray-500">
      No hay saldos registrados. Capture el saldo de las cuentas bancarias.
    </p>
  </CardContent>
</Card>
```

---

## 14. ESTADOS DE ERROR

### 14.1 Error de conexión

```jsx
<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>Error de conexión</AlertTitle>
  <AlertDescription>
    No se pudo conectar al servidor. Verifique su conexión e intente de nuevo.
  </AlertDescription>
</Alert>
```

### 14.2 Error de validación (ejemplo: cuenta duplicada)

```jsx
// En FormularioCuentaBancaria.jsx
{error && (
  <Alert variant="destructive" className="mb-4">
    <AlertCircle className="h-4 w-4" />
    <AlertDescription>{error}</AlertDescription>
  </Alert>
)}
```

### 14.3 Error: saldo duplicado

```jsx
<Alert variant="warning">
  <AlertTriangle className="h-4 w-4" />
  <AlertTitle>Saldo ya existe</AlertTitle>
  <AlertDescription>
    Ya existe un saldo vigente para esta cuenta y fecha. 
    Use la opción "Corregir" si necesita modificar el valor.
  </AlertDescription>
</Alert>
```

### 14.4 Error: cuenta con saldos vigentes

```jsx
<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>No se puede desactivar</AlertTitle>
  <AlertDescription>
    Esta cuenta tiene saldos vigentes. 
    Cancele los saldos antes de desactivar la cuenta.
  </AlertDescription>
</Alert>
```

---

## 15. VALIDACIONES FRONTEND

### 15.1 Formulario Cuenta Bancaria

| Campo | Validación | Mensaje de error |
|-------|------------|------------------|
| Banco | Requerido | "Seleccione un banco" |
| Número cuenta | 10-20 dígitos | "Debe tener entre 10 y 20 dígitos" |
| Número cuenta | Solo números | "Solo se permiten números" |
| CLABE | 18 dígitos exactos | "CLABE debe tener 18 dígitos" |
| CLABE | Solo números | "Solo se permiten números" |
| Alias | Min 3 caracteres | "Mínimo 3 caracteres" |
| Alias | Max 50 caracteres | "Máximo 50 caracteres" |

### 15.2 Formulario Captura Saldo

| Campo | Validación | Mensaje de error |
|-------|------------|------------------|
| Fecha | Requerido | "Seleccione una fecha" |
| Fecha | No futura | "La fecha no puede ser futura" |
| Saldo | Requerido | "Ingrese el saldo" |
| Saldo | Número válido | "Ingrese un número válido" |
| Observaciones | Max 500 chars | "Máximo 500 caracteres" |

### 15.3 Formulario Corrección/Cancelación

| Campo | Validación | Mensaje de error |
|-------|------------|------------------|
| Motivo | Requerido | "El motivo es obligatorio" |
| Motivo | Min 10 caracteres | "Mínimo 10 caracteres" |
| Motivo | Max 500 caracteres | "Máximo 500 caracteres" |

---

## 16. CONSUMO EXACTO DE ENDPOINTS

### 16.1 BLOQUE A — Cuentas Bancarias

| Acción UI | Endpoint | Método |
|-----------|----------|--------|
| Cargar catálogo bancos | `/api/v2/finanzas/bancos` | GET |
| Listar cuentas | `/api/v2/finanzas/cuentas-bancarias` | GET |
| Obtener cuenta | `/api/v2/finanzas/cuentas-bancarias/{id}` | GET |
| Crear cuenta | `/api/v2/finanzas/cuentas-bancarias` | POST |
| Editar cuenta | `/api/v2/finanzas/cuentas-bancarias/{id}` | PUT |
| Desactivar cuenta | `/api/v2/finanzas/cuentas-bancarias/{id}/desactivar` | POST |

### 16.2 BLOQUE B — Saldos Bancarios

| Acción UI | Endpoint | Método |
|-----------|----------|--------|
| Listar saldos de cuenta | `/api/v2/finanzas/cuentas-bancarias/{id}/saldos` | GET |
| Obtener último saldo | `/api/v2/finanzas/cuentas-bancarias/{id}/saldo-actual` | GET |
| Capturar saldo | `/api/v2/finanzas/saldos-bancarios` | POST |
| Corregir saldo | `/api/v2/finanzas/saldos-bancarios/{id}/corregir` | POST |
| Cancelar saldo | `/api/v2/finanzas/saldos-bancarios/{id}/cancelar` | POST |
| Ver historial | `/api/v2/finanzas/saldos-bancarios/{id}/historial` | GET |
| Saldo total | `/api/v2/finanzas/saldos-bancarios/total` | GET |

---

## 17. PERMISOS REQUERIDOS POR ACCIÓN

| Acción | Permiso | Roles sugeridos |
|--------|---------|-----------------|
| Ver cuentas | `finanzas.cuentas_bancarias.view` | Todos con acceso a Finanzas |
| Crear cuenta | `finanzas.cuentas_bancarias.manage` | SuperAdmin, Director Finanzas |
| Editar cuenta | `finanzas.cuentas_bancarias.manage` | SuperAdmin, Director Finanzas |
| Desactivar cuenta | `finanzas.cuentas_bancarias.manage` | SuperAdmin, Director Finanzas |
| Ver saldos | `finanzas.saldos.view` | Todos con acceso a Finanzas |
| Capturar saldo | `finanzas.saldos.manage` | SuperAdmin, Dir. Finanzas, Contador, Tesorero |
| Corregir saldo | `finanzas.saldos.manage` | SuperAdmin, Dir. Finanzas, Contador, Tesorero |
| Cancelar saldo | `finanzas.saldos.manage` | SuperAdmin, Dir. Finanzas, Contador, Tesorero |

**Implementación frontend:**

```jsx
// Ejemplo de ocultación de botones según permiso
{hasPermission('finanzas.cuentas_bancarias.manage') && (
  <Button onClick={onNuevaCuenta}>+ Nueva cuenta</Button>
)}
```

---

## 18. ENMASCARAMIENTO VISUAL

### 18.1 Regla general

**NUNCA** mostrar número de cuenta ni CLABE completos en la UI.

### 18.2 Implementación

Los endpoints ya devuelven datos enmascarados:
- Número cuenta: `****6789`
- CLABE: `****4567`

El frontend solo debe mostrar lo que recibe del backend.

### 18.3 Ejemplo visual

```
┌─────────────────────────────────────────────────────┐
│ BBVA Principal                                      │
├─────────────────────────────────────────────────────┤
│ Banco:         BBVA BANCOMER                        │
│ Cuenta:        ****6789                             │
│ CLABE:         ****4567                             │
│ Moneda:        MXN                                  │
│ Último saldo:  $1,250,000.75 (05/05/2026)          │
└─────────────────────────────────────────────────────┘
```

---

## 19. CONFIRMACIÓN: NO SE USA ENDPOINT DE DATOS COMPLETOS

> ✅ **CONFIRMADO**: El frontend NO consumirá ni implementará el endpoint 
> `GET /api/v2/finanzas/cuentas-bancarias/{id}/completa` porque:
> 
> 1. No fue autorizado su creación
> 2. No existe en el backend
> 3. Expondría datos bancarios sensibles
> 
> Todos los datos de cuenta se muestran SIEMPRE enmascarados.

---

## 20. ARCHIVOS FRONTEND PROPUESTOS

### 20.1 Estructura completa

```
/app/frontend/src/
├── components/
│   └── finanzas/
│       └── cuentas-bancarias/
│           ├── CuentasBancariasPage.jsx
│           ├── TablaCuentasBancarias.jsx
│           ├── FormularioCuentaBancaria.jsx
│           ├── ModalDesactivarCuenta.jsx
│           ├── DetalleCuentaBancaria.jsx
│           ├── saldos/
│           │   ├── FormularioCapturaSaldo.jsx
│           │   ├── FormularioCorreccionSaldo.jsx
│           │   ├── ModalCancelarSaldo.jsx
│           │   ├── HistorialSaldos.jsx
│           │   └── TarjetaSaldoTotal.jsx
│           └── hooks/
│               ├── useCuentasBancarias.js
│               ├── useSaldosBancarios.js
│               └── useBancos.js
│
└── pages/
    └── finanzas/
        └── CuentasBancariasPage.jsx  (o integrar en estructura existente)
```

### 20.2 Total de archivos nuevos

| Tipo | Cantidad |
|------|----------|
| Componentes JSX | 10 |
| Hooks | 3 |
| **Total** | **13 archivos** |

---

## 21. COMPONENTES REUTILIZABLES

### 21.1 Componentes Shadcn/UI a usar

| Componente | Uso |
|------------|-----|
| `Button` | Acciones principales |
| `Card` | Contenedores de información |
| `Dialog` | Modales |
| `Input` | Campos de texto |
| `Select` | Dropdown de banco/moneda |
| `Table` | Listado de cuentas y saldos |
| `Badge` | Estados (VIGENTE, CORREGIDO, CANCELADO) |
| `Alert` | Mensajes de error/advertencia |
| `Textarea` | Campo de motivo |
| `Calendar` | Selector de fecha |
| `Popover` | Date picker |

### 21.2 Iconos (lucide-react)

| Icono | Uso |
|-------|-----|
| `Landmark` | Cuentas bancarias |
| `Wallet` | Saldos |
| `Plus` | Agregar |
| `Pencil` | Editar |
| `Trash2` | Desactivar |
| `RotateCcw` | Corregir |
| `X` | Cancelar |
| `History` | Historial |
| `AlertCircle` | Error |
| `CheckCircle` | Éxito |

---

## 22. PRUEBAS FUNCIONALES

### 22.1 BLOQUE A — Cuentas

| # | Prueba | Criterio |
|---|--------|----------|
| 1 | Página carga sin errores | Sin errores en consola |
| 2 | Estado vacío se muestra | Mensaje + botón visible |
| 3 | Crear cuenta válida | Toast éxito, aparece en lista |
| 4 | Crear cuenta duplicada | Error visible |
| 5 | Editar alias | Alias actualizado |
| 6 | Desactivar cuenta sin saldos | Toast éxito, desaparece de lista |
| 7 | Desactivar cuenta con saldos | Error visible |
| 8 | Datos enmascarados | ****XXXX visible |

### 22.2 BLOQUE B — Saldos

| # | Prueba | Criterio |
|---|--------|----------|
| 9 | Capturar saldo válido | Toast éxito, aparece en historial |
| 10 | Capturar saldo duplicado | Error visible |
| 11 | Capturar saldo fecha futura | Error validación frontend |
| 12 | Corregir saldo | Anterior CORREGIDO, nuevo VIGENTE |
| 13 | Cancelar sin motivo | Error validación frontend |
| 14 | Cancelar con motivo | Toast éxito, badge CANCELADO |
| 15 | Historial muestra trazabilidad | Todos los estados visibles |
| 16 | Saldo total calcula correctamente | Suma de últimos vigentes |

---

## 23. PRUEBAS DE NO REGRESIÓN

| Módulo | Verificación |
|--------|--------------|
| CxP | Página carga correctamente |
| Cuadre Cortes Z | Sucursales se muestran (4) |
| Comercial V2 | Dashboard responde |
| Tablero Ejecutivo | No se modifica |
| Menús globales | Sin cambios |
| Filtros globales | Sin cambios |
| Login | Funciona correctamente |

---

## 24. ROLLBACK

### 24.1 Rollback de archivos

```bash
# Eliminar carpeta completa
rm -rf /app/frontend/src/components/finanzas/cuentas-bancarias/

# Si se modificó routing, revertir
git checkout -- /app/frontend/src/App.jsx
git checkout -- /app/frontend/src/routes.jsx  # o equivalente

# Rebuild
cd /app/frontend && yarn build
```

### 24.2 Rollback de navegación

Si se agregó entrada al menú de Finanzas, revertir el cambio en el archivo correspondiente.

**Tiempo estimado de rollback**: < 5 minutos

---

## 25. CRITERIOS DE ACEPTACIÓN

| # | Criterio | Obligatorio |
|---|----------|-------------|
| 1 | Página de cuentas bancarias accesible | ✅ |
| 2 | CRUD de cuentas funciona | ✅ |
| 3 | Captura de saldos funciona | ✅ |
| 4 | Corrección de saldos funciona | ✅ |
| 5 | Cancelación de saldos funciona | ✅ |
| 6 | Historial con trazabilidad | ✅ |
| 7 | Saldo total visible | ✅ |
| 8 | Datos siempre enmascarados | ✅ |
| 9 | Estados vacíos claros | ✅ |
| 10 | Errores claros | ✅ |
| 11 | Validaciones frontend | ✅ |
| 12 | No regresión en módulos existentes | ✅ |
| 13 | Sin datos demo | ✅ |
| 14 | Sin endpoint de datos completos | ✅ |

---

## SEPARACIÓN DE IMPLEMENTACIÓN PROPUESTA

### Fase 1: BLOQUE A — Catálogo de cuentas (Implementación mínima)

| Componente | Prioridad |
|------------|-----------|
| `CuentasBancariasPage` | P0 |
| `TablaCuentasBancarias` | P0 |
| `FormularioCuentaBancaria` | P0 |
| `ModalDesactivarCuenta` | P0 |
| `useCuentasBancarias` | P0 |
| `useBancos` | P0 |

**Resultado**: Usuario puede crear, editar y desactivar cuentas.

### Fase 2: BLOQUE B — Captura de saldos

| Componente | Prioridad |
|------------|-----------|
| `DetalleCuentaBancaria` | P0 |
| `FormularioCapturaSaldo` | P0 |
| `FormularioCorreccionSaldo` | P0 |
| `ModalCancelarSaldo` | P0 |
| `HistorialSaldos` | P0 |
| `TarjetaSaldoTotal` | P1 |
| `useSaldosBancarios` | P0 |

**Resultado**: Usuario puede capturar, corregir, cancelar saldos y ver total.

---

## CONFIRMACIONES EXPLÍCITAS

| Confirmación | Estado |
|--------------|--------|
| No se implementa todavía | ✅ |
| No se modifica frontend todavía | ✅ |
| No se crean tabs todavía | ✅ |
| No se tocan menús globales | ✅ |
| No se tocan filtros globales | ✅ |
| No se toca CxP | ✅ |
| No se toca Cuadre de Cortes Z | ✅ |
| No se toca Comercial V2 | ✅ |
| No se toca Compras | ✅ |
| No se toca Tablero Ejecutivo | ✅ |
| No se toca Propinas TPV | ✅ |
| No se toca Auth/RBAC | ✅ |
| No se usan datos demo | ✅ |
| No se expone cuenta/CLABE completas | ✅ |
| No se mezcla con efectivo pendiente | ✅ |
| No se crea dashboard consolidado | ✅ |

---

## AUTORIZACIÓN SOLICITADA

### Para BLOQUE A (Catálogo de cuentas):

1. ✅ Crear `CuentasBancariasPage.jsx`
2. ✅ Crear `TablaCuentasBancarias.jsx`
3. ✅ Crear `FormularioCuentaBancaria.jsx`
4. ✅ Crear `ModalDesactivarCuenta.jsx`
5. ✅ Crear hooks `useCuentasBancarias.js` y `useBancos.js`
6. ✅ Agregar ruta `/finanzas/cuentas-bancarias`
7. ✅ Agregar entrada en menú Finanzas

### Para BLOQUE B (Saldos - posterior):

8. ❓ Crear componentes de saldos
9. ❓ Crear `TarjetaSaldoTotal.jsx`

---

**ESTADO**: ⏳ **PROPUESTA FRONTEND P1-FASE5A.1 - PENDIENTE AUTORIZACIÓN**

*Documento: P1-FASE5A-1-FRONTEND-CUENTAS-SALDOS-BANCARIOS.md*  
*Fecha: 2025-12-06 v1.0*
