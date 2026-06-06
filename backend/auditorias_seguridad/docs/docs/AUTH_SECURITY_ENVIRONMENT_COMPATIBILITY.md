# AUTH SECURITY - COMPATIBILIDAD POR AMBIENTE
## FASE AUTH-SECURITY-01 - Arquitectura Dual por Ambiente

**Fecha:** 2025-12-27  
**Estado:** DOCUMENTADO  
**Propósito:** Documentar las diferencias de comportamiento de autenticación entre ambientes de Preview y Producción.

---

## 1. RESUMEN EJECUTIVO

AUTH-SECURITY-01 implementa una **arquitectura dual por ambiente**:

| Ambiente | Mecanismo Principal | Mecanismo Fallback | Persistencia Sesión | Protección XSS |
|----------|--------------------|--------------------|---------------------|----------------|
| **Producción** | Cookie httpOnly | Header Authorization | SÍ (según expiración) | **COMPLETA** |
| **Preview Emergent** | Cookie httpOnly (bloqueada por CORS) | memoryToken | NO (requiere re-login en F5) | **PARCIAL** |

**IMPORTANTE:** memoryToken **NO** es equivalente en seguridad a cookie httpOnly.

---

## 2. AMBIENTE: PRODUCCIÓN / DOMINIO CONTROLADO

### 2.1 Configuración Requerida

```
CORS:
- Access-Control-Allow-Credentials: true
- Access-Control-Allow-Origin: [dominio específico, NO wildcard]

Cookie:
- HttpOnly: true
- Secure: true
- SameSite: Lax (o None si cross-site requerido)
- Path: /
- Max-Age: 259200 (72 horas)
```

### 2.2 Comportamiento Esperado

1. **Login:** POST `/api/auth/login` → Set-Cookie con JWT httpOnly
2. **Requests:** Cookie enviada automáticamente por navegador
3. **Refresh (F5):** Sesión persiste (cookie sigue válida)
4. **Logout:** Cookie eliminada por backend
5. **Protección XSS:** JWT **INACCESIBLE** a JavaScript (cookie httpOnly)

### 2.3 Validaciones de Producción

| # | Test | Resultado Esperado |
|---|------|-------------------|
| 1 | Login | Cookie `edarsa_access_token` seteada |
| 2 | `/api/auth/me` con cookie | 200 OK + datos usuario |
| 3 | Refresh página (F5) | Sesión persiste |
| 4 | `document.cookie` no muestra token | Cookie httpOnly |
| 5 | XSS simulado no puede extraer token | Protección completa |
| 6 | CORS no usa wildcard | Origin específico |

---

## 3. AMBIENTE: PREVIEW EMERGENT

### 3.1 Limitación Técnica Documentada (ACTUALIZACIÓN 2025-04-27)

**NOTA IMPORTANTE:** La validación del 2025-04-27 demostró que las cookies httpOnly **SÍ FUNCIONAN** en el ambiente Preview de Emergent, contrario a lo documentado inicialmente.

El proxy/ingress de Emergent **sobreescribe** los headers CORS:

```
Respuesta del Backend:
  Access-Control-Allow-Origin: https://[app].preview.emergentagent.com
  Access-Control-Allow-Credentials: true

Respuesta después del Proxy:
  Access-Control-Allow-Origin: *  ← SOBREESCRITO
  (Access-Control-Allow-Credentials omitido o ignorado)
```

Sin embargo, dado que el frontend y backend están en el **mismo dominio** (`stock-tracker-990.preview.emergentagent.com`), el navegador **SÍ envía las cookies** correctamente (las restricciones de CORS para cookies solo aplican en cross-origin).

### 3.2 Solución: memoryToken (Fallback - NO ACTIVO EN PREVIEW ACTUAL)

El mecanismo `memoryToken` existe como fallback, pero la validación demostró que **NO se está usando activamente** porque las cookies funcionan:

```javascript
// /app/frontend/src/lib/api.js
let memoryToken = null;  // Token en memoria JS (FALLBACK)

// Después del login exitoso:
memoryToken = response.data.token;

// En cada request:
// SI NO hay cookie, usa memoryToken como fallback
config.headers.Authorization = `Bearer ${memoryToken}`;
```

### 3.3 Comportamiento REAL en Preview (Validado 2025-04-27)

1. **Login:** POST `/api/auth/login` → Cookie `edarsa_access_token` **SÍ SE SETEA**
2. **Requests:** Cookie enviada automáticamente por el navegador
3. **Refresh (F5):** Sesión **PERSISTE** ✅ (cookie sigue válida)
4. **Logout:** Cookie eliminada correctamente
5. **Protección XSS:** **COMPLETA** - Cookie httpOnly inaccesible a JS

### 3.4 Validaciones de Preview (ACTUALIZADAS)

| # | Test | Resultado Esperado | Resultado Real (2025-04-27) |
|---|------|-------------------|----------------------------|
| 1 | Login | Cookie seteada | ✅ Cookie `edarsa_access_token` |
| 2 | `/api/auth/me` con cookie | 200 OK + datos usuario | ✅ Funciona |
| 3 | Refresh página (F5) | ~~Sesión PERDIDA~~ | ✅ **Sesión PERSISTE** |
| 4 | localStorage/sessionStorage | VACÍO (no hay token) | ✅ Solo datos UI, no JWT |
| 5 | Navegación interna | Sesión persiste | ✅ Funciona |

**Reporte de validación:** `/app/docs/AUTH_PRODUCTION_VALIDATION_REPORT.md`

---

## 4. COMPARACIÓN DE SEGURIDAD

### 4.1 Vectores de Ataque

