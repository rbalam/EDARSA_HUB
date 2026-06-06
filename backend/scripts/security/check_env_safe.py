import os

REQUIRED = [
    "EDARSAHUB_SQL_HOST",
    "EDARSAHUB_SQL_PORT",
    "EDARSAHUB_SQL_DATABASE",
    "EDARSAHUB_SQL_USER",
    "EDARSAHUB_SQL_PASSWORD",
]

print("VALIDACION SEGURA DE VARIABLES")
for key in REQUIRED:
    value = os.getenv(key)
    print(f"{key}: {'OK' if value else 'FALTA'}")
