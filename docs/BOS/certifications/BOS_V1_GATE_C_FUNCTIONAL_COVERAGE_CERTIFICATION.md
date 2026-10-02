# BOS V1 Gate C - Functional Coverage Certification R3

## Alcance
Certificacion evidence-only. R3 corrige exclusivamente el harness roto por R2; no implementa ni corrige dominios funcionales.

## Matriz obligatoria
- comercial: comercial | ventas
- costos_margenes: costos | margen
- finanzas_tesoreria: finanzas | tesoreria | cxp | pago
- inventarios: inventario | almacen
- clientes_crm: cliente | crm
- operaciones: operacion | operaciones
- administracion: administracion | admin

## Regla de evidencia
Cada dominio requiere evidencia en el corpus del repositorio y en al menos un resultado terminal elegible del Universal Worker. Son elegibles solo resultados con certification CERTIFIED o CERTIFIED_READ_ONLY, percent_complete=100 y production_touched=false.

El nombre job_id se conserva como trazabilidad, pero no se acepta como unica representacion semantica de evidencia. Si un token no aparece en job_id pero si aparece en el contenido estructurado de un resultado terminal elegible, el caso se clasifica TEST_FALSE_NEGATIVE respecto al criterio anterior. Si no existe evidencia terminal elegible ni evidencia de repositorio, o falta cualquiera de ambas condiciones, se clasifica REAL_MISSING_EVIDENCE y el Gate falla cerrado.

## Restricciones
No Produccion. No SQL. No Mongo. No cambios al Universal Worker, Supervisor o watchdog. No jobs artificiales para satisfacer nombres. No cambios funcionales fuera de esta prueba y este dossier.
