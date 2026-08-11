# AUDITORÍA TÉCNICA — MENÚ COMPRAS (EDARSAHUB)
## Cumplimiento de Máximas Inquebrantables, RBAC, Canonicalización y Folios
**Fecha:** 2026-07-19
**Alcance:** `backend/modules/compras/*`, endpoints `/compras/*` en `backend/server.py` (líneas 9081–12960), `frontend/src/pages/Compras.js`, `frontend/src/components/compras/*`, `frontend/src/services/unidadesNegocioService.js`.
**Método:** Solo lectura. Sin cambios de código. Sin ejecución de SQL. Evidencia en formato `archivo:línea`.

---

## 0. ACTUALIZACIÓN 2026-07-19 (post-auditoría, misma sesión)

Después de esta auditoría, el usuario autorizó y se ejecutaron dos fases de remediación **en la misma sesión**, en paralelo con trabajo propio del usuario sobre `backend/modules/compras/sync_service.py` (commit `8793168d fix(compras): sincronizar canonicos sin duplicados`) que también movió gran parte de los endpoints legacy de este archivo hacia lectura NO-LIVE canónica. Como resultado, varias afirmaciones de las secciones 2-3 de este documento (escritas ANTES de ese trabajo) ya no reflejan el estado actual del código — se dejan como registro histórico del punto de partida, no como estado vigente. Ver `git log` / `git blame` de `backend/server.py` para el estado real más reciente en vez de los números de línea citados abajo.

**Fase 0 (inyección SQL) — hecha, luego superada.** Se parametrizaron las 5 queries de §4. Esa corrección quedó luego **sobrescrita/superada** por una reescritura más amplia (obra del usuario, no mía) que migró esas mismas funciones (`obtener_detalle_pedido_manual`, `obtener_detalle_pedido`) a leer 100% de `Compras_Pedidos`/`Compras_PedidosDetalle` (EDARSAHUB canónico), eliminando también la conexión live a MPRO — es decir, el resultado final es mejor que mi parche original.

**Fase 1 (RBAC funcional) — hecha.** Se creó `backend/modules/compras/access.py` (mismo patrón que `backend/modules/finanzas/access.py`: `require_compras_permission` contra RBAC SQL, códigos `COMPRAS_FACT_VER/CREAR/EJECUTAR/CONFIGURAR/GESTIONAR`). Se conectó a los **21 endpoints activos** de `/compras/*` (todos excepto los `-sql-first`, que hoy están deshabilitados por feature flag y sin tráfico real) — cada uno ahora exige tanto el permiso funcional como el alcance por servidor/unidad (`validate_server_access_by_empresa` / `_compras_resolve_scope` / `has_server_access` según el caso). Verificado con `python3 -m py_compile backend/server.py`.

**Hallazgo crítico durante Fase 1, ya resuelto:** el rol operativo real de compras es `COMPRAS` (confirmado por el usuario) y NO tenía ningún permiso `COMPRAS_FACT_*` concedido en las migraciones existentes (solo `DIRECCION`, `GERENTE_OPS`, `TESORERIA`, `SUPERADMIN`, `SUPERADMINISTRADOR` lo tenían). Activar el candado sin resolver esto habría bloqueado a los compradores reales. Se creó `backend/database/migrations/20260719_001_rbac_compras_rol_compras_explicit.sql` (mismo patrón transaccional/idempotente que `20260702_021_rbac_compras_operativo_explicit.sql`) que concede `VER/CREAR/EJECUTAR/CONFIGURAR/GESTIONAR` al rol `COMPRAS`.

**⚠️ ACCIÓN PENDIENTE OBLIGATORIA, FUERA DE MI ALCANCE DE EJECUCIÓN:** esa migración SQL **no se ha aplicado a la base de datos** — solo existe como archivo. Si el candado de permisos (ya activo en el código) se despliega **sin correr antes esta migración**, los usuarios con rol `COMPRAS` quedarán bloqueados (403) en todo el menú. Debe ejecutarse contra EDARSAHUB SQL antes o junto con este despliegue.

**Pendiente real (no tocado):** Fase 2 (retirar/objetar los endpoints `-sql-first` ahora redundantes dado que los legacy ya quedaron NO-LIVE — requiere confirmar que ya no hay diferencia funcional) y Fase 3 (canonicalizar Folio, §8). No se tocó RBAC de los endpoints `-sql-first` (siguen sin permiso ni scope) porque no tienen tráfico real (feature flag apagado) — bajo riesgo pero pendiente de limpieza.

