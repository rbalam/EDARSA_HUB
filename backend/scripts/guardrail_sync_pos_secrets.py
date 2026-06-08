#!/usr/bin/env python3
"""
Guardrail de secretos / hardcodes en el job de Sync POS (P1B).

Falla (exit 1) si detecta en el archivo del job:
- Hosts DDNS hardcodeados (*.ddns.net)
- Variables *_DB_PASS
- Usuario 'sa' literal
- IP/host SQL hardcodeado
- UNIDADES_CONFIG operativo (solo se permite como dict vacío deprecado)

No imprime secretos.
"""
import re
import sys
from pathlib import Path

JOB = Path(sys.argv[1] if len(sys.argv) > 1
           else "/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py")

text = JOB.read_text(encoding="utf-8", errors="ignore")
violations = []

checks = [
    ("DDNS hardcodeado", r"[A-Za-z0-9_.-]+\.ddns\.net"),
    ("DB_PASS POS", r"[A-Z0-9]+_DB_PASS"),
    ("usuario 'sa' literal", r"""["']sa["']"""),
    ("IP SQL hardcodeada", r"54\.39\.104\.176"),
]
for label, rx in checks:
    if re.search(rx, text, flags=re.I):
        violations.append(label)

if "UNIDADES_CONFIG" in text:
    if "UNIDADES_CONFIG = {}" not in text or "DEPRECATED" not in text:
        violations.append("UNIDADES_CONFIG operativo (debe estar deprecado como dict vacío)")

if violations:
    print("GUARDRAIL FALLÓ - violaciones detectadas:")
    for v in violations:
        print(" -", v)
    sys.exit(1)

print("GUARDRAIL OK: sin hardcodes POS críticos en el job.")
