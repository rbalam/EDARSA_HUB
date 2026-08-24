# EDARSAHUB V1.0 — Agent Operating Protocol

## Arquitectura canónica multiagente

Esta sección tiene prioridad cuando una instrucción operativa antigua contradiga el flujo multiagente actual.

### Fuentes de verdad

- Código: `rbalam/EDARSA_HUB`, rama `Edarsahub_Desarrollo`.
- Evidencia y certificación: `rbalam/EDARSAHUB_AUDIT_EVIDENCE`.
- Producción: `Edarsahub_Produccion`, fuera del flujo normal de desarrollo y sólo modificable mediante autorización explícita.

`EDARSAHUB_AUDIT_EVIDENCE` NO es un repositorio paralelo de código. No se debe copiar bidireccionalmente el árbol de código entre ambos repositorios.

Flujo canónico:

`solicitud -> agente ejecutor -> Edarsahub_Desarrollo -> pruebas/verificación -> worker -> AUDIT_EVIDENCE -> resumen/certificación`

Nunca:

`AUDIT_EVIDENCE <-> copia de código <-> Edarsahub_Desarrollo`

La evidencia puede referenciar archivos, commits y SHA del código; no debe convertirse en una segunda fuente de verdad del código.

### Regla contra desviaciones

Resolver el objetivo pedido sin cambiarlo por conveniencia técnica.

No detener el trabajo sólo porque no exista acceso directo a `/app`, VS Code, terminal o runtime. Si el agente todavía puede auditar, modificar, revisar o guardar cambios de forma segura mediante GitHub u otro canal autorizado, debe continuar y dejar pendientes únicamente las comprobaciones que requieran realmente el runtime.

No confundir `no tengo acceso a /app` con `no puedo continuar`.

No inventar acceso inexistente. No declarar ejecutada una prueba que no se ejecutó. No crear una arquitectura paralela para evitar una limitación.

### Roles

Los agentes —ChatGPT, Claude, Copilot, Antigravity, Codex u otros— pueden auditar, diseñar, programar y revisar dentro de sus permisos reales.

El worker de mirror es autoridad de integración, sincronización, verificación y apoyo a la certificación; NO es la única herramienta autorizada para programar y NO debe inventar cambios funcionales sólo por observar evidencia.

La programación y la certificación final son responsabilidades separadas.

### Concurrencia

Antes de modificar un archivo, leer su versión actual. Si otro agente lo cambió, volver a leer e integrar sobre la versión vigente. No sobrescribir trabajo válido de otro agente.

Un conflicto no autoriza `force push`, reset destructivo, clean destructivo ni pérdida de trabajo.

### Criterio de terminado

`JOB != DONE` hasta que, para el alcance que corresponda, exista evidencia de:

1. cambio implementado;
2. pruebas relevantes aprobadas;
3. commit válido;
4. ese commit publicado en `Edarsahub_Desarrollo`;
5. evidencia que referencia esa misma versión;
6. Producción no tocada salvo promoción explícitamente autorizada.

Si falta una condición obligatoria, informar estado parcial o bloqueado; nunca inventar `DONE`, `CERTIFIED` o `100%`.

### Resumen humano obligatorio

Todo trabajo terminado, parcial o bloqueado debe acompañarse de un resumen en **"español", lenguaje natural**, entendible por una persona común de aproximadamente 13 años sin conocimientos de programación.

Debe explicar: qué se hizo, qué cambió y para qué sirve, qué se comprobó, si funcionó, porcentaje real, qué falta y qué sigue. Los datos técnicos pueden ir al final como referencia y nunca sustituyen la explicación humana.

## Prioridad de herramientas

Prioridad operativa:
1. Antigravity
2. Codex
3. VS Code custom agents
4. Claude minimizado

No usar `.claude/agents` como fuente principal de configuración. Excepción permitida: únicamente `.claude/agents/edarsa-claude-haiku-auditor.md` como auditor Claude Haiku de solo lectura, uso excepcional y bajo autorización explícita.

## Rama y entorno

- Trabajar desde la raíz del checkout verificado.
- En Preview puede usarse `/app`. Cuando `/app` no esté disponible, continuar por un checkout limpio o GitHub cuando el canal disponible permita realizar el trabajo de forma segura.
- Rama obligatoria: `Edarsahub_Desarrollo`.
- No trabajar directo en `Edarsahub_Produccion`.
- Antes de modificar, verificar rama, versión y estado por los medios disponibles.

## Máximas de arquitectura

