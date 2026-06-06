# EDARSA HUB - Credenciales de Prueba

## Usuario SuperAdmin (Principal)
- **Email:** `ricardo@edarsa.com.mx`
- **Contraseña:** `Ricardo2835!`
- **Rol:** SUPERADMIN
- **Permisos:** Acceso global a todos los módulos y menús de sistema

## Usuario Administrador (Legacy)
- **Email:** `admin@edarsa.com`
- **Contraseña:** `admin123`
- **Rol:** Administrador
- **Permisos:** Acceso completo a todas las unidades de negocio

## Notas
- Las credenciales se autentican contra EDARSAHUB_SQL (tabla Usuario_Catalogo)
- El token JWT expira en 15 minutos
- No usar credenciales de prueba mostradas en frontend (`admin@inventario.com`) - son legacy
- SUPERADMIN detectado por CodigoRol='SUPERADMIN' o NivelJerarquia >= 100

## URLs de Prueba
- **Frontend:** `https://stock-tracker-990.preview.emergentagent.com`
- **Backend Health:** `https://stock-tracker-990.preview.emergentagent.com/api/health`
- **Login:** `https://stock-tracker-990.preview.emergentagent.com/api/auth/login`
- **Menús:** `https://stock-tracker-990.preview.emergentagent.com/api/sistema/menus/usuario`
