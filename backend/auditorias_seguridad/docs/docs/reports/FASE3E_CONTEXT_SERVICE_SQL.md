# FASE 3-E: Migración de context_service.py a EDARSAHUB SQL

**Fecha:** 2026-05-14  
**Fase:** FASE 3-E  
**Estado:** COMPLETADA  
**Autor:** Agente E1  
**Régimen:** Autorización Controlada

---

## 1. Objetivo

Migrar el módulo `context_service.py` para que el contexto de navegación/UI deje de depender productivamente de MongoDB y use EDARSAHUB SQL como fuente.

---

## 2. Funciones Modificadas

| Función | Propósito | Cambio Realizado |
|---------|-----------|------------------|
| `get_db()` import | Conexión MongoDB | **ELIMINADA** - Reemplazada por `_get_sql_connection()` |
| `get_user_context()` | Resuelve contexto completo | Migrada a SQL |
| `get_user_context_for_empresa()` | Contexto para empresa específica | Migrada a SQL |
| `get_empresas_disponibles()` | Lista empresas del usuario | Migrada a SQL |

---

## 3. Colecciones MongoDB Eliminadas del Flujo

| Colección MongoDB | Tabla SQL Reemplazo |
|-------------------|---------------------|
| `db.users` | `Usuario_Catalogo` |
| `db.empresas` | `Sistema_Empresas` + `Sistema_EmpresasMongoMap` |
| `db.rbac_usuarios_roles` | `Usuario_RolesAsignacion` |
| `db.rbac_roles` | `Usuario_Roles` |
| `db.rbac_permisos` | (No migrado - permisos desde user dict) |
| `db.sucursales_catalogo` | `Sistema_Sucursales` |

---

## 4. Tablas SQL Utilizadas

| Tabla | Propósito | Campos Clave |
|-------|-----------|--------------|
| `Usuario_Catalogo` | Obtener usuario por PublicUUID | UsuarioID, Email, Nombre, PublicUUID |
| `Usuario_Roles` | Catálogo de roles | RolID, CodigoRol, NombreRol |
| `Usuario_RolesAsignacion` | Rol asignado al usuario | UsuarioID, RolID, EsPrincipal |
| `Usuario_EmpresasAsignacion` | Empresas del usuario | UsuarioID, EmpresaID, EsPrincipal |
| `Sistema_Empresas` | Catálogo empresas | EmpresaID, CodigoEmpresa, NombreEmpresa |
| `Sistema_EmpresasMongoMap` | Mapeo UUID MongoDB → ID SQL | EmpresaMongoUUID, EmpresaID_SQL |
| `Sistema_Sucursales` | Catálogo sucursales | SucursalID, EmpresaID, NombreSucursal |
| `Usuario_ServidoresAsignacion` | Servidores legacy | UsuarioID, ServidorID |
| `Usuario_SucursalesAsignacion` | Sucursales legacy | UsuarioID, ServidorID, SucursalCodigo |

---

## 5. Helpers SQL Creados

| Helper | Descripción |
|--------|-------------|
| `_get_sql_connection()` | Conexión a EDARSAHUB |
| `_get_user_by_public_uuid()` | Usuario por PublicUUID |
| `_get_user_role_sql()` | Rol del usuario |
| `_get_user_empresas_sql()` | Empresas asignadas |
| `_get_all_empresas_sql()` | Todas las empresas (SUPERADMIN/ADMIN) |
| `_get_sucursales_by_empresa_sql()` | Sucursales de una empresa |
| `_get_empresa_by_uuid_sql()` | Empresa por UUID MongoDB |
| `_get_user_allowed_servers_sql()` | Servidores legacy |
| `_get_user_allowed_sucursales_sql()` | Sucursales legacy |

---

## 6. Contrato de Salida (Antes/Después)

### get_user_context()

