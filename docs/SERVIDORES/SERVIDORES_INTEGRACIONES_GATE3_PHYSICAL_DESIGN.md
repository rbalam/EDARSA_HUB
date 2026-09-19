# GATE 3 — Diseño físico exacto, sin ejecutar DDL

## Certificación de entrada
- Gate 2: `CERTIFIED / COMPLETE / 100%`.
- Gate 3A: `READ_ONLY_COMPLETE / CERTIFIED_READ_ONLY / 100% / PASS`.
- Gate 3A: `files_changed=[]`, `production_touched=false`, sin blockers.

## Principio
Este documento define el diseño físico objetivo. **No ejecuta ni autoriza automáticamente DDL/DML.** Gate 4 deberá convertir únicamente las piezas aprobadas en migraciones idempotentes con preflight SQL específico.

## 1. Unidad, timezone, locale y moneda

### Evidencia
Gate 3A confirmó como entidades reales `dbo.Unidades_Negocio` y `dbo.Sistema_UnidadesNegocioPerfilDigital`. `Sistema_UnidadesNegocioPerfilDigital` ya porta `Pais` y `Moneda`; `Sistema_TurnosOperativosUnidad` referencia unidad por código operativo. El núcleo económico existente `Economia_ContextoOperativo` usa `UnidadNegocioID uniqueidentifier` con FK a `dbo.Unidades_Negocio(id)` y `MonedaID` hacia `Proveedor_Monedas`. No se encontró una columna IANA/locale canónica en la unidad.

### Diseño
- `dbo.Unidades_Negocio` = **entidad canónica de unidad**. No crear otra tabla de unidades.
- `dbo.Sistema_UnidadesNegocioPerfilDigital` = metadata comercial/digital; conservar `Pais`/`Moneda` actual por compatibilidad, pero no convertirla en fuente FX.
- `dbo.Economia_ContextoOperativo` = fuente relacional para país/moneda económica por unidad cuando aplique vigencia.
- EXTEND candidato sobre `dbo.Unidades_Negocio`:
  - `timezone_iana nvarchar(100) NULL` — identificador IANA, por ejemplo `America/Merida`, nunca offset fijo.
  - `locale_operativo nvarchar(20) NULL` — por ejemplo `es-MX`, `en-US`.
- No duplicar moneda como una nueva columna textual: usar `Economia_ContextoOperativo.MonedaID` / `Proveedor_Monedas`; mantener campos legacy únicamente como compatibilidad.
- `Sistema_TurnosOperativosUnidad` conserva horarios; el cálculo de fecha operativa deberá resolver primero unidad -> `timezone_iana` y después interpretar el turno local.

## 2. Capacidades ↔ sincronizaciones

### Evidencia
Existen `Sistema_Capacidades` y `Sistema_Sync_Catalogo`, pero Gate 3A no certificó una FK/relación puente directa entre ambos. Los objetos `Sistema_SyncPOS_*` son implementación POS específica y no sustituyen la relación canónica.

### Diseño CREATE_CANDIDATE
Nombre propuesto siguiendo familia existente: `dbo.Sistema_Sync_Capacidades`.

Contrato físico:
- `SyncCapacidadID bigint IDENTITY(1,1) NOT NULL` PK.
- `CodigoSync` con **exactamente el mismo tipo/longitud** de `Sistema_Sync_Catalogo.Codigo`; FK a `Sistema_Sync_Catalogo(Codigo)`.
- `SistemaCapacidadID int NOT NULL`; FK a `Sistema_Capacidades(SistemaCapacidadID)`.
- `Obligatoria bit NOT NULL DEFAULT 1`.
- `Activo bit NOT NULL DEFAULT 1`.
- `FechaAlta datetime2(3) NOT NULL DEFAULT SYSUTCDATETIME()`.
- `FechaModificacion datetime2(3) NULL`.
- UNIQUE `(CodigoSync, SistemaCapacidadID)`.

No crear catálogos nuevos de sync/capacidades.

## 3. Ejecuciones, evidencia e idempotencia

### Evidencia
Gate 3A encontró múltiples objetos existentes. `dbo.Sync_Control_Ejecuciones` ya contiene `SyncRunID`, `SyncType`, `ServerID`, `EmpresaID`, rango, dry-run, contadores, `Status`, error, timestamps y duración. También existen `Sistema_Sync_ResyncLog`, `Sistema_SyncPOS_Bitacora`, `Sistema_SyncPOS_EstadoUnidad`, `Sync_Logs`.

### Diseño
`dbo.Sync_Control_Ejecuciones` = **ledger canónico de ejecución** a extender, no crear otra tabla de runs.

