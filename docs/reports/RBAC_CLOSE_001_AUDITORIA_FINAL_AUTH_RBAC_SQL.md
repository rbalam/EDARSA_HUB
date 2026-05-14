# RBAC-CLOSE-001: Auditoría Final de Cierre Auth/RBAC SQL

**Fecha:** 2026-05-14  
**Fase:** RBAC-CLOSE-001  
**Estado:** COMPLETADA  
**Autor:** Agente E1  
**Régimen:** Autorización Controlada

---

## 1. Estado Final Auth/RBAC

### HITO ALCANZADO:
**EDARSAHUB SQL es la fuente única productiva para el módulo Usuarios/Roles/Auth-RBAC operativo.**

| Componente | Estado | Fuente de Datos |
|------------|--------|-----------------|
| Login (`/api/auth/login`) | ✅ Migrado | EDARSAHUB SQL |
| `get_current_user()` | ✅ Migrado | EDARSAHUB SQL (via `_get_user_sql_only`) |
| `GET /api/users` | ✅ Migrado | EDARSAHUB SQL |
| `create_user()` | ✅ Migrado | EDARSAHUB SQL |
| `update_user()` | ✅ Migrado | EDARSAHUB SQL |
| `deactivate_user()` | ✅ Migrado | EDARSAHUB SQL |
| `PUT /api/users/{id}/permissions` | ✅ Migrado | EDARSAHUB SQL |
| Roles | ✅ Migrado | EDARSAHUB SQL (lectura) |
| Empresas permitidas | ✅ Migrado | EDARSAHUB SQL |
| `allowed_servers` | ✅ Migrado | EDARSAHUB SQL |
| `allowed_sucursales` | ✅ Migrado | EDARSAHUB SQL |
| `allowed_warehouses` | ✅ Migrado | EDARSAHUB SQL |

---

## 2. Operaciones Migradas a SQL

### Repository Functions (repository.py):
```python
find_user_by_email()    → delega a find_user_by_email_sql()
find_user_by_id()       → delega a find_user_by_id_sql()
create_user()           → delega a create_user_sql()
update_user()           → delega a update_user_sql()
deactivate_user()       → delega a deactivate_user_sql()
get_all_users()         → consulta directa a EDARSAHUB SQL
```

### Security Functions (security.py):
```python
get_current_user()      → usa _get_user_sql_only() (SQL-only, sin fallback MongoDB)
```

### Service Functions (service.py):
```python
update_user_permissions() → escribe directamente en tablas SQL:
    - Usuario_ServidoresAsignacion
    - Usuario_SucursalesAsignacion
    - Usuario_AlmacenesAsignacion
```

---

## 3. Evidencia GREP

### Referencias a db.users:
```
/app/backend/modules/auth/password_reset.py:190   ← FUERA DE ALCANCE (reset passwords)
/app/backend/modules/auth/password_reset.py:305   ← FUERA DE ALCANCE (reset passwords)
/app/backend/modules/auth/password_reset.py:316   ← FUERA DE ALCANCE (reset passwords)
/app/backend/modules/auth/context_service.py:44   ← FUERA DE ALCANCE (contexto UI)
/app/backend/modules/auth/context_service.py:135  ← FUERA DE ALCANCE (contexto UI)
/app/backend/modules/auth/context_service.py:194  ← FUERA DE ALCANCE (contexto UI)
/app/backend/core/auth/user_repository_sql.py:366 ← Función de comparación (no productiva)
```

### Referencias a AsyncIOMotorClient:
```
/app/backend/core/auth/user_repository_sql.py:354 ← Función de comparación (no productiva)
/app/backend/core/auth/user_repository_sql.py:363 ← Función de comparación (no productiva)
```

### Referencias a MONGODB_FALLBACK:
```
(ninguna encontrada) ✅
```

### repository.py (CRUD productivo):
```
grep -n "db\.users" /app/backend/modules/auth/repository.py
→ Sin referencias directas a db.users ✅
```

---

## 4. Usuario de Prueba

### Datos:
| Campo | Valor |
|-------|-------|
| Email | prueba.rbacg@edarsa.com.mx |
| PublicUUID | A0230819-64A2-4076-B3F9-2EF29E3764A9 |
| Estado en SQL | **DESACTIVADO** (Activo=0) |
| Estado en MongoDB | **NO EXISTE** |
| FechaModificacion | 2026-05-13 22:30:31 |
| ModifiedBy | RBAC-SCOPE-G |

### Acción tomada:
- ✅ Usuario desactivado en SQL durante RBAC-SCOPE-G
- ✅ Usuario NO fue creado en MongoDB (correcto)
- ✅ Usuario NO aparece en GET /api/users (filtrado por Activo=1)
- ✅ Usuario NO puede hacer login ("Usuario inactivo")

