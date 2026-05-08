# DIAGNÓSTICO INTEGRAL RBAC Y MODELO UNIDAD DE NEGOCIO
## EDARSA HUB - Arquitectura de Contexto por Usuario

**Fecha**: 2026-04-20
**Versión**: 1.0
**Autor**: Arquitecto de Software Senior

---

## 1. DIAGNÓSTICO DE RBAC Y CONTEXTO

### 1.1 MODELO ACTUAL

```
USUARIO
├── empresas_permitidas: [lista de IDs de empresas]
├── role: "Administrador" | "Usuario" | etc.
├── allowed_servers: [lista legacy - deprecada]
└── allowed_sucursales: {server_id: [sucursales]} (legacy - deprecada)

EMPRESA
├── id: UUID
├── codigo: "ORIGEN", "130QRO", etc.
├── nombre: "ORIGEN", "130 QRO", etc.
├── server_id: null (⚠️ NO POBLADO)
└── sucursal_origen_id: null (⚠️ NO POBLADO)

SERVER
├── id: UUID
├── name: "ManagmentPro", "CIENFUEGOS", etc.
├── system_type: "MPRO" | "SoftRestaurant"
└── empresa_id: null (⚠️ NO POBLADO)

SUCURSAL_CATALOGO
├── id: UUID
├── empresa_id: UUID (relaciona con empresa)
├── codigo: código interno
└── nombre: nombre visible

SUCURSAL_SERVIDOR_MAP
├── sucursal_id: UUID
├── server_id: UUID
└── sucursal_origen_id: ID en sistema externo
```

### 1.2 FLUJO ACTUAL DE RESOLUCIÓN

```
1. Usuario se autentica → Token contiene user_id
2. Backend obtiene empresas_permitidas del usuario
3. Endpoint /api/unidades-negocio:
   - Consulta empresas con id in empresas_permitidas
   - Consulta sucursales_catalogo por empresa_id
   - Consulta sucursal_servidor_map para obtener server_id
   - Retorna lista con: id, nombre, server_id, system_type, sucursales
```

### 1.3 PROBLEMAS DETECTADOS

#### A. FRONTEND HEREDADO NO MIGRADO

| Pantalla | Estado | Problema |
|----------|--------|----------|
| **AutorizacionCompras.js** | ❌ NO MIGRADO | Usa `selectedServer` + `selectedSucursal` como selectores visibles |
| **Dashboard.js** | ❌ NO MIGRADO | Muestra "Selecciona un Servidor" con nombres técnicos |
| **Finanzas.js** | ⚠️ PARCIAL | Usa `allowed_sucursales` legacy y muestra selector de sucursal |
| **Reportes.js** | ⚠️ PARCIAL | Internamente migrado pero sigue usando `server_id` en filtros |
| **Comercial.js** | ✅ MIGRADO | Usa Unidad de Negocio pero aún pasa `selectedServer` internamente |
| **Compras.js** | ✅ MIGRADO | Usa Unidad de Negocio correctamente |

#### B. SELECTOR DE SUCURSAL VISIBLE DONDE NO DEBE

| Componente | Ubicación | Estado |
|------------|-----------|--------|
| DashboardVentas | Comercial.js:357-375 | ⚠️ Muestra "Sucursal" si showSucursalSelector |
| TicketPerfecto | Comercial.js:818-832 | ⚠️ Muestra "Sucursal" |
| MetasVentas | Comercial.js:985-999 | ⚠️ Muestra "Sucursal" |
| VentasPorTiempo | Comercial.js:1109-1123 | ⚠️ Muestra "Sucursal" |
| MesasComensales | Comercial.js:1233-1247 | ⚠️ Muestra "Sucursal" |
| AutorizacionCompras | AutorizacionCompras.js:466-492 | ❌ Muestra "Servidor" + "Sucursal" |

#### C. BACKEND TODAVÍA DEPENDE DE server_id/sucursal_id

Los endpoints aún esperan `server_id` como parámetro de URL:
- `/api/comercial/dashboard/{server_id}`
- `/api/comercial/ticket-perfecto/{server_id}`
- `/api/comercial/metas/{server_id}`
- `/api/compras/dashboard/{server_id}`
- `/api/compras/pedidos-vigentes/{server_id}`
- `/api/dashboard/inventory-summary?server_id={server_id}`

#### D. MODELO LEGACY EN FINANZAS

