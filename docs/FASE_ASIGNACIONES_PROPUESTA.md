# FASE ASIGNACIONES - PROPUESTA FORMAL (v2)

## Parametrización de Responsables para Workflows de Inventarios

**Fecha**: Abril 2026  
**Versión**: 2.0 (Ajustada al modelo funcional)  
**Estado**: PROPUESTA PENDIENTE DE APROBACIÓN  
**Autor**: Sistema  
**Solicitante**: Usuario (Operativo EDARSA)

---

## CAMBIO PRINCIPAL vs v1

| Aspecto | v1 (Rechazada) | v2 (Esta propuesta) |
|---------|----------------|---------------------|
| **Modelo visible** | Server + Sucursal + Almacén | **Unidad de Negocio + Almacén** |
| **UI muestra** | Campos técnicos | **Solo conceptos de negocio** |
| **Resolución técnica** | Expuesta | **Interna/oculta** |

**Principio rector**: El usuario opera con el lenguaje del negocio (Unidad de Negocio), el sistema resuelve internamente los identificadores técnicos.

---

## 1. CONTEXTO Y PROBLEMA

### 1.1 Situación Actual

El job `inventarios_detector_job.py` detecta inventarios automáticamente y crea workflows. Sin embargo:

- La colección `config_asignaciones` está **completamente vacía**
- No existe **UI** para administrar las asignaciones
- El `OrquestadorService` usa fallback a `"SISTEMA_AUTOMATICO"` cuando no encuentra responsable
- Los workflows quedan sin dueño real

### 1.2 Objetivo

Crear una interfaz donde el usuario pueda definir:

```
UNIDAD DE NEGOCIO + ALMACÉN → USUARIO RESPONSABLE
```

Sin exponer conceptos técnicos como `server_id` o `sucursal_id`.

---

## 2. MODELO FUNCIONAL VISIBLE

### 2.1 Concepto de Negocio

El usuario trabaja con **Unidades de Negocio** (ej: "LA ESTELAR", "CIENFUEGOS", "130° QUERÉTARO").

Cada Unidad de Negocio puede tener uno o más **Almacenes** (ej: "General", "Bebidas", "Cocina").

La configuración define: **¿Quién es responsable de justificar diferencias de inventario en cada combinación?**

### 2.2 Matriz de Asignación (Vista Usuario)

| Unidad de Negocio | Almacén | Responsable | Estado |
|-------------------|---------|-------------|--------|
| LA ESTELAR | General | Juan Pérez | Activa |
| LA ESTELAR | Bebidas | María López | Activa |
| LA ESTELAR | *(todos)* | Carlos García | Activa |
| CIENFUEGOS | *(todos)* | Ana Martínez | Activa |
| 130° QUERÉTARO | Almacén Principal | Pedro Ruiz | Inactiva |

### 2.3 Reglas de Prioridad (Expresadas funcionalmente)

Cuando se detecta un inventario en **LA ESTELAR / Almacén Bebidas**:

1. **Buscar configuración específica**: LA ESTELAR + Bebidas → María López ✅
2. Si no existe, **buscar configuración general**: LA ESTELAR + (todos) → Carlos García
3. Si no existe ninguna → **NO crear workflow, alertar en Centro de Control**

**En palabras simples**: La configuración más específica gana. Si no hay ninguna, el sistema alerta.

---

## 3. MODELO DE DATOS (Interno)

### 3.1 Colección: `config_asignaciones`

```javascript
{
  // Identificador único
  "id": "uuid-v4",
  
  // === CLAVE FUNCIONAL (lo que el usuario ve/configura) ===
  "unidad_negocio_id": "emp-uuid-...",      // ID de la empresa/unidad
  "unidad_negocio_nombre": "LA ESTELAR",    // Nombre visible
  "almacen_id": "ALM_001",                  // ID del almacén ("" = todos)
  "almacen_nombre": "General",              // Nombre visible ("" = todos los almacenes)
  
  // === RESOLUCIÓN TÉCNICA (interno, NO expuesto en UI) ===
  "server_id": "a5ff0e25-...",              // Resuelto automáticamente
  "sucursal_id": "SUC_ESTELAR",             // Resuelto automáticamente
  
  // === ASIGNACIÓN ===
  "usuario_responsable_id": "user-uuid-...",
  "usuario_responsable_nombre": "Juan Pérez",
  "usuario_responsable_email": "juan.perez@edarsa.com.mx",
  
  // === CONTROL ===
  "activa": true,
  "prioridad": 20,                          // Calculada automáticamente
  
  // === AUDITORÍA ===
  "fecha_creacion": "2026-04-22T10:00:00Z",
  "usuario_creacion": "admin@edarsa.com.mx",
  "fecha_modificacion": "2026-04-22T10:00:00Z",
  "usuario_modificacion": "admin@edarsa.com.mx"
}
```

