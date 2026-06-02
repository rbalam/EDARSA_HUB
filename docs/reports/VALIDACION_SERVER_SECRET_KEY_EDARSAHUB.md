# VALIDACIÓN SERVER_SECRET_KEY EDARSAHUB

Generado: 2026-06-02T22:35:26+00:00

## Regla

SERVER_SECRET_KEY debe estar configurada en todo entorno que ejecute jobs, scheduler, sincronizaciones, dry-runs o conexiones a Servidores_Conexiones.

## Validación de variable de entorno

```text
SERVER_SECRET_KEY_STATUS= NO_CONFIGURADA
SERVER_SECRET_KEY_LENGTH= 0
```

## Validación de descifrado

```text
SERVER_SECRET_KEY_STATUS= NO_CONFIGURADA
SERVER_SECRET_KEY_LENGTH= 0
RESULT=FAIL
REASON= SERVER_SECRET_KEY no está configurada. No se pueden descifrar credenciales de Servidores_Conexiones.
```

## Archivos relacionados

```text
total 16
drwxr-xr-x  3 root root 4096 Jun  2 22:35 .
drwxr-xr-x 11 root root 4096 Jun  2 22:35 ..
drwxr-xr-x  2 root root 4096 Jun  2 22:35 __pycache__
-rw-r--r--  1 root root  605 Jun  2 22:35 server_secret_guard.py
-rwxr-xr-x  1 root root 25656 Jun  2 20:52 sync_sales_dry_run.py
-rwxr-xr-x  1 root root  8622 Jun  2 22:32 test_sql_connection_from_servidores.py
-rwxr-xr-x  1 root root  4205 Jun  2 22:35 validate_server_secret_key.py
```

## Conclusión esperada

- Si RESULT=OK: se pueden ejecutar pruebas de conexión y dry-runs.
- Si RESULT=FAIL: no ejecutar dry-runs ni jobs contra servidores externos.

## Seguridad

- No se imprimen passwords.
- No se imprime SERVER_SECRET_KEY.
- No se modifican credenciales.
- No se re-cifran secretos.
