"""Módulo Asistente IA (menú IA) - EDARSA HUB.

Chat conversacional general + insights + generación de texto usando OpenAI gpt-5.5
vía la MISMA conexión que Pricing IA (EMERGENT_LLM_KEY / LlmChat).

REGLAS:
- SQL-First: sesiones y mensajes se persisten en EDARSAHUB SQL (NO MongoDB).
- No hardcodear secretos (la key viene de EMERGENT_LLM_KEY en .env).
"""
