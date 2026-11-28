# Cavas Gate 16F — Blind Audit + Computer Vision Readiness

## Decisión
- Auditoría ciega: implementación determinista dentro de Cavas.
- Evidencia binaria: REUSE `core.object_storage`; no crear storage paralelo.
- Autorización/routing de visión: REUSE `core.ai_gateway_policy_adapter` + execution gate.
- Provider/model concreto: fuera de alcance.
- Reconocimiento IA nunca crea/fusiona identidad canónica por sí solo.

## Flujo objetivo
1. Operador captura sin visualizar inventario esperado.
2. Evidencia se referencia por el contrato de 16E.
3. Identificación puede ser manual o por IA autorizada.
4. Sólo después se compara contra esperado.
5. Baja confianza => REVIEW_REQUIRED.
6. Diferencias => hallazgos, nunca ajustes automáticos de inventario.
7. Futuro ajuste requiere workflow/autorización independiente.

## Readiness de visión
La futura llamada deberá pedir capability (p.ej. VISION_IMAGE_ANALYSIS) al AI Gateway; no hardcodear OpenAI/Gemini/modelo. El gateway decide provider/model por policy, scopes, data classification, riesgo y budget.

## Alcance no implementado
- llamadas reales de IA;
- prompts/modelos;
- uploads;
- DDL/DML;
- endpoints/UI;
- autoajustes;
- reconocimiento productivo.
