# PROPUESTA MIGRACIÓN AUTH/RBAC Y SERVIDORES A EDARSAHUB

**Documento:** FASE 0 - Paridad, Riesgo y Plan de Migración Controlada  
**Fecha:** 8 de Mayo 2026  
**Estado:** SOLO PROPUESTA - NO AUTORIZADA IMPLEMENTACIÓN  
**Autor:** Arquitectura de Sistemas

---

## 1. RESUMEN EJECUTIVO

Este documento presenta el análisis de paridad completo entre MongoDB y EDARSAHUB para los módulos de Auth/RBAC y Servidores, junto con una propuesta de migración segura en fases que NO ha sido autorizada para ejecución.

### Hallazgos Principales

| Categoría | MongoDB | EDARSAHUB | Paridad |
|-----------|---------|-----------|---------|
| **Usuarios** | 15 documentos | 0 registros | ⚠️ EDARSAHUB vacío |
| **Roles (legacy)** | 4 documentos | 5 registros | ✅ Similar |
| **RBAC Roles** | 6 documentos | N/A directo | ⚠️ Requiere mapeo |
| **RBAC Permisos** | 43 documentos | 0 registros | ⚠️ EDARSAHUB vacío |
| **RBAC Asignaciones** | 72 documentos | 0 registros | ⚠️ EDARSAHUB vacío |
| **Servidores** | 13 documentos | 17 registros | ✅ 13/13 coinciden |
| **Unidades Negocio** | 7 documentos | 5 registros | ⚠️ Diferencia de IDs |

### Conclusión de Paridad

- **Auth/RBAC:** Las tablas EDARSAHUB existen con estructura completa pero están VACÍAS. El sistema actual depende 100% de MongoDB para usuarios, permisos y sesiones.
  
- **Servidores:** Hay paridad completa de IDs (13/13 servidores MongoDB existen en EDARSAHUB). EDARSAHUB tiene 4 servidores adicionales que no están en MongoDB.

---

## 2. ESTADO ACTUAL

### 2.1 Login Actual (CRÍTICO)
```
Flujo actual:
1. Frontend → POST /api/auth/login (email, password)
2. Backend → db.users.find_one({"email": ...}) ← MongoDB
3. Backend → verify_password() 
4. Backend → create_access_token() (JWT)
5. Respuesta con token + user data
```

**Dependencia:** 100% MongoDB para autenticación.

### 2.2 RBAC Actual (CRÍTICO)
```
Flujo actual:
1. Request con Bearer token
2. get_current_user() → db.users.find_one() ← MongoDB
3. resolve_user_access_context() → lee user.empresas_permitidas ← MongoDB
4. Validación de permisos contra user.sec_permisos ← MongoDB
```

**Dependencia:** 100% MongoDB para autorización.

### 2.3 Servidores Actual (HÍBRIDO)
```
Flujo actual:
1. server_registry.py intenta leer EDARSAHUB primero
2. Si falla → fallback a db.servers ← MongoDB
3. Módulos Comercial/Compras/Finanzas leen server_registry
```

**Dependencia:** EDARSAHUB primario con fallback MongoDB.

---

## 3. PARIDAD MONGODB vs EDARSAHUB — AUTH/RBAC

### 3.1 Estructura de Usuarios

| Campo MongoDB (users) | Campo EDARSAHUB (Usuario_Catalogo) | Paridad |
|-----------------------|-----------------------------------|---------|
| `id` (UUID string) | `UsuarioID` (int) | ⚠️ TIPO DIFERENTE |
| `email` | `Email` (varchar 150) | ✅ |
| `password` (bcrypt hash) | `PasswordHashTexto` (varchar 255) | ✅ Compatible |
| `name` / `nombre` | `Nombre` + `Apellidos` → `NombreCompleto` | ✅ |
| `role` (string) | N/A directo - via RolesAsignacion | ⚠️ REQUIERE JOIN |
| `activo` / `active` | `Activo` (bit) | ✅ |
| `empresas_permitidas` (array) | N/A | ❌ NO EXISTE |
| `sucursales` (array) | N/A | ❌ NO EXISTE |
| `sec_permisos` (array) | N/A - via PermisosRolModulo | ⚠️ REQUIERE JOIN |
| `sec_rol` | N/A - via RolesAsignacion | ⚠️ REQUIERE JOIN |
| `permisos_catalogos` (array) | N/A | ❌ NO EXISTE |
| `puede_autorizar` | N/A | ❌ NO EXISTE |
| `puede_liberar` | N/A | ❌ NO EXISTE |
| `puede_solicitar` | N/A | ❌ NO EXISTE |
| `empresa_default_id` | N/A | ❌ NO EXISTE |
| `contexto_updated_at` | N/A | ❌ NO EXISTE |

