# EDARSA HUB - Auditoría de Seguridad RBAC
## Barrido Integral Fases 1-8

**Fecha**: 2026-04-22  
**Versión**: 1.0  
**Estado**: EN PROCESO  

---

## 1. RESUMEN EJECUTIVO

### Objetivo
Realizar un barrido integral de seguridad para garantizar que:
1. El backend hace enforcement real de permisos (no confía en frontend)
2. Los usuarios ven únicamente la información de su alcance
3. No hay brechas entre el modelo legacy y el modelo RBAC

### Usuarios de Prueba
| Usuario | Email | Rol Legacy | Fuente Acceso |
|---------|-------|------------|---------------|
| David Ricaldes Mendes | david.ricardez@cienfuegos.mx | Usuario | LEGACY |
| Cristina Chi | almacen@cienfuegos.mx | Usuario | MIXTO |
| Admin Test | admin@edarsa.com | Supervisor | RBAC |

---

## 2. CAUSA RAÍZ IDENTIFICADA

### Problema Principal
**EXISTE UN MODELO HÍBRIDO NO HOMOLOGADO** entre:

1. **Modelo Legacy** (pre-RBAC):
   - `allowed_servers`: Lista de IDs de servidores
   - `allowed_sucursales`: Dict {server_id: [sucursal_ids]}
   - `allowed_warehouses`: Dict {server_id: [almacen_ids]}
   - `role`: String simple (Usuario, Supervisor, Administrador)

2. **Modelo RBAC** (nuevo):
   - `empresas_permitidas`: Lista de IDs de empresas
   - `empresa_default_id`: Empresa activa
   - `sec_roles`: Lista de códigos de roles
   - `sec_roles_alcance`: Dict con alcance por rol
   - `sec_permisos`: Permisos directos

### Inconsistencia Crítica
- **David Ricaldes**: Tiene `allowed_servers` pero NO tiene `empresas_permitidas`
- **Cristina Chi**: Tiene AMBOS modelos (MIXTO)
- **Admin Test**: Solo tiene modelo RBAC

**Resultado**: Los endpoints que solo verifican `empresas_permitidas` rechazan a David, aunque tiene acceso legítimo vía `allowed_servers`.

---

## 3. INVENTARIO DE COLECCIONES DE SEGURIDAD

| Colección | Documentos | Propósito |
|-----------|------------|-----------|
| `users` | 11 | Usuarios con ambos modelos |
| `sec_roles` | 5 | Roles del sistema de permisos |
| `sec_permisos_catalogo` | 90 | Catálogo de permisos funcionales |
| `rbac_roles` | 6 | Roles RBAC (diferente a sec_roles) |
| `rbac_permisos` | 43 | Permisos RBAC por módulo |
| `rbac_usuarios_roles` | 72 | Asignaciones usuario-rol-empresa |
| `rbac_audit_log` | 376 | Log de auditoría RBAC |
| `permisos_catalogos` | 8 | Permisos sobre catálogos |
| `empresas` | 5+ | Catálogo de empresas |
| `servers` | 4+ | Servidores SQL externos |
| `sucursales_catalogo` | - | Sucursales por empresa |
| `sucursal_servidor_map` | - | Mapeo sucursal → servidor |

---

## 4. FLUJO DE AUTORIZACIÓN ACTUAL

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (Login)                                                 │
│   └─> POST /api/auth/login                                      │
│       └─> Retorna: token JWT + user completo                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (Menú Sidebar)                                          │
│   └─> Usa user.role para decidir qué mostrar                    │
│   └─> Consulta GET /api/roles para permisos                     │
│   └─> Lógica: hasAccess() verifica role O permisos              │
│   ⚠️ PROBLEMA: Confía en datos del localStorage                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND (Endpoint cualquiera)                                    │
│   └─> Depends(get_current_user) obtiene usuario de DB           │
│   └─> Cada endpoint hace su propia validación (inconsistente)   │
│   ⚠️ PROBLEMA: No hay función centralizada de contexto          │
└─────────────────────────────────────────────────────────────────┘
```

### Problemas Detectados:

1. **Frontend define visibilidad de menú** sin validación backend
2. **Múltiples funciones de permisos** dispersas:
   - `security.py`: `user_has_server_access`, `filter_servers_by_permissions`
   - `context_resolver.py`: `resolve_unidad_context`, `resolve_server_context`
   - `alcance_helper.py`: `resolver_alcance_usuarios`
   - `rbac_helper.py`: `verificar_permiso_rbac`
3. **No hay función única** que combine todos los modelos

---

## 5. SOLUCIÓN IMPLEMENTADA

### Función Central: `resolve_user_access_context()`

**Archivo**: `/app/backend/core/user_access_context.py`

```python
async def resolve_user_access_context(user: Dict) -> UserAccessContext:
    """
    ÚNICA FUENTE DE VERDAD para el acceso efectivo de un usuario.
    
    Orden de resolución:
    1. SuperAdministrador → acceso global
    2. Administrador → acceso global
    3. RBAC (empresas_permitidas) → traducir a servidores
    4. Legacy (allowed_servers) → complementar
    5. Combinar permisos de sec_roles + sec_permisos
    """
