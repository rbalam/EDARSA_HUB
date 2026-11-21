# ARBITROA BOS — A4 Foundation Implementation V1

## Alcance
Implementacion minima del Gate A4 conforme al contrato A3.

Incluye exclusivamente:
1. ARBITROA_Deportes
2. ARBITROA_Organizaciones
3. ARBITROA_Afiliaciones
4. ARBITROA_OrganizacionPersonas
5. ARBITROA_Sedes
6. ARBITROA_Canchas
7. ARBITROA_Reglamentos
8. Registro del satelite ARBITROA en Sistema_Modulos, Sistema_ModulosMenus y Sistema_ModulosPermisos.
9. Namespace backend/modules/arbitroa sin crecer backend/core.

No incluye tablas A5-A13, APIs de negocio, frontend funcional, GEO, SAFE, pagos ni automatizaciones.

## Principios
- EDARSAHUB SQL Server sigue siendo la unica fuente canonica.
- Gobierno_Persona, Usuario_Catalogo, Sistema_Empresas, Cliente_Catalogo y Gobierno_Documento se reutilizan.
- No MongoDB.
- No IDs hardcodeados.
- DDL idempotente, transaccional y fail-closed ante colisiones incompatibles.
- Production prohibida.
- SUPERADMIN conserva visibilidad global por el resolver BOS existente; no se asignan automaticamente permisos a roles ordinarios en A4.

## Ejecucion
El archivo de migracion queda versionado en Desarrollo y solo puede ejecutarse mediante el canal SQL_MIGRATION_DEVELOPMENT del Universal Worker, nunca con HRLectura como writer.

## Rollback
Mientras las tablas A4 permanezcan vacias y sin consumidores certificados, el rollback puede retirar exclusivamente los objetos ARBITROA creados por este gate en orden inverso. Una vez existan datos oficiales, se conserva la informacion y el rollback pasa a deshabilitar capacidad/rutas.
