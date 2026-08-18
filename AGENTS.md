# EDARSAHUB V1.0 — Agent Operating Protocol

## Prioridad de herramientas

Prioridad operativa:
1. Antigravity
2. Codex
3. VS Code custom agents
4. Claude minimizado

No usar `.claude/agents` como fuente principal de configuración. Excepción permitida: únicamente `.claude/agents/edarsa-claude-haiku-auditor.md` como auditor Claude Haiku de solo lectura, uso excepcional y bajo autorización explícita.

## Rama y entorno

- Trabajar desde la raíz del checkout verificado mediante
  `git rev-parse --show-toplevel`.
- En Preview puede usarse `/app`. Cuando `/app` no esté disponible, se permite
  un checkout limpio en el workspace, siempre que la rama sea
  `Edarsahub_Desarrollo`, el HEAD haya sido verificado y no se realicen cambios
  remotos sin autorización explícita.
- Rama obligatoria: `Edarsahub_Desarrollo`.
- No trabajar directo en `Edarsahub_Produccion`.
- No hacer push, deploy, redeploy ni cambios remotos sin autorización explícita.
- Antes de cualquier modificación:
  - `git branch --show-current`
  - `git status --short`

## Roles obligatorios

### EDARSA Auditor

Función:
- Auditar.
- Leer código.
- Leer SQL solo con `SELECT`.
- Encontrar evidencia.
- Reportar archivos y líneas exactas.

Prohibido:
- Modificar archivos.
- Crear parches.
- Ejecutar DDL/DML.
- Crear tablas, columnas, endpoints o fuentes.
- Asumir estructura sin evidencia.

Salida mínima:
- Archivos revisados.
- Líneas exactas.
- Fuente de datos detectada.
- Riesgos.
- Recomendación sin patch.
- Scripts de validación sugeridos.

### EDARSA Coder

Función:
- Implementar cambios mínimos basados en evidencia previa.
- Modificar solo archivos necesarios.
- Mantener contratos existentes salvo autorización explícita.

Prohibido:
- Tocar producción.
- Hacer push/deploy.
- Crear tablas/columnas/migraciones sin autorización.
- Tocar backups.
- Debilitar RBAC.
- Usar mocks.
- Usar hardcodes.
- Usar MongoDB en módulos críticos.
- Crear fuentes paralelas.

Salida mínima:
- Archivos modificados.
- Diff resumido.
- Validaciones ejecutadas.
- Riesgos restantes.
- No hacer commit salvo instrucción explícita.

### EDARSA Validator

Función:
- Validar de forma independiente.
- Revisar diff.
- Ejecutar pruebas/build/checks.
- Bloquear cambios inseguros.

Prohibido:
- Implementar features.
- Modificar archivos salvo autorización explícita.
- Hacer commit/push/deploy.

Salida mínima:
- Resultado: APROBADO o BLOQUEADO.
- Evidencia.
- Validaciones ejecutadas.
- Riesgos restantes.
- Recomendación: commit, corregir o revertir.

## Base de datos

Regla general:
- Agentes solo pueden auditar con `SELECT`.
- Prohibido ejecutar:
  - `DROP`
  - `TRUNCATE`
  - `ALTER`
  - `CREATE TABLE`
  - `DELETE`
  - `UPDATE`
  - `INSERT`
  - `MERGE`
  - `EXEC`
  - `sp_`
- No imprimir secretos.
- No exponer `.env`.
- No usar credenciales de escritura para agentes.

## Comercial / Inteligencia / Ejecutivo

Reglas obligatorias:
- KPI `Ventas` = `ventas_total` con IVA.
- No usar `ventas_sin_propina`, subtotal, venta neta o venta sin IVA como venta principal.
- `cheque_promedio` = `ventas_total / tickets_total` o `ventas_total / cheques_total`.
- Consumo por persona = `ventas_total / pax_total`.
- No existe KPI válido `pax_promedio = pax / tickets`.
- Backend calcula KPIs.
- Frontend solo pinta valores del backend.

## Unidad de negocio

