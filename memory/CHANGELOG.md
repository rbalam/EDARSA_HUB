# EDARSA HUB - Changelog

## [2026-06-07] Fase 26 — Panel Bitácora Admin CORE (lectura SQL-First de Servidores_Conexiones_Log)
- **Backend:** nuevo endpoint read-only `GET /api/admin/core-connections/audit-log?limit&server_id` en `api/admin_core_connections.py`. Lee `dbo.Servidores_Conexiones_Log` con `LEFT JOIN Servidores_Conexiones` (nombre de conexión), `CONVERT(...,126)` fecha ISO, parseo de `status` desde `datos_nuevos` JSON. NO expone secretos. `TOP` parametrizado (1–200). **Registrado ANTES de `GET /{server_id}`** para evitar colisión de ruta (si no, `/audit-log` caería en `/{server_id}` → 404). Verificado cURL: 200, count correcto, join de nombres OK, LIST sigue 200.
- **Frontend:** 4º tab **Bitácora** en `pages/Servidores.js` (`grid-cols-3`→`grid-cols-4`, `max-w-xl`→`max-w-2xl`). Carga lazy al abrir el tab (`useEffect` sobre `activeMainTab`), tabla con Fecha/Conexión/Acción/Usuario/Estado(badge)/Origen + botón Actualizar y estados loading/empty. `data-testid`: `tab-bitacora-core`, `bitacora-core-panel`, `bitacora-table`, `bitacora-row`, `bitacora-refresh-button`. Verificado screenshot autenticado: 41 registros renderizados.
- **Bonus (lint):** corregidos 6 errores ESLint **pre-existentes** en `Servidores.js` que el cambio expuso: 4× `no-undef` (`setSelectedConnection`/`setUniversalTesterOpen` en los botones "Test Universal" de las vistas lista SQL y API → remapeados a los estados reales `setServerForUniversalTest`/`setUniversalTestConnectionType`/`setUniversalTestOpen`) + 2× comillas sin escapar (`&quot;`). Lint final: 0 bloqueantes.

## [2026-06-07] Fase 25 — P2: previewCacheUtils preservación explícita de token de sesión
- **AUDITORÍA DE SCRIPT (rechazado):** `FASE25_*.sh` NO ejecutado. 3 defectos: (1) FATAL — ambos heredocs Python usan `Path("""__TARGET__""")` literal con `<<'PY'` y **sin** paso `sed` que sustituya `__TARGET__` por `$TARGET` → `FileNotFoundError`, aborta en GATE; (2) su GATE exige `sessionStorage.clear()`/`localStorage.clear()` que **NO existen** en el archivo real (limpieza selectiva vía `shouldClearKey()`) → SystemExit(4); (3) su modelo `clear()` total + lista de preservación es lo **opuesto** al diseño *opt-in* actual → regresión.
- **Verificación del objetivo:** el reset solo borra llaves que matchean patrones de caché (`edarsa*`/`EDARSA_CACHE_KEYS`). Confirmado que las 3 llaves de auth usadas por el frontend (`edarsa_memory_token`, `token`, `access_token`) **ya sobrevivían** el reset → objetivo de preservar token ya cumplido implícitamente.
- **Mejora mínima aplicada:** `shouldClearKey().NEVER_CLEAR` ampliado con `token`, `access_token`, `auth_token` (antes solo `edarsa_memory_token`/`user`/marcador). Hace la preservación de sesión **explícita y robusta** ante futuros cambios de `EDARSA_CACHE_KEYS`. Lint limpio (0 bloqueantes), hot-reload (cambio de 1 array, sin build).

## [2026-06-07] Fase 24 — P1: Cableado de `audit_core_action` en endpoint TEST de Admin CORE (SQL-First)
- **AUDITORÍA DE SCRIPT (rechazado):** `FASE24_*.sh` NO ejecutado. 2 defectos: (1) su GATE inspecciona solo la 1ª línea de la firma (`async def test_core_connection(`) y exige `server_id`/`current_user` ahí, pero la firma es **multilínea** → abortaba con SystemExit(4) sin parchear; (2) regresión latente: `current_user: Dict = Depends(lambda: None)` → en runtime es **None**; la llamada insertada `audit_core_action(user=None,...)` ejecutaría `user.get('id')` → **AttributeError → 500**, rompiendo el contrato (test devuelve 200/404).
- **Fix aplicado (corregido):** (a) blindaje en `audit_core_action`: `user = user or {}` al inicio (evita crash ante user None de cualquier caller); (b) cableado en `POST /{server_id}/test`: tras `result = test_core_connectivity(conn)` se invoca `audit_core_action(action='TEST_CORE_CONNECTION', user=current_user, core_id=server_id, status=result.get('status','SUCCESS'), details={...})` antes del `return result`. `status` derivado del resultado real (no hardcodeado).
- **Verificado (cURL/SQL):** `py_compile` OK, backend RUNNING. Endpoint test → **200 SUCCESS** (`duration_ms`, `message`, contrato intacto). Fila persistida en `dbo.Servidores_Conexiones_Log`: `accion='TEST_CORE_CONNECTION'`, `servidor_id` correcto, `datos_nuevos` JSON. Guardrails NO-MONGO + Admin CORE contract PASS, `health/v1` 200.
- **Nota:** `usuario` queda NULL porque el router usa `Depends(lambda: None)` (la auth se aplica al incluir el router en `server.py`, no inyecta el dict de usuario). Cablear el usuario real requeriría cambiar esa dependencia (fuera de alcance / riesgo). Backup `.bak_*`.

