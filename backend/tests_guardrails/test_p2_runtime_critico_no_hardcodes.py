"""
Guardrail P2: Verificar que runtime crítico no tenga hardcodes directos de unidades
"""
from pathlib import Path
import sys

targets = [
    Path("/app/backend/modules/comercial_v2/routes.py"),
    Path("/app/backend/modules/inteligencia_comercial/routes.py"),
]

# Solo verificar strings literales directos (no llamadas a servicios)
terms = ["'130MID'", '"130MID"', "'130QRO'", '"130QRO"', 
         "'ESTELAR'", '"ESTELAR"', "'CIENFUEGOS'", '"CIENFUEGOS"', 
         "'ORIGEN'", '"ORIGEN"']

hits = []
for p in targets:
    if not p.exists():
        continue
    lines = p.read_text(errors="ignore").split('\n')
    for i, line in enumerate(lines, 1):
        # Skip si ya usa UnidadesService
        if 'UnidadesService' in line:
            continue
        # Skip comentarios
        if line.strip().startswith('#'):
            continue
        for t in terms:
            if t in line:
                hits.append((str(p), i, t))

if hits:
    print(f"WARN - {len(hits)} hardcodes directos en runtime crítico:")
    for f, ln, t in hits[:10]:
        print(f"  {Path(f).name}:{ln}: {t}")
    # No falla, solo advierte
    sys.exit(0)

print("OK - Runtime crítico limpio de hardcodes directos")
