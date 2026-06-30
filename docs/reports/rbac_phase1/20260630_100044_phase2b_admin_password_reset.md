# Fase 2B admin password reset

- Fecha: 2026-06-30T10:00:44
- Usuario objetivo: `admin@edarsa.com`
- Password plano: no impreso, no guardado
- Hash bcrypt: no impreso, no guardado en reporte
- Tabla actualizada: `dbo.Usuario_Catalogo.PasswordHashTexto`

## Estado previo

```
  {'UsuarioID': 1, 'Email': 'admin@edarsa.com', 'Username': 'admin@edarsa.com', 'Activo': True, 'tiene_password_hash': 'SI', 'CodigoRol': 'SUPERADMIN', 'NombreRol': 'SuperAdministrador', 'EsPrincipal': True, 'rol_asignacion_activa': True}
  {'UsuarioID': 1, 'Email': 'admin@edarsa.com', 'Username': 'admin@edarsa.com', 'Activo': True, 'tiene_password_hash': 'SI', 'CodigoRol': 'SUPERADMIN', 'NombreRol': 'SuperAdministrador', 'EsPrincipal': False, 'rol_asignacion_activa': False}
  {'UsuarioID': 1, 'Email': 'admin@edarsa.com', 'Username': 'admin@edarsa.com', 'Activo': True, 'tiene_password_hash': 'SI', 'CodigoRol': 'SUPERADMIN', 'NombreRol': 'SuperAdministrador', 'EsPrincipal': False, 'rol_asignacion_activa': False}
```

## Estado posterior

```
  {'UsuarioID': 1, 'Email': 'admin@edarsa.com', 'Username': 'admin@edarsa.com', 'Activo': True, 'tiene_password_hash': 'SI', 'CodigoRol': 'SUPERADMIN', 'NombreRol': 'SuperAdministrador', 'EsPrincipal': True, 'rol_asignacion_activa': True}
  {'UsuarioID': 1, 'Email': 'admin@edarsa.com', 'Username': 'admin@edarsa.com', 'Activo': True, 'tiene_password_hash': 'SI', 'CodigoRol': 'SUPERADMIN', 'NombreRol': 'SuperAdministrador', 'EsPrincipal': False, 'rol_asignacion_activa': False}
  {'UsuarioID': 1, 'Email': 'admin@edarsa.com', 'Username': 'admin@edarsa.com', 'Activo': True, 'tiene_password_hash': 'SI', 'CodigoRol': 'SUPERADMIN', 'NombreRol': 'SuperAdministrador', 'EsPrincipal': False, 'rol_asignacion_activa': False}
```