## [2026-06-07] Fase 19 — Reactivación SQL-First de Destinatarios de Alertas + lecturas de Auditoría
- **Destinatarios de alertas (Centro de Control) REACTIVADOS sobre SQL.** Reescrito `core/centro_control/recipients_manager.py` completo a SQL-First sobre `dbo.Sistema_AlertasDestinatarios` (`ColeccionOrigen='alert_recipients'`, detalle en `PayloadMongo` JSON) vía `get_edarsahub_pymssql_connection`. Maneja JSON migrado (`$date`/`$oid`) y nuevo. `recipient_id` = `Id` (uniqueidentifier).
  - CRUD verificado end-to-end por API: LIST (2 migrados leídos), RESUMEN, ADD (200 + GUID), ADD duplicado (400), UPDATE (activo/nombre), filtro `solo_activos`, DELETE (cleanup). Endpoints `GET/POST/PUT/DELETE /api/centro-control/destinatarios` 100% funcionales (antes 500/deshabilitados).
- **Auditoría: `consultar_por_registro` y `consultar_por_modulo` migrados a SQL** (`dbo.Finanzas_AuditoriaFinanciera`, 73 registros). Nuevo helper `_consultar_auditoria_sql(predicate, limite)` lee `PayloadMongo`, normaliza `created_at` a ISO, ordena desc. Verificado: filtro por módulo (CONFIG→5), por registro (todos coinciden), orden descendente correcto. Ya NO usan `_get_mongo_db`.
- **Verificado:** `py_compile` OK, backend RUNNING, guardrails **9/9**, scan `modules/`+`core/` = 0 forbidden / 0 broken, `health/v1` healthy, Admin CORE paridad (200/2), destinatarios 200/total=2.
- **Nota:** ambas tablas son de aterrizaje Mongo→SQL (datos en `PayloadMongo` JSON); el modelo es 1:1 con lo migrado, sin pérdida. Escrituras de destinatarios crean filas nativas SQL (`MigradoDesdeMongo=0`).

## [2026-06-07] Fase 18 — P5-3D Cierre NO-MONGO en `core/` + guardrail extendido
- **Neutralizado `core/auditoria.py::_get_mongo_db`** (stub roto `client=None; client[db_name]` en try/except) → `return None` limpio. La auditoría persiste en SQL (`_guardar_sql` con commit es la ruta primaria); los callers (`_guardar_mongo`, `consultar_por_*`) ya estaban guardados → degradan a False/[].
- **Neutralizado `core/communications/scripts/__init__.py::main`** (init standalone con stub Mongo roto) → no-op NO-MONGO.
- **Neutralizado `core/centro_control/recipients_manager.py`**: `get_db`/`get_collection` → `None`; añadidos guards en `get_all_recipients` (→[]), `add/update/delete_recipient` (→RuntimeError claro "NO-MONGO, requiere migración SQL"). Feature de destinatarios de alertas era **Mongo-backed y ya rota** (crasheaba); ahora **degrada con gracia**: endpoints `GET /api/centro-control/destinatarios` y `/resumen` pasan de **500 → 200 vacío**. (Escrituras deshabilitadas hasta migración SQL.)
- **Limpiado comentario muerto** `modules/comercial/queries/hub.py:62` (`# from core.db import get_mongo_db`).
- **Guardrail extendido a `core/`:** `test_p5_1_no_mongo_residual_modules.py` ahora escanea `modules/` Y `core/` (imports pymongo/motor + patrón roto `client=None`). Scan = 0 imports prohibidos / 0 stubs rotos.
- **Verificado:** `py_compile` OK, backend RUNNING, guardrails **9/9**, `health/v1` healthy, Admin CORE en paridad (200/2), destinatarios 200. NO-MONGO end-to-end en runtime (`modules/`+`core/`) logrado.
- **Nota de proceso:** 2 veces un `search_replace` en paralelo sobre el MISMO archivo no persistió una edición (se detectó por verificación post-parche y se reaplicó). Aprendizaje: editar el mismo archivo de forma secuencial.

## [2026-06-07] Fase 17 — P5-3C Sunset `api_connections/repository.py` + retiro `core/mongo_compat`
- **AUDITORÍA DE SCRIPT (rechazado):** `fase17_*.sh` NO ejecutado — mismo defecto FATAL que P5-3A: reemplazaba `db.api_connections_cache.delete_one(` por `pass` dejando el `await` → **`await pass`** (SyntaxError), y escribía el archivo roto ANTES del `py_compile` → habría tirado el backend por hot-reload.
- **Decisión:** `api_connections_cache` y `api_health_logs` no las **lee** nadie (solo escritura) → **retirada limpia** (no migración).
- **Fix aplicado:** `modules/api_connections/repository.py`: removido `def get_mongo_db()` local; `_sync_to_mongo_cache` → no-op (`return False`); removido bloque de borrado de caché en `delete_api_connection`; removido bloque de health-log en test. Conteo `get_mongo_db`/`api_connections_cache`/`api_health_logs` = **0**. (Nota: había código duplicado de `_sync_to_mongo_cache`; se neutralizó en 2 pasos.)
- **Guardrail reescrito al end-state:** `test_api_connections_mongo_degrades_safe.py` ahora exige 0 residual Mongo + exports SQL-First.
- **Retiro `core/mongo_compat`:** sin consumidores runtime tras limpiar admin + api_connections. Neutralizado el último consumidor (`scripts/rotate_server_secret_key.py::sync_to_mongodb` → no-op NO-MONGO) y **eliminado `core/mongo_compat.py`** (backup en `auditorias_p5/`). Nuevo guardrail `test_no_mongo_compat.py` (archivo ausente + sin imports).
- **Verificado:** backend arrancó SIN errores de import, guardrails **9/9**, contrato Admin CORE en paridad (LIST 200/2, ITEM 20 keys), `GET /api/api-connections` 200, `health/v1` healthy.
- **PENDIENTE (residual Mongo separado, pre-existente y GUARDADO):** `core/auditoria.py::_get_mongo_db` (patrón `client=None; client[db_name]` en try/except → return None, degrada seguro). Mi guardrail cubre `modules/`; falta extenderlo a `core/` y neutralizar este stub. `modules/comercial/queries/hub.py:62` es solo un comentario.

