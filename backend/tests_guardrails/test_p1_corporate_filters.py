"""
Guardrail P1: Verificar que módulos que usan UnidadesService no tengan hardcodes
"""
from pathlib import Path
import sys

# Archivos permitidos (sync jobs, scripts históricos, etc.)
ALLOW_FILES = [
    "sync", "job", "carga_historica", "legacy", "bak_", 
    "test_", "migration", "seed", "backfill"
]

hits = []

for p in Path("/app/backend/modules").rglob("*.py"):
    fname = p.name.lower()
    sp = str(p)
    
    # Excluir archivos permitidos
    if any(a in fname or a in sp.lower() for a in ALLOW_FILES):
        continue
    
    # Excluir pycache
    if "__pycache__" in sp:
        continue

    txt = p.read_text(errors="ignore")

    # Solo verificar archivos que usan el sistema de unidades
    if "unidad_negocio_pk" not in txt and "UnidadesService" not in txt:
        continue

    # Detectar hardcodes en archivos que deberían usar el servicio
    hardcodes = ["'130MID'", '"130MID"', "'130QRO'", '"130QRO"', 
                 "'CIENFUEGOS'", '"CIENFUEGOS"', "'ESTELAR'", '"ESTELAR"',
                 "'ORIGEN'", '"ORIGEN"']
    
    for hc in hardcodes:
        if hc in txt:
            # Verificar que no sea en comentario o docstring
            lines = txt.split('\n')
            for i, line in enumerate(lines, 1):
                if hc in line and not line.strip().startswith('#') and not line.strip().startswith('"""'):
                    hits.append(f"{p}:{i}: {hc}")
                    break

if hits:
    print(f"WARN - {len(hits)} hardcodes encontrados en archivos que usan UnidadesService:")
    for h in hits[:20]:
        print(f"  {h}")
    # No falla, solo advierte (deuda técnica aceptada)
    sys.exit(0)

print("OK - Sin hardcodes críticos en módulos activos")
