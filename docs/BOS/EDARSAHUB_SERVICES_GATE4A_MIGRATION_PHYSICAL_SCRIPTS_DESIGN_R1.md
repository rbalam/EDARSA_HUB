# EDARSAHUB Services - Gate 4A Physical Migration Scripts Design R1

## Estado
Este Gate materializa exclusivamente el primer par forward/rollback versionado para Services Foundation. No ejecuta SQL ni workflows de migracion.

## Alcance R1
Se materializan solo:
- Services_Professions
- Services_Specialties

No se materializan aun Providers, Credentials, Engagements, Construction, Fabrication, Interiors ni Land porque requieren un cierre adicional de tipos exactos de FK y/o subgates condicionales antes de generar DDL seguro.

## Reglas del script
- DB_NAME debe ser EDARSAHUB.
- HRLectura aborta como writer.
- XACT_ABORT + transaccion + TRY/CATCH.
- CREATE solo si el objeto no existe.
- rollback bloqueado si hay datos.
- rollback bloqueado si ya existen dependencias Services.
- no Production.

## Validacion pendiente antes de cualquier ejecucion
1. certificar writer canonico Development;
2. certificar environment development;
3. certificar backup/restore point;
4. auditar naming/auditoria contra vecinos actuales;
5. probar sintaxis/idempotencia en dry-run;
6. revisar si CreatedAt/UpdatedAt deben usar helpers/convenciones fisicas diferentes antes de ejecutar.

## Siguiente paso
Gate 4A CERT READ_ONLY sobre estos artefactos. Solo despues se autoriza Gate 4A-R2 para ampliar Foundation con Providers/Credentials/ServiceCatalog/Resources, siempre con tipos exactos de FK medidos. Ningun script se ejecuta en este Gate.
