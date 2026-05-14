# FASE 2-G: Eliminación de Fallback MongoDB en Auth/RBAC

**Fecha de ejecución:** 14-Dic-2025  
**Régimen:** Autorización Controlada  
**Estado:** ✅ COMPLETADA

---

## 1. Resumen Ejecutivo

Se eliminó el fallback MongoDB del flujo de autenticación. EDARSAHUB SQL es ahora la **única fuente de autenticación** para usuarios productivos.

| Métrica | Valor |
|---------|-------|
| Usuarios productivos autenticados | 11/11 |
| auth_source | EDARSAHUB_SQL |
| MONGODB_FALLBACK | 0 (eliminado) |
| SQL_ERROR_FALLBACK | 0 |
| Usuarios @test.com rechazados | 3/3 |

---

## 2. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/backend/core/security.py` | Eliminado fallback MongoDB de `get_current_user()` y `get_current_user_dual()` |

### Funciones modificadas:

| Función | Antes | Después |
|---------|-------|---------|
| `get_current_user()` | SQL-first con fallback MongoDB | SQL-only |
| `get_current_user_dual()` | SQL-first con fallback MongoDB | SQL-only |
| `_get_user_sql_first_with_fallback()` | Existía | **ELIMINADA** |
| `_get_user_sql_only()` | No existía | **NUEVA** |

---

## 3. Flujo Auth Anterior (FASE 2-E)

```
Token JWT recibido
       │
       ▼
AUTH_SQL_FIRST_ENABLED?
       │
    ┌──┴──┐
    │true │false
    ▼     ▼
  SQL   MongoDB
  First  Directo
    │     
    ▼     
¿Encontrado?
    │     
  ┌─┴─┐   
  │Sí │No 
  ▼   ▼   
 OK  MongoDB Fallback ← ELIMINADO
         │
         ▼
      Usuario
```

---

## 4. Flujo Auth Nuevo (FASE 2-G)

```
Token JWT recibido
       │
       ▼
Verificar JWT
       │
       ▼
Buscar en EDARSAHUB SQL
(AuthRepositorySQL)
       │
       ▼
¿Encontrado y activo?
       │
    ┌──┴──┐
    │Sí   │No
    ▼     ▼
   OK    401 Unauthorized
         "Usuario no autorizado"
```

**Sin fallback a MongoDB.**

---

## 5. Referencias MongoDB Eliminadas del Flujo Auth

| Referencia | Estado |
|------------|--------|
| `_get_user_sql_first_with_fallback()` | ✅ ELIMINADA |
| `MONGODB_FALLBACK` como auth_source | ✅ ELIMINADO |
| `SQL_ERROR_FALLBACK` como auth_source | ✅ ELIMINADO |
| Fallback a `db.users` en `get_current_user()` | ✅ ELIMINADO |
| Fallback a `db.users` en `get_current_user_dual()` | ✅ ELIMINADO |

---

## 6. Referencias MongoDB Residuales (Fuera de Auth)

Estas referencias quedan como **deuda técnica** para fases futuras:

| Archivo | Uso | Prioridad |
|---------|-----|-----------|
| `/app/backend/modules/auth/password_reset.py` | Reset de contraseña | Media |
| `/app/backend/modules/auth/context_service.py` | Servicio de contexto | Media |
| `/app/backend/core/auth/user_repository_sql.py` | Función de comparación (no productiva) | Baja |

**Nota:** Estas referencias no afectan el flujo principal de autenticación (`get_current_user`).

---

## 7. Validación Usuarios Productivos

| Usuario | auth_source | Empresas | Status |
|---------|-------------|----------|--------|
| admin@inventario.com | EDARSAHUB_SQL | 5 | ✅ OK |
| ricardo@edarsa.com.mx | EDARSAHUB_SQL | 5 | ✅ OK |
| almacen@cienfuegos.mx | EDARSAHUB_SQL | 1 | ✅ OK |
| administracion@cienfuegos.mx | EDARSAHUB_SQL | 1 | ✅ OK |
| david.ricardez@cienfuegos.mx | EDARSAHUB_SQL | 1 | ✅ OK |
| carlos@alpuntoycoma.mx | EDARSAHUB_SQL | 5 | ✅ OK |
| eduardo@alpuntoycoma.mx | EDARSAHUB_SQL | 5 | ✅ OK |
| admin@edarsa.com | EDARSAHUB_SQL | 5 | ✅ OK |
| carlosruz@edarsa.com.mx | EDARSAHUB_SQL | 5 | ✅ OK |
| noxte@alpyc.com | EDARSAHUB_SQL | 5 | ✅ OK |
| auditoria@edarsa.com.mx | EDARSAHUB_SQL | 5 | ✅ OK |

**Total: 11/11 usuarios productivos autenticando desde SQL**

---

## 8. Validación Usuarios @test.com Rechazados

| Usuario | HTTP Code | Mensaje | Status |
|---------|-----------|---------|--------|
| superadmin2@test.com | 401 | Usuario no autorizado | ✅ RECHAZADO |
| usuario_test_portal@test.com | 401 | Usuario no autorizado | ✅ RECHAZADO |
| superadmin@test.com | N/A | Sin UUID | ✅ N/A |

