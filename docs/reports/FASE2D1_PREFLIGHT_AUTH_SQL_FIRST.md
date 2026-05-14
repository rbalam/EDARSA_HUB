# FASE 2-D.1: Preflight Auth SQL-First con Feature Flag Apagado

**Fecha de ejecución:** 14-Dic-2025  
**Régimen:** Autorización Controlada  
**Estado:** ✅ COMPLETADA  
**Autorización:** Recibida para preparar SQL-first sin activarlo

---

## 1. Objetivo

Preparar el cambio a SQL-first sin activarlo todavía, validando que el nuevo repositorio SQL puede reemplazar a MongoDB sin romper login, JWT, permisos, empresas, roles ni visibilidad de módulos.

---

## 2. Archivos Modificados

| Archivo | Cambio | Impacto |
|---------|--------|---------|
| `/app/backend/.env` | Agregado `AUTH_SQL_FIRST_ENABLED=false` | Feature flag apagado |
| `/app/backend/core/security.py` | Agregadas funciones de preflight pasivo | Sin impacto en flujo productivo |

### Funciones agregadas en `security.py`:

| Función | Descripción |
|---------|-------------|
| `_safe_user_for_log()` | Genera versión segura de usuario para logging (sin secretos) |
| `compare_user_mongo_vs_sql_passive()` | Comparación pasiva entre MongoDB y SQL |
| `log_auth_preflight_status()` | Loggea estado de preflight de forma segura |

### Código NO modificado (flujo productivo intacto):
- `get_current_user()` - Sigue usando MongoDB
- `get_current_user_dual()` - Sigue usando MongoDB
- `create_token()` - Sin cambios
- `verify_token()` - Sin cambios
- `login()` en `modules/auth/service.py` - Sin cambios

---

## 3. Feature Flag

### Configuración:
```
AUTH_SQL_FIRST_ENABLED=false
```

### Comportamiento:
| Valor | Descripción |
|-------|-------------|
| `false` (actual) | MongoDB es la fuente productiva. SQL solo se usa para comparación pasiva. |
| `true` (FASE 2-E) | SQL sería la fuente principal con fallback a MongoDB. **NO ACTIVAR sin autorización.** |

### Verificación runtime:
```python
>>> from core.security import AUTH_SQL_FIRST_ENABLED
>>> AUTH_SQL_FIRST_ENABLED
False
```

---

## 4. Comparación MongoDB vs SQL por Usuario

### IDs (PublicUUID):
| Email | ID MongoDB | ID SQL | Match |
|-------|------------|--------|-------|
| admin@edarsa.com | f648dd3f-2232-4245-ae5c-cf5108f6f6e9 | F648DD3F-2232-4245-AE5C-CF5108F6F6E9 | ✓ |
| admin@inventario.com | 0da77b7b-fe88-4e23-98bc-9cbf543d5ee3 | 0DA77B7B-FE88-4E23-98BC-9CBF543D5EE3 | ✓ |
| carlosruz@edarsa.com.mx | a5e56ed0-89b2-4d50-92f4-568a2106ab50 | A5E56ED0-89B2-4D50-92F4-568A2106AB50 | ✓ |
| noxte@alpyc.com | a72b325b-662f-4777-83ed-4dda6e8398a8 | A72B325B-662F-4777-83ED-4DDA6E8398A8 | ✓ |
| auditoria@edarsa.com.mx | e200de9e-0f3e-43a7-a4ea-1b47a1e9bbaf | E200DE9E-0F3E-43A7-A4EA-1B47A1E9BBAF | ✓ |
| almacen@cienfuegos.mx | 30702651-10a5-4e3a-9f83-245e2a52feb7 | 30702651-10A5-4E3A-9F83-245E2A52FEB7 | ✓ |
| administracion@cienfuegos.mx | 57dbb5ad-ed23-4ed6-8d60-f590a7622994 | 57DBB5AD-ED23-4ED6-8D60-F590A7622994 | ✓ |
| ricardo@edarsa.com.mx | 1e18a085-4092-40d8-aefa-bbafd1cdb939 | 1E18A085-4092-40D8-AEFA-BBAFD1CDB939 | ✓ |
| david.ricardez@cienfuegos.mx | f3ba4a2f-9cb9-4982-be09-31fbb67866b5 | F3BA4A2F-9CB9-4982-BE09-31FBB67866B5 | ✓ |
| carlos@alpuntoycoma.mx | 9dd2a053-4473-454a-b871-b257361f4701 | 9DD2A053-4473-454A-B871-B257361F4701 | ✓ |
| eduardo@alpuntoycoma.mx | 12d4041c-f013-4414-bd96-592e9d61559c | 12D4041C-F013-4414-BD96-592E9D61559C | ✓ |