### 3.2 Campos Visibles vs Internos

| Campo | Visible en UI | Editable | Descripción |
|-------|---------------|----------|-------------|
| `unidad_negocio_id` | ✅ Sí | ✅ Al crear | Selector de Unidad de Negocio |
| `unidad_negocio_nombre` | ✅ Sí | ❌ Auto | Nombre para mostrar |
| `almacen_id` | ✅ Sí | ✅ Al crear | Selector de Almacén |
| `almacen_nombre` | ✅ Sí | ❌ Auto | Nombre para mostrar |
| `usuario_responsable_id` | ✅ Sí | ✅ Siempre | Selector de Usuario |
| `activa` | ✅ Sí | ✅ Siempre | Toggle activo/inactivo |
| `server_id` | ❌ No | ❌ Auto | Resuelto internamente |
| `sucursal_id` | ❌ No | ❌ Auto | Resuelto internamente |
| `prioridad` | ❌ No | ❌ Auto | Calculada automáticamente |

### 3.3 Índice Único

```javascript
// Índice único por clave funcional
{
  "unidad_negocio_id": 1,
  "almacen_id": 1
}
```

### 3.4 Cálculo de Prioridad

| Configuración | Prioridad | Descripción |
|---------------|-----------|-------------|
| Unidad + Almacén específico | 20 | Más específica |
| Unidad + Todos los almacenes | 10 | General |

```python
def calcular_prioridad(almacen_id: str) -> int:
    return 20 if almacen_id else 10
```

---

## 4. RESOLUCIÓN INTERNA (Mapeo Técnico)

### 4.1 Mapeo: Unidad de Negocio → Identificadores Técnicos

El sistema ya tiene el mapeo en la colección `empresas`:

```javascript
// Colección: empresas
{
  "id": "emp-uuid-...",
  "nombre": "LA ESTELAR",
  "server_id": "a5ff0e25-...",           // ← Se extrae de aquí
  "sucursal_origen_id": "SUC_ESTELAR",   // ← Se extrae de aquí
  "activa": true
}
```

### 4.2 Proceso de Creación de Configuración

Cuando el usuario crea una asignación:

```
1. Usuario selecciona: "LA ESTELAR" (unidad_negocio_id = "emp-uuid-...")

2. Backend consulta empresas:
   empresa = db.empresas.find_one({"id": "emp-uuid-..."})

3. Backend extrae identificadores técnicos:
   server_id = empresa["server_id"]           // "a5ff0e25-..."
   sucursal_id = empresa["sucursal_origen_id"] // "SUC_ESTELAR"

4. Backend guarda config_asignaciones con TODOS los campos:
   {
     "unidad_negocio_id": "emp-uuid-...",     // Funcional
     "unidad_negocio_nombre": "LA ESTELAR",  // Funcional
     "almacen_id": "ALM_001",                // Funcional
     "server_id": "a5ff0e25-...",            // Técnico (interno)
     "sucursal_id": "SUC_ESTELAR",           // Técnico (interno)
     ...
   }
```

### 4.3 Proceso de Resolución (Cuando se detecta inventario)

Cuando el job detecta un inventario:

```
1. Job detecta inventario con: server_id="a5ff0e25-...", almacen_id="ALM_001"

2. Orquestador busca en config_asignaciones por campos TÉCNICOS:
   config = db.config_asignaciones.find_one({
     "server_id": "a5ff0e25-...",
     "almacen_id": "ALM_001",
     "activa": true
   })

3. Si encuentra → asigna a config.usuario_responsable_id
   Si NO encuentra → busca config general (almacen_id = "")
   Si NO existe ninguna → NO crear workflow, crear alerta
```