## [2026-06-07] Fase 16 — P5-3B-2/3 Admin CORE: retiro total de `get_mongo_db` (NO-MONGO completo)
- **AUDITORÍA DE SCRIPT (rechazado):** `fase16_*.sh` NO ejecutado. Defectos: (1) su `pattern_find` esperaba variable `mongo_doc` pero el código real usa `mongo_server` → abortaba; (2) su GATE/regex buscaba `'mongodb_id':` (literal dict) pero el código usa `formatted['mongodb_id'] =` (asignación) → abortaba; (3) habría sourceado `mongodb_id` desde SQL de forma incondicional → **agregaba 2 keys** al output rompiendo la paridad del contrato.
- **Análisis de contrato:** ambos endpoints llaman `format_core_connection(conn, include_mongo=True)`, pero como la conexión Mongo siempre era None, el bloque nunca agregaba `mongodb_id`/`mongo_synced` → el baseline tiene 20 keys sin esos campos.
- **Fix aplicado (corregido):** `api/admin_core_connections.py`: removido por completo el bloque vestigial `if include_mongo: ... db.servidores_conexiones.find_one ...` (mantiene salida idéntica) + removido el import `from core.mongo_compat import get_mongo_db`. `get_mongo_db` count en admin = **0**.
- **Guardrail actualizado:** `test_admin_core_import_source_is_correct` ahora exige `get_mongo_db not in txt` (end-state NO-MONGO) en vez de exigir el import de mongo_compat.
- **Verificado:** `py_compile` OK, backend RUNNING, guardrails **8/8**, **PARIDAD_CONTRATO=True** (item 20 keys exactas, 0 extra/0 faltan; LIST 200/2; 404s idénticos), `health/v1` healthy. Backup `.bak_*`.
- **Estado Admin CORE:** 100% SQL-First / NO-MONGO (auditoría→`Servidores_Conexiones_Log`, formateo desde fila SQL, sin `get_mongo_db`). Resta sunset: `modules/api_connections/repository.py` (caché/health-logs) y retiro final de `core/mongo_compat` cuando no queden consumidores.

## [2026-06-07] Fase 15 — P5-3B-1 Auditoría Admin CORE Mongo→SQL (`Servidores_Conexiones_Log`)
- **AUDITORÍA DE SCRIPT (rechazado):** `fase15_*.sh` NO ejecutado. Defectos: (1) su GATE busca `def _log_audit(` pero la función real es `audit_core_action` (línea 83) → habría abortado sin parchar; (2) mapeo de campos incorrecto (`log_data` tiene `core_connection_id`/`action`/`user_email`, no `server_id`/`user`); (3) no-canónico: abría `pymssql.connect` crudo desde env en vez de la conexión write-capable ya importada `get_edarsahub_pymssql_connection`.
- **Fix aplicado (corregido):** `api/admin_core_connections.py`: nuevo helper `_write_admin_audit_log_sql(log_data)` que inserta en `dbo.Servidores_Conexiones_Log` vía `get_edarsahub_pymssql_connection` (parametrizado `%s`, no bloqueante), mapeo correcto (`core_connection_id→servidor_id`, `action→accion`, `user_email→usuario`, `json.dumps(log_data)→datos_nuevos`, `GETDATE()→fecha`), truncado defensivo (`accion`≤20, `usuario`≤100 según esquema real). Reemplazado el bloque Mongo `db.auditoria_core_admin.insert_one(log_data)`. `import json` añadido.
- **Hallazgo:** `audit_core_action` es función muerta (sin callers) → migración valida sunset NO-MONGO; validado el INSERT directamente (no por endpoint).
- **Verificado:** smoke real → `INSERT_OK=True`, fila persistida en `Servidores_Conexiones_Log` (accion/usuario/datos_nuevos) y limpiada. Primer intento reveló truncamiento `accion` nvarchar(20) (escritura SÍ permitida → no es problema de permisos). Backend RUNNING, guardrails 8/8, **contrato Admin CORE = paridad total con baseline** (LIST 200/2, ITEM 200/20-keys, 404 idénticos), `health/v1` healthy. Backup `.bak_*`.
- PENDIENTE P5-3B-2/3: `get_mongo_db` sigue usado en `audit_core_action`... no — ya removido ahí; sigue en el formateo de item (`servidores_conexiones.find_one` → `mongodb_id`/`mongo_synced`, ~línea 249). Migrar a leer `mongodb_id` de la fila SQL y luego retirar el import `get_mongo_db`.

## [2026-06-07] Fase 14 — P5-3B Auditoría exacta pre-cutover Admin CORE (read-only)
- Script `fase14_*.sh` ejecutado (auditoría read-only, sin cambios código/BD/restart; SQL solo lectura a `INFORMATION_SCHEMA`/`TOP 1` mostrando **solo nombres de columnas**, sin valores → sin fuga de secretos).
- **Contrato HTTP congelado** (`auditorias_p5/FASE14_ADMIN_CORE_*`): `GET /core-connections`→200 `{status:SUCCESS,data:[2],meta}`; `GET /{id}`→200/404; `POST /{id}/test`→200 `{status,message,name,server_id,duration_ms,safe_error}`/404. DATA_KEYS documentadas.
- **Hallazgo:** los GET/POST ya son SQL-First sobre `dbo.Servidores_Conexiones`. Residual Mongo en admin = 2 puntos (ya no-op): `auditoria_core_admin.insert_one` y `servidores_conexiones.find_one` (mongodb_id/mongo_synced vestigial).
- **Destino SQL para auditoría identificado:** `dbo.Servidores_Conexiones_Log` (servidor_id, accion, datos_anteriores/nuevos, usuario, fecha, ip_origen). `mongodb_id` ya es columna en `Servidores_Conexiones`.
- **Blueprint cutover** escrito en `auditorias_p5/P5_3B_BLUEPRINT_CUTOVER_ADMIN_CORE.md` (5-6 pasos, bajo riesgo, validable contra contrato congelado). Pendiente aprobación para ejecutar el cutover (toca router vivo).

