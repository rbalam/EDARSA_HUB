# FASE 3-D: Migración de user_access_context.py a EDARSAHUB SQL

**Fecha:** 2026-05-14  
**Fase:** FASE 3-D  
**Estado:** COMPLETADA  
**Autor:** Agente E1  
**Régimen:** Autorización Controlada

---

## 1. Objetivo

Migrar el módulo `user_access_context.py` para que el acceso efectivo del usuario se resuelva desde EDARSAHUB SQL en lugar de MongoDB.

---

## 2. Funciones Modificadas

| Función | Propósito | Cambio Realizado |
|---------|-----------|------------------|
| `_get_db()` | Conexión MongoDB | **ELIMINADA** - Reemplazada por `_get_sql_connection()` |
| `resolve_user_access_context()` | Resuelve acceso efectivo | Migrada a SQL |
| `_resolver_acceso_global()` | Resuelve acceso SUPERADMIN/ADMIN | Migrada a SQL (`_resolver_acceso_global_sql()`) |
| `_resolver_servers_desde_empresas()` | Traduce empresas → servidores | Migrada a SQL (`_get_servers_from_empresas_sql()`) |
| `has_server_access()` | Valida acceso a servidor | Sin cambios (usa contexto) |
| `has_empresa_access()` | Valida acceso a empresa | Sin cambios (usa contexto) |
| `has_almacen_access()` | Valida acceso a almacén | Sin cambios (usa contexto) |
| `filter_servers()` | Filtra lista de servidores | Mejorado con case-insensitive |
| `filter_empresas()` | Filtra lista de empresas | Mejorado con case-insensitive |

---

## 3. Colecciones MongoDB Eliminadas del Flujo

| Colección MongoDB | Tabla SQL Reemplazo |
|-------------------|---------------------|
| `db.empresas` | `Sistema_Empresas` + `Sistema_EmpresasMongoMap` |
| `db.sucursales_catalogo` | `Sistema_Sucursales` |
| `db.sucursal_servidor_map` | `Sistema_SucursalServidorMapeo` |
| `db.servers` | `Servidores_Conexiones` |
| `db.users` | `Usuario_Catalogo` |
| `db.sec_roles` | `Usuario_Roles` + `Usuario_RolesAsignacion` |
| `db.sec_permisos_catalogo` | (Permisos desde user dict) |

---

## 4. Tablas SQL Utilizadas

| Tabla | Propósito | Campos Clave |
|-------|-----------|--------------|
| `Usuario_Catalogo` | Identificar UsuarioID SQL | UsuarioID, PublicUUID |
| `Usuario_RolesAsignacion` | Obtener rol efectivo | UsuarioID, RolID |
| `Usuario_Roles` | Código del rol | CodigoRol |
| `Usuario_EmpresasAsignacion` | Empresas asignadas | UsuarioID, EmpresaID, EsPrincipal |
| `Usuario_ServidoresAsignacion` | Servidores directos | UsuarioID, ServidorID |
| `Usuario_SucursalesAsignacion` | Sucursales permitidas | UsuarioID, ServidorID, SucursalCodigo |
| `Usuario_AlmacenesAsignacion` | Almacenes permitidos | UsuarioID, ServidorID, AlmacenCodigo |
| `Sistema_Empresas` | Catálogo empresas | EmpresaID, Activo |
| `Sistema_EmpresasMongoMap` | Mapeo UUID → ID SQL | EmpresaMongoUUID, EmpresaID_SQL |
| `Sistema_Sucursales` | Catálogo sucursales | SucursalID, EmpresaID |
| `Sistema_SucursalServidorMapeo` | Mapeo sucursal → servidor | SucursalID, ServidorID |
| `Servidores_Conexiones` | Catálogo servidores | id, visible_en_operaciones |

---

## 5. Helpers SQL Creados

| Helper | Descripción |
|--------|-------------|
| `_get_sql_connection()` | Conexión a EDARSAHUB |
| `_get_user_id_sql()` | UsuarioID desde PublicUUID |
| `_get_user_role_sql()` | Código de rol del usuario |
| `_get_all_empresas_sql()` | Todas las empresas activas |
| `_get_all_servers_sql()` | Todos los servidores visibles |
| `_get_user_empresas_sql()` | Empresas asignadas al usuario |
| `_get_user_servers_sql()` | Servidores directos asignados |
| `_get_servers_from_empresas_sql()` | Traduce empresas → servidores via mapeos |
| `_get_user_sucursales_sql()` | Sucursales por servidor |
| `_get_user_almacenes_sql()` | Almacenes por servidor |