### 4.4 Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                        CREACIÓN (UI)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Usuario selecciona:                                            │
│  [Unidad de Negocio: LA ESTELAR ▼]                             │
│  [Almacén: General ▼]                                          │
│  [Responsable: Juan Pérez ▼]                                   │
│                                                                 │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                   │
│  │ Backend resuelve internamente:          │                   │
│  │ • unidad_negocio_id → server_id         │                   │
│  │ • unidad_negocio_id → sucursal_id       │                   │
│  └─────────────────────────────────────────┘                   │
│         │                                                       │
│         ▼                                                       │
│  Guarda en config_asignaciones con campos funcionales + técnicos│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    RESOLUCIÓN (Job Automático)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Job detecta inventario:                                        │
│  server_id="a5ff0e25-...", almacen_id="ALM_001"                │
│                                                                 │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                   │
│  │ Orquestador busca por campos TÉCNICOS:  │                   │
│  │ • server_id + almacen_id (específico)   │                   │
│  │ • server_id + "" (general)              │                   │
│  └─────────────────────────────────────────┘                   │
│         │                                                       │
│         ▼                                                       │
│  ¿Encontró config?                                              │
│  • SÍ → Asignar workflow a usuario_responsable_id              │
│  • NO → Crear alerta en Centro de Control                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. CARGA DE ALMACENES

### 5.1 Dependencia de Unidad de Negocio

Los almacenes se cargan **dinámicamente** según la Unidad de Negocio seleccionada.

### 5.2 Fuente de Almacenes

**Opción implementada**: Consulta al servidor SQL de la Unidad de Negocio.

```python
async def get_almacenes_por_unidad(unidad_negocio_id: str) -> List[Dict]:
    """
    Obtiene los almacenes disponibles para una Unidad de Negocio.
    
    1. Buscar la empresa/unidad
    2. Obtener su server_id
    3. Consultar almacenes en el servidor SQL correspondiente
    """
    # Obtener datos de la unidad
    empresa = await db.empresas.find_one({"id": unidad_negocio_id})
    if not empresa:
        return []
    
    server = await db.servers.find_one({"id": empresa["server_id"]})
    if not server:
        return []
    
    # Query según tipo de sistema
    if server["system_type"] == "SoftRestaurant":
        query = "SELECT idalmacen AS id, nombre FROM almacen WHERE activo = 1"
    elif server["system_type"] == "MPRO":
        query = "SELECT id_almacen AS id, nombre FROM almacenes WHERE activo = 1"
    
    # Ejecutar query
    almacenes = execute_sql_query(server, query)
    
    return [{"id": str(a["id"]), "nombre": a["nombre"]} for a in almacenes]
```

### 5.3 Opción "Todos los almacenes"

En el selector siempre aparece como primera opción:
- **"(Todos los almacenes)"** → Se guarda con `almacen_id = ""`

---

## 6. REGLAS DE NEGOCIO

### 6.1 Validaciones al Crear

| Validación | Error si falla |
|------------|----------------|
| Unidad de Negocio debe existir | "Unidad de negocio no encontrada" |
| Usuario debe existir y estar activo | "Usuario no válido o inactivo" |
| No debe existir config duplicada | "Ya existe configuración para esta combinación" |

### 6.2 Validaciones al Editar

| Campo | Editable |
|-------|----------|
| Unidad de Negocio | ❌ No (crear nueva si cambia) |
| Almacén | ❌ No (crear nueva si cambia) |
| Usuario Responsable | ✅ Sí |
| Estado Activo | ✅ Sí |

### 6.3 Eliminación

- Eliminación **física** (no soft delete)
- Workflows existentes **NO se afectan**
- Nuevos inventarios de esa combinación **quedarán sin responsable** (se alertará)

### 6.4 Un Usuario en Múltiples Combinaciones

**Permitido**: Un mismo usuario puede ser responsable de múltiples combinaciones.

```
Ejemplo válido:
• LA ESTELAR / General → Juan Pérez
• LA ESTELAR / Bebidas → Juan Pérez
• CIENFUEGOS / (todos) → Juan Pérez
```

---

## 7. FALTA DE CONFIGURACIÓN

### 7.1 Comportamiento

Cuando se detecta un inventario y **NO existe configuración**:

1. **NO se crea workflow** (el inventario queda sin procesar)
2. **Se registra en bitácora** (`inventarios_sin_asignar`)
3. **Se crea ALERTA en Centro de Control** (severidad: warning)

### 7.2 Registro en Bitácora

