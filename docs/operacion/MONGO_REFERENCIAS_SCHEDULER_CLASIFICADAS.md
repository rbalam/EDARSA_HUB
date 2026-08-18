# Mongo — referencias Scheduler clasificadas

Estado: registro técnico para evitar reauditorías por falsos positivos.

## Alcance

Este documento clasifica referencias dentro de `backend/core/scheduler`.
No afirma que todo EDARSAHUB esté libre de código legacy Mongo.

Una coincidencia textual no es una dependencia runtime.

## Dependencias runtime directas detectadas

No se detectaron imports directos de `pymongo` o `motor` en el árbol Scheduler analizado.

## Referencias a stub de compatibilidad

- `backend/core/scheduler/jobs/inventarios_detector_job.py:148` — `core.mongo_stub:get_stub_database` — clasificación: `STUB_COMPATIBILIDAD`, no evidencia automática de I/O Mongo.
- `backend/core/scheduler/jobs/pedidos_detector_job.py:80` — `core.mongo_stub:get_stub_database` — clasificación: `STUB_COMPATIBILIDAD`, no evidencia automática de I/O Mongo.
- `backend/core/scheduler/scheduler_manager.py:1956` — `core.mongo_stub:get_stub_database` — clasificación: `STUB_COMPATIBILIDAD`, no evidencia automática de I/O Mongo.
- `backend/core/scheduler/scheduler_manager.py:109` — `core.mongo_stub:get_stub_database` — clasificación: `STUB_COMPATIBILIDAD`, no evidencia automática de I/O Mongo.

## Coincidencias textuales

| Archivo | Línea | Texto |
|---|---:|---|
| `backend/core/scheduler/job_logger.py` | 316 | `Compatibilidad legacy: antes creaba índices Mongo.` |
| `backend/core/scheduler/jobs/alertas_excepciones_job.py` | 11 | `- NO MongoDB: el estado de notificación se persiste en dbo.Sistema_Excepciones_Estado.` |
| `backend/core/scheduler/jobs/cxp_sync_job.py` | 11 | `NO MongoDB. NO toca KPIs canónicos.` |
| `backend/core/scheduler/jobs/inteligencia_comercial_enrich.py` | 18 | `NO toca KPIs canónicos. NO imprime secretos. NO usa MongoDB.` |
| `backend/core/scheduler/jobs/inventarios_detector_job.py` | 148 | `from core.mongo_stub import get_stub_database` |
| `backend/core/scheduler/jobs/pedidos_detector_job.py` | 80 | `from core.mongo_stub import get_stub_database` |
| `backend/core/scheduler/routes.py` | 39 | `NOTA: MongoDB ELIMINADO del sistema. Este módulo ahora opera con StubDatabase` |
| `backend/core/scheduler/routes.py` | 47 | `logger.info("[SCHEDULER_ROUTES] Inicializado con StubDatabase - MongoDB ELIMINADO")` |
| `backend/core/scheduler/routes.py` | 61 | `def is_mongo_available() -> bool:` |
| `backend/core/scheduler/scheduler_manager.py` | 109 | `from core.mongo_stub import get_stub_database` |
| `backend/core/scheduler/scheduler_manager.py` | 128 | `logger.info("[SCHEDULER] Inicializando con StubDatabase - MongoDB ELIMINADO")` |
| `backend/core/scheduler/scheduler_manager.py` | 1956 | `from core.mongo_stub import get_stub_database` |
| `backend/core/scheduler/sql_repository.py` | 5 | `Funciones SQL para los jobs del scheduler (reemplazo de MongoDB).` |

## Regla de reapertura

No volver a auditar una referencia ya clasificada solo porque un grep encuentre la palabra `mongo`.

Reabrir únicamente cuando ocurra al menos una de estas condiciones:

- aparece import de cliente Mongo real;
- `core.mongo_stub` cambia de implementación;
- aparece URI/cliente/conexión Mongo productiva;
- un endpoint/job comienza a depender del resultado Mongo;
- una prueba demuestra I/O Mongo real;
- se modifica el linaje del Scheduler.

Los comentarios, docstrings, nombres históricos y asserts de tests no constituyen por sí solos dependencia runtime.
