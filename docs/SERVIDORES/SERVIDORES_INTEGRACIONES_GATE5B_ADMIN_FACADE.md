# EDARSAHUB BOS — Gate 5B Administrative Facade

Fecha: 2026-09-09
Rama: `Edarsahub_Desarrollo`
Alcance: Servidores / Conexiones / Integraciones / Comunicaciones
Produccion: **NO TOCADA**

## 1. Resultado ejecutivo

Gate 5B implementa una fachada administrativa unica y READ_ONLY para el futuro Centro de Comunicaciones y Conexiones.

La fachada **compone** contratos existentes; no reemplaza ni duplica:

- `dbo.Servidores_Conexiones`
- `backend/core/server_registry.py`
- `backend/core/connection_resolver.py`
- `backend/core/connections/*`
- RBAC SQL existente
- `backend/modules/api_connections`
- `backend/api/admin_core_connections.py`
- `backend/core/communications`

No hubo DDL, DML, UI ni cambios en Produccion.

## 2. Modulo implementado

Nuevo modulo:

- `backend/modules/integrations_center/__init__.py`
- `backend/modules/integrations_center/repository.py`
- `backend/modules/integrations_center/service.py`
- `backend/modules/integrations_center/routes.py`

Pruebas de contrato:

- `backend/tests/test_integrations_center_gate5b.py`

Montaje:

- `backend/modules/api_connections/__init__.py`
- La fachada se incluye en `api_universal_test_router`, APIRouter existente sin prefijo propio.
- `backend/server.py` ya incluye ese router bajo `api_router`, cuyo prefijo es `/api`.
- Resultado: las rutas nuevas quedan bajo `/api/integrations-center/*` sin modificar `server.py`.

## 3. Endpoints Gate 5B

Todos son GET / READ_ONLY.

| Endpoint | Funcion |
|---|---|
| `GET /api/integrations-center/overview` | Resumen de conexiones, health, sync e infraestructura universal |
| `GET /api/integrations-center/connections` | Lista normalizada RBAC-aware de DATA_SOURCE, API_LOCAL y CORE autorizado |
| `GET /api/integrations-center/connections/{connection_id}` | Detalle seguro de una conexion dentro del alcance del usuario |
| `GET /api/integrations-center/catalogs` | Sistemas, versiones, capacidades, catalogo sync y puente sync-capacidad |
| `GET /api/integrations-center/communications` | Resumen de gobierno/log de Communications con `NOTIFICACIONES_VER` |

Filtros en `/connections`:

- `include_inactive`
- `connection_type`
- `system_type`
- `health_status`

## 4. Composicion canonica

### DATA_SOURCE

Origen: `core.server_registry.list_servers()`.

- Mantiene SQL-first.
- Mantiene filtrado de permisos del registry.
- No recupera secretos sin mascara.

### API_LOCAL

Origen: `modules.api_connections.repository.list_api_connections()`.

- No se crea CRUD paralelo.
- Se aplica `filter_servers_by_user_permissions()` antes de exponer la conexion.
- El API key sigue enmascarado; la fachada no proyecta valores de secretos.

### CORE

Origen: `api.admin_core_connections.get_core_connections_from_sql()` + `format_core_connection()`.

- Solo se agrega a la fachada cuando `es_superadmin(current_user)` es verdadero.
- No se debilita la regla existente de CORE.

### Health

Origen: `dbo.Servidores_ConexionEstado`.

- `activo` se conserva como flag administrativo.
- `activo` **NO** se interpreta como `CONNECTED`.
- Sin evidencia persistida, health = `UNKNOWN` / `has_evidence=false`.
- Cuando exista evidencia, se exponen estado, ultima prueba, exito/error, latencia y sync desde la tabla canonica.

### Sistemas y versiones

Reutiliza:

- `dbo.Sistema_Tipos`
- `dbo.Sistema_VersionesSistemas`

No se crea catalogo paralelo.

### Capacidades y sync

Reutiliza:

- `dbo.Sistema_Capacidades`
- `dbo.Sistema_Sync_Catalogo`
- `dbo.Sistema_Sync_Capacidades`
- `dbo.Sync_Control_Ejecuciones`

Gate 5B solo lee. Gate 5C conectara writers y adopcion real.

### Alcance corporativo

Se expone exclusivamente evidencia ya presente en el contrato de conexion:

- `empresa_id`
- `sucursales`

