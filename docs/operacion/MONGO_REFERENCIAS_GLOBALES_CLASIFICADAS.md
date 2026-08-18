# EDARSAHUB — Mongo — referencias globales clasificadas

Estado: vigente.

## Conclusión

En la auditoría estática realizada durante el cierre V1.0 se detectó un único
import directo de `pymongo`/`motor` dentro del backend versionado.

Ese import está en:

- `backend/auditorias_p5/backup_p5_07_auth_sql_only_20260606_062908/core/security.py`

Clasificación:

`CODIGO_LEGACY_BACKUP_NO_RUNTIME`

No forma parte del código productivo `backend/core/security.py` ni se encontró
un import exacto o registro runtime de ese módulo backup.

Por tanto, este hallazgo NO constituye dependencia Mongo productiva.

## Dominios críticos auditados

No se detectaron imports directos de clientes Mongo en:

- Scheduler;
- RBAC;
- Compras;
- Inventarios;
- Comercial;
- Operaciones.

SQL EDARSAHUB continúa siendo la única fuente canónica productiva.

## Referencias mongo_stub

Existen referencias de compatibilidad como:

- `core.mongo_stub`;
- `get_stub_database`;
- nombres, comentarios y tests asociados.

Clasificación:

`STUB_COMPATIBILIDAD`

Una referencia a `mongo_stub` no demuestra conexión ni I/O Mongo.

## Referencias históricas

El repositorio conserva:

- backups de auditorías;
- documentación histórica;
- nombres legacy;
- comentarios;
- tests contractuales;
- código de transición;
- archivos `.bak`.

Estas referencias pueden describir fases anteriores donde existió fallback o
integración Mongo.

Su presencia en el repositorio no significa que participen en el runtime actual.

## Error de auditoría que no debe repetirse

No utilizar:

`grep -R mongo`

como prueba de dependencia productiva.

Ese método mezcla:

- código runtime;
- backups;
- tests;
- comentarios;
- stubs;
- documentación;
- nombres históricos.

La clasificación debe basarse en linaje y ejecución.

## MongoDB prohibido como dependencia productiva

MongoDB no puede ser:

- fuente;
- fallback;
- cache productivo;
- lock;
- configuración;
- autenticación;
- almacenamiento paralelo;
- sincronización productiva;
- inicialización indirecta.

## Regla de reapertura

NO repetir una auditoría Mongo masiva únicamente porque aparezca una referencia
textual ya clasificada.

Reabrir únicamente con evidencia positiva nueva:

1. nuevo import de `pymongo`, `motor` o cliente equivalente en código runtime;
2. URI o cliente Mongo real;
3. conexión efectiva;
4. I/O Mongo demostrado;
5. cambio de implementación de `mongo_stub`;
6. endpoint/job que dependa de Mongo;
7. modificación del linaje productivo;
8. requisito explícito que reactive Mongo.

## Regla sobre backups

Los backups históricos bajo rutas de auditoría no son código productivo por
ubicación únicamente.

Aun así, no deben eliminarse automáticamente.

Antes de retirar un backup:

- validar propósito histórico;
- validar política de repositorio;
- validar que no exista consumidor;
- preservar trazabilidad requerida.

La clasificación de un backup histórico no autoriza a reintroducir su lógica en
el runtime.

## Criterio de cierre

Una referencia Mongo queda cerrada cuando tiene:

- archivo;
- clasificación;
- condición runtime;
- consumidor o ausencia demostrada;
- regla explícita para reapertura.

Con esta clasificación no debe repetirse la investigación desde cero.