- Una sola fuente de verdad por dominio.
- Auditar y reutilizar fuentes, tablas, servicios, catálogos y conectores canónicos antes de crear otros.
- No duplicar lógica de negocio.
- No usar MongoDB como fuente de negocio.
- No crear conexiones LIVE para endpoints, tableros o reportes salvo excepción expresamente autorizada.
- Frontend presenta; backend y SQL canónico determinan reglas y datos.
- RBAC siempre obligatorio.
- No hardcodes de políticas de negocio que deban ser configurables.
- No mocks, stubs ni datos falsos como comportamiento productivo.
- No ampliar el core cuando la funcionalidad pueda vivir en un módulo cohesionado.
- No tocar Producción sin autorización explícita.
- Ante incertidumbre de datos, permisos, fuente canónica o seguridad: fallar cerrado; no inventar.

## Roles operativos

### Auditor
Audita, lee código y encuentra evidencia. No modifica el sistema cuando está actuando exclusivamente como auditor.

### Coder
Implementa cambios mínimos basados en evidencia. No debilita RBAC, no crea fuentes paralelas, no usa mocks ni hardcodes y no toca Producción.

### Validator
Valida independientemente el cambio, pruebas, build, seguridad, RBAC y fuentes canónicas. Puede bloquear un cierre inseguro.

### Committer / integrador
Sólo integra cambios que hayan superado las validaciones exigidas por el alcance. Nunca usa operaciones destructivas para resolver concurrencia.

## Base de datos

Los cambios de base de datos requieren alcance y autorización adecuados. Nunca imprimir secretos ni exponer `.env`. Las auditorías deben preferir lectura. DDL/DML no autorizado queda prohibido.

## Comercial / Inteligencia / Ejecutivo

- KPI `Ventas` = `ventas_total` con IVA.
- No usar `ventas_sin_propina`, subtotal, venta neta o venta sin IVA como venta principal.
- `cheque_promedio` = `ventas_total / tickets_total` o `ventas_total / cheques_total`.
- Consumo por persona = `ventas_total / pax_total`.
- Backend calcula KPIs; frontend sólo presenta valores del backend.

## Unidad de negocio

Fuente canónica: `dbo.Unidades_Negocio`.
Servicios canónicos: `core.unidades_service.UnidadesService` y `core.corporate_filters.service.CorporateFilterService`.
Llave operativa: `unidad_negocio_pk`.

No derivar unidades desde vistas runtime, ventas, KPIs, `SELECT DISTINCT` operativo ni datos del periodo.

## Artefactos y seguridad del repositorio

Todo agente o automatización debe respetar `scripts/agent_guardrails/validate_repository_artifacts.py`.

- No `git add .`, `git add -A` ni `git add --all` en automatizaciones.
- Auditorías, dumps, traces, patches, logs y salidas reproducibles van a `/tmp` por defecto o al repositorio de evidencia cuando formen parte de una certificación válida.
- No incorporar respaldos, dumps, temporales, secretos, credenciales ni `.env`.
- Validator y automatizaciones que creen commits deben ejecutar los guardrails aplicables antes de aprobar o integrar.

## Memoria técnica obligatoria

Antes de modificar Scheduler, leer las reglas y documentos vigentes de Scheduler bajo `.agents/rules` y `docs/operacion`.

Antes de modificar Operaciones, Inventarios o Compras, leer `.agents/rules/edarsa-inventarios-compras-lessons.md` y los contratos canónicos vigentes en `docs/operacion`.

## Contexto universal antes de trabajar

Leer cuando estén disponibles:

1. `docs/agent-governance/AGENT_POLICY.md`
2. `docs/agent-governance/checkpoints/CURRENT.md`
3. `docs/agent-governance/decisions/ACTIVE_DECISIONS.md`
4. `docs/agent-governance/lessons/ARCHITECTURAL_FAILURES_AND_LESSONS.md`
5. documentos EKS aplicables
6. `memory/PRD.md`

En un checkout con herramientas locales, ejecutar los preflight/guardrails definidos por el repositorio. Si el agente opera únicamente mediante GitHub y no dispone de shell, no debe fingir haberlos ejecutado: continúa con las acciones seguras disponibles y deja esas comprobaciones para el worker/runtime.

## Regla final de autonomía

Avanzar autónomamente dentro de los permisos y herramientas reales disponibles. No pedir al usuario copiar scripts cuando exista un canal autorizado que permita realizar directamente el cambio. No detenerse por una limitación secundaria cuando exista otra ruta segura y canónica para continuar.
