# FASE 2-D: Auth Repository SQL Paralelo

**Fecha de ejecución:** 14-Dic-2025  
**Régimen:** Autorización Controlada  
**Estado:** ✅ COMPLETADA  
**Autorización:** Recibida del usuario para crear repositorio SQL paralelo y validar regla SUPERADMIN (Opción B)

---

## 1. Objetivo

Crear un repositorio SQL paralelo (`user_repository_sql.py`) que permita consultar datos de autenticación y RBAC desde EDARSAHUB SQL sin modificar el flujo productivo de MongoDB.

### Requisitos cumplidos:
- ✅ Crear `user_repository_sql.py` en `/app/backend/core/auth/`
- ✅ Implementar funciones equivalentes a MongoDB (`get_user_by_email`, `get_user_by_uuid`)
- ✅ Implementar regla SUPERADMIN con acceso global implícito (Opción B)
- ✅ Usar `PublicUUID` como `user['id']` para compatibilidad con JWT existente
- ✅ Incluir funciones de comparación MongoDB vs SQL
- ✅ No modificar código productivo de Auth (security.py, service.py)

---

## 2. Implementación

### Archivo creado: `/app/backend/core/auth/user_repository_sql.py`

**Clase principal:** `AuthRepositorySQL`

| Método | Descripción |
|--------|-------------|
| `get_user_by_email_sql(email)` | Busca usuario por email, devuelve dict compatible MongoDB |
| `get_user_by_public_uuid_sql(uuid)` | Busca usuario por PublicUUID |
| `get_user_auth_context_sql(email_or_uuid)` | Contexto completo de autenticación |
| `list_all_users_sql()` | Lista todos los usuarios con contexto |
| `_get_user_rol(cursor, usuario_id)` | Obtiene rol desde `Usuario_RolesAsignacion` |
| `_get_user_empresas(cursor, usuario_id, rol)` | Obtiene empresas permitidas (aplica regla SUPERADMIN) |
| `_get_all_active_empresas(cursor)` | Todas las empresas activas (para SUPERADMIN) |

**Funciones de validación:**
| Función | Descripción |
|---------|-------------|
| `validate_superadmin_rule()` | Valida que SUPERADMIN recibe acceso global |
| `compare_user_mongo_vs_sql(email)` | Compara usuario entre ambas fuentes |
| `list_auth_migration_differences()` | Lista diferencias para todos los usuarios |

---

## 3. Regla SUPERADMIN (Opción B)

### Definición:
> Si el usuario tiene rol `SUPERADMIN`, se le otorga acceso global implícito a todas las empresas activas, sin requerir asignación explícita en `Usuario_EmpresasAsignacion`.

### Implementación en `_get_user_empresas()`:
```python
if rol_codigo == 'SUPERADMIN':
    all_empresas = self._get_all_active_empresas(cursor)
    empresas_uuids = [e['uuid_mongo'] for e in all_empresas if e['uuid_mongo']]
    empresa_default = empresas_uuids[0] if empresas_uuids else None
    return empresas_uuids, empresa_default
```

### Validación:
| SuperAdmin | Empresas Resueltas | Esperadas | Regla Aplicada |
|------------|-------------------|-----------|----------------|
| admin@inventario.com | 5 | 5 | ✅ SÍ |
| ricardo@edarsa.com.mx | 5 | 5 | ✅ SÍ |

**Resultado:** La regla SUPERADMIN funciona correctamente. Ambos usuarios con rol SUPERADMIN reciben acceso automático a las 5 empresas activas sin necesidad de asignaciones explícitas en `Usuario_EmpresasAsignacion`.

---

## 4. Mapeo de Estructura SQL → MongoDB

### Estructura de respuesta compatible:
```python
{
    # Campos compatibles con MongoDB
    'id': str(PublicUUID),           # UUID como string
    'email': email,
    'name': nombre,
    'nombre': nombre,
    'role': rol_mongo,               # Mapeo: SUPERADMIN → SuperAdministrador
    'rol': rol_mongo,
    'active': bool(activo),
    'password': password_hash,       # Hash bcrypt
    'empresas_permitidas': [uuids],  # Lista de UUIDs MongoDB
    'empresa_default_id': uuid,      # UUID de empresa principal
    
    # Metadatos SQL (internos)
    '_sql_usuario_id': int,
    '_sql_rol_id': int,
    '_sql_rol_codigo': str,
    '_sql_mongo_legacy_id': str,
    '_source': 'EDARSAHUB_SQL',
    '_fetched_at': datetime_iso,
}
```

