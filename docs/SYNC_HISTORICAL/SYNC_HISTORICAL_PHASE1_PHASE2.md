# Sincronizacion Historica de Tablas - Fases 1 y 2

Estado: IMPLEMENTACION DE CONTRATO EN DESARROLLO  
Rama canonica: `Edarsahub_Desarrollo`  
Fuente funcional atomica: **Prompt Maestro de Implementacion - Sincronizacion Historica de Tablas**.

## 1. Regla de arquitectura

Este modulo no crea una segunda fuente de verdad. Se aplica la secuencia:

`REUTILIZAR -> EXTENDER -> COMPONER -> CREAR SOLO SI FALTA`.

No se crea otro Worker, otro catalogo de sistemas, otro catalogo de unidades ni un ledger paralelo.

## 2. Mapa canonico de fuentes de verdad

| Concepto | Fuente canonica reutilizada | Decision |
|---|---|---|
| Sistemas | `dbo.Sistema_Tipos` | REUSE |
| Variantes de nombre | `dbo.Sistema_TiposVariantes` | REUSE |
| Capacidades por sistema | `dbo.Sistema_Capacidades` | REUSE |
| Tipos de sincronizacion | `dbo.Sistema_Sync_Catalogo` | REUSE + EXTEND minimo |
| Compatibilidad sync <-> capacidad | `dbo.Sistema_Sync_Capacidades` | REUSE |
| Unidades de negocio | `dbo.Unidades_Negocio` | REUSE |
| Sucursal fisica | `dbo.Sistema_Sucursales` | REUSE cuando corresponda |
| Servidor / conexion / API | `dbo.Servidores_Conexiones` | REUSE |
| Estado de conexion | `dbo.Servidores_ConexionEstado` | REUSE |
| Version de sistema | `dbo.Sistema_VersionesSistemas` | REUSE |
| Ledger de ejecuciones | `dbo.Sync_Control_Ejecuciones` | REUSE |
| Evidencia por ejecucion | `dbo.Sync_Control_Evidencias` | REUSE |
| Ejecutor | WORKER UNIVERSAL V1.2 | REUSE exclusivo |

Relacion operativa ya establecida:

`Unidades_Negocio.server_id -> Servidores_Conexiones.id`.

La compatibilidad entre un tipo de sincronizacion y un sistema no se infiere por nombre. Se declara por la cadena:

`Sistema_Sync_Catalogo -> Sistema_Sync_Capacidades -> Sistema_Capacidades -> Sistema_Tipos`.

## 3. Equivalencias ya existentes en Sistema_Sync_Catalogo

El contrato del PDF pide metadata transversal. Antes de agregar columnas se reutilizan equivalentes:

| Contrato historico | Campo existente |
|---|---|
| capability/table key | `Codigo` |
| display_name | `Nombre` |
| category_name | `Grupo` |
| handler | `Handler` |
| destination table | `TablaDestino` |
| supports_historical | `PermiteResync` |
| dependencies | `Dependencias` |
| execution_order | `Orden` |
| enabled | `Activo` |

## 4. Extension minima autorizada para Fase 2

Solo se agregan conceptos sin equivalente canonico:

- `CategoriaCodigo`
- `EntidadCodigo`
- `CampoFecha`
- `ClaveNegocio` (JSON)
- `SoportaIncremental`
- `SoportaFullSync`
- `SoportaResume`
- `SoportaSafeStop`
- `VersionContrato`
- `MetadataJSON` (JSON)

Todos los flags nuevos nacen en **0**. No se habilitan capacidades por inferencia.

## 5. Regla fail-closed del registry

Una combinacion no es elegible para sincronizacion historica si falta cualquiera de estos elementos obligatorios:

- catalogo activo;
- `PermiteResync=1`;
- handler implementado;
- category key;
- entity key;
- campo de fecha cuando el tipo requiere rango;
- business key para idempotencia;
- vinculo explicito en `Sistema_Sync_Capacidades`;
- sistema y capacidad de sistema activos;
- vinculo activo.

Esto evita mostrar o ejecutar combinaciones inventadas.

## 6. No se hace seed de compatibilidades

La migracion **no** crea automaticamente filas en `Sistema_Sync_Capacidades` ni completa business keys.

Motivo: las equivalencias entre `CodigoSync`, sistema, tabla de origen, PK/business key y handler deben estar sustentadas por evidencia real. La politica universal indica **NUNCA ADIVINAR**.

Los vinculos se registraran explicitamente mediante el servicio canonico cuando cada capability sea certificada.

## 7. Protecciones

- `sync_comercial_abiertas_v2` no se modifica.
- Produccion no se modifica.
- No se exponen secretos.
- No se crea conexion del navegador a POS.
- No se agrega frontend en Fases 1-2.
- No se crea otro Worker.
- No se crea catalogo paralelo.

## 8. Archivos de contrato

- Migracion: `backend/database/migrations/20261009_001_sync_historical_capability_registry.sql`
- Validacion: `backend/database/validation/20261009_001_sync_historical_capability_registry_validation.sql`
- Rollback: `backend/database/rollback/20261009_001_sync_historical_capability_registry_rollback.sql`
- Servicio: `backend/modules/sistema/sync_catalogo_service.py`
- Tests: `backend/tests/test_sync_historical_capability_registry_contract.py`

## 9. Siguiente fase

Fase 3 debe crear el planner/orquestador usando este registry:

`Job padre -> Sistema -> Sucursal -> Capability -> Bloque temporal`.

El planner no debe ejecutar trabajo en la peticion HTTP. Debe producir unidades atomicas persistentes y entregables al WORKER UNIVERSAL V1.2.
