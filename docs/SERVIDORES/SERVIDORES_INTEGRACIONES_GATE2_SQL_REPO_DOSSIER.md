# GATE 2 — Dossier canónico SQL ↔ repo

## Frente
Servidores + Conexiones + Comunicaciones + Robot Universal + Toast + Internacionalización.

## Estado de certificación de entrada
- Gate 1: `READ_ONLY_COMPLETE / CERTIFIED_READ_ONLY / 100%`.
- Gate 2A: `READ_ONLY_COMPLETE / CERTIFIED_READ_ONLY / 100%`.
- Gate 2A basis: `READ_ONLY_SQL_PASS_PLUS_SANITIZED_EVIDENCE`.
- Gate 2A terminó sin blockers, sin files_changed y sin tocar Producción.
- Evidencia SQL obtenida por `readonly_sql_connection:default` / HRLectura.

## Regla de gobierno
Este dossier NO autoriza DDL. Antes de crear cualquier objeto se debe reutilizar lo existente y, cuando exista un gap real, diseñar el cambio mínimo en un gate posterior con preflight READ_ONLY_SQL. No Mongo como fuente/cache. No LIVE para tableros/reportes. No hardcodes. No robot Toast específico. Secretos nunca al frontend/logs/resultados.

## Matriz canónica REUSE / EXTEND / CREATE / DO_NOT_TOUCH

| Dominio | Evidencia SQL + repo | Decisión | Acción posterior permitida |
|---|---|---|---|
| Empresas | `dbo.Sistema_Empresas` existe y contiene identidad corporativa (`EmpresaID`, `CodigoEmpresa`, nombres, RFC, activo, auditoría). | REUSE | Reutilizar; no crear catálogo paralelo. |
| Unidad / perfil digital | `dbo.Sistema_UnidadesNegocioPerfilDigital` existe con `EmpresaID`, `UnidadNegocioID`, `ServerID`, ubicación, `Pais`, `Moneda`, URLs y metadata. El barrido dirigido no encontró `Sistema_UnidadesNegocio` con ese nombre exacto; el repo además usa servicios/catálogos de unidad existentes y `Unidades_Negocio` en compatibilidad. | REUSE / EXTEND | Resolver primero el catálogo canónico vigente de unidad; no crear otra tabla de unidades. Extender solo metadata faltante después de preflight. |
| Conexiones | `dbo.Servidores_Conexiones` existe y ya contiene conexión, tipo de sistema, credenciales cifradas, empresa/sucursales, queries/config, auditoría y `sistema_version_id`. | REUSE / EXTEND | Mantener como raíz de conexión. Normalizar relaciones faltantes sin duplicar conexión. |
| Sistema / aliases | `dbo.Sistema_Tipos` + `dbo.Sistema_TiposVariantes` existen. Repo tiene `SystemCapabilityResolver` SQL-first para normalizar aliases y consultar capacidades. | REUSE | No hardcodear Toast/MPRO/SoftRestaurant como arquitectura paralela. |
| Capacidades | `dbo.Sistema_Capacidades` existe y FK `SistemaTipoID -> Sistema_Tipos`. Repo ya tiene resolver central. | REUSE / EXTEND | Agregar capacidades como datos canónicos si faltan; no crear otro catálogo. |
| Versiones de sistemas | `dbo.Sistema_VersionesSistemas` existe. `Servidores_Conexiones.sistema_version_id` tiene FK `FK_Servidores_Conexiones_SistemaVersion`. Repo conserva script idempotente de control de versiones. | REUSE | Toda versión Toast/Soft/MPRO debe usar este modelo. |
| Mapeo por versión | `dbo.Sistema_MapeoTablasVersion` y `dbo.Sistema_MapeoColumnasVersion` existen y están enlazadas por FK a versión/mapeo. | REUSE / EXTEND | Usarlas como layout/mapeo declarativo por versión; no crear mapeadores físicos paralelos por proveedor. |
| Catálogo de sync | `dbo.Sistema_Sync_Catalogo` existe con permisos de resync, Handler/HandlerImplementado, destino, dependencias y activo. Repo `sync_catalogo_service.py` declara esta tabla como fuente única SQL. | REUSE / EXTEND | Relacionar capacidades/versiones/conexiones con el catálogo mediante el mínimo modelo faltante; no hardcodear scheduler. |
| Relación capacidades ↔ sync | Gate 2A descubrió objetos sync, pero no evidencia una relación canónica explícita y fuerte entre `Sistema_Capacidades` y `Sistema_Sync_Catalogo`. | CREATE_MINIMAL_RELATION if preflight confirms absence | Gate posterior debe auditar nombres/keys y proponer una relación mínima, no duplicar catálogos. |
| Secretos / credenciales | `Servidores_Conexiones` ya tiene `password_encrypted` y `api_key_encrypted`; Gate 2A encontró además `Finanzas_AdquirenteConectorCredenciales` en otro dominio. | EXTEND existing connection-secret model / DO_NOT_REUSE_FINANZAS | No crear vault genérico hasta auditar patrón exacto. No reutilizar tabla Finanzas para integraciones generales. Nunca copiar valores secretos. |
| Identificadores externos | Gate 2A `external_identifier_objects` devolvió 0 objetos con nomenclatura canónica explícita. Existen columnas externas dispersas. | CREATE candidate, ONLY after exact preflight | Diseñar tabla relacional genérica de IDs externos solo si un preflight demuestra que no existe equivalente semántico con otro nombre. |
| Layout / homologación | Gate 2A encontró objetos de layout/mapeo y ya existen `Sistema_MapeoTablasVersion`/`Sistema_MapeoColumnasVersion`. | REUSE / EXTEND | Declarar layouts por sistema/versión sobre estructuras existentes; no robot específico Toast. |
| Ejecución / evidencia / idempotencia | Gate 2A encontró 23 objetos candidatos de ejecuciones/evidencia. | REUSE-FIRST / AUDIT_REQUIRED | Antes de CREATE, auditar cuál es canónico para sync runs, evidencia, retry e idempotencia. |
| Turnos operativos | Gate 1 certificó `Sistema_TurnosOperativosUnidad`; repo lo usa para FechaOperacion. | REUSE / DO_NOT_TOUCH semantics | Mantener día operativo por unidad. No sustituir por día civil. |
| Timezone por unidad | Gate 2A dirigido no evidenció una columna IANA canónica en la estructura de unidad; repo todavía contiene `America/Mexico_City` como constante operativa en rutas/utilidades. | EXTEND candidate | Gate posterior debe ubicar la tabla canónica exacta de unidad y añadir/usar timezone IANA parametrizable solo si sigue ausente. Eliminar hardcode global gradualmente. |
| Idioma / locale | Gate 2A no certificó un modelo canónico claro de locale/idioma por unidad. | EXTEND or CREATE_CHILD candidate | Preflight específico antes de DDL; preferir metadata de unidad existente. |
| Moneda | `Sistema_UnidadesNegocioPerfilDigital.Moneda` existe; múltiples objetos financieros manejan tipo de cambio. | REUSE / AUDIT_FX | Reutilizar moneda de unidad; determinar fuente FX canónica antes de crear nada. |
| FX | Gate 2A encontró 44 objetos/constraints candidatos relacionados con moneda/tipo de cambio, por lo que no es válido crear una tabla FX nueva todavía. | DO_NOT_CREATE_YET | Auditar y elegir fuente canónica existente. |
| RBAC | Gate 2A encontró múltiples objetos de roles/permisos, incluyendo históricos/backups. | REUSE-FIRST / AUDIT_REQUIRED | Resolver tablas RBAC activas y aplicar permisos backend; no crear RBAC paralelo. |
| Estado operativo de conexión/sync | `Servidores_Conexiones` y `Sistema_Sync_Catalogo` contienen flags/status operativos parciales, pero no debe confundirse configuración con heartbeat real. | EXTEND / REUSE | Definir estado derivado de evidencia de ejecución/health; evitar hardcode o status stale. |
| Mongo | Existen rastros/documentación legacy en repo. | DO_NOT_TOUCH as source; REMOVE_DEPENDENCY progressively | No usar Mongo como fuente/cache para este frente. |
| Toast | No existe justificación para robot Toast dedicado. Las estructuras de sistema/version/mapeo/capacidad/sync ya son reutilizables. | REUSE UNIVERSAL ARCHITECTURE | Toast será provider/layout/configuración del motor universal, no un subsistema paralelo. |
| NetPay | Existe implementación/patrón previo. | REFERENCE_ONLY | Reutilizar patrones generalizables; no copiar el robot como nuevo robot Toast. |

