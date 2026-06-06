# AUTH_HTTPONLY_COOKIE_MIGRATION_PLAN
## FASE AUTH-SECURITY-01 - Migracion de Autenticacion a httpOnly Cookies

**Fecha:** 2025-12-XX  
**Estado:** PLAN TECNICO (No implementado)  
**Objetivo:** Eliminar almacenamiento de JWT en sessionStorage/localStorage y mover sesion a cookies httpOnly Secure SameSite.

---

## 1. AUDITORIA DEL FLUJO ACTUAL

### 1.1 Arquitectura de Autenticacion Actual

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FLUJO ACTUAL (Vulnerable a XSS)              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Frontend]                              [Backend]                  │
│                                                                     │
│  POST /api/auth/login ──────────────────► login_user()             │
│  { email, password }                      │                         │
│                                           ▼                         │
│                                      create_token()                 │
│                                           │                         │
│  ◄────────────────────────────────────────┘                         │
│  { token: "eyJ...", user: {...} }                                   │
│       │                                                             │
│       ▼                                                             │
│  sessionStorage.setItem('token', token)  ◄─── VULNERABLE A XSS     │
│  localStorage.setItem('token', token)    ◄─── VULNERABLE A XSS     │
│                                                                     │
│  Requests subsecuentes:                                             │
│  axios.interceptors.request ────────────────────────────►           │
│  Authorization: Bearer {token}           get_current_user()         │
│                                          verify_token()             │
│                                                                     │
│  401 Unauthorized ◄──────────────────────────────────────           │
│       │                                                             │
│       ▼                                                             │
│  clearSession()                                                     │
│  redirect('/login')                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Archivos Involucrados

#### Backend (FastAPI)
| Archivo | Funcion | Modificacion Requerida |
|---------|---------|------------------------|
| `/app/backend/core/security.py` | `create_token()`, `verify_token()`, `get_current_user()` | Agregar manejo de cookies |
| `/app/backend/modules/auth/routes.py` | `/auth/login`, `/auth/me`, `/auth/logout` | Setear/eliminar cookies |
| `/app/backend/modules/auth/service.py` | `login_user()` | Retornar cookie en lugar de token en body |
| `/app/backend/routes/portal_proveedores.py` | `create_portal_token()`, `get_current_supplier()` | Agregar soporte cookies para portal |
| `/app/backend/server.py` | Configuracion CORS | Agregar `allow_credentials=True` |

#### Frontend (React)
| Archivo | Funcion | Modificacion Requerida |
|---------|---------|------------------------|
| `/app/frontend/src/services/authStorage.js` | `getAccessToken()`, `setAccessToken()`, `clearSession()` | Eliminar storage de token |
| `/app/frontend/src/contexts/AuthContext.jsx` | `login()`, `logout()`, estado | Ya no guardar token localmente |
| `/app/frontend/src/lib/api.js` | Interceptores axios | Configurar `withCredentials: true` |
| `/app/frontend/src/lib/auth.js` | `getToken()`, `isAuthenticated()` | Depender de /api/auth/me |
| `/app/frontend/src/pages/Login.js` | `handleLogin()` | No guardar token en storage |
| `/app/frontend/src/portal/App.jsx` | `handleLogin()`, `handleLogout()` | Adaptar a cookies |

### 1.3 Endpoints de Auth Identificados

| Endpoint | Metodo | Funcion | Cookie Requerida |
|----------|--------|---------|------------------|
| `/api/auth/login` | POST | Login usuario EDARSA | Set-Cookie |
| `/api/auth/me` | GET | Usuario actual | Read Cookie |
| `/api/auth/me/context` | GET | Contexto completo | Read Cookie |
| `/api/auth/context` | POST | Cambiar empresa/sucursal | Read Cookie |
| `/api/auth/empresas` | GET | Empresas permitidas | Read Cookie |
| `/api/auth/me/access-context` | GET | Contexto de acceso | Read Cookie |
| `/api/auth/me/menu-permissions` | GET | Permisos de menu | Read Cookie |
| `/api/portal/auth/login` | POST | Login proveedor | Set-Cookie (diferente nombre) |
| `/api/portal/auth/register` | POST | Registro proveedor | No cookie |
| `/api/portal/auth/me` | GET | Proveedor actual | Read Cookie |

