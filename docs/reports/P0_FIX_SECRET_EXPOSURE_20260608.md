# P0 — Corrección Exposición de Secretos / POS SQL-First

**Fecha:** 2026-06-08
**Autor:** Agente E1. Implementación MANUAL corregida tras auditar el `.sh` del usuario.

## Dictamen del script `.sh` del usuario (RECHAZADO)
| Parche | Problema | Resolución |
|--------|----------|------------|
| 1 (JOB `inteligencia_comercial_sync_job.py`) | INNECESARIO + DUPLICA helpers ya creados en P1B (`get_unidades_negocio_pos`, etc.). El job ya estaba limpio. | Omitido. |
| 2 (`repository_softrestaurant.py`) | ROMPÍA la pantalla viva de Finanzas CxP (reemplazaba hosts por literal `"SERVIDOR_POS_CANONICO"` y password por `None`) sin cablear lo canónico, y NO redactaba el secreto real (`C0ntr4s3ña#2026`; solo buscaba `National09$` inexistente). | Reescrito correctamente (ver abajo). |
| 3 (`Servidores.js`) | ROMPÍA URLs funcionales reales (líneas 352/364 son fallback de "Conexiones API Locales", no placeholders). | Implementado según indicación del usuario. |

**Aclaración:** `EDARSAHUB_SQL_PASSWORD` en ~10 módulos es uso LEGÍTIMO (lee la password del hub canónico desde env). NO es vulnerabilidad; no se tocó.

## Único secreto en texto plano real encontrado
`backend/modules/finanzas/repository_softrestaurant.py` → `C0ntr4s3ña#2026` (líneas 54, 64) + password del hub usada como password de un POS (línea 44) + hosts/usuarios hardcodeados. **ELIMINADO.**

## Cambios aplicados (autorizados por el usuario)
### 1. `repository_softrestaurant.py` (LIVE — Finanzas CxP)
- `SOFTRESTAURANT_SERVERS` ya NO es un dict estático con secretos. Ahora se construye con
  `_build_softrestaurant_servers()`, que resuelve **host/puerto/db/usuario/password** desde
  `dbo.Unidades_Negocio.server_id` → `dbo.Servidores_Conexiones` vía
  `get_server_connection_config()` (helper canónico Comercial V2, sin duplicar desencriptado).
- Solo se conserva metadata NO-secreta (`id` corto UI y `view` CxP) en `_SOFTRESTAURANT_META`.
- Verificado: las 3 sucursales (130MID, ESTELAR, CIENFUEGOS) resuelven con `has_password=True`;
  endpoint `GET /api/finanzas/cuentas-por-pagar/sucursales` → **200** (pantalla NO rota).

### 2. `modules/comercial/adapters.py`
- Eliminados los **defaults hardcodeados** con IP pública (`http://54.39.104.176:8000|8001/query`)
  en `os.environ.get("API_MPRO_ORIGEN_URL"/"API_MPRO_QRO_URL")` (4 ocurrencias). Las vars ya
  existen en `.env` → comportamiento intacto, sin IP en código. Docstring de ejemplo neutralizado.

### 3. `modules/comercial_v2/carga_historica_24_meses.py`
- Eliminado `pm.close_pool('serverestelar.ddns.net', 6969, ...)` con host hardcodeado
  (best-effort; `reset_server_cache()` ya limpia el estado).

### 4. `core/server_registry.py`
- Neutralizado host de ejemplo `'130mid.ddns.net'` en docstring → `'servidor-pos-ejemplo.local'`.

### 5. `frontend/src/pages/Servidores.js`
- Eliminado el **fallback hardcodeado** de `loadApiConnections()` (2 conexiones con IP pública).
  En error de `GET /api-connections`: `setApiConnections([])` + `toast.error` controlado (no
  inventa conexiones ni expone IPs). Placeholder de URL → `https://servidor-local/query`.
- NO se tocaron los endpoints backend ni se movió a `REACT_APP_*` (seguirían expuestos en browser).

## Validaciones (sin testing_agent)
- `grep` runtime: **0** ocurrencias de `C0ntr4s3ña`, IP pública `54.39.104.176` y `*.ddns.net`
  en los archivos tocados; Servidores.js sin IP pública (validación paso 9 del usuario). ✅
- `py_compile`: OK (4 archivos backend). Lint Python: limpio (corregidos 4 issues pre-existentes
  F541/E722 en repository_softrestaurant). Lint JS: solo advisory.
- Build canónico `SOFTRESTAURANT_SERVERS`: 3/3 sucursales con credenciales canónicas, sin exponer password.
- Backend reiniciado: RUNNING, sin errores de arranque. Endpoint CxP 200.

## Nota
- Las credenciales ahora provienen de `Servidores_Conexiones` (fuente de verdad). Si la password
  canónica difiere de la antigua hardcodeada, ese es el valor correcto a usar/actualizar en SQL.
- Pendiente arquitectónico mayor (separado): `repository_softrestaurant.py` aún consulta el POS
  EN VIVO (subprocess) para CxP → viola NO-LIVE. Migrar a tabla pre-calculada en EDARSAHUB es
  trabajo futuro (requiere decisión del usuario).
