# CIERRE PILOTO RBAC - EVIDENCIA
## Alcance Real en PUT y DELETE /api/users

**Fecha:** Diciembre 2025  
**Estado:** COMPLETADO  
**Tipo:** Implementación - Cierre de Piloto RBAC Operativo

---

## 1. RESUMEN EJECUTIVO

Se implementó exitosamente la validación de alcance organizacional real en:
- `PUT /api/users/{id}`
- `DELETE /api/users/{id}`

**RESULTADO:** Un usuario con alcance limitado solo puede editar/eliminar usuarios dentro de su alcance organizacional.

---

## 2. ARCHIVOS MODIFICADOS

| Archivo | Cambio | Tipo |
|---------|--------|------|
| `/app/backend/core/alcance_helper.py` | Agregada función `verificar_usuario_en_alcance()` | Adición mínima |
| `/app/backend/modules/auth/service.py` | Validación de alcance en `update_user()` y `delete_user()` | Modificación |

---

## 3. ARCHIVOS NO MODIFICADOS (CONFIRMACIÓN)

| Archivo | Estado |
|---------|--------|
| `rbac_helper.py` | ✅ NO MODIFICADO |
| `get_current_user()` / `security.py` | ✅ NO MODIFICADO |
| `server.py` | ✅ NO MODIFICADO |
| `Layout.js` | ✅ NO MODIFICADO |
| `Usuarios.js` | ✅ NO MODIFICADO |
| Router global | ✅ NO MODIFICADO |
| Middleware global | ✅ NO MODIFICADO |
| Auth global | ✅ NO MODIFICADO |

---

## 4. LÓGICA IMPLEMENTADA

```
PUT /api/users/{id} y DELETE /api/users/{id}:

1. Verificar permiso RBAC (SISTEMA_USUARIOS_EDITAR/ELIMINAR) o fallback legacy
2. Verificar jerarquía (_can_manage_user) - regla existente preservada
3. NUEVO: Verificar alcance organizacional:
   - SuperAdmin → permitido
   - Alcance GLOBAL → permitido
   - Alcance específico → solo si target.empresa_default_id IN actor.empresas_ids
   - Sin alcance → fallback a empresas_permitidas
   - Fuera de alcance → HTTP 403
```

---

## 5. PRUEBAS EJECUTADAS

### 5.1 Pruebas de Alcance

| # | Test | Resultado |
|---|------|-----------|
| 1 | SuperAdmin puede editar cualquier usuario | ✅ PASÓ |
| 2 | Usuario con alcance EMPRESA edita DENTRO de alcance | ✅ PASÓ |
| 3 | Usuario con alcance EMPRESA NO puede editar FUERA de alcance | ✅ PASÓ |
| 4 | Usuario con alcance EMPRESA NO puede eliminar FUERA de alcance | ✅ PASÓ |
| 5 | Usuario con alcance EMPRESA puede eliminar DENTRO de alcance | ✅ PASÓ |

### 5.2 Pruebas de No Regresión

| Funcionalidad | Resultado |
|---------------|-----------|
| GET /api/users | ✅ 11 usuarios |
| GET /api/roles | ✅ 6 roles |
| GET /api/admin/bitacora | ✅ 55 registros |
| Login | ✅ Funciona |
| Dashboard Comercial | ✅ OK |
| FASE 9-14 | ✅ Sin regresiones |

---

## 6. RESPUESTAS HTTP

### Edición fuera de alcance:
```json
{"detail": "No tiene alcance para modificar este usuario"}
```

### Eliminación fuera de alcance:
```json
{"detail": "No tiene alcance para eliminar este usuario"}
```

---

## 7. AUDITORÍA (LOGS)

```
PUT /api/users/{id} DENEGADO por alcance: actor=test@..., target=admin@..., razon=FUERA_DE_ALCANCE
PUT /api/users/{id} PERMITIDO: actor=test@..., target=almacen@..., razon=EN_ALCANCE (RBAC)
DELETE /api/users/{id} DENEGADO por alcance: actor=test@..., target=admin@..., razon=FUERA_DE_ALCANCE
DELETE /api/users/{id} PERMITIDO: actor=test@..., target=test_delete@..., razon=EN_ALCANCE (RBAC)
```

---

## 8. COMPATIBILIDAD PRESERVADA

| Elemento | Estado |
|----------|--------|
| `users.role` | ✅ Intacto |
| `users.sec_permisos` | ✅ Intacto |
| `users.sec_roles` | ✅ Intacto |
| `users.sec_roles_alcance` | ✅ Ahora operativo en PUT/DELETE |
| `allowed_*` | ✅ Intacto (no usado en estos endpoints) |
| `empresas_permitidas` | ✅ Usado como fallback |
| Jerarquía legacy (`_can_manage_user`) | ✅ Preservada |

---

## 9. ROLLBACK

### Procedimiento:
```bash
# 1. Eliminar validación de alcance en update_user() y delete_user()
# 2. Eliminar función verificar_usuario_en_alcance() de alcance_helper.py
# 3. Restaurar docstrings originales
```

**Tiempo estimado:** 5 minutos

---

## 10. CONCLUSIÓN

### PILOTO RBAC OPERATIVO ✅

El piloto RBAC está ahora **100% operativo** para gestión de usuarios:

| Endpoint | Permiso RBAC | Alcance Real | Estado |
|----------|--------------|--------------|--------|
| GET /api/users | ✅ SISTEMA_USUARIOS_VER | ✅ Filtrado | OPERATIVO |
| PUT /api/users/{id} | ✅ SISTEMA_USUARIOS_EDITAR | ✅ Validado | OPERATIVO |
| DELETE /api/users/{id} | ✅ SISTEMA_USUARIOS_ELIMINAR | ✅ Validado | OPERATIVO |
| POST /api/users | ✅ SISTEMA_USUARIOS_CREAR | ❌ Pendiente | Fase futura |

**Un usuario con alcance organizacional limitado ahora:**
- Solo VE usuarios de su alcance ✅
- Solo puede EDITAR usuarios de su alcance ✅
- Solo puede ELIMINAR usuarios de su alcance ✅

**FIN DEL DOCUMENTO DE CIERRE PILOTO RBAC**