**Nota:** Los UUIDs son idénticos (solo difieren en mayúsculas/minúsculas por el cast SQL). La función de comparación normaliza ambos valores.

### Roles:
| Email | Rol MongoDB | Rol SQL | Mapeo |
|-------|-------------|---------|-------|
| admin@edarsa.com | Administrador | ADMIN | ✓ |
| admin@inventario.com | SuperAdministrador | SUPERADMIN | ✓ |
| carlosruz@edarsa.com.mx | Administrador | ADMIN | ✓ |
| noxte@alpyc.com | Supervisor | SUPERVISOR | ✓ |
| auditoria@edarsa.com.mx | Usuario | USUARIO | ✓ |
| almacen@cienfuegos.mx | Usuario | USUARIO | ✓ |
| administracion@cienfuegos.mx | Supervisor | SUPERVISOR | ✓ |
| ricardo@edarsa.com.mx | SuperAdministrador | SUPERADMIN | ✓ |
| david.ricardez@cienfuegos.mx | Usuario | USUARIO | ✓ |
| carlos@alpuntoycoma.mx | Administrador | ADMIN | ✓ |
| eduardo@alpuntoycoma.mx | Administrador | ADMIN | ✓ |

### Empresas:
| Email | Rol | Empresas Mongo | Empresas SQL | Estado |
|-------|-----|----------------|--------------|--------|
| admin@edarsa.com | ADMIN | 5 | 5 | ✓ |
| admin@inventario.com | SUPERADMIN | 5 | 5 (implícito) | ✓ |
| carlosruz@edarsa.com.mx | ADMIN | 5 | 5 | ✓ |
| noxte@alpyc.com | SUPERVISOR | 5 | 5 | ✓ |
| auditoria@edarsa.com.mx | USUARIO | 5 | 5 | ✓ |
| almacen@cienfuegos.mx | USUARIO | 1 | 1 | ✓ |
| administracion@cienfuegos.mx | SUPERVISOR | 1 | 1 | ✓ |
| ricardo@edarsa.com.mx | SUPERADMIN | 0 | 5 (implícito) | ✓ Regla SUPERADMIN |
| david.ricardez@cienfuegos.mx | USUARIO | 0 | 0 | ⚠️ Sin empresas |
| carlos@alpuntoycoma.mx | ADMIN | 0 | 0 | ⚠️ Sin empresas |
| eduardo@alpuntoycoma.mx | ADMIN | 0 | 0 | ⚠️ Sin empresas |

---

## 5. Validación Regla SUPERADMIN

### Definición:
> Si el usuario tiene rol `SUPERADMIN`, tiene acceso global implícito a todas las empresas activas sin necesidad de asignación explícita en `Usuario_EmpresasAsignacion`.

### Resultado:
| SUPERADMIN | Total Empresas Activas | Empresas Resueltas | Regla Aplicada |
|------------|------------------------|-------------------|----------------|
| admin@inventario.com | 5 | 5 | ✓ SÍ |
| ricardo@edarsa.com.mx | 5 | 5 | ✓ SÍ |

**Comportamiento correcto:** `ricardo@edarsa.com.mx` tiene 0 empresas en MongoDB pero resuelve 5 en SQL gracias a la regla SUPERADMIN.

---

## 6. Usuarios Sin Empresas Permitidas

Los siguientes usuarios **NO tienen `empresas_permitidas`** en MongoDB ni en SQL:

| Email | Rol SQL | Empresas SQL | Acción Recomendada |
|-------|---------|--------------|-------------------|
| david.ricardez@cienfuegos.mx | USUARIO | 0 | Asignar CIENFUEGOS o desactivar |
| carlos@alpuntoycoma.mx | ADMIN | 0 | Asignar empresas o desactivar |
| eduardo@alpuntoycoma.mx | ADMIN | 0 | Asignar empresas o desactivar |

**Nota:** Estos usuarios pueden autenticarse pero tendrán acceso limitado o nulo a datos de negocio. **Requieren decisión del propietario del sistema.**

