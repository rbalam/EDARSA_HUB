"""
Guardrail P1: No conexiones Live en módulos de visualización activos
Excluye: sync jobs, cargas históricas, scripts de migración, backups
"""
from pathlib import Path
import sys

ROOTS = [
    Path("/app/backend/modules/comercial_v2"),
    Path("/app/backend/modules/admin_sql"),
]

# Términos que indican conexión Live a sucursales
TERMS = ["10.0.0", "ddns", "serverestelar"]

# Archivos/patterns permitidos (sync jobs, cargas, etc.)
ALLOW = [
    "sync", "job", "scheduler", "legacy", "bak_",
    "carga_historica", "migration", "backfill", "seed"
]

hits = []
for root in ROOTS:
    if not root.exists():
        continue
    for p in root.rglob("*.py"):
        sp = str(p)
        fname = p.name.lower()
        # Excluir archivos permitidos
        if any(a.lower() in fname or a.lower() in sp.lower() for a in ALLOW):
            continue
        txt = p.read_text(errors="ignore").lower()
        for t in TERMS:
            if t.lower() in txt:
                hits.append((sp, t))

if hits:
    print("FAIL - Posible live en módulos activos:")
    for f,t in hits:
        print(f"  {f}: {t}")
    sys.exit(1)

print("OK - Sin live visual sospechoso en módulos activos (routes.py)")
