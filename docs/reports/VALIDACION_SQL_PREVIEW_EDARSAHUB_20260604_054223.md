# VALIDACIÓN SQL PREVIEW EDARSAHUB
Fecha: Thu Jun  4 05:42:23 UTC 2026
Host SQL: 4.255.36.175

## 1. Variables de entorno SQL disponibles, sin exponer secretos
```text
```

## 2. Prueba de red TCP a SQL Server puerto 1433
```text
ERROR TCP 4.255.36.175:1433: TimeoutError: timed out
```

## 3. Drivers ODBC instalados
```text
pyodbc ERROR: ImportError('libodbc.so.2: cannot open shared object file: No such file or directory')
```

## 4. Prueba de conexión pyodbc usando variables existentes
```text
ERROR import pyodbc: ImportError('libodbc.so.2: cannot open shared object file: No such file or directory')
```

