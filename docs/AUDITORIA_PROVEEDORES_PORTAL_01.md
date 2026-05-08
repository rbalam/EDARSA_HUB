# AUDITORIA_PROVEEDORES_PORTAL_01

**Fecha**: 2025-12-27  
**Módulo**: Portal de Proveedores  
**Archivo**: `/app/backend/routes/portal_proveedores.py`  
**Estado**: ✅ AUDITORÍA COMPLETADA - ✅ VULNERABILIDAD P0 CORREGIDA

---

## 1. ARQUITECTURA DEL PORTAL DE PROVEEDORES

### 1.1 Modelo de Autenticación Dual (CORRECTO)

El Portal de Proveedores implementa **DOS sistemas de autenticación completamente separados**:

| Tipo | Descripción | Método Auth | Cookie/Token | Alcance |
|------|-------------|-------------|--------------|---------|
| **A) Usuario Interno EDARSA HUB** | Empleados, admins | Email + Password | `edarsa_access_token` | Endpoints `/admin/*` |
| **B) Proveedor Externo** | Proveedores terceros | RFC + Password | `edarsa_portal_access_token` | Endpoints de proveedor |

### 1.2 Regla de Aislamiento

- Proveedor externo NO pertenece al menú Usuarios
- Proveedor externo NO tiene rol interno
- Proveedor externo NO puede ver otros proveedores
- Proveedor externo NO puede acceder a `/admin/*`
- Usuario interno puede administrar proveedores SI tiene permiso

---

## 2. DIAGNÓSTICO DE ENDPOINTS

### 2.1 Tabla de Diagnóstico Obligatoria

| Endpoint | Método | Tipo | Auth Esperada | Auth Actual | Usuario Permitido | Riesgo | Acción |
|----------|--------|------|---------------|-------------|-------------------|--------|--------|
| `/auth/register` | POST | login_proveedor | pública_controlada | pública | público | BAJO | OK - Control rate limit recomendado |
| `/auth/login` | POST | login_proveedor | pública_controlada | pública | público | BAJO | OK - No revela si RFC existe |
| `/auth/logout` | POST | proveedor_externo | proveedor_rfc_password | ninguna | proveedor | BAJO | OK - Solo limpia cookie |
| `/auth/me` | GET | proveedor_externo | proveedor_rfc_password | **OK (401)** | proveedor dueño | NINGUNO | ✅ PROTEGIDO |
| `/invoices` | GET | proveedor_externo | proveedor_rfc_password | **OK (401)** | proveedor dueño | NINGUNO | ✅ PROTEGIDO |
| `/invoices/upload` | POST | proveedor_externo | proveedor_rfc_password | **OK (401)** | proveedor dueño | NINGUNO | ✅ PROTEGIDO |
| `/invoices/{id}` | GET | proveedor_externo | proveedor_rfc_password | **OK (401)** | proveedor dueño | NINGUNO | ✅ PROTEGIDO |
| `/purchase-orders` | GET | proveedor_externo | proveedor_rfc_password | **OK (401)** | proveedor dueño | NINGUNO | ✅ PROTEGIDO |
| `/account-status` | GET | proveedor_externo | proveedor_rfc_password | **OK (401)** | proveedor dueño | NINGUNO | ✅ PROTEGIDO |
| `/saldos` | GET | proveedor_externo | proveedor_rfc_password | **OK (401)** | proveedor dueño | NINGUNO | ✅ PROTEGIDO |
| `/servers` | GET | config_admin | interna_edarsa | **NINGUNA (200)** | admin interno | **CRÍTICO** | ❌ AGREGAR AUTH INTERNA |
| `/admin/pending-suppliers` | GET | admin_interno | interna_edarsa | **NINGUNA (200)** | admin interno | **CRÍTICO** | ❌ AGREGAR AUTH INTERNA |
| `/admin/all-suppliers` | GET | admin_interno | interna_edarsa | **NINGUNA (200)** | admin interno | **CRÍTICO** | ❌ AGREGAR AUTH INTERNA |
| `/admin/approve-supplier` | POST | admin_interno | interna_edarsa | **NINGUNA (404)** | admin interno | **CRÍTICO** | ❌ AGREGAR AUTH INTERNA |
| `/admin/reset-password` | POST | admin_interno | interna_edarsa | **NINGUNA (404)** | admin interno | **CRÍTICO** | ❌ AGREGAR AUTH INTERNA |
| `/admin/supplier/{id}` | GET | admin_interno | interna_edarsa | **NINGUNA** | admin interno | **CRÍTICO** | ❌ AGREGAR AUTH INTERNA |
| `/admin/invoices` | GET | admin_interno | interna_edarsa | **NINGUNA (200)** | admin interno | **CRÍTICO** | ❌ AGREGAR AUTH INTERNA |
| `/admin/supplier/{id}` | DELETE | admin_interno | interna_edarsa | **NINGUNA** | admin interno | **CRÍTICO** | ❌ AGREGAR AUTH INTERNA |