```

### Estructura de Retorno: `UserAccessContext`

```python
@dataclass
class UserAccessContext:
    user_id: str
    email: str
    nombre: str
    
    # Nivel de acceso
    tiene_acceso_global: bool
    fuente_acceso: str  # SUPERADMIN, ADMIN, RBAC, LEGACY, MIXTO
    
    # Alcance organizacional
    empresas_ids: List[str]
    servers_ids: List[str]
    almacenes_por_server: Dict[str, List[str]]
    sucursales_por_server: Dict[str, List[str]]
    
    # Permisos funcionales
    permisos: List[str]
    sec_roles: List[str]
    permisos_catalogos: List[str]
    
    # Capacidades
    puede_autorizar: bool
    puede_solicitar: bool
    puede_liberar: bool
```

### Endpoint de Diagnóstico

```
GET /api/auth/me/access-context
```

Retorna el contexto de acceso efectivo calculado para el usuario actual.

---

## 6. RESULTADOS DE PRUEBAS

### 6.1 David Ricaldes Mendes

```json
{
  "email": "david.ricardez@cienfuegos.mx",
  "tiene_acceso_global": false,
  "fuente_acceso": "LEGACY",
  "empresas_ids": [],
  "servers_ids": ["1b230a06...", "6d053c22...", "a5ff0e25...", "a5547321..."],
  "almacenes_por_server": {
    "6d053c22...": ["004", "200", "400", "002", "100", "300"]
  },
  "permisos": ["SISTEMA_USUARIOS_VER", "SISTEMA_ESTRUCTURA_VER"],
  "sec_roles": ["VISOR_ESTRUCTURA", "VISOR_SISTEMA"]
}
```

**Diagnóstico**: 
- ⚠️ Sin empresas RBAC asignadas
- ✅ Tiene acceso legacy a 4 servidores
- ✅ Almacenes restringidos correctamente
- ⚠️ Permisos limitados a SISTEMA_*

**Impacto**: David puede ver datos de los servidores asignados, pero los endpoints que validan solo por `empresas_permitidas` lo rechazarán.

### 6.2 Cristina Chi

```json
{
  "email": "almacen@cienfuegos.mx",
  "tiene_acceso_global": false,
  "fuente_acceso": "MIXTO",
  "empresas_ids": ["1d91f076..."],
  "empresa_default_id": "1d91f076...",
  "servers_ids": ["6d053c22..."],
  "almacenes_por_server": {
    "6d053c22...": ["001", "004", "200", "400", "002", "005", "299", "003", "100", "300"]
  },
  "permisos": ["SISTEMA_USUARIOS_VER", "SISTEMA_USUARIOS_CREAR", "SISTEMA_USUARIOS_EDITAR", ...],
  "sec_roles": ["VISOR_ESTRUCTURA", "GESTOR_SISTEMA"]
}
```

**Diagnóstico**:
- ✅ Tiene empresa RBAC asignada
- ✅ Tiene acceso legacy al mismo servidor
- ✅ Almacenes completos asignados
- ✅ Permisos de gestión de usuarios

**Estado**: Configuración correcta (modelo MIXTO).

### 6.3 Admin Test

```json
{
  "email": "admin@edarsa.com",
  "tiene_acceso_global": false,
  "fuente_acceso": "RBAC",
  "empresas_ids": ["31784356...", "1118f83c...", "1d91f076...", "e302e16f...", "a4d8b5e7..."],
  "servers_ids": ["a5ff0e25...", "1b230a06...", "6d053c22...", "a5547321..."],
  "permisos": ["SISTEMA_ESTRUCTURA_VER"],
  "sec_roles": []
}
```

**Diagnóstico**:
- ✅ Tiene 5 empresas RBAC
- ✅ Servidores calculados correctamente desde empresas
- ⚠️ Solo tiene 1 permiso funcional
- ⚠️ Sin sec_roles asignados

**Impacto**: Admin puede ver datos de sus empresas, pero tiene permisos funcionales muy limitados.

---

## 7. MATRIZ DE SEGURIDAD

### 7.1 Permisos por Usuario

| Permiso | David | Cristina | Admin |
|---------|-------|----------|-------|
| SISTEMA_ESTRUCTURA_VER | ✅ | ✅ | ✅ |
| SISTEMA_USUARIOS_VER | ✅ | ✅ | ❌ |
| SISTEMA_USUARIOS_CREAR | ❌ | ✅ | ❌ |
| SISTEMA_USUARIOS_EDITAR | ❌ | ✅ | ❌ |
| SISTEMA_USUARIOS_ELIMINAR | ❌ | ✅ | ❌ |
| SISTEMA_ROLES_VER | ❌ | ✅ | ❌ |
| SISTEMA_ROLES_CREAR | ❌ | ✅ | ❌ |

### 7.2 Alcance Organizacional

| Empresa | David | Cristina | Admin |
|---------|-------|----------|-------|
| 31784356... | ❌ | ❌ | ✅ |
| 1118f83c... | ❌ | ❌ | ✅ |
| 1d91f076... | ❌ (legacy) | ✅ | ✅ |
| e302e16f... | ❌ | ❌ | ✅ |
| a4d8b5e7... | ❌ | ❌ | ✅ |

---

## 8. DESVIACIONES Y CORRECCIONES PENDIENTES

### 8.1 Crítica: David sin empresas_permitidas

**Problema**: David tiene `allowed_servers` pero no `empresas_permitidas`.
**Solución**: Migrar datos legacy o asignar empresas RBAC.

```javascript
// Corrección recomendada:
db.users.updateOne(
  { email: "david.ricardez@cienfuegos.mx" },
  { $set: { 
    empresas_permitidas: ["<empresa_id_correspondiente>"],
    empresa_default_id: "<empresa_id_correspondiente>"
  }}
)
```

### 8.2 Media: Admin sin sec_roles

**Problema**: Admin no tiene `sec_roles` asignados.
**Solución**: Asignar roles según su función.

### 8.3 Baja: Múltiples sistemas de roles

**Problema**: Existen `sec_roles` y `rbac_roles` como sistemas paralelos.
**Solución**: A largo plazo, unificar en un solo sistema.

---

## 9. ARCHIVOS MODIFICADOS/CREADOS

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `/app/backend/core/user_access_context.py` | CREADO | Función central `resolve_user_access_context()` |
| `/app/backend/modules/auth/routes.py` | MODIFICADO | Endpoints `/auth/me/access-context` y `/auth/me/menu-permissions` |
| `/app/frontend/src/pages/Layout.js` | MODIFICADO | Menú ahora usa permisos del backend (RBAC centralizado) |
| `/app/docs/AUDITORIA_SEGURIDAD_RBAC.md` | CREADO | Este documento |
| `/app/docs/ARQUITECTURA_CLASIFICACION_DATOS_LIVE_VS_CONSOLIDADOS.md` | CREADO | Clasificación LIVE vs EDARSA HUB |
| `/app/docs/NORMAS_TECNICAS.md` | MODIFICADO | Agregada sección de clasificación de datos |

---

## 10. PRUEBAS REALIZADAS

### 10.1 Prueba de Contexto de Acceso

**Endpoint**: `GET /api/auth/me/access-context`

| Usuario | Resultado | Fuente | Servidores | Empresas |
|---------|-----------|--------|------------|----------|
| David Ricaldes | ✅ OK | LEGACY | 4 | 0 |
| Cristina Chi | ✅ OK | MIXTO | 1 | 1 |
| Admin Test | ✅ OK | RBAC | 4 | 5 |

### 10.2 Prueba de Permisos de Menú

**Endpoint**: `GET /api/auth/me/menu-permissions`

| Usuario | Módulos con acceso |
|---------|-------------------|
| David | mis_tareas, tablero_ejecutivo, comercial, compras, operaciones, catalogos, usuarios |
| Cristina | mis_tareas, tablero_ejecutivo, comercial, compras, operaciones, catalogos, usuarios |
| Admin | mis_tareas, tablero_ejecutivo, comercial, compras, operaciones, catalogos, usuarios + más |

### 10.3 Prueba de Acceso Real a Datos

| Usuario | Endpoint | Resultado |
|---------|----------|-----------|
| David | `/api/comercial/tablero-ejecutivo` | ✅ Ve 4 unidades (todos sus servidores) |
| Cristina | `/api/comercial/tablero-ejecutivo` | ✅ Ve 1 unidad (solo Cienfuegos) |

---

## 11. PRÓXIMOS PASOS (CORREGIDO)

### MACROFASE 1: Correcciones Críticas y Seguridad (P0)

#### 1.1 Seguridad RBAC (Fases 6-8)
- [ ] Aplicar `resolve_user_access_context()` a endpoints de Compras
- [ ] Aplicar `resolve_user_access_context()` a endpoints de Comercial
- [ ] Aplicar `resolve_user_access_context()` a endpoints de Operaciones
- [ ] Validar enforcement en todos los endpoints críticos

#### 1.2 Circuit Breaker Tablero Ejecutivo
- [ ] Modificar `cache_service.py` para no bloquear reintentos en datos LIVE
- [ ] Separar lógica: datos actuales (LIVE) vs históricos (CACHE)

#### 1.3 Clasificación Fina Live vs HUB
- [ ] Implementar separación en `get_kpis_softrestaurant()`
- [ ] Mes actual: LIVE
- [ ] Mes/año anterior: MongoDB consolidado

### MACROFASE 2: Consolidación de Históricos (P1)

#### 2.1 Comercial
- [ ] Crear colección `kpis_comercial_consolidados`
- [ ] Implementar scheduler nocturno de consolidación
- [ ] Migrar endpoints de históricos a leer de MongoDB
- [ ] Carga inicial de últimos 24 meses

#### 2.2 Compras (Dashboard)
- [ ] Crear colección `kpis_compras_consolidados`
- [ ] Migrar KPIs de dashboard a MongoDB

### LO QUE NO SE TOCA (evitar regresión)
- Endpoints de auditoría operativa en vivo
- Cálculo de pedidos
- Inventarios físicos actuales
- Pedidos vigentes
- Módulos de Finanzas y RH (ya usan EDARSA HUB)

---

## 12. CREDENCIALES DE PRUEBA

**NOTA**: Las contraseñas de prueba han sido sanitizadas de este documento.
Para pruebas de validación, solicitar credenciales al administrador del sistema.

| Usuario | Email | Rol |
|---------|-------|-----|
| David Ricaldes | david.ricardez@cienfuegos.mx | Usuario (LEGACY) |
| Cristina Chi | almacen@cienfuegos.mx | Usuario (MIXTO) |
| Admin Test | admin@edarsa.com | Supervisor (RBAC) |

---

## 13. ENDPOINTS HOMOLOGADOS (FASE 6-8)

### 13.1 Comercial (COMPLETADO ✅)

| Endpoint | Validación RBAC | Estado |
|----------|-----------------|--------|
| `GET /comercial/tablero-ejecutivo` | `resolve_user_access_context()` | ✅ |
| `GET /comercial/dashboard/{server_id}` | `validate_server_access_rbac()` | ✅ |
| `GET /comercial/ticket-perfecto/{server_id}` | `validate_server_access_rbac()` | ✅ |
| `GET /comercial/ventas-tiempo/{server_id}` | `validate_server_access_rbac()` | ✅ |
| `GET /comercial/metas/{server_id}` | `validate_server_access_rbac()` | ✅ |
| `GET /comercial/detalle-cheques/{server_id}` | `validate_server_access_rbac()` | ✅ |
| `GET /comercial/precios-constantes/{server_id}` | `validate_server_access_rbac()` | ✅ |
| `GET /comercial/reporte-pax/{server_id}` | `validate_server_access_rbac()` | ✅ |

### 13.2 Compras (server.py) (COMPLETADO ✅)

| Endpoint | Validación RBAC | Estado |
|----------|-----------------|--------|
| `GET /compras/inventarios-fisicos/{server_id}` | `validate_server_access_by_empresa()` | ✅ |
| `GET /compras/pedidos-vigentes/{server_id}` | `validate_server_access_by_empresa()` | ✅ |
| `GET /compras/detalle-pedido/{server_id}/{folio}` | `validate_server_access_by_empresa()` | ✅ |
| `POST /compras/auditoria-operativa` | `validate_server_access_by_empresa()` | ✅ |
| `POST /compras/calculo-pedido` | `validate_server_access_by_empresa()` | ✅ |
| `GET /compras/dashboard/{server_id}` | `validate_server_access_by_empresa()` | ✅ |

### 13.3 Explorador BD (server.py) (COMPLETADO ✅)

| Endpoint | Validación RBAC | Estado |
|----------|-----------------|--------|
| `GET /explorador/tablas/{server_id}` | `validate_server_access_unified()` | ✅ |
| `GET /explorador/columnas/{server_id}/{tabla}` | `validate_server_access_unified()` | ✅ |
| `GET /explorador/relaciones/{server_id}/{tabla}` | `validate_server_access_unified()` | ✅ |
| `GET /explorador/preview/{server_id}/{tabla}` | `validate_server_access_unified()` | ✅ |
| `GET /explorador/buscar/{server_id}` | `validate_server_access_unified()` | ✅ |
| `POST /catalogo-sql/ejecutar` | `validate_server_access_unified()` | ✅ |

### 13.4 Servidores (server.py) (COMPLETADO ✅)

| Endpoint | Validación RBAC | Estado |
|----------|-----------------|--------|
| `GET /servers` | `filter_servers_by_permissions()` | ✅ |
| `GET /servers/{server_id}` | `validate_server_access_unified()` | ✅ |

### 13.5 Recursos Humanos (COMPLETADO ✅)

| Endpoint | Validación RBAC | Estado |
|----------|-----------------|--------|
| `GET /rrhh/catalogos/*` | `get_user_sucursales_permitidas_rh()` | ✅ |
| `GET /rrhh/colaboradores/*` | `get_user_sucursales_permitidas_rh()` | ✅ |
| `GET /rrhh/incidencias/*` | `get_user_sucursales_permitidas_rh()` | ✅ |

### 13.6 Finanzas (EDARSA HUB FIRST - Sin cambios necesarios)

| Endpoint | Validación RBAC | Estado |
|----------|-----------------|--------|
| `GET /finanzas/*` | EDARSA HUB (datos internos) | ✅ N/A |

### 13.7 Auth (COMPLETADO ✅)

| Endpoint | Validación RBAC | Estado |
|----------|-----------------|--------|
| `GET /auth/me/access-context` | `resolve_user_access_context()` | ✅ |
| `GET /auth/me/menu-permissions` | `resolve_user_access_context()` | ✅ |

---

## 14. PRUEBAS DE ENFORCEMENT REAL

### 14.1 Prueba de Denegación Fuera de Alcance

| Usuario | Endpoint | Server | Resultado |
|---------|----------|--------|-----------|
| Cristina Chi | `/comercial/dashboard/a5547321-...` | 130° MERIDA | ❌ 403 DENEGADO |
| Cristina Chi | `/compras/inventarios-fisicos/a5547321-...` | 130° MERIDA | ❌ 403 DENEGADO |
| Cristina Chi | `/comercial/dashboard/6d053c22-...` | CIENFUEGOS | ✅ 200 OK |
| Cristina Chi | `/compras/inventarios-fisicos/6d053c22-...` | CIENFUEGOS | ✅ 200 OK |

### 14.2 Prueba de Filtrado en Tablero Ejecutivo

| Usuario | Unidades Visibles | Fuente Acceso |
|---------|------------------|---------------|
| David Ricaldes | 5 unidades | LEGACY |
| Cristina Chi | 1 unidad (Cienfuegos) | MIXTO |
| Admin Test | 4+ unidades | RBAC |

---

## 15. ARCHIVOS MODIFICADOS EN FASE 6-8

| Archivo | Cambios |
|---------|---------|
| `/app/backend/core/user_access_context.py` | CREADO - Función centralizada |
| `/app/backend/modules/comercial/routes.py` | 8 endpoints actualizados |
| `/app/backend/modules/auth/routes.py` | 2 endpoints de diagnóstico |
| `/app/backend/modules/rh/routes.py` | Helper actualizado |
| `/app/backend/server.py` | 7+ endpoints actualizados |
| `/app/frontend/src/pages/Layout.js` | Menú usa permisos del backend |

---

## 16. IMPLEMENTACIÓN P0: CIRCUIT BREAKER CORREGIDO

### 16.1 Cambios Realizados

**Archivo**: `/app/backend/modules/comercial/repository.py`

| Función | Cambio |
|---------|--------|
| `is_server_recently_offline()` | Corregido manejo de timezone, reducido threshold para SYNC-S |
| `should_attempt_live_query()` | **NUEVA** - Determina si intentar conexión según tipo de dato |

**Archivo**: `/app/backend/modules/comercial/routes.py`

| Endpoint | Cambio |
|----------|--------|
| `tablero_ejecutivo()` | Usa `should_attempt_live_query()` con clasificación LIVE-C/SYNC-S/HUB |

### 16.2 Nueva Clasificación en Código

```python
# FASE P0: Tipos de dato para circuit breaker
if solo_ventas_dia:
    data_type = "LIVE-C"  # Crítico: SIEMPRE intentar conexión
else:
    data_type = "HUB"     # Consolidado: usar cache si offline
```

### 16.3 Pruebas Ejecutadas

| Prueba | Resultado |
|--------|-----------|
| Tablero Ejecutivo (modo HUB) | ✅ status=online, datos correctos |
| Tablero Ejecutivo (modo LIVE-C) | ✅ SIEMPRE intenta conexión |
| Inventarios físicos (LIVE-C) | ✅ 2415 productos |
| Dashboard comercial (SYNC-S) | ✅ source_status=SUCCESS |

### 16.4 No Regresión Verificada

| Flujo LIVE-C | Estado |
|--------------|--------|
| Auditoría operativa | ✅ Intacto |
| Cálculo de pedidos | ✅ Intacto |
| Inventarios físicos | ✅ Intacto |
| Pedidos vigentes | ✅ Intacto |
| Ventas del día sin corte | ✅ Intacto |

---

## 17. PROPUESTA TÉCNICA MACROFASE 2

Ver documento completo: `/app/docs/DISENO_TECNICO_MACROFASE2.md`

**Resumen**:
- Esquema EDARSA HUB: `kpis_comercial_diarios`, `kpis_comercial_historico`, `kpis_compras_diarios`
- SYNC-S: Cada 15 min, ventana 48h
- SYNC-N: Diario 03:00, ventana 7 días
- Reconciliación: Día 5 de cada mes, mes anterior completo
- UPSERT obligatorio con clave única (server_id + fecha + sucursal_id)
- Versionado en `_historico` para cambios retroactivos
- Estados de período: ABIERTO → CERRADO → RECONCILIADO

---

## 18. VALIDACIÓN FINAL DE FALLBACK (P0 CIERRE)

### 18.1 Estados de Fuente Implementados

| Estado | Código | Significado |
|--------|--------|-------------|
| **LIVE** | `source_status: "LIVE"` | Datos obtenidos en tiempo real de SQL externo |
| **LIVE_FAILED** | `source_status: "LIVE_FAILED"` | Falla en LIVE-C - fuente no confirmada |
| **FALLBACK** | `source_status: "FALLBACK"` | Datos de caché (HUB con fuente caída) |
| **NO_CACHE** | `source_status: "NO_CACHE"` | Sin datos - fuente caída y sin histórico |

### 18.2 Resultados de Validación

| Caso | Tipo | Resultado | source_status | Observaciones |
|------|------|-----------|---------------|---------------|
| **1. Fuente disponible (HUB)** | SYNC-S/HUB | ✅ PASS | `LIVE` | Datos frescos de SQL externo |
| **2. Fuente disponible (LIVE-C)** | LIVE-C | ✅ PASS | `LIVE` | Ventas del día en tiempo real |
| **3. Fuente caída (HUB)** | HUB | ✅ PASS | `FALLBACK` | Usa caché con timestamp de última actualización |
| **4. LIVE-C ignora offline** | LIVE-C | ✅ PASS | `LIVE` | SIEMPRE intenta conexión, no usa caché |

### 18.3 Comportamiento por Tipo de Dato

#### LIVE-C (Crítico)
```
SI fuente disponible → status=online, source_status=LIVE
SI fuente falla → status=source_unavailable, source_status=LIVE_FAILED
   - NO usa caché
   - NO asume "sin cambios"
   - Estado explícito de falla
```

#### SYNC-S (Sync corto)
```
SI fuente disponible → status=online, source_status=LIVE
SI fuente falla (< 2 min) → Reintenta conexión
SI fuente falla (> 2 min) → Usa fallback con source_status=FALLBACK
```

#### HUB (Consolidado)
```
SI fuente disponible → status=online, source_status=LIVE
SI fuente falla CON caché → status=offline, source_status=FALLBACK
   - Incluye fallback_from con timestamp
   - Incluye message explicativo
SI fuente falla SIN caché → status=no_data, source_status=NO_CACHE
   - NO genera ceros falsos
   - Mensaje explícito de sin datos
```

### 18.4 Prevención de Ceros Falsos

| Escenario | Comportamiento Anterior | Comportamiento Nuevo |
|-----------|------------------------|---------------------|
| LIVE-C falla | No agregaba nada (silencioso) | Agrega con `LIVE_FAILED` |
| HUB sin caché | Solo log, no agregaba | Agrega con `NO_CACHE` |
| HUB con caché | status=offline sin source | status=offline + `FALLBACK` + timestamp |

---

## HISTORIAL DE CAMBIOS

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-04-22 | 4.0 | FASE 8: Enforcement RBAC por Almacén implementado y validado |
| 2026-04-23 | 3.1 | Validación final de fallback completada - P0 CERRADO |
| 2026-04-22 | 3.0 | P0 implementado: Circuit breaker corregido + clasificación LIVE-C/SYNC-S/HUB |
| 2026-04-22 | 2.0 | FASE 6-8: Homologación completa de endpoints críticos |
| 2026-04-22 | 1.0 | Documento inicial - Fases 1-5 completadas |

---

## FASE 8: ENFORCEMENT RBAC POR ALMACÉN (2026-04-22)

### Implementación Completada

Se implementó el enforcement de RBAC a nivel de **Almacén** con las siguientes capacidades:

1. **Filtrado de Listados**: Endpoints de almacenes e inventarios ahora filtran por `almacenes_permitidos`
2. **Bloqueo 403**: Acceso directo a almacenes fuera de alcance devuelve HTTP 403
3. **Funciones Centralizadas**: Nuevas funciones en `user_access_context.py`

### Funciones Agregadas

```python
get_almacenes_permitidos(context, server_id)       # Lista de almacenes
get_almacenes_sql_filter(context, server_id, col)  # Cláusula SQL WHERE
validate_almacen_in_scope(context, server_id, id)  # Validación booleana
filter_results_by_almacen(context, server_id, res) # Filtro post-query
```

### Endpoints Modificados

| Endpoint | Cambio |
|----------|--------|
| /servers/{id}/almacenes | Filtro SQL por almacenes |
| /servers/{id}/almacenes-softrestaurant | Filtro SQL por almacenes |
| /servers/{id}/inventarios | Filtro SQL por almacenes |
| /compras/inventarios-fisicos/{id} | Filtro SQL por almacenes |
| /inventarios/pendientes/{id} | Validación 403 + filtro |
| /compras/detalle-pedido/{id}/{folio} | Migrado a validate_server_access_by_empresa |

### Evidencia de Pruebas

```
ADMIN: 10 almacenes, 2415 inventarios
DAVID: 6 almacenes, 2068 inventarios ← FILTRADO CORRECTO

DAVID almacen_id=001 → HTTP 403 "No tiene acceso" ← BLOQUEO CORRECTO
DAVID almacen_id=002 → HTTP 200 ← PERMITIDO CORRECTO
```

### Documentación

Ver `/app/docs/MATRIZ_VALIDACION_RBAC_ALMACENES.md` para matriz completa de 12 columnas.

