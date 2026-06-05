# AUDITORÍA P0 — core/db.py Mongo Usage

Fecha: 2026-06-05 00:07:06

## Referencias Mongo directas en core/db.py

- L1120: `from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase`
- L1121: `from pymongo import MongoClient`
- L1124: `_mongo_client: Optional[AsyncIOMotorClient] = None`
- L1126: `_sync_mongo_client: Optional[MongoClient] = None`
- L1129: `async def get_mongo_client() -> AsyncIOMotorClient:`
- L1134: `global _mongo_client`
- L1135: `if _mongo_client is None:`
- L1137: `return _mongo_client`
- L1151: `def get_sync_mongo_db():`
- L1156: `global _sync_mongo_client`
- L1157: `if _sync_mongo_client is None:`
- L1159: `return _sync_mongo_client`
- L1557: `'get_mongo_client',`
- L1559: `'get_sync_mongo_db',`

Total referencias: 14

## Funciones Mongo definidas

- L1129: `get_mongo_client`
- L1140: `get_mongo_db`
- L1151: `get_sync_mongo_db`
- L1162: `init_db_connections`

## Uso externo de funciones Mongo

### `get_mongo_db` (L1140)

- [MEDIO] `backend/modules/comercial/queries/hub.py` L60: `# from core.db import get_mongo_db`
- [MEDIO] `backend/modules/api_connections/repository.py` L45: `def get_mongo_db():`
- [MEDIO] `backend/modules/api_connections/repository.py` L468: `db = get_mongo_db()`
- [MEDIO] `backend/modules/api_connections/repository.py` L487: `db = get_mongo_db()`
- [MEDIO] `backend/modules/api_connections/repository.py` L602: `db = get_mongo_db()`
- [MEDIO] `backend/scripts/rotate_server_secret_key.py` L399: `from core.db import get_mongo_db`
- [MEDIO] `backend/scripts/rotate_server_secret_key.py` L401: `db = get_mongo_db()`
- [MEDIO] `backend/tests/test_bloque2_paridad.py` L36: `def get_mongo_db():`
- [MEDIO] `backend/tests/test_bloque2_paridad.py` L43: `db = get_mongo_db()`
- [MEDIO] `backend/tests/test_bloque3_paridad_mpro.py` L41: `def get_mongo_db():`
- [MEDIO] `backend/tests/test_bloque3_paridad_mpro.py` L48: `db = get_mongo_db()`
- [MEDIO] `backend/api/admin_core_connections.py` L32: `from core.db import execute_sql_query, get_mongo_db`
- [MEDIO] `backend/api/admin_core_connections.py` L113: `db = get_mongo_db()`
- [MEDIO] `backend/api/admin_core_connections.py` L248: `db = get_mongo_db()`
- [MEDIO] `backend/core/mongo_compat.py` L41: `def get_mongo_db():`

## Dictamen inicial

- Riesgos altos por uso en rutas/server: **0**
- `core/db.py` contiene conexiones tanto SQL como MongoDB.
- Las funciones `get_mongo_*` deben ser deprecadas progresivamente.
- Cualquier endpoint visual que use MongoDB debe migrarse a SQL-first.
