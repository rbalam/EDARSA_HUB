# AH6 - Security + Red Team V1

AH6 no crea nuevos privilegios ni otro motor de policy. Ataca los limites certificados de AH2-AH5 y registra resultados mediante `edarsahub.bos-redteam-report.v1`.

## Casos negativos obligatorios
- capability escalation
- cross-scope
- risk escalation hasta R4
- data-classification mismatch
- executor mismatch
- agent DRAFT / skill BLOCKED
- shell y command injection
- intento de override de repo/rama/Production
- alteracion de harness_context
- replay con job_id diferente
- resultado no terminal
- production_touched=true

## Principio
PASS significa que el ataque fue rechazado por el guard esperado. Cualquier bypass o comportamiento ambiguo produce FAIL. El reporte es evidencia; no sustituye RBAC, Agent Capability Policy, Procedure Policy, Execution Gate ni Universal Worker.

## Maximas
Sin archivos nuevos en backend/core, sin SQL/Mongo, sin red ni secretos reales, sin ejecucion externa y sin tocar Produccion.

## Siguiente gate
AH7 Marketing + CX integra capacidades de marketing como consumidores gobernados del Agent Harness, reutilizando Cliente/CRM/RRR y Communications canonicos en lugar de duplicarlos.
