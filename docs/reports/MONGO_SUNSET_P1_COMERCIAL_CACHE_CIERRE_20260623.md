# EDARSAHUB – Mongo Sunset / SQL-First
## Cierre P1 Comercial Cache – 23-Jun-2026

## Estado validado

- `backend/modules/comercial/cache_service.py` quedó sin runtime Mongo operativo.
- `db.comercial_cache` migrado a SQL-first usando `dbo.Sync_Response_Cache`.
- Validación:
  - `python3 -m py_compile backend/server.py backend/modules/comercial/cache_service.py` = OK.
  - Runtime Mongo en `cache_service.py` = 0.

## Tabla canónica utilizada

- `dbo.Sync_Response_Cache`

## Pendiente posterior

- Revisar uso funcional en endpoints:
  - `backend/modules/comercial/routes.py`
  - endpoints de metas y ticket perfecto.
