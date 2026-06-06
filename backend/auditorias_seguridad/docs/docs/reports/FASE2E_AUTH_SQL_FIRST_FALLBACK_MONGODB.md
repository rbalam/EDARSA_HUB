# FASE 2-E: Auth SQL-First con Fallback MongoDB

**Fecha de ejecución:** 14-Dic-2025  
**Régimen:** Autorización Controlada  
**Estado:** ✅ COMPLETADA  
**Feature Flag:** `AUTH_SQL_FIRST_ENABLED=true`

---

## 1. Objetivo

Cambiar `get_current_user()` para usar SQL Server (EDARSAHUB) como fuente primaria de autenticación, manteniendo MongoDB como fallback obligatorio.

---

## 2. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/backend/core/security.py` | Modificado `get_current_user()` y `get_current_user_dual()` |
| `/app/backend/.env` | `AUTH_SQL_FIRST_ENABLED=true` |

### Funciones modificadas/agregadas:

| Función | Descripción |
|---------|-------------|
| `get_current_user()` | Ahora usa SQL-first con fallback MongoDB |
| `get_current_user_dual()` | Actualizada para usar misma lógica SQL-first |
| `_get_user_sql_first_with_fallback()` | Nueva función que implementa el flujo SQL→MongoDB |
| `_validate_sql_user_structure()` | Valida estructura mínima del usuario SQL |

---

## 3. Feature Flag

```bash
AUTH_SQL_FIRST_ENABLED=true
```

| Valor | Comportamiento |
|-------|---------------|
| `true` | SQL primero → MongoDB fallback |
| `false` | MongoDB directo (comportamiento legacy) |

**Rollback inmediato:** Cambiar a `false` y reiniciar backend.

---

## 4. Flujo SQL-First Implementado

```
Token JWT recibido
       │
       ▼
Extraer email, user_id
       │
       ▼
AUTH_SQL_FIRST_ENABLED?
       │
    ┌──┴──┐
    │true │false
    ▼     ▼
  SQL   MongoDB
  First  Directo
    │     │
    ▼     │
AuthRepositorySQL     │
.get_user_by_uuid()   │
    │                 │
    ▼                 │
¿Encontrado y válido? │
    │                 │
  ┌─┴─┐               │
  │Sí │No             │
  ▼   ▼               │
EDARSAHUB_SQL         │
    │   │             │
    │   ▼             │
    │ MongoDB Fallback│
    │   │             │
    │   ▼             │
    │ ¿Encontrado?    │
    │   │             │
    │ ┌─┴─┐           │
    │ │Sí │No         │
    │ ▼   ▼           │
    │ MONGODB_FALLBACK│
    │     │   │       │
    │     │   ▼       │
    │     │  404      │
    │     │           │
    └─────┴───────────┘
           │
           ▼
    Retornar usuario
```

---

## 5. Flujo Fallback MongoDB

El fallback se activa en estos casos:

| Caso | auth_source |
|------|-------------|
| Usuario no existe en SQL | `MONGODB_FALLBACK` |
| Error de conexión SQL | `SQL_ERROR_FALLBACK` |
| Estructura SQL inválida | `MONGODB_FALLBACK` |

### Garantías:
- Ningún error SQL bloquea el login
- MongoDB siempre está disponible como respaldo
- Todos los fallbacks quedan loggeados

---

## 6. Estructura del Usuario Devuelto

### Desde SQL (EDARSAHUB_SQL):
```json
{
  "id": "0DA77B7B-FE88-4E23-98BC-9CBF543D5EE3",
  "email": "admin@inventario.com",
  "name": "Admin Inventario",
  "nombre": "Admin Inventario",
  "role": "SuperAdministrador",
  "rol": "SuperAdministrador",
  "active": true,
  "activo": true,
  "password": "$2b$12$...",
  "empresas_permitidas": ["uuid1", "uuid2", "uuid3", "uuid4", "uuid5"],
  "empresa_default_id": "uuid1",
  "_sql_usuario_id": 1,
  "_sql_rol_codigo": "SUPERADMIN",
  "_source": "EDARSAHUB_SQL",
  "_fetched_at": "2025-12-14T01:55:00.000Z"
}
```

### Desde MongoDB (fallback):
```json
{
  "id": "0da77b7b-fe88-4e23-98bc-9cbf543d5ee3",
  "email": "admin@inventario.com",
  "name": "Admin Inventario",
  "role": "SuperAdministrador",
  "active": true,
  "password": "$2b$12$...",
  "empresas_permitidas": ["uuid1", "uuid2", "uuid3", "uuid4", "uuid5"],
  "empresa_default_id": "uuid1"
}
```

**Nota:** MongoDB no tiene campo `_source`.

---

## 7. Validación de PublicUUID como user['id']

| Usuario | ID en SQL | ID en Mongo | Formato |
|---------|-----------|-------------|---------|
| admin@inventario.com | 0DA77B7B-FE88-4E23-98BC-9CBF543D5EE3 | 0da77b7b-fe88-4e23-98bc-9cbf543d5ee3 | UUID ✓ |
| ricardo@edarsa.com.mx | 1E18A085-4092-40D8-AEFA-BBAFD1CDB939 | 1e18a085-4092-40d8-aefa-bbafd1cdb939 | UUID ✓ |
| almacen@cienfuegos.mx | 30702651-10A5-4E3A-9F83-245E2A52FEB7 | 30702651-10a5-4e3a-9f83-245e2a52feb7 | UUID ✓ |