EXTEND candidatos mínimos:
- `ConexionID uniqueidentifier NULL` FK a `Servidores_Conexiones(id)`.
- `UnidadNegocioID uniqueidentifier NULL` FK a `Unidades_Negocio(id)`.
- `CodigoSync` del mismo tipo que `Sistema_Sync_Catalogo.Codigo`, FK a catálogo.
- `StartedAtUTC datetime2(3) NULL`.
- `FinishedAtUTC datetime2(3) NULL`.
- `IdempotencyKey nvarchar(200) NULL`, índice UNIQUE filtrado para valores no nulos.

CREATE_CANDIDATE hijo para evidencia, porque no debe inflarse el ledger con archivos/payloads:
`dbo.Sync_Control_Evidencias`
- `EvidenciaID bigint IDENTITY(1,1)` PK.
- `SyncControlID int NOT NULL` FK a `Sync_Control_Ejecuciones(SyncControlID)`.
- `TipoEvidencia nvarchar(50) NOT NULL` (`FILE`, `API_PAYLOAD`, `PORTAL_EXPORT`, `AUDIT`).
- `HashSHA256 char(64) NOT NULL`.
- `Referencia nvarchar(1000) NULL` — ubicación interna/controlada, nunca secreto.
- `NombreOriginal nvarchar(500) NULL`.
- `MimeType nvarchar(150) NULL`.
- `Bytes bigint NULL`.
- `FechaCapturaUTC datetime2(3) NOT NULL DEFAULT SYSUTCDATETIME()`.
- UNIQUE `(SyncControlID, HashSHA256)`.

`Sistema_SyncPOS_*` permanece como implementación especializada/legacy; el motor universal debe converger gradualmente al ledger genérico.

## 4. RBAC

### Evidencia
Gate 3A confirmó familia activa `Sistema_RBAC_Permisos`, `Sistema_RBAC_Roles`, `Sistema_RBAC_RolesPermisos`, además de `Sistema_RBAC_PerfilCatalogo`.

### Diseño
REUSE únicamente. **No crear tablas RBAC.** Gate 4 podrá sembrar permisos como filas idempotentes en `Sistema_RBAC_Permisos` y relaciones en `Sistema_RBAC_RolesPermisos`, usando códigos aprobados después de auditar los existentes. Backend debe validar permisos; frontend solo refleja.

## 5. Moneda y FX

### Evidencia
El repo y SQL ya contienen núcleo económico: `Economia_Series` soporta `EsTipoCambio`, `MonedaBaseID`, `MonedaCotizadaID`; `Economia_Valores` conserva `FechaPeriodo`, `Valor`, versiones, fuente/hash y `SyncRunID`. La migración del núcleo declara expresamente que tablas transaccionales con `TipoCambio` **no son fuente macroeconómica FX**.

### Diseño
- `Economia_Series` con `EsTipoCambio=1` = catálogo canónico de pares/series FX.
- `Economia_Valores` = histórico canónico de tasas por fecha/version/fuente.
- `Proveedor_Monedas` = catálogo de moneda.
- `Economia_ContextoOperativo.MonedaID` = moneda operativa/base contextual por empresa/unidad con vigencia.
- **NEW_TABLES_FOR_FX=0**.
- Conversión histórica: seleccionar serie base/cotizada + valor de `FechaPeriodo` correspondiente a la fecha del dato; no usar tasa actual para historia salvo solicitud explícita.

## 6. Identificadores externos

### Evidencia
Gate 3A encontró 28 columnas externas dispersas, pero no certificó una estructura genérica transversal. Por tanto no deben seguir agregándose `ToastLocationId`, `NetPayId`, etc. a tablas arbitrarias.

### Diseño CREATE_CANDIDATE
`dbo.Sistema_IdentificadoresExternos`
- `IdentificadorExternoID bigint IDENTITY(1,1) NOT NULL` PK.
- `UnidadNegocioID uniqueidentifier NULL` FK a `Unidades_Negocio(id)`.
- `SistemaTipoID int NOT NULL` FK a `Sistema_Tipos(SistemaTipoID)`.
- `SistemaVersionID uniqueidentifier NULL` FK a `Sistema_VersionesSistemas(sistema_version_id)`.
- `ConexionID uniqueidentifier NULL` FK a `Servidores_Conexiones(id)`.
- `TipoIdentificador nvarchar(80) NOT NULL` — ejemplo `LOCATION`, `MERCHANT`, `STORE`; dato, no proveedor hardcodeado.
- `ValorExterno nvarchar(300) NOT NULL`.
- `Activo bit NOT NULL DEFAULT 1`.
- `FechaAlta datetime2(3) NOT NULL DEFAULT SYSUTCDATETIME()`.
- `FechaModificacion datetime2(3) NULL`.
- CHECK: al menos `UnidadNegocioID` o `ConexionID` no nulo.
- UNIQUE `(SistemaTipoID, TipoIdentificador, ValorExterno)`.
- Índice por `(UnidadNegocioID, SistemaTipoID, Activo)`.