## [2026-06-07] Fase 13 — P5-3B-A Guardrails + snapshot contrato Admin CORE (pre-cutover)
- **AUDITORÍA DE SCRIPT (corregido antes de ejecutar):** `fase13_*.sh` tenía un defecto: 2 tests importan módulos de la app (`exec_module` de `admin_core_connections`, `from modules.api_connections import repository`) que requieren `EDARSAHUB_SQL_*`; bajo `pytest` desde bash el `.env` NO se carga → fallaban → `set -e` abortaba antes del snapshot. Confirmado: `EDARSAHUB_SQL_HOST` ausente en shell ambiente.
- **Fix permanente:** creado `tests_guardrails/conftest.py` que carga `/app/backend/.env` (`load_dotenv`) + asegura `/app/backend` en `sys.path`. Reutilizable por todos los guardrails que importen módulos.
- **Guardrails creados (6/6 PASS):**
  - `test_admin_core_contract_and_imports.py`: import correcto (`get_mongo_db` desde `core.mongo_compat`, no desde `core.db`), rutas esperadas (`GET ""`, `GET "/{server_id}"`, `POST "/{server_id}/test"`), módulo importa limpio con `router`.
  - `test_api_connections_mongo_degrades_safe.py`: `repository.py` sin import `from core.db import get_mongo_db`, conserva guardas `if db is None`, expone `create/update/delete_api_connection`.
- **Snapshot contrato HTTP actual (baseline para cutover)** en `auditorias_p5/FASE13_CONTRATO_ADMIN_CORE_*`: `GET /core-connections` → 200 `{status:SUCCESS, data:[2], meta}`; `GET /{id}` inexistente → 404 `{"detail":"Conexión CORE no encontrada"}`; `POST /{id}/test` inexistente → 404; `health/v1` → healthy.
- Sin cambios a runtime/BD/frontend/rutas. Listo para P5-3B (cutover SQL-First endpoint por endpoint contra este contrato).

## [2026-06-07] Fase 11 — P5-3A Fix import roto `get_mongo_db` → Admin CORE router reactivado
- **AUDITORÍA DE SCRIPT (rechazado):** `fase11_p5_3a_admin_core_api_connections_safe.sh` NO ejecutado. Defectos: (1) inyectaba helpers `_safe_mongo_*` REDUNDANTES en `admin_core_connections.py` (las ops Mongo líneas 116/251 ya están guardadas con `if db:` + try/except); (2) en `api_connections/repository.py` reemplazaba `db.api_connections_cache.delete_one(`/`update_one(`/`api_health_logs.insert_one(` por funciones SÍNCRONAS dejando el `await` delante → `await <dict>` = TypeError latente si Mongo volviera. Churn innecesario.
- **Fix mínimo aplicado (opción a real):** `api/admin_core_connections.py` línea 33 `from core.db import execute_sql_query, get_mongo_db` → split en `from core.db import execute_sql_query` + `from core.mongo_compat import get_mongo_db`. Causa raíz: `core/db.py` NO exporta `get_mongo_db` (vive en `core/mongo_compat.py`) → ImportError → el router Admin CORE NUNCA se registraba (34 WARNINGs históricos "Error registrando Admin CORE router").
- `modules/api_connections/repository.py`: SIN cambios — sus 3 ops Mongo (caché delete/update, health log insert) ya están guardadas con `if db is None`/`if db is not None`; `get_mongo_db()` (mongo_compat) retorna None → no-op seguro.
- Verificado: `py_compile` OK, backend RUNNING, **`GET /api/admin/core-connections` → 200** `{status,data,meta}` (antes 404 por no registrarse), sin error Admin CORE tras el último arranque, `health/v1` → healthy, guardrail NO-MONGO 2/2. Backup `.bak_*`.
- NOTA: migración SQL-First completa de estos endpoints (leer `dbo.Servidores_Conexiones`, auditoría/caché/health-logs a SQL) queda como lote futuro P5-3B (blueprint en `auditorias_p5/FASE11_P5_3_*`).

## [2026-06-07] Fase 10 — P5-2 Guardrail CI NO-MONGO + neutralización 2 stubs rotos extra
- **AUDITORÍA DE SCRIPT (rechazado):** `fase10_p5_2_requirements_guardrail.sh` NO ejecutado. Defectos: (1) GATE `get_mongo_db` aborta siempre — hay 12+ refs VIVAS (`core/mongo_compat.py`, `modules/api_connections/repository.py`, `api/admin_core_connections.py`, etc.); (2) objetivo ya cumplido: `requirements.txt` NO contiene `pymongo`/`motor`; (3) parche requirements roto: `'"$REQ_FILES"'` en heredoc `<<'PY'` (sin interpolación) → FileNotFoundError; (4) el guardrail que crea se auto-falla (`test_no_get_mongo_db_left` escanea su propio código que contiene `get_mongo_db`).
- **Guardrail creado (versión propia, acotada):** `tests_guardrails/test_p5_1_no_mongo_residual_modules.py` — pytest + standalone. Falla si reaparece en `/app/backend/modules/`: imports vivos `pymongo`/`motor`/`MongoClient`/`AsyncIOMotorClient`, o el patrón roto `client = None` usado como conexión (`db = client[...]`/`.find(`/`.find_one(`). Acotado a `modules/` → no se auto-falla. PASS (2/2).
- **Bonus:** el guardrail detectó 2 stubs Mongo rotos pre-existentes adicionales → neutralizados al patrón canónico deprecado-None:
  - `modules/finanzas/repository_cuadres_z.py::get_db` (código muerto: tesoreria usa la versión `_edarsahub` SQL).
  - `modules/configuracion/routes/config_asignaciones_routes.py::get_db` (router vivo, pero `get_db()` ya crasheaba en `client[db_name]` → sin regresión).