### 3.2 Campos Faltantes en EDARSAHUB (Usuario_Catalogo)

| Campo MongoDB | Propósito | Riesgo si no se migra |
|---------------|-----------|----------------------|
| `empresas_permitidas` | Filtro RBAC por empresa | **P0_CRÍTICO** - Sin esto, usuarios no pueden filtrar por empresa |
| `sucursales` | Filtro RBAC por sucursal | **P1_ALTO** - Filtros de sucursal fallarían |
| `sec_permisos` | Permisos directos del usuario | **P0_CRÍTICO** - Autorización rota |
| `sec_rol` | Rol RBAC asignado | **P0_CRÍTICO** - Nivel de acceso indefinido |
| `permisos_catalogos` | Catálogos permitidos | **P2_MEDIO** |
| `puede_autorizar/liberar/solicitar` | Flags de workflow | **P2_MEDIO** |
| `empresa_default_id` | Empresa por defecto | **P2_MEDIO** |

### 3.3 Campos que EDARSAHUB tiene y MongoDB NO

| Campo EDARSAHUB | Propósito | Valor |
|-----------------|-----------|-------|
| `RequiereMFA` | Multi-factor auth | Mejora seguridad |
| `PasswordTemporal` | Flag de password temporal | Mejora UX |
| `DebeCambiarPassword` | Forzar cambio | Mejora seguridad |
| `IntentosFallidos` | Contador bloqueo | Mejora seguridad |
| `Bloqueado` | Estado bloqueo | Mejora seguridad |
| `FechaBloqueo` | Timestamp bloqueo | Auditoría |
| `MotivoBloqueo` | Razón del bloqueo | Auditoría |
| `FechaExpiracionPassword` | Caducidad password | Mejora seguridad |
| `ZonaHoraria` | Timezone usuario | Mejora UX |
| `Idioma` | Idioma preferido | Mejora UX |

### 3.4 Estructura de Roles

| MongoDB (rbac_roles) | EDARSAHUB (Usuario_Roles) | Paridad |
|----------------------|---------------------------|---------|
| `id` (UUID) | `RolID` (int) | ⚠️ TIPO DIFERENTE |
| `nombre` | `NombreRol` | ✅ |
| `descripcion` | `Descripcion` | ✅ |
| `permisos` (array embedded) | N/A - via PermisosRolModulo | ⚠️ NORMALIZADO |
| `nivel_jerarquia` | N/A | ❌ NO EXISTE |
| `es_sistema` | `EsRolSistema` | ✅ |
| `activo` | `Activo` | ✅ |

**Datos actuales:**

MongoDB rbac_roles:
- ADMIN (nivel 100)
- DIRECCION (nivel 80)
- GERENTE_OPS (nivel 60)
- SUPERVISOR (nivel 40)
- AUDITOR (nivel 30)
- OPERADOR (nivel 20)

EDARSAHUB Usuario_Roles:
- ADMIN (Administrador)
- GERENCIA (Gerencia)
- COMPRAS (Compras)
- VENTAS (Ventas)
- TESORERIA (Tesoreria)

**⚠️ INCOMPATIBILIDAD:** Los roles no coinciden entre sistemas. Se requiere mapeo.

### 3.5 Estructura de Permisos

| MongoDB (rbac_permisos) | EDARSAHUB (Usuario_PermisosRolModulo) | Paridad |
|-------------------------|--------------------------------------|---------|
| `codigo` (ej: CARGOS_VER) | N/A - AccionID referencia Usuario_Acciones | ⚠️ DIFERENTE |
| `modulo` (string) | `ModuloID` (FK a Usuario_Modulos) | ⚠️ NORMALIZADO |
| `accion` (string) | `AccionID` (FK a Usuario_Acciones) | ⚠️ NORMALIZADO |
| `descripcion` | N/A | ❌ |