`Finanzas.js` líneas 270-310 usa:
```javascript
if (currentUser.allowed_sucursales) {
  Object.values(currentUser.allowed_sucursales).forEach(...)
}
```
Esto es el modelo legacy que debe ser reemplazado por `empresas_permitidas`.

### 1.4 CAUSA RAÍZ

1. **Migración incompleta**: Se creó el endpoint `/api/unidades-negocio` y el servicio `unidadesNegocioService.js`, pero no todas las pantallas fueron migradas.

2. **Doble modelo coexistente**: El usuario tiene tanto `empresas_permitidas` (nuevo) como `allowed_servers`/`allowed_sucursales` (legacy).

3. **Frontend controla seguridad**: Los selectores de servidor/sucursal en UI permiten elegir opciones que luego se envían al backend sin validación RBAC consistente.

4. **No hay resolución centralizada**: Cada pantalla resuelve el contexto de forma diferente.

---

## 2. DISEÑO CORRECTIVO PROPUESTO

### 2.1 MODELO CORRECTO

```
USUARIO
└── empresas_permitidas: [UUIDs]
    │
    ├── EMPRESA "130 QRO"
    │   └── SUCURSAL_CATALOGO "0025"
    │       └── SUCURSAL_SERVIDOR_MAP
    │           ├── server_id → ManagmentPro
    │           └── sucursal_origen_id → "0025"
    │
    └── EMPRESA "CIENFUEGOS"
        └── SUCURSAL_CATALOGO "CIENFUEGOS"
            └── SUCURSAL_SERVIDOR_MAP
                ├── server_id → CIENFUEGOS SR
                └── sucursal_origen_id → null (SR usa default)
```

### 2.2 FLUJO CORRECTO

```
┌────────────────────────────────────────────────────────────────┐
│ FRONTEND                                                        │
├────────────────────────────────────────────────────────────────┤
│ 1. Usuario selecciona UNIDAD DE NEGOCIO (visible)              │
│ 2. Frontend obtiene: unidad.id, unidad.server_id (interno)     │
│ 3. Llama a endpoint con unidad_negocio_id                      │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ BACKEND                                                         │
├────────────────────────────────────────────────────────────────┤
│ 1. Recibe unidad_negocio_id (o server_id para compatibilidad)  │
│ 2. Valida que usuario tenga acceso a esa unidad (RBAC)         │
│ 3. Resuelve internamente:                                       │
│    - server_id                                                  │
│    - sucursal_origen_id (para MPRO)                            │
│    - system_type (MPRO/SoftRestaurant)                         │
│ 4. Ejecuta query con contexto correcto                         │
│ 5. Retorna datos filtrados por RBAC                            │
└────────────────────────────────────────────────────────────────┘
```

### 2.3 REGLAS DE SEGURIDAD

1. **Backend valida SIEMPRE**: Todo endpoint debe verificar que el usuario tiene acceso a la unidad/servidor solicitado.

2. **Frontend NO decide seguridad**: El frontend solo muestra opciones autorizadas y envía la selección.

3. **Selector de Sucursal**:
   - NO mostrar si la unidad tiene 1 sola sucursal
   - NO mostrar si la unidad tiene `sucursal_origen_id` definida
   - Solo mostrar si hay múltiples sucursales Y es requerido funcionalmente

4. **Selector de Servidor**: NUNCA en pantallas funcionales de negocio.

---

## 3. MATRIZ DE RELACIÓN

| Usuario | Rol | Empresa | Unidad de Negocio | Sucursal | Servidor | Sistema |
|---------|-----|---------|-------------------|----------|----------|---------|
| admin@edarsa.com | Administrador | 31784356... | ORIGEN | ORIGEN | 1b230a06... (MPRO) | MPRO |
| admin@edarsa.com | Administrador | 1118f83c... | 130 QRO | 0025 | 1b230a06... (MPRO) | MPRO |
| admin@edarsa.com | Administrador | 1d91f076... | CIENFUEGOS | CIENFUEGOS | 6d053c22... | SoftRestaurant |
| admin@edarsa.com | Administrador | 7a62a4b9... | LA ESTELAR | LA ESTELAR | 57c1a273... | SoftRestaurant |
| admin@edarsa.com | Administrador | a4d8b5e7... | 130 MID | 130° MERIDA | a5547321... | SoftRestaurant |

---

## 4. CORRECCIÓN DE FRONTEND

### 4.1 PANTALLAS A CORREGIR

