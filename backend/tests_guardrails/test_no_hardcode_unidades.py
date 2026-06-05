from pathlib import Path
import sys

FORBIDDEN = [
    "130MID",
    "130QRO",
    "130° MERIDA",
    "130° QUERETARO",
    "LA ESTELAR",
    "CIENFUEGOS",
    "ORIGEN",
    "ESTELAR",
]

ALLOWLIST = [
    "tests_guardrails/test_no_hardcode_unidades.py",
    "reporte_hardcodes_criticos.txt",
    "auditoria_unidades_hardcodeadas.txt",
]

hits = []

for root in [Path("/app/backend"), Path("/app/frontend/src")]:
    if not root.exists():
        continue

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        sp = str(p)

        if any(x in sp for x in ["venv", "__pycache__", ".git", "node_modules"]):
            continue

        if any(a in sp for a in ALLOWLIST):
            continue

        if p.suffix not in [".py", ".js", ".jsx", ".ts", ".tsx"]:
            continue

        txt = p.read_text(errors="ignore")

        for term in FORBIDDEN:
            if term in txt:
                hits.append((sp, term))

if hits:
    print("FAIL - hardcodes de unidades encontrados:")
    for f, t in hits[:300]:
        print(f"{f}: {t}")
    sys.exit(1)

print("OK - sin hardcodes de unidades")
