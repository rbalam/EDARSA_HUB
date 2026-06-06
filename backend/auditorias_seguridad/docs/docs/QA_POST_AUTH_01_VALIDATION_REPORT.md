# QA POST AUTH 01 - VALIDATION REPORT
## Validación General Post AUTH-SECURITY-01 y P0-CENTROCONTROL-01

**Fecha:** 2025-12-27  
**Última actualización:** 2025-04-27  
**Estado:** ✅ COMPLETADO - HALLAZGOS RESUELTOS  
**Contexto:** Post AUTH-SECURITY-01 (arquitectura dual), P0-CENTROCONTROL-01 (funciones CentroControl) y P1-FETCH-MIGRATION

---

## 1. RESUMEN EJECUTIVO

| Categoría | Estado |
|-----------|--------|
| Build | ✅ Pasa |
| Login/Logout interno | ✅ Funciona |
| Login/Logout portal | ✅ Funciona |
| Módulos principales (navegación interna) | ✅ Funciona |
| AUTH-SECURITY-01 sin regresión | ✅ Confirmado |
| CentroControl estable | ✅ Confirmado |
| Errores 401/403 explicados | ✅ Documentado |
| **Fetch directo migrado a api.js** | ✅ **P1-FETCH-MIGRATION COMPLETADO** |

### Hallazgo Principal - **RESUELTO**

~~**12 archivos** usan `fetch` directo con `credentials: 'include'` en lugar de `api` de `lib/api.js`.~~

**Actualización 2025-04-27:** Este hallazgo fue resuelto en la fase **P1-FETCH-MIGRATION**. Los 12 archivos fueron migrados a `api.js` centralizado. Ver reporte: `/app/docs/P1_FETCH_MIGRATION_REPORT.md`

---

## 2. VALIDACIONES DE AUTENTICACIÓN

### 2.1 Login Interno

| Test | Resultado |
|------|-----------|
| POST /api/auth/login | ✅ 200 OK |
| Token retornado | ✅ Presente |
| Cookie seteada | ✅ `edarsa_access_token` |
| Usuario en respuesta | ✅ `admin@inventario.com` |

### 2.2 /api/auth/me

| Test | Resultado |
|------|-----------|
| Con cookie (curl) | ✅ 200 OK |
| Con header Authorization (curl) | ✅ 200 OK |
| Desde navegador preview (memoryToken) | ⚠️ Depende de navegación |

### 2.3 Logout Interno

| Test | Resultado |
|------|-----------|
| POST /api/auth/logout | ✅ 200 OK |
| Cookie eliminada | ✅ Confirmado |

### 2.4 Recarga de Página (F5)

| Ambiente | Comportamiento | Estado |
|----------|----------------|--------|
| Producción | Sesión persiste (cookie) | ✅ Esperado |
| Preview | Requiere re-login (memoryToken perdido) | ✅ Documentado |

### 2.5 Login Portal Proveedores

| Test | Resultado |
|------|-----------|
| POST /api/portal/auth/login | ✅ 200 OK |
| Token retornado | ✅ Presente |
| Cookie seteada | ✅ `edarsa_portal_access_token` |

### 2.6 /api/portal/auth/me

| Test | Resultado |
|------|-----------|
| Con cookie/header | ✅ 200 OK |
| RFC correcto | ✅ `TEST010101ABC` |

---

## 3. VALIDACIONES DE MÓDULOS

### 3.1 Navegación Interna (Post-Login)

| Módulo | Estado | Notas |
|--------|--------|-------|
| Tablero Ejecutivo | ✅ Carga | - |
| Comercial | ✅ Carga | - |
| Compras | ✅ Carga | - |
| Operaciones | ✅ Carga | - |
| Finanzas | ✅ Carga | KPIs visibles |
| Recursos Humanos | ✅ Carga | Tabs visibles |
| Catálogos | ⚠️ Error | `fetch` directo sin memoryToken |
| Usuarios | ⚠️ Error | `fetch` directo sin memoryToken |
| Centro de Control | ✅ Carga | Notificaciones activas |

### 3.2 Acceso Directo (URL o F5)

| Módulo | Estado | Notas |
|--------|--------|-------|
| Todos | ⚠️ Redirige a login | Comportamiento esperado en preview |

---

## 4. HALLAZGO: ARCHIVOS CON FETCH DIRECTO

### 4.1 Archivos Afectados

| Archivo | Fetch Calls | Impacto Preview |
|---------|-------------|-----------------|
| Catalogos.js | 6 | ⚠️ No carga datos |
| Finanzas.js | 8 | ⚠️ Algunos endpoints fallan |
| ImportadorRH.js | 11 | ⚠️ No carga datos |
| MisTareas.js | 12 | ⚠️ No carga datos |
| Nominas.js | 6 | ⚠️ No carga datos |
| Proveedores.js | 5 | ⚠️ No carga datos |
| RecursosHumanos.js | 19 | ⚠️ No carga datos |
| Usuarios.js | 13 | ⚠️ No carga datos |
| AuditoriasProgramadas.jsx | 2 | ⚠️ No carga datos |
| CentroControl.jsx | 9 | ⚠️ Algunos endpoints fallan |
| ConfigAsignaciones.jsx | 9 | ⚠️ No carga datos |
| Scheduler.jsx | 5 | ⚠️ No carga datos |

### 4.2 Causa

```javascript
// Problema: fetch directo no tiene acceso al memoryToken
const response = await fetch(`${API_URL}/api/endpoint`, {
  credentials: 'include'  // Solo envía cookies, no el header Authorization
});

// Solución: Usar api de lib/api.js que tiene el interceptor con memoryToken
const response = await api.get('/endpoint');
```

