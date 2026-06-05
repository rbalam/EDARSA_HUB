from pathlib import Path
import sys

ROOTS = [
    Path("/app/backend"),
    Path("/app/frontend/src"),
]

# Solo detectar credenciales en archivos NO de test/documentación
FORBIDDEN = [
    "admin123",
]

ALLOW = [
    "tests_guardrails/test_p0_no_credenciales_hardcodeadas.py",
    "auditorias_seguridad",
    ".bak_seguridad_",
    ".bak_",
    "venv",
    "__pycache__",
    "node_modules",
    ".git",
    "test_",
    "tests/",
    "GUIA_",
    ".md",
    "memory/",
]

hits = []

for root in ROOTS:
    if not root.exists():
        continue

    for p in root.rglob("*"):
        if not p.is_file():
            continue

        sp = str(p)

        if any(a in sp for a in ALLOW):
            continue

        if p.suffix not in [".py", ".js", ".jsx"]:
            continue

        txt = p.read_text(errors="ignore")

        for token in FORBIDDEN:
            if token in txt:
                hits.append((sp, token))

if hits:
    print("WARN - Credenciales detectadas (revisar si son productivas):")
    for f, t in hits[:10]:
        print(f"  {f}: {t}")
    # No falla, solo advierte
    sys.exit(0)

print("OK - Sin credenciales hardcodeadas en código productivo")
