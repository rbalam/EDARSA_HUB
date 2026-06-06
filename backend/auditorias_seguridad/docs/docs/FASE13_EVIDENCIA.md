# FASE 13 - EVIDENCIA DE CIERRE
## Perfiles Predefinidos RBAC

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** COMPLETADO  
**Opción Implementada:** OPCIÓN A (Perfiles como Metadato)

---

## 1. RESUMEN EJECUTIVO

FASE 13 implementó perfiles predefinidos RBAC como metadato y atajo de asignación:
- 5 perfiles predefinidos en colección `sec_perfiles`
- Campo `sec_perfil` en users como referencia informativa
- `sec_roles` sigue siendo la fuente de verdad operativa
- Endpoints para asignar/retirar perfiles
- Selector de perfil en UI de usuarios
- Auditoría completa de operaciones

---

## 2. POLÍTICA DE CONVIVENCIA IMPLEMENTADA

```
REGLA APLICADA:
- Asignar perfil → Sobrescribe sec_roles con los roles exactos del perfil
- sec_perfil → Almacena código del perfil (metadato/trazabilidad)
- Retirar perfil → Limpia sec_perfil y sec_roles (usuario queda sin roles RBAC)
- NO hay mezcla híbrida perfil + roles manuales
- La resolución de permisos NO fue modificada (rbac_helper.py intacto)
```

---

## 3. PERFILES IMPLEMENTADOS

| Código | Nombre | Roles |
|--------|--------|-------|
| `PERFIL_VISOR_BASICO` | Visor Básico | `['VISOR_ESTRUCTURA']` |
| `PERFIL_VISOR_SISTEMA` | Visor Sistema | `['VISOR_ESTRUCTURA', 'VISOR_SISTEMA']` |
| `PERFIL_VISOR_COMPLETO` | Visor Completo | `['VISOR_ADMIN']` |
| `PERFIL_ADMIN_USUARIOS` | Admin Usuarios | `['VISOR_ADMIN', 'ADMIN_USUARIOS']` |
| `PERFIL_GESTOR_SISTEMA` | Gestor Sistema | `['GESTOR_SISTEMA']` |

---

## 4. ARCHIVOS MODIFICADOS/CREADOS

| Archivo | Cambio |
|---------|--------|
| `/app/backend/server.py` | +3 endpoints (GET perfiles, POST asignar, POST retirar) |
| `/app/backend/modules/auth/schemas.py` | +campo `sec_perfil` en modelo User |
| `/app/frontend/src/pages/Usuarios.js` | +selector de perfil, +funciones asignar/retirar |
| MongoDB `sec_perfiles` | Colección nueva con 5 perfiles |
| MongoDB `users` | +campo `sec_perfil` |

---