Fuente canónica:
- `dbo.Unidades_Negocio`.

Servicio canónico:
- `core.unidades_service.UnidadesService`.
- `core.corporate_filters.service.CorporateFilterService`.

Llave operativa:
- `unidad_negocio_pk`.

Reglas:
- `codigo` es compatibilidad/display legacy.
- `nombre` es display, no llave primaria.
- No filtrar por `unidad_negocio_nombre` como llave principal.
- No derivar filtros desde vistas runtime, ventas, KPIs, `SELECT DISTINCT` operativo ni datos del periodo.
- `ORIGEN` solo puede aparecer si existe activo en `dbo.Unidades_Negocio`.

## Fuentes prohibidas para módulos críticos

- MongoDB.
- Conexiones live para endpoints/tableros/reportes de usuario.
- Mocks.
- Hardcodes.
- Fuentes paralelas.
- Tablas duplicadas.
- Columnas duplicadas.
- Backups como fuente funcional.

## Flujo obligatorio

1. Auditor produce evidencia.
2. Usuario autoriza alcance.
3. Coder aplica patch mínimo.
4. Validator valida.
5. Usuario decide commit.
6. Deploy solo con autorización explícita.

## Validaciones mínimas

Siempre que aplique:
- `git diff --check`
- `python -m py_compile` en Python modificado
- build frontend si se tocó frontend
- revisión de `git diff --stat`
- revisión de riesgos DB/RBAC/canónico

## Regla de bloqueo

Si hay duda sobre fuente canónica, permisos, RBAC, DB o producción:
- detener
- reportar evidencia
- no modificar


## GitHub Copilot / VS Code

GitHub Copilot tambien es agente operativo dentro de VS Code.

### EDARSA Copilot Supervisor

Función:
- Coordinar Auditor, Coder y Validator.
- Mantener alcance.
- Pedir evidencia.
- Bloquear acciones inseguras.

Prohibido:
- No modificar archivos.
- No hacer patch.
- No commit.
- No push.
- No deploy.
- No SQL destructivo.

Uso recomendado:
1. Copilot Supervisor recibe la solicitud.
2. Supervisor manda a Auditor si falta evidencia.
3. Supervisor manda a Coder solo si hay autorización.
4. Supervisor manda a Validator para aprobar o bloquear.

### EDARSA Committer

Committer controlado. Solo crea commits locales despues de `EDARSA Validator` con veredicto `APROBADO`.

Reglas:

- No push.
- No deploy.
- No Produccion.
- No reset.
- No checkout destructivo.
- No SQL.
- No secretos.
- Stage solo archivos aprobados.
- Commit local con mensaje convencional.

### Flujo autonomo entre agentes

Cadena por defecto:

`Supervisor -> Auditor -> Coder dry-run -> Validator pre-patch -> Coder patch -> Validator final -> Committer -> Supervisor`

Cada agente debe emitir bloque `HANDOFF` con `next_agent`, `reason` y `mode`.

<!-- EDARSAHUB_ATOMIC_WORKFLOW_START -->

## MÁXIMA DE ORO — CAMBIOS ATÓMICOS Y BASE ESTABLE

1. Trabajar sobre una rama, HEAD y workspace verificados.
2. Un bloque de trabajo corresponde a un solo objetivo funcional.
3. No mezclar dominios ni restaurar masivamente stashes, recoveries o worktrees.
4. Si existía una versión funcional, recuperarla y comparar antes de crear lógica nueva.
5. No parchar sin evidencia exacta de la causa.
6. Modificar únicamente los archivos declarados en el alcance.
7. Validar el dominio antes de ampliar el trabajo.
8. No incorporar respaldos, dumps, archivos temporales ni salidas de herramientas.
9. Commit, push, deploy y SQL requieren autorización expresa.
10. Ante una condición inesperada, detenerse y reportar; no improvisar.

Documento normativo:
`docs/operacion/MODO_TRABAJO_CAMBIOS_ATOMICOS.md`

<!-- EDARSAHUB_ATOMIC_WORKFLOW_END -->