---

## 0.1 ACTUALIZACIÓN 2026-07-23 — Fase 2 cerrada; Fase 3 acotada y diferida

**Fase 2 — hecha, pero no como se planteó arriba.** El plan original de esta línea 21 era migrar el frontend hacia los endpoints `-sql-first` y *luego* retirar los legacy. Ese plan quedó superado por los mismos hechos ya descritos en §0: los endpoints legacy usados por el frontend ya son NO-LIVE (leen tablas canónicas EDARSAHUB), así que los 8 endpoints `-sql-first` (nunca activados por `COMPRAS_SQL_FIRST_ENABLED`, cero referencias en frontend) quedaron sin ningún propósito. Se retiraron directamente en vez de migrar hacia ellos: `obtener_inventarios_fisicos_sql_first`, `obtener_pedidos_vigentes_sql_first`, `obtener_productos_para_captura_sql_first`, `obtener_detalle_movimientos_sql_first`, `obtener_facturas_proveedor_sql_first`, `obtener_detalle_factura_sql_first`, `obtener_detalle_consumos_sql_first`, `obtener_dashboard_compras_sql_first` (~732 líneas). Verificado: `python3 -m py_compile backend/server.py` compila; grep confirma cero referencias restantes a `sql-first`/`COMPRAS_SQL_FIRST_ENABLED` fuera de `core/sql_first/*` (módulo compartido, no exclusivo de Compras, no tocado).

**Fase 3 — investigada a fondo, y resultó mucho más grande de lo que asumía esta auditoría.** Antes de tocar nada se remapeó el alcance real (dos exploraciones de solo lectura) y se encontró que:
- Los campos plural/singular de folio (`folio_inv_inicial`/`folios_inv_inicial`, `folio_requisicion`/`folios_requisiciones`) **sí están en uso hoy en producción** — el frontend (`Compras.js:2121-2128`) los manda ambos en cada request real, y el backend los lee con fallback `plural or singular` (`server.py`, endpoint de auditoría operativa). No es código muerto.
- `Compras_Pedidos`, `Compras_Ordenes`, `Compras_Recepciones` **no están registradas en `Sistema_Gobierno_Tablas`** — aparecen `SIN_CLASIFICAR` en `docs/reports/MATRIZ_CANONICIDAD_TABLAS_EDARSAHUB.md`. Canonicalizar Folio de fondo implica primero resolver esta clasificación pendiente.
- Dos módulos fuera de Compras (`alertas_estrategicas/routes.py`, `backfill_corporativo/service.py`) leen la columna `Compras_Pedidos.FolioPedido` directamente — cualquier rename de columna los afectaría.
- Los nombres de columna en MPRO que asumía esta auditoría (`Pd_Folio`/`Rc_Folio`, §8) no coinciden con lo que usa hoy el job de sync real (`sync_service.py` usa `Pc_Folio`/`Oc_Folio`/`Re_Folio`); `Pd_Folio` sí existe pero en una superficie live independiente (`catalogo/consultas_mpro.py`, contra una tabla `Pedido` distinta de `Pedido_Compra`). Es decir, hay una 4ª convención de nombres no documentada antes.

Dado ese alcance, el usuario decidió **no** acometer la consolidación completa ahora. Se hizo solo la limpieza 100% segura y confirmada como código muerto:
- Campo `folio_documento` de `DetalleMovimientosRequest` en `backend/modules/compras/schemas.py` — nunca se leía en el endpoint (`server.py`, `obtener_detalle_movimientos_post`) ni lo mandaba ningún caller de frontend.
- Las 3 funciones stub inalcanzables `_legacy_calcular_pedido_sugerido_live_disabled`, `_legacy_obtener_productos_para_captura_live_disabled`, `_legacy_realizar_auditoria_operativa_live_disabled` — sin decorador `@api_router`, solo hacían `raise RuntimeError(...)`.

**Pendiente real, diferido a una iniciativa aparte (no una simple continuación de este audit):** consolidar los campos plural/singular de folio, registrar `Compras_Pedidos`/`Ordenes`/`Recepciones` en `Sistema_Gobierno_Tablas`, y resolver la inconsistencia de nombres MPRO entre `sync_service.py` y `catalogo/consultas_mpro.py`. Requiere su propio ciclo de auditoría-autorización dado que toca comportamiento en vivo y un vacío de gobierno de datos, no solo una limpieza de código.

---