**Ejemplo de diferencia:**
- MongoDB: `{"codigo": "CARGOS_VER", "modulo": "cargos", "accion": "ver"}`
- EDARSAHUB: Requiere JOINs: PermisosRolModulo → Modulos → Acciones

---

## 4. PARIDAD MONGODB vs EDARSAHUB — SERVIDORES/UNIDADES/SUCURSALES

### 4.1 Servidores

| Análisis | Resultado |
|----------|-----------|
| IDs en AMBOS sistemas | 13 ✅ |
| IDs solo en MongoDB | 0 |
| IDs solo en EDARSAHUB | 4 |

**Servidores exclusivos de EDARSAHUB:**
1. `817a0aa8-6170-4738-a8f6-a72ac36ba0df` - ORIGEN LOCAL
2. `dc44c86b-8f1f-4b44-9704-6cea89297c69` - TEST API LOCAL
3. `72f6e9a7-8ea2-4eb2-802e-4ee31753435e` - 130° QRO LOCAL
4. `31d62f39-632b-4684-b735-256bd9293a8f` - CIENFUEGOS NOMINPAQ

**Conclusión:** La paridad de servidores es BUENA. MongoDB es subconjunto de EDARSAHUB.

### 4.2 Unidades de Negocio

| MongoDB (sec_unidades_negocio) | EDARSAHUB (Unidades_Negocio) |
|--------------------------------|------------------------------|
| 7 documentos | 5 registros |

**Diferencia:** Los IDs NO coinciden entre sistemas. Se requiere mapeo por nombre.

### 4.3 Campos de Servidores

| Campo MongoDB (servers) | Campo EDARSAHUB (Servidores_Conexiones) | Paridad |
|-------------------------|----------------------------------------|---------|
| `id` | `id` (uniqueidentifier) | ✅ |
| `name` | `nombre` | ✅ |
| `system_type` | `system_type` | ✅ |
| `host` | `host` | ✅ |
| `port` | `port` | ✅ |
| `database` | `database_name` | ✅ |
| `username` | `username` | ✅ |
| `password` | `password_encrypted` | ✅ Cifrado diferente |
| `active` | `activo` | ✅ |
| `sucursales` (array JSON) | `sucursales` (nvarchar JSON) | ✅ |
| `visible_en_operaciones` | `visible_en_operaciones` | ✅ |
| `query_ventas` | `query_ventas` | ✅ |
| `query_inventario` | `query_inventario` | ✅ |
| `query_movimientos` | `query_movimientos` | ✅ |

**Conclusión:** Estructura de servidores es IDÉNTICA. Migración directa posible.

---

## 5. CAMPOS FALTANTES (RESUMEN)

### 5.1 Campos que EDARSAHUB necesita agregar

| Tabla | Campo Faltante | Tipo Propuesto | Criticidad |
|-------|----------------|----------------|------------|
| `Usuario_Catalogo` | `empresas_permitidas` | nvarchar(max) JSON | P0 |
| `Usuario_Catalogo` | `empresa_default_id` | nvarchar(100) | P2 |
| `Usuario_Catalogo` | `contexto_updated_at` | datetime2 | P3 |
| `Usuario_Roles` | `nivel_jerarquia` | int | P1 |
| NUEVA TABLA | `Usuario_Permisos_Especiales` | - | P2 |

### 5.2 Tablas que podrían requerirse

| Tabla Propuesta | Justificación | Criticidad |
|-----------------|---------------|------------|
| `Usuario_EmpresasPermitidas` | Relación N:M usuarios-empresas | P0 |
| `Usuario_SucursalesPermitidas` | Relación N:M usuarios-sucursales | P1 |
| `Sistema_Empresas` | Catálogo maestro de empresas | P1 |

---

## 6. RIESGOS P0/P1/P2/P3

### P0_CRÍTICO (Puede romper login, permisos, operación)