#### AutorizacionCompras.js (PRIORIDAD ALTA)
- **Línea 43**: `selectedServer` → `selectedUnidad`
- **Línea 47**: `selectedSucursal` → Eliminar o derivar de unidad
- **Línea 466-478**: Selector "Servidor" → Selector "Unidad de Negocio"
- **Línea 479-492**: Selector "Sucursal" → Condicional o eliminar

#### Dashboard.js (PRIORIDAD ALTA)
- **Línea 220-236**: Texto "Selecciona un Servidor" → "Selecciona una Unidad de Negocio"
- **Línea 230-232**: Opciones `server.name (server.system_type)` → `unidad.nombre`
- **Línea 318-330**: Selector de servidor → Selector de unidad

#### Finanzas.js (PRIORIDAD MEDIA)
- **Línea 270-306**: Lógica de `allowed_sucursales` → `empresas_permitidas`
- **Líneas de selector de sucursal**: Evaluar si aplica o eliminar

#### Reportes.js (PRIORIDAD MEDIA)
- Internamente usa server_id pero la UI ya tiene filtros RBAC
- Revisar exposición de `server_id` en filtros

### 4.2 COMPONENTES COMPARTIDOS A CREAR

```javascript
// /app/frontend/src/components/UnidadNegocioSelector.jsx
// Selector reutilizable de Unidad de Negocio con RBAC
```

### 4.3 LABELS Y PLACEHOLDERS A CORREGIR

| Actual | Correcto |
|--------|----------|
| "Servidor" | "Unidad de Negocio" |
| "Selecciona un Servidor" | "Selecciona una Unidad de Negocio" |
| "server.name (server.system_type)" | "unidad.nombre" |
| "ManagmentPro (MPRO)" | "ORIGEN" o nombre de unidad |
| "Sucursal" (en vista funcional) | Eliminar o auto-resolver |
| "Todas las sucursales" | Eliminar |

---

## 5. CORRECCIÓN DE BACKEND

### 5.1 HELPER CENTRALIZADO DE CONTEXTO

Crear `/app/backend/core/context_resolver.py`:

```python
async def resolve_unidad_context(user: Dict, unidad_id: str) -> Dict:
    """
    Resuelve el contexto completo de una unidad de negocio.
    
    Returns:
        {
            "unidad_id": str,
            "empresa_id": str,
            "server_id": str,
            "system_type": str,
            "sucursal_origen_id": str | None,
            "sucursales": List[Dict]
        }
    
    Raises:
        HTTPException 403 si usuario no tiene acceso
    """
```

### 5.2 ENDPOINTS A AJUSTAR

| Endpoint | Cambio |
|----------|--------|
| `/api/comercial/dashboard/{server_id}` | Agregar validación RBAC (ya hecho) |
| `/api/compras/dashboard/{server_id}` | Agregar validación RBAC |
| `/api/dashboard/inventory-summary` | Usar context_resolver |
| `/api/servers/{server_id}/almacenes` | Validar acceso por empresa |

### 5.3 VALIDACIÓN RBAC EN ENDPOINTS

Todo endpoint que reciba `server_id` debe:
1. Obtener `empresas_permitidas` del usuario
2. Verificar que el servidor pertenece a una empresa permitida
3. Rechazar con 403 si no tiene acceso

---

## 6. LISTA DE ARCHIVOS A MODIFICAR

### Frontend
- `/app/frontend/src/pages/AutorizacionCompras.js` (refactorizar completo)
- `/app/frontend/src/pages/Dashboard.js` (migrar a unidades)
- `/app/frontend/src/pages/Finanzas.js` (eliminar lógica legacy)
- `/app/frontend/src/pages/Comercial.js` (ya parcialmente migrado, limpiar)
- `/app/frontend/src/components/` (crear componente reutilizable)

### Backend
- `/app/backend/core/context_resolver.py` (crear nuevo)
- `/app/backend/modules/compras/routes.py` (agregar validación)
- `/app/backend/server.py` (endpoints de dashboard/inventarios)

---

## 7. PLAN DE IMPLEMENTACIÓN POR FASES

### FASE 1: BACKEND - Context Resolver (1-2 horas)
**Objetivo**: Crear capa centralizada de resolución de contexto

**Alcance**:
- Crear `/app/backend/core/context_resolver.py`
- Función `resolve_unidad_context(user, unidad_id)`
- Función `validate_server_access_rbac(user, server_id)`