Toast location se vincula aquí a la unidad canónica; nunca crea la unidad silenciosamente.

## 7. Health real de conexiones y sync

### Evidencia
Gate 3A confirmó objetos existentes `Servidores_ConexionEstado`, `Sistema_ServidoresConexionEstado`, `Sistema_ServidoresEstado` y `Sistema_SyncPOS_EstadoUnidad`. `Servidores_ConexionEstado` ya contiene `EstadoConexion`; `Sistema_SyncPOS_EstadoUnidad` conserva fechas y estado de última sync.

### Diseño
- `dbo.Servidores_ConexionEstado` = candidato canónico para health por conexión, por pertenecer a la misma familia de `Servidores_Conexiones`. REUSE/EXTEND; no crear `RobotConnectionHealth` ni equivalente.
- `Sistema_ServidoresConexionEstado` y `Sistema_ServidoresEstado` quedan como compatibilidad hasta auditar consumidores; Gate 4 no los elimina.
- EXTEND mínimo en `Servidores_ConexionEstado` solo si columnas no existen en preflight de migración:
  - `UltimaPruebaUTC datetime2(3) NULL`.
  - `UltimoExitoUTC datetime2(3) NULL`.
  - `UltimoErrorUTC datetime2(3) NULL`.
  - `UltimoErrorCodigo nvarchar(80) NULL`.
  - `UltimoErrorMensaje nvarchar(1000) NULL`.
  - `LatenciaMs int NULL`.
  - `UltimoSyncUTC datetime2(3) NULL`.
  - `UltimoSyncExitosoUTC datetime2(3) NULL`.
  - `FechaActualizacionUTC datetime2(3) NOT NULL DEFAULT SYSUTCDATETIME()`.
- Estado mostrado en BOS debe derivarse de health/evidencia, no únicamente de `Activo`.

## 8. Secretos y conexión
No crear tabla nueva en Gate 3. `Servidores_Conexiones` ya contiene secretos cifrados. Gate 4 debe separar API/UI de metadata y valores secretos: valor nunca se devuelve; descifrado solo en runtime; rotación y auditoría mediante RBAC. La eventual normalización a un child de secretos requiere gate propio, porque Finanzas ya tiene un patrón específico que no debe reutilizarse transversalmente a ciegas.

## 9. Motor universal / Toast
No crear `Toast_*` de dominio ni `ToastRobot`. El motor deberá resolver:
`Conexion -> Sistema/Version -> Capacidades -> Sync -> Executor -> Layout/Mapeo -> Ledger/Evidencia -> Mapper canonico`.
Toast será configuración de sistema/version/mapeos/IDs externos sobre el Browser/API Executor universal.

## Resumen físico
### REUSE
`Unidades_Negocio`, `Sistema_UnidadesNegocioPerfilDigital`, `Sistema_TurnosOperativosUnidad`, `Economia_ContextoOperativo`, `Proveedor_Monedas`, `Economia_Series`, `Economia_Valores`, `Sistema_Capacidades`, `Sistema_Sync_Catalogo`, `Sync_Control_Ejecuciones`, `Sistema_RBAC_*`, `Servidores_Conexiones`, `Servidores_ConexionEstado`, `Sistema_VersionesSistemas`, `Sistema_MapeoTablasVersion`, `Sistema_MapeoColumnasVersion`.

### EXTEND_CANDIDATE
1. `Unidades_Negocio`: `timezone_iana`, `locale_operativo`.
2. `Sync_Control_Ejecuciones`: conexión/unidad/sync/UTC/idempotencia.
3. `Servidores_ConexionEstado`: timestamps/latencia/error/sync health.

### CREATE_CANDIDATE
1. `Sistema_Sync_Capacidades` — puente catálogo sync ↔ capacidad.
2. `Sync_Control_Evidencias` — evidencia/hash por ejecución.
3. `Sistema_IdentificadoresExternos` — IDs externos universales vinculados a sistema/unidad/conexión.

### NO_CREATE
- Nuevas tablas de empresas/unidades/software/versiones/conexiones/sync/capacidades/RBAC/FX.
- Cualquier tabla `Toast_*` de negocio.
- `RobotConnection` o `ToastRobot`.

## Gate 4 permitido
Gate 4 podrá preparar migraciones idempotentes **solo** para EXTEND/CREATE_CANDIDATE anteriores, con un preflight READ_ONLY_SQL inmediatamente anterior que confirme que cada columna/tabla/índice/FK sigue ausente. No ejecutar Production.

`GATE_3_DESIGN_COMPLETE=true`
`DDL_EXECUTED=false`
`DML_EXECUTED=false`
`PRODUCTION_TOUCHED=false`
