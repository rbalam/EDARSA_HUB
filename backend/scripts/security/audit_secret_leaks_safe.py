from pathlib import Path
import os
import sys

ROOT = Path("/app/backend")

keys = [
    "EDARSAHUB_SQL_PASSWORD",
    "EDARSAHUB_SQL_USER",
    "EDARSAHUB_SQL_HOST",
    "MONGO_URL",
    "JWT_SECRET_KEY",
    "SECRET_KEY",
]

secret_values = []
for key in keys:
    value = os.getenv(key)
    if value and len(value) >= 4:
        secret_values.append((key, value))

hits = []

for p in ROOT.rglob("*"):
    if not p.is_file():
        continue

    sp = str(p).replace("/app/backend/", "")

    if any(x in sp for x in ["venv", "__pycache__", ".git", "auditorias_seguridad"]):
        continue

    if p.suffix.lower() not in [".py", ".sh", ".md", ".txt", ".json", ".log"]:
        continue

    txt = p.read_text(errors="ignore")

    for key, value in secret_values:
        if value in txt:
            hits.append((sp, key))

if hits:
    print("FAIL valores secretos presentes en archivos:")
    for sp, key in hits:
        print(sp, "=>", key, "PRESENTE")
    sys.exit(1)

print("PASS no se detectaron valores secretos reales en archivos auditados")