### Conclusión:
**El usuario de prueba NO queda activo productivo.** Permanece desactivado en SQL para auditoría.

---

## 5. Referencias MongoDB Residuales (Fuera del Alcance)

| Archivo | Uso | Clasificación | Prioridad Migración |
|---------|-----|---------------|---------------------|
| `password_reset.py` | Reset de passwords vía email | FUERA DE ALCANCE | P2 - Media |
| `context_service.py` | Contexto de UI/navegación | FUERA DE ALCANCE | P3 - Baja |
| `repository.py:get_all_users()` | Campos `sec_*` piloto | Metadatos no productivos | P4 - Muy baja |
| `user_repository_sql.py:compare_user_mongo_vs_sql()` | Diagnóstico | Función pasiva | No migrar |

### Justificación:
- **password_reset.py**: Flujo de recuperación de contraseña. No es CRUD de usuarios productivo.
- **context_service.py**: Proporciona contexto de UI para navegación. No afecta autenticación ni permisos.
- **Campos sec_***: Son metadatos de RBAC piloto, no permisos operativos productivos.

---

## 6. Validaciones Funcionales

| # | Validación | Resultado |
|---|-----------|-----------|
| 1 | Login funciona | ✅ |
| 2 | get_current_user usa SQL | ✅ (`_get_user_sql_only`) |
| 3 | GET /api/users devuelve 11 usuarios | ✅ |
| 4 | Crear usuario funciona en SQL | ✅ (probado en RBAC-SCOPE-G) |
| 5 | Actualizar usuario funciona en SQL | ✅ |
| 6 | Desactivar usuario funciona en SQL | ✅ |
| 7 | Guardar permisos funciona en SQL | ✅ (HTTP 200) |
| 8 | MongoDB no se modifica | ✅ |
| 9 | admin@inventario.com: 5 empresas, 8 servers | ✅ |
| 10 | ricardo@edarsa.com.mx: 5 empresas, SuperAdmin | ✅ |
| 11 | carlos@ y eduardo@ aparecen | ✅ |
| 12 | Usuarios @test.com no visibles | ✅ (0) |
| 13 | prueba.rbacg@edarsa.com.mx no activo | ✅ (desactivado) |
| 14 | /api/servers devuelve 8 servidores | ✅ |
| 15 | Tablero Ejecutivo carga | ✅ |
| 16 | Comercial V2 carga | ✅ |
| 17 | Finanzas carga | ✅ |
| 18 | Inventarios/Catálogos cargan | ✅ |
| 19 | No hay secretos ni hashes expuestos | ✅ |

---

## 7. Riesgos Residuales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| password_reset.py falla si MongoDB cae | Baja | Medio | Migrar a SQL en fase futura |
| context_service.py falla si MongoDB cae | Baja | Bajo | Migrar a SQL en fase futura |
| Campos sec_* no disponibles si MongoDB cae | Baja | Muy bajo | Son metadatos piloto, no críticos |

---

## 8. Recomendación Priorizada para Siguiente Fase

### Orden de migración recomendado:

| Prioridad | Fase | Descripción | Justificación |
|-----------|------|-------------|---------------|
| P1 | **FASE 3** | Empresas/Sucursales/Mapeos | Completa el módulo de contexto organizacional |
| P2 | password_reset.py | Reset de passwords a SQL | Elimina dependencia MongoDB en flujo de recuperación |
| P3 | context_service.py | Contexto de UI a SQL | Elimina dependencia MongoDB en navegación |
| P4 | FASE 4 | Reglas vivas de negocio | Requiere FASE 3 completada |
| P5 | FASE 5/6 | Eliminación total MongoDB | Solo después de migrar todo |

### Recomendación inmediata:
**Autorizar FASE 3 (Empresas/Sucursales/Mapeos)** como siguiente paso lógico para consolidar el contexto organizacional en SQL.

---

## Resumen Ejecutivo

| Aspecto | Estado |
|---------|--------|
| Auth/RBAC operativo independiente de MongoDB | ✅ |
| Usuario de prueba no activo productivo | ✅ |
| Referencias MongoDB residuales clasificadas | ✅ |
| Sin regresión funcional | ✅ |
| Reporte generado | ✅ |

### HITO CONFIRMADO:
> **EDARSAHUB SQL es la fuente única productiva para el módulo Usuarios/Roles/Auth-RBAC operativo.**

MongoDB ya NO participa en:
- Login
- Autenticación (get_current_user)
- Listado de usuarios
- CRUD de usuarios
- Gestión de permisos operativos (servers, sucursales, almacenes)
- Roles
- Empresas permitidas

MongoDB solo se usa para:
- Reset de passwords (fuera de alcance)
- Contexto de UI (fuera de alcance)
- Campos sec_* piloto (no productivos)
- Función de comparación diagnóstica (pasiva)

**FASE RBAC-CLOSE-001: COMPLETADA**