- Verificado: `py_compile` OK, backend RUNNING, `GET /api/health/v1` (auth) → 200 `healthy`, guardrail 2/2.
- NOTA pendiente: capa `core/mongo_compat.get_mongo_db` aún cableada en `api_connections`/`admin_core_connections` (residual Mongo mayor, fuera de alcance de este lote).

## [2026-06-07] Fase 9 — P5-1 Sunset mínimo `historical_kpis_repository.py` (NO-MONGO)
- Contexto: el módulo ya no tenía `import pymongo/motor` vivos; el riesgo real eran 3 funciones legacy Mongo ROTAS (`client = None` → `db = client['edarsa_hub']`) que reventarían si se reactivaran. Verificado: NINGÚN router importa el módulo (código muerto inerte).
- Neutralización quirúrgica por bloques de función: `_get_edarsahub_credentials`, `_get_edarsahub_credentials_sync` y `migrate_staging_mongo_kpis_to_sql` → stubs que retornan `{"disabled": True, "reason": "MONGO_LEGACY_SUNSET"/"MONGO_STAGING_SUNSET"}`. Sin tocar lógica SQL viva.
- Removido import huérfano `from core.secret_manager import decrypt_secret, is_encrypted_secret` (solo lo usaban las funciones Mongo retiradas).
- **AUDITORÍA DE SCRIPT (rechazado):** el script del usuario `fase9_p5_1_sunset_historical_kpis_minimo.sh` era un **no-op engañoso**: sus 3 regex usaban `\([^)]*\):` (esperan `):` pegado) pero las firmas reales son `() -> Dict:` y `migrate_...(` multilínea → 3× NO-MATCH. Habría reportado `PATCHED`+`health OK` SIN neutralizar nada. Se aplicó versión corregida (reemplazo por bloques línea-a-línea).
- Verificado: `py_compile` OK, `NO_MONGO_RESIDUAL`, backend RUNNING, `GET /api/health/v1` (auth) → 200 `overall_status=healthy` (6/6 dominios). Backup `.bak_*`.

## [2026-06-07] Bugfix server nombre + Fase 8B P2-2B (frontend Mis Tareas/Asignaciones)
- `modules/comercial/repository.py::_sql_row_to_server_dict`: agregado alias `'nombre'` (= `row['nombre']`) junto a `'name'` (consumidores que esperan `nombre`). Verificado: name/nombre poblados (130° MERIDA, CIENFUEGOS, LA ESTELAR, ManagmentPro). Nota: el "nombre None" reportado antes fue un falso positivo (la clave de salida es `name`).
- `frontend/src/pages/ConfigAsignaciones.jsx`: FIX bug real `getUserRole()` usaba `token` no declarado → `ReferenceError`. Ahora `const token = getToken()` (import `{ getToken }` de `lib/api`). + hardening `ensureArray`/`asString` en setters y Radix Selects (value string).
- `frontend/src/pages/MisTareas.js`: helpers `ensureArray`/`normalizeTareas`/`normalizePendientes`, null-safety en setters y derivados. Corregidos 3 lint bloqueantes preexistentes (comillas sin escapar `&quot;`; `set-state-in-effect` → efecto envuelto en `init()` async).
- Validado: `yarn build` BUILD_OK=1, lint 0 bloqueantes, consola sin `ReferenceError`. Captura autenticada bloqueada por PREVIEW_CACHE_RESET (limitación del preview). Scripts/back.: `/app/scripts/fase8b_*`, `.bak_*`.


## [2026-06-07] Bugfix — Dashboard Comercial "Servidor no encontrado en configuración"
- Causa raíz: `modules/comercial/repository.py::_get_server_by_id_sql` interpolaba `{id}` (función builtin `id` de Python → `'<built-in function id>'`) en el f-string del query en vez de `{server_id}`. La consulta a `Servidores_Conexiones` nunca encontraba el servidor → `get_server_by_id` retornaba None → el endpoint `/api/comercial/dashboard/{server_id}` respondía `source_status=ERROR, "Servidor no encontrado en configuración"`.
- Fix: usar `{server_id}` con escape de comillas (`safe_id = server_id.replace("'", "''")`) para evitar inyección SQL.
- Verificado: `GET /api/comercial/dashboard/{server_id}` → 200 `source_status=SUCCESS` en los 4 servidores (3 SoftRestaurant + 1 MPRO). `health/v1` → healthy. Backup `.bak_*`.


## [2026-06-07] Fase 8 — P2-2A Contención de ruido backend no bloqueante
- `core/health_checker.py`: `_check_mongodb` → `UNKNOWN` (residual deshabilitado, ya no `CRITICAL`); `_check_sql_servers` → `[]` (catálogo legacy dependía de Mongo); conteo no suma fallo por fuentes `UNKNOWN`. Resultado: `OVERALL=healthy, sources_failed=0`.
- `core/scheduler/jobs/crm_sync_job.py`: helper `_is_missing_schema_error` + `_skip_result`; `execute_crm_sla_check`/`execute_crm_actividades_vencidas` devuelven `SKIP` controlado ante esquema CRM incompleto (`Invalid column 'OportunidadID'`) en vez de spamear errores. Verificado: CRM_ACT=SKIP.
- `modules/fase2_operativo/services/sla_service.py`: guards `if not tarea or not isinstance(tarea,dict)` en `calcular_estado_sla`, loops y `notify_sla_warning/expired/escalated` (→ False). Sin crash con tarea None.
- Patches por `txt.replace()` de cadena exacta (fail-safe). Validado: 3/3 compile OK, backend RUNNING, `health/v1` (auth) → healthy. Script: `/app/scripts/fase8_p2_2a_contencion_ruido_backend.sh`.