## 1. VEREDICTO EJECUTIVO (ESTADO ORIGINAL AL MOMENTO DE LA AUDITORÍA — ver §0 para lo corregido después)

| Máxima / Requisito | Estado | Severidad |
|---|---|---|
| Máxima 1 — NO-LIVE en dashboards | ❌ **VIOLADA** (en producción, vía frontend) | 🔴 CRÍTICA |
| Máxima 3 — Sincronización controlada (conexión live solo en jobs) | ❌ **VIOLADA** | 🔴 CRÍTICA |
| Máxima 6 — Credenciales nunca al frontend | ⚠️ Riesgo indirecto (credenciales viajan por función live, no se detectó fuga directa al cliente) | 🟡 MEDIA |
| Máxima 7 — RBAC SQL-native (permisos funcionales) | ❌ **NO IMPLEMENTADA** para Compras | 🔴 CRÍTICA |
| Máxima 2/9 — MongoDB como fuente | ✅ CUMPLE (migración completada) | — |
| Máxima 6bis — No hardcode de unidades/servidores | ✅ CUMPLE | — |
| Inyección SQL (fuera de las 11 máximas, pero bloqueante para v1.0) | ❌ **CONFIRMADA** | 🔴 CRÍTICA |
| Folios end-to-end | ⚠️ Inconsistente, sin saneamiento de entrada | 🟠 ALTA |

**Conclusión:** el menú Compras **no está listo para v1.0**. El problema no es diseño ausente — existe una capa "SQL-First" NO-LIVE y con permisos ya construida en paralelo — sino que **el frontend nunca fue migrado a ella** y los endpoints legacy que sí usa producción tienen inyección SQL y cero enforcement de permisos funcionales.

---

## 2. ARQUITECTURA ENCONTRADA: DOS RUTAS PARALELAS, SOLO UNA EN USO

Para casi cada operación de Compras existen **dos endpoints**:

| Legacy (usado por frontend) | SQL-First (NO-LIVE, existe pero NO se usa) |
|---|---|
| `GET /compras/dashboard/{server_id}` (`server.py:12398`) | `GET /compras/dashboard-sql-first/{server_id}` (`server.py:12887`) |
| `GET /compras/inventarios-fisicos/{server_id}` (`server.py:9081`) | `GET /compras/inventarios-fisicos-sql-first/{server_id}` (`server.py:9176`) |
| `GET /compras/pedidos-vigentes/{server_id}` (`server.py:9276`) | `GET /compras/pedidos-vigentes-sql-first/{server_id}` (`server.py:9473`) |
| `GET /compras/facturas-proveedor/{server_id}` (`server.py:12569`) | `GET /compras/facturas-proveedor-sql-first/{server_id}` (`server.py:12675`) |
| `GET /compras/detalle-factura/{server_id}/{folio}` (`server.py:12623`) | `GET /compras/detalle-factura-sql-first/{server_id}/{folio}` (`server.py:12751`) |
| `POST /compras/detalle-movimientos` (`server.py:12062`) | `POST /compras/detalle-movimientos-sql-first` (`server.py:12192`) |
| `POST /compras/detalle-consumos` (`server.py:12314`) | `POST /compras/detalle-consumos-sql-first` (`server.py:12811`) |
| `POST /compras/productos-para-captura` (`server.py:10234`) | `POST /compras/productos-para-captura-sql-first` (`server.py:10508`) |

**Evidencia de que el frontend solo llama a la ruta legacy** (`frontend/src/pages/Compras.js:131,574,587,672,931,1000,1030,1786,1810,1882,1920,2012,2115`): ninguna llamada contiene `-sql-first`. Confirmado por grep — cero resultados de `sql-first` en `Compras.js` ni en `frontend/src/lib/api.js`.

Además, cada endpoint `-sql-first` está detrás de un feature flag apagado por defecto:
```python
if os.environ.get('COMPRAS_SQL_FIRST_ENABLED', 'false').lower() != 'true':
    return {'status': 'DISABLED', ...}
```
(`server.py:9494`, `10532`, `12214`, y análogos). No se encontró esta variable definida en ningún `.env` del repo — es decir, **la ruta compliant está muerta en la práctica** y la ruta que sirve a los usuarios reales es la live/legacy.

---

## 3. MÁXIMA 1 / 3 — CONEXIÓN LIVE DESDE ENDPOINTS DE DASHBOARD (CRÍTICO)

