# P1-REFRESH-TOKENS-TECHNICAL-PLAN
## Sistema de Refresh Tokens, Rotación y Sesiones Seguras para EDARSA HUB

**Fecha:** 2025-04-27  
**Estado:** DISEÑO TÉCNICO - NO IMPLEMENTAR AÚN  
**Versión:** 1.0  
**Autor:** Agente E1

---

## ÍNDICE

1. [Estado Actual](#1-estado-actual)
2. [Objetivo Propuesto](#2-objetivo-propuesto)
3. [Diseño de Cookies](#3-diseño-de-cookies)
4. [Modelo de Datos en EDARSAHUB](#4-modelo-de-datos-en-edarsahub)
5. [Endpoints Propuestos](#5-endpoints-propuestos)
6. [Flujo Interno (Usuarios)](#6-flujo-interno-usuarios)
7. [Flujo Portal Proveedores](#7-flujo-portal-proveedores)
8. [Seguridad](#8-seguridad)
9. [Compatibilidad](#9-compatibilidad)
10. [Plan de Implementación](#10-plan-de-implementación)
11. [Pruebas Necesarias](#11-pruebas-necesarias)
12. [Riesgos](#12-riesgos)
13. [Recomendación Final](#13-recomendación-final)

---

## 1. ESTADO ACTUAL

### 1.1 Access Token Actual

| Aspecto | Valor Actual | Ubicación |
|---------|--------------|-----------|
| **Tipo** | JWT (HS256) | `core/security.py` |
| **Duración** | 72 horas (configurable) | `JWT_EXPIRATION_HOURS` env var |
| **Payload** | `user_id`, `email`, `role`, `exp` | `create_token()` |
| **Almacenamiento** | Cookie httpOnly | `edarsa_access_token` |
| **Verificación** | `jwt.decode()` con secret | `verify_token()` |

### 1.2 Cookie Actual (Usuarios Internos)

```python
# /app/backend/core/security.py
AUTH_COOKIE_NAME = "edarsa_access_token"
AUTH_COOKIE_MAX_AGE = 72 * 60 * 60  # 72 horas

response.set_cookie(
    key=AUTH_COOKIE_NAME,
    value=token,          # JWT completo
    httponly=True,        # ✅ Protección XSS
    secure=is_production, # Solo HTTPS en producción
    samesite="lax",       # Protección CSRF básica
    path="/",             # Toda la aplicación
    max_age=AUTH_COOKIE_MAX_AGE
)
```

### 1.3 Cookie Actual (Portal Proveedores)

```python
# /app/backend/routes/portal_proveedores.py
PORTAL_COOKIE_NAME = "edarsa_portal_access_token"
PORTAL_COOKIE_MAX_AGE = 24 * 60 * 60  # 24 horas

response.set_cookie(
    key=PORTAL_COOKIE_NAME,
    value=token,
    httponly=True,
    secure=is_production,
    samesite="lax",
    path="/api/portal",   # Solo endpoints del portal
    max_age=PORTAL_COOKIE_MAX_AGE
)
```

### 1.4 Login/Logout Actual

**Login Interno (`/api/auth/login`):**
1. Valida credenciales contra MongoDB (`users` collection)
2. Genera JWT con `create_token()`
3. Setea cookie httpOnly con `set_auth_cookie()`
4. Retorna `{token, user}` en body (compatibilidad legacy)

**Logout Interno (`/api/auth/logout`):**
1. Elimina cookie con `clear_auth_cookie()`
2. No revoca el token (sigue siendo válido hasta expirar)

**Login Portal (`/api/portal/auth/login`):**
1. Valida RFC/contraseña contra MongoDB (`portal_suppliers`)
2. Genera JWT con `create_portal_token()`
3. Setea cookie con `set_portal_auth_cookie()`
4. Retorna token en body

**Logout Portal (`/api/portal/auth/logout`):**
1. Elimina cookie del portal
2. No revoca el token

### 1.5 Backend Dual (Vigente)

El sistema soporta autenticación dual para compatibilidad:

```python
# core/security.py - get_current_user_dual()
# Prioridad 1: Header Authorization: Bearer <token>
# Prioridad 2: Cookie edarsa_access_token
# Resultado: 401 si ninguno existe
```

**Nota:** La validación del 2025-04-27 confirmó que las cookies **funcionan correctamente** en Preview, por lo que el fallback `memoryToken` del frontend NO se está usando activamente.

### 1.6 Manejo de Expiración Actual

| Escenario | Comportamiento Actual |
|-----------|----------------------|
| Token válido | Request procesado normalmente |
| Token expirado | 401 "Token expirado" → Frontend redirige a login |
| Sin token | 401 "Not authenticated" → Frontend redirige a login |
| Token inválido | 401 "Token inválido" → Frontend redirige a login |

**Problema:** No hay refresh automático. Usuario debe re-autenticarse completamente cuando el token expira.

### 1.7 Diagrama Estado Actual

```
┌─────────────┐    POST /auth/login     ┌─────────────┐
│   Usuario   │ ──────────────────────► │   Backend   │
│  (Browser)  │                         │  (FastAPI)  │
└─────────────┘                         └─────────────┘
       │                                       │
       │ ◄─── JWT (cookie httpOnly, 72h) ────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│                    72 HORAS                          │
│  Request → Cookie enviada → JWT verificado → OK     │
└─────────────────────────────────────────────────────┘
       │
       ▼ (Expira)
┌─────────────┐
│   401       │ → Redirige a login → Re-autenticar
└─────────────┘
```

---

## 2. OBJETIVO PROPUESTO

### 2.1 Tokens

| Token | Duración | Propósito |
|-------|----------|-----------|
| **Access Token** | 15-30 minutos | Autorización de requests |
| **Refresh Token** | 7 días | Renovar access token sin re-login |

### 2.2 Características

- **Cookie httpOnly** para ambos tokens
- **Rotación** del refresh token en cada uso
- **Revocación** por logout y por seguridad (compromiso detectado)
- **Tabla de sesiones** en EDARSAHUB (SQL Server) como fuente de verdad

### 2.3 Diagrama Objetivo

```
┌─────────────┐    POST /auth/login     ┌─────────────┐
│   Usuario   │ ──────────────────────► │   Backend   │
│  (Browser)  │                         │  (FastAPI)  │
└─────────────┘                         └─────────────┘
       │                                       │
       │ ◄── Access Token (cookie, 15min) ────┤
       │ ◄── Refresh Token (cookie, 7d) ──────┤
       │                                       │
       ▼                                       ▼
┌───────────────────────┐        ┌───────────────────────┐
│  Cookie: access_token │        │  EDARSAHUB.Sesiones   │
│  (corta duración)     │        │  - refresh_token_hash │
└───────────────────────┘        │  - user_id            │
                                 │  - created_at         │
                                 │  - expires_at         │
                                 │  - revoked            │
                                 └───────────────────────┘
       │
       ▼ (Access expira)
┌─────────────────────────────────────────────────────────┐
│  POST /auth/refresh (automático)                        │
│  - Envía refresh_token (cookie)                         │
│  - Backend valida hash contra EDARSAHUB                 │
│  - Genera nuevo access_token + nuevo refresh_token      │
│  - Guarda nuevo hash, invalida el anterior              │
└─────────────────────────────────────────────────────────┘
```

---

## 3. DISEÑO DE COOKIES

### 3.1 Usuarios Internos

| Cookie | Valor | Atributos |
|--------|-------|-----------|
| `edarsa_access_token` | JWT (access) | `httpOnly`, `Secure`, `SameSite=Lax`, `Path=/`, `Max-Age=900` (15min) |
| `edarsa_refresh_token` | Opaque token (UUID) | `httpOnly`, `Secure`, `SameSite=Strict`, `Path=/api/auth/refresh`, `Max-Age=604800` (7d) |

**Justificación de SameSite:**
- Access: `Lax` permite requests de navegación normal
- Refresh: `Strict` porque solo se usa en endpoint específico

**Justificación de Path:**
- Access: `Path=/` para toda la API
- Refresh: `Path=/api/auth/refresh` para minimizar superficie de ataque

### 3.2 Portal Proveedores

| Cookie | Valor | Atributos |
|--------|-------|-----------|
| `edarsa_portal_access_token` | JWT (access) | `httpOnly`, `Secure`, `SameSite=Lax`, `Path=/api/portal`, `Max-Age=900` (15min) |
| `edarsa_portal_refresh_token` | Opaque token (UUID) | `httpOnly`, `Secure`, `SameSite=Strict`, `Path=/api/portal/auth/refresh`, `Max-Age=86400` (24h) |

**Nota:** El portal tiene refresh token más corto (24h vs 7d) porque los proveedores no requieren sesiones tan largas.

### 3.3 Código Propuesto

```python
# core/security.py - PROPUESTO (no implementar aún)

# Constantes de duración
ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_DAYS = 7

ACCESS_COOKIE_NAME = "edarsa_access_token"
REFRESH_COOKIE_NAME = "edarsa_refresh_token"

def set_access_cookie(response, token: str, is_production: bool = True):
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/",
        max_age=ACCESS_TOKEN_MINUTES * 60
    )

def set_refresh_cookie(response, token: str, is_production: bool = True):
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_production,
        samesite="strict",
        path="/api/auth/refresh",
        max_age=REFRESH_TOKEN_DAYS * 24 * 60 * 60
    )
```

---

## 4. MODELO DE DATOS EN EDARSAHUB

### 4.1 Tabla Principal: `Sesiones`

**Base de datos:** EDARSAHUB (SQL Server)  
**Propósito:** Almacenar sesiones activas y permitir revocación

```sql
-- PROPUESTO: No ejecutar aún

CREATE TABLE Sesiones (
    SesionID            UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    UsuarioID           INT NOT NULL,                    -- FK a Usuarios
    TipoUsuario         VARCHAR(20) NOT NULL,            -- 'interno' | 'proveedor'
    RefreshTokenHash    VARCHAR(128) NOT NULL,           -- SHA256 del refresh token
    FamiliaTokenID      UNIQUEIDENTIFIER NOT NULL,       -- Para detectar replay
    
    -- Timestamps
    FechaCreacion       DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaExpiracion     DATETIME2 NOT NULL,
    UltimaActividad     DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    
    -- Revocación
    Revocado            BIT NOT NULL DEFAULT 0,
    FechaRevocacion     DATETIME2 NULL,
    MotivoRevocacion    VARCHAR(100) NULL,               -- 'logout' | 'logout_all' | 'security' | 'expired'
    RevocadoPor         INT NULL,                        -- FK a Usuarios (admin que revocó)
    
    -- Contexto de seguridad
    IPCliente           VARCHAR(45) NULL,                -- IPv4 o IPv6
    UserAgent           VARCHAR(500) NULL,
    DispositivoID       VARCHAR(100) NULL,               -- Fingerprint opcional
    
    -- Auditoría
    FechaModificacion   DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    
    -- Índices implícitos en constraints
    CONSTRAINT FK_Sesiones_Usuarios FOREIGN KEY (UsuarioID) 
        REFERENCES Usuarios(UsuarioID) ON DELETE CASCADE,
    
    -- Índice único para búsqueda rápida por hash
    INDEX IX_Sesiones_TokenHash UNIQUE (RefreshTokenHash) WHERE Revocado = 0,
    
    -- Índice para listar sesiones de usuario
    INDEX IX_Sesiones_Usuario (UsuarioID, Revocado, FechaExpiracion),
    
    -- Índice para familia (detección de replay)
    INDEX IX_Sesiones_Familia (FamiliaTokenID, Revocado)
);
```

### 4.2 Tabla Secundaria: `SesionesHistorico`

**Propósito:** Auditoría de sesiones (opcional, recomendada para compliance)

```sql
-- PROPUESTO: Opcional

CREATE TABLE SesionesHistorico (
    HistoricoID         BIGINT IDENTITY(1,1) PRIMARY KEY,
    SesionID            UNIQUEIDENTIFIER NOT NULL,
    UsuarioID           INT NOT NULL,
    TipoUsuario         VARCHAR(20) NOT NULL,
    Accion              VARCHAR(50) NOT NULL,            -- 'login' | 'refresh' | 'logout' | 'revoked' | 'expired'
    
    FechaAccion         DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    IPCliente           VARCHAR(45) NULL,
    UserAgent           VARCHAR(500) NULL,
    
    -- Detalles adicionales
    DetallesJSON        NVARCHAR(MAX) NULL,              -- Metadata adicional
    
    INDEX IX_SesionesHist_Usuario (UsuarioID, FechaAccion DESC),
    INDEX IX_SesionesHist_Sesion (SesionID, FechaAccion DESC)
);
```

### 4.3 Tabla para Portal: `SesionesPortal`

**Propósito:** Sesiones de proveedores (separada de usuarios internos)

```sql
-- PROPUESTO: Estructura similar a Sesiones

CREATE TABLE SesionesPortal (
    SesionID            UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ProveedorID         VARCHAR(100) NOT NULL,           -- ID del proveedor en portal_suppliers
    RFC                 VARCHAR(15) NOT NULL,
    RefreshTokenHash    VARCHAR(128) NOT NULL,
    FamiliaTokenID      UNIQUEIDENTIFIER NOT NULL,
    
    FechaCreacion       DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaExpiracion     DATETIME2 NOT NULL,
    UltimaActividad     DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    
    Revocado            BIT NOT NULL DEFAULT 0,
    FechaRevocacion     DATETIME2 NULL,
    MotivoRevocacion    VARCHAR(100) NULL,
    
    IPCliente           VARCHAR(45) NULL,
    UserAgent           VARCHAR(500) NULL,
    
    INDEX IX_SesionesPortal_TokenHash UNIQUE (RefreshTokenHash) WHERE Revocado = 0,
    INDEX IX_SesionesPortal_Proveedor (ProveedorID, Revocado)
);
```

### 4.4 Consideraciones de Diseño

**¿Por qué EDARSAHUB (SQL Server) y no MongoDB?**

1. **EDARSAHUB es el cerebro:** Todas las entidades maestras (usuarios, servidores, sucursales) ya viven en SQL Server
2. **Transaccionalidad:** SQL Server garantiza ACID para operaciones de revocación
3. **Joins eficientes:** Para reportes de sesiones por usuario
4. **Índices únicos:** Para búsqueda rápida de refresh tokens
5. **Consistencia:** No hay riesgo de inconsistencia entre dos bases de datos

**¿Por qué almacenar solo el hash del refresh token?**

1. **Seguridad:** Si la base de datos es comprometida, los tokens no son útiles
2. **Irrecuperabilidad:** No se puede reconstruir el token desde el hash
3. **Verificación O(1):** SHA256(token) = hash almacenado

---

## 5. ENDPOINTS PROPUESTOS

### 5.1 Usuarios Internos

| Método | Endpoint | Función |
|--------|----------|---------|
| POST | `/api/auth/login` | Login (retorna access + refresh) |
| POST | `/api/auth/refresh` | Renovar access token |
| POST | `/api/auth/logout` | Logout (revoca sesión actual) |
| POST | `/api/auth/logout-all` | Logout de todas las sesiones |
| GET | `/api/auth/me` | Datos del usuario actual |
| GET | `/api/auth/sessions` | Listar sesiones activas (admin) |
| DELETE | `/api/auth/sessions/{session_id}` | Revocar sesión específica (admin) |

### 5.2 Portal Proveedores

| Método | Endpoint | Función |
|--------|----------|---------|
| POST | `/api/portal/auth/login` | Login proveedor |
| POST | `/api/portal/auth/refresh` | Renovar access token |
| POST | `/api/portal/auth/logout` | Logout proveedor |
| GET | `/api/portal/auth/me` | Datos del proveedor actual |

### 5.3 Especificación de Endpoints Clave

#### POST /api/auth/login

**Request:**
```json
{
  "email": "usuario@edarsa.com",
  "password": "secreto123"
}
```

**Response 200:**
```json
{
  "user": {
    "id": 123,
    "email": "usuario@edarsa.com",
    "role": "Administrador",
    "nombre": "Juan Pérez"
  },
  "expires_in": 900  // segundos (15 min)
}
```

**Cookies seteadas:**
- `edarsa_access_token` (JWT, 15 min)
- `edarsa_refresh_token` (UUID opaco, 7 días)

**Backend:**
1. Valida credenciales
2. Crea registro en `EDARSAHUB.Sesiones` con hash del refresh token
3. Genera access token (JWT)
4. Genera refresh token (UUID)
5. Setea ambas cookies

#### POST /api/auth/refresh

**Request:** Sin body. Cookies enviadas automáticamente.

**Response 200:**
```json
{
  "expires_in": 900
}
```

**Cookies actualizadas:**
- `edarsa_access_token` (nuevo JWT)
- `edarsa_refresh_token` (nuevo UUID, rotado)

**Backend:**
1. Lee `edarsa_refresh_token` de cookie
2. Busca hash en `EDARSAHUB.Sesiones` donde `Revocado = 0` y `FechaExpiracion > NOW()`
3. Si no existe: **Replay detectado** → Revoca toda la familia → 401
4. Si existe:
   - Genera nuevo access token
   - Genera nuevo refresh token
   - Actualiza `RefreshTokenHash` en BD (token antiguo inválido)
   - Setea nuevas cookies

#### POST /api/auth/logout

**Response 200:**
```json
{
  "message": "Sesión cerrada"
}
```

**Backend:**
1. Lee `edarsa_refresh_token` de cookie
2. Marca sesión como `Revocado = 1`, `MotivoRevocacion = 'logout'`
3. Elimina ambas cookies

#### POST /api/auth/logout-all

**Response 200:**
```json
{
  "message": "Todas las sesiones cerradas",
  "sessions_revoked": 3
}
```

**Backend:**
1. Obtiene `user_id` del access token actual
2. Revoca TODAS las sesiones del usuario en `EDARSAHUB.Sesiones`
3. Elimina cookies del request actual

---

## 6. FLUJO INTERNO (USUARIOS)

### 6.1 Login

```
Usuario                    Frontend                   Backend                  EDARSAHUB
   │                          │                          │                         │
   │── Ingresa credenciales ─►│                          │                         │
   │                          │── POST /auth/login ─────►│                         │
   │                          │                          │── Valida credenciales ──►│
   │                          │                          │◄── Usuario válido ──────│
   │                          │                          │                         │
   │                          │                          │── Genera access_token   │
   │                          │                          │── Genera refresh_token  │
   │                          │                          │── Hash(refresh_token) ──►│
   │                          │                          │                         │
   │                          │◄── Set-Cookie: access ───│                         │
   │                          │◄── Set-Cookie: refresh ──│                         │
   │                          │◄── 200 {user, exp} ──────│                         │
   │◄── Redirige a dashboard ─│                          │                         │
```

### 6.2 Access Token Expirado

```
Usuario                    Frontend                   Backend                  EDARSAHUB
   │                          │                          │                         │
   │── Click en módulo ──────►│                          │                         │
   │                          │── GET /api/finanzas ────►│                         │
   │                          │   (access_token cookie)  │                         │
   │                          │                          │── Verifica JWT ─────────│
   │                          │◄── 401 Token expirado ───│                         │
   │                          │                          │                         │
   │                          │── POST /auth/refresh ───►│                         │
   │                          │   (refresh_token cookie) │                         │
   │                          │                          │── Hash(refresh) ───────►│
   │                          │                          │◄── Sesión válida ──────│
   │                          │                          │── Nuevo hash ──────────►│
   │                          │                          │                         │
   │                          │◄── Set-Cookie: access ───│                         │
   │                          │◄── Set-Cookie: refresh ──│                         │
   │                          │◄── 200 OK ───────────────│                         │
   │                          │                          │                         │
   │                          │── GET /api/finanzas ────►│  (RETRY automático)     │
   │                          │◄── 200 {data} ───────────│                         │
   │◄── Muestra Finanzas ─────│                          │                         │
```

### 6.3 Refresh Token Rotado (Replay Detectado)

```
Atacante                   Víctima                    Backend                  EDARSAHUB
   │                          │                          │                         │
   │                          │── Login ────────────────►│                         │
   │                          │◄── refresh_token_v1 ─────│── Hash(v1) ────────────►│
   │                          │                          │                         │
   │── Roba refresh_token_v1 ─┤                          │                         │
   │                          │                          │                         │
   │                          │── Refresh normal ───────►│                         │
   │                          │◄── refresh_token_v2 ─────│── Hash(v2), invalida v1 ►│
   │                          │                          │                         │
   │── Usa refresh_token_v1 ─►│                          │                         │
   │                          │                          │── Busca Hash(v1) ──────►│
   │                          │                          │◄── NO ENCONTRADO ───────│
   │                          │                          │                         │
   │                          │                          │── REPLAY DETECTADO      │
   │                          │                          │── Revoca TODA familia ──►│
   │                          │                          │                         │
   │◄── 401 Sesión inválida ──│                          │                         │
   │                          │◄── 401 (próximo request) │                         │
   │                          │── Redirige a login ──────│                         │
```

### 6.4 Logout

```
Usuario                    Frontend                   Backend                  EDARSAHUB
   │                          │                          │                         │
   │── Click "Cerrar Sesión" ►│                          │                         │
   │                          │── POST /auth/logout ────►│                         │
   │                          │                          │── Revoca sesión ───────►│
   │                          │◄── Delete-Cookie: access ─│                         │
   │                          │◄── Delete-Cookie: refresh │                         │
   │                          │◄── 200 OK ───────────────│                         │
   │                          │                          │                         │
   │                          │── Limpia AuthContext ────│                         │
   │◄── Redirige a /login ────│                          │                         │
```

---

## 7. FLUJO PORTAL PROVEEDORES

### 7.1 Patrón Similar pero Separado

| Aspecto | Usuarios Internos | Portal Proveedores |
|---------|-------------------|-------------------|
| Tabla de sesiones | `EDARSAHUB.Sesiones` | `EDARSAHUB.SesionesPortal` |
| Cookie access | `edarsa_access_token` | `edarsa_portal_access_token` |
| Cookie refresh | `edarsa_refresh_token` | `edarsa_portal_refresh_token` |
| Duración access | 15 minutos | 15 minutos |
| Duración refresh | 7 días | 24 horas |
| Endpoints | `/api/auth/*` | `/api/portal/auth/*` |
| JWT type claim | `type: "internal"` | `type: "portal_supplier"` |

### 7.2 Separación de Cookies

- Cookie interna **NO** autentica endpoints del portal (path diferente)
- Cookie portal **NO** autentica endpoints internos (path diferente)
- JWT incluye `type` claim para validación explícita

### 7.3 Verificación de Separación

```python
# Backend - PROPUESTO

async def get_current_user_dual(request: Request):
    # ... verificar token ...
    
    payload = verify_token(token)
    
    # NUEVO: Verificar tipo de token
    if payload.get("type") == "portal_supplier":
        raise HTTPException(401, "Token de portal no válido para endpoints internos")
    
    # ... continuar ...

async def get_current_supplier_dual(request: Request):
    # ... verificar token ...
    
    payload = verify_token(token)
    
    # NUEVO: Verificar tipo de token
    if payload.get("type") != "portal_supplier":
        raise HTTPException(401, "Token interno no válido para portal")
    
    # ... continuar ...
```

---

## 8. SEGURIDAD

### 8.1 Almacenamiento de Tokens

| Ubicación | ¿Permitido? | Justificación |
|-----------|-------------|---------------|
| Cookie httpOnly | ✅ SÍ | Inaccesible a JavaScript |
| localStorage | ❌ NO | Vulnerable a XSS |
| sessionStorage | ❌ NO | Vulnerable a XSS |
| Variable JS | ⚠️ Solo memoryToken fallback | Temporal, no persistente |
| Base de datos | ✅ Solo hash | Irrecuperable si se filtra |

### 8.2 Hash del Refresh Token

```python
import hashlib
import secrets

def generate_refresh_token() -> str:
    """Genera un refresh token opaco (UUID + entropy)"""
    return secrets.token_urlsafe(32)  # 256 bits de entropía

def hash_refresh_token(token: str) -> str:
    """Hashea el refresh token para almacenamiento"""
    return hashlib.sha256(token.encode()).hexdigest()
```

**Propiedades:**
- Token plano **nunca** se almacena
- Hash es determinístico → mismo token = mismo hash
- SHA256 es one-way → no se puede reconstruir el token

### 8.3 Detección de Replay (Token Reutilizado)

**Mecanismo:** `FamiliaTokenID`

1. Login crea sesión con `FamiliaTokenID = NEWID()`
2. Refresh genera nuevo token pero mantiene `FamiliaTokenID`
3. Si se detecta refresh token inválido (ya rotado):
   - `FamiliaTokenID` identifica TODAS las sesiones relacionadas
   - Se revocan TODAS → Atacante y víctima quedan deslogueados
   - Fuerza re-autenticación

### 8.4 CSRF

**Evaluación:**
- `SameSite=Lax` en access token → Protección básica
- `SameSite=Strict` en refresh token → Protección máxima

**Conclusión:** `SameSite` es **suficiente** para este caso de uso. No se requiere token CSRF adicional porque:
1. Refresh endpoint solo acepta cookies (no JSON body con token)
2. `SameSite=Strict` bloquea requests cross-site
3. El único vector sería un subdomain takeover (bajo riesgo)

### 8.5 Rate Limiting

```python
# PROPUESTO - Configuración

RATE_LIMITS = {
    "/api/auth/login": {
        "window": 60,           # 1 minuto
        "max_requests": 5,      # 5 intentos
        "block_duration": 300   # 5 minutos de bloqueo
    },
    "/api/auth/refresh": {
        "window": 60,
        "max_requests": 20,     # Más permisivo (refresh automático)
        "block_duration": 60
    }
}
```

### 8.6 Auditoría de Sesiones

Cada evento se registra en `SesionesHistorico`:

| Acción | Se registra |
|--------|-------------|
| Login | ✅ Usuario, IP, User-Agent, timestamp |
| Refresh | ✅ Timestamp, IP (puede cambiar) |
| Logout | ✅ Voluntario vs expiración |
| Revocación | ✅ Quién revocó, motivo |
| Replay detectado | ✅ **ALERTA DE SEGURIDAD** |

### 8.7 No Exponer Tokens en Logs/Errores

```python
# PROPUESTO

import logging

def safe_log_request(request, error=None):
    """Log sin exponer tokens"""
    log_data = {
        "path": request.url.path,
        "method": request.method,
        "ip": request.client.host,
        # NO incluir: cookies, headers Authorization
    }
    if error:
        log_data["error"] = str(error)
        # NO incluir stack traces con tokens
    
    logging.info(f"Request: {log_data}")
```

---

## 9. COMPATIBILIDAD

### 9.1 No Romper Login Actual

**Estrategia:** Período de transición con soporte dual

```python
# FASE A: Login retorna token en body Y setea cookies
@router.post("/auth/login")
async def login(credentials, response):
    # ... validar ...
    
    access_token = create_access_token(user)
    refresh_token = create_refresh_token()
    
    # Setear cookies (nuevo)
    set_access_cookie(response, access_token)
    set_refresh_cookie(response, refresh_token)
    
    # MANTENER respuesta legacy para frontend actual
    return {
        "token": access_token,  # ← Frontend actual usa esto
        "user": user_data
    }
```

### 9.2 No Romper AuthContext

**Frontend actual:**
```javascript
// /app/frontend/src/context/AuthContext.js
const login = async (email, password) => {
  const response = await api.post('/auth/login', { email, password });
  setUser(response.data.user);
  // memoryToken para fallback (no se usa activamente)
};
```

**Cambio necesario (FASE B):**
```javascript
// Agregar interceptor para refresh automático
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401 && error.config.url !== '/auth/refresh') {
      // Intentar refresh
      try {
        await api.post('/auth/refresh');
        // Retry request original
        return api(error.config);
      } catch (refreshError) {
        // Refresh falló → logout
        logout();
        throw refreshError;
      }
    }
    throw error;
  }
);
```

### 9.3 No Romper api.js

**Mantener:**
- `withCredentials: true` → Envía cookies automáticamente
- Interceptor de Authorization (fallback memoryToken)
- Manejo de errores 401

**Agregar:**
- Interceptor de refresh automático
- Lógica de retry

### 9.4 No Romper Permisos/Roles/Filtros

**Sin cambios:** El payload del JWT mantiene:
- `user_id`
- `email`
- `role`

Los permisos se cargan desde MongoDB/SQL Server igual que antes.

### 9.5 Migración Gradual

| Fase | Frontend | Backend | Comportamiento |
|------|----------|---------|----------------|
| A | Sin cambios | Dual (body + cookies) | Login funciona igual, refresh no implementado |
| B | Interceptor refresh | Endpoint /refresh | Refresh automático si 401 |
| C | Eliminar memoryToken | Eliminar token en body | Solo cookies |

### 9.6 Rollback

Si hay problemas:
1. **Backend:** Revertir a `JWT_EXPIRATION_HOURS = 72`
2. **Frontend:** Revertir interceptor de refresh
3. **BD:** Tabla `Sesiones` puede quedarse vacía (no afecta)

---

## 10. PLAN DE IMPLEMENTACIÓN

### Fase A: Backend - Modelo + Endpoints Base

**Duración estimada:** 1-2 sesiones de trabajo

**Tareas:**
1. Crear tabla `EDARSAHUB.Sesiones` (script SQL)
2. Crear tabla `EDARSAHUB.SesionesHistorico` (opcional)
3. Implementar `generate_refresh_token()` y `hash_refresh_token()`
4. Modificar `/auth/login` para:
   - Generar access token corto (15 min)
   - Generar refresh token
   - Guardar hash en `Sesiones`
   - Setear ambas cookies
   - **MANTENER** respuesta legacy `{token, user}` en body
5. Implementar `/auth/refresh`:
   - Leer refresh token de cookie
   - Validar contra `Sesiones`
   - Detectar replay
   - Rotar token
   - Setear nuevas cookies
6. Modificar `/auth/logout` para:
   - Revocar sesión en `Sesiones`
   - Eliminar ambas cookies
7. Implementar `/auth/logout-all`

**Entregables:**
- Scripts SQL para tablas
- Endpoints funcionando
- Tests unitarios

**Rollback:** Si falla, mantener `JWT_EXPIRATION_HOURS = 72` y no usar refresh.

### Fase B: Frontend - Refresh Automático

**Duración estimada:** 1 sesión de trabajo

**Tareas:**
1. Agregar interceptor de respuesta en `api.js`:
   - Si 401 y no es `/auth/refresh`:
     - Llamar a `/auth/refresh`
     - Si éxito: retry request original
     - Si falla: logout
2. Manejar race conditions (múltiples requests simultáneas esperando refresh)
3. Actualizar AuthContext si es necesario

**Entregables:**
- Interceptor funcionando
- Refresh transparente para usuario
- No loops infinitos

### Fase C: Portal Proveedores

**Duración estimada:** 1 sesión de trabajo

**Tareas:**
1. Crear tabla `EDARSAHUB.SesionesPortal`
2. Implementar endpoints portal:
   - `/portal/auth/login` (modificar)
   - `/portal/auth/refresh` (nuevo)
   - `/portal/auth/logout` (modificar)
3. Separación de cookies por path

**Entregables:**
- Portal con refresh tokens
- Sesiones completamente separadas

### Fase D: Revocación y Administración

**Duración estimada:** 1 sesión de trabajo

**Tareas:**
1. Endpoint `/auth/sessions` (admin)
2. Endpoint `/auth/sessions/{id}` DELETE (admin)
3. UI opcional en Centro de Control para ver sesiones activas

**Entregables:**
- Admin puede ver y revocar sesiones
- Auditoría visible

### Fase E: Limpieza y Hardening

**Duración estimada:** 1 sesión de trabajo

**Tareas:**
1. Eliminar respuesta `{token}` en body (frontend no lo necesita)
2. Eliminar `memoryToken` del frontend
3. Rate limiting en login/refresh
4. Revisión de logs (no exponer tokens)
5. Documentación final

**Entregables:**
- Sistema limpio
- Sin código legacy
- Documentación completa

---

## 11. PRUEBAS NECESARIAS

### 11.1 Pruebas de Login

| # | Caso | Resultado Esperado |
|---|------|-------------------|
| 1 | Login con credenciales válidas | 200, cookies seteadas, usuario en body |
| 2 | Login con credenciales inválidas | 401, sin cookies |
| 3 | Login sin email | 400 validación |
| 4 | Login sin password | 400 validación |
| 5 | Login usuario desactivado | 403 |

### 11.2 Pruebas de Refresh

| # | Caso | Resultado Esperado |
|---|------|-------------------|
| 1 | Refresh con token válido | 200, nuevas cookies |
| 2 | Refresh sin cookie | 401 |
| 3 | Refresh con token expirado | 401 |
| 4 | Refresh con token revocado | 401 |
| 5 | Refresh token replay (ya rotado) | 401, familia revocada |
| 6 | Doble refresh simultáneo | Una falla, otra éxito (race condition) |

### 11.3 Pruebas de Expiración

| # | Caso | Resultado Esperado |
|---|------|-------------------|
| 1 | Request con access válido | 200 |
| 2 | Request con access expirado | 401 → refresh → retry → 200 |
| 3 | Access y refresh expirados | 401 → redirect a login |

### 11.4 Pruebas de Logout

| # | Caso | Resultado Esperado |
|---|------|-------------------|
| 1 | Logout normal | 200, cookies eliminadas, sesión revocada |
| 2 | Logout-all | 200, todas las sesiones revocadas |
| 3 | Request después de logout | 401 |

### 11.5 Pruebas de Replay

| # | Caso | Resultado Esperado |
|---|------|-------------------|
| 1 | Usar refresh token v1 después de rotar a v2 | 401, familia revocada |
| 2 | Siguiente request de víctima | 401 (forzar re-login) |

### 11.6 Pruebas Multi-Tab

| # | Caso | Resultado Esperado |
|---|------|-------------------|
| 1 | Tab A hace refresh | Tab B sigue funcionando (nuevo token compartido) |
| 2 | Tab A hace logout | Tab B detecta 401 en siguiente request |

### 11.7 Pruebas Portal

| # | Caso | Resultado Esperado |
|---|------|-------------------|
| 1 | Login portal | Cookies portal seteadas |
| 2 | Usar cookie portal en endpoint interno | 401 |
| 3 | Usar cookie interna en endpoint portal | 401 |
| 4 | Refresh portal | Nuevas cookies portal |

### 11.8 Pruebas de Permisos

| # | Caso | Resultado Esperado |
|---|------|-------------------|
| 1 | Usuario con permisos accede a módulo | 200 |
| 2 | Usuario sin permisos accede a módulo | 403 (no 401) |
| 3 | Admin revoca sesión de otro usuario | Sesión revocada |

### 11.9 Pruebas de Filtros

| # | Caso | Resultado Esperado |
|---|------|-------------------|
| 1 | Filtros de sucursal siguen funcionando | Datos filtrados correctamente |
| 2 | Contexto de usuario se mantiene | Mismos permisos antes/después de refresh |

### 11.10 Pruebas de Build

| # | Caso | Resultado Esperado |
|---|------|-------------------|
| 1 | `npm run build` frontend | 0 errores |
| 2 | `python -m pytest` backend | Tests pasan |

### 11.11 Pruebas de Seguridad

| # | Caso | Resultado Esperado |
|---|------|-------------------|
| 1 | `document.cookie` | No contiene tokens (httpOnly) |
| 2 | `localStorage` | Sin JWT |
| 3 | `sessionStorage` | Sin JWT |
| 4 | Logs del servidor | Sin tokens |
| 5 | Response body después de login (final) | Sin token (solo en transición) |

---

## 12. RIESGOS

### 12.1 Loops de Refresh

**Descripción:** Frontend entra en loop infinito de refresh si hay bug.

**Mitigación:**
- Contador de reintentos (máx 3)
- No hacer refresh si el request era a `/auth/refresh`
- Timeout entre reintentos

### 12.2 Race Conditions Multi-Tab

**Descripción:** Dos tabs hacen refresh simultáneo, una invalida el token de la otra.

**Mitigación:**
- Mutex/semáforo en frontend
- Primera que obtiene refresh lo guarda
- Segunda usa el token guardado

```javascript
let refreshPromise = null;

async function doRefresh() {
  if (refreshPromise) {
    return refreshPromise;
  }
  
  refreshPromise = api.post('/auth/refresh');
  try {
    await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}
```

### 12.3 Logout Incompleto

**Descripción:** Cookie no se elimina por error de path/domain.

**Mitigación:**
- Test explícito de logout
- Verificar que las cookies tienen el path correcto
- Frontend limpia estado local aunque backend falle

### 12.4 Cookies Path/Domain

**Descripción:** Cookie seteada con path incorrecto no se envía.

**Mitigación:**
- Access: `path=/` siempre
- Refresh: `path=/api/auth/refresh` exacto
- Test en múltiples browsers

### 12.5 Reloj/Expiración

**Descripción:** Diferencia de reloj entre cliente y servidor causa expiraciones inesperadas.

**Mitigación:**
- Access token con margen (15 min + 30 seg)
- Refresh proactivo cuando quedan < 60 segundos
- Usar tiempo del servidor, no del cliente

### 12.6 Compatibilidad Preview/Dominio Real

**Descripción:** Funciona en preview pero falla en dominio personalizado.

**Mitigación:**
- Probar en dominio personalizado ANTES de eliminar código legacy
- Mantener período de transición largo
- Documentar diferencias de CORS si las hay

---

## 13. RECOMENDACIÓN FINAL

### 13.1 Tiempos Sugeridos

| Token | Duración Recomendada | Justificación |
|-------|---------------------|---------------|
| **Access Token** | **15 minutos** | Balance entre seguridad y UX (refresh frecuente pero invisible) |
| **Refresh Token Interno** | **7 días** | Usuarios internos tienen sesiones largas (jornada laboral) |
| **Refresh Token Portal** | **24 horas** | Proveedores tienen sesiones más cortas y menor confianza |

### 13.2 Orden de Implementación

**Recomendación:** Implementar primero en **usuarios internos**.

**Razones:**
1. Mayor control sobre el ambiente
2. Usuarios pueden reportar problemas directamente
3. Portal tiene menos carga de desarrollo (menos endpoints)
4. Si hay bugs, afecta solo al equipo interno primero

### 13.3 Validar Dominio Personalizado Primero

**Recomendación:** SÍ validar en dominio real antes de implementar refresh tokens.

**Razones:**
1. Las cookies pueden comportarse diferente en dominio personalizado
2. CORS puede tener configuración diferente
3. Mejor validar la base antes de agregar complejidad

**Secuencia sugerida:**
1. ✅ Validar AUTH en Preview (COMPLETADO 2025-04-27)
2. **Validar AUTH en dominio personalizado** (pendiente deploy)
3. Implementar refresh tokens

### 13.4 Conclusión

El sistema de refresh tokens propuesto:

- ✅ **No usa MongoDB** como fuente maestra (usa EDARSAHUB SQL)
- ✅ **No guarda tokens planos** (solo hash)
- ✅ **Mantiene EDARSAHUB como cerebro** (tabla Sesiones en SQL Server)
- ✅ **Mantiene separación portal/interno** (tablas y cookies separadas)
- ✅ **Tiene rollback** (período de transición, código dual)
- ✅ **Tiene pruebas definidas** (sección 11)
- ✅ **No implementa código todavía** (solo diseño)

---

**Documento generado:** 2025-04-27  
**Estado:** DISEÑO TÉCNICO COMPLETADO  
**Próximo paso:** Aprobar plan → Implementar Fase A
