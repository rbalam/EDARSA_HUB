from pathlib import Path
import sys
import re

ROOT = Path("/app/backend")

ALLOW = [
    "core/sql_first/db.py",
    "core/sql_first/connection_factory.py",
    "scripts/",
    "tests/",
    "tests_guardrails/",
    "auditorias_",
    "venv",
    "__pycache__",
    ".git",
]

# Patrones de llamada real (no strings)
CALL_PATTERNS = [
    r'[^"\']\bpyodbc\.connect\s*\(',
    r'[^"\']\bpymssql\.connect\s*\(',
    r'[^"\']\bcreate_engine\s*\(',
]

hits = []

for p in ROOT.rglob("*.py"):
    sp = str(p).replace("/app/backend/", "")

    if any(a in str(p) for a in ALLOW):
        continue

    txt = p.read_text(errors="ignore")
    
    # Verificar si hay llamadas reales (no strings de configuración)
    for pattern in CALL_PATTERNS:
        if re.search(pattern, txt):
            # Verificar que no sea solo un string de configuración
            lines = txt.split('\n')
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    # Si está dentro de comillas como valor de lista/dict, ignorar
                    if '"pyodbc.connect' in line or '"pymssql.connect' in line or '"create_engine' in line:
                        continue
                    if "'pyodbc.connect" in line or "'pymssql.connect" in line or "'create_engine" in line:
                        continue
                    hits.append(f"{sp}:{i}")

if hits:
    print("FAIL conexiones SQL directas fuera de core/sql_first:")
    for h in hits:
        print(h)
    sys.exit(1)

print("PASS: 0 conexiones SQL directas en runtime")