### 2.2 Resumen de Riesgos

| Severidad | Cantidad | Descripción |
|-----------|----------|-------------|
| ✅ OK | 10 | Endpoints correctamente protegidos |
| ❌ CRÍTICO | 8 | Endpoints admin SIN autenticación |

---

## 3. VULNERABILIDADES DETECTADAS

### 3.1 P0-PORTAL-PROVEEDORES-AUTH-01: Endpoints Admin sin Autenticación

**Descripción**: Los endpoints `/admin/*` y `/servers` del Portal de Proveedores NO validan autenticación de usuario interno EDARSA HUB. Cualquier actor anónimo puede:

1. **Listar todos los proveedores** (`GET /admin/all-suppliers`)
2. **Ver proveedores pendientes** (`GET /admin/pending-suppliers`)
3. **Aprobar/rechazar proveedores** (`POST /admin/approve-supplier`)
4. **Resetear contraseñas de proveedores** (`POST /admin/reset-password`)
5. **Eliminar proveedores** (`DELETE /admin/supplier/{id}`)
6. **Ver todas las facturas** (`GET /admin/invoices`)
7. **Ver servidores disponibles** (`GET /servers`)

**Impacto**:
- Exposición de datos sensibles de proveedores (RFC, razón social, datos bancarios)
- Manipulación de estados de cuenta de proveedores
- Acceso no autorizado a información financiera
- Posible suplantación de identidad mediante reset de contraseñas

**Evidencia de Prueba**:
```bash
# Sin token - devuelve 200 con datos
curl -s https://edarsa-hub-preview.emergentagent.com/api/portal/admin/all-suppliers
# Resultado: HTTP 200 - Lista completa de proveedores

# Sin token - permite ejecutar lógica de negocio
curl -s -X POST https://edarsa-hub-preview.emergentagent.com/api/portal/admin/reset-password \
  -H "Content-Type: application/json" \
  -d '{"rfc":"ABC123456789","new_password":"hacked123"}'
# Resultado: HTTP 404 (busca el RFC - NO devuelve 401)
```

---

## 4. VALIDACIÓN DE ENDPOINTS DE PROVEEDOR

### 4.1 Aislamiento de Datos (CORRECTO)

Los endpoints de proveedor SÍ validan correctamente:

```python
# Ejemplo: /invoices filtrado por supplier_id del token
query = {"supplier_id": current_supplier["id"]}  # ✅ Correcto
```

Un proveedor autenticado:
- ✅ Solo ve sus propias facturas
- ✅ Solo ve su propio estado de cuenta
- ✅ Solo ve sus propios saldos
- ✅ No puede consultar otro proveedor cambiando parámetro

### 4.2 Prueba de Login Proveedor

```bash
# Login NO revela si RFC existe (mensaje genérico)
curl -s -X POST .../api/portal/auth/login \
  -H "Content-Type: application/json" \
  -d '{"rfc":"NOEXISTE123","password":"test"}'
# Resultado: {"detail":"RFC o contraseña incorrectos"} ✅
```

---

## 5. CORRECCIÓN REQUERIDA

### 5.1 Solución Propuesta

Importar y aplicar `get_current_user` de `core/security.py` a todos los endpoints `/admin/*`:

```python
from core.security import get_current_user

@portal_router.get("/admin/all-suppliers")
async def get_all_suppliers(current_user: dict = Depends(get_current_user)):
    # Validar permiso adicional si se requiere
    # ...existing logic...
```

### 5.2 Endpoints a Corregir

| # | Endpoint | Línea |
|---|----------|-------|
| 1 | `GET /admin/pending-suppliers` | 856 |
| 2 | `GET /admin/all-suppliers` | 867 |
| 3 | `POST /admin/approve-supplier` | 878 |
| 4 | `POST /admin/reset-password` | 912 |
| 5 | `GET /admin/supplier/{identifier}` | 970 |
| 6 | `GET /admin/invoices` | 991 |
| 7 | `GET /servers` | 1016 |
| 8 | `DELETE /admin/supplier/{supplier_id}` | 1027 |

---

## 6. ESTADO FINAL

| Categoría | Estado |
|-----------|--------|
| Endpoints Proveedor | ✅ SEGURO |
| Endpoints Admin | ✅ SEGURO (P0-PORTAL-PROVEEDORES-AUTH-01 CORREGIDO) |
| Aislamiento de Datos | ✅ CORRECTO |
| Login Proveedor | ✅ SEGURO |
| Arquitectura Dual | ✅ CORRECTA |

**CORRECCIÓN APLICADA**: Ver `/app/docs/P0_PORTAL_PROVEEDORES_AUTH_01_REPORT.md`

---

*Documento generado por auditoría automatizada - 2025-12-27*
*Actualizado post-corrección: 2025-12-27*