| Riesgo | Descripción | Módulos Afectados |
|--------|-------------|-------------------|
| R-P0-001 | Si se migra auth sin poblar empresas_permitidas, usuarios pierden acceso | TODOS |
| R-P0-002 | Si se migra sin sec_permisos, autorización falla | TODOS |
| R-P0-003 | Diferencia de tipo ID (string vs int) puede romper JOINs | Auth, RBAC |
| R-P0-004 | SuperAdministrador debe seguir funcionando en todo momento | TODOS |
| R-P0-005 | Logout/refresh token debe seguir funcionando | Auth |

### P1_ALTO (Puede ocultar servidores, sucursales, romper dashboards)

| Riesgo | Descripción | Módulos Afectados |
|--------|-------------|-------------------|
| R-P1-001 | Diferencia de IDs en Unidades_Negocio puede romper filtros | Comercial, Compras, Finanzas |
| R-P1-002 | Perder fallback MongoDB sin validar EDARSAHUB completo | TODOS |
| R-P1-003 | Roles no coinciden entre sistemas - mapeo incorrecto | RBAC |
| R-P1-004 | sec_sucursales vs RH_Cat_Sucursales tienen IDs diferentes | Reportes, Filtros |

### P2_MEDIO (Datos incompletos, inconsistencias)

| Riesgo | Descripción | Módulos Afectados |
|--------|-------------|-------------------|
| R-P2-001 | permisos_catalogos no tiene equivalente directo | Catálogos |
| R-P2-002 | puede_autorizar/liberar/solicitar sin equivalente | Workflows |
| R-P2-003 | 4 servidores en EDARSAHUB no visibles si código lee MongoDB | Configuración |

### P3_BAJO (UI no crítica, logs)

| Riesgo | Descripción | Módulos Afectados |
|--------|-------------|-------------------|
| R-P3-001 | scheduler_job_log perdería histórico si se elimina MongoDB | Monitoreo |
| R-P3-002 | dashboard_cache perdería si no hay equivalente | Performance |

---

## 7. ENDPOINTS AFECTADOS

### 7.1 Endpoints que leen MongoDB para Auth/Users

| Endpoint | Archivo | Línea | Colección |
|----------|---------|-------|-----------|
| `POST /auth/login` | `server.py` | ~6375 | `db.users` |
| `GET /auth/me` | `security.py` | 265 | `db.users` |
| `GET /dashboard/metrics` | `server.py` | 6280 | `db.users` |
| `PUT /users/{id}/permissions` | `server.py` | 13182-13202 | `db.users` |
| `GET /usuarios/listar` | `server.py` | 13963-13971 | `db.users`, `db.roles` |
| `POST /auth/forgot-password` | `password_reset.py` | - | `db.users` |
| `POST /auth/reset-password` | `password_reset.py` | - | `db.users` |

### 7.2 Endpoints que leen MongoDB para Servers

| Endpoint | Archivo | Línea | Colección |
|----------|---------|-------|-----------|
| `GET /servers` | `server.py` | 1186 | `db.servers` (fallback) |
| `POST /servers` | `server.py` | 1129 | `db.servers` |
| `PUT /servers/{id}` | `server.py` | 1239 | `db.servers` |
| `DELETE /servers/{id}` | `server.py` | 1297 | `db.servers` |
| `GET /servers/{id}/ping` | `server.py` | 1352 | `db.servers` |

### 7.3 Endpoints que YA leen EDARSAHUB

| Endpoint | Módulo | Tabla EDARSAHUB |
|----------|--------|-----------------|
| `GET /v2/finanzas/*` | Finanzas | Finanzas_* |
| `GET /rh/*` | RH | RH_* |
| `GET /comercial/tablero-ejecutivo` | Comercial | Comercial_Ventas_Dia_Abiertas_v2 (fallback) |

---

## 8. ARCHIVOS AFECTADOS

### 8.1 Archivos que usan db.users (17 archivos)

```
/app/backend/server.py
/app/backend/core/security.py
/app/backend/core/user_access_context.py
/app/backend/modules/auth/password_reset.py
/app/backend/modules/auth/context_service.py
/app/backend/modules/auth/repository.py
/app/backend/modules/fase2_operativo/services/cargos_service.py
/app/backend/modules/fase2_operativo/services/orquestador_service.py
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py
/app/backend/modules/manuales_operativos/triggers.py
/app/backend/core/communications/notifications/service.py
/app/backend/routes/portal_proveedores.py
/app/backend/init_queries.py
```