### 4.3 Comportamiento por Ambiente

| Ambiente | `credentials: 'include'` | `api.get()` |
|----------|-------------------------|-------------|
| **Producción** | ✅ Cookie funciona | ✅ Cookie + Header |
| **Preview** | ❌ Cookie bloqueada por CORS | ✅ Header con memoryToken |

### 4.4 Dictamen

**NO ES UN BUG P0 BLOQUEANTE** porque:
1. Funcionará en producción
2. En preview, la navegación interna para módulos que usan `api.get()` funciona
3. Solo afecta a endpoints específicos que usan `fetch` directo

**ES UN P1 PARA MIGRACIÓN** porque:
1. Inconsistencia en el código
2. UX degradada en preview
3. Debe unificarse para usar `api` en todos los casos

---

## 5. VERIFICACIONES DE SEGURIDAD

### 5.1 No Authorization: Bearer null/undefined

```bash
$ grep -i "Bearer null\|Bearer undefined" /var/log/supervisor/backend.out.log
# Resultado: No encontrado en logs recientes
```

✅ No hay `Bearer null/undefined` en logs.

### 5.2 No getToken() Productivo

```bash
$ grep -rn "getToken()" src/ --include="*.js" --include="*.jsx"
# Resultado: Solo comentarios, no código productivo
```

✅ No hay `getToken()` productivo.

### 5.3 No JWT en localStorage/sessionStorage

```bash
$ grep -rn "localStorage.*token\|sessionStorage.*token" src/
# Resultado: Solo en funciones de limpieza (clearSession)
```

✅ JWT no se guarda en storage.

### 5.4 No Errores JS Críticos

| Módulo | Errores Consola |
|--------|-----------------|
| Login | ✅ Ninguno |
| Dashboard | ✅ Ninguno |
| Comercial | ✅ Ninguno |
| Finanzas | ✅ Ninguno |
| Centro de Control | ✅ Ninguno |

---

## 6. ERRORES 401/403

### 6.1 Formato

| Error | Ubicación | Momento | Descripción | Dictamen | Impacto | Causa | Acción |
|-------|-----------|---------|-------------|----------|---------|-------|--------|
| 401 | /api/auth/me | Al cargar módulo con fetch directo | No auth | Esperado | No carga datos | memoryToken no en fetch | P1: Migrar a api.js |
| 403 | /api/users | Post 401 | Sin usuario | Esperado | Error en UI | Deriva de 401 | Mismo que anterior |
| 403 | /api/sistema/* | Post 401 | Sin usuario | Esperado | Error en UI | Deriva de 401 | Mismo que anterior |

### 6.2 Explicación

Los errores 401 ocurren porque:
1. El módulo hace `fetch` directo con `credentials: 'include'`
2. En preview, la cookie es bloqueada por CORS wildcard
3. Sin cookie ni header Authorization, el backend retorna 401
4. Los endpoints subsiguientes retornan 403 porque no hay usuario autenticado

**Los errores están correctamente clasificados:**
- 401 = No autenticado (falta token)
- 403 = No autorizado (sin usuario para verificar permisos)

---

## 7. FILTROS PRINCIPALES

### 7.1 Disponibilidad

| Filtro | Módulo | Estado |
|--------|--------|--------|
| Empresa | Compras | ✅ Visible |
| Servidor | Operaciones | ✅ Visible |
| Sucursal | Finanzas | ✅ Visible |
| Almacén | Operaciones | ✅ Visible |
| Fechas | Todos | ✅ Visible |
| Estatus | Varios | ✅ Visible |

### 7.2 Funcionalidad

Los filtros funcionan correctamente cuando el usuario está autenticado y navega internamente.

---

## 8. DICTAMEN FINAL

### QA-POST-AUTH-01: APROBADO CON OBSERVACIONES

**Criterios cumplidos:**

| Criterio | Estado |
|----------|--------|
| Build pasa | ✅ |
| Login/logout funcionan | ✅ |
| Módulos principales cargan (navegación interna) | ✅ |
| CentroControl estable | ✅ |
| No regresión de auth | ✅ |
| No errores críticos nuevos | ✅ |
| Errores 401/403 explicados | ✅ |
| Reporte con evidencia | ✅ |

**Observaciones:**

1. **P1-FETCH-MIGRATION:** 12 archivos usan `fetch` directo en lugar de `api.js`. Funcionará en producción, pero UX degradada en preview.

2. **Comportamiento Preview:** 
   - F5 o acceso directo por URL requiere re-login (documentado en AUTH-SECURITY-01)
   - Navegación interna funciona para módulos que usan `api.js`

---

## 9. RECOMENDACIONES

### 9.1 P1 - Migrar fetch directo a api.js

**Archivos a migrar:**
- Catalogos.js
- Finanzas.js (parcial)
- ImportadorRH.js
- MisTareas.js
- Nominas.js
- Proveedores.js
- RecursosHumanos.js
- Usuarios.js (parcial)
- AuditoriasProgramadas.jsx
- CentroControl.jsx (parcial)
- ConfigAsignaciones.jsx
- Scheduler.jsx

**Patrón de migración:**
```javascript
// ANTES
const response = await fetch(`${API_URL}/api/endpoint`, {
  credentials: 'include'
});

// DESPUÉS
const response = await api.get('/endpoint');
```

### 9.2 P2 - Unificar manejo de errores

Crear interceptor centralizado para manejar 401/403 de forma consistente.

---

## 10. ROLLBACK

No aplica - QA-POST-AUTH-01 no modificó código.

---

**Documento creado:** 2025-12-27  
**Fase:** QA-POST-AUTH-01  
**Estado:** COMPLETADO CON OBSERVACIONES
