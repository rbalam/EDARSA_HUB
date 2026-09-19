# AH2 - Registry Foundation V1

AH2 implementa contratos versionados e in-memory para Agent Registry y Skill Registry en `backend/modules/agent_harness`, respetando Core Slimming. No crea persistencia SQL porque AH1 demostro que no existen tablas canonicas dedicadas y este gate no necesita inventarlas para validar el modelo.

El Registry no autoriza ejecuciones. Solo declara identidad, version, dominios, capacidades requeridas/ceiling, scopes, riesgo, clasificacion de datos, budgets, procedencia y executors permitidos. La autorizacion efectiva sigue en RBAC + Capability Policy + Procedure Policy + Execution Gate.

Fail-closed: schemas invalidos, riesgos/descripciones desconocidas, executors fuera del allow-list, versiones duplicadas, dependencias que tambien son conflictos y skills externas APPROVED sin checksum/licencia son rechazadas.

Executors reconocidos en V1: worker, ai_gateway, agent_reach y communications. No shell arbitrario.

Persistencia durable y cualquier DDL quedan fuera de AH2 y requieren gate posterior con justificacion REUSE/EXTEND/CREATE basada en evidencia.