### 8.2 Archivos que usan db.servers (38 archivos)

```
/app/backend/server.py
/app/backend/core/server_registry.py
/app/backend/core/connection_resolver.py
/app/backend/core/context_resolver.py
/app/backend/core/user_access_context.py
/app/backend/core/server_connection_manager.py
/app/backend/core/resilient_sql.py
/app/backend/core/health_checker.py
/app/backend/core/scheduler/jobs/pedidos_detector_job.py
/app/backend/core/scheduler/jobs/inventarios_detector_job.py
/app/backend/modules/comercial/historical_kpis_repository.py
/app/backend/modules/finanzas/tesoreria.py
/app/backend/modules/finanzas/repository_real.py
/app/backend/modules/finanzas/historical_kpis_repository.py
/app/backend/modules/finanzas/propinas_tpv/*.py (6 archivos)
/app/backend/modules/compras/historical_kpis_repository.py
/app/backend/modules/catalogos/repository.py
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py
/app/backend/modules/configuracion/services/almacenes_sync_service.py
/app/backend/routes/portal_proveedores.py
/app/backend/scripts/*.py (8 scripts)
```

---

## 9. MÓDULOS BLINDADOS QUE NO DEBEN TOCARSE

| Módulo | Razón | Dependencia Crítica |
|--------|-------|---------------------|
| **Tablero Ejecutivo** | Módulo de alta visibilidad ejecutiva | Comercial_Ventas_Dia_Abiertas_v2 |
| **Comercial** | KPIs de ventas en producción | SQL vivo + EDARSAHUB fallback |
| **Compras** | Operación diaria de compras | SQL vivo MPRO |
| **Finanzas** | Módulo ya migrado a EDARSAHUB | Finanzas_* |
| **RH/Nóminas** | Módulo ya migrado a EDARSAHUB | RH_* |
| **Login** | Punto único de entrada | MongoDB users (NO TOCAR AÚN) |

---

## 10. ESTRATEGIA DE MIGRACIÓN SEGURA

### Principios Fundamentales

1. **NUNCA** romper login existente
2. **NUNCA** dejar usuarios sin acceso
3. **SIEMPRE** mantener fallback funcional
4. **SIEMPRE** validar con usuario piloto primero
5. **SIEMPRE** poder hacer rollback inmediato

### Patrón de Migración: "Espejo → Validación → Activación → Observación → Retiro"

```
┌─────────────────────────────────────────────────────────────────┐
│                    ESTADO ACTUAL                                 │
│  MongoDB ────────────────────────────► Sistema                  │
│  (fuente única)                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASE A2: ESPEJO                               │
│  MongoDB ────────────────────────────► Sistema                  │
│      │                                                           │
│      └──── sync ────► EDARSAHUB (replica silenciosa)            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASE A3: VALIDACIÓN PARALELA                  │
│  MongoDB ────────────────────────────► Sistema                  │
│      │                                      │                    │
│      └──── sync ────► EDARSAHUB ──compare──┘                    │
│                       (valida paridad)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASE A4: PILOTO                               │
│  MongoDB ────────────────────────────► Sistema (mayoría)        │
│                                                                  │
│  EDARSAHUB ─────────────────────────► Usuario Piloto            │
│                                       (SuperAdministrador)       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASE A5: ACTIVACIÓN GENERAL                   │
│  EDARSAHUB ─────────────────────────► Sistema                   │
│      │                                                           │
│  MongoDB ◄──── fallback automático si EDARSAHUB falla           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASE A7: RETIRO (después de observación)      │
│  EDARSAHUB ─────────────────────────► Sistema                   │
│                                                                  │
│  MongoDB (desactivado, backup histórico)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. ESTRATEGIA DE ROLLBACK

### Rollback Inmediato (< 1 minuto)

```python
# Variable de entorno para rollback instantáneo
USE_EDARSAHUB_AUTH = os.environ.get('USE_EDARSAHUB_AUTH', 'false').lower() == 'true'

# En get_current_user():
if USE_EDARSAHUB_AUTH:
    user = await get_user_from_edarsahub(email)
