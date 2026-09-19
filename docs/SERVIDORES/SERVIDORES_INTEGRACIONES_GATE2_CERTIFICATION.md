# CERTIFICACIÓN FORMAL — GATE 2

## Frente
Servidores + Conexiones + Comunicaciones + Robot Universal + Toast + Internacionalización.

## Resultado
**GATE_2 = CERTIFIED / COMPLETE / 100%**

## Evidencia vinculada
- Gate 1: `servers-integrations-gate1-readonly-sql-r3-20260908` → `READ_ONLY_COMPLETE / CERTIFIED_READ_ONLY / 100%`.
- Gate 2A: `servers-integrations-gate2a-gap-sql-readonly-20260908` → `READ_ONLY_COMPLETE / CERTIFIED_READ_ONLY / 100% / PASS`, sin cambios de archivos ni Producción.
- Gate 2B: `servers-integrations-gate2b-sql-repo-dossier-20260908` → `INTEGRATED / quality_gate=PASS / tests=PASS / blockers=[] / production_touched=false`.
- Dossier integrado: `docs/SERVIDORES/SERVIDORES_INTEGRACIONES_GATE2_SQL_REPO_DOSSIER.md`.
- SHA del commit del dossier: `1ec68762a4e3c1ea923c4206435292b512b3afa7`.
- El commit `1ec68762...` modificó exclusivamente el dossier anterior.
- SHA convergido verificado de `Edarsahub_Desarrollo` y `mirror/emergent-live`: `65fe54fb91d7a05efb6f1280378e613dbdb67d6f`.
- `1ec68762...` es ancestro de `65fe54fb...`.
- El delta `1ec68762... -> 65fe54fb...` no modifica `docs/SERVIDORES/SERVIDORES_INTEGRACIONES_GATE2_SQL_REPO_DOSSIER.md`.

## Decisión de arquitectura certificada
Gate 2 confirma REUSE-FIRST. No se autoriza crear catálogos paralelos de empresas, unidades, sistemas, versiones, conexiones, capacidades o sincronizaciones. `Servidores_Conexiones`, `Sistema_Tipos`, `Sistema_TiposVariantes`, `Sistema_Capacidades`, `Sistema_VersionesSistemas`, `Sistema_MapeoTablasVersion`, `Sistema_MapeoColumnasVersion`, `Sistema_Sync_Catalogo` y `Sistema_TurnosOperativosUnidad` deben reutilizarse/extenderse según el dossier. Toast debe incorporarse como configuración/homologación sobre infraestructura universal, no como robot específico.

## Gaps autorizados para Gate 3
1. Entidad canónica de unidad para timezone IANA, locale/idioma y moneda operativa.
2. Relación capacidades ↔ sync, solo si preflight confirma ausencia semántica.
3. Modelo canónico de ejecuciones/evidencia/idempotencia entre candidatos existentes.
4. RBAC activo para conexiones/secretos/syncs.
5. Fuente FX canónica existente.
6. IDs externos genéricos, solo si preflight confirma ausencia de equivalente.
7. Health real de conexiones separado de flags de configuración.

## Restricciones posteriores
- `DDL=NO` como consecuencia automática de Gate 2.
- `DML=NO`.
- `PRODUCTION=NO`.
- El siguiente paso es Gate 3 de preflight/diseño físico exacto.
- Antes de cualquier CREATE/ALTER debe existir evidencia READ_ONLY_SQL específica del gap.

## Certificación
`CERTIFICATION_BASIS = GATE2A_CERTIFIED_READ_ONLY + GATE2B_INTEGRATED_PASS + SINGLE_FILE_SCOPE_VERIFIED + SHA_DESCENDANT_CONVERGENCE + DOSSIER_UNCHANGED`

`GATE_2_CERTIFIED=true`
`GATE_2_PERCENT_COMPLETE=100`
`PRODUCTION_TOUCHED=false`