**Los usuarios @test.com no pueden autenticarse.**

---

## 9. Validación SUPERADMIN

| SUPERADMIN | Empresas | Regla Aplicada |
|------------|----------|----------------|
| admin@inventario.com | 5 | ✅ Acceso global implícito |
| ricardo@edarsa.com.mx | 5 | ✅ Acceso global implícito |

---

## 10. Validación JWT/PublicUUID

| Campo | Valor | Validación |
|-------|-------|------------|
| user['id'] | 0DA77B7B-FE88-4E23-98BC-9CBF543D5EE3 | ✅ Es UUID |
| Estructura JWT | user_id, email, role, exp | ✅ Sin cambios |
| UsuarioID SQL interno | No expuesto | ✅ Correcto |

---

## 11. Evidencia Grep

### db.users en Auth:
```bash
$ grep -R "db.users" /app/backend/core/security.py
# (Sin resultados - eliminado de security.py)

$ grep -R "db.users" /app/backend/modules/auth/
/app/backend/modules/auth/password_reset.py:    user = db.users.find_one(...)  # Fuera de flujo principal
/app/backend/modules/auth/context_service.py:    user = await db.users.find_one(...)  # Fuera de flujo principal
```

### MONGODB_FALLBACK:
```bash
$ grep -R "MONGODB_FALLBACK" /app/backend/core/ /app/backend/modules/auth/
# (Sin resultados)
```

### SQL_ERROR_FALLBACK:
```bash
$ grep -R "SQL_ERROR_FALLBACK" /app/backend/core/ /app/backend/modules/auth/
# (Sin resultados)
```

---

## 12. Evidencia de No Regresión

| Endpoint | Resultado |
|----------|-----------|
| GET /api/auth/me | ✅ OK (11 usuarios) |
| GET /api/servers | ✅ 8 servidores |
| GET /api/v2/comercial/dashboard | ✅ 4 unidades |
| GET /api/comercial/tablero-ejecutivo | ✅ OK |
| Usuarios @test.com | ✅ Rechazados (401) |
| SUPERADMIN | ✅ 5 empresas cada uno |

---

## 13. Rollback Técnico Documentado

### Si se necesita revertir a fallback MongoDB:

1. Restaurar la función `_get_user_sql_first_with_fallback()` en `security.py`
2. Cambiar `_get_user_sql_only()` por `_get_user_sql_first_with_fallback()` en:
   - `get_current_user()`
   - `get_current_user_dual()`
3. Reiniciar backend

### Código de rollback disponible en:
- Git history (commit anterior a FASE 2-G)
- `/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md` (documentación del flujo anterior)

---

## 14. Riesgos Residuales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Error SQL bloquea login | Baja | SQL Server altamente disponible. Logs de SQL_ERROR para monitoreo. |
| password_reset.py usa MongoDB | Media | Deuda técnica para fase futura. No afecta login. |
| context_service.py usa MongoDB | Media | Deuda técnica para fase futura. No afecta login. |

---

## 15. Recomendación para FASE 3

### Prerrequisitos cumplidos para FASE 3:

✅ Auth/RBAC migrado a SQL  
✅ Usuarios productivos usando EDARSAHUB_SQL  
✅ Fallback MongoDB eliminado de flujo principal  
✅ Regla SUPERADMIN funcionando  

### Siguiente paso recomendado:

**FASE 3: Migración de Empresas/Sucursales a SQL**

Scope sugerido:
1. Migrar `db.empresas` a `Sistema_Empresas`
2. Migrar `db.sucursales` a `Sistema_Sucursales`
3. Actualizar endpoints que leen de MongoDB
4. Mantener Sistema_EmpresasMongoMap como puente

---

## 16. Criterios de Aceptación

| Criterio | Estado |
|----------|--------|
| Auth/RBAC ya no usa MongoDB fallback | ✅ |
| 11/11 usuarios productivos autentican desde SQL | ✅ |
| Usuarios @test.com desactivados no pueden iniciar sesión | ✅ |
| No existe MONGODB_FALLBACK productivo | ✅ |
| SQL_ERROR_FALLBACK = 0 | ✅ |
| JWT no cambia | ✅ |
| SUPERADMIN conserva acceso global | ✅ |
| Módulos principales no presentan regresión | ✅ |
| Reporte generado | ✅ |

---

## 17. Conclusión

**FASE 2 COMPLETADA.**

La migración de Auth/RBAC de MongoDB a EDARSAHUB SQL ha sido completada exitosamente:

- ✅ DDL Auth/RBAC creado y validado
- ✅ Usuarios migrados a SQL
- ✅ Roles asignados
- ✅ Empresas mapeadas y asignadas
- ✅ Repositorio SQL implementado
- ✅ SQL-first activado
- ✅ Usuarios pendientes saneados
- ✅ **Fallback MongoDB eliminado**

**EDARSAHUB SQL es ahora la única fuente de autenticación productiva.**

---

*Reporte generado bajo régimen de Autorización Controlada.*  
*MongoDB ya no es parte del flujo de autenticación productivo.*