## Gaps reales que sobreviven Gate 2
1. Resolver de forma inequívoca la entidad canónica de unidad que debe portar `timezone_iana`, locale/idioma y moneda operativa, reutilizando catálogos actuales.
2. Auditar si ya existe una relación semántica capacidades ↔ sync bajo otro nombre. Solo si no existe, diseñar relación mínima.
3. Auditar el modelo canónico existente de ejecuciones/evidencia/idempotencia entre los 23 candidatos antes de crear objetos.
4. Auditar RBAC activo y permisos exactos de administrar conexiones/secretos/syncs.
5. Auditar fuente FX canónica entre objetos existentes; prohibido crear otra hasta resolverla.
6. Preflight específico para IDs externos: el barrido por nombre dio 0 objetos explícitos, pero debe descartarse equivalente semántico antes de CREATE.
7. Separar configuración (`activo`, Handler, etc.) de health real derivado de ejecuciones, para que el status de servidor no quede stale.

## DDL permitido después de este Gate
Ninguno automáticamente. El siguiente gate debe ser un `READ_ONLY_SQL preflight` de los seis gaps anteriores. Solo después podrá generarse DDL mínimo, idempotente y sin duplicación.

## Certificación Gate 2
Gate 2 queda documentalmente cerrado cuando este dossier se integra sin cambios fuera de `docs/SERVIDORES/SERVIDORES_INTEGRACIONES_GATE2_SQL_REPO_DOSSIER.md`, con validación `git_diff_check`, Production=false y sin DDL/DML.