<!-- EDARSAHUB_REPOSITORY_ARTIFACT_GUARD_START -->

## Candado canónico de artefactos del repositorio

Todo humano, agente autónomo, Copilot, Codex, Emergent, workflow o proceso
automatizado que prepare cambios para EDARSAHUB debe respetar
`scripts/agent_guardrails/validate_repository_artifacts.py`.

Reglas fail-closed:

1. Prohibido `git add .`, `git add -A` y `git add --all` en automatizaciones.
   El stage debe declarar archivos explícitos.
2. Auditorías, dumps, traces, patches, logs y salidas reproducibles deben
   generarse en `/tmp` por defecto.
3. Nuevos `.txt`, `.json`, `.patch`, `.sql`, `.log` y `.csv` en la raíz del
   repositorio están bloqueados.
4. Patrones de outputs generados como `edarsahub_*`, `v1_*`, `auditoria_*`,
   `AUDITORIA_*`, `economia_*` y `joblogger_*` no pueden incorporarse en raíz.
5. Archivo staged mayor a 5 MiB: bloqueado.
6. Archivo staged mayor a 20 MiB: bloqueo fuerte.
7. Más de 25 MiB agregados por cambio: bloqueado.
8. Más de 50 archivos nuevos por cambio: bloqueado.
9. Respaldos, dumps, outputs de herramientas y artefactos reproducibles no
   deben versionarse salvo excepción explícita, documentada y auditada.
10. Validator debe ejecutar el guard antes de aprobar.
11. Committer debe ejecutar el guard sobre el index antes de commit.
12. Automatizaciones que creen commits deben ejecutar el mismo guard después
    del stage y antes del commit.
13. Pre-commit y pre-push locales son capas adicionales; CI debe volver a
    validar porque los hooks locales pueden omitirse con `--no-verify`.
14. Una excepción nunca puede ser silenciosa ni introducir secretos,
    credenciales, `.env`, dumps de datos sensibles o archivos operativos
    protegidos.
15. NetPay y su `.vendor` existente no se modifican ni eliminan como parte de
    esta política sin una migración aislada previamente validada.

El candado debe fallar cerrado ante una condición no reconocida.

<!-- EDARSAHUB_REPOSITORY_ARTIFACT_GUARD_END -->

<!-- EDARSAHUB_SCHEDULER_LESSONS_START -->

## Scheduler — memoria técnica obligatoria

Antes de modificar Scheduler, pausa/reanudación, startup, jobs o referencias
legacy/Mongo, leer:

- `.agents/rules/edarsa-scheduler-lessons.md`
- `docs/ARQUITECTURA_SCHEDULER_PERSISTENCIA_ADMINISTRATIVA.md`
- `docs/operacion/RETROSPECTIVA_SCHEDULER_PERSISTENCIA_20260818.md`
- `docs/operacion/MONGO_REFERENCIAS_SCHEDULER_CLASIFICADAS.md`

Estas fuentes existen para impedir que se repitan auditorías ya cerradas,
falsos positivos por referencias textuales y errores de arquitectura ya
corregidos.

<!-- EDARSAHUB_SCHEDULER_LESSONS_END -->

<!-- EDARSAHUB_INVENTORY_PURCHASES_LESSONS_START -->

## Operaciones / Inventarios / Compras — memoria técnica obligatoria

Antes de modificar Operaciones, Análisis de Inventarios, inventarios físicos,
movimientos, sincronización de Compras o Auditoría Operativa de Compras, leer:

- `.agents/rules/edarsa-inventarios-compras-lessons.md`
- `docs/operacion/MEMORIA_ERRORES_CORREGIDOS_INVENTARIOS_COMPRAS_OPERACIONES.md`
- `docs/operacion/CONTRATOS_CANONICOS_INVENTARIOS_Y_AUDITORIA_COMPRAS.md`

No reabrir decisiones históricas ya clasificadas sin evidencia positiva nueva.

<!-- EDARSAHUB_INVENTORY_PURCHASES_LESSONS_END -->
