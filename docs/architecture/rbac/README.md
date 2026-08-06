# Arquitectura RBAC de EDARSAHUB

Documentación oficial, versionada y obligatoria de usuarios, roles, permisos, alcances y autorización.

## Máximas

- Nunca adivines: primero evidencia exacta.
- SQL EDARSAHUB es la única fuente canónica.
- MongoDB no puede ser fuente, fallback, cache ni dependencia runtime.
- SUPERADMIN es la máxima autoridad efectiva.
- Ningún elemento funcional puede implementarse sin RBAC, alcance, validación backend, visibilidad frontend y auditoría.
- Toda modificación RBAC debe actualizar estos documentos.

## Evidencia

- Rama: `Edarsahub_Desarrollo`
- HEAD: `28a1cfd28c6323c2f2d654c68e34d29c3a6b4d75`
- Login SQL de auditoría: `HRLectura`
- DML ejecutado: `NO`
- Datos modificados: `NO`

## Índice

1. [Modelo canónico](01_modelo_canonico.md)
2. [Tablas SQL](02_tablas_sql.md)
3. [Usuarios e identidades](03_usuarios_identidades.md)
4. [Roles y jerarquía](04_roles_jerarquia.md)
5. [Módulos, acciones y permisos](05_modulos_acciones_permisos.md)
6. [Alcances y contexto](06_alcances_contexto_efectivo.md)
7. [Backend, rutas y helpers](07_backend_rutas_helpers.md)
8. [Frontend, menús y guards](08_frontend_menus_guards.md)
9. [Seeds y migraciones](09_seeds_migraciones.md)
10. [Auditoría y bitácoras](10_bitacora_auditoria.md)
11. [Autorizaciones contextuales](11_autorizaciones_contextuales.md)
12. [Procedimiento para nuevas capacidades](12_procedimiento_nuevas_capacidades.md)
13. [Legacy y deuda técnica](13_legacy_deuda_tecnica.md)
