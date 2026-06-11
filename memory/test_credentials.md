# Credenciales de prueba — EDARSA HUB

## CRM principal (interno)
- **Email:** admin@edarsa.com
- **Password:** pruebas123
- **Rol:** SuperAdministrador

## Portal Inteligencia Comercial (EXTERNO) — /inteligencia-comercial
- **Email:** socio@externo.com
- **Password:** socio123
- **Unidades asignadas:** ORIGEN, LA ESTELAR (ESTELAR)
- Creado vía: Proveedores → pestaña "Usuarios Inteligencia"
- Login externo propio (cookie httpOnly `edarsa_intel_access_token`)

> Nota: los usuarios externos del portal de inteligencia se almacenan en SQL
> (`dbo.Portal_Inteligencia_Usuarios`), NO en MongoDB.