---

## 6. Contrato de Salida (Antes/Después)

### UserAccessContext.to_dict()

**ANTES (MongoDB):**
```python
{
    "user_id": "uuid",
    "email": "user@example.com",
    "nombre": "Usuario",
    "tiene_acceso_global": True,
    "fuente_acceso": "SUPERADMIN",
    "empresas_ids": ["uuid1", "uuid2"],
    "empresa_default_id": "uuid1",
    "servers_ids": ["server-uuid1"],
    "almacenes_por_server": {"server-uuid1": ["001", "002"]},
    "sucursales_por_server": {"server-uuid1": ["default"]},
    "permisos": [],
    "sec_roles": [],
    ...
}
```

**DESPUÉS (SQL):**
```python
{
    "user_id": "uuid",
    "email": "user@example.com", 
    "nombre": "Usuario",
    "tiene_acceso_global": True,
    "fuente_acceso": "SUPERADMIN",
    "empresas_ids": ["uuid1", "uuid2"],  # UUIDs MongoDB (compatibilidad)
    "empresa_default_id": "uuid1",
    "servers_ids": ["server-uuid1"],  # UUIDs lowercase
    "almacenes_por_server": {"server-uuid1": ["001", "002"]},
    "sucursales_por_server": {"server-uuid1": ["default"]},
    "permisos": [],
    "sec_roles": [],
    ...
}
```

**Contrato preservado al 100%**

---

## 7. Validación por Usuario

### Usuarios con Acceso Global

| Usuario | Rol | Empresas | Servidores | Fuente | Estado |
|---------|-----|----------|------------|--------|--------|
| ricardo@edarsa.com.mx | SuperAdministrador | 5 | 8 | SUPERADMIN | ✅ |
| admin@inventario.com | Administrador | 5 | 8 | ADMIN | ✅ |
| carlos@alpuntoycoma.mx | Administrador | 5 | 8 | ADMIN | ✅ |
| eduardo@alpuntoycoma.mx | Administrador | 5 | 8 | ADMIN | ✅ |

### Usuarios con Alcance Limitado

| Usuario | Rol | Empresas | Empresa | Servidores | Almacenes | Fuente | Estado |
|---------|-----|----------|---------|------------|-----------|--------|--------|
| david.ricardez@cienfuegos.mx | Usuario | 1 | CIENFUEGOS | 1 (via RBAC) + 3 (directo) | 0 | MIXTO | ✅ |
| almacen@cienfuegos.mx | Usuario | 1 | CIENFUEGOS | 1 | 10 (001-400) | MIXTO | ✅ |
| administracion@cienfuegos.mx | Supervisor | 1 | CIENFUEGOS | 1 | 0 | MIXTO | ✅ |

---

## 8. Validación SUPERADMIN

```
SUPERADMIN ricardo@edarsa.com.mx:
├── tiene_acceso_global: True ✅
├── empresas_ids: 5 empresas ✅
│   ├── 31784356-6d0b-47ce-8fe8-c8a442e45a07 (ORIGEN)
│   ├── 1118f83c-fd45-4681-8006-5e92dd6d01c1 (130 QRO)
│   ├── 1d91f076-a28e-49a5-b445-84aa767737b6 (CIENFUEGOS)
│   ├── e302e16f-2d97-4119-9ad9-bb5b00b71367 (LA ESTELAR)
│   └── a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff (130 MID)
├── servers_ids: 8 servidores ✅
│   ├── a5547321-1139-4d2b-9d53-182ca737b6b6 (130° MERIDA)
│   ├── 6d053c22-523e-48c0-b72b-96081e2d781b (CIENFUEGOS)
│   ├── f8a9049a-96e8-4210-84ae-595ffa2822fa (EDARSA HUB)
│   ├── a5ff0e25-f029-43db-b634-d4ac814c904f (LA ESTELAR)
│   ├── 1b230a06-ffaf-4c70-bd27-b1be3579dea6 (ManagmentPro)
│   └── ... (3 servidores de test)
└── fuente_acceso: SUPERADMIN ✅
```

---

## 9. Evidencia grep