## [2026-06-07] Fase 7 — P2-1 Neutralización residual Mongo en Comercial
- `modules/comercial/kpis_repository.py :: upsert_kpi_comercial`: guard temprano `if db is None -> return {"action":"SKIP","disabled":True,"reason":"MONGO_COMMERCIAL_DEPRECATED"}`. Elimina el crash `None[COLLECTION].find_one(...)` en cada sync (la función la importa `api/sync_receiver.py:147`, que solo lee `result["action"]`).
- Hallazgo: el script original apuntaba a 4 funciones inexistentes y omitía la única Mongo viva; se implementó la neutralización correcta. Las `get_*`/`cerrar_periodos_anteriores` no las importa ningún router (código muerto inerte).
- Verificado: smoke `upsert_kpi_comercial` → SKIP no-op sin crash; `health/v1` → healthy.
- Script: `/app/scripts/fase7_p2_1_neutralizar_mongo_comercial.sh` (versión corregida).


## [2026-06-07] Fase 6 — Endpoint semáforo `/api/health/v1` (SQL-First / NO-LIVE)
- Nuevo módulo `backend/modules/health_v1/routes.py` + registro en `server.py` (import tras finanzas.health; include tras `app.include_router(api_router)`).
- `GET /api/health/v1` agrega salud canónica de los 6 dominios estabilizados: sql_canonic, tablero_comercial (vistas v2_Runtime queryables), users_roles, config_operativa, explorador_bd (helper local), finanzas (tablas requeridas). NO consulta operativos externos.
- Resultado: `overall_status=healthy`, 200 en ~1.7s. Probe de vistas = queryability estructural (vista vacía ≠ rota).
- NOTA: bloqueado el registro del script del usuario (prepend de import en línea 1 → antes de `load_dotenv()` → habría roto el arranque). Registrado de forma segura.
- Scripts: `/app/scripts/fase6_crear_health_v1.sh` (versión corregida) y `/app/scripts/fase6_validar_health_v1.sh`.


## [2026-06-07] Fase 1 — Estabilización V1.0: 5 P0 cerrados (SQL-First / NO-MONGO / NO-LIVE)
Todos validados con cURL/pytest (sin testing_agent, por prohibición). Backups `.bak_*` por archivo.
- **P0-1 Vistas corruptas (Tablero/Comercial)**: normalizadas `vw_vw_..._Runtime_Runtime` → `vw_Comercial_KPIs_Diarios_v2_Runtime` y `..._Mensuales_v2_Runtime` en 10 archivos vivos. `GET /api/comercial/tablero-ejecutivo` y `/api/dashboard-ejecutivo/resumen` → 200 con datos EDARSAHUB_SQL.
- **P0-2 RBAC + CRUD Usuarios/Roles**: `core/rbac_helper.py` reescrito SQL-First **async** (`run_in_threadpool`, bypass por CodigoRol `SUPERADMIN`/`ADMIN`+NivelJerarquia, fail-closed). Añadidas 11 funciones **module-level** SQL-First en `modules/auth/repository.py` (get_db→None, get_users_by_empresas, get_all_roles, find_role_by_id/by_name, create/update/delete_role, count_users_with_role, create_default_roles, deactivate_user). `core/alcance_helper.py`: SuperAdmin reconoce CodigoRol `SUPERADMIN`. CRUD users/roles GET/POST/PUT/DELETE → 200. pytest `tests/test_rbac_helper.py` 5/5.
- **P0-3 Configuración Operativa (cursor tupla-vs-dict)**: helpers `_rows_dicts`/`_one_dict` en `api/configuracion_operativa_unidades.py` (3 sitios fetch, incl. `/todas/`). Endpoints config-operativa + probar-fecha-operacion → 200.
- **P0-4 Explorador BD**: repuesto `_execute_sql_direct_with_error` en `core/db.py` (async, `asyncio.to_thread(execute_sql_query)`). `/api/explorador/conexiones-explorables` (13) y `/api/explorador/tablas/{server_id}` → 200.
- **P0-5 Finanzas /health 502**: `include_server_details` default `True→False` en `modules/finanzas/health.py`. Health canónico solo EDARSAHUB (NO-LIVE) → 200 en 0.28s; sondeo externo ahora opt-in (`?include_server_details=true`).
- NOTA scripts del usuario: 3 de 5 traían defectos detectados antes de ejecutar (líneas no cubiertas en FASE1/FASE3; métodos de clase vs module-level en FASE2b; **SyntaxError** en FASE5). Se implementaron versiones corregidas. FASE4 estaba correcto.


## [2026-06-07] Fase 0 — Auditorías profundas A/B/C (SIN cambios de código de app)
- Doc actualizado: `/app/auditorias_p5/AUDITORIA_V1_PRODUCCION_MATRIZ.md` (secciones 6 y 7).
- **A (UI smoke, 12 menús)**: ningún logout ni crash; KPIs Tablero/Comercial vacíos (403+vista); Config.Operativa atascada (500); Mis Tareas 12 JS-err, Asignaciones 8 JS-err.
- **B (NO-LIVE)**: guard rail `LEGACY_LIVE_DISABLED` OK; intentos live en logs = jobs de sync (ETL); **vista corrupta `vw_vw...` en 88 referencias** (Comercial/Tablero KPIs).
- **C (RBAC)**: `core/rbac_helper.verificar_permiso_rbac` es Mongo y crashea → rompe CRUD usuarios/roles (NO-MONGO + 500); SUPERADMIN no bypassa scope de unidad en `comercial_v2` (403); enforcement disperso.
- Test users (autorizados): `qa.superadmin@edarsa.com`/`QaSuper2026!` (nuevo) y `admin@edarsa.com`/`pruebas123` (promovido a SUPERADMIN).