---

## 7. Evidencia de No Regresión

### Endpoints verificados:

| Endpoint | Estado | Resultado |
|----------|--------|-----------|
| `GET /api/auth/me` | ✓ OK | Email, Role, 5 empresas |
| `GET /api/servers` | ✓ OK | 8 servidores |
| `GET /api/v2/comercial/dashboard` | ✓ OK | 4 unidades |
| Login con JWT | ✓ OK | Token genera y valida correctamente |

### JWT no cambió:
```json
{
  "user_id": "0da77b7b-fe88-4e23-98bc-9cbf543d5ee3",
  "email": "admin@inventario.com",
  "role": "SuperAdministrador",
  "exp": 1778982253
}
```

### MongoDB sigue siendo fuente productiva:
- `get_current_user()` sin modificar
- `login()` sin modificar
- Todas las consultas de autenticación van a `db.users`

---

## 8. Riesgos Residuales

| Riesgo | Mitigación | Severidad |
|--------|------------|-----------|
| UUIDs difieren en case (mayús/minús) | Normalizar comparación con `.upper()` | Baja |
| 3 usuarios sin empresas | Documentados, requieren decisión | Media |
| SUPERADMIN sin empresas en Mongo | Resuelto con regla implícita | Mitigado |
| DuplicateKeyError RBAC | Issue existente (RBAC-DUPKEY-001), no relacionado | Conocido |

---

## 9. Logging Seguro

### Campos que SÍ se loggean:
- `email`
- `auth_source` (MONGODB_CURRENT)
- `auth_sql_ready` (true/false)
- `auth_sql_diff` (true/false)
- `empresas_count` (número, no UUIDs)
- `has_password_hash` (true/false)

### Campos que NO se loggean:
- `password` (hash bcrypt)
- `token` (JWT completo)
- UUIDs de empresas (solo conteos)

---

## 10. Checklist para Autorizar FASE 2-E

| # | Criterio | Estado |
|---|----------|--------|
| 1 | Feature flag `AUTH_SQL_FIRST_ENABLED` existe | ✅ |
| 2 | Feature flag está apagado (false) | ✅ |
| 3 | 11/11 usuarios resuelven en SQL | ✅ |
| 4 | PublicUUID == MongoDB id (normalizado) | ✅ |
| 5 | Regla SUPERADMIN funciona (2/2) | ✅ |
| 6 | Usuarios sin empresas documentados (3) | ✅ |
| 7 | JWT payload sin cambios | ✅ |
| 8 | `get_current_user` sin modificar | ✅ |
| 9 | Login productivo intacto | ✅ |
| 10 | Endpoints críticos funcionan | ✅ |
| 11 | Logging no expone secretos | ✅ |
| 12 | Reporte FASE 2-D.1 generado | ✅ |

### Para activar FASE 2-E se requiere:

1. **Autorización explícita** del propietario del sistema
2. Modificar `get_current_user()` para:
   - Primero consultar SQL (`AuthRepositorySQL.get_user_by_public_uuid_sql()`)
   - Si SQL falla, fallback a MongoDB
   - Loggear fuente usada
3. Cambiar `AUTH_SQL_FIRST_ENABLED=true` (solo después de autorización)
4. Período de observación de fallbacks

---

## 11. Archivos de Referencia

| Archivo | Descripción |
|---------|-------------|
| `/app/backend/.env` | Feature flag AUTH_SQL_FIRST_ENABLED=false |
| `/app/backend/core/security.py` | Funciones de preflight agregadas |
| `/app/backend/core/auth/user_repository_sql.py` | Repositorio SQL paralelo |
| `/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md` | Reporte FASE 2-D |

---

## 12. Criterios de Aceptación

| Criterio | Estado |
|----------|--------|
| El sistema sigue autenticando productivamente con MongoDB | ✅ |
| SQL-first queda preparado pero apagado | ✅ |
| No cambia el comportamiento productivo | ✅ |
| No cambia JWT | ✅ |
| No cambia frontend | ✅ |
| Hay comparación pasiva MongoDB vs SQL | ✅ |
| Se generó el reporte | ✅ |

---

*Reporte generado bajo régimen de Autorización Controlada.*  
*MongoDB sigue siendo la fuente productiva. SQL-first listo pero apagado.*  
*Siguiente paso: Autorización para FASE 2-E.*