```bash
$ grep -R "db.empresas" /app/backend/core/user_access_context.py
(sin resultados) ✅

$ grep -R "db.sucursales_catalogo" /app/backend/core/user_access_context.py
(sin resultados) ✅

$ grep -R "db.sucursal_servidor_map" /app/backend/core/user_access_context.py
(sin resultados) ✅

$ grep -R "db.server_sucursales_config" /app/backend/core/user_access_context.py
(sin resultados) ✅

$ grep -R "db.servers" /app/backend/core/user_access_context.py
(sin resultados) ✅

$ grep -R "db.users" /app/backend/core/user_access_context.py
(sin resultados) ✅

$ grep -R "db.sec_roles" /app/backend/core/user_access_context.py
(sin resultados) ✅

$ grep -R "db.sec_permisos_catalogo" /app/backend/core/user_access_context.py
(sin resultados) ✅

$ grep -R "_get_db" /app/backend/core/user_access_context.py
(sin resultados) ✅

$ grep -R "AsyncIOMotorClient" /app/backend/core/user_access_context.py
(sin resultados) ✅

$ grep -R "motor.motor_asyncio" /app/backend/core/user_access_context.py
(sin resultados) ✅
```

**Total referencias MongoDB productivas: 0**

---

## 10. Pruebas de No Regresión

| Prueba | Resultado |
|--------|-----------|
| Login funciona | ✅ |
| Auth SQL-first funciona | ✅ |
| `/api/users` retorna 11 usuarios | ✅ |
| `/api/servers` retorna 8 servidores | ✅ |
| `/api/config-asignaciones/unidades-negocio` retorna 5 unidades | ✅ |
| `/api/v2/comercial/health` status ok | ✅ |
| `/api/v2/comercial/unidades` retorna 6 unidades | ✅ |
| SUPERADMIN resuelve 5 empresas y 8 servidores | ✅ |
| Usuario CIENFUEGOS resuelve 1 empresa | ✅ |
| Almacenes por servidor preservados | ✅ |
| Sucursales por servidor preservados | ✅ |

---

## 11. Inconsistencias Detectadas

| Elemento | Observación | Impacto |
|----------|-------------|---------|
| `sec_roles` en SQL | Los permisos de sec_roles se toman del user dict, no de una tabla SQL | BAJO - Funciona correctamente, deuda técnica menor |
| `sec_permisos_catalogo` | No hay tabla equivalente en SQL | BAJO - Los permisos vienen del user dict |

---

## 12. Riesgos Residuales

| Riesgo | Mitigación |
|--------|------------|
| Permisos funcionales (`sec_roles`) aún provienen del user dict | Documentado como deuda técnica; funcionalidad no afectada |
| Catálogo de permisos no migrado a SQL | Considerar migración en fase futura si se requiere |

---

## 13. Archivos NO Modificados (Según Autorización)

| Archivo | Estado |
|---------|--------|
| `/app/backend/core/context_service.py` | NO TOCADO (FASE 3-E) |
| Frontend | NO TOCADO |
| Auth/RBAC | NO TOCADO |
| Login/JWT | NO TOCADO |
| Tablero Ejecutivo | NO TOCADO |
| Comercial V2 | NO TOCADO |
| Finanzas | NO TOCADO |
| Compras | NO TOCADO |
| Inventarios | NO TOCADO |

---

## 14. Validación de las 5 Relaciones

| Empresa | Sucursal | Servidor | System Type | Estado |
|---------|----------|----------|-------------|--------|
| ORIGEN | ORIGEN | ManagmentPro | MPRO | ✅ |
| 130 QRO | 130° QUERETARO | ManagmentPro | MPRO | ✅ |
| CIENFUEGOS | CIENFUEGOS | CIENFUEGOS | SoftRestaurant | ✅ |
| LA ESTELAR | LA ESTELAR | LA ESTELAR | SoftRestaurant | ✅ |
| 130 MID | 130° MERIDA | 130° MERIDA | SoftRestaurant | ✅ |

---

## 15. Recomendación para FASE 3-E

1. **Migrar `context_service.py`** siguiendo el mismo patrón.
2. **Evaluar migración de `sec_roles`** a tabla SQL si se requiere resolución desde SQL.
3. **Validar módulos que usan `resolve_user_access_context()`** para asegurar compatibilidad.

---

## Resumen Ejecutivo

| Aspecto | Estado |
|---------|--------|
| `user_access_context.py` migrado a SQL | ✅ |
| 0 referencias MongoDB productivas | ✅ |
| Usuarios resuelven acceso desde SQL | ✅ |
| SUPERADMIN conserva acceso global (5 empresas, 8 servidores) | ✅ |
| Usuarios limitados conservan su alcance | ✅ |
| Contrato de salida preservado | ✅ |
| `context_service.py` NO TOCADO | ✅ |
| Sin regresión en endpoints | ✅ |

**FASE 3-D: COMPLETADA**
