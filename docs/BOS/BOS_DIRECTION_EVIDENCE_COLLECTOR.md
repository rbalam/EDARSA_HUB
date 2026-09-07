# BOS Direccion - Recolector read-only de evidencia

## Objetivo
Construir el snapshot de avance BOS V1.0 exclusivamente a partir de los siete resultados terminales formales definidos por el manifest canonico.

## Fuente
El recolector recibe un directorio read-only que contiene archivos `<job_id>.json`. Solo busca los job IDs autorizados por `bos_program_manifest.py`. No enumera ni interpreta otros jobs como avance del Programa.

## Fail-closed
Un archivo faltante, ilegible, JSON invalido o con `job_id` distinto al esperado se trata como evidencia ausente. Un resultado valido pero no CERTIFIED puede ser leido por el collector, pero el motor de status no lo cuenta como avance.

## Snapshot
El snapshot `edarsahub.bos-direction-status.v1` incluye porcentaje global, estado de certificacion, cinco frentes, milestones, conteo de gates certificados y conteo de gates faltantes/no certificados.

## Restricciones
Este gate no escribe en SQL, Mongo, Worker, GitHub ni Production y no modifica el Tablero Ejecutivo congelado. Tampoco persiste snapshots.

## Siguiente gate
Conectar este collector a una fuente remota/read-only autorizada de `worker/results` y publicar de forma idempotente el snapshot canónico de Direccion con timestamp, SHA de evidencia e historico de cambios.