`unidad_negocio_ids` se devuelve vacio mientras no exista un mapeo inequivoco certificado dentro del contrato de conexion. No se infiere ni se fabrica una relacion de unidad.

### Secretos

La fachada solo expone metadata:

- `password_configured`
- `api_key_configured`

Quedan excluidos valores/campos de secreto como password, password_encrypted, password_decrypted, api_key, api_key_encrypted, api_key_decrypted, token y secret.

### Communications

Reutiliza:

- `dbo.Sistema_NotificacionesConfig`
- `dbo.Operativo_Notificaciones_Log`
- `backend/core/communications`
- permiso `NOTIFICACIONES_VER`

La ruta legacy `/api/v2/notificaciones-whatsapp` permanece como compatibilidad hasta Gate 5D. No se crea arquitectura por proveedor.

## 5. Compatibilidad

Gate 5B no elimina ni redirige writers existentes.

Se mantienen:

- `/api/servers`
- `/api/api-connections`
- `/api/admin/core-connections`
- `/api/v2/notificaciones-whatsapp`
- Universal Query Tester existente

La nueva fachada es el contrato de lectura que consumira la UI en Gate 5E. Los endpoints legacy siguen siendo adapters durante la transicion.

## 6. Pruebas de contrato incluidas

`backend/tests/test_integrations_center_gate5b.py` cubre:

1. todas las rutas Gate 5B son GET;
2. los paths esperados existen;
3. la fachada se monta sobre el router API existente;
4. secretos no se proyectan;
5. `activo=true` no inventa health;
6. health solo cambia a conectado cuando existe evidencia canonica.

Ademas se corrigieron dos riesgos detectados durante la auditoria de implementacion:

- import lazy de `api_connections.repository` para evitar ciclo de inicializacion del paquete;
- comparacion case-insensitive de UUID para health/enrichment sin modificar el ID entregado al cliente.

## 7. Validacion automatica — estado real

La implementacion esta integrada en Desarrollo y la revision estructural del contrato queda cerrada.

Se agrego una certificacion dirigida en:

- `.github/workflows/servers-integrations-gate5b-cert.yml`
- commit disparador: `4d779f3d509dbb3e9df2a153904ad123c5fd9a3d`
- check: `certify-gate5b`
- run: `34410295298`

El job termino `failure` antes de ejecutar cualquier step: GitHub reporto `steps=[]`. Por tanto no llego a checkout, instalacion de dependencias, `py_compile`, `pytest` ni mount-check. Es un fallo de infraestructura/runner y **no evidencia un fallo del codigo**, pero tampoco permite declarar certificacion runtime PASS.

La validacion estatica adicional confirmo que los nombres de columnas usados por la fachada coinciden con contratos existentes ya usados por el repositorio (`Sistema_Tipos` y `Sistema_VersionesSistemas`) y que la fachada no introduce writers.

Estado honesto:

- IMPLEMENTACION_REPO = 100%
- REVISION_ESTRUCTURAL = PASS
- STATIC_SCHEMA_CONTRACT = PASS
- AUTOMATED_RUNTIME_CERTIFICATION = PENDING_INFRASTRUCTURE
- DDL_EXECUTED = NO
- DML_EXECUTED = NO
- PRODUCTION_TOUCHED = NO

## 8. Limite Gate 5B / siguiente Gate

Gate 5B no escribe health, ledger, evidencia, capacidades ni IDs externos.

Gate 5C debe conectar los flujos reales, en este orden:

1. persistencia de prueba/health en `Servidores_ConexionEstado`;
2. writer comun de `Sync_Control_Ejecuciones` usando `ConexionID`, `UnidadNegocioID`, `CodigoSync`, UTC e idempotencia;
3. `Sync_Control_Evidencias`;
4. adopcion de `Sistema_Sync_Capacidades`;
5. `Sistema_IdentificadoresExternos`;
6. resolucion real de timezone/locale por unidad.

Gate 5D reconectara configuracion/providers/templates/queue de Communications a SQL canonico existente.
Gate 5E construira la UI consumiendo esta fachada.

## 9. Cierre

`GATE_5B_IMPLEMENTATION = 100%`

La fachada administrativa unica esta implementada sin reemplazar `Servidores_Conexiones`, `server_registry`, resolvers ni RBAC. La certificacion automatica queda pendiente exclusivamente por indisponibilidad del runner y debe ejecutarse antes de declarar `GATE_5B_CERTIFIED=100%`.
