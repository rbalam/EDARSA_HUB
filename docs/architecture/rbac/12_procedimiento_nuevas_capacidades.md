# Procedimiento obligatorio para nuevas capacidades

Antes de crear menú, tab, botón, checkbox, reporte, proceso, filtro, catálogo, configuración, endpoint o acción:

1. Auditar módulo existente.
2. Auditar acción existente.
3. Auditar permiso existente.
4. Auditar alcance existente.
5. Reutilizar estructura canónica.
6. Definir roles.
7. Confirmar SUPERADMIN.
8. Crear guard backend.
9. Crear visibilidad frontend.
10. Crear validación de alcance.
11. Crear bitácora.
12. Crear pruebas.
13. Actualizar esta documentación.

## Prohibiciones

- No hardcode.
- No MongoDB.
- No permisos implícitos.
- No bypass por nombre de rol.
- No agregar elementos funcionales sin RBAC.
