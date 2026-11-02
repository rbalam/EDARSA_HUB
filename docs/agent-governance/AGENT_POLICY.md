# EDARSAHUB - Universal AI Agent Policy

Aplica a Copilot, Codex/ChatGPT, Claude, Gemini, Antigravity, Kimi, Grok y agentes futuros.

## Reglas obligatorias

1. NUNCA ADIVINAR.
2. AUDITAR antes de crear o modificar.
3. REUTILIZAR > EXTENDER > COMPONER > CREAR.
4. SQL EDARSAHUB es la fuente canónica.
5. MongoDB runtime/fallback/cache/config/fuente paralela está prohibido.
6. No hardcodes funcionales.
7. Backend authoritative para permisos y reglas críticas.
8. RBAC debe considerar usuario, rol, permiso y contexto empresa/unidad/sucursal.
9. Una sola fuente de verdad por concepto.
10. No duplicar estados, workflows, catálogos o fuentes.
11. Evitar crecer backend/core; preferir dominio propietario.
12. Fail-closed ante identidad, permiso, contexto o configuración inválidos.
13. No crear tablas, columnas, roles, permisos, acciones, jobs o endpoints sin auditar si ya existen.
14. No usar conexiones LIVE salvo excepción explícitamente documentada.
15. No mocks productivos.

## SQL de auditoría

Único login read-only permitido: HRLectura.

Antes de consultas de negocio validar:

DB_NAME() = EDARSAHUB
SUSER_SNAME() = HRLectura
USER_NAME() = HRLectura

Si no coincide: ABORTAR.

Nunca usar otro login para auditoría read-only.

## Secretos

Nunca mostrar passwords, tokens, API keys, secretos o cadenas completas de conexión.

Nunca ejecutar:

source backend/.env

## Git

Rama de trabajo: Edarsahub_Desarrollo.

Workspace compartido.

Prohibido:
- git reset --hard
- git clean
- stash global
- checkout/restore destructivo de cambios ajenos

Antes de modificar:
- git branch --show-current
- git rev-parse HEAD
- git status --short

## Flujo obligatorio

AUDITORIA
-> DIAGNOSTICO
-> PLAN
-> IMPLEMENTACION
-> VALIDACION
-> CHECKPOINT

No aplicar patches a ciegas.

## Continuidad

La memoria NO vive en la conversación del agente.

Todo agente debe leer:

- AGENTS.md
- docs/agent-governance/AGENT_POLICY.md
- docs/agent-governance/checkpoints/CURRENT.md
- docs/agent-governance/decisions/ACTIVE_DECISIONS.md
- docs/agent-governance/lessons/ARCHITECTURAL_FAILURES_AND_LESSONS.md
- documentos EKS aplicables
- memory/PRD.md

Despues de una desconexion:
leer CURRENT.md y continuar exclusivamente desde NEXT, salvo la excepcion unica EDARSAHUB_MCP_RECOVERY registrada abajo.

Excepcion EDARSAHUB_MCP_RECOVERY (unica y de alcance limitado):
- Solo se activa cuando ACTIVE_DECISIONS.md registra la aprobacion humana y existe docs/agent-governance/checkpoints/MCP_UNIVERSAL_WORKER.md con WORKSTREAM=EDARSAHUB_MCP_RECOVERY.
- CURRENT.md y el NEXT de CxP se leen y preservan sin cambios. Para esta excepcion, continuar exclusivamente desde el NEXT del checkpoint MCP.
- Alcance: auditoria READ_ONLY y preparacion de gobernanza mediante el Universal Worker existente.
- No autoriza implementacion MCP, publicacion de JOB MCP tecnico, activar EDARSAHUB_MCP_INPROCESS=1 ni cambios en Produccion.
- CxP permanece pausado durante el trabajo MCP. No hay ejecucion paralela y se permite un solo writer.
- Si falta aprobacion, existe duplicado/conflicto o el contexto no coincide, detenerse sin modificar archivos.

No repetir DO_NOT_REPEAT salvo evidencia nueva.
