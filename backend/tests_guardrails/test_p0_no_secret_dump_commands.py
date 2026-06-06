from pathlib import Path
import re
import sys

ROOT = Path("/app/backend")

FORBIDDEN_PATTERNS = [
    re.compile(r"\bcat\s+\.env\b"),
    re.compile(r"\bgrep\b.*PASSWORD.*\.env", re.IGNORECASE),
    re.compile(r"\bgrep\b.*SECRET.*\.env", re.IGNORECASE),
    re.compile(r"\bgrep\b.*TOKEN.*\.env", re.IGNORECASE),
    re.compile(r"\bgrep\b.*EDARSAHUB_SQL.*\.env", re.IGNORECASE),
    re.compile(r"\bprintenv\b"),
    re.compile(r"(^|[;&|]\s*)env\s*($|[;&|])", re.M),
]

ALLOW = [
    "tests_guardrails/test_p0_no_secret_dump_commands.py",
    "auditorias_seguridad",
    "venv",
    "__pycache__",
    ".git",
]

hits = []

for p in ROOT.rglob("*"):
    if not p.is_file():
        continue

    sp = str(p).replace("/app/backend/", "")

    if any(a in sp for a in ALLOW):
        continue

    if p.suffix.lower() not in [".py", ".sh", ".md", ".txt"]:
        continue

    txt = p.read_text(errors="ignore")

    for pattern in FORBIDDEN_PATTERNS:
        for _ in pattern.finditer(txt):
            hits.append((sp, pattern.pattern))

if hits:
    print("FAIL comandos que pueden exponer secretos:")
    for sp, pattern in hits:
        print(sp, "=>", pattern)
    sys.exit(1)

print("PASS no hay comandos de exposición de secretos")