Los endpoints legacy activos consultan MPRO/SoftRestaurant **en tiempo real**, en el momento del request HTTP del usuario, vía `execute_sql_query(server['host'], server['port'], ...)`. Esto es exactamente el antipatrón prohibido en `docs/EDARSAHUB_MAXIMAS_INQUEBRANTABLES.md` (líneas 40–57) — el endpoint no está en `/scheduler/`, `/jobs/` ni `/sync/`.

Evidencia puntual (patrón se repite decenas de veces entre `server.py:9081` y `server.py:12960`):
- `server.py:9426-9438` — `obtener_detalle_pedido_manual`: construye query con `f"""...{folio}..."""` y la ejecuta contra `server['host']` en vivo.
- `server.py:9662-9689` — `obtener_detalle_pedido`: mismo patrón, dos queries live contra MPRO.
- El bloque completo `9081-9700` (`obtener_inventarios_fisicos`, `obtener_pedidos_vigentes`) encadena decenas de `execute_sql_query(...)` contra el servidor origen dentro del handler HTTP.

El propio código sabe que esto es lo prohibido — los comentarios en los endpoints `-sql-first` lo dicen explícitamente: *"Sin fallback LIVE"*, *"NO conecta a SoftRestaurant/MPRO directamente"* (`server.py:9482-9484`, `12089`). Es decir, el equipo ya diagnosticó el problema y construyó la solución; falta el corte (cutover).

**Nota de blindaje cruzada:** el reporte previo `docs/reports/auditoria_finanzas_filtros_datos_unidades.md` documenta explícitamente que Compras fue tratado como módulo "blindado / no tocar" durante la auditoría de Finanzas — es decir, este problema es preexistente y conocido, no introducido recientemente.

---

## 4. INYECCIÓN SQL (bloqueante, no es parte de las 11 máximas pero impide "operativo v1.0")

**Estado: ✅ CORREGIDO 2026-07-19 (Fase 0 ejecutada, autorizada por el usuario).**

`folio` llegaba como parámetro de ruta (`str`, sin validar formato) y se interpolaba directo en SQL sin parametrizar en `obtener_detalle_pedido_manual` y `obtener_detalle_pedido` (funciones que en ese momento estaban en las líneas `server.py:9417-9470` y `server.py:9644-9690` de esta auditoría; los números de línea se movieron tras el parche). Se reemplazó `execute_sql_query(...)` + f-string por `execute_sql_query_params(...)` + placeholders `%s` y tupla de parámetros — mismo patrón ya usado correctamente en los endpoints `-sql-first` (p. ej. `server.py:9508-9513` en la versión original) y en `core/db.py:366` (`execute_sql_query_params`, ya existente en el repo, no se creó infraestructura nueva). Verificado con `python3 -m py_compile backend/server.py` → compila sin errores. Ambas funciones ahora en `server.py:9928` (`obtener_detalle_pedido_manual`) y `server.py:10157` (`obtener_detalle_pedido`).

Pendiente (no cubierto por Fase 0, ver §10-11): validar en runtime con una prueba de red real, y decidir si estas dos funciones deben migrarse también a NO-LIVE (siguen consultando MPRO en vivo vía `execute_sql_query_params` contra `server['host']`, ya no son inyectables pero siguen violando Máxima 1/3 — eso es Fase 2, no Fase 0).

---

## 5. MÁXIMA 7 — RBAC: CERO ENFORCEMENT FUNCIONAL, ENFORCEMENT DE ALCANCE PARCIAL

`backend/modules/auth/routes.py:514-518` define permisos funcionales para el menú Compras:
```python
"compras": ["COMPRAS_VER", "COMPRAS_DASHBOARD_VER", "COMPRAS_INVENTARIOS_VER"],
```
pero esto **solo se usa para decidir qué ítems de menú mostrar** en `/auth/me/menus` (`auth/routes.py:619`). Ningún endpoint de `/compras/*` valida estos códigos. Búsqueda exhaustiva (`grep -rn "COMPRAS_VER\|require_compras" backend/`) devuelve un único resultado: la definición del mapa de menú. **No existe un `backend/modules/compras/access.py`** análogo a `backend/modules/finanzas/access.py` (que sí implementa `require_finanzas_permission`, `get_finanzas_allowed_unidad_pks`, etc. — patrón canónico ya validado en este repo, ver commits recientes en Finanzas).

Adicionalmente, el enforcement de **alcance por servidor/unidad** (`validate_server_access_by_empresa`, `server.py:8881`) — que sí impediría a un usuario consultar una unidad que no le corresponde — solo se invoca en **7 de 28** endpoints de compras:

