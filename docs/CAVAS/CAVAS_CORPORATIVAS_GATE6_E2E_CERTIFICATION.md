# Cavas Corporativas - Gate 6 E2E

Gate de certificacion end-to-end sobre los contratos cerrados de Gates 1-5.

## Superficie certificada
- Dominio: `backend/modules/cavas_corporativas/domain.py`
- Repositorio SQL: `backend/modules/cavas_corporativas/repository.py`
- Servicio: `backend/modules/cavas_corporativas/service.py`
- API: `backend/modules/cavas_corporativas/routes.py`
- Registro backend: `backend/server.py` via `api_router.include_router(cavas_corporativas_router)`
- Frontend: consumo de `/cavas/corporativas/evaluar` y `/cavas/corporativas/aplicar`
- RBAC: permisos SQL canonicos `cava_socios.*` certificados en Gate 5 R2

## Reglas
- SQL Server canonico.
- Sin Mongo como fuente.
- Sin hardcodes funcionales nuevos.
- Sin bypass RBAC.
- Sin Produccion.
- Sin DDL/DML SQL en este gate.

La certificacion terminal de este dossier depende exclusivamente del resultado del Worker: pytest de dominio/repositorio/servicio/rutas, py_compile y build frontend deben terminar PASS.