### 1.4 Elementos que NO Deben Modificarse

- Logica de negocio de todos los modulos
- Menus y navegacion
- RBAC y permisos (solo el transporte del token cambia)
- Estructura de datos del usuario
- Filtros por empresa/sucursal/almacen
- MongoDB como fuente de datos
- EDARSAHUB (no moverlo como cerebro)

---

## 2. ARQUITECTURA PROPUESTA

### 2.1 Flujo con httpOnly Cookies

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUJO PROPUESTO (Seguro contra XSS)              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Frontend]                              [Backend]                  │
│                                                                     │
│  POST /api/auth/login ──────────────────► login_user()             │
│  { email, password }                      │                         │
│  credentials: 'include'                   ▼                         │
│                                      create_token()                 │
│                                           │                         │
│  ◄────────────────────────────────────────┘                         │
│  HTTP 200 + Set-Cookie: edarsa_token=eyJ...; HttpOnly; Secure;     │
│            SameSite=Strict; Path=/api; Max-Age=259200              │
│                                                                     │
│  { user: {...} }  ◄─── Solo datos usuario, SIN TOKEN               │
│       │                                                             │
│       ▼                                                             │
│  setUser(user)   ◄─── Solo guardar datos no sensibles              │
│  NO token en JS  ◄─── INACCESIBLE A XSS                            │
│                                                                     │
│  Requests subsecuentes:                                             │
│  axios con credentials: 'include' ──────────────────────►          │
│  Cookie: edarsa_token=eyJ...             get_current_user()         │
│                                          verify_cookie_token()      │
│                                                                     │
│  POST /api/auth/logout ─────────────────────────────────►          │
│  ◄─────────────────────── Set-Cookie: edarsa_token=; Max-Age=0     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Configuracion de Cookies

```python
# Configuracion recomendada para produccion
COOKIE_CONFIG = {
    "key": "edarsa_token",          # Nombre de la cookie
    "value": token,                  # JWT firmado
    "httponly": True,                # Inaccesible a JavaScript
    "secure": True,                  # Solo HTTPS (desactivar en dev)
    "samesite": "strict",            # Proteccion CSRF
    "path": "/api",                  # Solo enviar a rutas /api
    "max_age": 72 * 60 * 60,         # 72 horas (igual que JWT actual)
    "domain": None                   # Usar dominio actual
}

# Cookie separada para portal de proveedores
PORTAL_COOKIE_CONFIG = {
    "key": "portal_token",
    "httponly": True,
    "secure": True,
    "samesite": "strict",
    "path": "/api/portal",           # Solo rutas del portal
    "max_age": 24 * 60 * 60          # 24 horas (igual que portal actual)
}
```

### 2.3 Cambios en CORS

```python
# server.py - CORS actualizado
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://edarsa-hub.preview.emergentagent.com",
        "http://localhost:3000"  # Para desarrollo
    ],
    allow_credentials=True,  # CRITICO: Permitir cookies cross-origin
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 3. PLAN DE IMPLEMENTACION

### Fase 1: Backend - Soporte Dual (Token Header + Cookie)

**Objetivo:** Permitir que el backend acepte autenticacion tanto por header Authorization como por cookie, sin romper nada.

**Archivos a modificar:**
1. `core/security.py` - Nueva funcion `get_token_from_request()`
2. `modules/auth/routes.py` - Login retorna cookie + user (sin token en body)
3. `modules/auth/routes.py` - Nuevo endpoint `/auth/logout` (POST)
4. `routes/portal_proveedores.py` - Mismo patron para portal

**Codigo propuesto:**

```python
# core/security.py - Nuevo
from fastapi import Request, Response

def set_auth_cookie(response: Response, token: str, max_age: int = 259200):
    """Establece la cookie de autenticacion."""
    response.set_cookie(
        key="edarsa_token",
        value=token,
        httponly=True,
        secure=os.environ.get("ENV", "production") == "production",
        samesite="strict",
        path="/api",
        max_age=max_age
    )

