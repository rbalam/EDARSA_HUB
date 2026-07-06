# EDARSAHUB V1.0 — instrucciones globales para GitHub Copilot / VS Code

Usar `AGENTS.md` como contrato principal del repositorio.

Prioridad operativa:
1. Antigravity
2. Codex
3. GitHub Copilot / VS Code
4. Claude minimizado

Agentes Copilot disponibles:
- EDARSA Copilot Supervisor: coordina, no edita.
- EDARSA Auditor: audita, no edita.
- EDARSA Coder: implementa cambios minimos.
- EDARSA Validator: valida y bloquea.

No crear `.claude/agents` excepto `.claude/agents/edarsa-claude-haiku-auditor.md`, permitido solo como auditor Claude Haiku de solo lectura, uso excepcional y bajo autorización explícita.

Reglas críticas:
- Rama obligatoria: `Edarsahub_Desarrollo`.
- No tocar producción.
- No push/deploy sin autorización explícita.
- No MongoDB en módulos críticos.
- No conexiones live para endpoints/tableros/reportes.
- No mocks.
- No hardcodes.
- No fuentes paralelas.
- No tocar RBAC ni debilitarlo.
- No patch sin evidencia exacta.
- DB solo `SELECT` para auditorías.
- KPI Ventas = `ventas_total` con IVA.
- Unidad de negocio: fuente `dbo.Unidades_Negocio`, llave `unidad_negocio_pk`.
