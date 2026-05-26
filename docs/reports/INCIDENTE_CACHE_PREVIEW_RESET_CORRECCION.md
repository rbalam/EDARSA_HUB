# INCIDENTE P0-CACHE-PREVIEW - CORRECCIÓN IMPLEMENTADA

**Fecha:** 2026-05-26  
**Estado:** COMPLETADO

---

## 1. ARCHIVOS MODIFICADOS

### 1.1 Frontend (Nuevos)

| Archivo | Propósito |
|---------|-----------|
| `/app/frontend/src/lib/previewCacheUtils.js` | Utilidades de detección y limpieza de caché |

**Funciones implementadas:**
- `isPreviewMode()` - Detecta ambiente preview
- `getEnvironmentInfo()` - Info del ambiente
- `clearPreviewFrontendCache(options)` - Limpia cachés frontend
- `clearReactQueryCache(queryClient)` - Limpia React Query
- `clearCacheOnLogout()` - Limpia al cerrar sesión
- `clearPreviewBackendCache(api)` - Llama endpoint backend

### 1.2 Frontend (Modificados)

| Archivo | Cambio |
|---------|--------|
| `/app/frontend/src/contexts/AuthContext.jsx` | Integración de limpieza de caché |

**Cambios:**
1. Import de funciones de `previewCacheUtils.js`
2. `useEffect` inicial para limpiar caché al montar
3. `loginWithData()` limpia caché antes de login
4. `logout()` limpia caché al cerrar sesión
5. Llamada a `clearPreviewBackendCache()` para admin

### 1.3 Backend (Nuevos)

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/api/admin_cache.py` | Endpoints de administración de caché |

**Endpoints:**
- `GET /api/admin/cache/status` - Estado de cachés
- `POST /api/admin/cache/clear-preview` - Limpia cachés (solo preview)

### 1.4 Backend (Modificados)

| Archivo | Cambio |
|---------|--------|
| `/app/backend/server.py` | Registro del router admin_cache |

---

## 2. FUNCIÓN isPreviewMode()

```javascript
export function isPreviewMode() {
  // Variable explícita
  if (process.env.REACT_APP_PREVIEW_MODE === 'true') return true;
  
  // URL de preview de Emergent
  const hostname = window.location.hostname;
  if (hostname.includes('preview.emergentagent.com')) return true;
  if (hostname.includes('staging')) return true;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return true;
  
  return false;
}
```

---

## 3. LLAVES DE CACHÉ LIMPIADAS

### Frontend
```javascript
const EDARSA_CACHE_KEYS = [
  // Auth
  'edarsa_memory_token', 'auth_token', 'token', 'user',
  // Selecciones
  'selectedServer', 'selectedUnidadNegocio', 'selectedEmpresa',
  // Catálogos
  'servers', 'servidores', 'unidades', 'empresas',
  // Módulos
  'dashboard', 'comercial', 'finanzas', 'operaciones', 'catalogo', 'compras',
  // RBAC
  'rbac', 'permisos', 'permissions',
  // Filtros
  'filtros', 'filters', 'dateRange',
  // Otros
  'edarsa_', 'edarsahub_'
];
```

### Backend
```python
# Limpiados por clear-preview:
- _server_status_cache (core/db.py)
- context_resolver (si tiene caché)
- server_registry (si tiene caché)
- db_pool_cooldowns
```

---

## 4. VALIDACIONES REALIZADAS

| Validación | Resultado |
|------------|-----------|
| Frontend compila | ✅ OK |
| Backend arranca | ✅ OK |
| `GET /api/admin/cache/status` | ✅ `is_preview_mode: true` |
| `POST /api/admin/cache/clear-preview` | ✅ 3 cachés limpiados |
| `/api/servers` post-clear | ✅ 9 servidores |
| `/api/unidades-negocio` post-clear | ✅ 5 unidades |
| No MongoDB | ✅ Confirmado |
| No live connections | ✅ Confirmado |
| No secretos expuestos | ✅ Confirmado |

---

## 5. CONFIRMACIONES DE SEGURIDAD

| Aspecto | Estado |
|---------|--------|
| No afecta producción | ✅ Solo ejecuta si `isPreviewMode()=true` |
| No borra datos SQL | ✅ Solo limpia cachés en memoria |
| No expone secretos | ✅ Endpoints protegidos por RBAC |
| Token manejado correctamente | ✅ No se borra token activo post-login |
| No loop infinito | ✅ Marcador de sesión previene |

---

## 6. USO

### Automático (Frontend)
Al cargar la app en modo preview, se ejecuta automáticamente:
1. Limpieza de localStorage/sessionStorage
2. Limpieza de Browser Caches
3. Marcador de sesión para evitar repetición

### Manual (Admin)
```bash
# Status de cachés
curl -X GET /api/admin/cache/status \
  -H "Authorization: Bearer $TOKEN"

# Limpiar cachés (solo preview)
curl -X POST /api/admin/cache/clear-preview \
  -H "Authorization: Bearer $TOKEN"
```

---

## 7. LOGS ESPERADOS

### Frontend (Console)
```
[PREVIEW_CACHE_RESET] Initializing cache cleanup on app mount...
[PREVIEW_CACHE_RESET] localStorage cleared: 5 keys
[PREVIEW_CACHE_RESET] sessionStorage cleared: 2 keys
[PREVIEW_CACHE_RESET] Browser caches cleared: 0
[PREVIEW_CACHE_RESET] Cache cleanup completed
```

### Backend
```
[PREVIEW_CACHE_CLEAR] Requested by admin@inventario.com
[PREVIEW_CACHE_CLEAR] Server registry cache check - no persistent cache found
[PREVIEW_CACHE_CLEAR] Context resolver cache check - no persistent cache found
[PREVIEW_CACHE_CLEAR] DB pool cooldowns reset
[PREVIEW_CACHE_CLEAR] Completed: cleared=[...], failed=[...]
```

---

**Firmado:** E1 Agent  
**Estado:** CORRECCIÓN COMPLETADA Y VALIDADA