| Con validación de alcance | Sin ninguna validación de alcance (server_id llega directo del cliente) |
|---|---|
| `inventarios-fisicos` (9081) | `dashboard/{server_id}` (12398) — **usado por frontend** |
| `pedidos-vigentes` (9276) | `parametros/{server_id}` GET y POST (10152, 10181) |
| `detalle-pedido-manual` (9417) | `productos-para-captura` (10234) — **usado por frontend** |
| `detalle-movimientos` GET (9572) | `auditoria-operativa` (10618) *(nota: sí valida — ver tabla completa)* |
| `detalle-consumos` GET (9609) | `inventarios-provisionales` (11867, 11929, 11982, 12019) |
| `detalle-pedido/{server_id}/{folio}` (9644) | `detalle-movimientos` POST (12062) — **usado por frontend** |
| `calculo-pedido` (9691) | `detalle-consumos` POST (12314) — **usado por frontend** |
| | `analisis` (12502) — **usado por frontend** |
| | `facturas-proveedor` (12569) — **usado por frontend** |
| | `detalle-factura` (12623) — **usado por frontend** |

Es decir: **la mitad de los endpoints que el frontend realmente invoca no verifican que el `server_id`/`unidad_negocio_id` solicitado pertenezca al usuario**. Cualquier usuario autenticado (mesero, comprador de una sola unidad, etc.) puede, cambiando el parámetro en la URL, leer el dashboard, facturas y parámetros de compra de **cualquier otra unidad de negocio** — esto es un control de acceso roto a nivel de objeto (IDOR/BOLA), no solo una brecha de "máxima" arquitectónica.

Contraste positivo: `GET /unidades-negocio` (`server.py:3825-3974`) sí filtra correctamente qué unidades ve cada usuario en el selector (`server.py:3904-3927`), y `frontend/src/services/unidadesNegocioService.js` consume ese endpoint sin hardcodear nada. Pero ese filtro solo protege el *dropdown* — no protege los endpoints de datos si el usuario arma la URL directamente.

---

## 6. MONGODB — CUMPLE

Todas las menciones de MongoDB en `backend/modules/compras/*` son comentarios históricos de migración ya completada (`repository.py:11-14`, `repository_compras_sql.py:8-16`, `repository_pedidos_sql.py:7-16`, `__init__.py:59` con `init_compras_module(None)  # MongoDB eliminado`, `server.py:452`). No se detectó `pymongo`, `MongoClient` ni `motor` activo en el módulo. **Cero dependencia de Mongo confirmada.**

---

## 7. HARDCODE — CUMPLE (en la capa revisada)

- Backend: sin credenciales, IPs ni nombres de unidad (`CIENFUEGOS`, `130MID`, `ESTELAR`, etc.) hardcodeados dentro de `backend/modules/compras/*.py`.
- Frontend: `Compras.js` no contiene listas hardcodeadas de unidades/servidores; usa `fetchUnidadesNegocio()` (`frontend/src/services/unidadesNegocioService.js:36-49`) que consulta `/unidades-negocio` dinámicamente.
- Se detectaron sí varios `TODO` sin resolver (`server.py:2257` — *"TODO: Implementar para MPRO si es necesario"*) y retornos `0.0` de relleno (`server.py:2300`, `2456`) que deberían revisarse caso por caso antes de v1.0, aunque no son "hardcode" en el sentido de la máxima.

---

## 8. FOLIOS — INCONSISTENTE, SIN CANONIZAR

No existe un campo `Folio` único y canónico de extremo a extremo; conviven al menos tres convenciones simultáneas según el sistema origen y la tabla EDARSAHUB:

| Capa | Nombre de campo | Ejemplo |
|---|---|---|
| MPRO — Pedido | `Pd_Folio` (`server.py:9451,9671`) | — |
| MPRO — Orden de compra | `Oc_Folio` (`server.py:9457,9683`, `274`) | — |
| MPRO — Requisición | `Rc_Folio` (`server.py:9433`) | — |
| EDARSAHUB canónico (sync) | `Compras_Pedidos.Folio`, `Compras_Ordenes.Folio`, `Compras_Recepciones.Folio` (`server.py:1004-1009`) | — |
| Schemas de request | `folio_inventario_fisico`, `folio_pedido_comparar`, `folio_inv_inicial`/`folios_inv_inicial` (legacy singular + nuevo plural conviviendo), `folio_requisicion`/`folios_requisiciones` (`schemas.py:34-64`) | ambos conviven "por compatibilidad" |

