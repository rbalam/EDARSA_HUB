# FASE 16 - EVIDENCIA DE CIERRE
## Aplicación de Alcance Organizacional Real en GET /api/users

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** COMPLETADO  
**Tipo:** Implementación Controlada - Piloto Módulo Sistema

---

## 1. RESUMEN EJECUTIVO

FASE 16 implementó exitosamente el **primer filtrado real** por alcance organizacional (`sec_roles_alcance`) en el endpoint `GET /api/users`.

**RESULTADO:** Un usuario con alcance EMPRESA: CIENFUEGOS ahora solo ve usuarios de esa empresa (2 usuarios), mientras que SuperAdmin sigue viendo todos (30 usuarios).

---

## 2. ARCHIVOS CREADOS/MODIFICADOS

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `/app/backend/core/alcance_helper.py` | **NUEVO** - Helper de resolución de alcance | 130 |
| `/app/backend/modules/auth/service.py` | Modificado `get_users()` para aplicar filtrado | +20 |
| `/app/backend/modules/auth/repository.py` | Agregado `get_users_by_empresas()` | +15 |

---

## 3. ARCHIVOS NO MODIFICADOS (CONFIRMACIÓN)

| Archivo | Estado |
|---------|--------|
| `rbac_helper.py` | ✅ NO MODIFICADO |
| `get_current_user()` | ✅ NO MODIFICADO |
| `server.py` | ✅ NO MODIFICADO |
| `Layout.js` | ✅ NO MODIFICADO |
| `Usuarios.js` | ✅ NO MODIFICADO |
| Router global | ✅ NO MODIFICADO |
| Middleware global | ✅ NO MODIFICADO |
| Auth global | ✅ NO MODIFICADO |

---

## 4. POLÍTICA DE RESOLUCIÓN IMPLEMENTADA

```
ORDEN DE RESOLUCIÓN:
1. SuperAdministrador → ACCESO GLOBAL (sin filtro)
2. sec_roles_alcance con tipo GLOBAL → ACCESO GLOBAL
3. sec_roles_alcance con tipo EMPRESA → filtrar por empresa_id
4. sec_roles_alcance con tipo UNIDAD → filtrar por empresas de unidades
5. sec_roles_alcance con tipo SUCURSAL → filtrar por empresas de sucursales
6. Sin sec_roles_alcance → FALLBACK a empresas_permitidas
7. Sin nada válido → conjunto vacío

REGLA DE COMBINACIÓN:
Si usuario tiene múltiples roles con distintos alcances → UNIÓN de empresas
```

---

## 5. PRUEBAS EJECUTADAS

### 5.1 Filtrado por Alcance

| Usuario | Alcance | Usuarios Visibles | Esperado | Resultado |
|---------|---------|-------------------|----------|-----------|
| `ricardo@edarsa.com.mx` (SuperAdmin) | N/A | 30 | Todos | ✅ PASS |
| `test@edarsa.com` | EMPRESA: CIENFUEGOS | 2 | Solo CIENFUEGOS | ✅ PASS |

### 5.2 Protección RBAC Existente

| Usuario | Permiso | Resultado | Estado |
|---------|---------|-----------|--------|
| Usuario sin `SISTEMA_USUARIOS_VER` | Ninguno | HTTP 403 | ✅ PASS |

### 5.3 No Regresión

| Endpoint/Funcionalidad | Resultado |
|------------------------|-----------|
| GET /api/roles | ✅ 6 roles |
| GET /api/admin/bitacora | ✅ 55 registros |
| GET /api/admin/perfiles | ✅ 5 perfiles |
| Dashboard Comercial | ✅ Funciona |
| Login | ✅ Funciona |
| FASE 9-14 | ✅ Sin regresiones |

---

## 6. EVIDENCIA DE FILTRADO

### 6.1 SuperAdmin (30 usuarios)

```bash
curl -X GET "$API_URL/api/users" -H "Authorization: Bearer $SA_TOKEN"
# Resultado: 30 usuarios
```

### 6.2 Usuario con Alcance CIENFUEGOS (2 usuarios)

```bash
curl -X GET "$API_URL/api/users" -H "Authorization: Bearer $TEST_TOKEN"
# Resultado: 2 usuarios
# - almacen@cienfuegos.mx
# - administracion@cienfuegos.mx
```

---

## 7. USUARIOS POR EMPRESA (VERIFICACIÓN)

| Empresa | Usuarios |
|---------|----------|
| CIENFUEGOS | 2 |
| ORIGEN | 14 |
| 130 QRO | 0 |
| Otras | 14 |
| **TOTAL** | **30** |

---

## 8. COMPATIBILIDAD PRESERVADA

| Elemento | Estado |
|----------|--------|
| `users.role` | ✅ Intacto |
| `users.rbac_role` | ✅ Intacto |
| `users.sec_permisos` | ✅ Intacto |
| `users.sec_roles` | ✅ Intacto |
| `users.sec_perfil` | ✅ Intacto |
| `users.sec_roles_alcance` | ✅ AHORA SE APLICA (solo GET /api/users) |
| `allowed_servers` | ✅ Intacto (no usado en este endpoint) |
| `allowed_sucursales` | ✅ Intacto |
| `allowed_warehouses` | ✅ Intacto |
| `empresas_permitidas` | ✅ Usado como fallback |

---

## 9. ROLLBACK

### Procedimiento

```bash
# 1. Revertir service.py a llamar repo.get_all_users() directamente
# 2. Eliminar import de alcance_helper
# 3. Eliminar función get_users_by_empresas() de repository.py
# 4. Eliminar /app/backend/core/alcance_helper.py
```

**Tiempo estimado:** 5 minutos

---

## 10. LO QUE NO SE IMPLEMENTÓ (CONFIRMACIÓN)

| Elemento | Estado |
|----------|--------|
| Filtrado en PUT /api/users | ❌ NO implementado |
| Filtrado en DELETE /api/users | ❌ NO implementado |
| Filtrado en POST /api/users | ❌ NO implementado |
| Filtrado en /api/roles | ❌ NO implementado |
| Filtrado en módulos operativos | ❌ NO implementado |
| Modificación de `rbac_helper.py` | ❌ NO modificado |
| Modificación de frontend | ❌ NO modificado |

---

## 11. CONCLUSIÓN

FASE 16 completada exitosamente bajo el alcance autorizado:
- Filtrado real por `sec_roles_alcance` implementado en `GET /api/users`
- SuperAdmin sigue viendo todos los usuarios
- Usuarios con alcance específico ven solo usuarios de su alcance
- Fallback a `empresas_permitidas` funciona correctamente
- Sin modificación de componentes transversales
- Sin regresiones detectadas
- Sistema legacy intacto

**FIN DEL DOCUMENTO DE EVIDENCIA FASE 16**
