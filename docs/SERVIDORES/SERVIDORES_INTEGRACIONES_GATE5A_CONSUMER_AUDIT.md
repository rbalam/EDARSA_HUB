# EDARSAHUB BOS — Gate 5A Consumer Audit

Fecha: 2026-09-09
Rama: `Edarsahub_Desarrollo`
Alcance: Servidores / Integraciones / Comunicaciones
Produccion: **NO TOCADA**

## 1. Resultado ejecutivo

Gate 5A audito consumidores reales antes de construir la UI unificada. La infraestructura de Gate 4 esta creada y certificada, pero su adopcion funcional todavia es parcial.

Resultado de auditoria SQL READ_ONLY ejecutada con `HRLectura` en GitHub Actions run `34382322790`:

- `GATE5A_READONLY=PASS`
- `PRODUCTION_TOUCHED=NO`
- Base: `EDARSAHUB`
- Conexiones registradas: **26**
- Conexiones activas: **14**
- `Servidores_ConexionEstado`: **0 filas**
- `Sync_Control_Ejecuciones`: **4,712 filas legacy**
- Runs con `ConexionID`: **0**
- Runs con `UnidadNegocioID`: **0**
- Runs con `CodigoSync`: **0**
- Runs con timestamps UTC nuevos: **0**
- Runs con `IdempotencyKey`: **0**
- `Sistema_Sync_Capacidades`: **0 filas**
- `Sync_Control_Evidencias`: **0 filas**
- `Sistema_IdentificadoresExternos`: **0 filas**
- Unidades: **5**
- Unidades con `timezone_iana`: **0**
- Unidades con `locale_operativo`: **0**
- `Operativo_Notificaciones_Log`: **0 filas**

Conclusión: **Gate 4 resolvio la infraestructura; Gate 5 debe conectar los consumidores reales. No se requiere crear otra infraestructura paralela.**

## 2. Matriz de consumidores