Riesgos concretos:
1. El folio nunca se valida/normaliza antes de usarse en SQL (ver §4 — inyección).
2. `schemas.py` mantiene simultáneamente la forma legacy singular y la nueva plural para folios de inventario/requisición sin un adaptador único que las unifique — cualquier cliente nuevo debe conocer ambas.
3. No hay una vista o tabla `Sistema_Gobierno_Tablas`-registrada que documente "Folio" como concepto canónico único (Máxima 4/11) — cada tabla de compras define su propio campo Folio de forma independiente sin un mapeo central documentado.

**Recomendación:** antes de v1.0, definir `FolioCanonico` (o similar) como concepto único documentado en gobierno de tablas, con función de normalización compartida (regex de formato válido) aplicada en el borde de entrada de cada endpoint — no solo por estética, sino porque es la causa raíz de la inyección SQL de §4.

---

## 9. ARCHIVOS REVISADOS

**Backend:**
`backend/modules/compras/routes.py`, `service.py`, `schemas.py`, `repository.py`, `repository_compras_sql.py`, `repository_pedidos_sql.py`, `sync_service.py`, `eventos_compras.py`, `system_type_utils.py`, `historical_kpis_repository.py`, `sql_first_repository.py`, `adapters/*`, `__init__.py`; `backend/server.py` líneas 421-452, 815-1220, 3825-3974, 8881-8977, 9081-12960; `backend/modules/auth/routes.py` líneas 440-650; `backend/modules/finanzas/access.py` (referencia de patrón canónico); `backend/core/policies/no_live_dashboard_policy.py`.

**Frontend:**
`frontend/src/pages/Compras.js`, `frontend/src/services/unidadesNegocioService.js`, `frontend/src/lib/api.js` (grep de rutas `/compras/*`).

---

## 10. PENDIENTES / BLOQUEOS PARA CERRAR ESTA AUDITORÍA

Por calibración de auditoría (evidencia solo de código estático), **falta evidencia de Network real** (request/response en vivo) para confirmar en runtime:
- Que `COMPRAS_SQL_FIRST_ENABLED` efectivamente está apagado en el entorno de producción/staging actual (solo se confirmó que no hay default `true` ni `.env` en el repo).
- Explotabilidad real de la inyección en `folio` contra una base MPRO viva (no se ejecutó ningún query, por regla de auditoría solo-lectura).

**BLOQUEADO** para certificar runtime: se requiere autorización explícita del usuario para ejecutar una prueba de red controlada (`curl`/Postman) contra un entorno de staging, o compartir logs de acceso reales.

---

## 11. PLAN DE REMEDIACIÓN PROPUESTO PARA v1.0 (SIN EJECUTAR — PENDIENTE AUTORIZACIÓN)

1. **Fase 0 (bloqueante, urgente):** parametrizar las 5 queries con inyección SQL de §4 (`server.py:9433,9451,9457,9671,9683`). Riesgo bajo, cambio quirúrgico.
2. **Fase 1 (RBAC):** crear `backend/modules/compras/access.py` siguiendo el patrón ya validado de `backend/modules/finanzas/access.py` (`require_compras_permission`, `get_compras_allowed_unidad_pks`) y aplicarlo a los 10 endpoints activos del frontend que hoy no validan alcance (§5).
3. **Fase 2 (NO-LIVE cutover):** migrar `frontend/src/pages/Compras.js` para consumir los endpoints `-sql-first` ya existentes, activar `COMPRAS_SQL_FIRST_ENABLED`, validar paridad de datos por unidad (mismo patrón de blindaje usado en la auditoría de Finanzas), y solo entonces retirar/deprecar los endpoints legacy live.
4. **Fase 3 (Folios):** documentar y normalizar el concepto canónico de Folio (Máxima 4/11), con función única de saneamiento de entrada reutilizada por todos los endpoints.

Cada fase requiere autorización y validación de no-regresión por unidad antes de avanzar a la siguiente, siguiendo el mismo protocolo ya usado en las auditorías de Finanzas y Comercial de este repositorio.

---

**Siguiente agente recomendado:** EDARSA Auditor (para completar validación de Network con autorización) o EDARSA Coder (para Fase 0, con autorización explícita y dry-run previo).

HANDOFF:
next_agent: EDARSA Copilot Supervisor
reason: Se requiere autorización explícita del usuario para ejecutar cualquier fase de remediación (empezando por Fase 0, inyección SQL) antes de involucrar a Coder.
mode: auto_if_available_otherwise_user_confirm