def clear_auth_cookie(response: Response):
    """Elimina la cookie de autenticacion."""
    response.delete_cookie(
        key="edarsa_token",
        path="/api"
    )

async def get_current_user_flexible(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Obtiene usuario desde cookie O header Authorization.
    Prioridad: Cookie > Header (para transicion gradual)
    """
    token = None
    
    # Primero intentar cookie
    token = request.cookies.get("edarsa_token")
    
    # Fallback a header Authorization
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = verify_token(token)
    db = get_db()
    user = await db.users.find_one({"email": payload['email']}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user
```

```python
# modules/auth/routes.py - Login modificado
from fastapi import Response

@router.post("/auth/login")
async def login(credentials: UserLogin, response: Response):
    """Autentica un usuario y setea cookie httpOnly."""
    result = await service.login_user(credentials.email, credentials.password)
    
    # Setear cookie
    set_auth_cookie(response, result["token"])
    
    # Retornar solo usuario (sin token en body)
    return {"user": result["user"]}

@router.post("/auth/logout")
async def logout(response: Response):
    """Cierra sesion eliminando la cookie."""
    clear_auth_cookie(response)
    return {"message": "Sesion cerrada"}
```

### Fase 2: Frontend - Adaptar a Cookies

**Objetivo:** El frontend deja de guardar tokens y confía en cookies.

**Archivos a modificar:**
1. `lib/api.js` - Agregar `withCredentials: true`
2. `services/authStorage.js` - Eliminar funciones de token (deprecar gradualmente)
3. `contexts/AuthContext.jsx` - Solo guardar `user`, no `token`
4. `pages/Login.js` - No guardar token
5. `lib/auth.js` - `isAuthenticated()` consulta backend

**Codigo propuesto:**

```javascript
// lib/api.js - Actualizado
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // CRITICO: Enviar cookies en requests
});

// Ya no necesita interceptor para agregar Authorization header
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Limpiar estado local y redirigir
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

```javascript
// contexts/AuthContext.jsx - Simplificado
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Al montar, verificar si hay sesion activa
  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await api.get('/auth/me');
        setUser(response.data);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    checkSession();
  }, []);

  const login = useCallback(async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    setUser(response.data.user);  // Solo guardar user, cookie ya esta seteada
    return response.data;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      setUser(null);
    }
  }, []);

  // ... resto igual
}
```

### Fase 3: Portal de Proveedores

**Objetivo:** Aplicar mismo patron al portal, con cookie separada.

**Archivos:**
- `routes/portal_proveedores.py` - Cookies con nombre diferente
- `portal/App.jsx` - Adaptar igual que app principal

### Fase 4: Limpieza y Deprecacion

**Objetivo:** Eliminar codigo legacy de sessionStorage/localStorage.

**Archivos a limpiar:**
- `authStorage.js` - Eliminar funciones de token (mantener solo preferencias)
- Remover fallbacks a localStorage en todo el proyecto
- Actualizar documentacion

---

## 4. COMPATIBILIDAD Y ROLLBACK

### 4.1 Estrategia de Transicion

Durante la migracion, el backend aceptara AMBOS metodos:
1. Cookie `edarsa_token` (nuevo, prioritario)
2. Header `Authorization: Bearer {token}` (legacy, fallback)

Esto permite:
- Deploy gradual sin downtime
- Rollback inmediato si hay problemas
- Usuarios con sesiones activas no pierden acceso

### 4.2 Plan de Rollback

Si se detectan problemas:
1. Revertir cambios en frontend (volver a usar header Authorization)
2. Backend sigue aceptando ambos metodos
3. Investigar y corregir antes de re-intentar

### 4.3 Verificacion de Compatibilidad

Antes de eliminar soporte para header Authorization:
- [ ] Login/logout funcionan con cookies
- [ ] /api/auth/me retorna usuario desde cookie
- [ ] Todos los endpoints protegidos funcionan
- [ ] Portal de proveedores funciona con cookies separadas
- [ ] CORS permite credentials correctamente
- [ ] Filtros por empresa/sucursal siguen funcionando
- [ ] RBAC y permisos intactos

---

## 5. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|--------------|---------|------------|
| CORS mal configurado | Alta | Critico | Probar exhaustivamente antes de deploy |
| Cookies no enviadas en requests | Media | Alto | Verificar `withCredentials` en todos los axios |
| Sesiones perdidas en migracion | Media | Medio | Soporte dual durante transicion |
| Portal proveedores roto | Media | Medio | Cookie separada con path diferente |
| Desarrollo local falla | Alta | Bajo | `secure: false` en desarrollo |

---

## 6. CRITERIOS DE EXITO

1. **Seguridad:** Token JWT inaccesible desde JavaScript (verificar con DevTools)
2. **Funcionalidad:** Todos los flujos de login/logout funcionan
3. **Compatibilidad:** Usuarios existentes no pierden sesion
4. **Performance:** Sin degradacion perceptible
5. **Portal:** Proveedores pueden operar normalmente

---

## 7. CHECKLIST PRE-IMPLEMENTACION

- [ ] Documento revisado y aprobado
- [ ] Backup de archivos a modificar
- [ ] Entorno de pruebas disponible
- [ ] Credenciales de prueba verificadas
- [ ] Plan de rollback documentado
- [ ] Comunicacion a usuarios (si aplica)

---

**Estado:** IMPLEMENTADO - Arquitectura Dual por Ambiente (2025-12-27)  
**Resultado:** 
- Producción: Cookie httpOnly (JWT inaccesible a JS)
- Preview: memoryToken fallback (JWT accesible durante runtime)

---

## 8. HISTORIAL DE IMPLEMENTACIÓN

### Fase 1 - Backend Dual ✅ COMPLETADO
- `core/security.py`: Implementado `get_current_user_dual()`, `set_auth_cookie()`, `clear_auth_cookie()`
- `modules/auth/routes.py`: Login setea cookie, agregado `/auth/logout`, `/auth/me` usa dual
- CORS configurado con orígenes explícitos y `allow_credentials=True`
- **Reporte:** `/app/docs/AUTH_SECURITY_PHASE_1_BACKEND_DUAL_REPORT.md`

### Fase 2 - Frontend Cookies ✅ COMPLETADO
- `api.js` con `withCredentials: true`
- Token NO se guarda en sessionStorage/localStorage
- AuthContext simplificado (solo guarda `user` como caché UI)
- **Reporte:** `/app/docs/AUTH_SECURITY_PHASE_2_FRONTEND_COOKIES_REPORT.md`

### Fase 3 - Portal Proveedores ✅ COMPLETADO
- Cookie separada: `edarsa_portal_access_token` con `path=/api/portal`
- Token NO se guarda en sessionStorage del portal
- Endpoint `/portal/auth/logout` implementado
- **Reporte:** `/app/docs/AUTH_SECURITY_PHASE_3_PORTAL_COOKIES_REPORT.md`

### Fase 3.5 - Validación Final ✅ COMPLETADO
- Auditoría de seguridad sin modificar código
- Detectado riesgo de `Authorization: Bearer null`
- **Reporte:** `/app/docs/AUTH_SECURITY_FINAL_VALIDATION_REPORT.md`

### Fase 3.6 - Migración Fetch Directo ✅ COMPLETADO
- 5 páginas corregidas: Compras.js, Finanzas.js, Nominas.js, AuditoriasProgramadas.jsx, ConfigAsignaciones.jsx
- Headers `Authorization: Bearer null` eliminados
- **Reporte:** `/app/docs/AUTH_SECURITY_PHASE_3_6_FETCH_MIGRATION_REPORT.md`

### Fase 4 - Limpieza Legacy Controlada ✅ COMPLETADO
- 10 archivos migrados a `credentials: 'include'`
- Backend tolerante a `Bearer null/undefined`
- **Reporte:** `/app/docs/AUTH_SECURITY_PHASE_4_LEGACY_CLEANUP_REPORT.md`

### Fase 4.1 - Migración de getToken() Restantes ✅ COMPLETADO
- 18 archivos adicionales migrados
- 0 usos productivos de `getToken()` en frontend
- **Reporte:** `/app/docs/AUTH_SECURITY_PHASE_4_1_GETTOKEN_MIGRATION_REPORT.md`

### Fase 4.2 - Eliminación de Funciones Deprecated ✅ COMPLETADO
- Funciones eliminadas: `getToken()`, `getAccessToken()`, `setAccessToken()`, `removeAccessToken()`, `getAuthHeaders()`
- Hook eliminado: `useAuthToken.js`
- **Reporte:** `/app/docs/AUTH_SECURITY_PHASE_4_2_DEPRECATED_REMOVAL_REPORT.md`

### Fase 4.3 - Fallback memoryToken para Preview ✅ IMPLEMENTADO (2025-12-27)
- Detectado: Proxy Emergent sobreescribe CORS con wildcard
- Implementado: memoryToken como fallback temporal
- Documentado: Riesgo XSS de memoryToken
- **Reporte:** `/app/docs/AUTH_SECURITY_ENVIRONMENT_COMPATIBILITY.md`

---

## 9. ARQUITECTURA DUAL POR AMBIENTE

### Producción (Cookie httpOnly)

| Aspecto | Estado |
|---------|--------|
| Mecanismo | Cookie httpOnly |
| JWT accesible a JS | **NO** |
| Protección XSS | **COMPLETA** |
| Persistencia sesión | SÍ (según expiración) |
| CORS | Origin específico |

### Preview Emergent (memoryToken Fallback)

| Aspecto | Estado |
|---------|--------|
| Mecanismo | memoryToken (variable JS) |
| JWT accesible a JS | **SÍ** (durante runtime) |
| Protección XSS | **PARCIAL** |
| Persistencia sesión | NO (F5 requiere re-login) |
| Causa | Proxy sobreescribe CORS con wildcard |

### Corrección de Afirmaciones

**INCORRECTO:**
- "memoryToken es seguro contra XSS"
- "JWT completamente inaccesible a JavaScript"

**CORRECTO:**
- JWT NO se persiste en localStorage/sessionStorage
- En producción, JWT viaja por cookie httpOnly (inaccesible a JS)
- En preview, memoryToken es fallback temporal no persistente
- memoryToken NO protege contra XSS activo en runtime

---

## 10. RESULTADO FINAL

| Criterio de Éxito | Producción | Preview |
|-------------------|------------|---------|
| Token JWT inaccesible desde JavaScript | ✅ | ⚠️ Accesible runtime |
| Todos los flujos de login/logout funcionan | ✅ | ✅ |
| Sin degradación de performance | ✅ | ✅ |
| Portal de proveedores operativo | ✅ | ✅ |
| Funciones legacy eliminadas | ✅ | ✅ |
| Token NO en localStorage/sessionStorage | ✅ | ✅ |
| Sesión persiste en refresh | ✅ | ❌ |

---

## 11. DICTAMEN

**AUTH-SECURITY-01 cerrada con arquitectura dual por ambiente:**

- **Producción** = Cookie httpOnly (JWT inaccesible a JS)
- **Preview Emergent** = memoryToken temporal no persistente por limitación CORS/ingress

Riesgo XSS de memoryToken documentado.
Refresh tokens pendiente.

---

## APENDICE A: Archivos de Referencia Completos

### authStorage.js actual (a deprecar parcialmente)
- Lineas 27-42: `getAccessToken()` - A ELIMINAR
- Lineas 48-54: `setAccessToken()` - A ELIMINAR
- Lineas 96-101: `clearAccessToken()` - A ELIMINAR
- Lineas 135-151: `getPreference()`/`setPreference()` - MANTENER

### AuthContext.jsx actual (a simplificar)
- Lineas 39-40: Estado `token` - A ELIMINAR
- Lineas 84-92: `login()` - Simplificar (no guardar token)
- Lineas 114-116: `authHeaders` - A ELIMINAR (ya no necesario)

### api.js actual (a modificar)
- Linea 7: Agregar `withCredentials: true`
- Lineas 15-26: Eliminar interceptor de request que agrega Authorization