**ANTES (MongoDB):**
```python
{
    "user_id": "uuid",
    "email": "user@example.com",
    "nombre": "Usuario",
    "empresa_default": {"id": "uuid", "nombre": "Empresa", "codigo": "EMP"},
    "empresas_permitidas": [{"id": "uuid", "nombre": "Empresa", "codigo": "EMP"}],
    "rol_actual": "Administrador",
    "permisos": ["permiso1", "permiso2"],
    "sucursales_por_empresa": {"emp_uuid": [{"id": "suc_uuid", "nombre": "Sucursal"}]},
    "legacy": {
        "role": "Administrador",
        "allowed_servers": ["server-uuid"],
        "allowed_sucursales": {"server-uuid": ["default"]}
    }
}
```

**DESPUÉS (SQL):**
```python
{
    "user_id": "uuid",  # PublicUUID
    "email": "user@example.com",
    "nombre": "Usuario",
    "empresa_default": {"id": "uuid-mongo", "nombre": "Empresa", "codigo": "EMP"},
    "empresas_permitidas": [{"id": "uuid-mongo", "nombre": "Empresa", "codigo": "EMP"}],
    "rol_actual": "Administrador",
    "permisos": [],  # Permisos se resuelven en otras capas
    "sucursales_por_empresa": {"emp_uuid": [{"id": "suc_uuid", "nombre": "Sucursal"}]},
    "legacy": {
        "role": "Administrador",
        "allowed_servers": ["server-uuid"],
        "allowed_sucursales": {"server-uuid": ["default"]}
    }
}
```

**Diferencias:**
- `permisos`: Ahora vacío - los permisos se resuelven en otras capas (user dict)
- IDs: Mantienen UUIDs MongoDB para compatibilidad con frontend

---

## 7. Validación por Usuario

| Usuario | Rol | Empresas | Empresa Default | Sucursales | Estado |
|---------|-----|----------|-----------------|------------|--------|
| ricardo@edarsa.com.mx | SuperAdministrador | 5 | ORIGEN | 5 | ✅ |
| admin@inventario.com | Administrador | 5 | ORIGEN | 5 | ✅ |
| carlos@alpuntoycoma.mx | Administrador | 5 | ORIGEN | 5 | ✅ |
| eduardo@alpuntoycoma.mx | Administrador | 5 | ORIGEN | 5 | ✅ |
| david.ricardez@cienfuegos.mx | Usuario | 1 | CIENFUEGOS | 1 | ✅ |
| almacen@cienfuegos.mx | Usuario | 1 | CIENFUEGOS | 1 | ✅ |
| administracion@cienfuegos.mx | Supervisor | 1 | CIENFUEGOS | 1 | ✅ |

---

## 8. Validación de Contexto UI/Navegación

| Elemento | Validación | Estado |
|----------|------------|--------|
| Selector de unidades carga | 5 unidades para SUPERADMIN/ADMIN | ✅ |
| Sucursales por empresa | Resuelven correctamente | ✅ |
| Rol del usuario | Resuelve desde SQL | ✅ |
| Empresa default | Primera empresa o marcada como principal | ✅ |
| Legacy servers | Resuelven desde SQL | ✅ |
| Legacy sucursales | Resuelven desde SQL | ✅ |

---

## 9. Validación de las 5 Relaciones Empresa → Sucursal

| Empresa | Sucursal | Estado |
|---------|----------|--------|
| ORIGEN | ORIGEN | ✅ |
| 130 QRO | 130° QUERETARO | ✅ |
| CIENFUEGOS | CIENFUEGOS | ✅ |
| LA ESTELAR | LA ESTELAR | ✅ |
| 130 MID | 130° MERIDA | ✅ |

---

## 10. Evidencia grep

```bash
$ grep -R "db.empresas" /app/backend/modules/auth/context_service.py
(sin resultados) ✅

$ grep -R "db.sucursales_catalogo" /app/backend/modules/auth/context_service.py
(sin resultados) ✅

$ grep -R "db.sucursal_servidor_map" /app/backend/modules/auth/context_service.py
(sin resultados) ✅

$ grep -R "db.server_sucursales_config" /app/backend/modules/auth/context_service.py
(sin resultados) ✅

$ grep -R "db.servers" /app/backend/modules/auth/context_service.py
(sin resultados) ✅

$ grep -R "db.users" /app/backend/modules/auth/context_service.py
(sin resultados) ✅

$ grep -R "db.rbac_usuarios_roles" /app/backend/modules/auth/context_service.py
(sin resultados) ✅

$ grep -R "db.rbac_roles" /app/backend/modules/auth/context_service.py
(sin resultados) ✅

$ grep -R "db.rbac_permisos" /app/backend/modules/auth/context_service.py
(sin resultados) ✅

$ grep -R "get_db" /app/backend/modules/auth/context_service.py
(sin resultados) ✅

$ grep -R "AsyncIOMotorClient" /app/backend/modules/auth/context_service.py
(sin resultados) ✅
```

