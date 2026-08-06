# Modelo canónico RBAC

## Flujo

`Usuario → Roles → Módulos → Acciones → Permisos → Alcances → Autorización → Bitácora`

## Componentes canónicos

- `Usuario_Catalogo`
- `Usuario_Roles`
- `Usuario_Modulos`
- `Usuario_Acciones`
- `Usuario_PermisosRolModulo`
- `Usuario_RBAC_Asignacion`
- `Usuario_RBAC_Bitacora`

## Regla

La autorización efectiva se resuelve en backend. La ocultación frontend no sustituye la validación de seguridad.