| Vector | Cookie httpOnly (Prod) | memoryToken (Preview) | localStorage (Legacy) |
|--------|------------------------|----------------------|----------------------|
| XSS activo en runtime | ❌ No accesible | ⚠️ **ACCESIBLE** | ⚠️ **ACCESIBLE** |
| XSS persistente | ❌ No accesible | ⚠️ **ACCESIBLE** | ⚠️ **ACCESIBLE** |
| Robo post-refresh | ❌ No accesible | ❌ Token limpiado | ⚠️ **ACCESIBLE** |
| Inspección DevTools | ❌ Cookie httpOnly | ⚠️ Variable visible | ⚠️ Storage visible |
| CSRF | ⚠️ Requiere SameSite | ❌ No vulnerable | ❌ No vulnerable |

### 4.2 Nivel de Protección

```
Seguridad Alta:    Cookie httpOnly + Secure + SameSite
                   └── JWT INACCESIBLE a JavaScript
                   └── Protección completa contra XSS
                   
Seguridad Media:   memoryToken (fallback)
                   └── JWT NO persiste en storage
                   └── JWT SE LIMPIA en refresh
                   └── JWT ACCESIBLE durante sesión activa
                   └── VULNERABLE a XSS activo en runtime
                   
Seguridad Baja:    localStorage/sessionStorage (ELIMINADO)
                   └── JWT persiste entre sesiones
                   └── JWT accesible siempre
                   └── VULNERABLE a XSS en cualquier momento
```

---

## 5. ARQUITECTURA DE AUTENTICACIÓN DUAL

### 5.1 Diagrama de Flujo

```
                    ┌─────────────────────────────────────┐
                    │           POST /api/auth/login      │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │  Backend genera JWT + Set-Cookie    │
                    │  + Retorna token en body (fallback) │
                    └─────────────────┬───────────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              │                                               │
    ┌─────────▼─────────┐                         ┌──────────▼──────────┐
    │   PRODUCCIÓN      │                         │   PREVIEW EMERGENT  │
    │   CORS correcto   │                         │   CORS wildcard     │
    └─────────┬─────────┘                         └──────────┬──────────┘
              │                                               │
    ┌─────────▼─────────┐                         ┌──────────▼──────────┐
    │ Cookie httpOnly   │                         │ Cookie BLOQUEADA    │
    │ funciona          │                         │ por navegador       │
    └─────────┬─────────┘                         └──────────┬──────────┘
              │                                               │
    ┌─────────▼─────────┐                         ┌──────────▼──────────┐
    │ Requests usan     │                         │ Frontend guarda     │
    │ cookie automática │                         │ memoryToken         │
    └─────────┬─────────┘                         └──────────┬──────────┘
              │                                               │
    ┌─────────▼─────────┐                         ┌──────────▼──────────┐
    │ JWT INACCESIBLE   │                         │ Requests usan       │
    │ a JavaScript      │                         │ Authorization header│
    └───────────────────┘                         └──────────┬──────────┘
                                                             │
                                                  ┌──────────▼──────────┐
                                                  │ JWT ACCESIBLE       │
                                                  │ durante runtime     │
                                                  └─────────────────────┘
```

### 5.2 Backend: Autenticación Dual

```python
# /app/backend/core/security.py
async def get_current_user_dual(request) -> Dict:
    """
    Prioridad de lectura:
    1. Cookie httpOnly (producción)
    2. Header Authorization (fallback para preview)
    """
    token = None
    
    # 1. Intentar cookie (producción)
    token = request.cookies.get("edarsa_access_token")
    
    # 2. Fallback a header (preview)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            header_token = auth_header[7:]
            # Ignorar valores inválidos
            if header_token and header_token not in ("null", "undefined", ""):
                token = header_token
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verificar y retornar usuario...
```

---

## 6. RECOMENDACIONES PARA PRODUCCIÓN

### 6.1 Configuración CORS

```python
# server.py - Producción
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[
        "https://edarsa-hub.com",  # Dominio de producción
        # NO usar "*"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6.2 Verificación Pre-Deploy

- [ ] CORS no usa wildcard con credentials
- [ ] Cookie httpOnly verificada en navegador
- [ ] Sesión persiste después de F5
- [ ] Token no visible en DevTools > Application > Storage
- [ ] Token no extraíble con `document.cookie`
- [ ] memoryToken NO se usa si cookie funciona

---

## 7. RIESGOS DOCUMENTADOS

### 7.1 Riesgo: XSS en Preview

| Atributo | Valor |
|----------|-------|
| Ambiente | Preview Emergent |
| Descripción | Un ataque XSS activo puede extraer memoryToken |
| Impacto | Robo de sesión durante runtime |
| Mitigación | Solo ambiente de desarrollo/preview |
| Aceptación | Aceptado para preview, NO para producción |

### 7.2 Riesgo: Sesión no Persistente en Preview

| Atributo | Valor |
|----------|-------|
| Ambiente | Preview Emergent |
| Descripción | F5 o navegación directa requiere re-login |
| Impacto | Inconveniencia de usuario |
| Mitigación | Documentado, aceptado para preview |
| Aceptación | Aceptado para preview |

---

## 8. DICTAMEN

**AUTH-SECURITY-01** implementa una arquitectura de autenticación dual:

**Producción (cookie httpOnly):**
- JWT completamente inaccesible a JavaScript
- Protección completa contra XSS
- Sesión persistente según expiración

**Preview Emergent (memoryToken fallback):**
- JWT NO persiste en localStorage/sessionStorage
- JWT accesible a JavaScript durante runtime
- Sesión NO persiste en refresh
- memoryToken **NO** es equivalente a cookie httpOnly
- memoryToken **NO** protege contra XSS activo

**Estado:** Arquitectura dual documentada y funcional.

---

**Documento creado:** 2025-12-27  
**Última actualización:** 2025-12-27