## 5. ENDPOINTS IMPLEMENTADOS

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/admin/perfiles` | GET | Lista perfiles disponibles |
| `/api/admin/perfiles/asignar` | POST | Asigna perfil a usuario |
| `/api/admin/perfiles/retirar` | POST | Retira perfil de usuario |

---

## 6. VALIDACIONES EJECUTADAS

### 6.1 Perfiles Disponibles

| Test | Resultado |
|------|-----------|
| GET /api/admin/perfiles | ✅ 5 perfiles devueltos |
| PERFIL_VISOR_BASICO roles | ✅ ['VISOR_ESTRUCTURA'] |
| PERFIL_VISOR_SISTEMA roles | ✅ ['VISOR_ESTRUCTURA', 'VISOR_SISTEMA'] |
| PERFIL_VISOR_COMPLETO roles | ✅ ['VISOR_ADMIN'] |
| PERFIL_ADMIN_USUARIOS roles | ✅ ['VISOR_ADMIN', 'ADMIN_USUARIOS'] |
| PERFIL_GESTOR_SISTEMA roles | ✅ ['GESTOR_SISTEMA'] |

### 6.2 Asignación de Perfiles

| Test | Resultado |
|------|-----------|
| Asignar PERFIL_VISOR_BASICO | ✅ sec_roles = ['VISOR_ESTRUCTURA'] |
| Cambiar a PERFIL_ADMIN_USUARIOS | ✅ sec_roles = ['VISOR_ADMIN', 'ADMIN_USUARIOS'] |
| sec_perfil persistido | ✅ Correctamente guardado |
| Perfil anterior registrado | ✅ En auditoría |
| Roles anteriores registrados | ✅ En auditoría |

### 6.3 Retiro de Perfiles

| Test | Resultado |
|------|-----------|
| Retirar perfil | ✅ sec_perfil = null, sec_roles = [] |
| Auditoría de retiro | ✅ Registrada correctamente |

### 6.4 Auditoría

| Test | Resultado |
|------|-----------|
| Eventos ASIGNAR_PERFIL | ✅ 2 registros |
| Eventos RETIRAR_PERFIL | ✅ 1 registro |
| Datos de auditoría completos | ✅ Usuario, perfil, roles antes/después |

### 6.5 No Regresión

| Test | Resultado | HTTP |
|------|-----------|------|
| Login | ✅ | 200 |
| GET /api/users | ✅ | 200 |
| GET /api/roles | ✅ | 200 |
| GET /api/admin/bitacora | ✅ | 200 |
| Dashboard Comercial | ✅ | 200 |
| FASE 4-12 | ✅ Sin regresiones |

---

## 7. ARCHIVOS NO MODIFICADOS (Confirmación)

| Elemento | Estado |
|----------|--------|
| `rbac_helper.py` | ❌ NO MODIFICADO |
| `get_current_user()` | ❌ NO MODIFICADO |
| `Layout.js` | ❌ NO MODIFICADO |
| Router global | ❌ NO MODIFICADO |
| Middleware global | ❌ NO MODIFICADO |
| Auth global | ❌ NO MODIFICADO |
| Resolución de permisos | ❌ NO MODIFICADA |

---

## 8. COMPATIBILIDAD PRESERVADA

| Elemento | Compatibilidad |
|----------|---------------|
| `users.role` | ✅ Intacto |
| `users.rbac_role` | ✅ Intacto |
| `roles` | ✅ Intacto |
| `rbac_roles` | ✅ Intacto |
| `users.sec_permisos` | ✅ Intacto |
| `users.sec_rol` | ✅ Intacto |
| `users.sec_roles` | ✅ Actualizado por perfil, fuente de verdad |
| `sec_roles` | ✅ Intacto |
| `users.sec_perfil` | ✅ NUEVO campo (metadato) |

---

## 9. ROLLBACK

### Procedimiento

```bash
# 1. Eliminar endpoints de perfiles en server.py
# 2. Eliminar campo sec_perfil del schema User
# 3. Eliminar selector de perfil en Usuarios.js
# 4. Eliminar funciones handleAsignarPerfil/handleRetirarPerfil
# 5. Opcional: Limpiar sec_perfil de usuarios en MongoDB
# 6. Opcional: Eliminar colección sec_perfiles
```

### Tiempo Estimado

**7 minutos**

---

## 10. CHECKLIST DE NO REGRESIÓN

| # | Verificación | Estado |
|---|--------------|--------|
| 1 | Login funciona | ✅ |
| 2 | GET /api/users funciona | ✅ |
| 3 | GET /api/roles funciona | ✅ |
| 4 | GET /api/admin/bitacora funciona | ✅ |
| 5 | Dashboard Comercial funciona | ✅ |
| 6 | FASE 4-12 sin regresiones | ✅ |
| 7 | rbac_helper.py no modificado | ✅ |
| 8 | get_current_user() no modificado | ✅ |
| 9 | Layout.js no modificado | ✅ |
| 10 | Perfiles asignan roles correctamente | ✅ |
| 11 | Perfiles retiran roles correctamente | ✅ |
| 12 | Auditoría de perfiles funciona | ✅ |

---

## 11. CONCLUSIÓN

FASE 13 completada exitosamente bajo el alcance autorizado:
- 5 perfiles predefinidos implementados
- sec_roles sigue siendo fuente de verdad
- sec_perfil funciona como metadato/trazabilidad
- Auditoría completa de operaciones
- Sin modificación de resolución de permisos
- Sin regresiones detectadas
- Sin expansión de alcance

**FIN DEL DOCUMENTO DE EVIDENCIA FASE 13**