```javascript
// Colección: inventarios_sin_asignar
{
  "id": "uuid",
  "unidad_negocio_id": "emp-uuid-...",
  "unidad_negocio_nombre": "LA ESTELAR",
  "almacen_id": "ALM_NUEVO",
  "almacen_nombre": "Almacén Nuevo",
  "folio_inventario": "176",
  "fecha_inventario": "2026-04-22",
  "total_diferencias": 45,
  "valor_diferencias": 12500.00,
  "fecha_deteccion": "2026-04-22T10:30:00Z",
  "estado": "PENDIENTE_CONFIGURACION",
  "alerta_id": "alerta-uuid-..."  // Referencia a la alerta creada
}
```

### 7.3 Alerta en Centro de Control

```javascript
// Se crea automáticamente en alertas_sistema
{
  "id": "alerta-uuid-...",
  "tipo": "INVENTARIO_SIN_RESPONSABLE",
  "severidad": "warning",
  "titulo": "Inventario sin responsable configurado",
  "mensaje": "Se detectó inventario en LA ESTELAR / Almacén Nuevo pero no hay responsable configurado. El workflow no se creó.",
  "modulo": "inventarios",
  "fecha_creacion": "2026-04-22T10:30:00Z",
  "datos": {
    "unidad_negocio": "LA ESTELAR",
    "almacen": "Almacén Nuevo",
    "folio": "176",
    "valor_diferencias": 12500.00
  },
  "accion_sugerida": "Configurar responsable en Configuración → Asignaciones de Inventarios",
  "acknowledged": false
}
```

---

## 8. ENDPOINTS CRUD

### 8.1 Base URL

```
/api/config-asignaciones
```

### 8.2 Endpoints

#### GET /api/config-asignaciones
**Descripción**: Listar configuraciones  
**Query params**:
- `unidad_negocio_id` (opcional): Filtrar por unidad
- `activa` (opcional): true/false
- `skip`, `limit`: Paginación

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-1",
      "unidad_negocio_id": "emp-uuid-...",
      "unidad_negocio_nombre": "LA ESTELAR",
      "almacen_id": "ALM_001",
      "almacen_nombre": "General",
      "usuario_responsable_id": "user-uuid",
      "usuario_responsable_nombre": "Juan Pérez",
      "usuario_responsable_email": "juan@edarsa.com.mx",
      "activa": true,
      "fecha_creacion": "2026-04-22T10:00:00Z"
    }
  ],
  "total": 15
}
```

**Nota**: Los campos `server_id` y `sucursal_id` **NO se incluyen** en la respuesta.

#### GET /api/config-asignaciones/unidades-negocio
**Descripción**: Listar unidades de negocio disponibles para configurar  
**Response**:
```json
{
  "success": true,
  "data": [
    {"id": "emp-1", "nombre": "LA ESTELAR"},
    {"id": "emp-2", "nombre": "CIENFUEGOS"},
    {"id": "emp-3", "nombre": "130° QUERÉTARO"}
  ]
}
```

#### GET /api/config-asignaciones/almacenes/{unidad_negocio_id}
**Descripción**: Listar almacenes de una unidad de negocio  
**Response**:
```json
{
  "success": true,
  "data": [
    {"id": "", "nombre": "(Todos los almacenes)"},
    {"id": "ALM_001", "nombre": "General"},
    {"id": "ALM_002", "nombre": "Bebidas"},
    {"id": "ALM_003", "nombre": "Cocina"}
  ]
}
```

#### POST /api/config-asignaciones
**Descripción**: Crear nueva configuración  
**Body**:
```json
{
  "unidad_negocio_id": "emp-uuid-...",
  "almacen_id": "ALM_001",
  "usuario_responsable_id": "user-uuid"
}
```

**Proceso interno**:
1. Validar que unidad_negocio_id existe
2. Obtener server_id y sucursal_id de la empresa
3. Validar que no existe duplicado
4. Guardar con todos los campos (funcionales + técnicos)

**Response (201)**:
```json
{
  "success": true,
  "data": { ...config_creada_sin_campos_tecnicos },
  "message": "Configuración creada exitosamente"
}
```

#### PUT /api/config-asignaciones/{id}
**Descripción**: Actualizar configuración  
**Body**:
```json
{
  "usuario_responsable_id": "nuevo-user-uuid",
  "activa": true
}
```

**Campos editables**:
- `usuario_responsable_id`
- `activa`

#### DELETE /api/config-asignaciones/{id}
**Descripción**: Eliminar configuración  
**Response (200)**:
```json
{
  "success": true,
  "message": "Configuración eliminada"
}
```

---

## 9. UI - DISEÑO

### 9.1 Ubicación

**Ruta**: `/configuracion/asignaciones-inventarios`  
**Menú**: Configuración → Asignaciones de Inventarios  
**Acceso**: Usuarios con permiso `CONFIG_ASIGNACIONES_*`

### 9.2 Pantalla Principal

```
┌─────────────────────────────────────────────────────────────────┐
│  ASIGNACIONES DE INVENTARIOS                                    │
│  Define quién es responsable de justificar diferencias          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [+ Nueva Asignación]                    🔍 Buscar...           │
│                                                                 │
│  Filtros: [Unidad de Negocio ▼] [Estado ▼]                     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ UNIDAD DE NEGOCIO │ ALMACÉN         │ RESPONSABLE       │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ LA ESTELAR        │ General         │ Juan Pérez        │   │
│  │                   │                 │ [●] Activa        │   │
│  │                   │                 │ [Editar] [🗑️]     │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ LA ESTELAR        │ Bebidas         │ María López       │   │
│  │                   │                 │ [●] Activa        │   │
│  │                   │                 │ [Editar] [🗑️]     │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ LA ESTELAR        │ (todos)         │ Carlos García     │   │
│  │                   │                 │ [●] Activa        │   │
│  │                   │                 │ [Editar] [🗑️]     │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ CIENFUEGOS        │ (todos)         │ Ana Martínez      │   │
│  │                   │                 │ [●] Activa        │   │
│  │                   │                 │ [Editar] [🗑️]     │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ 130° QUERÉTARO    │ Almacén Princ.  │ Pedro Ruiz        │   │
│  │                   │                 │ [○] Inactiva      │   │
│  │                   │                 │ [Editar] [🗑️]     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Mostrando 5 de 12 │ [< Anterior] [Siguiente >]                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.3 Modal: Nueva Asignación