## [2026-06-07] Fase 0 — Auditoría v1.0 producción (SIN cambios de código)
- Entregable: `/app/auditorias_p5/AUDITORIA_V1_PRODUCCION_MATRIZ.md` (matriz por menú: front/back, endpoints, auth, RBAC, filtros, tablas canónicas, legacy/stub, live prohibido, mongo residual, estado, riesgo, recomendación).
- Bloqueadores hallados: **Tablero Ejecutivo 500** (vista corrupta `vw_vw_vw_vw_..._Runtime_Runtime...` → real `vw_Comercial_KPIs_Diarios_v2_Runtime`); **Explorador BD** import roto `_execute_sql_direct_with_error`; **Finanzas /health 502**; intentos **NO-LIVE** a operativos en logs; **Mongo residual** alcanzable en `comercial/cache_service|kpis_repository|historical_kpis_repository`.
- Sin correcciones aplicadas (a la espera de aprobación de Fase 1).


## [2026-06-07] Limpieza de menú: rutas rotas → "Pronto" + 2 rutas corregidas

- **2 ítems con ruta mal escrita corregidos** (apuntaban a rutas inexistentes pese a tener pantalla):
  - `Asignaciones`: `/asignaciones` → `/configuracion/asignaciones` (validado: abre "Asignaciones de Inventarios").
  - `Config. Operativa`: `/configuracion-operativa` → `/admin/configuracion-operativa`.
- **11 módulos sin pantalla marcados `comingSoon: true`** (Inventarios, Host to Host, Contabilidad, Comisiones, Inteligencia Artificial, Calidad/Auditoría, Proyectos, Marketing, Activos Fijos, Integraciones, Programación). `EnterpriseSidebarMenu` los renderiza **deshabilitados** (no clicables) con badge **"Pronto"** y tooltip "— Próximamente". `go()` ignora ítems `comingSoon`.
- **Validado (playwright)**: clic en ítem `comingSoon` (Contabilidad) NO navega ni expulsa; ítem corregido (Asignaciones) abre su pantalla. Lint limpio.


## [2026-06-07] FIX lote: Permisos 403, crash Select, logout navegación (Issue #1) y race recarga (Issue #2)

### 🐞 Guardar permisos de usuario → "Error al guardar permisos" (backend, 403/404)
- `PUT /api/users/{id}/permissions` devolvía **403** porque `ROLE_HIERARCHY` (modules/auth/service.py) solo reconocía `NombreRol` legacy ('SuperAdministrador'), pero el JWT usa `CodigoRol` canónico ('SUPERADMIN'/'ADMIN'). → Mapeados AMBOS (NombreRol + CodigoRol) a la escala legacy y `_get_role_level` ahora tolera mayúsculas.
- Tras el 403, había un **404 latente**: el servicio resolvía el usuario solo por `PublicUUID`, pero el frontend envía el `UsuarioID` numérico. → Resolución por `TRY_CONVERT(INT)` OR `PublicUUID`.
- **Validado (curl)**: 200 "Permisos actualizados" con id numérico + payload de sucursales/almacenes (inserts confirmados en SQL). Datos de prueba limpiados.

### 🐞 Crash runtime `<Select.Item /> value=""` (frontend)
- `BitacoraComponents.jsx` tenía 2 `SelectItem value=""` (Radix lo prohíbe). → Centinela `value="todos"` mapeado a `''` en `onValueChange` (preserva la lógica del filtro). Lint limpio.

### 🐞 Issue #1: logout al navegar Operaciones → Tablero Ejecutivo (frontend, sin 401/403)
- Causa raíz: el favorito "Dirección / Tablero Ejecutivo" (`enterpriseMenuConfig.js`) apuntaba a `/dashboard-ejecutivo`, ruta **inexistente** en App.js → catch-all `*` → `/login`. (~13 ítems de menú más apuntan a rutas no construidas con el mismo efecto.)
- Fix: (1) corregido path → `/tablero-ejecutivo`; (2) catch-all `*` ahora usa `CatchAllRedirect`: si hay sesión → `/tablero-ejecutivo`, si no → `/login` (evita logout espurio en CUALQUIER ruta desconocida).
- **Validado (playwright)**: clic en Tablero y ruta rota `/inventarios` ya NO expulsan.

### 🐞 Issue #2: race 403 en recarga dura del dashboard (frontend)
- `accessContextService.getAuthHeaders()` leía el token de la llave `'token'` (inexistente) en vez de la canónica `'edarsa_memory_token'` → `/auth/access-context` iba SIN Bearer → 403. → Usa `getToken()` canónico.
- `previewCacheUtils.shouldClearKey` borraba `edarsa_memory_token` (prefijo 'edarsa') en cada carga (BUILD_VERSION=Date.now()) → token perdido en recarga. → Lista `NEVER_CLEAR` protege token/usuario/marcador.
- **Validado (playwright)**: recarga dura + reload puro de Operaciones → 0×401/403, sin logout; access-context = 200.

### 🐞 Enlace de reset apuntaba a host bloqueado (backend)
- `forgot_password` usaba el `Origin`/`Referer` de la request; si el usuario entraba por `*.preview.emergentcf.cloud` (bloqueado, 403), el correo armaba ese enlace. → Siempre usa `FRONTEND_URL` canónico.

## [2026-06-07] FIX: Pantalla "Restablecer contraseña" saltaba al login

