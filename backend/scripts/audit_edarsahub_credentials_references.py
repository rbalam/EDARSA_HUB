from pathlib import Path
import re

ROOT = Path("/app/backend")
IGNORE = {
    "core/config/edarsahub_config.py",
    "core/config/edarsahub_sql.py",
    "scripts/audit_edarsahub_credentials_references.py",
}

patterns = [
    r"EDARSAHUB_SQL_HOST",
    r"EDARSAHUB_SQL_PORT",
    r"EDARSAHUB_SQL_DATABASE",
    r"EDARSAHUB_SQL_USER",
    r"EDARSAHUB_SQL_PASSWORD",
    r"EDARSAHUB_HOST",
    r"EDARSAHUB_DATABASE",
    r"EDARSAHUB_USERNAME",
    r"EDARSAHUB_PASSWORD",
    r"'HRLectura'",
    r"'National09",
]

hits = []

for p in ROOT.rglob("*.py"):
    rel = str(p.relative_to(ROOT))
    if rel in IGNORE or ".bak" in rel or "__pycache__" in rel or "backup" in rel.lower():
        continue

    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        continue
        
    for i, line in enumerate(txt.splitlines(), start=1):
        if any(re.search(pat, line, re.I) for pat in patterns):
            hits.append((rel, i, line.strip()))

print("=== REFERENCIAS PENDIENTES CREDENCIALES EDARSAHUB ===")
print(f"TOTAL: {len(hits)}")

current = None
for rel, i, line in hits[:80]:  # Limitar output
    if rel != current:
        current = rel
        print(f"\n--- {rel} ---")
    # Redactar passwords
    safe = re.sub(r"National09[^'\"]*", "***", line)
    safe = re.sub(r"(password['\"]?\s*[:=]\s*['\"])[^'\"]+", r"\1***", safe, flags=re.I)
    print(f"L{i}: {safe[:100]}")

if len(hits) > 80:
    print(f"\n... y {len(hits) - 80} más")
