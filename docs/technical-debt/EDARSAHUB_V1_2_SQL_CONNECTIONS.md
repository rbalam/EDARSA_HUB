# EDARSAHUB V1.2 - Deuda tecnica de conexiones SQL

## Contexto

EDARSAHUB V1.0 adopta una normalizacion incremental de conexiones
para mantener el sistema operativo y reducir el riesgo de regresion.

La base V1.0 incluye:

- configuracion SQL lazy;
- variables EDARSAHUB_SQL_* canonicas;
- adaptador central de drivers;
- fachada SQL-first compatible;
- validacion fail-closed de HRLectura;
- validacion de identidad SQL efectiva;
- runner sin efectos secundarios durante importacion;
- dry-run sin conexion;
- cierre y rollback defensivos.

## Alcance obligatorio para V1.2

1. Auditar permisos SQL efectivos, no solamente nombres de login.
2. Implementar gestor de secretos, rotacion y trazabilidad.
3. Crear contratos tipados separados para:
   - read-only;
   - runtime funcional;
   - migraciones.
4. Limitar retries a operaciones transitorias e idempotentes.
5. Incorporar circuit breaker donde corresponda.
6. Agregar observabilidad estructurada y OpenTelemetry.
7. Formalizar pooling y ciclo de vida de conexiones.
8. Crear context managers transaccionales canonicos.
9. Eliminar aperturas directas restantes fuera del adaptador.
10. Incorporar guardrails CI contra:
    - drivers directos;
    - configuracion en import-time;
    - nombres de variables legacy;
    - logins prohibidos;
    - carga funcional de archivos .env;
    - secretos en logs.
11. Definir y retirar formalmente compatibilidad legacy.
12. Evaluar cifrado TLS y configuracion de certificados.
13. Reemplazar el fallback amplio de drivers en `get_external_sql_connection` por una politica fail-closed, despues de auditar sus consumidores POS.

## Exclusiones

Los siguientes directorios y archivos historicos no forman parte
del runtime y no deben migrarse como consumidores activos:

- backend/auditorias_p4/backup_*
- archivos *.bak*
- reportes historicos de auditoria

Se conservan exclusivamente como evidencia.
