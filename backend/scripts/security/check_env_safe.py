import os

REQUIRED = [
    "EDARSAHUB_SQL_HOST",
    "EDARSAHUB_SQL_PORT",
    "EDARSAHUB_SQL_DATABASE",
    "EDARSAHUB_SQL_USER",
    "EDARSAHUB_SQL_PASSWORD",
]

print("VALIDACION SEGURA DE VARIABLES")
missing = []
for key in REQUIRED:
    ok = bool(os.getenv(key))
    print(f"{key}: {'OK' if ok else 'FALTA'}")
    if not ok:
        missing.append(key)

if missing:
    raise SystemExit(1)