| Consumidor / superficie | Estado Gate 5A | Evidencia | Accion siguiente |
|---|---|---|---|
| `dbo.Servidores_Conexiones` | **YA USA** | Fuente SQL canonica de conexiones | NO TOCAR estructura base; reutilizar |
| `backend/core/server_registry.py` | **YA USA** | CRUD `/api/servers` y numerosos consumidores migrados desde `db.servers` | Mantener como acceso canonico existente |
| `backend/core/connection_resolver.py` y `backend/core/connections/*` | **YA USA / NO DUPLICAR** | Resolvers existentes | Reusar; no crear otro resolver |
| `/api/servers` CRUD | **YA USA** | Diagnosticos previos confirman POST/GET/PUT/DELETE en registry SQL | Mantener compatibilidad |
| `backend/modules/api_connections` CRUD | **YA USA PARCIAL** | Lee/escribe `Servidores_Conexiones`; secrets enmascarados | Integrar al API administrativo unificado sin duplicar CRUD |
| `frontend/src/pages/Servidores.js` | **MIGRAR / CONSOLIDAR** | Consume `/api-connections` separado del flujo `/servers` | Gate 5E debe consumir una fachada administrativa unica |
| `UniversalQueryTester.jsx` | **MIGRAR / COMPATIBILIDAD** | Separa endpoint API vs SQL | Backend unificado primero; conservar adapter hasta migrar UI |
| `test_api_connection_health()` | **MIGRAR PRIORIDAD P0** | Prueba conectividad pero no persiste health | Escribir resultado canonico en `Servidores_ConexionEstado` |
| `dbo.Servidores_ConexionEstado` | **INFRA SIN CONSUMIDOR** | 0 filas | Gate 5C: health writer + reader derivados de evidencia real |
| flag `Servidores_Conexiones.activo` | **NO USAR COMO HEALTH** | Configuracion actual usa `activo`; tabla health vacia | Mantener como enable/config flag; estado operativo sale de health |
| `/test-api-connection` en `backend/server.py` | **DEPRECAR P0** | Recibe URL/API key y hace `requests.get` directo | Sustituir por test por `ConexionID`, resolver, secret server-side, RBAC y health persistido |
| `/api-connections/sync-cache` | **DEPRECAR NOMBRE/COMPAT** | Mongo ya no sincroniza; endpoint es no-op de compatibilidad | Mantener temporalmente adapter; retirar del Centro unificado |
| `Sync_Control_Ejecuciones` | **YA USA LEGACY / MIGRAR IN PLACE** | 4,712 filas, 0 en todos los campos universales | Gate 5C: writer comun que complete contexto, UTC e idempotencia |
| jobs `sync_compras`, `detect_nuevos_compras`, `sync_recetas`, `sync_historicos` | **MIGRAR** | Consumen/escriben ledger legacy | Integrar mediante servicio comun, sin crear otro ledger |
| `Sync_Control_Evidencias` | **INFRA SIN CONSUMIDOR** | 0 filas | Gate 5C: registrar hashes/referencias de evidencia por run |
| `Sistema_Sync_Capacidades` | **INFRA SIN CONSUMIDOR** | 0 filas | Gate 5C: poblar relacion desde catalogos existentes y usarla para elegibilidad |
| `Sistema_IdentificadoresExternos` | **INFRA SIN CONSUMIDOR** | 0 filas | Gate 5C: adapters registran IDs externos aqui; no crear columnas por proveedor |
| `Unidades_Negocio.timezone_iana` / `locale_operativo` | **INFRA SIN ADOPCION** | 5 unidades, 0 configuradas | Gate 5C: configuracion + resolver operativo por unidad |
| `backend/core/utils/operational_window.py` y fecha operativa | **MIGRAR** | Historicamente usa timezone Mexico City | Resolver Unidad > timezone IANA antes de turno; sin hardcode global |
| `backend/core/communications/notifications/repository.py` logs | **YA USA SQL** | `Operativo_Notificaciones_Log` SQL-first | Reutilizar auditoria/log existente |
| Communications config/provider/templates/queue | **MIGRAR / RECONECTAR** | Repository SQL-first los tiene neutralizados (`None`, `[]`, no-op) | Auditar `Sistema_NotificacionesConfig` y reutilizar antes de DDL nuevo |
| `/api/v2/notificaciones-whatsapp/*` | **COMPATIBILIDAD / MIGRAR** | RBAC existe pero superficie es canal/proveedor-especifica | Fachada administrativa generica en Gate 5B/5D; conservar compatibilidad transitoria |
| RBAC existente | **YA USA / EXTENDER SOLO SI FALTA** | Communications usa `NOTIFICACIONES_*`; tablas RBAC canonicas existen | Gate 5B/5F: mapear permisos exactos, no crear RBAC paralelo |

## 3. Hallazgos por dominio

### 3.1 Conexiones

La administracion base de servidores esta mucho mas avanzada que la nueva infraestructura de health. `Servidores_Conexiones` ya es la fuente SQL y `server_registry` ya reemplazo numerosos bypasses Mongo. Esto se conserva.

La brecha principal es semantica: **`activo` no equivale a conectado**. Gate 5 debe separar:

- `activo`: habilitacion/configuracion administrativa.
- health: ultima prueba, ultimo exito/error, latencia, ultima sync y ultima sync exitosa.

Hoy `Servidores_ConexionEstado` tiene cero filas, por lo que cualquier UI que pinte "conectado/sin conexion" sin escribir/leer esta evidencia todavia usa una señal incompleta o legacy.

### 3.2 Sync / ejecuciones

`Sync_Control_Ejecuciones` es el ledger correcto y ya tiene historia real: 4,712 filas. No debe reemplazarse. La migracion es **in place**.

Los campos Gate 4 estan 0% adoptados. Debe existir un unico helper/service de ejecucion que pueda convivir con las columnas legacy y complete gradualmente:

- `ConexionID`
- `UnidadNegocioID`
- `CodigoSync`
- `StartedAtUTC`
- `FinishedAtUTC`
- `IdempotencyKey`

Los jobs no deben implementar cada uno una variante propia de la escritura del ledger.

### 3.3 Capacidades e IDs externos

Las tablas universales existen y estan vacias. Eso es correcto para una infraestructura recien aplicada, pero confirma que **ningun provider/adaptador real las consume aun**.

Gate 5C debe conectar adapters existentes a:

- `Sistema_Sync_Capacidades`
- `Sistema_IdentificadoresExternos`

No deben aparecer `ToastLocationID`, `NetPayFooID`, `TwilioSomethingID` u otras columnas dispersas por proveedor.

### 3.4 Timezone / locale

Las cinco unidades carecen de `timezone_iana` y `locale_operativo`. Por tanto, la precedencia objetivo Unidad > Empresa > Plataforma aun no puede operar desde estas columnas.

Gate 5C debe resolver configuracion y consumo. No corresponde introducir otro campo de timezone ni mantener `America/Mexico_City` como regla global cuando exista valor de unidad.

### 3.5 Comunicaciones

Communications ya tiene infraestructura real, RBAC y log SQL. No se debe reescribir como un monolito de conexiones.

La deuda relevante es que config/provider/templates/queue quedaron neutralizados durante el retiro de Mongo. Antes de crear cualquier tabla nueva, debe auditarse y reutilizarse `Sistema_NotificacionesConfig` y estructuras SQL existentes.

La ruta `/api/v2/notificaciones-whatsapp` puede mantenerse por compatibilidad, pero **no debe convertirse en la navegacion primaria del Centro**. WhatsApp/Twilio es un adapter/canal, no una entidad arquitectonica superior.

## 4. Orden de migracion aprobado por Gate 5A

### Gate 5B — API administrativa unificada

Crear/reusar una fachada backend de administracion que componga, no duplique:

- conexiones
- sistema/version
- capacidades
- health
- sync
- alcance empresa/unidad/sucursal
- metadata de secretos, nunca valores
- communications governance

Debe mantener endpoints legacy como adapters durante la transicion.

### Gate 5C — adopcion de flujos reales

Prioridad:

1. health writer/reader en `Servidores_ConexionEstado`;
2. writer comun de `Sync_Control_Ejecuciones` con nuevos campos;
3. evidencia e idempotencia;
4. capacidades↔sync;
5. IDs externos;
6. timezone/locale por unidad.

### Gate 5D — Communications

Reconectar config/provider/templates/queue a SQL canonico existente, con auditoria previa de `Sistema_NotificacionesConfig`; integrar providers bajo gobierno comun sin tabs/arquitectura por proveedor.

### Gate 5E — UI

Solo despues de 5B-5D: Centro de Comunicaciones y Conexiones con filtros por tipo, capacidad, empresa, unidad, sistema, estado y direccion. Frontend pinta datos del backend; no decide health ni conexiones.

### Gate 5F — RBAC y E2E

Validar lectura/administracion/test/activacion/sync/rotacion por permisos y alcance corporativo.

### Gate 5G — certificacion funcional

Certificar flujo completo conexion -> test -> health -> sync -> evidencia -> UI, sin secreto expuesto, sin Mongo, sin provider-specific architecture y sin Production.

## 5. NO TOCAR / NO CREAR

- `Edarsahub_Produccion`.
- Otra tabla de conexiones.
- Otro ledger de ejecuciones.
- Otro resolver de conexiones.
- Otro RBAC.
- Otra tabla FX/moneda.
- Otra tabla de health.
- Robots/tablas `Toast_*`.
- Copias de arquitectura NetPay/Twilio por proveedor.
- Nuevas tablas de Communications antes de auditar `Sistema_NotificacionesConfig` y objetos existentes.

## 6. Cierre Gate 5A

**GATE_5A = 100% AUDIT COMPLETE**

La infraestructura Gate 4 esta disponible, pero su adopcion funcional universal es esencialmente **0% en health, contexto universal de sync, evidencia, capacidades↔sync, IDs externos y timezone/locale**. Esto no es un fallo de Gate 4: define exactamente el trabajo de Gate 5C.

La base de conexiones existente (`Servidores_Conexiones` + registry/resolvers) ya tiene adopcion significativa y debe ser reutilizada. Gate 5B no debe reemplazarla; debe ofrecer una fachada administrativa cohesionada para que Gate 5E pueda construir la UI sin duplicar logica.

Evidencia SQL: GitHub Actions run `34382322790`, `HRLectura`, `GATE5A_READONLY=PASS`, Production `NO`.