**Diferencia:** SQL devuelve en MAYÚSCULAS, MongoDB en minúsculas. Ambos son UUIDs válidos.

---

## 8. Validación Regla SUPERADMIN

| SUPERADMIN | Empresas Mongo | Empresas SQL | Regla Aplicada |
|------------|----------------|--------------|----------------|
| admin@inventario.com | 5 | 5 | ✓ (explícitas) |
| ricardo@edarsa.com.mx | 0 | 5 | ✓ (implícitas) |

**Resultado:** `ricardo@edarsa.com.mx` ahora tiene acceso a las 5 empresas gracias a la regla SUPERADMIN implementada en SQL.

---

## 9. Pruebas con AUTH_SQL_FIRST_ENABLED=true

| Test | Resultado |
|------|-----------|
| GET /api/auth/me (admin@inventario.com) | ✓ `_source: EDARSAHUB_SQL` |
| GET /api/auth/me (ricardo@edarsa.com.mx) | ✓ 5 empresas, `_source: EDARSAHUB_SQL` |
| GET /api/auth/me (almacen@cienfuegos.mx) | ✓ 1 empresa, `_source: EDARSAHUB_SQL` |
| GET /api/servers | ✓ 8 servidores |
| GET /api/v2/comercial/dashboard | ✓ 4 unidades |

---

## 10. Pruebas con AUTH_SQL_FIRST_ENABLED=false

| Test | Resultado |
|------|-----------|
| GET /api/auth/me (admin@inventario.com) | ✓ Sin `_source` (MongoDB) |
| ID en respuesta | ✓ minúsculas (formato MongoDB) |
| Rollback inmediato | ✓ Funciona correctamente |

---

## 11. Prueba de Fallback Forzado

| Usuario | En SQL | En Mongo | Resultado |
|---------|--------|----------|-----------|
| superadmin2@test.com | ❌ | ✓ | ✓ Resuelto desde MongoDB (sin `_source`) |

**Comportamiento correcto:** Usuario que no está en SQL se resuelve desde MongoDB fallback.

---

## 12. Evidencia de No Regresión

| Endpoint | Estado |
|----------|--------|
| GET /api/auth/me | ✓ OK |
| GET /api/servers | ✓ 8 servidores |
| GET /api/v2/comercial/dashboard | ✓ 4 unidades |
| Login productivo | ✓ Sin cambios en flujo |
| JWT payload | ✓ Sin cambios (user_id, email, role, exp) |

---

## 13. Logging Seguro

### Campos loggeados:
```
[AUTH] auth_source=EDARSAHUB_SQL, email=admin@inventario.com, role=SuperAdministrador
[AUTH-FALLBACK] Usuario resuelto desde MongoDB: superadmin2@test.com, reason=MONGODB_FALLBACK
```

### Campos NO loggeados:
- `password` (hash bcrypt)
- `token` (JWT completo)
- UUIDs de empresas completos

---

## 14. Riesgos Residuales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| SQL Server no disponible | Media | Fallback MongoDB automático |
| Diferencia de case en UUIDs | Baja | JWT usa UUID del token, no del user |
| 3 usuarios sin empresas | Media | Documentados, requieren decisión |
| Usuarios @test.com no migrados | Baja | Resuelven vía fallback MongoDB |

---

## 15. Checklist para FASE 2-F (Observación)

| # | Criterio | Validado |
|---|----------|----------|
| 1 | Monitorear logs de `auth_source` | Pendiente |
| 2 | Identificar usuarios que usan fallback | Pendiente |
| 3 | Medir % de requests SQL vs MongoDB | Pendiente |
| 4 | Verificar que no hay errores SQL | Pendiente |
| 5 | Confirmar que SUPERADMIN funciona consistentemente | Pendiente |
| 6 | Documentar cualquier fallback inesperado | Pendiente |

---

## 16. Criterios de Aceptación

| Criterio | Estado |
|----------|--------|
| SQL-first funciona con fallback MongoDB | ✅ |
| MongoDB fallback sigue activo | ✅ |
| Rollback por feature flag funciona | ✅ |
| Login funciona | ✅ |
| JWT no cambia | ✅ |
| Tablero Ejecutivo funciona | ✅ |
| SUPERADMIN conserva acceso global | ✅ |
| Reporte generado | ✅ |

---

## 17. Próximos Pasos

### FASE 2-F: Período de Observación
- Monitorear logs de auth_source durante operación normal
- Identificar patrones de fallback
- Validar estabilidad con usuarios reales

### FASE 2-G: Eliminar Fallback MongoDB (Futuro)
- Solo después de período de observación exitoso
- Requiere autorización explícita
- Eliminar código de fallback

---

## 18. Archivos de Referencia

| Archivo | Descripción |
|---------|-------------|
| `/app/backend/.env` | `AUTH_SQL_FIRST_ENABLED=true` |
| `/app/backend/core/security.py` | Funciones modificadas |
| `/app/backend/core/auth/user_repository_sql.py` | Repositorio SQL |
| `/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md` | Reporte previo |

---

*Reporte generado bajo régimen de Autorización Controlada.*  
*SQL Server es ahora la fuente primaria de autenticación con fallback MongoDB activo.*