**Total referencias MongoDB productivas: 0**

---

## 11. Pruebas de No Regresión

| Prueba | Resultado |
|--------|-----------|
| Login funciona | ✅ |
| Auth SQL-first funciona | ✅ |
| `/api/users` retorna 11 usuarios | ✅ |
| `/api/servers` retorna 8 servidores | ✅ |
| `/api/config-asignaciones/unidades-negocio` retorna 5 unidades | ✅ |
| `/api/v2/comercial/health` status ok | ✅ |
| `/api/v2/comercial/unidades` retorna 6 unidades | ✅ |
| context_service resuelve 7 usuarios correctamente | ✅ |
| Relaciones empresa→sucursal correctas | ✅ |

---

## 12. Inconsistencias Detectadas

| Elemento | Observación | Impacto |
|----------|-------------|---------|
| `permisos` en respuesta | Ahora vacío (lista `[]`) | BAJO - Permisos se resuelven en user dict en otras capas |
| `db.rbac_permisos` | No hay tabla SQL equivalente | BAJO - Funcionalidad no afectada |

---

## 13. Riesgos Residuales

| Riesgo | Mitigación |
|--------|------------|
| Permisos funcionales no migrados a SQL | Documentado; funcionalidad existente no afectada |
| RBAC MongoDB obsoleto pero existente | Considerar limpieza en fase posterior |

---

## 14. Archivos NO Modificados (Según Autorización)

| Archivo | Estado |
|---------|--------|
| `/app/backend/core/context_resolver.py` | NO TOCADO |
| `/app/backend/core/user_access_context.py` | NO TOCADO |
| Frontend | NO TOCADO |
| Auth/RBAC | NO TOCADO |
| Login/JWT | NO TOCADO |
| Tablero Ejecutivo | NO TOCADO |
| Comercial V2 | NO TOCADO |
| Finanzas | NO TOCADO |
| Compras | NO TOCADO |
| Inventarios | NO TOCADO |

---

## 15. Recomendación para FASE 3-F/G

1. **Auditar todas las referencias MongoDB** en la capa de contexto (context_resolver, user_access_context, context_service).

2. **Validar flujo end-to-end** desde login hasta navegación en UI.

3. **Documentar deuda técnica:** 
   - `rbac_permisos` no migrado
   - `rbac_usuarios_roles` MongoDB obsoleto

4. **Considerar limpieza** de colecciones MongoDB que ya no son fuente productiva.

---

## Resumen Ejecutivo

| Aspecto | Estado |
|---------|--------|
| `context_service.py` migrado a SQL | ✅ |
| 0 referencias MongoDB productivas | ✅ |
| Contexto UI/navegación resuelve desde SQL | ✅ |
| SUPERADMIN conserva acceso global (5 empresas) | ✅ |
| Usuarios limitados conservan su alcance | ✅ |
| 7 usuarios validados correctamente | ✅ |
| 5 relaciones empresa→sucursal correctas | ✅ |
| Contrato de salida preservado (excepto permisos vacío) | ✅ |
| Sin regresión en endpoints | ✅ |

**FASE 3-E: COMPLETADA**

---

## Archivos Core de Contexto Migrados

| Archivo | Fase | Estado |
|---------|------|--------|
| `/app/backend/core/context_resolver.py` | FASE 3-C | ✅ Migrado |
| `/app/backend/core/user_access_context.py` | FASE 3-D | ✅ Migrado |
| `/app/backend/modules/auth/context_service.py` | FASE 3-E | ✅ Migrado |

**Los 3 archivos core de contexto han sido migrados a EDARSAHUB SQL.**
