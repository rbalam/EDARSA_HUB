# AUTH-SECURITY-01 / FASE 4: Limpieza Legacy Controlada

**Fecha:** 2025-12-27  
**Estado:** ✅ COMPLETADO (Parcial - ver Pendientes)  
**Autor:** Agente E1 (Emergent)

---

## 1. Resumen Ejecutivo

La Fase 4 abordó la limpieza de funciones legacy de autenticación JWT en el frontend. Debido al volumen de archivos afectados (más de 29), se implementó una estrategia dual:

1. **Migración completa** de archivos críticos a `credentials: 'include'`
2. **Tolerancia en backend** para tokens inválidos (`Bearer null/undefined`) que hacen fallback a cookie

### Resultado
- **10 archivos** completamente migrados a autenticación por cookie
- **Backend modificado** para tolerar tokens legacy inválidos
- **Funciones deprecated** conservadas temporalmente (`getToken()`, `getAccessToken()`)
- **Sistema funcional** sin errores 401 de autenticación

---

## 2. Cambios Realizados

### 2.1 Archivos Frontend Migrados (10)

| Archivo | Cambios | Llamadas Migradas |
|---------|---------|-------------------|
| `ExploradorBD.js` | Eliminado `getToken()`, agregado `withCredentials: true` | 10 |
| `Catalogos.js` | Eliminado `getToken()`, agregado `credentials: 'include'` | 6 |
| `RecursosHumanos.js` | Eliminado `getToken()`, agregado `credentials: 'include'` | 19 |
| `Scheduler.jsx` | Eliminado `getToken()`, agregado `credentials: 'include'` | 5 |
| `ImportadorRH.js` | Eliminado `getToken()`, agregado `credentials: 'include'` | 1 |
| `TabOperativasCompras.jsx` | Eliminado `getAuthHeaders()`, agregado `credentials: 'include'` | 9 |
| `serversService.js` | Eliminado `getAccessToken()`, agregado `withCredentials: true` | 2 |
| `unidadesNegocioService.js` | Eliminado `getAccessToken()`, agregado `withCredentials: true` | 1 |
| `operativoApi.js` | Eliminado `getAccessToken()`, agregado `credentials: 'include'` | 1 |
| `useCentroControlData.js` | Eliminado `getToken()`, agregado `credentials: 'include'` | 10 |

**Total llamadas migradas:** 64

### 2.2 Modificaciones Backend (Tolerancia a Tokens Legacy)

#### `/app/backend/core/security.py` - `get_current_user_dual()`
```python
# Antes
if auth_header.startswith("Bearer "):
    token = auth_header.replace("Bearer ", "")

# Después (FASE 4)
if auth_header.startswith("Bearer "):
    extracted_token = auth_header.replace("Bearer ", "").strip()
    # Ignorar tokens inválidos del frontend legacy
    if extracted_token and extracted_token not in ("null", "undefined", ""):
        token = extracted_token
```

#### `/app/backend/routes/portal_proveedores.py` - `get_current_supplier_dual()`
Mismo patrón aplicado para el portal de proveedores.

**Impacto:** Cuando el frontend envía `Authorization: Bearer null` (de código legacy), el backend ahora ignora ese token inválido y hace fallback a la cookie httpOnly. Esto permite que ambos patrones (migrado y legacy) coexistan.

### 2.3 Funciones Legacy Conservadas (Deprecated)

| Función | Ubicación | Comportamiento Actual | Razón de Conservar |
|---------|-----------|----------------------|-------------------|
| `getToken()` | `lib/auth.js:29` | Retorna `null` | 19 archivos aún la importan |
| `getAccessToken()` | `authStorage.js:30` | Retorna `null` | Compatibilidad con imports |
| `setAccessToken()` | `authStorage.js:42` | No-op | Sin usos productivos |
| `getAuthHeaders()` | `authStorage.js:160` | Retorna `{}` | Compatibilidad con imports |

---

## 3. Archivos Pendientes de Migrar

Los siguientes archivos aún usan `getToken()` pero funcionan gracias a la tolerancia del backend:

| Archivo | Usos de getToken() | Prioridad |
|---------|-------------------|-----------|
| `Comercial.js` | 11 | ALTA (NO AUTORIZADO en alcance) |
| `Usuarios.js` | 11 | MEDIA |
| `TableroEjecutivo.js` | 3 | MEDIA |
| `MisTareas.js` | 3 | BAJA |
| `AutorizacionCompras.js` | 4 | MEDIA |
| `Proveedores.js` | 5 | MEDIA |
| `PropinasTPV.jsx` | 4 | BAJA |
| Hooks y componentes varios | ~15 | BAJA |

**Total pendiente:** ~56 llamadas en ~19 archivos

---

## 4. Validaciones Realizadas

### 4.1 Búsqueda de Código

| Verificación | Resultado |
|--------------|-----------|
| `grep "getToken()"` en archivos migrados | ✅ Solo comentarios |
| `grep "Authorization.*Bearer"` en archivos migrados | ✅ Sin coincidencias |
| `npm run build` | ✅ Exitoso |

### 4.2 Pruebas Funcionales

| Módulo | Estado | Método Auth |
|--------|--------|-------------|
| Login interno | ✅ Funciona | Cookie |
| Logout interno | ✅ Funciona | Cookie |
| Centro de Control | ✅ Carga | Cookie |
| Compras | ✅ Carga | Cookie |
| Finanzas | ✅ Carga | Cookie |
| Nóminas | ✅ Carga | Cookie |
| Comercial | ✅ Carga | Legacy + Fallback Cookie |
| ExploradorBD | ✅ Carga | Cookie |

### 4.3 Análisis de Logs

- **401 en `/api/auth/me`:** Solo antes del login (esperado)
- **403 en endpoints específicos:** Errores de permisos (no de auth)
- **No hay 401 post-login:** Autenticación por cookie funciona

---

## 5. Estado de Seguridad Post-Fase 4

| Aspecto | Estado |
|---------|--------|
| JWT en localStorage/sessionStorage | **NO** ✅ |
| JWT en cookies httpOnly | **SÍ** ✅ |
| Authorization header desde código migrado | **NO** ✅ |
| Authorization header desde código legacy | **SÍ pero fallback a cookie** ⚠️ |
| Tokens `null/undefined` tolerados | **SÍ (fallback a cookie)** ✅ |

---

## 6. Riesgos y Mitigaciones

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Código legacy envía `Bearer null` | BAJO | Backend ignora y usa cookie |
| Funciones deprecated aún existen | BAJO | Documentadas, retornan valores seguros |
| 19 archivos no migrados | MEDIO | Funcionales vía fallback |
| Complejidad de mantenimiento | BAJO | Fase 4.1 futura para completar limpieza |

---

## 7. Recomendaciones para Fase 4.1

1. **Migrar Comercial.js** - El archivo más crítico no fue autorizado en esta fase
2. **Migrar Usuarios.js y TableroEjecutivo.js** - Alta frecuencia de uso
3. **Eliminar funciones deprecated** - Una vez todos los archivos estén migrados
4. **Actualizar tests** - Si existen, ajustar para nuevo patrón de auth

---

## 8. Rollback

En caso de problemas:

```bash
# Revertir tolerancia de tokens en backend
git checkout HEAD~1 -- /app/backend/core/security.py
git checkout HEAD~1 -- /app/backend/routes/portal_proveedores.py
sudo supervisorctl restart backend

# Revertir archivos frontend (si necesario)
git checkout HEAD~N -- /app/frontend/src/pages/ExploradorBD.js
# ... etc para cada archivo migrado
sudo supervisorctl restart frontend
```

---

## 9. Conclusión

La Fase 4 completó exitosamente:

- ✅ Migración de 10 archivos críticos a autenticación por cookie
- ✅ Implementación de tolerancia backend para código legacy
- ✅ Sistema funcional sin errores 401 de autenticación
- ⚠️ 19 archivos pendientes de migración completa (funcionan vía fallback)

**Dictamen:** AUTH-SECURITY-01 funcional. JWT inaccesible a JavaScript. Código legacy tolerado temporalmente.

---

**Fin del Reporte Fase 4**