**Riesgos**: Bajo (nuevo código, no modifica existente)

**Criterio de aceptación**:
- Context resolver puede obtener server_id, sucursal, system_type de una unidad
- Validación RBAC funciona correctamente

---

### FASE 2: MIGRACIÓN AutorizacionCompras.js (2-3 horas)
**Objetivo**: Migrar pantalla de Autorización de Compras al modelo de Unidad de Negocio

**Alcance**:
- Reemplazar selector de Servidor por Unidad de Negocio
- Eliminar selector de Sucursal visible
- Mantener lógica de almacenes e inventarios

**Riesgos**: Medio (pantalla crítica de operaciones)

**Criterio de aceptación**:
- Usuario ve "Unidad de Negocio" no "Servidor"
- No ve selector de "Sucursal"
- Cálculo de pedidos funciona igual

---

### FASE 3: MIGRACIÓN Dashboard.js (1-2 horas)
**Objetivo**: Migrar Dashboard de Operaciones al modelo de Unidad de Negocio

**Alcance**:
- Reemplazar "Selecciona un Servidor" por "Selecciona una Unidad de Negocio"
- Usar servicio unidadesNegocioService

**Riesgos**: Bajo

**Criterio de aceptación**:
- Usuario ve nombres de unidades de negocio, no servidores
- Métricas cargan correctamente

---

### FASE 4: LIMPIEZA Finanzas.js (1-2 horas)
**Objetivo**: Eliminar lógica legacy de allowed_sucursales

**Alcance**:
- Reemplazar lógica de allowed_sucursales por empresas_permitidas
- Evaluar si selector de sucursal aplica o eliminar

**Riesgos**: Medio (módulo de finanzas crítico)

**Criterio de aceptación**:
- No usa allowed_sucursales
- Datos se filtran correctamente por RBAC

---

### FASE 5: PRUEBAS Y NO REGRESIÓN (2-3 horas)
**Objetivo**: Validar que todo funciona sin regresiones

**Alcance**:
- Probar todas las pantallas migradas
- Probar con usuarios de diferentes permisos
- Validar que no hay fuga de datos

---

## 8. PLAN DE NO REGRESIÓN

### Tests Obligatorios

| Escenario | Esperado |
|-----------|----------|
| Usuario con 1 unidad de negocio | No ve selector, unidad auto-seleccionada |
| Usuario con múltiples unidades | Ve selector de unidad, no de servidor |
| Unidad con 1 sucursal | No ve selector de sucursal |
| Unidad MPRO con sucursal_origen_id | Sucursal auto-resuelta |
| Unidad SoftRestaurant | Sucursal = 'default' auto-resuelta |
| Intento de acceso a servidor no autorizado | Backend rechaza con 403 |
| Exportaciones | Datos correctos, sin fuga |

### Pantallas a Validar

- [ ] Compras > Dashboard
- [ ] Compras > Autorización
- [ ] Compras > Análisis
- [ ] Operaciones > Dashboard
- [ ] Comercial > Todos los tabs
- [ ] Finanzas > Todos los tabs
- [ ] Reportes > Todos los filtros

---

## 9. CRITERIO DE ACEPTACIÓN FINAL

✅ El frontend funcional usa "Unidad de Negocio" como filtro principal
✅ El backend resuelve sucursal/servidor/origen internamente
✅ Los filtros respetan RBAC real
✅ No se exponen detalles técnicos al usuario final
✅ No aparecen "Servidor" ni "Sucursal" donde ya no deben
✅ No hay regresión transversal
✅ No se rompió seguridad
✅ No se rompieron dashboards ni reportes

---

## 10. RECOMENDACIONES INMEDIATAS

### PRIORIDAD ALTA (Implementar ahora)
1. **AutorizacionCompras.js**: Es el caso más crítico - muestra "Servidor" visible
2. **Dashboard.js**: Visible a todos los usuarios, muestra "Selecciona un Servidor"

### PRIORIDAD MEDIA (Implementar después)
3. **Finanzas.js**: Limpiar lógica legacy de allowed_sucursales
4. **Comercial.js**: Limpieza menor - ya usa Unidad de Negocio

### PUEDE ESPERAR
5. **Reportes.js**: Funciona internamente bien, mejoras menores

---

**Siguiente paso recomendado**: Solicitar aprobación del usuario para proceder con FASE 1 y FASE 2.
