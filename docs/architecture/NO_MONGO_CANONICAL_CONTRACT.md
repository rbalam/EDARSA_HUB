# Contrato canónico NO-MONGO — EDARSAHUB

## Estado arquitectónico

EDARSAHUB SQL es la fuente única productiva para módulos críticos y nuevos desarrollos.

MongoDB no puede utilizarse como:

- fuente primaria;
- fallback productivo;
- caché productiva;
- repositorio auxiliar operativo;
- mecanismo de permisos, RBAC, usuarios o scopes;
- fuente de dashboards;
- persistencia de jobs;
- fuente comercial, financiera o de inventarios.

## Qué constituye una regresión Mongo

Una auditoría solo debe declarar dependencia Mongo si existe evidencia de al menos uno de estos elementos:

1. import de `pymongo`, `motor`, `MongoClient` o `AsyncIOMotorClient`;
2. creación de conexión Mongo;
3. lectura/escritura Mongo real;
4. operaciones como `find_one`, `insert_one`, `update_one`, `delete_one`, etc.;
5. fallback productivo hacia Mongo;
6. Mongo como fuente de verdad o caché operativa.

Un grep de la palabra `mongo` no es evidencia suficiente.

## Nombres SQL históricos permitidos

Los siguientes nombres pueden existir en SQL Server por razones de migración o compatibilidad histórica:

- `PayloadMongo`
- `MongoId`
- `MigradoDesdeMongo`
- `ColeccionOrigen`

Su presencia no significa que exista MongoDB runtime.

No deben renombrarse sin una migración de esquema específica, auditada y reversible.

## Auditoría financiera

Estado esperado:

- persistencia exclusivamente en EDARSAHUB SQL;
- sin fallback Mongo;
- sin `_get_mongo_db`;
- sin `_guardar_mongo`;
- sin `to_mongo_doc`;
- `PayloadMongo` puede continuar como nombre de columna SQL histórica.

## API Connections

Estado esperado:

- EDARSAHUB SQL es fuente única;
- CREATE y UPDATE no sincronizan a Mongo;
- no existe `_sync_to_mongo_cache`;
- `sync_all_to_mongo_cache()` se conserva temporalmente solo como contrato público legacy del endpoint `/api-connections/sync-cache`;
- dicho endpoint no realiza IO Mongo y únicamente verifica/enumera conexiones canónicas SQL.

El nombre `sync-cache` es deuda técnica de compatibilidad API.

## Tests canónicos

Los tests NO-MONGO deben validar comportamiento y estructura real:

- ausencia de drivers Mongo;
- ausencia de IO Mongo;
- ausencia de helpers privados muertos;
- ausencia de fallback productivo;
- comportamiento SQL-only.

No deben depender de strings artificiales como:

- `EDARSAHUB_NO_MONGO_LEGACY_STUB`
- `EDARSAHUB_NO_MONGO_LEGACY_SERIALIZER`

salvo que esos identificadores formen parte real del contrato productivo.

## Historia relevante

Commits históricos de referencia identificados durante auditoría:

- `dbfd5024772509a870e42319e9615b17cc424fe4`
  - retiro de compatibilidad Mongo muerta en Auditoría.
- `a3a7fd9870e82114aa2271093f03f0dbb11ac44f`
  - retiro de semántica legacy Mongo cache en API Connections.

Estos commits pertenecían a una rama lateral y no deben aplicarse mediante cherry-pick sin auditoría.

Su lógica puede reutilizarse quirúrgicamente cuando sea compatible con HEAD actual.

## Procedimiento obligatorio para futuras auditorías

Antes de reportar una dependencia Mongo:

1. leer este documento;
2. distinguir nombres SQL históricos de runtime Mongo;
3. buscar imports y drivers;
4. buscar conexiones reales;
5. buscar operaciones IO;
6. buscar fallback productivo;
7. identificar callers;
8. verificar fuente de verdad;
9. revisar historia Git antes de parchear;
10. no modificar runtime únicamente para satisfacer un grep o marcador textual.

## Deuda técnica

Pendientes permitidos para una versión posterior, siempre que continúen siendo SQL-only:

- renombrar endpoints legacy como `/sync-cache`;
- renombrar funciones públicas cuyo nombre conserva `mongo`;
- evaluar migración de columnas SQL históricas `PayloadMongo`, `MongoId`, etc.;
- limpiar documentación histórica que describa arquitecturas Mongo ya retiradas.

Cualquier renombrado debe preservar compatibilidad, RBAC, trazabilidad y rollback.