else:
    user = await db.users.find_one({"email": email})  # MongoDB original
```

**Rollback:** Cambiar variable de entorno y reiniciar servicio.

### Rollback Automático (Fallback)

```python
async def get_current_user_resilient(email: str):
    try:
        # Intentar EDARSAHUB
        user = await get_user_from_edarsahub(email)
        if user:
            return user
    except Exception as e:
        logger.warning(f"EDARSAHUB auth failed, falling back to MongoDB: {e}")
    
    # Fallback a MongoDB
    return await db.users.find_one({"email": email})
```

### Puntos de No Retorno

| Fase | ¿Reversible? | Acción de Rollback |
|------|--------------|-------------------|
| A0-A3 | ✅ Sí | Solo se lee/compara, nada cambia |
| A4 | ✅ Sí | Desactivar flag de piloto |
| A5 | ✅ Sí | Cambiar USE_EDARSAHUB_AUTH=false |
| A6 | ✅ Sí | Fallback automático funciona |
| A7 | ⚠️ Parcial | Restaurar MongoDB desde backup |

---

## 12. PRUEBAS OBLIGATORIAS ANTES DE AUTORIZAR IMPLEMENTACIÓN

### 12.1 Pruebas de Paridad (Pre-Migración)

| # | Prueba | Criterio de Éxito |
|---|--------|-------------------|
| T-01 | Verificar todos los usuarios MongoDB existen en EDARSAHUB | 15/15 usuarios |
| T-02 | Verificar passwords son validables en EDARSAHUB | Hash compatible |
| T-03 | Verificar roles tienen mapeo definido | 6/6 roles mapeados |
| T-04 | Verificar permisos tienen equivalente | 43/43 permisos |
| T-05 | Verificar empresas_permitidas tiene destino | Campo agregado o tabla |

### 12.2 Pruebas de Login (Post-Migración Piloto)

| # | Prueba | Criterio de Éxito |
|---|--------|-------------------|
| T-10 | Login SuperAdministrador funciona | Token válido |
| T-11 | Login con credenciales incorrectas falla | 401 correcto |
| T-12 | Refresh token funciona | Nuevo token válido |
| T-13 | Logout invalida sesión | Sesión cerrada |
| T-14 | MFA funciona (si aplica) | Validación correcta |

### 12.3 Pruebas de RBAC (Post-Migración Piloto)

| # | Prueba | Criterio de Éxito |
|---|--------|-------------------|
| T-20 | SuperAdministrador ve todos los módulos | Sidebar completo |
| T-21 | Usuario normal ve solo módulos permitidos | Filtrado correcto |
| T-22 | Filtro de empresa funciona | Datos filtrados |
| T-23 | Filtro de sucursal funciona | Datos filtrados |
| T-24 | Permisos funcionales se evalúan correctamente | Acceso/denegación correcto |

### 12.4 Pruebas de Servidores (Post-Migración)

| # | Prueba | Criterio de Éxito |
|---|--------|-------------------|
| T-30 | Lista de servidores coincide | 17/17 servidores |
| T-31 | Conexión a cada servidor funciona | Ping exitoso |
| T-32 | Queries configuradas funcionan | Datos retornados |
| T-33 | Módulo Comercial funciona | Dashboard carga |
| T-34 | Módulo Compras funciona | Inventarios cargan |

### 12.5 Pruebas de Rollback

| # | Prueba | Criterio de Éxito |
|---|--------|-------------------|
| T-40 | Cambiar USE_EDARSAHUB_AUTH=false restaura MongoDB | Login funciona |
| T-41 | Fallback automático activa si EDARSAHUB falla | Login sigue funcionando |
| T-42 | Tiempo de rollback < 1 minuto | Verificado |

---

## 13. FASES PROPUESTAS

### FASE A: Migración Auth/RBAC

| Fase | Descripción | Riesgo | Reversible |
|------|-------------|--------|------------|
| **A0** | Backup completo de MongoDB collections auth | NINGUNO | ✅ |
| **A1** | Script de análisis de paridad (ESTE DOCUMENTO) | NINGUNO | ✅ |
| **A2** | Poblar EDARSAHUB en modo espejo (INSERT, sin cambiar lectura) | BAJO | ✅ |
| **A3** | Validación paralela login MongoDB vs EDARSAHUB (comparación) | BAJO | ✅ |
| **A4** | Activar EDARSAHUB solo para SuperAdministrador piloto | MEDIO | ✅ |
| **A5** | Activar EDARSAHUB para todos los usuarios | ALTO | ✅ |
| **A6** | Mantener MongoDB como fallback (2-4 semanas) | BAJO | ✅ |
| **A7** | Retirar dependencia MongoDB (después de observación) | MEDIO | ⚠️ Parcial |

**Duración estimada:** 4-6 semanas (con autorización incremental)

### FASE B: Consolidación Servidores

| Fase | Descripción | Riesgo | Reversible |
|------|-------------|--------|------------|
| **B0** | Backup de MongoDB servers collection | NINGUNO | ✅ |
| **B1** | Script de paridad IDs (COMPLETADO EN ESTE DOCUMENTO) | NINGUNO | ✅ |
| **B2** | Sincronizar 4 servidores faltantes de EDARSAHUB → MongoDB | BAJO | ✅ |
| **B3** | Eliminar fallback MongoDB en server_registry.py | MEDIO | ✅ |
| **B4** | Validar módulos Comercial/Compras/Finanzas | ALTO | ✅ |
| **B5** | Retiro gradual de MongoDB servers | MEDIO | ⚠️ Parcial |

**Duración estimada:** 2-3 semanas

---

## 14. RECOMENDACIÓN FINAL

### Estado del Diagnóstico: ✅ COMPLETADO

Este documento presenta el análisis completo de paridad entre MongoDB y EDARSAHUB para Auth/RBAC y Servidores. Los hallazgos principales son:

1. **Auth/RBAC:** EDARSAHUB tiene tablas completas pero VACÍAS. El sistema depende 100% de MongoDB. Migración requiere poblar datos y agregar campos faltantes (empresas_permitidas).

2. **Servidores:** Paridad casi completa (13/17 IDs coinciden). EDARSAHUB ya es primario con fallback MongoDB funcional.

### Recomendación de Prioridad

| Prioridad | Acción | Justificación |
|-----------|--------|---------------|
| **P0** | Agregar campos faltantes a EDARSAHUB (empresas_permitidas, etc.) | Sin esto, migración es imposible |
| **P1** | Ejecutar FASE A0-A3 (backup, espejo, validación) | Prepara migración sin riesgo |
| **P2** | Ejecutar FASE B2-B3 (sincronizar servidores) | Elimina fallback innecesario |
| **P3** | Ejecutar FASE A4-A5 (activación piloto y general) | Solo después de validación completa |

### Próximo Paso Inmediato

**SOLICITAR AUTORIZACIÓN** para:
1. Agregar columnas faltantes a `Usuario_Catalogo` en EDARSAHUB
2. Crear tabla `Usuario_EmpresasPermitidas` si se aprueba modelo relacional
3. Ejecutar FASE A0 (backup de MongoDB)

---

## 15. AUTORIZACIÓN REQUERIDA

### Para proceder con implementación se requiere:

- [ ] **AUTORIZACIÓN FASE A0:** Ejecutar backup de MongoDB auth collections
- [ ] **AUTORIZACIÓN FASE A1:** (Completado - este documento)
- [ ] **AUTORIZACIÓN DDL:** Agregar columnas a Usuario_Catalogo
- [ ] **AUTORIZACIÓN FASE A2:** Poblar EDARSAHUB en modo espejo
- [ ] **AUTORIZACIÓN FASE A4:** Activar piloto SuperAdministrador
- [ ] **AUTORIZACIÓN FASE B2:** Sincronizar servidores faltantes

### Firmas

| Rol | Nombre | Fecha | Autorización |
|-----|--------|-------|--------------|
| Usuario/Propietario | _________________ | __________ | ⬜ A0 ⬜ DDL ⬜ A2 ⬜ A4 ⬜ B2 |
| Arquitectura | Sistema | 2026-05-08 | N/A (solo propuesta) |

---

**FIN DEL DOCUMENTO DE PROPUESTA**

*Este documento es de solo lectura. Ningún cambio ha sido realizado al sistema.*
*Toda implementación requiere autorización expresa del usuario.*