```
┌─────────────────────────────────────────┐
│  Nueva Asignación                    [X]│
├─────────────────────────────────────────┤
│                                         │
│  Unidad de Negocio *                    │
│  [▼ Seleccionar unidad de negocio  ]    │
│                                         │
│  Almacén                                │
│  [▼ (Todos los almacenes)          ]    │
│  ℹ️ Se carga según la unidad             │
│                                         │
│  Usuario Responsable *                  │
│  [▼ Seleccionar usuario            ]    │
│  🔍 Buscar por nombre o email           │
│                                         │
│  ─────────────────────────────────────  │
│  ⚠️ Esta configuración determina quién  │
│  recibirá los workflows de inventario   │
│  para justificar las diferencias.       │
│  ─────────────────────────────────────  │
│                                         │
│  [Cancelar]              [Guardar]      │
│                                         │
└─────────────────────────────────────────┘
```

### 9.4 Modal: Editar Asignación

```
┌─────────────────────────────────────────┐
│  Editar Asignación                   [X]│
├─────────────────────────────────────────┤
│                                         │
│  Unidad de Negocio                      │
│  ┌─────────────────────────────────┐    │
│  │ LA ESTELAR                      │    │
│  └─────────────────────────────────┘    │
│  🔒 No editable                         │
│                                         │
│  Almacén                                │
│  ┌─────────────────────────────────┐    │
│  │ General                         │    │
│  └─────────────────────────────────┘    │
│  🔒 No editable                         │
│                                         │
│  Usuario Responsable *                  │
│  [▼ Juan Pérez                     ]    │
│                                         │
│  Estado                                 │
│  [●] Activa   [○] Inactiva              │
│                                         │
│  [Cancelar]              [Guardar]      │
│                                         │
└─────────────────────────────────────────┘
```

### 9.5 Confirmación de Eliminación

```
┌─────────────────────────────────────────┐
│  ⚠️ Confirmar Eliminación            [X]│
├─────────────────────────────────────────┤
│                                         │
│  ¿Eliminar esta asignación?             │
│                                         │
│  • LA ESTELAR / General → Juan Pérez    │
│                                         │
│  Los inventarios futuros de esta        │
│  combinación no tendrán responsable     │
│  asignado automáticamente.              │
│                                         │
│  [Cancelar]         [Sí, eliminar]      │
│                                         │
└─────────────────────────────────────────┘
```

---

## 10. SEGURIDAD

### 10.1 Permisos

| Acción | Permiso |
|--------|---------|
| Ver configuraciones | `CONFIG_ASIGNACIONES_READ` |
| Crear/Editar | `CONFIG_ASIGNACIONES_WRITE` |
| Eliminar | `CONFIG_ASIGNACIONES_DELETE` |

