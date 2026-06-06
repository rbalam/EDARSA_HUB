# P0_PORTAL_PROVEEDORES_AUTH_01_REPORT

**Fecha**: 2025-12-27  
**Tipo**: Corrección de Seguridad P0  
**Archivo Modificado**: `/app/backend/routes/portal_proveedores.py`  
**Estado**: ✅ CORREGIDO Y VALIDADO

---

## 1. PROBLEMA DETECTADO

### 1.1 Vulnerabilidad Original

8 endpoints administrativos del Portal de Proveedores estaban expuestos **sin autenticación**:

| # | Endpoint | Método | Riesgo |
|---|----------|--------|--------|
| 1 | `/admin/all-suppliers` | GET | Exposición de todos los proveedores |
| 2 | `/admin/pending-suppliers` | GET | Exposición de proveedores pendientes |
| 3 | `/admin/approve-supplier` | POST | Aprobación/rechazo no autorizado |
| 4 | `/admin/reset-password` | POST | Reset de contraseñas sin control |
| 5 | `/admin/supplier/{id}` | GET | Consulta de detalles sensibles |
| 6 | `/admin/invoices` | GET | Acceso a todas las facturas |
| 7 | `/admin/supplier/{id}` | DELETE | Eliminación de proveedores |
| 8 | `/servers` | GET | Exposición de infraestructura |

### 1.2 Impacto

- Exposición de datos sensibles (RFC, razón social, datos bancarios)
- Manipulación no autorizada de proveedores
- Posible suplantación de identidad via reset de password
- Exposición de configuración de servidores

---

## 2. CORRECCIÓN IMPLEMENTADA

### 2.1 Helper de Autenticación Admin

Se creó la función `require_portal_admin()` que implementa **autenticación + autorización**:

```python
async def require_portal_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True))
) -> dict:
    """
    1. Verifica token JWT válido
    2. Rechaza tokens de proveedor externo (type=portal_supplier)
    3. Busca usuario en MongoDB
    4. Valida rol SuperAdministrador o Administrador
    """
```

### 2.2 Endpoints Protegidos

Todos los 8 endpoints ahora incluyen:
```python
async def endpoint_name(..., current_user: dict = Depends(require_portal_admin)):
```

### 2.3 Comportamiento de Seguridad

| Escenario | Código HTTP | Mensaje |
|-----------|-------------|---------|
| Sin token | 403 | "Not authenticated" |
| Token de proveedor | 401 | "TOKEN_TIPO_INVALIDO" |
| Usuario interno sin permiso | 403 | "PERMISO_DENEGADO" |
| Admin autorizado | 200 | Respuesta normal |

---

## 3. VALIDACIONES REALIZADAS

### 3.1 Sin Autenticación → Rechazado

```bash
curl /api/portal/admin/all-suppliers
# HTTP 403 - {"detail":"Not authenticated"}
```

### 3.2 Proveedor Externo → Rechazado

```bash
curl /api/portal/admin/all-suppliers -H "Authorization: Bearer {PORTAL_TOKEN}"
# HTTP 401 - {"detail":{"error":"TOKEN_TIPO_INVALIDO",...}}
```

### 3.3 Usuario Interno sin Permiso → Rechazado

```bash
curl /api/portal/admin/all-suppliers -H "Authorization: Bearer {USER_TOKEN}"
# HTTP 403 - {"detail":{"error":"PERMISO_DENEGADO","rol_actual":"Usuario",...}}
```

### 3.4 Admin Autorizado → Permitido

```bash
curl /api/portal/admin/all-suppliers -H "Authorization: Bearer {ADMIN_TOKEN}"
# HTTP 200 - [lista de proveedores]
```

### 3.5 Sin Regresión en Portal Proveedor

| Endpoint | Estado |
|----------|--------|
| `/auth/login` | ✅ Funciona |
| `/auth/me` | ✅ Funciona |
| `/invoices` | ✅ Funciona |
| `/account-status` | ✅ Funciona |
| `/auth/logout` | ✅ Funciona |

### 3.6 Sin Regresión en Auth Interna

| Endpoint | Estado |
|----------|--------|
| `/auth/login` | ✅ Funciona |
| `/auth/me` | ✅ Funciona |
| `/users` | ✅ Funciona |
| `/compras/dashboard` | ✅ Funciona |

---

## 4. CAMBIOS EN CÓDIGO

### 4.1 Antes (VULNERABLE)

```python
@portal_router.get("/admin/all-suppliers")
async def get_all_suppliers():
    # Sin autenticación - VULNERABLE
    suppliers = await db.portal_suppliers.find(...).to_list(500)
    return suppliers
```

### 4.2 Después (SEGURO)

```python
@portal_router.get("/admin/all-suppliers")
async def get_all_suppliers(current_user: dict = Depends(require_portal_admin)):
    # Con autenticación interna + validación de rol
    suppliers = await db.portal_suppliers.find(...).to_list(500)
    return suppliers
```

---

## 5. ARQUITECTURA DE SEGURIDAD

### 5.1 Separación de Autenticaciones

```
┌─────────────────────────────────────────────────────────────┐
│                    PORTAL DE PROVEEDORES                     │
├─────────────────────────┬───────────────────────────────────┤
│   PROVEEDOR EXTERNO     │       ADMIN INTERNO EDARSA        │
├─────────────────────────┼───────────────────────────────────┤
│ Login: RFC + Password   │ Login: Email + Password           │
│ Cookie: edarsa_portal_* │ Cookie: edarsa_access_token       │
│ Token type: portal_supplier │ Token type: internal          │
│ Acceso: Solo sus datos  │ Acceso: Todos los proveedores     │
│ Endpoints: /auth/*, /invoices, etc │ Endpoints: /admin/*   │
└─────────────────────────┴───────────────────────────────────┘
```

### 5.2 Roles Permitidos para Admin

- `SuperAdministrador` ✅
- `Administrador` ✅
- `Supervisor` ❌
- `Usuario` ❌

---

## 6. DEUDA TÉCNICA

### 6.1 Permiso Granular Pendiente

Actualmente se valida por rol legacy (`SuperAdministrador`/`Administrador`). 

**Recomendación futura**: Crear permiso RBAC específico:
- `PORTAL_PROVEEDORES_ADMIN` - Acceso completo a admin del portal
- `PORTAL_PROVEEDORES_VER` - Solo lectura de proveedores
- `PORTAL_PROVEEDORES_APROBAR` - Aprobar/rechazar

---

## 7. ROLLBACK

En caso de necesitar revertir:

```bash
git log --oneline -5  # Identificar commit anterior
git checkout {COMMIT_ID} -- /app/backend/routes/portal_proveedores.py
sudo supervisorctl restart backend
```

---

## 8. RESUMEN

| Métrica | Valor |
|---------|-------|
| Endpoints corregidos | 8 |
| Líneas modificadas | ~100 |
| Tests de regresión | 10+ |
| Tiempo de corrección | ~30 min |
| Severidad original | P0 CRÍTICO |
| Estado actual | ✅ SEGURO |

---

*Documento generado: 2025-12-27*
