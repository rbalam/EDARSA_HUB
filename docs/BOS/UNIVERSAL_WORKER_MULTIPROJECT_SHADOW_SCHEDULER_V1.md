# Universal Worker Multi-Project Shadow Scheduler V1

Estado: SHADOW ONLY. No ejecuta jobs, no mueve archivos de lifecycle y no reemplaza al Universal Worker actual.

## Objetivo
Simular decisiones de scheduling multiproyecto para validar concurrencia segura antes de cualquier cutover.

## Metadata opcional
Los jobs worker-job.v2 pueden incorporar scheduling con project_id, bounded_context, resource_claims, conflict_domains, priority_class, fairness_weight y max_parallelism.

Los jobs legacy siguen siendo válidos. Sin metadata reciben defaults conservadores LEGACY_GLOBAL + GLOBAL_GIT_WRITER.

## Reglas
- READ_ONLY disjunto puede proponerse en paralelo.
- MUTATION solo se considera paralela con metadata explícita y recursos disjuntos.
- Recursos compartidos y dominios globales se serializan.
- max_parallelism limita slots por proyecto.
- fairness ponderado evita starvation.
- Shadow no adquiere locks ni ejecuta jobs.

## Cutover
No existe cutover en este Gate. El dispatcher actual sigue siendo la única autoridad.