### 🐞 Bug (P0 reportado por usuario)
- **Síntoma**: El correo de recuperación llega y el enlace abre la pantalla de nueva contraseña, pero ésta "no se detiene": se muestra un instante y de inmediato salta a la ventana de iniciar sesión, sin poder capturar la nueva contraseña.
- **Causa raíz (frontend)**: `ResetPassword`/`ForgotPassword` se renderizan dentro de `<AuthProvider>`, que al montar llama a `GET /auth/me`. Sin sesión → 401. El interceptor de `lib/api.js` redirigía a `/login` para toda ruta que no fuera login/portales (no contemplaba el flujo de recuperación).
- **Fix**: En `lib/api.js` se añadió `isAuthFlowPage` (`/forgot-password`, `/reset-password`) a la lista de exclusión del redirect forzado en 401. El backend NO se tocó (el token, SMTP y reset SQL ya funcionaban).
- **Validado (screenshot)**: `/reset-password?token=...` permanece estable 4s, sin redirect; el input `reset-password-new` queda disponible para escribir la nueva contraseña.

## [2026-06-06] FASE AUTH-V2-ALIGN: Operaciones v2 (401/403/500) + forgot-password

### ✅ Capa 1 — Auth frontend (alineación canónica)
- **Problema**: `operativoApi.js` y 5 componentes hacían `fetch` crudo solo con `credentials:'include'` (cookie). El backend v2 solo lee el header Bearer → 401 (require_permission) / 403 (HTTPBearer de get_current_user).
- **Fix**: `getToken()` exportado desde `lib/api.js` (fuente única). Helper `authedFetch()` en `operativoApi.js` inyecta `Authorization: Bearer` + mantiene cookie. Migrados SLACard, ResponsabilidadCard, ResponsabilidadPendientesPanel, ResponsabilidadAccionesModal, WorkflowList a `authedFetch`.
- **Validado (browser)**: las 8 rutas v2 ahora envían `auth_header=True`; 401/403 → resueltos.

### ✅ Capa 2 — RBAC roto a nivel app
- **Bug A (isoformat)**: `core/rbac/repository_sql.py:445/693` hacía `fecha.isoformat()` sobre string (FreeTDS tds_version 7.0 devuelve DATETIME2 como string). → `hasattr(...,'isoformat')`.
- **Bug B (seed por request)**: `RBACService` usaba flag de instancia; `middleware.py` instancia por request → `seed_permisos+seed_roles` corrían en CADA petición (≈6s + timeouts intermitentes → 500). → flag a nivel de **clase** (`_seeded`), seeding una sola vez por proceso.
- **Validado (curl)**: `require_permission` ahora pasa para Ricardo (SUPERADMIN). v2/health=200; sla sin token=401, con token=500 (Capa 3).

### ✅ forgot-password (mismo origen datetime-string)
- `password_reset.py:138` `ventana_exp.replace(tzinfo=...)` sobre string → `TypeError`. Helper `_coerce_aware_dt()` (maneja str DATETIME2 de 7 decimales, datetime naive/aware, None).
- **Validado**: endpoint → 200, envía correo real vía SMTP `mail.edarsa.com.mx`. SMTP confirmado OK (login + sendmail).
- Test regresión: `backend/tests/test_password_reset_datetime.py` (6/6 passed).

### ⏸ Capa 3 — DIFERIDA por decisión del usuario (bloque separado y auditado)
- `dashboard/tareas/workflows/sla/responsabilidad` dependen de Mongo eliminado: `db_utils.py:30-31` hace `None[db_name]` → `'NoneType' subscriptable` → 500. NO se aplicó degradación por stub ni migración SQL (acuerdo explícito).

### Lint pre-existente (NO introducido en esta sesión)
- `react-hooks/set-state-in-effect` (SLACard, ResponsabilidadCard, ResponsabilidadPendientesPanel) y `react/no-unescaped-entities` (ResponsabilidadPendientesPanel:215) ya existían; mi diff solo cambió `fetch`→`authedFetch` e imports. No se refactorizó (fuera de alcance / riesgo).

## [2026-05-25] Sesión Actual

### ✅ CORTES-Z-RESILIENCIA-001: Mejora de Resiliencia Arquitectónica
- **Problema**: El health check anterior reportaba timeout como "normal", lo cual fue rechazado
- **Diagnóstico**: Confirmado que Cortes Z ya era SQL-FIRST (lee de `Finanzas_CortesCaja`)
- **Causa real**: Intermitencias del servidor EDARSAHUB SQL, no arquitectura
- **Mejora**: Endpoint ya no lanza error 500, retorna estado controlado `EDARSAHUB_UNREACHABLE`
- **Archivos**: `repository_cortes_caja_edarsahub.py`, `tesoreria.py`

## [2026-05-25] Sesión Anterior

### ✅ FINANZAS-TESORERIA-SQL-001: Cortes Z migrados a SQL
- Creado `repository_cortes_caja_edarsahub.py`
- Endpoint lee de `Finanzas_CortesCaja`
- 4,083 cortes históricos disponibles

### ✅ FINANZAS-TESORERIA-MONGO-002: Cuadres Z migrados a SQL
- Modificado `tesoreria.py` para usar repositorio SQL
- Agregados métodos `listar_cuadres_z_por_server_id()`, `obtener_resumen_por_server_id()`

### ✅ Migración credenciales hardcodeadas
- Movidas credenciales de `server.py` a `.env`
- CORS origin para producción agregado

### ✅ BUG-COMPETIDORES-001 resuelto
- Corregido mapeo de campos en CompetidorModal
- Agregados campos de redes sociales

## Problemas conocidos de infraestructura
- **EDARSAHUB SQL (54.39.104.176)**: Intermitencias de conectividad ocasionales
- **SoftRestaurant (189.162.155.142)**: Connection refused intermitente
