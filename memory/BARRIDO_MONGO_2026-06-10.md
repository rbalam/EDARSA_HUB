# Barrido NO-MONGO (2026-06-10) — Dependencias `get_db()` / `db.<col>` legacy

## Objetivo
Detectar rutas que aún ejecutan operaciones MongoDB legacy y que, bajo la máxima
NO-MONGO (`get_db()` → None), lanzan `AttributeError` → HTTP 500.

## Metodología
- `grep` de patrones `get_db().<col>.<op>` y `db.<col>.<op>` en `modules/` y `core/`.
- Verificación EN VIVO (cURL con `admin@edarsa.com`) de cada endpoint sospechoso para
  distinguir crashers reales de código guardado/inalcanzable.

## Resultado: 2 crashers reales (CORREGIDOS) + resto seguro

### ✅ Corregidos (migrados a SQL-First en este barrido)
| Endpoint | Causa | Fix |
|---|---|---|
| `GET /api/v2/notificaciones/log` | `db.notificaciones_log.find()` con db=None | Lee de `EDARSAHUB.Operativo_Notificaciones_Log` |
| `GET /api/v2/documentos/historial` | `db.documentos_generados.find()` con db=None | Lee de `EDARSAHUB.Operativo_DocumentosGenerados` |
| `POST /api/v2/notificaciones/verificar-vencidas` | ops Mongo síncronas | Guardado: retorna resultado vacío (detección migrada a módulo SLA) |

### 🟢 Seguros (no crashean — verificado)
- `modules/comercial/cache_service.py` (10 usos): todos dentro de `try/except` → degrada a cache-miss. Dashboard comercial OK.
- `core/server_registry.py` (11 usos): módulo migrado a SQL; `db.servers.*` son fallback inalcanzable. `GET /api/servers` → 200.
- `core/security.py`, `modules/auth/repository.py`, `core/auditoria.py`, `core/communications/routes.py`: inicializados con `StubDatabase` (no None) → operan sin persistencia, sin crash.
- `modules/finanzas/propinas_tpv/*`: endpoints responden (404/422 de validación, no 500).
- `modules/fase2_operativo/routes/documentos_routes.py` (excel/pdf insert log): dentro de try/except interno → solo warning.
- `modules/rh/importador/repository.py` (`get_db().servers`): inicializado vía `init(database)`.

## Nota arquitectónica
`StubDatabase` (`core/mongo_stub.py`) es el patrón sancionado de transición: tolera ops
Mongo async sin fallar. Los crashers ocurren SOLO donde un `get_db()`/`get_database()`
local retorna `None` (no el stub) Y la ruta usa estilo pymongo **síncrono**
(`list(db.x.find())`), que el stub async tampoco soporta.

## Recomendación de saneamiento futuro (P2/P3)
Las rutas legacy con db síncrono que aún existen pero hoy NO están en flujos activos
deben migrarse a SQL-First o eliminarse en el sunset final de Mongo (Fase 6).
