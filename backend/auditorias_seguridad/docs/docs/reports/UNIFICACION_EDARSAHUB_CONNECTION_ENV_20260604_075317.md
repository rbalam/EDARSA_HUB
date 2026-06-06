# UNIFICACIÓN CONEXIÓN EDARSAHUB SQL DESDE .env
Fecha: Thu Jun  4 07:53:17 UTC 2026

## 1. Backup
```text
/app/backend/server.py -> /app/backend/server.py.backup_env_connection_20260604_075317
/app/backend/modules/compras/sync_service.py -> /app/backend/modules/compras/sync_service.py.backup_env_connection_20260604_075317
```

## 2. Validación de credenciales hardcoded
```text
OK: sin credenciales hardcoded detectadas
```

## 3. Validación sintaxis Python
```text
OK py_compile
```

## 4. Referencias get_edarsahub_connection
```text
/app/backend/server.py:12:def get_edarsahub_connection():
/app/backend/modules/compras/sync_service.py:30:def get_edarsahub_connection():
/app/backend/modules/compras/sync_service.py:72:        conn = get_edarsahub_connection()
/app/backend/modules/compras/sync_service.py:134:        conn = get_edarsahub_connection()
/app/backend/modules/compras/sync_service.py:267:        conn = get_edarsahub_connection()
/app/backend/modules/compras/sync_service.py:400:        conn = get_edarsahub_connection()
/app/backend/modules/compras/sync_service.py:462:        conn = get_edarsahub_connection()
/app/backend/modules/compras/sync_service.py:482:        conn = get_edarsahub_connection()
/app/backend/modules/compras/sync_service.py:546:        conn = get_edarsahub_connection()
/app/backend/modules/compras/sync_service.py:629:        conn = get_edarsahub_connection()
/app/backend/modules/compras/sync_service.py:770:        conn = get_edarsahub_connection()
/app/backend/modules/compras/sync_service.py:912:        conn = get_edarsahub_connection()
/app/backend/modules/compras/sync_service.py:1054:        conn = get_edarsahub_connection()
/app/backend/modules/compras/sync_service.py:1196:        conn = get_edarsahub_connection()
```