### Mapeo de roles SQL → MongoDB:
| Código SQL | Nombre MongoDB |
|------------|----------------|
| SUPERADMIN | SuperAdministrador |
| ADMIN | Administrador |
| SUPERVISOR | Supervisor |
| USUARIO | Usuario |
| VISOR | Visor |

---

## 5. Validación Funcional

### Test 1: SUPERADMIN (admin@inventario.com)
```
Email: admin@inventario.com
ID (PublicUUID): 0DA77B7B-FE88-4E23-98BC-9CBF543D5EE3
Rol: SuperAdministrador
Activo: True
Empresas: 5 (acceso global implícito)
Tiene Hash: True
Fuente: EDARSAHUB_SQL
```

### Test 2: Usuario Normal (almacen@cienfuegos.mx)
```
Email: almacen@cienfuegos.mx
ID (PublicUUID): 30702651-10A5-4E3A-9F83-245E2A52FEB7
Rol: Usuario
Empresas: 1 (solo CIENFUEGOS)
Empresa Default: 1d91f076-a28e-49a5-b445-84aa767737b6
```

### Resumen de usuarios SQL:
| Rol | Cantidad |
|-----|----------|
| SUPERADMIN | 2 |
| ADMIN | 4 |
| SUPERVISOR | 2 |
| USUARIO | 3 |
| **Total** | **11** |

---

## 6. Usuarios Pendientes (Sin empresas_permitidas en MongoDB)

Los siguientes usuarios existen en SQL pero no tienen asignaciones de empresas porque sus registros originales en MongoDB tampoco las tenían:

| Email | Rol SQL | Empresas SQL | Comentario |
|-------|---------|--------------|------------|
| ricardo@edarsa.com.mx | SUPERADMIN | 5 (implícito) | ✅ Resuelto por regla SUPERADMIN |
| david.ricardez@cienfuegos.mx | USUARIO | 0 | Pendiente de decisión |
| carlos@alpuntoycoma.mx | ADMIN | 0 | Pendiente de decisión |
| eduardo@alpuntoycoma.mx | ADMIN | 0 | Pendiente de decisión |

**Nota:** `ricardo@edarsa.com.mx` tiene acceso global gracias a la regla SUPERADMIN. Los otros 3 usuarios requieren decisión del propietario del sistema para asignar empresas.

---

## 7. Código Productivo NO MODIFICADO

Los siguientes archivos permanecen intactos y siguen usando MongoDB:

| Archivo | Función | Estado |
|---------|---------|--------|
| `/app/backend/core/security.py` | `get_current_user()` | 🔒 INTACTO - Usa MongoDB |
| `/app/backend/modules/auth/service.py` | `login()`, `authenticate()` | 🔒 INTACTO - Usa MongoDB |
| `/app/backend/server.py` | Endpoints Auth | 🔒 INTACTO |

**El sistema productivo sigue operando 100% con MongoDB para autenticación.**

---

## 8. Criterios de Aceptación

| Criterio | Estado |
|----------|--------|
| Repositorio SQL creado sin modificar código productivo | ✅ |
| Funciones equivalentes a MongoDB implementadas | ✅ |
| Regla SUPERADMIN (Opción B) implementada | ✅ |
| PublicUUID usado como `user['id']` | ✅ |
| Validación de regla SUPERADMIN exitosa | ✅ |
| Hash bcrypt disponible en respuestas | ✅ |
| Empresas mapeadas correctamente | ✅ |
| No hay regresión en Auth productivo | ✅ |

---

## 9. Próximos Pasos (Requieren Autorización)

### FASE 2-E: Cambiar `get_current_user` a SQL-first con fallback MongoDB
- Modificar `/app/backend/core/security.py`
- Usar `AuthRepositorySQL.get_user_by_public_uuid_sql()` como fuente principal
- Mantener fallback a MongoDB si SQL no encuentra el usuario
- Logging de fuente usada

### FASE 2-F: Período de Observación
- Monitorear logs de fallback MongoDB
- Validar que todos los logins resuelven desde SQL

### FASE 2-G: Eliminar Fallback MongoDB
- Remover código de fallback
- `get_current_user` depende 100% de SQL

---

## 10. Archivos de Referencia

| Archivo | Descripción |
|---------|-------------|
| `/app/backend/core/auth/user_repository_sql.py` | Repositorio SQL paralelo (NUEVO) |
| `/app/backend/core/auth/__init__.py` | Exportaciones del módulo |
| `/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md` | Validación previa |

---

*Reporte generado bajo régimen de Autorización Controlada.*  
*MongoDB sigue siendo la fuente productiva de autenticación hasta que se autorice FASE 2-E.*
