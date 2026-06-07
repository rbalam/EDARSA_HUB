# EDARSA HUB - Credenciales de Prueba

## Usuario SuperAdmin (Principal)
- **Email:** `ricardo@edarsa.com.mx`
- **Contraseña:** `Ricardo2835!`  ⚠️ NOTA (2026-06-07): el login devuelve "Credenciales inválidas"; al parecer la contraseña fue cambiada/está en proceso de reset. Para pruebas usar la cuenta Administrador de abajo.
- **Rol:** SUPERADMIN
- **Permisos:** Acceso global a todos los módulos y menús de sistema

## Usuario Administrador (Legacy)
- **Email:** `admin@edarsa.com`
- **Contraseña:** `pruebas123`  (actualizada 2026-06-07)
- **Rol:** **SUPERADMIN** (promovido 2026-06-07 a solicitud del usuario; antes era ADMIN). UsuarioID=1.
- **Permisos:** 28 módulos visibles. Tiene `unidades_permitidas` asignadas y `unidad_activa`.

## Usuario SUPERADMIN de QA (creado 2026-06-07 para validación de auditoría)
- **Email:** `qa.superadmin@edarsa.com`
- **Contraseña:** `QaSuper2026!`
- **Rol:** SUPERADMIN (RolID=6) · UsuarioID=22 · PublicUUID `5498a725-62ef-4df5-a83f-d8fea9520e50`
- **Login:** OK (verificado). 28 módulos visibles.
- ⚠️ **Sin unidades asignadas**: `access-context` devuelve `unidades_permitidas=0`, `unidad_activa=None` (las unidades provienen de asignación explícita, NO se auto-otorgan a SUPERADMIN). Útil para auditar pantallas con filtro por unidad sin contexto.

## Notas
- Las credenciales se autentican contra EDARSAHUB_SQL (tabla Usuario_Catalogo)
- El token JWT expira en 15 minutos
- No usar credenciales de prueba mostradas en frontend (`admin@inventario.com`) - son legacy
- SUPERADMIN detectado por CodigoRol='SUPERADMIN' o NivelJerarquia >= 100

## URLs de Prueba
- **Frontend:** `https://erp-crm-enterprise-1.preview.emergentagent.com`
- **Backend Health:** `https://erp-crm-enterprise-1.preview.emergentagent.com/api/health`
- **Login:** `https://erp-crm-enterprise-1.preview.emergentagent.com/api/auth/login`
- **Menús:** `https://erp-crm-enterprise-1.preview.emergentagent.com/api/sistema/menus/usuario`
