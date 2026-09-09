# Cavas Corporativas - Certificacion de ejecucion SQL

Fecha UTC de ejecucion certificada: 2026-09-07

## Ejecucion real
- Workflow: `Cavas Corporativas Development Migration`
- Run: `#3`
- Run ID: `34165247416`
- Trigger commit: `8c077cd1fc85cff58a6e18f04daffe6ca6e99dcf`
- Rama: `Edarsahub_Desarrollo`
- Resultado del job: `success`
- Production touched: `false`

## Migracion inmutable
- Script: `backend/database/migrations/20260907_cavas_corporativas_core.sql`
- Blob SHA esperado y ejecutado: `072153e91c8721cbfa09cf6a0bb770ffab814494`
- Preflight: 0 tablas objetivo, 0 constraints objetivo y 0 indices objetivo preexistentes

## Permisos efectivos
- Database: `EDARSAHUB`
- Login/user: `HRLectura`
- CREATE TABLE: 1
- ALTER dbo: 1

## Ejecucion del runner
Runner canonico: `backend/tools/edarsahub_sql_runner.py --mode migrate`
Resultado: `Ejecucion completada correctamente.`

## Post-DDL read-only
- 8 tablas presentes
- 8 primary keys
- Indices requeridos presentes: `UX_CC_Alcance`, `IX_CC_Convenios_OrganizacionEstado`, `IX_CC_Autorizados_Identidad`, `IX_CC_Aplicaciones_Operacion`
- External foreign keys: 0
- Foreign keys: solo internas al dominio
- Seed rows: 0 en las 8 tablas

Tablas:
1. `dbo.CavasCorporativas_OrganizacionesRef`
2. `dbo.CavasCorporativas_Convenios`
3. `dbo.CavasCorporativas_ConvenioUnidades`
4. `dbo.CavasCorporativas_Autorizados`
5. `dbo.CavasCorporativas_Beneficios`
6. `dbo.CavasCorporativas_BeneficioAlcances`
7. `dbo.CavasCorporativas_Politicas`
8. `dbo.CavasCorporativas_AplicacionesBeneficio`

## Evidencia GitHub Actions
- Artifact: `cavas-corporativas-development-migration-34165247416`
- Artifact ID: `10033932063`
- Size: 4273 bytes
- Digest: `sha256:e23dd64b9bf3e010947917052a1ac05cd6c6cbe6940a05f3a851856e48101ffe`

## Conclusion
La migracion core de Cavas Corporativas fue ejecutada realmente en la base canonica EDARSAHUB y paso la certificacion read-only posterior. No hubo seed data, no hubo FKs externas y Produccion no fue tocada.