### 10.2 Roles con Acceso

| Rol | READ | WRITE | DELETE |
|-----|------|-------|--------|
| SuperAdministrador | ✅ | ✅ | ✅ |
| Administrador | ✅ | ✅ | ❌ |
| Gerente Operativo | ✅ | ❌ | ❌ |

### 10.3 Auditoría

Todas las operaciones se registran:
- `CONFIG_ASIGNACION_CREAR`
- `CONFIG_ASIGNACION_EDITAR`
- `CONFIG_ASIGNACION_ELIMINAR`

---

## 11. ROLLBACK

### 11.1 Desactivar Funcionalidad

Variable de entorno: `ASIGNACIONES_ENABLED=false`

**Comportamiento con flag desactivado**:
- UI oculta del menú
- Endpoints retornan 503
- Orquestador usa fallback legacy (usuario_ejecutor_id)

### 11.2 Preservar Datos

- Workflows existentes **NO se modifican**
- La colección `config_asignaciones` se preserva
- Solo afecta la creación de nuevos workflows

---

## 12. RESUMEN DE CAMBIOS vs v1

| Aspecto | v1 | v2 |
|---------|----|----|
| Selector principal | Server | Unidad de Negocio |
| Selector secundario | Sucursal | (eliminado) |
| Selector terciario | Almacén | Almacén |
| Campos en UI | server_id, sucursal_id | NINGUNO técnico |
| Almacenes se cargan | Manual/estático | Dinámico según unidad |
| Falta de config | Solo bitácora | Bitácora + Alerta Centro Control |
| Usuario múltiple | No definido | SÍ permitido |

---

## 13. CRITERIOS DE ACEPTACIÓN

### Backend
- [ ] Endpoint lista configuraciones SIN campos técnicos
- [ ] Endpoint carga almacenes dinámicamente por unidad
- [ ] Al crear, resuelve server_id/sucursal_id internamente
- [ ] Índice único por unidad_negocio_id + almacen_id

### Integración
- [ ] Orquestador busca por campos técnicos internamente
- [ ] Si no hay config → Crear alerta en Centro de Control
- [ ] Variable ASIGNACIONES_ENABLED permite rollback

### Frontend
- [ ] Selector de Unidad de Negocio (NO servidor)
- [ ] Selector de Almacén dependiente de la unidad
- [ ] NO muestra server_id ni sucursal_id en ningún lugar
- [ ] Campos no editables se muestran como solo lectura

---

## 14. APROBACIÓN

**Estado**: ✅ APROBADA E IMPLEMENTADA

**Fecha de aprobación**: Abril 2026
**Ajustes solicitados**: 
- Modelo visible cambiado de Server → Unidad de Negocio
- Almacenes desde catálogo local, NO consulta SQL en tiempo real
- Alerta en Centro de Control cuando falta configuración

## 15. NOTAS DE IMPLEMENTACIÓN

### Backend
- **Repositorio**: `/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py`
- **Routes**: `/app/backend/modules/configuracion/routes/config_asignaciones_routes.py`
- **Colección MongoDB**: `config_asignaciones` (índice único: unidad_negocio_id + almacen_id)
- **Colección auxiliar**: `almacenes_catalogo` (catálogo local de almacenes)

### Orquestador Modificado
- **Archivo**: `/app/backend/modules/fase2_operativo/services/orquestador_service.py`
- **Método**: `_obtener_usuario_responsable()` ahora usa `config_asignaciones`
- **Comportamiento**: Si no hay config → NO crea workflow, registra en `inventarios_sin_asignar` y crea alerta

### Frontend
- **Página**: `/app/frontend/src/pages/ConfigAsignaciones.jsx`
- **Ruta**: `/configuracion/asignaciones`
- **Menú**: Sistema → Asignaciones

### Endpoints
- `GET /api/config-asignaciones` - Listar
- `GET /api/config-asignaciones/unidades-negocio` - Catálogo unidades
- `GET /api/config-asignaciones/almacenes/{unidad_id}` - Catálogo almacenes (local)
- `POST /api/config-asignaciones` - Crear
- `PUT /api/config-asignaciones/{id}` - Actualizar
- `DELETE /api/config-asignaciones/{id}` - Eliminar

---

**FIN DEL DOCUMENTO - VERSIÓN 2.0 IMPLEMENTADA**
